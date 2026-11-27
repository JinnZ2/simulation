# Experiment results — 2026-11-27

Runs of the laptop-CPU-tier experiments designed in [`../`](../README.md), against `main` at
`f5284363f777551d8b2d09ead1ff88de6fd0cbbf` (engine digest 2026-11-26). Each folder has `run.py` (fixed
seeds), the raw output, and a `RESULTS.md`. That file lists deviations first, then the environment,
results against the pre-registered prediction, what the result does and doesn't establish, and any
dated design note. The design files themselves are unchanged.

Environment: Python 3.14.8, numpy 2.5.5, scipy 1.18.1, scikit-learn 1.9.1, tigramite 5.2.10.1, on a
4-vCPU Intel Xeon @ 2.90 GHz (Linux 6.1.155). **The machine was shared** with other jobs (load average
4–28), which mainly affects runtimes and invalidated the SSP-01 timings. Shared helpers:
[`common.py`](common.py). Toy results are toy results. None of these runs touches a real LLM.

| Experiment | Issue | Scale | Verdict | Key number |
|---|---|---|---|---|
| [EXP-ENG-04](EXP-ENG-04/RESULTS.md) NEW HYPOTHESIS replay | #58 | full | **SUPPORTED** | Flagged in 203/203 topic-runs after first crossing, incl. 152/152 with 0 new on-topic findings; the alternative rules are also 100% once crossed |
| [EXP-HVD-01](EXP-HVD-01/RESULTS.md) engine hidden-variable rule, operating characteristics | #59 | full | Part 1 **SUPPORTED**; part 2 **FALSIFIED** at φ ≥ 0.9 | engine_abs power < 0.5 in 100% of n ≤ 200 cells; permutation FPR 0.104 at φ = 0.99 |
| [EXP-HVD-02](EXP-HVD-02/RESULTS.md) residual screen vs LPCMCI | #60 | PILOT (20/100 datasets) | **FALSIFIED** (generator favours the screen) | Screen recall 0.99 vs LPCMCI 0.14–0.22 at matched FPR |
| [EXP-HVD-03](EXP-HVD-03/RESULTS.md) planted signal in engine data | #61 | full | a < b **SUPPORTED**; b ≥ 60% threshold **INCONCLUSIVE** | k = 2: engine 1%, variant 55.5% [48.6, 62.2] at FPR 4.5% |
| [EXP-RGC-01](EXP-RGC-01/RESULTS.md) CKA/Procrustes instrument validation | #62 | (i)–(ii) full; (iii) PILOT | **SUPPORTED** (debiased CKA); whitened CKA **FALSIFIED** | Debiased p95 \|CKA\| ≤ 0.0015 on random pairs at n = 2000; whitened misorders 12/12 cells |
| [EXP-AAQ-02](EXP-AAQ-02/RESULTS.md) AWQ mechanism ablation | #45 | PILOT (synthetic layers) | **SUPPORTED** (toy); Hadamard sub-prediction not supported | Permuted/true MSE ratio 2.21 (10/10 layers) |
| [EXP-CCO-01](EXP-CCO-01/RESULTS.md) prune/quantize order vs margin | #50 | PILOT (toy MLP, RTN only) | **INCONCLUSIVE** (underpowered at 5 seeds) | s = 90%, b = 3, interleaved: +8.0 pp [−0.1, +16.2] at 5 seeds; +10.0 [+6.5, +13.4] at 20 (not pre-registered) |
| [EXP-WMC-01](EXP-WMC-01/RESULTS.md) noisy-TV across bonus families | #67 | stage 1 (tabular) | ICM vs count **SUPPORTED**; disagreement < 1.5× **FALSIFIED** | Time-on-TV ratio: ICM 21.8× [14.2, 29.9], count 1.0×, disagreement 6.75× [3.4, 11.9] |
| [EXP-SSP-01](EXP-SSP-01/RESULTS.md) sparse-kernel factorial, CPU arm | #65 | PILOT (reduced grid) | **INCONCLUSIVE** (timings invalid under contention) | Same-FLOP masked-dense control showed a spurious 2.5× "speedup" |

## Not run
- **Needs human labels**: EXP-ENG-01 (#55), EXP-ENG-02 (#56), EXP-CAL-01 (#47). EXP-ENG-03 (#57) is
  network-tier, but its outcome is the human-labelled on-topic rate.
- **GPU, LLM, cluster or edge-device tiers**: AAQ-01, AAQ-03, CAL-02, CAL-03, CCO-02, DCM-01 (1B LLM on CPU and
  GPU), DCM-02, DCM-03 (edge devices), RGC-02, RGC-03, SSP-02, WMC-02. Also not run: the real-scale
  stages of AAQ-02, CCO-01, RGC-01 (iii), WMC-01 (stage 2) and SSP-01 (GPU arm and full CPU grid).
