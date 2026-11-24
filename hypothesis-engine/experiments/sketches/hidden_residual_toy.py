#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — pilot harness for EXP-HVD-01/02 (see ../hidden-variable-detection-causal-discovery-from-residuals.md).

Linear-Gaussian SCM with a latent confounder Z (AR(1) in time, coefficient phi):
    X_t = a Z_t + e_x,   Y_t = b X_t + c Z_t + e_y
An analyst regresses Y on X (OLS) and inspects residuals r_t. Detectors:
  engine_abs : the hypothesis engine's rule shape — mean|r| >= 0.1 AND |pearson(|r|, cand)| > 0.5
  signed     : |pearson(r, cand)| > 0.5 (same threshold, signed residual)
  signed_perm: signed correlation with a circular-shift permutation p-value < 0.05
                (preserves the candidate's autocorrelation; the naive test does not)
Candidates: 'proxy' = Z + noise (true hidden-variable proxy) and 'null' = an independent
AR(1) series with the SAME phi (pure spurious-correlation control).
Reports trigger rates over many replicates: power on 'proxy', false-positive rate on 'null'.

    python3 hidden_residual_toy.py [--reps 300] [--n 200] [--c 1.0] [--phi 0.95]
"""
import argparse
import numpy as np


def ar1(rng, n, phi):
    z = np.zeros(n); e = rng.standard_normal(n) * np.sqrt(1 - phi ** 2)
    for t in range(1, n):
        z[t] = phi * z[t - 1] + e[t]
    return z


def corr(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a @ a) * (b @ b))
    return 0.0 if d == 0 else float(a @ b / d)


def perm_p(r, cand, rng, k=199):
    obs = abs(corr(r, cand)); n = len(r)
    null = [abs(corr(r, np.roll(cand, rng.integers(n // 10, n - n // 10)))) for _ in range(k)]
    return (1 + sum(v >= obs for v in null)) / (k + 1)


def one(rng, n, a, b, c, phi, proxy_noise):
    Z = ar1(rng, n, phi)
    X = a * Z + rng.standard_normal(n)
    Y = b * X + c * Z + rng.standard_normal(n)
    beta = (X @ Y) / (X @ X)
    r = Y - beta * X
    cands = {"proxy": Z + proxy_noise * rng.standard_normal(n), "null": ar1(rng, n, phi)}
    out = {}
    for name, s in cands.items():
        out[(name, "engine_abs")] = np.abs(r).mean() >= 0.1 and abs(corr(np.abs(r), s)) > 0.5
        out[(name, "signed")] = abs(corr(r, s)) > 0.5
        out[(name, "signed_perm")] = perm_p(r, s, rng) < 0.05
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--a", type=float, default=0.8)
    ap.add_argument("--b", type=float, default=1.0)
    ap.add_argument("--c", type=float, default=1.0)
    ap.add_argument("--phi", type=float, default=0.95)
    ap.add_argument("--proxy-noise", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    tally = {}
    for _ in range(a.reps):
        for k, v in one(rng, a.n, a.a, a.b, a.c, a.phi, a.proxy_noise).items():
            tally[k] = tally.get(k, 0) + bool(v)
    for det in ("engine_abs", "signed", "signed_perm"):
        print(f"{det:12s} trigger rate: proxy {tally[('proxy', det)] / a.reps:.3f}   "
              f"null(AR1 phi={a.phi}) {tally[('null', det)] / a.reps:.3f}")
    print("SKETCH output on a synthetic SCM. Rates depend on every parameter above; sweep them.")
