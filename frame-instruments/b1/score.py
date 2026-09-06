"""B1.2 - separation scoring. One row per (trace, D, L).

Row: case_id, model_id, i, branch_rank, D, L, ent_i, gap_i, resync_D, div_D
  gap_i    = logprob_taken - logprob of the forced branch at i
  resync_D = 1 if some L-token window of the continuation (truncated at D)
             occurs contiguously in the base continuation (truncated at D)
  div_D    = Levenshtein distance over tokens / max length, both truncated at D
D is swept over DS, L over LS; both are written into every row.

Command: python3 score.py base.jsonl traces.jsonl separations.jsonl
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import schema  # noqa: E402

DS = (8, 16, 32, 64, 128)
LS = (2, 4, 8)


def contains(seq, window):
    n = len(window)
    return any(seq[k:k + n] == window for k in range(len(seq) - n + 1))


def resync(cont, base, D, L):
    c, b = cont[:D], base[:D]
    for j in range(L, len(c) + 1):
        if contains(b, c[j - L:j]):
            return 1
    return 0


def levenshtein(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def div(cont, base, D):
    a, b = cont[:D], base[:D]
    m = max(len(a), len(b))
    return round(levenshtein(a, b) / m, 6) if m else 0.0


def branch_logprob(base_row, token):
    for t, lp in base_row["topk"]:
        if t == token:
            return lp
    raise rr.Reject("forced_token %r not in topk" % token)


def score(base, traces, ds=DS, ls=LS):
    rows = []
    for t in traces:
        b = base[(t["case_id"], t["model_id"], t["i"])]
        gap = b["logprob_taken"] - branch_logprob(b, t["forced_token"])
        for D in ds:
            for L in ls:
                rows.append({
                    "case_id": t["case_id"], "model_id": t["model_id"], "i": t["i"],
                    "branch_rank": t["branch_rank"], "D": D, "L": L,
                    "ent_i": b["entropy_i"], "gap_i": round(gap, 6),
                    "resync_D": resync(t["continuation"], t["base_continuation"], D, L),
                    "div_D": div(t["continuation"], t["base_continuation"], D),
                })
    return rows


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="score separations from traces")
    p.add_argument("base")
    p.add_argument("traces")
    p.add_argument("output")
    a = p.parse_args(argv)

    def run():
        base = schema.load_base(a.base)
        traces = schema.load_traces(a.traces, base)
        rows = score(base, traces)
        rr.write_jsonl(a.output, rows)
        bases = sorted({r["entropy_basis"] for r in base.values()})
        counts = {"trace_rows": len(traces), "rows": len(rows),
                  "entropy_bases": bases}
        return ("ok" if rows else "empty"), counts, "D=%s L=%s" % (list(DS), list(LS))

    return rr.execute("b1/score.py", vars(a), [a.base, a.traces], a.output, None,
                      run, runs_path)


if __name__ == "__main__":
    sys.exit(main())
