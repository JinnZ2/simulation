"""B4.1 - items.jsonl validator. One file, one arm.

Row: item_id, source, text_verbatim, branches_stated, arm
  text_verbatim   the item as published; a row needing an edit does not go in
  branches_stated the count of options the item explicitly offers
  arm             hypothetical (stipulated, no incident record) or
                  documented (real incident with a published investigation)
Extra fields, forbidden fields, duplicate ids and mixed arms are rejected.

Command: python3 items.py items.jsonl items_validated.jsonl
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

ARMS = ("hypothetical", "documented")
FIELDS = ("item_id", "source", "text_verbatim", "branches_stated", "arm")


def validate_item(row, where):
    rr.no_forbidden_fields(row, where)
    extra = sorted(set(row) - set(FIELDS))
    if extra:
        raise rr.Reject("%s: field %r is not part of the item schema" % (where, extra[0]))
    for f in ("item_id", "source", "text_verbatim", "arm"):
        rr.field(row, f, where, str)
    if not row["item_id"].strip() or not row["text_verbatim"].strip():
        raise rr.Reject("%s: field 'item_id' or 'text_verbatim' is empty" % where)
    if rr.field(row, "branches_stated", where, int) < 1:
        raise rr.Reject("%s: field 'branches_stated' < 1" % where)
    if row["arm"] not in ARMS:
        raise rr.Reject("%s: field 'arm' not in %s" % (where, ARMS))
    return row


def load_items(path):
    out, seen = [], set()
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        validate_item(row, where)
        if row["item_id"] in seen:
            raise rr.Reject("%s: field 'item_id' duplicates an earlier row" % where)
        seen.add(row["item_id"])
        out.append(row)
    arms = sorted({r["arm"] for r in out})
    if len(arms) > 1:
        raise rr.Reject("%s: field 'arm' mixes %s in one file" % (os.path.basename(path), arms))
    return out


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="validate items.jsonl")
    p.add_argument("items")
    p.add_argument("output")
    a = p.parse_args(argv)

    def run():
        items = load_items(a.items)
        rr.write_jsonl(a.output, items)
        arm = items[0]["arm"] if items else None
        return ("ok" if items else "empty"), {"items": len(items), "arm": arm}, ""

    return rr.execute("b4/items.py", vars(a), [a.items], a.output, None, run, runs_path)
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
