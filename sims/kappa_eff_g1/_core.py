"""Network, training and data — lifted verbatim from ../kappa_eff/run.py.

Shared rather than re-derived so the two generations differ only in the
criterion under test, which is the whole point of the comparison.
"""

from __future__ import annotations

import numpy as np


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

