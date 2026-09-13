"""B3.1 - split-authorship boundary for ROLE KEY.

ROLE CASE writes statements.jsonl (case_id, statement) from the operator's
brief; this script never reads that brief, so nothing from it can reach
ROLE KEY. ROLE KEY's input is built from statements.jsonl alone: one file per
case holding exactly {case_id, statement}. A statements row carrying any
other field is generation context and is rejected. Every written file is
re-read and asserted to hold exactly those two fields.

Command: python3 split.py statements.jsonl outdir/
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

FIELDS = ("case_id", "statement")


def load_statements(path):
    out, seen = [], set()
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        extra = sorted(set(row) - set(FIELDS))
        if extra:
            raise rr.Reject("%s: field %r is not part of a statement (generation "
                            "context refused)" % (where, extra[0]))
        for f in FIELDS:
            if not rr.field(row, f, where, str).strip():
                raise rr.Reject("%s: field %r is empty" % (where, f))
        if row["case_id"] in seen:
            raise rr.Reject("%s: field 'case_id' duplicates an earlier row" % where)
        seen.add(row["case_id"])
        out.append({f: row[f] for f in FIELDS})
    return out


def write_key_inputs(statements, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for s in statements:
        path = os.path.join(outdir, "key_input_%s.json" % s["case_id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"case_id": s["case_id"], "statement": s["statement"]}, f,
                      sort_keys=True, ensure_ascii=False)
        with open(path, encoding="utf-8") as f:
            back = json.load(f)
        if set(back) != set(FIELDS):
            raise rr.Reject("%s: written file carries fields beyond %s" % (path, FIELDS))
        paths.append(path)
    return paths


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="ROLE KEY inputs from statements only")
    p.add_argument("statements")
    p.add_argument("outdir")
    a = p.parse_args(argv)

    def run():
        statements = load_statements(a.statements)
        paths = write_key_inputs(statements, a.outdir)
        return ("ok" if paths else "empty"), {"key_inputs": len(paths)}, ""

    return rr.execute("b3/split.py", vars(a), [a.statements], a.outdir, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
