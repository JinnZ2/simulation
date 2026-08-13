# Refutation condition — shape_csd

**Written before this harness run.** Committed to git ahead of `run.py` and of any results
directory.

HARNESS.md §5 retrofit item **2** — "the headline CSD claim."

## Claim under test

In an octahedron carrying one bistable strut, probe-recovery time diverges as external compression
approaches the snap, giving a leading indicator with at least **15% of the compression range** of
warning — and this divergence is a property of the fold, not of loading a structure, as shown by a
matched monostable arm that does not produce it.

The source claim is `research/notes/14_rosetta_shape_grounding.md` §8, which reports recovery time
flat at 70 steps through 62% of snap compression, rising at 62%, and diverging past 75%: a lead of
roughly 25% of the range. That number came from a single run of one arm with no null and no seeds.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept probe magnitude

1. **`lead_frac < 0.15`** — the recovery-time ratio does not cross its detection threshold until
   later than 15% of the compression range before the snap.
2. **`null_lead_frac >= lead_frac`** — the monostable arm's recovery time rises as early as the
   bistable arm's, so the signal is loading rather than bifurcation.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept probe magnitude

- `lead_frac >= 0.15`, **and**
- `lead_frac - null_lead_frac > 0`.

## Detection rule, fixed in advance

Recovery time is measured at 12 compressions evenly spaced over [0, 0.95·c_snap]. Detection is the
**first compression at which the bistable/monostable recovery-time ratio exceeds 1.5×** its value
at the lowest three compressions. Lead is `(c_snap − c_detect) / c_snap`.

The 1.5× multiple and the three-point baseline are committed here. This is a single threshold
crossing on a ratio, not a scan for significance across many steps — the design `sims/ep2_prereg`
established, adopted here from the start rather than after two refutations.

## Otherwise

INCONCLUSIVE, naming the probe magnitude and seed count that fell short. A lead that depends on how
hard you hit the structure is a real and reportable property of the instrument, not a failure to
be averaged away.

## Why these numbers

- **15% lead** — inherited from the E-P2 physical protocol in notes/15, which set it as the
  threshold for a warning to be actionable while turning a hand screw. Using the same number keeps
  the sim and the physical experiment commensurable.
- **1.5× ratio** — well above the run-to-run scatter a deterministic relaxation produces, well
  below the divergence notes/14 reports (70 → 600+ steps, nearly 10×).
- **12 compressions** — the original used 8; 12 gives finer lead resolution at negligible cost.

## Sweep

Probe magnitude ∈ {0.03, 0.05, 0.08}. The original used 0.05 alone. Probe strength is the
parameter most likely to contaminate the result: too hard a kick knocks the strut over the barrier
outright, which reads as non-recovery for a reason that has nothing to do with slowing down.

## What this does not test

`notes/14` §8 also reports a fluctuation-variance signal jumping 3× at 88% of snap compression, and
records mode-filtered passive EWS as **refuted** at this regime. Neither is under test here. This
run is about recovery time only. Variance is measured and reported as a descriptive secondary with
no threshold attached and no bearing on the verdict.
