"""B1.4 -- summary of a separations file. Runs identically on the real
file and the permuted one; nothing here branches on which it received.

    python3 summarise.py separations.jsonl summary.jsonl

Rows written, by "kind":
  cases      case_ids, model_ids, N, D and L values present, row count
  cell       per (N, D, L, model_id): n_rows, mean_div, resync_rate,
             n_top_decile, top_decile (position keys), ent_div_overlap
  stability  Jaccard overlap of top-decile position sets between adjacent
             D values (N, L fixed), adjacent L values (N, D fixed) and
             adjacent N values (D, L fixed)
  cross_model per (N, D, L, case_id, model pair): Jaccard overlap of the
             two models' top-decile positions on that case (RU-4). Only
             written when two or more models are present. Positions are
             compared by index i, so this is meaningful only where the
             models share a tokenizer or the producer aligned positions;
             the permuted file supplies the chance level.

N levels are the distinct selection_N values present. Membership is
nested: a row belongs to every level >= its own N, so the N=50 cell holds
the N=10 and N=25 positions too. A position key is
"case_id:i:branch_rank". The top decile is the top ceil(n/10) rows by
div_D, ties broken by position key so the set is deterministic.
ent_div_overlap is the Jaccard overlap between the top decile by entropy
and the top decile by div_D in the same cell.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

NEEDED = ("case_id", "model_id", "i", "branch_rank", "N", "D", "L", "ent_i", "resync_D", "div_D")


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


def _cell(key, cell, deciles, out):
    N, D, L, model = key
    by_div = top_decile(cell, "div_D")
    deciles[key] = by_div
    out.append({
        "kind": "cell", "N": N, "D": D, "L": L, "model_id": model,
        "n_rows": len(cell),
        "mean_div": round(sum(r["div_D"] for r in cell) / len(cell), 6),
        "resync_rate": round(sum(r["resync_D"] for r in cell) / len(cell), 6),
        "n_top_decile": len(by_div),
        "top_decile": by_div,
        "ent_div_overlap": round(jaccard(top_decile(cell, "ent_i"), by_div), 6),
    })


def _stability(axis, model, fixed, a, b, deciles, ka, kb, out):
    if ka in deciles and kb in deciles:
        row = {"kind": "stability", "axis": axis, "model_id": model}
        row.update(fixed)
        row.update({"from": a, "to": b, "jaccard": round(jaccard(deciles[ka], deciles[kb]), 6)})
        out.append(row)


def _cross_model(Ns, Ds, Ls, models, cases, deciles, out):
    if len(models) < 2:
        return
    for N in Ns:
        for D in Ds:
            for L in Ls:
                for case in cases:
                    for ia, a in enumerate(models):
                        for b in models[ia + 1:]:
                            ka, kb = (N, D, L, a), (N, D, L, b)
                            if ka not in deciles or kb not in deciles:
                                continue
                            sa = [k for k in deciles[ka] if k.startswith(case + ":")]
                            sb = [k for k in deciles[kb] if k.startswith(case + ":")]
                            if not sa and not sb:
                                continue
                            out.append({"kind": "cross_model", "N": N, "D": D, "L": L, "case_id": case,
                                        "model_a": a, "model_b": b, "jaccard": round(jaccard(sa, sb), 6)})


def summarise(rows: list[dict]) -> list[dict]:
    for n, r in enumerate(rows, 1):
        missing = [f for f in NEEDED if f not in r]
        if missing:
            raise SchemaError(f"separations.jsonl line {n}: missing field '{missing[0]}'")
    Ns = sorted({r["N"] for r in rows})
    Ds = sorted({r["D"] for r in rows})
    Ls = sorted({r["L"] for r in rows})
    models = sorted({r["model_id"] for r in rows})
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        for N in Ns:
            if r["N"] <= N:
                cells[(N, r["D"], r["L"], r["model_id"])].append(r)
    cases = sorted({r["case_id"] for r in rows})
    out = [{"kind": "cases", "case_ids": cases, "model_ids": models,
            "N_values": Ns, "D_values": Ds, "L_values": Ls, "n_rows": len(rows)}]
    deciles: dict[tuple, list[str]] = {}
    for key in sorted(cells):
        _cell(key, cells[key], deciles, out)
    for model in models:
        for N in Ns:
            for L in Ls:
                for a, b in zip(Ds, Ds[1:]):
                    _stability("D", model, {"N": N, "L": L}, a, b, deciles, (N, a, L, model), (N, b, L, model), out)
            for D in Ds:
                for a, b in zip(Ls, Ls[1:]):
                    _stability("L", model, {"N": N, "D": D}, a, b, deciles, (N, D, a, model), (N, D, b, model), out)
        for D in Ds:
            for L in Ls:
                for a, b in zip(Ns, Ns[1:]):
                    _stability("N", model, {"D": D, "L": L}, a, b, deciles, (a, D, L, model), (b, D, L, model), out)
    _cross_model(Ns, Ds, Ls, models, cases, deciles, out)
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
              "stability": sum(1 for r in out if r["kind"] == "stability"),
              "cross_model": sum(1 for r in out if r["kind"] == "cross_model")}
    return "ok", counts, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("summarise", argv, ["<in:separations.jsonl>", "<out:summary.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
