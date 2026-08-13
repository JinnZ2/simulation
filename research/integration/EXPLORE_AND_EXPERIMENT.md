# Places to Explore & Experiments to Run — Pattern Intersections Across the Ecosystem

Date: 2026-08-13 · Basis: notes/08–11, INTEGRATION_POINTS.md.
Every experiment lists: apparatus · cost · what it would show · what it would NOT show. All Tier-0 items are stdlib-only Python.

---

## A. Pattern-intersection questions (the research agenda)

**Q1. Is a calibration gate a sheaf?** The gate's DEFER-on-incoherent-reads is formally a failed sheaf-gluing condition over the cover of shared observables (Goguen sheaf semantics). If so, the sheaf Laplacian's kernel dimension is a *computable global-consistency metric* for multi-substrate systems — a new, principled signal for the cascade audit.

**Q2. Is integral feedback the universal calibration answer?** Bacterial chemotaxis proves topology-not-tuning gives robust perfect adaptation (Barkai–Leibler/Yi). Which of the ecosystem's calibration problems (sensor drift, baseline wander, AGC artifacts) are solvable by integral-feedback topology instead of per-device tuning? Prediction: any calibration that currently needs a fitted constant can be replaced by a dm/dt = g(a − a₀) loop if the measurand has a homeostatic setpoint.

**Q3. Does the residual-stream bus architecture beat point-to-point for multi-substrate sensing?** Transformers, multiphysics operator splitting, and stigmergic swarms all use one shared additive medium instead of n² channels. Test whether GBCB multi-sensor rigs (EM + thermal + mechanical) fuse better through an additive bus with learned projections than through pairwise converters.

**Q4. How many overlays can one substrate carry?** VSA bundling capacity ~√d gives a formal bound. Map it to: frequency-multiplexed sensor channels on one wire, features-per-dimension in compressed nets (superposition), and energy domains per bond-graph edge. Is √d the universal overlay bound across all three?

**Q5. Is compression a chart-selection problem?** SliceGPT rotates to the activation-PCA basis and deletes minor components = choosing the atlas's best chart. Manifold-capacity theory says function dies when R_M²D_M exceeds surviving width. Do ID-profile-matched per-layer budgets (notes/09 H2) dominate uniform budgets because they respect the chart structure?

**Q6. Where does coordination-free fusion break?** CALM: monotone ops need no coordination; non-monotone ops (outlier rejection, resets) are the coordination points. Empirically: which cascade-audit signals are monotone (safe for distributed sensing) and which force synchronization?

**Q7. Can morphogenesis-style setpoint control compile into bond graphs?** Levin: V_mem networks converge to stored target anatomy; gap-junction conductance = edge weight. Bond-graph edge weights are already conductance-like. Can GBCB compile a *goal pattern* (not a mechanism) into a gap-junction-style RC network that relaxes to the target — "compile the what, physics solves the how"?

**Q8. Does recursion depth predict collapse-signal quality?** Consciousness theories converge on recurrence mattering; cascade detection needs temporal depth (AR(1), flickering). Hypothesis: feedforward-only monitoring pipelines are structurally blind to collapse precursors that recurrent pipelines catch — test with the six-signal audit fed by feedforward vs recurrent feature extractors.

