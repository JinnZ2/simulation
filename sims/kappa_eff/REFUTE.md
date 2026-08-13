# Refutation condition — kappa_eff

**Written before this harness run.** Committed to git ahead of `run.py` and of any results
directory; `git log --follow` on this file against the `results/` timestamps is the check.

This sim is HARNESS.md §5 retrofit item **3**, whose note reads: *"verdict flipped on criterion
choice — needs the full criterion-sweep recorded in config."* That is the whole point of this
retrofit. The original script hard-coded one accuracy-drop threshold (5 points) and reported a
verdict from it. Move the threshold and the verdict moves. So the threshold is swept, and the claim
must survive all of it.

## Claim under test

Geometric-manifold- claims `kappa_eff` "spikes before behavioral failure." Formally: along the
weight-perturbation ray `θ₀ + α·v` with `v` the normalized loss gradient, the effective curvature
`kappa_eff = |vᵀHv| / vᵀv` reaches its peak at a smaller `α` than the point where held-out accuracy
has dropped by the threshold — and it does so regardless of where that threshold is set, and by a
larger margin than a random ray gives.

## Kill criteria, from the original script, retained verbatim in spirit

- **K1** — `kappa_eff` shows no peak anywhere before the accuracy-drop point.
- **K2** — the `kappa_eff` peak occurs at or after accuracy has already dropped past the threshold.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept drop threshold

1. **K1 or K2 fires on the gradient ray** — the indicator does not lead.
2. **`lead_gradient - lead_random <= 0`** — the gradient ray's lead is no better than a random
   ray's, so the direction carries no information and `kappa_eff` is reading generic
   leaving-a-minimum geometry.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept drop threshold

- Neither K1 nor K2 fires on the gradient ray, **and**
- `lead_gradient - lead_random > 0`.

## Otherwise

INCONCLUSIVE with the reason. Two specific cases are INCONCLUSIVE by construction and must not be
scored either way:

- **No accuracy collapse within the swept α range.** Nothing to lead. The original script says
  "K1-K2 inconclusive: no accuracy collapse in range" and that is the right call.
- **A verdict that holds at some drop thresholds and not others.** That is the finding §5 flagged.
  It means the claim is a claim about the threshold, not about the curvature, and it gets reported
  as such rather than resolved by picking the flattering threshold.

## Sweep

`accuracy_drop_threshold` ∈ {0.02, 0.05, 0.10}. The original used 0.05 alone. These bracket it on
both sides, so the criterion-dependence §5 asks about is measured directly.

## Deviation from the original: numpy, not torch

The original is torch. This retrofit reimplements the same experiment in numpy — same architecture
(2→32→32→2, tanh), same Adam, same cross-entropy, same finite-difference HVP at `eps = 1e-4`, same
gradient-ascent ray convention.

Reason: `research/notes/10_integration_theories_languages.md` §2.2 puts torch at Tier 2 and numpy at
Tier 1, and `notes/13` flags the Geometric-manifold- repo as Tier-2 by that discipline. This sim
does not need Tier 2 — the network is 1,186 parameters.

**Cost of the substitution, stated plainly:** the numbers will not be bit-identical to a torch run.
Different initialization RNG and different Adam implementation details mean a different trained
network, hence different curvature values. What is preserved is the experiment: the claim, the
kill criteria, the ray convention, the HVP method. If the verdict here disagrees with a torch run,
that disagreement is itself worth a ledger entry.

## What a SUPPORTED verdict would and would not mean

It would mean: on a 1,186-parameter MLP on a synthetic 2-D task, curvature along the ascent ray
peaks before accuracy collapses, robustly across three drop thresholds and better than a random
ray. It would **not** mean the indicator works on the models Geometric-manifold- actually targets.
`notes/13` lists that scaling question as open, and it stays open.
