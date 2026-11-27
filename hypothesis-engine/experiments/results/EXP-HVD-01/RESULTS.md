# EXP-HVD-01 — Operating characteristics of the engine's hidden-variable rule — RESULTS (2026-11-27)

Design: [`../../hidden-variable-detection-causal-discovery-from-residuals.md`](../../hidden-variable-detection-causal-discovery-from-residuals.md#exp-hvd-01--operating-characteristics-of-the-engines-rule-synthetic-planted-latent)
(issue #59). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json) (all 576 cells),
[`stdout.txt`](stdout.txt) (summary).

**Verdict: part 1 SUPPORTED, part 2 FALSIFIED at high autocorrelation; overall falsifier NOT met.**
- The engine-shaped rule has power < 0.5 in every cell with n ≤ 200, and power ≈ 0 almost everywhere.
- The circular-shift permutation test holds its false-positive rate (FPR) near α for φ ≤ 0.5, but is
  anticonservative at φ = 0.9 (about 0.07) and φ = 0.99 (about 0.10, up to 0.175 in one cell).
  So "signed_perm FPR within [0.03, 0.07] across φ" fails.
- H0 (engine_abs power ≥ 0.8 at FPR ≤ 0.05 in most cells) is rejected: no cell in any variant meets it.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, scipy 1.18.1, Linux 6.1.155
  x86_64, Intel Xeon @ 2.90 GHz (4 vCPU, shared). Runtime 37.9 s.
- Seeds: cell i uses `default_rng(10_000 + i)` (recorded per cell in `raw_output.json`).
- 1000 replicates per cell. The Monte Carlo SE of a rate near 0.05 is 0.0069.
  Grid: n {20, 50, 200, 1000} × c {0.25, 0.5, 1, 2} × φ {0, 0.5, 0.9, 0.99} × proxy noise {0.1, 0.5, 1},
  × 3 SCM variants (linear; tanh link; sign-flip between halves, as the design's Threats section asks).

## Deviations and fixed choices (recorded before results)
1. Fixed a = 0.8 (X on Z) and b = 1 (Y on X). The design doesn't specify these. The analyst fits OLS of
   Y on X without an intercept, as in the sketch. Z is a stationary AR(1) with unit variance.
2. The permutation test uses every circular shift in [n/10, n − n/10]. The sketch sampled 199 shifts
   at random. At n = 20 this leaves 17 shifts, so the minimum attainable p is 1/17 ≈ 0.059 > 0.05.
   Power and FPR are therefore 0 by construction at n = 20. FPR summaries for signed_perm use n ≥ 50.
3. ROC: reported as AUC per detector, computed on the detector's statistic, rather than as plotted curves.

## Results (linear SCM unless stated)

Engine-shaped rule (folded |residual|, mean|r| ≥ 0.1 and |pearson(|r|, cand)| > 0.5):

| | linear | tanh | signflip |
|---|---|---|---|
| Cells (n ≤ 200) with power < 0.5 | 100% | 100% | 100% |
| Cells with power ≥ 0.8 and FPR ≤ 0.05 | 0% | 0% | 0% |
| Median power / median AUC | 0 / 0.525 | 0 / 0.504 | 0 / 0.563 |
| Power by n (20, 50, 200, 1000) | 0.039, 0.003, 0.000, 0.000 | 0.026, 0.001, 0, 0 | 0.062, 0.018, 0.010, 0.006 |

Signed residual with circular-shift permutation p < 0.05 (linear). Power by n × latent effect c,
averaged over φ and proxy noise:

| n \ c | 0.25 | 0.5 | 1 | 2 |
|---|---|---|---|---|
| 20 | 0 | 0 | 0 | 0 |
| 50 | 0.09 | 0.25 | 0.58 | 0.76 |
| 200 | 0.35 | 0.78 | 0.93 | 0.97 |
| 1000 | 0.94 | 1.00 | 1.00 | 1.00 |

Signed_perm FPR against an independent AR(1) with the same φ (linear; MC SE ≈ 0.007 per cell):

| φ | n = 50 | n = 200 | n = 1000 | mean (n ≥ 50) | max cell |
|---|---|---|---|---|---|
| 0 | 0.049 | 0.049 | 0.049 | 0.049 | 0.068 |
| 0.5 | 0.053 | 0.055 | 0.048 | 0.052 | 0.067 |
| 0.9 | 0.073 | 0.072 | 0.059 | 0.068 | 0.094 |
| 0.99 | 0.095 | 0.123 | 0.094 | 0.104 | 0.175 |

Only 69% of n ≥ 50 cells have FPR in [0.03, 0.07] (tanh 74%, signflip 62%). The thresholded signed rule
(|r| > 0.5, no permutation) has a median AUC of 0.90 but a median power of 0.02 at the engine's threshold.
In the sign-flip variant every detector fails (AUC 0.45–0.56). Folding |r| didn't rescue it: power was
0.006–0.06.

## What this establishes, and what it doesn't
- For this SCM family, the engine's hidden-variable rule is close to blind. Folding the residual
  (|r|) removes the linear association with a symmetric latent, so the |r| > 0.5 test almost never
  fires, even at n = 1000 and c = 2. It doesn't even help in the sign-flip regime it was meant to handle.
- Using the signed residual with a permutation p-value is a large improvement. At high
  autocorrelation, though, circular shifts of length n/10 don't break dependence enough: the FPR roughly
  doubles at φ = 0.99. A fix should use a block or surrogate null that accounts for φ, or a larger
  minimum shift.
- It doesn't say whether any suggestion the engine actually produced is right or wrong (see
  EXP-HVD-03). In the engine's own data, beta is > 0.5 for almost every claim, so folding there is
  nearly a no-op. The engine's failure there comes from other parts of the rule (see HVD-03).
- Toy SCM only: Gaussian noise, one latent, one proxy.

## Design note (2026-11-27)
The design's part-2 prediction implicitly assumed that circular shifts give an exact null for any φ.
They don't when φ is close to 1 at these n. The original design text is unchanged; this note records
why that sub-prediction failed.
