"""Shared run record. Every script in this folder appends one row to
runs.jsonl per invocation, on every path: ok, void, error, empty.

A failed run is a first-class row. It is written by the same code path as
a success, in the same shape, so failures stay comparable across attempts.

runs.jsonl lives beside the script's declared output (or beside its first
input when the script writes nothing). Nothing else is written anywhere.

Stdlib only. No network.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

STATUSES = ("ok", "void", "error", "empty")
EXIT_CODE = {"ok": 0, "empty": 0, "void": 2, "error": 1}


class SchemaError(ValueError):
    """Input rejected. The message names the file, line and field."""


def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def args_hash(args) -> str:
    return sha256_text(json.dumps([str(a) for a in args]))


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_jsonl(path, name: str | None = None) -> list[dict]:
    """One JSON object per non-blank line. Bad JSON or a non-object is a
    SchemaError naming the line."""
    name = name or Path(path).name
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SchemaError(f"{name} line {lineno}: invalid JSON ({exc.msg})") from None
            if not isinstance(obj, dict):
                raise SchemaError(f"{name} line {lineno}: row is not an object")
            rows.append(obj)
    return rows


def write_jsonl(path, rows) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            n += 1
    return n


def runs_path_for(output_file, fallback) -> Path:
    anchor = Path(output_file) if output_file else Path(fallback)
    base = anchor if anchor.is_dir() else anchor.parent
    return base / "runs.jsonl"


def write_record(runs_path, *, script, args, seed, input_files, output_file,
                 status, counts, notes) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")
    stamp = utc_now()
    ahash = args_hash(args)
    rec = {
        "run_id": f"{script}-{stamp}-{ahash[:8]}",
        "utc": stamp,
        "script": script,
        "args_hash": ahash,
        "seed": seed,
        "input_files": [{"name": Path(f).name, "sha256": sha256_file(f)} for f in input_files],
        "output_file": str(output_file) if output_file else None,
        "status": status,
        "counts": dict(counts or {}),
        "notes": notes or "",
    }
    p = Path(runs_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def run(script, args, seed, input_files, output_file, body) -> int:
    """Run body() -> (status, counts, notes) under the record discipline.

    Any exception becomes a status "error" row with the message in notes.
    One summary line goes to stdout. The return value is the exit code.
    """
    fallback = input_files[0] if input_files else "."
    runs_path = runs_path_for(output_file, fallback)
    try:
        status, counts, notes = body()
    except SchemaError as exc:
        status, counts, notes = "error", {}, str(exc)
    except Exception as exc:  # noqa: BLE001 - every failure is a row
        status, counts, notes = "error", {}, f"{type(exc).__name__}: {exc}"
    rec = write_record(runs_path, script=script, args=args, seed=seed,
                       input_files=input_files, output_file=output_file,
                       status=status, counts=counts, notes=notes)
    summary = " ".join(f"{k}={v}" for k, v in rec["counts"].items())
    tail = f" {summary}" if summary else ""
    note = f" -- {rec['notes']}" if rec["notes"] else ""
    print(f"[{script}] {status}{tail}{note}")
    return EXIT_CODE[status]


def positional(argv, names) -> list[str]:
    """Exactly len(names) positional arguments or a usage SchemaError."""
    if len(argv) != len(names):
        raise SchemaError("usage: " + " ".join(names))
    return list(argv)


def main_guard(script, argv, names, seed_index, body_factory) -> int:
    """Parse positionals, then run() with input/output taken from names.

    names entries starting with '<in:' are inputs, '<out:' the output; the
    seed, if any, sits at seed_index.
    """
    try:
        args = positional(argv, names)
    except SchemaError as exc:
        print(f"[{script}] error -- {exc}")
        return EXIT_CODE["error"]
    inputs = [a for a, n in zip(args, names) if n.startswith("<in:")]
    outs = [a for a, n in zip(args, names) if n.startswith("<out:")]
    seed = int(args[seed_index]) if seed_index is not None else None
    return run(script, args, seed, inputs, outs[0] if outs else None,
               lambda: body_factory(args))


if __name__ == "__main__":
    print("runrecord.py is a module; import it.", file=sys.stderr)
    sys.exit(1)
