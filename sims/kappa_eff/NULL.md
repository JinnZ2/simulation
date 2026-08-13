# Null model — kappa_eff

**Null model name:** `random_ray`

## What the null does

Everything identical — same trained network, same finite-difference Hessian-vector product, same
`eps = 1e-4`, same perturbation magnitudes, same kill criteria — except the perturbation direction
`v` is a **random unit vector** in weight space instead of the normalized loss gradient.

The Geometric-manifold- convention is an ascent ray: `v = g/‖g‖`. That direction is chosen to find
damage fast. The null asks the obvious question: is `kappa_eff` a leading indicator *because it
tracks curvature along a meaningful direction*, or would any direction do?

## What result would mean "no effect"

The claim is that `kappa_eff = |vᵀHv| / vᵀv` peaks **before** held-out accuracy collapses along the
ray, so it can serve as an early-warning signal.

Two ways that can be empty:

1. **Any direction gives the same answer.** In a high-dimensional weight space, a random ray
   through a trained minimum walks into rising curvature and falling accuracy too. If the random
   ray produces the same lead, `kappa_eff` is reporting the generic geometry of leaving a minimum,
   not anything about the ascent direction that damage actually travels.
2. **No accuracy collapse in range.** With no collapse there is nothing to lead, and the kill
   criteria are undefined rather than passed. This is scored INCONCLUSIVE, never SUPPORTED —
   see `REFUTE.md`.

HARNESS.md §4 already gestures at this: it cites "the kappa_eff random-ray result" as its example
of INCONCLUSIVE being a first-class verdict. This run measures it rather than citing it.

## Why not shuffled labels

The obvious alternative null — retrain on shuffled labels — costs a full training run per seed and
answers a different question (is the trained model doing anything?). The claim here is specifically
about *direction*, so the null holds the model fixed and varies only the ray. That isolates the one
thing the claim depends on.

## Ceiling and floor

`kappa_eff` is a curvature magnitude with no natural scale, so absolute values mean little across
seeds. What is comparable, and what the verdict uses, is the **lead**: the gap in perturbation
magnitude between the `kappa_eff` peak and the accuracy-drop point. A useful indicator has a
positive lead on the gradient ray and a smaller one on the random ray. Equal leads mean the
direction was irrelevant.
