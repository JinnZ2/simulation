#!/usr/bin/env python3
"""render_ledger -- cost of rendering only observed cells, and the deletion signature.

Co-authored (Kavik + Claude, 2026-11-01). CC0. stdlib only. Pre-registration: REFUTE.md, NULL.md
(committed before this file). SYNTHETIC world; says nothing observational.
"""
from __future__ import annotations

import random
import sys
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402


def consistent(cell: int, t: int, states: int) -> int:
    return (cell * 2654435761 + t * 40503 + 12345) % states


def measure(seed: int, point: dict, config: dict) -> dict:
    w = config["world"]
    N, T, M = w["cells"], w["steps"], w["states"]
    full = N * T
    if point["observer"] == "any_interaction":
        # every cell interacts with something every step: observed every step, no gaps.
        # Closed form (same accounting as the loop below with |S_t| = N): every policy
        # computes every cell every step, and no cell is ever re-observed after a gap.
        return {"saving_keep": 0.0, "saving_recompute": 0.0, "saving_delete": 0.0,
                "coverage_keep": 1.0, "contra_keep": 0.0, "contra_recompute": 0.0,
                "contra_delete": 0.0, "reobs_after_gap": 0.0}
    rng = random.Random(seed)
    k = int(point["p_observe"] * N)
    record = bytearray(N)
    rec_size = 0
    last = array("i", [-1]) * N
    seen = bytearray(N)
    prev = set()
    cost_keep = cost_rec = cost_del = 0
    reobs = mis_del = mis_keep = mis_rec = 0
    for t in range(T):
        S = rng.sample(range(N), k)
        Sset = set(S)
        for c in S:
            if not record[c]:
                record[c] = 1
                rec_size += 1
            # recompute: catch up from the last computed step (from 0 if never computed)
            cost_rec += t - last[c] if last[c] >= 0 else t + 1
            last[c] = t
            # delete: continuing observation costs 1; a fresh instantiation costs 1
            cost_del += 1
            if c not in prev and seen[c]:
                reobs += 1
                fresh = rng.randrange(M)                      # no history kept
                if fresh != consistent(c, t, M):
                    mis_del += 1
                # keep-record and recompute both return consistent(c, t): their state was
                # evolved (keep) or caught up (recompute) from the rule, so mis_keep and
                # mis_rec stay 0 by construction -- stated in REFUTE.md, not discovered.
            seen[c] = 1
        cost_keep += rec_size
        prev = Sset
    return {"saving_keep": 1 - cost_keep / full, "saving_recompute": 1 - cost_rec / full,
            "saving_delete": 1 - cost_del / full, "coverage_keep": rec_size / N,
            "contra_keep": mis_keep / reobs if reobs else 0.0,
            "contra_recompute": mis_rec / reobs if reobs else 0.0,
            "contra_delete": mis_del / reobs if reobs else 0.0, "reobs_after_gap": float(reobs)}


def null(seed: int, point: dict, config: dict) -> dict:
    return {"saving_keep": 0.0, "saving_recompute": 0.0, "saving_delete": 0.0, "coverage_keep": 1.0,
            "contra_keep": 0.0, "contra_recompute": 0.0, "contra_delete": 0.0, "reobs_after_gap": 0.0}


def grade(obs: list, null_obs: list, config: dict) -> Verdict:
    rp = config["refute_params"]
    seeds = config["seeds"]
    fails = {s: [] for s in seeds}
    for row in obs:
        s, p, m = row["seed"], row["sweep"], row["metrics"]
        if p["observer"] == "any_interaction":
            for pol in ("keep", "recompute", "delete"):
                if m["saving_" + pol] >= rp["max_saving_any_interaction"]:
                    fails[s].append("any_interaction saving %s %.3f" % (pol, m["saving_" + pol]))
        else:
            if p["p_observe"] == 0.1 and m["coverage_keep"] < rp["min_coverage_p01"]:
                fails[s].append("coverage %.4f at p=0.1" % m["coverage_keep"])
            if m["contra_delete"] == 0:
                fails[s].append("delete contradiction rate 0 at p=%s" % p["p_observe"])
        if m["contra_keep"] > 0 or m["contra_recompute"] > 0:
            fails[s].append("keep/recompute contradiction > 0")
    bad = [s for s in seeds if fails[s]]
    detail = {"failing_seeds": {str(s): fails[s] for s in bad}}
    if len(bad) >= rp["refute_at_seeds"]:
        return Verdict(REFUTED, "%d of %d seeds fail: %s" % (len(bad), len(seeds), fails[bad[0]]), detail)
    if len(seeds) - len(bad) >= rp["support_at_seeds"]:
        hum = [r["metrics"] for r in obs if r["sweep"]["observer"] == "humans_only"]
        return Verdict(SUPPORTED,
                       "all parts hold at %d of %d seeds; delete contradiction rate %.3f-%.3f; "
                       "any-interaction saving 0 for every policy" % (
                           len(seeds) - len(bad), len(seeds), min(m["contra_delete"] for m in hum),
                           max(m["contra_delete"] for m in hum)), detail)
    return Verdict(INCONCLUSIVE, "between thresholds: %d failing seeds" % len(bad), detail)


if __name__ == "__main__":
    v = run(HERE / "config.json", measure, null, grade)
    sys.exit(0 if v.verdict in (SUPPORTED, REFUTED, INCONCLUSIVE) else 1)
