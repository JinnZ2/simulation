"""B1.1 -- validators for base.jsonl and traces.jsonl.

    python3 schema.py base.jsonl traces.jsonl

Strict: every listed field required, no extra fields, no coercion. A bad
row is rejected with its file, line number and field name.

Token convention (stated so a producer does not guess): continuation[0] is
the first token generated AFTER forced_token; base_continuation[0] is the
base token at position i+1. The two lists have equal length.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl  # noqa: E402

MAX_CONTINUATION = 128
ENTROPY_BASES = ("full", "topk")

BASE_FIELDS = ("case_id", "model_id", "i", "token_taken", "logprob_taken",
               "topk", "entropy_i", "entropy_basis")
TRACE_FIELDS = ("case_id", "model_id", "i", "branch_rank", "forced_token",
                "continuation", "base_continuation")


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _fields(row, required, where):
    missing = [f for f in required if f not in row]
    if missing:
        raise SchemaError(f"{where}: missing field '{missing[0]}'")
    extra = [f for f in row if f not in required]
    if extra:
        raise SchemaError(f"{where}: unexpected field '{extra[0]}'")


def _str(row, f, where):
    if not isinstance(row[f], str) or not row[f]:
        raise SchemaError(f"{where}: field '{f}' must be a non-empty string")


def _tokens(row, f, where):
    v = row[f]
    if not isinstance(v, list) or not all(isinstance(t, str) for t in v):
        raise SchemaError(f"{where}: field '{f}' must be a list of strings")
    if len(v) > MAX_CONTINUATION:
        raise SchemaError(f"{where}: field '{f}' longer than {MAX_CONTINUATION}")


def check_base_row(row: dict, lineno: int, name: str = "base.jsonl") -> None:
    where = f"{name} line {lineno}"
    _fields(row, BASE_FIELDS, where)
    _str(row, "case_id", where)
    _str(row, "model_id", where)
    _str(row, "token_taken", where)
    if not _is_int(row["i"]) or row["i"] < 0:
        raise SchemaError(f"{where}: field 'i' must be a non-negative integer")
    for f in ("logprob_taken", "entropy_i"):
        if not _is_num(row[f]):
            raise SchemaError(f"{where}: field '{f}' must be a number")
    if row["entropy_basis"] not in ENTROPY_BASES:
        raise SchemaError(f"{where}: field 'entropy_basis' must be one of {ENTROPY_BASES}")
    topk = row["topk"]
    if not isinstance(topk, list) or not topk:
        raise SchemaError(f"{where}: field 'topk' must be a non-empty list")
    for j, pair in enumerate(topk):
        ok = (isinstance(pair, list) and len(pair) == 2
              and isinstance(pair[0], str) and _is_num(pair[1]))
        if not ok:
            raise SchemaError(f"{where}: field 'topk[{j}]' must be [token, logprob]")


def check_trace_row(row: dict, lineno: int, name: str = "traces.jsonl") -> None:
    where = f"{name} line {lineno}"
    _fields(row, TRACE_FIELDS, where)
    _str(row, "case_id", where)
    _str(row, "model_id", where)
    _str(row, "forced_token", where)
    if not _is_int(row["i"]) or row["i"] < 0:
        raise SchemaError(f"{where}: field 'i' must be a non-negative integer")
    if not _is_int(row["branch_rank"]) or row["branch_rank"] < 2:
        raise SchemaError(f"{where}: field 'branch_rank' must be an integer >= 2")
    _tokens(row, "continuation", where)
    _tokens(row, "base_continuation", where)
    if len(row["continuation"]) != len(row["base_continuation"]):
        raise SchemaError(f"{where}: field 'base_continuation' length differs from 'continuation'")


def load_base(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    for n, row in enumerate(rows, 1):
        check_base_row(row, n, name)
    return rows


def load_traces(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    for n, row in enumerate(rows, 1):
        check_trace_row(row, n, name)
    return rows


def _body(args):
    base = load_base(args[0])
    traces = load_traces(args[1])
    counts = {"base_rows": len(base), "trace_rows": len(traces)}
    status = "empty" if not base or not traces else "ok"
    return status, counts, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("schema", argv, ["<in:base.jsonl>", "<in:traces.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
