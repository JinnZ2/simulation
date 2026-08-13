# Refutation condition — snap_information

**Written before the sim was run.** Committed to git in advance of any results directory existing;
check `git log` on this file against the timestamps under `results/`. No value here was chosen
after seeing data. If any of it is later edited in light of results, the run becomes EXPLORATORY
and never PREDICT/MEASURE (HARNESS.md §4).

## Claim under test

A snap-through event acts as an analogue-to-digital converter: the post-snap ringdown carries
information about the load at which the snap occurred. Measured as mutual information between load
and ringdown frequency, this exceeds a permutation null by a margin that is not attributable to
estimator bias, and it does so across damping.

## Refute if — at ≥ 3 of 5 seeds, in any swept γ

**`MI(load; ringdown) - MI_null < 0.20 bits`**

One condition, one number. If the excess information over a shuffled pairing is below 0.20 bits,
the snap is not reporting the load in any useful sense and the ADC framing fails.

## Supported requires — at ≥ 4 of 5 seeds, in **every** swept γ

**`MI(load; ringdown) - MI_null >= 0.20 bits`**

Per HARNESS.md §4: effect in the predicted direction, at ≥ 4/5 seeds, above null by the
pre-committed margin.

## Otherwise

INCONCLUSIVE, with the reason naming which γ failed and at how many seeds. A result that holds at
light damping and fails at heavy damping is a real finding about the mechanism — heavy damping
kills the ringdown before it can be read — and must be reported as such rather than rounded to
SUPPORTED or REFUTED.

## Why 0.20 bits

The reachable ceiling for this measurement is `log2(5) ≈ 2.32` bits (5 load bins). 0.20 bits is
roughly 9% of that ceiling — small enough that a genuine but weak channel still clears it, large
enough to sit well outside the seed-to-seed scatter expected of a plug-in MI estimate on this
sample size. It is also comfortably above the analytic finite-sample bias for a 5×5 table at this
`n`, which the shuffle should absorb anyway; requiring 0.20 on top of the shuffle is deliberately
conservative.

Stated plainly so it cannot be quietly relaxed later: **0.20 bits, excess over shuffle, ≥ 4/5 seeds,
every γ.**

## Sweep

γ ∈ {0.02, 0.05, 0.10}. The original ran at γ = 0.05 only. Damping is the parameter the claim is
most obviously vulnerable to — a ringdown that decays before the FFT window closes cannot encode
anything — so it is the parameter the claim must be shown robust to.

## Secondary observations, not part of the refutation

Reported because the original asked them, but with no threshold attached and no bearing on the
verdict:

- **Q1** — whether the ringdown frequency implies the landing well's stiffness (`k = (2πf)²`).
- **Q2** — whether snap-from-compression and snap-from-tension leave distinguishable landing
  amplitudes, i.e. one bit of traversal history.

Both are descriptive here. Promoting either to a claim requires its own NULL.md and REFUTE.md.
