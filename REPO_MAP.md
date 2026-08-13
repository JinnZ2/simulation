# Repo map

Pieces live in separate folders until they're integrated. Nothing below imports anything from
another folder — that's deliberate.

| Folder / file | What it is | State |
|---|---|---|
| `simulation/` | the bounded world — logistic regeneration, deference/idolatry, shocks, Jubilee | **live**; 42 tests, full 10k-cycle run verified |
| `hypothesis-engine/` | autonomous research pipeline — explore → log → claim → test → modify → hidden-variables → consolidate | **live**; 10 tests, offline run verified, CI wired |
| `research/` | imported research bundle — notes 00–10, plans, cross-repo integration matrix, and `TODO.md` (the NN-compression charter) | reference material |
| `assumption_lab.py` | `AssumptionPlayground` — label exploration | standalone |
| `culture_ontology_notes.py` | cultural ontology notes script | standalone |
| `.github/workflows/` | `tests.yml` (both suites + a no-PyYAML run), `hypothesis-engine.yml` | active on push |

## Quick start

```bash
cd simulation        && python3 run.py --cycles 500
cd hypothesis-engine && python3 scripts/hypothesis_engine.py --dry-run
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

`simulation/` is not connected to either. The obvious future link is the engine's hidden-variable
scan (`stage_hidden`) reading the simulation's per-cycle JSONL instead of only its own findings
log — both already speak residual series. Nothing has been built for that.

## Not yet integrated

- `simulation/` and `hypothesis-engine/` share no code. Both implement their own notion of a
  measured series; neither knows about the other.
- `research/` targets five repos (COH, GBCB, MCPM, CDT, hypothesis-engine); only the
  hypothesis-engine drop-in has been promoted into this repo and made to run.
- Phase 7 research outputs (`notes/11`, `integration/EXPLORE_AND_EXPERIMENT.md`) are referenced by
  `research/TODO.md` but were not in the imported archive.
- The `hypothesis-engine` cron is inert until this branch merges — GitHub runs scheduled workflows
  only from the default branch.
