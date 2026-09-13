"""B4.5 - agreement across reconstructors, wrapping B2's agree.py.

Requirement lists are unordered free text, so matching is external: it
arrives as matches.jsonl (item_id, req_a, req_b, matched) and --match-source
records who or what produced it. Matched pairs join requirements into
classes (union-find); each reconstructor's list becomes a set of classes;
agreement is B2's pairwise set agreement (mean Jaccard) and the count of
disjoint pairs. A matched pair whose two requirements do not currently sit
on the same item is counted as cross-item and not joined - that is what a
shuffled file does to real matches, and the count is printed.

Output rows: header (match_source, n_items, matches_rows, matches_true,
matches_cross_item, matches_unknown_req, seed); per item (item_id,
n_reconstructors, n_requirements, n_classes, pairwise_agreement,
full_disagreement, n_singletons, singletons).

Command: python3 agreement.py requirements.jsonl matches.jsonl agreement.jsonl
         --match-source "<who or what matched>"
"""
import argparse
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE), os.path.join(os.path.dirname(HERE), "b2")]
import runrecord as rr  # noqa: E402
import agree  # noqa: E402
import requirements as req_mod  # noqa: E402


def load_matches(path):
    out = []
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        rr.no_forbidden_fields(row, where)
        for f in ("item_id", "req_a", "req_b"):
            rr.field(row, f, where, str)
        rr.field(row, "matched", where, bool, allow_bool=True)
        out.append(row)
    return out


def find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def agreement(rows, matches, match_source):
    item_of = {r["req_id"]: r["item_id"] for r in rows}
    parent = {r["req_id"]: r["req_id"] for r in rows}
    n_true = cross = unknown = 0
    for m in matches:
        if not m["matched"]:
            continue
        n_true += 1
        a, b = m["req_a"], m["req_b"]
        if a not in item_of or b not in item_of:
            unknown += 1
        elif item_of[a] != item_of[b]:
            cross += 1
        else:
            parent[find(parent, a)] = find(parent, b)
    seeds = sorted({r["seed"] for r in rows if "seed" in r})
    header = {"match_source": match_source, "n_items": len(set(item_of.values())),
              "matches_rows": len(matches), "matches_true": n_true,
              "matches_cross_item": cross, "matches_unknown_req": unknown,
              "seed": seeds[0] if len(seeds) == 1 else (seeds or None)}
    by_item = defaultdict(list)
    for r in rows:
        by_item[r["item_id"]].append(r)
    out = [header]
    for item in sorted(by_item):
        rs = by_item[item]
        classes = defaultdict(list)
        for r in rs:
            classes[find(parent, r["req_id"])].append(r)
        recs = sorted({r["reconstructor_id"] for r in rs})
        sets = [{find(parent, r["req_id"]) for r in rs if r["reconstructor_id"] == rid} for rid in recs]
        mean_j, disjoint = agree.pairwise_set_agreement(sets)
        singles = [c for c in classes.values() if len({r["reconstructor_id"] for r in c}) == 1]
        out.append({
            "item_id": item, "n_reconstructors": len(recs), "n_requirements": len(rs),
            "n_classes": len(classes), "pairwise_agreement": mean_j,
            "full_disagreement": disjoint, "n_singletons": len(singles),
            "singletons": sorted(({k: r[k] for k in ("req_id", "reconstructor_id",
                                                      "requirement_text", "settling_test")}
                                  for c in singles for r in c), key=lambda s: s["req_id"]),
        })
    return out


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="agreement across reconstructors")
    p.add_argument("requirements")
    p.add_argument("matches")
    p.add_argument("output")
    p.add_argument("--match-source", required=True)
    a = p.parse_args(argv)

    def run():
        rows = req_mod.load_requirements(a.requirements)
        out = agreement(rows, load_matches(a.matches), a.match_source)
        rr.write_jsonl(a.output, out)
        h = out[0]
        counts = {"items": h["n_items"], "matches_true": h["matches_true"],
                  "matches_cross_item": h["matches_cross_item"],
                  "singletons": sum(r["n_singletons"] for r in out[1:])}
        return ("ok" if rows else "empty"), counts, ""

    return rr.execute("b4/agreement.py", vars(a), [a.requirements, a.matches], a.output,
                      None, run, runs_path)
