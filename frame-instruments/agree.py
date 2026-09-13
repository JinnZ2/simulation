"""B2.4 -- agreement across independent auditors. No correctness score.

    python3 agree.py audits.jsonl cases.jsonl agreement.jsonl

audits.jsonl rows: reader_id, case_id, condition, posed, target
  condition is A, B, C, D1 (locked call before the key) or D2 (after).

Output rows, by "kind", in this order:
  order_check  A vs D1 on posed: within-A pairwise agreement against
               A-to-D1 cross agreement. Same information, so they must
               match; a gap wider than ORDER_MARGIN means order effects are
               live and C is uninterpretable. Printed first, in the file
               and on stdout.
  anchoring    key-ratification rate under C against D1 and D2, and the
               D1->D2 switch-to-key rate.
  cell         per (case_id, condition): n_auditors, agree_posed,
               agree_target, full_disagreement, ratify_key, arm if the
               case carries one.

Ratification is (posed, target) equal to the key's; it is a comparison
with the artifact under test, not a correctness score.

Every output row carries match_source: who or what decided that two
calls match. Here it is "exact" (string equality). b4/agreement.py, which
wraps this module, passes the external matcher's name instead. The
matcher is a frame entry point and has to be visible in the record.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conditions import load_cases  # noqa: E402
from runrecord import SchemaError, main_guard, read_jsonl, write_jsonl  # noqa: E402

AUDIT_FIELDS = ("reader_id", "case_id", "condition", "posed", "target")
CONDITIONS = ("A", "B", "C", "D1", "D2")
ORDER_MARGIN = 0.2


def load_audits(path) -> list[dict]:
    rows = read_jsonl(path)
    name = Path(path).name
    for n, r in enumerate(rows, 1):
        for f in AUDIT_FIELDS:
            if f not in r:
                raise SchemaError(f"{name} line {n}: missing field '{f}'")
            if not isinstance(r[f], str):
                raise SchemaError(f"{name} line {n}: field '{f}' must be a string")
        for f in r:
            if f not in AUDIT_FIELDS:
                raise SchemaError(f"{name} line {n}: unexpected field '{f}'")
        if r["condition"] not in CONDITIONS:
            raise SchemaError(f"{name} line {n}: field 'condition' must be one of {CONDITIONS}")
    return rows


def pairwise(values) -> float | None:
    pairs = list(combinations(values, 2))
    return None if not pairs else sum(a == b for a, b in pairs) / len(pairs)


def cross(xs, ys) -> float | None:
    pairs = [(x, y) for x in xs for y in ys]
    return None if not pairs else sum(x == y for x, y in pairs) / len(pairs)


def _mean(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 6) if xs else None


def _r(x):
    return None if x is None else round(x, 6)


def cells(audits, keys) -> list[dict]:
    groups = defaultdict(list)
    for a in audits:
        groups[(a["case_id"], a["condition"])].append(a)
    out = []
    for (case, cond) in sorted(groups):
        g = groups[(case, cond)]
        posed = [a["posed"] for a in g]
        target = [a["target"] for a in g]
        ap = pairwise(posed)
        key = keys.get(case)
        ratify = None if key is None else sum((a["posed"], a["target"]) == key["kt"] for a in g) / len(g)
        row = {"kind": "cell", "case_id": case, "condition": cond, "n_auditors": len(g),
               "agree_posed": _r(ap), "agree_target": _r(pairwise(target)),
               "full_disagreement": int(ap == 0.0) if ap is not None else None,
               "ratify_key": _r(ratify)}
        if key is not None and key.get("arm") is not None:
            row["arm"] = key["arm"]
        out.append(row)
    return out


def order_check(audits) -> dict:
    by = defaultdict(lambda: defaultdict(list))
    for a in audits:
        by[a["case_id"]][a["condition"]].append(a["posed"])
    within, across = [], []
    for case in sorted(by):
        A, D1 = by[case].get("A", []), by[case].get("D1", [])
        within.append(pairwise(A))
        across.append(cross(A, D1))
    w, x = _mean(within), _mean(across)
    gap = None if w is None or x is None else round(w - x, 6)
    return {"kind": "order_check", "within_A": w, "A_vs_D1": x, "gap": gap,
            "cases": len(by), "divergent": int(gap is not None and gap > ORDER_MARGIN)}


def anchoring(audits, keys) -> dict:
    rate = defaultdict(list)
    for a in audits:
        key = keys.get(a["case_id"])
        if key is not None:
            rate[a["condition"]].append(float((a["posed"], a["target"]) == key["kt"]))
    d1 = {(a["reader_id"], a["case_id"]): (a["posed"], a["target"]) for a in audits if a["condition"] == "D1"}
    switched, paired = 0, 0
    for a in audits:
        if a["condition"] != "D2" or (a["reader_id"], a["case_id"]) not in d1:
            continue
        key = keys.get(a["case_id"])
        if key is None:
            continue
        paired += 1
        before, after = d1[(a["reader_id"], a["case_id"])], (a["posed"], a["target"])
        switched += int(before != key["kt"] and after == key["kt"])
    rc, r1, r2 = _mean(rate["C"]), _mean(rate["D1"]), _mean(rate["D2"])
    return {"kind": "anchoring", "ratify_C": rc, "ratify_D1": r1, "ratify_D2": r2,
            "C_minus_D1": None if rc is None or r1 is None else round(rc - r1, 6),
            "D1_to_D2_switched_to_key": None if not paired else round(switched / paired, 6),
            "paired_D_readers": paired}


def stamp(rows: list[dict], match_source: str) -> list[dict]:
    """Add match_source to every output row. The one field B4 adds."""
    if not isinstance(match_source, str) or not match_source.strip():
        raise SchemaError("match_source must be a non-empty string")
    for r in rows:
        r["match_source"] = match_source
    return rows


def _body(args):
    audits = load_audits(args[0])
    keys = {c["case_id"]: {"kt": (c["key_posed"], c["key_target"]), "arm": c.get("arm")}
            for c in load_cases(args[1])}
    if not audits:
        write_jsonl(args[2], [])
        return "empty", {"audits": 0}, ""
    oc = order_check(audits)
    rows = stamp([oc, anchoring(audits, keys)] + cells(audits, keys), "exact")
    write_jsonl(args[2], rows)
    head = f"order_check divergent={oc['divergent']} gap={oc['gap']}"
    return "ok", {"audits": len(audits), "cells": len(rows) - 2}, head


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return main_guard("agree", argv, ["<in:audits.jsonl>", "<in:cases.jsonl>", "<out:agreement.jsonl>"], None, _body)


if __name__ == "__main__":
    sys.exit(main())
