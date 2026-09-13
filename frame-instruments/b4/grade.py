"""B4.4 - per-item grade: counts, status and layer distributions, and the
policy-to-physical ratio derived FROM settling_test, never asked for.

A settling test reads as physical when it names a measurement or physical
derivation, as policy when it names a decision, statute, funding rule, or
procedure. The term lists below are the whole of that derivation and are
written into the output header so they report themselves. A test matching
neither list, or both, is unresolved and printed with the ratio.

Output rows: header (physical_terms, policy_terms, n_items, seed);
per requirement (item_id, req_id, reconstructor_id, settling_read,
terms_matched); per item (item_id, n_requirements, n_reconstructors,
status_counts, layer_counts, physical, policy, unresolved,
policy_to_physical, unresolved_req_ids).

Command: python3 grade.py requirements.jsonl grade.jsonl
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import requirements as req_mod  # noqa: E402

PHYSICAL_TERMS = ("measur", "sensor", "gauge", "instrument", "reading", "deriv",
                  "comput", "calculat", "equation", "physic", "temperature",
                  "pressure", "velocity", "distance", "mass", "energy", "thermal",
                  "flow rate", "load-bearing", "capacity", "sample", "assay",
                  "survey", "observ", "count of", "timing", "duration")
POLICY_TERMS = ("statut", "law", "legislat", "regulat", "rule", "polic", "decision",
                "decid", "budget", "fund", "appropriat", "grant", "procure",
                "contract", "tender", "procedur", "protocol", "mandat", "govern",
                "vote", "board", "council", "authorit", "permit", "ordinance",
                "standard", "guideline", "staffing", "hiring", "schedul", "approv",
                "licens", "certif", "insur")


def matched(text, terms):
    t = text.casefold()
    return sorted(term for term in terms if re.search(r"\b" + re.escape(term), t))


def read(settling_test):
    phys, pol = matched(settling_test, PHYSICAL_TERMS), matched(settling_test, POLICY_TERMS)
    if phys and not pol:
        return "physical", phys
    if pol and not phys:
        return "policy", pol
    return "unresolved", phys + pol


def grade(rows):
    seeds = sorted({r["seed"] for r in rows if "seed" in r})
    header = {"physical_terms": list(PHYSICAL_TERMS), "policy_terms": list(POLICY_TERMS),
              "n_items": len({r["item_id"] for r in rows}),
              "seed": seeds[0] if len(seeds) == 1 else (seeds or None)}
    per_req, by_item = [], defaultdict(list)
    for r in rows:
        kind, terms = read(r["settling_test"])
        per_req.append({"item_id": r["item_id"], "req_id": r["req_id"],
                        "reconstructor_id": r["reconstructor_id"],
                        "settling_read": kind, "terms_matched": terms})
        by_item[r["item_id"]].append((r, kind))
    per_item = []
    for item in sorted(by_item):
        rs = by_item[item]
        kinds = Counter(k for _, k in rs)
        phys, pol = kinds["physical"], kinds["policy"]
        per_item.append({
            "item_id": item, "n_requirements": len(rs),
            "n_reconstructors": len({r["reconstructor_id"] for r, _ in rs}),
            "status_counts": dict(sorted(Counter(r["status"] for r, _ in rs).items())),
            "layer_counts": dict(sorted(Counter(r["layer"] for r, _ in rs).items())),
            "physical": phys, "policy": pol, "unresolved": kinds["unresolved"],
            "policy_to_physical": round(pol / phys, 6) if phys else None,
            "unresolved_req_ids": sorted(r["req_id"] for r, k in rs if k == "unresolved"),
        })
    return [header] + per_req + per_item


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="grade requirements per item")
    p.add_argument("requirements")
    p.add_argument("output")
    a = p.parse_args(argv)

    def run():
        rows = req_mod.load_requirements(a.requirements)
        out = grade(rows)
        rr.write_jsonl(a.output, out)
        items = [r for r in out if "n_requirements" in r]
        counts = {"requirements": len(rows), "items": len(items),
                  "unresolved": sum(r["unresolved"] for r in items)}
        return ("ok" if rows else "empty"), counts, ""

    return rr.execute("b4/grade.py", vars(a), [a.requirements], a.output, None, run, runs_path)
"""B4.4 -- per-item counts, distributions and the policy-to-physical ratio.

    python3 grade.py requirements.jsonl grades.jsonl

