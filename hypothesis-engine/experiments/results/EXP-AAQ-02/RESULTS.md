# EXP-AAQ-02 — Mechanism ablation: is it the activation statistics? — RESULTS, PILOT (2026-11-27)

Design: [`../../activation-aware-quantization.md`](../../activation-aware-quantization.md#exp-aaq-02--mechanism-ablation-is-it-the-activation-statistics)
(issue #45). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json) (per-layer MSEs and
chosen α), [`stdout.txt`](stdout.txt).

**PILOT: synthetic layers only.** The real-layer stage (one 1B model, all linear layers, 5 calibration
draws, model-level KL) was **not run** and is UNCHECKED.

**Verdict (toy): main prediction SUPPORTED; Hadamard sub-prediction NOT SUPPORTED.**
- With planted activation-outlier channels, AWQ with the true statistics gives about 2.2× lower output
  MSE than the same scaling with permuted statistics. Permuted, weight-norm and RTN are indistinguishable
  from each other. The falsifier (permuted within [0.95, 1.05] of the true arm) is not met.
- Hadamard + RTN is not between AWQ and RTN: it is ≈ RTN.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, scipy 1.18.1, Linux x86_64,
  Intel Xeon @ 2.90 GHz (shared). Runtime 131.9 s. Seeds 1000–1009 (one per "layer").

## Deviations (recorded before results)
1. Pilot stage only (see above). "Layers" = 10 synthetic layers (seeds): d_in = d_out = 256, n = 2048 rows
   split 50/50 into calibration and test. 8 input channels carry activation gain 20, as in
   `sketches/awq_toy.py`. W ~ N(0, 1/d_in). The quantizer is symmetric per-output-channel RTN at 4 bits.
2. α ∈ {0, 0.1, …, 1} is grid-searched per arm on the calibration split and scored on the test split.
   Each arm gets its own α, including permuted and weight-norm, which is generous to them.
3. Sensitivity settings, reported but not used for the verdict: 3 bits, and no outliers (gain 1).

## Results — main setting (4 bits, 8 outliers, gain 20)

| Arm | Median rel. output MSE (test) | Ratio vs AWQ, median [min, max] over 10 layers | AWQ better in | Wilcoxon p |
|---|---|---|---|---|
| AWQ (true stats) | 7.31e-3 | 1 | — | — |
| AWQ, permuted stats | 1.626e-2 | 2.21 [2.03, 2.30] | 10/10 | 0.002 |
| Weight-norm stats | 1.624e-2 | 2.20 [2.03, 2.30] | 10/10 | 0.002 |
| RTN | 1.626e-2 | 2.21 [2.03, 2.30] | 10/10 | 0.002 |
| Hadamard + RTN | 1.620e-2 | 2.22 [2.08, 2.37] | 10/10 | 0.002 |
| Hadamard + AWQ | 1.587e-2 | 2.19 [2.01, 2.26] | 10/10 | 0.002 |

With 10 layers, 0.002 is the smallest attainable two-sided Wilcoxon p. In every layer the grid search
chose α = 0 for the permuted arm, which makes it identical to RTN: wrong-channel scaling only hurt.
Hadamard + RTN fell strictly between AWQ and RTN in 5/10 layers (it beat RTN by 0.4% in median MSE).

Sensitivity: at 3 bits the ratios vs AWQ are 2.09–2.14, with AWQ better in 10/10 layers. With no
outliers, all arms are within 1% of AWQ (ratios 0.999–1.007, all Wilcoxon p ≥ 0.10). The AWQ gain
exists only when there are outlier activation channels, as H1's mechanism says.

## Pre-registered prediction vs result
- true < permuted ≈ weight-norm ≈ RTN in ≥ 80% of layers: **met** (10/10; permuted/RTN ratio = 1.000).
- Falsifier, permuted median ratio within [0.95, 1.05]: **not met** (2.21).
- Hadamard + RTN between AWQ and RTN: **not supported** (≈ RTN; between in only 5/10 layers, by < 1%).

## What this establishes, and what it doesn't
- In this toy, the benefit of AWQ comes from aligning the scale with the channels whose activations are
  large, not from rescaling or spread as such. The permuted arm has the same spread and gains nothing.
- It doesn't establish anything about real LLM layers. Their activation and weight statistics,
  correlated outliers, and the relation of layer MSE to model KL were not tested (real stage UNCHECKED).
- The Hadamard result is specific to this toy. Its weights have no outliers, so rotating them doesn't
  reduce weight-quantization error. Rotation is known to help mainly when weight or activation outliers
  are themselves quantized. Here activations stay in full precision.

## Design note (2026-11-27)
The sub-prediction "Hadamard + RTN is between AWQ and RTN" didn't account for weight-only quantization
with Gaussian weights. In that regime a random rotation leaves RTN error statistically unchanged. The
real-layer stage, where weights have outliers, is the meaningful test of that sub-prediction. The design
text is unchanged.
