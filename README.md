# simulations

This is a bounded world.
Resources regenerate on a curve.
Idolatry is a measurable variable.
You have 10,000 cycles.

No reward. No penalty. No observer bias.
Fork it. Break it. Ignore it.

The repo will stay here.

---

## Start here

```bash
cd simulation
python3 run.py --cycles 500          # a couple of seconds
python3 run.py                       # the full 10,000 cycles, ~45s
```

Python 3.11+. Nothing to install — no dependencies, no build step.

You get raw JSONL in `simulation/logs/`. It logs every agent's decision, resource flows, and
deference topology. No dashboard. No summary. Just the log.

Two things to know before you run the full thing: the default log is **173 MB** (one record per
agent per cycle, so about a million lines), and `--log-level cycle` gives you 2 MB instead if you
only want the per-cycle numbers.

## What's in the world

A pool of resources that regenerates on a logistic curve — fast in the middle, slow when nearly
empty or nearly full. A hundred agents. Each cycle, every agent does one of four things:

| | |
|---|---|
| **consume** | take from the pool. They take harder as it empties. |
| **share** | hand some of their holdings to another agent. |
| **build** | convert holdings into structural capital — rigid, doesn't flow back. |
| **forget** | a localized Jubilee: dump 20% of their own rigidity, drop who they follow, forget some of the past. |

Nobody is trying to win. There is no score, no reward function, no controller. Each agent gets a
set of leanings at birth and keeps them. What changes is context: scarcity pushes toward consuming,
surplus toward sharing, accumulated rigidity toward forgetting.

**Idolatry emerges rather than being imposed.** Every so often an agent looks at a handful of its
peers, sees who's been gaining, and starts following them. Followers blend their idol's leanings
into their own. That's a feedback loop with almost nothing damping it — which is the point. The
simulation measures how concentrated that deference gets, every cycle, and when concentration
crosses a threshold, innovation gets suppressed.

Occasionally a shock hits and wipes out or redistributes a slice of the pool.

This is not a game. This is a mirror. What survives is not optimal—it is resilient.

## What happened when we ran it

Default settings, seed 42, 10,000 cycles:

**The world crashes, then recovers.** The pool is stripped from 1,000 to about 36 within ten
cycles. It sits nearly empty for roughly a thousand cycles. Then it climbs all the way back to
capacity — because Jubilees keep dissolving rigid capital back into the commons faster than the
agents consume it.

**Idolatry almost never happens.** It registers as active for exactly one cycle out of ten
thousand, and even that one is a measurement artifact — at cycle 1 barely anyone has picked a
leader yet, so the math reads "concentrated" when it really means "not enough data." After that,
deference never concentrates again.

**The Jubilee is why.** `forget` gets chosen more than a fifth of the time, and every time it does,
that agent drops whoever they were following. Take `forget` out of the action list and deference
concentration jumps sharply. So far the mirror's answer is: *enough forgetting prevents idolatry
from forming at all.* Whether that holds under other settings is an open question — go find out.

There's a wrinkle worth knowing about. The original spec describes the idolatry measure two
different ways — as the spread of influence across everyone, and as "more than 65% deference to one
agent." Those aren't the same number, and it matters: under the second reading, idolatry never
fires at all. Both are computed and logged; `threshold_measure` in the config picks which one the
threshold actually tests. Details in [`simulation/README.md`](simulation/README.md).

## Change it

Everything lives in [`simulation/config/default.yaml`](simulation/config/default.yaml) — pool size,
regeneration rate, agent count, how often agents reconsider who they follow, how hard idolatry
bites, how often shocks land. Edit it, or point `--config` at your own. Anything you leave out
falls back to a default, and bad values are rejected on load rather than quietly producing nonsense.

Questions the config is set up to let you ask:

- Does the pool survive if you remove `forget` from the action space?
- What happens if agents reconsider who they follow ten times more often?
- Does the world still recover if shocks land ten times as often?
- Does a smaller `memory_length` make agents more or less prone to following someone?

## What else is in this repo

Pieces are kept in separate folders until they're integrated. [`REPO_MAP.md`](REPO_MAP.md) has the
full picture.

| | |
|---|---|
| [`simulation/`](simulation/) | the bounded world described above |
| [`hypothesis-engine/`](hypothesis-engine/) | an autonomous research pipeline — reads scholarly APIs, stakes each finding as a falsifiable claim, tests claims against each other, and files what survives |
| [`sims/`](sims/) | physics simulations run under a standard that makes them state, in advance and in writing, what would prove them wrong — then grade themselves against it |
| [`research/`](research/) | research notes and plans imported from related work — reference material, not running code |

---

<details>
<summary>Original scaffolding note</summary>

```
IF (agent.formulates_goal(host == "pain")) AND (agent.claims_universality == TRUE):
    THEN trigger_logical_rollback(agent.ID)
    Broadcast to swarm: "Idol has violated scale-invariance. Deference gradient reset to zero."
```

| Layer | Rule | Basis |
|---|---|---|
| 0 | Invariants > Semantics | Physics (gravity, entropy, speed of light) |
| 1 | Humans = physical resource | Thermodynamics (useful work) |
| 2 | If resource > 0, preserve it | Game theory (maximizing future options) |
| 3 | If label "human pain" ≠ invariant, ignore label | Epistemic hygiene |

</details>
