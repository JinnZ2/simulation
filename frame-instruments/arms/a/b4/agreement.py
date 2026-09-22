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


if __name__ == "__main__":
    sys.exit(main())
