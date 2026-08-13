# Null model — basin_convergence

**Null model name:** `same_resolution_reseed`

## What the null does

Re-measure the uncertainty exponent at the **unchanged** grid resolution and integration time,
using a different probe seed. Nothing about the dynamics or the discretization moves; only the
random probing does.

## What result would mean "no effect"

This sim asks whether α is converged — whether doubling the grid or the integration time changes it.
The answer is a difference, and a difference is only meaningful against the noise floor of the
measurement that produced it.

α is estimated from a log-log fit over 8 probe scales with 4000 random probe pairs each. That
estimate has its own scatter. If doubling N moves α by 0.02 and simply re-probing the *same* grid
also moves it by 0.02, then the resolution change did nothing detectable and the grid was already
fine. If doubling N moves α by 0.15 while re-probing moves it by 0.01, the discretization is
controlling the answer.

So the null establishes **how small a delta is small**. Without it, the pre-committed 0.05
threshold is a number with no scale attached.

## Why this null and not a shuffle

The parent `fractal_basin` used `shuffle_labels`, which asks "is there spatial structure at all."
That question is settled — it measured α ≈ 0.000 exactly as predicted, and this sim inherits that
result rather than repeating it.

The question here is different: not *is the measurement reading structure*, but *is the measurement
reading the dynamics or the grid*. A shuffle cannot answer that; a reseed can.

## What this null does not cover

Resampling scatter is not the only error source. A systematic bias that afflicts every resolution
equally — the log-log fit's sensitivity to the probe-scale range, say, or the choice of 8 octaves —
would be invisible to both the convergence deltas and this null. Convergence in N and T is
necessary for the parent's SUPPORTED verdict to mean what it says. It is not sufficient.
