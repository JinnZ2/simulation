# frame-instruments

Four stdlib instruments built to three work orders:

- **B1** runner-up trace scoring (offline half, permutation null)
- **B2** audit-isolation runner (A/B/C/D, commit lock, agreement not correctness)
- **B3** split-authorship harness (arm-tagged cases feeding B2)
- **B4** dilemma reconstruction (five-state grading, shuffle null, calibration)

The work orders are at the top of this folder. They are the fixed ruler
and are byte-identical across every arm.

## This folder holds more than one build of them

Two independent builds exist, `arms/a` and `arms/b`. Both are green.
Neither is canonical. `ARMS.md` says how that happened and why both are
kept; the short version is that a merge tried to collapse them, damaged
the ten files where their layouts happened to agree, and left the
forty-one where they did not.

```text
python3 run_arms.py            run every arm's suites, per arm, per build
python3 coverage.py            each arm against the work order, no total
python3 coverage.py --queue    only the rows that differ, cheapest first
python3 coverage.py --provenance   each arm vs the commit it came from
python3 test_coverage.py       checks on this machinery; prints its count
```

Every one of those prints per arm. None of them produces a number that
summarises an arm, ranks the arms, or names a winner. That is enforced
by an AST guard in `test_coverage.py`, planted against.

## Working in an arm

Run an arm's suites from inside the arm; each arm bootstraps its own
`sys.path` and expects its own layout.

```text
arms/a   nested    python3 arms/a/b1/test_b1.py
arms/b   flat      cd arms/b/tests && python3 test_b1.py
```

Do not move code between arms, and do not add a file to the top level
that an arm should own. The top level holds the ruler and the
instruments that read it; the arms hold the builds. Keeping them
disjoint is what makes a third arm safe to add.

## Adding an arm

1. `arms/<id>/` -- a complete build. Nothing outside it.
2. `PARENT` and `DECLARED_EDITS` in `coverage.py` get its provenance.
3. `python3 coverage.py --provenance` must return VERBATIM+DECLARED.
4. `python3 run_arms.py` must find and pass its suites.

Nothing else changes. The table grows a column; the queue re-sorts.

## Constraints, from the work order

```text
Python 3, STANDARD LIBRARY ONLY      no numpy, no pandas, no requests
NO NETWORK in any script             model calls arrive as files
deterministic                        every seed is an argument and is recorded
one command, file paths as arguments
nothing over ~300 lines              split rather than grow
output is JSONL, one object per line
every run appends one row to runs.jsonl, ON EVERY PATH:
    ok / void / error / empty -- a failed run is a first-class row
no label / category / type / interpretation field in any output schema
    categories, if anyone wants them, are computed downstream
```

CC0.