**Q9. Is the ledger a Tarski stratum?** Ledger-anchored stratification (each level's claims hashed into the level below) is the engineering dodge to self-reference limits. Formal question: does hash-chained stratification give a well-founded trust order that naive self-certification (Löb-blocked) cannot?

**Q10. Do biological controversy cascades show up in the ecosystem's own metrics?** The wood-wide-web positive-citation-bias case (Karst 2023) is exactly an escape-hatch/citation-decay pathology the falsification ledger and knowledge-health scores (notes/08 P3.2) are built to detect. Can the ledger's escape-hatch flag + reference-rot monitor detect a *simulated* citation-bias cascade?

---

## B. Experiment list (ordered by cost)

### Tier 0 — stdlib-only, days
| # | Experiment | Apparatus | Shows / does not show |
|---|---|---|---|
| E1 | **Integral-feedback calibrator**: replace fitted offset in a CDT substrate example with dm/dt = g(a−a₀) loop; sweep parameters 10× | ~40 LOC | topology-based drift rejection is tuning-free / not that it beats Kalman on all noise models |
| E2 | **Tero-law network optimizer**: conductance loop on small graphs (Kirchhoff by Jacobi relaxation); compare to Dijkstra shortest path | ~80 LOC | flow-adaptive growth converges to near-optimal fault-tolerant networks / not that it scales |
| E3 | **Stentor habituation unit**: two-state Markov switch as alarm-fatigue suppressor in the cascade audit | ~20 LOC | provable habituation = fewer false alarms under repeated benign stimuli / nothing about real neural habituation |
| E4 | **Quorum-triggered regime switch**: Hill-function population comparator switching cascade-audit sensitivity | ~30 LOC | analog voting gives hysteresis-stable mode switching / not optimal threshold placement |
| E5 | **Negative-selection anomaly detector**: self-set deletion detector population as cheap EWS layer | ~60 LOC | immune-style detection covers known-normal space / coverage of novel anomalies unproven |
| E6 | **Sheaf-consistency gate**: cellular sheaf on a sensor graph; kernel dim of sheaf Laplacian as global-consistency score; wire into audit as computed S5/S6 pressures | ~150 LOC | Q1's formal reading works numerically / not yet that it beats hand-set thresholds |
| E7 | **CALM pipeline**: KPN-style stdlib fusion with CRDT states; verify monotone variants are schedule-independent, non-monotone diverge | ~100 LOC | Q6 empirically / only at toy scale |
| E8 | **PCIst on nets**: normalized Lempel–Ziv of binarized perturbation response on a trained tiny MLP, pre/post-compression | ~80 LOC + Tier-1 net | compression changes integration complexity of response / **explicitly NOT consciousness detection** |
| E9 | **VSA capacity probe**: bundling capacity ~√d verified empirically; multiplex synthetic sensor codes, measure decode fidelity vs channel count | ~60 LOC | Q4's bound holds for synthetic channels / not for correlated real sensors |
| E10 | **Gray–Scott + bus overlay**: reaction–diffusion on list grid with additive shared bus vs Strang splitting baseline | ~120 LOC (slow, ~10⁴ cells) | Q3's bus architecture trades accuracy/stability how? / toy physics only |

### Tier 1–2 — numpy/torch, weeks
| # | Experiment | Apparatus | Shows / does not show |
|---|---|---|---|
| E11 | **Memo core study**: activation-aware 4-bit vs pruning vs low-rank at matched memory budgets (50/25/12.5%), ResNet-18 + small decoder; geometry battery (principal angles, CKA, Procrustes, mutual-kNN, TWO-NN ID) + ECE + error-set overlap + Pareto atlas | torch + probe sets | whether geometry-preserving methods dominate transfer/robustness at matched accuracy / single-model-family generality |
| E12 | **Tangent-projected quantization** (notes/09 H1): project quant error onto activation tangent space vs random equal-norm | torch | manifold-aware quantization exists / mechanism generality |
| E13 | **ID-matched rank allocation** (H2): hunchback-aware per-layer budgets vs uniform at fixed total rank | torch + TWO-NN | Q5 / estimator-dependence of ID |
| E14 | **Grassmannian distillation** (H3): subspace-angle + CKA + D_M losses vs logit-KD; few-shot transfer probes | torch | geometry-targeted KD preserves transfer / whether logit fidelity suffers |
| E15 | **Regime detector**: NTK-stability/parameter-distance pre-screen deciding kernel-regime vs feature-regime compression criteria | numpy | the two theories apply where predicted / threshold calibration is empirical |
| E16 | **Sheaf neural calibration**: learn restriction maps between substrate stalks on overlapping environmental states; JL-packed calibration codes decoded by tiny SAE | numpy/torch | Q1/Q3 at ML scale / SAE feature causality (flagged [C] in literature) |
| E17 | **Recurrence-ablation ladder**: feedforward vs Elman vs reservoir feature extractors feeding the six-signal audit on synthetic tipping series | numpy | Q8 / synthetic-series realism |
| E18 | **Workspace probe**: global-workspace-style shared bus architecture vs pipelined MLP on multi-task benchmarks; score Butlin B1–B4 / VK1–VK3 checklists mechanically | torch | architectural indicator-property scoring is operationalizable / **NOT machine consciousness** |

### Tier 3 — hardware, months
| # | Experiment | Apparatus | Shows / does not show |
|---|---|---|---|
| E19 | **Morphogenetic bond-graph compile**: compile target voltage pattern into gap-junction-style RC network (GBCB emitter → KiCad); verify relaxation to setpoint under perturbation | GBCB + RP2040 + resistor/cap array | Q7's "compile the what" works for a 4×4 grid / scalability to real morphologies |
| E20 | **Additive sensor bus on one wire**: frequency-multiplexed EM+thermal+mechanical channels on a single RP2040 ADC line; decode via Q4 capacity rules | RP2040 + analog front-end | practical overlay count on real hardware / nothing about wireless/multi-node |
| E21 | **Federated octopus control**: segmented per-sucker-style controllers on a MicroPython sensor chain with stigmergic shared state (no central node) | 3–5 RP2040 nodes | distributed resilience under node loss / real-time guarantees |
| E22 | **Ledger-anchored telemetry loop**: GBCB serial_csv → CDT ledger entries with Merkle batch certificates; BMC-checked invariants in CI | GBCB + CDT | tamper-evident continuous hardware falsification works end-to-end / tamper-*proof* (needs signatures, documented boundary) |

---

## C. Places to explore (under-mapped territory)

1. **Sheaf Laplacian as universal consistency layer** — nobody has wired cellular-sheaf consistency into sensor calibration gates; the math is ready (Curry, Hansen–Ghrist) and stdlib-computable.
2. **Integral feedback as calibration primitive** — biology's most robust control result is absent from sensor-calibration engineering practice.
3. **Overlay capacity bounds for physical substrates** — VSA's √d has no analog published for multiplexed analog sensor channels; a measured bound would be a genuine contribution.
4. **Chart-aware compression** — SliceGPT uses one global PCA basis per block; atlas-style *multi-chart* compression (different bases in different input regions, glued by gating) is unexplored.
5. **Citation-bias early warning** — the Karst et al. wood-wide-web audit was manual; the ledger + reference-rot + escape-hatch stack could automate detection of positive-citation cascades. Apply first to the fungal-language literature as a case study.
6. **Marker-battery methodology for non-biological systems** — Cogitate-style pre-registered divergent-prediction batteries applied to *engineering* collapse prediction (not consciousness): two competing cascade theories, kill criteria, independent execution. The hypothesis-engine GitHub Action is already the right chassis.
7. **Anti-unification as repair operator** — least-general-generalization search as the mechanism behind CDT's hitting-set repair: when claims conflict, retract to their coarsest common generalization instead of deleting.
