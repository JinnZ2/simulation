# Cross-Domain-Toolkit — Strengthening & Improvement Proposals

Repo: https://github.com/JinnZ2/Cross-Domain-Toolkit · stdlib-only Python ≥3.7 · MIT
Basis: `/mnt/agents/output/notes/08_cross_domain_toolkit.md` (code-verified deep-read + 30-domain atlas + logic/knowledge research)
Constraint honored throughout: **stdlib-only, no build step, extensions as examples/new modules — never core special-casing.**

---

## P0 — Highest-leverage additions (do first)

### P0.1 `opinions.py` — Subjective-logic confidence binding (replaces ad-hoc noisy-OR)
**Why:** The gate's noisy-OR determinacy `1−Π(1−cᵢ)` and reliability-weighted confidence are an *unnamed reinvention* of Jøsang's subjective logic, which is exactly isomorphic to the Beta posterior the ledger lineage already uses: ω=(b,d,u,a), b=r/(W+r+s), d=s/(W+r+s), u=W/(W+r+s), W=2. Adopting it names the math, adds the **uncertainty mass u as a first-class output** (the gate currently collapses it away), and gives correct fusion semantics: *cumulative* for independent substrates, *averaging* for dependent ones — today's noisy-OR silently assumes independence.
**Change:** New module `multi_substrate_calibration/opinions.py` (~150 LOC). `bound_read()` emits an Opinion; fusion dispatches on a complementary/competitive classification of the substrate pair; gate reports `(determinacy, u)`.
**Falsifiable claim:** "Under correlated substrates, cumulative-vs-averaging dispatch prevents determinacy overstatement vs current noisy-OR" — testable with a synthetic two-correlated-probe example.

### P0.2 `conflict.py` — Dempster–Shafer conflict mass K as a seventh signal channel
**Why:** The six-signal audit takes caller-supplied pressures; there is no principled bridge from the calibration gate to the audit. D-S conflict mass $K = \sum_{A\cap B=\emptyset} m_1(A)m_2(B)$ between substrates *is* a computed "coherence under contradiction" pressure (signal S5) instead of a hand-set one. Do **not** use D-S for fusion (Zadeh paradox at K→1) — only as a detector feed.
**Change:** ~80 LOC module; example `gate_to_audit.py` wiring gate conflict → SignalReads.

### P0.3 `eigentrust.py` — Ledger-fed substrate trust
**Why:** Calibration `reliability` is currently a caller-supplied constant. But the ledger *already records* each substrate's falsification track record. Close the loop: EigenTrust power iteration t^{(k+1)} = (1−α)Cᵀt^(k) + αp over per-substrate hit rates (~60 LOC, dicts only) → GROUND-role eligibility thresholded on global trust. This makes "an unproven substrate cannot dominate the gate" *earned by evidence* rather than asserted.

### P0.4 Example pack — eight cusp-structured domains
**Why:** Eight atlas domains instantiate the existing spinodal h* = 2/√27 *directly* (structural buckling, vdW phase transition, Semenov runaway, ice-albedo/AMOC, Allee collapse, grid nose curve, Griffith fracture, fisheries MSY). Shipping reference mappers h_eff(…) for these turns the audit from an abstract instrument into a calibrated one — exactly what examples/model_collapse.py did for ML.
**Change:** `cascade_regime_audit/examples/` additions, each ~60–100 LOC with the domain's canonical threshold constants from the atlas; tests use synthetic fold-approach series.

---

## P1 — Knowledge-system layer (the "integration & assessment" capability)

### P1.1 `integrate/graph.py` — Content-addressed triple store + PROV-O emission
**Why:** Cross-domain integration needs a common record model. Triples (s,p,o) with spo/pos/osp indexes + BGP join ≈ 250–350 LOC covers ~80% of queries. JSON-LD-shaped records with `urn:falsify:claim:<ledger_hash>` @ids make every claim content-addressed for free. PROV-O mapping is ~1:1 onto existing classes (Claim/Prediction/Reality → prov:Entity; mismatch evaluation → prov:Activity; substrate → prov:Agent; revision → wasDerivedFrom) — standards-compliant provenance vocabulary for ~100 LOC.
**Change:** New top-level package `integrate/` (extension, not core surgery). Emit PROV-N-style records from any ledger via adapter — core stays untouched.

