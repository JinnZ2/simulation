"""B3.2 -- join statements and keys into the cases.jsonl B2 consumes.

    python3 join.py statements.jsonl keys.jsonl ARM cases.jsonl

keys.jsonl rows carry exactly case_id, key_posed, key_target, key_why.
Rows are joined on case_id. Nothing is dropped silently: statements with
no key and keys with no statement are counted in the run record and their
ids listed in its notes. Every output row carries ARM (see arms.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arms import ARMS, check  # noqa: E402
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402
from split import load_statements  # noqa: E402

KEY_FIELDS = ("case_id", "key_posed", "key_target", "key_why")


def load_keys(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    seen = set()
    for n, r in enumerate(rows, 1):
        for f in KEY_FIELDS:
            if f not in r:
                raise SchemaError(f"{name} line {n}: missing field '{f}'")
            if not isinstance(r[f], str) or not r[f].strip():
                raise SchemaError(f"{name} line {n}: field '{f}' must be a non-empty string")
        for f in r:
            if f not in KEY_FIELDS:
                raise SchemaError(f"{name} line {n}: unexpected field '{f}'")
        if r["case_id"] in seen:
            raise SchemaError(f"{name} line {n}: duplicate case_id {r['case_id']!r}")
        seen.add(r["case_id"])
    return rows


def join(statements, keys, arm: str):
    if arm not in ARMS:
        raise SchemaError(f"ARM must be one of {ARMS}, got {arm!r}")
    by_key = {k["case_id"]: k for k in keys}
    joined, no_key = [], []
    for s in statements:
        k = by_key.get(s["case_id"])
        if k is None:
            no_key.append(s["case_id"])
            continue
        joined.append({"case_id": s["case_id"], "statement": s["statement"], "key_posed": k["key_posed"],
                       "key_target": k["key_target"], "key_why": k["key_why"], "arm": arm})
    have = {s["case_id"] for s in statements}
    no_statement = [k["case_id"] for k in keys if k["case_id"] not in have]
    return joined, no_key, no_statement


def _body(args):
    statements, keys, arm = load_statements(args[0]), load_keys(args[1]), args[2]
    joined, no_key, no_statement = join(statements, keys, arm)
    check(joined)
    n = write_jsonl(args[3], joined)
    counts = {"joined": n, "statements_unmatched": len(no_key), "keys_unmatched": len(no_statement)}
    notes = f"arm={arm}"
    if no_key:
        notes += f"; statements without key: {','.join(no_key[:10])}"
    if no_statement:
        notes += f"; keys without statement: {','.join(no_statement[:10])}"
    return ("empty" if n == 0 else "ok"), counts, notes


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:statements.jsonl>", "<in:keys.jsonl>", "ARM", "<out:cases.jsonl>"]
    return main_guard("join", argv, names, None, _body)


if __name__ == "__main__":
    sys.exit(main())
