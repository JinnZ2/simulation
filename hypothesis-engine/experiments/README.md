# Experiments for the hypothesis-engine drafts

Written 2026-11-24, against `main` at **`0419d4791de3e80afd5b028e27475977dce89cd4`**
("chore(engine): research digest 2026-11-23"; drafts regenerated 2026-11-23T17:01:48Z). Engine scripts
last changed in `0e1b4a5` (2026-09-06).

This directory is hand-written. It doesn't modify the engine's generated files (`hypotheses/`, `data/`,
`engine_report.md`), its config, or its scripts. The sketches read engine data and import the engine
module read-only.

**Status of everything here: PROPOSED.** Nothing has been run at the scale described. No result is
reported. Sketch outputs are synthetic and serve only to check harnesses and size samples.

## How to read these files

Each topic file has: (1) what the engine claims and on what evidence, with a source spot-check table;
(2a) gaps the engine recorded; (2b) gaps identified here; (3) falsifiable experiments with a null,
variables, design, pre-registered prediction and falsifier, analysis, threats, cost tier, and what a
result would and wouldn't establish.

Statements are tagged by kind where it matters: **CODE** (read from the engine source), **AUDIT**
(counted from `data/` at the commit above), **LIVE-CHECK** (an API call made on 2026-11-24), and
**UNCHECKED**. Agreement between a sketch and a prediction is a numerical check of a toy, not empirical
support.

Start with [engine-validity.md](engine-validity.md). Its gaps (E1–E9) apply to every topic: in short,
"surviving claims" are first sentences of abstracts, retrieved by an OR-of-words arXiv query, that
survived a token-overlap test which only ever accumulates passes. Each topic's survivors therefore
come mostly from lexical matching rather than measurement. Most headline statements are off topic
(e.g. CAL: *Blazar Boosted Dark Matter in IceCube*; WMC: a rhombohedral-graphene paper).

## Index

| Topic | Gaps | Experiments | Feasibility tier | Status |
|---|---|---|---|---|
| [Engine validity (cross-cutting)](engine-validity.md) | E1–E9 | EXP-ENG-01 human relevance/support audit · EXP-ENG-02 corroboration vs human-judged support · EXP-ENG-03 retrieval query-syntax ablation · EXP-ENG-04 replay of NEW HYPOTHESIS vs new content | Laptop (+ person-hours for 01; network for 03) | PROPOSED |
| [Activation-aware quantization](activation-aware-quantization.md) (H1) | G1–G7 | EXP-AAQ-01 data-free vs activation-informed at matched effective bits · EXP-AAQ-02 mechanism ablation (permuted stats, rotation) · EXP-AAQ-03 calibration-domain mismatch AWQ vs GPTQ | Single GPU (02 pilot: laptop) | PROPOSED |
| [Structured sparsity and hardware-matched pruning](structured-sparsity-and-hardware-matched-pruning.md) (H2) | G1–G5 | EXP-SSP-01 kernel factorial format × runtime × shape · EXP-SSP-02 end-to-end at matched quality | Laptop CPU + single GPU | PROPOSED |
| [Compression composition and ordering](compression-composition-and-ordering.md) (H4) | G1–G5 | EXP-CCO-01 order effect vs seed noise with an equivalence margin · EXP-CCO-02 out-of-sample test of the Progressive Intensity Hypothesis | Laptop pilot; single GPU | PROPOSED |
| [Representation geometry under compression](representation-geometry-under-compression.md) (H3/H5) | G1–G5 | EXP-RGC-01 instrument validation incl. seed null · EXP-RGC-02 error anisotropy vs weight MSE as damage predictor · EXP-RGC-03 distillation: behaviour vs geometry against a seed baseline | Laptop (01); single GPU | PROPOSED |
| [Deployment-aware compression metrics](deployment-aware-compression-metrics.md) (atlas) | G1–G5 | EXP-DCM-01 nominal ratio vs measured cost · EXP-DCM-02 calibration shift under quantization vs estimator noise · EXP-DCM-03 cross-hardware rank stability | Laptop + single GPU; field/edge (03) | PROPOSED |
| [Calibration and falsifiability of LLM agents](calibration-and-falsifiability-of-llm-agents.md) | G1–G5 | EXP-CAL-01 calibration of the engine's own `beta_confidence` · EXP-CAL-02 elicitation method × metric · EXP-CAL-03 "state a falsification condition" intervention with placebo arm | Laptop + labelling (01); single GPU | PROPOSED |
| [Hidden-variable detection / causal discovery from residuals](hidden-variable-detection-causal-discovery-from-residuals.md) | G1–G5 | EXP-HVD-01 operating characteristics of the engine's rule · EXP-HVD-02 residual screening vs LPCMCI · EXP-HVD-03 planted-signal recovery on a copy of engine data | Laptop CPU | PROPOSED |
| [World models and curiosity-driven learning](world-models-and-curiosity-driven-learning.md) | G1–G5 | EXP-WMC-01 noisy-TV susceptibility across bonus families · EXP-WMC-02 one-step model accuracy vs planning return | Laptop pilot; single GPU | PROPOSED |

Totals: 9 files, 51 gaps (9 cross-cutting + 42 topic-specific), 25 experiments.

## Which topics actually changed (the 30 open "NEW HYPOTHESIS" issues)

