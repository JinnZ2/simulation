#!/usr/bin/env python3
"""ep2_prereg_v3/run.py — fixed-checkpoint differential E-P2. No scanning, one t-test."""
import json, hashlib, time, os
import numpy as np

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "config.json")))
P = CFG["params"]
C0, CHK = P["baseline_compression"], P["checkpoint"]

def tau_fold(c, cr): return P["tau0"]*np.sqrt(1-C0/P["snap_compression"])/(np.sqrt(max(1e-9,1-c/P["snap_compression"]))*(1-cr))
def tau_rigid(c, cr): return P["tau0"]*(1+0.5*cr)

def meas(rng, noise, fold, comp, i):
    cr = P["creep_per_step"]*i*(1+0.2*rng.standard_normal())
    t = tau_fold(comp, cr) if fold else tau_rigid(comp, cr)
    return t*(1+noise*rng.standard_normal(P["flicks_per_step"]))

def trial(rng, noise, null):
    # baseline ratio (compression C0, i=0) and checkpoint ratio (CHK)
    def ratio(comp, i):
        a = meas(rng, noise, not null, comp, i)   # test arm (rigid when null)
        b = meas(rng, noise, False, comp, i)      # control arm
        return np.mean(a)/np.mean(b)
    r0 = np.mean([ratio(C0, 0) for _ in range(3)])
    r1s = np.array([ratio(CHK, int((CHK-C0)/P["step"])) for _ in range(3)])
    r0s = np.array([ratio(C0, 0) for _ in range(3)])
    tstat = (r1s.mean()-r0s.mean())/np.sqrt(r1s.var(ddof=1)/3 + r0s.var(ddof=1)/3 + 1e-12)
    return tstat > 1.86

results = {"config": CFG, "arms": {}}
for noise in CFG["sweeps"]["timing_noise"]:
    for arm, null in [("checkpoint", False), ("checkpoint_null", True)]:
        per = {}
        for seed in CFG["seeds"]:
            rng = np.random.default_rng(seed*1000+int(noise*100))
            hits = sum(trial(rng, noise, null) for _ in range(60))
            per[str(seed)] = {"positive_rate": hits/60}
        results["arms"][f"{arm}_noise{noise}"] = per

def rates(k): return [results["arms"][k][s]["positive_rate"] for s in results["arms"][k]]
det5 = rates("checkpoint_noise0.05"); nul5 = rates("checkpoint_null_noise0.05")
det10 = rates("checkpoint_noise0.1")
c1 = sum(1 for r in det5 if r > 0.8)          # seed-level: fires in >80% of trials
c2 = float(np.mean(nul5))
c3 = np.median(det10) > 0.5
if c1 < 4 or c2 > 0.10 or not c3:
    verdict = "REFUTED"; reason = f"seeds>80%: {c1}/5; null FP {c2:.2f}; 10%-noise median {np.median(det10):.2f}"
else:
    verdict = "SUPPORTED"; reason = f"{c1}/5 seeds fire >80%; null FP {c2:.2f}<=0.10; 10% noise median {np.median(det10):.2f}"
results["verdict"] = verdict; results["verdict_reason"] = reason

ts = time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
outdir = os.path.join(os.path.dirname(__file__), "results", ts); os.makedirs(outdir, exist_ok=True)
mj = json.dumps(results, indent=1)
json.dump(results, open(os.path.join(outdir,"metrics.json"),"w"), indent=1)
entry = {"type":"PREDICT","claim":CFG["claim"],"refute_if":CFG["refute_if"],"verdict":verdict,
         "reason":reason,"metrics_hash":hashlib.sha256(mj.encode()).hexdigest(),
         "config_hash":hashlib.sha256(json.dumps(CFG,sort_keys=True).encode()).hexdigest(),
         "seeds":len(CFG["seeds"]),"sim":"ep2_prereg_v3","run":ts}
open(os.path.join(outdir,"ledger_entry.jsonl"),"w").write(json.dumps(entry)+"\n")
open(os.path.join(outdir,"summary.md"),"w").write(
    f"# E-P2 v3 (fixed checkpoint) {ts}\n\n**Verdict: {verdict}** — {reason}\n\n" +
    "\n".join(f"## {k}\n" + "\n".join(f"- seed {s}: positive rate {d['positive_rate']:.2f}"
              for s,d in results['arms'][k].items()) for k in results["arms"]))
print(f"VERDICT: {verdict} — {reason}")
print(f"-> {outdir}")
