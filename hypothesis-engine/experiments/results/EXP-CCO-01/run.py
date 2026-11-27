#!/usr/bin/env python3
"""EXP-CCO-01 (PILOT, toy MLP) — is the prune/quantize order effect larger than seed noise and a 0.5 pp margin?
Design: ../../compression-composition-and-ordering.md (EXP-CCO-01). This runs the design's laptop pilot
(numpy MLP from sketches/noncommutativity_toy.py), NOT ResNet-18/CIFAR-10 or a small LM.

Model/data: 2-layer ReLU MLP (32-128-10) on a synthetic 10-class Gaussian-mixture task (4000 train /
2000 test), trained 1500 SGD steps. Per seed: data, init, training and the fine-tune minibatch stream;
the stream is shared by both orders, so comparisons are paired.
Operators: P = global magnitude pruning to sparsity s in {0.5, 0.7, 0.9};
           Q = symmetric per-output-channel RTN at b in {8, 4, 3} bits.
           (The design's GPTQ-style Q arm is not run; see RESULTS.md.)
Recovery budget (factor): none | interleaved (k = 100 masked SGD steps after each operator) |
           end (2k = 200 steps after both). Quantization is re-applied at the end of any fine-tuned
           pipeline (the deployed artefact is quantized) and the mask re-applied.
Ablations (no fine-tune and interleaved): scale recomputation after pruning off (P->Q uses scales
           from the dense weights); exact tie-breaking in Q->P (random tie-break so exactly s are pruned).
Outcome: test accuracy; paired difference acc(P->Q) - acc(Q->P) in percentage points.
Analysis: per cell, TOST at +-0.5 pp (90% CI) for equivalence and a one-sided minimal-effect t test for
|delta| > 0.5 pp; Holm over the 9 cells within each fine-tune arm. Margin sensitivity 0.25 and 1.0 pp.
Seeds: 5 (as designed); a 20-seed rerun is reported as a secondary, not pre-registered, analysis.

    python3 run.py           # numpy + scipy; writes raw_output.json
"""
from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "sketches"))
from common import env, save  # noqa: E402
import noncommutativity_toy as toy  # noqa: E402  (make_data, init, forward, train)

S = (0.5, 0.7, 0.9)
B = (8, 4, 3)
K = 100


def prune(p, s, exact_ties=False, rng=None):
    w = np.concatenate([np.abs(p[0]).ravel(), np.abs(p[2]).ravel()])
    if not exact_ties:
        thr = np.quantile(w, s)
        m = [(np.abs(p[0]) > thr).astype(float), (np.abs(p[2]) > thr).astype(float)]
    else:
        n_prune = int(round(s * w.size))
        order = np.lexsort((rng.random(w.size), w))      # by magnitude, random among ties
        keep = np.ones(w.size); keep[order[:n_prune]] = 0
        n0 = p[0].size
        m = [keep[:n0].reshape(p[0].shape), keep[n0:].reshape(p[2].shape)]
    return [p[0] * m[0], p[1], p[2] * m[1], p[3]], m


def quant(p, b, scales=None):
    qmax = 2 ** (b - 1) - 1
    out = list(p)
    for j, i in enumerate((0, 2)):
        sc = (np.abs(p[i]).max(0, keepdims=True) / qmax + 1e-12) if scales is None else scales[j]
        out[i] = np.clip(np.round(p[i] / sc), -qmax - 1, qmax) * sc
    return out


def dense_scales(p, b):
    qmax = 2 ** (b - 1) - 1
    return [np.abs(p[i]).max(0, keepdims=True) / qmax + 1e-12 for i in (0, 2)]


def pipeline(base, order, s, b, ft, X, y, seed, no_rescale=False, exact_ties=False):
    rng = np.random.default_rng(10_000 + seed)          # shared fine-tune stream across orders
    tie_rng = np.random.default_rng(20_000 + seed)
    p = [w.copy() for w in base]
    masks = None
    fixed_scales = dense_scales(base, b) if no_rescale else None
    for op in order:
        if op == "P":
            p, masks = prune(p, s, exact_ties=exact_ties and order == "QP", rng=tie_rng)
        else:
            p = quant(p, b, scales=fixed_scales)
        if ft == "interleaved":
            p = toy.train(p, X, y, K, rng, lr=0.02, masks=masks)
    if ft == "end":
        p = toy.train(p, X, y, 2 * K, rng, lr=0.02, masks=masks)
    if ft != "none":
        p = quant(p, b, scales=fixed_scales)
        p[0] *= masks[0]; p[2] *= masks[1]
    return p


