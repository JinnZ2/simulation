#!/usr/bin/env python3
"""kappa_eff_g1 — does curvature ONSET lead behavioural collapse?

Successor to `kappa_eff` (REFUTED on peak-based criteria). Reads ONLY config.json
+ CLI overrides (§3). EXPLORATORY — see REFUTE.md.

Two changes from the parent, both pre-registered:
  - the indicator is the first alpha where kappa_eff reaches 2x baseline (onset),
    not its argmax (peak). A maximum cannot lead the event it is the turning
    point of; an onset can.
  - the two rays are compared at MATCHED DAMAGE — each at its own 5-point
    accuracy drop — rather than by lead in alpha units. The parent's FINDINGS
    recorded that flaw in its own condition: rays that wreck the model at
    different rates are not comparable on an alpha axis.

Network, training and data are imported from the parent rather than re-derived,
so the two generations differ only in the criterion.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from _core import (  # noqa: E402
    flatten,
    forward,
    loss_and_grad,
    make_data,
    train,
    unflatten,
)
from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

CONFIG = HERE / "config.json"


def kappa_eff(theta: np.ndarray, v: np.ndarray, template, X, y, eps: float) -> float:
    """|v'Hv| / v'v by central finite difference — GM's convention, unchanged."""
    _, g_plus = loss_and_grad(unflatten(theta + eps * v, template), X, y)
    _, g_minus = loss_and_grad(unflatten(theta - eps * v, template), X, y)
    hvp = (flatten(g_plus) - flatten(g_minus)) / (2 * eps)
    return float(abs(v @ hvp) / (v @ v))


def accuracy(theta: np.ndarray, template, X, y) -> float:
    logits, _ = forward(unflatten(theta, template), X)
    return float(np.mean(logits.argmax(axis=1) == y))


def ray_profile(seed: int, width: int, config: dict[str, Any],
                random_ray: bool) -> dict[str, Any]:
    m = dict(config["model"])
    m["hidden"] = width
    rng = np.random.default_rng(seed)
    Xtr, Xte, ytr, yte = make_data(rng, m)
    params = train(rng, Xtr, ytr, m)
    theta0 = flatten(params)

    _, grads = loss_and_grad(params, Xtr, ytr)
    direction = (np.random.default_rng(seed + 10_000).standard_normal(theta0.size)
                 if random_ray else flatten(grads))
    v = direction / np.linalg.norm(direction)

    base_acc = accuracy(theta0, params, Xte, yte)
    rows = []
    for alpha in m["alphas"]:
        theta = theta0 + alpha * v
        rows.append({"alpha": float(alpha),
                     "kappa": kappa_eff(theta, v, params, Xtr, ytr, m["hvp_eps"]),
                     "acc": accuracy(theta, params, Xte, yte)})
    return {"base_acc": base_acc, "rows": rows}


def onset_stats(profile: dict[str, Any], rise_multiple: float,
                drop: float) -> dict[str, float]:
    """Onset of the rise, the damage point, and curvature growth at matched damage."""
    rows, base = profile["rows"], profile["base_acc"]
    kappa0 = rows[0]["kappa"]

    alpha_rise = next((r["alpha"] for r in rows
                       if kappa0 > 0 and r["kappa"] >= rise_multiple * kappa0), None)
    drop_row = next((r for r in rows if r["acc"] - base <= -drop), None)

    if drop_row is None:
        return {"collapsed": 0.0, "alpha_rise": float("nan"), "alpha_drop": float("nan"),
                "kappa_ratio_at_drop": float("nan"), "rise_leads": 0.0,
                "kappa_baseline": kappa0, "base_acc": base}

    return {
        "collapsed": 1.0,
        "alpha_rise": float("nan") if alpha_rise is None else alpha_rise,
        "alpha_drop": drop_row["alpha"],
        # curvature growth by the time this ray has done the agreed amount of damage
        "kappa_ratio_at_drop": (drop_row["kappa"] / kappa0) if kappa0 > 0 else float("nan"),
        "rise_leads": float(alpha_rise is not None and alpha_rise < drop_row["alpha"]),
        "kappa_baseline": kappa0,
        "base_acc": base,
    }


