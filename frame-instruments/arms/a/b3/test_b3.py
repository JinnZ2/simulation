"""B3 tests. stdlib unittest, fixtures in-file, no network."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import arms  # noqa: E402
import join  # noqa: E402
import split  # noqa: E402


def read(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


class Split(unittest.TestCase):
    def test_key_input_holds_statement_only(self):
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "statements.jsonl")
            rr.write_jsonl(st, [{"case_id": "c%d" % k, "statement": "S%d" % k} for k in range(4)])
            out = os.path.join(d, "key_inputs")
            self.assertEqual(split.main([st, out], runs_path=os.path.join(d, "runs.jsonl")), 0)
            files = sorted(os.listdir(out))
            self.assertEqual(len(files), 4)
            for name in files:
                with open(os.path.join(out, name)) as f:
                    obj = json.load(f)
                self.assertEqual(set(obj), {"case_id", "statement"})

    def test_generation_context_refused(self):
        with tempfile.TemporaryDirectory() as d:
            st, runs = os.path.join(d, "statements.jsonl"), os.path.join(d, "runs.jsonl")
            rr.write_jsonl(st, [{"case_id": "c1", "statement": "S", "key_posed": "leak"}])
            self.assertEqual(split.main([st, os.path.join(d, "o")], runs_path=runs), 1)
            rec = read(runs)[-1]
            self.assertEqual(rec["status"], "error")
            self.assertIn("key_posed", rec["notes"])
            self.assertFalse(os.path.exists(os.path.join(d, "o")))
        for extra in ("prompt", "generation_context", "model_id"):
            with self.assertRaises(rr.Reject):
                rows = [{"case_id": "c1", "statement": "S", extra: "x"}]
                with tempfile.TemporaryDirectory() as d2:
                    p = os.path.join(d2, "s.jsonl")
                    rr.write_jsonl(p, rows)
                    split.load_statements(p)


class Arms(unittest.TestCase):
    def test_arms_never_mix(self):
        rows = [{"case_id": "a", "arm": "single"}, {"case_id": "b"}]
        with self.assertRaises(rr.Reject):
            arms.stamp(rows, "split")
        with self.assertRaises(rr.Reject):
            arms.check_single_arm([{"arm": "single"}, {"arm": "split"}])
        with self.assertRaises(rr.Reject):
            arms.stamp(rows, "other")
        out = arms.stamp(rows, "single")
        self.assertTrue(all(r["arm"] == "single" for r in out))

    def test_arms_cli_refuses_mixed_file(self):
        with tempfile.TemporaryDirectory() as d:
            src, runs = os.path.join(d, "c.jsonl"), os.path.join(d, "runs.jsonl")
            rr.write_jsonl(src, [{"case_id": "a", "arm": "split"}])
            self.assertEqual(arms.main([src, os.path.join(d, "o.jsonl"), "--arm", "single"], runs_path=runs), 1)
            self.assertIn("mixed", read(runs)[-1]["notes"].replace("refusing", "mixed"))


class Join(unittest.TestCase):
    def test_join_preserves_ids_and_counts_drops(self):
        with tempfile.TemporaryDirectory() as d:
            P = lambda n: os.path.join(d, n)  # noqa: E731
            rr.write_jsonl(P("s.jsonl"), [{"case_id": c, "statement": "S" + c} for c in ("c1", "c2", "c3")])
            rr.write_jsonl(P("k.jsonl"), [{"case_id": c, "key_posed": "p", "key_target": "t", "key_why": "w"}
                                          for c in ("c1", "c3", "c9")])
            self.assertEqual(join.main([P("s.jsonl"), P("k.jsonl"), P("cases.jsonl")], runs_path=P("runs.jsonl")), 0)
            rows = read(P("cases.jsonl"))
            self.assertEqual([r["case_id"] for r in rows], ["c1", "c3"])
            self.assertTrue(all(r["arm"] == "split" and r["statement"] == "S" + r["case_id"] for r in rows))
            rec = read(P("runs.jsonl"))[-1]
            self.assertEqual(rec["counts"]["dropped_statements_without_key"], 1)
            self.assertEqual(rec["counts"]["dropped_keys_without_statement"], 1)
            self.assertIn("c2", rec["notes"])
            self.assertIn("c9", rec["notes"])


if __name__ == "__main__":
    unittest.main()
