"""B2.1 - four presentation files from cases.jsonl.

cases.jsonl: case_id, statement, key_posed, key_target, key_why (arm optional,
never carried). Each output row carries case_id, condition, presented_text ONLY.
    A  statement only
    B  key only (posed + target + why), no statement
    C  both, simultaneous
    D  statement only; the key is released by lock.py after a locked commit
A withheld field whose text appears inside presented_text is a leak and the
run is rejected.

Command: python3 conditions.py cases.jsonl outdir/
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

CONDITIONS = ("A", "B", "C", "D")
KEY_FIELDS = ("key_posed", "key_target", "key_why")
FIELDS = ("case_id", "statement") + KEY_FIELDS


def load_cases(path):
    out, seen = [], set()
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        rr.no_forbidden_fields(row, where)
        for f in FIELDS:
            rr.field(row, f, where, str)
        if row["case_id"] in seen:
            raise rr.Reject("%s: field 'case_id' duplicates an earlier row" % where)
        seen.add(row["case_id"])
        out.append(row)
    return out


def key_text(case):
    return "posed: %s\ntarget: %s\nwhy: %s" % tuple(case[f] for f in KEY_FIELDS)


def withheld(case, condition):
    if condition in ("A", "D"):
        return [case[f] for f in KEY_FIELDS]
    if condition == "B":
        return [case["statement"]]
    return []


def present(case, condition):
    if condition in ("A", "D"):
        text = case["statement"]
    elif condition == "B":
        text = key_text(case)
    else:
        text = case["statement"] + "\n\n" + key_text(case)
    row = {"case_id": case["case_id"], "condition": condition, "presented_text": text}
    assert_no_leak(row, withheld(case, condition))
    return row


def assert_no_leak(row, withheld_values):
    if set(row) != {"case_id", "condition", "presented_text"}:
        raise rr.Reject("case %s: row carries fields beyond the three allowed"
                        % row.get("case_id"))
    for v in withheld_values:
        if v.strip() and v.strip() in row["presented_text"]:
            raise rr.Reject("case %s condition %s: withheld text present in "
                            "presented_text" % (row["case_id"], row["condition"]))


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="emit A/B/C/D presentation files")
    p.add_argument("cases")
    p.add_argument("outdir")
    a = p.parse_args(argv)

    def run():
        cases = load_cases(a.cases)
        os.makedirs(a.outdir, exist_ok=True)
        for c in CONDITIONS:
            rows = [present(case, c) for case in cases]
            for row, case in zip(rows, cases):
                assert_no_leak(row, withheld(case, c))
            rr.write_jsonl(os.path.join(a.outdir, c + ".jsonl"), rows)
        return ("ok" if cases else "empty"), {"cases": len(cases), "files": len(CONDITIONS)}, ""

    return rr.execute("b2/conditions.py", vars(a), [a.cases], a.outdir, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
