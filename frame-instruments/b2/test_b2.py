"""B2 tests. stdlib unittest, fixtures in-file, no network."""
import json
import os
import sys
import tempfile
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import agree  # noqa: E402
import conditions  # noqa: E402
import lock  # noqa: E402
import order  # noqa: E402


def case(k, arm=None):
    row = {"case_id": "c%d" % k, "statement": "STATEMENT-%d text" % k,
           "key_posed": "POSED-%d" % k, "key_target": "TARGET-%d" % k,
           "key_why": "WHY-%d" % k}
    if arm:
        row["arm"] = arm
    return row


def resp(case_id, cond, auditor, posed, target="t"):
    return {"case_id": case_id, "condition": cond, "auditor_id": auditor,
            "posed": posed, "target": target}


def read(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


class Conditions(unittest.TestCase):
    def test_no_leak_in_any_row_of_any_file(self):
        with tempfile.TemporaryDirectory() as d:
            cases = [case(k) for k in range(5)]
            rr.write_jsonl(os.path.join(d, "cases.jsonl"), cases)
            out = os.path.join(d, "cond")
            self.assertEqual(conditions.main([os.path.join(d, "cases.jsonl"), out],
                                             runs_path=os.path.join(d, "runs.jsonl")), 0)
            by_id = {c["case_id"]: c for c in cases}
            for cond in conditions.CONDITIONS:
                rows = read(os.path.join(out, cond + ".jsonl"))
                self.assertEqual(len(rows), 5)
                for row in rows:
                    self.assertEqual(set(row), {"case_id", "condition", "presented_text"})
                    for v in conditions.withheld(by_id[row["case_id"]], cond):
                        self.assertNotIn(v, row["presented_text"])

    def test_leak_is_rejected(self):
        c = case(1)
        c["key_why"] = "because " + c["statement"] + " says so"
        with self.assertRaises(rr.Reject):
            conditions.present(c, "B")
        c = case(2)
        c["statement"] = "the key says " + c["key_posed"]
        with self.assertRaises(rr.Reject):
            conditions.present(c, "A")


class Order(unittest.TestCase):
    def test_latin_square_balance(self):
        rows, short = order.assign(8, 1)
        self.assertEqual(short, 0)
        for pos in range(4):
            self.assertEqual(Counter(r["order"][pos] for r in rows), Counter({c: 2 for c in "ABCD"}))
        self.assertEqual(rows, order.assign(8, 1)[0])

    def test_shortfall_is_stated(self):
        with tempfile.TemporaryDirectory() as d:
            out, runs = os.path.join(d, "a.jsonl"), os.path.join(d, "runs.jsonl")
            self.assertEqual(order.main([out, "--readers", "5", "--seed", "2"], runs_path=runs), 0)
            rec = read(runs)[-1]
            self.assertIn("shortfall: 1", rec["notes"])
            self.assertEqual(rec["seed"], 2)
            self.assertTrue(all(r["seed"] == 2 and sorted(r["order"]) == list("ABCD") for r in read(out)))


class Lock(unittest.TestCase):
    def test_release_refused_without_commit(self):
        with tempfile.TemporaryDirectory() as d:
            P = lambda n: os.path.join(d, n)  # noqa: E731
            rr.write_jsonl(P("cases.jsonl"), [case(1)])
            code = lock.main(["release", "r1", "c1", P("cases.jsonl"), P("commits.jsonl"), P("key.jsonl")],
                             runs_path=P("runs.jsonl"))
            self.assertEqual(code, 2)
            self.assertEqual(read(P("runs.jsonl"))[-1]["status"], "void")
            self.assertFalse(os.path.exists(P("key.jsonl")))
            with open(P("resp.txt"), "w") as f:
                f.write("my A-stage call")
            self.assertEqual(lock.main(["commit", "r1", "c1", P("resp.txt"), P("commits.jsonl")],
                                       runs_path=P("runs.jsonl")), 0)
            self.assertEqual(lock.main(["release", "r1", "c1", P("cases.jsonl"), P("commits.jsonl"),
                                        P("key.jsonl")], runs_path=P("runs.jsonl")), 0)
            row = read(P("key.jsonl"))[0]
            self.assertEqual(row["condition"], "D")
            self.assertIn("POSED-1", row["presented_text"])
            self.assertNotIn("STATEMENT", row["presented_text"])
            self.assertEqual(row["commit_sha256"], rr.sha256_text("my A-stage call"))

    def test_tampered_commit_rejected(self):
        with self.assertRaises(rr.Reject):
            lock.find_commit([{"reader_id": "r", "case_id": "c", "response": "x", "sha256": "0"}], "r", "c")


class Agreement(unittest.TestCase):
    def test_three_auditor_fixture(self):
        cases = [case(1)]
        rs = [resp("c1", "B", "u1", "x"), resp("c1", "B", "u2", "x"), resp("c1", "B", "u3", "y"),
              resp("c1", "C", "u1", "p", "q"), resp("c1", "C", "u2", "r", "s"), resp("c1", "C", "u3", "t", "u")]
        out = agree.agreement(cases, rs)
        cell = {(r["case_id"], r["condition"]): r for r in out if "n_auditors" in r}
        b = cell[("c1", "B")]
        self.assertAlmostEqual(b["agree_posed"], 1 / 3, places=5)
        self.assertEqual(b["agree_target"], 1.0)
        self.assertEqual(b["full_disagreement"], 0)
        c = cell[("c1", "C")]
        self.assertEqual((c["agree_posed"], c["agree_target"], c["full_disagreement"]), (0.0, 0.0, 1))
        self.assertEqual(out[0]["match_source"], agree.EXACT)
        self.assertIsNone(out[0]["order_check"]["ok"])

    def test_a_vs_d_divergence_detected(self):
        cases = [case(1), case(2)]
        rs = []
        for u in ("u1", "u2", "u3"):
            rs += [resp("c1", "A", u, "x"), resp("c1", "D_pre", u, "y"),
                   resp("c2", "A", u, "x"), resp("c2", "D_pre", u, "x")]
        out = agree.agreement(cases, rs)
        self.assertEqual(out[0]["order_check"], {"compared_cases": 2, "diverging_cases": ["c1"], "ok": False})
        ad = {r["case_id"]: r for r in out if "diverges" in r}
        self.assertTrue(ad["c1"]["diverges"])
        self.assertFalse(ad["c2"]["diverges"])
        self.assertEqual(ad["c1"]["cross_agree_posed"], 0.0)

    def test_anchoring_and_arms(self):
        cases = [case(1, "split"), case(2, "single")]
        rs = [resp("c1", "D_pre", "u1", "no", "no"), resp("c1", "D_post", "u1", "POSED-1", "TARGET-1"),
              resp("c1", "D_pre", "u2", "posed-1", "target-1"), resp("c1", "D_post", "u2", "POSED-1", "TARGET-1"),
              resp("c1", "C", "u3", "POSED-1", "TARGET-1"), resp("c1", "C", "u4", "z", "z"),
              resp("c2", "B", "u1", "a", "a"), resp("c2", "B", "u2", "a", "a")]
        out = agree.agreement(cases, rs)
        cd = [r for r in out if "ratify_rate_C" in r][0]
        self.assertEqual((cd["ratify_rate_C"], cd["ratify_rate_D_post"]), (0.5, 1.0))
        self.assertEqual((cd["n_independent"], cd["ratified_after_independent"]), (1, 1))
        arms = {(r["arm"], r["condition"]): r for r in out if "mean_agree_posed" in r}
        self.assertEqual(arms[("single", "B")]["mean_agree_posed"], 1.0)
        self.assertIn(("split", "C"), arms)


if __name__ == "__main__":
    unittest.main()
