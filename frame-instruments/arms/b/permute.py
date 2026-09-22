"""B1.3 -- permutation null for separations.jsonl.

    python3 permute.py separations.jsonl separations_permuted.jsonl SEED

Within each stratum (case_id, model_id, D, L) the (ent_i, gap_i, resync_D,
div_D) tuples are shuffled across the (i, branch_rank) rows. Row count,
strata and every other field are preserved. The seed is written to the run
record. Strata are permuted independently, so any agreement between
adjacent D or L cells in the permuted file is chance.
"""

from __future__ import annotations

import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

TUPLE = ("ent_i", "gap_i", "resync_D", "div_D")
STRATUM = ("case_id", "model_id", "D", "L")


def permute(rows: list[dict], seed: int) -> list[dict]:
    for n, r in enumerate(rows, 1):
        missing = [f for f in TUPLE + STRATUM if f not in r]
        if missing:
            raise SchemaError(f"separations.jsonl line {n}: missing field '{missing[0]}'")
    rng = random.Random(seed)
    groups: dict[tuple, list[int]] = defaultdict(list)
    for idx, r in enumerate(rows):
        groups[tuple(r[f] for f in STRATUM)].append(idx)
    out = [dict(r) for r in rows]
    for key in sorted(groups):
        idxs = groups[key]
        tuples = [tuple(rows[i][f] for f in TUPLE) for i in idxs]
        rng.shuffle(tuples)
        for i, tup in zip(idxs, tuples):
            out[i].update(dict(zip(TUPLE, tup)))
    return out


def _body(args):
    rows = read_jsonl(args[0])
    seed = int(args[2])
    out = permute(rows, seed)
    n = write_jsonl(args[1], out)
    strata = len({tuple(r[f] for f in STRATUM) for r in rows})
    return ("empty" if n == 0 else "ok"), {"rows": n, "strata": strata}, f"seed={seed}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:separations.jsonl>", "<out:separations_permuted.jsonl>", "SEED"]
    return main_guard("permute", argv, names, 2, _body)


if __name__ == "__main__":
    sys.exit(main())
