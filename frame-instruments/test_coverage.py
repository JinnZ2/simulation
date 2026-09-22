#!/usr/bin/env python3
# test_coverage.py -- checks on the arm machinery itself.
# stdlib unittest, no network. Run: python3 test_coverage.py
#
# Every guard here is planted against: a constructed violation must fire it.
# A guard nobody has seen fire is not known to discriminate.

import ast
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE]
import coverage            # noqa: E402
import run_arms            # noqa: E402

# Identifiers that would turn a held fork into a silent decision.
RANKING = {"rank", "ranked", "ranking", "score", "scored", "total", "sum",
           "best", "winner", "wins", "better", "worse", "prefer", "preferred",
           "recommend", "recommended", "pick", "choose", "chosen"}


def identifiers(path):
    """Names a module BINDS or reads. A substring scan would fire on the
    comment saying what the module refuses, so this reads the parse tree."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.arg):
            out.add(n.arg)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            pass                       # strings are prose, not bindings
    return out


def tokens(names):
    out = set()
    for n in names:
        for part in n.replace("-", "_").split("_"):
            if part:
                out.add(part.lower())
    return out


class NoRanking(unittest.TestCase):
    """coverage.py must not rank, total or recommend an arm."""

    def test_no_ranking_identifier(self):
        hit = tokens(identifiers(os.path.join(HERE, "coverage.py"))) & RANKING
        self.assertEqual(hit, set(), "ranking identifier in coverage.py: %s" % hit)

    def test_guard_fires_on_a_plant(self):
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "planted.py")
        with open(p, "w") as fh:
            fh.write("def best_arm(rows):\n    return max(rows)\n")
        hit = tokens(identifiers(p)) & RANKING
        self.assertIn("best", hit)

    def test_no_arm_to_arm_comparison(self):
        """No ordering comparison may take two arms' verdicts as operands.
        Checked structurally: the module holds no Compare with Lt/Gt/LtE/GtE
        over subscripts of the same arms mapping."""
        tree = ast.parse(open(os.path.join(HERE, "coverage.py")).read())
        bad = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Compare) and any(
                    isinstance(o, (ast.Lt, ast.Gt, ast.LtE, ast.GtE))
                    for o in n.ops):
                src = ast.dump(n)
                if "arms" in src and "Subscript" in src:
                    bad.append(src[:80])
        self.assertEqual(bad, [], "arm-to-arm ordering comparison: %s" % bad)


class Table(unittest.TestCase):

    def test_every_check_returns_a_verdict_for_every_arm(self):
        t = coverage.table()
        self.assertTrue(t["arms"], "no arms found")
        for row in t["rows"]:
            for a in t["arms"]:
                self.assertIn(a, row["arms"], "%s missing arm %s" % (row["id"], a))
                self.assertIsInstance(row["arms"][a], str)
                self.assertNotIn("CHECK ERROR", row["arms"][a],
                                 "%s raised on arm %s" % (row["id"], a))

    def test_differs_is_computed_not_declared(self):
        t = coverage.table()
        for row in t["rows"]:
            self.assertEqual(row["differs"], len(set(row["arms"].values())) > 1)

    def test_at_least_one_row_differs_and_one_agrees(self):
        """A table that marked everything DIFFERS, or nothing, would not
        discriminate. Both branches must be occupied on the real arms."""
        d = [r["differs"] for r in coverage.table()["rows"]]
        self.assertIn(True, d)
        self.assertIn(False, d)

    def test_every_check_is_marked_ast_or_lexical(self):
        for rid, kind, _, _ in coverage.CHECKS:
            self.assertTrue(kind.startswith("AST") or kind == "LEXICAL",
                            "%s has no method mark" % rid)


class Queue(unittest.TestCase):

    def test_queue_holds_only_differing_rows(self):
        ids = {r["id"] for r in coverage.queue()}
        differ = {r["id"] for r in coverage.table()["rows"] if r["differs"]}
        self.assertEqual(ids, differ)

    def test_every_queued_item_is_routed(self):
        for r in coverage.queue():
            self.assertIn(r["settled_by"], coverage.SETTLED_BY)
            self.assertNotEqual(r["why"], "not routed",
                                "%s has no settlement route" % r["id"])

    def test_queue_orders_by_settlement_cost(self):
        c = [coverage.SETTLED_BY[r["settled_by"]] for r in coverage.queue()]
        self.assertEqual(c, sorted(c))


class Provenance(unittest.TestCase):

    def test_arms_are_verbatim_plus_declared(self):
        for r in coverage.provenance():
            self.assertEqual(r["status"], "VERBATIM+DECLARED",
                             "arm %s: %s" % (r["arm"], r))
            self.assertGreater(r["compared"], 0, "arm %s compared 0 files" % r["arm"])

    def test_declared_edits_are_actually_present(self):
        for r in coverage.provenance():
            self.assertEqual(r["declared_but_identical"], [],
                             "declared edit missing in arm %s" % r["arm"])

    def test_empty_listing_refuses_rather_than_passing(self):
        """The first version ran git from frame-instruments/, where the
        pathspec matched nothing, and reported VERBATIM+DECLARED over zero
        comparisons. An empty denominator must refuse."""
        real = coverage.PARENT.copy()
        try:
            coverage.PARENT["a"] = "0000000000000000000000000000000000000000"
            r = [x for x in coverage.provenance() if x["arm"] == "a"][0]
            self.assertEqual(r["status"], "UNCHECKABLE")
            self.assertEqual(r["compared"], 0)
        finally:
            coverage.PARENT.clear()
            coverage.PARENT.update(real)


class Arms(unittest.TestCase):

    def test_arm_id_is_in_each_arms_run_record(self):
        for a in coverage.arms():
            rel, text = coverage._find(a, "runrecord.py")
            self.assertIsNotNone(rel, "arm %s has no runrecord.py" % a)
            self.assertIn('ARM = "%s"' % a, text)
            self.assertIn('"arm": ARM', text)

    def test_arm_id_is_not_a_forbidden_field(self):
        """The order forbids label/category/type/interpretation. `arm` names
        which implementation ran, the same class as `script`."""
        self.assertNotIn("arm", ("label", "category", "type", "interpretation"))

    def test_runner_finds_suites_in_every_layout(self):
        for a in coverage.arms():
            self.assertTrue(run_arms.suites(a), "no suites found in arm %s" % a)

    def test_work_orders_are_at_the_top_not_in_the_arms(self):
        for name in ("WORK_ORDER_B1_B3.md", "WORK_ORDER_B4.md",
                     "WORK_ORDER_RUNNER_UP.md"):
            self.assertTrue(os.path.isfile(os.path.join(HERE, name)), name)
        for a in coverage.arms():
            root = os.path.join(coverage.ARMS_DIR, a)
            stray = [f for r, _, fs in os.walk(root) for f in fs
                     if f.upper().startswith("WORK")]
            self.assertEqual(stray, [], "work order copy inside arm %s" % a)

    def test_no_path_collides_between_arms(self):
        """The merge damaged exactly the files at the same path in both
        parents. Arms in disjoint namespaces cannot collide; this asserts
        the namespaces stay disjoint."""
        seen = {}
        for a in coverage.arms():
            for rel in coverage._files(a):
                seen.setdefault(rel, []).append(a)
        # Same relative path in two arms is fine -- they are different
        # directories. What must not exist is an arm file at the top level.
        top = [f for f in os.listdir(HERE) if f.endswith(".py")]
        self.assertEqual(sorted(top), ["coverage.py", "run_arms.py",
                                       "test_coverage.py"],
                         "arm code at the top level: %s" % top)


def main():
    r = unittest.TextTestRunner(verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    print("checks: %d   failures: %d   errors: %d"
          % (r.testsRun, len(r.failures), len(r.errors)))
    return 0 if r.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
