# Refutation conditions (pre-committed 2026-08-14, before any harness run)
E-P2 claim: probe-flick recovery time leads the snap by >= 15% of the load range.

The claim is REFUTED if EITHER:
1. Median first-detection lead < 15% of the load range (0.30..0.60 compression span),
   in at least 3 of 5 seeds, at the central timing-noise level (5%); OR
2. The rigid-strut null arm produces detections at a rate > 20% (the signal is then
   indistinguishable from creep drift + multiple-comparison false alarms).

The claim is INCONCLUSIVE if:
- Detection occurs but lead is highly seed-variable (median passes, <4/5 seeds pass), or
- Verdict flips across the timing-noise sweep (passes at 2%, fails at 10%) without a
  monotone noise-robustness pattern.

Any change to this file after results exist marks the run EXPLORATORY.
