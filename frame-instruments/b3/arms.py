"""B3.3 - arms. Every row of a cases file carries its arm; a file never mixes.

    single  one instance writes statement and key together (baseline)
    split   two instances, no shared context

Stamps --arm on every row of a cases file. A row already carrying a different
arm means two arms in one file, and the run is rejected.

Command: python3 arms.py cases.jsonl output.jsonl --arm single|split
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

ARMS = ("single", "split")


def check_single_arm(rows, where="rows"):
    arms = {r.get("arm") for r in rows if "arm" in r}
    bad = sorted(a for a in arms if a not in ARMS)
    if bad:
        raise rr.Reject("%s: field 'arm' value %r not in %s" % (where, bad[0], ARMS))
    if len(arms) > 1:
        raise rr.Reject("%s: arms %s mixed in one file" % (where, sorted(arms)))
    return arms.pop() if arms else None


def stamp(rows, arm, where="rows"):
    if arm not in ARMS:
        raise rr.Reject("arm %r not in %s" % (arm, ARMS))
    present = check_single_arm(rows, where)
    if present not in (None, arm):
        raise rr.Reject("%s: rows carry arm %r; refusing to write arm %r into the same "
                        "file" % (where, present, arm))
    return [dict(r, arm=arm) for r in rows]


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="stamp an arm onto a cases file")
    p.add_argument("cases")
    p.add_argument("output")
    p.add_argument("--arm", required=True)
    a = p.parse_args(argv)

    def run():
        rows = [r for _, r in rr.read_jsonl(a.cases)]
        for n, r in enumerate(rows, 1):
            rr.no_forbidden_fields(r, "%s:%d" % (os.path.basename(a.cases), n))
        out = stamp(rows, a.arm, os.path.basename(a.cases))
        rr.write_jsonl(a.output, out)
        return ("ok" if out else "empty"), {"rows": len(out), "arm": a.arm}, ""

    return rr.execute("b3/arms.py", vars(a), [a.cases], a.output, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
