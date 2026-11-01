#!/usr/bin/env python3
"""lattice_anisotropy -- cubic-axis alignment statistic with orientation scan + exposure correction.

Co-authored (Kavik + Claude, 2026-11-01). CC0. stdlib only. Pre-registration: REFUTE.md, NULL.md
(committed before this file). SYNTHETIC skies only -- no observational data (the Pierre Auger
release was unreachable 2026-11-01; ../simulation_register/auger_loader_stub.py refuses).
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

_THR: dict = {}
_FA: dict = {}


def rot_from_quat(q):
    a, b, c, d = q
    return ((a*a+b*b-c*c-d*d, 2*(b*c-a*d), 2*(b*d+a*c)),
            (2*(b*c+a*d), a*a-b*b+c*c-d*d, 2*(c*d-a*b)),
            (2*(b*d-a*c), 2*(c*d+a*b), a*a-b*b-c*c+d*d))


def random_rotation(rng):
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(v * v for v in q))
    return rot_from_quat([v / n for v in q])


def iso(rng):
    z = 2 * rng.random() - 1
    p = 2 * math.pi * rng.random()
    r = math.sqrt(1 - z * z)
    return (r * math.cos(p), r * math.sin(p), z)


def exposure_weight(u):
    dec = math.asin(max(-1.0, min(1.0, u[2])))
    if dec >= math.radians(45):
        return 0.0
    return max(0.0, math.cos(dec + math.radians(35)))


def draw(rng, n, kind, cfg, f=0.0):
    st = cfg["stat"]
    out = []
    if kind == "aligned":
        R = random_rotation(rng)            # true lattice, not on the scan grid
        sig = math.radians(st["aligned_spread_deg"])
    if kind == "dipole":
        dvec = iso(rng)
        A = st["dipole_amplitude"]
    while len(out) < n:
        if kind == "aligned" and rng.random() < f:
            ax = [0.0, 0.0, 0.0]
            ax[rng.randrange(3)] = rng.choice((-1.0, 1.0))
            v = [ax[i] + rng.gauss(0, sig) for i in range(3)]
            nv = math.sqrt(sum(x * x for x in v))
            v = [x / nv for x in v]
            # lattice frame -> sky frame: R^T v
            u = tuple(sum(R[j][i] * v[j] for j in range(3)) for i in range(3))
            out.append(u)
            continue
        u = iso(rng)
        if kind == "exposure" and rng.random() > exposure_weight(u):
            continue
        if kind == "dipole":
            c = sum(a * b for a, b in zip(u, dvec))
            if rng.random() > (1 + A * c) / (1 + A):
                continue
        out.append(u)
    return out


def scanned_stat(ev, rots):
    best = 0.0
    n = len(ev)
    for R in rots:
        (a0, a1, a2), (b0, b1, b2), (c0, c1, c2) = R
        s = 0.0
        for x, y, z in ev:
            p = a0 * x + a1 * y + a2 * z
            q = b0 * x + b1 * y + b2 * z
            r = c0 * x + c1 * y + c2 * z
            p *= p; q *= q; r *= r
            s += p * p + q * q + r * r
        s /= n
        if s > best:
            best = s
    return best


def rotations(cfg):
    rng = random.Random(cfg["stat"]["orientation_seed"])
    return [random_rotation(rng) for _ in range(cfg["stat"]["orientations"])]


def threshold(seed, n, exposure, cfg, rots):
    key = (seed, n, exposure)
    if key not in _THR:
        rng = random.Random(seed * 7919 + n + (1 if exposure else 0) * 104729)
        vals = sorted(scanned_stat(draw(rng, n, "exposure" if exposure else "iso", cfg), rots)
                      for _ in range(cfg["stat"]["null_skies"]))
        _THR[key] = vals[min(len(vals) - 1, int((1 - cfg["stat"]["alpha"]) * len(vals)))]
    return _THR[key]


def false_alarms(seed, n, cfg, rots):
    key = (seed, n)
    if key not in _FA:
        rng = random.Random(seed * 31 + n * 17 + 5)
        k = cfg["stat"]["test_skies"]
        t_uni, t_exp = threshold(seed, n, False, cfg, rots), threshold(seed, n, True, cfg, rots)
        dip = sum(scanned_stat(draw(rng, n, "dipole", cfg), rots) > t_uni for _ in range(k)) / k
        exp_vals = [scanned_stat(draw(rng, n, "exposure", cfg), rots) for _ in range(k)]
        _FA[key] = {"fa_dipole": dip,
                    "fa_exposure_corrected": sum(v > t_exp for v in exp_vals) / k,
                    "fa_exposure_uncorrected": sum(v > t_uni for v in exp_vals) / k}
    return _FA[key]


def measure(seed, point, cfg):
    rots = rotations(cfg)
    n, f = point["n_events"], point["aligned_fraction"]
    t = threshold(seed, n, False, cfg, rots)
    rng = random.Random(seed * 1009 + n + int(f * 1000))
    k = cfg["stat"]["test_skies"]
    power = sum(scanned_stat(draw(rng, n, "aligned", cfg, f), rots) > t for _ in range(k)) / k
    out = {"power": power, "threshold_uniform": t}
    out.update(false_alarms(seed, n, cfg, rots))
    return out


def null(seed, point, cfg):
    rots = rotations(cfg)
    n = point["n_events"]
    t = threshold(seed, n, False, cfg, rots)
    rng = random.Random(seed * 2003 + n + int(point["aligned_fraction"] * 1000) + 1)
    k = cfg["stat"]["test_skies"]
    return {"fa_isotropic": sum(scanned_stat(draw(rng, n, "iso", cfg), rots) > t for _ in range(k)) / k}


def grade(obs, null_obs, cfg):
    rp = cfg["refute_params"]
    seeds = cfg["seeds"]
    pp = rp["power_point"]
    fails, neg_ok = {s: [] for s in seeds}, {s: False for s in seeds}
    for r in obs:
        s, p, m = r["seed"], r["sweep"], r["metrics"]
        if m["fa_dipole"] > rp["max_false_alarm"]:
            fails[s].append("dipole FA %.3f at n=%d" % (m["fa_dipole"], p["n_events"]))
        if m["fa_exposure_corrected"] > rp["max_false_alarm"]:
            fails[s].append("corrected-exposure FA %.3f at n=%d" % (m["fa_exposure_corrected"], p["n_events"]))
        if m["fa_exposure_uncorrected"] > rp["max_false_alarm"]:
            neg_ok[s] = True
        if p["n_events"] == pp["n_events"] and p["aligned_fraction"] == pp["aligned_fraction"] and m["power"] < rp["min_power"]:
            fails[s].append("power %.2f at the power point" % m["power"])
    fails = {s: sorted(set(v)) for s, v in fails.items()}
    detail = {"failing": {str(s): v for s, v in fails.items() if v},
              "uncorrected_exposure_triggered": {str(s): v for s, v in neg_ok.items()},
              "power": {"%s|n=%d|f=%.2f" % (r["seed"], r["sweep"]["n_events"], r["sweep"]["aligned_fraction"]):
                        r["metrics"]["power"] for r in obs},
              "fa_isotropic_null": [r["metrics"]["fa_isotropic"] for r in null_obs]}
    bad = [s for s in seeds if fails[s]]
    if len(bad) >= rp["refute_at_seeds"]:
        return Verdict(REFUTED, "%d of %d seeds fail: %s" % (len(bad), len(seeds), fails[bad[0]]), detail)
    if sum(neg_ok.values()) < rp["support_at_seeds"]:
        return Verdict(INCONCLUSIVE, "uncorrected exposure triggered at only %d of %d seeds: the required "
                       "negative case tested nothing" % (sum(neg_ok.values()), len(seeds)), detail)
    if len(seeds) - len(bad) >= rp["support_at_seeds"]:
        pw = [r["metrics"]["power"] for r in obs if r["sweep"] == pp]
        return Verdict(SUPPORTED, "false alarms <= %.2f on dipole and corrected exposure, power %.2f-%.2f at n=%d f=%.2f, "
                       "uncorrected exposure triggers at %d/%d seeds" % (
                           rp["max_false_alarm"], min(pw), max(pw), pp["n_events"], pp["aligned_fraction"],
                           sum(neg_ok.values()), len(seeds)), detail)
    return Verdict(INCONCLUSIVE, "between thresholds: %d failing seeds" % len(bad), detail)


if __name__ == "__main__":
    run(HERE / "config.json", measure, null, grade)
