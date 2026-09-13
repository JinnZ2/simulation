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
"""B4.6 -- the null: requirement lists reassigned to the WRONG items.

    python3 nullshuffle.py requirements.jsonl SEED requirements_shuffled.jsonl

Each reconstructor's item-to-item map is a seeded derangement drawn
independently, so on any item the lists being compared came from
different original items. Row count, reconstructor ids, req ids, texts,
statuses, tests and layers are preserved; only item_id moves. Fewer than
two items cannot be deranged and exits void.

Matching is external, so the shuffled file needs its own matches.jsonl
before agreement.py runs on it. grade.py runs on it unchanged.

If agreement survives this, reconstructors are producing boilerplate
rather than item-specific reconstruction. That is a finding about the
protocol, filed beside the real result, never a reason to hide it.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from requirements import load_requirements  # noqa: E402
from runrecord import main_guard, write_jsonl  # noqa: E402


def derangement(items: list[str], rng: random.Random) -> dict[str, str]:
    """A permutation with no fixed point. Rejection sampling, then a
    rotation as the deterministic fallback."""
    for _ in range(200):
        perm = list(items)
        rng.shuffle(perm)
        if all(a != b for a, b in zip(items, perm)):
            return dict(zip(items, perm))
    k = rng.randrange(1, len(items))
    return {a: items[(i + k) % len(items)] for i, a in enumerate(items)}


def shuffle(rows: list[dict], seed: int) -> list[dict]:
    items = sorted({r["item_id"] for r in rows})
    if len(items) < 2:
        return []
    rng = random.Random(seed)
    maps = {rid: derangement(items, rng) for rid in sorted({r["reconstructor_id"] for r in rows})}
    out = []
    for r in rows:  # input order preserved; only item_id moves
        moved = dict(r)
        moved["item_id"] = maps[r["reconstructor_id"]][r["item_id"]]
        out.append(moved)
    return out


def _body(args):
    rows = load_requirements(args[0])
    seed = int(args[1])
    items = {r["item_id"] for r in rows}
    if len(items) < 2:
        return "void", {"rows": len(rows), "items": len(items)}, "fewer than two items; nothing to derange"
    out = shuffle(rows, seed)
    write_jsonl(args[2], out)
    return "ok", {"rows": len(out), "items": len(items), "reconstructors": len({r["reconstructor_id"] for r in rows})}, f"seed={seed}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("b4.nullshuffle", argv, ["<in:requirements.jsonl>", "SEED", "<out:requirements_shuffled.jsonl>"], 1, _body)


if __name__ == "__main__":
    sys.exit(main())
