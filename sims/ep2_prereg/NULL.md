# Null model — ep2_prereg

**Null model name:** `rigid_arm_creep_only`

## What the null does

Run the identical measurement protocol — same compression steps, same probe impulses, same
recovery-time estimator, same statistical test — against a **rigid** arm: a frame whose strut has
no bistability and therefore no fold. Its recovery time is constant with compression except for
material creep, modelled as PETG creeping 0.4% per dwell step exactly as the bistable arm does.

## What result would mean "no effect"

Recovery time rising as the load increases is *not* by itself evidence of critical slowing down.
Creep raises it too. A viscoelastic strut gets slower as it is held under load, fold or no fold,
and a monotone rise is what both produce.

So "no effect" is not a flat recovery-time curve. It is **a rise indistinguishable from the rigid
arm's**. The quantity that separates them is the ratio:

```
ratio(c) = tau_bistable(c) / tau_rigid(c)
```

Creep is common to both and divides out. What survives is the fold's `1/√(1 − c/c_snap)`
divergence, or nothing.

This is not a hypothetical correction. `notes/15` records the v1 formulation — absolute recovery
time, no rigid arm — firing detection on the null at **96%**. Nearly every "detection" was creep.
The null is the entire reason the protocol has two arms.

## The second thing the null catches

Even on the ratio, scanning fifteen compression steps for any significant t-statistic gave a null
false-positive rate of **82%** (v2). Fifteen chances to cross a threshold at nominal α = 0.05 is
not a nominal α = 0.05 test. The null exposes the multiple-comparisons inflation that the point
estimate hides, which is why the pre-committed single checkpoint exists.

Both failure modes are measured again in this run rather than taken on trust: `run.py` evaluates
all three criteria (absolute scan, differential scan, differential checkpoint) on both arms at
every seed and noise level, and reports all six numbers.

## Ceiling and floor

- A perfect detector: detection 1.00 on the bistable arm, false positive 0.05 on the rigid arm.
- A useless detector: the two rates equal, whatever their value.

The gap between the two rates is the whole result. A detection rate reported without its null rate
is uninterpretable, and under v1 it was actively misleading.
