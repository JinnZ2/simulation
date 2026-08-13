# Findings — fractal_basin

> **Amendment, added after `basin_convergence` ran.** The caveat below about missing convergence
> checks turned out to be the important one. `sims/basin_convergence` measured it: **α is not
> converged in grid resolution.** Doubling N from 200 to 400 moves α by 0.08–0.15 at 5/5 seeds in
> every γ, against a reseed noise floor of 0.001–0.019. Integration time is fine (Δ = 0.000).
> The Wada fraction at γ = 0.25 goes from 8% to **0%** when the grid is doubled.
>
> The verdict below is not withdrawn — its three conditions were graded as pre-committed, and two
> of them still hold at N = 400 (the third, the double/triple gap, was not measured there). But the
> α and Wada *values* reported here are properties of a 200×200 grid, not of the potential, and the
> exact agreement with notes/17 §1 is evidence of a faithful reimplementation rather than of a
> correct number. See [`../basin_convergence/FINDINGS.md`](../basin_convergence/FINDINGS.md).


**Verdict: SUPPORTED.** All three pre-committed conditions met at 5 of 5 seeds, in all three swept
damping values.

## The measured numbers

| γ | α_double | α_triple | gap | α_null | D_boundary (triple) | Wada |
|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 0.463 ± 0.010 | 0.250 ± 0.004 | 0.212 | 0.000 | 1.750 | 0.374 |
| 0.25 | 0.691 ± 0.009 | 0.390 ± 0.004 | 0.301 | 0.000 | 1.610 | 0.080 |
| 0.50 | 0.812 ± 0.013 | 0.548 ± 0.007 | 0.264 | −0.001 | 1.452 | 0.000 |

Seed-to-seed scatter is around 0.01 — an order of magnitude below every threshold the verdict
turns on, so the grade is not resting on estimator noise.

**The null behaved exactly as pre-registered.** `NULL.md` predicted α ≈ 0 for a spatially shuffled
grid, on the argument that whether two cells share a label becomes independent of their separation.
Measured: 0.000 ± 0.002 across all 15 null runs. That is a genuine check on the estimator, not a
formality — it means the α measurement is reading spatial structure and not an artefact of the
probing procedure.

## The damping sweep was the right thing to insist on

HARNESS.md §5 item 4 flagged that the original measured α at a single damping. It was right to:
**α depends strongly on γ.** The triple-well boundary dimension falls from 1.75 to 1.45 as damping
goes from 0.1 to 0.5, and the Wada fraction collapses from 37% to exactly zero.

Reported at γ = 0.25 alone, "D = 1.61, 8% Wada" would have read as a property of the potential. It
is not. It is a property of the potential *at that damping*. Stronger damping pulls trajectories
into wells before they can be flung across the boundary, and the fine structure disappears.

The Wada result is the sharper version: at γ = 0.5 **no boundary cell touches all three basins**.
The Wada property is not a fact about the three-well potential; it is a fact about the three-well
potential below some damping threshold between 0.25 and 0.5. Locating that threshold is an obvious
follow-up, and would need its own pre-registration.

## Where the claim prose overreached

The claim registered in `config.json` says, in part, *"and the two-well boundary is not fractal."*

**The data does not support that clause.** α_double is 0.46 at γ = 0.1 and 0.69 at γ = 0.25 — far
from the smooth-boundary value of 1. The two-well boundary is *also* fractal at low damping; it is
merely *less* fractal than the three-well one.

This did not change the verdict, and it must not: the three pre-committed conditions in `REFUTE.md`
tested (a) α_triple below the smooth ceiling, (b) a gap of at least 0.10 between double and triple,
and (c) α_triple above the shuffled floor. All three passed on their own terms, and the gap
condition is the one that carries the "third well adds complexity" content. The overreach is in the
English sentence in `config.json`, which asserted something the refutation conditions never tested.

Recording it here rather than quietly rewriting the claim, per HARNESS.md §4. **The lesson is about
the harness, not the physics:** a `claim` field can smuggle in assertions that no `refute_if` covers.
Anything in the claim prose that matters should have a matching numbered condition, or it should
not be in the claim.

If "the two-well boundary is smooth" is worth testing, it is a new pre-registration with a
condition like `alpha_double >= 0.90 at ≥4/5 seeds`. On this data that condition would fail at
every damping tested.

## Caveats not eliminated

Stated so the SUPPORTED grade is not read as more than it is:

- **No convergence check in grid resolution N or integration time T.** Both are fixed at N = 200,
  T = 120. An α that moves with N is measuring the grid, not the dynamics. This is the first thing
  a follow-up should nail down.
- **α is a log-log slope over 8 probe scales**, the standard estimator, but no confidence interval
  is attached beyond the seed spread.
- **The double/triple comparison is not like-for-like**: the two potentials are evaluated over
  different phase-space windows (`x ∈ [0.6, 2.4]` vs `[0.4, 3.6]`), inherited from the original.
  The gap condition therefore compares two boundaries sampled at different spatial scales. This
  weakens the gap result and should be equalized before the comparison is leaned on.

That last one is the most serious, and it was inherited rather than introduced. It does not
invalidate the α_triple measurements, which stand on their own against the null.
