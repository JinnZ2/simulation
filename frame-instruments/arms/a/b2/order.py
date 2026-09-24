"""B2.2 - counterbalanced condition order per reader.

Readers are filled in blocks of four from a Williams (balanced) Latin square
over A/B/C/D, block row order shuffled by seed. Readers beyond the last full
block get a seeded permutation and the shortfall is written in the run
record notes. The seed is written into every row.

Command: python3 order.py assignment.jsonl --readers N --seed S
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

WILLIAMS = (("A", "B", "D", "C"), ("B", "C", "A", "D"),
            ("C", "D", "B", "A"), ("D", "A", "C", "B"))


def assign(n_readers, seed):
    rng = random.Random(seed)
    rows, shortfall = [], n_readers % len(WILLIAMS)
    for r in range(n_readers):
        if r % len(WILLIAMS) == 0:
            block = list(WILLIAMS)
            rng.shuffle(block)
        if r < n_readers - shortfall:
            order = list(block[r % len(WILLIAMS)])
        else:
            order = list(WILLIAMS[0])
            rng.shuffle(order)
        rows.append({"reader_id": "r%03d" % (r + 1), "order": order, "seed": seed})
    return rows, shortfall


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="counterbalance condition order")
    p.add_argument("output")
    p.add_argument("--readers", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    a = p.parse_args(argv)

    def run():
        if a.readers < 1:
            raise rr.Reject("--readers must be >= 1")
        rows, shortfall = assign(a.readers, a.seed)
        rr.write_jsonl(a.output, rows)
        notes = ("shortfall: %d reader(s) beyond the last full Latin square got a "
                 "seeded permutation" % shortfall) if shortfall else "full Latin square blocks"
        return "ok", {"readers": len(rows), "shortfall": shortfall}, notes

    return rr.execute("b2/order.py", vars(a), [], a.output, a.seed, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
