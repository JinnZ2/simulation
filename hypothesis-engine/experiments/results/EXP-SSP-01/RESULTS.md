# EXP-SSP-01 — Kernel-level factorial (CPU arm) — RESULTS, PILOT (2026-11-27)

Design: [`../../structured-sparsity-and-hardware-matched-pruning.md`](../../structured-sparsity-and-hardware-matched-pruning.md#exp-ssp-01--kernel-level-factorial-sparsity-format--runtime-support--shape)
(issue #65). Code: [`run.py`](run.py). Match labels and grid were written before any timing:
[`match_labels.json`](match_labels.json). Raw timings: [`session_1.json`](session_1.json),
[`session_2.json`](session_2.json), [`session_3.json`](session_3.json). Analysis:
[`raw_output.json`](raw_output.json), [`stdout.txt`](stdout.txt).

**PILOT, CPU arm only, on a heavily shared machine.** The GPU arm and the d = 4096 × batch 256 and
d = 8192 cells were **not run** and are UNCHECKED.

**Verdict: INCONCLUSIVE (measurement invalid under contention).** The analysis as specified would
read "falsified": two unmatched dense-kernel cells (masked-dense 50% and 2:4-in-dense at d = 2048,
batch 256) show a 2.5× and 3.1× "speedup" with the session-bootstrap CI above 1. Those arms run the
identical OpenBLAS kernel on the same shape and FLOPs as dense, so a real speedup is impossible. A
re-check at lower load gave dense 17.9 ms vs masked-dense 17.6 ms (≤ 2% apart). The sessions
therefore measured machine contention, not formats, and **no conclusion about H1 is drawn.**

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5 (scipy-openblas 0.3.34,
  DYNAMIC_ARCH), scipy 1.18.1. Intel Xeon @ 2.90 GHz, 4 vCPU, Linux 6.1.155.
  `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`.
- 3 sessions, each a new process, run back-to-back 18:27–19:02 UTC with 60 s gaps. Runtimes were 902,
  620 and 464 s. The 1/5/15-minute load average at the end of each session was 24/26/23, 17/20/21 and
  13/15/18 on 4 vCPUs. Other agents' jobs were running and weren't touched.

## Deviations (recorded before results)
1. **Grid reduced** to (d, batch) ∈ {(2048, 1), (2048, 16), (2048, 256), (4096, 1), (4096, 16)}. Under this
   load a single CSR-50% GEMM at d = 4096, batch 256 took about 3 s, so the full grid at 110 calls per
   arm wasn't feasible within the time budget.
2. **Sessions**: 3 new processes back-to-back, not "different times of day / reboot".
3. **Sparse kernels**: scipy.sparse CSR and BSR (32×32) single-threaded reference kernels. No MKL/oneDNN
   sparse library was available, so "best available non-naive kernel" isn't met. 2:4 has no CPU sparse
   path and is labelled unmatched.
4. **Single-thread BLAS**, to make dense and sparse comparable and to reduce the impact of contention.
5. **Machine contention** (load average 13–26 on 4 vCPUs) violates the design's measurement assumptions.
   This deviation is fatal to the comparison (see the verdict).

## Results (median speedup over dense across 3 sessions [session-bootstrap 95% CI]; full grid in `stdout.txt`)

| Arm (label) | d=2048 b=1 | d=2048 b=16 | d=2048 b=256 | d=4096 b=1 | d=4096 b=16 |
|---|---|---|---|---|---|
| masked_dense_50 (unmatched control) | 0.92 [0.84, 1.03] | 0.95 [0.59, 2.06] | **2.55 [2.29, 2.69]** | 1.00 [1.00, 1.01] | 0.92 [0.92, 0.99] |
| nm_2of4_dense (unmatched control) | 1.01 [0.99, 1.02] | 1.03 [0.69, 5.07] | **3.14 [1.11, 4.95]** | 1.02 [0.11, 1.03] | 1.03 [0.23, 1.06] |
| struct_50 (matched) | 2.11 | 7.20 [2.47, 16.3] | 2.99 | 2.56 | 1.44 [0.95, 2.08] |
| csr_50 / 70 / 90 (matched) | 0.17 / 0.38 / 1.30 | 0.45 / 0.45 / 9.2 | 0.17 / 0.24 / 1.22 | 0.34 / 0.23 / 1.95 | 0.70 / 1.13 / 3.24 |
| bsr32_50 / 75 (matched) | 0.51 / 1.16 | 0.15 / 0.29 | 0.06 / 0.19 | 0.34 / 1.81 | 0.47 / 0.47 |

The identical-FLOP controls carry the diagnosis. Wherever they are far from 1.0 (or their CI is very
wide, as at d = 2048, batch 16, where session 1 differs from sessions 2–3 by up to 10×), the cell is
contaminated. In the d = 2048, batch 256 cell the dense arm took 90–105 ms in all three sessions, while
masked-dense took 38–39 ms. A standalone re-check of the same arrays and code at load about 10 gave
17.9 ms vs 17.6 ms. The effect is a scheduling artefact. Its cause (systematic timing position in the
rotation, or co-tenant phases) wasn't isolated.

The pattern that does look stable across sessions (at low CI width) is consistent with prior
expectation but isn't evidence here. Channel-pruned dense (struct_50) is about 2–3× faster, CSR is
slower than dense at ≤ 70% sparsity, and CSR at 90% is faster at small batch.

## Pre-registered prediction vs result
- "Every matched cell ≥ 1.1× at d ≥ 4096 and batch ≥ 16": only one such cell was run (d = 4096, b = 16).
  CSR-50%, BSR-50% and BSR-75% were all < 1 there. Under the labels as written, this part would fail.
  The labels, written before timing, treated every zero-skipping scipy kernel as "matched". That
  includes reference CSR/BSR kernels that are known to lose to dense BLAS at moderate sparsity. This is
  a labelling issue; see the design note.
- "No unmatched cell robustly ≥ 1.1×": violated on paper by the dense-kernel controls, but that is a
  measurement artefact, as shown above.
- **Not decided.** A rerun is needed on an otherwise idle machine (load < 1). It should include a
  pre-check that masked-dense/dense lies within [0.97, 1.03] in every cell before accepting a session.

## What this establishes, and what it doesn't
- It establishes that, on this shared machine today, wall-clock kernel timing wasn't trustworthy even
  with 100 repeats, medians and 3 sessions. The built-in identical-FLOP controls detected this.
- It establishes nothing about H1 or H2, nothing about the GPU arm, and nothing about end-to-end latency.

## Design note (2026-11-27)
1. "Runtime-matched" should be defined per (format, sparsity, batch), not per format. A reference CSR
   kernel is "supported" but isn't expected to beat dense BLAS at 50% sparsity. Labels written per
   format, as here, make the "every matched cell" clause test kernel quality rather than matching.
2. The design should require an idle-machine check, using the masked-dense/dense control within ±3% in
   every cell, as an acceptance criterion for each session.

The design text is unchanged.
