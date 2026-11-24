#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — measurement-harness skeleton for EXP-SSP-01 and EXP-DCM-01
(see ../structured-sparsity-and-hardware-matched-pruning.md, ../deployment-aware-compression-metrics.md).

On whatever CPU runs it, times y = x W for one weight matrix stored as:
  dense            : float32 dense
  masked_dense_50  : dense with 50% zeros (same kernel, same FLOPs) — the 'zero count is
                     not speed' control
  nm_2of4_dense    : 2:4 pattern zeros, still dense kernel (no sparse-tensor-core path on CPU)
  csr_50 / csr_90  : scipy.sparse CSR at 50% / 90% unstructured sparsity (if scipy present)
  struct_50        : 50% of output channels removed (a smaller dense matrix)
Protocol: warm-up, R timed repeats, report median and p95 latency and bytes-in-memory
(including CSR index arrays). Then marks the bytes-vs-median-latency Pareto set.
Numbers are machine-, BLAS-, thread- and thermal-state-specific; record them with
`--env` output and never compare across machines.

    python3 latency_harness.py [--d 2048] [--batch 8] [--reps 50] [--env]
"""
import argparse
import os
import platform
import time
import numpy as np

try:
    import scipy.sparse as sp
except Exception:  # scipy optional
    sp = None


def timeit(fn, reps, warm=5):
    for _ in range(warm):
        fn()
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter(); fn(); ts.append(time.perf_counter() - t0)
    ts = np.array(ts) * 1e3
    return float(np.median(ts)), float(np.percentile(ts, 95))


def pareto(rows):
    keep = []
    for r in rows:
        dominated = any(o is not r and o["bytes"] <= r["bytes"] and o["p50"] <= r["p50"]
                        and (o["bytes"] < r["bytes"] or o["p50"] < r["p50"]) for o in rows)
        keep.append(not dominated)
    return keep


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=2048)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--env", action="store_true")
    a = ap.parse_args()
    if a.env:
        print(platform.platform(), platform.processor(), "cpus", os.cpu_count(), "numpy", np.__version__,
              "OMP_NUM_THREADS", os.environ.get("OMP_NUM_THREADS"))
    rng = np.random.default_rng(0)
    W = rng.standard_normal((a.d, a.d)).astype(np.float32)
    x = rng.standard_normal((a.batch, a.d)).astype(np.float32)
    arms = {"dense": W}
    m = W.copy(); m[np.abs(m) < np.median(np.abs(m))] = 0; arms["masked_dense_50"] = m
    nm = W.reshape(a.d, -1, 4).copy()
    order = np.argsort(np.abs(nm), axis=2)
    np.put_along_axis(nm, order[:, :, :2], 0, axis=2); arms["nm_2of4_dense"] = nm.reshape(a.d, a.d)
    arms["struct_50"] = np.ascontiguousarray(W[:, : a.d // 2])
    rows = []
    for name, M in arms.items():
        p50, p95 = timeit(lambda: x @ M, a.reps)
        rows.append({"arm": name, "bytes": M.nbytes, "p50": p50, "p95": p95})
    if sp is not None:
        for s in (0.5, 0.9):
            M = W.copy(); M[np.abs(M) < np.quantile(np.abs(M), s)] = 0
            C = sp.csr_matrix(M)       # x @ C computed as (C.T @ x.T).T
            CT = C.T.tocsr()
            p50, p95 = timeit(lambda: (CT @ x.T).T, a.reps)
            rows.append({"arm": f"csr_{int(s*100)}", "bytes": C.data.nbytes + C.indices.nbytes + C.indptr.nbytes,
                         "p50": p50, "p95": p95})
    for r, k in zip(rows, pareto(rows)):
        print(f"{r['arm']:16s} bytes {r['bytes']/1e6:8.2f} MB   p50 {r['p50']:8.3f} ms   p95 {r['p95']:8.3f} ms  {'PARETO' if k else ''}")
    print("SKETCH: one matmul on this machine. Not an end-to-end model latency; not portable across hardware.")
