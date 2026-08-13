# Findings — basin_convergence

**Verdict: REFUTED.** Doubling the grid resolution moves α by 0.08–0.15 at 5 of 5 seeds in every
swept damping. The pre-committed limit was 0.05.

## The numbers

| γ | α at N=200 | α at N=400 | Δ_N | Δ_T | reseed noise floor |
|---|---:|---:|---:|---:|---:|
| 0.10 | 0.254 | 0.341 | 0.082 – 0.093 | **0.000** | 0.001 – 0.017 |
| 0.25 | 0.392 | 0.516 | 0.118 – 0.134 | **0.000** | 0.000 – 0.015 |
| 0.50 | 0.540 | 0.675 | 0.095 – 0.150 | **0.000** | 0.002 – 0.019 |

The null did exactly the job it was there for. Re-probing the same grid moves α by 0.001–0.019, so
the resolution effect is **5 to 100 times the measurement's own noise floor**. This is not a
marginal call.

**Integration time is fine.** Δ_T is exactly 0.000 everywhere — by T = 120 the trajectories have
settled into their wells and running to 240 changes no label. One of the two audited parameters is
converged and one is not, which is a more useful answer than a single pass/fail.

## What this means for the parent, precisely

`fractal_basin`'s α values are **resolution-dependent**, and α rises consistently with resolution:
the boundary looks *less* fractal the finer you measure it. Whether it converges to something below
1, or keeps climbing toward the smooth-boundary value, is not determined by two resolutions.

Being careful about what does *not* follow: the parent's verdict is not automatically overturned.
Its three conditions at N = 400 stand as far as measured — α_triple = 0.675 is still below the 0.90
ceiling, and still far above the shuffled floor of ≈ 0. But the second condition, the 0.10 gap
between double-well and triple-well α, **was not tested here** — this run measured the triple-well
grid only. Two of the three margins have shrunk; the third is unmeasured.

So the correct statement is: *the parent's numbers are artifacts of the grid; whether its verdict
survives at finer resolution is untested.* Measuring α_double at N = 400 is a cheap next step and
would settle it.

## The Wada result is the sharper casualty

Reported ungraded, but it moves more than α does:

| γ | Wada at N=200 | Wada at N=400 |
|---|---:|---:|
| 0.10 | 37.4% | **16.4%** |
| 0.25 | 8.0% | **0.0%** |
| 0.50 | 0.0% | 0.0% |

The "8% of boundary cells touch all three basins at γ = 0.25" figure — which appears in
`research/notes/17_fractals_bio_cosmo_trig.md` §1 and which this repo replicated exactly — **drops
to zero when the grid is doubled.** On this evidence it is a discretization artifact. A Wada test
counts labels in a fixed-radius neighbourhood; at coarse resolution that neighbourhood spans more
of the phase space and picks up more basins.

## Why this run existed

This is the case the harness is built for, and it is worth stating plainly.

`fractal_basin` was SUPPORTED at 5/5 seeds. It reproduced the notes/17 numbers to three significant
figures from an independent reimplementation. By every check available at the time it looked solid,
and the replication made it look more solid.

**Replication cannot catch a shared discretization error.** Two implementations of the same
algorithm at the same grid resolution will agree on the same wrong number, and their agreement will
be read as confirmation. That is exactly what happened here: this repo's exact match with notes/17
was evidence the code was faithful, and no evidence at all that the number was right.

Only varying the discretization catches it, and nothing but a deliberate convergence audit varies
the discretization. `fractal_basin`'s own FINDINGS listed this as the first thing a follow-up should
nail down; it took one run to go from SUPPORTED-and-replicated to refuted-in-the-measurement.

## What should happen next

1. **N = 800 at γ = 0.25**, to see whether α is converging or still climbing. Three points settle
   the shape; two cannot.
2. **α_double at N = 400**, to determine whether the parent's gap condition survives.
3. **Amend the parent.** `fractal_basin/FINDINGS.md` should carry a pointer to this result so its
   SUPPORTED verdict is not read without it. The ledger keeps both entries; the reader needs the
   link.
4. **notes/17 §1's numbers should be requalified** as measured at N = 200, not as properties of the
   potential — particularly the Wada figure.
