#!/usr/bin/env python3
"""kappa_eff — does effective curvature lead behavioural failure?

Retrofit of original_kappa_eff_kill_test.py to Sim Harness Standard v1 (§5 item 3,
whose note reads "verdict flipped on criterion choice — needs the full criterion-
sweep recorded in config"). Reads ONLY config.json + CLI overrides (§3).

Changes from the original, recorded rather than silent:
  - the accuracy-drop threshold, hard-coded at 5 points, is swept {0.02,0.05,0.10}.
    That is the criterion whose choice flips the verdict.
  - a random_ray null is measured at every point; the original had none.
  - 5 seeds; the original ran one fixed torch.manual_seed(0).
  - numpy instead of torch (notes/10 §2.2 tiering; 1,186 parameters does not need
    Tier 2). Same architecture, optimizer, HVP method and ray convention; the
    numbers will not be bit-identical to a torch run. See REFUTE.md.
  - "no accuracy collapse in range" stays INCONCLUSIVE, as in the original.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import INCONCLUSIVE, REFUTED, SUPPORTED, Verdict, run  # noqa: E402

CONFIG = Path(__file__).resolve().parent / "config.json"


# --------------------------------------------------------------------------
# A 2-32-32-2 tanh MLP with cross-entropy, in numpy
# --------------------------------------------------------------------------

def init_params(rng: np.random.Generator, hidden: int) -> list[np.ndarray]:
    """Kaiming-uniform-ish fan-in init, matching torch.nn.Linear's default scale."""
    shapes = [(2, hidden), (hidden,), (hidden, hidden), (hidden,), (hidden, 2), (2,)]
    params = []
    for shape in shapes:
        fan_in = shape[0] if len(shape) == 2 else params[-1].shape[0]
        bound = 1.0 / np.sqrt(fan_in)
        params.append(rng.uniform(-bound, bound, size=shape))
    return params


def flatten(params: list[np.ndarray]) -> np.ndarray:
    return np.concatenate([p.ravel() for p in params])


def unflatten(theta: np.ndarray, template: list[np.ndarray]) -> list[np.ndarray]:
    out, i = [], 0
    for p in template:
        n = p.size
        out.append(theta[i:i + n].reshape(p.shape))
        i += n
    return out


def forward(params: list[np.ndarray], X: np.ndarray):
    W1, b1, W2, b2, W3, b3 = params
    z1 = X @ W1 + b1
    a1 = np.tanh(z1)
    z2 = a1 @ W2 + b2
    a2 = np.tanh(z2)
    return z2 @ W3 + b3, (a1, a2)


def softmax_ce(logits: np.ndarray, y: np.ndarray) -> float:
    shifted = logits - logits.max(axis=1, keepdims=True)
    logsumexp = np.log(np.exp(shifted).sum(axis=1)) + logits.max(axis=1)
    return float(np.mean(logsumexp - logits[np.arange(len(y)), y]))


def loss_and_grad(params: list[np.ndarray], X: np.ndarray,
                  y: np.ndarray) -> tuple[float, list[np.ndarray]]:
    W1, b1, W2, b2, W3, b3 = params
    n = len(y)
    logits, (a1, a2) = forward(params, X)
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    probs = exp / exp.sum(axis=1, keepdims=True)

    dlogits = probs.copy()
    dlogits[np.arange(n), y] -= 1.0
    dlogits /= n

    gW3 = a2.T @ dlogits
    gb3 = dlogits.sum(axis=0)
    da2 = dlogits @ W3.T
    dz2 = da2 * (1.0 - a2 ** 2)
    gW2 = a1.T @ dz2
    gb2 = dz2.sum(axis=0)
    da1 = dz2 @ W2.T
    dz1 = da1 * (1.0 - a1 ** 2)
    gW1 = X.T @ dz1
    gb1 = dz1.sum(axis=0)

    return softmax_ce(logits, y), [gW1, gb1, gW2, gb2, gW3, gb3]


