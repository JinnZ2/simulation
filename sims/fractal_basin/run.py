#!/usr/bin/env python3
"""fractal_basin — is a three-well basin boundary fractal, across damping?

Retrofit of original_fractal_basin_sim.py to Sim Harness Standard v1.
Reads ONLY config.json + CLI overrides (§3).

Changes from the original, all recorded here rather than silently:
  - gamma is swept {0.1, 0.25, 0.5}; the original measured alpha at 0.25 only.
    HARNESS.md §5 item 4 flags exactly this.
  - 5 probe seeds; the original used a single rng.
  - a shuffle_labels null is measured alongside every real grid.
  - the basin grid is computed once per (gamma, potential) and shared across
    probe seeds. The grid is deterministic — only the probing is stochastic —
    so recomputing it per seed would burn 5x the time for identical arrays.
  - np.save of .npy figures dropped; those paths pointed outside the repo.
    Basin grids are summarized in metrics.json instead.
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
# Physics — unchanged from the original
# --------------------------------------------------------------------------

def basin_grid(centers: list[float], N: int, xr: tuple[float, float],
               vr: tuple[float, float], dt: float, T: float,
               gamma: float) -> tuple[np.ndarray, np.ndarray]:
    """Integrate every initial condition at once; label by nearest well."""
    def F(x: np.ndarray) -> np.ndarray:
        h = 1e-5
        E = lambda z: np.prod([(z - c) ** 2 for c in centers], axis=0)
        return -(E(x + h) - E(x - h)) / (2 * h)

    xs = np.linspace(*xr, N)
    vs = np.linspace(*vr, N)
    X, V = np.meshgrid(xs, vs)
    for _ in range(int(T / dt)):
        V += dt * (F(X) - gamma * V)
        X += dt * V
    G = np.argmin(np.abs(X[..., None] - np.array(centers)), axis=-1)
    return G.astype(int), xs


def uncertainty_exponent(G: np.ndarray, xs: np.ndarray, n_probe: int,
                         rng: np.random.Generator) -> float:
    """Slope of log f(eps) against log eps. 1 => smooth boundary."""
    N = G.shape[0]
    dx = xs[1] - xs[0]
    epss = dx * 2.0 ** np.arange(0, 8)
    fs = []
    for eps in epss:
        dj = max(1, int(round(eps / dx)))
        if N - 2 - dj <= 2:
            fs.append(0.0)
            continue
        i = rng.integers(2, N - 2, n_probe)
        j = rng.integers(2, N - 2 - dj, n_probe)
        fs.append(float(np.mean(G[i, j] != G[i, j + dj])))
    epss = np.asarray(epss)
    fs = np.asarray(fs)
    mask = fs > 0
    if mask.sum() < 2:
        return float("nan")
    return float(np.polyfit(np.log(epss[mask]), np.log(fs[mask]), 1)[0])


def wada_fraction(G: np.ndarray, rad: int) -> tuple[float, int]:
    """Share of boundary cells whose neighbourhood touches all three basins."""
    N = G.shape[0]
    total = wada = 0
    for i in range(rad, N - rad):
        row = G[i - rad:i + rad + 1]
        for j in range(rad, N - rad):
            u = np.unique(row[:, j - rad:j + rad + 1])
            if len(u) > 1:
                total += 1
                wada += (len(u) == 3)
    return wada / max(total, 1), total


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------

_GRID_CACHE: dict[tuple[float, str], tuple[np.ndarray, np.ndarray]] = {}


def _grid_for(gamma: float, which: str, config: dict[str, Any]):
    """Deterministic per (gamma, potential) — computed once, reused per seed."""
    key = (gamma, which)
    if key not in _GRID_CACHE:
        g = config["grid"]
        _GRID_CACHE[key] = basin_grid(
            centers=g[f"{which}_centers"], N=g["N"],
            xr=tuple(g[f"{which}_xr"]), vr=tuple(g[f"{which}_vr"]),
            dt=g["dt"], T=g["T"], gamma=gamma)
    return _GRID_CACHE[key]


def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    g = config["grid"]
    gamma = sweep["gamma"]
    rng = np.random.default_rng(seed)

    G2, xs2 = _grid_for(gamma, "double", config)
    G3, xs3 = _grid_for(gamma, "triple", config)

    alpha_double = uncertainty_exponent(G2, xs2, g["n_probe"], rng)
    alpha_triple = uncertainty_exponent(G3, xs3, g["n_probe"], rng)
    wada, boundary_cells = wada_fraction(G3, g["wada_radius"])

    return {
        "alpha_double": alpha_double,
        "alpha_triple": alpha_triple,
        "d_boundary_double": 2.0 - alpha_double,
        "d_boundary_triple": 2.0 - alpha_triple,
        "alpha_gap": alpha_double - alpha_triple,
        "wada_fraction": wada,
        "boundary_cells": float(boundary_cells),
        "basin_share_triple_0": float(np.mean(G3 == 0)),
        "basin_share_triple_1": float(np.mean(G3 == 1)),
        "basin_share_triple_2": float(np.mean(G3 == 2)),
    }


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """shuffle_labels — same statistic on a spatially scrambled grid."""
    g = config["grid"]
    gamma = sweep["gamma"]
    rng = np.random.default_rng(seed + 10_000)

    G3, xs3 = _grid_for(gamma, "triple", config)
    flat = G3.flatten().copy()
    rng.shuffle(flat)
    shuffled = flat.reshape(G3.shape)

    alpha_null = uncertainty_exponent(shuffled, xs3, g["n_probe"], rng)
    wada_null, _ = wada_fraction(shuffled, g["wada_radius"])
    return {"alpha_null": alpha_null, "wada_fraction_null": wada_null}


# --------------------------------------------------------------------------
# Grading — evaluates REFUTE.md against the data, nothing else
# --------------------------------------------------------------------------

def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]
    ceiling = p["smooth_alpha_ceiling"]
    min_gap = p["min_double_minus_triple"]
    min_above_null = p["min_triple_above_null"]

    per_gamma: dict[float, dict[str, Any]] = {}
    for row in obs:
        gamma = row["sweep"]["gamma"]
        matching_null = next(n for n in null_obs
                             if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        m, nm = row["metrics"], matching_null["metrics"]
        bucket = per_gamma.setdefault(gamma, {
            "fail_smooth": 0, "fail_gap": 0, "fail_null": 0, "pass_all": 0, "n": 0})
        bucket["n"] += 1
        fail_smooth = not (m["alpha_triple"] < ceiling)
        fail_gap = not (m["alpha_gap"] >= min_gap)
        fail_null = not (m["alpha_triple"] - nm["alpha_null"] >= min_above_null)
        bucket["fail_smooth"] += fail_smooth
        bucket["fail_gap"] += fail_gap
        bucket["fail_null"] += fail_null
        bucket["pass_all"] += not (fail_smooth or fail_gap or fail_null)

    details = {str(k): v for k, v in sorted(per_gamma.items())}

    refuted = []
    for gamma, b in sorted(per_gamma.items()):
        if b["fail_smooth"] >= p["refute_at_seeds"]:
            refuted.append(f"gamma={gamma}: alpha_triple >= {ceiling} at "
                           f"{b['fail_smooth']}/{b['n']} seeds")
        if b["fail_gap"] >= p["refute_at_seeds"]:
            refuted.append(f"gamma={gamma}: alpha_double - alpha_triple < {min_gap} at "
                           f"{b['fail_gap']}/{b['n']} seeds")
        if b["fail_null"] >= p["refute_at_seeds"]:
            refuted.append(f"gamma={gamma}: alpha_triple - alpha_null < {min_above_null} at "
                           f"{b['fail_null']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_all"] >= p["support_at_seeds"] for b in per_gamma.values()):
        return Verdict(SUPPORTED,
                       f"all three conditions met at >= {p['support_at_seeds']}/5 seeds "
                       f"in every swept gamma", details)

    weak = [f"gamma={g}: {b['pass_all']}/{b['n']} seeds met all conditions"
            for g, b in sorted(per_gamma.items())
            if b["pass_all"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   "no refutation threshold reached, but support requires >= "
                   f"{p['support_at_seeds']}/5 seeds in every gamma — " + "; ".join(weak),
                   details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
