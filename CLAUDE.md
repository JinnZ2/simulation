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
                    reconstruction) + shared runrecord.py.
                    ** DOES NOT IMPORT AT HEAD -- see Known defects. **

research/           notes 00-18, plans, briefs, figures. Reference
                    material, not running code.
```

## The two front-page files, and a hazard

```text
STATUS.md    GENERATED between the <!-- generated:begin/end --> markers
             by `python3 status.py`. The next-steps half below the
             marker is hand-written and survives regeneration.
             CI runs `status.py --check`, so a stale STATUS.md is red.

REPO_MAP.md  hand-written layout. Currently lists frame-instruments
             TWICE, with 36 tests in one row and 35 in the other.
```

**HAZARD: `python3 status.py` rewrites STATUS.md in place.** Running it
to see what it says *changes the repo's front page*, and in an
environment missing pytest it writes `0 tests pass ()`. This is the
instrument editing the tree it measures. Run it only when you intend to
regenerate, and check `git status` after any exploratory run.

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

## Known defects (verified 2026-09-22, NOT repaired)

**frame-instruments does not parse. Nine files are two versions
concatenated.**

```text
frame-instruments/runrecord.py      307 lines = 151 + 164, both halves whole
frame-instruments/b4/items.py       and 7 more under b4/
        agreement.py  calibrate.py  grade.py  nullshuffle.py
        reconstruct.py  report.py  requirements.py
```

Traced: merge `5997025` ("Merge branch 'main' into
claude/frame-instruments-setup-jathyz", 2026-09-12) resolved by taking
**both sides**. `git show 85a3714:frame-instruments/runrecord.py` is 151
lines and `git show 5e04a33:...` is 164; the file on disk is the first
truncated mid-`for`-body with the second appended whole. Every B1..B4
test imports `runrecord`, so all 36 of them die at import with
`IndentationError`, and the CI leg that runs `pytest tests/` in
`frame-instruments/` is red at HEAD.

`STATUS.md` states **190 tests pass (... frame-instruments 36)**. That
is false at HEAD and not an environment artifact -- it is a syntax error
in checked-in code.

The repair is to pick ONE parent's version per file and re-run
`python3 frame-instruments/bN/test_bN.py`. It is not a merge to redo by
hand line by line.

**frame-instruments is also duplicated, and the copies differ.**

```text
frame-instruments/*.py       +  tests/       flat copy
frame-instruments/bN/*.py    +  bN/test_bN.py nested copy
```

Every same-named pair DIFFERS (`score.py` vs `b1/score.py`, `agree.py`
vs `b2/agree.py`, and so on, 13 pairs), as do all four test files. The
three work orders are duplicated identically
(`WORKORDER_*.md` == `workorders/*.md`). Files that live in one place do
not drift; two copies already have. Deciding which tree is canonical is
a prerequisite to the repair above, not a follow-up.

## What runs in this container

```text
simulation/run.py           YES   (PyYAML present; fallback also exists)
sims/                       NO    numpy absent
*/tests via pytest          NO    pytest absent -- three of four suites
frame-instruments/bN/test   NO    but for a CODE defect, not the environment
status.py                   YES   and it REWRITES STATUS.md; see hazard
```

So three suites are unverifiable here for an environment reason and one
is broken for a real one. Do not report a change to `sims/` or
`hypothesis-engine/` as tested.

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
python3 frame-instruments/bN/test_bN.py                          # stdlib; broken at HEAD
python3 sims/ledger_hook.py --check                              # ledger integrity
python3 sims/explore.py                                          # recycle refuted claims
python3 sims/shadow.py                                           # what nothing measures
python3 status.py --check                                        # read-only
python3 status.py                                                # REWRITES STATUS.md
```
