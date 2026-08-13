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
| [`ep2_prereg`](ep2_prereg/) | **SUPPORTED** | The physical instrument's E-P2 protocol has the power to detect an approaching snap with 18.3% lead at 10% timing noise — but only with two arms and one pre-committed checkpoint. The criteria it replaces fire on a rigid null 44% and ~95% of the time |
| [`snap_information`](snap_information/) | **REFUTED** | Excess information over the null was *negative* at 5/5 seeds. Diagnosis: the load cancels out of the equations of motion, so the effect is zero by algebra — the claim was never testable in this model |
| [`shape_csd`](shape_csd/) | **REFUTED** | The recovery-time divergence is real and large (110→600 steps, variance up 11–83×) — but a *monostable* frame with no fold shows the same rise under the same compression, at 4/5 seeds with hard probes. Compressing a spring network softens it; a single-arm measurement can't tell that from CSD |
| [`kappa_eff`](kappa_eff/) | **REFUTED** | Curvature rises early but *peaks* late, and the kill criteria are peak-based. K1/K2 fired at 5/5 seeds at every drop threshold. "Spikes before failure" doesn't distinguish onset from maximum, and they have opposite lead properties |

Each writes findings alongside the raw artifacts — see the `FINDINGS.md` in each folder.

Retrofit queue status (HARNESS.md §5): items **1** (`ep2_prereg`), **2** (`shape_csd`, the
headline CSD claim), **3** (`kappa_eff`), **4** (`fractal_basin`) and part of **5**
(`snap_information`) are done. The rest of item 5 — `s3_s7.py`, `shape_fold_*.py`,
`rosetta_shape_sim.py`, `shape_specialization_sim.py`, `shape_mode_filtered_ews.py` — sits
unretrofitted in [`_unretrofitted/`](_unretrofitted/) with the originals' recorded output.

**Three of five verdicts are REFUTED, and every one of them was refuted by its null.** That is the
standard working, not the sims failing: each had a real-looking signal that survived until it was
compared against a matched control.

## Run one

```bash
cd sims/fractal_basin    && python3 run.py    # ~25s
cd sims/snap_information && python3 run.py    # ~20s
cd sims/ep2_prereg       && python3 run.py    # ~2s
cd sims/kappa_eff        && python3 run.py    # ~5s
cd sims/shape_csd        && python3 run.py    # ~10s, stdlib only
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

## Recycling a refuted claim

Three of five verdicts here are REFUTED, each with a diagnosed cause and a "what a corrected test
would look like" section. `explore.py` carries that forward into the next pre-registration.

```bash
python3 explore.py                        # what's recyclable, and what's hiding in the metrics
python3 explore.py --hidden               # hidden-variable scan only
python3 explore.py --cross-domain         # where this structure recurs
python3 explore.py --scaffold shape_csd   # write a successor candidate
```

**It does not write refutation conditions and it does not run anything.** A tool that reformulated
a claim until it passed would automate exactly what HARNESS.md §4 forbids, and would be fast at it.
So `--scaffold` emits a folder whose `refute_if` is empty — `harness/manifest.py` refuses to load
it — plus a REFUTE.md of TODO prompts carrying the parent's diagnosis, hidden-variable candidates,
and cross-domain leads. A person writes the condition, or the successor never runs.

Three guards, each mirroring something the ecosystem already does:

| guard | mirrors |
|---|---|
| only REFUTED/INCONCLUSIVE claims may be recycled | the falsification ledger's `refute()` gate — no retuning a claim that survived (notes/08 §A.3) |
| lineage bounded at generation 3, then journalled to `unknown_journal.jsonl` | `hypothesis_engine.py`'s escape hatch at 3 reformulations |
| successors carry `exploratory: true` | HARNESS.md §4 — reformulated claims never re-enter as PREDICT |

**Hidden-variable scan.** Correlates every recorded-but-ungraded metric against the swept
parameters, flagging `|r| > 0.5` — the same trigger the hypothesis engine's HND stage uses. A
strong correlate that no refutation condition mentions is either a confound or the measurement that
should have been graded. Metrics that are affine restatements of a graded one (`d_boundary = 2 − α`)
are detected and labelled as such rather than reported as discoveries.

**Cross-domain transfer.** Matches a sim's structural signature — fold, information channel,
curvature, detector — against `research/notes/08` Part B, which identifies eight domains whose
governing equations instantiate the cusp normal form directly. These are prompts for a human, not
evidence, and the tool says so where it prints them.

Tests: `python3 -m pytest tests/ -q` (63 tests, mostly about what the harness and the recycler *refuse*).

## Layout

```
sims/
├── HARNESS.md              # the standard
├── harness/                # stdlib-only implementation of it
│   ├── manifest.py         # §2 config validation — refuses non-conforming sims
│   └── runner.py           # §3 execution contract, §4 verdict discipline
├── ledger_hook.py          # §1 central ledger
├── ledger.jsonl            # append-only
├── explore.py              # recycle refuted claims into successor candidates
├── unknown_journal.jsonl   # lineages that hit the escape hatch
├── adapters/               # foreign claim formats in (see adapters/README.md)
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

