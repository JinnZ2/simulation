#!/usr/bin/env python3
"""snap_information — does a snap-through event report the load that caused it?

Retrofit of original_snap_information_sim.py to Sim Harness Standard v1.
Reads ONLY config.json + CLI overrides (§3).

Changes from the original, all recorded here rather than silently:
  - gamma is swept {0.02, 0.05, 0.10}; the original ran at 0.05 only.
  - 5 seeds; the original used unseeded np.random, so it was not reproducible.
  - a shuffle_load_labels null is measured alongside every MI estimate, and the
    verdict is decided on the excess over that null, never on raw MI. NULL.md
    explains why: a plug-in MI estimate on a 5x5 table is biased upward and is
    never zero even for independent variables.
  - trajectories are integrated as one vectorized ensemble instead of a Python
    loop per trajectory. Identical physics, same dt, ~50x faster, which is what
    makes 5 seeds x 3 gammas affordable.
  - Q1 and Q2 from the original are kept as descriptive secondaries; they carry
    no threshold and do not touch the verdict (see REFUTE.md).
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
# Physics — double well E(x) = a (x-c0)^2 (x-c1)^2, damped
# --------------------------------------------------------------------------

def make_potential(a: float, centers: list[float]):
    c0, c1 = centers

    def E(x):
        return a * (x - c0) ** 2 * (x - c1) ** 2

    def F(x, h: float = 1e-5):
        return -(E(x + h) - E(x - h)) / (2 * h)

    return E, F


def stiffness(c: float, a: float, centers: list[float]) -> float:
    c0, c1 = centers
    return 2 * a * ((c - c1) ** 2 + 4 * (c - c0) * (c - c1) + (c - c0) ** 2)


def simulate_ensemble(x0: np.ndarray, v0: np.ndarray, loads: np.ndarray,
                      F, dt: float, T: float, gamma: float) -> np.ndarray:
    """Integrate a whole ensemble at once. Returns (steps, n_traj)."""
    x = np.asarray(x0, dtype=float).copy()
    v = np.asarray(v0, dtype=float).copy()
    loads = np.asarray(loads, dtype=float)
    steps = int(T / dt)
    traj = np.empty((steps, x.size))
    for k in range(steps):
        v += dt * (F(x - loads) - gamma * v)
        x += dt * v
        traj[k] = x
    return traj


def ringdown_freq(traj: np.ndarray, dt: float, tail_frac: float) -> np.ndarray:
    """Dominant non-DC frequency of each column's tail."""
    seg = traj[int(traj.shape[0] * tail_frac):]
    seg = seg - seg.mean(axis=0, keepdims=True)
    sp = np.abs(np.fft.rfft(seg, axis=0))
    fr = np.fft.rfftfreq(seg.shape[0], dt)
    idx = np.argmax(sp[1:], axis=0) + 1
    return fr[idx]


# --------------------------------------------------------------------------
# Mutual information
# --------------------------------------------------------------------------

def mutual_info(x: np.ndarray, y: np.ndarray, bins: int) -> float:
    """Plug-in MI in bits over quantile bins. Biased upward — always compare
    against the permutation null rather than against zero."""
    def H(p):
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))

    edges_x = np.quantile(x, np.linspace(0, 1, bins + 1)[1:-1])
    edges_y = np.quantile(y, np.linspace(0, 1, bins + 1)[1:-1])
    cx = np.digitize(x, edges_x)
    cy = np.digitize(y, edges_y)
    n = len(x)
    pxy = np.zeros((bins, bins))
    np.add.at(pxy, (cx, cy), 1.0)
    pxy /= n
    return H(pxy.sum(axis=1)) + H(pxy.sum(axis=0)) - H(pxy.flatten())


