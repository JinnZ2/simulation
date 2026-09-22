#!/usr/bin/env python3
# coverage.py -- score every arm against the shared work order.
# CC0, stdlib only, no network. Runs from frame-instruments/.
#
# WHAT THIS DOES
#     frame-instruments holds N independent builds of ONE set of work
#     orders. This scores each arm against the order, requirement by
#     requirement, and prints where the arms DIFFER.
#
# WHAT IT MUST NOT DO
#     It does not total, score, rank, or recommend an arm. There is no
#     number summarising an arm anywhere in this file, and no comparison
#     operator takes two arms' results as operands. A "winner" column
#     would turn a held fork into a decision nobody recorded making.
#     Enforced by test_coverage.py walking this module's AST.
#
# THE LIMIT, STATED HERE RATHER THAN AT THE BOTTOM
#     Requirements marked LEXICAL are word/pattern lookups and a rewrite
#     steps around them. Requirements marked AST read the parse tree and
#     do not. The mark is printed with every row. A verdict of "absent"
#     from a LEXICAL check is a property of THE PATTERN, never proof the
#     arm lacks the property. This checker's first draft reported both
#     arms failing the L sweep because it searched for [2, 4, 8] where
#     both arms write (2, 4, 8): a false negative, in the direction of
#     under-reporting coverage, found by reading the code it had just
#     graded.
#
# usage:
#     python3 coverage.py                 # the requirement table
#     python3 coverage.py --queue         # discriminators, cheapest first
#     python3 coverage.py --provenance    # arms vs their parent commits
#     python3 coverage.py --json
#     python3 coverage.py --selftest

import ast
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS_DIR = os.path.join(HERE, "arms")

# Provenance: each arm is a verbatim checkout of one merge parent, plus a
# declared modification list. ARMS.md carries the argument; this is the data.
PARENT = {"a": "85a3714", "b": "5e04a33"}
DECLARED_EDITS = {
    "a": {"runrecord.py": "ARM constant + one provenance field in record()",
          "b1/test_b1.py": "run-record key-set pin widened by exactly one key"},
    "b": {"runrecord.py": "ARM constant + one provenance field in write_record()"},
}
# Files moved out of the arms to the top level because they are identical in
# every arm (the work orders) or are spec rather than code (liftable/).
HOISTED = ("workorders/", "WORKORDER_", "liftable/", "runs/")

NETWORK = {"socket", "urllib", "http", "ftplib", "smtplib", "telnetlib",
           "requests", "httpx", "xmlrpc"}
THIRD_PARTY = {"numpy", "pandas", "scipy", "yaml", "pytest", "matplotlib"}


def arms():
    return sorted(d for d in os.listdir(ARMS_DIR)
                  if os.path.isdir(os.path.join(ARMS_DIR, d)))


def _files(arm):
    out = {}
    root = os.path.join(ARMS_DIR, arm)
    for r, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".py"):
                p = os.path.join(r, f)
                out[os.path.relpath(p, root)] = open(p, encoding="utf-8").read()
    return out


def _find(arm, *basenames):
    """First file in this arm whose basename matches. Layouts differ by arm,
    so nothing here may assume a path."""
    hits = [(rel, text) for rel, text in _files(arm).items()
            if os.path.basename(rel) in basenames]
    if not hits:
        return None, ""
    # Shallowest path wins. Arm b has both report.py and b4/report.py; a
    # plain sort picks b4/report.py and silently grades the wrong module.
    hits.sort(key=lambda rt: (rt[0].count(os.sep), rt[0]))
    return hits[0]


def _trees(arm):
    for rel, text in sorted(_files(arm).items()):
        try:
            yield rel, ast.parse(text)
        except SyntaxError:
            continue


