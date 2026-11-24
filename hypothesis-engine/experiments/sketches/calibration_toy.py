#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — pilot harness for EXP-CAL-02 (see ../calibration-and-falsifiability-of-llm-agents.md)
and the calibration arm of EXP-DCM-02.

Question it instruments: how much of a reported ECE difference between two systems is
estimator choice and sample size rather than calibration? Simulates a binary-correctness
task where the true P(correct | stated confidence) is known, so the TRUE calibration error
is computable, then compares estimators:
  ece_w15   equal-width 15-bin ECE (common default)
  ece_m15   equal-mass 15-bin ECE
  brier     Brier score;  nll  log loss
for (A) a continuous-confidence model and (B) a 'verbalized' model that only states
confidences on a coarse grid {0.5,0.6,...,1.0} (typical of LLM verbal confidence).
Reports estimator mean and spread over replicates at several n, plus the true value.

    python3 calibration_toy.py [--reps 200]
"""
import argparse
import numpy as np


def ece(conf, correct, bins=15, mass=False):
    if mass:
        edges = np.quantile(conf, np.linspace(0, 1, bins + 1))
    else:
        edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.searchsorted(edges, conf, side="right") - 1, 0, bins - 1)
    tot = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            tot += m.mean() * abs(conf[m].mean() - correct[m].mean())
    return tot


def simulate(rng, n, verbal, temp=1.6):
    true_logit = rng.normal(1.0, 1.5, n)
    p_true = 1 / (1 + np.exp(-true_logit))                  # P(correct)
    conf = 1 / (1 + np.exp(-true_logit * temp))              # overconfident model
    conf = np.clip(conf, 0.5, 0.999)
    if verbal:
        conf = np.clip(np.round(conf * 10) / 10, 0.5, 1.0)
    correct = (rng.random(n) < p_true).astype(float)
    return conf, correct, p_true


def true_ce(rng, verbal, n=400_000):
    conf, _, p = simulate(rng, n, verbal)
    # true L1 calibration error: E|E[p|conf] - conf|; conf is a deterministic fn of logit
    if verbal:
        return float(sum((conf == v).mean() * abs(p[conf == v].mean() - v) for v in np.unique(conf)))
    return float(np.abs(p - conf).mean())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    for verbal in (False, True):
        print(f"\n{'verbalized grid' if verbal else 'continuous'} confidence; true L1 calibration error ~= {true_ce(rng, verbal):.4f}")
        for n in (100, 300, 1000, 5000):
            vals = {k: [] for k in ("ece_w15", "ece_m15", "brier", "nll")}
            for _ in range(a.reps):
                c, y, _ = simulate(rng, n, verbal)
                vals["ece_w15"].append(ece(c, y)); vals["ece_m15"].append(ece(c, y, mass=True))
                vals["brier"].append(((c - y) ** 2).mean())
                cc = np.clip(c, 1e-6, 1 - 1e-6)
                vals["nll"].append(-(y * np.log(cc) + (1 - y) * np.log(1 - cc)).mean())
            print(f"  n={n:5d} " + "  ".join(f"{k} {np.mean(v):.4f}±{np.std(v):.4f}" for k, v in vals.items()))
    print("\nSKETCH output on synthetic data. Use it to size samples for the real experiment, not as a finding.")
