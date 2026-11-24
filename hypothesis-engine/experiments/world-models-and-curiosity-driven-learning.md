# World models and curiosity-driven learning — what needs to be known, and experiments (EXP-WMC)

Draft read: `hypotheses/world-models-and-curiosity-driven-learning.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

No charter hypothesis is attached in `config/topics.json`; its queries are "world models model-based
reinforcement learning", "curiosity-driven exploration intrinsic motivation", and "surprise minimization
active inference agents". Working questions used here: **(1) do prediction-error curiosity bonuses get
captured by irreducible stochasticity (the "noisy TV"), and which bonus families avoid it? (2) does
better one-step world-model accuracy translate into better planning return?**

## 1. What the engine claims, and on what evidence

**Headline statement:** "*Skyrmion Fractional Chern Insulator: An Intrinsically Multiband Route to
Fractionalization in Rhombohedral Graphene* reports…". NEW HYPOTHESIS, 111 surviving claims. The
headline is condensed-matter physics and irrelevant. It's the only topic whose headline changed in the
last 6 engine runs (2026-11-05 and 2026-11-19); the 2026-11-19 run added 57 supporting claims
(48 → 105). That is the largest single-run jump in any topic, and it's churn in retrieval, not new
evidence on the question.

**Evidence base (AUDIT):** 129 findings; 121 claims; 111 surviving. The core-term screen hits 13/111,
and 1 of the 98 arXiv survivors. Top-ranked survivors (0.86) include 3D assembly agents, AI weather
ensemble blending and physics-research agents; at 0.83, plasmonic dimers and Kepler transit-timing
variations. On-topic survivors exist at 0.83: *Wonder Wins Ways*, *Contributions of expected learning
progress and perceptual novelty to curiosity-driven exploration*, and *Curiosity-driven Exploration in
Sparse-reward MARL*. Real pool 108 vs size-matched cross-topic pool 25 under the ratchet.

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What the abstract shows | Bearing |
|---|---|---|---|
| Wonder Wins Ways, arXiv:2509.20648 (supporting, 0.83) | Yes | States that "artificial curiosity often confuses environmental stochasticity with meaningful novelty"; proposes contextual calibration in MARL. | Directly on the noisy-TV question. Results UNCHECKED. |
| Curiosity-driven Exploration in Sparse-reward MARL (Li & Gajane), arXiv:2302.10825 (supporting, 0.83) | Yes | Discusses ICM's detachment problem; proposes I-Go-Explore. | On topic. Results UNCHECKED. |
| State-space world models for MBRL, arXiv:2502.20168 (finding) | Yes | State-space models as world models in model-based RL. | On topic for question 2. Results UNCHECKED. |
| Contributions of expected learning progress and perceptual novelty… (supporting, 0.83) | Listed; not fetched | — | UNCHECKED. |
| Headline (rhombohedral graphene) | Not fetched | — | None (E2). |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- 8 escape-hatched claims. As in the other topics, the journal records that a claim was narrowed, not
  which measurement is missing.

### (b) Gaps identified here
- **G1. Noisy-TV susceptibility is asserted more often than measured under matched conditions.** The
  comparison needs the same environment, the same budget and the same base learner across bonus
  families (count-based, ICM prediction error, RND, ensemble disagreement, learning progress), with an
  explicit stochastic distractor and a no-distractor control.
- **G2. Operationalizing "captured".** Time-on-distractor, coverage (distinct states visited) and
  extrinsic return on a downstream sparse-reward task are three different outcomes. A method can spend
  time on the TV and still explore well.
- **G3. Learning progress is fragile to estimate.** Learning-progress bonuses depend on the window and
  smoothing used to measure the error decrease. The tabular sketch's naive estimator explored poorly
  (low coverage in a default run). That's a weakness of the sketch's estimator, not evidence about
  learning progress, and it shows that estimator choice must be an explicit, ablated variable.
- **G4. Objective mismatch.** Training a world model to minimize one-step prediction error isn't the
  same as training it to support planning. Whether lower one-step error predicts higher return across
  model variants needs a direct correlational test with enough variants. Prior literature on objective
  mismatch in MBRL exists but wasn't checked here: UNCHECKED.
- **G5. Seeds and variance.** Deep RL results vary widely across seeds. Small seed counts with
  point-estimate comparisons are unreliable; report interval estimates (e.g. IQM with bootstrap CIs).

## 3. Experiments

### EXP-WMC-01 — Noisy-TV susceptibility across bonus families, matched conditions
- **Gaps:** G1, G2, G3, G5.
- **H1:** With a stochastic distractor present, prediction-error bonuses (ICM-style) spend a larger
  fraction of steps on the distractor and reach lower coverage than count-based and ensemble-disagreement
  bonuses. Without the distractor, the gap disappears. **H0:** The distractor × bonus-family interaction
  on time-on-distractor is zero.
- **Variables:** Bonus family ∈ {none, count/pseudo-count, ICM, RND, ensemble disagreement, learning
  progress (2 estimator windows)}; distractor ∈ {absent, present}. Outcomes: time-on-distractor
  (primary), state coverage, downstream extrinsic return after reward is revealed.
- **Design:** Stage 1 (pilot): tabular gridworld, `sketches/curiosity_toy.py`, 30 seeds. Stage 2:
  MiniGrid (e.g. a MultiRoom or KeyCorridor variant) with a noisy-TV tile that outputs random
  observations when the agent acts on it; PPO base learner, same hyperparameters across families except
  the bonus scale (tuned once on the no-distractor environment and then frozen); 10 seeds × 5 M steps
  per arm.
- **Pre-registered prediction:** ICM time-on-distractor with the TV > 3× without the TV;
  count and disagreement < 1.5×. **Falsified if** ICM's ratio is within the CI of count's ratio.
- **Analysis:** Interaction contrast of time-on-distractor with a seed-level bootstrap; IQM and 95% CIs
  for coverage and return.
- **Threats:** Bonus-scale tuning favours some families. Tuning on the no-distractor environment and
  freezing is the control. Observation-encoding choices affect ICM and RND differently; report the
  architecture.
- **Tier:** Stage 1 laptop CPU (seconds). Stage 2 single GPU or a multicore CPU, about 2–4 days of wall
  time for 7 × 2 × 10 runs (rough).
- **Would establish:** Relative susceptibility on these environments. **Would not establish:**
  Behaviour on 3D or pixel-rich domains, or anything about active inference.
- **Sketch:** `sketches/curiosity_toy.py`. Its learning-progress bonus is crude (see G3), so treat
  that arm as unvalidated.

### EXP-WMC-02 — Does one-step world-model accuracy predict planning return?
- **Gap:** G4.
- **H1:** Across world-model variants trained on the same data, the rank correlation between held-out
  one-step prediction error and planning return is weak (|ρ| < 0.5). **H0:** Strong negative correlation
  (ρ ≤ −0.5: lower error, higher return).
- **Variables:** ≥ 20 world-model variants (capacity, training steps, loss weighting, deterministic vs
  stochastic heads), all trained on one fixed replay dataset. Predictors: one-step MSE / NLL, and k-step
  rollout error (k = 5, 15). Outcome: return of a fixed planner (MPC with CEM, fixed budget) using each
  model.
- **Design:** 2 continuous-control tasks from an open suite (e.g. DeepMind Control cartpole-swingup,
  cheetah-run); 3 planning seeds per variant.
- **Pre-registered prediction:** |ρ(one-step error, return)| < 0.5, with k-step rollout error more
  predictive than one-step error. **Falsified if** ρ(one-step error, return) ≤ −0.5 with the CI upper
  bound < −0.3 on both tasks.
- **Analysis:** Spearman with a bootstrap over variants; partial correlation controlling for model
  capacity.
- **Threats:** Variant set design determines the correlation range; pre-register the variant grid.
  Planner hyperparameters are fixed and reported.
- **Tier:** Single GPU, about 2–3 GPU-days (rough).
- **Would establish:** Whether one-step accuracy is a usable selection criterion for world models on
  these tasks. **Would not establish:** Results for latent-imagination agents (Dreamer-style), which
  train policies inside the model rather than planning.
