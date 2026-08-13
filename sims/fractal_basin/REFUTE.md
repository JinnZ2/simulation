# Refutation condition — fractal_basin

**Written before the sim was run.** Committed to git in advance of any results directory
existing; check `git log` on this file against the timestamps under `results/`. No value here was
chosen after seeing data. If any of it is later edited in light of results, the run becomes
EXPLORATORY and never PREDICT/MEASURE (HARNESS.md §4).

## Claim under test

In a damped oscillator with a three-well potential, the basin boundary is **fractal**: its
uncertainty exponent α is bounded away from the smooth-boundary value of 1, and bounded away from
the structureless null of ≈ 0. The two-well boundary is not fractal. This holds across damping.

## Refute if — any of these, at ≥ 3 of 5 seeds, in any swept γ

1. **`alpha_triple >= 0.90`** — the boundary is indistinguishable from smooth.
2. **`alpha_double - alpha_triple < 0.10`** — the third well buys no additional boundary
   complexity, so "three wells make it fractal" fails.
3. **`alpha_triple - alpha_null < 0.20`** — the triple-well exponent is not meaningfully above the
   shuffled floor, so a low α is not evidence of structure.

Any one of the three is sufficient to refute. They are separate failure modes, not a conjunction.

## Supported requires — all of, at ≥ 4 of 5 seeds, in **every** swept γ

- `alpha_triple < 0.90` (below smooth), **and**
- `alpha_double - alpha_triple >= 0.10` (the third well matters), **and**
- `alpha_triple - alpha_null >= 0.20` (above the structureless floor).

This mirrors HARNESS.md §4: effect in the predicted direction, at ≥ 4/5 seeds, above null by the
pre-committed margin.

## Otherwise

INCONCLUSIVE, with the reason naming which condition failed and where. Per §4, INCONCLUSIVE is a
first-class verdict — a γ-dependent result (fractal at low damping, smooth at high) is a real
finding and must not be rounded to either edge.

## Why these numbers

- **0.90** — α is a noisy estimate from a log-log fit over 8 probe scales. Theory says a smooth
  boundary gives exactly 1; 0.90 leaves roughly a 10% band for estimator noise before we would call
  a smooth boundary fractal.
- **0.10 separation** — smaller than the gap the double/triple contrast should produce if the
  effect is real at all, and larger than the seed-to-seed scatter a 4000-probe estimate should show.
- **0.20 above null** — the null sits at ≈ 0 by construction, so this asks the triple-well exponent
  to be at least a fifth of the way to the smooth value. Below that, the measurement is not
  distinguishing dynamics from noise.

## Sweep

γ ∈ {0.1, 0.25, 0.5}, mandatory. HARNESS.md §5 item 4 flags this sim specifically: the original
measured α at a single damping (γ = 0.25), which cannot show whether the result is a property of
the potential or of one damping choice. The claim above is a claim about *all three*.

## What would make this more than a toy

Not committed to here, listed so it is not mistaken for having been done: convergence of α in grid
resolution N and integration time T. The present run fixes both. A result that moves with N is an
artefact of the grid, not the dynamics.