"""B4.5 -- agreement across reconstructors from externally supplied matches.

    python3 agreement.py requirements.jsonl matches.jsonl MATCH_SOURCE agreement.jsonl

Requirement lists are unordered free text, so exact match will not work.
Two requirements from different reconstructors MATCH when their settling
tests name the same decision, statute or measurement. That judgement is
made outside this script and arrives as matches.jsonl:
  item_id, req_a, req_b, matched      (req_* = "<reconstructor_id>/<req_id>")
MATCH_SOURCE names who or what produced it and is stamped on every output
row through agree.stamp(), B2's one added field. The matcher is a frame
entry point and has to be visible in the record.

Matched pairs are closed into clusters. For each pair of reconstructors,
agreement is the Jaccard overlap of the clusters each touches; the item's
pairwise agreement is the mean over pairs. full_disagreement is 1 when
two or more reconstructors share no cluster at all. A singleton is a
cluster returned by exactly one reconstructor; singletons are printed in
full, never discarded: each is either noise or the one reader who saw it.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agree import _mean, stamp  # noqa: E402
from requirements import load_requirements  # noqa: E402
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

MATCH_FIELDS = ("item_id", "req_a", "req_b", "matched")


def ref(r: dict) -> str:
    return f"{r['reconstructor_id']}/{r['req_id']}"


def load_matches(path, reqs: list[dict]) -> list[dict]:
    known = {(r["item_id"], ref(r)) for r in reqs}
    rows = read_jsonl(path)
    name = Path(path).name
    for n, m in enumerate(rows, 1):
        where = f"{name} line {n}"
        for f in MATCH_FIELDS:
            if f not in m:
                raise SchemaError(f"{where}: missing field '{f}'")
        for f in m:
            if f not in MATCH_FIELDS:
                raise SchemaError(f"{where}: unexpected field '{f}'")
        if not isinstance(m["matched"], bool):
            raise SchemaError(f"{where}: field 'matched' must be true or false")
        for f in ("req_a", "req_b"):
            if not isinstance(m[f], str) or "/" not in m[f]:
                raise SchemaError(f"{where}: field '{f}' must be '<reconstructor_id>/<req_id>'")
            if (m["item_id"], m[f]) not in known:
                raise SchemaError(f"{where}: {f} {m[f]!r} not in requirements for item {m['item_id']!r}")
        if m["req_a"].split("/")[0] == m["req_b"].split("/")[0]:
            raise SchemaError(f"{where}: req_a and req_b come from the same reconstructor")
    return rows


def clusters(item_reqs: list[dict], item_matches: list[dict]) -> list[set[str]]:
    parent = {ref(r): ref(r) for r in item_reqs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for m in item_matches:
        if m["matched"]:
            parent[find(m["req_a"])] = find(m["req_b"])
    groups = defaultdict(set)
    for x in parent:
        groups[find(x)].add(x)
    return sorted(groups.values(), key=lambda g: sorted(g))


def jaccard(a, b) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def agreement(reqs: list[dict], matches: list[dict]) -> list[dict]:
    by_item, m_by_item = defaultdict(list), defaultdict(list)
    for r in reqs:
        by_item[r["item_id"]].append(r)
    for m in matches:
        m_by_item[m["item_id"]].append(m)
    items, singletons = [], []
    for item in sorted(by_item):
        cl = clusters(by_item[item], m_by_item[item])
        recs = sorted({r["reconstructor_id"] for r in by_item[item]})
        touched = {rid: {i for i, g in enumerate(cl) if any(x.startswith(rid + "/") for x in g)} for rid in recs}
        pair_scores = [jaccard(touched[a], touched[b]) for a, b in combinations(recs, 2)]
        shared = sum(1 for g in cl if len({x.split("/")[0] for x in g}) >= 2)
        single = [g for g in cl if len({x.split("/")[0] for x in g}) == 1]
        items.append({"kind": "item", "item_id": item, "n_reconstructors": len(recs),
                      "n_requirements": len(by_item[item]), "n_clusters": len(cl), "n_shared_clusters": shared,
                      "pairwise_agreement": _mean(pair_scores) if pair_scores else None,
                      "full_disagreement": int(len(recs) >= 2 and shared == 0) if len(recs) >= 2 else None,
                      "n_singletons": len(single), "n_matches_supplied": len(m_by_item[item])})
        lookup = {ref(r): r for r in by_item[item]}
        for g in single:
            for x in sorted(g):
                r = lookup[x]
                singletons.append({"kind": "singleton", "item_id": item, "reconstructor_id": r["reconstructor_id"],
                                   "req_id": r["req_id"], "requirement_text": r["requirement_text"],
                                   "settling_test": r["settling_test"], "layer": r["layer"]})
    return items + singletons


def _body(args):
    reqs = load_requirements(args[0])
    matches = load_matches(args[1], reqs)
    rows = stamp(agreement(reqs, matches), args[2])
    write_jsonl(args[3], rows)
    items = [r for r in rows if r["kind"] == "item"]
    counts = {"items": len(items), "matches": len(matches),
              "singletons": sum(1 for r in rows if r["kind"] == "singleton")}
    return ("empty" if not reqs else "ok"), counts, f"match_source={args[2]}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:requirements.jsonl>", "<in:matches.jsonl>", "MATCH_SOURCE", "<out:agreement.jsonl>"]
    return main_guard("b4.agreement", argv, names, None, _body)


if __name__ == "__main__":
    sys.exit(main())
