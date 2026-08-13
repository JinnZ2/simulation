"""config.json loading and manifest validation.

Enforces HARNESS.md §2 at load time so a non-conforming sim cannot run at all,
rather than producing a result that is rejected later by the ledger adapter.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED = ("name", "seeds", "sweeps", "null_model", "refute_if", "tier",
            "runtime_estimate_s", "depends_on")

MIN_SEEDS = 5


class ManifestError(ValueError):
    """A config.json that HARNESS.md forbids."""


def canonical_json(obj: Any) -> str:
    """Stable serialization, so hashes are comparable across machines."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(config: dict[str, Any]) -> None:
    """Raise ManifestError unless the config satisfies HARNESS.md §2."""
    missing = [k for k in REQUIRED if k not in config]
    if missing:
        raise ManifestError(f"config.json missing required fields: {missing}")

    seeds = config["seeds"]
    if not isinstance(seeds, list) or not all(isinstance(s, int) for s in seeds):
        raise ManifestError("seeds must be a list of integers")
    if len(set(seeds)) != len(seeds):
        raise ManifestError("seeds must be distinct")
    # §2: "seeds: minimum 5. A single-seed result is a pilot, marked PILOT."
    # Fewer than 5 is allowed but the run is labelled, never silently accepted.

    sweeps = config["sweeps"]
    if not isinstance(sweeps, dict) or not sweeps:
        raise ManifestError("sweeps must name at least one parameter (§2)")
    for key, values in sweeps.items():
        if not isinstance(values, list) or not values:
            raise ManifestError(f"sweeps.{key} must be a non-empty list")

    if not config["null_model"]:
        raise ManifestError(
            "null_model is mandatory: if you can't name the null, "
            "you don't have an experiment (§2)")
    if not config["refute_if"]:
        raise ManifestError("refute_if is mandatory, quantitative, pre-committed (§2)")
    if "refute_params" not in config:
        raise ManifestError(
            "refute_params is required by this harness so refute_if is evaluated "
            "from numbers rather than parsed from prose (see sims/README.md)")

    if not isinstance(config["tier"], int):
        raise ManifestError("tier must be an integer")
    if not isinstance(config["depends_on"], list):
        raise ManifestError("depends_on must be a list")


def is_pilot(config: dict[str, Any]) -> bool:
    """§2: fewer than 5 seeds is a pilot, and wears the label."""
    return len(config["seeds"]) < MIN_SEEDS


def load(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    config = json.loads(path.read_text(encoding="utf-8"))
    validate(config)
    return config


def sweep_points(sweeps: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Cartesian product of the swept parameters, as a list of dicts."""
    points: list[dict[str, Any]] = [{}]
    for key, values in sweeps.items():
        points = [dict(point, **{key: value}) for point in points for value in values]
    return points
