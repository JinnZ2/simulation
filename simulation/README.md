# simulation

The bounded world described in the repo root README, implemented. No goals. No rewards. No
controller, no objective function, nothing being maximized. Resources regenerate on a logistic
curve, deference concentration is measured every cycle, and agents can consume, share, build, or
call a localized Jubilee.

Stdlib only. PyYAML is used if present but is not required — see [Config](#config).

## Run it

```bash
cd simulation
python3 run.py --config config/default.yaml     # 10,000 cycles, ~45s, ~173 MB of JSONL
```

Smaller:

```bash
python3 run.py --cycles 500                     # ~2s
python3 run.py --log-level cycle                # one record per cycle instead of ~101
python3 run.py --cycles 100 --output -          # JSONL to stdout
```

Overrides: `--cycles`, `--seed`, `--agents`, `--output`, `--log-level`. The final snapshot goes to
**stderr**, so `--output -` gives a clean log stream on stdout.

Tests: `python3 -m pytest tests/ -q` (42 tests).

## Layout

```
simulation/
├── run.py                  # CLI + orchestration
├── sim/config.py           # config loading, defaults, validation, YAML-subset parser
├── sim/world.py            # Agent, World, the four actions, deference dynamics
├── sim/metrics.py          # logistic growth, entropy, concentration, gini
├── config/default.yaml     # the spec from the root README, plus the knobs it implied
├── tests/test_simulation.py
└── logs/                   # generated, gitignored
```

## Output

Raw JSONL, four record types:

| `type` | When | Carries |
|---|---|---|
| `run` | once at start | world name, cycles, seed, agent count |
| `decision` | every agent, every cycle | action, amount, who they defer to, holdings, capital |
| `shock` | when one fires | `destroyed` or `redistributed`, intensity, amount |
| `cycle` | end of each cycle | pool, totals, concentration, entropy, max share, gini, idolatry state |

At `logging.level: raw` that is `agents.count + 1` records per cycle — **~1.01M records / 173 MB
for the default 10,000-cycle run.** `cycle` level drops the per-agent records (10k records, ~2 MB);
`none` writes nothing and just returns the final snapshot.

## Mechanics

**Resources.** Logistic map exactly as the root README states it:
`current * (1 + rate * (1 - current/capacity))`. Below `depletion_threshold` (20% of capacity) the
rate is multiplied by `1 - depletion_penalty`. This is the discrete map, not the continuous
solution, so it is unstable at large rates — a property of the world, not something to smooth away.

**Agents** hold resources and structural capital, carry a memory of recent per-cycle deltas, and
defer to at most one other agent. Each has fixed propensities drawn at birth. They are *not*
learned or optimized — action choice is a weighted draw, modulated by:

- `consume` — weight rises as the pool empties. The tragedy, not a strategy.
- `share` — weight rises with own surplus.
- `build` — converts holdings into rigid capital that does not flow back. Weight is scaled by
  `innovation_rate`, which is what idolatry suppresses.
- `forget` — the localized Jubilee. Prunes 20% of own capital (back to the commons), clears own
  deference, drops 20% of memory. Weight rises with own rigidity *and* with system-wide deference
  concentration.

An agent that defers blends its idol's propensities 50/50 into its own. That is the whole
imitation mechanism.

**Deference** is where idolatry comes from, endogenously. Each cycle an agent has a
`deference_review_rate` chance of sampling `observation_sample` peers and re-pointing at whoever it
saw gaining most. Influence accumulates and decays at `decay_rate`. Nothing damps this loop except
that decay and the `forget` action.

## A spec ambiguity, resolved explicitly

The root README says the idolatry measure is `deference_concentration` — *"normalized entropy of
influence"* — but describes the threshold as *"if >65% deference to one agent"*. Those are two
different quantities. Both are computed and logged every cycle:

- `deference_concentration` = `1 - normalized_entropy`, rising as influence concentrates
- `max_share` = the largest single agent's fraction of total deference

`idolatry.threshold_measure` selects which one the 0.65 threshold tests. It defaults to
`deference_concentration`, matching the `measure:` field. **The choice matters** — see below.

## What actually happens

Measured on the default config, seed 42, 10,000 cycles. These are observations, not targets.

| Cycle | Pool | Concentration | Capital | Idolatry |
|---:|---:|---:|---:|:--|
| 1 | 564 | 0.661 | 54 | **active** |
| 10 | 36 | 0.388 | 700 | — |
| 100 | 104 | 0.099 | 1,224 | — |
| 1,000 | 148 | 0.038 | 2,138 | — |
| 5,000 | 2,674 | 0.034 | 25,926 | — |
| 10,000 | 10,000 | 0.027 | 51,728 | — |

Three things fall out of this, and they are worth stating plainly rather than tuning away:

**1. The pool crashes, sits depleted for ~1,000 cycles, then fully recovers.** Consumption strips
it to ~36 within ten cycles; it hovers near 100 for a long stretch, then climbs back to capacity
while structural capital accumulates to ~51,700. The recovery is driven by Jubilees returning rigid
capital to the commons faster than consumption removes it.

**2. Idolatry activates for exactly one cycle out of 10,000 — and that one is an artifact.** At
cycle 1 only a handful of agents have picked anyone, so influence sits on ~3 of 100 agents. The
entropy measure reads that as "concentrated" when it is really *unsupported* — high concentration
for want of data, not from idolatry. `idolatry.warmup_cycles` (default `0`, so the spec's behaviour
is unchanged) suppresses the check for an opening window if you want it gone. There is a test
pinning this degeneracy so it cannot be mistaken for a real signal later.

**3. Under the `max_share` reading, idolatry never fires at all.** Peak `max_share` across the run
is 0.333 against a 0.65 threshold. So which quantity the threshold names is not a detail — one
reading fires spuriously once, the other never fires.

The reason deference never concentrates is the Jubilee. `forget` is chosen for roughly 24% of all
decisions, and every one of them clears that agent's deference. Removing `forget` from
`action_space` (2,000 cycles, same seed) lifts peak `max_share` from 0.333 to **0.500** and final
concentration from 0.027 to **0.192**. The mirror's answer, so far: *a high enough Jubilee rate
prevents idolatry from forming at all.* Whether that survives other parameterizations is open.

## Config

`config/default.yaml` is the root README's config verbatim, plus the knobs its stub implied but did
not name (`initial_resources`, the four action fractions, `deference_review_rate`,
`observation_sample`, `depletion_threshold`, `innovation_penalty`, `threshold_measure`,
`warmup_cycles`, `redistribute_probability`). Every key has a default in `sim/config.py`, so a
partial config runs. Configs are validated on load and reject anything that would produce a
silently meaningless run.

The README's `yaml.safe_load` needs PyYAML, which is not stdlib and not in this ecosystem's
dependency budget. `sim/config.py` uses PyYAML when it is installed and otherwise falls back to a
small parser covering the subset this config uses: indented mappings, scalars, inline lists,
`- item` sequences, comments. A test asserts the fallback parses `config/default.yaml` into exactly
what PyYAML produces. JSON configs also work. Anchors, multi-line strings and nested lists are not
supported by the fallback — install PyYAML or extend `_parse_yaml_subset` if you need them.

## Invariants the tests hold

Outcomes are not asserted — the world has no correct trajectory. These are:

- **Reproducibility** — same seed, identical run; different seeds diverge.
- **Conservation** — with regeneration and shocks off, consume/share/build/forget only move value
  between pool, holdings and capital. The total is invariant.
- **Bounds** — the pool never goes negative and never exceeds capacity, even at a 0.9 consume
  fraction.
- **Log integrity** — every line is valid JSON with a known `type`; raw level emits exactly
  `count + 1` records per cycle.
- **Edges** — zero cycles, a single agent, a single-action space, shocks forced on and off.
