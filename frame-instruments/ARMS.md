# ARMS -- the held fork, and why it is held

## What happened

Merge `5997025` (2026-09-12, "Merge branch 'main' into
claude/frame-instruments-setup-jathyz") joined two independent builds of
three byte-identical work orders. It resolved by taking **both sides**.

```text
  parent A  85a3714              parent B  5e04a33
  nested layout                  flat layout
  b1/ b2/ b3/ b4/                *.py at root + b4/
  workorders/                    WORKORDER_*.md
  b1/test_b1.py                  tests/test_b1.py

  PATH INTERSECTION  10 files  ->  10 concatenations, both halves whole
  PATH DISJOINT      41 files  ->  41 files intact

  correlation: exact. The damage IS the intersection.
```

The ten: `runrecord.py`, `README.md`, and the eight modules under `b4/`.
Nine failed to parse. The tenth was `README.md`, which has no syntax to
break, so nothing reported it -- 40 + 99 = 139 lines, both halves whole.

Divergent layout **protected** b1-b3. Convergent layout **destroyed**
b4, the shared run record, and the README.

## Why both arms are kept

Checked out clean from their own parents, **both arms compile and both
run 4/4 suites green**. Neither was broken. The merge was.

`discriminate.py` from the `decision-aperture` sibling, run on all 25
same-named pairs: **25 of 25 DISCRIMINATES**, 0.32 to 0.54 against a
threshold of 0.20, with a self-control of 0.0000. No cosmetic twins.
The two arms barely share a function name.

Scored against the shared work order -- the one fixed ruler, identical
in both parents -- **neither arm dominates**. `coverage.py` prints the
table; `coverage.py --queue` prints only the rows that differ. Picking
one arm drops whatever the other holds alone, silently, which is what
the default merge resolution would have done had it produced parseable
files.

## Layout

```text
frame-instruments/
  WORK_ORDER_B1_B3.md      the ruler. Byte-identical in both parents,
  WORK_ORDER_B4.md         so one copy, at the top, outside every arm.
  WORK_ORDER_RUNNER_UP.md
  liftable/                spec, not code. Arm A only in the parents.
  coverage.py              scores each arm against the order. No total.
  run_arms.py              runs every arm's suites. No total across arms.
  test_coverage.py         guards on the machinery, each planted against.
  arms/
    a/    <- 85a3714 verbatim + declared edits.  b1/ b2/ b3/ b4/, own runs/
    b/    <- 5e04a33 verbatim + declared edits.  flat + b4/ + tests/, own runs/
```

Arms sit in disjoint namespaces. A future merge of a third arm cannot
collide with these, because nothing in an arm shares a path with
anything in another arm. That is the property the whole layout is for,
and `test_coverage.py::test_no_path_collides_between_arms` asserts it.

## The declared edits

Each arm is its parent's tree verbatim except for the edits below.
`python3 coverage.py --provenance` compares every file against the
parent commit and refuses unless the differing set is exactly this:

```text
arm a   runrecord.py    ARM constant + one provenance field in record()
arm a   b1/test_b1.py   run-record key-set pin widened by exactly one key
arm b   runrecord.py    ARM constant + one provenance field in write_record()
```

`arm` names WHICH IMPLEMENTATION produced a row. It is provenance, the
same class as `script`, `seed` and `args_hash`, and is not one of the
four fields the order forbids (`label`, `category`, `type`,
`interpretation`) -- those are categories, and the order says categories
are computed downstream from these files.

Arm A's `b1/test_b1.py` needed widening because it **pins the run-record
key set**, so adding a field turned it red. The repair added `arm` to
the pinned set. It did not loosen the assertion: the pin is the property
that caught the change, and loosening it would delete that property to
make room for the thing it caught.

## What building the arms found

Adding one field to the record turned **exactly one arm red**. Arm A
pins the key set in a test; arm B does not. Nothing in the reading found
that -- the build found it, and it is now row R14 in the table.

## The discriminator queue

`python3 coverage.py --queue`. It ranks REQUIREMENTS by how a difference
gets settled, cheapest first. It does not rank arms.

```text
WORK_ORDER_TEXT     the answer is already written in the order
OPERATOR_DECISION   a person decides; the order does not say
MEASUREMENT         needs data nobody has
```

## What is NOT decided here

No arm is selected. No arm is merged into the other. No third design is
built from both. Those are three different next moves and each is the
operator's, not this layout's. What the layout buys is that all three
stay available, and that the fork is on the record with its
discriminators attached rather than resolved by a merge driver nobody
watched.

## Limits

- `coverage.py` rows marked `LEXICAL` are pattern lookups; a rewrite
  steps around them. Rows marked `AST` read the parse tree. The mark is
  printed on every row.
- Four defects were found in `coverage.py` **by running it**, not by
  reading it: a `[2, 4, 8]` pattern that missed `(2, 4, 8)` in both
  arms; an ambiguous basename lookup that graded `b4/report.py` in place
  of `report.py`; a permuted-branch test that fired on a docstring and
  then on a loader import; and a provenance check that passed over zero
  comparisons because a git pathspec resolved against the wrong
  directory. Three of the four ran toward under-reporting an arm's
  coverage. The fourth reported a clean provenance having compared
  nothing.
- The divergence numbers are **structural** (AST / token multiset), not
  behavioural. Two arms that differ only in behaviour would read as
  identical, and that false negative is `discriminate.py`'s own stated
  limit.
- Nothing here says an arm is correct. It says what each one covers.
