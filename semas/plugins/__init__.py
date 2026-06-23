"""SEMAS evolution plugin layer.

This package defines extension points that allow external self-evolution
methodologies (e.g. FunctionEvolve, SIA, Gödel Agent) to be plugged into the
SEMAS orchestration loop without modifying the core framework.
"""

from __future__ import annotations

from semas.plugins.base import (
    CandidateOptimizer,
    MutatorStrategy,
    SelfModificationPolicy,
    WeightUpdateStrategy,
)
from semas.plugins.registry import PluginRegistry

__all__ = [
    "CandidateOptimizer",
    "MutatorStrategy",
    "SelfModificationPolicy",
    "WeightUpdateStrategy",
    "PluginRegistry",
]
