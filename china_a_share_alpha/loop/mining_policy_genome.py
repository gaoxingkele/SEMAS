"""Recursive Self-Improvement (RSI) policy genome for the factor-mining loop.

Outer-loop object: mining-loop hyperparameters / gates / search policy.
Inner-loop object: factor expressions (unchanged).

Islands keep open-ended search from collapsing onto one repair recipe
(relax_dedup + expand_dag + shrink_top_n).

[source: SEMAS_SELF_UPGRADE_DESIGN.md]
[source: arXiv:2410.04444]
[source: arXiv:2505.22954]
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

import yaml

# Orthogonal RSI mutation surfaces. Evaluator gates are deliberately excluded:
# the search policy must not make itself look better by changing its examiner.
ISLANDS: tuple[str, ...] = (
    "search_budget",
    "parent_selection",
    "diversity",
    "structure",
)

MUTATION_FIELDS: dict[str, tuple[str, ...]] = {
    "search_budget": ("population_size", "max_generations", "patience"),
    "parent_selection": ("parent_mode", "global_epsilon", "dag_edge_similarity"),
    "diversity": (
        "semantic_dedup_corr_threshold",
        "keep_diversity_slots",
        "top_n",
    ),
    "structure": ("ast_regularizer_enabled", "ast_similarity_tau"),
}

LEGACY_ISLAND_MAP: dict[str, str] = {
    "search": "search_budget",
    "gate_relax": "diversity",
    "structure_light": "structure",
    "promote_soft": "diversity",
    "global_mix": "parent_selection",
}


@dataclass
class MiningPolicyGenome:
    """Evolvable outer-loop policy for one factor-mining iteration."""

    semantic_dedup_corr_threshold: float = 0.95
    keep_diversity_slots: int = 0
    ast_regularizer_enabled: bool = True
    ast_similarity_tau: float = 0.85
    parent_mode: str = "dag_neighbors"  # or "global"
    population_size: int = 25
    max_generations: int = 8
    patience: int = 3
    global_epsilon: float = 0.15
    dag_edge_similarity: float = 0.35
    top_n: int = 10
    promote_hold_sharpe_threshold: float = 0.03
    max_selection_correlation_gate: float = 0.7
    island: str = "search_budget"
    version: int = 1
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MiningPolicyGenome":
        allowed = {f.name for f in fields(cls)}
        cleaned = {k: v for k, v in data.items() if k in allowed}
        if "island" in cleaned:
            cleaned["island"] = LEGACY_ISLAND_MAP.get(
                str(cleaned["island"]), str(cleaned["island"])
            )
            if cleaned["island"] not in ISLANDS:
                cleaned["island"] = "search_budget"
        return cls(**cleaned)

    @classmethod
    def from_yaml(cls, path: Path) -> "MiningPolicyGenome":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(raw)

    def to_yaml(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    def fingerprint(self) -> tuple[Any, ...]:
        """Coarse signature used for novelty / anti-collapse sampling."""
        return (
            round(float(self.semantic_dedup_corr_threshold), 2),
            int(self.keep_diversity_slots),
            str(self.parent_mode),
            int(self.top_n),
            round(float(self.ast_similarity_tau), 2),
            int(bool(self.ast_regularizer_enabled)),
            round(float(self.global_epsilon), 2),
            round(float(self.max_selection_correlation_gate), 2),
            round(float(self.promote_hold_sharpe_threshold), 2),
            str(self.island),
        )


def apply_policy_to_loop_config(
    base_loop: dict[str, Any],
    policy: MiningPolicyGenome,
) -> dict[str, Any]:
    """Overlay policy knobs onto a factor_mining_loop_config dict."""
    cfg = dict(base_loop)
    cfg["semantic_dedup_corr_threshold"] = float(policy.semantic_dedup_corr_threshold)
    cfg["keep_diversity_slots"] = int(policy.keep_diversity_slots)
    cfg["ast_regularizer_enabled"] = bool(policy.ast_regularizer_enabled)
    cfg["ast_similarity_tau"] = float(policy.ast_similarity_tau)
    cfg["top_n"] = int(policy.top_n)
    cfg["promote_hold_sharpe_threshold"] = float(policy.promote_hold_sharpe_threshold)
    cfg["max_selection_correlation_gate"] = float(policy.max_selection_correlation_gate)
    cfg["rsi_policy_version"] = int(policy.version)
    cfg["rsi_policy_notes"] = str(policy.notes)
    cfg["rsi_island"] = str(policy.island)
    return cfg


def apply_policy_to_evolution_config(
    base_evo: dict[str, Any],
    policy: MiningPolicyGenome,
) -> dict[str, Any]:
    """Overlay policy knobs onto the evolution YAML dict."""
    cfg = dict(base_evo)
    cfg["population_size"] = int(policy.population_size)
    cfg["max_generations"] = int(policy.max_generations)
    cfg["patience"] = int(policy.patience)
    cfg["parent_mode"] = str(policy.parent_mode)
    cfg["global_epsilon"] = float(policy.global_epsilon)
    cfg["dag_edge_similarity"] = float(policy.dag_edge_similarity)
    cfg["ast_regularizer_enabled"] = bool(policy.ast_regularizer_enabled)
    cfg["ast_similarity_tau"] = float(policy.ast_similarity_tau)
    return cfg


__all__ = [
    "ISLANDS",
    "MUTATION_FIELDS",
    "MiningPolicyGenome",
    "apply_policy_to_loop_config",
    "apply_policy_to_evolution_config",
]
