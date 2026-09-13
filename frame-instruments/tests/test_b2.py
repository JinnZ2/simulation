"""B2 tests. stdlib unittest, no network, fixtures generated in-file."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import agree  # noqa: E402
import conditions  # noqa: E402
import lock  # noqa: E402
import order  # noqa: E402
from runrecord import read_jsonl, write_jsonl  # noqa: E402


def case(n, arm=None):
    row = {"case_id": f"k{n}", "statement": f"statement text {n} alpha",
           "key_posed": f"posed {n} beta", "key_target": f"target {n} gamma", "key_why": f"why {n} delta"}
    if arm:
        row["arm"] = arm
    return row


def audit(reader, case_id, cond, posed, target):
    return {"reader_id": reader, "case_id": case_id, "condition": cond, "posed": posed, "target": target}


class Conditions(unittest.TestCase):
    def test_no_withheld_field_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            cases = [case(i) for i in range(5)]
            write_jsonl(t / "cases.jsonl", cases)
            self.assertEqual(conditions.main([str(t / "cases.jsonl"), str(t / "out")]), 0)
            by_id = {c["case_id"]: c for c in cases}
            for cond in conditions.CONDITIONS:
                rows = read_jsonl(t / "out" / f"{cond}.jsonl")
                self.assertEqual(len(rows), 5)
                for r in rows:
                    self.assertEqual(set(r), {"case_id", "condition", "presented_text"})
                    self.assertEqual(r["condition"], cond)
                    src = by_id[r["case_id"]]
                    for f in conditions.withheld(cond):
                        self.assertNotIn(src[f], r["presented_text"], (cond, f))
            self.assertIn("statement text 2", read_jsonl(t / "out" / "C.jsonl")[2]["presented_text"])
            self.assertIn("posed 2", read_jsonl(t / "out" / "C.jsonl")[2]["presented_text"])

    def test_key_quoting_whole_statement_is_rejected(self):
        c = case(1)
        c["key_why"] = "because " + c["statement"]
        with self.assertRaises(conditions.SchemaError):
            conditions.presentation([c], "B")


class Order(unittest.TestCase):
    def test_latin_square_block_is_balanced(self):
        rows, note = order.assign(8, seed=1)
        self.assertEqual(len(rows), 8)
        for block in (rows[:4], rows[4:]):
            for pos in range(4):
                self.assertEqual(sorted(r["order"][pos] for r in block), ["A", "B", "C", "D"])
        self.assertNotIn("not fully counterbalanced", note)

    def test_remainder_is_declared(self):
        rows, note = order.assign(6, seed=2)
        self.assertEqual(len(rows), 6)
        self.assertIn("2 reader(s) on seeded permutations", note)
        self.assertEqual(order.assign(6, 2)[0], rows)


class Lock(unittest.TestCase):
    def test_release_refused_without_commit_then_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            write_jsonl(t / "cases.jsonl", [case(1)])
            commits, key_out = t / "commits.jsonl", t / "key.jsonl"
            code = lock.main(["release", "r1", "k1", str(t / "cases.jsonl"), str(commits), str(key_out)])
            self.assertEqual(code, 2)
            self.assertFalse(key_out.exists())
            recs = read_jsonl(t / "runs.jsonl")
            self.assertEqual(recs[-1]["status"], "void")
            (t / "resp.txt").write_text("my locked call\n")
            self.assertEqual(lock.main(["commit", "r1", "k1", str(t / "resp.txt"), str(commits)]), 0)
            self.assertEqual(read_jsonl(commits)[0]["sha256"], lock.sha256_text("my locked call\n"))
            code = lock.main(["release", "r1", "k1", str(t / "cases.jsonl"), str(commits), str(key_out)])
            self.assertEqual(code, 0)
            released = read_jsonl(key_out)[0]
            self.assertIn("posed 1 beta", released["presented_text"])
            self.assertNotIn("statement text 1", released["presented_text"])
            # a different reader is still locked out
            code = lock.main(["release", "r2", "k1", str(t / "cases.jsonl"), str(commits), str(key_out)])
            self.assertEqual(code, 2)


class Agreement(unittest.TestCase):
    def test_three_auditor_math(self):
        keys = {"k1": {"kt": ("p", "t"), "arm": None}}
        rows = agree.cells([audit("a", "k1", "B", "p", "t"), audit("b", "k1", "B", "p", "t"),
                            audit("c", "k1", "B", "q", "t")], keys)
        cell = rows[0]
        self.assertEqual(cell["n_auditors"], 3)
        self.assertAlmostEqual(cell["agree_posed"], 1 / 3, places=5)
        self.assertAlmostEqual(cell["agree_target"], 1.0)
        self.assertEqual(cell["full_disagreement"], 0)
        self.assertAlmostEqual(cell["ratify_key"], 2 / 3, places=5)
        alone = agree.cells([audit("a", "k1", "A", "p", "t")], keys)[0]
        self.assertIsNone(alone["agree_posed"])
        self.assertIsNone(alone["full_disagreement"])

    def test_A_vs_D1_divergence_detected(self):
        same = [audit("a", "k1", "A", "x", "t"), audit("b", "k1", "A", "x", "t"),
                audit("c", "k1", "D1", "x", "t"), audit("d", "k1", "D1", "x", "t")]
        self.assertEqual(agree.order_check(same)["divergent"], 0)
        diverged = [audit("a", "k1", "A", "x", "t"), audit("b", "k1", "A", "x", "t"),
                    audit("c", "k1", "D1", "y", "t"), audit("d", "k1", "D1", "y", "t")]
        oc = agree.order_check(diverged)
        self.assertEqual(oc["divergent"], 1)
        self.assertAlmostEqual(oc["gap"], 1.0)

    def test_anchoring_and_arm_carried(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            write_jsonl(t / "cases.jsonl", [case(1, arm="split")])
            audits = [audit("a", "k1", "C", "posed 1 beta", "target 1 gamma"),
                      audit("b", "k1", "C", "other", "target 1 gamma"),
                      audit("c", "k1", "D1", "other", "z"), audit("c", "k1", "D2", "posed 1 beta", "target 1 gamma"),
                      audit("d", "k1", "D1", "other", "z"), audit("d", "k1", "D2", "other", "z")]
            write_jsonl(t / "audits.jsonl", audits)
            self.assertEqual(agree.main([str(t / "audits.jsonl"), str(t / "cases.jsonl"), str(t / "agreement.jsonl")]), 0)
            rows = read_jsonl(t / "agreement.jsonl")
            self.assertEqual(rows[0]["kind"], "order_check")
            anch = rows[1]
            self.assertAlmostEqual(anch["ratify_C"], 0.5)
            self.assertAlmostEqual(anch["ratify_D1"], 0.0)
            self.assertAlmostEqual(anch["D1_to_D2_switched_to_key"], 0.5)
            self.assertTrue(all(r.get("arm") == "split" for r in rows if r["kind"] == "cell"))
            self.assertTrue(all(r["match_source"] == "exact" for r in rows))
            self.assertFalse(any(k in r for r in rows for k in ("label", "category", "type", "interpretation")))


if __name__ == "__main__":
    unittest.main()
