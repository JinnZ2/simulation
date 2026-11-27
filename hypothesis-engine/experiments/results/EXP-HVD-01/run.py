#!/usr/bin/env python3
"""EXP-HVD-01 — Operating characteristics of the engine's hidden-variable rule.
Design: ../../hidden-variable-detection-causal-discovery-from-residuals.md (EXP-HVD-01).

SCM (per replicate, length n):
    Z_t AR(1) with coefficient phi, stationary start, unit variance
    X_t = a Z_t + e_x
    Y_t = b X_t + g(Z_t) + e_y,    e ~ N(0, 1)
  variant 'linear'   : g(Z) = c Z
  variant 'tanh'     : g(Z) = c tanh(Z)                   (nonlinear link)
  variant 'signflip' : g(Z) = +c Z for t < n/2, -c Z after (latent acts with opposite signs)
Analyst: OLS of Y on X (no intercept, as in the sketch), residual r.
Candidates: proxy = Z + proxy_noise * N(0,1);  null = independent AR(1), same phi.
Detectors (thresholds as in the engine's stage_hidden):
  engine_abs  : mean|r| >= 0.1 and |pearson(|r|, cand)| > 0.5
  signed      : |pearson(r, cand)| > 0.5
  signed_perm : circular-shift permutation p < 0.05 for |pearson(r, cand)|, using EVERY shift
                in [n//10, n - n//10] (exhaustive; the sketch sampled 199 shifts at random)
Grid: n {20,50,200,1000} x c {0.25,0.5,1,2} x phi {0,0.5,0.9,0.99} x proxy_noise {0.1,0.5,1};
1000 replicates per cell; fixed a=0.8, b=1.0. Seeds: one integer per cell, derived from its index.

    python3 run.py [--reps 1000]       # numpy only; writes raw_output.json
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import env, save  # noqa: E402

NS = (20, 50, 200, 1000)
CS = (0.25, 0.5, 1.0, 2.0)
PHIS = (0.0, 0.5, 0.9, 0.99)
NOISES = (0.1, 0.5, 1.0)
VARIANTS = ("linear", "tanh", "signflip")
A, B = 0.8, 1.0


def ar1(rng, reps, n, phi):
    z = np.empty((reps, n))
    z[:, 0] = rng.standard_normal(reps)
    e = rng.standard_normal((reps, n)) * np.sqrt(1 - phi ** 2)
    for t in range(1, n):
        z[:, t] = phi * z[:, t - 1] + e[:, t]
    return z


def zscore(x):
    x = x - x.mean(axis=1, keepdims=True)
    s = np.sqrt((x * x).sum(axis=1, keepdims=True))
    s[s == 0] = 1.0
    return x / s


def circ_corr(u, v):
    """Pearson correlation of u with every circular shift of v, rows independently."""
    U, V = zscore(u), zscore(v)
    return np.fft.irfft(np.conj(np.fft.rfft(V, axis=1)) * np.fft.rfft(U, axis=1), n=u.shape[1], axis=1)


def cell(rng, n, c, phi, noise, variant, reps):
    Z = ar1(rng, reps, n, phi)
    X = A * Z + rng.standard_normal((reps, n))
    if variant == "linear":
        g = c * Z
    elif variant == "tanh":
        g = c * np.tanh(Z)
    else:
        sign = np.where(np.arange(n) < n // 2, 1.0, -1.0)
        g = c * Z * sign
    Y = B * X + g + rng.standard_normal((reps, n))
    beta = (X * Y).sum(1) / (X * X).sum(1)
    r = Y - beta[:, None] * X
    out = {}
    shifts = np.arange(n // 10, n - n // 10)
    for name, s in (("proxy", Z + noise * rng.standard_normal((reps, n))), ("null", ar1(rng, reps, n, phi))):
        abs_stat = np.abs(np.sum(zscore(np.abs(r)) * zscore(s), axis=1))
        gate = np.abs(r).mean(1) >= 0.1
        cc = circ_corr(r, s)            # cc[:, 0] is the observed correlation
        obs = np.abs(cc[:, 0])
        null = np.abs(cc[:, shifts])
        p = (1 + (null >= obs[:, None] - 1e-12).sum(1)) / (1 + len(shifts))
        out[name] = {"engine_abs": gate & (abs_stat > 0.5), "signed": obs > 0.5, "signed_perm": p < 0.05,
                     "s_engine": np.where(gate, abs_stat, 0.0), "s_signed": obs, "s_perm": 1 - p}
    res = {}
    for det in ("engine_abs", "signed", "signed_perm"):
        res[det] = {"power": float(out["proxy"][det].mean()), "fpr": float(out["null"][det].mean())}
    for det, key in (("engine_abs", "s_engine"), ("signed", "s_signed"), ("signed_perm", "s_perm")):
        a, b = out["proxy"][key], out["null"][key]
        # AUC = P(stat_proxy > stat_null) + 0.5 P(tie)
        allv = np.concatenate([a, b])
        ranks = allv.argsort().argsort().astype(float)
        # average ranks for ties
        _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
        sums = np.bincount(inv, weights=ranks)
        ranks = (sums / cnt)[inv]
        res[det]["auc"] = float((ranks[: len(a)].sum() - len(a) * (len(a) - 1) / 2) / (len(a) * len(b)))
    res["min_attainable_p"] = 1 / (1 + len(shifts))
    return res


def mc_ci(p, n):
    se = np.sqrt(max(p * (1 - p), 1e-12) / n)
    return [round(max(0.0, p - 1.96 * se), 4), round(min(1.0, p + 1.96 * se), 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1000)
    args = ap.parse_args()
    t0 = time.time()
    rows = []
    grid = list(itertools.product(VARIANTS, NS, CS, PHIS, NOISES))
    for i, (variant, n, c, phi, noise) in enumerate(grid):
        rng = np.random.default_rng(10_000 + i)
        r = cell(rng, n, c, phi, noise, variant, args.reps)
        rows.append({"variant": variant, "n": n, "c": c, "phi": phi, "proxy_noise": noise, "seed": 10_000 + i, **r})
    # summaries
    summ = {}
    for variant in VARIANTS:
        R = [r for r in rows if r["variant"] == variant]
        small = [r for r in R if r["n"] <= 200]
        s = {"cells": len(R)}
        for det in ("engine_abs", "signed", "signed_perm"):
            s[det] = {
                "frac_cells_power_lt_0.5_n_le_200": float(np.mean([r[det]["power"] < 0.5 for r in small])),
                "frac_cells_power_ge_0.8_and_fpr_le_0.05": float(np.mean([(r[det]["power"] >= 0.8) and (r[det]["fpr"] <= 0.05) for r in R])),
                "median_power": float(np.median([r[det]["power"] for r in R])),
                "median_auc": float(np.median([r[det]["auc"] for r in R])),
                "fpr_range": [float(min(r[det]["fpr"] for r in R)), float(max(r[det]["fpr"] for r in R))],
            }
        # signed_perm FPR by phi, excluding n=20 (min attainable p > 0.05) and pooled over the rest
        s["signed_perm_fpr_by_phi_n_ge_50"] = {
            str(phi): float(np.mean([r["signed_perm"]["fpr"] for r in R if r["phi"] == phi and r["n"] >= 50]))
            for phi in PHIS}
        s["signed_perm_cells_fpr_in_[0.03,0.07]_n_ge_50"] = float(np.mean(
            [0.03 <= r["signed_perm"]["fpr"] <= 0.07 for r in R if r["n"] >= 50]))
        s["signed_perm_fpr_max_by_phi_n_ge_50"] = {
            str(phi): float(max(r["signed_perm"]["fpr"] for r in R if r["phi"] == phi and r["n"] >= 50)) for phi in PHIS}
        s["engine_abs_power_by_n"] = {str(n): float(np.mean([r["engine_abs"]["power"] for r in R if r["n"] == n])) for n in NS}
        s["signed_perm_power_by_n"] = {str(n): float(np.mean([r["signed_perm"]["power"] for r in R if r["n"] == n])) for n in NS}
        s["engine_abs_fpr_by_phi"] = {str(p): float(np.mean([r["engine_abs"]["fpr"] for r in R if r["phi"] == p])) for p in PHIS}
        s["signed_fpr_by_phi"] = {str(p): float(np.mean([r["signed"]["fpr"] for r in R if r["phi"] == p])) for p in PHIS}
        summ[variant] = s
    out = {"env": env(), "reps_per_cell": args.reps, "a": A, "b": B, "summary": summ, "cells": rows,
           "mc_se_at_rate_0.05": float(np.sqrt(0.05 * 0.95 / args.reps)), "runtime_s": round(time.time() - t0, 1)}
    save(HERE / "raw_output.json", out)
    import json
    print(json.dumps(summ, indent=1))
    print("runtime_s", out["runtime_s"])


if __name__ == "__main__":
    main()
