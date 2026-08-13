"""Config loading.

The README specifies `config/default.yaml` and `yaml.safe_load`. PyYAML is not
in the standard library, and the surrounding ecosystem is stdlib-only, so this
module uses PyYAML when it happens to be installed and otherwise falls back to a
small parser covering the subset of YAML the config actually uses: nested
mappings by indentation, scalars, inline lists, comments, blank lines, and
`- item` sequences. JSON configs are also accepted.

If you extend default.yaml past that subset (anchors, multi-line strings, nested
lists), either install PyYAML or extend `_parse_yaml_subset`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:  # pragma: no cover - depends on environment
    import yaml  # type: ignore
    HAVE_PYYAML = True
except ImportError:
    HAVE_PYYAML = False


# --------------------------------------------------------------------------
# Defaults — mirror config/default.yaml so a partial config still runs
# --------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "world": {"name": "Basin", "cycles": 10000, "seed": 42},
    "resources": {
        "type": "regenerating_pool",
        "initial": 1000.0,
        "capacity": 10000.0,
        "regeneration_rate": 0.02,
        "depletion_penalty": 0.3,
        "depletion_threshold": 0.2,
    },
    "agents": {
        "count": 100,
        "memory_length": 50,
        "initial_resources": 10.0,
        "consume_fraction": 0.02,
        "share_fraction": 0.25,
        "build_fraction": 0.35,
        "forget_fraction": 0.2,
        "deference_review_rate": 0.05,
        "observation_sample": 8,
        "action_space": ["consume", "share", "build", "forget"],
    },
    "idolatry": {
        "enabled": True,
        "measure": "deference_concentration",
        "threshold": 0.65,
        "threshold_measure": "deference_concentration",
        "innovation_penalty": 0.4,
        "decay_rate": 0.005,
        "warmup_cycles": 0,
    },
    "shocks": {
        "enabled": True,
        "frequency": 0.001,
        "intensity_range": [0.1, 0.4],
        "redistribute_probability": 0.5,
    },
    "logging": {"level": "raw", "output": "logs/run_{timestamp}.jsonl"},
}

VALID_LOG_LEVELS = ("raw", "cycle", "none")


# --------------------------------------------------------------------------
# YAML subset parser
# --------------------------------------------------------------------------

_INLINE_LIST = re.compile(r"^\[(.*)\]$")


def _coerce(token: str) -> Any:
    """Turn a YAML scalar into a Python value."""
    token = token.strip()
    if not token:
        return None
    if (token.startswith('"') and token.endswith('"')) or \
       (token.startswith("'") and token.endswith("'")):
        return token[1:-1]
    lowered = token.lower()
    if lowered in ("true", "yes", "on"):
        return True
    if lowered in ("false", "no", "off"):
        return False
    if lowered in ("null", "~", "none"):
        return None
    inline = _INLINE_LIST.match(token)
    if inline:
        body = inline.group(1).strip()
        if not body:
            return []
        return [_coerce(part) for part in body.split(",")]
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token


def _strip_comment(line: str) -> str:
    """Drop a trailing ``#`` comment that is not inside quotes."""
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _significant_lines(text: str) -> list[tuple[int, str]]:
    """(indent, content) for every line that carries data."""
    out: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line.strip():
            continue
        out.append((len(line) - len(line.lstrip(" ")), line.strip()))
    return out


