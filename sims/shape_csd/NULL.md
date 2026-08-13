# Null model — shape_csd

**Null model name:** `monostable_strut`

## What the null does

The identical octahedron, the identical relaxation solver, the identical impulse probe and
recovery-time estimator — with the bistable strut replaced by an ordinary **monostable** spring of
matched stiffness. Same compression ramp, same probe magnitude, same everything else.

A monostable strut has no fold. There is no second well to snap into, so there is no saddle-node
approach and no critical slowing down to detect. Whatever recovery-time structure the null shows is
what the *apparatus* produces, not what the bifurcation produces.

## What result would mean "no effect"

The claim is mechanical critical slowing down: as compression approaches the snap, the strut's
effective stiffness collapses as `√(1 − c/c_snap)` and probe-recovery time diverges as its inverse.

The trap is the same one that refuted the E-P2 v1 formulation next door, and it is worth stating in
full because it is the single most expensive lesson in this folder: **a recovery time that rises
with load is not evidence of a fold.** Compressing any spring network changes its geometry and its
effective stiffness. A monostable frame under increasing compression will show *some* recovery-time
trend. If the bistable frame's trend is not clearly larger, there is no CSD result — only a loaded
structure getting softer, which is ordinary mechanics.

So "no effect" is **a recovery-time rise indistinguishable from the monostable arm's**, and the
verdict is decided on the ratio between arms rather than on the bistable arm's curve alone.

`sims/ep2_prereg` measured what skipping this costs: without a matched no-fold arm, the false-alarm
rate on a strut with no bifurcation at all was 90–100%.

## Ceiling and floor

- Floor: the two arms' recovery-time curves coincide; the ratio is flat at 1; no lead.
- Ceiling: the null is flat while the bistable arm diverges; the ratio grows without bound as the
  probe stops returning at all.

The second is what notes/14 §8 reports qualitatively — probes past ~75% of snap compression no
longer recover, which is loss of resilience rather than slow recovery. A probe that never returns
is recorded at the estimator's ceiling, and that censoring is itself the signal.
