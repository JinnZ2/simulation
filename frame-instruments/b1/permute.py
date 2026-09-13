"""B1.3 - permutation null. Shuffles which position index carries which
(ent_i, gap_i, resync_D, div_D) tuple, within each (case_id, model_id,
branch_rank, D, L) stratum, so every other field is preserved. The seed is
written into every output row.

Command: python3 permute.py separations.jsonl separations_permuted.jsonl --seed N
"""
import argparse
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

TUPLE = ("ent_i", "gap_i", "resync_D", "div_D")
STRATUM = ("case_id", "model_id", "branch_rank", "D", "L")


def permute(rows, seed):
    rng = random.Random(seed)
    strata = defaultdict(list)
    for idx, r in enumerate(rows):
        strata[tuple(r[k] for k in STRATUM)].append(idx)
    out = [dict(r, seed=seed) for r in rows]
    for key in sorted(strata, key=repr):
        idxs = strata[key]
        tuples = [tuple(rows[k][f] for f in TUPLE) for k in idxs]
        rng.shuffle(tuples)
        for k, t in zip(idxs, tuples):
            for f, v in zip(TUPLE, t):
                out[k][f] = v
    return out


def load(path):
    rows = []
    for n, r in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        for f in STRATUM + TUPLE + ("i",):
            rr.field(r, f, where)
        rows.append(r)
    return rows


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="permutation null for separations")
    p.add_argument("separations")
    p.add_argument("output")
    p.add_argument("--seed", type=int, required=True)
    a = p.parse_args(argv)

    def run():
        rows = load(a.separations)
        out = permute(rows, a.seed)
        rr.write_jsonl(a.output, out)
        return ("ok" if out else "empty"), {"rows": len(out)}, ""

    return rr.execute("b1/permute.py", vars(a), [a.separations], a.output, a.seed,
                      run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
