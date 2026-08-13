# TODO — Neural-Network Compression as an Empirical Research Program

Status: open / not started. This is a research charter, not a backlog of chores.

## Framing

Treat NN compression as a **multi-objective constrained optimization problem**: preserve task
behavior while reducing storage, memory bandwidth, latency, energy, and possibly adaptation cost.
Not as a catalog of tricks.

**Starting hypothesis:** the most effective compression depends more on
*architecture–hardware–workload coupling* than on any universally best algorithm. One comparative
study found VGG16 favored pruning while ResNets were more amenable to quantization. [ieee]

The standard taxonomy — pruning, quantization, low-rank decomposition, distillation — is best read
as **complementary rather than competing** choices. [nih +1]

---

## Do not collapse "compression ratio" into performance

Measure at minimum:

- [ ] **Checkpoint size** — bytes on disk, *including* scales, zero-points, sparse indices, runtime metadata.
- [ ] **Peak RAM/VRAM** — deployment feasibility gate.
- [ ] **Latency and throughput** — median *and* tail, at a stated batch size, sequence length, hardware target.
- [ ] **Energy per inference** — decisive for edge / continuous operation.
- [ ] **Task retention** — accuracy/F1 for classifiers; perplexity + downstream/behavioral eval for LMs.
- [ ] **Robustness retention** — distribution shift, rare classes, long contexts, adversarial/noisy input.
- [ ] **Training/compression cost** — GPU-hours, calibration-set size, fine-tuning epochs.

Why this matters: a 4-bit weight representation nominally gives 8× reduction from FP32 yet may give
little speedup when dequantization and memory layout dominate. Conversely, structured channel
pruning can cut nominal FLOPs less dramatically while running substantially faster on ordinary
dense hardware.

---

## Anchor papers (initial backbone for transformer/LLM work)

- [ ] **GPTQ** — one-shot, approximate second-order, weight-only post-training quantization.
      Reported 175B GPT quantized to 3–4 bits/weight in ~4 GPU-hours with negligible reported
      degradation. [arxiv +1]
- [ ] **AWQ** — activation-aware, hardware-oriented weight quantization. Central result: a small
      fraction of salient weights matters disproportionately; uses activation-informed per-channel
      scaling rather than weight magnitude alone. [arxiv +1]
- [ ] **SparseGPT** — one-shot pruning for very large GPT-family models. Reported ≥50% sparsity
      without retraining and minimal loss; later reporting describes 50–60% unstructured sparsity
      on OPT-175B and BLOOM-176B. [arxiv +2]
- [ ] **Compression order (2026)** — composite compression tends to work better when
      lower-perturbation operations precede stronger ones. Argues for explicitly testing
      Q→P vs P→Q rather than assuming order is irrelevant. [openreview]
- [ ] **Low-rank / structured pruning for CNNs and sensor models** — low-rank work formulates the
      question as finding each layer's *lowest acceptable rank under a performance constraint*,
      which aligns with a geometric / information-preservation framing. [berkeley]

---

## Proposed research matrix

Focus on whether a method **preserves functional subspaces**, not merely scalar accuracy.

### Base models (at least one per category)

- [ ] CNN: ResNet-18 or MobileNetV3
- [ ] Transformer encoder: a small BERT-like model
- [ ] Decoder LLM: a 1–8B open-weight model that fits available hardware
- [ ] Optional: a recurrent / world-model or JEPA-like predictive encoder, where representation
      geometry is central

### Compression arms

Hold **base model, task, dataset split, hardware, runtime, and measurement harness fixed.**

1. [ ] FP16/BF16 baseline
2. [ ] INT8 post-training quantization
3. [ ] 4-bit weight-only quantization
4. [ ] Unstructured magnitude pruning
5. [ ] Structured channel/head/block pruning
6. [ ] Low-rank replacement with a layerwise rank budget
7. [ ] Distilled student at matched parameter or latency budget
8. [ ] Hybrids: prune → quantize, quantize → prune, factorize → quantize

