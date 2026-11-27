#!/usr/bin/env python3
"""EXP-HVD-03 — Planted-signal recovery on a copy of the engine's own data.
Design: ../../hidden-variable-detection-causal-discovery-from-residuals.md (EXP-HVD-03).

Reads data/claim_tree.json and data/findings_log.jsonl READ-ONLY into memory; the engine's
stage_hidden writes only to a temp file. Per trial:
  1. pick a topic at random; pick each publication period (finding `date`[:7], the engine's own
     period key) present in that topic independently with prob 0.5 (resample if none or all);
  2. plant: passed += k for every claim of that topic whose finding falls in a picked period;
  3. detectors:
     a  : engine stage_hidden, unmodified (its only candidate is findings_rate). Recovered = it
          emits a suggestion for the planted topic.
     a2 : (secondary, not in the design) the engine's rule (folded residual, i mod M pairing,
          mean|res| >= 0.1 and |r| > 0.5) applied to the planted indicator series itself.
     b  : variant: signed residual (beta - 0.5); candidate aligned by each claim's own period;
          p-value from permuting the indicator across periods (999 permutations); recovered if p < 0.05.
k in {1, 2, 4}: 200 trials each; k = 0 (nothing planted, same random period sets): 200 trials -> FPR.

    python3 run.py          # numpy + stdlib; writes raw_output.json
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import ENGINE, env, save  # noqa: E402

sys.path.insert(0, str(ENGINE / "scripts"))
import hypothesis_engine as he  # noqa: E402  read-only use

TRIALS = 200
KS = (0, 1, 2, 4)
PERMS = 999


def wilson(x, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def main():
    t0 = time.time()
    findings = he.read_jsonl(ENGINE / "data/findings_log.jsonl")
    base_tree = he.load_tree(ENGINE / "data/claim_tree.json")
    period = {f["hash"]: f.get("date", "")[:7] for f in findings}
    periods_all = sorted({f.get("date", "")[:7] for f in findings if f.get("date")})
    by_topic = defaultdict(list)
    for c in base_tree.claims.values():
        by_topic[c.scope.get("topic", "")].append(c.id)
    topics = sorted(by_topic)

    # residual distribution before planting
    pre = {}
    for t in topics:
        res = np.array([abs(base_tree.claims[i].beta_confidence - 0.5) for i in by_topic[t]])
        sgn = np.array([base_tree.claims[i].beta_confidence - 0.5 for i in by_topic[t]])
        pre[t] = {"n_claims": len(res), "mean_abs_res": float(res.mean()), "sd_abs_res": float(res.std()),
                  "frac_beta_below_0.5": float((sgn < 0).mean()), "frac_beta_eq_0.5": float((sgn == 0).mean()),
                  "median_passed": float(np.median([base_tree.claims[i].passed for i in by_topic[t]])),
                  "n_periods": len({period.get(i, '') for i in by_topic[t]})}
    # unmodified engine on unmodified data (deterministic)
    with tempfile.TemporaryDirectory() as td:
        base_sugg = he.stage_hidden(copy.deepcopy(base_tree), findings, Path(td) / "h.jsonl")
    base_flag_topics = sorted({s["topic"] for s in base_sugg})

    rng = np.random.default_rng(20261127)
    rows = []
    for k in KS:
        for trial in range(TRIALS):
            t = topics[rng.integers(len(topics))]
            ids = by_topic[t]
            per = sorted({period.get(i, "") for i in ids})
            while True:
                pick = {p for p in per if rng.random() < 0.5}
                if 0 < len(pick) < len(per):
                    break
            tree = copy.deepcopy(base_tree)
            for i in ids:
                if period.get(i, "") in pick:
                    tree.claims[i].passed += k
            # (a) engine, unmodified
            with tempfile.TemporaryDirectory() as td:
                sugg = he.stage_hidden(tree, findings, Path(td) / "h.jsonl")
            rec_a = any(s["topic"] == t for s in sugg)
            claims = [tree.claims[i] for i in ids]   # same order as the engine (tree order)
            beta = np.array([c.beta_confidence for c in claims])
            # (a2) engine rule on the planted indicator, engine-style pairing
            ind_by_period = np.array([1.0 if p in pick else 0.0 for p in periods_all])
            cand_a2 = [ind_by_period[j % len(periods_all)] for j in range(len(claims))]
            res_abs = list(np.abs(beta - 0.5))
            r_a2 = he.pearson_r(res_abs, cand_a2)
            rec_a2 = (np.mean(res_abs) >= 0.1) and abs(r_a2) > 0.5 and abs(abs(r_a2) - 1) > 1e-9
            # (b) signed residual, aligned by period, period-permutation p
            res_s = beta - 0.5
            pidx = np.array([per.index(period.get(i, "")) for i in ids])
            ind = np.array([1.0 if p in pick else 0.0 for p in per])
            def stat(v):
                x = v[pidx]
                if x.std() == 0 or res_s.std() == 0:
                    return 0.0
                return abs(np.corrcoef(res_s, x)[0, 1])
            obs = stat(ind)
            null = np.array([stat(rng.permutation(ind)) for _ in range(PERMS)])
            p_b = (1 + (null >= obs - 1e-12).sum()) / (1 + PERMS)
            rows.append({"k": k, "trial": trial, "topic": t, "n_periods_topic": len(per), "n_picked": len(pick),
                         "a": bool(rec_a), "a2": bool(rec_a2), "r_a2": round(r_a2, 4),
                         "b": bool(p_b < 0.05), "p_b": round(float(p_b), 4), "r_b": round(float(obs), 4)})
    summ = {}
    for k in KS:
        R = [r for r in rows if r["k"] == k]
        summ[str(k)] = {d: {"rate": sum(r[d] for r in R) / len(R), "wilson95": wilson(sum(r[d] for r in R), len(R))}
                        for d in ("a", "a2", "b")}
        summ[str(k)]["b_median_abs_r"] = float(np.median([r["r_b"] for r in R]))
    # per-topic recovery of (b) at k=2
    per_topic = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["k"] == 2:
            per_topic[r["topic"]][0] += r["b"]; per_topic[r["topic"]][1] += 1
    out = {"env": env(), "trials_per_k": TRIALS, "perms": PERMS, "periods_all": periods_all,
           "engine_on_unplanted_data_flags_topics": base_flag_topics,
           "engine_on_unplanted_data_suggestions": base_sugg,
           "residuals_before_planting": pre, "summary": summ,
           "b_recovery_k2_by_topic": {t: v for t, v in per_topic.items()},
           "trials": rows, "runtime_s": round(time.time() - t0, 1)}
    save(HERE / "raw_output.json", out)
    print(json.dumps({"engine_unplanted_flags": base_flag_topics, "summary": summ,
                      "b_k2_by_topic": dict(per_topic)}, indent=1))
    print("runtime_s", out["runtime_s"])


if __name__ == "__main__":
    main()
