"""B3.2 - join statements.jsonl and keys.jsonl into the cases.jsonl B2 reads.

keys.jsonl: case_id, key_posed, key_target, key_why (ROLE KEY's output).
Rows on one side with no partner are dropped, counted, and listed in the
run record. Every output row carries --arm (default split; arms.py refuses
a mix).

Command: python3 join.py statements.jsonl keys.jsonl cases.jsonl [--arm split]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import arms  # noqa: E402
import split  # noqa: E402

KEY_FIELDS = ("key_posed", "key_target", "key_why")


def load_keys(path):
    out = {}
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        rr.no_forbidden_fields(row, where)
        rr.field(row, "case_id", where, str)
        for f in KEY_FIELDS:
            rr.field(row, f, where, str)
        if row["case_id"] in out:
            raise rr.Reject("%s: field 'case_id' duplicates an earlier row" % where)
        out[row["case_id"]] = row
    return out


def join(statements, keys, arm):
    rows, no_key, no_statement = [], [], sorted(set(keys) - {s["case_id"] for s in statements})
    for s in statements:
        k = keys.get(s["case_id"])
        if k is None:
            no_key.append(s["case_id"])
            continue
        row = {"case_id": s["case_id"], "statement": s["statement"]}
        row.update({f: k[f] for f in KEY_FIELDS})
        rows.append(row)
    return arms.stamp(rows, arm), no_key, no_statement


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="join statements and keys into cases")
    p.add_argument("statements")
    p.add_argument("keys")
    p.add_argument("output")
    p.add_argument("--arm", default="split")
    a = p.parse_args(argv)

    def run():
        rows, no_key, no_statement = join(split.load_statements(a.statements),
                                          load_keys(a.keys), a.arm)
        rr.write_jsonl(a.output, rows)
        counts = {"joined": len(rows), "dropped_statements_without_key": len(no_key),
                  "dropped_keys_without_statement": len(no_statement), "arm": a.arm}
        notes = "; ".join(x for x in (
            "no key for %s" % no_key if no_key else "",
            "no statement for %s" % no_statement if no_statement else "") if x)
        return ("ok" if rows else "empty"), counts, notes

    return rr.execute("b3/join.py", vars(a), [a.statements, a.keys], a.output, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
