#!/usr/bin/env python3
"""EXP-AAQ-02 (PILOT, synthetic layers only) — is AWQ's gain carried by the activation statistics?
Design: ../../activation-aware-quantization.md (EXP-AAQ-02). The design's pilot stage; the real-layer
stage (one 1B model, all linear layers, 5 calibration draws) is NOT run (needs a GPU-class setup).

Synthetic layer y = x W, d_in = d_out = 256, n = 2048 rows split 50/50 into calibration / test.
x has n_out "outlier" input channels with gain g (main setting: 8 channels, g = 20, as in
sketches/awq_toy.py). W ~ N(0, 1/d_in). Quantizer: symmetric per-output-channel RTN at b bits.
Arms (each alpha in {0, 0.1, ..., 1} grid-searched on the calibration split; scored on test):
  rtn         plain RTN
  awq         s_j = mean|x_j|^alpha (true per-channel activation magnitudes)
  awq_perm    the same vector randomly permuted across channels (same spread, wrong channels)
  wnorm       s_j = mean_k |W_jk|^alpha (weight-norm statistics, no activations)
  had_rtn     random Hadamard rotation (H diag(+-1) / sqrt(d)) applied to x and W, then RTN
  had_awq     rotation, then AWQ on the rotated activations' magnitudes
Metric: relative output MSE ||xW - x Q(W)||^2 / ||xW||^2 on the test split.
"Layers": 10 seeds per setting (main: b = 4, 8 outliers, g = 20). Sensitivity settings (reported,
not used for the verdict): b = 3; no outliers (g = 1).

    python3 run.py           # numpy + scipy; writes raw_output.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import hadamard
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import env, save  # noqa: E402

ALPHAS = np.linspace(0, 1, 11)


def q_rtn(W, bits):
    qmax = 2 ** (bits - 1) - 1
    s = np.abs(W).max(axis=0, keepdims=True) / qmax + 1e-12
    return np.clip(np.round(W / s), -qmax - 1, qmax) * s


def rel(X, W, Wq):
    Y = X @ W
    return float(((Y - X @ Wq) ** 2).sum() / (Y ** 2).sum())


def scaled(W, s, bits):
    return q_rtn(W * s[:, None], bits) / s[:, None]


def best_scale(Xc, W, stat, bits):
    errs = [(rel(Xc, W, scaled(W, stat ** a, bits)), a) for a in ALPHAS]
    e, a = min(errs)
    return stat ** a, float(a)


def layer(seed, bits, n_out, gain, d=256, n=2048):
    rng = np.random.default_rng(seed)
    g = np.ones(d)
    g[rng.choice(d, n_out, replace=False)] = gain
    X = rng.standard_normal((n, d)) * g
    W = rng.standard_normal((d, d)) / np.sqrt(d)
    Xc, Xt = X[: n // 2], X[n // 2:]
    a_mag = np.abs(Xc).mean(0)
    w_mag = np.abs(W).mean(1)
    out, alphas = {}, {}
    out["rtn"] = rel(Xt, W, q_rtn(W, bits))
    s, alphas["awq"] = best_scale(Xc, W, a_mag, bits)
    out["awq"] = rel(Xt, W, scaled(W, s, bits))
    perm = rng.permutation(a_mag)
    s, alphas["awq_perm"] = best_scale(Xc, W, perm, bits)
    out["awq_perm"] = rel(Xt, W, scaled(W, s, bits))
    s, alphas["wnorm"] = best_scale(Xc, W, w_mag, bits)
    out["wnorm"] = rel(Xt, W, scaled(W, s, bits))
    Q = hadamard(d) * rng.choice([-1.0, 1.0], d)[None, :] / np.sqrt(d)   # orthogonal
    Wr = Q.T @ W                                    # x W = (x Q)(Q^T W)
    Xcr, Xtr = Xc @ Q, Xt @ Q
    out["had_rtn"] = rel(Xtr, Wr, q_rtn(Wr, bits))
    s, alphas["had_awq"] = best_scale(Xcr, Wr, np.abs(Xcr).mean(0), bits)
    out["had_awq"] = rel(Xtr, Wr, scaled(Wr, s, bits))
    return out, alphas


SETTINGS = {"main_b4_out8_g20": (4, 8, 20.0), "sens_b3_out8_g20": (3, 8, 20.0), "sens_b4_no_outliers": (4, 8, 1.0)}
ARMS = ("rtn", "awq", "awq_perm", "wnorm", "had_rtn", "had_awq")


def main():
    t0 = time.time()
    res = {"env": env(), "settings": {}}
    for name, (bits, n_out, gain) in SETTINGS.items():
        rows = [layer(1000 + s, bits, n_out, gain) for s in range(10)]
        errs = {a: np.array([r[0][a] for r in rows]) for a in ARMS}
        summ = {"bits": bits, "n_outliers": n_out, "gain": gain, "seeds": list(range(1000, 1010)),
                "per_layer": {a: errs[a].tolist() for a in ARMS},
                "alphas": [r[1] for r in rows], "median": {a: float(np.median(errs[a])) for a in ARMS}}
        ratios = {}
        for a in ARMS:
            if a == "awq":
                continue
            r = errs[a] / errs["awq"]
            ratios[a] = {"median_ratio_vs_awq": float(np.median(r)), "min": float(r.min()), "max": float(r.max()),
                         "frac_layers_awq_better": float((r > 1).mean()),
                         "wilcoxon_p_two_sided": float(wilcoxon(errs[a], errs["awq"]).pvalue)}
        summ["ratios_vs_awq"] = ratios
        hr = errs["had_rtn"]
        summ["had_rtn_between_awq_and_rtn_frac"] = float(((hr > errs["awq"]) & (hr < errs["rtn"])).mean())
        res["settings"][name] = summ
    res["runtime_s"] = round(time.time() - t0, 1)
    save(HERE / "raw_output.json", res)
    for name, s in res["settings"].items():
        print("==", name, "median rel MSE", {a: f"{v:.3e}" for a, v in s["median"].items()})
        for a, r in s["ratios_vs_awq"].items():
            print(f"   {a:9s} ratio vs awq median {r['median_ratio_vs_awq']:.3f} [{r['min']:.3f},{r['max']:.3f}] "
                  f"awq better in {r['frac_layers_awq_better']:.0%}  wilcoxon p={r['wilcoxon_p_two_sided']:.4f}")
        print("   had_rtn strictly between awq and rtn in", s["had_rtn_between_awq_and_rtn_frac"])
    print("runtime_s", res["runtime_s"])


if __name__ == "__main__":
    main()
