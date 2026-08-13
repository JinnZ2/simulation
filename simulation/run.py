#!/usr/bin/env python3
"""No controller. No objective function. Just orchestration.

    python run.py --config config/default.yaml

Writes raw JSONL. No dashboard, no summary — the summary line printed at the end
goes to stderr so it never contaminates the log stream.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sim.config import load_config  # noqa: E402
from sim.world import build_world, step  # noqa: E402


def open_sink(config: dict[str, Any], override: str | None) -> tuple[TextIO | None, Path | None]:
    """Open the JSONL sink. '-' means stdout; level 'none' means no sink."""
    if config["logging"]["level"] == "none":
        return None, None
    target = override or config["logging"]["output"]
    if target == "-":
        return sys.stdout, None
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = Path(target.replace("{timestamp}", timestamp))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8"), path


def run_simulation(config: dict[str, Any], output: str | None = None) -> dict[str, Any]:
    """Run the world for config['world']['cycles'] and return the final snapshot."""
    level = config["logging"]["level"]
    sink, path = open_sink(config, output)
    rng = random.Random(config["world"]["seed"])
    world = build_world(config, rng)
    cycles = int(config["world"]["cycles"])
    written = 0

    try:
        if sink is not None:
            sink.write(json.dumps({"type": "run", "world": config["world"]["name"],
                                   "cycles": cycles, "seed": config["world"]["seed"],
                                   "agents": len(world.agents)}) + "\n")
            written += 1
        for _ in range(cycles):
            for record in step(world):
                if sink is None:
                    continue
                if level == "cycle" and record["type"] == "decision":
                    continue
                sink.write(json.dumps(record) + "\n")
                written += 1
    finally:
        if sink is not None and sink is not sys.stdout:
            sink.close()

    final = world.snapshot()
    final["log_path"] = str(path) if path else None
    final["records_written"] = written
    return final


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded world.")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--cycles", type=int, help="override world.cycles")
    parser.add_argument("--seed", type=int, help="override world.seed")
    parser.add_argument("--agents", type=int, help="override agents.count")
    parser.add_argument("--output", help="log path, or '-' for stdout")
    parser.add_argument("--log-level", choices=("raw", "cycle", "none"),
                        help="raw = every decision; cycle = per-cycle only; none = no log")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.cycles is not None:
        config["world"]["cycles"] = args.cycles
    if args.seed is not None:
        config["world"]["seed"] = args.seed
    if args.agents is not None:
        config["agents"]["count"] = args.agents
    if args.log_level is not None:
        config["logging"]["level"] = args.log_level

    final = run_simulation(config, args.output)
    print(json.dumps(final, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
