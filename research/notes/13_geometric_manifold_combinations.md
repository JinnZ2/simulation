# 13 — Geometric-manifold- (Basin Repair Framework) × Seven Questions × Ecosystem

Date: 2026-08-13 · Repo: github.com/JinnZ2/Geometric-manifold- (CC0, ~2.1k LOC, torch+numpy+scipy+pandas; one stdlib-only controller)
Basis: code-level deep-read + notes/09–12.

---

## 1. What the repo actually is (verified internals)

**Basin Repair Framework**: model safety as geometry. Safe configs = KL-ball B_θ = {θ : KL(f_θ ‖ f_θ₀) < ε}, ε=0.1. Three manifold layers:

| Layer | Mechanism | Key math |
|---|---|---|
| Data | GMR k-NN cleaning (k=10), asymmetric: majority dropped below conf 0.7, minority **never fully dropped** (β′=0.1 invariant) | label-agreement fraction as geometric confidence |
| Parameter | curvature-aware trust-region repair, adversarial saddle loss | total = task − λ_asym·safety (minus sign intentional); C(θ)=exp(−λ_curv·risk − ‖θ−θ_ref‖); trust radius hard clamp 0.05 |
| Policy | trajectory alignment | JS(P‖Q), conf = 1−JS/ln2, reanchor blend (1−s)P+sQ, s=0.1 |

Plus: **κ_eff = |v·Hv|/v·v** (finite-difference Rayleigh quotient of safety Hessian) as claimed **leading indicator** — "spikes before behavioral failure"; Fisher-weighted repair energy C=δᵀGδ with trend-ratio spike detection; a pure-stdlib `GenericRepairController` (natural gradient on diagonal-Fisher proxy, adaptive μ) that **exports a falsifiable CLAIM_TABLE** (`falsification_condition`, `status: OPEN`, `ISS_proof_pending: True`).

**Declared weaknesses** (their own docs): ISS proof pending; Lyapunov certificate dV/dt≤0 unproven; phase labels "heuristic, not certified"; "this codebase is entirely theoretical and structurally isolated... must be fed live external data or it becomes an echo chamber of its own geometry"; wants automated phase-transition detector + drift-sweep phase diagrams.

**Fieldlink**: bash/jq cross-repo sync with exactly one peer — **Rosetta-Shape-Core** (new ecosystem repo: shape ontology; this repo maps data→ICOSA, parameter→DODECA, policy→OCTA, confidence→TETRA, thermo→CUBE).

---

## 2. Combinations with the seven questions

### C1 · Sheaf consistency (Q1) × three manifold layers — *the natural sheaf problem*
The three layers are three stalks over the same underlying object (the model). Their confidence aggregation (0.2/0.5/0.3 weighted sum) is currently a scalar mash. Reframe: each layer's state = local section; **consistency between layers = sheaf gluing condition**. Our S1 sim showed λ₁ ≈ 0.176φ² detects and *localizes* the inconsistent edge. Applied here: disagreement between parameter-layer confidence and policy-layer JS-confidence is a measurable λ₁ lift, and leave-one-layer-out identifies which layer is lying. **Concrete: build the 3-node sheaf (data/parameter/policy), compute λ₁ as a fourth meta-signal, test whether it fires before κ_eff does.** Also directly answers their "echo chamber" worry — sheaf inconsistency is exactly the signature of layers that stopped agreeing with reality.

### C2 · Integral feedback (Q2) × repair controller — *and the pending ISS proof*
The repair controller is a regulator chasing a setpoint (KL < ε). Our S2 result: integral feedback gives tuning-free robust setpoint control under ×10 plant perturbation, at a few-percent noise penalty. Their controller uses adaptive μ and trust clamps — heuristic gain scheduling. **Proposal: add an integral term on basin-violation (I = ∫ max(0, KL−ε) dt) to the repair gain, and frame the pending ISS proof through the internal-model-principle lens** (Yi et al.: robust perfect regulation ⟺ integral feedback; Bin et al. 2022 survey). This gives the proof a target: ISS for their loop *reduces to* standard results once the integrator is explicit. Their μ-adaptation (×1.05 when out of basin) is already a discrete integrator in disguise — name it, analyze it, prove around it.

