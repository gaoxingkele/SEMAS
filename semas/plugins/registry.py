"""Plugin registry for SEMAS evolution extensions.

Plugins can be registered programmatically or discovered via Python
``entry_points``. The registry is intentionally minimal to keep SEMAS
portable.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from semas.plugins.base import (
    CandidateOptimizer,
    MutatorStrategy,
    SelfModificationPolicy,
    WeightUpdateStrategy,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Collects evolution plugins and exposes them to the Orchestrator."""

    def __init__(self) -> None:
        self._mutator_strategies: list[MutatorStrategy] = []
        self._candidate_optimizers: list[CandidateOptimizer] = []
        self._weight_update_strategies: list[WeightUpdateStrategy] = []
        self._self_mod_policy: SelfModificationPolicy | None = None

    # ------------------------------------------------------------------
    # Programmatic registration
    # ------------------------------------------------------------------
    def register_mutator_strategy(self, strategy: MutatorStrategy) -> None:
        self._mutator_strategies.append(strategy)

    def register_candidate_optimizer(self, optimizer: CandidateOptimizer) -> None:
        self._candidate_optimizers.append(optimizer)

    def register_weight_update_strategy(self, strategy: WeightUpdateStrategy) -> None:
        self._weight_update_strategies.append(strategy)

    def register_self_modification_policy(self, policy: SelfModificationPolicy) -> None:
        self._self_mod_policy = policy

    # ------------------------------------------------------------------
    # Entry-point discovery
    # ------------------------------------------------------------------
    def load_entry_points(self) -> None:
        """Load plugins registered via ``pyproject.toml`` entry points.

        Supported groups:

        - ``semas.mutator_strategy``
        - ``semas.candidate_optimizer``
        - ``semas.weight_update_strategy``
        - ``semas.self_modification_policy``
        """
        try:
            from importlib.metadata import entry_points
        except ImportError:  # pragma: no cover
            import importlib_metadata as entry_points  # type: ignore

        groups = {
            "semas.mutator_strategy": self.register_mutator_strategy,
            "semas.candidate_optimizer": self.register_candidate_optimizer,
            "semas.weight_update_strategy": self.register_weight_update_strategy,
            "semas.self_modification_policy": self.register_self_modification_policy,
        }

        eps = entry_points()
        for group, register in groups.items():
            for ep in eps.get(group, []):
                try:
                    obj = ep.load()
                    register(obj() if callable(obj) else obj)
                    logger.info("Loaded plugin %s from %s", ep.name, ep.value)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to load plugin %s: %s", ep.value, exc)

    # ------------------------------------------------------------------
    # Configuration-driven loading
    # ------------------------------------------------------------------
    def load_from_config(self, config: dict[str, Any]) -> None:
        """Load plugins by dotted import paths.

        Example config::

            {
                "mutator_strategies": [
                    "semas.plugins.function_evolve:FunctionEvolveToolMutator",
                ],
                "candidate_optimizers": [
                    "semas.plugins.function_evolve:FunctionEvolveToolOptimizer",
                ],
            }
        """
        for path in config.get("mutator_strategies", []):
            self.register_mutator_strategy(self._import(path))
        for path in config.get("candidate_optimizers", []):
            self.register_candidate_optimizer(self._import(path))
        for path in config.get("weight_update_strategies", []):
            self.register_weight_update_strategy(self._import(path))
        policy = config.get("self_modification_policy")
        if policy:
            self.register_self_modification_policy(self._import(policy))

    @staticmethod
    def _import(dotted_path: str) -> Any:
        module_name, _, attr_name = dotted_path.partition(":")
        module = importlib.import_module(module_name)
        obj = getattr(module, attr_name)
        return obj() if callable(obj) else obj

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    @property
    def mutator_strategies(self) -> list[MutatorStrategy]:
        return list(self._mutator_strategies)

    @property
    def candidate_optimizers(self) -> list[CandidateOptimizer]:
        return list(self._candidate_optimizers)

    @property
    def weight_update_strategies(self) -> list[WeightUpdateStrategy]:
        return list(self._weight_update_strategies)

    @property
    def self_modification_policy(self) -> SelfModificationPolicy | None:
        return self._self_mod_policy
