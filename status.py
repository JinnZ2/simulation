#!/usr/bin/env python3
"""Regenerate the generated half of STATUS.md.

    python3 status.py           # rewrite STATUS.md
    python3 status.py --check   # non-zero exit if it is stale

STATUS.md is meant to be read on a phone: one screen, narrow lines, no wide
tables. Half of it is facts that go stale (verdicts, test counts) and half is
judgement (what to do next). The facts are generated from the repo so they
cannot drift; the judgement lives between HAND-WRITTEN markers and is never
touched by this script.

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUS = ROOT / "STATUS.md"

BEGIN = "<!-- generated:begin -->"
END = "<!-- generated:end -->"

SUITES = ["sims", "simulation", "hypothesis-engine"]

# frame-instruments holds more than one independent build of one work order.
# Its suites are counted PER ARM and kept out of the repo total: summing two
# arms would report 72 tests of coverage where there are two implementations
# of one requirement set. See frame-instruments/ARMS.md.
ARMED = "frame-instruments"


def test_count(folder: str) -> int | None:
    """Collect-only, so this stays fast enough to run on every edit."""
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", f"{folder}/tests", "-q", "--collect-only"],
            cwd=ROOT, capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return None
    match = re.search(r"(\d+) tests? collected", out) or re.search(r"(\d+) test", out.strip().splitlines()[-1] if out.strip() else "")
    return int(match.group(1)) if match else None


def arm_counts() -> dict:
    """Tests per arm, never summed across arms. Empty dict if unavailable;
    an absent count is not a zero."""
    try:
        out = subprocess.run(
            [sys.executable, "run_arms.py", "--json"],
            cwd=ROOT / ARMED, capture_output=True, text=True, timeout=300)
    except Exception:
        return {}
    try:
        data = json.loads(out.stdout)
    except Exception:
        return {}
    res = {}
    for arm, rows in data.items():
        if any(r.get("ran") is None for r in rows):
            continue
        res[arm] = sum(r["ran"] for r in rows)
    return res


def ledger_rows() -> list[dict]:
    path = ROOT / "sims" / "ledger.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def generated_block() -> str:
    rows = ledger_rows()
    supported = [r for r in rows if r["verdict"] == "SUPPORTED"]
    refuted = [r for r in rows if r["verdict"] == "REFUTED"]
    inconclusive = [r for r in rows if r["verdict"] == "INCONCLUSIVE"]
    counts = {f: test_count(f) for f in SUITES}
    total = sum(v for v in counts.values() if v)
    arms = arm_counts()

    lines = ["## Where things stand", ""]
    tally = f"{len(supported)} supported, {len(refuted)} refuted"
    if inconclusive:
        tally += f", {len(inconclusive)} inconclusive"
    lines.append(f"**{len(rows)} experiments run** — {tally}.")
    lines.append("")
    lines.append(f"**{total} tests pass** "
                 f"({', '.join(f'{k} {v}' for k, v in counts.items() if v)}).")
    lines.append("")
    if arms:
        per = ", ".join(f"arm {a} {n}" for a, n in sorted(arms.items()))
        lines.append(f"**`frame-instruments` passes per arm** ({per}) — two "
                     f"independent builds of one work order, counted apart "
                     f"rather than summed. See `frame-instruments/ARMS.md`.")
    else:
        lines.append("**`frame-instruments` arm counts unavailable** — "
                     "`run_arms.py` did not report.")
    lines.append("")
    lines.append("*A refutation is a working experiment, not a broken one.*")
    lines.append("")

    lines.append("### Experiments")
    lines.append("")
    # supported first, then refuted; both spelled out rather than pass/fail
    order = {"SUPPORTED": 0, "INCONCLUSIVE": 1, "REFUTED": 2}
    for r in sorted(rows, key=lambda r: (order.get(r["verdict"], 3), r["name"])):
        tag = " *(exploratory)*" if r.get("type") == "EXPLORATORY" else ""
        lines.append(f"- `{r['name']}` — **{r['verdict'].lower()}**{tag}")
    lines.append("")

    lines.append("### Pieces")
    lines.append("")
    lines.append("- `sims/` — experiments + harness, live")
    lines.append("- `simulation/` — the bounded world, live")
    lines.append("- `hypothesis-engine/` — research pipeline, live")
    lines.append("- `frame-instruments/` — runner-up trace scoring, audit isolation, split authorship, dilemma reconstruction; "
                 "two arms held, neither canonical, live")
    lines.append("- `research/` — notes 00–18, reference only")
    lines.append("")

    lines.append("### Tools")
    lines.append("")
    lines.append("- `sims/explore.py` — recycle refuted claims")
    lines.append("- `sims/shadow.py` — find what nothing measures")
    lines.append("- `sims/ledger_hook.py --check` — verify integrity")
    lines.append("- `frame-instruments/coverage.py` — each arm against the work order")
    lines.append("- `frame-instruments/coverage.py --queue` — where the arms differ")
    return "\n".join(lines)


def render(existing: str | None) -> str:
    block = generated_block()
    if existing and BEGIN in existing and END in existing:
        head, rest = existing.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return f"{head}{BEGIN}\n{block}\n{END}{tail}"
    raise SystemExit("STATUS.md is missing its generated:begin/end markers")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate STATUS.md facts.")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if STATUS.md is stale; write nothing")
    args = parser.parse_args(argv)

    if not STATUS.exists():
        raise SystemExit("STATUS.md not found")

    # An environment without pytest counts every suite as None, and the old
    # code turned that into "0 tests pass ()" -- an absent measurement written
    # as a zero, onto the repo's front page, by anyone who ran this to see
    # what it said. Refuse instead. A count nobody could take is not a count.
    if all(test_count(f) is None for f in SUITES):
        print("cannot count any suite (is pytest installed?) -- "
              "refusing to write a total this environment cannot measure",
              file=sys.stderr)
        return 3

    current = STATUS.read_text(encoding="utf-8")
    updated = render(current)

    if args.check:
        if current == updated:
            print("STATUS.md is current")
            return 0
        print("STATUS.md is stale — run: python3 status.py", file=sys.stderr)
        return 1

    STATUS.write_text(updated, encoding="utf-8")
    print("STATUS.md updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
