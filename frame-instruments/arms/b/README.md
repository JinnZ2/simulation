# frame-instruments

Four stdlib-only instruments. B1 to B3 are built in order from
`WORKORDER_frame_instruments.md` (B1's reference spec is
`WORKORDER_runner_up_trace.md`); B4 lives in `b4/` and is built from
`WORKORDER_b4_dilemma_reconstruction.md`. Nothing here opens a network
socket; model and human output arrives as files.

```
B1  runner-up trace, offline half      traces.jsonl ──► separations ──► summary ──► report.md
                                                          │                 ▲
                                                          └─► permute ──► summary (second output, never a gate)
B2  audit isolation A/B/C/D            cases.jsonl ──► conditions ──► readers ──► audits.jsonl ──► agree
                                                          lock.py holds D's key behind a committed call
B3  split authorship                   statements ──► split ──► keys ──► join ──► cases.jsonl (arm-tagged) ──► B2
B4  dilemma reconstruction (b4/)       items ──► reconstruct ──► reconstructors ──► requirements ──► grade
                                                                                        │             agreement ◄── matches (external)
                                                                                        └─► nullshuffle ──► (new matches) ──► agreement/grade
                                       documented arm: calibrate ◄── factors + factor_matches (external)
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

# B4 (from frame-instruments/; b4/report.py is distinct from B1's report.py)
python3 b4/items.py        items.jsonl
python3 b4/reconstruct.py  items.jsonl N_RECONSTRUCTORS OUTDIR
python3 b4/requirements.py requirements.jsonl              # void if only true/false used
python3 b4/grade.py        requirements.jsonl grades.jsonl
python3 b4/agreement.py    requirements.jsonl matches.jsonl MATCH_SOURCE agreement.jsonl
python3 b4/nullshuffle.py  requirements.jsonl SEED requirements_shuffled.jsonl
python3 b4/calibrate.py    requirements.jsonl items_documented.jsonl factors.jsonl factor_matches.jsonl MATCH_SOURCE calibration.jsonl
python3 b4/report.py       items_hypothetical.jsonl items_documented.jsonl requirements.jsonl grades.jsonl agreement.jsonl \
                           grades_shuffled.jsonl agreement_shuffled.jsonl calibration.jsonl report.md

python3 -m pytest tests/ -q
```

## Conventions that a producer has to know

- `traces.jsonl`: `continuation[0]` is the first token generated after
  `forced_token`; `base_continuation[0]` is the base token at `i+1`.
  `selection_N` is the smallest stage-B N whose top-N-by-entropy set held
  the position; membership is nested downstream, so the N=50 cell holds
  the N=10 and N=25 positions too. Required.
- `separations.jsonl` carries `N`, `D` and `L` on every row; `summarise.py`
  sweeps all three and reports adjacent-N stability beside D and L.
- Cross-model overlap (RU-4) is written only when two or more models are
  present, and compares positions by index i. It is meaningful only where
  the models share a tokenizer or the producer aligned positions. The
  permuted file is its chance level; there is no threshold.
- `resync_D`: an L-gram ending at or before continuation token D occurs
  anywhere in the first D base tokens. Unaligned on purpose. L is swept
  over {2, 4, 8} and written into every row.
- `permute.py` shuffles tuples within (case_id, model_id, D, L) strata,
  independently per stratum, so adjacent-D agreement in the permuted file
  is chance.
- `audits.jsonl` conditions are A, B, C, D1 (locked call) and D2 (after
  the key). `agree.py` prints the A-vs-D1 order check first.
- B4 matching is external. `matches.jsonl` rows are
  `item_id, req_a, req_b, matched` with `req_* = "<reconstructor_id>/<req_id>"`;
  `factor_matches.jsonl` rows are `item_id, factor_id, req, matched`. The
  matcher's name is the MATCH_SOURCE argument and is stamped on every
  output row. The shuffled requirements need their own matches file.
- B4's physical/policy split is two lexicons in `b4/grade.py`, applied to
  `settling_test` only. Neither or both matching counts as unresolved and
  is printed with the ratio.
- B4 status has six values (true, false, lapsed, partial, unknown,
  undifferentiated). The work order calls this five-state grading and
  lists six; all six are accepted, and a file using only true/false is
  void.
- Exit codes: 0 ok/empty, 2 void, 1 error.
- No output row anywhere carries `label`, `category`, `type` or
  `interpretation`. `arm` is an experimental arm declared in `arms.py`.
