# EXP-RGC-01 — Instrument validation before any comparison — RESULTS (2026-11-27)

Design: [`../../representation-geometry-under-compression.md`](../../representation-geometry-under-compression.md#exp-rgc-01--instrument-validation-before-any-comparison)
(issue #62). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json), [`stdout.txt`](stdout.txt).

Checks (i) and (ii) ran at full design scale. **Check (iii) is a PILOT**: sklearn MLPs on 8×8 digits, not
ResNet-18 on CIFAR-10.

**Verdict: SUPPORTED for unwhitened debiased linear CKA, which passes (i), (ii) and the (iii) pilot.
FALSIFIED for debiased CKA on whitened activations, which fails (ii) in every cell.** Biased CKA fails (i)
as predicted. Procrustes passes (ii) and (iii) but has no zero point for (i).

The design named "debiased CKA on whitened activations, or Procrustes distance" as candidate primary
metrics. This run rules out the whitened variant. Debiased CKA without whitening, or Procrustes, remain
usable.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, scipy 1.18.1,
  scikit-learn 1.9.1. Intel Xeon @ 2.90 GHz, 4 vCPU (shared, load 10–28). Runtime 3711.9 s.
  Seed `default_rng(20261127)` for (i) and (ii). MLP seeds 0–4 for (iii).

## Deviations and fixed choices (recorded before results)
1. **(i)** "Study n and d": n = 2000 (the probe size in the design) with d ∈ {64, 128, 256, 512}
   (ResNet-18 channel widths), plus n ∈ {50, 200, 1000} at d = 1000 (the design's n = 50, d = 1000 stress
   case). 100 independent Gaussian pairs each. Pass rule for a CKA metric: 95th percentile of
   |value| ≤ 0.05 (the design's falsifier is "|debiased CKA| > 0.05 on random pairs").
2. **(ii)** Base: n = 2000 with spectrum exp(−j / (d/8)), in a random orthogonal basis. Equal-Frobenius
   isotropic noise vs noise in the top k = d/16 PCs, at noise/signal norm ratios {0.1, 0.3, 1.0}. 50
   replicates, bootstrap CI of the paired difference. Pass = correct sign with the CI excluding 0 in
   every cell.
3. **Whitening**: PCA whitening with ridge 1e-3 × the mean eigenvalue, only when n > d.
4. **(iii) PILOT**: torch and a GPU aren't available. Instead: 5 sklearn MLPs (128, 64) on digits; per-
   output-channel RTN of all weights at 8, 4 and 3 bits; the probe is the 540-image test split; both
   hidden layers (not 4). Separation = compressed-vs-parent similarity lies outside the range of the 10
   seed-vs-seed pairs.

## Results

(i) Random pairs: mean and 95th percentile of |value|

| n, d | biased CKA | debiased CKA | debiased CKA, whitened | Procrustes (no 0 point) |
|---|---|---|---|---|
| 2000, 64 | 0.031 / 0.032 ✓ | 0.000 / 0.0015 ✓ | 0.000 / 0.0016 ✓ | 1.70 |
| 2000, 128 | 0.060 / 0.061 ✗ | 0.000 / 0.0012 ✓ | 0.000 / 0.0013 ✓ | 1.57 |
| 2000, 256 | 0.113 / 0.115 ✗ | 0.000 / 0.0015 ✓ | 0.000 / 0.0013 ✓ | 1.40 |
| 2000, 512 | 0.204 / 0.205 ✗ | 0.000 / 0.0013 ✓ | 0.000 / 0.0012 ✓ | 1.16 |
| 50, 1000 | 0.952 / 0.956 ✗ | −0.003 / **0.059 ✗** | n/a (n ≤ d) | 0.025 |
| 200, 1000 | 0.833 / 0.836 ✗ | −0.001 / 0.013 ✓ | n/a | 0.100 |
| 1000, 1000 | 0.500 / 0.501 ✗ | 0.000 / 0.003 ✓ | n/a | 0.500 |

(ii) Equal-norm perturbations. Paired difference, with positive meaning top-PC noise was judged more
damaging (correct):

| Metric | Cells correct with CI excluding 0 | Range of mean difference |
|---|---|---|
| biased CKA | 12 / 12 | +0.013 (ratio 0.1) … +0.41 (ratio 1.0) |
| debiased CKA | 12 / 12 | +0.013 … +0.41 |
| debiased CKA, whitened | **0 / 12**, wrong sign everywhere | −0.18 … −0.70 |
| Procrustes | 12 / 12 (94–100% of replicates per cell) | +0.0001 … +0.066 |

Whitening sets all PC variances to about 1. Noise confined to the top PCs then perturbs a few
directions out of d, while isotropic noise is amplified in the many low-variance directions. The
whitened metric therefore inverts the ranking, which is a structural property, not a sample-size effect.

(iii) PILOT, digits MLPs. FP test accuracy is 97.8–98.0%. After RTN it is 97.8–98.0% (8-bit), 97.4–98.0%
(4-bit) and 97.4–98.0% (3-bit).

| Layer, metric | seed-vs-seed (10 pairs) | FP vs 8-bit | FP vs 4-bit | FP vs 3-bit |
|---|---|---|---|---|
| L1, debiased CKA | 0.917–0.932 | 1.000 | 0.999 | 0.995–0.996 |
| L2, debiased CKA | 0.869–0.917 | 1.000 | 0.999 | 0.989–0.993 |
| L1, whitened debiased CKA | 0.377–0.390 | 1.000 | 0.977–0.980 | 0.897–0.904 |
| L2, whitened debiased CKA | 0.360–0.381 | 1.000 | 0.969–0.973 | 0.863–0.874 |
| L1, Procrustes | 0.141–0.155 | 0.000 | 0.002 | 0.010–0.011 |
| L2, Procrustes | 0.140–0.168 | 0.000 | 0.003 | 0.013–0.016 |

Every metric separates compressed-vs-parent from seed-vs-seed, with no overlap at any bit width.

## Pre-registered prediction vs result
- "Debiased CKA passes (i)–(ii)": **met** at the study's n = 2000 (95th percentile ≤ 0.0015; 12/12 cells
  in (ii)). At the stress case n = 50, d = 1000 its 95th percentile is 0.059 (mean −0.003, the noise of
  an unbiased estimator at n = 50). That slightly exceeds the 0.05 rule, so n = 50 is too small for this
  tolerance.
- "Biased CKA fails (i) at n = 50, d = 1000": **met** (0.95). It also fails at n = 2000 once d ≥ 128.
- Falsifier "|debiased CKA| > 0.05 on random pairs, or doesn't order the perturbations": not met for
  unwhitened debiased CKA at the study's n. **Met for the whitened variant**, which misorders every (ii)
  cell.
- (iii) separation: met in the pilot.

## What this establishes, and what it doesn't
- Choose unwhitened debiased CKA or Procrustes as the primary metric for EXP-RGC-02/03. Don't use
  whitened CKA, and don't use biased CKA at d/n ≳ 0.05.
- Check (iii) on a toy MLP only shows that the metric isn't saturated by seed variation in this
  setting. ResNet-18/CIFAR-10 (UNCHECKED) could behave differently: its seed-vs-seed CKA is typically
  higher, so separation is harder.
- This says nothing about H3 or H5.

## Design note (2026-11-27)
The design listed "debiased CKA on whitened activations" as a candidate primary metric. Check (ii) shows
that whitening inverts the top-PC vs isotropic ranking that H1(ii) requires, so it should be dropped
from the candidates. The design text is unchanged.
