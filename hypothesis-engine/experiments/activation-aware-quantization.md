# Activation-aware quantization — what needs to be known, and experiments (EXP-AAQ)

Draft read: `hypotheses/activation-aware-quantization.md` at `0419d4791de3e80afd5b028e27475977dce89cd4`
(regenerated 2026-11-23T17:01:48Z). Written 2026-11-24. All experiments PROPOSED.
Cross-cutting engine gaps E1–E9 and EXP-ENG-* are in [engine-validity.md](engine-validity.md).

Charter hypothesis this topic feeds (`config/topics.json`, `research/TODO.md` #1): **H1 — at equal bit
budgets, activation-informed quantization schemes beat weight-only heuristics.**

## 1. What the engine claims, and on what evidence

**Headline statement:** "On topic activation-aware quantization, *Compressive Domains and a Bound for the
Number of Components of the Fixed Locus of a Self-Map of the Berkovich Line* reports: We introduce the
notion of a 'compressive domain' …". Status NEW HYPOTHESIS, 135 surviving claims.

**What that statement is:** The first sentence of a non-archimedean dynamics paper, chosen as headline
because it is the first surviving claim in tree order. It isn't a claim about quantization, and it isn't
a hypothesis.

**Evidence base (AUDIT, `sketches/engine_audit.py`):** 154 findings (135 arXiv, 19 Semantic Scholar);
142 claims; 135 surviving (123 from arXiv). A lexical core-term screen
(`quantiz|PTQ|AWQ|GPTQ|low-bit|int4|int8|fp4`) hits 26/135 surviving claims and 14/123 arXiv survivors.
That screen is lexical too. Human relevance is EXP-ENG-01. The "(0.80)–(0.91)" numbers are Laplace-smoothed
counts of lexical matches (E8). No supporting claim states an effect size; the claims are first sentences (E1).

**Source spot-checks** (metadata and abstract read on 2026-11-24 from the arXiv API / Crossref; anything
beyond the abstract is UNCHECKED):

| Cited as | Exists? | What the abstract shows | Bearing on H1 |
|---|---|---|---|
| AWQ, arXiv:2306.00978 (Lin et al.) | Yes, v6 | Claims that protecting ~1% of salient weights reduces quantization error; salient channels should be found from the **activation** distribution, not weights; per-channel scaling; no backprop or reconstruction, "so it generalizes to different domains"; TinyChat >3× speedup over HF FP16. | Direct, but it's the method's own claim. The engine staked it as "(no abstract)" (S2 copy, 0.67) and via the GetMobile reprint, DOI 10.1145/3714983.3714987 (Crossref: GetMobile, 2025-01-20). |
| KronQ, arXiv:2607.07964 | Yes, v2 | Says second-order PTQ (incl. GPTQ) builds objectives from **input activation** statistics and adds gradient covariance (Kronecker-factored Hessian). | Relevant to the taxonomy problem (G2): GPTQ is "weight-only" in output format but activation-informed in objective. |
| Quamba2, arXiv:2503.22879 | Yes, v4 | PTQ framework for selective SSMs; W4A8 etc. | Scope extension (SSMs); results beyond the abstract UNCHECKED. |
| PTQ4DiT, arXiv:2405.16005 | Yes, v3 | PTQ for diffusion transformers. | Scope extension; results UNCHECKED. |
| Headline: arXiv:2608.14545 (Faber, Patra) | Yes | Fixed points of rational maps on the Berkovich line. | None. It entered through E2 (matched one query word). |
| arXiv:2610.37645 (Multi-State Linear Attention), top-ranked (0.91) | Yes | Linear attention routing. | None for H1. |

**Recorded by the engine as unknown (escape-hatched, so removed from the tree):** ORQ-ViT, *AAAC:
Activation-Aware Adaptive Codebooks for 4-bit LLM Weight Quantization*, *G²PTQ*/*G2PTQ*
(the same paper staked twice under two spellings), and others. These are among the most on-topic items
the engine saw, and it dropped them because of lexical failures (E3, E5). Existence: UNCHECKED.

## 2. What science needs to be known

### (a) Gaps the engine recorded
- No refuted claims and no hidden-variable suspects for this topic. Neither result is informative
  (E3, E7).
- Escape-hatched on-topic papers (above): unresolved, and dropped rather than tested.

### (b) Gaps identified here
- **G1. "Equal bit budget" isn't defined.** Group size, scales and zero-points, mixed-precision outlier
  storage and codebooks change the effective bits per weight. A 4-bit g128 scheme with FP16 scales is
  about 4.125 b/w for scales alone (16/128); with zero-points it's more. Comparisons have to be at
  matched **effective** bits counted from the serialized checkpoint, not nominal bits.
- **G2. The arms aren't classified.** "Weight-only" describes the stored format (AWQ is weight-only
  storage), whereas "activation-informed" describes how the quantizer is chosen. GPTQ uses the
  activation Gram matrix XᵀX (KronQ's abstract says this explicitly). H1 needs a contrast fixed in
  advance: **data-free** (RTN; others such as HQQ, whose data-free status is UNCHECKED) vs
  **activation-statistics-informed** (AWQ, GPTQ, SmoothQuant-style).
- **G3. Mechanism vs side effect.** If AWQ wins, is it because of activation *magnitude* specifically,
  or because any per-channel rescaling with the right spread changes rounding? A permuted-statistics
  control is needed.
- **G4. Calibration-data dependence.** AWQ's abstract claims domain generalization because it uses no
  reconstruction. That's a testable comparative claim against GPTQ under calibration/evaluation domain
  mismatch, and it is UNCHECKED here.
- **G5. Sources of variance.** PTQ is deterministic given a calibration subset. The honest seed is the
  calibration-sample draw, not a training seed. Effects at 4-bit are often small, so without a seed
  distribution a "win" can't be told apart from sampling noise.
- **G6. Rotation confound.** Rotation methods (QuaRot, SpinQuant; IDs per `research/notes/09`, not
  re-checked here) reduce outliers without activation-dependent scaling. If a random Hadamard rotation
  plus RTN matches AWQ, "activation-informed" isn't the operative variable.
- **G7. Metric choice.** Perplexity, KL to the FP16 model, and downstream accuracy can rank methods
  differently. Choose a primary metric in advance.

## 3. Experiments

### EXP-AAQ-01 — Data-free vs activation-informed at matched effective bits
- **Gaps:** G1, G2, G5, G7.
- **H1:** At matched effective bits per weight, activation-informed methods (AWQ, GPTQ) give lower
  token-level KL to the FP16 model than data-free methods (RTN, plus one more data-free method
  confirmed as such before the run). **H0:** No difference beyond calibration-draw variance.
- **Variables:** Primary: mean per-token KL(FP16 ‖ quantized) on 2M held-out WikiText-2 / C4-val
  tokens. Secondary: perplexity; zero-shot ARC-e, PIQA, HellaSwag, WinoGrande (lm-eval-harness).
  Effective bits = serialized checkpoint bytes × 8 / number of quantized weights.
- **Design:** Models: 3 open families at ≤ 1.5B (e.g. Pythia-1.4B, Qwen2.5-1.5B, Llama-3.2-1B; check
  licences). Bits: 3 and 4; group size 128; match effective bits within ±0.05 b/w, adjusting group size
  if needed. Calibration: 128 × 2048-token sequences from C4-train, 5 independent draws (seeds 0–4).
  Data-free methods get the same 5 "draws" (identical results; this keeps the design balanced).
  Total cells: 3 models × 2 bit-widths × 4 methods × 5 draws = 120 quantizations.
- **Pre-registered prediction:** Activation-informed beats data-free at 3-bit in all 3 models, and at
  4-bit in ≥ 2 of 3. In each case the 5-draw mean difference is larger than 2 × the pooled draw SD.
  **Falsified if** a data-free method is within 1 draw-SD of or better than the best activation-informed
  method in ≥ 3 of 6 model × bit cells.
- **Analysis:** Paired by model × bit. Linear mixed model KL ~ method_class × bits + (1 | model) +
  (1 | draw); report the method-class effect with a 95% CI. A sign test over cells as the robust check.
  Report every cell, not only the winners.
- **Threats:** Implementation quality (use reference implementations at pinned commits); kernel
  differences don't matter here because this is accuracy only; tokenizer differences across families
  (compare within model only).
- **Tier:** Single GPU (24–80 GB). Quantization takes minutes per model at this size; evaluation
  dominates, roughly 1–3 GPU-days in total. That's a rough estimate, not measured.
- **Would establish:** Whether H1 holds for small decoder LMs at 3/4-bit under this accounting.
  **Would not establish:** Behaviour at 7B+ (outlier structure is known to change with scale; UNCHECKED
  here), at W4A4 or KV-cache quantization, or anything about latency.

### EXP-AAQ-02 — Mechanism ablation: is it the activation statistics?
- **Gaps:** G3, G6.
- **H1:** AWQ-style scaling from the true per-channel activation magnitudes reduces output error more
  than the same scaling with channel-permuted statistics, weight-norm-derived statistics, or a random
  orthogonal (Hadamard) rotation + RTN. **H0:** Permuted or rotation arms are within noise of the
  true-statistics arm.
- **Variables:** Layer-wise relative output MSE ‖XW − XQ(W)‖² / ‖XW‖² on held-out activations
  (primary, cheap), and model-level KL as in EXP-AAQ-01 for the winning arms.
- **Design:** Arms: RTN; AWQ (true |x̄_j|^α, α grid-searched on a calibration split); AWQ with the
  |x̄| vector randomly permuted across channels (same spread, wrong assignment); weight-norm scaling
  (|W| column means^α); random Hadamard + RTN; Hadamard + AWQ. Pilot on synthetic layers
  (`sketches/awq_toy.py`, 10 seeds), then real layers from one 1B model: all linear layers, 5
  calibration draws.
- **Pre-registered prediction:** true-statistics < permuted ≈ weight-norm ≈ RTN on output MSE, in ≥ 80%
  of layers. Hadamard + RTN is somewhere between AWQ and RTN. **Falsified if** the permuted arm matches
  the true arm (median per-layer ratio within [0.95, 1.05]); then the gain is spread-induced, not
  activation-specific.
- **Analysis:** Per-layer ratios vs AWQ; Wilcoxon signed-rank across layers; report the distribution,
  not just the median.
- **Threats:** The α grid search is fit on calibration data. Score on a disjoint split, which the sketch
  does. Layer-wise MSE may not predict model-level damage; that's what EXP-RGC-02 tests.
- **Tier:** Pilot: laptop CPU (seconds). Real: single GPU, hours.
- **Would establish:** Whether activation magnitude, as opposed to rescaling per se or outlier removal
  per se, carries the benefit. **Would not establish:** That AWQ's particular scaling law is optimal.
- **Sketch:** `sketches/awq_toy.py` (synthetic outlier channels; arms rtn / wscale / awq_like /
  rand_scale). Its output is a harness check, not evidence about LLM layers.

### EXP-AAQ-03 — Calibration-domain mismatch: AWQ vs GPTQ
- **Gap:** G4.
- **H1 (the claim from AWQ's abstract):** Under calibration/evaluation domain mismatch, GPTQ degrades
  more than AWQ. **H0:** The degradation is equal within noise, or AWQ degrades more.
- **Design:** 2 models (≤ 1.5B), 3-bit and 4-bit. Calibration domains: C4 prose, code (an
  open-licensed code corpus), math (GSM8K train questions). Evaluation domains: the same three. A full
  3 × 3 domain grid × 2 methods × 5 calibration draws.
- **Variables:** Mismatch penalty = KL(eval domain | calibrated off-domain) − KL(eval domain |
  calibrated on-domain).
- **Pre-registered prediction:** GPTQ's mean mismatch penalty is larger than AWQ's in ≥ 4 of 6
  off-diagonal cells per model. **Falsified if** AWQ's penalty is ≥ GPTQ's in ≥ 3 of 6 cells for both
  models.
- **Analysis:** Mixed model penalty ~ method × (cal, eval) + (1 | draw); report the interaction.
- **Threats:** Corpus size and sequence length must be matched across calibration domains; tokenizer
  efficiency differs across domains (compare KL per token within domain only).
- **Tier:** Single GPU, about 1 GPU-day (rough).
- **Would establish:** Whether one claimed advantage of AWQ replicates on small models.
  **Would not establish:** Anything about domains not tested.
