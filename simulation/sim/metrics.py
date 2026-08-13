"""Measurements over the world. No objectives here — just observation."""

from __future__ import annotations

import math
from typing import Iterable, Mapping


def logistic_growth(current: float, capacity: float, rate: float) -> float:
    """Logistic step, exactly as specified in the README stub.

        current * (1 + rate * (1 - current / capacity))

    Note this is the discrete-map form, not the continuous solution. It is
    unstable for large `rate` (period-doubling above ~2.0), which is a property
    of the world, not a bug to be smoothed away.
    """
    if capacity <= 0:
        return 0.0
    return current * (1.0 + rate * (1.0 - current / capacity))


def shannon_entropy(weights: Iterable[float]) -> float:
    """Shannon entropy in nats of a non-negative weight vector, normalized to
    a probability distribution first. Zero-weight entries contribute nothing."""
    vals = [w for w in weights if w > 0.0]
    total = sum(vals)
    if total <= 0.0:
        return 0.0
    return -sum((w / total) * math.log(w / total) for w in vals)


def normalized_entropy(weights: Iterable[float]) -> float:
    """Entropy scaled to [0, 1] by the maximum possible for this many bins.

    1.0 = influence spread perfectly evenly. 0.0 = one agent holds everything.
    """
    vals = list(weights)
    n = len(vals)
    if n <= 1:
        return 0.0
    return shannon_entropy(vals) / math.log(n)


def deference_concentration(influence: Mapping[int, float]) -> float:
    """The idolatry measure named in config: `deference_concentration`.

    Defined as 1 - normalized_entropy, so it rises as deference concentrates.
    0.0 = perfectly distributed, 1.0 = total concentration on one agent.
    """
    return 1.0 - normalized_entropy(influence.values())


def max_share(influence: Mapping[int, float]) -> float:
    """Largest single agent's fraction of total deference.

    Tracked alongside concentration because the config is ambiguous about which
    quantity the 0.65 threshold refers to — see `sim/config.py`.
    """
    total = sum(influence.values())
    if total <= 0.0:
        return 0.0
    return max(influence.values()) / total


def gini(values: Iterable[float]) -> float:
    """Gini coefficient of a non-negative distribution. 0 = even, 1 = one holder."""
    vals = sorted(v for v in values)
    n = len(vals)
    if n == 0:
        return 0.0
    total = sum(vals)
    if total <= 0.0:
        return 0.0
    cumulative = sum((i + 1) * v for i, v in enumerate(vals))
    return (2.0 * cumulative) / (n * total) - (n + 1.0) / n
