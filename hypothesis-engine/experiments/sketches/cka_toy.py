#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — instrument checks for EXP-RGC-01/02 (see ../representation-geometry-under-compression.md).

Three checks a geometry metric must pass BEFORE it is used to compare compression arms:
  1. invariance : linear CKA(H, H R) for orthogonal R should be 1 (rotation-based
                  compression is invisible to CKA by construction).
  2. null bias  : CKA between INDEPENDENT random matrices with n samples << d features.
                  Biased (standard) CKA is inflated; the debiased estimator (HSIC_1,
                  Song et al. 2012 / Kornblith-style unbiased HSIC) should sit near 0.
  3. anisotropy : synthetic 'quantization' noise of equal Frobenius norm, injected
                  (a) isotropically vs (b) along the top-k principal directions;
                  reports CKA and effective-rank shift for both. Equal-MSE perturbations
                  that a metric cannot tell apart make it useless for H3.

    python3 cka_toy.py [--seed 0]
"""
import argparse
import numpy as np


def center(K):
    n = K.shape[0]; H = np.eye(n) - 1 / n
    return H @ K @ H


def cka_biased(X, Y):
    Kx, Ky = center(X @ X.T), center(Y @ Y.T)
    return float((Kx * Ky).sum() / np.sqrt((Kx * Kx).sum() * (Ky * Ky).sum()))


def hsic_unbiased(K, L):
    n = K.shape[0]
    K = K.copy(); L = L.copy(); np.fill_diagonal(K, 0); np.fill_diagonal(L, 0)
    one = np.ones(n)
    t = (K * L).sum() + (one @ K @ one) * (one @ L @ one) / ((n - 1) * (n - 2)) - 2 / (n - 2) * (one @ K @ L @ one)
    return t / (n * (n - 3))


def cka_debiased(X, Y):
    K, L = X @ X.T, Y @ Y.T
    return float(hsic_unbiased(K, L) / np.sqrt(hsic_unbiased(K, K) * hsic_unbiased(L, L)))


def eff_rank(X):
    s = np.linalg.svd(X - X.mean(0), compute_uv=False) ** 2
    p = s / s.sum()
    return float(np.exp(-(p * np.log(p + 1e-12)).sum()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=0)
    rng = np.random.default_rng(ap.parse_args().seed)
    n, d = 500, 64
    spec = np.exp(-np.arange(d) / 8.0)                    # anisotropic 'activation' spectrum
    H = rng.standard_normal((n, d)) * np.sqrt(spec)
    R, _ = np.linalg.qr(rng.standard_normal((d, d)))
    print(f"1. CKA(H, H R), R orthogonal: biased {cka_biased(H, H @ R):.4f}")
    for nn, dd in ((50, 1000), (200, 1000), (1000, 1000)):
        A, B = rng.standard_normal((nn, dd)), rng.standard_normal((nn, dd))
        print(f"2. independent random, n={nn:4d} d={dd}: biased CKA {cka_biased(A, B):.4f}  debiased {cka_debiased(A, B):+.4f}")
    noise_norm = 0.3 * np.linalg.norm(H)
    E_iso = rng.standard_normal((n, d)); E_iso *= noise_norm / np.linalg.norm(E_iso)
    U = np.linalg.svd(H - H.mean(0), full_matrices=False)[2][:4]          # top-4 directions
    E_top = rng.standard_normal((n, 4)) @ U; E_top *= noise_norm / np.linalg.norm(E_top)
    print(f"3. equal-norm noise ({noise_norm:.1f}); base eff. rank {eff_rank(H):.2f}")
    for name, E in (("isotropic", E_iso), ("top-4 PCs", E_top)):
        print(f"   {name:10s}: CKA {cka_biased(H, H + E):.4f}  debiased {cka_debiased(H, H + E):.4f}  eff.rank {eff_rank(H + E):.2f}")
    print("SKETCH: instrument sanity checks on synthetic matrices, not a finding about any network.")