### C3 · Overlay capacity (Q3) × three signals on one parameter vector
Three overlays (data confidence, parameter curvature, policy JS) are superimposed on one θ. Our S3 finding: uncleaned superposition degrades as Φ(1/√(k−1)), but **cleanup memory (known reference patterns) restores capacity dramatically**; FDM-style separation beats code-division by ~100×. Their θ_ref plays exactly the cleanup-memory role. **Proposal: treat the three layer-signals as overlaid channels; measure how many independent safety signals can actually ride one parameter vector before crosstalk** (k=3 is nearly free; the interesting question is the roadmap's planned math_stepper/curiosity/provenance channels pushing k to 6–8). Predicts when the 0.2/0.5/0.3 aggregation must fail and channels need structural separation (FDM analog: separate subspaces/per-layer bases).

### C4 · Atlas compression (Q4) × trust regions as charts — *the strongest fit*
A trust region is literally a chart: local linear/ quadratic model valid within radius 0.05. Their framework has ONE basin (one chart around θ_ref). Our S4 measured the payoff of multi-chart structure: infinite advantage on clustered data, 15× at moderate curvature, 2× at high curvature. **Proposal: multi-basin atlas repair** — multiple reference points {θ_refⁱ} (e.g., safe configs for different task regimes), a gating function = partition of unity choosing the local chart, transition maps on overlaps. The atlas/ directory currently holds sync manifests, not geometric atlases; this would make the name true. Also connects to SliceGPT-style chart-aware compression (notes/09): the safety basin of a compressed model needs its own chart, not the uncompressed model's.

### C5 · Citation-bias detection (Q5) × their planned intake valve
Claude-to-do wants `curiosity_loop.py` (ArXiv/NIST/USPTO retrieval) with provenance weights (1.0 cited / 0.1 speculative) and `[LIKELY HALLUCINATION]` tags. Our S5 sim: supportive-citation fraction saturates at ~0.90 under even mild bias (0.3); hub concentration is non-discriminating alone. **Proposal: wire the falsification-ledger escape-hatch flag + supportive-fraction detector + reference-rot monitor into the intake valve from day one** — provenance weight becomes a computed ledger quantity, not a hand-set constant. The CMN/wood-wide-web literature (Karst 2023) is the validation case study.

### C6 · Marker battery with kill criteria (Q6) × the κ_eff leading-indicator claim — *ready to run*
Their README claims κ_eff "spikes before behavioral failure (basin_kl exceeds epsilon)." That is a **falsifiable, pre-registrable claim with a natural kill criterion** — exactly our S6 protocol. **Proposal: adversarial-collaboration-style test**: Theory A (κ_eff is a leading indicator: κ spike precedes KL breach by ≥k steps in ≥p% of drift runs) vs Theory B (κ_eff is coincident or lagging; trivial baseline = KL rate-of-change predicts breach as well). Pre-register thresholds, run drift sweeps 0.05–0.9 (their energy_sweep mode already does the sweep), both theories scored by a theory-neutral harness. This is the cheapest high-value experiment available — the apparatus exists in-repo.

### C7 · Anti-unification repair (Q7) × repair operators
Their repair = pull back to θ_ref (deletion-flavored: discard drift) or convex reanchor (blend). S7 showed LGG-refinement dominates deletion. **Proposal: third repair mode — generalize the basin**: when drift is *beneficial* (task improvement, safety preserved), instead of pulling back, expand/re-anchor the basin to the least generalization containing both θ_ref and θ_current (in weight space: the minimal larger trust region / in distribution space: the minimal KL-ball expansion with a recorded claim). Every basin expansion enters the CLAIM_TABLE as a refutable claim ("the expanded basin remains safe under perturbation σ") — repair events become falsification candidates instead of silent state changes.

---

## 3. Combinations with the wider ecosystem

- **CDT cascade audit**: κ_eff, energy trend ratio, JS confidence, and combined confidence are four ready-made signal reads; **h_eff = KL/ε** is a normalized forcing analog — drift toward basin boundary maps onto STRESSED/CASCADE regimes. The repo's phase classifier (stable/threshold/critical at κ>20, KL>2ε, trend>3) is a hand-rolled cascade audit; swap in CDT's six-signal + spinodal machinery for principled thresholds.
- **CDT falsification ledger**: their `to_claim_table()` with `falsification_condition`/`status: OPEN` is 80% of the ledger's Claim format — a thin adapter makes repair events hash-chained entries. ISS_proof_pending becomes an OPEN claim with a refutation set, not a comment.
- **CDT calibration gate**: their `constraint_fn → (name, satisfied, desc)` triples match the gate's determinacy interface; GROUND = measured model behavior, PREDICT = basin model.
- **GBCB hardware**: their to-do explicitly wants "physical grounding feedback loop updating the reference basin from real execution friction" — GBCB's timestamped CSV contract + serial adapters are the intake; hardware-in-the-loop basin repair is the demo.
- **Rosetta-Shape-Core**: the fieldlink peer is itself an integration target — its shape ontology (ICOSA/DODECA/OCTA/TETRA/CUBE assignments) could be grounded via notes/11 geometry (why those assignments? what invariants do the shapes encode?) — currently whimsical; could become load-bearing.
- **Hypothesis engine**: their Ideas.md wants autolab-style automation; the hypothesis-engine Action (topics: κ_eff leading-indicator test, atlas repair, ISS proof) is the chassis.

## 4. Recommended first moves (cost-ordered)

1. **C6 κ_eff kill-criteria test** — in-repo apparatus, days, produces a publishable positive or negative result either way.
2. **C1 three-layer sheaf λ₁** — ~100 LOC stdlib, new meta-signal, directly addresses "echo chamber."
3. **Claim-table → CDT ledger adapter** — ~60 LOC, makes ISS/phase claims first-class falsifiable objects.
4. **C2 integral-term repair + ISS framing** — moderate effort, targets their own stated open problem.
5. **C4 multi-basin atlas** — the flagship extension; quarter-scale project; makes `atlas/` literally true.

**Cautions**: repo is not stdlib-only (torch/scipy/pandas) — ecosystem Tier-2 by our stack discipline; keep adapters file-format-based (CSV/JSON manifests, which atlas/exports already are). κ_eff's finite-difference HVP (eps=1e-4, unnormalized v) needs noise-robustness checks before C6 — part of the pre-registration. The Rosetta shape mappings are decorative today; treat as schema, not physics.
