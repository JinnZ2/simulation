#!/usr/bin/env python3
"""kappa_eff_g2 — curvature onset, measured from a minimum that exists.

Successor to `kappa_eff_g1` (REFUTED). Reads ONLY config.json + CLI overrides.
EXPLORATORY. Last generation before the escape hatch — see REFUTE.md.

One change from generation 1, in the apparatus rather than the claim:

  L2 regularization (weight_decay = 0.01) makes the objective coercive, so a
  finite minimizer exists. Without it, cross-entropy on a memorizable training
  set has no minimum at all and the gradient norm *rises* with training. Every
  network is then gated on ||grad|| <= 0.02 at theta0, and a failed gate makes
  the run INCONCLUSIVE rather than graded.

kappa_eff and the ascent ray are both taken on the regularized objective — the
one that actually has the minimum being stood on.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "kappa_eff_g1"))

from _core import (  # noqa: E402
    flatten,
    forward,
    init_params,
    loss_and_grad,
    make_data,
    unflatten,
)
from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

CONFIG = HERE / "config.json"


# --------------------------------------------------------------------------
# Regularized objective — the one with a minimum
# --------------------------------------------------------------------------

def reg_grad(params: list[np.ndarray], X: np.ndarray, y: np.ndarray,
             wd: float) -> list[np.ndarray]:
    """Gradient of loss + (wd/2)||theta||^2."""
    _, grads = loss_and_grad(params, X, y)
    return [g + wd * p for g, p in zip(grads, params)]


def train(rng: np.random.Generator, X: np.ndarray, y: np.ndarray,
          m: dict[str, Any]) -> list[np.ndarray]:
    """Adam with cosine decay on the regularized objective.

    Decay matters: a constant rate leaves the iterate orbiting the minimum, and
    the gradient norm never settles low enough to clear the gate.
    """
    params = init_params(rng, m["hidden"])
    ms = [np.zeros_like(p) for p in params]
    vs = [np.zeros_like(p) for p in params]
    b1, b2, eps = 0.9, 0.999, 1e-8
    epochs, lr0, wd = m["epochs"], m["lr"], m["weight_decay"]
    for step in range(1, epochs + 1):
        lr = lr0 * 0.5 * (1 + np.cos(np.pi * step / epochs))
        for i, g in enumerate(reg_grad(params, X, y, wd)):
            ms[i] = b1 * ms[i] + (1 - b1) * g
            vs[i] = b2 * vs[i] + (1 - b2) * g * g
            params[i] -= lr * (ms[i] / (1 - b1 ** step)) / \
                (np.sqrt(vs[i] / (1 - b2 ** step)) + eps)
    return params


def kappa_eff(theta: np.ndarray, v: np.ndarray, template, X, y,
              eps: float, wd: float) -> float:
    """|v'Hv| / v'v on the regularized objective, by central difference."""
    g_plus = flatten(reg_grad(unflatten(theta + eps * v, template), X, y, wd))
    g_minus = flatten(reg_grad(unflatten(theta - eps * v, template), X, y, wd))
    hvp = (g_plus - g_minus) / (2 * eps)
    return float(abs(v @ hvp) / (v @ v))


def accuracy(theta: np.ndarray, template, X, y) -> float:
    logits, _ = forward(unflatten(theta, template), X)
    return float(np.mean(logits.argmax(axis=1) == y))


def ray_profile(seed: int, width: int, config: dict[str, Any],
                random_ray: bool) -> dict[str, Any]:
    m = dict(config["model"])
    m["hidden"] = width
    wd = m["weight_decay"]
    rng = np.random.default_rng(seed)
    Xtr, Xte, ytr, yte = make_data(rng, m)
    params = train(rng, Xtr, ytr, m)
    theta0 = flatten(params)

    grads = flatten(reg_grad(params, Xtr, ytr, wd))
    grad_norm = float(np.linalg.norm(grads))          # the convergence gate

    direction = (np.random.default_rng(seed + 10_000).standard_normal(theta0.size)
                 if random_ray else grads)
    v = direction / np.linalg.norm(direction)

    base_acc = accuracy(theta0, params, Xte, yte)
    rows = [{"alpha": float(a),
             "kappa": kappa_eff(theta0 + a * v, v, params, Xtr, ytr, m["hvp_eps"], wd),
             "acc": accuracy(theta0 + a * v, params, Xte, yte)}
            for a in m["alphas"]]
    return {"base_acc": base_acc, "grad_norm": grad_norm, "rows": rows}


def onset_stats(profile: dict[str, Any], rise_multiple: float,
                drop: float) -> dict[str, float]:
    rows, base = profile["rows"], profile["base_acc"]
    kappa0 = rows[0]["kappa"]
    alpha_rise = next((r["alpha"] for r in rows
                       if kappa0 > 0 and r["kappa"] >= rise_multiple * kappa0), None)
    drop_row = next((r for r in rows if r["acc"] - base <= -drop), None)

    common = {"grad_norm": profile["grad_norm"], "kappa_baseline": kappa0,
              "base_acc": base}
    if drop_row is None:
        return {"collapsed": 0.0, "alpha_rise": float("nan"), "alpha_drop": float("nan"),
                "kappa_ratio_at_drop": float("nan"), "rise_leads": 0.0, **common}
    return {
        "collapsed": 1.0,
        "alpha_rise": float("nan") if alpha_rise is None else alpha_rise,
        "alpha_drop": drop_row["alpha"],
        "kappa_ratio_at_drop": (drop_row["kappa"] / kappa0) if kappa0 > 0 else float("nan"),
        "rise_leads": float(alpha_rise is not None and alpha_rise < drop_row["alpha"]),
        **common,
    }


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
    p = config["refute_params"]
    stats = onset_stats(profile_for(seed, sweep["hidden_width"], config, True),
                        p["rise_multiple"], p["accuracy_drop"])
    return {f"rand_{k}": v for k, v in stats.items()}


def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]
    gate = p["convergence_gate"]

    # Apparatus check first. A claim about geometry at a minimum, measured from
    # somewhere that is not a minimum, is not evidence about the claim.
    failed_gate = [(r["seed"], r["sweep"]["hidden_width"],
                    round(r["metrics"]["grad_grad_norm"], 5))
                   for r in obs if r["metrics"]["grad_grad_norm"] > gate]
    if failed_gate:
        return Verdict(INCONCLUSIVE,
                       f"convergence gate ||grad|| <= {gate} failed at "
                       f"{len(failed_gate)}/{len(obs)} networks: {failed_gate[:5]} — "
                       "the run measures the apparatus, not the claim",
                       {"failed_gate": failed_gate})

    per_width: dict[int, dict[str, Any]] = {}
    for row in obs:
        width = row["sweep"]["hidden_width"]
        matched = next(n for n in null_obs
                       if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        m, nm = row["metrics"], matched["metrics"]
        bucket = per_width.setdefault(width, {
            "n": 0, "no_collapse": 0, "no_lead": 0, "no_gain": 0, "pass_all": 0,
            "grad_ratio": [], "rand_ratio": [], "grad_norm": []})
        bucket["n"] += 1
        bucket["grad_norm"].append(round(m["grad_grad_norm"], 5))

        if m["grad_collapsed"] == 0.0:
            bucket["no_collapse"] += 1
            continue

        no_lead = m["grad_rise_leads"] == 0.0
        grad_ratio = m["grad_kappa_ratio_at_drop"]
        rand_ratio = nm["rand_kappa_ratio_at_drop"]
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
            refuted.append(f"width={width}: the {p['rise_multiple']}x rise does not precede "
                           f"the {p['accuracy_drop']:.0%} drop at {b['no_lead']}/{b['n']} seeds")
        if b["no_gain"] >= p["refute_at_seeds"]:
            refuted.append(f"width={width}: at matched damage the gradient ray's curvature has "
                           f"risen no further than a random ray's at {b['no_gain']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_all"] >= p["support_at_seeds"] for b in per_width.values()):
        return Verdict(SUPPORTED,
                       f"from a converged minimum, kappa_eff reaches {p['rise_multiple']}x "
                       f"baseline before the {p['accuracy_drop']:.0%} accuracy drop and beats "
                       f"the random ray at matched damage, at >= {p['support_at_seeds']}/5 "
                       "seeds at every width", details)

    weak = [f"width={w}: {b['pass_all']}/{b['n']} seeds passed"
            for w, b in sorted(per_width.items()) if b["pass_all"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   "the indicator is width-dependent — " + "; ".join(weak), details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
