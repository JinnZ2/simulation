# Deployment-aware compression metrics — what needs to be known, and experiments (EXP-DCM)

Draft read: `hypotheses/deployment-aware-compression-metrics.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

Charter deliverable (`config/topics.json`, `research/TODO.md` "Minimal reproducible study"): a
**deployment-aware Pareto atlas** with physical cost (bytes, peak memory, median and tail latency,
energy) against functional and representational damage (task score, calibration, geometry). Implied
hypothesis: **nominal compression ratio is a poor proxy for deployed cost, and rankings change across
cost axes and hardware.**

## 1. What the engine claims, and on what evidence

**Headline statement:** "*Information-theoretic Generalization Analysis for Expected Calibration
Error* reports: (no abstract) [restricted: narrower scope … (run 2026-08-17)]". NEW HYPOTHESIS, 11
surviving claims. The headline has no content (E9). It has been reformulated once, and the suffix is the
only scope information (E5).

**Evidence base (AUDIT):** 36 findings (17 Crossref, 16 S2, 3 arXiv); 18 claims; 11 surviving. The
survivors are mostly ECE-methodology papers, some not about ML models at all (*Regression Calibration
for Covariate Measurement Error*; *RegCalReliab*, a CRAN package), plus event-driven edge processors. A
strict compression × cost/calibration co-occurrence screen hits 1/11. **The draft has barely changed:**
in 5 of the last 6 engine commits the body was identical apart from the timestamp line; on 2026-11-19
three claims were added (8 → 11).

**Hidden-variable suspects shown in the draft:** `findings_rate`, r = −0.577, −0.577, −0.959
(2026-08-31 … 2026-09-10). By E7 these correlate claim *i* with month *i mod M*. They are unaligned
series with no significance test, and they don't describe a hidden variable.

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What it shows | Bearing |
|---|---|---|---|
| Quantized Can Still Be Calibrated…, DOI 10.18653/v1/2025.acl-long.1473 (escape-hatched) | Yes (Crossref: ACL 2025 long; no abstract in Crossref) | Title implies a framework for calibration of quantized LLMs. | Directly on the calibration arm; content UNCHECKED; dropped by the engine. |
| Robust and Trustworthy TinyML-Based EEG Seizure Detection with Quantized Inference, DOI 10.1109/NewCAS64543.2026.11673986 | Yes (NEWCAS 2026) | First sentence: confidence estimates under quantized inference. | On-topic (calibration under quantization, MCU); results UNCHECKED. |
| SMECE, arXiv:2603.14092 | Yes | ECE "commits a category error" when labels are themselves probabilities; proposes a soft-label ECE. | Calibration-metric methodology; relevant to G4. |
| Understanding Model Calibration…, arXiv:2501.19047 | Yes | Introductory blog post on ECE and its drawbacks. | Background. |
| KV Pareto, arXiv:2512.01953 (finding, not a survivor) | Yes | Maps the memory vs accuracy frontier across KV-cache quantization, chunked prefill and weight quantization for edge deployment. | Directly on the atlas idea; not among the survivors. |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- 18 escape-hatched claims, the most of any topic relative to size (18 of 36 findings). They include
  *Accuracy-Latency Trade-offs Under Neural Network Compression in Safety-Critical Edge AI…* and
  *On-Device LLMs … Systematic Survey of Compression, Runtime Efficiency…* (contents UNCHECKED). The
  on-topic literature ends up in the unknown journal, not the hypothesis.
- The `findings_rate` suspects (artefactual; see above).

### (b) Gaps identified here
- **G1. Measuring cost.** Energy: RAPL covers CPU/DRAM only; NVML polling undersamples short bursts;
  idle power must be subtracted; prefill and decode must be separated (all per `research/notes/09`
  §1.4; not independently re-checked here). Bytes must include scales, zero-points, sparse indices and
  runtime metadata. Latency must state batch size, sequence length, threads and hardware.
- **G2. Front stability.** Pareto-front membership is a statistic of noisy measurements. A method can be
  "on the front" because of one fast session. Membership needs a probability, not a yes/no.
- **G3. Nominal vs measured.** The implied hypothesis (nominal ratio ≠ deployed cost) needs a predictive
  test: how well does nominal bits × params rank-predict measured latency, energy and peak memory?
- **G4. Calibration under compression.** Whether compression changes calibration by more than estimator
  noise depends on sample size and on the estimator (binning ECE vs Brier vs NLL). `sketches/calibration_toy.py`
  shows, on synthetic data, that binned ECE is biased upward at small n (it overstates the known true
  error at n = 100 and converges by n ≈ 5,000) and that its replicate spread at n = 100–300 is several
  hundredths. Whether that matters depends on the effect sizes in the real comparison, which this file
  doesn't assume. That's a simulation property, not a finding about any model.
- **G5. Cross-hardware transfer.** An atlas measured on one device may not transfer. Rank stability
  across devices is itself an open empirical question.

## 3. Experiments

### EXP-DCM-01 — Does nominal compression predict measured cost?
- **Gaps:** G1, G3.
- **H1:** Across ≥ 12 compressed variants of one model, Spearman(nominal compression ratio, measured
  decode latency) < 0.5 on at least one of two hardware targets. **H0:** ρ ≥ 0.5 on both.
- **Variables:** Nominal ratio = FP16 bytes / (nominal bits × params / 8). Measured: serialized bytes,
  peak resident memory, p50 and p95 decode latency per token (batch 1 and 8, 512-token context),
  energy per token (idle-subtracted; RAPL on CPU, NVML on GPU, sampling rate recorded).
- **Design:** One 1B-scale LLM; variants: FP16, INT8, 4-bit (2 methods), 3-bit, 2:4, unstructured 50%,
  structured 25%/50%, low-rank 50%, plus two hybrids, for ≥ 12 in total. Hardware: one x86 CPU and one
  GPU. 3 sessions × ≥ 50 timed repeats per variant.
- **Pre-registered prediction:** ρ < 0.5 on CPU (unstructured and low-bit variants without kernel
  support break the ordering). **Falsified if** ρ ≥ 0.5 on both targets with the CI lower bound > 0.3.
- **Analysis:** Spearman with a session-level bootstrap; also report the full measured table.
- **Threats:** Kernel availability decides the result. That's the point, but record library versions;
  thermal drift (interleave variants within a session).
- **Tier:** Single GPU + laptop CPU, about 1 day of wall time (rough). The harness skeleton is
  `sketches/latency_harness.py`.
- **Would establish:** For one model and two devices, how far nominal ratio misranks deployed cost.
  **Would not establish:** A general law.

### EXP-DCM-02 — Does quantization change calibration beyond estimator noise?
- **Gap:** G4.
- **H1:** At 3-bit, Brier score (primary; ECE secondary) on multiple-choice QA rises over FP16 by more
  than the bootstrap 95% CI half-width. 4-bit and 8-bit don't. **H0:** No bit-width differs from FP16
  beyond the CI.
- **Variables:** Confidence = softmax probability over answer options; correctness. Brier, NLL, 15-bin
  equal-mass ECE, and ECE with a bootstrap CI.
- **Design:** 2 open 1–3B models × {FP16, W8, W4-AWQ, W4-GPTQ, W3}. Benchmarks with ≥ 5,000 items in
  total (e.g. MMLU test + ARC-Challenge). n is chosen so that the CI half-width on Brier is ≤ 0.005,
  sized with `sketches/calibration_toy.py` and then confirmed on FP16 bootstrap. Same prompts and
  answer extraction for every arm.
- **Pre-registered prediction:** As H1. **Falsified if** W3's Brier increase is within the CI, or if W8
  differs from FP16 beyond the CI (that would point to an implementation problem, so stop and debug,
  without interpreting it).
- **Analysis:** Paired bootstrap over items (same items across arms); report all three estimators;
  draw conclusions from the pre-registered primary metric only.
- **Threats:** Accuracy changes drive Brier; report the accuracy–calibration decomposition (Brier =
  reliability − resolution + uncertainty). Multiple-choice probability isn't verbalized confidence (see
  EXP-CAL-02).
- **Tier:** Single GPU, under 1 GPU-day (rough).
- **Would establish:** Whether calibration shift is detectable at these bit-widths at this n.
  **Would not establish:** Calibration of generative, free-form outputs.

### EXP-DCM-03 — Cross-hardware rank stability of the atlas
- **Gaps:** G2, G5.
- **H1:** Kendall τ between method rankings by p50 latency on device A and device B is < 0.6 for at
  least one pair among {x86 laptop, ARM SBC, consumer GPU}. **H0:** τ ≥ 0.6 for all pairs.
- **Design:** The same variant set as EXP-DCM-01, restricted to formats each device can run (record
  exclusions; don't impute). Front-membership probability per variant per device from 1,000 bootstrap
  resamples of the session-level measurements.
- **Pre-registered prediction:** τ(laptop CPU, GPU) < 0.6. **Falsified if** every pair has τ ≥ 0.6 with
  the CI lower bound > 0.4.
- **Analysis:** Kendall τ with a bootstrap CI; front-membership probabilities reported as a table.
- **Threats:** Device availability; runtime differences (llama.cpp vs PyTorch) are confounded with the
  device unless the runtime is held fixed where possible.
- **Tier:** Field / edge devices (ARM board) + laptop + single GPU.
- **Would establish:** Whether one atlas can serve several devices. **Would not establish:** Rankings on
  devices not measured.