The engine has opened a "new hypotheses" issue on every run since 2026-08-17 (30 open, #4 to #42). By
construction (E6, CODE) the marker fires for every topic with ≥ 3 survivors, whether or not anything
changed. Counted with `sketches/engine_audit.py churn 6` over the last six engine commits touching
`hypotheses/` (`63b0660` 11-05, `697756b` 11-09, `9a4af0e` 11-12, `4b4247c` 11-16, `24b0f14` 11-19,
`0419d47` 11-23). Entries are new supporting-claim URLs per run → surviving count at 11-23:

| Topic | New supporting claims per run (11-05 … 11-23) | Surviving | Verdict |
|---|---|---|---|
| Activation-aware quantization | +7, +4, +7, +7, +4, +7 | 135 | Grows every run |
| Calibration of LLM agents | +4, +12, +6, +7, +8, +9 | 208 | Grows every run |
| Structured sparsity | +2, +4, +4, +3, +9, +5 | 126 | Grows every run |
| World models / curiosity | +4, +1, +1, +4, +57, +6 | 111 | Grows; the only topic whose headline changed (11-05, 11-19) |
| Hidden-variable detection | +0, +3, +1, +2, +4, +0 | 44 | Slow; 11-05 identical except timestamp, 11-23 only a rescore |
| Compression ordering | +2, +2, +2, +1, +1, +0 | 49 | Slow; 11-23 only a rescore |
| Deployment-aware metrics | +0, +0, +0, +0, +3, +0 | 11 | Re-reported unchanged in 5 of 6 runs (body identical except timestamp) |
| Representation geometry | +0 in all 6 | 7 | Re-reported unchanged: no new claim in 6 runs; identical body in 4 of 6, the rest only unknown-list additions |

No supporting claim was removed in any of these runs, and no claim in any topic is refuted. "Changed
content" here means new or re-ordered lexical matches. It doesn't mean new evidence on the topic's
question (see EXP-ENG-01). EXP-ENG-04 turns this note into a replay test.

## Highest-value cheap experiments

1. **EXP-ENG-01**, human relevance and support audit (laptop + about 8–12 person-hours). Everything
   built on the drafts depends on whether survivors are on topic and supported. It also supplies the
   labels for EXP-ENG-02 and EXP-CAL-01.
2. **EXP-ENG-04**, NEW HYPOTHESIS replay (laptop, minutes). It explains the 30 repeated issues and
   gives a concrete test for any fix to the marker.
3. **EXP-HVD-01**, operating characteristics of the engine's hidden-variable rule (laptop, minutes).
   Power and false-positive rate under a planted latent are currently unknown.

The best cheap substantive (non-engine) experiment is **EXP-CCO-01**, whose pilot runs on a laptop.

## UNCHECKED or unverified items

- Every cited paper's content beyond its abstract (or title, where Crossref has no abstract). Existence
  and abstracts were checked on 2026-11-24 for the papers listed in each file's source table.
- Results of AWQ (2306.00978), the Progressive Intensity Hypothesis (2603.18426), LPCMCI (2007.01884)
  and Reiser (2209.03427), Xiong et al. (2306.13063), GrACE (2509.09438), *Wonder Wins Ways*
  (2509.20648), Li & Gajane (2302.10825), state-space world models (2502.20168), and *Rethinking CKA in
  KD* (2401.11824).
- Crossref items with no abstract: *Quantized Can Still Be Calibrated* (ACL 2025, 10.18653/v1/2025.acl-long.1473),
  *Confidence Elicitation Improves Selective Generation* (SMC 2024), InferFast (ICS 2026).
- Not fetched: *Epistemic Closure and Falsifiability in AI-Mediated Self-Referential Systems*
  (10.20944/preprints202603.1068.v1), *Accuracy-Latency Trade-offs … Safety-Critical Edge AI*
  (10.21203/rs.3.rs-9384240/v1), *Equivalence between RSA, CKA, CCA* (10.1101/2024.10.23.619871),
  *Contributions of expected learning progress and perceptual novelty…*, and every headline paper.
- **Discrepancy:** `research/notes/09` summarizes Stanton et al. (2106.05945) as "students match
  predictions, diverge in representations" and calls H5 "confirmed by literature". The abstract
  reports that students often *don't* match the teacher's predictive distribution and doesn't mention
  representations. Whether the body supports the note is UNCHECKED; the note is not edited here.
- Measurement-practice points taken from `research/notes/09` (RAPL scope, NVML sampling, whitening
  before CKA/ID) weren't independently re-verified.
- The `stage_hidden` docstring says it "mirrors modules/hnd.py"; no `hnd.py` exists in the repo at this
  commit.
- Compute estimates are rough planning figures, not measurements.

## Sketches (offline, not results)

All run offline in seconds with Python 3 and numpy; `engine_audit.py` is stdlib-only. They print
synthetic or audit numbers. None is a finding. No tests were added: `status.py --check` counts tests,
and CI would flag a stale `STATUS.md`.

| Sketch | For | Run |
|---|---|---|
| `sketches/engine_audit.py` | EXP-ENG-01..04, churn note | `python3 sketches/engine_audit.py relevance\|control\|survival\|churn 6` |
| `sketches/awq_toy.py` | EXP-AAQ-02 pilot | `python3 sketches/awq_toy.py` |
| `sketches/latency_harness.py` | EXP-SSP-01, EXP-DCM-01 | `python3 sketches/latency_harness.py --env` |
| `sketches/noncommutativity_toy.py` | EXP-CCO-01 pilot | `python3 sketches/noncommutativity_toy.py` |
| `sketches/cka_toy.py` | EXP-RGC-01 | `python3 sketches/cka_toy.py` |
| `sketches/calibration_toy.py` | EXP-CAL-02, EXP-DCM-02 sizing | `python3 sketches/calibration_toy.py` |
| `sketches/hidden_residual_toy.py` | EXP-HVD-01 | `python3 sketches/hidden_residual_toy.py` |
| `sketches/curiosity_toy.py` | EXP-WMC-01 stage 1 | `python3 sketches/curiosity_toy.py` |

Run from `hypothesis-engine/experiments/`.
