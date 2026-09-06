"""B4.6 - null: reassign each reconstructor's requirement lists to the WRONG
items. Per reconstructor, the items they covered are rotated by a seeded
offset in 1..n-1, so no list stays on its own item and every item still
receives one list per reconstructor. Row count and every other field are
preserved; the seed is written into every row. A reconstructor with a
single item cannot be moved and is named in the run record.

Command: python3 nullshuffle.py requirements.jsonl requirements_shuffled.jsonl --seed N
"""
import argparse
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import requirements as req_mod  # noqa: E402


def shuffle(rows, seed):
    rng = random.Random(seed)
    items_of = defaultdict(set)
    for r in rows:
        items_of[r["reconstructor_id"]].add(r["item_id"])
    mapping, unshuffled = {}, []
    for rid in sorted(items_of):
        items = sorted(items_of[rid])
        n = len(items)
        if n < 2:
            unshuffled.append(rid)
            k = 0
        else:
            k = rng.randrange(1, n)
        for j, item in enumerate(items):
            mapping[(rid, item)] = items[(j + k) % n]
    out = [dict(r, item_id=mapping[(r["reconstructor_id"], r["item_id"])], seed=seed)
           for r in rows]
    return out, unshuffled


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="reassign requirement lists to wrong items")
    p.add_argument("requirements")
    p.add_argument("output")
    p.add_argument("--seed", type=int, required=True)
    a = p.parse_args(argv)

    def run():
        rows = req_mod.load_requirements(a.requirements)
        out, unshuffled = shuffle(rows, a.seed)
        rr.write_jsonl(a.output, out)
        moved = sum(1 for x, y in zip(rows, out) if x["item_id"] != y["item_id"])
        notes = ("single-item reconstructors left in place: %s" % unshuffled) if unshuffled else ""
        return ("ok" if out else "empty"), {"rows": len(out), "moved": moved}, notes

    return rr.execute("b4/nullshuffle.py", vars(a), [a.requirements], a.output, a.seed,
                      run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
