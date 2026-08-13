# Refutation condition — shape_csd_g1

**Written before this harness run**, and before `run.py` existed. Successor to `shape_csd`
(generation 1), which was REFUTED. **EXPLORATORY**, stamped as such by the harness (§4).

## Claim under test

With a monostable control arm matched to the bistable arm in **both geometry and stiffness**,
probe-recovery time on the bistable arm still diverges before the snap with at least 15% of the
compression range of warning, and the control does not produce the same divergence.

This is the parent's claim with the control corrected. The refutation conditions and thresholds are
**identical to the parent's** — nothing has been relaxed. Only the null's construction changed, and
it changed in the direction that makes the claim *harder* to defend on a technicality: the control
is now a fairer competitor, not a weaker one.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept probe magnitude

1. **`lead_frac < 0.15`** — the recovery-time ratio does not cross its threshold early enough.
2. **`null_lead_frac >= lead_frac`** — the geometry-matched monostable arm rises as early as the
   bistable one, so the signal is loading rather than bifurcation.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept probe magnitude

- `lead_frac >= 0.15`, **and**
- `lead_frac - null_lead_frac > 0`.

## Detection rule — unchanged from the parent

Recovery time at 12 compressions evenly spaced over `[0, 0.95·c_snap]`. Detection is the first
compression at which the bistable/monostable recovery-time ratio exceeds **1.5×** its value at the
lowest **three** compressions. Lead is `(c_snap − c_detect) / c_snap`. One pre-committed threshold
crossing on a between-arm ratio; no scanning for significance.

## Otherwise

INCONCLUSIVE, naming the probe magnitude and seed count. A claim that holds at 0.03 and 0.05 but
not 0.08 is a real and reportable bound on the instrument's usable probe window, and is to be
reported that way rather than averaged into a single verdict.

## What this run can and cannot settle

**Can:** whether the parent's refutation was caused by my mismatched control or by the physics.
That is a clean fork and either branch is worth having.

**Cannot:** whether the recovery-time divergence is *large enough to be useful* on a real printed
frame, where the control will never match as exactly as two configurations of the same solver.
A simulated matched control is the friendliest possible case. If the claim fails even here, it will
not survive a physical build; if it passes here, the print is still the test.

## Secondary, no threshold attached

`barrier_crossings` — compressions where the probe left the strut in the wrong well. Diagnostic
only, so that a failure at high probe magnitude can be attributed rather than merely recorded.
Fluctuation variance is likewise reported and ungraded, as in the parent.
