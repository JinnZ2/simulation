# CLAUDE.md

Guidance for working in this repository. Public; CC0; nothing here is private.

## What this repository is

**Four independent subsystems that share a repo and share no code.** That
is deliberate and stated in `REPO_MAP.md`: pieces live in separate
folders until they are integrated, and nothing imports across a folder
boundary. Treat each as its own repo with its own contract.

```text
simulation/         a bounded world. logistic pool, 100 agents,
                    4 actions (consume / share / build / forget),
                    emergent deference -> measured idolatry, shocks.
                    NO reward, NO score, NO controller. Raw JSONL out.
                    Python 3.11+. PyYAML optional (loader has a fallback).

hypothesis-engine/  autonomous research pipeline, 7 stages:
                    explore -> log -> claim -> test -> modify
                             -> hidden -> consolidate
                    Network at the explore stage only; --dry-run is offline.

sims/               physics sims under SIM HARNESS STANDARD v1:
                    config.json + NULL.md + REFUTE.md written BEFORE the
                    run; >= 5 seeds; >= 1 sweep; the sim GRADES ITSELF
                    SUPPORTED / REFUTED / INCONCLUSIVE against a
                    pre-committed threshold and appends to ledger.jsonl.
                    + explore.py (recycle refuted claims)
                    + shadow.py (cartography of what nothing measures)
                    numpy required.

frame-instruments/  four stdlib instruments B1..B4 (runner-up trace
                    scoring, audit isolation, split authorship, dilemma
                    reconstruction). TWO INDEPENDENT BUILDS are held as
                    arms/a and arms/b; neither is canonical. The three
                    work orders sit at the top as the shared ruler.
                    Both arms green, 36 tests each, counted apart.

research/           notes 00-18, plans, briefs, figures. Reference
                    material, not running code.
```

## The two front-page files, and a hazard

```text
STATUS.md    GENERATED between the <!-- generated:begin/end --> markers
             by `python3 status.py`. The next-steps half below the
             marker is hand-written and survives regeneration.
             CI runs `status.py --check`, so a stale STATUS.md is red.

REPO_MAP.md  hand-written layout. One row per piece; it listed
             frame-instruments twice with conflicting counts until
             2026-09-22 and now carries the held fork instead.
```

**`python3 status.py` rewrites STATUS.md in place**, so it is still the
instrument editing the tree it measures: run it when you intend to
regenerate, and check `git status` after an exploratory run. What it no
longer does is write a total it could not measure -- with no pytest it
now REFUSES (exit 3) and touches nothing, where it used to put
`0 tests pass ()` on the front page. An absent count is not a zero.

## Hard constraints

```text
no cross-folder imports      each subsystem stands alone; keep it that way
sims/: pre-registration      NULL.md and REFUTE.md before run.py, never after
sims/: refuting is working   a REFUTED verdict is a result, not a bug to fix
sims/: no edit-to-rescue     a wrong null or a wrong model is a NEW
                             pre-registration, not an edit to the old one
                             (see snap_information, shape_csd FINDINGS.md)
frame-instruments/: stdlib   no pip, no network
license: CC0
```

## Energy map of sims/ -- where a claim is refused

```text
config.json (seeds >= 5, >= 1 sweep, null_model, refute_if)
    |
    | missing null_model      -> not an experiment; the ledger adapter rejects it
    | missing refute_if       -> rejected upstream, at the harness
    | single seed             -> admitted, marked PILOT in the ledger
    v
run.py: ALL seeds x ALL sweep points x the null
    |
    v
evaluate refute_if AGAINST THE DATA
    |
    +-- SUPPORTED / REFUTED / INCONCLUSIVE, self-graded
    +-- metrics.json + summary.md + ledger_entry.jsonl
    |
    +--> explore.py   a refuted claim is the most informative output here
    |                 and is otherwise a dead end; this walks from
    |                 "we know why it failed" to the next pre-registration
    +--> shadow.py    finds structure nothing is pointed at, inferred from
                      residuals in measurements that WERE taken
```

Two results in the tree worth reading before adding a sim, because both
are about the method rather than the physics:

- `basin_convergence` **refuted a result supported at 5/5 seeds and
  replicated exactly.** Replication does not catch a shared grid error.
- `shape_csd_g1` **reversed its parent's refutation** by fixing one
  control. A refutation can be wrong too.

## The held fork in frame-instruments (repaired 2026-09-22)

Merge `5997025` (2026-09-12) joined two independent builds of three
byte-identical work orders by taking **both sides**.

```text
  parent A  85a3714 nested     parent B  5e04a33 flat
  PATH INTERSECTION  10 files -> 10 concatenations, both halves whole
  PATH DISJOINT      41 files -> 41 intact

  correlation: exact. The damage WAS the intersection.
```

