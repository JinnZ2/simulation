"""B3.3 -- the two arms, declared once. A file carries one arm or none.

    python3 arms.py cases.jsonl

single  one instance writes statement and key together (baseline)
split   two instances, no shared context

check() is imported by join.py; the command line validates an existing
file. Mixed arms in one file are refused, not reconciled.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl  # noqa: E402

ARMS = ("single", "split")


def check(rows: list[dict], name: str = "cases.jsonl") -> str | None:
    """Return the file's single arm, or raise. Empty input returns None."""
    seen = set()
    for n, r in enumerate(rows, 1):
        if "arm" not in r:
            raise SchemaError(f"{name} line {n}: missing field 'arm'")
        if r["arm"] not in ARMS:
            raise SchemaError(f"{name} line {n}: field 'arm' must be one of {ARMS}")
        seen.add(r["arm"])
        if len(seen) > 1:
            raise SchemaError(f"{name} line {n}: arms {sorted(seen)} mixed in one file")
    return next(iter(seen)) if seen else None


def _body(args):
    rows = read_jsonl(args[0])
    arm = check(rows, Path(args[0]).name)
    return ("empty" if not rows else "ok"), {"rows": len(rows)}, f"arm={arm}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("arms", argv, ["<in:cases.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