def _observe(seed: int, gamma: float, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """The snapped ensemble: (loads, ringdown frequencies)."""
    p = config["physics"]
    _, F = make_potential(p["a"], p["well_centers"])
    rng = np.random.default_rng(seed)

    loads = np.repeat(np.linspace(0.0, p["load_max"], p["n_loads"]), p["reps_per_load"])
    # start compressed on the short-well side, release, snap toward the long well
    x0 = p["well_centers"][0] + loads
    v0 = p["v0_jitter"] * rng.standard_normal(loads.size)

    traj = simulate_ensemble(x0, v0, loads, F, p["dt"], p["T"], gamma)
    freqs = ringdown_freq(traj, p["dt"], p["tail_frac"])
    freqs = freqs + p["sensor_noise"] * rng.standard_normal(freqs.size)
    return loads, freqs


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------

def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    p = config["physics"]
    gamma = sweep["gamma"]
    loads, freqs = _observe(seed, gamma, config)
    mi = mutual_info(loads, freqs, p["mi_bins"])

    # --- descriptive secondaries (Q1, Q2) — no threshold, no verdict weight ---
    _, F = make_potential(p["a"], p["well_centers"])
    long_well = p["well_centers"][1]
    k_true = stiffness(long_well, p["a"], p["well_centers"])

    probe_loads = np.array([0.0, 0.1, 0.2])
    tr = simulate_ensemble(p["well_centers"][0] + probe_loads,
                           np.zeros(3), probe_loads, F, p["dt"], p["T"], gamma)
    f_probe = ringdown_freq(tr, p["dt"], p["tail_frac"])
    k_implied = float(np.mean((2 * np.pi * f_probe) ** 2))

    # Q2: direction memory — compression side vs tension side
    starts = np.array([p["well_centers"][0] + 0.3, p["well_centers"][1] - 0.3])
    tr2 = simulate_ensemble(starts, np.zeros(2), np.zeros(2), F, p["dt"], p["T"], gamma)
    tail = tr2[int(tr2.shape[0] * 0.7):]
    amp_compression = float(np.abs(tail[:, 0] - p["well_centers"][1]).max())
    amp_tension = float(np.abs(tail[:, 1] - p["well_centers"][0]).max())

    return {
        "mi_bits": mi,
        "ringdown_freq_mean": float(freqs.mean()),
        "ringdown_freq_std": float(freqs.std()),
        "k_true_landing": float(k_true),
        "k_implied_from_ringdown": k_implied,
        "amp_from_compression": amp_compression,
        "amp_from_tension": amp_tension,
        "amp_separation": abs(amp_compression - amp_tension),
    }


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """shuffle_load_labels — identical physics, association destroyed."""
    p = config["physics"]
    gamma = sweep["gamma"]
    loads, freqs = _observe(seed, gamma, config)
    rng = np.random.default_rng(seed + 10_000)

    draws = [mutual_info(rng.permutation(loads), freqs, p["mi_bins"])
             for _ in range(p["null_permutations"])]
    draws = np.asarray(draws)
    return {
        "mi_null_bits": float(draws.mean()),
        "mi_null_p95": float(np.quantile(draws, 0.95)),
        "mi_null_std": float(draws.std()),
    }


# --------------------------------------------------------------------------
# Grading — evaluates REFUTE.md against the data, nothing else
# --------------------------------------------------------------------------

def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]
    threshold = p["min_excess_bits"]

    per_gamma: dict[float, dict[str, Any]] = {}
    for row in obs:
        gamma = row["sweep"]["gamma"]
        matching_null = next(n for n in null_obs
                             if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        excess = row["metrics"]["mi_bits"] - matching_null["metrics"]["mi_null_bits"]
        bucket = per_gamma.setdefault(gamma, {"pass": 0, "fail": 0, "n": 0, "excess": []})
        bucket["n"] += 1
        bucket["excess"].append(round(excess, 4))
        if excess >= threshold:
            bucket["pass"] += 1
        else:
            bucket["fail"] += 1

    details = {str(k): v for k, v in sorted(per_gamma.items())}

    refuted = [f"gamma={g}: excess MI < {threshold} bits at {b['fail']}/{b['n']} seeds"
               for g, b in sorted(per_gamma.items())
               if b["fail"] >= p["refute_at_seeds"]]
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass"] >= p["support_at_seeds"] for b in per_gamma.values()):
        return Verdict(SUPPORTED,
                       f"excess MI >= {threshold} bits at >= {p['support_at_seeds']}/5 "
                       f"seeds in every swept gamma", details)

    weak = [f"gamma={g}: {b['pass']}/{b['n']} seeds cleared {threshold} bits"
            for g, b in sorted(per_gamma.items()) if b["pass"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   f"no refutation threshold reached, but support requires >= "
                   f"{p['support_at_seeds']}/5 seeds in every gamma — " + "; ".join(weak),
                   details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
