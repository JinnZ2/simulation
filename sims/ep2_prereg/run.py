#!/usr/bin/env python3
"""ep2_prereg — statistical power of the E-P2 physical protocol.

Retrofit of original_ep2_prereg_sim.py to Sim Harness Standard v1 (§5 item 1).
Reads ONLY config.json + CLI overrides (§3).

Changes from the original, recorded rather than silent:
  - a rigid-arm null (creep, no fold) is measured at every point. The original
    had no null at all, which is how the v1 formulation reached 96% false
    positives before anyone noticed (notes/15).
  - all three criteria are evaluated on both arms every run: absolute_scan,
    differential_scan, differential_checkpoint. The verdict uses only the
    pre-committed one; the other two are recorded so the multiple-comparisons
    cost is a measured number.
  - timing noise is swept {0.02, 0.05, 0.10}; the original ran a sensitivity
    loop but reported one headline at 5%.
  - 5 seeds, each a distinct trial block.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

CONFIG = Path(__file__).resolve().parent / "config.json"


# --------------------------------------------------------------------------
# Physics — fold normal form, unchanged from the original
# --------------------------------------------------------------------------

def tau_bistable(comp: float, creep: float, p: dict[str, Any]) -> float:
    """Recovery time on the bistable arm: tau ~ 1/k_eff, k_eff ~ sqrt(1 - c/c_snap)."""
    snap, tau0, c0 = p["snap_compression"], p["tau0"], p["baseline_compression"]
    k_rel = np.sqrt(max(1e-9, 1.0 - comp / snap)) * (1.0 - creep)
    return tau0 * np.sqrt(1.0 - c0 / snap) / k_rel


def tau_rigid(comp: float, creep: float, p: dict[str, Any]) -> float:
    """Recovery time on the rigid arm: no fold, so creep only.

    This is the null's entire content. If a real rigid frame turns out to have
    any load-dependent recovery time, this model is optimistic and the measured
    false-positive rates are better than reality.
    """
    return p["tau0"] / (1.0 - creep)


def _measure_arm(rng: np.random.Generator, noise: float, p: dict[str, Any],
                 bistable: bool) -> tuple[np.ndarray, np.ndarray]:
    """One trial: (compressions, per-step probe samples) for the given arm."""
    snap, step, c0 = p["snap_compression"], p["step"], p["baseline_compression"]
    comps = np.arange(c0, snap - 0.0001, step)
    n_probe = p["probes_per_step"]
    samples = np.empty((len(comps), n_probe))
    tau_fn = tau_bistable if bistable else tau_rigid
    for i, c in enumerate(comps):
        true_tau = tau_fn(float(c), p["creep_per_step"] * i, p)
        samples[i] = true_tau * (1.0 + noise * rng.standard_normal(n_probe))
    return comps, samples


def _welch_t(current: np.ndarray, baseline: np.ndarray) -> float:
    n_c, n_b = len(current), len(baseline)
    denom = np.sqrt(current.var(ddof=1) / n_c + baseline.var(ddof=1) / n_b)
    if denom <= 0:
        return 0.0
    return float((current.mean() - baseline.mean()) / denom)


# --------------------------------------------------------------------------
# The three criteria
# --------------------------------------------------------------------------

def _scan(comps: np.ndarray, series: np.ndarray, p: dict[str, Any]) -> float | None:
    """Sequential scan: first compression whose t-statistic clears threshold.

    Fifteen chances at a nominal alpha of 0.05. That is the multiple-comparisons
    machine notes/15 identified; it is measured here, not assumed.
    """
    base_n = p["baseline_steps"]
    baseline = series[:base_n].flatten()
    for i in range(base_n, len(comps)):
        if _welch_t(series[i], baseline) > p["t_threshold"]:
            return float(comps[i])
    return None


def _checkpoint(comps: np.ndarray, series: np.ndarray, p: dict[str, Any]) -> bool:
    """One t-test at the pre-committed compression. No scanning."""
    base_n = p["baseline_steps"]
    baseline = series[:base_n].flatten()
    idx = int(np.argmin(np.abs(comps - p["checkpoint_compression"])))
    return _welch_t(series[idx], baseline) > p["t_threshold"]


def _trial(rng: np.random.Generator, noise: float, p: dict[str, Any],
           bistable: bool) -> dict[str, Any]:
    comps, arm = _measure_arm(rng, noise, p, bistable=bistable)
    _, rigid = _measure_arm(rng, noise, p, bistable=False)
    ratio = arm / rigid                      # creep divides out
    return {
        "absolute_scan": _scan(comps, arm, p),
        "differential_scan": _scan(comps, ratio, p),
        "differential_checkpoint": _checkpoint(comps, ratio, p),
    }


def _rates(rng: np.random.Generator, noise: float, p: dict[str, Any],
           bistable: bool) -> dict[str, float]:
    trials = p["trials"]
    results = [_trial(rng, noise, p, bistable) for _ in range(trials)]

    abs_hits = [r["absolute_scan"] for r in results if r["absolute_scan"] is not None]
    dif_hits = [r["differential_scan"] for r in results if r["differential_scan"] is not None]
    checkpoint_rate = float(np.mean([r["differential_checkpoint"] for r in results]))

    snap, load_range = p["snap_compression"], p["load_range"]
    checkpoint_lead = (snap - p["checkpoint_compression"]) / load_range

    out = {
        "rate_absolute_scan": len(abs_hits) / trials,
        "rate_differential_scan": len(dif_hits) / trials,
        "rate_differential_checkpoint": checkpoint_rate,
        "checkpoint_lead_frac": checkpoint_lead,
    }
    out["median_lead_absolute_scan"] = (
        float(np.median([(snap - d) / load_range for d in abs_hits])) if abs_hits else float("nan"))
    out["median_lead_differential_scan"] = (
        float(np.median([(snap - d) / load_range for d in dif_hits])) if dif_hits else float("nan"))
    return out


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------

def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    p = config["physics"]
    rng = np.random.default_rng(seed)
    rates = _rates(rng, sweep["timing_noise"], p, bistable=True)
    return {f"detection_{k}": v for k, v in rates.items()}


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """rigid_arm_creep_only — the same protocol on an arm with no fold."""
    p = config["physics"]
    rng = np.random.default_rng(seed + 10_000)
    rates = _rates(rng, sweep["timing_noise"], p, bistable=False)
    return {f"fp_{k}": v for k, v in rates.items()}


# --------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------

def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]
    min_detect, max_fp = p["min_detection_rate"], p["max_false_positive"]

    per_noise: dict[float, dict[str, Any]] = {}
    for row in obs:
        noise = row["sweep"]["timing_noise"]
        matched = next(n for n in null_obs
                       if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        detect = row["metrics"]["detection_rate_differential_checkpoint"]
        fp = matched["metrics"]["fp_rate_differential_checkpoint"]
        bucket = per_noise.setdefault(noise, {
            "n": 0, "fail_detect": 0, "fail_fp": 0, "pass_both": 0,
            "detect": [], "fp": [],
            "scan_fp": [], "abs_scan_fp": []})
        bucket["n"] += 1
        bucket["detect"].append(round(detect, 3))
        bucket["fp"].append(round(fp, 3))
        bucket["scan_fp"].append(round(matched["metrics"]["fp_rate_differential_scan"], 3))
        bucket["abs_scan_fp"].append(round(matched["metrics"]["fp_rate_absolute_scan"], 3))
        fail_detect = detect < min_detect
        fail_fp = fp > max_fp
        bucket["fail_detect"] += fail_detect
        bucket["fail_fp"] += fail_fp
        bucket["pass_both"] += not (fail_detect or fail_fp)

    details = {str(k): v for k, v in sorted(per_noise.items())}

    refuted = []
    for noise, b in sorted(per_noise.items()):
        if b["fail_detect"] >= p["refute_at_seeds"]:
            refuted.append(f"noise={noise}: detection < {min_detect} at "
                           f"{b['fail_detect']}/{b['n']} seeds")
        if b["fail_fp"] >= p["refute_at_seeds"]:
            refuted.append(f"noise={noise}: null false positive > {max_fp} at "
                           f"{b['fail_fp']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_both"] >= p["support_at_seeds"] for b in per_noise.values()):
        return Verdict(SUPPORTED,
                       f"pre-committed checkpoint: detection >= {min_detect} and null false "
                       f"positive <= {max_fp} at >= {p['support_at_seeds']}/5 seeds in every "
                       "swept timing noise", details)

    weak = [f"noise={n}: {b['pass_both']}/{b['n']} seeds met both"
            for n, b in sorted(per_noise.items()) if b["pass_both"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   f"no refutation threshold reached, but support requires >= "
                   f"{p['support_at_seeds']}/5 seeds in every noise level — " + "; ".join(weak),
                   details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
