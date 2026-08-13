# Repo map

For current state rather than layout, see [`STATUS.md`](STATUS.md).

Pieces live in separate folders until they're integrated. Nothing below imports anything from
another folder — that's deliberate.

| Folder / file | What it is | State |
|---|---|---|
| `simulation/` | the bounded world — logistic regeneration, deference/idolatry, shocks, Jubilee | **live**; 42 tests, full 10k-cycle run verified |
| `hypothesis-engine/` | autonomous research pipeline — explore → log → claim → test → modify → hidden-variables → consolidate | **live**; 10 tests, offline run verified, CI wired |
| `sims/` | physics sims under Sim Harness Standard v1 — pre-registered, self-grading, ledger-native, with a guarded recycler for refuted claims | **live**; 90 tests, 8 sims run (3 SUPPORTED, 5 REFUTED), plus a claim recycler and a shadow cartographer |
| `research/` | imported research bundle — notes 00–18, plans, briefs, terminology map, hardware, figures, cross-repo integration matrix, and `TODO.md` | reference material |
| `assumption_lab.py` | `AssumptionPlayground` — label exploration | standalone |
| `culture_ontology_notes.py` | cultural ontology notes script | standalone |
| `.github/workflows/` | `tests.yml` (all three suites + a no-PyYAML run), `hypothesis-engine.yml` | active on push |

## Quick start

```bash
cd simulation           && python3 run.py --cycles 500
cd hypothesis-engine    && python3 scripts/hypothesis_engine.py --dry-run
cd sims/fractal_basin   && python3 run.py
```

Note the root README's `python run.py --config config/default.yaml` now means
`cd simulation && python3 run.py --config config/default.yaml` — the piece moved into its own
folder, its contents otherwise unchanged from the spec.

## How the pieces connect

Only one link exists so far, and it is one-directional documentation — no code imports:

- `research/TODO.md` states the compression research charter and its five hypotheses.
- `hypothesis-engine/config/topics.json` carries one topic per hypothesis, each tagged with
  `charter_hypothesis`. Running the engine accumulates literature drafts against H1–H5 in
  `hypothesis-engine/hypotheses/`.

`simulation/` and `sims/` are not connected to either. Two obvious future links, neither built:

- The engine's hidden-variable scan (`stage_hidden`) could read `simulation/`'s per-cycle JSONL
  instead of only its own findings log — both already speak residual series.
- `simulation/` could be brought under `sims/`'s harness. It currently asserts invariants in tests
  but has no NULL.md, no pre-committed refutation condition, and no self-grading verdict. Its
  idolatry finding is exactly the kind of claim the harness exists to discipline.

## Not yet integrated

- `simulation/`, `hypothesis-engine/` and `sims/` share no code. Each implements its own notion of
  a measured series; none knows about the others.
- `sims/snap_information` is REFUTED for a structural reason — the load cancels out of the
  equations of motion. Rebuilding it is a new pre-registration, not an edit; see its `FINDINGS.md`.
- `research/` targets five repos (COH, GBCB, MCPM, CDT, hypothesis-engine); only the
  hypothesis-engine drop-in has been promoted into this repo and made to run.
- HARNESS.md §5's retrofit queue: items 1–4 and part of 5 are done. The rest of item 5 sits
  unretrofitted in `sims/_unretrofitted/` (`s3_s7.py`, `shape_fold_*.py`, `rosetta_shape_sim.py`,
  `shape_specialization_sim.py`, `shape_mode_filtered_ews.py`) with the originals' recorded output.
- `sims/shape_csd` is REFUTED against a null whose geometry does not match the test arm. The
  corrected null is a new pre-registration, not an edit — see its `FINDINGS.md`.
- The `hypothesis-engine` cron is inert until this branch merges — GitHub runs scheduled workflows
  only from the default branch.
