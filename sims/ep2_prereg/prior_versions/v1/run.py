#!/usr/bin/env python3
"""ep2_prereg/run.py — harness-standard E-P2 pre-registration.
Reads config.json only. Runs seeds x noise sweep x null arm. Grades itself.
Writes results/<timestamp>/{metrics.json, summary.md, ledger_entry.jsonl}."""
import json, hashlib, sys, time, os
import numpy as np

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "config.json")))
P = CFG["params"]

def tau_true(comp, creep, snap, tau0, c0):
    k_rel = np.sqrt(max(1e-9, 1.0 - comp/snap)) * (1.0 - creep)
    return tau0 * np.sqrt(1.0 - c0/snap) / k_rel

def tau_null(comp, creep, tau0):
    return tau0 * (1.0 + 0.5*creep)   # drift only, no fold

def detect_lead(rng, noise, null=False):
    comps = np.arange(P["baseline_compression"], P["snap_compression"], P["step"])
    taus = []
    for i, c in enumerate(comps):
        t = tau_null(c, P["creep_per_step"]*i, P["tau0"]) if null else \
            tau_true(c, P["creep_per_step"]*i, P["snap_compression"], P["tau0"], P["baseline_compression"])
        taus.append(np.mean(t*(1+noise*rng.standard_normal(P["flicks_per_step"]))))
    taus = np.array(taus); base = taus[:5]
    for i in range(5, len(comps)):
        cur = taus[i]*(1+noise*rng.standard_normal(P["flicks_per_step"]))
        tstat = (cur.mean()-base.mean())/np.sqrt(cur.var(ddof=1)/5 + base.var(ddof=1)/5)
        if tstat > P["t_stat_threshold"]:
            return (P["snap_compression"] - comps[i]) / 0.30, True
    return 0.0, False

results = {"config": CFG, "arms": {}}
verdicts = []
for noise in CFG["sweeps"]["timing_noise"]:
    for arm, null in [("bistable", False), ("rigid_null", True)]:
        per_seed = {}
        for seed in CFG["seeds"]:
            rng = np.random.default_rng(seed*1000 + int(noise*100))
            leads, det = [], 0
            for _ in range(P["n_trials_per_seed"]):
                lead, fired = detect_lead(rng, noise, null)
                leads.append(lead); det += fired
            per_seed[str(seed)] = {"detection_rate": det/P["n_trials_per_seed"],
                                   "median_lead": float(np.median([l for l in leads if l > 0] or [0]))}
        results["arms"][f"{arm}_noise{noise}"] = per_seed

# --- self-grading against REFUTE.md ---
def median_leads(arm_key):
    return [results["arms"][arm_key][s]["median_lead"] for s in results["arms"][arm_key]]
def det_rates(arm_key):
    return [results["arms"][arm_key][s]["detection_rate"] for s in results["arms"][arm_key]]

central = "bistable_noise0.05"
null_central = "rigid_null_noise0.05"
fails = sum(1 for l in median_leads(central) if l < 0.15)
null_rate = float(np.mean(det_rates(null_central)))
robust = all(np.median(median_leads(f"bistable_noise{n}")) >= 0.15 for n in CFG["sweeps"]["timing_noise"])

if fails >= 3 or null_rate > 0.20:
    verdict = "REFUTED"
    reason = f"seeds failing 15% lead: {fails}/5; null detection rate {null_rate:.2f}"
elif fails > 1 or not robust:
    verdict = "INCONCLUSIVE"
    reason = f"seed-variable or noise-fragile (fails={fails}, robust={robust}, null={null_rate:.2f})"
else:
    verdict = "SUPPORTED"
    reason = f"median lead {np.median(median_leads(central))*100:.0f}% >= 15% at >=4/5 seeds; null rate {null_rate:.2f} <= 0.20; robust across noise sweep: {robust}"

results["verdict"] = verdict
results["verdict_reason"] = reason

# --- write outputs ---
ts = time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
outdir = os.path.join(os.path.dirname(__file__), "results", ts)
os.makedirs(outdir, exist_ok=True)
mj = json.dumps(results, indent=1)
mh = hashlib.sha256(mj.encode()).hexdigest()
ch = hashlib.sha256(json.dumps(CFG, sort_keys=True).encode()).hexdigest()
json.dump(results, open(os.path.join(outdir, "metrics.json"), "w"), indent=1)

entry = {"type": "PREDICT", "claim": CFG["claim"], "refute_if": CFG["refute_if"],
         "verdict": verdict, "reason": reason,
         "metrics_hash": mh, "config_hash": ch, "seeds": len(CFG["seeds"]),
         "null_model": CFG["null_model"], "sim": "ep2_prereg", "run": ts}
with open(os.path.join(outdir, "ledger_entry.jsonl"), "w") as f:
    f.write(json.dumps(entry) + "\n")

with open(os.path.join(outdir, "summary.md"), "w") as f:
    f.write(f"# E-P2 pre-registration run {ts}\n\n**Verdict: {verdict}** — {reason}\n\n")
    for k in results["arms"]:
        f.write(f"## {k}\n")
        for s, d in results["arms"][k].items():
            f.write(f"- seed {s}: detection {d['detection_rate']:.2f}, median lead {d['median_lead']*100:.1f}%\n")

print(f"VERDICT: {verdict} — {reason}")
print(f"outputs -> {outdir}")
