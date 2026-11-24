#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — pilot harness for EXP-AAQ-01 (see ../activation-aware-quantization.md).

Synthetic single linear layer y = x W. Inputs have a few high-magnitude "outlier"
channels. Compares, at the SAME weight bit-width and group size:
  rtn       : round-to-nearest, per-output-channel symmetric
  wscale    : weight-only heuristic — per-input-channel scale from column |W| (no activations)
  awq_like  : per-input-channel scale s_j = mean|x_j|^alpha, alpha grid-searched on a
              CALIBRATION split, error reported on a disjoint TEST split
  rand_scale: control — scales drawn at random with the same spread as awq_like
Metric: relative output MSE ||xW - x Q(W)||^2 / ||xW||^2 on the test split.
Assumption made explicit: scales are folded into the previous op, so they cost no
extra bits (true for AWQ when a preceding LayerNorm/linear exists; not universal).

    python3 awq_toy.py [--seeds 10] [--bits 4] [--outliers 8]
"""
import argparse
import numpy as np


def quant_rtn(W, bits):
    qmax = 2 ** (bits - 1) - 1
    scale = np.abs(W).max(axis=0, keepdims=True) / qmax + 1e-12   # per output column
    return np.clip(np.round(W / scale), -qmax - 1, qmax) * scale


def rel_err(X, W, Wq):
    Y = X @ W
    return float(((Y - X @ Wq) ** 2).sum() / (Y ** 2).sum())


def scaled_quant(W, s, bits):
    return quant_rtn(W * s[:, None], bits) / s[:, None]


def run(seed, d_in=256, d_out=256, n=2048, bits=4, n_out=8, out_gain=20.0):
    rng = np.random.default_rng(seed)
    gains = np.ones(d_in)
    gains[rng.choice(d_in, n_out, replace=False)] = out_gain
    X = rng.standard_normal((n, d_in)) * gains
    W = rng.standard_normal((d_in, d_out)) / np.sqrt(d_in)
    Xc, Xt = X[: n // 2], X[n // 2:]
    a_mag = np.abs(Xc).mean(axis=0)
    res = {"rtn": rel_err(Xt, W, quant_rtn(W, bits))}
    w_mag = np.abs(W).mean(axis=1)
    best = min((rel_err(Xc, W, scaled_quant(W, w_mag ** a, bits)), a) for a in np.linspace(0, 1, 11))
    res["wscale"] = rel_err(Xt, W, scaled_quant(W, w_mag ** best[1], bits))
    best = min((rel_err(Xc, W, scaled_quant(W, a_mag ** a, bits)), a) for a in np.linspace(0, 1, 11))
    s = a_mag ** best[1]
    res["awq_like"] = rel_err(Xt, W, scaled_quant(W, s, bits))
    res["rand_scale"] = rel_err(Xt, W, scaled_quant(W, rng.permutation(s), bits))
    res["alpha"] = best[1]
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--bits", type=int, default=4)
    ap.add_argument("--outliers", type=int, default=8)
    a = ap.parse_args()
    rows = [run(s, bits=a.bits, n_out=a.outliers) for s in range(a.seeds)]
    for k in ("rtn", "wscale", "awq_like", "rand_scale"):
        v = np.array([r[k] for r in rows])
        print(f"{k:10s} rel. output MSE: median {np.median(v):.3e}  [min {v.min():.3e}, max {v.max():.3e}]")
    d = np.array([r["rtn"] - r["awq_like"] for r in rows])
    print(f"paired rtn - awq_like > 0 in {int((d > 0).sum())}/{len(d)} seeds (sign test is the pre-registered stat)")
    print("SKETCH output on synthetic data. Says nothing about real LLM layers.")
