"""B1 tests. stdlib unittest, synthetic fixtures in-file, no network."""
import json
import os
import sys
import tempfile
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import permute  # noqa: E402
import report  # noqa: E402
import schema  # noqa: E402
import score  # noqa: E402
import summarise  # noqa: E402

T = ["t%d" % k for k in range(128)]   # base continuation tokens
G = ["g%d" % k for k in range(128)]   # tokens that never occur in the base


def base_row(i=0, case="c1", model="m1", ent=1.0, basis="full"):
    return {"case_id": case, "model_id": model, "i": i, "token_taken": "a",
            "logprob_taken": -0.1, "topk": [["a", -0.1], ["b", -2.0], ["c", -3.0]],
            "entropy_i": ent, "entropy_basis": basis}


def trace_row(cont, i=0, case="c1", model="m1", rank=2, token="b"):
    return {"case_id": case, "model_id": model, "i": i, "branch_rank": rank,
            "forced_token": token, "continuation": cont,
            "base_continuation": T[:len(cont)]}


def rows_for(cont, **kw):
    b = base_row(**{k: v for k, v in kw.items() if k in ("i", "case", "model", "ent")})
    t = trace_row(cont, **{k: v for k, v in kw.items() if k in ("i", "case", "model")})
    return score.score({(b["case_id"], b["model_id"], b["i"]): b}, [t])


class Resync(unittest.TestCase):
    def test_rejoins_immediately(self):
        for r in rows_for(list(T)):
            self.assertEqual(r["resync_D"], 1, r)
            self.assertEqual(r["div_D"], 0.0)

    def test_never_rejoins(self):
        rows = rows_for([T[0]] + G[1:])
        for r in rows:
            self.assertEqual(r["resync_D"], 0, r)
        for L in score.LS:
            divs = [r["div_D"] for r in sorted(rows, key=lambda r: r["D"]) if r["L"] == L]
            self.assertEqual(divs, sorted(divs))
            self.assertTrue(all(x < y for x, y in zip(divs, divs[1:])), divs)

    def test_rejoin_at_token_20(self):
        for r in rows_for(G[:20] + T[20:]):
            self.assertEqual(r["resync_D"], 1 if r["D"] >= 32 else 0, r)

    def test_L_sensitivity(self):
        for r in rows_for(G[:125] + T[125:]):
            if r["D"] == 128:
                self.assertEqual(r["resync_D"], 1 if r["L"] == 2 else 0, r)

    def test_gap_and_sweep_shape(self):
        rows = rows_for(list(T))
        self.assertEqual(len(rows), len(score.DS) * len(score.LS))
        self.assertAlmostEqual(rows[0]["gap_i"], 1.9)
        self.assertEqual(set(rows[0]), {"case_id", "model_id", "i", "branch_rank", "D",
                                        "L", "ent_i", "gap_i", "resync_D", "div_D"})

    def test_levenshtein(self):
        self.assertEqual(score.levenshtein(list("kitten"), list("sitting")), 3)
        self.assertEqual(score.levenshtein([], list("ab")), 2)


class Permutation(unittest.TestCase):
    def test_preserves_count_and_multiset(self):
        rows = []
        for i in range(6):
            rows += rows_for(G[:i * 5] + T[i * 5:], i=i, ent=float(i))
        out = permute.permute(rows, seed=7)
        self.assertEqual(len(out), len(rows))
        key = lambda r: tuple(r[f] for f in permute.TUPLE)  # noqa: E731
        self.assertEqual(Counter(map(key, rows)), Counter(map(key, out)))
        for r in out:
            self.assertEqual(r["seed"], 7)
        for a, b in zip(rows, out):
            for f in permute.STRATUM + ("i",):
                self.assertEqual(a[f], b[f])
        self.assertEqual(out, permute.permute(rows, seed=7))
        self.assertNotEqual([key(r) for r in out], [key(r) for r in rows])


class Schema(unittest.TestCase):
    def test_malformed_row_rejected_and_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            base, traces, runs = [os.path.join(d, n) for n in ("b.jsonl", "t.jsonl", "runs.jsonl")]
            bad = base_row()
            del bad["entropy_basis"]
            rr.write_jsonl(base, [base_row(), dict(bad, i=1)])
            rr.write_jsonl(traces, [trace_row(list(T))])
            code = schema.main([base, traces], runs_path=runs)
            self.assertEqual(code, 1)
            with open(runs) as f:
                rec = json.loads(f.read().splitlines()[-1])
            self.assertEqual(rec["status"], "error")
            self.assertIn("b.jsonl:2", rec["notes"])
            self.assertIn("entropy_basis", rec["notes"])
            self.assertEqual(set(rec), {"run_id", "utc", "script", "arm", "args_hash",
                                        "seed", "input_files", "output_file", "status",
                                        "counts", "notes"})

    def test_forbidden_field_rejected(self):
        with self.assertRaises(rr.Reject):
            schema.validate_base_row(dict(base_row(), label="x"), "b:1")

    def test_trace_without_base_rejected(self):
        with self.assertRaises(rr.Reject):
            schema.validate_trace_row(trace_row(list(T), i=9), "t:1", {})


class Pipeline(unittest.TestCase):
    def test_end_to_end_and_void_without_permuted(self):
        with tempfile.TemporaryDirectory() as d:
            P = lambda n: os.path.join(d, n)  # noqa: E731
            bases, traces = [], []
            for i in range(12):
                bases.append(base_row(i=i, ent=float(i)))
                traces.append(trace_row(G[:i * 8] + T[i * 8:], i=i))
            rr.write_jsonl(P("base.jsonl"), bases)
            rr.write_jsonl(P("traces.jsonl"), traces)
            self.assertEqual(score.main([P("base.jsonl"), P("traces.jsonl"), P("sep.jsonl")],
                                        runs_path=P("runs.jsonl")), 0)
            self.assertEqual(permute.main([P("sep.jsonl"), P("perm.jsonl"), "--seed", "3"],
                                          runs_path=P("runs.jsonl")), 0)
            self.assertEqual(summarise.main([P("sep.jsonl"), P("s_real.jsonl")],
                                            runs_path=P("runs.jsonl")), 0)
            code = report.main([P("s_real.jsonl"), P("s_perm.jsonl"), P("report.md")],
                               runs_path=P("runs.jsonl"))
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(P("report.md")))
            self.assertEqual(summarise.main([P("perm.jsonl"), P("s_perm.jsonl")],
                                            runs_path=P("runs.jsonl")), 0)
            self.assertEqual(report.main([P("s_real.jsonl"), P("s_perm.jsonl"), P("report.md"),
                                          "--base", P("base.jsonl")], runs_path=P("runs.jsonl")), 0)
            with open(P("report.md")) as f:
                text = f.read()
            for h in ("## 1. Counts", "## 2. D sweep", "## 3. L sweep", "## 4. Stability",
                      "## 5. REAL vs PERMUTED", "## 6. NULLS TRIGGERED"):
                self.assertIn(h, text)
            self.assertEqual(text.count("\n## "), 6)
            with open(P("runs.jsonl")) as f:
                recs = [json.loads(l) for l in f]
            self.assertEqual([r["status"] for r in recs], ["ok", "ok", "ok", "void", "ok", "ok"])
            self.assertEqual(recs[1]["seed"], 3)


if __name__ == "__main__":
    unittest.main()
