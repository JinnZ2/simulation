"""B1.5 - report.md from the real and permuted summaries. Six sections, in
order, no others. The permuted result is a second output, never a gate: if
the permuted summary is missing the run is `void` and no report is written.

N1-N5 thresholds are arguments, printed with the numbers they gate.

Command: python3 report.py summary_real.jsonl summary_permuted.jsonl report.md
         [--base base.jsonl ...] [--n1 0.9 --n2 0.95 --n3 0.5 --n4 0.5 --n5 0.5]
"""
import argparse
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import schema  # noqa: E402
import summarise  # noqa: E402


def load_summary(path):
    if not os.path.exists(path):
        raise rr.Void("summary missing: %s" % os.path.basename(path))
    rows = [r for _, r in rr.read_jsonl(path)]
    if not rows or "n_rows" not in rows[0]:
        raise rr.Reject("%s:1: field 'n_rows' missing (no header row)" % path)
    cells = [r for r in rows if "n" in r]
    stab = [r for r in rows if "jaccard" in r]
    return rows[0], cells, stab


def fmt(v):
    if v is None:
        return "-"
    return "%.3f" % v if isinstance(v, float) else str(v)


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows]
    return out


def sweep(cells, first, second):
    return table(["model_id", first, second, "n", "mean_div", "resync_rate",
                  "top_decile_positions"],
                 [(c["model_id"], c[first], c[second], c["n"], c["mean_div"],
                   c["resync_rate"], c["top_decile_positions"])
                  for c in sorted(cells, key=lambda c: (c["model_id"], c[first], c[second]))])


def stability_table(stab):
    rows = []
    for s in stab:
        if "D_a" in s:
            rows.append((s["model_id"], "D", s["L"], s["D_a"], s["D_b"], s["jaccard"]))
        else:
            rows.append((s["model_id"], "L", s["D"], s["L_a"], s["L_b"], s["jaccard"]))
    return table(["model_id", "axis", "held", "a", "b", "jaccard"], rows)


def side_by_side(real, perm):
    pc = {(c["model_id"], c["D"], c["L"]): c for c in perm}
    rows = []
    for c in sorted(real, key=lambda c: (c["model_id"], c["D"], c["L"])):
        q = pc.get((c["model_id"], c["D"], c["L"]), {})
        rows.append((c["model_id"], c["D"], c["L"], c["mean_div"], q.get("mean_div"),
                     c["resync_rate"], q.get("resync_rate"),
                     c["top_decile_positions"], q.get("top_decile_positions")))
    return table(["model_id", "D", "L", "real mean_div", "perm mean_div",
                  "real resync", "perm resync", "real top-decile", "perm top-decile"], rows)


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def n5_number(base_paths):
    """Jaccard of top-decile entropy position sets between entropy bases."""
    by_basis = defaultdict(list)
    for path in base_paths:
        for row in schema.load_base(path).values():
            by_basis[row["entropy_basis"]].append(
                (row["entropy_i"], "%s:%s:%d" % (row["case_id"], row["model_id"], row["i"])))
    if len(by_basis) < 2:
        return None, sorted((k, len(v)) for k, v in by_basis.items())
    sets = [summarise.top_decile(v)[0] for _, v in sorted(by_basis.items())]
    return summarise.jaccard(sets[0], sets[1]), sorted((k, len(v)) for k, v in by_basis.items())


def nulls(real_cells, real_stab, perm_stab, a):
    dmax = max(c["D"] for c in real_cells) if real_cells else None
    n1 = min((c["resync_rate"] for c in real_cells), default=None)
    n2 = min((c["sep_rate_high_ent"] for c in real_cells
              if c["D"] == dmax and c["sep_rate_high_ent"] is not None), default=None)
    n3 = min((s["jaccard"] for s in real_stab if "D_a" in s), default=None)
    rm, pm = mean(s["jaccard"] for s in real_stab), mean(s["jaccard"] for s in perm_stab)
    n4 = (pm / rm) if (rm not in (None, 0) and pm is not None) else None
    n5, bases = n5_number(a.base or [])
    rows = [
        ("N1", "min resync_rate over cells", n1, ">= %.2f" % a.n1,
         n1 is not None and n1 >= a.n1),
        ("N2", "min sep_rate_high_ent at D=%s" % dmax, n2, ">= %.2f" % a.n2,
         n2 is not None and n2 >= a.n2),
        ("N3", "min adjacent-D jaccard (N not swept offline)", n3, "< %.2f" % a.n3,
         n3 is not None and n3 < a.n3),
        ("N4", "perm/real mean stability jaccard (real=%s)" % fmt(rm), n4,
         ">= %.2f" % a.n4, n4 is not None and n4 >= a.n4),
        ("N5", "entropy top-decile jaccard across bases %s" % bases, n5,
         "< %.2f" % a.n5, n5 is not None and n5 < a.n5),
    ]
    return table(["null", "number", "value", "triggers when", "triggered"],
                 [(k, d, v, t, ("yes" if f else ("no" if v is not None else "not assessable")))
                  for k, d, v, t, f in rows])


def build(real, perm, a):
    rh, rc, rs = real
    ph, pc, ps = perm
    out = ["# B1 report", ""]
    out += ["## 1. Counts and case set", "",
            "| file | rows | positions | cases | models | seed |", "|---|---|---|---|---|---|"]
    for h in (rh, ph):
        out.append("| %s | %d | %d | %s | %s | %s |" % (
            h["source"], h["n_rows"], h["positions"], ", ".join(h["cases"]),
            ", ".join(h["models"]), h["seed"]))
    out += ["", "## 2. D sweep", ""] + sweep(rc, "D", "L")
    out += ["", "## 3. L sweep", ""] + sweep(rc, "L", "D")
    out += ["", "## 4. Stability overlaps", ""] + stability_table(rs)
    out += ["", "## 5. REAL vs PERMUTED", ""] + side_by_side(rc, pc)
    out += ["", "stability (adjacent D and L) real vs permuted:", ""]
    out += table(["file", "mean jaccard", "min jaccard"],
                 [(rh["source"], mean(s["jaccard"] for s in rs), min((s["jaccard"] for s in rs), default=None)),
                  (ph["source"], mean(s["jaccard"] for s in ps), min((s["jaccard"] for s in ps), default=None))])
    out += ["", "## 6. NULLS TRIGGERED", ""] + nulls(rc, rs, ps, a)
    return "\n".join(out) + "\n"


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="B1 report from two summaries")
    p.add_argument("real")
    p.add_argument("permuted")
    p.add_argument("output")
    p.add_argument("--base", nargs="*", default=[])
    for k, d in (("n1", 0.9), ("n2", 0.95), ("n3", 0.5), ("n4", 0.5), ("n5", 0.5)):
        p.add_argument("--" + k, type=float, default=d)
    a = p.parse_args(argv)

    def run():
        real = load_summary(a.real)
        perm = load_summary(a.permuted)
        text = build(real, perm, a)
        os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        return "ok", {"real_cells": len(real[1]), "perm_cells": len(perm[1])}, ""

    return rr.execute("b1/report.py", vars(a), [a.real, a.permuted] + list(a.base),
                      a.output, None, run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