# Training dominates cost and is independent of nothing swept here except width,
# so each (seed, width, ray) profile is computed once.
_CACHE: dict[tuple[int, int, bool], dict[str, Any]] = {}


def profile_for(seed: int, width: int, config: dict[str, Any],
                random_ray: bool) -> dict[str, Any]:
    key = (seed, width, random_ray)
    if key not in _CACHE:
        _CACHE[key] = ray_profile(seed, width, config, random_ray)
    return _CACHE[key]


def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    p = config["refute_params"]
    stats = onset_stats(profile_for(seed, sweep["hidden_width"], config, False),
                        p["rise_multiple"], p["accuracy_drop"])
    return {f"grad_{k}": v for k, v in stats.items()}


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """random_ray — same everything, direction replaced by a random unit vector."""
    p = config["refute_params"]
    stats = onset_stats(profile_for(seed, sweep["hidden_width"], config, True),
                        p["rise_multiple"], p["accuracy_drop"])
    return {f"rand_{k}": v for k, v in stats.items()}


def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]

    per_width: dict[int, dict[str, Any]] = {}
    for row in obs:
        width = row["sweep"]["hidden_width"]
        matched = next(n for n in null_obs
                       if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        m, nm = row["metrics"], matched["metrics"]
        bucket = per_width.setdefault(width, {
            "n": 0, "no_collapse": 0, "no_lead": 0, "no_gain": 0, "pass_all": 0,
            "grad_ratio": [], "rand_ratio": []})
        bucket["n"] += 1

        if m["grad_collapsed"] == 0.0:
            bucket["no_collapse"] += 1
            continue

        no_lead = m["grad_rise_leads"] == 0.0
        grad_ratio = m["grad_kappa_ratio_at_drop"]
        rand_ratio = nm["rand_kappa_ratio_at_drop"]
        # a null ray that never collapses gives no ratio to beat; treat as 1.0 (no rise)
        rand_ratio = 1.0 if np.isnan(rand_ratio) else rand_ratio
        no_gain = not (grad_ratio > rand_ratio)

        bucket["grad_ratio"].append(round(float(grad_ratio), 3))
        bucket["rand_ratio"].append(round(float(rand_ratio), 3))
        bucket["no_lead"] += no_lead
        bucket["no_gain"] += no_gain
        bucket["pass_all"] += not (no_lead or no_gain)

    details = {str(k): v for k, v in sorted(per_width.items())}

    stalled = [f"width={w}: no accuracy collapse in range at {b['no_collapse']}/{b['n']} seeds"
               for w, b in sorted(per_width.items())
               if b["no_collapse"] >= p["refute_at_seeds"]]
    if stalled:
        return Verdict(INCONCLUSIVE, "nothing to lead — " + "; ".join(stalled), details)

    refuted = []
    for width, b in sorted(per_width.items()):
        if b["no_lead"] >= p["refute_at_seeds"]:
            refuted.append(f"width={width}: the {p['rise_multiple']}x rise does not precede the "
                           f"{p['accuracy_drop']:.0%} drop at {b['no_lead']}/{b['n']} seeds")
        if b["no_gain"] >= p["refute_at_seeds"]:
            refuted.append(f"width={width}: at matched damage the gradient ray's curvature has "
                           f"risen no further than a random ray's at {b['no_gain']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_all"] >= p["support_at_seeds"] for b in per_width.values()):
        return Verdict(SUPPORTED,
                       f"kappa_eff reaches {p['rise_multiple']}x baseline before the "
                       f"{p['accuracy_drop']:.0%} accuracy drop, and beats the random ray at "
                       f"matched damage, at >= {p['support_at_seeds']}/5 seeds at every width",
                       details)

    weak = [f"width={w}: {b['pass_all']}/{b['n']} seeds passed"
            for w, b in sorted(per_width.items()) if b["pass_all"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   "the indicator is width-dependent — " + "; ".join(weak), details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
