# Findings — ep2_prereg

**Verdict: SUPPORTED.** The pre-committed checkpoint fired at 100% detection with a 2–6.5% null
false-positive rate, at 5 of 5 seeds, at every swept timing noise.

## The pre-committed criterion

| timing noise | detection (bistable) | false positive (rigid null) |
|---:|---:|---:|
| 0.02 | 1.00 | 0.030 – 0.065 |
| 0.05 | 1.00 | 0.025 – 0.060 |
| 0.10 | 1.00 | 0.020 – 0.055 |

Detection is saturated and the false-positive rate sits at or below the nominal α = 0.05, well
inside the pre-committed 0.10 ceiling. The protocol has ample statistical power at 10% timing
noise, which was the realistic worst case for phone-grade accelerometry.

## The criterion comparison is the actual result

All three criteria were measured on both arms at every point. The null false-positive rates:

| criterion | null FP @ 0.02 | @ 0.05 | @ 0.10 | verdict if used |
|---|---:|---:|---:|---|
| absolute scan | 1.000 | ~0.999 | 0.895 – 0.935 | unusable |
| differential scan | 0.415 – 0.475 | 0.395 – 0.465 | ~0.44 | unusable |
| **differential checkpoint** | **0.030 – 0.065** | **0.025 – 0.060** | **0.020 – 0.055** | **the claim** |

Two independent failure modes, cleanly separated:

**Creep alone produces near-certain false alarms.** The absolute-scan criterion fires on a rigid
strut — no fold, no bistability, nothing to slow down — in 90–100% of trials. PETG creeping 0.4%
per dwell step raises recovery time monotonically, and a monotone rise is exactly what the
detector was looking for. Without the second arm, essentially every "detection" would have been
creep.

**Scanning is the second, independent inflation.** On the ratio, where creep divides out, the
sequential scan still fires on the null ~44% of the time. Fifteen compression steps, each tested
at a nominal one-sided α ≈ 0.05, gives `1 − 0.95¹⁵ ≈ 54%` — the observed rate is squarely a
multiple-comparisons artifact and nothing else. Pre-committing one checkpoint collapses it to the
nominal rate.

## Partial replication of the notes/15 arc

`research/notes/15_physical_shape_instrument.md` records the same three-stage arc from earlier
runs. Comparing:

| version | notes/15 null FP | measured here |
|---|---:|---:|
| v1 absolute scan | 0.96 | 0.895 – 1.000 |
| v2 differential scan | 0.82 | 0.395 – 0.475 |
| v3 differential checkpoint | 0.05 | 0.020 – 0.065 |

v1 and v3 replicate closely. **v2 did not** — 44% here against 82% reported.

### The v2 gap, resolved

The original v1/v2/v3 implementations were supplied later and are preserved under
[`prior_versions/`](prior_versions/). With both in hand the cause is identifiable, and it is
neither a physics difference nor a bug: **it is how the baseline of the t-test is formed.**

My first guess was wrong. Their rigid arm uses a different creep law (`τ₀·(1 + 0.5·creep)` against
my `τ₀/(1 − creep)`) and adds a ±20% per-arm creep realization, so creep does not divide out of
their ratio. That looked like the obvious candidate. It is not — swapping either or both in gives
0.81–0.83 regardless:

| null physics | differential-scan false positive |
|---|---:|
| my creep law, no jitter | 0.81 |
| their creep law, no jitter | 0.81 |
| my creep law, their jitter | 0.83 |
| their creep law, their jitter | 0.82 |

The actual difference is in the statistics. On **identical physics and identical data**, varying
only the baseline:

| t-test construction | false positive |
|---|---:|
| mine — baseline is 25 raw probe samples (5 steps × 5 probes) | **0.45** |
| theirs — baseline is 5 step-level means; the current value is re-noised | **0.78** |

Their baseline entries are already averaged over 5 flicks, so their variance is smaller by roughly
5×, while the current sample carries full probe noise. The Welch denominator therefore
under-estimates the baseline's spread and the t-statistic is inflated, which fires more often on
the null. Mine keeps the same noise structure on both sides.

**Mine is the statistically consistent construction; theirs is the conservative one**, in that it
reports a worse null rate than the data warrants. The qualitative conclusion is identical and both
are far above 5%: sequential scanning is unusable either way. But the 82% figure quoted in notes/15
is inflated by a variance mismatch, and the defensible number for a consistent test is ~44%. Worth
knowing before either is cited as the cost of scanning.

## What this does and does not establish

**Does:** the E-P2 protocol, as specified with two arms and one pre-committed checkpoint at
compression 0.44, has the statistical power to detect an approaching snap with an 18.3% lead,
robustly to 10% timing noise. The physical experiment is worth building.

**Does not:** show that the fold law holds in a printed PETG frame. This sim *assumes* the physics
— `τ ∝ 1/√(1 − c/c_snap)` with a calibrated τ₀ = 70 — and measures only whether the statistics can
see it. A SUPPORTED verdict here is a green light for the build, not evidence about the build.

The null arm is where the assumption does the most work. It models a rigid strut as creep-only
with no load-dependent recovery time. If a real rigid frame shows any stiffening or softening
under compression, the ratio picks it up as signal and the false-positive rates above are
optimistic. **The first thing to measure on the physical instrument is the rigid arm alone**, before
trusting any differential number from it.

## Consequence for the physical protocol

Already stated in notes/15 and confirmed here with numbers: the print must be built as **two
frames** — one bistable, one geometrically identical but rigid — and the analysis must use a single
pre-committed checkpoint. Continuous scanning for the earliest possible warning needs a
multiple-comparison correction (O'Brien–Fleming alpha spending was the suggested v4); on this
evidence, uncorrected scanning would report a warning on a rigid frame roughly half the time.
