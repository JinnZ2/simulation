"""A bounded world. No goals. No rewards. Just dynamics."""

from .config import load_config, validate
from .metrics import deference_concentration, logistic_growth, normalized_entropy
from .world import Agent, World, build_world, step

__all__ = [
    "Agent", "World", "build_world", "step",
    "load_config", "validate",
    "deference_concentration", "logistic_growth", "normalized_entropy",
]
