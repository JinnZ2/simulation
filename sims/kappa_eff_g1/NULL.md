# Null model — kappa_eff_g1

**Null model name:** `random_ray`

Same null as the parent, kept deliberately: a random unit direction in weight space, everything
else identical. It worked. What failed in the parent was the statistic compared across it, not the
control itself.

## What the null does

`kappa_eff` is measured along `θ₀ + α·v` with `v` a random unit vector instead of the normalized
loss gradient. Same network, same finite-difference HVP at `eps = 1e-4`, same α grid.

## What result would mean "no effect"

The claim is that curvature along the *ascent* direction warns of damage. A random ray tests
whether the direction matters at all: in a high-dimensional weight space, leaving a trained minimum
in any direction eventually raises curvature and lowers accuracy.

The parent established what the random ray does here — curvature stays flat (0.152 → 0.016, no
peak) while accuracy falls slowly. So the direction *does* carry information. The parent's problem
was that it compared the two rays on **lead measured in α units**, and the two rays damage the
model at completely different rates. A random ray strolls out of the basin, so its accuracy
collapse arrives at large α and any indicator gets a large, meaningless head start. The gradient
ray wrecks the model fast, compressing everything into small α.

Comparing head starts measured in α across rays with different damage rates is not a comparison.

## The fix: compare at matched damage

Both rays are evaluated at **their own** 5-point accuracy drop. The question becomes:

> by the time each ray has done equal damage, how far has curvature risen from its baseline?

`kappa_ratio_at_drop = kappa(α_drop) / kappa(0)`, computed per ray. If the gradient ray's curvature
has risen further by the time the model is equally broken, the direction carries information about
damage. If both have risen the same amount, it does not.

This puts the two rays on a common axis — accuracy loss — instead of a parameterization that means
different things along each.

## Ceiling and floor

- Floor: `kappa_ratio_at_drop` equal for both rays; direction is irrelevant.
- Ceiling: the gradient ray's curvature has multiplied severalfold while the random ray's is flat
  at 1.0, which is roughly what the parent's raw curves suggest but never tested this way.
