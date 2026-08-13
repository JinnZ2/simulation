# Findings — snap_information

**Verdict: REFUTED.** Excess mutual information over the permutation null was below the
pre-committed 0.20 bits at 5 of 5 seeds, in all three swept damping values.

The refutation condition was not touched after seeing data. This file diagnoses the result; it does
not revise the grade.

## The measured numbers

Excess MI (`MI(load; ringdown) - MI_null`), all five seeds, every γ:

```
-0.023, -0.065, -0.034, -0.027, -0.046  bits
```

Not merely below 0.20 — **negative**, and negative by more than the seed scatter. The real pairing
carries slightly *less* apparent information than a shuffled pairing. That is the signature of a
channel with no signal in it at all: both numbers are estimator bias, and which one lands higher is
a coin flip.

The second tell: the excess values are **identical to four decimals across γ = 0.02, 0.05 and
0.10.** Damping is the parameter this claim should be most sensitive to. A measurement that does
not move at all when damping changes by 5× is not measuring the dynamics.

## Why: the load cancels out of the equations

The toy model shifts the wells with load by evaluating the force at `x - load`, and starts each
trajectory at `1.2 + load` — that is, at the same position *relative to the shifted well*.

Substitute `u = x - load`:

```
du/dt = v
dv/dt = F(u) - γv          initial condition  u₀ = 1.2,  v₀ = jitter
```

The load has vanished. Every trajectory is the same trajectory in `u`, displaced by a constant
`load` in `x`. The ringdown estimator removes the mean before the FFT, so that constant displacement
is removed too.

**`MI(load; ringdown) ≡ 0` as a matter of algebra, not as an empirical finding.**

Verified numerically — two trajectories at `load = 0.0` and `load = 0.25`, compared in the shifted
coordinate:

```
max |u(load=0) - u(load=0.25)| over the whole trajectory  =  0.0
```

Exactly zero, not small. The only load-correlated variation left in the observable is the sensor
noise added afterwards, which is independent of load by construction.

## What this means for the claim

The claim — a snap event digitizes accumulated analogue load into a discrete report — is **not
disproved by this result.** It was never tested. The model as written cannot express the effect,
because the load enters as a pure translation and the initial condition is specified in the
translated frame, so it has no dynamical consequence at all.

This is a stronger and more useful outcome than a weak effect would have been. It says the
experiment needs rebuilding, not more seeds.

## What a real test would require

Any one of these breaks the translation symmetry and gives the load something to do:

1. **Load changes the well geometry, not just its position** — e.g. deepen one well relative to the
   other, or move the two centers apart, so the landing stiffness genuinely depends on load. The
   ringdown frequency then has something load-dependent to report, which is what Q1 assumes is
   happening.
2. **Fix the initial condition in the lab frame** — release from a fixed `x₀` regardless of load,
   so the load determines how far up the barrier the system starts and therefore its snap energy.
3. **Add a tilt term** `E(x) - load·x`, the standard way a control parameter enters a double well.
   This is almost certainly what was intended: it shifts the wells *and* changes their relative
   depths and curvatures.

Option 3 is the smallest change and the most physically conventional.

## Also worth fixing, independently

The ringdown estimator is bin-limited. With `T = 250`, `dt = 0.01` and `tail_frac = 0.5`, the FFT
sees 125 s of signal, giving a resolution of `1/125 = 0.008 Hz` against a measured frequency of
about `0.136 Hz` — roughly 6% granularity. Even with a genuine load dependence, any frequency shift
smaller than one bin would be invisible. A quadratic interpolation around the spectral peak, or
zero-padding, would recover sub-bin resolution cheaply.

The measured `ringdown_freq_std` across the whole ensemble was `0.0019`, essentially equal to the
`0.002` sensor noise that was deliberately added — confirming the estimator returned a constant bin
for every trajectory.

## Status

The sim conforms to the harness and grades itself correctly. The physics needs rebuilding before
the claim can be tested. A rebuilt version is a **new pre-registration** — new NULL.md, new
REFUTE.md, committed before running — not an edit to this one.
