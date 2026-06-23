"""Configurable collaboration topology for the mingli five-agent system."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MingliWorkflow:
    """Workflow genes that control discussion, voting, and review behavior."""

    discussion_rounds: int = 2
    cross_check_enabled: bool = True
    reconciliation_enabled: bool = True
    source_review_strictness: str = "standard"  # standard | strict
    vote_threshold: float = 0.75
    preserve_conflicts: bool = True

    def to_meta(self) -> dict[str, Any]:
        """Serialize workflow for storage in AgentGenome.meta."""
        return asdict(self)


def workflow_from_meta(meta: dict[str, Any] | None) -> MingliWorkflow:
    """Load workflow genes from genome metadata with validation."""
    raw = dict((meta or {}).get("workflow", {}))
    defaults = MingliWorkflow()
    data = defaults.to_meta()
    data.update(raw)
    rounds = int(data["discussion_rounds"])
    data["discussion_rounds"] = min(3, max(1, rounds))
    data["vote_threshold"] = min(1.0, max(0.0, float(data["vote_threshold"])))
    if data["source_review_strictness"] not in {"standard", "strict"}:
        data["source_review_strictness"] = defaults.source_review_strictness
    return MingliWorkflow(**data)


def evolve_workflow(current: MingliWorkflow, strategy_name: str) -> MingliWorkflow:
    """Return a workflow variant aligned to a named evolution strategy."""
    if strategy_name == "debate_depth":
        return MingliWorkflow(
            discussion_rounds=2,
            cross_check_enabled=True,
            reconciliation_enabled=True,
            source_review_strictness=current.source_review_strictness,
            vote_threshold=current.vote_threshold,
            preserve_conflicts=True,
        )
    if strategy_name == "citation_precision":
        return MingliWorkflow(
            discussion_rounds=current.discussion_rounds,
            cross_check_enabled=current.cross_check_enabled,
            reconciliation_enabled=current.reconciliation_enabled,
            source_review_strictness="strict",
            vote_threshold=current.vote_threshold,
            preserve_conflicts=current.preserve_conflicts,
        )
    if strategy_name == "synthesis_calibration":
        return MingliWorkflow(
            discussion_rounds=max(2, current.discussion_rounds),
            cross_check_enabled=True,
            reconciliation_enabled=current.reconciliation_enabled,
            source_review_strictness=current.source_review_strictness,
            vote_threshold=0.8,
            preserve_conflicts=True,
        )
    if strategy_name == "combined_strategy":
        return MingliWorkflow(
            discussion_rounds=3,
            cross_check_enabled=True,
            reconciliation_enabled=True,
            source_review_strictness="strict",
            vote_threshold=0.8,
            preserve_conflicts=True,
        )
    return current
