# sims/adapters

Adapters that bring claims from other repos into this ledger. Stdlib only. The core never imports
an adapter; adapters read a foreign format and emit ledger entries.

## `gm_claimtable_to_ledger.py`

Imported as supplied. Reads a Geometric-manifold- `CLAIM_TABLE` export (JSON list of claim dicts)
and appends each to a hash-chained ledger as a `PREDICT` entry with its refutation condition
attached.

Its one load-bearing behaviour, and the reason it belongs here: **a claim with no refutation
condition is rejected, not imported.** That is the same rule `harness/manifest.py` enforces on
`config.json`, arriving from the other direction.

```bash
python3 gm_claimtable_to_ledger.py <claim_table.json> [ledger.jsonl]
```

### Not wired into `sims/ledger.jsonl`

Deliberately. The two ledgers have different chain formats:

| | `gm_claimtable_to_ledger.py` | `sims/ledger_hook.py` |
|---|---|---|
| entry type | `PREDICT` — a claim awaiting test | `MEASURE` / `EXPLORATORY` — a claim already graded |
| chaining | `prev_hash` + `hash` per entry, genesis `"GENESIS"` | flat append, keyed on `metrics_hash` |
| provenance | foreign repo's claim table | a run under this harness with a verdict |

Mixing them would put untested claims and graded results in one stream with no way to tell which
is which, and would break `ledger_hook.py --check`, whose integrity check re-hashes each run's
`metrics.json`. An imported GM claim has no `metrics.json` to hash.

If GM claims should become entries here, the right move is to run them **as sims** — each claim
gets a `config.json`, a `NULL.md`, a pre-committed `REFUTE.md`, and a verdict — rather than
importing an assertion and calling it a ledger entry. `research/notes/13_geometric_manifold_combinations.md`
§4 lists that as recommended first move #3, sized at ~60 LOC; the work is in writing the refutation
conditions, not the adapter.

`sims/kappa_eff/` is the first instance of doing it that way: a GM claim, pre-registered and graded
under this harness rather than imported as a `PREDICT` line.
