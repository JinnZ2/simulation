# Refutation conditions v3 (pre-committed 2026-08-14 — third operationalization)
v1 REFUTED: absolute t-test + scanning -> creep confound (null 96%).
v2 REFUTED: differential ratio + scanning -> multiple-comparison false alarms (null 82%).
v3 removes BOTH confounds by construction: differential ratio, ONE pre-committed
checkpoint (compression 0.44 = fixed 18.3% lead), ONE t-test per trial. No scanning.

REFUTED if ANY:
1. Checkpoint detection in <4/5 seeds at central noise (5%); OR
2. Null-arm checkpoint false-positive rate > 10% (single test => nominal 5%; >10%
   means the differential measurement itself is unstable); OR
3. Detection collapses at 10% noise (not instrument-grade robust).

Physical note: v3 tests a weaker but cleaner claim — presence of signal at a fixed
lead — rather than earliest-detection scanning. If v3 passes, a scanning variant with
a multiple-comparison correction (e.g., O'Brien-Fleming spending) becomes v4.