### Evaluation probes (beyond standard task scores)

- [ ] **CKA or SVCCA** between baseline and compressed hidden states
- [ ] **Layerwise activation covariance spectra** and effective rank
- [ ] **Calibration** — ECE, Brier score
- [ ] **Error-set overlap** — are compressed-model errors merely more frequent, or *qualitatively different*?
- [ ] **Stability** under input perturbation and distribution shift
- [ ] **Generative-specific** — token-level divergence, prompt-level response agreement, long-context
      degradation, tool/function-call reliability

Goal: answer *"which compression preserves the model's internal organization?"* rather than
*"which one retains benchmark score?"*

---

## High-value hypotheses

1. [ ] **Activation-informed schemes outperform weight-only heuristics at equal bit budgets.**
       AWQ's finding that a small set of weights carries disproportionate activation-level
       importance supports this. [mit]
2. [ ] **Structured sparsity wins in real latency only when it matches the accelerator/runtime.**
       Unstructured pruning may produce excellent zero counts but limited practical acceleration on
       standard dense kernels.
3. [ ] **Quantization error is anisotropic in representation space.** Sensitive channels and outlier
       dimensions likely matter more than average per-layer MSE suggests — making spectral and
       geometric metrics potentially more predictive than weight reconstruction error.
4. [ ] **Compression composition is noncommutative.** Measure `C₂(C₁(M)) ≠ C₁(C₂(M))`, especially for
       pruning and low-bit quantization. The emerging sequencing result makes this experimentally
       timely. [openreview]
5. [ ] **Distillation may restore behavior, not internal geometry.** A student can match labels or
       logits while learning a materially different latent topology — important if the model is used
       as a reusable predictive substrate rather than a single-task classifier.

---

## Minimal reproducible study (first paper-quality experiment)

- **Question:** At matched memory budgets, does activation-aware 4-bit quantization preserve task
  behavior *and* hidden-state geometry better than pruning or low-rank compression?
- **Models:** ResNet-18 and one small decoder transformer.
- **Budgets:** 50%, 25%, 12.5% of baseline model-storage footprint.
- **Methods:** INT8 PTQ; GPTQ/AWQ-style 4-bit; structured pruning; unstructured pruning;
  truncated-SVD / low-rank.
- **Outcomes:** task score, ECE, median/p95 latency, peak memory, joules/inference if measurable,
  CKA, effective-rank shift, perturbation robustness.
- **Analysis:** **Pareto fronts**, not a single winner — accuracy vs bytes, latency, energy.

**Key deliverable:** a *deployment-aware Pareto atlas* — each method represented by its physical
cost and its functional/representational damage. More useful than another leaderboard based solely
on parameter count.

---

## Reference tables

### What each method removes or changes

| Method | What it removes or changes |
| --- | --- |
| Quantization | Bits per weight, activation cache value |
| Pruning | Weights, channels, blocks |
| Low-rank factorization | Effective rank of matrix |
| Knowledge distillation | Student-model capacity |
| Architecture redesign / NAS | The computational graph |
| Entropy coding | Redundancy in storage |

### Primary benefit by method

*Transcribed as given; the sparsification rows below are inconsistent in the source and need a pass
to reconcile axis (what is sparsified) against benefit before this table is used for planning.*

| Compression method | Primary benefit |
| --- | --- |
| Quantization | Usually the most direct memory-bandwidth win |
| Sparsification — KV | Can reduce compute and memory bandwidth |
| Sparsification — heads, layers | Reduces dense linear-layer parameters and FLOPs |
| Sparsification — matrices/tensors | Can produce a genuinely sparse dense model |
| Sparsification — capacity | Often gives real deployment gains |
| Sparsification — spatial graph itself | Additional disk-size reduction |
| Sparsification — stored values | *(no benefit listed in source)* |

---

## Session log (carried over)

### Phase 6 — Integration folder + NN/manifold/language research (2026-08-13)

