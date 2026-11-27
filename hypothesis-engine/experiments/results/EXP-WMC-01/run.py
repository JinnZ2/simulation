#!/usr/bin/env python3
"""EXP-WMC-01 stage 1 (tabular pilot) — noisy-TV susceptibility across bonus families.
Design: ../../world-models-and-curiosity-driven-learning.md (EXP-WMC-01).

Environment and agent loop follow sketches/curiosity_toy.py (15x15 grid, 8 observation symbols,
epsilon-greedy over the 4 neighbours' stored bonus, eps=0.1, lr=0.2, T=3000). The sketch only has the
TV present. This script adds a distractor switch: with tv=False the designated TV cell emits its fixed
symbol like every other cell, and we still count the steps spent on that cell (time-on-distractor-cell).
Seeds are paired: seed s gives the same start, TV location and symbol map with and without the TV.

Bonus families (no bonus scale: action choice is argmax, so scale tuning is moot in this toy):
  none        : random walk
  count       : 1/sqrt(N(s')+1)                                    (as sketch)
  icm         : running forward-model prediction error at s'        (sketch 'pred_error')
  rnd         : tabular RND. Fixed random target f(o) in R^8; predictor g(o) trained by SGD (lr);
                bonus at a cell = squared error ||g(o)-f(o)||^2 of the last observation seen there
  disagree    : ensemble of K=5 tabular forward models, each updated on an observation with
                prob 0.5 (bootstrap mask); bonus = mean over symbols of the across-member variance
                of predicted probabilities at s' (x K, so that it is O(1))
  lp_w1       : learning progress, window 1 (as sketch): max(err_{t-1} - err_t, 0) + 1e-3/(N+1)
  lp_w10      : learning progress, window 10 visits: max(err_{t-10} - err_t, 0) + 1e-3/(N+1)
  disagree_avg: POST-HOC, EXPLORATORY (added after the first run; not pre-registered): as disagree, but
                each member is a running sample average (lr = 1/n_k) instead of an EMA with lr = 0.2,
                so members converge on a stochastic cell and disagreement can decay there
Outcomes: time-on-distractor-cell fraction (primary), coverage (fraction of cells visited).
Ratio per family = mean time-on-cell with TV / mean without TV; 95% CI by seed-level bootstrap (paired).
Interaction contrast: (TV - noTV time-on-cell) for icm minus the same for count, bootstrap CI.

    python3 run.py [--seeds 30] [--T 3000] [--procs 4]
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import env, save  # noqa: E402

MOVES = [(0, 1), (1, 0), (0, -1), (-1, 0)]
FAMILIES = ("none", "count", "icm", "rnd", "disagree", "lp_w1", "lp_w10", "disagree_avg")
K_ENS = 5


def run(agent, seed, tv_on, T=3000, size=15, n_sym=8, eps=0.1, lr=0.2):
    rng = np.random.default_rng(seed)
    tv = tuple(rng.integers(0, size, 2))
    pos = tuple(rng.integers(0, size, 2))
    sym = rng.integers(0, n_sym, (size, size))
    # separate streams so that the environment draws are identical across agents/conditions
    arng = np.random.default_rng([seed, 1])      # agent: eps, tie-breaks, ensemble masks
    orng = np.random.default_rng([seed, 2])      # TV noise
    target = np.random.default_rng([seed, 3]).normal(size=(n_sym, 8))
    N = np.zeros((size, size))
    err = np.ones((size, size))
    hist = {}                                      # per-cell error history (LP windows)
    model = np.full((size, size, n_sym), 1.0 / n_sym)
    ens = np.full((K_ENS, size, size, n_sym), 1.0 / n_sym)
    ens += 1e-2 * arng.random(ens.shape); ens /= ens.sum(-1, keepdims=True)
    dis = np.full((size, size), 1.0)
    ens_n = np.zeros((K_ENS, size, size))
    pred = np.zeros((n_sym, 8)); rnd_b = np.full((size, size), 1.0)
    on_tv = 0
    for _ in range(T):
        nbrs = [(min(max(pos[0] + dx, 0), size - 1), min(max(pos[1] + dy, 0), size - 1)) for dx, dy in MOVES]
        if agent == "none" or arng.random() < eps:
            nxt = nbrs[arng.integers(4)]
        else:
            if agent == "count":
                b = [1 / np.sqrt(N[c] + 1) for c in nbrs]
            elif agent == "icm":
                b = [err[c] for c in nbrs]
            elif agent == "rnd":
                b = [rnd_b[c] for c in nbrs]
            elif agent in ("disagree", "disagree_avg"):
                b = [dis[c] for c in nbrs]
            else:
                w = 1 if agent == "lp_w1" else 10
                b = []
                for c in nbrs:
                    h = hist.get(c)
                    old = h[-w] if h is not None and len(h) >= w else 1.0   # err w visits ago
                    b.append(max(old - err[c], 0) + 1e-3 / (N[c] + 1))
            b = np.array(b) + 1e-9 * arng.random(4)
            nxt = nbrs[int(np.argmax(b))]
        pos = nxt; N[pos] += 1; on_tv += pos == tv
        o = int(orng.integers(n_sym)) if (tv_on and pos == tv) else int(sym[pos])
        # forward model (ICM / LP)
        e = 1 - model[pos][o]
        h = hist.setdefault(pos, deque(maxlen=10)); h.append(err[pos])
        err[pos] = (1 - lr) * err[pos] + lr * e
        model[pos] *= (1 - lr); model[pos][o] += lr
        # ensemble (disagreement)
        mask = arng.random(K_ENS) < 0.5
        for k in np.flatnonzero(mask):
            lk = lr
            if agent == "disagree_avg":
                ens_n[k][pos] += 1; lk = 1.0 / (ens_n[k][pos] + 1)
            ens[k, pos] *= (1 - lk); ens[k, pos, o] += lk
        dis[pos] = K_ENS * ens[:, pos].var(axis=0).mean()
        # RND on the observation
        d = pred[o] - target[o]
        rnd_b[pos] = float(d @ d)
        pred[o] -= lr * d
    return float((N > 0).mean()), on_tv / T


def _job(j):
    f, s, flag, T = j
    return run(f, s, flag, T=T)


def boot_ratio(a, b, rng, B=10000):
    """a, b: paired per-seed arrays (TV, noTV). CI for mean(a)/mean(b) and mean(a-b)."""
    n = len(a); idx = rng.integers(0, n, (B, n))
    ma, mb = a[idx].mean(1), b[idx].mean(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = ma / mb
    return r, ma - mb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--T", type=int, default=3000)
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    t0 = time.time()
    seeds = list(range(20261127, 20261127 + a.seeds))
    raw = {f: {"tv": [], "notv": []} for f in FAMILIES}
    jobs = [(f, s, flag, a.T) for f in FAMILIES for s in seeds for flag in (True, False)]
    with ProcessPoolExecutor(a.procs) as ex:
        res = list(ex.map(_job, jobs, chunksize=8))
    for (f, s, flag, _), r in zip(jobs, res):
        raw[f]["tv" if flag else "notv"].append(r)
    rng = np.random.default_rng(7)
    summary = {}
    boots = {}
    for f in FAMILIES:
        tv = np.array([x[1] for x in raw[f]["tv"]]); no = np.array([x[1] for x in raw[f]["notv"]])
        ctv = np.array([x[0] for x in raw[f]["tv"]]); cno = np.array([x[0] for x in raw[f]["notv"]])
        r, d = boot_ratio(tv, no, rng)
        boots[f] = d
        rf = r[np.isfinite(r)]
        summary[f] = {
            "time_on_cell_tv_mean": tv.mean(), "time_on_cell_notv_mean": no.mean(),
            "ratio": tv.mean() / no.mean() if no.mean() > 0 else float("inf"),
            "ratio_ci95": [float(np.percentile(rf, 2.5)), float(np.percentile(rf, 97.5))] if rf.size else None,
            "ratio_boot_infinite_frac": float(1 - rf.size / r.size),
            "diff_mean": float((tv - no).mean()),
            "diff_ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "coverage_tv_mean": ctv.mean(), "coverage_notv_mean": cno.mean(),
            "coverage_tv_ci95": [float(np.percentile(ctv[rng.integers(0, len(ctv), (5000, len(ctv)))].mean(1), q)) for q in (2.5, 97.5)],
            "coverage_notv_ci95": [float(np.percentile(cno[rng.integers(0, len(cno), (5000, len(cno)))].mean(1), q)) for q in (2.5, 97.5)],
        }
    # interaction contrasts vs count (same bootstrap indices are not shared; independent bootstraps
    # of the paired differences give a conservative CI for the difference of differences)
    inter = {}
    for f in FAMILIES:
        if f == "count":
            continue
        dd = boots[f] - boots["count"]
        inter[f] = {"mean": summary[f]["diff_mean"] - summary["count"]["diff_mean"],
                    "ci95": [float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))]}
    out = {"experiment": "EXP-WMC-01", "stage": "1 (tabular pilot)", "env": env(),
           "config": {"seeds": seeds, "T": a.T, "size": 15, "n_sym": 8, "eps": 0.1, "lr": 0.2, "K_ens": K_ENS},
           "summary": summary, "interaction_vs_count": inter, "raw": raw,
           "runtime_s": round(time.time() - t0, 1)}
    save(HERE / "raw_output.json", out)
    for f in FAMILIES:
        s = summary[f]
        print(f"{f:9s} tv {s['time_on_cell_tv_mean']:.4f} notv {s['time_on_cell_notv_mean']:.4f} "
              f"ratio {s['ratio']:.2f} CI {s['ratio_ci95']} cov tv {s['coverage_tv_mean']:.3f} notv {s['coverage_notv_mean']:.3f}")
    for f, v in inter.items():
        print(f"interaction {f} - count: {v['mean']:.4f} CI {v['ci95']}")
    print(f"runtime {out['runtime_s']} s")


if __name__ == "__main__":
    main()
