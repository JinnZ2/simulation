"""B1.5 -- report.md from the real and permuted summaries.

    python3 report.py summary_real.jsonl summary_permuted.jsonl report.md

Six sections, in order, no others. The permuted result is a second output,
never a gate: both are printed or the report is not written. A missing
permuted summary exits with status void and still writes its run record.

Null triggers (section 6) use the thresholds declared below. Each is
printed with the number that triggered it or the number that did not.
N5 (top-k sensitivity of the entropy ordering) cannot be evaluated from a
separations file, which carries one entropy per position; it is printed
as not evaluable rather than silently omitted.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runrecord import SchemaError, main_guard, read_jsonl  # noqa: E402

N1_RESYNC_FLOOR = 0.9      # N1 if every cell's resync_rate >= this
N2_OVERLAP_FLOOR = 0.9     # N2 if every cell's ent_div_overlap >= this
N3_STABILITY_FLOOR = 0.5   # N3 if any adjacent-D or adjacent-L Jaccard < this
N4_MARGIN = 0.1            # N4 if permuted mean stability >= real mean stability - this


def _load(path):
    rows = read_jsonl(path)
    cases = [r for r in rows if r.get("kind") == "cases"]
    if len(cases) != 1:
        raise SchemaError(f"{Path(path).name}: expected exactly one 'cases' row, found {len(cases)}")
    return cases[0], [r for r in rows if r.get("kind") == "cell"], [r for r in rows if r.get("kind") == "stability"]


def _fmt(x) -> str:
    return f"{x:.3f}" if isinstance(x, float) else str(x)


def _table(header, rows) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_fmt(v) for v in r) + " |" for r in rows]
    return lines


def _sweep(cells, axis, other) -> list[list]:
    """Rows of (axis value, other value, model, n, mean_div, resync, n_top) sorted by axis."""
    key = (lambda c: (c[axis], c[other], c["model_id"]))
    return [[c[axis], c[other], c["model_id"], c["n_rows"], c["mean_div"], c["resync_rate"], c["n_top_decile"]]
            for c in sorted(cells, key=key)]


def _mean(xs) -> float | None:
    return round(sum(xs) / len(xs), 6) if xs else None


def nulls(cells, stab, p_stab) -> list[tuple[str, bool, str]]:
    out = []
    resync_min = min((c["resync_rate"] for c in cells), default=None)
    out.append(("N1 separations land only on wording",
                resync_min is not None and resync_min >= N1_RESYNC_FLOOR,
                f"min resync_rate over cells = {_fmt(resync_min)} (trigger >= {N1_RESYNC_FLOOR})"))
    ov_min = min((c["ent_div_overlap"] for c in cells), default=None)
    out.append(("N2 every high-entropy position separates",
                ov_min is not None and ov_min >= N2_OVERLAP_FLOOR,
                f"min ent_div_overlap over cells = {_fmt(ov_min)} (trigger >= {N2_OVERLAP_FLOOR})"))
    j_min = min((s["jaccard"] for s in stab), default=None)
    out.append(("N3 results depend on D or on L",
                j_min is not None and j_min < N3_STABILITY_FLOOR,
                f"min adjacent Jaccard = {_fmt(j_min)} (trigger < {N3_STABILITY_FLOOR})"))
    real_m, perm_m = _mean([s["jaccard"] for s in stab]), _mean([s["jaccard"] for s in p_stab])
    fired = real_m is not None and perm_m is not None and perm_m >= real_m - N4_MARGIN
    out.append(("N4 permuted run clusters as well as the real run", fired,
                f"mean stability real = {_fmt(real_m)}, permuted = {_fmt(perm_m)} (trigger permuted >= real - {N4_MARGIN})"))
    out.append(("N5 top-k truncation changes the entropy ordering", False,
                "not evaluable from separations.jsonl; needs base.jsonl with entropy under both bases"))
    return out


def render(real, perm) -> str:
    cases, cells, stab = real
    p_cases, p_cells, p_stab = perm
    L = ["# Runner-up trace report", ""]
    L += ["## 1. Counts and case set", "",
          f"- rows: {cases['n_rows']} real, {p_cases['n_rows']} permuted",
          f"- cases ({len(cases['case_ids'])}): " + ", ".join(cases["case_ids"]),
          f"- models ({len(cases['model_ids'])}): " + ", ".join(cases["model_ids"]),
          f"- D values: {cases['D_values']}", f"- L values: {cases['L_values']}", ""]
    head = ["D", "L", "model", "n", "mean_div", "resync", "n_top"]
    L += ["## 2. D sweep", ""] + _table(head, _sweep(cells, "D", "L")) + [""]
    L += ["## 3. L sweep", ""] + _table(["L", "D", "model", "n", "mean_div", "resync", "n_top"], _sweep(cells, "L", "D")) + [""]
    shead = ["axis", "model", "fixed", "from", "to", "jaccard"]
    srows = [[s["axis"], s["model_id"], s.get("L", s.get("D")), s["from"], s["to"], s["jaccard"]] for s in stab]
    L += ["## 4. Stability overlaps", ""] + _table(shead, srows) + [""]
    L += ["## 5. Real vs permuted", "", "Real:", ""] + _table(head, _sweep(cells, "D", "L"))
    L += ["", "Permuted:", ""] + _table(head, _sweep(p_cells, "D", "L"))
    prows = [[s["axis"], s["model_id"], s.get("L", s.get("D")), s["from"], s["to"], s["jaccard"]] for s in p_stab]
    L += ["", "Real stability:", ""] + _table(shead, srows) + ["", "Permuted stability:", ""] + _table(shead, prows) + [""]
    L += ["## 6. Nulls triggered", ""]
    for name, fired, number in nulls(cells, stab, p_stab):
        L.append(f"- {'TRIGGERED' if fired else 'not triggered'} -- {name}: {number}")
    return "\n".join(L) + "\n"


def _body(args):
    if not Path(args[1]).is_file():
        return "void", {}, f"permuted summary missing: {args[1]}; report not written"
    real, perm = _load(args[0]), _load(args[1])
    text = render(real, perm)
    Path(args[2]).write_text(text, encoding="utf-8")
    fired = sum(1 for _, f, _ in nulls(real[1], real[2], perm[2]) if f)
    return "ok", {"cells": len(real[1]), "stability": len(real[2]), "nulls_triggered": fired}, ""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ["<in:summary_real.jsonl>", "<in:summary_permuted.jsonl>", "<out:report.md>"]
    return main_guard("report", argv, names, None, _body)


if __name__ == "__main__":
    sys.exit(main())
