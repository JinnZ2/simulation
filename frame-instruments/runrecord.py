"""Shared run record for every frame-instruments script. Stdlib only, no network.

Every run of every script appends one object to runs/runs.jsonl:
    run_id, utc, script, args_hash, seed, input_files (name+sha256),
    output_file, status, counts, notes
status is one of ok, void, error, empty. A run that fails, voids, or returns
nothing writes its record by the same code path as a success (execute()).
"""
import datetime
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS_PATH = os.path.join(ROOT, "runs", "runs.jsonl")
STATUSES = ("ok", "void", "error", "empty")
EXIT = {"ok": 0, "empty": 0, "void": 2, "error": 1}
FORBIDDEN_FIELDS = ("label", "category", "type", "interpretation")


class Reject(Exception):
    """Input refused. Maps to status `error`."""


class Void(Exception):
    """The run cannot produce its result. Maps to status `void`."""


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
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


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path):
    """Return [(lineno, obj)]. Blank lines are skipped. Bad JSON -> Reject."""
    if not os.path.exists(path):
        raise Reject("%s: missing" % path)
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
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
            except ValueError as e:
                raise Reject("%s:%d: not JSON (%s)" % (path, n, e))
            if not isinstance(obj, dict):
                raise Reject("%s:%d: row is not an object" % (path, n))
            rows.append((n, obj))
    return rows


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def no_forbidden_fields(obj, where):
    for k in FORBIDDEN_FIELDS:
        if k in obj:
            raise Reject("%s: forbidden field %r" % (where, k))


def field(row, name, where, kinds=None, allow_bool=False):
    """Fetch a required field, checking its type. Missing or wrong -> Reject."""
    if name not in row:
        raise Reject("%s: field %r missing" % (where, name))
    v = row[name]
    if kinds is not None:
        if isinstance(v, bool) and not allow_bool:
            raise Reject("%s: field %r is a bool" % (where, name))
        if not isinstance(v, kinds):
            raise Reject("%s: field %r has wrong type" % (where, name))
    return v


NUMBER = (int, float)


def args_hash(args):
    return sha256_text(json.dumps(args, sort_keys=True, default=str))[:16]


def input_entries(paths):
    out = []
    for p in paths:
        if p is None:
            continue
        p = str(p)
        out.append({"name": os.path.basename(p),
                    "sha256": sha256_file(p) if os.path.isfile(p) else None})
    return out


def record(script, args, seed, inputs, output, status, counts, notes,
           runs_path=None):
    if status not in STATUSES:
        raise ValueError("bad status %r" % status)
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    ah = args_hash(args)
    row = {
        "run_id": sha256_text(utc + script + ah)[:12],
        "utc": utc,
        "script": script,
        "args_hash": ah,
        "seed": seed,
        "input_files": input_entries(inputs),
        "output_file": os.path.basename(str(output)) if output else "",
        "status": status,
        "counts": counts or {},
        "notes": notes or "",
    }
    path = runs_path or RUNS_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return row


def execute(script, args, inputs, output, seed, fn, runs_path=None):
    """Run fn() -> (status, counts, notes); write the record whatever happens.

    Returns the process exit code. Reject -> error, Void -> void, any other
    exception -> error. The record is written on every path.
    """
    counts, notes = {}, ""
    try:
        status, counts, notes = fn()
        if status not in ("ok", "empty"):
            raise ValueError("fn returned status %r" % status)
    except Reject as e:
        status, notes = "error", str(e)
    except Void as e:
        status, notes = "void", str(e)
    except Exception as e:  # noqa: BLE001 - every failure is a row
        status, notes = "error", "%s: %s" % (type(e).__name__, e)
    row = record(script, args, seed, inputs, output, status, counts, notes,
                 runs_path)
    print("%s %s run_id=%s out=%s counts=%s%s" % (
        script, status, row["run_id"], row["output_file"],
        json.dumps(counts, sort_keys=True), (" notes=" + notes) if notes else ""))
    return EXIT[status]
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
