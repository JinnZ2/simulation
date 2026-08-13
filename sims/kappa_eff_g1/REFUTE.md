# Refutation condition — kappa_eff_g1

**Written before this harness run**, and before `run.py` existed. Successor to `kappa_eff`
(generation 1), which was REFUTED. This entry is **EXPLORATORY** and the harness stamps it as such:
a claim reformulated after seeing data never re-enters the ledger as PREDICT (HARNESS.md §4).

## Why the parent failed, and why this is a different claim

The parent tested K1/K2, which are **peak-based**: the `kappa_eff` maximum must precede the
accuracy drop. It fired at 5/5 seeds at every threshold.

The diagnosis was structural. Curvature along an ascent ray rises, peaks, then collapses as the
weights reach the high-loss plateau. **A maximum cannot lead the event it is the turning point
of.** As `research/notes/16_inenvironment_results.md` §9d puts it, the peak-based reading is
"unfalsifiable-in-reverse — it must fail by construction."

Two independent implementations reached that conclusion: this repo's harness run (numpy, 5 seeds,
3 drop thresholds, random-ray null) and notes/16 §9d (torch, single seed, GM's own apparatus).
They also agree on the fix. GM's own phase classifier is rise-based (`κ > 20 + trend > 3`), so the
rise formulation is what the repo operationally uses anyway; only the README sentence was
peak-shaped.

**So this is not a threshold moved to rescue a failed claim.** It is a different feature of the
same curve — onset rather than maximum — and the two have opposite lead properties by construction.

## Claim under test

Along the gradient-ascent ray, `kappa_eff` reaches **2× its baseline before** held-out accuracy
drops 5 points; this holds across network widths; and at matched damage the gradient ray's
curvature has risen further than a random ray's.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept width

1. **`alpha_rise >= alpha_drop`** — the 2× rise does not precede the 5-point drop, so onset does
   not lead either and the whole indicator is coincident.
2. **`kappa_ratio_at_drop_gradient <= kappa_ratio_at_drop_random`** — at equal accuracy loss the
   ascent direction's curvature has risen no further than a random direction's, so the direction
   carries nothing.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept width

- `alpha_rise < alpha_drop`, **and**
- `kappa_ratio_at_drop_gradient > kappa_ratio_at_drop_random`.

## Otherwise

INCONCLUSIVE, naming the width. A result that holds at width 32 but not 16 or 64 would say the
indicator is a property of one network size, which is worth knowing before anyone scales it.

Also INCONCLUSIVE by construction, as in the parent: **no accuracy collapse within the α range**
leaves nothing to lead.

## Why these numbers

- **2× baseline** — GM's own classifier is a rise-and-trend test, and notes/16 §9d used exactly
  `κ ≥ 2× baseline` when it measured the rise-based version. Reusing it keeps the two commensurable.
- **5-point drop** — the parent's middle threshold, and the one the original script hard-coded.
  Held fixed here because the criterion under test has moved to the other side of the comparison;
  sweeping both at once would confound which change mattered.
- **Width {16, 32, 64}** — notes/16 §9d closes by saying the full test "needs ≥5 seeds and ≥2
  architectures." This run has 5 seeds and 3 widths.

## What a SUPPORTED verdict would mean

That on small MLPs, curvature onset along the ascent ray leads behavioural collapse and does so
better than a random direction. It would license one concrete change: GM's CLAIM_TABLE entry should
read `kappa_eff ≥ 2× baseline before Δacc ≤ −5pt` rather than "spikes before behavioral failure."

It would **not** establish anything about the model scales GM targets. Three widths of a
2-layer MLP on a synthetic 2-D task is not an architecture sweep in any meaningful sense.
