"""Tests for shadow.py.

A shadow detector's danger is crying shadow everywhere: an oracle that flags
everything is indistinguishable from one that knows nothing. So these test the
detectors fire on real residuals AND stay quiet on manufactured coincidences.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import shadow  # noqa: E402


def fake(name="s", sweeps=None, params=None, metrics=None, claim="", refute_if="x < 1",
         refute_params=None, tmp=None):
    config = {
        "name": name, "claim": claim, "seeds": [0, 1, 2, 3, 4],
        "sweeps": sweeps if sweeps is not None else {"g": [1, 2]},
        "null_model": "shuffle", "refute_if": refute_if,
        "refute_params": refute_params or {"x": 1},
        "tier": 0, "runtime_estimate_s": 1, "depends_on": [],
        "block": params or {},
    }
    obs = [{"seed": i, "sweep": {"g": 1}, "metrics": m}
           for i, m in enumerate(metrics or [])]
    return {"path": tmp or ROOT, "name": name, "config": config,
            "metrics": {"observations": obs} if metrics else None}


# --------------------------------------------------------------------------
# censoring
# --------------------------------------------------------------------------

def test_censoring_fires_on_a_pile_up_at_a_config_limit():
    metrics = [{"tau": 600.0}] * 8 + [{"tau": 100.0}, {"tau": 200.0}]
    found = shadow.censoring_shadows(fake(params={"recovery_max_t": 600.0}, metrics=metrics))
    assert found and found[0]["metric"] == "tau"
    assert found[0]["set_by"] == "recovery_max_t"
    assert found[0]["attribution_confident"]


def test_censoring_withholds_attribution_on_a_trivial_constant():
    """1.0 matches something in every config; that is coincidence, not evidence."""
    metrics = [{"ratio": 1.0}] * 8 + [{"ratio": 0.5}, {"ratio": 0.7}]
    found = shadow.censoring_shadows(fake(params={"stiffness": 1.0}, metrics=metrics))
    assert found and found[0]["set_by"] is None
    assert not found[0]["attribution_confident"]
    assert "coincidence" in found[0]["evidence"]


def test_censoring_ignores_indicator_flags():
    """A 0/1 flag piling up is its normal behaviour, not a truncated measurement."""
    metrics = [{"fired": 1.0}] * 8 + [{"fired": 0.0}, {"fired": 0.0}]
    assert shadow.censoring_shadows(fake(params={"x": 1.0}, metrics=metrics)) == []


def test_censoring_ignores_a_constant_metric():
    metrics = [{"c": 5.0}] * 10
    assert shadow.censoring_shadows(fake(params={"c_limit": 5.0}, metrics=metrics)) == []


def test_censoring_needs_no_metrics_to_be_safe():
    assert shadow.censoring_shadows(fake()) == []


# --------------------------------------------------------------------------
# discretization
# --------------------------------------------------------------------------

def test_discretization_flags_a_fixed_mesh_parameter():
    found = shadow.discretization_shadows(fake(params={"N": 200, "epochs": 200}))
    assert {f["parameter"] for f in found} == {"N", "epochs"}


def test_discretization_ignores_a_swept_mesh_parameter():
    found = shadow.discretization_shadows(
        fake(sweeps={"epochs": [100, 200]}, params={"epochs": 200}))
    assert not [f for f in found if f["parameter"] == "epochs"]


def test_discretization_ignores_a_parameter_varied_by_a_doubled_partner():
    """basin_convergence varies N via N_doubled; that is not a pinned mesh."""
    found = shadow.discretization_shadows(fake(params={"N": 200, "N_doubled": 400}))
    assert found == []


def test_discretization_ignores_non_mesh_parameters():
    found = shadow.discretization_shadows(fake(params={"stiffness": 1.2, "tolerance": 0.05}))
    assert found == []


# --------------------------------------------------------------------------
# cross-sim
# --------------------------------------------------------------------------

def test_cross_sim_flags_a_parameter_another_sim_sweeps():
    a = fake(name="a", params={"hidden": 32})
    b = fake(name="b", sweeps={"hidden_width": [16, 64]})
    found = shadow.cross_sim_shadows(a, [a, b])
    assert found and found[0]["parameter"] == "hidden"
    assert "b:hidden_width" in found[0]["swept_by"]


def test_cross_sim_does_not_conflate_a_count_with_a_magnitude():
    """n_probe (how many probes) is not probe_magnitude (how hard). Stemming
    them together invents a residual that is not there."""
    a = fake(name="a", params={"n_probe": 4000})
    b = fake(name="b", sweeps={"probe_magnitude": [0.03, 0.05]})
    assert shadow.cross_sim_shadows(a, [a, b]) == []


def test_cross_sim_ignores_what_this_sim_already_sweeps():
    a = fake(name="a", sweeps={"gamma": [0.1, 0.5]}, params={"gamma": 0.1})
    b = fake(name="b", sweeps={"gamma": [0.2]})
    assert shadow.cross_sim_shadows(a, [a, b]) == []


def test_stem_normalizes_a_suffix_but_not_a_count_prefix():
    assert shadow.stem("hidden_width") == shadow.stem("hidden")
    assert shadow.stem("n_probe") != shadow.stem("probe_magnitude")


# --------------------------------------------------------------------------
# claim
# --------------------------------------------------------------------------

def test_claim_flags_an_untested_assertion():
    found = shadow.claim_shadows(fake(
        claim="alpha stays below the ceiling, and the two-well boundary is not fractal",
        refute_if="alpha >= 0.9", refute_params={"alpha_ceiling": 0.9}))
    assert any("fractal" in f["clause"] for f in found)


def test_claim_stays_quiet_when_the_condition_covers_it():
    found = shadow.claim_shadows(fake(
        claim="alpha stays below the ceiling",
        refute_if="alpha >= ceiling", refute_params={"alpha": 0.9}))
    assert found == []


def test_claim_needs_a_claim():
    assert shadow.claim_shadows(fake(claim="")) == []


# --------------------------------------------------------------------------
# the backtest is itself a test
# --------------------------------------------------------------------------

def test_backtest_recovers_every_known_shadow():
    """The shadows this repo paid for must be visible in prior artifacts.

    If this fails, the detectors have regressed into not measuring anything.
    """
    sims = [shadow.load(d) for d in shadow.sim_dirs()]
    text, ok = shadow.backtest(sims)
    assert ok, text


def test_known_shadows_name_real_sims():
    names = {s["name"] for s in (shadow.load(d) for d in shadow.sim_dirs())}
    for known in shadow.KNOWN_SHADOWS:
        assert known["sim"] in names
        assert known["detector"] in set(shadow.DETECTORS) | {"cross_sim"}
