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
