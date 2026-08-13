# Findings — shape_csd_g1

**Verdict: SUPPORTED.** At 5 of 5 seeds at every probe magnitude — including 0.08, where the parent
failed hardest. The geometry-matched control never fires: `null_lead_frac` is **0.000 in all
fifteen runs**.

## The parent's refutation was my confound, not the physics

| | parent (`shape_csd`) | here (matched control) |
|---|---|---|
| control rest length | 1.5 (well midpoint) | 1.8 (matches the test arm) |
| control stiffness | 1.0 (approximate) | 0.864 (exact `E''` at the long well) |
| null fires at probe 0.03 | 2/5 seeds | **0/5** |
| null fires at probe 0.08 | 4/5 seeds | **0/5** |
| verdict | REFUTED | **SUPPORTED** |

Bistable leads are essentially unchanged from the parent (0.40–0.74 of the compression range). What
changed is the control: once it starts in the same geometry, its recovery time does not rise at all
under the same compression ramp, and the between-arm ratio is clean.

So `research/notes/14_rosetta_shape_grounding.md` §8's claim survives with a proper control. **The
recovery-time divergence is a property of the fold, not of loading a spring network** — provided
the control is matched in configuration, not merely in stiffness.

## A mechanism I asserted in the parent, now falsified

`shape_csd/FINDINGS.md` explained the parent's probe-0.08 failure this way:

> the bistable arm itself fails at 2 of 5 seeds because a hard kick knocks the strut over the
> barrier outright, which reads as non-recovery for the wrong reason

That was a plausible mechanical story, and the `barrier_crossings` diagnostic added for this run —
pre-committed in NULL.md, precisely to make such a failure attributable — **measures zero crossings
in every run, at every probe magnitude.** The probe never knocks the strut into the other well at
0.08.

The parent's probe-0.08 failure was the mismatched control softening faster than the test arm, not
the test arm breaking. I got the verdict's cause right and the mechanism wrong, and I would not have
found that without adding an instrument to test my own explanation.

The lesson generalizes: a diagnosis written into FINDINGS.md is a claim like any other, and it is
worth building the diagnostic that could contradict it.

## What is still true from the parent

Nothing here rescues the parent's central lesson, which stands unchanged: **a recovery time that
rises with load is not evidence of a fold, and a single-armed measurement cannot tell the
difference.** The parent's mismatched control still rose under compression, which is exactly the
ordinary softening the two-arm design exists to subtract. The fix was to make the control fair, not
to remove it.

## What this does not establish

**A simulated matched control is the friendliest possible case.** Both arms here are configurations
of the same relaxation solver, differing in one term of one force law. Two printed frames will
differ in strut lengths, joint friction, print anisotropy and creep, and their recovery times will
not track each other this cleanly.

That the claim passes here is necessary, not sufficient. It does mean the physical build is worth
doing — which after the parent's refutation was genuinely in doubt.

Also unchanged and unaddressed: `censored_points` runs at 5–7 of 12 compressions, meaning the probe
often fails to return within the 600-step ceiling. The lead is therefore measured partly through a
censoring boundary rather than a graded slowdown. Whether the divergence is smooth up to the snap
or effectively a step function at the censoring limit is not resolved by this measurement, and a
higher ceiling would answer it.

## Consequence for the physical protocol

`research/notes/15_physical_shape_instrument.md` already mandates a two-frame build. This sharpens
the specification:

**The control frame must match the bistable frame's geometry at rest — same strut length, same node
positions — not merely its stiffness.** In simulation that distinction was the entire difference
between REFUTED and SUPPORTED. On a printed instrument it is a machining tolerance, and it is now
the single most important one in the build.