def train(rng: np.random.Generator, X: np.ndarray, y: np.ndarray,
          m: dict[str, Any]) -> list[np.ndarray]:
    """Full-batch Adam, matching the original's optimizer and epoch count."""
    params = init_params(rng, m["hidden"])
    ms = [np.zeros_like(p) for p in params]
    vs = [np.zeros_like(p) for p in params]
    b1, b2, eps, lr = 0.9, 0.999, 1e-8, m["lr"]
    for step in range(1, m["epochs"] + 1):
        _, grads = loss_and_grad(params, X, y)
        for i, g in enumerate(grads):
            ms[i] = b1 * ms[i] + (1 - b1) * g
            vs[i] = b2 * vs[i] + (1 - b2) * g * g
            m_hat = ms[i] / (1 - b1 ** step)
            v_hat = vs[i] / (1 - b2 ** step)
            params[i] -= lr * m_hat / (np.sqrt(v_hat) + eps)
    return params


def make_data(rng: np.random.Generator, m: dict[str, Any]):
    """The original's synthetic task: sign of sin(2.5 x1) with noise."""
    n = m["n_samples"]
    x1 = rng.random(n) * 3 - 1.5
    y = (np.sin(2.5 * x1) + 0.3 * rng.standard_normal(n) > 0).astype(int)
    X = np.stack([x1, rng.random(n) * 3 - 1.5], axis=1)
    split = m["n_train"]
    return X[:split], X[split:], y[:split], y[split:]


# --------------------------------------------------------------------------
# The measurement: kappa_eff and accuracy along a ray
# --------------------------------------------------------------------------

def kappa_eff(theta: np.ndarray, v: np.ndarray, template, X, y, eps: float) -> float:
    """|v'Hv| / v'v by central finite difference of the gradient — GM's convention."""
    _, g_plus = loss_and_grad(unflatten(theta + eps * v, template), X, y)
    _, g_minus = loss_and_grad(unflatten(theta - eps * v, template), X, y)
    hvp = (flatten(g_plus) - flatten(g_minus)) / (2 * eps)
    return float(abs(v @ hvp) / (v @ v))


def accuracy(theta: np.ndarray, template, X, y) -> float:
    logits, _ = forward(unflatten(theta, template), X)
    return float(np.mean(logits.argmax(axis=1) == y))


def _ray_profile(seed: int, config: dict[str, Any], random_ray: bool) -> dict[str, Any]:
    m = config["model"]
    rng = np.random.default_rng(seed)
    Xtr, Xte, ytr, yte = make_data(rng, m)
    params = train(rng, Xtr, ytr, m)
    theta0 = flatten(params)

    _, grads = loss_and_grad(params, Xtr, ytr)
    if random_ray:
        direction = np.random.default_rng(seed + 10_000).standard_normal(theta0.size)
    else:
        direction = flatten(grads)          # GM energy_sweep convention: ascent ray
    v = direction / np.linalg.norm(direction)

    base_acc = accuracy(theta0, params, Xte, yte)
    rows = []
    for alpha in m["alphas"]:
        theta = theta0 + alpha * v
        rows.append({
            "alpha": float(alpha),
            "kappa": kappa_eff(theta, v, params, Xtr, ytr, m["hvp_eps"]),
            "acc": accuracy(theta, params, Xte, yte),
        })
    return {"base_acc": base_acc, "rows": rows}


def _kill_criteria(profile: dict[str, Any], drop_threshold: float) -> dict[str, float]:
    """K1/K2 from the original, evaluated at the given drop threshold."""
    rows = profile["rows"]
    base = profile["base_acc"]
    kappas = [r["kappa"] for r in rows]
    alphas = [r["alpha"] for r in rows]

    peak_alpha = alphas[int(np.argmax(kappas))]
    drop_alpha = next((r["alpha"] for r in rows if r["acc"] - base < -drop_threshold), None)

    if drop_alpha is None:
        return {"collapsed": 0.0, "k1": 0.0, "k2": 0.0,
                "peak_alpha": peak_alpha, "drop_alpha": float("nan"),
                "lead": float("nan"), "base_acc": base}

    # K1: no peak before collapse (flat kappa, peak sitting at alpha=0)
    k1 = float(max(kappas[1:]) < 1.2 * kappas[0] and peak_alpha == 0.0)
    # K2: peak at or after collapse
    k2 = float(peak_alpha >= drop_alpha)
    return {"collapsed": 1.0, "k1": k1, "k2": k2,
            "peak_alpha": peak_alpha, "drop_alpha": drop_alpha,
            "lead": drop_alpha - peak_alpha, "base_acc": base}


# Training dominates the cost and does not depend on the swept threshold, so each
# (seed, ray) profile is computed once and re-graded at each threshold.
_PROFILE_CACHE: dict[tuple[int, bool], dict[str, Any]] = {}


