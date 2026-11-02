# Refutation condition — ising_critical_slowing

Co-authored (2026-11-01). CC0. **Written before run.py existed.** Generation 0,
MEASURE. Source: work order WO3 #5(b) and SIMULATION_REGISTER.md G4, G7.

## Model

2-D Ising, periodic L x L, J = 1, single-spin Metropolis, one sweep = L^2 attempted flips.
Burn-in 1000 sweeps; measurement 4000 / 8000 / 16000 sweeps at L = 4 / 8 / 16 (4000 at T = 1.5).
Observable |m|. Integrated autocorrelation time by automatic windowing (window M = smallest with
M >= 6 tau(M)).

## Claim

z, the slope of log tau against log L over L = 4, 8, 16:
- at Tc = 2.269: z >= 1.5 (the published single-spin-Metropolis value is about 2.17 -- VERIFY;
  Nightingale & Bloete 1996)
- at T = 3.0: z < 0.5

## Refute if — either, at >= 3 of 5 seeds

- z(Tc) < 1.5
- z(T = 3.0) >= 0.5

INCONCLUSIVE if tau(Tc, L = 16) < 5 x the shuffled-series floor at >= 2 of 5 seeds (the run
was too short to see memory). SUPPORTED requires both parts at >= 4 of 5 seeds.

## Recorded, not graded (G7)

At T = 1.5 every seed runs from an ORDERED start (all up) and from a RANDOM start, and both tau
values are recorded. The first-run value 83 at T = 1.5, L = 32 (other code) is reported in the
register as a domain-trapping artifact of a random start. Whether trapping happens is a property
of single runs (a random quench gets stuck in stripes in some runs, not others), so it is
recorded per seed rather than graded.

## Scope limit, stated before running

L stops at 16: in pure Python, enough sweeps at L = 32 to resolve tau at Tc would take hours.
z from L = 4..16 includes small-size corrections. A REFUTED from too-short runs would show up
as tau(Tc, 16) near the floor, which the INCONCLUSIVE condition catches.
