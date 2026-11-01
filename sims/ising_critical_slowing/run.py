#!/usr/bin/env python3
"""ising_critical_slowing -- autocorrelation time vs L at Tc, plus the G7 start-state record.

Co-authored (Kavik + Claude, 2026-11-01). CC0. stdlib only. Pre-registration: REFUTE.md, NULL.md
(committed before this file). Synthetic model; says nothing observational.

Estimator note (implementation detail REFUTE.md left open): the normalised autocorrelation of
|m| is evaluated at lags 1..20 and then at lags growing 5% per step, integrated by the
trapezoid rule; the window stops at the first lag M with M >= c * tau(M), c = 6. Checked
against an AR(1) series of known tau in --check-estimator.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

TC = 2.269
_CACHE: dict = {}


def metropolis_series(L: int, T: float, sweeps: int, burn: int, rng: random.Random, start: str) -> list:
    N = L * L
    s = [1] * N if start == "ordered" else [rng.choice((-1, 1)) for _ in range(N)]
    nb = [((i // L) * L + (i + 1) % L, (i // L) * L + (i - 1) % L, (i + L) % N, (i - L) % N) for i in range(N)]
    w = {4: math.exp(-4.0 / T), 8: math.exp(-8.0 / T)}
    rand, randrange = rng.random, rng.randrange
    out = []
    M = sum(s)
    for sweep in range(burn + sweeps):
        for _ in range(N):
            i = randrange(N)
            a, b, c, d = nb[i]
            dE = 2 * s[i] * (s[a] + s[b] + s[c] + s[d])
            if dE <= 0 or rand() < w[dE]:
                s[i] = -s[i]
                M += 2 * s[i]
        if sweep >= burn:
            out.append(abs(M) / N)
    return out


def tau_int(x: list, c: float = 6.0) -> float:
    n = len(x)
    m = sum(x) / n
    d = [v - m for v in x]
    var = sum(v * v for v in d) / n
    if var == 0:
        return 0.5

    def rho(t):
        return sum(d[i] * d[i + t] for i in range(n - t)) / ((n - t) * var)

    lags, vals = [0], [1.0]
    t = 1
    tau = 0.5
    while t < n // 2:
        lags.append(t)
        vals.append(rho(t))
        tau = 0.5 + sum((lags[k] - lags[k - 1]) * (vals[k] + vals[k - 1]) / 2 for k in range(1, len(lags))) - 0.5
        tau = max(tau, 0.5)
        if t >= c * tau:
            break
        t = t + 1 if t < 20 else max(t + 1, int(t * 1.05))
    return tau


def measure(seed: int, point: dict, config: dict) -> dict:
    mc = config["mc"]
    T, L = point["T"], point["L"]
    sweeps = mc["sweeps_T_1_5"] if T == 1.5 else mc["sweeps_by_L"][str(L)]
    rng = random.Random(seed * 1000 + L * 10 + int(T * 100))
    xo = metropolis_series(L, T, sweeps, mc["burn_in"], rng, "ordered")
    _CACHE[(seed, T, L)] = xo
    out = {"tau_ordered": tau_int(xo, mc["window_c"]), "mean_abs_m_ordered": sum(xo) / len(xo)}
    if T == 1.5:   # G7: recorded, not graded
        xr = metropolis_series(L, T, sweeps, mc["burn_in"], rng, "random")
        out["tau_random_start"] = tau_int(xr, mc["window_c"])
        out["mean_abs_m_random_start"] = sum(xr) / len(xr)
    return out


def null(seed: int, point: dict, config: dict) -> dict:
    x = list(_CACHE[(seed, point["T"], point["L"])])
    random.Random(seed + 99).shuffle(x)
    return {"tau_shuffled": tau_int(x, config["mc"]["window_c"])}


def slope(Ls, taus):
    xs = [math.log(v) for v in Ls]
    ys = [math.log(max(v, 1e-9)) for v in taus]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)


def grade(obs: list, null_obs: list, config: dict) -> Verdict:
    rp = config["refute_params"]
    seeds = config["seeds"]
    Ls = config["sweeps"]["L"]
    tau = {(r["seed"], r["sweep"]["T"], r["sweep"]["L"]): r["metrics"]["tau_ordered"] for r in obs}
    floor = {(r["seed"], r["sweep"]["T"], r["sweep"]["L"]): r["metrics"]["tau_shuffled"] for r in null_obs}
    z_tc = {s: slope(Ls, [tau[(s, TC, L)] for L in Ls]) for s in seeds}
    z_hot = {s: slope(Ls, [tau[(s, 3.0, L)] for L in Ls]) for s in seeds}
    short = [s for s in seeds if tau[(s, TC, max(Ls))] < rp["floor_multiple"] * floor[(s, TC, max(Ls))]]
    detail = {"z_tc": z_tc, "z_hot": z_hot, "tau_tc_Lmax": {s: tau[(s, TC, max(Ls))] for s in seeds},
              "g7_T1_5": {s: {L: (tau[(s, 1.5, L)],
                                  next(r["metrics"]["tau_random_start"] for r in obs
                                       if r["seed"] == s and r["sweep"]["T"] == 1.5 and r["sweep"]["L"] == L))
                              for L in Ls} for s in seeds}}
    if len(short) >= 2:
        return Verdict(INCONCLUSIVE, "tau(Tc, L=%d) under %gx the shuffled floor at %d seeds: runs too short"
                       % (max(Ls), rp["floor_multiple"], len(short)), detail)
    bad = [s for s in seeds if z_tc[s] < rp["z_tc_min"] or z_hot[s] >= rp["z_hot_max"]]
    zt = sorted(z_tc.values())
    zh = sorted(z_hot.values())
    if len(bad) >= rp["refute_at_seeds"]:
        return Verdict(REFUTED, "z(Tc) %.2f-%.2f, z(3.0) %.2f-%.2f; %d seeds fail" % (zt[0], zt[-1], zh[0], zh[-1], len(bad)), detail)
    if len(seeds) - len(bad) >= rp["support_at_seeds"]:
        return Verdict(SUPPORTED, "z(Tc) %.2f-%.2f >= %.1f and z(3.0) %.2f-%.2f < %.1f at %d of %d seeds"
                       % (zt[0], zt[-1], rp["z_tc_min"], zh[0], zh[-1], rp["z_hot_max"], len(seeds) - len(bad), len(seeds)), detail)
    return Verdict(INCONCLUSIVE, "%d seeds fail, between thresholds" % len(bad), detail)


def check_estimator():
    rng = random.Random(1)
    for phi in (0.5, 0.9, 0.98):
        x, v = [], 0.0
        for _ in range(40000):
            v = phi * v + rng.gauss(0, 1)
            x.append(v)
        true = 0.5 * (1 + phi) / (1 - phi)
        print("AR(1) phi=%.2f  true tau_int %.2f  estimated %.2f" % (phi, true, tau_int(x)))


if __name__ == "__main__":
    if "--check-estimator" in sys.argv:
        check_estimator()
        sys.exit(0)
    v = run(HERE / "config.json", measure, null, grade)
    sys.exit(0)