Nine of the ten failed to parse. The tenth was `README.md` -- 40 + 99 =
139 lines, both halves whole, no syntax to break, so nothing reported
it. Checked out clean from their own parents, **both builds compile and
both run 4/4 suites green**. Neither was broken; the merge was.

Both are now kept, in disjoint namespaces:

```text
frame-instruments/
  WORK_ORDER_*.md      the ruler, identical in both parents, one copy
  coverage.py          each arm against the order. No total, no ranking.
  run_arms.py          every arm's suites. No total across arms.
  test_coverage.py     guards on the machinery, each planted against
  arms/a               85a3714 verbatim + declared edits
  arms/b               5e04a33 verbatim + declared edits
```

Nothing in an arm shares a path with anything in another arm, so the
collision that caused 100% of the damage cannot recur;
`test_coverage.py` asserts it. Neither arm is selected: on the 16
checked requirements **7 differ and neither dominates**, and
`coverage.py --queue` says what would settle each. `ARMS.md` carries
the argument, the declared edits, and the limits.

Rules that follow from it:

- Do not pick an arm, merge one into the other, or build a third from
  both without recording the decision. All three are live options and
  each is the operator's call.
- Do not add an arm's code to the top level, and do not move code
  between arms. The top level holds the ruler and the instruments that
  read it.
- A new arm is `arms/<id>/` plus its provenance in `coverage.py`'s
  `PARENT` and `DECLARED_EDITS`, and must return `VERBATIM+DECLARED`.
- `coverage.py` must never total, rank or recommend an arm. An AST
  guard in `test_coverage.py` enforces it and is planted against.
- Counts stay per arm. Summing two arms reports 72 tests of coverage
  where there are two implementations of one requirement set;
  `status.py` prints them apart for that reason.

## What runs in this container

```text
simulation/run.py                  YES
sims/<name>/run.py                 NO    numpy absent
sims|simulation|hypothesis-engine
  /tests via pytest                YES   after `pip install pytest`
                                         (93 / 42 / 19 at time of writing)
frame-instruments/run_arms.py      YES   stdlib; 36 per arm
frame-instruments/coverage.py      YES   --provenance needs full git history
status.py                          YES   REWRITES STATUS.md; refuses if it
                                         cannot count
```

`pytest` is not preinstalled but installs cleanly, so the three suites
are verifiable here. A `sims/<name>/run.py` is not -- numpy is absent,
and no change to a sim may be reported as tested.

## Conventions when editing

- A new experiment is a `sims/<name>/` folder with `config.json`,
  `NULL.md` and `REFUTE.md` **written first**, then `run.py`. If you
  cannot name the null, there is no experiment yet.
- Never edit a sim to change its verdict. Supersede it: a new folder, a
  new pre-registration, and a `FINDINGS.md` in the old one saying why.
  `prior_versions/` under `ep2_prereg` is the shape.
- `sims/_unretrofitted/` holds originals plus their recorded output,
  waiting on HARNESS.md section 5. Retrofitting one means writing its
  NULL and REFUTE from what was known *before* its recorded run, not
  from the output sitting next to it.
- STATUS.md's generated half is written by `status.py`; edit `status.py`
  or the sims, never the block. The hand-written half below the marker
  is yours.
- `REPO_MAP.md` and `STATUS.md` both state counts. A count that nothing
  recomputes is a typed number; prefer naming the command.
- The subsystems share no code **on purpose**. The two obvious links
  (engine's `stage_hidden` reading `simulation/`'s JSONL; `simulation/`
  brought under the `sims/` harness) are named in REPO_MAP as not built.
  Building one is a decision to record, not a tidy-up.

## Commands

```sh
cd simulation        && python3 run.py --cycles 500              # seconds
cd simulation        && python3 run.py                           # 10k cycles, ~45s, 173 MB log
cd simulation        && python3 run.py --log-level cycle         # 2 MB instead
cd hypothesis-engine && python3 scripts/hypothesis_engine.py --dry-run   # offline
cd sims/fractal_basin && python3 run.py                          # needs numpy

python3 -m pytest tests/ -q        # inside simulation/ hypothesis-engine/ sims/

cd frame-instruments && python3 run_arms.py           # every arm, per build
cd frame-instruments && python3 coverage.py           # arms vs the work order
cd frame-instruments && python3 coverage.py --queue   # only where they differ
cd frame-instruments && python3 coverage.py --provenance
cd frame-instruments && python3 test_coverage.py      # prints its count
python3 sims/ledger_hook.py --check                              # ledger integrity
python3 sims/explore.py                                          # recycle refuted claims
python3 sims/shadow.py                                           # what nothing measures
python3 status.py --check                                        # read-only
python3 status.py                                                # REWRITES STATUS.md
```
