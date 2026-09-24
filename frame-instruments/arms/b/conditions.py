"""B2.1 -- four presentation files from cases.jsonl.

    python3 conditions.py cases.jsonl OUTDIR

Writes OUTDIR/A.jsonl, B.jsonl, C.jsonl, D.jsonl. Every row carries
case_id, condition, presented_text and nothing else. Withheld fields never
appear: A and D carry the statement only, B carries the key only, C both.
D's key is released by lock.py after a committed A-stage response.

A withheld field whose full text occurs inside the presented text (a key
that quotes the whole statement, say) is a leak by construction and is
rejected, not passed through.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

CASE_FIELDS = ("case_id", "statement", "key_posed", "key_target", "key_why")
OPTIONAL = ("arm",)
CONDITIONS = ("A", "B", "C", "D")
KEY_FIELDS = ("key_posed", "key_target", "key_why")


def check_case(row: dict, lineno: int, name: str = "cases.jsonl") -> None:
    where = f"{name} line {lineno}"
    for f in CASE_FIELDS:
        if f not in row:
            raise SchemaError(f"{where}: missing field '{f}'")
        if not isinstance(row[f], str) or not row[f].strip():
            raise SchemaError(f"{where}: field '{f}' must be a non-empty string")
    for f in row:
        if f not in CASE_FIELDS + OPTIONAL:
            raise SchemaError(f"{where}: unexpected field '{f}'")


def load_cases(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    seen = set()
    for n, r in enumerate(rows, 1):
        check_case(r, n, name)
        if r["case_id"] in seen:
            raise SchemaError(f"{name} line {n}: duplicate case_id {r['case_id']!r}")
        seen.add(r["case_id"])
    return rows


def key_text(row: dict) -> str:
    return f"POSED: {row['key_posed']}\nTARGET: {row['key_target']}\nWHY: {row['key_why']}"


def present(row: dict, condition: str) -> str:
    if condition in ("A", "D"):
        return row["statement"]
    if condition == "B":
        return key_text(row)
    if condition == "C":
        return f"STATEMENT: {row['statement']}\n\n{key_text(row)}"
    raise SchemaError(f"unknown condition {condition!r}")


def withheld(condition: str) -> tuple[str, ...]:
    if condition in ("A", "D"):
        return KEY_FIELDS
    if condition == "B":
        return ("statement",)
    return ()


def presentation(rows: list[dict], condition: str) -> list[dict]:
    out = []
    for r in rows:
        text = present(r, condition)
        for f in withheld(condition):
            if r[f].strip() and r[f].strip() in text:
                raise SchemaError(f"case {r['case_id']!r} condition {condition}: withheld field '{f}' would appear in presented_text")
        out.append({"case_id": r["case_id"], "condition": condition, "presented_text": text})
    return out


def _body(args):
    rows = load_cases(args[0])
    outdir = Path(args[1])
    outdir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for c in CONDITIONS:
        counts[c] = write_jsonl(outdir / f"{c}.jsonl", presentation(rows, c))
    return ("empty" if not rows else "ok"), counts, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("conditions", argv, ["<in:cases.jsonl>", "<out:OUTDIR>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
