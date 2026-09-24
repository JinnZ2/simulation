"""B1.4 - summary over a separations file. Identical on real and permuted input.

Output rows (distinguished by their keys, not by a type field):
  header    n_rows, positions, cases, models, seed, source
  cell      model_id, D, L, n, mean_div, resync_rate, sep_rate_all,
            sep_rate_high_ent, top_decile_threshold, top_decile_positions,
            top_decile_ids
  stability model_id, L, D_a, D_b, jaccard      (adjacent D, same L)
            model_id, D, L_a, L_b, jaccard      (adjacent L, same D)

Command: python3 summarise.py separations.jsonl summary.jsonl
"""
import argparse
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import permute  # noqa: E402


def pos_id(r):
    return "%s:%d" % (r["case_id"], r["i"])


def top_decile(pairs):
    """pairs: [(value, position)]. Return (set of positions, threshold)."""
    if not pairs:
        return set(), None
    vals = sorted((v for v, _ in pairs), reverse=True)
    thr = vals[max(1, math.ceil(len(vals) / 10)) - 1]
    return {p for v, p in pairs if v >= thr}, thr


def jaccard(a, b):
    u = a | b
    return round(len(a & b) / len(u), 6) if u else 0.0


def summarise(rows, source=""):
    seeds = sorted({r["seed"] for r in rows if "seed" in r})
    header = {
        "n_rows": len(rows),
        "positions": len({pos_id(r) for r in rows}),
        "cases": sorted({r["case_id"] for r in rows}),
        "models": sorted({r["model_id"] for r in rows}),
        "seed": seeds[0] if len(seeds) == 1 else (seeds or None),
        "source": source,
    }
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model_id"], r["D"], r["L"])].append(r)
    cells, sets = [], {}
    for key in sorted(groups):
        g = groups[key]
        n = len(g)
        resync_rate = sum(r["resync_D"] for r in g) / n
        div_set, thr = top_decile([(r["div_D"], pos_id(r)) for r in g])
        ent_by_pos = {pos_id(r): r["ent_i"] for r in g}
        high_ent, _ = top_decile([(e, p) for p, e in ent_by_pos.items()])
        he_rows = [r for r in g if pos_id(r) in high_ent]
        sets[key] = div_set
        cells.append({
            "model_id": key[0], "D": key[1], "L": key[2], "n": n,
            "mean_div": round(sum(r["div_D"] for r in g) / n, 6),
            "resync_rate": round(resync_rate, 6),
            "sep_rate_all": round(1 - resync_rate, 6),
            "sep_rate_high_ent": round(
                sum(1 - r["resync_D"] for r in he_rows) / len(he_rows), 6)
            if he_rows else None,
            "top_decile_threshold": thr,
            "top_decile_positions": len(div_set),
            "top_decile_ids": sorted(div_set),
        })
    stability = []
    models = sorted({k[0] for k in groups})
    ds = sorted({k[1] for k in groups})
    ls = sorted({k[2] for k in groups})
    for m in models:
        for L in ls:
            for da, db in zip(ds, ds[1:]):
                if (m, da, L) in sets and (m, db, L) in sets:
                    stability.append({"model_id": m, "L": L, "D_a": da, "D_b": db,
                                      "jaccard": jaccard(sets[(m, da, L)], sets[(m, db, L)])})
        for D in ds:
            for la, lb in zip(ls, ls[1:]):
                if (m, D, la) in sets and (m, D, lb) in sets:
                    stability.append({"model_id": m, "D": D, "L_a": la, "L_b": lb,
                                      "jaccard": jaccard(sets[(m, D, la)], sets[(m, D, lb)])})
    return [header] + cells + stability


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="summarise a separations file")
    p.add_argument("separations")
    p.add_argument("output")
    a = p.parse_args(argv)

    def run():
        rows = permute.load(a.separations)
        out = summarise(rows, os.path.basename(a.separations))
        rr.write_jsonl(a.output, out)
        counts = {"rows_in": len(rows), "cells": sum(1 for r in out if "n" in r),
                  "stability_pairs": sum(1 for r in out if "jaccard" in r)}
        return ("ok" if rows else "empty"), counts, ""

    seed = None
    return rr.execute("b1/summarise.py", vars(a), [a.separations], a.output, seed,
                      run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
