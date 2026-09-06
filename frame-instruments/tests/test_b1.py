"""B1 tests. stdlib unittest, no network, fixtures generated in-file."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import permute  # noqa: E402
import report  # noqa: E402
import schema  # noqa: E402
import score  # noqa: E402
import summarise  # noqa: E402
from runrecord import read_jsonl, write_jsonl  # noqa: E402

D_ALL = score.D_SWEEP
L_ALL = score.L_SWEEP


def base_row(i, ent=1.0, taken="a", runner="b", model="m"):
    return {"case_id": "c1", "model_id": model, "i": i, "token_taken": taken,
            "logprob_taken": -0.5, "topk": [[taken, -0.5], [runner, -1.5], ["z", -3.0]],
            "entropy_i": ent, "entropy_basis": "topk"}


def trace_row(i, cont, base, rank=2, forced="b", N=10, model="m"):
    return {"case_id": "c1", "model_id": model, "i": i, "branch_rank": rank, "forced_token": forced,
            "selection_N": N, "continuation": cont, "base_continuation": base}


def by_dl(rows):
    return {(r["D"], r["L"]): r for r in rows}


class ResyncAndDiv(unittest.TestCase):
    def test_rejoins_immediately(self):
        base = [f"t{k}" for k in range(128)]
        rows = score.score([base_row(0)], [trace_row(0, list(base), base)])
        self.assertEqual(len(rows), len(D_ALL) * len(L_ALL))
        for r in rows:
            self.assertEqual(r["resync_D"], 1)
            self.assertEqual(r["div_D"], 0.0)

    def test_never_rejoins(self):
        base = [f"b{k}" for k in range(128)]
        cont = [f"c{k}" for k in range(128)]
        rows = by_dl(score.score([base_row(0)], [trace_row(0, cont, base)]))
        for (D, L), r in rows.items():
            self.assertEqual(r["resync_D"], 0)
            self.assertEqual(r["div_D"], 1.0)
        # div rises with D in absolute terms: distance is D itself here
        self.assertEqual(score.levenshtein(cont[:8], base[:8]), 8)
        self.assertEqual(score.levenshtein(cont[:64], base[:64]), 64)

    def test_rejoin_at_token_20_shows_the_sweep(self):
        base = [f"b{k}" for k in range(128)]
        cont = [f"c{k}" for k in range(20)] + base[20:]
        rows = by_dl(score.score([base_row(0)], [trace_row(0, cont, base)]))
        for L in L_ALL:
            self.assertEqual(rows[(8, L)]["resync_D"], 0)
            self.assertEqual(rows[(16, L)]["resync_D"], 0)
            for D in (32, 64, 128):
                self.assertEqual(rows[(D, L)]["resync_D"], 1, (D, L))
        self.assertGreater(rows[(8, 4)]["div_D"], rows[(128, 4)]["div_D"])

    def test_L_sensitivity_three_token_suffix(self):
        base = [f"b{k}" for k in range(16)]
        cont = [f"c{k}" for k in range(13)] + base[13:16]
        rows = by_dl(score.score([base_row(0)], [trace_row(0, cont, base)]))
        self.assertEqual(rows[(16, 2)]["resync_D"], 1)
        self.assertEqual(rows[(16, 4)]["resync_D"], 0)
        self.assertEqual(rows[(16, 8)]["resync_D"], 0)

    def test_gap_and_entropy_carried(self):
        rows = score.score([base_row(3, ent=2.5)], [trace_row(3, ["x"], ["y"])])
        self.assertAlmostEqual(rows[0]["gap_i"], 1.0)
        self.assertEqual(rows[0]["ent_i"], 2.5)
        self.assertEqual(set(rows[0]), set(score.FIELDS))

    def test_levenshtein(self):
        self.assertEqual(score.levenshtein(list("kitten"), list("sitting")), 3)
        self.assertEqual(score.levenshtein([], list("ab")), 2)


class Permutation(unittest.TestCase):
    def _rows(self):
        base = [base_row(i, ent=float(i)) for i in range(6)]
        traces = [trace_row(i, [f"c{i}{k}" for k in range(32)], [f"b{k}" for k in range(32)]) for i in range(6)]
        return score.score(base, traces)

    def test_preserves_count_and_multiset(self):
        rows = self._rows()
        out = permute.permute(rows, seed=7)
        self.assertEqual(len(out), len(rows))
        key = lambda r: (r["D"], r["L"], r["ent_i"], r["gap_i"], r["resync_D"], r["div_D"])  # noqa: E731
        self.assertEqual(Counter(map(key, rows)), Counter(map(key, out)))
        for a, b in zip(rows, out):
            self.assertEqual((a["i"], a["branch_rank"], a["D"], a["L"]), (b["i"], b["branch_rank"], b["D"], b["L"]))

    def test_deterministic_and_moves_something(self):
        rows = self._rows()
        self.assertEqual(permute.permute(rows, 3), permute.permute(rows, 3))
        self.assertNotEqual([r["ent_i"] for r in permute.permute(rows, 3)], [r["ent_i"] for r in rows])


class SchemaAndRecord(unittest.TestCase):
    def test_malformed_row_rejected_and_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.jsonl"
            traces = Path(tmp) / "traces.jsonl"
            bad = base_row(0)
            bad["entropy_basis"] = "guess"
            write_jsonl(base, [base_row(1), bad])
            write_jsonl(traces, [])
            code = schema.main([str(base), str(traces)])
            self.assertEqual(code, 1)
            recs = read_jsonl(Path(tmp) / "runs.jsonl")
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["status"], "error")
            self.assertIn("line 2", recs[0]["notes"])
            self.assertIn("entropy_basis", recs[0]["notes"])
            self.assertEqual(len(recs[0]["input_files"]), 2)

    def test_selection_N_required(self):
        row = trace_row(0, ["x"], ["y"])
        del row["selection_N"]
        with self.assertRaises(schema.SchemaError) as cm:
            schema.check_trace_row(row, 2)
        self.assertIn("selection_N", str(cm.exception))
        self.assertEqual(score.score([base_row(0)], [trace_row(0, ["x"], ["y"], N=25)])[0]["N"], 25)

    def test_extra_field_rejected(self):
        row = base_row(0)
        row["label"] = "x"
        with self.assertRaises(schema.SchemaError) as cm:
            schema.check_base_row(row, 5)
        self.assertIn("label", str(cm.exception))


class NSweep(unittest.TestCase):
    def test_nested_membership_and_N_stability(self):
        base = [base_row(i, ent=float(i)) for i in range(6)]
        traces = [trace_row(i, [f"c{i}{k}" for k in range(16)], [f"b{k}" for k in range(16)],
                            N=10 if i < 2 else 25) for i in range(6)]
        out = summarise.summarise(score.score(base, traces))
        cells = {(c["N"], c["D"], c["L"]): c for c in out if c["kind"] == "cell"}
        self.assertEqual(cells[(10, 8, 2)]["n_rows"], 2)
        self.assertEqual(cells[(25, 8, 2)]["n_rows"], 6)
        self.assertEqual(out[0]["N_values"], [10, 25])
        n_axis = [s for s in out if s["kind"] == "stability" and s["axis"] == "N"]
        self.assertEqual(len(n_axis), len(D_ALL) * len(L_ALL))
        self.assertTrue(all(s["from"] == 10 and s["to"] == 25 and "D" in s and "L" in s for s in n_axis))


class CrossModel(unittest.TestCase):
    def _two_models(self, flip):
        base, traces = [], []
        for model in ("m1", "m2"):
            for i in range(10):
                base.append(base_row(i, ent=float(i), model=model))
                # m1 separates at i=9; m2 at i=9 too, or at i=0 when flipped
                sep = (i == 9) if (model == "m1" or not flip) else (i == 0)
                cont = [f"x{i}{k}" for k in range(16)] if sep else [f"b{k}" for k in range(16)]
                traces.append(trace_row(i, cont, [f"b{k}" for k in range(16)], model=model))
        return summarise.summarise(score.score(base, traces))

    def test_same_positions_overlap_fully_and_disjoint_zero(self):
        xm = [r for r in self._two_models(flip=False) if r["kind"] == "cross_model"]
        self.assertEqual(len(xm), len(D_ALL) * len(L_ALL))
        self.assertTrue(all(r["jaccard"] == 1.0 and r["case_id"] == "c1" for r in xm))
        self.assertEqual({(r["model_a"], r["model_b"]) for r in xm}, {("m1", "m2")})
        xm = [r for r in self._two_models(flip=True) if r["kind"] == "cross_model"]
        self.assertTrue(all(r["jaccard"] == 0.0 for r in xm))

    def test_single_model_writes_no_cross_rows(self):
        out = summarise.summarise(score.score([base_row(0)], [trace_row(0, ["x"] * 8, ["y"] * 8)]))
        self.assertFalse([r for r in out if r["kind"] == "cross_model"])


class Pipeline(unittest.TestCase):
    def test_end_to_end_and_void_without_permuted(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            base = [base_row(i, ent=float(i)) for i in range(12)]
            traces = [trace_row(i, [f"c{i}{k}" for k in range(64)] if i % 2 else [f"b{k}" for k in range(64)],
                                [f"b{k}" for k in range(64)]) for i in range(12)]
            write_jsonl(t / "base.jsonl", base)
            write_jsonl(t / "traces.jsonl", traces)
            self.assertEqual(score.main([str(t / "base.jsonl"), str(t / "traces.jsonl"), str(t / "sep.jsonl")]), 0)
            self.assertEqual(summarise.main([str(t / "sep.jsonl"), str(t / "sum_real.jsonl")]), 0)
            self.assertEqual(report.main([str(t / "sum_real.jsonl"), str(t / "missing.jsonl"), str(t / "report.md")]), 2)
            self.assertFalse((t / "report.md").exists())
            self.assertEqual(permute.main([str(t / "sep.jsonl"), str(t / "sep_p.jsonl"), "11"]), 0)
            self.assertEqual(summarise.main([str(t / "sep_p.jsonl"), str(t / "sum_perm.jsonl")]), 0)
            self.assertEqual(report.main([str(t / "sum_real.jsonl"), str(t / "sum_perm.jsonl"), str(t / "report.md")]), 0)
            text = (t / "report.md").read_text()
            for h in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6."):
                self.assertIn(h, text)
            self.assertIn("N5", text)
            self.assertIn("| D | L | N | model |", text)
            self.assertIn("N values: [10]", text)
            self.assertIn("one model present", text)
            statuses = [r["status"] for r in read_jsonl(t / "runs.jsonl")]
            self.assertEqual(statuses, ["ok", "ok", "void", "ok", "ok", "ok"])
            seeds = [r["seed"] for r in read_jsonl(t / "runs.jsonl") if r["script"] == "permute"]
            self.assertEqual(seeds, [11])


if __name__ == "__main__":
    unittest.main()