def _literal_tuples(tree):
    """Every tuple/list literal of plain numbers in a parse tree."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.Tuple, ast.List)):
            vals = []
            for e in n.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, (int, float)):
                    vals.append(e.value)
                else:
                    vals = None
                    break
            if vals:
                out.append(tuple(vals))
    return out


def _imports(arm):
    mods = set()
    for _, tree in _trees(arm):
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                mods.add(n.module.split(".")[0])
    return mods


# ---------------------------------------------------------------- checks
# Each returns a short string. Never a number that could be summed.

def r_forbidden(arm):
    txt = _files(arm)
    instrument = [r for r, t in txt.items()
                  if os.path.basename(r) == "runrecord.py" and "FORBIDDEN" in t]
    tests = [r for r, t in txt.items()
             if "interpretation" in t and "test" in os.path.basename(r)]
    if instrument:
        return "instrument (%s)" % instrument[0]
    if tests:
        return "test only (%s)" % tests[0]
    return "not located"


def _sweep(arm, want, mod):
    rel, text = _find(arm, mod)
    if not rel:
        return "no %s" % mod
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "unparseable"
    return "swept %s" % (want,) if want in _literal_tuples(tree) else "NOT swept"


def r_dsweep(arm):
    return _sweep(arm, (8, 16, 32, 64, 128), "score.py")


def r_lsweep(arm):
    return _sweep(arm, (2, 4, 8), "score.py")


def r_status(arm):
    _, t = _find(arm, "runrecord.py")
    have = [s for s in ("ok", "void", "error", "empty") if '"%s"' % s in t]
    return "%d/4 (%s)" % (len(have), ",".join(have))


def r_record_on_failure(arm):
    _, t = _find(arm, "runrecord.py")
    try:
        tree = ast.parse(t)
    except SyntaxError:
        return "unparseable"
    for n in ast.walk(tree):
        if isinstance(n, ast.Try):
            bare = any(h.type is None or (isinstance(h.type, ast.Name)
                       and h.type.id == "Exception") for h in n.handlers)
            if bare:
                return "catches Exception, then writes"
    return "no catch-all located"


def r_network(arm):
    hit = sorted(_imports(arm) & NETWORK)
    return "clean" if not hit else "IMPORTS " + ",".join(hit)


def r_stdlib(arm):
    hit = sorted(_imports(arm) & THIRD_PARTY)
    return "clean" if not hit else "IMPORTS " + ",".join(hit)


def r_length(arm):
    worst = max(((len(t.splitlines()), r) for r, t in _files(arm).items()))
    return "max %d lines (%s)" % worst


def r_levenshtein(arm):
    rel, text = _find(arm, "score.py")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "unparseable"
    fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    hand = [f for f in fns if "lev" in f.lower() or "dist" in f.lower()]
    return "hand-written (%s)" % hand[0] if hand else "not located in score.py"


def r_stability(arm):
    _, t = _find(arm, "summarise.py")
    return "jaccard present" if "jaccard" in t.lower() else "no jaccard"


def r_thresholds(arm):
    _, t = _find(arm, "report.py")
    try:
        tree = ast.parse(t)
    except SyntaxError:
        return "unparseable"
    named = [n.targets[0].id for n in tree.body
             if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
             and n.targets[0].id.startswith("N") and n.targets[0].id.isupper()]
    return "named constants (%s)" % ",".join(named) if named else "inline"


def r_seed(arm):
    _, t = _find(arm, "runrecord.py")
    return "in record" if '"seed"' in t else "absent"


def r_permuted_branch(arm):
    """It cannot branch on which file it got if it never names one."""
    rel, t = _find(arm, "summarise.py")
    if not rel:
        return "no summarise.py"
    try:
        tree = ast.parse(t)
    except SyntaxError:
        return "unparseable"
    # A docstring is a Constant too. Skip them; a module that DESCRIBES the
    # permuted file in prose has not branched on it.
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant):
                doc.add(id(b[0].value))
    def mentions(node):
        for n in ast.walk(node):
            if id(n) in doc:
                continue
            name = (n.id if isinstance(n, ast.Name) else
                    n.attr if isinstance(n, ast.Attribute) else
                    n.value if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    else "")
            if "perm" in str(name).lower():
                return str(name)[:40]
        return None
    # The requirement is about BRANCHING, not mention. Arm a imports permute
    # to reuse its loader; reusing a loader is not branching. Three states,
    # because "mentions it without branching" is neither of the other two.
    for n in ast.walk(tree):
        if isinstance(n, ast.If):
            hit = mentions(n.test)
            if hit:
                return "BRANCHES on permuted (%s)" % hit
    hit = mentions(tree)
    return "references %s, no branch" % hit if hit else "no permuted reference"


def r_keyset_pinned(arm):
    """Found by building the arms: adding one field to the run record turned
    exactly one arm red. That arm pins the key set; the other does not."""
    for rel, t in _files(arm).items():
        if "test" in os.path.basename(rel) and "set(rec)" in t:
            return "pinned (%s)" % rel
    return "not pinned"


def r_ledger_location(arm):
    _, t = _find(arm, "runrecord.py")
    if "RUNS_PATH" in t:
        return "one global ledger"
    if "runs_path_for" in t:
        return "beside each output"
    return "not located"


def r_selection_n(arm):
    _, t = _find(arm, "score.py")
    return "carries N" if '"N"' in t else "no N field"


CHECKS = [
    ("R1", "AST+LEX", "no label/category/type/interpretation in any output schema", r_forbidden),
    ("R2", "AST", "D swept over {8,16,32,64,128}", r_dsweep),
    ("R3", "AST", "L IS AN ARGUMENT, swept over {2,4,8}, in every row", r_lsweep),
    ("R4", "LEXICAL", "status is one of ok/void/error/empty", r_status),
    ("R5", "AST", "a run that fails STILL WRITES ITS RECORD", r_record_on_failure),
    ("R6", "AST", "NO NETWORK at any point in any script", r_network),
    ("R7", "AST", "STANDARD LIBRARY ONLY", r_stdlib),
    ("R8", "AST", "nothing over ~300 lines", r_length),
    ("R9", "AST", "Levenshtein written by hand, no library", r_levenshtein),
    ("R10", "LEXICAL", "STABILITY: Jaccard over adjacent D and L", r_stability),
    ("R11", "AST", "N1-N5 printed with the number that triggered", r_thresholds),
    ("R12", "LEXICAL", "seed written into the output", r_seed),
    ("R13", "AST", "summarise runs identically on real and permuted", r_permuted_branch),
    ("R14", "LEXICAL", "run-record key set pinned by a test", r_keyset_pinned),
    ("R15", "LEXICAL", "runs.jsonl location", r_ledger_location),
    ("R16", "LEXICAL", "score row carries selection N", r_selection_n),
]

# How a discriminator gets settled. Ordered cheapest first: the order text is
# already written down; an operator decision needs a person; a measurement
# needs data nobody has yet.
SETTLED_BY = {
    "WORK_ORDER_TEXT": 0,
    "OPERATOR_DECISION": 1,
    "MEASUREMENT": 2,
}
ROUTE = {
    "R1": ("WORK_ORDER_TEXT", "the order states the rule for ANY output schema "
           "in ANY build; a per-build test does not reach that scope"),
    "R8": ("OPERATOR_DECISION", "both are under the ~300 ceiling; the difference "
           "carries no requirement"),
    "R11": ("WORK_ORDER_TEXT", "the order requires each null printed WITH its "
            "number; named constants make the number greppable, inline does not"),
    "R14": ("WORK_ORDER_TEXT", "the order makes the record schema fixed; a pin "
            "is how a fixed schema stays fixed"),
    "R15": ("WORK_ORDER_TEXT", "the order says runs.jsonl (singular) and that "
            "failed runs must be COMPARABLE ACROSS ATTEMPTS"),
    "R13": ("OPERATOR_DECISION", "neither arm branches, so both satisfy the "
            "requirement; the difference is reuse of a loader and carries no "
            "requirement"),
    "R16": ("MEASUREMENT", "selection_N comes from the reference spec's stage B; "
            "whether it is needed downstream is unmeasured"),
}


def table():
    ar = arms()
    rows = []
    for rid, kind, quote, fn in CHECKS:
        vals = {}
        for a in ar:
            try:
                vals[a] = fn(a)
            except Exception as exc:                       # noqa: BLE001
                vals[a] = "CHECK ERROR: %s" % type(exc).__name__
        rows.append({"id": rid, "kind": kind, "requirement": quote,
                     "arms": vals, "differs": len(set(vals.values())) > 1})
    return {"arms": ar, "rows": rows}


def queue():
    """Discriminators only, cheapest settlement first. Ranks REQUIREMENTS,
    never arms."""
    out = []
    for row in table()["rows"]:
        if not row["differs"]:
            continue
        route, why = ROUTE.get(row["id"], ("OPERATOR_DECISION", "not routed"))
        out.append({"id": row["id"], "requirement": row["requirement"],
                    "arms": row["arms"], "settled_by": route, "why": why})
    out.sort(key=lambda r: (SETTLED_BY[r["settled_by"]], r["id"]))
    return out


def provenance():
    """Each arm against its parent commit. The only differing files must be
    the declared edits."""
    out = []
    for a in arms():
        par = PARENT[a]
        root = os.path.join(ARMS_DIR, a)
        try:
            # git pathspecs resolve against cwd, so this must run from the
            # repo root. Run from frame-instruments/ it matched nothing and
            # the check passed over an empty denominator -- a clean verdict
            # on zero comparisons. The empty listing is now a refusal.
            top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                 cwd=HERE, capture_output=True, text=True,
                                 check=True).stdout.strip()
            listing = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", par, "--", "frame-instruments"],
                cwd=top, capture_output=True, text=True, check=True).stdout.split()
            if not listing:
                raise ValueError("parent %s lists no frame-instruments files" % par)
        except Exception as exc:                            # noqa: BLE001
            out.append({"arm": a, "parent": par, "status": "UNCHECKABLE",
                        "reason": "%s: %s" % (type(exc).__name__, exc),
                        "differs": [], "missing": [], "undeclared": [], "compared": 0})
            continue
        differs, missing = [], []
        for path in listing:
            rel = path[len("frame-instruments/"):]
            if rel.startswith(HOISTED) or any(rel.startswith(h) for h in HOISTED):
                continue
            local = os.path.join(root, rel)
            want = subprocess.run(["git", "show", "%s:%s" % (par, path)],
                                  cwd=top, capture_output=True, check=True).stdout
            if not os.path.exists(local):
                missing.append(rel)
            elif open(local, "rb").read() != want:
                differs.append(rel)
        declared = set(DECLARED_EDITS.get(a, {}))
        undeclared = sorted(set(differs) - declared)
        compared = len([p for p in listing
                        if not any(p[len("frame-instruments/"):].startswith(h)
                                   for h in HOISTED)])
        undeclared_missing = sorted(set(declared) - set(differs))
        status = ("VERBATIM+DECLARED" if not undeclared and not missing
                  and not undeclared_missing else "UNDECLARED DIVERGENCE")
        out.append({"arm": a, "parent": par, "differs": sorted(differs),
                    "missing": sorted(missing), "undeclared": undeclared,
                    "declared_but_identical": undeclared_missing,
                    "compared": compared, "status": status})
    return out


def render(t):
    ar = t["arms"]
    w = max(len(a) for a in ar)
    print("REQUIREMENT COVERAGE -- each arm against the shared work order.")
    print("No total. No ranking. A row that DIFFERS is a held fork, not a fault.\n")
    for row in t["rows"]:
        mark = "  <-- DIFFERS" if row["differs"] else ""
        print("%-4s [%-7s] %s%s" % (row["id"], row["kind"], row["requirement"], mark))
        for a in ar:
            print("       arm %-*s : %s" % (w, a, row["arms"][a]))
    n = len([r for r in t["rows"] if r["differs"]])
    print("\n%d of %d requirements differ across %d arms. "
          "Run --queue for how each is settled." % (n, len(t["rows"]), len(ar)))


def render_queue(q):
    print("DISCRIMINATOR QUEUE -- requirements where the arms differ.")
    print("Ordered by how a difference gets settled, cheapest first.")
    print("This ranks REQUIREMENTS. It does not rank arms.\n")
    for i, r in enumerate(q, 1):
        print("%d. %-4s [%s] %s" % (i, r["id"], r["settled_by"], r["requirement"]))
        for a, v in sorted(r["arms"].items()):
            print("      arm %s: %s" % (a, v))
        print("      %s\n" % r["why"])
    if not q:
        print("(empty -- the arms agree on every checked requirement)")


def render_prov(p):
    print("PROVENANCE -- each arm against the merge parent it was taken from.\n")
    for r in p:
        print("arm %s  <-  %s   %s   (%d files compared)"
              % (r["arm"], r["parent"], r["status"], r.get("compared", 0)))
        if r.get("reason"):
            print("    %s" % r["reason"])
        for f in r.get("declared_but_identical", []):
            print("    DECLARED EDIT NOT PRESENT: %s" % f)
        for f in r["differs"]:
            why = DECLARED_EDITS.get(r["arm"], {}).get(f, "UNDECLARED")
            print("    differs: %-18s %s" % (f, why))
        for f in r["missing"]:
            print("    MISSING: %s" % f)
        print()


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        import test_coverage
        return test_coverage.main()
    if "--provenance" in args:
        p = provenance()
        print(json.dumps(p, indent=2)) if "--json" in args else render_prov(p)
        return 0 if all(r["status"] == "VERBATIM+DECLARED" for r in p) else 1
    if "--queue" in args:
        q = queue()
        print(json.dumps(q, indent=2)) if "--json" in args else render_queue(q)
        return 0
    t = table()
    print(json.dumps(t, indent=2)) if "--json" in args else render(t)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
