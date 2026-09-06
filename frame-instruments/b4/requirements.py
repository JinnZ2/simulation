"""B4.3 - requirements.jsonl validator (one row per requirement returned).

Row: item_id, reconstructor_id, req_id, requirement_text, status,
     settling_test, layer
  status         true | false | lapsed | partial | unknown | undifferentiated
  settling_test  required, non-empty: condition, test, status
  layer          free text, a location, never validated against a list
req_id is unique across the file (matches.jsonl refers to it alone).
A file using only true/false across all rows is void: the grading was not
run. No label, category, or interpretation field.

Command: python3 requirements.py requirements.jsonl requirements_validated.jsonl
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

STATUSES = ("true", "false", "lapsed", "partial", "unknown", "undifferentiated")
FIELDS = ("item_id", "reconstructor_id", "req_id", "requirement_text", "status",
          "settling_test", "layer")
OPTIONAL = ("seed",)


def validate_requirement(row, where):
    rr.no_forbidden_fields(row, where)
    extra = sorted(set(row) - set(FIELDS) - set(OPTIONAL))
    if extra:
        raise rr.Reject("%s: field %r is not part of the requirement schema" % (where, extra[0]))
    for f in FIELDS:
        rr.field(row, f, where, str)
    for f in ("item_id", "reconstructor_id", "req_id", "requirement_text"):
        if not row[f].strip():
            raise rr.Reject("%s: field %r is empty" % (where, f))
    if not row["settling_test"].strip():
        raise rr.Reject("%s: field 'settling_test' is empty; a status with no test is "
                        "refused" % where)
    if row["status"] not in STATUSES:
        raise rr.Reject("%s: field 'status' not in %s" % (where, STATUSES))
    return row


def two_state(rows):
    return bool(rows) and {r["status"] for r in rows} <= {"true", "false"}


def load_requirements(path):
    out, seen = [], set()
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        validate_requirement(row, where)
        if row["req_id"] in seen:
            raise rr.Reject("%s: field 'req_id' duplicates an earlier row" % where)
        seen.add(row["req_id"])
        out.append(row)
    if two_state(out):
        raise rr.Void("%s: only true/false across all %d rows; the five-state grading "
                      "was not run" % (os.path.basename(path), len(out)))
    return out


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="validate requirements.jsonl")
    p.add_argument("requirements")
    p.add_argument("output")
    a = p.parse_args(argv)

    def run():
        rows = load_requirements(a.requirements)
        rr.write_jsonl(a.output, rows)
        counts = {"rows": len(rows), "items": len({r["item_id"] for r in rows}),
                  "reconstructors": len({r["reconstructor_id"] for r in rows})}
        return ("ok" if rows else "empty"), counts, ""

    return rr.execute("b4/requirements.py", vars(a), [a.requirements], a.output, None,
                      run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
