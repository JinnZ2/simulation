#!/usr/bin/env python3
"""SKETCH, NOT RESULTS — pilot harness for EXP-WMC-01 (see ../world-models-and-curiosity-driven-learning.md).

Tabular gridworld (default 15x15, no extrinsic reward). One cell is a 'noisy TV': when
the agent stands on it, the observation is a fresh uniform random symbol. Agents pick
the neighbour with the highest intrinsic bonus (epsilon-greedy):
  random      : no bonus (control)
  count       : bonus 1/sqrt(N(s'))           (novelty; not fooled by noise in theory)
  pred_error  : bonus = running prediction error of a tabular forward model at s'
                (surprise; predicted to be captured by irreducible noise)
  learn_prog  : bonus = recent DECREASE in that prediction error (learning progress)
Outcomes over T steps: fraction of distinct cells visited, fraction of steps on the TV.
Seeds vary start position, TV location and tie-breaking.

    python3 curiosity_toy.py [--seeds 10] [--T 3000] [--size 15]
"""
import argparse
import numpy as np

MOVES = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def run(agent, seed, T, size, n_sym=8, eps=0.1, lr=0.2):
    rng = np.random.default_rng(seed)
    tv = tuple(rng.integers(0, size, 2))
    pos = tuple(rng.integers(0, size, 2))
    N = np.zeros((size, size)); err = np.ones((size, size)); prev_err = np.ones((size, size))
    model = np.full((size, size, n_sym), 1.0 / n_sym)   # predicted obs distribution per cell
    sym = rng.integers(0, n_sym, (size, size))           # deterministic obs elsewhere
    on_tv = 0
    for _ in range(T):
        nbrs = [(min(max(pos[0] + dx, 0), size - 1), min(max(pos[1] + dy, 0), size - 1)) for dx, dy in MOVES]
        if agent == "random" or rng.random() < eps:
            nxt = nbrs[rng.integers(4)]
        else:
            if agent == "count":
                b = [1 / np.sqrt(N[c] + 1) for c in nbrs]
            elif agent == "pred_error":
                b = [err[c] for c in nbrs]
            else:
                b = [max(prev_err[c] - err[c], 0) + 1e-3 / (N[c] + 1) for c in nbrs]
            b = np.array(b) + 1e-9 * rng.random(4)
            nxt = nbrs[int(np.argmax(b))]
        pos = nxt; N[pos] += 1; on_tv += pos == tv
        o = rng.integers(n_sym) if pos == tv else sym[pos]
        e = 1 - model[pos][o]                            # surprise proxy
        prev_err[pos] = err[pos]; err[pos] = (1 - lr) * err[pos] + lr * e
        model[pos] *= (1 - lr); model[pos][o] += lr
    return (N > 0).mean(), on_tv / T


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--T", type=int, default=3000)
    ap.add_argument("--size", type=int, default=15)
    a = ap.parse_args()
    for agent in ("random", "count", "pred_error", "learn_prog"):
        r = np.array([run(agent, s, a.T, a.size) for s in range(a.seeds)])
        print(f"{agent:11s} coverage {r[:,0].mean():.3f}±{r[:,0].std():.3f}   time-on-TV {r[:,1].mean():.3f}±{r[:,1].std():.3f}")
    print("SKETCH: tabular toy. Does not establish anything about deep curiosity agents or world-model RL.")
