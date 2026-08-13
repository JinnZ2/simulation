# sims

Simulations that conform to [Sim Harness Standard v1](HARNESS.md): reproducible, falsifiable and
ledger-native **by construction, not by culture**.

The short version of what the standard buys: a sim cannot produce a result here without having said
in advance what would count as being wrong, and having said what "no effect" looks like. The
harness enforces that at config-load time, so a non-conforming sim doesn't run at all rather than
being caught downstream.

## Current results

| Sim | Verdict | What happened |
|---|---|---|
| [`fractal_basin`](fractal_basin/) | **SUPPORTED** | Three-well boundary is fractal at every damping tested; boundary dimension falls 1.75 → 1.45 as γ goes 0.1 → 0.5, and the Wada property vanishes entirely by γ = 0.5 |
| [`snap_information`](snap_information/) | **REFUTED** | Excess information over the null was *negative* at 5/5 seeds. Diagnosis: the load cancels out of the equations of motion, so the effect is zero by algebra — the claim was never testable in this model |

Both write findings alongside the raw artifacts:
[`fractal_basin/FINDINGS.md`](fractal_basin/FINDINGS.md),
[`snap_information/FINDINGS.md`](snap_information/FINDINGS.md).

## Run one

```bash
cd sims/fractal_basin && python3 run.py       # ~25s
cd sims/snap_information && python3 run.py    # ~20s
```

Needs numpy (the sims; the harness itself is stdlib-only). Options: `--seeds N [N...]` to override,
`--results-dir` to write elsewhere, `--quiet`.

Each run writes `results/<timestamp>/` containing `metrics.json`, `summary.md` and
`ledger_entry.jsonl`. Nothing is overwritten — a rerun makes a new directory.

```bash
python3 ledger_hook.py            # append new runs to the central ledger
python3 ledger_hook.py --show     # what's in it
python3 ledger_hook.py --check    # verify hashes, write nothing
```

`ledger_hook.py --check` re-hashes every `metrics.json` and compares it against what the ledger
recorded, so a results file edited after the fact is detectable rather than merely discouraged.

Tests: `python3 -m pytest tests/ -q` (32 tests, mostly about what the harness *refuses*).

## Layout

```
sims/
├── HARNESS.md              # the standard
├── harness/                # stdlib-only implementation of it
│   ├── manifest.py         # §2 config validation — refuses non-conforming sims
│   └── runner.py           # §3 execution contract, §4 verdict discipline
├── ledger_hook.py          # §1 central ledger
├── ledger.jsonl            # append-only
├── tests/
└── <name>/
    ├── run.py              # reads ONLY config.json + CLI overrides
    ├── config.json         # the manifest
    ├── NULL.md             # what "no effect" looks like
    ├── REFUTE.md           # falsification thresholds, written BEFORE running
    ├── FINDINGS.md         # what the run meant (added after)
    └── results/<stamp>/    # metrics.json, summary.md, ledger_entry.jsonl
```

## Two documented deviations from HARNESS.md

**`refute_params` is required.** §2 shows `refute_if` as a prose sentence
(`"detection lead < 15% of load range at >=3 of 5 seeds"`). A sentence can't be evaluated against
data without a parser, and a parser for English refutation conditions is a worse idea than the
problem it solves. So each config carries a `refute_params` object with the same numbers in
machine-readable form, and `run.py` grades from those. The prose and the numbers must agree — that
agreement is a human responsibility, and it is why both appear in `summary.md` side by side.

**`FINDINGS.md` is an addition.** The standard defines `NULL.md` and `REFUTE.md` as pre-run
documents and `summary.md` as auto-generated. Neither is the right home for "here is what this
result means and what we should do about it," written after the fact by a person. That is
`FINDINGS.md`. It is never read by the harness and never affects a verdict.

## Pre-registration is checkable, not claimed

§4 says a `refute_if` edited after seeing data makes the entry EXPLORATORY, never PREDICT. That is
only enforceable if you can tell when the condition was written.

Both sims' `NULL.md`, `REFUTE.md` and `config.json` were committed **in a commit that deliberately
contained no `run.py` and no results** — the thresholds could not have been fitted to data that did
not exist yet. `git log --follow sims/*/REFUTE.md` against the timestamps in `results/` is the
check. If you retrofit another sim, do the same: commit the pre-registration on its own first.

## What the two retrofits changed

Both originals are kept beside the retrofit as `original_*.py` for comparison. Neither original was
reproducible: `fractal_basin_sim.py` measured α at a single damping with one probe seed,
`snap_information_sim.py` used unseeded `np.random` throughout.

| | fractal_basin | snap_information |
|---|---|---|
| seeds | 1 → 5 | unseeded → 5 |
| sweep | γ = 0.25 only → {0.1, 0.25, 0.5} | γ = 0.05 only → {0.02, 0.05, 0.10} |
| null | none → `shuffle_labels` | none → `shuffle_load_labels` |
| verdict | none → self-graded | none → self-graded |
| other | `.npy` writes to a path outside the repo dropped; basin grid computed once per γ and shared across probe seeds | trajectories vectorized into one ensemble integration, ~50× faster, identical physics |

The γ sweep was mandated by HARNESS.md §5 item 4 for `fractal_basin`. It earned its keep
immediately: α moves from 0.25 to 0.55 across the swept range, so the original's single-damping
number described one operating point, not the potential.

## The snap_information result is the argument for the standard

That sim had a plausible claim, a working implementation, and printed output that read as a
finding — `"a snap event is an ADC: it digitizes accumulated analog load into discrete report"`.

Three things the harness required, in order, took it apart:

1. **A sweep.** Excess information was identical to four decimals across a 5× change in damping.
   A measurement that ignores the parameter it should be most sensitive to is not measuring.
2. **A null.** Raw MI was ~0.1 bits, which looks like something. Against the permutation null it
   was *negative* — the real pairing carried less apparent information than a shuffled one.
3. **A pre-committed threshold.** With no number fixed in advance, 0.1 bits is arguable. With
   0.20 bits committed beforehand, it isn't.

Following those three signals to their cause found that the load enters the equations of motion as
a pure translation and the initial condition is specified in the translated frame — so the load
cancels exactly, and `MI(load; ringdown) ≡ 0` before a single trajectory is integrated. Verified:
two trajectories 0.25 apart in load differ by exactly `0.0` in the shifted coordinate.

The claim isn't disproved. It was never tested. That is a more useful thing to learn than a weak
effect would have been, and none of the three steps that found it depended on anyone being careful
in the moment.
