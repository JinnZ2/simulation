"""B4.6 - null: reassign each reconstructor's requirement lists to the WRONG
items. Per reconstructor, the items they covered are rotated by a seeded
offset in 1..n-1, so no list stays on its own item and every item still
receives one list per reconstructor. Offsets are drawn against the
reconstructors already placed so that lists which shared an item land on
different items wherever the item count allows (at most n-1 reconstructors
can be pairwise separated over n items); the pairs that still land together
(co_moved_pairs) are written to the run record. Row count and every other field are preserved; the seed is written
into every row. A reconstructor with a single item cannot be moved and is
named in the run record.

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

def rotation(items, k):
    return {item: items[(j + k) % len(items)] for j, item in enumerate(items)}


def co_moved(candidate, placed):
    """Pairs (other reconstructor, item) where both lists land on one item again."""
    return sum(1 for m in placed for item, dest in candidate.items()
               if item in m and m[item] == dest)


def shuffle(rows, seed):
    rng = random.Random(seed)
    items_of = defaultdict(set)
    for r in rows:
        items_of[r["reconstructor_id"]].add(r["item_id"])
    mapping, placed, unshuffled, together = {}, [], [], 0
    for rid in sorted(items_of):
        items = sorted(items_of[rid])
        n = len(items)
        if n < 2:
            unshuffled.append(rid)
            best = rotation(items, 0)
        else:
            offsets = list(range(1, n))
            rng.shuffle(offsets)
            best, best_cost = None, None
            for k in offsets:
                cand = rotation(items, k)
                cost = co_moved(cand, placed)
                if best is None or cost < best_cost:
                    best, best_cost = cand, cost
                if cost == 0:
                    break
            together += best_cost
        placed.append(best)
        for item, dest in best.items():
            mapping[(rid, item)] = dest
    out = [dict(r, item_id=mapping[(r["reconstructor_id"], r["item_id"])], seed=seed)
           for r in rows]
    return out, unshuffled, together


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="reassign requirement lists to wrong items")
    p.add_argument("requirements")
    p.add_argument("output")
    p.add_argument("--seed", type=int, required=True)
    a = p.parse_args(argv)

    def run():
        rows = req_mod.load_requirements(a.requirements)
        out, unshuffled, together = shuffle(rows, a.seed)
        rr.write_jsonl(a.output, out)
        moved = sum(1 for x, y in zip(rows, out) if x["item_id"] != y["item_id"])
        notes = "; ".join(x for x in (
            ("single-item reconstructors left in place: %s" % unshuffled) if unshuffled else "",
            ("co_moved_pairs: %d list pairs that shared an item landed together again"
             % together) if together else "") if x)
        return ("ok" if out else "empty"), {"rows": len(out), "moved": moved,
                                            "co_moved_pairs": together}, notes

    return rr.execute("b4/nullshuffle.py", vars(a), [a.requirements], a.output, a.seed,
                      run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
