#!/usr/bin/env python3
"""EXP-ENG-04 — Replay: does NEW HYPOTHESIS track new content?  (design: ../../engine-validity.md)

Offline replay of hypothesis-engine stages 3-5 + the stage-7 marker rule over the real
findings log, one batch per engine run (grouped by retrieved_at date).

Arms
  a  current rules: the engine's own stage_claim / stage_test / stage_modify / stage_consolidate,
     imported read-only, writing only to a temp dir.
  b  each (claim, partner) pair is evaluated at most once across runs (ever, including after
     reformulation); everything else as in (a).
  c  (b) plus: a claim counts as surviving only with >= 3 distinct supporting partners from
     >= 2 distinct sources (the beta >= 0.7 shortcut is not used).
Outcomes per run x topic: flagged (>= 3 surviving), new findings, new on-topic findings by the
EXP-ENG-01 lexical screen (CORE regex in sketches/engine_audit.py).
Also: validation of arm (a) against the actual hypotheses/ history in git.

    python3 run.py            # writes raw_output.json next to this file; stdlib only
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import ENGINE, EXPERIMENTS, env, save  # noqa: E402

sys.path.insert(0, str(ENGINE / "scripts"))
sys.path.insert(0, str(EXPERIMENTS / "sketches"))
import hypothesis_engine as he  # noqa: E402  read-only use
from engine_audit import CORE  # noqa: E402

TOPICS = [t["name"] for t in json.loads((ENGINE / "config/topics.json").read_text())["topics"]]


def batches():
    rows = he.read_jsonl(ENGINE / "data/findings_log.jsonl")
    by = defaultdict(list)
    for r in rows:
        by[r["retrieved_at"][:10]].append(r)
    return [(d, by[d]) for d in sorted(by)]


def on_topic(r):
    return bool(re.search(CORE.get(r["topic"], "$^"), f"{r['title']} {r['abstract']}", re.I | re.S))


# ---------------------------------------------------------------- arm (a)
def arm_a(runs, tmp: Path):
    tree = he.DependencyTree()
    seen = []
    out = []
    for date, rows in runs:
        new = [he.Finding(**{k: r[k] for k in he.Finding.__dataclass_fields__}) for r in rows]
        he.stage_claim(new, tree, tmp / "a_unknown.jsonl")
        seen += rows
        he.stage_test(tree, seen)
        he.stage_modify(tree, tmp / "a_unknown.jsonl", tmp / "a_reform.jsonl")
        cons = he.stage_consolidate(tree, [{"name": t} for t in TOPICS], tmp / "a_unknown.jsonl",
                                    tmp / "a_hidden.jsonl", tmp / "a_hyp")
        surv = defaultdict(int)
        for c in tree.claims.values():
            if c.status == "survived" or c.beta_confidence >= 0.7:
                surv[c.scope.get("topic", "")] += 1
        out.append({"date": date, "flagged": sorted(cons["new_hypotheses"]),
                    "surviving": dict(surv)})
    return out, tree


# ---------------------------------------------------------------- arms (b), (c)
def arm_bc(runs, strict: bool):
    """Same claim/modify rules as the engine, but pairs are evaluated once ever."""
    claims = {}          # id -> state
    seen = []
    out = []
    for date, rows in runs:
        for r in rows:   # stage_claim, same text and falsifiability routing as the engine
            text = f"On topic {r['topic']}, {r['title']} reports: {he.first_sentence(r['abstract']) or '(no abstract)'}"
            fals = he.derive_falsification(r["topic"], r["abstract"])
            if he.classify_falsifiability(f"{text} {fals}") == "unfalsifiable":
                continue
            claims[r["hash"]] = {"text": text, "topic": r["topic"], "passed": 0, "failed": 0,
                                 "reform": 0, "tested": set(), "sup_sources": set(),
                                 "sup_partners": set()}
        seen += rows

        def survived(c):
            if strict:
                return len(c["sup_partners"]) >= 3 and len(c["sup_sources"]) >= 2
            return c["passed"] >= 3 or (1 + c["passed"]) / (2 + c["passed"] + c["failed"]) >= 0.7

        by_topic = defaultdict(list)
        for r in seen:
            by_topic[r["topic"]].append(r)
        for cid, c in claims.items():
            if c["failed"] >= 3 or (c["passed"] >= 3 and not strict) or (strict and survived(c)):
                continue  # absorbing, as in the engine
            for r in by_topic[c["topic"]]:
                if r["hash"] == cid or r["hash"] in c["tested"]:
                    continue
                c["tested"].add(r["hash"])
                v = he.corroboration(c["text"], f"{r.get('title','')} {r.get('abstract','')}")
                if v > 0:
                    c["passed"] += 1
                    c["sup_partners"].add(r["hash"]); c["sup_sources"].add(r["source"])
                elif v < 0:
                    c["failed"] += 1
        for cid in list(claims):  # stage_modify, same thresholds
            c = claims[cid]
            if c["failed"] >= 2 or c["failed"] >= 3:
                c["passed"] = c["failed"] = 0
                c["sup_partners"] = set(); c["sup_sources"] = set()
                c["reform"] += 1
                c["text"] += f" [restricted: narrower scope within {c['topic']} (run {date})]"
                if c["reform"] >= 3:
                    del claims[cid]
        surv = defaultdict(int)
        for c in claims.values():
            if survived(c):
                surv[c["topic"]] += 1
        out.append({"date": date, "flagged": sorted(t for t in TOPICS if surv[t] >= 3),
                    "surviving": dict(surv)})
    return out


# ---------------------------------------------------------------- actual history
def actual_history():
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                          cwd=ENGINE).stdout.strip()
    hyp = "hypothesis-engine/hypotheses"
    log = subprocess.run(["git", "log", "--reverse", "--format=%h %ad", "--date=short", "--", hyp],
                         capture_output=True, text=True, cwd=root).stdout.split("\n")
    hist = []
    for line in filter(None, log):
        sha, d = line.split()
        flagged, surv = [], {}
        for t in TOPICS:
            r = subprocess.run(["git", "show", f"{sha}:{hyp}/{he.slugify(t)}.md"], capture_output=True,
                               text=True, cwd=root)
            m = re.search(r"Status: \*\*(.*?)\*\* \((\d+) surviving", r.stdout)
            if m:
                surv[t] = int(m.group(2))
                if m.group(1) == "NEW HYPOTHESIS":
                    flagged.append(t)
        hist.append({"commit": sha, "date": d, "flagged": sorted(flagged), "surviving": surv})
    return hist


def summarize(arm, runs):
    first = {}
    after_total = after_flagged = after_zero_new = after_zero_new_flagged = 0
    unflag_after_cross = []
    for i, (rec, (date, rows)) in enumerate(zip(arm, runs)):
        new_on = defaultdict(int)
        for r in rows:
            new_on[r["topic"]] += on_topic(r)
        rec["new_on_topic"] = dict(new_on)
        rec["new_findings"] = {t: sum(r["topic"] == t for r in rows) for t in TOPICS}
        for t in TOPICS:
            if t in first:
                after_total += 1
                f = t in rec["flagged"]
                after_flagged += f
                if new_on[t] == 0:
                    after_zero_new += 1
                    after_zero_new_flagged += f
                if not f:
                    unflag_after_cross.append((date, t))
            elif t in rec["flagged"]:
                first[t] = date
    return {"first_crossing": first, "topic_runs_after_first_crossing": after_total,
            "flagged_after_first_crossing": after_flagged,
            "topic_runs_after_crossing_with_0_new_on_topic": after_zero_new,
            "of_which_flagged": after_zero_new_flagged,
            "unflagged_after_crossing": unflag_after_cross,
            "flags_total": sum(len(r["flagged"]) for r in arm)}


def main():
    t0 = time.time()
    e = env()
    runs = batches()
    with tempfile.TemporaryDirectory() as td:
        a, tree = arm_a(runs, Path(td))
    b = arm_bc(runs, strict=False)
    c = arm_bc(runs, strict=True)
    res = {"env": e, "n_runs": len(runs), "run_dates": [d for d, _ in runs],
           "arms": {"a": summarize(a, runs), "b": summarize(b, runs), "c": summarize(c, runs)},
           "per_run": {"a": a, "b": b, "c": c}}
    # validation of arm (a) against the real tree and the real git history
    real = json.loads((ENGINE / "data/claim_tree.json").read_text())["claims"]
    real_surv = defaultdict(int)
    for cl in real:
        if cl["status"] == "survived" or cl["beta_confidence"] >= 0.7:
            real_surv[cl["scope"]["topic"]] += 1
    res["validation"] = {"final_surviving_replay_a": a[-1]["surviving"],
                         "final_surviving_real_tree": dict(real_surv),
                         "claims_replay_a": len(tree.claims), "claims_real": len(real),
                         "actual_history": actual_history()}
    res["runtime_s"] = round(time.time() - t0, 1)
    save(HERE / "raw_output.json", res)
    for k in "abc":
        s = res["arms"][k]
        print(k, {kk: v for kk, v in s.items() if kk != "unflagged_after_crossing"},
              "unflagged:", len(s["unflagged_after_crossing"]))
    print("final surviving replay(a) vs real:")
    for t in TOPICS:
        print(f"  {t[:50]:50s} {a[-1]['surviving'].get(t,0):4d} {real_surv.get(t,0):4d}")
    print("runtime_s", res["runtime_s"])


if __name__ == "__main__":
    main()
