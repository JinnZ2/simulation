# Notes 16 — In-environment follow-through on the physical instrument + C6
2026-08-14 · status: sims run here; all honest-flag verdicts below

## 9a. SCAD static review (no openscad binary in sandbox)
- Fixed a real bug: `vertex_node` sockets were bored with `rotate([0,a,0])` (all in the
  x–z plane, including one straight through the node's own axis). Now `rotate([a,0,0])`:
  4 sockets in the plane perpendicular to the node axis — correct octahedral incidence.
  Assembly note added: rotate node 45° so sockets aim at the 4 neighbors.
- Remaining v1 limitations (documented, not blocking): apex_cap slot angles are
  approximate; sockets don't self-aim at neighbors (assembly rotation handles it);
  snap-fit clearances assume a calibrated FDM printer (test-coupons advised).

## 9b. E-P2 pre-registration expectations (sims/ep2_prereg_sim.py)
Fold normal form: k_eff ∝ sqrt(1 − c/c_snap), τ_recovery ∝ 1/k_eff (mean-field fold
exponent 1/2; matches shape_csd_probes.py measured 70→600+).
Protocol modeled: 0.30→0.495 compression in 0.01 steps, 60 s dwell, 5 flicks/step.
- 200/200 simulated trials detect CSD before the snap.
- Median first detection at compression 0.350 → **lead ≈ 48% of load range**,
  far above the 15% pre-registered threshold. PASS predicted.
- **Honest caveat:** detection before ~0.42 is partly creep-drift-driven (0.4%/step
  assumed). The fold-specific divergence dominates from 0.44 onward
  (τ: 70 → 140 (0.44) → 177 (0.46) → 272 (0.48) → 473 (0.49), creep-inclusive).
  Recommend in-protocol control: an identical rigid-strut frame run in parallel;
  creep affects both, CSD only the bistable one → difference isolates the fold.
- Robustness: 48% lead holds at 2%/5%/10% timing noise; degrades to 45% at 15%.
  A phone accelerometer (phyphox, 100–500 Hz) is comfortably inside this envelope.

## 9c. GM claim-table → CDT ledger adapter
`integration/gm_claimtable_to_ledger.py` (stdlib, ~60 LOC). Converts GM CLAIM_TABLE
JSON into hash-chained PREDICT entries. Key design decision consistent with the
ledger ethos: **claims exported without an explicit refutation condition are
rejected at import** (reported, not silently admitted). GM's CLAIM_TABLE exports
carry `ISS_proof_pending: True` statuses — these map to PREDICT type.

## 9d. C6 mini — κ_eff leading-indicator test, actually run (torch CPU)
sims/kappa_eff_kill_test.py. Tiny MLP (2-32-32-2, tanh) on synthetic 1-D manifold
data; sweep θ + α·v with GM's own conventions (finite-difference HVP, ε=1e-4,
κ_eff = |v·Hv|/v·v).

- **Random ray: INCONCLUSIVE.** Basin is wide along random directions — accuracy
  holds (±0.4 pt) out to α=0.5, κ_eff flat (0.027→0.025). No boundary crossed.
  This itself is informative: κ_eff on random rays carries no signal; GM's
  energy_sweep uses the ascent ray for a reason.
- **Ascent ray (v = ∇L/||∇L||):** κ_eff climbs monotonically 0.065 → 0.61 across
  α = 0 → 1.5, a **9.3× rise**, peaking exactly at the collapse point (α=1.5,
  acc −9.2 pt) and falling after (0.20 at α=3.0, acc −56 pt — post-barrier, as
  the cusp geometry predicts).
- **Verdict depends on operationalization — logged both:**
  - Peak-based criterion (κ peak must precede accuracy drop): **K2 FIRED —
    refuted.** The peak *is* the collapse; a peak can never lead.
  - Rise-based criterion (κ doubles before accuracy drops 5 pt): **SUPPORTED.**
    κ_eff doubles by α≈0.75 and is 5.4× by α=1.0, while Δacc at α=1.0 is only
    −2.4 pt. GM's own phase classifier (κ>20 + trend>3) is rise-based, so in GM's
    own operational terms the claim survived this test.
  - Recommendation to GM: the claim-table entry should specify the *rise-based*
    operationalization ("κ_eff ≥ 2× baseline before Δacc ≤ −5 pt"), because the
    peak-based reading is unfalsifiable-in-reverse (it must fail by construction).
- Limitations: single seed, single dataset, one tiny net. This is a smoke test,
  not the pre-registered C6 — the full version needs GM's energy_sweep apparatus,
  ≥5 seeds, and ≥2 architectures.

## Cross-cutting
- The fold law sqrt(1 − c/c_snap) now connects three levels: sim octahedron
  (notes/14 §8), physical protocol expectations (9b), and NN basin geometry (9d —
  the same saddle-node mathematics governs κ_eff's rise-then-collapse profile).
  One catastrophe, three substrates — exactly the Rosetta claim, now with numbers.