def acc(p, X, y):
    return float((toy.forward(p, X)[1].argmax(1) == y).mean())


def run_seeds(seeds):
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        Xtr, ytr, Xte, yte = toy.make_data(rng)
        base = toy.train(toy.init(rng), Xtr, ytr, 1500, rng)
        rec = {"seed": seed, "dense_acc": acc(base, Xte, yte), "cells": {}}
        for s, b in itertools.product(S, B):
            for ft in ("none", "interleaved", "end"):
                variants = {"main": {}}
                if ft in ("none", "interleaved"):
                    variants["no_rescale"] = {"no_rescale": True}
                    variants["exact_ties"] = {"exact_ties": True}
                for vname, kw in variants.items():
                    a_pq = acc(pipeline(base, "PQ", s, b, ft, Xtr, ytr, seed, **kw), Xte, yte)
                    a_qp = acc(pipeline(base, "QP", s, b, ft, Xtr, ytr, seed, **kw), Xte, yte)
                    rec["cells"][f"s={s}|b={b}|ft={ft}|{vname}"] = [a_pq, a_qp]
        rows.append(rec)
    return rows


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, running)
    return adj


def analyse(rows, margin):
    out = {}
    keys = rows[0]["cells"].keys()
    for key in keys:
        d = np.array([100 * (r["cells"][key][0] - r["cells"][key][1]) for r in rows])
        n = len(d)
        m, sd = d.mean(), d.std(ddof=1)
        se = sd / np.sqrt(n) if sd > 0 else 1e-12
        t90 = stats.t.ppf(0.95, n - 1)
        p_lo = 1 - stats.t.cdf((m + margin) / se, n - 1)      # H0: delta <= -margin
        p_hi = stats.t.cdf((m - margin) / se, n - 1)          # H0: delta >= +margin
        p_tost = max(p_lo, p_hi)
        # minimal-effect: H0 |delta| <= margin, in the direction of the observed mean
        p_me = (1 - stats.t.cdf((abs(m) - margin) / se, n - 1))
        out[key] = {"mean_pp": float(m), "sd_pp": float(sd), "ci90": [float(m - t90 * se), float(m + t90 * se)],
                    "p_tost": float(p_tost), "p_min_effect": float(p_me), "diffs_pp": d.tolist()}
    # Holm within each (ft, variant) family over the 9 cells
    fams = {}
    for key in keys:
        _, _, ft, v = key.split("|")
        fams.setdefault((ft, v), []).append(key)
    for fam, ks in fams.items():
        for test in ("p_tost", "p_min_effect"):
            adj = holm(np.array([out[k][test] for k in ks]))
            for k, a in zip(ks, adj):
                out[k][test + "_holm"] = float(a)
                out[k]["equivalent" if test == "p_tost" else "exceeds_margin"] = bool(a < 0.05)
    return out


def main():
    t0 = time.time()
    rows5 = run_seeds(range(5))
    rows20 = run_seeds(range(20))
    dense_sd = float(np.std([r["dense_acc"] for r in rows20], ddof=1) * 100)
    res = {"env": env(), "k_steps": K, "dense_acc_5": [r["dense_acc"] for r in rows5],
           "dense_acc_sd_pp_20_seeds": dense_sd,
           "primary_5_seeds": {str(mg): analyse(rows5, mg) for mg in (0.5, 0.25, 1.0)},
           "secondary_20_seeds": {str(mg): analyse(rows20, mg) for mg in (0.5, 0.25, 1.0)},
           "raw_5": rows5, "raw_20": rows20}
    res["runtime_s"] = round(time.time() - t0, 1)
    save(HERE / "raw_output.json", res)
    print("dense acc (5 seeds)", res["dense_acc_5"], "dense SD over 20 seeds (pp)", round(dense_sd, 3))
    for label, A in (("PRIMARY 5 seeds, margin 0.5", res["primary_5_seeds"]["0.5"]),
                     ("SECONDARY 20 seeds, margin 0.5", res["secondary_20_seeds"]["0.5"])):
        print("==", label)
        for k, v in A.items():
            if k.endswith("|main") or "interleaved" in k:
                print(f"  {k:38s} mean {v['mean_pp']:+.3f} pp  90%CI [{v['ci90'][0]:+.3f},{v['ci90'][1]:+.3f}]  "
                      f"equiv={v['equivalent']} exceeds={v['exceeds_margin']}")
    print("runtime_s", res["runtime_s"])


if __name__ == "__main__":
    main()
