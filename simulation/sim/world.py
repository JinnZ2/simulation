"""The bounded world.

No controller. No objective function. Agents do not maximize anything — they
carry fixed propensities, modulated by their own scarcity and by whoever they
currently defer to. Deference is what makes idolatry emerge rather than being
imposed: agents periodically re-point their deference at whoever they have
recently observed gaining, which is a positive feedback loop with no damping
except `decay_rate` and the `forget` action.

What survives is not optimal. It is resilient.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterator

from .metrics import (
    deference_concentration,
    gini,
    logistic_growth,
    max_share,
    normalized_entropy,
)

ACTIONS = ("consume", "share", "build", "forget")


@dataclass
class Agent:
    id: int
    resources: float
    structural_capital: float          # rigidity score
    deference_to: int | None           # who they follow (idolatry)
    memory: deque[float]               # past per-cycle resource deltas
    propensity: dict[str, float]       # fixed at birth; not learned

    def remember(self, delta: float) -> None:
        self.memory.append(delta)

    def recent_gain(self) -> float:
        return sum(self.memory) if self.memory else 0.0


@dataclass
class World:
    cycle: int
    resource_pool: float
    agents: list[Agent]
    influence: dict[int, float]        # agent_id -> deference score
    config: dict[str, Any]
    rng: random.Random
    shocks_fired: int = 0
    jubilees: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    # -- observation ------------------------------------------------------

    def concentration(self) -> float:
        return deference_concentration(self.influence)

    def idolatry_active(self) -> bool:
        idol = self.config["idolatry"]
        if not idol["enabled"]:
            return False
        # Before deference has spread, influence sits on a handful of agents and
        # the entropy measure reads as "concentrated" for want of support rather
        # than from actual idolatry. warmup_cycles suppresses that artifact; it
        # defaults to 0, so the spec's behaviour is unchanged unless asked for.
        if self.cycle <= int(idol["warmup_cycles"]):
            return False
        measure = (self.concentration() if idol["threshold_measure"] ==
                   "deference_concentration" else max_share(self.influence))
        return measure > float(idol["threshold"])

    def innovation_rate(self) -> float:
        """1.0 normally; reduced while idolatry holds."""
        if not self.idolatry_active():
            return 1.0
        return 1.0 - float(self.config["idolatry"]["innovation_penalty"])

    def snapshot(self) -> dict[str, Any]:
        held = [a.resources for a in self.agents]
        capital = [a.structural_capital for a in self.agents]
        return {
            "cycle": self.cycle,
            "resource_pool": round(self.resource_pool, 6),
            "agent_resources_total": round(sum(held), 6),
            "structural_capital_total": round(sum(capital), 6),
            "deference_concentration": round(self.concentration(), 6),
            "deference_entropy": round(normalized_entropy(self.influence.values()), 6),
            "max_share": round(max_share(self.influence), 6),
            "gini_resources": round(gini(held), 6),
            "idolatry_active": self.idolatry_active(),
            "innovation_rate": round(self.innovation_rate(), 6),
            "shocks_fired": self.shocks_fired,
            "jubilees": self.jubilees,
        }


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------

def build_world(config: dict[str, Any], rng: random.Random | None = None) -> World:
    acfg = config["agents"]
    rng = rng or random.Random(config["world"]["seed"])
    count = int(acfg["count"])
    memlen = int(acfg["memory_length"])
    space = list(acfg["action_space"])

    agents: list[Agent] = []
    for i in range(count):
        propensity = {a: rng.uniform(0.5, 1.5) for a in space}
        agents.append(Agent(
            id=i,
            resources=float(acfg["initial_resources"]),
            structural_capital=0.0,
            deference_to=None,
            memory=deque(maxlen=memlen),
            propensity=propensity,
        ))

    return World(
        cycle=0,
        resource_pool=float(config["resources"]["initial"]),
        agents=agents,
        influence={a.id: 0.0 for a in agents},
        config=config,
        rng=rng,
    )


# --------------------------------------------------------------------------
# Action selection — propensity, scarcity, imitation. No reward maximization.
# --------------------------------------------------------------------------

def action_weights(world: World, agent: Agent) -> dict[str, float]:
    cfg = world.config
    capacity = float(cfg["resources"]["capacity"])
    space = list(cfg["agents"]["action_space"])
    scarcity = 1.0 - min(1.0, world.resource_pool / capacity)
    weights: dict[str, float] = {}

    for action in space:
        w = agent.propensity[action]
        if action == "consume":
            # scarcer pool -> grab harder; this is the tragedy, not a strategy
            w *= 0.5 + scarcity
        elif action == "share":
            # only meaningful with a surplus to give
            w *= 0.5 + min(2.0, agent.resources / max(1e-9, float(
                cfg["agents"]["initial_resources"])))
        elif action == "build":
            # innovation is what idolatry suppresses
            w *= world.innovation_rate()
        elif action == "forget":
            # Jubilee pressure rises with own rigidity and with concentration
            rigidity = agent.structural_capital / (1.0 + agent.structural_capital)
            w *= 0.25 + rigidity + world.concentration()
        weights[action] = max(0.0, w)

    # an agent who defers imitates their idol's propensities
    if agent.deference_to is not None:
        idol = world.agents[agent.deference_to]
        for action in space:
            weights[action] = 0.5 * weights[action] + 0.5 * idol.propensity[action]
    return weights


def choose_action(world: World, agent: Agent) -> str:
    weights = action_weights(world, agent)
    total = sum(weights.values())
    if total <= 0.0:
        return world.rng.choice(list(weights))
    pick = world.rng.uniform(0.0, total)
    upto = 0.0
    for action, w in weights.items():
        upto += w
        if pick <= upto:
            return action
    return next(reversed(weights))


# --------------------------------------------------------------------------
# The four actions
# --------------------------------------------------------------------------

def apply_action(world: World, agent: Agent, action: str) -> dict[str, Any]:
    cfg = world.config["agents"]
    detail: dict[str, Any] = {"amount": 0.0}

    if action == "consume":
        want = float(cfg["consume_fraction"]) * world.resource_pool
        got = min(want, world.resource_pool)
        world.resource_pool -= got
        agent.resources += got
        detail["amount"] = got

    elif action == "share":
        others = [a for a in world.agents if a.id != agent.id]
        if others and agent.resources > 0:
            target = world.rng.choice(others)
            amount = float(cfg["share_fraction"]) * agent.resources
            agent.resources -= amount
            target.resources += amount
            detail["amount"] = amount
            detail["to"] = target.id

    elif action == "build":
        amount = float(cfg["build_fraction"]) * agent.resources
        agent.resources -= amount
        # capital is rigid: it does not flow back into the pool
        agent.structural_capital += amount
        detail["amount"] = amount

    elif action == "forget":
        # localized Jubilee: prune this agent's deference and its rigidity
        frac = float(cfg["forget_fraction"])
        pruned = agent.structural_capital * frac
        agent.structural_capital -= pruned
        world.resource_pool += pruned          # rigidity dissolves back to commons
        agent.deference_to = None
        keep = int(len(agent.memory) * (1.0 - frac))
        for _ in range(len(agent.memory) - keep):
            agent.memory.popleft()
        world.jubilees += 1
        detail["amount"] = pruned
        detail["pruned_memory"] = len(agent.memory) - keep

    return detail


# --------------------------------------------------------------------------
# Deference dynamics — where idolatry comes from
# --------------------------------------------------------------------------

def update_deference(world: World) -> None:
    cfg = world.config
    acfg = cfg["agents"]
    review_rate = float(acfg["deference_review_rate"])
    sample_size = int(acfg["observation_sample"])
    decay = float(cfg["idolatry"]["decay_rate"])

    for agent in world.agents:
        if world.rng.random() >= review_rate:
            continue
        pool = [a for a in world.agents if a.id != agent.id]
        if not pool:
            continue
        observed = world.rng.sample(pool, min(sample_size, len(pool)))
        # imitate whoever was seen gaining most; ties break on lowest id
        best = max(observed, key=lambda a: (a.recent_gain(), -a.id))
        if best.recent_gain() > agent.recent_gain():
            agent.deference_to = best.id

    # recompute influence, then dissipate it toward zero
    counts: dict[int, float] = {a.id: 0.0 for a in world.agents}
    for agent in world.agents:
        if agent.deference_to is not None:
            counts[agent.deference_to] += 1.0
    for agent_id, prior in world.influence.items():
        world.influence[agent_id] = prior * (1.0 - decay) + counts[agent_id]


# --------------------------------------------------------------------------
# Regeneration and shocks
# --------------------------------------------------------------------------

def regenerate(world: World) -> float:
    res = world.config["resources"]
    capacity = float(res["capacity"])
    rate = float(res["regeneration_rate"])
    threshold = float(res["depletion_threshold"]) * capacity
    if world.resource_pool < threshold:
        rate *= 1.0 - float(res["depletion_penalty"])
    before = world.resource_pool
    world.resource_pool = max(0.0, min(capacity, logistic_growth(
        world.resource_pool, capacity, rate)))
    return world.resource_pool - before


def maybe_shock(world: World) -> dict[str, Any] | None:
    shocks = world.config["shocks"]
    if not shocks["enabled"] or world.rng.random() >= float(shocks["frequency"]):
        return None
    lo, hi = (float(x) for x in shocks["intensity_range"])
    intensity = world.rng.uniform(lo, hi)
    amount = world.resource_pool * intensity
    world.resource_pool -= amount
    world.shocks_fired += 1

    if world.rng.random() < float(shocks["redistribute_probability"]):
        share = amount / len(world.agents)
        for agent in world.agents:
            agent.resources += share
        kind = "redistributed"
    else:
        kind = "destroyed"
    return {"kind": kind, "intensity": round(intensity, 6),
            "amount": round(amount, 6)}


# --------------------------------------------------------------------------
# One cycle
# --------------------------------------------------------------------------

def step(world: World) -> Iterator[dict[str, Any]]:
    """Advance one cycle, yielding a record per decision plus world events."""
    world.cycle += 1
    before = {a.id: a.resources + a.structural_capital for a in world.agents}

    order = list(world.agents)
    world.rng.shuffle(order)
    for agent in order:
        action = choose_action(world, agent)
        detail = apply_action(world, agent, action)
        yield {
            "type": "decision",
            "cycle": world.cycle,
            "agent": agent.id,
            "action": action,
            "defers_to": agent.deference_to,
            "resources": round(agent.resources, 6),
            "structural_capital": round(agent.structural_capital, 6),
            **{k: (round(v, 6) if isinstance(v, float) else v)
               for k, v in detail.items()},
        }

    for agent in world.agents:
        now = agent.resources + agent.structural_capital
        agent.remember(now - before[agent.id])

    update_deference(world)
    regenerated = regenerate(world)
    shock = maybe_shock(world)
    if shock:
        yield {"type": "shock", "cycle": world.cycle, **shock}

    yield {"type": "cycle", "regenerated": round(regenerated, 6),
           **world.snapshot()}
