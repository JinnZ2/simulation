# EXP-CCO-01 — Is the prune/quantize order effect larger than seed noise and the margin? — RESULTS, PILOT (2026-11-27)

Design: [`../../compression-composition-and-ordering.md`](../../compression-composition-and-ordering.md#exp-cco-01--is-the-order-effect-larger-than-seed-noise-and-the-equivalence-margin)
(issue #50). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json) (per-seed accuracies
for both orders, all tests at margins 0.25, 0.5 and 1.0), [`stdout.txt`](stdout.txt).

**PILOT: toy MLP only.** ResNet-18/CIFAR-10, the small LM and the GPTQ-style Q arm were **not run** and
are UNCHECKED.

**Verdict (pre-registered 5 seeds): INCONCLUSIVE (underpowered).** Equivalence holds at s = 50%, b = 8, as
predicted. At s = 90%, b = 3 with interleaved fine-tuning the mean order effect is +8.0 pp, but its 90% CI
is [−0.1, +16.2]. After Holm correction no cell exceeds the margin, so H1's half of the prediction isn't
shown. The falsifier (equivalence in every cell, including the most aggressive) is **not met**: 13 of the
27 cells are not equivalent.

A secondary 20-seed run, **not pre-registered**, supports H1 at s = 90% with interleaved fine-tuning for
all three bit widths (Holm-adjusted minimal-effect p < 0.05). For example, s = 90%, b = 3 gives +10.0 pp,
90% CI [+6.5, +13.4]. P→Q is better.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, scipy 1.18.1, Linux x86_64,
  Intel Xeon @ 2.90 GHz (4 vCPU, heavily shared, load about 20). Runtime 672.8 s.
- Seeds 0–4 (primary) and 0–19 (secondary). Each seed fixes the data, init, base training and the
  fine-tune minibatch stream (`default_rng(10_000 + seed)`), shared by both orders, so the differences
  are paired.

## Deviations (recorded before results)
1. **Model and data**: the design's laptop pilot, using the numpy MLP from `sketches/noncommutativity_toy.py`
   (32-128-10 ReLU, synthetic 10-class Gaussian mixture, 4000 train / 2000 test, 1500 SGD steps). The
   outcome is top-1 test accuracy. No perplexity or KL is computed because there is no LM.
2. **Q arm**: symmetric per-output-channel RTN only. The GPTQ-style arm was not run.
3. **Recovery budget**: k = 100 masked SGD steps after each operator (interleaved), or 2k = 200 at the
   end. This is plain SGD on float weights, not quantization-aware training. Every fine-tuned pipeline is
   re-quantized and re-masked at the end, so the deployed artefact is always pruned and quantized.
4. **Ablations**: "no_rescale" uses quantization scales from the dense weights. "exact_ties" breaks
   magnitude ties at random in Q→P so that exactly s are pruned. Both were run for the none and
   interleaved arms, but not for end.
5. **Holm** is applied across the 9 s × b cells within each fine-tune arm. The minimal-effect test is
   one-sided in the observed direction with H0 |δ| ≤ margin.
6. **The secondary 20-seed run includes the 5 primary seeds**, so it isn't independent confirmation.
7. **Margin justification** (Threats section): the dense model reaches 100% test accuracy on every seed
   (SD over 20 seeds = 0.011 pp). The seed SD therefore can't justify 0.5 pp. The task is at ceiling,
   which compresses differences in mild cells (see the design note).

## Results — paired difference acc(P→Q) − acc(Q→P), pp (primary, 5 seeds, mean [90% CI])

| s \ b | 8 | 4 | 3 |
|---|---|---|---|
| **No fine-tune** | | | |
| 50% | 0.00 [0, 0] ✓ | 0.00 [0, 0] ✓ | +0.20 [−0.23, +0.63] |
| 70% | +0.01 [−0.05, +0.07] ✓ | +0.17 [−0.13, +0.47] | +1.69 [−0.49, +3.87] |
| 90% | +0.51 [−0.04, +1.06] | −0.47 [−4.99, +4.05] | +3.92 [−4.85, +12.69] |
| **Interleaved (k after each)** | | | |
| 50% | 0.00 ✓ | 0.00 ✓ | 0.00 ✓ |
| 70% | +0.03 [0.00, +0.06] ✓ | +0.01 [−0.07, +0.09] ✓ | +0.20 [−0.04, +0.44] |
| 90% | +6.52 [+0.36, +12.68] | +4.60 [−6.79, +15.99] | **+8.04 [−0.11, +16.19]** |
| **End (2k after both)** | | | |
| 50% | 0.00 ✓ | 0.00 ✓ | +0.02 [−0.02, +0.06] ✓ |
| 70% | −0.01 [−0.03, +0.01] ✓ | +0.01 [−0.05, +0.07] ✓ | +0.02 [−0.03, +0.07] ✓ |
| 90% | −0.02 [−0.85, +0.81] | 0.00 [−9.68, +9.68] | +3.87 [−1.79, +9.53] |

✓ = TOST-equivalent at ±0.5 pp after Holm. No cell has a Holm-significant minimal effect at 5 seeds.
Equivalent cells: 14/27 at ±0.5 pp, 14/27 at ±0.25 pp, 17/27 at ±1.0 pp.

Secondary, 20 seeds (not pre-registered): the cells that exceed the margin after Holm are s = 90% with
interleaved fine-tuning at b = 8 (+6.3 pp [+4.7, +7.8]), b = 4 (+6.1 [+2.9, +9.3]) and b = 3
(+10.0 [+6.5, +13.4]). The set is the same at margins 0.25, 0.5 and 1.0. At s = 90%, b = 3 the mean accuracy
is 85.8% for P→Q vs 75.8% for Q→P. With end-only fine-tuning the order effect at s = 90% shrinks to
+0.1 to +4.3 pp, and none of these cells passes either test.

Ablations: exact_ties is identical to main everywhere, because with continuous weights there are no
magnitude ties. no_rescale reduces the interleaved effect at s = 90% (b = 3: +5.7 vs +8.0 pp at 5 seeds;
+6.1 vs +10.0 at 20 seeds). Recomputing scales after pruning is part of why P→Q wins.

## Pre-registered prediction vs result
- Equivalence at s = 50%, b = 8: **met** (all three fine-tune arms).
- H1 at s = 90%, b = 3 with fine-tuning: **not shown at 5 seeds** (interleaved CI includes 0; Holm
  minimal-effect p = 0.48). It is shown in the non-pre-registered 20-seed run.
- Falsifier (equivalence everywhere): **not met**.
- At this scale the 5-seed design is underpowered for the aggressive cells. The per-seed SD of the order
  effect there is about 8–10 pp.

## What this establishes, and what it doesn't
- In a toy MLP, prune/quantize order is practically irrelevant at mild settings. At 90% sparsity with
  interleaved recovery, pruning first then quantizing is better by several pp (20-seed evidence). The
  effect depends on the recovery schedule: it mostly disappears when all fine-tuning happens at the end.
- It doesn't establish anything for ResNet-18/CIFAR-10, LMs, GPTQ, or quantization-aware fine-tuning.
  It also doesn't establish why the order matters (EXP-CCO-02).

## Design note (2026-11-27)
The pilot task is at ceiling (dense accuracy 100%). That makes the mild cells trivially equivalent and
prevents a seed-SD-based justification of the 0.5 pp margin. A harder pilot task (dense accuracy around
85–90%) and about 20 seeds would be needed for the pilot to test the design as intended. The design text
is unchanged.
