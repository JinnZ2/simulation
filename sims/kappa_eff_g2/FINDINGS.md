# Findings — kappa_eff_g2

**Verdict: INCONCLUSIVE.** The convergence gate passed everywhere. The claim then held cleanly at
width 16 (5/5 seeds) and degraded with width (2/5 at both 32 and 64), which is the pre-registered
definition of width-dependence rather than of support or refutation.

## The apparatus finally worked

Gradient norms at θ₀, against a gate of 0.02:

| width | ‖∇L‖ across 5 seeds |
|---|---|
| 16 | 0.00039, 0.00034, 0.00027, 0.00028, 0.00025 |
| 32 | 0.00020, 0.00033, 0.00013, 0.00033, 0.00013 |
| 64 | 0.00707, 0.00037, 0.00013, 0.00611, 0.00076 |

Three orders of magnitude below the inherited setup, which sat at 0.05–0.57. For the first time in
this lineage the measurement is taken from an actual minimum, of an objective that actually has one.

## At width 16 the effect is large and clean

Curvature growth by the time each ray has done 5 points of damage:

| seed | gradient ray | random ray |
|---|---:|---:|
| 0 | **9.7×** | 1.39× |
| 1 | **13.8×** | 1.08× |
| 2 | **20.5×** | 0.90× |
| 3 | **15.0×** | 0.56× |
| 4 | **21.1×** | 1.33× |

The ascent direction's curvature multiplies ten- to twenty-fold while a random direction's barely
moves. The onset also precedes the drop at every seed. Had the sweep been width 16 alone, this
would read SUPPORTED with an unusually strong margin.

## It falls apart with width, and the reason is informative

At width 32: two seeds fail the lead condition, one fails the null comparison, one never collapses.
At width 64: **two of five seeds show no 5-point accuracy drop at all** within α ≤ 3.

That last detail is the explanation, and it resolves the disagreement generation 1 flagged with
`research/notes/16_inenvironment_results.md` §9d.

notes/16 measured this in torch and found the rise-based criterion SUPPORTED, with accuracy falling
only 2.4 points at α = 1.0. Generation 1 measured it in numpy and found accuracy collapsing 50×
sooner. I recorded that as an unexplained implementation difference.

It is not implementation noise. **The basin's extent along the ascent ray grows with network
width.** Wider networks tolerate far more travel before behaviour degrades, so at width 64 there is
frequently no collapse inside the swept range and therefore nothing for the indicator to lead. The
torch network in notes/16 was behaving like the wide end of this sweep; generation 1's undertrained
networks behaved like the narrow end. Both observations were correct about different regimes.

## What this settles and what it does not

**Settles:** the peak-based reading of GM's claim fails by construction (generation 0), and that
failure was not an artefact of undertrained networks (this run, from converged minima). The
rise-based reading is real and strong — at width 16 it is a 10–20× effect against a null that does
nothing. So "κ_eff spikes before behavioural failure" is not empty; it is *conditional*.

**Does not settle:** the condition. The indicator works where the model collapses inside the probed
range and is undefined where it does not. Whether that boundary tracks width, basin geometry, the α
range, or something else is exactly what three generations have not pinned down.

**The recommendation to GM stands and gets sharper.** The CLAIM_TABLE entry should say
`kappa_eff ≥ 2× baseline before Δacc ≤ −5pt` — the rise formulation, not the peak — *and* it should
state the regime: measured from a regularized minimum, on a model whose accuracy collapses within
the probed perturbation range. A claim that is silent about its regime is unfalsifiable in the
direction that matters.

## The escape hatch fired

This was generation 3 of the lineage, and `explore.py` refused to scaffold a successor:

```
escape hatch fired for kappa_eff_g2 at generation 3.
Written to unknown_journal.jsonl; no successor scaffolded.
lineage reached generation 3; a claim reformulated 3 times is not converging.
```

That is the correct outcome and worth not arguing with. Three reformulations produced three
genuinely different findings — the peak cannot lead, the objective had no minimum, the effect is
width-conditional — and each was real. But the pattern from here would be narrowing the claim until
it fits the data, and the guard exists precisely because that pattern is invisible from inside it.

**What this lineage should become instead:** not a fourth reformulation of "does curvature warn,"
but a new question with its own pre-registration — *what determines whether a model collapses
within a bounded perturbation of its minimum?* That is the quantity every generation here has
actually been at the mercy of, and none has measured. `shadow.py` would call it the parameter
everything depended on and nothing swept.
