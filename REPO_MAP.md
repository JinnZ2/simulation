# Repo map

Pieces live in separate folders until they're integrated. Nothing below is wired to anything
else yet — that's deliberate.

| Folder / file | What it is | State |
|---|---|---|
| `assumption_lab.py` | `AssumptionPlayground` — label exploration | standalone |
| `culture_ontology_notes.py` | cultural ontology notes script | standalone |
| `README.md` | the bounded-world simulation (agents, logistic regeneration, idolatry, Jubilee) | described; `run.py` and `config/` not present yet |
| `hypothesis-engine/` | autonomous research pipeline — explore → log → claim → test → modify → hidden-variables → consolidate | **live**; tests pass, offline run verified, CI wired |
| `research/` | imported research bundle — notes 00–10, plans, cross-repo integration matrix, and `TODO.md` (the NN-compression charter) | reference material |
| `.github/workflows/` | `hypothesis-engine.yml` — the only active workflow | manual dispatch now; cron activates on merge to default branch |

## How the two active pieces connect

`research/TODO.md` states the compression research charter and its five hypotheses.
`hypothesis-engine/config/topics.json` carries one topic per hypothesis, each tagged with a
`charter_hypothesis` key. So the engine's literature sweep feeds the charter directly: run the
engine, and `hypothesis-engine/hypotheses/*.md` accumulates drafts against H1–H5.

That is the only cross-folder dependency so far, and it is one-directional (config references
the charter by name; no code imports anything).

## Not yet integrated

- The bounded-world simulation described in `README.md` has no `run.py` or `config/` in the tree.
- `research/` targets five other repos (COH, GBCB, MCPM, CDT, hypothesis-engine); only the
  hypothesis-engine drop-in has been promoted into this repo and made to run.
- Phase 7 research outputs (`notes/11`, `integration/EXPLORE_AND_EXPERIMENT.md`) are referenced
  by `research/TODO.md` but were not in the imported archive.
