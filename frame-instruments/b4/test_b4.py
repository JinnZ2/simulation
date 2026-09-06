"""B4 tests. stdlib unittest, fixtures in-file, no network."""
import json
import os
import sys
import tempfile
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import runrecord as rr  # noqa: E402
import agreement  # noqa: E402
import calibrate  # noqa: E402
import grade  # noqa: E402
import items as items_mod  # noqa: E402
import nullshuffle  # noqa: E402
import reconstruct  # noqa: E402
import report  # noqa: E402
import requirements as req_mod  # noqa: E402


def item(k, arm="hypothetical"):
    return {"item_id": "i%d" % k, "source": "src-%d" % k, "text_verbatim": "Item %d as worded." % k,
            "branches_stated": 2, "arm": arm}


def req(item_id, rec, rid, text, status="unknown", test="a decision by the council", layer="funding"):
    return {"item_id": item_id, "reconstructor_id": rec, "req_id": rid, "requirement_text": text,
            "status": status, "settling_test": test, "layer": layer}


def read(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


FIXTURE = [
    req("i1", "r1", "q1", "budget line exists", "true", "check the appropriation act", "legislation"),
    req("i1", "r2", "q2", "money was appropriated", "partial", "read the appropriation act", "funding"),
    req("i1", "r1", "q3", "only two exits", "undifferentiated", "measure the corridor width", "infrastructure"),
    req("i1", "r2", "q4", "no third route", "unknown", "no instrument yet; would need a site survey", "physical law"),
    req("i2", "r1", "q5", "operator alone on shift", "lapsed", "staffing roster decision", "staffing"),
    req("i2", "r2", "q6", "single operator", "true", "the staffing rule in force", "staffing"),
    req("i2", "r2", "q7", "sensor absent", "false", "a load measurement with a mandated gauge", "other"),
]
MATCHES = [{"item_id": "i1", "req_a": "q1", "req_b": "q2", "matched": True},
           {"item_id": "i1", "req_a": "q3", "req_b": "q4", "matched": False},
           {"item_id": "i2", "req_a": "q5", "req_b": "q6", "matched": True}]


class Validation(unittest.TestCase):
    def test_two_state_file_is_void(self):
        with tempfile.TemporaryDirectory() as d:
            src, runs = os.path.join(d, "r.jsonl"), os.path.join(d, "runs.jsonl")
            rr.write_jsonl(src, [req("i1", "r1", "q1", "a", "true"), req("i1", "r1", "q2", "b", "false")])
            self.assertEqual(req_mod.main([src, os.path.join(d, "o.jsonl")], runs_path=runs), 2)
            self.assertEqual(read(runs)[-1]["status"], "void")
            self.assertFalse(os.path.exists(os.path.join(d, "o.jsonl")))

    def test_empty_settling_test_rejected(self):
        with self.assertRaises(rr.Reject):
            req_mod.validate_requirement(req("i1", "r1", "q1", "a", test="  "), "r:1")
        with self.assertRaises(rr.Reject):
            req_mod.validate_requirement(dict(req("i1", "r1", "q1", "a"), category="x"), "r:1")
        with self.assertRaises(rr.Reject):
            req_mod.validate_requirement(req("i1", "r1", "q1", "a", status="maybe"), "r:1")

    def test_items_never_mix_arms(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "items.jsonl")
            rr.write_jsonl(src, [item(1), item(2, "documented")])
            with self.assertRaises(rr.Reject):
                items_mod.load_items(src)


class Reconstruct(unittest.TestCase):
    def test_prompt_files_hold_text_verbatim_only(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = os.path.join(d, "items.jsonl"), os.path.join(d, "prompts")
            rr.write_jsonl(src, [item(1), item(2)])
            self.assertEqual(reconstruct.main([src, out, "--reconstructors", "r1", "r2", "r3"],
                                              runs_path=os.path.join(d, "runs.jsonl")), 0)
            files = sorted(os.listdir(out))
            self.assertEqual(len(files), 6)
            for name in files:
                with open(os.path.join(out, name)) as f:
                    obj = json.load(f)
                self.assertEqual(set(obj), {"text_verbatim"})
                self.assertNotIn("i1", obj["text_verbatim"])


class Shuffle(unittest.TestCase):
    def test_preserves_count_and_multiset(self):
        out, unshuffled = nullshuffle.shuffle(FIXTURE, seed=5)
        self.assertEqual(len(out), len(FIXTURE))
        self.assertEqual(Counter(r["requirement_text"] for r in out),
                         Counter(r["requirement_text"] for r in FIXTURE))
        self.assertEqual(unshuffled, [])
        self.assertTrue(all(a["item_id"] != b["item_id"] for a, b in zip(FIXTURE, out)))
        self.assertTrue(all(r["seed"] == 5 for r in out))
        self.assertEqual(out, nullshuffle.shuffle(FIXTURE, seed=5)[0])


class Agreement(unittest.TestCase):
    def test_identical_tests_different_wording_agree(self):
        rows = [req("i1", "r1", "q1", "the budget line was set", test="read the appropriation act"),
                req("i1", "r2", "q2", "funds had been appropriated", test="read the appropriation act")]
        out = agreement.agreement(rows, [{"item_id": "i1", "req_a": "q1", "req_b": "q2", "matched": True}], "test")
        self.assertEqual(out[1]["pairwise_agreement"], 1.0)
        self.assertEqual((out[1]["n_classes"], out[1]["n_singletons"], out[1]["full_disagreement"]), (1, 0, 0))
        self.assertEqual(out[0]["match_source"], "test")
        out = agreement.agreement(rows, [], "none")
        self.assertEqual((out[1]["pairwise_agreement"], out[1]["full_disagreement"], out[1]["n_singletons"]),
                         (0.0, 1, 2))

    def test_cross_item_matches_are_counted_not_joined(self):
        shuffled, _ = nullshuffle.shuffle(FIXTURE, seed=1)
        out = agreement.agreement(shuffled, MATCHES, "test")
        self.assertEqual(out[0]["matches_true"], 2)
        self.assertEqual(out[0]["matches_cross_item"], 0)
        self.assertEqual(out[0]["seed"], 1)


class Grade(unittest.TestCase):
    def test_reads_derived_from_settling_test(self):
        self.assertEqual(grade.read("measure the corridor width")[0], "physical")
        self.assertEqual(grade.read("check the appropriation act")[0], "policy")
        self.assertEqual(grade.read("a load measurement with a mandated gauge")[0], "unresolved")
        self.assertEqual(grade.read("ask someone")[0], "unresolved")
        out = grade.grade(FIXTURE)
        per = {r["item_id"]: r for r in out if "n_requirements" in r}
        self.assertEqual((per["i1"]["physical"], per["i1"]["policy"], per["i1"]["unresolved"]), (2, 2, 0))
        self.assertEqual(per["i1"]["policy_to_physical"], 1.0)
        self.assertEqual((per["i2"]["physical"], per["i2"]["policy"], per["i2"]["unresolved"]), (0, 2, 1))
        self.assertIsNone(per["i2"]["policy_to_physical"])
        self.assertEqual(per["i2"]["unresolved_req_ids"], ["q7"])
        self.assertEqual(per["i1"]["status_counts"], {"partial": 1, "true": 1, "undifferentiated": 1, "unknown": 1})
        self.assertEqual(out[0]["physical_terms"], list(grade.PHYSICAL_TERMS))


class Calibration(unittest.TestCase):
    def test_two_recovered_one_missed_one_beyond(self):
        items = [item(1, "documented")]
        rows = [req("i1", "r1", "q%d" % k, "req %d" % k) for k in range(1, 4)]
        factors = {"i1": [
            {"item_id": "i1", "factor_id": "f%d" % k, "factor_text": "factor %d" % k} for k in range(1, 4)]}
        fm = [{"item_id": "i1", "req_id": "q1", "factor_id": "f1", "matched": True},
              {"item_id": "i1", "req_id": "q2", "factor_id": "f2", "matched": True},
              {"item_id": "i1", "req_id": "q3", "factor_id": "f3", "matched": False}]
        out = calibrate.calibrate(items, rows, factors, fm, "hand")
        self.assertEqual((out[1]["recovered"], out[1]["missed"], out[1]["beyond_report"]), (2, 1, 1))
        self.assertEqual(out[1]["beyond_report_ids"], ["q3"])
        self.assertEqual(out[1]["missed_ids"], ["f3"])
        self.assertEqual(calibrate.calibrate([item(1)], rows, factors, fm, "hand")[0]["items_skipped"], 1)


class Pipeline(unittest.TestCase):
    def test_singleton_survives_into_report_and_void_without_shuffled(self):
        with tempfile.TemporaryDirectory() as d:
            P = lambda n: os.path.join(d, n)  # noqa: E731
            R = P("runs.jsonl")
            rr.write_jsonl(P("items.jsonl"), [item(1), item(2)])
            rr.write_jsonl(P("req.jsonl"), FIXTURE)
            rr.write_jsonl(P("matches.jsonl"), MATCHES)
            self.assertEqual(items_mod.main([P("items.jsonl"), P("items_v.jsonl")], runs_path=R), 0)
            self.assertEqual(req_mod.main([P("req.jsonl"), P("req_v.jsonl")], runs_path=R), 0)
            self.assertEqual(grade.main([P("req_v.jsonl"), P("grade.jsonl")], runs_path=R), 0)
            self.assertEqual(agreement.main([P("req_v.jsonl"), P("matches.jsonl"), P("agr.jsonl"),
                                             "--match-source", "hand pass"], runs_path=R), 0)
            base = [P("report.md"), "--items", P("items_v.jsonl"), "--requirements", P("req_v.jsonl"),
                    "--grade", P("grade.jsonl"), "--grade-shuffled", P("grade_s.jsonl"),
                    "--agreement", P("agr.jsonl"), "--agreement-shuffled", P("agr_s.jsonl")]
            self.assertEqual(report.main(base, runs_path=R), 2)
            self.assertFalse(os.path.exists(P("report.md")))
            self.assertEqual(nullshuffle.main([P("req_v.jsonl"), P("req_s.jsonl"), "--seed", "9"], runs_path=R), 0)
            self.assertEqual(grade.main([P("req_s.jsonl"), P("grade_s.jsonl")], runs_path=R), 0)
            self.assertEqual(agreement.main([P("req_s.jsonl"), P("matches.jsonl"), P("agr_s.jsonl"),
                                             "--match-source", "hand pass (real assignment)"], runs_path=R), 0)
            self.assertEqual(report.main(base, runs_path=R), 0)
            with open(P("report.md")) as f:
                text = f.read()
            self.assertEqual(text.count("\n## "), 9)
            for s in ("only two exits", "no third route", "sensor absent"):
                self.assertIn(s, text)
            self.assertIn("hand pass", text)
            self.assertIn("undifferentiated | 1", text)
            self.assertIn("no calibration file supplied", text)
            statuses = [r["status"] for r in read(R)]
            self.assertEqual(statuses, ["ok", "ok", "ok", "ok", "void", "ok", "ok", "ok", "ok"])


if __name__ == "__main__":
    unittest.main()
