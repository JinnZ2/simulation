"""B1.4 -- summary of a separations file. Runs identically on the real
file and the permuted one; nothing here branches on which it received.

    python3 summarise.py separations.jsonl summary.jsonl

Rows written, by "kind":
  cases      case_ids, model_ids, D and L values present, row count
  cell       per (D, L, model_id): n_rows, mean_div, resync_rate,
             n_top_decile, top_decile (position keys), ent_div_overlap
  stability  Jaccard overlap of top-decile position sets between adjacent
             D values (L fixed) and adjacent L values (D fixed)

A position key is "case_id:i:branch_rank". The top decile is the top
ceil(n/10) rows by div_D, ties broken by position key so the set is
deterministic. ent_div_overlap is the Jaccard overlap between the top
decile by entropy and the top decile by div_D in the same cell.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

NEEDED = ("case_id", "model_id", "i", "branch_rank", "D", "L", "ent_i", "resync_D", "div_D")


def pos_key(r: dict) -> str:
    return f"{r['case_id']}:{r['i']}:{r['branch_rank']}"


def top_decile(rows: list[dict], field: str) -> list[str]:
    k = max(1, math.ceil(len(rows) / 10))
    ordered = sorted(rows, key=lambda r: (-r[field], pos_key(r)))
    return sorted(pos_key(r) for r in ordered[:k])


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def summarise(rows: list[dict]) -> list[dict]:
    for n, r in enumerate(rows, 1):
        missing = [f for f in NEEDED if f not in r]
        if missing:
            raise SchemaError(f"separations.jsonl line {n}: missing field '{missing[0]}'")
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        cells[(r["D"], r["L"], r["model_id"])].append(r)
    out = [{
        "kind": "cases",
        "case_ids": sorted({r["case_id"] for r in rows}),
        "model_ids": sorted({r["model_id"] for r in rows}),
        "D_values": sorted({r["D"] for r in rows}),
        "L_values": sorted({r["L"] for r in rows}),
        "n_rows": len(rows),
    }]
    deciles: dict[tuple, list[str]] = {}
    for key in sorted(cells):
        D, L, model = key
        cell = cells[key]
        by_div = top_decile(cell, "div_D")
        by_ent = top_decile(cell, "ent_i")
        deciles[key] = by_div
        out.append({
            "kind": "cell", "D": D, "L": L, "model_id": model,
            "n_rows": len(cell),
            "mean_div": round(sum(r["div_D"] for r in cell) / len(cell), 6),
            "resync_rate": round(sum(r["resync_D"] for r in cell) / len(cell), 6),
            "n_top_decile": len(by_div),
            "top_decile": by_div,
            "ent_div_overlap": round(jaccard(by_ent, by_div), 6),
        })
    Ds = sorted({k[0] for k in cells})
    Ls = sorted({k[1] for k in cells})
    models = sorted({k[2] for k in cells})
    for model in models:
        for L in Ls:
            for a, b in zip(Ds, Ds[1:]):
                if (a, L, model) in deciles and (b, L, model) in deciles:
                    out.append({"kind": "stability", "axis": "D", "model_id": model, "L": L,
                                "from": a, "to": b,
                                "jaccard": round(jaccard(deciles[(a, L, model)], deciles[(b, L, model)]), 6)})
        for D in Ds:
            for a, b in zip(Ls, Ls[1:]):
                if (D, a, model) in deciles and (D, b, model) in deciles:
                    out.append({"kind": "stability", "axis": "L", "model_id": model, "D": D,
                                "from": a, "to": b,
                                "jaccard": round(jaccard(deciles[(D, a, model)], deciles[(D, b, model)]), 6)})
    return out


def _body(args):
    rows = read_jsonl(args[0])
    if not rows:
        write_jsonl(args[1], [])
        return "empty", {"rows": 0}, ""
    out = summarise(rows)
    write_jsonl(args[1], out)
    counts = {"rows": len(rows),
              "cells": sum(1 for r in out if r["kind"] == "cell"),
              "stability": sum(1 for r in out if r["kind"] == "stability")}
    return "ok", counts, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("summarise", argv, ["<in:separations.jsonl>", "<out:summary.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
