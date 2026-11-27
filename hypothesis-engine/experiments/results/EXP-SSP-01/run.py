#!/usr/bin/env python3
"""EXP-SSP-01, CPU arm, PILOT: kernel-level factorial (sparsity format x runtime support x shape).
Design: ../../structured-sparsity-and-hardware-matched-pruning.md (EXP-SSP-01).
Extends sketches/latency_harness.py (same arms + 70% CSR and 32x32 block-sparse BSR at 50/75%).

Match labels and the grid are read from match_labels.json, written before any timing.
One process = one session:   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 run.py --session 1
After all sessions:          python3 run.py --analyze
Per cell and arm: 10 warm-ups, 100 timed repeats (perf_counter around one GEMM y = x W; CPU is
synchronous so no device sync is needed); p50, p95, bytes resident (values + indices + indptr).
Arm order is rotated per cell so that slow drift does not always hit the same arm.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import env, save  # noqa: E402

CFG = json.loads((HERE / "match_labels.json").read_text())


def timeit(fn, reps, warm):
    for _ in range(warm):
        fn()
    ts = np.empty(reps)
    for i in range(reps):
        t0 = time.perf_counter(); fn(); ts[i] = time.perf_counter() - t0
    ts *= 1e3
    return float(np.median(ts)), float(np.percentile(ts, 95))


def arms_for(W, d):
    a = {"dense": ("dense", W)}
    m = W.copy(); m[np.abs(m) < np.median(np.abs(m))] = 0; a["masked_dense_50"] = ("dense", m)
    nm = W.reshape(d, -1, 4).copy()
    order = np.argsort(np.abs(nm), axis=2)
    np.put_along_axis(nm, order[:, :, :2], 0, axis=2); a["nm_2of4_dense"] = ("dense", nm.reshape(d, d))
    a["struct_50"] = ("dense", np.ascontiguousarray(W[:, : d // 2]))
    for s in (0.5, 0.7, 0.9):
        M = W.copy(); M[np.abs(M) < np.quantile(np.abs(M), s)] = 0
        a[f"csr_{int(s * 100)}"] = ("sparse", sp.csr_matrix(M.T))        # y^T = W^T x^T
    for s in (0.5, 0.75):                                                 # 32x32 block magnitude pruning
        B = W.reshape(d // 32, 32, d // 32, 32)
        norms = np.sqrt((B ** 2).sum(axis=(1, 3)))
        keep = norms >= np.quantile(norms, s)
        M = (B * keep[:, None, :, None]).reshape(d, d)
        a[f"bsr32_{int(s * 100)}"] = ("sparse", sp.bsr_matrix(M.T, blocksize=(32, 32)))
    return a


def nbytes(kind, M):
    if kind == "dense":
        return int(M.nbytes)
    return int(M.data.nbytes + M.indices.nbytes + M.indptr.nbytes)


def session(k):
    t0 = time.time()
    g = CFG["grid"]
    rng = np.random.default_rng(20261127)
    rows = []
    for ci, (d, b) in enumerate(g["d_batch"]):
        W = rng.standard_normal((d, d)).astype(np.float32)
        x = rng.standard_normal((b, d)).astype(np.float32)
        xT = np.ascontiguousarray(x.T)
        arms = arms_for(W, d)
        names = list(arms)
        rot = (ci + k) % len(names)
        for name in names[rot:] + names[:rot]:
            kind, M = arms[name]
            fn = (lambda M=M: x @ M) if kind == "dense" else (lambda M=M: M @ xT)
            p50, p95 = timeit(fn, g["reps"], g["warmup"])
            rows.append({"d": d, "batch": b, "arm": name, "bytes": nbytes(kind, M), "p50_ms": p50, "p95_ms": p95})
            print(f"s{k} d={d} b={b} {name:16s} p50 {p50:9.3f} ms p95 {p95:9.3f}", flush=True)
    e = env()
    e["OMP_NUM_THREADS"] = os.environ.get("OMP_NUM_THREADS"); e["OPENBLAS_NUM_THREADS"] = os.environ.get("OPENBLAS_NUM_THREADS")
    try:
        e["loadavg_end"] = os.getloadavg()
    except OSError:
        pass
    save(HERE / f"session_{k}.json", {"session": k, "env": e, "rows": rows, "runtime_s": round(time.time() - t0, 1)})


def analyze():
    sess = [json.loads(p.read_text()) for p in sorted(HERE.glob("session_*.json"))]
    labels = CFG["labels"]
    rng = np.random.default_rng(0)
    cells = {}
    for s in sess:
        dense = {(r["d"], r["batch"]): r["p50_ms"] for r in s["rows"] if r["arm"] == "dense"}
        for r in s["rows"]:
            if r["arm"] == "dense":
                continue
            cells.setdefault((r["d"], r["batch"], r["arm"]), {"sp": [], "bytes": r["bytes"]})["sp"].append(dense[(r["d"], r["batch"])] / r["p50_ms"])
    out = []
    for (d, b, arm), v in sorted(cells.items()):
        spd = np.array(v["sp"])
        boot = np.median(spd[rng.integers(0, len(spd), (10000, len(spd)))], axis=1)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        out.append({"d": d, "batch": b, "arm": arm, "label": labels[arm], "bytes": v["bytes"],
                    "speedup_per_session": spd.tolist(), "speedup_median": float(np.median(spd)),
                    "ci95_session_boot": [float(lo), float(hi)], "min": float(spd.min()), "max": float(spd.max())})
    matched_big = [r for r in out if r["label"] == "matched" and r["d"] >= 4096 and r["batch"] >= 16]
    unmatched_robust = [r for r in out if r["label"] == "unmatched" and r["speedup_median"] >= 1.1 and r["ci95_session_boot"][0] > 1.0]
    verdict = {
        "n_sessions": len(sess),
        "matched_cells_d>=4096_b>=16": [(r["arm"], r["d"], r["batch"], round(r["speedup_median"], 3)) for r in matched_big],
        "all_matched_big_>=1.1": all(r["speedup_median"] >= 1.1 for r in matched_big),
        "unmatched_robust_>=1.1": [(r["arm"], r["d"], r["batch"], round(r["speedup_median"], 3)) for r in unmatched_robust],
        "any_unmatched_>=1.1_any_shape": [(r["arm"], r["d"], r["batch"], round(r["speedup_median"], 3)) for r in out if r["label"] == "unmatched" and r["speedup_median"] >= 1.1],
    }
    save(HERE / "raw_output.json", {"experiment": "EXP-SSP-01", "stage": "CPU arm PILOT", "labels": labels,
                                     "grid": CFG["grid"], "cells": out, "verdict_inputs": verdict,
                                     "sessions": [{"session": s["session"], "env": s["env"], "runtime_s": s["runtime_s"]} for s in sess]})
    for r in out:
        print(f"d={r['d']:5d} b={r['batch']:4d} {r['arm']:16s} {r['label']:9s} speedup {r['speedup_median']:.3f} "
              f"[{r['ci95_session_boot'][0]:.3f}, {r['ci95_session_boot'][1]:.3f}] sessions {np.round(r['speedup_per_session'], 3).tolist()}")
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=int)
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze()
    else:
        session(a.session)
