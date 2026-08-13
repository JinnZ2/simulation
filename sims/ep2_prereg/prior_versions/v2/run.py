#!/usr/bin/env python3
"""ep2_prereg_v2/run.py — differential E-P2. Bistable arm minus rigid control arm,
same compression schedule, independent creep realizations. Null = two rigid struts."""
import json, hashlib, time, os
import numpy as np

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "config.json")))
P = CFG["params"]

def tau_fold(comp, creep, snap, tau0, c0):
    return tau0 * np.sqrt(1.0 - c0/snap) / (np.sqrt(max(1e-9, 1.0 - comp/snap)) * (1.0 - creep))

def tau_rigid(comp, creep, tau0):
    return tau0 * (1.0 + 0.5*creep)

def arm_series(rng, noise, fold):
    comps = np.arange(P["baseline_compression"], P["snap_compression"], P["step"])
    out = []
    for i, c in enumerate(comps):
        creep = P["creep_per_step"]*i * (1 + 0.2*rng.standard_normal())  # per-arm creep realization
        t = tau_fold(c, creep, P["snap_compression"], P["tau0"], P["baseline_compression"]) if fold \
            else tau_rigid(c, creep, P["tau0"])
        out.append(np.mean(t*(1+noise*rng.standard_normal(P["flicks_per_step"]))))
    return comps, np.array(out)

def trial(rng, noise, null):
    a = arm_series(rng, noise, fold=not null)
    b = arm_series(rng, noise, fold=False)   # control arm always rigid
    comps = a[0]; diff = a[1]/b[1]           # ratio removes multiplicative drift
    base = diff[:5]
    for i in range(5, len(comps)):
        cur = diff[i]*(1+noise*rng.standard_normal(P["flicks_per_step"]))
        tstat = (cur.mean()-base.mean())/np.sqrt(cur.var(ddof=1)/5 + base.var(ddof=1)/5)
        if tstat > P["t_stat_threshold"]:
            return (P["snap_compression"]-comps[i])/0.30, True
    return 0.0, False

results = {"config": CFG, "arms": {}}
for noise in CFG["sweeps"]["timing_noise"]:
    for arm, null in [("differential", False), ("differential_null", True)]:
        per_seed = {}
        for seed in CFG["seeds"]:
            rng = np.random.default_rng(seed*1000 + int(noise*100))
            leads, det = [], 0
            for _ in range(P["n_trials_per_seed"]):
                lead, fired = trial(rng, noise, null)
                leads.append(lead); det += fired
            per_seed[str(seed)] = {"detection_rate": det/P["n_trials_per_seed"],
                                   "median_lead": float(np.median([l for l in leads if l > 0] or [0]))}
        results["arms"][f"{arm}_noise{noise}"] = per_seed

def med(key): return [results["arms"][key][s]["median_lead"] for s in results["arms"][key]]
def det(key): return [results["arms"][key][s]["detection_rate"] for s in results["arms"][key]]
central, nullc = "differential_noise0.05", "differential_null_noise0.05"
fails = sum(1 for l in med(central) if l < 0.15)
null_rate = float(np.mean(det(nullc)))
robust = all(np.median(med(f"differential_noise{n}")) >= 0.15 for n in CFG["sweeps"]["timing_noise"])

if fails >= 3 or null_rate > 0.20:
    verdict, reason = "REFUTED", f"fails={fails}/5, null rate {null_rate:.2f}"
elif fails > 1 or not robust:
    verdict, reason = "INCONCLUSIVE", f"fails={fails}, robust={robust}, null={null_rate:.2f}"
else:
    verdict, reason = "SUPPORTED", f"median lead {np.median(med(central))*100:.0f}%, null {null_rate:.2f}, robust={robust}"
results["verdict"] = verdict; results["verdict_reason"] = reason

ts = time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
outdir = os.path.join(os.path.dirname(__file__), "results", ts); os.makedirs(outdir, exist_ok=True)
mj = json.dumps(results, indent=1)
json.dump(results, open(os.path.join(outdir, "metrics.json"), "w"), indent=1)
entry = {"type": "PREDICT", "claim": CFG["claim"], "refute_if": CFG["refute_if"],
         "verdict": verdict, "reason": reason,
         "metrics_hash": hashlib.sha256(mj.encode()).hexdigest(),
         "config_hash": hashlib.sha256(json.dumps(CFG, sort_keys=True).encode()).hexdigest(),
         "seeds": len(CFG["seeds"]), "sim": "ep2_prereg_v2", "run": ts}
open(os.path.join(outdir, "ledger_entry.jsonl"), "w").write(json.dumps(entry)+"\n")
with open(os.path.join(outdir, "summary.md"), "w") as f:
    f.write(f"# E-P2 v2 (differential) run {ts}\n\n**Verdict: {verdict}** — {reason}\n")
    for k in results["arms"]:
        f.write(f"\n## {k}\n")
        for s, d in results["arms"][k].items():
            f.write(f"- seed {s}: det {d['detection_rate']:.2f}, lead {d['median_lead']*100:.1f}%\n")
print(f"VERDICT: {verdict} — {reason}")
print(f"-> {outdir}")
