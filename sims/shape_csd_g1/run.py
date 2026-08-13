#!/usr/bin/env python3
"""shape_csd_g1 — the CSD claim against a GEOMETRY-MATCHED control.

Successor to `shape_csd` (REFUTED). Reads ONLY config.json + CLI overrides (§3).
EXPLORATORY — see REFUTE.md. Stdlib only.

One change from the parent, and only one: the monostable control arm now sits at
the same rest length as the bistable arm (1.8, not the 1.5 well midpoint) and
carries the quartic's exact curvature at that point (0.864 = 2a(l2-l1)^2). The
two frames now start in identical geometry and differ only in whether a second
well exists.

Every threshold, the detection rule and the probe sweep are unchanged from the
parent. Nothing was relaxed; the control was made fairer, not weaker.

Added: a `barrier_crossings` diagnostic counting compressions where the probe
left the strut in the wrong well — so a failure at high probe magnitude is
attributable rather than merely recorded. It carries no threshold.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

CONFIG = Path(__file__).resolve().parent / "config.json"

V0 = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
EDGES = [(i, j) for i in range(6) for j in range(i + 1, 6)
         if abs(sum(a * b for a, b in zip(V0[i], V0[j]))) < 0.5]
BI = EDGES.index((0, 2))          # the strut under test
D0 = math.sqrt(2.0)


# --------------------------------------------------------------------------
# Mechanics — unchanged from the original except for the monostable option
# --------------------------------------------------------------------------

def strut_force(length: float, m: dict[str, Any], bistable: bool) -> float:
    """Force along the strut. Bistable: quartic with wells at l1, l2.

    Monostable (the null): an ordinary linear spring with rest length at the
    midpoint of the two wells, so it sits in the same geometric regime with no
    second well to snap into.
    """
    l1, l2 = m["l1"], m["l2"]
    if bistable:
        return -2 * m["aa"] * (length - l1) * (length - l2) * (2 * length - l1 - l2)
    # Geometry-matched control: same rest length as the bistable arm's starting
    # well, and the quartic's exact curvature there. The parent used the well
    # midpoint, which put the two arms in different configurations.
    return -m["monostable_stiffness"] * (length - m["monostable_rest_length"])


def relax(V, comp: float, iters: int, m: dict[str, Any], bistable: bool,
          kick=None):
    V = [list(v) for v in V]
    if kick is not None:
        V[kick[0]][kick[1]] += kick[2]
    rate = m["relax_rate"]
    for _ in range(iters):
        G = [[0.0] * 3 for _ in range(6)]
        for k, (i, j) in enumerate(EDGES):
            d = [V[i][a] - V[j][a] for a in range(3)]
            length = math.sqrt(sum(x * x for x in d)) + 1e-12
            if k == BI:
                f = strut_force(length, m, bistable) / length
            else:
                f = (length - D0 * (1 - comp)) / length
            for a in range(3):
                G[i][a] += f * d[a]
                G[j][a] -= f * d[a]
        for i in range(6):
            for a in range(3):
                V[i][a] -= rate * G[i][a]
    return V


def strut_len(V) -> float:
    i, j = EDGES[BI]
    return math.sqrt(sum((V[i][a] - V[j][a]) ** 2 for a in range(3)))


def start_config(m: dict[str, Any]):
    """Octahedron with the strut set to its long stable length."""
    V = [list(v) for v in V0]
    i, j = EDGES[BI]
    d = [V[i][a] - V[j][a] for a in range(3)]
    scale = m["l2"] / math.sqrt(sum(x * x for x in d))
    V[j] = [V[i][a] - d[a] * scale for a in range(3)]
    return V


def find_snap(m: dict[str, Any]) -> float:
    """Ramp compression until the strut drops to its short branch."""
    V = relax(start_config(m), 0.0, 300, m, bistable=True)
    for ci in range(m["snap_scan_steps"]):
        comp = ci * m["snap_step"]
        V = relax(V, comp, 150, m, bistable=True)
        if strut_len(V) < m["snap_threshold"]:
            return comp
    return m["snap_scan_steps"] * m["snap_step"]


def recovery_time(comp: float, m: dict[str, Any], bistable: bool,
                  magnitude: float, rng: random.Random) -> tuple[float, bool]:
    """Impulse the frame, count steps until the strut returns to within tol.

    Also reports whether the probe left the strut in the other well — a barrier
    crossing, which is non-recovery for a reason unrelated to slowing down.
    """
    V = relax(start_config(m), comp, m["settle_iters"], m, bistable)
    l0 = strut_len(V)
    node, axis = rng.randrange(6), rng.randrange(3)
    Vk = relax(V, comp, 1, m, bistable, kick=(node, axis, magnitude))
    dev0 = abs(strut_len(Vk) - l0)
    if dev0 < 1e-12:
        return 0.0, False
    step = m["recovery_iters"]
    for t in range(m["recovery_max_t"] // step):
        Vk = relax(Vk, comp, step, m, bistable)
        if abs(strut_len(Vk) - l0) < m["recovery_tol"] * dev0:
            return float(t * step), False
    # never returned: crossed the barrier, or merely very slow?
    crossed = bistable and abs(strut_len(Vk) - m["l1"]) < m["barrier_crossing_tol"]
    return float(m["recovery_max_t"]), crossed


def fluctuation_variance(comp: float, m: dict[str, Any], bistable: bool,
                         rng: random.Random) -> float:
    V = relax(start_config(m), comp, m["settle_iters"], m, bistable)
    lengths = []
    for _ in range(m["variance_kicks"]):
        Vk = relax(V, comp, 15, m, bistable,
                   kick=(rng.randrange(6), rng.randrange(3),
                         rng.gauss(0, m["variance_sigma"])))
        lengths.append(strut_len(Vk))
    mean = sum(lengths) / len(lengths)
    return sum((x - mean) ** 2 for x in lengths) / len(lengths)


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------

_SNAP_CACHE: dict[str, float] = {}


def _snap_for(config: dict[str, Any]) -> float:
    """Deterministic given the mechanics; computed once."""
    if "snap" not in _SNAP_CACHE:
        _SNAP_CACHE["snap"] = find_snap(config["mechanics"])
    return _SNAP_CACHE["snap"]


def _curve(seed: int, magnitude: float, config: dict[str, Any],
           bistable: bool) -> tuple[list[float], list[float], int]:
    m = config["mechanics"]
    snap = _snap_for(config)
    rng = random.Random(seed if bistable else seed + 10_000)
    comps = [snap * m["max_compression_frac"] * k / (m["n_compressions"] - 1)
             for k in range(m["n_compressions"])]
    results = [recovery_time(c, m, bistable, magnitude, rng) for c in comps]
    taus = [r[0] for r in results]
    crossings = sum(1 for r in results if r[1])
    return comps, taus, crossings


def _lead(comps: list[float], ratio: list[float], snap: float,
          p: dict[str, Any]) -> float:
    """First compression where the ratio exceeds threshold x its baseline."""
    base_n = p["baseline_points"]
    baseline = sum(ratio[:base_n]) / base_n
    if baseline <= 0:
        return 0.0
    for c, r in zip(comps[base_n:], ratio[base_n:]):
        if r > p["ratio_threshold"] * baseline:
            return (snap - c) / snap
    return 0.0                                  # never detected


def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    magnitude = sweep["probe_magnitude"]
    snap = _snap_for(config)
    comps, tau_bi, crossings = _curve(seed, magnitude, config, bistable=True)
    _, tau_mono, _ = _curve(seed, magnitude, config, bistable=False)
    ratio = [b / mo if mo > 0 else 1.0 for b, mo in zip(tau_bi, tau_mono)]

    m = config["mechanics"]
    rng = random.Random(seed + 777)
    var_low = fluctuation_variance(comps[1], m, True, rng)
    var_high = fluctuation_variance(comps[-1], m, True, rng)

    return {
        "snap_compression": snap,
        "lead_frac": _lead(comps, ratio, snap, config["refute_params"]),
        "tau_baseline": sum(tau_bi[:3]) / 3.0,
        "tau_final": tau_bi[-1],
        "tau_ratio_final": ratio[-1],
        "censored_points": float(sum(1 for t in tau_bi if t >= m["recovery_max_t"])),
        "barrier_crossings": float(crossings),
        # descriptive secondaries — no threshold, no verdict weight
        "variance_low": var_low,
        "variance_high": var_high,
        "variance_ratio": (var_high / var_low) if var_low > 0 else float("nan"),
    }


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """geometry_matched_monostable_strut — same rest length, same stiffness, no second well."""
    magnitude = sweep["probe_magnitude"]
    snap = _snap_for(config)
    comps, tau_mono, _ = _curve(seed, magnitude, config, bistable=False)
    # the null's own "detection": does the monostable arm's recovery time rise
    # against its own baseline as much as the ratio test demands?
    baseline = sum(tau_mono[:config["refute_params"]["baseline_points"]]) / \
        config["refute_params"]["baseline_points"]
    self_ratio = [t / baseline if baseline > 0 else 1.0 for t in tau_mono]
    return {
        "null_lead_frac": _lead(comps, self_ratio, snap, config["refute_params"]),
        "null_tau_baseline": baseline,
        "null_tau_final": tau_mono[-1],
        "null_rise_factor": (tau_mono[-1] / baseline) if baseline > 0 else float("nan"),
    }


# --------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------

def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]
    min_lead = p["min_lead_frac"]

    per_mag: dict[float, dict[str, Any]] = {}
    for row in obs:
        magnitude = row["sweep"]["probe_magnitude"]
        matched = next(n for n in null_obs
                       if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        lead = row["metrics"]["lead_frac"]
        null_lead = matched["metrics"]["null_lead_frac"]
        bucket = per_mag.setdefault(magnitude, {
            "n": 0, "fail_lead": 0, "fail_null": 0, "pass_both": 0,
            "leads": [], "null_leads": []})
        bucket["n"] += 1
        bucket["leads"].append(round(lead, 4))
        bucket["null_leads"].append(round(null_lead, 4))
        fail_lead = lead < min_lead
        fail_null = null_lead >= lead
        bucket["fail_lead"] += fail_lead
        bucket["fail_null"] += fail_null
        bucket["pass_both"] += not (fail_lead or fail_null)

    details = {str(k): v for k, v in sorted(per_mag.items())}

    refuted = []
    for magnitude, b in sorted(per_mag.items()):
        if b["fail_lead"] >= p["refute_at_seeds"]:
            refuted.append(f"probe={magnitude}: lead < {min_lead} at "
                           f"{b['fail_lead']}/{b['n']} seeds")
        if b["fail_null"] >= p["refute_at_seeds"]:
            refuted.append(f"probe={magnitude}: monostable arm rises as early as the "
                           f"bistable one at {b['fail_null']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_both"] >= p["support_at_seeds"] for b in per_mag.values()):
        return Verdict(SUPPORTED,
                       f"recovery-time ratio crosses {p['ratio_threshold']}x with >= "
                       f"{min_lead:.0%} lead, beating the monostable null, at >= "
                       f"{p['support_at_seeds']}/5 seeds at every probe magnitude", details)

    weak = [f"probe={mg}: {b['pass_both']}/{b['n']} seeds met both"
            for mg, b in sorted(per_mag.items()) if b["pass_both"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   f"no refutation threshold reached, but support requires >= "
                   f"{p['support_at_seeds']}/5 seeds at every probe magnitude — "
                   + "; ".join(weak), details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
