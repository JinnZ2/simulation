# Findings — kappa_eff

**Verdict: REFUTED.** K1 or K2 fired at 5 of 5 seeds at every swept accuracy-drop threshold, and
the gradient ray's lead was no better than a random ray's at 3–4 of 5 seeds.

## What the curve actually looks like

Seed 0, gradient-ascent ray, baseline held-out accuracy 0.914:

| α | accuracy | Δacc | kappa_eff |
|---:|---:|---:|---:|
| 0.00 | 0.914 | +0.000 | 0.259 |
| 0.05 | 0.906 | −0.008 | 0.505 |
| 0.10 | 0.894 | −0.020 | 0.837 |
| 0.20 | 0.874 | −0.040 | 1.722 |
| 0.30 | 0.804 | −0.110 | **2.602 ← peak** |
| 0.50 | 0.606 | −0.308 | 2.168 |
| 1.00 | 0.600 | −0.314 | 0.131 |
| 3.00 | 0.566 | −0.348 | 0.060 |

## The diagnosis: the criterion tests the wrong feature of the curve

`kappa_eff` **rises early**. By α = 0.05 it has already doubled from baseline, while accuracy has
fallen less than one point. If the claim were "curvature starts climbing before behaviour
degrades," this data would support it.

But `kappa_eff` **peaks late**, and K1/K2 are peak-based criteria. The peak sits at α = 0.30, by
which point accuracy has already dropped 11 points. So K2 — "peak occurs at or after accuracy has
dropped past threshold" — fires at every threshold tested.

This is not an accident of tuning. It is structural. Curvature along an ascent ray must come back
down: once the perturbation carries the weights past the barrier and onto the flat high-loss
plateau, the second derivative collapses (0.06 by α = 3.0, below its own baseline). **A peak is
intrinsically a late statistic when the underlying quantity is a rise-then-fall.** The argmax
cannot lead the event; it marks the turn.

## The criterion sweep did not flip the verdict — and that itself is informative

HARNESS.md §5 item 3 flagged this sim as one whose "verdict flipped on criterion choice" and asked
for the criterion sweep to be recorded in config. It is, and the outcome is the opposite of what
the note anticipated: across drop thresholds of 0.02, 0.05 and 0.10, the verdict is REFUTED at all
three. K1/K2 fired 5/5 seeds at every threshold.

So the drop threshold is **not** the criterion that flips this verdict. The criterion that matters
is *peak versus rise* — a different axis, and one that was never swept because both the original
script and the notes treat "spike" as unambiguous. It is not: a spike has an onset and a maximum,
and they say different things about lead time.

## The random-ray null did its job, in an unexpected direction

Along a random ray, `kappa_eff` is essentially flat and monotonically decreasing (0.152 → 0.016),
with no peak at all — K1 fires by construction. So the gradient ray *is* doing something a random
direction does not: it finds rising curvature.

But on the **lead** statistic the gradient ray does not win. Per-seed lead differences
(gradient minus random), at drop threshold 0.05:

```
-0.75, +0.05, -0.25, -1.75, 0.00
```

Mostly negative. The reason is mechanical: a random ray leaves the minimum slowly, so its accuracy
collapse happens at large α while its (flat) kappa "peak" sits at α = 0 — yielding a large
meaningless lead. The gradient ray damages the model fast, compressing everything into small α.
**Comparing raw lead in α units across rays with different damage rates is not a fair comparison**,
and that is a flaw in my own pre-registered condition, not in the claim. It is recorded here rather
than quietly fixed: the condition was committed before the data existed, it was evaluated as
written, and the verdict stands as graded.

## What a corrected test would look like

A new pre-registration, not an edit to this one:

1. **Rise onset, not peak.** Define the indicator as the smallest α where `kappa_eff` exceeds a
   pre-committed multiple of baseline (say 1.5×), and ask whether *that* precedes the accuracy
   drop. On this data it would: 1.5× baseline is crossed before α = 0.10, and accuracy has fallen
   two points there.
2. **Normalize the ray.** Compare lead in units of *damage* rather than α — e.g. at matched
   accuracy loss — so rays with different damage rates are commensurable.
3. **Keep the random-ray null.** It cleanly showed the gradient direction carries information the
   random one does not; it just could not be compared on the statistic I chose.

## Scope

This is a 1,186-parameter MLP on a synthetic 2-D task, in numpy rather than the original's torch
(see REFUTE.md for what that substitution costs). The result says the peak-based kill criteria fail
*here*. Whether they fail on the models Geometric-manifold- actually targets is a separate and
still-open question — `research/notes/13_geometric_manifold_combinations.md` lists the κ_eff test
as the cheapest high-value experiment available, and this makes it cheaper still by ruling out one
formulation before anyone spends GPU time on it.

The useful takeaway for that repo: **the README claim "κ_eff spikes before behavioral failure" is
not yet a falsifiable statement**, because "spikes" does not distinguish onset from maximum. Those
have opposite lead properties. Pinning it down is a one-line change to the claim and a new
refutation condition.