Input: memo on NN compression as an empirical research program (taxonomy, metrics, GPTQ/AWQ/SparseGPT
backbone, research matrix, Pareto atlas). Request: deep research into neural networks, manifold
possibilities, code languages needed, perceptron integration theories + the memo; deliver a new
folder of possible integration points across all repos worked on.

**Stage 1 — parallel research (4 explore subagents)**
- R1 — NN compression science: verify/expand memo (GPTQ, AWQ, SparseGPT, order effects, CKA/SVCCA,
  effective rank, ECE, Pareto methodology); add 2024–2026 developments.
- R2 — Manifold possibilities: manifold hypothesis, intrinsic dimension, information geometry, NTK,
  representation topology, geometric deep learning; what "preserving functional subspaces" means
  formally.
- R3 — Perceptron & integration theories: perceptron convergence, MLP expressivity, signal
  integration theories (IIT, global workspace, predictive processing, Conant–Ashby), multi-substrate
  sensor integration theory.
- R4 — Code languages: given the stdlib-only Python ethos of the JinnZ2 ecosystem — when to stay
  pure-Python vs C/Rust/Julia/WASM/Mojo; embedded (MicroPython/C); accelerator stacks;
  interoperability patterns (FFI, WASM, IPC/CSV streams).

**Stage 2 — synthesis (orchestrator)**
- `notes/09_nn_compression_manifolds.md` (R1+R2 merged)
- `notes/10_integration_theories_languages.md` (R3+R4 merged)
- `integration/INTEGRATION_POINTS.md` — cross-repo integration matrix across
  curly-octo-happiness, hypothesis-engine, Geometric-to-Binary-Computational-Bridge,
  Mathematical-collapse-prevention-model, Cross-Domain-Toolkit + the new research.

### Phase 7 — Meta-structures / parallel processing / geometric overlays / consciousness & biological intelligence (2026-08-13)

**Stage 1 — parallel research (4 explore subagents)**
- R1 — Meta-structures & meta-meta integration: meta-learning (MAML), hypernetworks, meta-materials,
  meta-languages/grammars, sheaf/category theory of structures, hierarchical abstraction ladders;
  what "structure on structures" means formally; integration schemes across levels.
- R2 — Parallel processing & geometric overlays: parallel computing paradigms (SIMD, dataflow, actor,
  cellular automata, neuromorphic), compositional semantics; geometric overlays as fiber bundles,
  sheaf neural networks, graph coverings, multi-view geometry, layered field overlays
  (EM + chemical + mechanical fields on one substrate).
- R3 — Consciousness studies, 2024–2026 state of the art: theories landscape post-Cogitate
  (IIT / GNW / HOT / FEP / active inference / predictive processing), structural and functional
  correlates, machine-consciousness assessments (Butlin et al. 2023, AI consciousness reports 2025),
  testable markers.
- R4 — Biological intelligences beyond brains: slime molds, plant signaling, immune computation,
  bacterial quorum sensing, xenobots/anthrobots, morphogenesis and bioelectricity (Levin), octopus
  distributed cognition, fungal networks; minimal cognition; what compute paradigm each suggests.

**Stage 2 — synthesis (orchestrator)**
- `notes/11_meta_structures_consciousness_bio_intelligence.md`
- `integration/EXPLORE_AND_EXPERIMENT.md` — pattern-intersection questions + concrete experiment
  list tied to the ecosystem repos.

---

## Open items before starting

- [ ] Resolve the bracketed citations (`[ieee]`, `[nih]`, `[arxiv]`, `[openreview]`, `[mit]`,
      `[berkeley]`) into full references.
- [ ] Reconcile the sparsification rows in the "Primary benefit" table.
- [ ] Decide the hardware target(s) — the coupling hypothesis makes this a first-class experimental
      variable, not an implementation detail.
- [ ] Fix the measurement harness *before* running any arm; every number above is only comparable
      if the harness is held constant.
