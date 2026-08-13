"""Tests for the bounded world.

These check mechanics and conservation, not outcomes. The world has no
objective, so there is no "correct" trajectory to assert — only invariants that
must hold however it evolves.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from run import run_simulation  # noqa: E402
from sim import config as cfgmod  # noqa: E402
from sim.config import DEFAULTS, deep_merge, load_config, validate  # noqa: E402
from sim.metrics import (  # noqa: E402
    deference_concentration,
    gini,
    logistic_growth,
    max_share,
    normalized_entropy,
)
from sim.world import build_world, regenerate, step  # noqa: E402

CONFIG = ROOT / "config" / "default.yaml"


def small_config(**overrides):
    base = deep_merge(DEFAULTS, {
        "world": {"cycles": 20, "seed": 7},
        "agents": {"count": 8},
        "logging": {"level": "none"},
    })
    return deep_merge(base, overrides)


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------

def test_logistic_growth_matches_readme_formula():
    assert logistic_growth(100.0, 1000.0, 0.02) == pytest.approx(100 * (1 + 0.02 * 0.9))


def test_logistic_growth_is_zero_at_capacity():
    assert logistic_growth(1000.0, 1000.0, 0.02) == pytest.approx(1000.0)


def test_normalized_entropy_bounds():
    assert normalized_entropy([1, 1, 1, 1]) == pytest.approx(1.0)
    assert normalized_entropy([1, 0, 0, 0]) == pytest.approx(0.0)
    assert normalized_entropy([]) == 0.0


def test_concentration_is_inverse_of_entropy():
    influence = {0: 3.0, 1: 1.0, 2: 1.0}
    assert deference_concentration(influence) == pytest.approx(
        1.0 - normalized_entropy(influence.values()))


def test_max_share_and_gini_extremes():
    assert max_share({0: 5.0, 1: 5.0}) == pytest.approx(0.5)
    assert max_share({0: 0.0, 1: 0.0}) == 0.0
    assert gini([1, 1, 1, 1]) == pytest.approx(0.0, abs=1e-9)
    assert gini([0, 0, 0, 100]) > 0.7


def test_concentration_is_degenerate_at_low_support():
    """The startup artifact: few holders reads as 'concentrated' regardless.

    This is why idolatry.warmup_cycles exists. Three agents holding equal
    influence out of a hundred is not idolatry, but the entropy measure scores
    it above the 0.65 threshold.
    """
    influence = {i: (1.0 if i < 3 else 0.0) for i in range(100)}
    assert deference_concentration(influence) > 0.65


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def test_default_config_loads_and_validates():
    config = load_config(CONFIG)
    assert config["world"]["name"] == "Basin"
    assert config["world"]["cycles"] == 10000
    assert config["agents"]["action_space"] == ["consume", "share", "build", "forget"]
    assert config["shocks"]["intensity_range"] == [0.1, 0.4]


def test_yaml_fallback_parses_default_config_identically(monkeypatch):
    """The stdlib parser must agree with PyYAML on the real config file."""
    if not cfgmod.HAVE_PYYAML:  # pragma: no cover
        pytest.skip("PyYAML absent; nothing to compare against")
    import yaml
    text = CONFIG.read_text(encoding="utf-8")
    expected = yaml.safe_load(text)
    monkeypatch.setattr(cfgmod, "HAVE_PYYAML", False)
    assert cfgmod.parse_config_text(text) == expected


def test_yaml_fallback_handles_subset_features():
    parsed = cfgmod._parse_yaml_subset(
        'a: 1\n'
        'b: "quoted # not a comment"\n'
        'c: true\n'
        'd: [1, 2, 3]\n'
        'nested:\n'
        '  x: 1.5\n'
        '  deeper:\n'
        '    y: null\n'
        'seq:\n'
        '  - one\n'
        '  - two   # trailing comment\n'
    )
    assert parsed == {
        "a": 1, "b": "quoted # not a comment", "c": True, "d": [1, 2, 3],
        "nested": {"x": 1.5, "deeper": {"y": None}},
        "seq": ["one", "two"],
    }


def test_partial_config_inherits_defaults(tmp_path):
    path = tmp_path / "partial.yaml"
    path.write_text("world:\n  cycles: 5\n", encoding="utf-8")
    config = load_config(path)
    assert config["world"]["cycles"] == 5
    assert config["world"]["name"] == "Basin"          # from defaults
    assert config["agents"]["count"] == 100            # from defaults


def test_json_config_accepted(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"world": {"cycles": 3}}), encoding="utf-8")
    assert load_config(path)["world"]["cycles"] == 3


@pytest.mark.parametrize("bad", [
    {"agents": {"count": 0}},
    {"resources": {"capacity": 0.0}},
    {"shocks": {"intensity_range": [0.5, 0.2]}},
    {"idolatry": {"threshold": 1.5}},
    {"idolatry": {"threshold_measure": "vibes"}},
    {"logging": {"level": "chatty"}},
    {"agents": {"action_space": ["consume", "pray"]}},
    {"agents": {"action_space": []}},
])
def test_validate_rejects_bad_configs(bad):
    with pytest.raises(ValueError):
        validate(deep_merge(DEFAULTS, bad))


# --------------------------------------------------------------------------
# world mechanics
# --------------------------------------------------------------------------

def test_build_world_is_deterministic_under_seed():
    a = build_world(small_config(), random.Random(7))
    b = build_world(small_config(), random.Random(7))
    assert [x.propensity for x in a.agents] == [x.propensity for x in b.agents]


def test_run_is_reproducible():
    first = run_simulation(small_config())
    second = run_simulation(small_config())
    assert first == second


def test_different_seeds_diverge():
    a = run_simulation(small_config(world={"seed": 1}))
    b = run_simulation(small_config(world={"seed": 2}))
    assert a != b


def test_value_is_conserved_without_regeneration_or_shocks():
    """Total value only moves between pool, holdings and capital.

    consume/share/build/forget are all transfers, so with regeneration and
    shocks switched off the sum is invariant.
    """
    config = small_config(
        resources={"regeneration_rate": 0.0},
        shocks={"enabled": False},
        world={"cycles": 50},
    )
    world = build_world(config, random.Random(config["world"]["seed"]))
    total = lambda w: (w.resource_pool + sum(a.resources for a in w.agents)
                       + sum(a.structural_capital for a in w.agents))
    start = total(world)
    for _ in range(50):
        list(step(world))
    assert total(world) == pytest.approx(start, rel=1e-9)


def test_pool_never_negative_and_never_exceeds_capacity():
    config = small_config(world={"cycles": 200}, agents={"consume_fraction": 0.9})
    world = build_world(config, random.Random(3))
    capacity = config["resources"]["capacity"]
    for _ in range(200):
        list(step(world))
        assert 0.0 <= world.resource_pool <= capacity


def test_depletion_penalty_slows_regeneration():
    """Compare at the *same* pool level with the penalty on and off.

    Comparing a depleted pool against a healthy one would measure the logistic
    term (1 - c/K), which is larger when the pool is low — the opposite of what
    this test is about.
    """
    capacity = DEFAULTS["resources"]["capacity"]
    depleted = 0.1 * capacity                      # below the 20% threshold

    penalized_world = build_world(small_config(), random.Random(1))
    penalized_world.resource_pool = depleted
    penalized = regenerate(penalized_world)

    free_world = build_world(
        small_config(resources={"depletion_penalty": 0.0}), random.Random(1))
    free_world.resource_pool = depleted
    unpenalized = regenerate(free_world)

    assert penalized < unpenalized
    assert penalized == pytest.approx(unpenalized * 0.7)   # 1 - 0.3


def test_no_penalty_above_the_depletion_threshold():
    capacity = DEFAULTS["resources"]["capacity"]
    healthy = 0.5 * capacity                       # above the threshold

    a = build_world(small_config(), random.Random(1))
    a.resource_pool = healthy
    b = build_world(small_config(resources={"depletion_penalty": 0.0}),
                    random.Random(1))
    b.resource_pool = healthy

    assert regenerate(a) == pytest.approx(regenerate(b))


def test_idolatry_suppresses_innovation_rate():
    config = small_config(idolatry={"threshold": 0.0})   # always over threshold
    world = build_world(config, random.Random(1))
    world.influence = {a.id: 0.0 for a in world.agents}
    world.influence[0] = 1.0
    world.cycle = 1
    assert world.idolatry_active()
    assert world.innovation_rate() == pytest.approx(0.6)


def test_warmup_cycles_suppresses_the_startup_artifact():
    config = small_config(idolatry={"threshold": 0.0, "warmup_cycles": 5})
    world = build_world(config, random.Random(1))
    world.influence[0] = 1.0
    world.cycle = 3
    assert not world.idolatry_active()
    world.cycle = 6
    assert world.idolatry_active()


def test_idolatry_can_be_disabled():
    config = small_config(idolatry={"enabled": False, "threshold": 0.0})
    world = build_world(config, random.Random(1))
    world.influence[0] = 1.0
    world.cycle = 99
    assert not world.idolatry_active()
    assert world.innovation_rate() == 1.0


def test_forget_prunes_capital_and_clears_deference():
    from sim.world import apply_action
    config = small_config()
    world = build_world(config, random.Random(1))
    agent = world.agents[0]
    agent.structural_capital = 100.0
    agent.deference_to = 3
    pool_before = world.resource_pool

    detail = apply_action(world, agent, "forget")

    assert agent.structural_capital == pytest.approx(80.0)   # 20% pruned
    assert agent.deference_to is None
    assert world.resource_pool == pytest.approx(pool_before + 20.0)
    assert detail["amount"] == pytest.approx(20.0)
    assert world.jubilees == 1


def test_build_converts_holdings_to_rigid_capital():
    from sim.world import apply_action
    world = build_world(small_config(), random.Random(1))
    agent = world.agents[0]
    agent.resources = 100.0
    apply_action(world, agent, "build")
    assert agent.resources == pytest.approx(65.0)
    assert agent.structural_capital == pytest.approx(35.0)


def test_share_moves_value_between_agents_without_creating_it():
    from sim.world import apply_action
    world = build_world(small_config(), random.Random(1))
    giver = world.agents[0]
    giver.resources = 100.0
    before = sum(a.resources for a in world.agents)
    detail = apply_action(world, giver, "share")
    assert sum(a.resources for a in world.agents) == pytest.approx(before)
    assert detail["to"] != giver.id


def test_only_configured_actions_are_taken():
    from sim.world import choose_action
    config = small_config(agents={"action_space": ["consume"]})
    world = build_world(config, random.Random(1))
    for agent in world.agents:
        assert choose_action(world, agent) == "consume"


def test_shock_fires_at_frequency_one_and_moves_resources():
    config = small_config(shocks={"frequency": 1.0, "redistribute_probability": 0.0})
    world = build_world(config, random.Random(1))
    records = list(step(world))
    shocks = [r for r in records if r["type"] == "shock"]
    assert len(shocks) == 1
    assert shocks[0]["kind"] == "destroyed"
    assert world.shocks_fired == 1


def test_shocks_disabled_never_fire():
    config = small_config(shocks={"enabled": False}, world={"cycles": 100})
    world = build_world(config, random.Random(1))
    for _ in range(100):
        assert not [r for r in step(world) if r["type"] == "shock"]


# --------------------------------------------------------------------------
# logging
# --------------------------------------------------------------------------

def test_raw_log_has_one_decision_per_agent_per_cycle(tmp_path):
    out = tmp_path / "run.jsonl"
    config = small_config(world={"cycles": 10}, logging={"level": "raw"},
                          shocks={"enabled": False})
    run_simulation(config, str(out))
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    decisions = [r for r in rows if r["type"] == "decision"]
    cycles = [r for r in rows if r["type"] == "cycle"]
    assert len(cycles) == 10
    assert len(decisions) == 10 * config["agents"]["count"]
    assert rows[0]["type"] == "run"


def test_cycle_level_log_omits_decisions(tmp_path):
    out = tmp_path / "run.jsonl"
    run_simulation(small_config(world={"cycles": 5}, logging={"level": "cycle"}), str(out))
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert not [r for r in rows if r["type"] == "decision"]
    assert len([r for r in rows if r["type"] == "cycle"]) == 5


def test_log_level_none_writes_nothing(tmp_path):
    out = tmp_path / "run.jsonl"
    result = run_simulation(small_config(logging={"level": "none"}), str(out))
    assert not out.exists()
    assert result["records_written"] == 0


def test_timestamp_placeholder_is_expanded(tmp_path):
    out = tmp_path / "run_{timestamp}.jsonl"
    result = run_simulation(small_config(world={"cycles": 2},
                                         logging={"level": "cycle"}), str(out))
    assert "{timestamp}" not in result["log_path"]
    assert Path(result["log_path"]).exists()


def test_every_log_record_is_valid_json_with_a_type(tmp_path):
    out = tmp_path / "run.jsonl"
    config = small_config(world={"cycles": 30}, shocks={"frequency": 1.0},
                          logging={"level": "raw"})
    run_simulation(config, str(out))
    for line in out.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        assert record["type"] in ("run", "decision", "cycle", "shock")


def test_zero_cycles_is_a_valid_run():
    result = run_simulation(small_config(world={"cycles": 0}))
    assert result["cycle"] == 0


def test_single_agent_world_runs():
    result = run_simulation(small_config(agents={"count": 1}, world={"cycles": 10}))
    assert result["cycle"] == 10
    assert not math.isnan(result["deference_concentration"])
