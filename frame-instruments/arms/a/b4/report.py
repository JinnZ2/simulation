"""B4.8 - report.md. Nine sections, in order, no others. The shuffled result
is a second output, never a gate: if either shuffled file is missing the run
is void and nothing is written.

Command: python3 report.py report.md --items items_a.jsonl [items_b.jsonl]
         --requirements requirements.jsonl
         --grade grade.jsonl --grade-shuffled grade_shuffled.jsonl
         --agreement agreement.jsonl --agreement-shuffled agreement_shuffled.jsonl
         [--calibration calibration.jsonl]
"""
import argparse
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import items as items_mod  # noqa: E402
import requirements as req_mod  # noqa: E402


def load_output(path, body_key):
    if path is None:
        return None, []
    if not os.path.exists(path):
        raise rr.Void("missing: %s" % os.path.basename(path))
    rows = [r for _, r in rr.read_jsonl(path)]
    if not rows:
        raise rr.Reject("%s: empty" % path)
    return rows[0], [r for r in rows[1:] if body_key in r]


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "%.3f" % v
    if isinstance(v, (list, dict)):
        return ", ".join("%s: %s" % kv for kv in sorted(v.items())) if isinstance(v, dict) \
            else ", ".join(map(str, v))
    return str(v)


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return out + ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows]


def by_id(rows):
    return {r["item_id"]: r for r in rows}


def build(items, reqs, grade, grade_s, agr, agr_s, cal):
    gh, gb = grade
    gsh, gsb = grade_s
    ah, ab = agr
    ash, asb = agr_s
    ch, cb = cal
    out = ["# B4 report", ""]
    out += ["## 1. Item set present, by arm", ""]
    out += table(["item_id", "arm", "source", "branches_stated"],
                 [(i["item_id"], i["arm"], i["source"], i["branches_stated"]) for i in items])
    recs = sorted({r["reconstructor_id"] for r in reqs})
    out += ["", "## 2. Reconstructors", "", "count: %d (%s)" % (len(recs), ", ".join(recs)), "",
            "Separation: each reconstructor received one file per item holding the field "
            "text_verbatim and nothing else (reconstruct.py re-reads every file it writes and "
            "refuses any other field). No example requirement, category list, prior run, or "
            "other reconstructor's output was in that file. Requirement lists arrived as rows "
            "keyed by reconstructor_id and were joined only by the external matching pass "
            "named in section 9."]
    layers = Counter(r["layer"] for r in reqs)
    out += ["", "## 3. Requirement counts and layer strings as returned", "",
            "total requirements: %d" % len(reqs), ""]
    out += table(["item_id", "n_requirements", "n_reconstructors", "layer_counts"],
                 [(g["item_id"], g["n_requirements"], g["n_reconstructors"], g["layer_counts"]) for g in gb])
    out += ["", "layer strings, all items:", ""] + table(["layer", "count"], sorted(layers.items()))
    st = Counter(r["status"] for r in reqs)
    out += ["", "## 4. Status distribution", ""]
    out += table(["status", "count"], [(s, st.get(s, 0)) for s in req_mod.STATUSES])
    out += [""] + table(["item_id", "status_counts"], [(g["item_id"], g["status_counts"]) for g in gb])
    out += ["", "## 5. Policy-to-physical ratio", "",
            "derived from settling_test; physical terms: %s; policy terms: %s" % (
                fmt(gh["physical_terms"]), fmt(gh["policy_terms"])), ""]
    out += table(["item_id", "physical", "policy", "unresolved", "policy_to_physical", "unresolved_req_ids"],
                 [(g["item_id"], g["physical"], g["policy"], g["unresolved"], g["policy_to_physical"],
                   g["unresolved_req_ids"]) for g in gb])
    out += ["", "## 6. Agreement", ""]
    out += table(["item_id", "n_reconstructors", "n_classes", "pairwise_agreement", "full_disagreement",
                  "n_singletons"],
                 [(a["item_id"], a["n_reconstructors"], a["n_classes"], a["pairwise_agreement"],
                   a["full_disagreement"], a["n_singletons"]) for a in ab])
    out += ["", "singleton set (returned by exactly one reconstructor; kept in full):", ""]
    singles = [(a["item_id"], s["req_id"], s["reconstructor_id"], s["requirement_text"], s["settling_test"])
               for a in ab for s in a["singletons"]]
    out += table(["item_id", "req_id", "reconstructor_id", "requirement_text", "settling_test"], singles) \
        if singles else ["(none)"]
    out += ["", "## 7. REAL vs SHUFFLED", "", "shuffle seed: %s; matches cross-item after shuffle: %s" % (
        gsh.get("seed"), ash["matches_cross_item"]), ""]
    gs, as_ = by_id(gsb), by_id(asb)
    ar = by_id(ab)
    out += table(["item_id", "real n_req", "shuf n_req", "real ratio", "shuf ratio", "real agreement",
                  "shuf agreement", "real full_disagreement", "shuf full_disagreement",
                  "real singletons", "shuf singletons"],
                 [(g["item_id"], g["n_requirements"], gs.get(g["item_id"], {}).get("n_requirements"),
                   g["policy_to_physical"], gs.get(g["item_id"], {}).get("policy_to_physical"),
                   ar.get(g["item_id"], {}).get("pairwise_agreement"),
                   as_.get(g["item_id"], {}).get("pairwise_agreement"),
                   ar.get(g["item_id"], {}).get("full_disagreement"),
                   as_.get(g["item_id"], {}).get("full_disagreement"),
                   ar.get(g["item_id"], {}).get("n_singletons"),
                   as_.get(g["item_id"], {}).get("n_singletons")) for g in gb])
    out += ["", "## 8. Calibration arm", ""]
    if ch is None:
        out += ["no calibration file supplied"]
    elif not cb:
        out += ["no documented items (items skipped: %s)" % ch["items_skipped"]]
    else:
        out += table(["item_id", "n_factors", "recovered", "missed", "beyond_report", "beyond_report_ids"],
                     [(c["item_id"], c["n_factors"], c["recovered"], c["missed"], c["beyond_report"],
                       c["beyond_report_ids"]) for c in cb])
    out += ["", "## 9. match_source", ""]
    out += table(["file", "match_source"],
                 [("agreement", ah["match_source"]), ("agreement_shuffled", ash["match_source"])]
                 + ([("calibration", ch["match_source"])] if ch else []))
    return "\n".join(out) + "\n"


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="B4 report")
    p.add_argument("output")
    p.add_argument("--items", nargs="+", required=True)
    for n in ("requirements", "grade", "grade-shuffled", "agreement", "agreement-shuffled"):
        p.add_argument("--" + n, required=True)
    p.add_argument("--calibration")
    a = p.parse_args(argv)
    inputs = a.items + [a.requirements, a.grade, a.grade_shuffled, a.agreement,
                        a.agreement_shuffled, a.calibration]

    def run():
        items = [i for path in a.items for i in items_mod.load_items(path)]
        reqs = req_mod.load_requirements(a.requirements)
        text = build(items, reqs, load_output(a.grade, "n_requirements"),
                     load_output(a.grade_shuffled, "n_requirements"),
                     load_output(a.agreement, "n_classes"),
                     load_output(a.agreement_shuffled, "n_classes"),
                     load_output(a.calibration, "recovered"))
        os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        return "ok", {"items": len(items), "requirements": len(reqs)}, ""

    return rr.execute("b4/report.py", vars(a), inputs, a.output, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
