# Compression composition and ordering — what needs to be known, and experiments (EXP-CCO)

Draft read: `hypotheses/compression-composition-and-ordering.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

Charter hypothesis (`research/TODO.md` #4): **H4 — compression composition is noncommutative,
C₂(C₁(M)) ≠ C₁(C₂(M)), especially for pruning and low-bit quantization.** `research/notes/09` §1.2
records that "prune-first is universally optimal" (attributed there to Harma 2025; UNCHECKED here) is
contradicted by arXiv:2603.18426, and recommends that paper's Progressive Intensity Hypothesis as the
framing.

## 1. What the engine claims, and on what evidence

**Headline statement:** "*Model Compression with Keras Pruning and Post-Training Quantization* reports:
This talks about the techniques used to compress a model…". NEW HYPOTHESIS, 49 surviving claims.
The headline is on-topic in vocabulary, but it is a tutorial-style description with no ordering result.

**Evidence base (AUDIT):** 82 findings (46 arXiv, 18 Crossref, 18 S2); 79 claims; 49 surviving. A
two-method co-occurrence screen hits 26/49, the highest rate of the eight topics, because S2 and Crossref
dominate the survivors here (34/49), not arXiv (E2). 19/82 findings have no abstract (E9).
**Homonym contamination:** The Crossref query "composite model compression noncommutative" retrieved
materials-science papers on compressive failure of composite laminates, rock and foam. Several survive
at 0.80–0.89, e.g. *Failure analysis of thin-walled composite profiles subjected to axial compression*,
which appears twice.

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What the abstract shows | Bearing on H4 |
|---|---|---|---|
| arXiv:2603.18426 (Kim et al., "Prune-then-Quantize or Quantize-then-Prune?") — **not in the engine's tree**; cited by `research/notes/09` | Yes | Formulates compression-order optimization; proposes the **Progressive Intensity Hypothesis** (weaker perturbations should precede stronger ones); "theoretical guarantees showing that the relative benefit of one order increases with the underlying performance gap"; experiments on language and vision models. | Direct. The engine never retrieved the most relevant paper. |
| Joint Pruning & Quantization for Extremely Sparse NNs, arXiv:2010.01892 | Yes | Two-stage pruning + quantization pipeline for stereo depth; "pruning and quantization should be investigated jointly"; ~99% memory reduction. | Joint compression, not an order comparison. |
| Optimal Brain Compression, DOI 10.52202/068431-0323 | Yes (Crossref: NeurIPS 35, 2022; no abstract in Crossref, so the engine staked "(no abstract)") | Unified PTQ + pruning framework (from title and venue; content UNCHECKED). | Possibly relevant; UNCHECKED. |
| Failure analysis of thin-walled composite profiles … | Listed twice | Materials mechanics. | None (homonym). |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- 3 escape-hatched claims; no refutations; no hidden-variable suspects.

### (b) Gaps identified here
- **G1. Inequality alone is nearly guaranteed and so says almost nothing.** Pruning and rounding are
  nonlinear, data-dependent maps, so C₂∘C₁ = C₁∘C₂ exactly would be surprising. The scientific content
  is (i) whether the order effect is larger than seed-to-seed variation and practically relevant (an
  equivalence margin is needed), and (ii) whether its **sign is predictable** in advance.
- **G2. Fine-tuning budget is a confounder.** If one order gets recovery training between the steps
  and the other doesn't, or gets more steps, the order effect is confounded with training. Total
  recovery tokens and their placement must be matched.
- **G3. "Intensity" can be circular.** The Progressive Intensity Hypothesis needs intensity measured
  before and separately from the composite outcome (e.g. single-operation damage on a calibration split),
  then used to predict the order on held-out configurations.
- **G4. Definition of each operator under composition.** Does Q→P prune on quantized magnitudes, with
  ties? Does P→Q recompute scales after pruning? These implementation choices can produce or remove the
  effect; they must be specified and varied.
- **G5. Replication status.** 2603.18426's experimental claims are UNCHECKED here; an independent
  replication on other models is the point of EXP-CCO-02.

## 3. Experiments

### EXP-CCO-01 — Is the order effect larger than seed noise and the equivalence margin?
- **Gaps:** G1, G2, G4.
- **H1:** |acc(P→Q) − acc(Q→P)| exceeds a 0.5-percentage-point equivalence margin in at least one
  sparsity × bit-width cell. **H0 (equivalence):** For all cells, the 90% CI of the paired difference
  lies within ±0.5 pp (TOST).
- **Variables:** Top-1 accuracy (vision) or perplexity and KL to the dense model (LM). P = global
  magnitude pruning at s ∈ {50, 70, 90}%. Q = symmetric per-channel RTN and a GPTQ-style arm at
  b ∈ {8, 4, 3}.
- **Design:** ResNet-18 / CIFAR-10 and a small LM (≤ 160M parameters). For each order, a matched recovery
  budget: k steps after each operator, or all 2k steps at the end, run as a separate factor. 5 seeds;
  each seed fixes the base model and the fine-tuning data order, shared across both orders so the
  comparison is paired. Include the no-fine-tune arm as a near-structural negative control (G4).
  Ablations: scale recomputation on/off after pruning; tie-handling in Q→P.
- **Pre-registered prediction:** Equivalence (H0) holds at s = 50%, b = 8. H1 holds at s = 90%, b = 3
  with fine-tuning. **Falsified if** equivalence holds in every cell, including the most aggressive one.
- **Analysis:** Paired differences per cell, TOST at ±0.5 pp, Holm correction across the 9 cells.
- **Threats:** Margin choice (justify 0.5 pp from the seed SD of the uncompressed model and report
  sensitivity at 0.25 and 1.0); implementation details (G4).
- **Tier:** Pilot: laptop CPU (`sketches/noncommutativity_toy.py`). Real: single GPU, under 1 GPU-day
  for CIFAR plus a small LM (rough).
- **Would establish:** Where order matters by a practically relevant amount for these operators and
  scales. **Would not establish:** Why, or which order is better in general (EXP-CCO-02).
- **Sketch:** `sketches/noncommutativity_toy.py` (numpy MLP, P/Q both orders, with and without matched
  fine-tuning, paired seeds).

### EXP-CCO-02 — Out-of-sample test of the Progressive Intensity Hypothesis
- **Gaps:** G3, G5.
- **H1 (PIH, per 2603.18426's abstract):** Applying the lower-intensity operator first gives the better
  composite. The benefit of the better order grows with the intensity gap.
  **H0:** Order chosen by measured intensity predicts the better composite no better than chance (50%),
  and the benefit isn't associated with the gap.
- **Variables:** Intensity of each operator = its standalone damage (ΔKL or Δaccuracy) on a calibration
  split, measured before any composite run. Outcome: which order wins on a held-out test split, and by
  how much.
- **Design:** Operators: pruning (unstructured, 2:4), quantization (8/4/3-bit), low-rank (rank ratio
  0.5/0.25). All ordered pairs at several strengths, giving ≥ 40 configurations across 2 architectures
  (one CNN, one small transformer). Freeze the predictions in a file and commit it before running the
  composites. 3 seeds per configuration.
- **Pre-registered prediction:** Order predicted by intensity is correct in ≥ 70% of configurations, and
  Spearman(intensity gap, order benefit) > 0.3. **Falsified if** accuracy ≤ 60% (binomial test vs 0.5
  not significant at α = 0.05) or the Spearman CI includes 0.
- **Analysis:** Binomial test on prediction accuracy; Spearman with a bootstrap CI over configurations;
  configurations where the two intensities are within noise are reported separately as "no prediction".
- **Threats:** Intensity measured on the same data as the outcome (use disjoint splits); configurations
  are not independent (cluster the bootstrap by operator pair).
- **Tier:** Single GPU, about 2–3 GPU-days (rough).
- **Would establish:** Whether PIH predicts outside the original paper's settings. **Would not
  establish:** The theoretical guarantee in 2603.18426, which this does not check.
