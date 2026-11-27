# EXP-HVD-02 — Residual screening vs LPCMCI with known latents — RESULTS, PILOT (2026-11-27)

Design: [`../../hidden-variable-detection-causal-discovery-from-residuals.md`](../../hidden-variable-detection-causal-discovery-from-residuals.md#exp-hvd-02--residual-screening-vs-lpcmci-on-benchmarks-with-known-latents)
(issue #60). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json) (every dataset's truth,
residual p-values and |r|, LPCMCI flags and runtimes), [`stdout.txt`](stdout.txt).

**PILOT: 20 datasets per cell instead of 100. No FCI-style baseline.**

**Verdict (pilot, this generator): FALSIFIED.** In all 6 high-autocorrelation cells (φ = 0.9), and in fact
all 12 cells at both α, the permutation-calibrated residual screen has higher recall than LPCMCI at
LPCMCI's own FPR, with the bootstrap CI of the difference entirely below 0. The pre-registered falsifier
("residual screen has higher recall at matched FPR in the high-autocorrelation cells") is met.

**Strong caveat:** the generator I wrote favours the screen (deviation 3 below). The scoring is also
strict for LPCMCI (only `<->` counts). The result says the screen wins on this benchmark. It doesn't
say the screen is a better causal-discovery method.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, scipy 1.18.1, tigramite
  5.2.10.1 (pip-installed for this run). Intel Xeon @ 2.90 GHz, 4 vCPU (shared, load 10–28),
  `OMP_NUM_THREADS=1`, 3 worker processes. Runtime 2885.5 s.
- Seeds: dataset seed = 1000 × cell index + dataset index. 24 cells × 20 datasets = 480 datasets.
  LPCMCI took 1.7 s (N = 5, T = 200) to about 30 s (N = 10, L = 2, T = 1000, φ = 0.9) per α under load.

## Deviations (recorded before results)
1. **Scale**: 20 datasets per cell, not 100, as a PILOT. With 20–40 positive pairs per cell, recall CIs are
   about ±0.15–0.2. 100 per cell would need about 4 h of CPU on an idle 4-core machine.
2. **No FCI-style baseline**: tigramite 5.2 has no SVAR-FCI. The causal-learn FCI isn't time-series aware
   and wasn't installed.
3. **Generator** (re-implemented, not the 2007.01884 code): linear SVAR with lag-1 links only. Each latent
   drives exactly 2 observed variables at lag 1 (coef ±0.6), with N random observed lag-1 links (±0.3)
   and spectral radius < 0.97. There are **no contemporaneous links**, so residual correlation at lag 0
   comes only from latents. That is the easiest possible case for a contemporaneous residual screen.
4. **LPCMCI** settings: ParCorr (analytic), tau_max = 2, pc_alpha ∈ {0.01, 0.05}. A pair counts as flagged
   only if some lag-0..2 edge between i and j is `<->`, which is the only mark asserting a latent common
   cause.
5. **Matched FPR**: per cell, the screen is thresholded on |r| pooled across the cell's datasets, so that
   its FPR ≤ LPCMCI's FPR at that α. The screen's own p < 0.05 rule is also reported.

## Results (recall of confounded pairs; mean over the 6 cells of each autocorrelation level)

| φ | α | LPCMCI recall | LPCMCI FPR | Screen recall at LPCMCI's FPR | Cells with CI(LPCMCI − screen) < 0 |
|---|---|---|---|---|---|
| 0.5 | 0.01 | 0.20 | 0.026 | 0.98 | 6 / 6 |
| 0.5 | 0.05 | 0.20 | 0.057 | 0.99 | 6 / 6 |
| 0.9 | 0.01 | 0.14 | 0.022 | 0.99 | 6 / 6 |
| 0.9 | 0.05 | 0.22 | 0.041 | 0.99 | 6 / 6 |

Per-cell differences (LPCMCI − screen) range from −0.47 [−0.63, −0.32] (N = 5, L = 2, T = 500, φ = 0.5,
α = 0.01) to −1.00 [−1.00, −1.00]. Full table in `stdout.txt`. At its own p < 0.05 rule the screen has
recall 0.99 and FPR 0.06.

Post-hoc check, not pre-registered: I reran LPCMCI (α = 0.05) on 10 datasets in each of three cells and
recorded every edge mark on the true confounded pairs. LPCMCI makes the pair adjacent at some lag in 7–10
of 10 cases, but often orients the edge as `-->`, `<--`, `o->` or `x-x` instead of `<->`. Its low recall
is therefore largely an orientation and scoring outcome: it detects the dependence but often doesn't
call it latent.

## Pre-registered prediction vs result
- "LPCMCI ≥ residual screen in recall at matched FPR at high autocorrelation": **not met** (0.14–0.22
  vs 0.99).
- Falsifier: **met**, in all φ = 0.9 cells.

## What this establishes, and what it doesn't
- It establishes that, on a benchmark where latents are the only source of contemporaneous dependence,
  a simple signed permutation-tested residual screen finds the confounded pairs almost perfectly at
  about nominal FPR. LPCMCI at these settings rarely labels them `<->`.
- It doesn't establish that the engine's actual hidden-variable rule works. That rule uses a folded
  residual and |r| > 0.5, and fails in EXP-HVD-01/03. The screen tested here is the fixed variant.
- It doesn't establish that the screen beats LPCMCI on benchmarks with contemporaneous links,
  nonlinear links, or latents at other lags. On such benchmarks the screen would also flag directly
  linked pairs, and its FPR against "latent pairs" would rise. The 2007.01884 generators weren't used.
  Real-world data wasn't tested.

## Design note (2026-11-27)
The design should require a generator with contemporaneous observed links, plus a second LPCMCI
scoring rule (adjacency + not-oriented-as-direct) next to strict `<->`. Without both, the comparison is
tilted towards the screen, as here. The design text is unchanged.
