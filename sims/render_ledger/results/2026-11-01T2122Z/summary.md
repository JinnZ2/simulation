# render_ledger — SUPPORTED

Run: 2026-11-01T21:22:23Z · 9.7s · 5 seeds × 4 sweep points

## Claim

Render-on-observation saves compute only when the observer set is restricted (A1): with any-interaction observers the saving is below 1% for every consistency policy; with humans-only observation at p=0.1 the keep-record policy covers at least 99% of cells within 200 steps; and only true deletion produces contradictions on repeat observation (delete rate > 0, keep-record and recompute rate = 0, humans-only).

## Pre-committed refutation condition

> any_interaction saving >= 0.01 for any policy, OR keep-record coverage < 0.99 at p_observe=0.1 humans_only, OR delete contradiction rate == 0 humans_only, OR keep-record/recompute contradiction rate > 0 - any of these at >=3 of 5 seeds

## Verdict

**SUPPORTED** — all parts hold at 5 of 5 seeds; delete contradiction rate 0.999-0.999; any-interaction saving 0 for every policy

## Detail

```json
{
  "failing_seeds": {}
}
```

## Measurements

| seed | p_observe | observer | contra_delete | contra_keep | contra_recompute | coverage_keep | reobs_after_gap | saving_delete | saving_keep | saving_recompute |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | humans_only | 0.9990 | 0.0000 | 0.0000 | 0.8654 | 111472.0000 | 0.9900 | 0.4292 | 0.4284 |
| 1 | 0.01 | humans_only | 0.9990 | 0.0000 | 0.0000 | 0.8651 | 111566.0000 | 0.9900 | 0.4287 | 0.4287 |
| 2 | 0.01 | humans_only | 0.9990 | 0.0000 | 0.0000 | 0.8654 | 111475.0000 | 0.9900 | 0.4288 | 0.4284 |
| 3 | 0.01 | humans_only | 0.9992 | 0.0000 | 0.0000 | 0.8674 | 111255.0000 | 0.9900 | 0.4280 | 0.4286 |
| 4 | 0.01 | humans_only | 0.9991 | 0.0000 | 0.0000 | 0.8666 | 111400.0000 | 0.9900 | 0.4283 | 0.4284 |
| 0 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0 | 0.1 | humans_only | 0.9991 | 0.0000 | 0.0000 | 1.0000 | 1700888.0000 | 0.9000 | 0.0452 | 0.0450 |
| 1 | 0.1 | humans_only | 0.9990 | 0.0000 | 0.0000 | 1.0000 | 1701360.0000 | 0.9000 | 0.0451 | 0.0451 |
| 2 | 0.1 | humans_only | 0.9990 | 0.0000 | 0.0000 | 1.0000 | 1700647.0000 | 0.9000 | 0.0450 | 0.0450 |
| 3 | 0.1 | humans_only | 0.9990 | 0.0000 | 0.0000 | 1.0000 | 1701545.0000 | 0.9000 | 0.0451 | 0.0447 |
| 4 | 0.1 | humans_only | 0.9990 | 0.0000 | 0.0000 | 1.0000 | 1700811.0000 | 0.9000 | 0.0449 | 0.0451 |
| 0 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Null model — `full_compute`

| seed | p_observe | observer | contra_delete | contra_keep | contra_recompute | coverage_keep | reobs_after_gap | saving_delete | saving_keep | saving_recompute |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.01 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 0.01 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.01 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.01 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.01 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.01 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0 | 0.1 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 0.1 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.1 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.1 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.1 | humans_only | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.1 | any_interaction | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

---

Generated by `sims/harness`. Do not edit — rerun instead.
