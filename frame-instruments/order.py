"""B2.2 -- counterbalanced condition order per reader.

    python3 order.py N_READERS SEED assignment.jsonl

Readers are filled in blocks of four from a Williams Latin square (each
condition once per position, each condition preceded once by every other),
block rows shuffled by the seed. A remainder that does not fill a block
gets seeded permutations and the shortfall is written to the run record.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, write_jsonl  # noqa: E402

CONDITIONS = ("A", "B", "C", "D")
WILLIAMS = (("A", "B", "D", "C"), ("B", "C", "A", "D"), ("C", "D", "B", "A"), ("D", "A", "C", "B"))


def assign(n_readers: int, seed: int) -> tuple[list[dict], str]:
    if n_readers < 1:
        raise SchemaError("N_READERS must be >= 1")
    rng = random.Random(seed)
    rows = []
    full, rest = divmod(n_readers, len(WILLIAMS))
    for _ in range(full):
        square = list(WILLIAMS)
        rng.shuffle(square)
        for order in square:
            rows.append({"reader_id": f"r{len(rows) + 1:03d}", "order": list(order)})
    for _ in range(rest):
        order = list(CONDITIONS)
        rng.shuffle(order)
        rows.append({"reader_id": f"r{len(rows) + 1:03d}", "order": order})
    note = f"{full} full Latin square block(s) of {len(WILLIAMS)}"
    if rest:
        note += f"; {rest} reader(s) on seeded permutations, order not fully counterbalanced"
    return rows, note


def _body(args):
    n, seed = int(args[0]), int(args[1])
    rows, note = assign(n, seed)
    write_jsonl(args[2], rows)
    return "ok", {"readers": len(rows), "conditions": len(CONDITIONS)}, f"seed={seed}; {note}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("order", argv, ["N_READERS", "SEED", "<out:assignment.jsonl>"], 1, _body)


if __name__ == "__main__":
    sys.exit(main())
