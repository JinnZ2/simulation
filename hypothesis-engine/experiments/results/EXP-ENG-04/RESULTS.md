# EXP-ENG-04 — Replay: does NEW HYPOTHESIS track new content? — RESULTS (2026-11-27)

Design: [`../../engine-validity.md`](../../engine-validity.md#exp-eng-04--replay-does-new-hypothesis-track-new-content)
(issue #58). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json).

**Verdict: SUPPORTED** for the pre-registered H1. Under the current rules, every topic stays flagged on
every run after it first crosses 3 survivors, including runs where it received no new on-topic findings.
The alternative rules (b) and (c) produce fewer flags, as predicted, but only by delaying or preventing
the first crossing. Once a topic crosses, they also stay flagged on every later run, so they don't make
the flag track new content either.

## Run record
- Commit: `f5284363f777551d8b2d09ead1ff88de6fd0cbbf` (main, engine run 2026-11-26). Data: `data/findings_log.jsonl`
  (997 findings), read-only.
- Environment: Python 3.14.8, Linux x86_64, Intel Xeon @ 2.90 GHz (4 vCPU, shared with other jobs), stdlib only
  (numpy 2.5.5 present but not used). Runtime 55 s. Deterministic: no random numbers are used.
- Engine code versions: `scripts/` changed in 907c942 (08-13), 72d6b6a (08-18) and 0e1b4a5 (09-06). Diffing
  907c942..HEAD shows that only hashing/fetching and `stage_hidden` changed. Stages 3–5 and the
  stage-7 marker rule are identical across the history, so one replay with the current code is valid
  for all 31 runs.

## Deviations (recorded before results)
1. **Run batches** = findings grouped by `retrieved_at` date (31 batches, 2026-08-17 … 2026-11-26). This is
   how the design defines "run-sized batches". It matches the 31 engine commits to `hypotheses/`.
2. **"New on-topic findings"** uses the lexical core-term screen from `sketches/engine_audit.py`
   (`CORE`). No human labels exist (EXP-ENG-01 hasn't been run). The screen is narrow, so "0 new on-topic"
   means "0 new findings matching the topic's core terms", not a relevance judgement.
3. **Arm (b) detail not fixed by the design**: a (claim, partner) pair is evaluated at most once *ever*,
   including after a claim is reformulated (its text changes, but the pair is not re-tested).
4. **Arm (c) detail**: survival = ≥ 3 distinct supporting partners from ≥ 2 distinct partner sources. The
   engine's `beta ≥ 0.7` shortcut isn't used. Reformulation resets the partner sets.

## Validation of the replay
Arm (a) reproduces the real engine exactly: in all 31 engine commits, the set of flagged topics and the
per-topic surviving counts in `hypotheses/*.md` match the replay. The final surviving counts also match
`data/claim_tree.json` (CAL 218, WMC 119, AAQ 140, SSP 132, CCO 49, HVD 46, DCM 11, RGC 7).

## Results

| Arm | Flags total (31 runs × 8 topics) | Topics ever flagged | Topic-runs after first crossing | …of which flagged | Topic-runs after crossing with 0 new on-topic findings | …of which flagged |
|---|---|---|---|---|---|---|
| (a) current rules | 211 | 8 | 203 | **203 (100%)** | 152 | **152 (100%)** |
| (b) pairs once | 176 | 7 (not RGC) | 169 | 169 (100%) | 122 | 122 (100%) |
| (c) (b) + ≥3 partners, ≥2 sources | 154 | 7 (not RGC) | 147 | 147 (100%) | 109 | 109 (100%) |

First crossing dates under (a): CAL and CCO 08-17, AAQ 08-20, DCM 08-24, HVD 09-06, SSP 09-07, WMC 09-10,
RGC 09-28. Under (c), RGC never crosses (0 survivors at the end), HVD crosses on 10-12 with 3 survivors,
and DCM on 10-12 with 7.

In the last six runs (11-09 … 11-26), 33–38 findings arrived per run, of which 1–6 per run (all topics
together) matched a topic's core terms. All 8 topics were flagged in every one of those runs under (a).

## Pre-registered prediction vs result
- "(a) flags every topic on every run after its first crossing": **yes**, 203/203 topic-runs. The falsifier
  (some topic unflagged in a later run under (a)) was not observed. Escape-hatching never removed
  enough survivors to drop a topic below 3.
- "(b)/(c) flag fewer": **yes** (176 and 154 vs 211). But the reduction comes only from later or absent
  first crossings. After crossing, (b) and (c) are also 100% flagged, including in runs with no new
  on-topic findings. Survival stays absorbing under both, so no rule tested here makes the flag a
  signal of new content.

## What this establishes, and what it doesn't
- It establishes that the NEW HYPOTHESIS marker, and therefore the issue opened on every run, carries
  no information about what arrived in that run. It's a function of whether a topic has ever had ≥ 3
  survivors. This holds for the real history (replay matches it exactly) and is consistent with E6.
- It doesn't establish which rule should replace it. A flag that tracks content needs a rule based on
  *change* (e.g. new survivors since the last run, or a changed headline), not on a level. Choosing one
  is a design decision for the owner, informed by EXP-ENG-02.
- It doesn't establish relevance. "On-topic" here is the lexical screen (deviation 2).
