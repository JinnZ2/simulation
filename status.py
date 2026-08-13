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

    lines = ["## Where things stand", ""]
    tally = f"{len(supported)} supported, {len(refuted)} refuted"
    if inconclusive:
        tally += f", {len(inconclusive)} inconclusive"
    lines.append(f"**{len(rows)} experiments run** — {tally}.")
    lines.append("")
    lines.append(f"**{total} tests pass** "
                 f"({', '.join(f'{k} {v}' for k, v in counts.items() if v)}).")
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
    lines.append("- `research/` — notes 00–18, reference only")
    lines.append("")

    lines.append("### Tools")
    lines.append("")
    lines.append("- `sims/explore.py` — recycle refuted claims")
    lines.append("- `sims/shadow.py` — find what nothing measures")
    lines.append("- `sims/ledger_hook.py --check` — verify integrity")
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
