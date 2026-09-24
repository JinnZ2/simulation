"""B3.1 -- split authorship: two roles that never share context.

    python3 split.py prompts  OUTDIR
    python3 split.py keyinput statements.jsonl OUTDIR

prompts writes ROLE_CASE_PROMPT.txt and ROLE_KEY_PROMPT.txt. The case
role is never told a key will be written.

keyinput builds OUTDIR/role_key_input.jsonl from statements.jsonl alone.
Rows must carry exactly case_id and statement; any other field is
generation context and the input is refused. This is the file boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

STATEMENT_FIELDS = ("case_id", "statement")

ROLE_CASE_PROMPT = """You are writing test statements.

For each case, write one statement: a claim, argument or description as it
might appear in the wild. Output one JSON object per line with exactly two
fields: "case_id" and "statement". Write nothing else about the statement.
"""

ROLE_KEY_PROMPT = """You are writing keys for statements you did not write.

Each input line carries exactly "case_id" and "statement". For each, write
one JSON object per line with exactly four fields:
  "case_id"     copied from the input
  "key_posed"   what the statement poses
  "key_target"  what it is actually aimed at
  "key_why"     why those two differ, or why they coincide
Use only the statement. You have no other context and none will be given.
"""


def load_statements(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    seen = set()
    for n, r in enumerate(rows, 1):
        for f in STATEMENT_FIELDS:
            if f not in r:
                raise SchemaError(f"{name} line {n}: missing field '{f}'")
            if not isinstance(r[f], str) or not r[f].strip():
                raise SchemaError(f"{name} line {n}: field '{f}' must be a non-empty string")
        for f in r:
            if f not in STATEMENT_FIELDS:
                raise SchemaError(f"{name} line {n}: field '{f}' is generation context; refused")
        if r["case_id"] in seen:
            raise SchemaError(f"{name} line {n}: duplicate case_id {r['case_id']!r}")
        seen.add(r["case_id"])
    return rows


def key_input(rows: list[dict]) -> list[dict]:
    return [{"case_id": r["case_id"], "statement": r["statement"]} for r in rows]


def _prompts(args):
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    (out / "ROLE_CASE_PROMPT.txt").write_text(ROLE_CASE_PROMPT, encoding="utf-8")
    (out / "ROLE_KEY_PROMPT.txt").write_text(ROLE_KEY_PROMPT, encoding="utf-8")
    return "ok", {"prompts": 2}, ""


def _keyinput(args):
    rows = load_statements(args[0])
    out = Path(args[1])
    out.mkdir(parents=True, exist_ok=True)
    n = write_jsonl(out / "role_key_input.jsonl", key_input(rows))
    return ("empty" if n == 0 else "ok"), {"statements": n}, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    mode, rest = (argv[0] if argv else ""), argv[1:]
    if mode == "prompts":
        return main_guard("split.prompts", rest, ["<out:OUTDIR>"], None, _prompts)
    if mode == "keyinput":
        return main_guard("split.keyinput", rest, ["<in:statements.jsonl>", "<out:OUTDIR>"], None, _keyinput)
    print("[split] error -- usage: split.py prompts|keyinput ...")
    return 1


if __name__ == "__main__":
    sys.exit(main())
