# Null model — kappa_eff_g2

**Null model name:** `random_ray`

Unchanged from generations 1 and 2's parent: a random unit direction in weight space, everything
else identical. The control was never the problem in this lineage.

## What the null does

`kappa_eff` measured along `θ₀ + α·v` with `v` a random unit vector instead of the normalized
gradient of the regularized objective. Same trained network, same finite-difference HVP at
`eps = 1e-4`, same α grid, same matched-damage comparison.

## What result would mean "no effect"

Leaving a minimum in *any* direction eventually raises curvature and lowers accuracy. The claim is
about the ascent direction specifically, so the null asks whether the direction carries information
at all.

Both rays are evaluated at **their own** 5-point accuracy drop, so the comparison is at matched
damage rather than at matched α. Generation 1 established why: rays that wreck the model at
different rates are not comparable on an α axis, and comparing raw lead there handed the random ray
a spurious advantage.

`kappa_ratio_at_drop = kappa(α_drop) / kappa(0)` per ray. If the gradient ray's curvature has risen
further by the time the model is equally broken, the direction is informative. If not, it isn't.

## The null this generation adds: a minimum that exists

The deeper control here is not a direction, it is the **objective**.

Generation 1 found the networks were not at a minimum — gradient norm 0.57 at width 64 after the
inherited 200-epoch budget, and held-out accuracy *rising* along the ascent ray, which only happens
from an undertrained point. Chasing that turned up something worse: with unregularized
cross-entropy on a training set this network can memorize, **there is no finite minimizer at all.**
Training longer makes the gradient norm go *up* (0.16 → 0.31 at width 16 from 3k to 6k epochs) as
the weights grow without bound.

So "curvature at the minimum" was not a hard measurement in generations 0 and 1. It was an
ill-posed one. There was nothing to be at.

Adding L2 (`weight_decay = 0.01`) makes the objective coercive, so a finite minimizer exists and
can be reached: measured gradient norms are 0.0001–0.007 across all 15 (seed, width) pairs, three
orders of magnitude below the inherited setup.

**`kappa_eff` is measured on the same regularized objective that was minimized**, and the ascent
ray is that objective's gradient. Measuring the curvature of one function at the minimum of a
different one would reintroduce the error this generation exists to fix.

## Ceiling and floor

- Floor: `kappa_ratio_at_drop` equal for both rays.
- Ceiling: the gradient ray's curvature multiplies severalfold while the random ray's stays at 1.0.
