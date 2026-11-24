# Calibration and falsifiability of LLM agents — what needs to be known, and experiments (EXP-CAL)

Draft read: `hypotheses/calibration-and-falsifiability-of-llm-agents.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

No charter hypothesis is attached to this topic in `config/topics.json`. Its queries are "calibration
large language model agents", "falsifiability epistemic grounding LLM", and "confidence elicitation
language models". The working question used here: **Do LLM agents' stated confidences track their
accuracy, and does requiring explicit falsification conditions improve the reliability of what they
assert?** This topic is also reflexive: the engine itself assigns confidences (`beta_confidence`) to
claims, and those can be tested the same way.

## 1. What the engine claims, and on what evidence

**Headline statement:** "*Blazar Boosted Dark Matter in IceCube* reports: We study the sensitivity of
IceCube to blazar-boosted dark matter…". NEW HYPOTHESIS, 208 surviving claims. The headline is an
astroparticle-physics paper and irrelevant (E2).

**Evidence base (AUDIT):** 248 findings (211 arXiv, 20 Crossref, 17 S2); 218 claims; 208 surviving,
the largest count of any topic. A core-term screen (calibration/confidence/uncertainty/falsifiability
co-occurring with LLM/agent) hits 21/208 survivors, and 7 of the 179 arXiv survivors. The top-ranked
supporting claims include an agentic financial architecture (0.95), on-CPU reasoning caching (CPU-ARC,
0.94), and street-interface morphology assessment (0.91). These are about LLM agents but not about
calibration or falsifiability. With a size-matched partner pool from other topics, 61 claims would
survive under the ratchet vs 159 with the real pool, so the same-topic pool adds real signal. But that
signal is lexical ("LLM", "agent" are shared), not evidence of calibration (E3, E4).

**Confidence semantics:** `beta_confidence = (1 + passed) / (2 + passed + failed)` (engine source,
line ~91), the posterior mean of a Beta(1,1) prior over pass/fail corroboration outcomes. A value of
0.95 means "many partner claims shared words with this one", not "95% probability this claim is true".
The draft doesn't say so.

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What it shows | Bearing |
|---|---|---|---|
| Can LLMs Express Their Uncertainty? (Xiong et al.), arXiv:2306.13063 (finding) | Yes | Defines a black-box confidence-elicitation framework (prompting, sampling, aggregation). | Directly on topic. Specific numerical conclusions UNCHECKED. |
| GrACE, arXiv:2509.09438 (finding) | Yes | Confidence from hidden-state similarity to a special token. | On topic (white-box method). Results UNCHECKED. |
| Confidence Elicitation Improves Selective Generation…, DOI 10.1109/SMC54092.2024.10831438 (supporting, 0.90) | Yes (Crossref: IEEE SMC 2024; no abstract) | Title only. | On topic. Content UNCHECKED. |
| CPU-ARC, arXiv:2611.09891 (supporting, 0.94) | Yes | Agentic reasoning caching for CPU inference. | Not about calibration or falsifiability. |
| Epistemic Closure and Falsifiability in AI-Mediated Self-Referential Systems, DOI 10.20944/preprints202603.1068.v1 (finding log) | Not fetched | — | UNCHECKED. |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- 30 escape-hatched claims, the most of any topic. These are the claims that failed corroboration and
  were narrowed in scope. The journal records the escape hatch, not a specific missing measurement.

### (b) Gaps identified here
- **G1. The engine's confidence is uncalibrated, and its calibration is unknown.** `beta_confidence` is
  presented next to claims as if it were a probability. Nobody has measured whether P(claim is on topic
  and supported | beta = 0.9) is anywhere near 0.9. EXP-ENG-01's labels can answer it.
- **G2. Elicitation method as a confound.** Verbalized confidence, sampling consistency, and token
  probability produce different numbers for the same answer. Verbal confidences cluster on a coarse grid
  (0.8, 0.9, 0.95), which changes how binned ECE behaves (`sketches/calibration_toy.py`, synthetic).
- **G3. Metric choice.** Equal-width ECE is biased upward at small n and depends on binning; Brier and
  NLL are proper scoring rules. For probabilistic labels ECE is ill-defined (SMECE, arXiv:2603.14092).
  `research/notes/09` recommends NLL/Brier as primary.
- **G4. "Falsifiability" lacks an operational definition.** Candidates: the agent states a concrete
  condition under which its claim would be wrong; the condition is checkable; the agent abstains or
  revises when the condition is met. Each needs a measurable outcome. The most usable is selective
  prediction: does requiring a falsification condition improve accuracy at a fixed coverage (AURC)?
- **G5. Agent vs single-turn.** Calibration of single-turn QA doesn't transfer automatically to
  multi-step agents, where errors compound and confidence can be updated by tool output.

## 3. Experiments

### EXP-CAL-01 — Is the engine's `beta_confidence` calibrated?
- **Gap:** G1.
- **H1:** Among surviving claims, the human-labelled probability of "on topic AND supported by the
  cited source" is monotonically increasing in `beta_confidence`. **H0 (pre-registered expectation):**
  It isn't. P(on topic and supported) is flat across confidence bins and far below the stated value.
- **Variables:** `beta_confidence` from `data/claim_tree.json` (read-only); the outcome is binary, from
  the EXP-ENG-01 human labels (two raters, κ reported).
- **Design:** Stratified sample of 240 claims: 30 per topic, stratified across confidence terciles.
  Labels are blind to confidence. n = 240 gives a Brier CI half-width of about ±0.03 under a normal
  approximation (a rough planning figure).
- **Pre-registered prediction:** Spearman(beta, label) < 0.2; Brier score worse than a constant
  predictor equal to the base rate. **Falsified if** Spearman ≥ 0.3 with the CI excluding 0, and the
  reliability diagram is within ±0.1 of the diagonal.
- **Analysis:** Reliability diagram (equal-mass bins), Brier and its decomposition, Spearman with a
  bootstrap CI; per-topic breakdown is descriptive.
- **Threats:** Label noise (two raters and adjudication); topic heterogeneity.
- **Tier:** Laptop CPU + about 8 hours of human labelling.
- **Would establish:** Whether the engine's displayed numbers are interpretable as probabilities.
  **Would not establish:** Anything about LLM agents' calibration.

### EXP-CAL-02 — Elicitation method × metric for LLM confidence
- **Gaps:** G2, G3.
- **H1:** Sampling-consistency confidence has lower Brier than verbalized confidence on the same
  questions and the same model. **H0:** No difference beyond the paired bootstrap CI.
- **Variables:** Three confidence sources per answer: verbalized (prompted 0–100), consistency
  (agreement rate over k = 10 samples at T = 0.7), and token probability of the answer option. Outcome:
  correctness. Metrics: Brier (primary), NLL, equal-mass ECE, AURC.
- **Design:** 2 open-weight 7–8B instruction-tuned models; TriviaQA (open answer, normalized exact
  match) + MMLU subset; n = 2,000 items per dataset, sized so the CI half-width on paired Brier
  differences is ≤ 0.01 (to be confirmed with a pilot bootstrap). Same prompts across methods; fixed
  seeds.
- **Pre-registered prediction:** consistency < verbalized in Brier on both models. **Falsified if** the
  paired difference CI includes 0 on both models.
- **Analysis:** Paired bootstrap over items; report all metrics; draw conclusions only from Brier.
- **Threats:** Answer normalization errors (manual audit of 200 items); the extra compute of the
  consistency method (report compute per item; a matched-compute comparison is a secondary analysis).
- **Tier:** Single GPU, about 1 GPU-day (rough).
- **Would establish:** Which elicitation method is better calibrated for these models and tasks.
  **Would not establish:** Calibration in multi-step agent settings (G5).
- **Sketch:** `sketches/calibration_toy.py` (estimator behaviour on synthetic data; use it to size n).

### EXP-CAL-03 — Does requiring a falsification condition improve selective accuracy?
- **Gaps:** G4, G5.
- **H1:** An agent that must state, before answering, a concrete condition under which its answer
  would be wrong, then check it with a tool where possible, achieves lower AURC than the same agent
  without that step. **H0:** No AURC difference beyond the CI.
- **Variables:** Arm A: standard ReAct-style agent with verbalized confidence. Arm B: arm A plus the
  falsification-condition step. Arm C (placebo control): arm A plus a same-length "restate the question"
  step, controlling for extra tokens and deliberation. Outcome: correctness; confidence; AURC; coverage
  at 90% selective accuracy.
- **Design:** A multi-hop QA benchmark with a retrieval tool (e.g. HotpotQA-distractor); 1 open 7–8B
  model; n = 1,000 questions; randomized assignment of question order; 3 seeds.
- **Pre-registered prediction:** AURC(B) < AURC(C) ≤ AURC(A). **Falsified if** AURC(B) isn't lower than
  AURC(C) (any gain is then attributable to extra tokens, not falsification).
- **Analysis:** Paired bootstrap of AURC differences; a manual audit of 100 stated conditions for
  checkability (fraction that are concrete, observable, and actually checked).
- **Threats:** Prompt sensitivity (2 paraphrases per arm); retrieval failures confound both arms equally.
- **Tier:** Single GPU, about 1–2 GPU-days (rough).
- **Would establish:** Whether this specific prompting intervention improves selective prediction on
  one benchmark. **Would not establish:** That agents are "falsifiable" in a philosophical sense, or
  that the effect holds for other models.
