#!/usr/bin/env python3
# run_arms.py -- run every arm's test suites. CC0, stdlib only, no network.
#
# Each arm has its own layout, so nothing here may assume a path: suites are
# found by filename (test_b*.py) and run from their own directory, which is
# what each arm's sys.path bootstrap expects.
#
# Reports PER ARM PER BUILD. It does not total across arms and does not
# compare them: a suite is green or it is not, and two arms both being green
# is not evidence about either one.
#
# usage:  python3 run_arms.py [--arm a] [--json]
# exit:   0 all green, 1 a suite failed, 3 no suites found

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS_DIR = os.path.join(HERE, "arms")
COUNT = re.compile(r"^Ran (\d+) tests?", re.M)


def suites(arm):
    root = os.path.join(ARMS_DIR, arm)
    found = []
    for r, _, fs in os.walk(root):
        for f in sorted(fs):
            if re.fullmatch(r"test_b\d+\.py", f):
                found.append((f[len("test_"):-3], r, f))
    return sorted(found)


def run_one(build, cwd, fname):
    p = subprocess.run([sys.executable, fname], cwd=cwd,
                       capture_output=True, text=True)
    m = COUNT.search(p.stderr) or COUNT.search(p.stdout)
    tail = (p.stderr.strip().splitlines() or ["(no output)"])[-1]
    return {"build": build, "dir": os.path.relpath(cwd, HERE), "file": fname,
            "ran": int(m.group(1)) if m else None,
            "ok": p.returncode == 0, "last_line": tail}


def main(argv):
    args = argv[1:]
    only = args[args.index("--arm") + 1] if "--arm" in args else None
    if not os.path.isdir(ARMS_DIR):
        print("no arms/ directory", file=sys.stderr)
        return 3
    arms = sorted(d for d in os.listdir(ARMS_DIR)
                  if os.path.isdir(os.path.join(ARMS_DIR, d))
                  and (only is None or d == only))
    out = {}
    for a in arms:
        out[a] = [run_one(b, c, f) for b, c, f in suites(a)]
    if not any(out.values()):
        print("no test_b*.py found under arms/", file=sys.stderr)
        return 3
    if "--json" in args:
        print(json.dumps(out, indent=2))
    else:
        for a in arms:
            print("arm %s" % a)
            for r in out[a]:
                n = "?" if r["ran"] is None else r["ran"]
                print("   %-4s %-24s %-4s %s tests   %s"
                      % (r["build"], r["dir"], "OK" if r["ok"] else "FAIL",
                         n, "" if r["ok"] else r["last_line"]))
            print()
        print("Per arm, per build. No total across arms: two arms both green "
              "is not evidence about either one.")
    return 0 if all(r["ok"] for rs in out.values() for r in rs) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
