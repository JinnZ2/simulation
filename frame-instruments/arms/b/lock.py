"""B2.3 -- condition D's commit lock as a process boundary.

    python3 lock.py commit  READER CASE response.txt commits.jsonl
    python3 lock.py release READER CASE cases.jsonl commits.jsonl key_out.jsonl

commit appends the reader's A-stage response and its sha256 to
commits.jsonl and exits. It never opens cases.jsonl.

release writes the key for (reader, case) to key_out.jsonl only if a
commit row exists for that pair; otherwise it refuses with status void
and writes its run record. It never writes commits.jsonl.

No invocation holds both a commit and an unlocked key.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conditions import key_text, load_cases  # noqa: E402
from runrecord import SchemaError, main_guard, read_jsonl, sha256_text, utc_now, write_jsonl  # noqa: E402


def commit(reader: str, case: str, response_path, commits_path) -> dict:
    text = Path(response_path).read_text(encoding="utf-8")
    if not text.strip():
        raise SchemaError(f"{Path(response_path).name}: empty response; nothing to commit")
    row = {"reader_id": reader, "case_id": case, "sha256": sha256_text(text),
           "response": text, "utc": utc_now()}
    p = Path(commits_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def committed(reader: str, case: str, commits_path) -> bool:
    if not Path(commits_path).is_file():
        return False
    return any(r.get("reader_id") == reader and r.get("case_id") == case
               for r in read_jsonl(commits_path))


def release(reader: str, case: str, cases_path, commits_path, out_path):
    if not committed(reader, case, commits_path):
        return "void", {}, f"no commit for reader={reader} case={case}; key withheld"
    match = [r for r in load_cases(cases_path) if r["case_id"] == case]
    if not match:
        raise SchemaError(f"{Path(cases_path).name}: no case_id {case!r}")
    write_jsonl(out_path, [{"reader_id": reader, "case_id": case, "condition": "D",
                            "presented_text": key_text(match[0])}])
    return "ok", {"released": 1}, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else ""
    rest = argv[1:]
    if mode == "commit":
        names = ["READER", "CASE", "<in:response.txt>", "<out:commits.jsonl>"]
        return main_guard("lock.commit", rest, names, None,
                          lambda a: ("ok", {"committed": 1}, commit(a[0], a[1], a[2], a[3])["sha256"][:12]))
    if mode == "release":
        names = ["READER", "CASE", "<in:cases.jsonl>", "<in:commits.jsonl>", "<out:key_out.jsonl>"]
        return main_guard("lock.release", rest, names, None,
                          lambda a: release(a[0], a[1], a[2], a[3], a[4]))
    print("[lock] error -- usage: lock.py commit|release ...")
    return 1


if __name__ == "__main__":
    sys.exit(main())
