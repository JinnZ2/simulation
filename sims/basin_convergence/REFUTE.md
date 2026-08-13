# Refutation condition — basin_convergence

**Written before this harness run**, and before `run.py` existed.

This is an **audit of a SUPPORTED result**, not a successor to a refuted one. `fractal_basin`
passed all three of its pre-committed conditions at 5/5 seeds and reproduced
`research/notes/17_fractals_bio_cosmo_trig.md` §1 to three significant figures. Its own FINDINGS.md
then listed, under caveats not eliminated:

> **No convergence check in grid resolution N or integration time T.** Both are fixed at N = 200,
> T = 120. An α that moves with N is measuring the grid, not the dynamics. This is the first thing
> a follow-up should nail down.

This is that follow-up. An unaudited SUPPORTED verdict is the most dangerous entry in a ledger,
because nothing downstream will question it.

Generation 0, `MEASURE` — a fresh claim about the measurement, pre-registered before running, not
a reformulation. `explore.py` would have refused to recycle `fractal_basin` at all, correctly.

## Claim under test

The uncertainty exponent for the triple-well basin boundary is converged in both discretization
parameters: doubling the grid resolution (200 → 400) or the integration time (120 → 240) changes α
by less than 0.05, at every damping swept.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept γ

1. **`|alpha(2N) − alpha(N)| >= 0.05`** — α depends on grid resolution.
2. **`|alpha(2T) − alpha(T)| >= 0.05`** — α depends on integration time.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept γ

- `|Δ_N| < 0.05`, **and**
- `|Δ_T| < 0.05`.

## Otherwise

INCONCLUSIVE, naming which parameter and which γ. Convergence at low damping but not high (or the
reverse) is a real and specific finding: it would say the parent's γ sweep — its headline result,
α moving 0.25 → 0.55 — is partly a discretization artifact at one end, and would identify which end.

## Why 0.05

The parent's verdict turned on three margins: α_triple below 0.90, a gap of at least 0.10 between
double and triple, and 0.20 above the shuffled floor. Its measured seed-to-seed scatter was about
0.01.

0.05 is half the smallest margin the parent's verdict depended on. A discretization error larger
than that could move the parent's conclusion; smaller than that could not. The number is chosen
against the claim it is auditing, not against convenience.

The null reports the reseed scatter at base resolution so 0.05 can be read against the measurement's
own noise floor rather than taken on faith.

## What a REFUTED verdict here would mean

That `fractal_basin`'s SUPPORTED verdict is not yet safe to build on, and that the notes/17 numbers
(α = 0.69 / 0.39, Wada 8%) — which this repo replicated exactly — are properties of a 200×200 grid
integrated for 120 time units, not of the potential. Both runs would have been reproducibly wrong
in the same way, which is precisely what a replication cannot catch and a convergence check can.

## Secondary, no threshold attached

Wada fraction at each resolution and integration time, reported ungraded. The parent found it
collapsing from 37% at γ = 0.1 to exactly 0% at γ = 0.5; whether that collapse is also
resolution-dependent is worth seeing, but locating the threshold is a separate claim and a separate
pre-registration.
