#!/usr/bin/env python3
"""basin_convergence — is fractal_basin's alpha converged, or is it measuring the grid?

An audit of a SUPPORTED result. `fractal_basin` passed all three of its
pre-committed conditions and reproduced notes/17 §1 to three significant figures,
but measured alpha at a single grid resolution and integration time with no
convergence check — which its own FINDINGS.md flagged as the first thing a
follow-up should nail down.

Reads ONLY config.json + CLI overrides (§3).

The physics is imported from the parent rather than re-derived, so any difference
in alpha comes from the discretization and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "fractal_basin"))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402
from run import basin_grid, uncertainty_exponent, wada_fraction  # noqa: E402

CONFIG = HERE / "config.json"

# (gamma, N, T) -> (grid, xs). Grids are deterministic; only probing is stochastic,
# so each is computed once and shared across all five probe seeds.
_GRIDS: dict[tuple[float, int, float], tuple[np.ndarray, np.ndarray]] = {}


def grid_for(gamma: float, N: int, T: float, g: dict[str, Any]):
    key = (gamma, N, T)
    if key not in _GRIDS:
        _GRIDS[key] = basin_grid(
            centers=g["triple_centers"], N=N,
            xr=tuple(g["triple_xr"]), vr=tuple(g["triple_vr"]),
            dt=g["dt"], T=T, gamma=gamma)
    return _GRIDS[key]


def alpha_at(gamma: float, N: int, T: float, seed: int,
             g: dict[str, Any]) -> tuple[float, float]:
    grid, xs = grid_for(gamma, N, T, g)
    rng = np.random.default_rng(seed)
    alpha = uncertainty_exponent(grid, xs, g["n_probe"], rng)
    wada, _ = wada_fraction(grid, g["wada_radius"])
    return alpha, wada


def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    g = config["grid"]
    gamma = sweep["gamma"]

    a_base, w_base = alpha_at(gamma, g["N"], g["T"], seed, g)
    a_bigN, w_bigN = alpha_at(gamma, g["N_doubled"], g["T"], seed, g)
    a_bigT, w_bigT = alpha_at(gamma, g["N"], g["T_doubled"], seed, g)

    return {
        "alpha_base": a_base,
        "alpha_2N": a_bigN,
        "alpha_2T": a_bigT,
        "delta_N": abs(a_bigN - a_base),
        "delta_T": abs(a_bigT - a_base),
        # descriptive secondaries, ungraded
        "wada_base": w_base,
        "wada_2N": w_bigN,
        "wada_2T": w_bigT,
        "d_boundary_base": 2.0 - a_base,
    }


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """same_resolution_reseed — how much does alpha move from re-probing alone?

    Establishes the measurement's own noise floor, so the pre-committed 0.05 can
    be read against something rather than taken on faith.
    """
    g = config["grid"]
    gamma = sweep["gamma"]
    a_base, _ = alpha_at(gamma, g["N"], g["T"], seed, g)
    a_reseed, _ = alpha_at(gamma, g["N"], g["T"], seed + 10_000, g)
    return {
        "alpha_reseed": a_reseed,
        "delta_reseed": abs(a_reseed - a_base),
    }


def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]
    max_delta = p["max_delta"]

    per_gamma: dict[float, dict[str, Any]] = {}
    for row in obs:
        gamma = row["sweep"]["gamma"]
        matched = next(n for n in null_obs
                       if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        m, nm = row["metrics"], matched["metrics"]
        bucket = per_gamma.setdefault(gamma, {
            "n": 0, "fail_N": 0, "fail_T": 0, "pass_both": 0,
            "delta_N": [], "delta_T": [], "delta_reseed": []})
        bucket["n"] += 1
        bucket["delta_N"].append(round(m["delta_N"], 4))
        bucket["delta_T"].append(round(m["delta_T"], 4))
        bucket["delta_reseed"].append(round(nm["delta_reseed"], 4))
        fail_N = m["delta_N"] >= max_delta
        fail_T = m["delta_T"] >= max_delta
        bucket["fail_N"] += fail_N
        bucket["fail_T"] += fail_T
        bucket["pass_both"] += not (fail_N or fail_T)

    details = {str(k): v for k, v in sorted(per_gamma.items())}

    refuted = []
    for gamma, b in sorted(per_gamma.items()):
        if b["fail_N"] >= p["refute_at_seeds"]:
            refuted.append(f"gamma={gamma}: |alpha(2N) - alpha(N)| >= {max_delta} at "
                           f"{b['fail_N']}/{b['n']} seeds")
        if b["fail_T"] >= p["refute_at_seeds"]:
            refuted.append(f"gamma={gamma}: |alpha(2T) - alpha(T)| >= {max_delta} at "
                           f"{b['fail_T']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_both"] >= p["support_at_seeds"] for b in per_gamma.values()):
        return Verdict(SUPPORTED,
                       f"doubling grid resolution or integration time moves alpha by less "
                       f"than {max_delta} at >= {p['support_at_seeds']}/5 seeds in every "
                       "swept gamma", details)

    weak = [f"gamma={g}: {b['pass_both']}/{b['n']} seeds converged on both axes"
            for g, b in sorted(per_gamma.items()) if b["pass_both"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   "convergence is damping-dependent — " + "; ".join(weak), details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
