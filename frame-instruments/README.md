# frame-instruments

Three stdlib-only instruments, built in order from
`WORKORDER_frame_instruments.md`. B1's reference spec is
`WORKORDER_runner_up_trace.md`. Nothing here opens a network socket; model
output arrives as files.

```
B1  runner-up trace, offline half      traces.jsonl ──► separations ──► summary ──► report.md
                                                          │                 ▲
                                                          └─► permute ──► summary (second output, never a gate)
B2  audit isolation A/B/C/D            cases.jsonl ──► conditions ──► readers ──► audits.jsonl ──► agree
                                                          lock.py holds D's key behind a committed call
B3  split authorship                   statements ──► split ──► keys ──► join ──► cases.jsonl (arm-tagged) ──► B2
```

Every script appends one row to `runs.jsonl` beside its output, on every
path: `ok`, `void`, `error`, `empty`. Failure is a row, never an absence.
Seeds are written into that row.

## Commands

```bash
# B1
python3 schema.py    base.jsonl traces.jsonl
python3 score.py     base.jsonl traces.jsonl separations.jsonl
python3 permute.py   separations.jsonl separations_permuted.jsonl SEED
python3 summarise.py separations.jsonl summary_real.jsonl
python3 summarise.py separations_permuted.jsonl summary_permuted.jsonl
python3 report.py    summary_real.jsonl summary_permuted.jsonl report.md

# B2
python3 conditions.py cases.jsonl OUTDIR          # A/B/C/D presentation files
python3 order.py      N_READERS SEED assignment.jsonl
python3 lock.py commit  READER CASE response.txt commits.jsonl
python3 lock.py release READER CASE cases.jsonl commits.jsonl key_out.jsonl
python3 agree.py      audits.jsonl cases.jsonl agreement.jsonl

# B3
python3 split.py prompts  OUTDIR
python3 split.py keyinput statements.jsonl OUTDIR
python3 join.py  statements.jsonl keys.jsonl single|split cases.jsonl
python3 arms.py  cases.jsonl

python3 -m pytest tests/ -q
```

## Conventions that a producer has to know

- `traces.jsonl`: `continuation[0]` is the first token generated after
  `forced_token`; `base_continuation[0]` is the base token at `i+1`.
- `resync_D`: an L-gram ending at or before continuation token D occurs
  anywhere in the first D base tokens. Unaligned on purpose. L is swept
  over {2, 4, 8} and written into every row.
- `permute.py` shuffles tuples within (case_id, model_id, D, L) strata,
  independently per stratum, so adjacent-D agreement in the permuted file
  is chance.
- `audits.jsonl` conditions are A, B, C, D1 (locked call) and D2 (after
  the key). `agree.py` prints the A-vs-D1 order check first.
- Exit codes: 0 ok/empty, 2 void, 1 error.
- No output row anywhere carries `label`, `category`, `type` or
  `interpretation`. `arm` is an experimental arm declared in `arms.py`.
