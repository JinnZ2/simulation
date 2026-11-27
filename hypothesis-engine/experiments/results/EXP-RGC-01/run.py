#!/usr/bin/env python3
"""EXP-RGC-01 — Instrument validation before any comparison.
Design: ../../representation-geometry-under-compression.md (EXP-RGC-01).

Metrics on (n x d) activation matrices (rows = probe inputs):
  cka_b   biased linear CKA (Kornblith-style HSIC estimator)
  cka_d   debiased linear CKA (unbiased HSIC estimator)
  cka_dw  debiased CKA after PCA-whitening each matrix (ridge 1e-3 * mean eigenvalue); only when n > d
  proc    orthogonal-Procrustes distance on centred, Frobenius-normalised matrices: 2 - 2 * ||X^T Y||_*
Checks:
  (i)  independent Gaussian random pairs: n = 2000 with d in {64, 128, 256, 512} (probe-set size and
       ResNet-18 channel widths), plus n in {50, 200, 1000} with d = 1000; 100 pairs each.
       Pass for a CKA metric: 95th percentile of |value| <= 0.05.  Procrustes has no 0 point; reported only.
  (ii) equal-Frobenius-norm perturbations of an anisotropic base (spectrum exp(-j / (d/8))):
       isotropic noise vs noise confined to the top-k PCs (k = max(1, d/16)), at norm ratios
       {0.1, 0.3, 1.0}; n = 2000; 50 replicates. Correct order: top-PC noise gives LOWER similarity
       (higher Procrustes distance). Pass: paired mean difference has the correct sign and its
       bootstrap 95% CI excludes 0, in every (d, ratio) cell.
  (iii) PILOT (deviation): sklearn MLPs on the 8x8 digits data instead of ResNet-18 / CIFAR-10 (no GPU,
       no torch here). 5 seeds, hidden (128, 64), ReLU; per-output-channel symmetric RTN of all weights at
       8 / 4 / 3 bits; probe = the 540-image test split; both hidden layers. Separation = compressed-vs-
       parent similarity compared with the seed-vs-seed distribution (10 pairs).

    python3 run.py           # numpy + scikit-learn; writes raw_output.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import env, save  # noqa: E402


def gram(X):
    X = X - X.mean(0)
    return X @ X.T


def cka_b(X, Y):
    K, L = gram(X), gram(Y)
    return float((K * L).sum() / np.sqrt((K * K).sum() * (L * L).sum()))


def hsic_u(K, L):
    n = K.shape[0]
    K = K.copy(); L = L.copy()
    np.fill_diagonal(K, 0); np.fill_diagonal(L, 0)
    one = np.ones(n)
    t = (K * L).sum() + (one @ K @ one) * (one @ L @ one) / ((n - 1) * (n - 2)) - 2 / (n - 2) * (one @ K @ (L @ one))
    return t / (n * (n - 3))


def cka_d(X, Y):
    K, L = X @ X.T, Y @ Y.T
    a, b = hsic_u(K, K), hsic_u(L, L)
    return float(hsic_u(K, L) / np.sqrt(a * b)) if a > 0 and b > 0 else float("nan")


def whiten(X):
    X = X - X.mean(0)
    C = X.T @ X / len(X)
    w, V = np.linalg.eigh(C)
    w = np.maximum(w, 0) + 1e-3 * w.mean()
    return X @ V / np.sqrt(w)


def cka_dw(X, Y):
    if X.shape[0] <= X.shape[1]:
        return float("nan")
    return cka_d(whiten(X), whiten(Y))


def proc(X, Y):
    X = X - X.mean(0); Y = Y - Y.mean(0)
    X /= np.linalg.norm(X); Y /= np.linalg.norm(Y)
    return float(2 - 2 * np.linalg.svd(X.T @ Y, compute_uv=False).sum())


METRICS = {"cka_b": cka_b, "cka_d": cka_d, "cka_dw": cka_dw, "proc": proc}


def check_i(rng):
    out = []
    for n, d in [(2000, 64), (2000, 128), (2000, 256), (2000, 512), (50, 1000), (200, 1000), (1000, 1000)]:
        vals = {m: [] for m in METRICS}
        for _ in range(100):
            A, B = rng.standard_normal((n, d)), rng.standard_normal((n, d))
            for m, f in METRICS.items():
                vals[m].append(f(A, B))
        row = {"n": n, "d": d}
        for m, v in vals.items():
            v = np.array(v)
            if np.all(np.isnan(v)):
                row[m] = None
                continue
            row[m] = {"mean": float(np.mean(v)), "sd": float(np.std(v)), "p95_abs": float(np.percentile(np.abs(v), 95)),
                      "pass_p95_abs_le_0.05": bool(np.percentile(np.abs(v), 95) <= 0.05) if m != "proc" else None}
        out.append(row)
    return out


def check_ii(rng):
    out = []
    n = 2000
    for d in (64, 128, 256, 512):
        k = max(1, d // 16)
        spec = np.exp(-np.arange(d) / (d / 8))
        for ratio in (0.1, 0.3, 1.0):
            diffs = {m: [] for m in METRICS}
            for _ in range(50):
                H = rng.standard_normal((n, d)) * np.sqrt(spec)
                R, _ = np.linalg.qr(rng.standard_normal((d, d)))
                H = H @ R                      # random basis, so PCs are not coordinate axes
                norm = ratio * np.linalg.norm(H - H.mean(0))
                Ei = rng.standard_normal((n, d)); Ei *= norm / np.linalg.norm(Ei)
                U = np.linalg.svd(H - H.mean(0), full_matrices=False)[2][:k]
                Et = rng.standard_normal((n, k)) @ U; Et *= norm / np.linalg.norm(Et)
                for m, f in METRICS.items():
                    si, st = f(H, H + Ei), f(H, H + Et)
                    # signed so that a positive value = top-PC noise judged MORE damaging (correct)
                    diffs[m].append((si - st) if m != "proc" else (st - si))
            row = {"d": d, "k": k, "ratio": ratio}
            for m, v in diffs.items():
                v = np.array(v)
                if np.all(np.isnan(v)):
                    row[m] = None
                    continue
                bs = [np.mean(rng.choice(v, len(v))) for _ in range(2000)]
                lo, hi = np.percentile(bs, [2.5, 97.5])
                row[m] = {"mean_diff": float(v.mean()), "ci95": [float(lo), float(hi)],
                          "frac_reps_correct": float((v > 0).mean()), "pass": bool(lo > 0)}
            out.append(row)
    return out


def rtn(W, bits):
    q = 2 ** (bits - 1) - 1
    s = np.abs(W).max(axis=0, keepdims=True) / q      # per output channel (columns in sklearn coefs_)
    s[s == 0] = 1
    return np.round(W / s).clip(-q, q) * s


def acts(coefs, intercepts, X):
    h, out = X, []
    for W, b in zip(coefs[:-1], intercepts[:-1]):
        h = np.maximum(h @ W + b, 0)
        out.append(h)
    return out


def check_iii():
    from sklearn.datasets import load_digits
    from sklearn.model_selection import train_test_split
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    X, y = load_digits(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=540, random_state=0, stratify=y)
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    models = []
    for seed in range(5):
        m = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=400, random_state=seed).fit(Xtr, ytr)
        models.append(m)
    res = {"test_acc_fp": [float(m.score(Xte, yte)) for m in models], "layers": {}}
    A = [acts(m.coefs_, m.intercepts_, Xte) for m in models]
    for li in range(2):
        L = {}
        for mname, f in METRICS.items():
            seed_pairs = [f(A[i][li], A[j][li]) for i in range(5) for j in range(i + 1, 5)]
            comp = {}
            for bits in (8, 4, 3):
                vals = []
                for s, m in enumerate(models):
                    Aq = acts([rtn(W, bits) for W in m.coefs_], m.intercepts_, Xte)
                    vals.append(f(A[s][li], Aq[li]))
                comp[str(bits)] = vals
            L[mname] = {"seed_vs_seed": seed_pairs, "fp_vs_quant": comp}
        res["layers"][str(li)] = L
    accq = {}
    for bits in (8, 4, 3):
        accs = []
        for m in models:
            cw = [rtn(W, bits) for W in m.coefs_]
            h = Xte
            for W, b in zip(cw[:-1], m.intercepts_[:-1]):
                h = np.maximum(h @ W + b, 0)
            logits = h @ cw[-1] + m.intercepts_[-1]
            accs.append(float((logits.argmax(1) == yte).mean()))
        accq[str(bits)] = accs
    res["test_acc_quant"] = accq
    return res


def main():
    t0 = time.time()
    rng = np.random.default_rng(20261127)
    e = env()
    try:
        import sklearn
        e["sklearn"] = sklearn.__version__
    except ImportError:
        pass
    out = {"env": e, "check_i": check_i(rng), "check_ii": check_ii(rng), "check_iii_PILOT": check_iii(),
           "runtime_s": None}
    out["runtime_s"] = round(time.time() - t0, 1)
    save(HERE / "raw_output.json", out)
    print("(i)")
    for r in out["check_i"]:
        print(r["n"], r["d"], {m: (round(v["mean"], 4), round(v["p95_abs"], 4), v["pass_p95_abs_le_0.05"]) if v else None
                               for m, v in r.items() if m in METRICS})
    print("(ii)")
    for r in out["check_ii"]:
        print(r["d"], r["ratio"], {m: (round(v["mean_diff"], 5), [round(x, 5) for x in v["ci95"]], v["frac_reps_correct"])
                                   if v else None for m, v in r.items() if m in METRICS})
    print("(iii) PILOT", json.dumps({"acc_fp": out["check_iii_PILOT"]["test_acc_fp"], "acc_q": out["check_iii_PILOT"]["test_acc_quant"]}))
    for li, L in out["check_iii_PILOT"]["layers"].items():
        for m, v in L.items():
            ss = np.array(v["seed_vs_seed"])
            print(f" layer {li} {m:6s} seed-vs-seed [{ss.min():.4f},{ss.max():.4f}]",
                  {b: [round(min(x), 4), round(max(x), 4)] for b, x in v["fp_vs_quant"].items()})
    print("runtime_s", out["runtime_s"])


if __name__ == "__main__":
    main()
