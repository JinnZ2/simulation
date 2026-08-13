# research/

Consolidated research bundle for the JinnZ2 repo ecosystem, imported 2026-08-13 from the
`OKComputer_Complexity_Engineering__Robotics_Plan` archive, plus the NN-compression research
charter (`TODO.md`).

This folder is **reference and planning material**. Nothing here is wired into this repo's
simulation code (`assumption_lab.py`, `culture_ontology_notes.py`); it documents work targeting
several other repos in the ecosystem.

## Contents

### Charter / active TODO
| File | What it is |
|---|---|
| `TODO.md` | NN compression as an empirical research program — metrics, anchor papers, compression arms, geometric probes, five hypotheses, minimal reproducible study, Pareto-atlas deliverable |

> Read `TODO.md` against `notes/09_nn_compression_manifolds.md` §1.2, which records verification
> corrections to the memo the TODO was written from (notably: the "prune-first is universally
> optimal" claim is refuted; use the Progressive Intensity Hypothesis framing instead). Where the
> two disagree, notes/09 is the verified source.

### Plans
| File | What it is |
|---|---|
| `plan.md` | The multi-phase research plan that produced this bundle (Stages 1–3, Phases 2, 3, 6) |
| `PLAN_FORWARD.md` | Roadmap for curly-octo-happiness × complexity engineering / cybernetics / robotics — Phase 0 grounding through VSM instantiation |
| `HARDWARE_INTEGRATION_PLAN.md` | curly-octo-happiness × Geometric-to-Binary-Computational-Bridge; gap table G1–G12, stdlib-only / phone-or-Pi / parts-scarce constraint |
| `CROSS_DOMAIN_TOOLKIT_PROPOSALS.md` | Prioritized P0/P1 proposals for Cross-Domain-Toolkit (subjective logic, D-S conflict mass, EigenTrust, cusp-domain example pack) |

### Notes
| File | Domain |
|---|---|
| `notes/00_INDEX.md` | Index + cross-cutting thesis for notes 01–05 |
| `notes/01_newest_hypotheses.md` | Epistemic grounding, falsification, calibration, self-model hypotheses |
| `notes/02_ai_training.md` | Learning/update rules, confidence propagation, RLVR/GRPO, optimizers, scaling laws |
| `notes/03_transformer_design.md` | Gray-code bitstream encodings, attention variants, MoE, norm-free design |
| `notes/04_neural_architecture.md` | GAE/HND/FDM diagnostics, geometric inference, NAS, KAN, MoE routing, hidden-variable discovery |
| `notes/05_learning_simulation_design.md` | World models, curiosity, dreams, skill libraries, falsification-driven environments |
| `notes/06_complexity_cybernetics_robotics.md` | Effective complexity, ε-machines, SOC, scale-free fragility, antifragility, VSM, causal emergence |
| `notes/07_MCPM_collapse_research.md` | Grounding for the collapse metric M(S); calibration sources per term |
| `notes/08_cross_domain_toolkit.md` | Code-verified deep-read + 30-domain equation atlas + logic/knowledge-systems layer |
| `notes/09_nn_compression_manifolds.md` | Compression science verified (GPTQ/AWQ/SparseGPT exact numbers) + manifold/representation geometry |
| `notes/10_integration_theories_languages.md` | Perceptron & integration theories; language/stack strategy |

### Integration
| File | What it is |
|---|---|
| `integration/INTEGRATION_POINTS.md` | Cross-repo integration matrix (IP-1 …) across COH, hypothesis-engine, GBCB, MCPM, CDT |

### Drop-in code — promoted out of this folder

The hypothesis engine that shipped in this bundle now lives at the repo root as
[`../hypothesis-engine/`](../hypothesis-engine/), with its workflow at
`.github/workflows/hypothesis-engine.yml`. It is a running piece, not reference material, so it
was moved out. Its topics config now carries one topic per hypothesis in `TODO.md`.

## The five repos this material targets

| Repo | Role |
|---|---|
| curly-octo-happiness (COH) | AI/learning science core — claim epistemics, Gray-coded bitstreams, GAE/HND/FDM diagnostics |
| hypothesis-engine (HE) | Automation layer — explore→log→claim→test→modify→hidden-variables→consolidate |
| Geometric-to-Binary-Computational-Bridge (GBCB) | Hardware bridge — bond-graph IR, emitters, verify loop, GEIS encoder |
| Mathematical-collapse-prevention-model (MCPM) | Collapse metric M(S), BLACK/RED/AMBER/GREEN verdicts |
| Cross-Domain-Toolkit (CDT) | Portable kernels — falsification ledger, multi-substrate calibration, cascade regime audit |

## Known gaps in this bundle

- **Phase 7 outputs are missing.** `TODO.md`'s session log describes
  `notes/11_meta_structures_consciousness_bio_intelligence.md` and
  `integration/EXPLORE_AND_EXPERIMENT.md`; neither is in the archive. The bundle stops at Phase 6.
- Several documents reference `/mnt/agents/output/...` paths from the workspace that produced them.
  Those paths correspond to this folder's root — mentally substitute `research/`.
- Citations in `TODO.md` are still bracketed placeholders (`[ieee]`, `[arxiv]`, …). `notes/09` has
  the resolved versions for the compression papers.