### P1.2 `assess/belnap.py` + `assess/atms.py` — Contradiction-tolerant assessment spine
**Why:** Multi-domain evidence will contradict. Classical logic explodes; the toolkit currently has no truth-value semantics for claims at all.
- Belnap 4-valued {T,F,Both,Neither} (~80 LOC): pending predictions = Neither; contradicted = Both (queryable, non-infecting).
- de Kleer ATMS (~200 LOC): claims = nodes, substrate endorsements = assumptions, detected contradictions = nogoods. Payoff: **dependency-directed retraction** — when EigenTrust (P0.3) discredits a substrate, label filtering enumerates every claim that depended on it. This is the single strongest structural match to the existing architecture.

### P1.3 `assess/argumentation.py` — Dung grounded semantics
**Why:** The ledger answers "was this claim refuted?" but not "what is currently defensible overall?" Claims = arguments; Mismatch records = undercut attacks; grounded extension via least fixed point (O(|A|²), ~100 LOC) = the defensible claim set. Skip preferred/stable (exponential).

### P1.4 `assess/repair.py` — Minimal hitting-set repair
**Why:** Assessment should end in action. Reiter diagnoses = minimal hitting sets of conflict sets; ATMS nogoods ARE the conflict sets, so this is one pipeline (~120 LOC, greedy approximation acceptable). Output: minimal claim-retraction sets restoring consistency — each proposed retraction enters the ledger as a falsifiable claim itself (the toolkit eats its own cooking).

---

## P2 — Verification & audit hardening

### P2.1 `verify/dpll.py` + `verify/bmc.py` — Ledger invariants as checkable theorems
**Why:** `Ledger.verify()` checks hashes at runtime; BMC *proves* the invariants: hash-chain integrity and append-only monotonicity under all length-k operation sequences (encode I ∧ ⋀T ∧ ¬P, ~150 LOC on a ~100 LOC DPLL core — the Z3-pluggable `checker=` slot already anticipates this). A satisfying assignment is a concrete counterexample trace. Stdlib DPLL means the verification story stays dependency-free.

### P2.2 `verify/merkle.py` — Third-party audit certificates
**Why:** Hash chain is tamper-evident but verification requires the whole ledger. Merkle batch trees (~40 LOC) give sibling-path proofs: an auditor confirms entry #4,317 with O(log n) data. Upgrades "trust us" to "check this."

### P2.3 Signatures (documented boundary, not code)
REVIEW 2.7 noted tamper-evident ≠ tamper-proof. Stdlib has no asymmetric crypto; document the boundary in METHOD.md and define the `signer=` slot signature now so a future optional HMAC/ed25519 adapter drops in without breaking the chain format.

---

## P3 — Domain-calibration & knowledge-health examples

### P3.1 Ledger-ready domain examples (threshold arithmetic, cheap data)
Seismology (b-value MLE = 1/(ln10·(M̄−M_c))), epidemiology (R₀ from early growth Λ ≈ γ(R₀−1)), sovereign debt (s* = (r−g)/(1+g)·b), ML scaling-law extrapolation (fitted A,B,E,α,β), SRE error budgets (burn rate vs 1−SLO), soil salinity (Maas–Hoffman a,b per crop). Each is a worked `falsification_ledger/examples/` file with refutation_set + logical_form exercising the symbolic checker.
### P3.2 `assess/health.py` — Knowledge-health report
Composite score from free components: Belnap-Both fraction, mean pairwise K, FAIR metrics (persistent @id, complete wasGeneratedBy chains), reference-rot scan (scheduled @id liveness via urllib HEAD). Frames corpus decay (half-life 4–9 yr for cited URLs) as a first-class monitored signal.
### P3.3 Bullwhip/variance-amplification example
`BW = Var(orders)/Var(demand)` with Chen lower bound 1 + 2L/p + 2L²/p² and F-test gate — showcases an EWS signal that is *itself* a falsified-or-not statistic.

---

## What NOT to build (documented extension points only)
Full SPARQL, DL reasoners, preferred/stable argumentation, da Costa logics, fuzzy machinery, Bayesian-network CPT engine, D-S as a fusion operator, asymmetric crypto in-core. Each violates stdlib-only economics or has a cheaper equivalent above.

## Sequencing
1. **P0** (one cycle): opinions.py, conflict.py, eigentrust.py + cusp examples — pure additions, no core breakage.
2. **P1**: integrate/graph.py first (record model everything else emits into), then belnap→atms→argumentation→repair as one assessment spine.
3. **P2** in parallel with P1 (independent modules).
4. **P3** continuously — each new domain example is independent.

Total new code ≈ 1,800–2,200 LOC across ~12 modules, all stdlib, all testable with `python -m unittest`.
