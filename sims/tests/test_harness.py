"""Tests for the harness itself.

The harness enforces HARNESS.md. If it can be talked out of that enforcement, every
result downstream is worth less, so these tests are mostly about what it *refuses*.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness import (  # noqa: E402
    INCONCLUSIVE,
    REFUTED,
    SUPPORTED,
    ManifestError,
    Verdict,
    run,
    sweep_points,
    validate,
)
from harness.manifest import is_pilot, sha256_of  # noqa: E402


def good_config(**overrides):
    config = {
        "name": "t", "seeds": [0, 1, 2, 3, 4], "sweeps": {"g": [1, 2]},
        "null_model": "shuffle", "refute_if": "x < 1", "refute_params": {"x": 1},
        "tier": 0, "runtime_estimate_s": 1, "depends_on": [],
    }
    config.update(overrides)
    return config


# --------------------------------------------------------------------------
# §2 manifest enforcement
# --------------------------------------------------------------------------

def test_good_config_validates():
    validate(good_config())


@pytest.mark.parametrize("field", ["name", "seeds", "sweeps", "null_model",
                                   "refute_if", "tier", "runtime_estimate_s",
                                   "depends_on"])
def test_every_required_field_is_required(field):
    config = good_config()
    del config[field]
    with pytest.raises(ManifestError):
        validate(config)


def test_null_model_is_mandatory():
    """§2: if you can't name the null, you don't have an experiment."""
    with pytest.raises(ManifestError, match="null"):
        validate(good_config(null_model=""))


def test_refute_if_is_mandatory():
    with pytest.raises(ManifestError, match="refute_if"):
        validate(good_config(refute_if=""))


def test_refute_params_is_required_by_this_harness():
    config = good_config()
    del config["refute_params"]
    with pytest.raises(ManifestError, match="refute_params"):
        validate(config)


def test_sweeps_must_name_at_least_one_parameter():
    with pytest.raises(ManifestError, match="sweeps"):
        validate(good_config(sweeps={}))


def test_sweep_values_must_be_non_empty():
    with pytest.raises(ManifestError):
        validate(good_config(sweeps={"g": []}))


def test_duplicate_seeds_rejected():
    with pytest.raises(ManifestError, match="distinct"):
        validate(good_config(seeds=[0, 0, 1, 2, 3]))


def test_fewer_than_five_seeds_is_a_pilot_not_an_error():
    """§2 allows it; the run wears the PILOT label rather than being blocked."""
    config = good_config(seeds=[0])
    validate(config)
    assert is_pilot(config)
    assert not is_pilot(good_config())


def test_sweep_points_is_the_cartesian_product():
    points = sweep_points({"a": [1, 2], "b": ["x", "y", "z"]})
    assert len(points) == 6
    assert {"a": 1, "b": "x"} in points
    assert {"a": 2, "b": "z"} in points


# --------------------------------------------------------------------------
# §4 verdict discipline
# --------------------------------------------------------------------------

def test_verdict_must_be_one_of_the_three():
    with pytest.raises(ValueError):
        Verdict("MOSTLY_FINE", "reason")


def test_a_verdict_without_a_reason_is_rejected():
    with pytest.raises(ValueError, match="reason"):
        Verdict(SUPPORTED, "")


def test_all_three_verdicts_are_constructible():
    for name in (SUPPORTED, REFUTED, INCONCLUSIVE):
        assert Verdict(name, "because").verdict == name


# --------------------------------------------------------------------------
# §3 execution contract — artifacts
# --------------------------------------------------------------------------

def _write_config(tmp_path, **overrides):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(good_config(**overrides)), encoding="utf-8")
    return path


def test_run_emits_all_four_artifacts(tmp_path):
    path = _write_config(tmp_path, claim="a claim")
    results = tmp_path / "results" / "stamp"

    measure = lambda seed, sweep, config: {"v": float(seed + sweep["g"])}
    null = lambda seed, sweep, config: {"v_null": 0.0}
    grade = lambda obs, nulls, config: Verdict(SUPPORTED, "all good", {"n": len(obs)})

    verdict = run(path, measure, null, grade,
                  argv=["--results-dir", str(results), "--quiet"])

    assert verdict.verdict == SUPPORTED
    assert (results / "metrics.json").exists()
    assert (results / "summary.md").exists()
    assert (results / "ledger_entry.jsonl").exists()

    metrics = json.loads((results / "metrics.json").read_text())
    # 5 seeds x 2 sweep points, measured and nulled
    assert len(metrics["observations"]) == 10
    assert len(metrics["null_observations"]) == 10
    assert metrics["verdict"] == SUPPORTED
    assert metrics["reason"] == "all good"


def test_ledger_entry_carries_hashes_and_the_refutation_condition(tmp_path):
    path = _write_config(tmp_path, claim="a claim")
    results = tmp_path / "results" / "stamp"
    run(path, lambda s, w, c: {"v": 1.0}, lambda s, w, c: {"v": 0.0},
        lambda o, n, c: Verdict(REFUTED, "nope"),
        argv=["--results-dir", str(results), "--quiet"])

    entry = json.loads((results / "ledger_entry.jsonl").read_text())
    assert entry["type"] == "MEASURE"
    assert entry["verdict"] == REFUTED
    assert entry["reason"] == "nope"
    assert entry["refute_if"] == "x < 1"
    assert entry["null_model"] == "shuffle"
    assert entry["claim"] == "a claim"
    assert len(entry["metrics_hash"]) == 64
    assert len(entry["config_hash"]) == 64


def test_metrics_hash_matches_the_file_on_disk(tmp_path):
    import hashlib
    path = _write_config(tmp_path)
    results = tmp_path / "results" / "stamp"
    run(path, lambda s, w, c: {"v": 1.0}, lambda s, w, c: {"v": 0.0},
        lambda o, n, c: Verdict(SUPPORTED, "ok"),
        argv=["--results-dir", str(results), "--quiet"])

    entry = json.loads((results / "ledger_entry.jsonl").read_text())
    actual = hashlib.sha256((results / "metrics.json").read_bytes()).hexdigest()
    assert entry["metrics_hash"] == actual


def test_exploratory_flag_downgrades_the_entry_type(tmp_path):
    """§4: a refute_if edited after seeing data is EXPLORATORY, never PREDICT."""
    path = _write_config(tmp_path, exploratory=True)
    results = tmp_path / "results" / "stamp"
    run(path, lambda s, w, c: {"v": 1.0}, lambda s, w, c: {"v": 0.0},
        lambda o, n, c: Verdict(SUPPORTED, "ok"),
        argv=["--results-dir", str(results), "--quiet"])
    entry = json.loads((results / "ledger_entry.jsonl").read_text())
    assert entry["type"] == "EXPLORATORY"


def test_pilot_runs_are_labelled_in_metrics_and_ledger(tmp_path):
    path = _write_config(tmp_path)
    results = tmp_path / "results" / "stamp"
    run(path, lambda s, w, c: {"v": 1.0}, lambda s, w, c: {"v": 0.0},
        lambda o, n, c: Verdict(SUPPORTED, "ok"),
        argv=["--results-dir", str(results), "--seeds", "0", "--quiet"])

    assert json.loads((results / "metrics.json").read_text())["pilot"] is True
    assert json.loads((results / "ledger_entry.jsonl").read_text())["pilot"] is True


def test_summary_names_the_verdict_and_the_refutation_condition(tmp_path):
    path = _write_config(tmp_path, claim="the claim under test")
    results = tmp_path / "results" / "stamp"
    run(path, lambda s, w, c: {"v": 1.0}, lambda s, w, c: {"v": 0.0},
        lambda o, n, c: Verdict(INCONCLUSIVE, "not enough seeds cleared it"),
        argv=["--results-dir", str(results), "--quiet"])

    text = (results / "summary.md").read_text()
    assert "INCONCLUSIVE" in text
    assert "the claim under test" in text
    assert "x < 1" in text                       # the refute_if, quoted
    assert "not enough seeds cleared it" in text


def test_config_hash_is_stable_under_key_order():
    assert sha256_of({"a": 1, "b": 2}) == sha256_of({"b": 2, "a": 1})


def test_grade_receives_every_seed_and_sweep_point(tmp_path):
    path = _write_config(tmp_path)
    seen = {}

    def grade(obs, nulls, config):
        seen["pairs"] = {(row["seed"], row["sweep"]["g"]) for row in obs}
        return Verdict(SUPPORTED, "ok")

    run(path, lambda s, w, c: {"v": 1.0}, lambda s, w, c: {"v": 0.0}, grade,
        argv=["--results-dir", str(tmp_path / "r"), "--quiet"])

    assert seen["pairs"] == {(s, g) for s in range(5) for g in (1, 2)}


# --------------------------------------------------------------------------
# The two retrofitted sims conform
# --------------------------------------------------------------------------

SHIPPED = ["fractal_basin", "snap_information", "ep2_prereg", "kappa_eff", "shape_csd"]


@pytest.mark.parametrize("name", SHIPPED)
def test_shipped_configs_conform_to_the_standard(name):
    config = json.loads((ROOT / name / "config.json").read_text(encoding="utf-8"))
    validate(config)
    assert len(config["seeds"]) >= 5
    assert config["sweeps"]
    assert config["claim"]


@pytest.mark.parametrize("name", SHIPPED)
def test_each_sim_has_its_pre_registration_documents(name):
    for doc in ("NULL.md", "REFUTE.md"):
        assert (ROOT / name / doc).exists(), f"{name}/{doc} missing"


@pytest.mark.parametrize("name", SHIPPED)
def test_every_graded_number_is_pre_committed_in_writing(name):
    """No number the grader uses may be absent from the pre-committed documents.

    refute_params is what run.py actually grades against. Every value in it must
    appear either in the one-line refute_if prose or in REFUTE.md — both of which
    are committed before the sim runs. A threshold that exists only in the config
    is one nobody agreed to in advance, which is the drift this rule prevents.

    Detection-rule parameters (how the signal is computed) legitimately live in
    REFUTE.md rather than the one-line prose; refutation thresholds belong in both.
    """
    folder = ROOT / name
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    committed = config["refute_if"] + "\n" + (folder / "REFUTE.md").read_text(encoding="utf-8")
    for key, value in config["refute_params"].items():
        if key.endswith("_at_seeds"):
            continue
        forms = {str(value), str(value).rstrip("0").rstrip("."), f"{value:.0%}"
                 if isinstance(value, float) and value < 1 else str(value)}
        assert any(f in committed for f in forms), (
            f"{name}: refute_params.{key}={value} appears in neither refute_if "
            "nor REFUTE.md — it was never pre-committed")
