"""B3 tests. stdlib unittest, no network, fixtures generated in-file."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import arms  # noqa: E402
import conditions  # noqa: E402
import join  # noqa: E402
import split  # noqa: E402
from runrecord import SchemaError, read_jsonl, write_jsonl  # noqa: E402


def stmt(n):
    return {"case_id": f"s{n}", "statement": f"statement {n}"}


def key(n):
    return {"case_id": f"s{n}", "key_posed": f"posed {n}", "key_target": f"target {n}", "key_why": f"why {n}"}


class Split(unittest.TestCase):
    def test_key_input_carries_no_generation_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            write_jsonl(t / "statements.jsonl", [stmt(1), stmt(2)])
            self.assertEqual(split.main(["keyinput", str(t / "statements.jsonl"), str(t / "out")]), 0)
            rows = read_jsonl(t / "out" / "role_key_input.jsonl")
            self.assertEqual(len(rows), 2)
            for r in rows:
                self.assertEqual(set(r), {"case_id", "statement"})
            leaky = stmt(3)
            leaky["generation_context"] = "the key will say posed 3"
            write_jsonl(t / "leaky.jsonl", [leaky])
            self.assertEqual(split.main(["keyinput", str(t / "leaky.jsonl"), str(t / "out2")]), 1)
            self.assertFalse((t / "out2" / "role_key_input.jsonl").exists())
            rec = read_jsonl(t / "runs.jsonl")[-1]
            self.assertEqual(rec["status"], "error")
            self.assertIn("generation_context", rec["notes"])

    def test_prompts_never_mention_a_key_to_the_case_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(split.main(["prompts", tmp]), 0)
            case_prompt = (Path(tmp) / "ROLE_CASE_PROMPT.txt").read_text()
            self.assertNotIn("key", case_prompt.lower())
            self.assertIn("statement", (Path(tmp) / "ROLE_KEY_PROMPT.txt").read_text())


class Arms(unittest.TestCase):
    def test_mixed_arms_refused(self):
        rows = [{"case_id": "a", "arm": "single"}, {"case_id": "b", "arm": "split"}]
        with self.assertRaises(SchemaError) as cm:
            arms.check(rows)
        self.assertIn("mixed", str(cm.exception))
        self.assertEqual(arms.check([{"case_id": "a", "arm": "split"}]), "split")
        with self.assertRaises(SchemaError):
            arms.check([{"case_id": "a", "arm": "other"}])
        with self.assertRaises(SchemaError):
            join.join([stmt(1)], [key(1)], "other")


class Join(unittest.TestCase):
    def test_preserves_ids_and_counts_drops(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            write_jsonl(t / "statements.jsonl", [stmt(1), stmt(2), stmt(3)])
            write_jsonl(t / "keys.jsonl", [key(1), key(3), key(9)])
            code = join.main([str(t / "statements.jsonl"), str(t / "keys.jsonl"), "split", str(t / "cases.jsonl")])
            self.assertEqual(code, 0)
            rows = read_jsonl(t / "cases.jsonl")
            self.assertEqual([r["case_id"] for r in rows], ["s1", "s3"])
            self.assertTrue(all(r["arm"] == "split" for r in rows))
            rec = read_jsonl(t / "runs.jsonl")[-1]
            self.assertEqual(rec["counts"], {"joined": 2, "statements_unmatched": 1, "keys_unmatched": 1})
            self.assertIn("s2", rec["notes"])
            self.assertIn("s9", rec["notes"])
            # the joined file is what B2 consumes, arm included
            self.assertEqual(conditions.main([str(t / "cases.jsonl"), str(t / "cond")]), 0)
            for r in read_jsonl(t / "cond" / "B.jsonl"):
                self.assertNotIn("arm", r)
                self.assertNotIn("statement", r["presented_text"])


if __name__ == "__main__":
    unittest.main()
