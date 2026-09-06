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
