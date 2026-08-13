# hypothesis-engine

Autonomous, **stdlib-only, deterministic** research pipeline. It queries free scholarly APIs,
stakes each finding as a falsifiable claim, tests claims by cross-source corroboration,
reformulates failures until an escape hatch fires, scans for hidden variables, and consolidates
survivors into hypothesis drafts. No LLM in the loop — it runs free on GitHub runners.

Design doc: [`docs/hypothesis_engine.md`](docs/hypothesis_engine.md).

## Layout

```
hypothesis-engine/
├── scripts/hypothesis_engine.py   # the whole engine (798 lines, stdlib only)
├── scripts/sample_findings.json   # 5 findings / 2 topics, used by --dry-run
├── config/topics.json             # what to research
├── docs/hypothesis_engine.md      # pipeline design doc
├── tests/test_hypothesis_engine.py
├── data/                          # generated: findings log, claim tree, journals, report
└── hypotheses/                    # generated: one .md per topic
```

`data/` and `hypotheses/` do not exist until a run creates them.

## Run it

```bash
cd hypothesis-engine

# offline — bundled sample findings, no network
python3 scripts/hypothesis_engine.py --dry-run

# live
python3 scripts/hypothesis_engine.py --max-per-topic 5

# single topic, output somewhere scratch
python3 scripts/hypothesis_engine.py \
  --config /tmp/one-topic.json --data-dir /tmp/data --hypotheses-dir /tmp/hyp
```

Flags: `--config`, `--dry-run`, `--max-per-topic`, `--data-dir`, `--hypotheses-dir`, `--sample`.

Tests: `pip install pytest && python3 -m pytest tests/ -q` (10 tests).

## Topics

`config/topics.json` carries two groups:

1. **Ecosystem topics** (original three) — LLM calibration/falsifiability, hidden-variable
   detection, world models and curiosity.
2. **Charter topics** (five, added here) — one per hypothesis in
   [`../research/TODO.md`](../research/TODO.md): activation-aware quantization, structured
   sparsity, compression ordering, representation geometry, deployment-aware metrics. Each
   carries a `charter_hypothesis` key naming the hypothesis it feeds. That key is documentation
   only — the engine reads `name`, `queries`, `sources` and ignores the rest.

Current cost: 8 topics, 23 queries, up to 55 API calls per run.

Adding a topic: append an entry, commit. The next scheduled run picks it up.

## CI

`.github/workflows/hypothesis-engine.yml` at the repo root (workflows only execute from there).
Two jobs: `test` (pytest + offline smoke run) then `run-engine`, which runs live, uploads
`data/` and `hypotheses/` as artifacts, commits results back, and opens an issue when the report
contains the `NEW HYPOTHESIS` marker (≥3 surviving claims on a topic).

Triggers: `workflow_dispatch` (inputs: `topic`, `max_per_topic`, `dry_run`) and cron Mon/Thu
06:00 UTC. **The cron only fires once this branch is merged** — GitHub runs scheduled workflows
from the default branch only. Until then the engine is manual-dispatch only.

## Verification status

| Check | Result |
|---|---|
| Unit tests | 10/10 pass (Python 3.11) |
| Offline `--dry-run`, 8-topic config | all 7 stages complete; 5 findings → 4 claims staked, 1 → unknown journal, 2 hypothesis files |
| Live network run | **not verifiable from this sandbox** — see below |

The three scholarly hosts (`export.arxiv.org`, `api.semanticscholar.org`, `api.crossref.org`)
are blocked by this development sandbox's egress policy; all three return 403 at the proxy. The
engine degraded exactly as designed — logged each failure, continued, completed every stage with
zero findings. GitHub runners have open egress, so CI is the first place a live run can be
observed. Treat the first `run-engine` result as the real network smoke test.

## Known limitations

Carried from the design doc — these are deliberate, not defects:

- **Claim extraction is template-based**, not semantically parsed. False positives are expected
  and are handled by staking + testing, not by better parsing.
- **Cross-source corroboration is weak evidence.** Corroboration is not replication; hypothesis
  drafts are starting points for human review.
- **Findings without abstracts produce thin claims** that tend to route to the unknown journal.
  Crossref abstract coverage is patchy.
