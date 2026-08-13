# Plan: Research + Consolidated Notes from curly-octo-happiness

## Stage 1 — Repo Exploration (explore subagent)
- Clone/browse https://github.com/JinnZ2/curly-octo-happiness
- Inventory files, extract all equations, hypotheses, principles, code-level design ideas
- Output: repo content brief

## Stage 2 — External Research (parallel explore subagents)
- A: Newest hypotheses (2024-2026) in AI/ML theory relevant to repo themes
- B: AI training methods & transformer design advances
- C: Neural architecture & learning simulation design
- Cross-validate findings

## Stage 3 — Consolidated Notes (writing)
- One consolidated notes file per domain: hypotheses, AI training, transformer design, neural architecture, learning simulation design
- Each: equations (LaTeX), principles, research notes tying repo content to literature
- Deliverable: markdown notes in /mnt/agents/output/

## Phase 2 — Complexity Engineering / Cybernetics / Advanced Robotics × repo → plan forward
Stage 1: 3 parallel research agents (complexity engineering; cybernetics; advanced robotics), each briefed with repo architecture summary, asked for equations/principles + concrete interaction points.
Stage 2: Orchestrator synthesizes into notes/06 and a PLAN_FORWARD.md (roadmap: concrete modules to build in the repo).

## Phase 3 — Autonomous Hypothesis Engine (GitHub Action)
Deliverables in /mnt/agents/output/hypothesis-engine/ (drop-in for the repo):
- .github/workflows/hypothesis-engine.yml — scheduled + workflow_dispatch, commits artifacts, opens issue on new hypotheses
- scripts/hypothesis_engine.py — explore→log→claim→test→modify claim→hidden-variable scan→consolidate, using grounding/ package
- config/topics.yml — search topics; docs/hypothesis_engine.md
Coder subagent implements; orchestrator validates spec coverage.

---

## Phase 6 — Integration folder + NN/manifold/language research (2026-08-13)

User input: pasted memo on NN compression as empirical research program (taxonomy, metrics, GPTQ/AWQ/SparseGPT backbone, research matrix, Pareto atlas). Request: deep research into neural networks, manifold possibilities, code languages needed, perceptron integration theories + the memo; deliver a new folder of possible integration points across all repos worked on.

### Stage 1 — Parallel research (4 explore subagents)
- R1: NN compression science — verify/expand memo (GPTQ, AWQ, SparseGPT, order effects, CKA/SVCCA, effective rank, ECE, Pareto methodology); add 2024–2026 developments.
- R2: Manifold possibilities — manifold hypothesis, intrinsic dimension, information geometry, NTK, representation topology, geometric deep learning; what "preserving functional subspaces" means formally.
- R3: Perceptron & integration theories — perceptron convergence, MLP expressivity, signal integration theories (IIT, global workspace, predictive processing, Conant–Ashby), multi-substrate sensor integration theory.
- R4: Code languages — given stdlib-only Python ethos of JinnZ2 ecosystem: when to stay pure-Python vs C/Rust/Julia/WASM/Mojo; embedded (MicroPython/C), accelerator stacks; interoperability patterns (FFI, WASM, IPC/CSV streams).

### Stage 2 — Synthesis (orchestrator)
- /mnt/agents/output/notes/09_nn_compression_manifolds.md (R1+R2 merged)
- /mnt/agents/output/notes/10_integration_theories_languages.md (R3+R4 merged)
- /mnt/agents/output/integration/INTEGRATION_POINTS.md — cross-repo integration matrix across: curly-octo-happiness, hypothesis-engine, Geometric-to-Binary-Computational-Bridge, Mathematical-collapse-prevention-model, Cross-Domain-Toolkit + the new research.
