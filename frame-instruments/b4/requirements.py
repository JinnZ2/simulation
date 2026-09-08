"""B4.3 -- validate requirements.jsonl, the reconstructors' return.

    python3 requirements.py requirements.jsonl

Rows carry exactly: item_id, reconstructor_id, req_id, requirement_text,
status, settling_test, layer.

status is graded, not binary: true, false, lapsed, partial, unknown,
undifferentiated. "undifferentiated" means no instrument yet
distinguishes the candidate readings; it is not "false" and nothing here
collapses it. A file whose rows use only true/false is refused with
status void: a two-state return means the grading was not run.

settling_test is required and non-empty. A status with no test attached
is rejected. layer is free text naming where the requirement sits; it is
collected and counted downstream, never validated against a list.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runrecord import SchemaError, main_guard, read_jsonl  # noqa: E402

FIELDS = ("item_id", "reconstructor_id", "req_id", "requirement_text",
          "status", "settling_test", "layer")
STATUSES = ("true", "false", "lapsed", "partial", "unknown", "undifferentiated")
BINARY = {"true", "false"}


def check_requirement(row: dict, lineno: int, name: str = "requirements.jsonl") -> None:
    where = f"{name} line {lineno}"
    for f in FIELDS:
        if f not in row:
            raise SchemaError(f"{where}: missing field '{f}'")
    for f in row:
        if f not in FIELDS:
            raise SchemaError(f"{where}: unexpected field '{f}'")
    for f in FIELDS:
        if not isinstance(row[f], str):
            raise SchemaError(f"{where}: field '{f}' must be a string")
    for f in ("item_id", "reconstructor_id", "req_id", "requirement_text", "layer"):
        if not row[f].strip():
            raise SchemaError(f"{where}: field '{f}' must be non-empty")
    if not row["settling_test"].strip():
        raise SchemaError(f"{where}: field 'settling_test' is empty; a status with no test attached is rejected")
    if row["status"] not in STATUSES:
        raise SchemaError(f"{where}: field 'status' must be one of {STATUSES}")


def two_state(rows: list[dict]) -> bool:
    return bool(rows) and {r["status"] for r in rows} <= BINARY


def load_requirements(path) -> list[dict]:
    """Schema-valid rows. Does not apply the two-state rule; callers that
    need it use two_state()."""
    rows = read_jsonl(path)
    name = Path(path).name
    seen = set()
    for n, r in enumerate(rows, 1):
        check_requirement(r, n, name)
        key = (r["item_id"], r["reconstructor_id"], r["req_id"])
        if key in seen:
            raise SchemaError(f"{name} line {n}: duplicate req_id {r['req_id']!r} for this item and reconstructor")
        seen.add(key)
    return rows


def _body(args):
    rows = load_requirements(args[0])
    counts = {"rows": len(rows), "items": len({r["item_id"] for r in rows}),
              "reconstructors": len({r["reconstructor_id"] for r in rows}),
              "statuses_used": len({r["status"] for r in rows})}
    if not rows:
        return "empty", counts, ""
    if two_state(rows):
        return "void", counts, "only true/false used across all rows; the five-state grading was not run"
    return "ok", counts, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("b4.requirements", argv, ["<in:requirements.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