def _parse_block(lines: list[tuple[int, str]], start: int,
                 indent: int) -> tuple[Any, int]:
    """Parse one block at `indent`, returning (value, index after the block).

    A block is a sequence if its first line begins with '- ', otherwise a
    mapping. Nesting is resolved by recursion on deeper indentation, so no
    parser-wide mutable state is needed.
    """
    if lines[start][1].startswith("- "):
        items: list[Any] = []
        i = start
        while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            items.append(_coerce(lines[i][1][2:]))
            i += 1
        return items, i

    mapping: dict[str, Any] = {}
    i = start
    while i < len(lines) and lines[i][0] == indent:
        line_indent, content = lines[i]
        if ":" not in content:
            raise ValueError(f"expected 'key: value', got {content!r}")
        key, _, value = content.partition(":")
        key, value = key.strip(), value.strip()
        i += 1
        if value:
            mapping[key] = _coerce(value)
            continue
        # empty value: a nested block if the next line is deeper, else null
        if i < len(lines) and lines[i][0] > line_indent:
            mapping[key], i = _parse_block(lines, i, lines[i][0])
        else:
            mapping[key] = None
    return mapping, i


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the indentation-based mapping/sequence subset used by the config."""
    lines = _significant_lines(text)
    if not lines:
        return {}
    value, consumed = _parse_block(lines, 0, lines[0][0])
    if consumed != len(lines):
        bad = lines[consumed]
        raise ValueError(f"unexpected indentation at {bad[1]!r}")
    if not isinstance(value, dict):
        raise ValueError("expected a mapping at the top level")
    return value


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `override` onto a copy of `base`."""
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def parse_config_text(text: str, is_json: bool = False) -> dict[str, Any]:
    if is_json:
        return json.loads(text)
    if HAVE_PYYAML:
        return yaml.safe_load(text) or {}
    return _parse_yaml_subset(text)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a config file and merge it over DEFAULTS."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    parsed = parse_config_text(text, is_json=path.suffix.lower() == ".json")
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    config = deep_merge(DEFAULTS, parsed)
    validate(config)
    return config


def validate(config: dict[str, Any]) -> None:
    """Fail loudly on configs that would produce silently meaningless runs."""
    world, res = config["world"], config["resources"]
    agents, shocks = config["agents"], config["shocks"]
    idol, logcfg = config["idolatry"], config["logging"]

    if int(world["cycles"]) < 0:
        raise ValueError("world.cycles must be >= 0")
    if int(agents["count"]) < 1:
        raise ValueError("agents.count must be >= 1")
    if int(agents["memory_length"]) < 1:
        raise ValueError("agents.memory_length must be >= 1")
    if float(res["capacity"]) <= 0:
        raise ValueError("resources.capacity must be > 0")
    if float(res["initial"]) < 0:
        raise ValueError("resources.initial must be >= 0")
    if not 0.0 <= float(res["depletion_penalty"]) <= 1.0:
        raise ValueError("resources.depletion_penalty must be in [0, 1]")
    if not 0.0 <= float(shocks["frequency"]) <= 1.0:
        raise ValueError("shocks.frequency must be in [0, 1]")

    lo, hi = shocks["intensity_range"]
    if not 0.0 <= float(lo) <= float(hi) <= 1.0:
        raise ValueError("shocks.intensity_range must satisfy 0 <= lo <= hi <= 1")

    if not 0.0 <= float(idol["threshold"]) <= 1.0:
        raise ValueError("idolatry.threshold must be in [0, 1]")
    if idol["threshold_measure"] not in ("deference_concentration", "max_share"):
        raise ValueError("idolatry.threshold_measure must be "
                         "'deference_concentration' or 'max_share'")
    if not 0.0 <= float(idol["innovation_penalty"]) <= 1.0:
        raise ValueError("idolatry.innovation_penalty must be in [0, 1]")
    if int(idol["warmup_cycles"]) < 0:
        raise ValueError("idolatry.warmup_cycles must be >= 0")

    if logcfg["level"] not in VALID_LOG_LEVELS:
        raise ValueError(f"logging.level must be one of {VALID_LOG_LEVELS}")

    unknown = set(agents["action_space"]) - {"consume", "share", "build", "forget"}
    if unknown:
        raise ValueError(f"unknown actions in agents.action_space: {sorted(unknown)}")
    if not agents["action_space"]:
        raise ValueError("agents.action_space must not be empty")
