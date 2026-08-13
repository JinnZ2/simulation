"""Tests for explore.py.

The tool's value is in what it refuses. A recycler that would reformulate any
claim until it passed is worse than no recycler, so these mostly test the gates.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import explore  # noqa: E402
from harness import ManifestError, validate  # noqa: E402


def fake_sim(verdict="REFUTED", generation=0, metrics=None, sweep_key="g",
             findings="", claim="a fold claim about snap"):
    obs = metrics or [
        {"seed": s, "sweep": {sweep_key: v}, "metrics": {"graded_x": float(v),
                                                         "spare_y": float(v) * 2.0}}
        for v in (1, 2, 3) for s in range(3)
    ]
    return {
        "path": ROOT / "fake",
        "name": "fake",
        "config": {
            "name": "fake", "claim": claim, "seeds": [0, 1, 2, 3, 4],
            "sweeps": {sweep_key: [1, 2, 3]}, "null_model": "shuffle",
            "refute_if": "graded_x < 1", "refute_params": {"graded_x": 1},
            "tier": 0, "runtime_estimate_s": 1, "depends_on": [],
            "generation": generation,
        },
        "metrics": {"verdict": verdict, "reason": "because", "observations": obs},
        "findings": findings,
    }


# --------------------------------------------------------------------------
# Guard 1 — only refuted claims may be recycled
# --------------------------------------------------------------------------

def test_refuses_to_recycle_a_supported_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="refusing to recycle"):
        explore.scaffold(fake_sim(verdict="SUPPORTED"))


@pytest.mark.parametrize("verdict", ["REFUTED", "INCONCLUSIVE"])
def test_recyclable_verdicts_scaffold(tmp_path, monkeypatch, verdict):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    dest = explore.scaffold(fake_sim(verdict=verdict))
    assert dest.exists()
    assert (dest / "config.json").exists()
    assert (dest / "REFUTE.md").exists()
    assert (dest / "NULL.md").exists()


# --------------------------------------------------------------------------
# Guard 2 — the escape hatch bounds a lineage
# --------------------------------------------------------------------------

def test_escape_hatch_fires_at_the_generation_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    monkeypatch.setattr(explore, "UNKNOWN_JOURNAL", tmp_path / "unknown_journal.jsonl")
    with pytest.raises(SystemExit, match="escape hatch"):
        explore.scaffold(fake_sim(generation=explore.ESCAPE_HATCH_GENERATION - 1))

    entries = [json.loads(line) for line in
               (tmp_path / "unknown_journal.jsonl").read_text().splitlines()]
    assert entries[0]["type"] == "ESCAPE_HATCH"
    assert entries[0]["generation"] == explore.ESCAPE_HATCH_GENERATION


def test_escape_hatch_scaffolds_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    monkeypatch.setattr(explore, "UNKNOWN_JOURNAL", tmp_path / "j.jsonl")
    with pytest.raises(SystemExit):
        explore.scaffold(fake_sim(generation=5))
    assert not any(p.is_dir() for p in tmp_path.iterdir())


def test_generation_increments_along_a_lineage(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    dest = explore.scaffold(fake_sim(generation=1))
    config = json.loads((dest / "config.json").read_text())
    assert config["generation"] == 2
    assert config["derived_from"] == "fake"
    assert config["depends_on"] == ["fake"]


# --------------------------------------------------------------------------
# Guard 3 — the scaffold cannot run until a human writes the condition
# --------------------------------------------------------------------------

def test_scaffolded_config_is_rejected_by_the_harness(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    dest = explore.scaffold(fake_sim())
    config = json.loads((dest / "config.json").read_text())
    assert config["refute_if"] == ""
    with pytest.raises(ManifestError, match="refute_if"):
        validate(config)


def test_scaffolded_config_is_marked_exploratory(tmp_path, monkeypatch):
    """§4: a claim reformulated after seeing data never re-enters as PREDICT."""
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    dest = explore.scaffold(fake_sim())
    assert json.loads((dest / "config.json").read_text())["exploratory"] is True


def test_scaffold_does_not_invent_a_claim_or_a_null(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    dest = explore.scaffold(fake_sim())
    config = json.loads((dest / "config.json").read_text())
    assert config["claim"].startswith("TODO")
    assert config["null_model"].startswith("TODO")


def test_scaffold_refuses_to_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    explore.scaffold(fake_sim())
    with pytest.raises(SystemExit, match="already exists"):
        explore.scaffold(fake_sim())


# --------------------------------------------------------------------------
# Hidden-variable scan
# --------------------------------------------------------------------------

def test_finds_an_ungraded_metric_that_tracks_the_sweep():
    found = explore.hidden_variables(fake_sim())
    names = [f["metric"] for f in found]
    assert "spare_y" in names
    assert "graded_x" not in names        # graded, so not hidden


def test_flags_an_affine_restatement_rather_than_calling_it_a_discovery():
    """d_boundary = 2 - alpha is a restatement, not a hidden variable."""
    obs = [{"seed": s, "sweep": {"g": v},
            "metrics": {"graded_x": float(v), "spare_y": 2.0 - float(v)}}
           for v in (1, 2, 3) for s in range(3)]
    found = explore.hidden_variables(fake_sim(metrics=obs))
    spare = next(f for f in found if f["metric"] == "spare_y")
    assert spare["restates"] == "graded_x"


def test_constant_metrics_are_not_reported():
    obs = [{"seed": s, "sweep": {"g": v},
            "metrics": {"graded_x": float(v), "spare_y": 7.0}}
           for v in (1, 2, 3) for s in range(3)]
    assert not [f for f in explore.hidden_variables(fake_sim(metrics=obs))
                if f["metric"] == "spare_y"]


def test_nan_metrics_are_skipped():
    obs = [{"seed": s, "sweep": {"g": v},
            "metrics": {"graded_x": float(v), "spare_y": float("nan")}}
           for v in (1, 2, 3) for s in range(3)]
    assert not [f for f in explore.hidden_variables(fake_sim(metrics=obs))
                if f["metric"] == "spare_y"]


def test_pearson_matches_known_values():
    assert explore.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert explore.pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)
    assert explore.pearson([1, 1, 1], [1, 2, 3]) == 0.0


# --------------------------------------------------------------------------
# Cross-domain and lead extraction
# --------------------------------------------------------------------------

def test_fold_signature_carries_the_cusp_domain_table():
    transfers = explore.cross_domain(fake_sim(claim="a bistable snap under load"))
    fold = next(t for t in transfers if t["signature"] == "fold")
    assert "B7 climate tipping" in fold["domains"]
    assert len(fold["domains"]) == 8


def test_unrelated_claim_gets_no_transfer():
    assert explore.cross_domain(fake_sim(claim="an unrelated botanical survey")) == []


def test_leads_join_bullets_that_wrap_across_lines():
    findings = ("## What a corrected test would look like\n\n"
                "1. **Rise onset, not peak.** Define the indicator as the smallest\n"
                "   alpha where kappa exceeds a multiple of baseline.\n"
                "2. Normalize the ray.\n")
    leads = explore.successor_leads(fake_sim(findings=findings))
    assert leads and len(leads[0]["items"]) == 2
    assert leads[0]["items"][0].endswith("multiple of baseline.")


def test_no_findings_yields_no_leads():
    assert explore.successor_leads(fake_sim(findings="")) == []


def test_report_names_recyclable_and_non_recyclable(tmp_path, monkeypatch):
    monkeypatch.setattr(explore, "ROOT", tmp_path)
    text = explore.report([fake_sim(verdict="SUPPORTED"), fake_sim()], True, True)
    assert "may not be reformulated" in text
    assert "--scaffold" in text
