# Hidden-variable detection / causal discovery from residuals — what needs to be known, and experiments (EXP-HVD)

Draft read: `hypotheses/hidden-variable-detection-causal-discovery-from-residuals.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

No charter hypothesis is attached to this topic in `config/topics.json`; its queries are "hidden variable
detection residual correlation" and "causal discovery latent variables time series". This topic is also
reflexive: the engine has its own hidden-variable stage (`stage_hidden`), and that stage is the most
directly testable object here.

## 1. What the engine claims, and on what evidence

**Headline statement:** "*Joint Estimation of Sparse Multilayer Networks via Graph Limits* reports:
Network datasets in modern applications often involve multiple types of interactions…" (arXiv:2608.14536).
NEW HYPOTHESIS, 44 surviving claims. The headline is about network estimation, not hidden variables or
residual-based causal discovery.

**Evidence base (AUDIT):** 128 findings; 127 claims; 44 surviving. The core-term screen hits 8/44.
Survivors at 0.83 include lattice-field renormalization, Bell local-hidden-variable models (the
lexical match on "hidden variable" is a quantum-foundations sense), world-action models for robots, and
diffusion representation conditioning. On-topic survivors exist: *Causal discovery for time series with
latent confounders* (0.83) and *High-recall causal discovery for autocorrelated time series with latent
confounders* (LPCMCI, 0.67). Real pool 38 vs size-matched cross-topic pool 13 under the ratchet.

**The engine's own hidden-variable rule** (`scripts/hypothesis_engine.py`, `stage_hidden`, read-only):
residual = |beta_confidence − 0.5| per claim; a suggestion fires if mean residual ≥ 0.1 and
|Pearson r(residual, candidate)| > 0.5. The docstring says this "mirrors modules/hnd.py", but no file
`hnd.py` exists anywhere in the repo at this commit (searched 2026-11-24). Two candidate series were
already removed after the 2026-08-17 run: `confidence_trend` (an affine map of the residual, r = 1 by
algebra) and `source_diversity` (constant). A guard now rejects |r| = 1. The remaining candidate,
`findings_rate`, indexes the per-month findings count by claim index *i mod M* (E7). Claims and months
aren't aligned, there's no significance test, and the residual is folded (absolute value), which throws
away sign. `data/hidden_variables.jsonl` holds 5 rows: the 2 removed `confidence_trend` artefacts and 3
DCM `findings_rate` rows. This topic's draft lists none.

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What the abstract shows | Bearing |
|---|---|---|---|
| LPCMCI, Gerhardus & Runge, arXiv:2007.01884 (supporting, 0.67) | Yes | FCI-type methods have low recall in autocorrelated time series with latent confounders; the low effect size of CI tests is identified as the cause; LPCMCI includes known parents in conditioning sets to raise effect size. | Directly on topic and a ready baseline for EXP-HVD-02. |
| Causal discovery for time series with latent confounders (Reiser), arXiv:2209.03427 (supporting, 0.83) | Yes | Evaluates LPCMCI; reports it "performs much better than a random algorithm". | On topic (evaluation study). Details UNCHECKED. |
| OrthoFormer, arXiv:2603.07431 (finding) | Yes | Instrumental-variable estimation in transformer hidden states. | Adjacent (IV, not residual screening). |
| Canonical-correlation residual fault detection, DOI 10.1038/s41598-026-74736-5 (finding) | Yes (Sci Rep, 2026-10-17) | Residual-based fault detection. | Adjacent (residual generators in engineering). Details UNCHECKED. |
| Headline, arXiv:2608.14536 | Listed in log; not fetched | — | Off topic by title. |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- One escape-hatched claim (*Causal Discovery in High-Dimensional Time Series with Latent Confounders
  via Score-Based…*). No hidden-variable suspects for this topic.

### (b) Gaps identified here
- **G1. Operating characteristics of the engine's rule are unknown.** No one has measured its power or
  false-positive rate, either on synthetic data with a planted confounder or on the engine's own data.
  A threshold on |r| without a null distribution for autocorrelated series is known to give spurious
  correlations (Yule's nonsense-correlation problem); what matters is how often, at these n and
  autocorrelations.
- **G2. Alignment.** Residual and candidate need a common index (time or claim). The `i mod M` mapping
  creates an arbitrary pairing; any correlation it produces doesn't refer to anything.
- **G3. Folding.** |residual| removes sign. A confounder that pushes outcomes in both directions is
  invisible to a signed test; a confounder with consistent sign is attenuated by folding. Which matters
  more is an empirical question about the generating process.
- **G4. Residual screening vs established causal discovery.** Whether a residual-correlation screen
  adds anything over LPCMCI/FCI-type methods with known latent structure hasn't been tested.
- **G5. Identification limits.** Even a valid residual correlation with a proxy shows association, not
  that the proxy is the hidden cause. Proxies can be colliders or mediators.

## 3. Experiments

### EXP-HVD-01 — Operating characteristics of the engine's rule (synthetic, planted latent)
- **Gaps:** G1, G3.
- **H1:** At the engine's thresholds, on a linear-Gaussian SCM with an AR(1) latent confounder, the
  engine-shaped rule (folded residual, |r| > 0.5) has power < 0.5 against a true proxy of the latent,
  and a permutation-calibrated signed test has false-positive rate ≈ α against an independent AR(1)
  series with the same autocorrelation. **H0:** The engine-shaped rule has power ≥ 0.8 at FPR ≤ 0.05.
- **Variables:** Detector ∈ {engine_abs, signed with threshold, signed with circular-shift permutation
  p}. Sweep n ∈ {20, 50, 200, 1000}, latent effect c ∈ {0.25, 0.5, 1, 2}, autocorrelation φ ∈ {0, 0.5,
  0.9, 0.99}, proxy noise ∈ {0.1, 0.5, 1}. Outcomes: power (proxy candidate), FPR (null candidate).
- **Design:** 1,000 replicates per cell (the Monte Carlo SE of a rate near 0.05 is ≈ 0.007). Seeds fixed
  and recorded.
- **Pre-registered prediction:** engine_abs power < 0.5 in most cells at n ≤ 200; signed_perm FPR within
  [0.03, 0.07] across φ. **Falsified if** engine_abs achieves power ≥ 0.8 with FPR ≤ 0.05 across the
  majority of cells.
- **Analysis:** Power/FPR tables with Monte Carlo CIs; ROC curves by sweeping the threshold.
- **Threats:** Results depend on the SCM family. Add a nonlinear variant (tanh link) and a variant where
  the latent acts with opposite signs in two regimes (the case that folding should handle better).
- **Tier:** Laptop CPU (minutes).
- **Would establish:** How the engine's rule behaves when the truth is known, for this SCM family.
  **Would not establish:** That any suggestion the engine has produced is right or wrong. That's
  EXP-HVD-03.
- **Sketch:** `sketches/hidden_residual_toy.py`. A default run (n = 200, c = 1, φ = 0.95) on synthetic
  data showed engine_abs firing on neither proxy nor null, the thresholded signed rule rarely firing,
  and the permutation test detecting the proxy at about nominal FPR. That's one parameter cell of a
  sketch, not a result.

### EXP-HVD-02 — Residual screening vs LPCMCI on benchmarks with known latents
- **Gap:** G4.
- **H1:** On synthetic time-series benchmarks with known latent confounders, LPCMCI (tigramite) achieves
  higher recall of confounded pairs at matched FPR than a permutation-calibrated residual screen.
  **H0:** No recall difference beyond the bootstrap CI.
- **Design:** Use the benchmark generators of 2007.01884 or the tigramite toy models, re-implemented if
  necessary: N ∈ {5, 10} variables, 1–2 latents, T ∈ {200, 500, 1000}, autocorrelation ∈ {0.5, 0.9};
  100 datasets per cell. Methods: LPCMCI (α = 0.01, 0.05), FCI-style baseline, residual screen
  (regress each variable on its observed lags, signed permutation test of residual cross-correlation).
- **Pre-registered prediction:** LPCMCI ≥ residual screen in recall at matched FPR at high
  autocorrelation. The residual screen may be competitive at low autocorrelation and large T. **Falsified
  if** the residual screen has higher recall at matched FPR in the high-autocorrelation cells.
- **Analysis:** Recall/FPR per cell with bootstrap CIs; runtime reported.
- **Threats:** Matching FPR across methods with different outputs (PAGs vs pairwise flags): define the
  evaluation target in advance as the set of variable pairs with a latent common cause.
- **Tier:** Laptop CPU (hours; tigramite is CPU-only).
- **Would establish:** Whether the engine's style of screening is worth keeping over a standard method
  on these benchmarks. **Would not establish:** Performance on real-world data, where ground truth is
  unknown.

### EXP-HVD-03 — Planted-signal recovery on a copy of the engine's own data
- **Gaps:** G1, G2.
- **H1:** When a known synthetic signal is planted into a copy of the engine's confidence data (claim
  outcomes shifted by a variable aligned to claim date), the current `stage_hidden` recovers it less
  often than a date-aligned, signed, permutation-tested variant. **H0:** Recovery rates are equal.
- **Design:** Copy `data/claim_tree.json` and `data/findings_log.jsonl` into a temp directory (never
  modify the originals). For each of 200 trials, plant a signal: shift `passed` for claims whose finding
  date falls in randomly chosen months by +k, with k ∈ {1, 2, 4}. Run (a) the engine's `stage_hidden`
  imported read-only and (b) the variant: residual is signed, candidate is aligned by the claim's finding
  month, and the p-value comes from a month-block permutation. Also run 200 no-plant trials for FPR.
- **Pre-registered prediction:** (a) recovers < 20% of plants at k = 2; (b) recovers ≥ 60% with FPR ≤
  0.05. **Falsified if** (a) recovers ≥ 60% at k = 2 with FPR ≤ 0.05.
- **Analysis:** Recovery and FPR with Wilson CIs.
- **Threats:** The ratchet (E4) saturates confidences near 1, which limits residual variance. Report the
  residual distribution before planting.
- **Tier:** Laptop CPU.
- **Would establish:** Whether the engine's hidden stage can detect a signal of known size in its own
  data. **Would not establish:** That a real hidden variable exists or doesn't in the engine's history.
