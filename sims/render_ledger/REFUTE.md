# Refutation condition — render_ledger

Co-authored (Kavik + Claude, 2026-11-01). CC0. **Written before run.py existed.** Generation 0,
MEASURE. Source: work order WO3 #4 (render_ledger_toy) and SIMULATION_REGISTER.md A1, A6, G6.

## World

100,000 cells x 200 steps. Each cell's consistent state at step t is a deterministic function
of (cell, t). Observation per step: `humans_only` = a random fraction p of cells;
`any_interaction` = every cell (decoherence: everything interacts with something).

Policies (A6):
- keep-record: once observed, a cell is kept in the record and computed every later step.
- recompute (offset): an unobserved cell is not computed; on observation it is caught up from
  its last computed step.
- delete: an unobserved cell is forgotten; on re-observation after a gap it is instantiated
  fresh, with no history.

Cost = cell-updates; saving = 1 - cost / (cells x steps).
Contradiction = a re-observation after a gap whose state differs from the consistent history.

## Claim

1. any_interaction: saving < 1% for every policy.
2. humans_only, p = 0.1: keep-record covers >= 99% of cells within 200 steps.
3. humans_only: delete contradiction rate > 0; keep-record and recompute rate = 0.

## Refute if — any, at >= 3 of 5 seeds

- any_interaction saving >= 0.01 for any policy
- keep-record coverage < 0.99 at p = 0.1, humans_only
- delete contradiction rate == 0, humans_only
- keep-record or recompute contradiction rate > 0

SUPPORTED requires every part at >= 4 of 5 seeds. Otherwise INCONCLUSIVE.

## Known in advance (stated, not hidden)

Parts 1 and 3 hold largely by construction of the policies: the toy is an accounting check
that the definitions do what A1 and A6 say, not a discovery. Part 2 is arithmetic
(1 - 0.9^200), checked by simulation.
