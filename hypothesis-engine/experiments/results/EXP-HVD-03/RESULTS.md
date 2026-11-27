# EXP-HVD-03 — Planted-signal recovery on a copy of the engine's data — RESULTS (2026-11-27)

Design: [`../../hidden-variable-detection-causal-discovery-from-residuals.md`](../../hidden-variable-detection-causal-discovery-from-residuals.md#exp-hvd-03--planted-signal-recovery-on-a-copy-of-the-engines-own-data)
(issue #61). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json) (every trial).

**Verdict: H1 (a < b) SUPPORTED. On (b)'s pre-registered threshold the result is INCONCLUSIVE, leaning
short. Falsifier NOT met.**
- At k = 2 the unmodified engine recovered 1% of plants. The signed, aligned, permutation-tested
  variant recovered 55.5% (Wilson 95% CI 48.6–62.2%) at an FPR of 4.5% (2.4–8.3%).
- The prediction "(b) ≥ 60% with FPR ≤ 0.05" isn't met at the point estimate. The CIs include both 60%
  and 5%, so this run can't decide that part.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, Linux x86_64, Intel Xeon
  @ 2.90 GHz (shared). Runtime 77.3 s. Seed `default_rng(20261127)`. 200 trials per k ∈ {0, 1, 2, 4};
  999 permutations.
- `data/claim_tree.json` and `data/findings_log.jsonl` are read into memory only. The engine's
  `stage_hidden` is imported unmodified and writes only to a temp file. The originals were not modified
  (`git status` is clean outside `results/`).

## Deviations and fixed choices (recorded before results)
1. **"Month"** = the engine's own period key, `finding.date[:7]`. For older papers this is a year
   (e.g. "2016"), so the 16 periods are a mix of years and 2026 months.
2. Each trial picks one topic at random and includes each of its periods independently with probability
   0.5 (resampled if none or all are picked). Then `passed += k` for every claim of that topic whose
   finding falls in a picked period. Recovery counts only for the planted topic.
3. (a) counts as recovered if the engine emits a suggestion for the planted topic. Its only candidate
   series is `findings_rate`, so it can't name the planted variable; any suggestion counts in its favour.
4. Added a secondary arm, (a2): the engine's rule (folded residual, i mod M pairing, |r| > 0.5) applied
   directly to the planted indicator. It isn't in the design and is reported separately.
5. k = 0 uses the same random period sets with nothing planted. It gives the FPR of every arm.

## Residuals before planting (threat: ratchet saturation)
Median `passed` = 3 in 5 of 8 topics. In those topics |beta − 0.5| ≈ 0.29 ± 0.06, beta < 0.5 for 0% of
claims, and beta = 0.5 for 1–3%. In HVD and RGC, 61% and 77% of claims sit at exactly 0.5 (never tested).
The engine run on the unplanted data emits no suggestions.

## Results

| k | (a) engine | (a2) engine rule on planted indicator | (b) signed + aligned + permutation | (b) median \|r\| |
|---|---|---|---|---|
| 0 (FPR) | 0.0% [0, 1.9] | 2.0% [0.8, 5.0] | **4.5% [2.4, 8.3]** | 0.14 |
| 1 | 0.0% [0, 1.9] | 0.0% [0, 1.9] | 27.5% [21.8, 34.1] | 0.34 |
| 2 | **1.0% [0.3, 3.6]** | 0.0% [0, 1.9] | **55.5% [48.6, 62.2]** | 0.51 |
| 4 | 0.0% [0, 1.9] | 0.0% [0, 1.9] | 71.5% [64.9, 77.3] | 0.70 |

Effect size at k = 2: (b) − (a) = 54.5 percentage points. The Wilson intervals don't overlap.
(b)'s recovery at k = 2 by planted topic (recovered/trials): AAQ 28/30, HVD 25/31, WMC 19/19, RGC 19/34,
CAL 8/22, SSP 7/18, CCO 5/22, DCM 0/24. With only 6 periods, DCM's indicator has at most C(6, 3) = 20
distinct arrangements, so its minimum permutation p is ≥ 0.05. Recovery there is impossible by
construction.

## Pre-registered prediction vs result
- (a) < 20% at k = 2: **met** (1%).
- (b) ≥ 60% with FPR ≤ 0.05: **not met at the point estimate** (55.5%, FPR 4.5%). Both CIs straddle the
  thresholds, so this part is inconclusive at 200 trials. About 900 trials per k would separate 55% from
  60% with a CI half-width of about ±3%.
- Falsifier ((a) ≥ 60% at k = 2): **not met**.

## What this establishes, and what it doesn't
- It establishes that the engine's hidden stage can't detect a date-aligned shift of +2 passes in its
  own data. Even the engine's threshold rule applied to the true planted series (a2) never fires. The
  rule, not only the candidate choice, is the bottleneck.
- A signed, aligned, permutation-tested variant detects it about half the time at the nominal FPR.
  It does worse on topics with few periods or many untested claims.
- It doesn't establish that any real hidden variable exists, or doesn't, in the engine's history. It
  also says nothing about plants of other shapes (e.g. shifts in `failed`, or source-aligned plants).

## Design note (2026-11-27)
The 60% threshold for (b) was set without a power calculation for this data. Given 6–13 periods per
topic and the ratchet saturation above, about 55% at k = 2 is roughly what a period-level permutation
test can reach. The original design text is unchanged.
