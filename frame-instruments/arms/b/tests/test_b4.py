"""B4 tests. stdlib unittest, no network, fixtures generated in-file."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "b4"))

import agreement  # noqa: E402
import calibrate  # noqa: E402
import grade  # noqa: E402
import items  # noqa: E402
import nullshuffle  # noqa: E402
import reconstruct  # noqa: E402
import requirements  # noqa: E402
from runrecord import read_jsonl, write_jsonl  # noqa: E402


def _load_b4_report():
    spec = importlib.util.spec_from_file_location("b4_report", HERE / "b4" / "report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b4_report = _load_b4_report()


def item(n, arm="hypothetical"):
    return {"item_id": f"it{n}", "source": f"source {n}", "text_verbatim": f"Verbatim text of item {n}.",
            "branches_stated": 2, "arm": arm}


def req(it, rec, k, text, test, status="partial", layer="infrastructure"):
    return {"item_id": it, "reconstructor_id": rec, "req_id": f"q{k}", "requirement_text": text,
            "status": status, "settling_test": test, "layer": layer}


class Requirements(unittest.TestCase):
    def test_two_state_file_is_void(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "requirements.jsonl"
            write_jsonl(p, [req("it1", "r001", 1, "a", "measure the pressure", status="true"),
                            req("it1", "r001", 2, "b", "check the statute", status="false")])
            self.assertEqual(requirements.main([str(p)]), 2)
            rec = read_jsonl(Path(tmp) / "runs.jsonl")[-1]
            self.assertEqual(rec["status"], "void")
            self.assertIn("true/false", rec["notes"])
            write_jsonl(p, [req("it1", "r001", 1, "a", "measure the pressure", status="true"),
                            req("it1", "r001", 2, "b", "check the statute", status="undifferentiated")])
            self.assertEqual(requirements.main([str(p)]), 0)

    def test_empty_settling_test_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "requirements.jsonl"
            write_jsonl(p, [req("it1", "r001", 1, "a", "   ")])
            self.assertEqual(requirements.main([str(p)]), 1)
            rec = read_jsonl(Path(tmp) / "runs.jsonl")[-1]
            self.assertEqual(rec["status"], "error")
            self.assertIn("settling_test", rec["notes"])
            self.assertIn("line 1", rec["notes"])


class Reconstruct(unittest.TestCase):
    def test_every_prompt_file_carries_text_verbatim_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            its = [item(1), item(2)]
            write_jsonl(t / "items.jsonl", its)
            self.assertEqual(reconstruct.main([str(t / "items.jsonl"), "3", str(t / "prompts")]), 0)
            files = sorted(p for p in (t / "prompts").glob("*.jsonl") if p.name != "manifest.jsonl")
            self.assertEqual(len(files), 6)
            texts = {i["item_id"]: i["text_verbatim"] for i in its}
            for f in files:
                rows = read_jsonl(f)
                self.assertEqual(len(rows), 1)
                self.assertEqual(set(rows[0]), {"text_verbatim"})
                item_id = f.name.split("__")[0]
                self.assertEqual(rows[0]["text_verbatim"], texts[item_id])
            manifest = read_jsonl(t / "prompts" / "manifest.jsonl")
            self.assertEqual(len(manifest), 6)

    def test_mixed_arms_refused(self):
        with self.assertRaises(items.SchemaError):
            items.check_item(item(1, arm="other"), 1)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "items.jsonl"
            write_jsonl(p, [item(1), item(2, arm="documented")])
            self.assertEqual(items.main([str(p)]), 1)
            self.assertIn("mixed", read_jsonl(Path(tmp) / "runs.jsonl")[-1]["notes"])


class Shuffle(unittest.TestCase):
    def test_preserves_count_and_texts_and_moves_every_row(self):
        rows = [req(f"it{i}", r, k, f"text {i} {r} {k}", "measure x") for i in range(3) for r in ("r001", "r002") for k in range(2)]
        out = nullshuffle.shuffle(rows, seed=5)
        self.assertEqual(len(out), len(rows))
        self.assertEqual(Counter(r["requirement_text"] for r in out), Counter(r["requirement_text"] for r in rows))
        self.assertTrue(all(a["item_id"] != b["item_id"] for a, b in zip(rows, out)))
        self.assertEqual(out, nullshuffle.shuffle(rows, seed=5))
        self.assertEqual(nullshuffle.shuffle(rows[:2], seed=1), [])


class Agreement(unittest.TestCase):
    def test_identical_tests_different_wording_agree_via_matches(self):
        reqs = [req("it1", "r001", 1, "A permit regime must exist", "the county permit ordinance"),
                req("it1", "r002", 1, "Permits have to be required by the county", "the county permit ordinance")]
        matched = [{"item_id": "it1", "req_a": "r001/q1", "req_b": "r002/q1", "matched": True}]
        rows = agreement.agreement(reqs, matched)
        self.assertEqual(rows[0]["pairwise_agreement"], 1.0)
        self.assertEqual(rows[0]["full_disagreement"], 0)
        self.assertEqual(rows[0]["n_singletons"], 0)
        rows = agreement.agreement(reqs, [])
        self.assertEqual(rows[0]["pairwise_agreement"], 0.0)
        self.assertEqual(rows[0]["full_disagreement"], 1)
        self.assertEqual(rows[0]["n_singletons"], 2)

    def test_grade_split_from_settling_test(self):
        self.assertEqual(grade.classify("measure the tensile load on the beam"), "physical")
        self.assertEqual(grade.classify("read the funding statute"), "policy")
        self.assertEqual(grade.classify("ask around"), "neither")
        self.assertEqual(grade.classify("measure what the budget allows"), "both")
        g = grade.grade([req("it1", "r001", 1, "a", "measure x"), req("it1", "r001", 2, "b", "the statute"),
                         req("it1", "r001", 3, "c", "ask around", status="undifferentiated", layer="other")])[0]
        self.assertEqual((g["physical"], g["policy"], g["unresolved"]), (1, 1, 1))
        self.assertEqual(g["ratio_policy_to_physical"], 1.0)
        self.assertEqual(g["status"]["undifferentiated"], 1)
        self.assertEqual(g["layer"], {"infrastructure": 2, "other": 1})


class Pipeline(unittest.TestCase):
    def test_singleton_survives_into_report_and_void_without_shuffle(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            write_jsonl(t / "items_h.jsonl", [item(1), item(2)])
            reqs = [req("it1", "r001", 1, "shared one", "measure the pressure"),
                    req("it1", "r002", 1, "shared one reworded", "measure the pressure"),
                    req("it1", "r002", 2, "ONLY ONE READER SAW THIS", "the appropriation vote", status="unknown", layer="funding"),
                    req("it2", "r001", 1, "x", "measure y"), req("it2", "r002", 1, "x2", "measure y")]
            write_jsonl(t / "requirements.jsonl", reqs)
            write_jsonl(t / "matches.jsonl", [{"item_id": "it1", "req_a": "r001/q1", "req_b": "r002/q1", "matched": True},
                                              {"item_id": "it2", "req_a": "r001/q1", "req_b": "r002/q1", "matched": True}])
            R, A, G = str(t / "requirements.jsonl"), str(t / "agreement.jsonl"), str(t / "grades.jsonl")
            self.assertEqual(grade.main([R, G]), 0)
            self.assertEqual(agreement.main([R, str(t / "matches.jsonl"), "human:tester", A]), 0)
            self.assertTrue(all(r["match_source"] == "human:tester" for r in read_jsonl(A)))
            args = [str(t / "items_h.jsonl"), str(t / "none.jsonl"), R, G, A, str(t / "gs.jsonl"), str(t / "as.jsonl"),
                    str(t / "calibration.jsonl"), str(t / "report.md")]
            self.assertEqual(b4_report.main(args), 2)
            self.assertFalse((t / "report.md").exists())
            self.assertEqual(nullshuffle.main([R, "3", str(t / "rs.jsonl")]), 0)
            self.assertEqual(grade.main([str(t / "rs.jsonl"), str(t / "gs.jsonl")]), 0)
            write_jsonl(t / "ms.jsonl", [])
            self.assertEqual(agreement.main([str(t / "rs.jsonl"), str(t / "ms.jsonl"), "none", str(t / "as.jsonl")]), 0)
            self.assertEqual(b4_report.main(args), 0)
            text = (t / "report.md").read_text()
            self.assertIn("ONLY ONE READER SAW THIS", text)
            self.assertIn("human:tester", text)
            self.assertIn("documented: not supplied", text)
            self.assertIn("no calibration run supplied", text)
            for n in range(1, 10):
                self.assertIn(f"## {n}.", text)


class Calibration(unittest.TestCase):
    def test_two_recovered_one_missed_one_beyond(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            write_jsonl(t / "items.jsonl", [item(1, arm="documented")])
            write_jsonl(t / "requirements.jsonl", [req("it1", "r001", k, f"req {k}", f"measure {k}") for k in (1, 2, 3)])
            write_jsonl(t / "factors.jsonl", [{"item_id": "it1", "factor_id": f"f{k}", "factor_text": f"factor {k}"} for k in (1, 2, 3)])
            write_jsonl(t / "fm.jsonl", [{"item_id": "it1", "factor_id": "f1", "req": "r001/q1", "matched": True},
                                         {"item_id": "it1", "factor_id": "f2", "req": "r001/q2", "matched": True},
                                         {"item_id": "it1", "factor_id": "f3", "req": "r001/q3", "matched": False}])
            code = calibrate.main([str(t / "requirements.jsonl"), str(t / "items.jsonl"), str(t / "factors.jsonl"),
                                   str(t / "fm.jsonl"), "model:matcher", str(t / "calibration.jsonl")])
            self.assertEqual(code, 0)
            pooled = [r for r in read_jsonl(t / "calibration.jsonl") if r["kind"] == "item"][0]
            self.assertEqual((pooled["recovered"], pooled["missed"], pooled["beyond_report"]), (2, 1, 1))
            self.assertEqual(pooled["match_source"], "model:matcher")
            write_jsonl(t / "items.jsonl", [item(1)])
            code = calibrate.main([str(t / "requirements.jsonl"), str(t / "items.jsonl"), str(t / "factors.jsonl"),
                                   str(t / "fm.jsonl"), "model:matcher", str(t / "calibration.jsonl")])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