def _profile_for(seed: int, config: dict[str, Any], random_ray: bool) -> dict[str, Any]:
    key = (seed, random_ray)
    if key not in _PROFILE_CACHE:
        _PROFILE_CACHE[key] = _ray_profile(seed, config, random_ray)
    return _PROFILE_CACHE[key]


def measure(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    threshold = sweep["accuracy_drop_threshold"]
    grad = _kill_criteria(_profile_for(seed, config, False), threshold)
    rand = _kill_criteria(_profile_for(seed, config, True), threshold)
    out = {f"grad_{k}": v for k, v in grad.items()}
    # the random ray's lead is needed at grading time to form the difference
    out["random_lead"] = rand["lead"]
    out["random_collapsed"] = rand["collapsed"]
    return out


def null(seed: int, sweep: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    """random_ray — identical everything, direction replaced by a random unit vector."""
    threshold = sweep["accuracy_drop_threshold"]
    rand = _kill_criteria(_profile_for(seed, config, True), threshold)
    return {f"rand_{k}": v for k, v in rand.items()}


# --------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------

def grade(obs: list[dict[str, Any]], null_obs: list[dict[str, Any]],
          config: dict[str, Any]) -> Verdict:
    p = config["refute_params"]

    per_threshold: dict[float, dict[str, Any]] = {}
    for row in obs:
        threshold = row["sweep"]["accuracy_drop_threshold"]
        matched = next(n for n in null_obs
                       if n["seed"] == row["seed"] and n["sweep"] == row["sweep"])
        m, nm = row["metrics"], matched["metrics"]
        bucket = per_threshold.setdefault(threshold, {
            "n": 0, "no_collapse": 0, "kill_fired": 0, "no_gain_over_null": 0,
            "pass_all": 0, "leads": []})
        bucket["n"] += 1

        if m["grad_collapsed"] == 0.0:
            bucket["no_collapse"] += 1
            continue

        kill = m["grad_k1"] > 0 or m["grad_k2"] > 0
        rand_lead = nm["rand_lead"]
        # a null ray that never collapses cannot beat the gradient ray on lead
        gain = m["grad_lead"] - (0.0 if np.isnan(rand_lead) else rand_lead)
        bucket["leads"].append(round(float(gain), 4))
        bucket["kill_fired"] += kill
        bucket["no_gain_over_null"] += gain <= 0
        bucket["pass_all"] += not (kill or gain <= 0)

    details = {str(k): v for k, v in sorted(per_threshold.items())}

    # INCONCLUSIVE by construction: nothing to lead
    stalled = [f"threshold={t}: no accuracy collapse in range at {b['no_collapse']}/{b['n']} seeds"
               for t, b in sorted(per_threshold.items())
               if b["no_collapse"] >= p["refute_at_seeds"]]
    if stalled:
        return Verdict(INCONCLUSIVE,
                       "K1/K2 undefined — " + "; ".join(stalled), details)

    refuted = []
    for threshold, b in sorted(per_threshold.items()):
        if b["kill_fired"] >= p["refute_at_seeds"]:
            refuted.append(f"threshold={threshold}: K1/K2 fired at "
                           f"{b['kill_fired']}/{b['n']} seeds")
        if b["no_gain_over_null"] >= p["refute_at_seeds"]:
            refuted.append(f"threshold={threshold}: gradient ray's lead no better than a "
                           f"random ray's at {b['no_gain_over_null']}/{b['n']} seeds")
    if refuted:
        return Verdict(REFUTED, "; ".join(refuted), details)

    if all(b["pass_all"] >= p["support_at_seeds"] for b in per_threshold.values()):
        return Verdict(SUPPORTED,
                       f"kappa_eff peaks before collapse and beats the random ray at >= "
                       f"{p['support_at_seeds']}/5 seeds at every swept drop threshold", details)

    weak = [f"threshold={t}: {b['pass_all']}/{b['n']} seeds passed"
            for t, b in sorted(per_threshold.items()) if b["pass_all"] < p["support_at_seeds"]]
    return Verdict(INCONCLUSIVE,
                   "verdict depends on the drop threshold — the criterion-dependence HARNESS.md "
                   "§5 flagged. " + "; ".join(weak), details)


if __name__ == "__main__":
    run(CONFIG, measure, null, grade)
