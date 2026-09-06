"""B4.1 -- validate items.jsonl. One arm per file.

    python3 items.py items.jsonl

Rows carry exactly: item_id, source, text_verbatim, branches_stated, arm.
text_verbatim is the item as published. Nothing here rewrites it; an
item that needs an edit to fit the schema does not go in. arm is
"hypothetical" or "documented" and a file mixing the two is refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runrecord import SchemaError, main_guard, read_jsonl  # noqa: E402

FIELDS = ("item_id", "source", "text_verbatim", "branches_stated", "arm")
ARMS = ("hypothetical", "documented")


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check_item(row: dict, lineno: int, name: str = "items.jsonl") -> None:
    where = f"{name} line {lineno}"
    for f in FIELDS:
        if f not in row:
            raise SchemaError(f"{where}: missing field '{f}'")
    for f in row:
        if f not in FIELDS:
            raise SchemaError(f"{where}: unexpected field '{f}'")
    for f in ("item_id", "source", "text_verbatim"):
        if not isinstance(row[f], str) or not row[f].strip():
            raise SchemaError(f"{where}: field '{f}' must be a non-empty string")
    if not _is_int(row["branches_stated"]) or row["branches_stated"] < 1:
        raise SchemaError(f"{where}: field 'branches_stated' must be an integer >= 1")
    if row["arm"] not in ARMS:
        raise SchemaError(f"{where}: field 'arm' must be one of {ARMS}")


def load_items(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    seen, arms = set(), set()
    for n, r in enumerate(rows, 1):
        check_item(r, n, name)
        if r["item_id"] in seen:
            raise SchemaError(f"{name} line {n}: duplicate item_id {r['item_id']!r}")
        seen.add(r["item_id"])
        arms.add(r["arm"])
        if len(arms) > 1:
            raise SchemaError(f"{name} line {n}: arms {sorted(arms)} mixed in one file")
    return rows


def _body(args):
    rows = load_items(args[0])
    arm = rows[0]["arm"] if rows else None
    return ("empty" if not rows else "ok"), {"items": len(rows)}, f"arm={arm}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("b4.items", argv, ["<in:items.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
