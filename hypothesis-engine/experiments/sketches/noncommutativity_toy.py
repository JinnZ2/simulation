#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — pilot harness for EXP-CCO-01 (see ../compression-composition-and-ordering.md).

Trains a small numpy MLP on a synthetic 10-class task, then applies
  P = global magnitude pruning to sparsity s,   Q = symmetric per-channel RTN at b bits
in both orders, with an optional short fine-tune between and after steps (masked, then
re-quantized), and reports the paired difference in test accuracy and in output KL to
the dense model. Seeds vary the data, init and the fine-tune minibatch order.

Without fine-tuning, P∘Q vs Q∘P differ only through scale recomputation and magnitude
ties; that difference is near-structural and is the NEGATIVE CONTROL. The scientific
question (EXP-CCO-01) is the fine-tuned case.

    python3 noncommutativity_toy.py [--seeds 5] [--sparsity 0.7] [--bits 3] [--ft-steps 200]
"""
import argparse
import numpy as np


def make_data(rng, n=6000, d=32, k=10):
    centers = rng.standard_normal((k, d)) * 1.5
    y = rng.integers(0, k, n)
    X = centers[y] + rng.standard_normal((n, d))
    return X[: n * 2 // 3], y[: n * 2 // 3], X[n * 2 // 3:], y[n * 2 // 3:]


def init(rng, d=32, h=128, k=10):
    return [rng.standard_normal((d, h)) / np.sqrt(d), np.zeros(h),
            rng.standard_normal((h, k)) / np.sqrt(h), np.zeros(k)]


def forward(p, X):
    H = np.maximum(X @ p[0] + p[1], 0)
    Z = H @ p[2] + p[3]
    Z -= Z.max(1, keepdims=True)
    P = np.exp(Z); P /= P.sum(1, keepdims=True)
    return H, P


def train(p, X, y, steps, rng, lr=0.1, masks=None, bs=128):
    for _ in range(steps):
        idx = rng.integers(0, len(X), bs)
        x, t = X[idx], y[idx]
        H, P = forward(p, x)
        G = P.copy(); G[np.arange(bs), t] -= 1; G /= bs
        gW2, gb2 = H.T @ G, G.sum(0)
        GH = (G @ p[2].T) * (H > 0)
        gW1, gb1 = x.T @ GH, GH.sum(0)
        for i, g in zip(range(4), (gW1, gb1, gW2, gb2)):
            p[i] -= lr * g
        if masks is not None:
            p[0] *= masks[0]; p[2] *= masks[1]
    return p


def prune(p, s):
    w = np.concatenate([np.abs(p[0]).ravel(), np.abs(p[2]).ravel()])
    thr = np.quantile(w, s)
    m = [(np.abs(p[0]) > thr).astype(float), (np.abs(p[2]) > thr).astype(float)]
    return [p[0] * m[0], p[1], p[2] * m[1], p[3]], m


def quant(p, b):
    qmax = 2 ** (b - 1) - 1
    out = list(p)
    for i in (0, 2):
        sc = np.abs(p[i]).max(0, keepdims=True) / qmax + 1e-12
        out[i] = np.clip(np.round(p[i] / sc), -qmax - 1, qmax) * sc
    return out


def evaluate(p, ref_P, X, y):
    _, P = forward(p, X)
    acc = float((P.argmax(1) == y).mean())
    kl = float((ref_P * (np.log(ref_P + 1e-12) - np.log(P + 1e-12))).sum(1).mean())
    return acc, kl


def pipeline(base, order, s, b, ft, X, y, seed):
    rng = np.random.default_rng(10_000 + seed)   # same fine-tune stream for both orders
    p = [w.copy() for w in base]; masks = None
    for op in order:
        if op == "P":
            p, masks = prune(p, s)
        else:
            p = quant(p, b)
        if ft:
            p = train(p, X, y, ft, rng, lr=0.02, masks=masks)
    if ft and "Q" in order:
        p = quant(p, b)       # deployed artifact must be quantized
        if masks is not None:
            p[0] *= masks[0]; p[2] *= masks[1]
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--sparsity", type=float, default=0.7)
    ap.add_argument("--bits", type=int, default=3)
    ap.add_argument("--ft-steps", type=int, default=200)
    a = ap.parse_args()
    for ft in (0, a.ft_steps):
        dacc, dkl = [], []
        for seed in range(a.seeds):
            rng = np.random.default_rng(seed)
            Xtr, ytr, Xte, yte = make_data(rng)
            base = train(init(rng), Xtr, ytr, 1500, rng)
            _, ref = forward(base, Xte)
            pq = evaluate(pipeline(base, "PQ", a.sparsity, a.bits, ft, Xtr, ytr, seed), ref, Xte, yte)
            qp = evaluate(pipeline(base, "QP", a.sparsity, a.bits, ft, Xtr, ytr, seed), ref, Xte, yte)
            dacc.append(pq[0] - qp[0]); dkl.append(pq[1] - qp[1])
        dacc, dkl = np.array(dacc), np.array(dkl)
        print(f"fine-tune steps={ft:4d}: acc(P->Q) - acc(Q->P) mean {dacc.mean():+.4f} sd {dacc.std(ddof=1):.4f};"
              f"  KL(P->Q) - KL(Q->P) mean {dkl.mean():+.4f}  (n={a.seeds} paired seeds)")
    print("SKETCH output on a synthetic toy. Not evidence about real models or the Progressive Intensity Hypothesis.")
