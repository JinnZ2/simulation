# Findings — shape_csd

**Verdict: REFUTED.** At probe magnitude 0.08, the monostable null arm's recovery time rose as
early as the bistable arm's at 4 of 5 seeds.

## The snap point replicates exactly

Snap compression measured at **0.495**, matching `research/notes/14_rosetta_shape_grounding.md` §8
and the `SNAP = 0.495` constant that `sims/ep2_prereg` inherits. The mechanics are reproduced
correctly; what follows is not an implementation problem.

## The CSD signal is real and large

On the bistable arm, recovery time goes from a baseline of 110–300 steps to the 600-step censoring
ceiling, with the probe failing to return at 5–7 of the 12 compressions tested. Fluctuation
variance rises by 11× to 83× across the compression range. Leads at probe magnitudes 0.03 and 0.05
are 0.48–0.74 of the compression range — far above the 0.15 the claim needed.

Taken alone, that is a textbook critical-slowing-down result and it is roughly what notes/14 §8
reports from the single-arm run.

## The null fires too, and that is the finding

| probe magnitude | bistable leads | monostable (null) leads | seeds where null ≥ bistable |
|---|---|---|---|
| 0.03 | 0.57, 0.48, 0.74, 0.74, 0.57 | 0.00, **0.74**, 0.00, **0.57**, 0.00 | 1/5 |
| 0.05 | 0.57, 0.48, 0.74, 0.74, 0.57 | 0.00, **0.74**, 0.00, **0.57**, 0.00 | 1/5 |
| 0.08 | 0.48, 0.48, **0.00**, 0.74, **0.00** | 0.74, 0.74, 0.65, 0.57, 0.74 | **4/5** |

A monostable strut has no second well and no fold. It cannot undergo critical slowing down. Yet
under the same compression ramp its recovery time crosses the same 1.5× threshold, at two of five
seeds even with gentle probes, and at nearly every seed with a hard one.

**Compressing a spring network softens it.** Recovery time rises for reasons that have nothing to
do with a bifurcation, and at probe 0.08 that ordinary mechanical effect dominates the measurement
entirely — while the bistable arm's own detection fails at 2 of 5 seeds because a hard kick knocks
the strut over the barrier outright, which reads as non-recovery for the wrong reason.

This is the E-P2 lesson transposed from materials to mechanics. There, creep raised recovery time
on a rigid strut and produced 90–100% false alarms. Here, compression does the same thing to a
monostable frame. Both times, a single-arm measurement of "recovery time rises before failure" was
measuring the apparatus.

## A confound in my own null, recorded rather than fixed

The monostable strut's rest length is the midpoint of the two wells, 1.5, while the bistable strut
starts in its long well at 1.8. The two arms are matched in stiffness (monostable k = 1.0 against
the bistable quartic's k ≈ 0.86 at the long well) but **not in geometry** — they sit at different
strut lengths, so the frames are in different configurations and soften differently under the same
compression.

That makes this null harsher than a clean control. A fairer one would place the monostable rest
length at 1.8 so both arms begin in the same geometry and differ only in the presence of a second
well.

I am not changing it. The null was committed before the data existed, the verdict was graded
against it as written, and swapping in a more favourable null now would make this run EXPLORATORY
under HARNESS.md §4 — the exact move the standard exists to prevent. The corrected null is a **new
pre-registration**, and it is the obvious next run.

What that re-run cannot do is rescue the probe-0.08 result: at that magnitude the bistable arm
itself fails at 2 of 5 seeds. Probe magnitude belongs in the physical protocol as a specified,
bounded quantity, not a free choice.

## Consequences for the physical instrument

`research/notes/15_physical_shape_instrument.md` E-P2 already mandates a two-frame build, from the
ep2 analysis. This result says the same thing about a different confound and adds two requirements:

1. **The rigid/monostable control frame must match the bistable frame's geometry**, not just its
   stiffness — same strut length at rest, same node positions. Otherwise the control softens
   differently under load and the ratio is not clean.
2. **Probe magnitude must be pinned and reported.** The dropped-nut impulse in E-P2 is a good
   design because it is repeatable, but its magnitude needs to be small enough not to knock the
   strut over the barrier. On this evidence the usable window is narrow, and finding its edges is
   worth a run of its own.

## Status of the notes/14 §8 claim

Not refuted as physics. The recovery-time divergence is present, large, and reproduces. What is
refuted is the **inference**: that observing that divergence on a bistable frame demonstrates
critical slowing down. Against a no-fold control under identical loading, this measurement does not
yet separate the two. The claim needs the matched-geometry null before it can be made.