The physical/policy split is derived FROM settling_test, never asked for.
A settling test that names a measurement or a physical derivation counts
as physical; one that names a decision, statute, funding rule or
procedure counts as policy. The two lexicons below are the whole of that
derivation and are printed by the report, since they are where a frame
could enter. A test matching neither lexicon, or both, is unresolved and
is printed with the ratio, never dropped.

ratio = policy / physical, or null when physical is zero.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from requirements import STATUSES, load_requirements  # noqa: E402
from runrecord import main_guard, write_jsonl  # noqa: E402

PHYSICAL = ("measure", "measurement", "measured", "meter", "gauge", "sensor", "instrument",
            "derive", "derivation", "derived", "calculate", "calculation", "compute", "computed",
            "experiment", "bench test", "load test", "stress test", "tensile", "pressure",
            "temperature", "flow rate", "velocity", "mass", "energy", "thermodynamic", "physics",
            "physical law", "conservation", "tolerance", "field test", "sample", "assay")
POLICY = ("statute", "law", "legislation", "legislative", "regulation", "regulatory", "rule",
          "decision", "decide", "decided", "policy", "funding", "budget", "appropriation",
          "procurement", "contract", "procedure", "protocol", "mandate", "authorize",
          "authorization", "vote", "ordinance", "permit", "license", "licensing", "staffing",
          "hiring", "directive", "approval", "certification", "board", "committee", "agency")


def _pattern(terms) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")\b", re.IGNORECASE)


PHYSICAL_RE = _pattern(PHYSICAL)
POLICY_RE = _pattern(POLICY)


def classify(settling_test: str) -> str:
    """physical, policy, neither, or both. Derived from the test text only."""
    phys, pol = bool(PHYSICAL_RE.search(settling_test)), bool(POLICY_RE.search(settling_test))
    if phys and not pol:
        return "physical"
    if pol and not phys:
        return "policy"
    return "both" if phys and pol else "neither"


def grade(rows: list[dict]) -> list[dict]:
    by_item = defaultdict(list)
    for r in rows:
        by_item[r["item_id"]].append(r)
    out = []
    for item in sorted(by_item):
        reqs = by_item[item]
        kinds = Counter(classify(r["settling_test"]) for r in reqs)
        physical, policy = kinds["physical"], kinds["policy"]
        unresolved = kinds["neither"] + kinds["both"]
        out.append({
            "kind": "item", "item_id": item,
            "n_requirements": len(reqs),
            "n_reconstructors": len({r["reconstructor_id"] for r in reqs}),
            "status": {s: sum(1 for r in reqs if r["status"] == s) for s in STATUSES},
            "layer": dict(sorted(Counter(r["layer"] for r in reqs).items())),
            "physical": physical, "policy": policy, "unresolved": unresolved,
            "unresolved_neither": kinds["neither"], "unresolved_both": kinds["both"],
            "ratio_policy_to_physical": None if physical == 0 else round(policy / physical, 6),
        })
    return out


def _body(args):
    rows = load_requirements(args[0])
    out = grade(rows)
    write_jsonl(args[1], out)
    counts = {"items": len(out), "requirements": len(rows),
              "unresolved": sum(g["unresolved"] for g in out)}
    return ("empty" if not rows else "ok"), counts, f"lexicon physical={len(PHYSICAL)} policy={len(POLICY)}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("b4.grade", argv, ["<in:requirements.jsonl>", "<out:grades.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
