# Refutation condition — ep2_prereg

**Written before this harness run.** Committed to git in advance of `run.py` and of any results
directory. `git log --follow` on this file against the timestamps under `results/` is the check.

This sim is HARNESS.md §5 retrofit item **1** — "becomes the physical instrument's formal
pre-registration." It is the pre-registration for experiment E-P2 in
`research/notes/15_physical_shape_instrument.md`: a printed octahedron with one bistable strut,
probed with a fixed impulse at each compression step, whose recovery time should diverge before
the strut snaps.

## Claim under test

Under the fold normal form `k_eff ∝ √(1 − c/c_snap)`, probe recovery time `τ ∝ 1/k_eff` diverges
as compression approaches the snap. Measured **differentially** — the bistable arm's recovery time
divided by an identical rigid arm's — and tested at **one pre-committed checkpoint**, this detects
the approaching snap with a lead of at least 15% of the load range, while a rigid-only null fires
no more than 10% of the time.

The differential-and-checkpoint design is not incidental. `notes/15` records that the two earlier
formulations were refuted, and why:

| version | design | outcome |
|---|---|---|
| v1 | absolute recovery time, sequential scan for any t > 1.86 | REFUTED — null fired 96%; creep alone mimics CSD |
| v2 | differential ratio, sequential scan | REFUTED — null 82%; scanning 15 steps is a multiple-comparisons machine |
| v3 | differential ratio, one pre-committed checkpoint | SUPPORTED |

This run pre-registers **v3** and measures all three criteria at every point, so the size of the
multiple-comparisons effect is recorded as a number rather than asserted from memory.

## Pre-committed checkpoint

**Compression 0.44**, against a snap at 0.495 and a load range of 0.30. That is a lead of
`(0.495 − 0.44)/0.30 = 18.3%`, comfortably above the 15% the claim requires. The checkpoint is
fixed here, before running, and is not to be moved.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept noise level

1. **`detection_rate_checkpoint < 0.80`** — the pre-committed checkpoint fails to fire on the
   bistable arm in at least 80% of trials.
2. **`null_false_positive_checkpoint > 0.10`** — the rigid arm, which has creep but no fold, fires
   more than 10% of the time.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept noise level

- `detection_rate_checkpoint >= 0.80`, **and**
- `null_false_positive_checkpoint <= 0.10`.

## Otherwise

INCONCLUSIVE, naming the noise level and seed count that fell short. A result that holds at 2% and
5% timing noise but fails at 10% is a real finding about how good the timing needs to be, and
belongs in the physical protocol as a measurement-precision requirement — not rounded away.

## Why these numbers

- **0.80 detection** — the printed instrument gets one run per build session; a detector that fires
  four times in five is usable, one that fires half the time is not.
- **0.10 false positive** — nominal α = 0.05 doubled, to leave room for the creep model being
  wrong in the optimistic direction.
- **15% lead** — inherited from the E-P2 protocol in notes/15, which set it as the threshold for
  the warning to be actionable while turning a hand screw.

## Sweep

Timing noise ∈ {0.02, 0.05, 0.10}. Recovery time is measured from an oscillation-envelope fit on
phone-grade accelerometry; 10% is a realistic worst case for that instrument, and the claim has to
survive it or the protocol needs better sensing.

## What is simulated versus what is claimed

This is a **model of the physical experiment**, not the experiment. It uses the fold law with a
calibrated `TAU0 = 70` at baseline compression 0.30 and PETG creep at 0.4% per step, both from
notes/15. A SUPPORTED verdict here means *the protocol has adequate statistical power under the
assumed physics* — it is not evidence that the physics holds. That evidence requires the print.

The null arm is where the assumed physics is doing the most work: it models a rigid strut as
creep-only with no fold. If a real rigid frame shows any load-dependent recovery time, the null is
optimistic and the false-positive numbers here are too good.
