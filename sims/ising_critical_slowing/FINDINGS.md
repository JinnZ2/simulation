# Findings — ising_critical_slowing

Co-authored (2026-11-01). CC0. Synthetic model.

**REFUTED** against the pre-committed condition (4 of 5 seeds fail), mostly on the off-critical
half of the claim.

```text
tau_int of |m| (seed 0)     L=4     L=8     L=16     z over L=4..16 (all seeds)
T = 2.269 (Tc)              3.2     8.9     31.6     1.47 - 1.93   needed >= 1.5 (1 seed below)
T = 3.0                     2.7     3.7     5.1      0.47 - 0.88   needed <  0.5 (4 seeds above)
shuffled floor              ~0.5 everywhere; tau(Tc, 16) = 22-40, far above the 5x floor gate
```

## Reading

- Critical slowing is present and large: from L = 4 to 16, tau at Tc rises about tenfold, at
  T = 3.0 about twofold. The pre-registered split (z >= 1.5 vs z < 0.5) still fails: at these
  sizes the correlation length at T = 3.0 is not small against L, so tau has not saturated yet.
  The threshold encoded an infinite-size expectation on a 4..16 range.
- z(Tc) sits below the published single-spin-Metropolis value (~2.17, VERIFY), as expected
  from small sizes and finite runs.

## G7 (recorded, not graded)

At T = 1.5, ordered and random starts gave tau 1.3-3.2 at every L <= 16 and every seed; mean |m|
0.98-0.99 for both. No domain trapping appeared at these sizes. The first-run value 83 at
T = 1.5, L = 32 (other code) is neither reproduced nor explained here: L = 32 was not run.

## Successor, not an edit (per CLAUDE.md)

A new pre-registration, not a change to this one. Candidates: (a) extend T = 3.0 to L = 32-64
where tau should saturate; (b) grade the GAP z(Tc) - z(T = 3.0) >= 1.0 instead of two absolute
thresholds; (c) add T = 1.5, L = 32 with several random-start replicas for G7. Each needs its
NULL.md and REFUTE.md written before its run.
