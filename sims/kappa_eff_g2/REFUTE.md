# Refutation condition — kappa_eff_g2

**Written before this harness run**, before `run.py` existed. Successor to `kappa_eff_g1`
(generation 2), which was REFUTED. **EXPLORATORY** — a claim reformulated after seeing data never
re-enters the ledger as PREDICT (HARNESS.md §4).

**This is the last generation this lineage gets.** `explore.py`'s escape hatch fires at generation
3: if this is refuted, the lineage goes to `unknown_journal.jsonl` rather than being reformulated a
fourth time. A claim patched three times is not converging on truth.

## What changed, and why it is not a threshold move

The claim's *conditions* are identical to generation 1's — same 2× rise, same 5-point drop, same
matched-damage comparison against a random ray. Nothing has been relaxed.

What changed is the **apparatus**: the networks are now trained to a minimum that exists.

Generation 1 was graded on networks that were not at a minimum, and the reason turned out to be
structural rather than a budget problem: unregularized cross-entropy on a memorizable training set
has no finite minimizer, so training longer makes the gradient norm rise. `NULL.md` documents the
measurements. L2 regularization makes a minimizer exist; the gradient norm now sits at 0.0001–0.007
instead of 0.05–0.57.

Calibrating an instrument before an experiment is not the same as tuning a hypothesis after seeing
its result. The distinction this run relies on: **the training recipe was fixed before any
`kappa_eff` value was measured under it**, and the conditions below were fixed before that. What
would violate the discipline is adjusting `rise_multiple` or `accuracy_drop` now, and neither has
moved.

## Convergence gate

Every trained network must satisfy `‖∇L_regularized‖ ≤ 0.02` at θ₀.

A run where any network fails the gate is **INCONCLUSIVE**, never SUPPORTED or REFUTED. A claim
about geometry at a minimum, measured from somewhere that is not a minimum, is not evidence about
the claim — it is evidence about the apparatus, and generations 0 and 1 already supplied that.

The gate has ~2.8× margin against the worst observed value (0.007 at width 64). It is a real check,
not a rubber stamp: it will fail if the recipe stops working at some width or seed.

## Refute if — either, at ≥ 3 of 5 seeds, in any swept width

1. **`alpha_rise >= alpha_drop`** — the 2× rise does not precede the 5-point drop.
2. **`kappa_ratio_at_drop_gradient <= kappa_ratio_at_drop_random`** — at equal accuracy loss the
   ascent direction's curvature has risen no further than a random direction's.

## Supported requires — both, at ≥ 4 of 5 seeds, in **every** swept width

- `alpha_rise < alpha_drop`, **and**
- `kappa_ratio_at_drop_gradient > kappa_ratio_at_drop_random`.

## Otherwise INCONCLUSIVE

Three ways, all first-class:

- any network fails the convergence gate (apparatus, not evidence);
- no accuracy collapse within the α range (nothing to lead);
- the result holds at some widths and not others — generation 1's finding was exactly this, and if
  it survives a genuine minimum it is a statement about network size rather than about curvature.

## What a SUPPORTED verdict would license

One concrete change, and only one: Geometric-manifold-'s CLAIM_TABLE entry should read
`kappa_eff ≥ 2× baseline before Δacc ≤ −5pt`, measured at a regularized minimum, rather than
"spikes before behavioral failure."

It would **not** transfer to the model scales GM targets. Three widths of a 2-layer MLP on a
synthetic 2-D task is not an architecture sweep, and `research/notes/13` lists the scaling question
as open regardless of how this run lands.

## What a REFUTED verdict would mean

That the claim fails even under the most favourable conditions this lineage can construct: a real
minimum, a fair null, a criterion matched to the shape of the curve, and damage-matched comparison.
At that point the honest move is the escape hatch, not a fourth reformulation.
