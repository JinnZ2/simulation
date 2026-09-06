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
