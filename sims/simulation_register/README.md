# simulation_register/ -- simulation hypothesis: assumptions, gaps, calculators

Co-authored (Kavik + Claude, 2026-11-01). CC0. stdlib only (unlike most of `sims/`, no numpy).
Not a harness sim: nothing here grades a claim or writes to `../ledger.jsonl`. The graded toys are
harness sims beside it.

```text
SIMULATION_REGISTER.md     A1-A6 assumptions, G1-G7 gaps, reframe, lattice defaults, extinction gap
CONVERGENCE_RANKING.md     test design: rules ranked by independent lineages (no sim yet)
landauer_budget.py         1e120 ops at 2.7 K vs mass-energy; genome deletion cost  (DERIVED; inputs VERIFY)
phase_change_entropy.py    G4(a): entropy jump in bits per transition              (DERIVED; inputs VERIFY)
auger_loader_stub.py       real-data loader; REFUSES without a local release file (data unreachable 2026-11-01)

graded toys (Sim Harness Standard v1; pre-registered; self-graded; ledger):
../lattice_anisotropy/       G5: cubic-axis alignment, orientation scan, exposure correction
../render_ledger/            A1, A6, G6: render-on-observation cost; deletion signature
../ising_critical_slowing/   G4(b), G7: autocorrelation vs L at Tc; ordered vs random start
```

Rule for every number: a source, or VERIFY. Synthetic is not observational.
