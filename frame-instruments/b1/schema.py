"""B1.1 - validators for base.jsonl and traces.jsonl. Reject names line and field.

base.jsonl, one row per position:
    case_id, model_id, i, token_taken, logprob_taken,
    topk: [[token, logprob], ...], entropy_i, entropy_basis ("full"|"topk")
traces.jsonl, one row per forced continuation:
    case_id, model_id, i, branch_rank, forced_token,
    continuation: [token, ...] (<= 128, the tokens generated AFTER forced_token),
    base_continuation: [token, ...] (same length, the tokens after token_taken)

Command: python3 schema.py base.jsonl traces.jsonl
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402

MAX_CONT = 128
ENTROPY_BASES = ("full", "topk")


def _key(row):
    return (row["case_id"], row["model_id"], row["i"])


def _token_list(row, name, where):
    v = rr.field(row, name, where, list)
    for k, t in enumerate(v):
        if not isinstance(t, str):
            raise rr.Reject("%s: field %r[%d] is not a string" % (where, name, k))
    return v


def validate_base_row(row, where):
    rr.no_forbidden_fields(row, where)
    rr.field(row, "case_id", where, str)
    rr.field(row, "model_id", where, str)
    if rr.field(row, "i", where, int) < 0:
        raise rr.Reject("%s: field 'i' is negative" % where)
    rr.field(row, "token_taken", where, str)
    rr.field(row, "logprob_taken", where, rr.NUMBER)
    topk = rr.field(row, "topk", where, list)
    if not topk:
        raise rr.Reject("%s: field 'topk' is empty" % where)
    for k, pair in enumerate(topk):
        if (not isinstance(pair, list) or len(pair) != 2
                or not isinstance(pair[0], str)
                or isinstance(pair[1], bool) or not isinstance(pair[1], rr.NUMBER)):
            raise rr.Reject("%s: field 'topk'[%d] is not [token, logprob]" % (where, k))
    if rr.field(row, "entropy_i", where, rr.NUMBER) < 0:
        raise rr.Reject("%s: field 'entropy_i' is negative" % where)
    if rr.field(row, "entropy_basis", where, str) not in ENTROPY_BASES:
        raise rr.Reject("%s: field 'entropy_basis' not in %s" % (where, ENTROPY_BASES))
    return row


def validate_trace_row(row, where, base):
    rr.no_forbidden_fields(row, where)
    rr.field(row, "case_id", where, str)
    rr.field(row, "model_id", where, str)
    rr.field(row, "i", where, int)
    if rr.field(row, "branch_rank", where, int) < 1:
        raise rr.Reject("%s: field 'branch_rank' < 1" % where)
    forced = rr.field(row, "forced_token", where, str)
    cont = _token_list(row, "continuation", where)
    basec = _token_list(row, "base_continuation", where)
    if len(cont) > MAX_CONT:
        raise rr.Reject("%s: field 'continuation' longer than %d" % (where, MAX_CONT))
    if len(basec) != len(cont):
        raise rr.Reject("%s: field 'base_continuation' length differs from "
                        "'continuation'" % where)
    b = base.get(_key(row))
    if b is None:
        raise rr.Reject("%s: field 'i' has no base row for (case_id, model_id, i)" % where)
    if forced not in [t for t, _ in b["topk"]]:
        raise rr.Reject("%s: field 'forced_token' not in the base row's topk" % where)
    return row


def load_base(path):
    """Return {(case_id, model_id, i): row}. Duplicates are rejected."""
    out = {}
    for n, row in rr.read_jsonl(path):
        where = "%s:%d" % (os.path.basename(path), n)
        validate_base_row(row, where)
        k = _key(row)
        if k in out:
            raise rr.Reject("%s: field 'i' duplicates an earlier row" % where)
        out[k] = row
    return out


def load_traces(path, base):
    return [validate_trace_row(row, "%s:%d" % (os.path.basename(path), n), base)
            for n, row in rr.read_jsonl(path)]


def main(argv=None, runs_path=None):
    p = argparse.ArgumentParser(description="validate base.jsonl and traces.jsonl")
    p.add_argument("base")
    p.add_argument("traces")
    a = p.parse_args(argv)

    def run():
        base = load_base(a.base)
        traces = load_traces(a.traces, base)
        counts = {"base_rows": len(base), "trace_rows": len(traces)}
        return ("ok" if traces else "empty"), counts, ""

    return rr.execute("b1/schema.py", vars(a), [a.base, a.traces], "", None, run,
                      runs_path)


if __name__ == "__main__":
    sys.exit(main())
