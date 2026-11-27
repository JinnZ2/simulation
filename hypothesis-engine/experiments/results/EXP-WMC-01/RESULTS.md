# EXP-WMC-01 — Noisy-TV susceptibility across bonus families — RESULTS, stage 1 only (2026-11-27)

Design: [`../../world-models-and-curiosity-driven-learning.md`](../../world-models-and-curiosity-driven-learning.md#exp-wmc-01--noisy-tv-susceptibility-across-bonus-families-matched-conditions)
(issue #67). Code: [`run.py`](run.py). Raw output: [`raw_output.json`](raw_output.json) (per-seed coverage and
time-on-cell for every family × condition), [`stdout.txt`](stdout.txt).

**Stage 1 (tabular pilot) only.** Stage 2 (MiniGrid + PPO, 10 seeds × 5M steps) was **not run** and is
UNCHECKED.

**Verdict (tabular toy): ICM vs count SUPPORTED; "disagreement < 1.5×" FALSIFIED for the pre-specified
ensemble.** Falsifier for H1 NOT met.
- The prediction-error (ICM-style) agent spends 21.8× more time on the distractor cell when it is a noisy
  TV (95% CI 14.2–29.9). Count-based spends exactly 1.0×.
- Ensemble disagreement spends 6.8× more (3.4–11.9), which breaks the "disagreement < 1.5×" part.
- A post-hoc variant whose members converge (sample averages instead of EMAs) gets 1.5× (1.2–1.9).
  It wasn't pre-registered and is reported only as exploratory.

## Run record
- Commit `f5284363f777551d8b2d09ead1ff88de6fd0cbbf`. Python 3.14.8, numpy 2.5.5, Linux x86_64, Intel Xeon @
  2.90 GHz (shared, load about 28). Runtime 202.8 s (4 processes).
- Seeds 20261127–20261156 (30, as designed). Each seed fixes the start, TV location and symbol map, and
  is paired across the TV and no-TV conditions. The agent, TV-noise and RND-target RNG streams are
  separate, so environment draws are identical across conditions and families.

## Deviations (recorded before results)
1. **No-TV control added.** The sketch only has the TV present. With the TV absent, the designated cell
   emits its fixed symbol like every other cell, and we still count the time spent on it.
2. **Families**: none, count, ICM (the sketch's `pred_error`), RND and ensemble disagreement (K = 5
   tabular forward models with Bernoulli(0.5) update masks, EMA lr = 0.2 like the ICM model;
   disagreement = K × the mean across-member variance of the predicted probabilities). RND and
   disagreement aren't in the sketch; they were written for this run. LP uses windows 1 and 10 visits.
   The LP arm is unvalidated, as the design warns.
3. **RND here is weak by construction.** Its input is the observation symbol (8 symbols shared by all
   225 cells), so its predictor learns all 8 targets quickly. It isn't a test of RND as used on pixels.
4. **No bonus-scale tuning**: actions are argmax over the bonus, so scale is irrelevant in this toy.
   **No downstream extrinsic return**: the toy has no reward. Coverage is reported but saturates at 1.0
   for every bonus agent at T = 3000, so it doesn't discriminate.
5. **Bug fix before the reported run**: in the first run, both LP windows used the oldest stored error
   (up to 10 visits back), so lp_w1 = lp_w10. Fixed (`h[-w]`) and everything was rerun. All other arms
   reproduced bit-for-bit. The first run's output is kept in
   [`stdout_first_run_lp_bug.txt`](stdout_first_run_lp_bug.txt). During the same rerun I added `disagree_avg` as a **post-hoc exploratory**
   arm after seeing the EMA-ensemble result. It isn't part of the pre-registered test.

## Results (30 paired seeds, T = 3000, 15×15 grid; uniform-random share of one cell = 1/225 = 0.0044)

| Family | Time on cell, TV | Time on cell, no TV | Ratio TV / no TV [95% CI] | Interaction vs count, Δ fraction [95% CI] | Coverage TV / no TV |
|---|---|---|---|---|---|
| none (random) | 0.0050 | 0.0050 | 1.00 [1.00, 1.00] | 0.000 | 0.976 / 0.976 |
| count | 0.0044 | 0.0044 | **1.00 [1.00, 1.00]** | — | 1.000 / 1.000 |
| ICM (pred. error) | 0.0953 | 0.0044 | **21.8 [14.2, 29.9]** | +0.091 [+0.058, +0.127] | 1.000 / 1.000 |
| RND (obs symbol) | 0.0042 | 0.0040 | 1.04 [0.93, 1.16] | +0.000 [−0.000, +0.001] | 1.000 / 1.000 |
| disagreement (EMA members) | 0.0219 | 0.0032 | **6.75 [3.38, 11.91]** | +0.019 [+0.009, +0.031] | 1.000 / 1.000 |
| LP, window 1 | 0.0009 | 0.0037 | 0.24 [0.19, 0.29] | −0.003 [−0.004, −0.002] | 0.496 / 0.493 |
| LP, window 10 | 0.0022 | 0.0044 | 0.50 [0.39, 0.60] | −0.002 [−0.003, −0.001] | 0.410 / 0.407 |
| *disagreement, averaging members (post hoc)* | 0.0057 | 0.0038 | 1.50 [1.19, 1.91] | +0.002 [+0.001, +0.003] | 1.000 / 1.000 |

CIs come from a seed-level bootstrap (10,000 resamples). Count's trajectory doesn't depend on
observations, so it is identical with and without the TV and its CI is degenerate.

## Pre-registered prediction vs result
- ICM ratio > 3×: **met** (21.8×, CI lower bound 14.2).
- Count ratio < 1.5×: **met** (1.00×).
- Disagreement ratio < 1.5×: **not met** (6.75×, CI lower bound 3.4) for the ensemble specified before the
  run.
- Falsifier (ICM's ratio within count's CI): **not met**. The ICM × distractor interaction is clearly
  non-zero, so H0 is rejected for ICM vs count.

## What this establishes, and what it doesn't
- In a tabular toy, a prediction-error bonus is captured by an irreducible-noise cell (about 9.5% of all
  steps on one of 225 cells), while a count bonus is unaffected. That reproduces the noisy-TV effect in
  its simplest form.
- Ensemble disagreement is robust to the noisy TV only if the members converge. With constant-step-size
  (EMA) members, disagreement on the TV cell never decays and the agent is attracted to it. The
  post-hoc averaging variant suggests that convergence is the relevant factor, but it wasn't
  pre-registered and needs its own test.
- The LP agents in this toy stop exploring (coverage 0.41–0.50) and avoid the TV. They aren't a
  validated learning-progress implementation.
- It doesn't establish anything about deep curiosity agents, MiniGrid, pixel observations or active
  inference (stage 2, UNCHECKED). It says nothing about downstream return.

## Design note (2026-11-27)
The design's "disagreement < 1.5×" prediction implicitly assumes ensemble members whose predictions
converge on stochastic transitions (e.g. trained to convergence, or with decaying step sizes). That
assumption should be stated, and the step-size schedule made a factor, in stage 2. The design text is
unchanged.
