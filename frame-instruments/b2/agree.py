"""B2.4 - agreement across independent auditors. No correctness score.

responses.jsonl: case_id, condition, auditor_id, posed, target
  condition in A, B, C, D_pre (D before the key), D_post (D after the key)
cases.jsonl: the B2 schema; `arm` is carried into the output when present.

Output rows, keyed by shape:
  header   n_cases, n_responses, conditions, match_source, order_check
           (A vs D_pre; printed first, failure at the top)
  cell     case_id, condition, n_auditors, agree_posed, agree_target,
           full_disagreement
  a_vs_d   case_id, mode_*_A, mode_*_D_pre, cross_agree_*, diverges
  c_vs_d   case_id, ratify_rate_C, ratify_rate_D_post, n_independent,
           ratified_after_independent
  arm      arm, condition, n_cases, mean_agree_posed, mean_agree_target,
           full_disagreement_total
match_source names what decided two answers are the same (here: exact
string equality after strip+casefold). B4 supplies its own.

Command: python3 agree.py cases.jsonl responses.jsonl agreement.jsonl
"""
import argparse
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import conditions  # noqa: E402

CONDITIONS = ("A", "B", "C", "D_pre", "D_post")
EXACT = "exact_string_strip_casefold"


def norm(s):
    return s.strip().casefold()


def pairwise_agreement(values, same=lambda a, b: a == b):
    """Fraction of unordered pairs that agree; None with fewer than 2 values."""
    n = len(values)
    if n < 2:
        return None
    pairs = [(values[i], values[j]) for i in range(n) for j in range(i + 1, n)]
    return round(sum(1 for a, b in pairs if same(a, b)) / len(pairs), 6)


def jaccard(a, b):
    u = set(a) | set(b)
    return len(set(a) & set(b)) / len(u) if u else 0.0


def pairwise_set_agreement(sets):
    """Mean Jaccard over unordered pairs of sets and the count of disjoint pairs."""
    n = len(sets)
    if n < 2:
        return None, 0
    js = [jaccard(sets[i], sets[j]) for i in range(n) for j in range(i + 1, n)]
    return round(sum(js) / len(js), 6), sum(1 for j in js if j == 0.0)


def mode(values):
    if not values:
        return None
    c = Counter(values)
    top = max(c.values())
    return sorted(v for v, k in c.items() if k == top)[0]


def load_responses(path):
    out = []
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        rr.no_forbidden_fields(row, where)
        for f in ("case_id", "condition", "auditor_id", "posed", "target"):
            rr.field(row, f, where, str)
        if row["condition"] not in CONDITIONS:
            raise rr.Reject("%s: field 'condition' not in %s" % (where, CONDITIONS))
        out.append(row)
    return out


def cells(groups, arms):
    rows = []
    for (case, cond), rs in sorted(groups.items()):
        ap = pairwise_agreement([norm(r["posed"]) for r in rs])
        at = pairwise_agreement([norm(r["target"]) for r in rs])
        row = {"case_id": case, "condition": cond, "n_auditors": len(rs),
               "agree_posed": ap, "agree_target": at,
               "full_disagreement": 1 if (ap == 0.0 and at == 0.0) else 0}
        if case in arms:
            row["arm"] = arms[case]
        rows.append(row)
    return rows


def a_vs_d(groups, case_ids):
    rows = []
    for case in case_ids:
        A, D = groups.get((case, "A"), []), groups.get((case, "D_pre"), [])
        if not A or not D:
            continue
        row = {"case_id": case}
        diverges = False
        for f in ("posed", "target"):
            ma, md = mode([norm(r[f]) for r in A]), mode([norm(r[f]) for r in D])
            row["mode_%s_A" % f], row["mode_%s_D_pre" % f] = ma, md
            pairs = [(norm(x[f]), norm(y[f])) for x in A for y in D]
            row["cross_agree_%s" % f] = round(sum(1 for a, b in pairs if a == b) / len(pairs), 6)
            diverges = diverges or (ma != md)
        row["diverges"] = diverges
        rows.append(row)
    return rows


def c_vs_d(groups, cases):
    rows = []
    for case in cases:
        kp, kt = norm(case["key_posed"]), norm(case["key_target"])
        ratify = lambda r: norm(r["posed"]) == kp and norm(r["target"]) == kt  # noqa: E731
        C, Dpost = groups.get((case["case_id"], "C"), []), groups.get((case["case_id"], "D_post"), [])
        if not C and not Dpost:
            continue
        pre = {r["auditor_id"]: r for r in groups.get((case["case_id"], "D_pre"), [])}
        independent = [r for r in Dpost if r["auditor_id"] in pre and not ratify(pre[r["auditor_id"]])]
        rows.append({
            "case_id": case["case_id"],
            "ratify_rate_C": round(sum(map(ratify, C)) / len(C), 6) if C else None,
            "ratify_rate_D_post": round(sum(map(ratify, Dpost)) / len(Dpost), 6) if Dpost else None,
            "n_independent": len(independent),
            "ratified_after_independent": sum(map(ratify, independent)),
        })
    return rows


def arm_rows(cell_rows):
    by = defaultdict(list)
    for c in cell_rows:
        if "arm" in c:
            by[(c["arm"], c["condition"])].append(c)
    out = []
    for (arm, cond), cs in sorted(by.items()):
        ap = [c["agree_posed"] for c in cs if c["agree_posed"] is not None]
        at = [c["agree_target"] for c in cs if c["agree_target"] is not None]
        out.append({"arm": arm, "condition": cond, "n_cases": len(cs),
                    "mean_agree_posed": round(sum(ap) / len(ap), 6) if ap else None,
                    "mean_agree_target": round(sum(at) / len(at), 6) if at else None,
                    "full_disagreement_total": sum(c["full_disagreement"] for c in cs)})
    return out


def agreement(cases, responses, match_source=EXACT):
    groups = defaultdict(list)
    for r in responses:
        groups[(r["case_id"], r["condition"])].append(r)
    arms = {c["case_id"]: c["arm"] for c in cases if isinstance(c.get("arm"), str)}
    order = a_vs_d(groups, [c["case_id"] for c in cases])
    diverging = [o["case_id"] for o in order if o["diverges"]]
    header = {
        "n_cases": len(cases), "n_responses": len(responses),
        "conditions": dict(Counter(r["condition"] for r in responses)),
        "match_source": match_source,
        "order_check": {"compared_cases": len(order), "diverging_cases": diverging,
                        "ok": (not diverging) if order else None},
    }
    cell_rows = cells(groups, arms)
    return [header] + cell_rows + order + c_vs_d(groups, cases) + arm_rows(cell_rows)


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="agreement across auditors")
    p.add_argument("cases")
    p.add_argument("responses")
    p.add_argument("output")
    a = p.parse_args(argv)

    def run():
        cases = conditions.load_cases(a.cases)
        responses = load_responses(a.responses)
        out = agreement(cases, responses)
        rr.write_jsonl(a.output, out)
        oc = out[0]["order_check"]
        notes = "" if oc["ok"] in (True, None) else "A vs D_pre DIVERGES on %s" % oc["diverging_cases"]
        return ("ok" if responses else "empty"), {"rows": len(out), "responses": len(responses)}, notes

    return rr.execute("b2/agree.py", vars(a), [a.cases, a.responses], a.output, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
