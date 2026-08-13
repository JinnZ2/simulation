# Findings — kappa_eff_g1

**Verdict: REFUTED.** The 2× rise does not precede the 5-point accuracy drop at 5/5, 4/5 and 5/5
seeds across widths 16, 32 and 64. At width 64 the gradient ray also loses to the random ray at
matched damage, at 5/5 seeds.

This is a **different refutation from the parent's**. The parent showed the *peak* cannot lead.
This shows that in this implementation there is often no rise to lead with.

## Curvature does not rise at all at two of three widths

Gradient ray, seed 0, curvature as a multiple of its baseline:

| α | width 16 | width 32 | width 64 |
|---:|---:|---:|---:|
| 0.00 | 1.00 | 1.00 | 1.00 |
| 0.02 | 1.01 | — | **0.69** |
| 0.05 | 1.01 | — | **0.30** |
| 0.10 | 1.02 | — | **0.11** |
| 0.30 | 0.98 | ~10 (peak region) | 0.04 |
| 0.65 | 0.63 | — | 0.03 |

At width 16 curvature is flat and then declines monotonically — it never reaches 1.05×, let alone
2×. At width 64 it **collapses immediately**, losing 70% by α = 0.05. Only width 32 — the parent's
width — shows the rise-then-peak-then-fall shape that both the parent and notes/16 §9d describe.

Baseline curvature itself varies by more than two orders of magnitude across widths: κ₀ = 0.233
(w16), 0.259 (w32), **58.999** (w64). A criterion phrased as "2× baseline" means something
completely different at each.

## This disagrees with notes/16 §9d, and the reason matters

notes/16 §9d measured the rise-based criterion in torch and found it **SUPPORTED**: κ doubles by
α ≈ 0.75 while accuracy has fallen only 2.4 points at α = 1.0.

Here, accuracy collapses far earlier along the ray. At width 64 it has already dropped 4.6 points
by α = 0.02 — fifty times sooner. The two implementations are not measuring the same geometry: the
torch network's basin extends much further along the ascent ray than this numpy network's does.

That is not a discrepancy to be split. It is the finding: **whether curvature onset leads collapse
depends on how far the trained network's basin extends along the ascent direction**, and that
differs between two reasonable implementations of the same experiment.

## The likely cause, and a real defect in my setup

Checking convergence — which is what turned this up — the networks are **not trained to a minimum**:

| width | epochs | ‖∇L‖ | test acc |
|---|---:|---:|---:|
| 16 | 200 (as configured) | 0.164 | 0.868 |
| 16 | 2000 | 0.040 | 0.912 |
| 32 | 200 | 0.047 | 0.914 |
| 64 | 200 (as configured) | **0.570** | 0.894 |
| 64 | 2000 | 0.024 | 0.868 |

At width 64 the gradient norm is 0.57 after the configured 200 epochs — nowhere near stationary.
That explains both the enormous κ₀ and the immediate collapse: the ray starts from a steep,
non-stationary point, so moving along it descends in curvature while wrecking accuracy.

The diagnostic that makes this unambiguous: **at width 16, held-out accuracy rises along the ascent
ray**, from 0.868 to 0.910 at α = 0.25, before falling. Moving *up* the training-loss gradient
improves test accuracy. That only happens from an undertrained point.

The 200-epoch budget was inherited from the original script and carried into the parent and into
this pre-registration without question. A claim about curvature *at a minimum* requires an actual
minimum, and neither generation established one. The verdict stands as graded — the conditions were
committed before the data existed and evaluated as written — but it is a verdict about
under-trained networks.

## A bug found and fixed, with no effect on any result

`softmax_ce` computed `logsumexp` as `log(Σ exp(shifted)) + shifted.max(axis=1)`, where `shifted`
is already mean-shifted so `shifted.max` is identically zero. It should be `logits.max(axis=1)`.
The returned loss was wrong by the row maximum and went **negative**, which is impossible for
cross-entropy.

It changed nothing. `loss_and_grad` derives gradients analytically from the softmax probabilities
rather than by differentiating that scalar, and no code path consumes the loss value — `train` and
`kappa_eff` both take only the gradients. Fixed in both this sim and the parent, and verified: the
parent re-runs to byte-identical observations and details.

Recording it because a wrong number that happens not to matter is still a wrong number, and the
next person to use `softmax_ce` for anything would have been misled.

## What generation 2 needs

Not scaffolded here — this lineage is at generation 1, and `explore.py` allows one more before the
escape hatch. A generation 2 should:

1. **Gate on convergence.** Train until ‖∇L‖ falls below a pre-committed threshold, or fail the
   run. Every claim in this lineage is about geometry at a minimum.
2. **Normalize the curvature criterion across widths.** "2× baseline" is not comparable when
   baselines span 0.23 to 59. Curvature relative to the loss scale, or a rank-based criterion,
   would be.
3. **Reconcile with notes/16 in torch.** If the torch network's basin genuinely extends further,
   that is worth understanding rather than attributing to implementation noise — it may be a real
   difference between the optimizers' endpoints.

Until then the honest position is: **GM's claim is neither established nor refuted.** The
peak-based reading fails by construction (parent), the rise-based reading is
implementation-dependent and was tested here from non-stationary points (this run), and the
question of what curvature does along an ascent ray from a genuine minimum remains open.
