# Null model — shape_csd_g1

**Null model name:** `geometry_matched_monostable_strut`

## What changed from the parent's null

The parent used a monostable strut whose rest length sat at the **midpoint of the two wells (1.5)**
while the bistable strut started in its **long well (1.8)**. The arms were matched in stiffness but
not in geometry: they sat at different strut lengths, so the two frames were in different
configurations and softened differently under the same compression.

That is a confound, and the parent's FINDINGS.md recorded it rather than fixing it mid-run. This
run fixes it:

| | parent | here |
|---|---|---|
| monostable rest length | 1.5 (well midpoint) | **1.8 (matches the bistable arm's start)** |
| monostable stiffness | 1.0 (approximate) | **0.864** — exactly `E''` of the quartic at `l = 1.8` |
| geometry at compression 0 | different | identical |

`E(l) = a(l−l₁)²(l−l₂)²` has `E''(l₂) = 2a(l₂−l₁)² = 2(1.2)(0.6)² = 0.864`. The control now matches
the test arm in both position and local curvature at the start of the ramp, and differs only in
having no second well to fall into.

## What result would mean "no effect"

Unchanged from the parent, and worth restating because it is the entire point: **a recovery time
that rises with load is not evidence of a fold.** Compressing any spring network softens it.

The parent measured how much of the signal that accounts for, and the answer was: most of it. The
mismatched control crossed the same 1.5× threshold at 2/5 seeds with gentle probes and 4/5 with
hard ones. The open question this run answers is whether that was the fold-free physics or the
geometry mismatch.

Two outcomes, both informative:

- **The matched control stops firing** → the parent's refutation was driven by my confound, the CSD
  signal is real, and notes/14 §8's claim survives with a proper control.
- **The matched control still fires** → the refutation stands on its own, ordinary softening
  genuinely mimics critical slowing down in this apparatus, and single-arm CSD measurement on a
  compressed frame is not viable regardless of how the control is built.

## The probe-magnitude sweep is unchanged, deliberately

The parent failed hardest at probe magnitude 0.08, partly because a hard kick knocks the bistable
strut over the barrier outright — non-recovery for a reason that has nothing to do with slowing
down. It is tempting to drop 0.08 from the sweep now that this is known.

**It stays.** Dropping a swept point because the parent failed there is exactly the tuning
HARNESS.md §4 exists to prevent, and the claim as written is a claim about the range 0.03–0.08. If
it refutes again at 0.08, the correct conclusion is that the claim is true only over a narrower
probe window, and that window belongs in the physical protocol.

A diagnostic is added instead: `barrier_crossings` counts compressions where the probe left the
strut in the other well. It carries no threshold and does not touch the verdict — it exists so a
failure at 0.08 is *attributable* rather than merely recorded.
