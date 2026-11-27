#!/usr/bin/env python3
"""EXP-HVD-02 (PILOT scale) — residual screening vs LPCMCI on synthetic series with known latents.
Design: ../../hidden-variable-detection-causal-discovery-from-residuals.md (EXP-HVD-02).

Generator (re-implemented linear SVAR, lag-1 links only, unit Gaussian noise, 200-step burn-in):
  N observed + L latent variables; every variable has auto-coefficient `auto`;
  N random observed->observed lag-1 links with coefficient +-0.3;
  each latent drives 2 distinct observed variables at lag 1 with coefficient +-0.6;
  resampled until the spectral radius is < 0.97. Latents are then dropped.
  Truth: observed pairs (i, j) sharing a latent parent.
Methods:
  LPCMCI (tigramite, ParCorr analytic, tau_max = 2, pc_alpha in {0.01, 0.05});
    a pair is flagged if any lag 0..2 edge between i and j is '<->'.
  residual screen: OLS of each observed variable on lags 1..2 of all observed variables; for each
    pair, |Pearson| of the contemporaneous residuals with an exhaustive circular-shift permutation
    p-value. At matched FPR the screen is thresholded on |r| pooled within the cell (see evaluate).
  (the design's FCI-style baseline is not run: tigramite 5.2 has no SVAR-FCI; see RESULTS.md)
Grid: N {5, 10} x L {1, 2} x T {200, 500, 1000} x auto {0.5, 0.9}; DATASETS per cell (pilot: 20,
design: 100). Seeds: dataset seed = 1000 * cell_index + dataset_index.

    python3 run.py [--datasets 20] [--procs 4]     # needs numpy, scipy, tigramite
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import env, save  # noqa: E402

GRID = list(itertools.product((5, 10), (1, 2), (200, 500, 1000), (0.5, 0.9)))
TAU = 2


def gen(rng, N, L, T, auto):
    M = N + L
    while True:
        A = np.eye(M) * auto
        for _ in range(N):
            i, j = rng.choice(N, 2, replace=False)
            A[j, i] = rng.choice([-1, 1]) * 0.3
        pairs = set()
        for l in range(L):
            ch = rng.choice(N, 2, replace=False)
            for c in ch:
                A[c, N + l] = rng.choice([-1, 1]) * 0.6
            pairs.add(tuple(sorted(int(c) for c in ch)))
        if np.max(np.abs(np.linalg.eigvals(A))) < 0.97:
            break
    X = np.zeros((T + 200, M))
    e = rng.standard_normal((T + 200, M))
    for t in range(1, T + 200):
        X[t] = A @ X[t - 1] + e[t]
    return X[200:, :N], pairs


def residual_screen(X):
    T, N = X.shape
    Z = np.hstack([X[TAU - k: T - k] for k in range(1, TAU + 1)])
    Z = np.hstack([Z, np.ones((len(Z), 1))])
    Y = X[TAU:]
    R = Y - Z @ np.linalg.lstsq(Z, Y, rcond=None)[0]
    n = len(R)
    Rz = (R - R.mean(0)) / (R.std(0) * np.sqrt(n))
    F = np.fft.rfft(Rz, axis=0)
    shifts = np.arange(n // 10, n - n // 10)
    p = {}
    for i in range(N):
        for j in range(i + 1, N):
            cc = np.fft.irfft(np.conj(F[:, j]) * F[:, i], n=n)
            obs = abs(cc[0])
            p[(i, j)] = (float((1 + (np.abs(cc[shifts]) >= obs - 1e-12).sum()) / (1 + len(shifts))), float(obs))
    return p


def lpcmci_flags(X, alpha):
    from tigramite import data_processing as pp
    from tigramite.independence_tests.parcorr import ParCorr
    from tigramite.lpcmci import LPCMCI
    N = X.shape[1]
    lp = LPCMCI(dataframe=pp.DataFrame(X), cond_ind_test=ParCorr(significance="analytic"), verbosity=0)
    g = lp.run_lpcmci(tau_max=TAU, pc_alpha=alpha)["graph"]
    return {(i, j): bool(any(g[i, j, tau] == "<->" or g[j, i, tau] == "<->" for tau in range(TAU + 1)))
            for i in range(N) for j in range(i + 1, N)}


def job(args):
    ci, di = args
    N, L, T, auto = GRID[ci]
    seed = 1000 * ci + di
    rng = np.random.default_rng(seed)
    X, pairs = gen(rng, N, L, T, auto)
    t0 = time.time()
    p = residual_screen(X)
    t_res = time.time() - t0
    out = {"cell": ci, "dataset": di, "seed": seed, "truth": sorted(pairs), "res_p": {f"{i},{j}": v[0] for (i, j), v in p.items()},
           "res_r": {f"{i},{j}": v[1] for (i, j), v in p.items()},
           "t_res": t_res}
    for a in (0.01, 0.05):
        t0 = time.time()
        f = lpcmci_flags(X, a)
        out[f"lp_{a}"] = sorted(f"{i},{j}" for (i, j), v in f.items() if v)
        out[f"t_lp_{a}"] = time.time() - t0
    return out


def evaluate(recs, alpha, rng=None):
    """Recall/FPR of LPCMCI at alpha, and residual-screen recall at <= LPCMCI's FPR (pooled)."""
    pos_lp = neg_lp = tp = fp = 0
    pos_p, neg_p, pos_r, neg_r = [], [], [], []
    for r in recs:
        truth = {f"{i},{j}" for i, j in r["truth"]}
        flags = set(r[f"lp_{alpha}"])
        for k, p in r["res_p"].items():
            if k in truth:
                pos_lp += 1; tp += k in flags; pos_p.append(p); pos_r.append(r["res_r"][k])
            else:
                neg_lp += 1; fp += k in flags; neg_p.append(p); neg_r.append(r["res_r"][k])
    rec_lp, fpr_lp = tp / pos_lp, fp / neg_lp
    pos_p, neg_p = np.array(pos_p), np.array(neg_p)
    pos_r, neg_r = np.array(pos_r), np.array(neg_r)
    # rank pairs by |residual correlation| (pooled within the cell; all datasets share T, so the
    # permutation p is a near-monotone function of it but has ties at its floor). Flag |r| > th with
    # th = the (k+1)-th largest null-pair |r|, k = floor(FPR_lp * n_neg): at most k negatives flagged.
    sn = np.sort(neg_r)[::-1]
    k = int(np.floor(fpr_lp * len(sn) + 1e-9))
    best = float(sn[k]) if k < len(sn) else -1.0
    rec_res = float((pos_r > best).mean())
    return {"lp_recall": rec_lp, "lp_fpr": fpr_lp, "res_recall_at_lp_fpr": rec_res,
            "res_threshold": best, "res_fpr_at_threshold": float((neg_r > best).mean()),
            "res_recall_at_0.05": float((pos_p < 0.05).mean()), "res_fpr_at_0.05": float((neg_p < 0.05).mean()),
            "n_pos": int(pos_lp), "n_neg": int(neg_lp)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", type=int, default=20)
    ap.add_argument("--procs", type=int, default=4)
    args = ap.parse_args()
    t0 = time.time()
    jobs = [(ci, di) for ci in range(len(GRID)) for di in range(args.datasets)]
    with Pool(args.procs) as pool:
        recs = pool.map(job, jobs, chunksize=1)
    rng = np.random.default_rng(7)
    cells = []
    for ci, (N, L, T, auto) in enumerate(GRID):
        R = [r for r in recs if r["cell"] == ci]
        row = {"N": N, "L": L, "T": T, "auto": auto, "datasets": len(R)}
        for a in (0.01, 0.05):
            ev = evaluate(R, a)
            boots = []
            for _ in range(1000):
                Rb = [R[i] for i in rng.integers(len(R), size=len(R))]
                e = evaluate(Rb, a)
                boots.append(e["lp_recall"] - e["res_recall_at_lp_fpr"])
            ev["diff_lp_minus_res"] = ev["lp_recall"] - ev["res_recall_at_lp_fpr"]
            ev["diff_boot95"] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
            row[str(a)] = ev
        row["mean_t_lp_0.05_s"] = float(np.mean([r["t_lp_0.05"] for r in R]))
        cells.append(row)
    out = {"env": env(), "datasets_per_cell": args.datasets, "tau_max": TAU, "cells": cells, "records": recs,
           "runtime_s": round(time.time() - t0, 1)}
    save(HERE / "raw_output.json", out)
    for c in cells:
        print(c["N"], c["L"], c["T"], c["auto"], *[
            f"a={a}: lp rec {c[a]['lp_recall']:.2f} fpr {c[a]['lp_fpr']:.3f} | res rec@fpr {c[a]['res_recall_at_lp_fpr']:.2f} "
            f"diff {c[a]['diff_lp_minus_res']:+.2f} [{c[a]['diff_boot95'][0]:+.2f},{c[a]['diff_boot95'][1]:+.2f}]"
            for a in ("0.01", "0.05")])
    print("runtime_s", out["runtime_s"])


if __name__ == "__main__":
    main()
