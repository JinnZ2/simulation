# Structured sparsity and hardware-matched pruning — what needs to be known, and experiments (EXP-SSP)

Draft read: `hypotheses/structured-sparsity-and-hardware-matched-pruning.md` at
`0419d4791de3e80afd5b028e27475977dce89cd4` (regenerated 2026-11-23T17:01:48Z). Written 2026-11-24.
All experiments PROPOSED. Engine gaps E1–E9: [engine-validity.md](engine-validity.md).

Charter hypothesis (`research/TODO.md` #2): **H2 — structured sparsity wins real latency only when it
matches the accelerator/runtime.** Unstructured pruning can reach high zero counts with little speedup
on dense kernels.

## 1. What the engine claims, and on what evidence

**Headline statement:** "*GPU implementation of mixed quantum-classical Liouville molecular dynamics
without momentum jump* reports: We implemented on GPU a mixed quantum-classical Liouville molecular
dynamics simulation…". NEW HYPOTHESIS, 126 surviving claims. This is a chemistry-simulation paper and
says nothing about H2.

**Evidence base (AUDIT):** 145 findings (129 arXiv); 133 claims; 126 surviving (113 arXiv). A core-term
screen (`prun|sparsit|2:4|N:M`) hits 16/126 survivors and 3/113 arXiv survivors. Those are the lowest
on-topic arXiv rates among the charter topics, consistent with E2 (queries such as
"unstructured sparsity dense kernel acceleration gap" OR-match "gap", "dense", "kernel").

**Source spot-checks** (2026-11-24; beyond-abstract content UNCHECKED):

| Cited as | Exists? | What the abstract shows | Bearing on H2 |
|---|---|---|---|
| SpenseGPT, arXiv:2606.10445 | Yes | 2:4 is "widely supported by modern accelerators, providing up to a 2x theoretical speedup"; strict 50% causes accuracy loss; relaxed formats "require specialized compiler support or introduce runtime overheads that limit end-to-end speedup"; proposes a hybrid 2:4 + dense split compatible with existing GEMM libraries. | Direct and consistent with H2 as a premise. The staked first sentence is background, not their measurement. |
| From 2:4 to 8:16, arXiv:2507.03052 | Yes | 8:16 semi-structured sparsity with outlier handling; storage 0.875 vs 0.75 bits/element. | Accuracy and storage. Latency on real hardware UNCHECKED. |
| InferFast, DOI 10.1145/3797905.3800530 | Yes (Crossref: ICS 2026, 2026-07-05; no abstract in Crossref) | Title: "Bridging the Gap Between Unstructured LLM Sparsity and Practical GPU Throughput". | Possibly a counterexample to H2's "only" (unstructured made fast). Content UNCHECKED. |
| Silent Until Sparse, arXiv:2509.08747 | Cited; not fetched | Backdoors via 2:4. | Off-question (security). UNCHECKED. |
| Headline (quantum-classical MD) | Not fetched | — | None (E2). |

## 2. What science needs to be known

### (a) Gaps the engine recorded
- 12 escape-hatched claims for this topic in `unknown_journal.jsonl`. No refuted claims; no
  hidden-variable suspects.

### (b) Gaps identified here
- **G1. "Matches the runtime" must be defined before measuring, or H2 is circular.** Otherwise any
  observed speedup can be re-described as "matched". Define a match as: the runtime used has a kernel
  that consumes the sparse pattern without materializing the dense matrix (e.g. 2:4 via
  sparse-tensor-core libraries on sm80+ GPUs; block-sparse kernels at the matching block size; a
  narrower dense GEMM for channel pruning).
- **G2. "Wins" needs a reference and a matched-quality condition.** Is the speedup vs dense at equal
  accuracy, or at equal sparsity? H2 as stated compares formats; the useful version compares them at
  matched task quality.
- **G3. Kernel speedup and end-to-end speedup differ.** Attention, KV-cache traffic, dequantization,
  layer norms and launch overhead dilute GEMM gains. Decode (memory-bound) and prefill (compute-bound)
  behave differently, and batch size changes which regime applies.
- **G4. "Only" is a universal claim.** It is falsified by one robust counterexample (a fast unstructured
  kernel such as the InferFast title suggests; content UNCHECKED). So the experiment has to include the
  strongest available unstructured kernels, not only naive CSR.
- **G5. Measurement hygiene.** Warm-up, clock and thermal state, thread count, synchronization, and
  tail (p95/p99) as well as median.

## 3. Experiments

### EXP-SSP-01 — Kernel-level factorial: sparsity format × runtime support × shape
- **Gaps:** G1, G4, G5.
- **H1:** Median GEMM speedup over dense is ≥ 1.1× only in cells pre-registered as runtime-matched.
  **H0:** Speedup doesn't depend on the match label.
- **Variables:** Latency per GEMM, median and p95 over ≥ 100 timed repeats after ≥ 10 warm-ups, with
  device synchronization; bytes resident (values plus indices plus metadata).
- **Design:** Formats: dense; unstructured at 50/70/90% (best available sparse kernel per platform,
  including at least one non-naive kernel); 2:4; block-sparse 32×32 at 50/75%; channel-pruned dense at
  50%. Platforms: one x86 CPU, one Ampere-or-newer GPU. Shapes: d ∈ {2048, 4096, 8192}, batch tokens
  ∈ {1, 16, 256}. Match labels are written into a config file before any timing.
  3 independent sessions (reboot or new process; different times of day).
- **Pre-registered prediction:** Every matched cell shows ≥ 1.1× at d ≥ 4096 and batch ≥ 16, and no
  unmatched cell shows ≥ 1.1× with the session-level 95% CI excluding 1.0. **Falsified if** any
  unmatched cell shows a robust ≥ 1.1× speedup (counterexample to "only"), or if matched 2:4 shows no
  speedup at the largest shapes.
- **Analysis:** Speedup ratio per cell; CI from a session-level bootstrap (sessions are the unit, not
  repeats). Report the full grid.
- **Threats:** BLAS and thread defaults (pin them and record `--env`); GPU clock boost (lock clocks or
  record them); "best available kernel" is a moving target (record library versions).
- **Tier:** CPU arm on a laptop (`sketches/latency_harness.py`); GPU arm on a single GPU, a few hours.
- **Would establish:** Kernel-level support for or against H2 on the tested platforms and libraries.
  **Would not establish:** End-to-end model latency, or other hardware.
- **Sketch:** `sketches/latency_harness.py`. It times one CPU matmul per format, including
  masked-dense and 2:4-in-dense controls with identical FLOPs, and marks the bytes-vs-p50 Pareto set.
  Its numbers are specific to the machine that runs it.

### EXP-SSP-02 — End-to-end at matched quality
- **Gaps:** G2, G3.
- **H1:** At matched held-out perplexity (within ±2% of each other), structured or 2:4 pruned models
  give higher decode tokens/s than unstructured-pruned models on a matched runtime, and the same
  ordering doesn't hold on an unmatched runtime. **H0:** The orderings are the same on both runtimes.
- **Design:** One 1–3B open LLM. Unstructured 50% (Wanda- or SparseGPT-style), 2:4, and structured
  head/channel pruning. Tune each arm's sparsity to hit the shared perplexity target. Short
  recovery fine-tune, identical token budget (e.g. 50M tokens) and 3 seeds per arm. Runtimes: one with
  2:4 kernels on GPU, and the same model on CPU (no sparse support). Measure prefill and decode
  separately, at batch 1 and 16, sequence lengths 512 and 4096.
- **Pre-registered prediction:** On the GPU runtime, 2:4 decode throughput ≥ 1.1× dense and
  > unstructured. On CPU, 2:4 ≈ dense (within 5%). **Falsified if** the ordering is the same on both
  runtimes.
- **Analysis:** Throughput ratios with seed × session bootstrap CIs; perplexity reported alongside so
  the match condition can be audited.
- **Threats:** The perplexity match leaves downstream quality unmatched (report one downstream task);
  structured pruning changes shapes, which can by chance align with faster kernels (record shapes).
- **Tier:** Single GPU, about 1–2 GPU-days (rough).
- **Would establish:** Whether runtime match predicts real speedup at matched quality for one model.
  **Would not establish:** Generality across model families or larger scales.
