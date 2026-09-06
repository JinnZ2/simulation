"""B1.2 -- separation scoring. Offline; no model, no network.

    python3 score.py base.jsonl traces.jsonl separations.jsonl

One row per (trace, D, L): D swept over {8,16,32,64,128} by truncating the
stored continuation, L (rejoin match length) swept over {2,4,8}. Both are
written into every row. Neither is a constant.

resync_D: 1 if the continuation rejoins the base within D tokens, where
"rejoins" means some L-gram ending at or before token D of the continuation
occurs as a contiguous run anywhere in the first D tokens of the base
continuation. Unaligned on purpose: a forced token often shifts the
alignment by a word and an aligned test would miss a genuine rejoin.

div_D: Levenshtein distance over tokens between the two continuations,
both truncated at D, divided by the longer length.

gap_i: logprob_taken minus the logprob of forced_token in topk at i.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, write_jsonl  # noqa: E402
from schema import load_base, load_traces  # noqa: E402

D_SWEEP = (8, 16, 32, 64, 128)
L_SWEEP = (2, 4, 8)
FIELDS = ("case_id", "model_id", "i", "branch_rank", "D", "L",
          "ent_i", "gap_i", "resync_D", "div_D")


def levenshtein(a, b) -> int:
    """Token-level edit distance, two-row dynamic programme."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ta in enumerate(a, 1):
        cur = [i]
        for j, tb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ta != tb)))
        prev = cur
    return prev[-1]


def div(cont, base, D: int) -> float:
    c, b = cont[:D], base[:D]
    longest = max(len(c), len(b))
    return 0.0 if longest == 0 else levenshtein(c, b) / longest


def resync(cont, base, D: int, L: int) -> int:
    c, b = cont[:D], base[:D]
    if len(c) < L or len(b) < L:
        return 0
    grams = {tuple(b[j:j + L]) for j in range(len(b) - L + 1)}
    return int(any(tuple(c[e - L:e]) in grams for e in range(L, len(c) + 1)))


def gap(base_row: dict, forced_token: str, where: str) -> float:
    for token, logprob in base_row["topk"]:
        if token == forced_token:
            return base_row["logprob_taken"] - logprob
    raise SchemaError(f"{where}: forced_token {forced_token!r} not in topk at i={base_row['i']}")


def score(base_rows, traces, name: str = "traces.jsonl") -> list[dict]:
    index = {(r["case_id"], r["model_id"], r["i"]): r for r in base_rows}
    out = []
    for n, t in enumerate(traces, 1):
        where = f"{name} line {n}"
        key = (t["case_id"], t["model_id"], t["i"])
        if key not in index:
            raise SchemaError(f"{where}: no base row for case_id={key[0]!r} model_id={key[1]!r} i={key[2]}")
        b = index[key]
        g = gap(b, t["forced_token"], where)
        for D in D_SWEEP:
            d = div(t["continuation"], t["base_continuation"], D)
            for L in L_SWEEP:
                out.append({
                    "case_id": t["case_id"], "model_id": t["model_id"], "i": t["i"],
                    "branch_rank": t["branch_rank"], "D": D, "L": L,
                    "ent_i": b["entropy_i"], "gap_i": g,
                    "resync_D": resync(t["continuation"], t["base_continuation"], D, L),
                    "div_D": round(d, 6),
                })
    return out


def _body(args):
    base = load_base(args[0])
    traces = load_traces(args[1])
    rows = score(base, traces, Path(args[1]).name)
    n = write_jsonl(args[2], rows)
    bases = sorted({r["entropy_basis"] for r in base})
    counts = {"traces": len(traces), "rows": n, "D": len(D_SWEEP), "L": len(L_SWEEP)}
    return ("empty" if n == 0 else "ok"), counts, f"entropy_basis={','.join(bases)}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:base.jsonl>", "<in:traces.jsonl>", "<out:separations.jsonl>"]
    return main_guard("score", argv, names, None, _body)


if __name__ == "__main__":
    sys.exit(main())
