# Representation geometry under compression — what needs to be known, and experiments (EXP-RGC)

Draft read: `hypotheses/representation-geometry-under-compression.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

Charter hypotheses (`research/TODO.md` #3, #5):
**H3 — quantization error is anisotropic in representation space**, so spectral and geometric metrics
should predict damage better than per-layer weight MSE.
**H5 — distillation may restore behavior but not internal geometry.**

## 1. What the engine claims, and on what evidence

**Headline statement:** "*Modular Functors with Singularities from Vertex Operator Algebras Beyond
Rigidity and Finiteness* reports: For a vertex operator algebra V … we propose a construction for spaces
of conformal blocks…". NEW HYPOTHESIS, 7 surviving claims. This is a mathematical-physics paper and
irrelevant to H3/H5.

**Evidence base (AUDIT):** 42 findings (27 arXiv, 15 S2); 35 claims; 7 surviving. The core-term screen
hits 3/7. With a size-matched partner pool from other topics, the number of claims that would survive
under the E4 ratchet is 5, the same as with the real pool (5). For this topic, the test stage can't be
told apart from a cross-topic control. **This draft hasn't changed since at least 2026-11-05:** no
supporting claim was added in the last 6 engine commits, and 4 of those 6 regenerated an identical body
apart from the timestamp line (see README).

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What the abstract shows | Bearing |
|---|---|---|---|
| Rethinking CKA in Knowledge Distillation, arXiv:2401.11824 (supporting, 0.80) | Yes | CKA used as a distillation objective; analysis of "the essence of CKA". | H5 instrument. Results UNCHECKED. |
| Correcting Biased CKA Measures …, arXiv:2405.01012 (escape-hatched) | Yes | In the low-data, high-dimensional regime, **biased CKA gives high similarity even for pairs of random matrices**; demonstrated on fMRI/MEG (THINGS). | Direct instrument-validity warning for H3/H5. The engine dropped it. |
| Verifying the Union of Manifolds Hypothesis for Image Data (S2) | Listed | Intrinsic-dimension structure of image data. | Background. UNCHECKED. |
| Headline (VOA modular functors) | Not fetched | — | None (E2). |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- Escape-hatched (7): CKA bias correction (above), RSA/CKA/CCA equivalence, a survey of
  intrinsic-dimension estimators, *Low-Rank Prehab*, *Nonlinear spiked covariance matrices…*, and
  others. These are mostly instrument papers, the ones that would tell you how to measure H3/H5, and
  the engine removed them.

### (b) Gaps identified here
- **G1. Instrument validity comes first.** Linear CKA is invariant to orthogonal transforms and
  isotropic scaling, so rotation-based compression (QuaRot, SliceGPT) is invisible to it by
  construction (`research/notes/09` §1.2 item 5, and confirmed numerically by `sketches/cka_toy.py`
  check 1 as a mathematical identity, not an empirical result). Biased CKA is inflated when n ≪ d
  (2405.01012). LLM activations are anisotropic (a cone), so un-whitened angle and ID metrics are
  confounded by it.
- **G2. A null baseline is needed.** Geometry of a compressed model vs its parent has to be compared
  with geometry of independently seeded parents. Otherwise "geometry changed" has no scale. For H5 this
  baseline is central: two teachers trained from different seeds already differ.
- **G3. H3's operational form.** "Anisotropic" must mean something measurable: e.g. the fraction of
  quantization-error energy falling in the top-k principal directions of the layer-input activation
  covariance, compared with the isotropic expectation k/d. The predictive claim needs a held-out
  comparison against weight MSE and output MSE as baselines.
- **G4. H5's operational form.** "Restores behavior" needs a margin (e.g. top-1 agreement ≥ 98% and
  KL ≤ ε). "Not geometry" needs a geometric distance that is significantly larger than the
  seed-baseline distance from G2. Without both margins, H5 can't be falsified.
- **G5. Multiple metrics, multiple layers.** Testing many metrics × layers inflates false positives.
  Pre-register one primary metric and one layer set.

## 3. Experiments

### EXP-RGC-01 — Instrument validation before any comparison
- **Gaps:** G1, G2, G5.
- **H1:** The chosen primary metric (debiased CKA on whitened activations, or Procrustes distance)
  (i) is ≈ 0 between independent random matrices at the study's n and d, (ii) ranks known synthetic
  perturbations of equal Frobenius norm correctly (top-PC noise more damaging than isotropic), and
  (iii) separates compressed-vs-parent distance from seed-vs-seed distance on real networks.
  **H0:** Fails any of (i)–(iii).
- **Design:** (i)–(ii) synthetic, as in `sketches/cka_toy.py`, at the real n and d of the probe set.
  (iii) 5 independently seeded ResNet-18 models on CIFAR-10; for each, FP vs INT8 / 4-bit / 3-bit PTQ
  on a fixed 2,000-image probe set, at 4 layers.
- **Pre-registered prediction:** Debiased CKA passes (i)–(ii), and biased CKA fails (i) at n = 50,
  d = 1000. **Falsified (for the chosen metric) if** |debiased CKA| > 0.05 on random pairs, or if it
  doesn't order the synthetic perturbations.
- **Analysis:** Report every metric on every check; choose the primary metric from this experiment only,
  before EXP-RGC-02/03.
- **Tier:** Laptop CPU for (i)–(ii) (seconds); single GPU or a patient CPU for (iii).
- **Would establish:** Which metric is usable at these sizes. **Would not establish:** Anything about H3
  or H5.
- **Sketch:** `sketches/cka_toy.py`.

### EXP-RGC-02 — H3: does error anisotropy predict damage beyond weight/output MSE?
- **Gap:** G3.
- **H1:** Across quantization configurations, the top-k-projected error energy (activation-covariance
  basis) predicts model-level damage better than per-layer weight MSE and output MSE.
  **H0:** No gain in out-of-sample rank correlation.
- **Variables:** Predictors per configuration, aggregated over layers: weight MSE; output MSE; E_top-k =
  ‖P_k(XΔW)‖² / ‖XΔW‖² with P_k from the FP activation covariance (k fixed at 1% of d in advance).
  Outcome: ΔKL to the FP model on held-out text.
- **Design:** One 1B-scale decoder. Configurations: ≥ 60, varying bits (3/4), group size
  (32/64/128/per-channel), method (RTN / AWQ / GPTQ), and which layer types are quantized. Split
  configurations 2:1 into train and held-out, stratified by method.
- **Pre-registered prediction:** On held-out configurations, Spearman(predictor with E_top-k, ΔKL)
  exceeds Spearman(weight MSE, ΔKL) by ≥ 0.1. **Falsified if** the bootstrap 95% CI of the difference
  includes 0.
- **Analysis:** Spearman differences with a paired bootstrap over held-out configurations; a sensitivity
  analysis over k ∈ {0.5, 1, 5}% d, reported but not used for the verdict.
- **Threats:** Method is collinear with anisotropy (AWQ specifically reshapes error), so stratify by
  method and also report within-method correlations.
- **Tier:** Single GPU, about 1 GPU-day (rough).
- **Would establish:** Whether one specific anisotropy statistic is a better damage proxy for one model.
  **Would not establish:** That geometry is the causal mechanism of damage.

### EXP-RGC-03 — H5: behaviour restored, geometry not?
- **Gaps:** G2, G4.
- **H1:** Students distilled to behavioural equivalence (top-1 agreement ≥ 98% with the teacher and
  mean KL ≤ 0.05 on held-out data) have student–teacher geometric distance larger than the
  teacher–teacher seed baseline. **H0:** Student–teacher distance is within the seed-baseline
  distribution.
- **Design:** Teacher: ResNet-18 on CIFAR-100, 5 seeds (the seed baseline). Students: (a) the same
  architecture and (b) a narrower ResNet; logit KD vs relational KD vs CKA-based KD (2401.11824-style),
  3 seeds each. Geometry: the primary metric from EXP-RGC-01 at matched relative depth. Only students
  that meet the behavioural margin enter the geometric comparison.
- **Pre-registered prediction:** Logit-KD students exceed the 95th percentile of the seed baseline in
  distance. A CKA-KD student is closer, which is partly circular because it optimizes the metric; so
  evaluate it on a second, non-optimized metric. **Falsified if** logit-KD student distances fall within
  the seed baseline.
- **Analysis:** Permutation test, student vs seed-baseline distances; report students that fail the
  behavioural margin separately.
- **Threats:** Circularity for metric-optimizing KD (handled above); layer correspondence across
  different widths (use relative depth; report sensitivity).
- **Tier:** Single GPU, about 1–2 GPU-days (rough).
- **Would establish:** H5 for CIFAR-scale CNN distillation under these margins. **Would not establish:**
  The same for LLM distillation, or that geometric differences matter for downstream reuse. That needs a
  transfer test, which is out of scope here.
- **Prior literature, and a discrepancy to resolve:** `research/notes/09` §1.4 summarizes Stanton et al.
  2021 (arXiv:2106.05945, *Does Knowledge Distillation Really Work?*) as "students match predictions,
  diverge in representations". The abstract (checked 2026-11-24) says something different: there
  "often remains a surprisingly large discrepancy between the predictive distributions of the teacher
  and the student", even with enough capacity, and it attributes this to optimization difficulty. The
  abstract doesn't mention representations. Whether the body supports the note's summary is UNCHECKED.
  For this design it matters in one way: if students often fail the behavioural margin, the
  geometric comparison runs on a selected subset. So report how many students pass the margin, and
  treat a low pass rate as a finding in itself.
