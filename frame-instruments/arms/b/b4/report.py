"""B4.8 -- report.md from everything. Nine sections, in order, no others.

    python3 report.py items_hypothetical.jsonl items_documented.jsonl requirements.jsonl \
        grades.jsonl agreement.jsonl grades_shuffled.jsonl agreement_shuffled.jsonl \
        calibration.jsonl report.md

Either items file may be absent (that arm is then reported as not
supplied); calibration.jsonl may be absent (section 8 says so). The
shuffled grades and agreement are a second output, never a gate: if
either is missing this exits void and writes no report.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from grade import PHYSICAL, POLICY  # noqa: E402
from items import load_items  # noqa: E402
from requirements import STATUSES, load_requirements  # noqa: E402
from runrecord import main_guard, read_jsonl  # noqa: E402

SEPARATION = ("Each reconstructor received one file per item from reconstruct.py holding "
              "text_verbatim and no other field: no other reconstructor's output, no example "
              "requirement, no category list, no prior run. Matching between reconstructors was "
              "done outside the scripts and is named in section 9.")


def _fmt(x) -> str:
    return "null" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def _table(header, rows) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_fmt(v) for v in r) + " |" for r in rows]
    return lines + [""]


def _optional(path, loader):
    return loader(path) if Path(path).is_file() else None


def _grade_rows(grades) -> list[list]:
    return [[g["item_id"], g["n_requirements"], g["physical"], g["policy"], g["unresolved"],
             g["unresolved_neither"], g["unresolved_both"], g["ratio_policy_to_physical"]] for g in grades]


def _agree_rows(items) -> list[list]:
    return [[a["item_id"], a["n_reconstructors"], a["n_requirements"], a["n_clusters"], a["n_shared_clusters"],
             a["pairwise_agreement"], a["full_disagreement"], a["n_singletons"]] for a in items]


GHEAD = ["item", "n_req", "physical", "policy", "unresolved", "neither", "both", "policy/physical"]
AHEAD = ["item", "reconstructors", "n_req", "clusters", "shared", "pairwise", "full_disagree", "singletons"]


def render(hyp, doc, reqs, grades, agree, s_grades, s_agree, calib) -> str:
    L = ["# Dilemma reconstruction report", ""]
    L += ["## 1. Item set by arm", ""]
    for arm, items in (("hypothetical", hyp), ("documented", doc)):
        if items is None:
            L.append(f"- {arm}: not supplied")
        else:
            L.append(f"- {arm}: {len(items)} item(s)")
            L += [f"  - {it['item_id']} ({it['branches_stated']} branches stated) -- {it['source']}" for it in items]
    L.append("")
    recs = sorted({r["reconstructor_id"] for r in reqs})
    L += ["## 2. Reconstructors", "", f"- count: {len(recs)} ({', '.join(recs)})", f"- separation: {SEPARATION}", ""]
    L += ["## 3. Requirement counts and layers as returned", "", f"- requirements: {len(reqs)} across {len(grades)} item(s)", ""]
    L += _table(["layer (verbatim)", "count"], sorted(Counter(r["layer"] for r in reqs).items(), key=lambda kv: (-kv[1], kv[0])))
    L += ["## 4. Status distribution", ""]
    L += _table(["item"] + list(STATUSES), [[g["item_id"]] + [g["status"][s] for s in STATUSES] for g in grades])
    L += ["## 5. Policy-to-physical ratio per item", "",
          f"Split derived from settling_test by two lexicons (physical: {len(PHYSICAL)} terms; policy: {len(POLICY)} terms), "
          "never asked for. unresolved = neither lexicon matched, or both did.", ""] + _table(GHEAD, _grade_rows(grades))
    a_items = [a for a in agree if a["kind"] == "item"]
    singles = [a for a in agree if a["kind"] == "singleton"]
    L += ["## 6. Agreement", ""] + _table(AHEAD, _agree_rows(a_items))
    L += ["Singleton set, in full (returned by exactly one reconstructor; kept, not discarded):", ""]
    L += [f"- {s['item_id']} / {s['reconstructor_id']} / {s['req_id']} [{s['layer']}]: {s['requirement_text']} "
          f"-- settled by: {s['settling_test']}" for s in singles] or ["- (none)"]
    L.append("")
    sa_items = [a for a in s_agree if a["kind"] == "item"]
    L += ["## 7. Real vs shuffled", "", "Real agreement:", ""] + _table(AHEAD, _agree_rows(a_items))
    L += ["Shuffled agreement:", ""] + _table(AHEAD, _agree_rows(sa_items))
    L += ["Real grades:", ""] + _table(GHEAD, _grade_rows(grades)) + ["Shuffled grades:", ""] + _table(GHEAD, _grade_rows(s_grades))
    L += ["## 8. Calibration arm", ""]
    if calib is None:
        L += ["- no calibration run supplied", ""]
    else:
        head = ["item", "reconstructor", "named", "recovered", "missed", "beyond_report", "n_req"]
        rows = [[c["item_id"], c.get("reconstructor_id", "(pooled)"), c["named_factors"], c["recovered"], c["missed"],
                 c["beyond_report"], c["n_requirements"]] for c in calib]
        L += _table(head, rows) + ["beyond_report is printed, not scored: a reconstruction may reach a node the investigation did not.", ""]
    sources = sorted({r.get("match_source") for r in agree + (calib or []) if r.get("match_source")})
    L += ["## 9. match_source", ""] + [f"- {s}" for s in sources] + [""]
    return "\n".join(L)


def _body(args):
    missing = [a for a in (args[5], args[6]) if not Path(a).is_file()]
    if missing:
        return "void", {}, f"shuffled output missing: {missing[0]}; report not written"
    hyp, doc = _optional(args[0], load_items), _optional(args[1], load_items)
    reqs = load_requirements(args[2])
    grades, agree = read_jsonl(args[3]), read_jsonl(args[4])
    s_grades, s_agree = read_jsonl(args[5]), read_jsonl(args[6])
    calib = _optional(args[7], read_jsonl)
    Path(args[8]).write_text(render(hyp, doc, reqs, grades, agree, s_grades, s_agree, calib), encoding="utf-8")
    counts = {"items": len(grades), "requirements": len(reqs),
              "singletons": sum(1 for a in agree if a["kind"] == "singleton"), "calibrated": 0 if calib is None else 1}
    return "ok", counts, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:items_hypothetical.jsonl>", "<in:items_documented.jsonl>", "<in:requirements.jsonl>",
             "<in:grades.jsonl>", "<in:agreement.jsonl>", "<in:grades_shuffled.jsonl>",
             "<in:agreement_shuffled.jsonl>", "<in:calibration.jsonl>", "<out:report.md>"]
    return main_guard("b4.report", argv, names, None, _body)


if __name__ == "__main__":
    sys.exit(main())