Every sim's `NULL.md`, `REFUTE.md` and `config.json` were committed **in a commit that deliberately
contained no `run.py` and no results** — the thresholds could not have been fitted to data that did
not exist yet. `git log --follow sims/*/REFUTE.md` against the timestamps in `results/` is the
check. If you retrofit another sim, do the same: commit the pre-registration on its own first.

## What the retrofits changed

Every original is kept beside its retrofit as `original_*.py`. **None of the four was
reproducible**: two used a single hard-coded seed, two used unseeded `np.random`. None had a null.

| | fractal_basin | snap_information | ep2_prereg | kappa_eff |
|---|---|---|---|---|
| seeds | 1 → 5 | unseeded → 5 | unseeded → 5 | 1 fixed → 5 |
| sweep | γ=0.25 → {0.1, 0.25, 0.5} | γ=0.05 → {0.02, 0.05, 0.10} | noise 5% → {2%, 5%, 10%} | drop threshold 5pt → {2, 5, 10} |
| null | none → `shuffle_labels` | none → `shuffle_load_labels` | none → `rigid_arm_creep_only` | none → `random_ray` |
| verdict | none → self-graded | none → self-graded | none → self-graded | printed → self-graded |
| other | `.npy` writes outside the repo dropped; grid computed once per γ | ensemble vectorized, ~50× faster, identical physics | all three criteria measured on both arms every run | torch → numpy (Tier-1 discipline, notes/10 §2.2) |

Two sweeps were mandated by HARNESS.md §5 itself — γ for `fractal_basin` (item 4) and the criterion
sweep for `kappa_eff` (item 3). Both earned their keep, in opposite ways: α moves from 0.25 to 0.55
across γ, so the original's single-damping number described one operating point rather than the
potential; while the `kappa_eff` verdict turned out **not** to depend on the swept criterion at all,
which located the real criterion-dependence somewhere else entirely (peak versus onset).

## Cross-validation against the research notes

`fractal_basin` reproduces `research/notes/17_fractals_bio_cosmo_trig.md` §1 exactly, at the
original's damping:

| quantity | notes/17 | measured here (γ = 0.25) |
|---|---:|---:|
| α double-well | 0.69 | 0.691 |
| α triple-well | 0.39 | 0.390 |
| Wada fraction | 8% | 8.0% |

Three significant figures on all three, from an independent reimplementation under the harness.
That is a genuine replication of the earlier result, and it makes the γ sweep's finding — that
these numbers move a lot with damping — a claim about the same measurement rather than a different
one.

`snap_information` is consistent with `research/notes/18_flip_as_event.md` §3, which already called
the load-to-ringdown channel an "honest null" at 0.22 bits of 3.46. The harness strengthens that:
the MI is not merely small, it is *below a permutation null*, and the cause is structural rather
than statistical.

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
