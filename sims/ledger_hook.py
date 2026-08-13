#!/usr/bin/env python3
"""Append per-run ledger entries to the central ledger (HARNESS.md §1).

    python3 ledger_hook.py              # scan sims/*/results/*/ and append new entries
    python3 ledger_hook.py --check      # verify the ledger against results, change nothing
    python3 ledger_hook.py --show       # print the ledger as a table

Idempotent: an entry already in the ledger (matched on metrics_hash) is skipped, so
rerunning after a new sim run appends only what is new.

The ledger is append-only by construction. Entries are never rewritten — a rerun of a
sim produces a new results directory, a new metrics hash, and a new line. The history
of a claim is the sequence of its entries.

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger.jsonl"


def discover_entries() -> list[dict[str, Any]]:
    """Every ledger_entry.jsonl under sims/<name>/results/<stamp>/."""
    entries = []
    for path in sorted(ROOT.glob("*/results/*/ledger_entry.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                entry["_source"] = str(path.relative_to(ROOT))
                entries.append(entry)
    return entries


def read_ledger() -> list[dict[str, Any]]:
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def verify_hashes(entries: list[dict[str, Any]]) -> list[str]:
    """Re-hash each metrics.json and compare against what the entry recorded."""
    import hashlib
    problems = []
    for entry in entries:
        source = entry.get("_source")
        if not source:
            continue
        metrics = ROOT / Path(source).parent / "metrics.json"
        if not metrics.exists():
            problems.append(f"{source}: metrics.json missing")
            continue
        actual = hashlib.sha256(metrics.read_bytes()).hexdigest()
        if actual != entry["metrics_hash"]:
            problems.append(
                f"{source}: metrics_hash mismatch — recorded {entry['metrics_hash'][:12]}, "
                f"actual {actual[:12]} (metrics.json was edited after the run)")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Central ledger hook.")
    parser.add_argument("--check", action="store_true",
                        help="verify hashes and report unappended runs; write nothing")
    parser.add_argument("--show", action="store_true", help="print the ledger as a table")
    args = parser.parse_args(argv)

    found = discover_entries()
    existing = read_ledger()
    known = {entry["metrics_hash"] for entry in existing}
    new = [entry for entry in found if entry["metrics_hash"] not in known]

    if args.show:
        rows = existing or found
        if not rows:
            print("ledger is empty")
            return 0
        width = max(len(r["name"]) for r in rows)
        print(f"{'name'.ljust(width)}  {'verdict':<13} {'type':<12} seeds  run_at")
        for r in rows:
            pilot = " PILOT" if r.get("pilot") else ""
            print(f"{r['name'].ljust(width)}  {r['verdict']:<13} {r['type']:<12} "
                  f"{r['seeds']:<6} {r['run_at']}{pilot}")
        return 0

    problems = verify_hashes(found)
    for problem in problems:
        print(f"TAMPER: {problem}", file=sys.stderr)

    if args.check:
        print(f"{len(found)} run(s) on disk, {len(existing)} in ledger, "
              f"{len(new)} unappended, {len(problems)} hash problem(s)")
        return 1 if problems else 0

    if problems:
        print("refusing to append while hashes disagree", file=sys.stderr)
        return 1

    if not new:
        print(f"ledger up to date ({len(existing)} entries)")
        return 0

    with LEDGER.open("a", encoding="utf-8") as handle:
        for entry in new:
            handle.write(json.dumps({k: v for k, v in entry.items()
                                     if k != "_source"}, sort_keys=True) + "\n")
    print(f"appended {len(new)} entr{'y' if len(new) == 1 else 'ies'} to {LEDGER.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
