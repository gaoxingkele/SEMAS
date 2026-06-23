"""Plugin interfaces for extending SEMAS evolution.

All interfaces are defined as Protocols so that third-party packages can
implement them without inheriting from SEMAS classes.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from semas.genome.genome import AgentGenome


@runtime_checkable
class MutatorStrategy(Protocol):
    """Generate candidate genome variations based on failure context.

    This is the primary extension point for alternative mutation algorithms
    (e.g. FunctionEvolve's AST tree edits, Gödel Agent's self-modification).
    """

    def mutate(
        self,
        agent: AgentGenome,
        failure_logs: list[str],
        context: dict[str, Any],
    ) -> list[AgentGenome]:
        """Return a list of candidate genomes.

        Args:
            agent: The current agent genome that produced the failure.
            failure_logs: Normalized failure descriptions.
            context: Optional runtime context. Implementations may expect keys
                such as ``repository`` (GenomeRepository), ``evaluator``,
                ``sandbox``, or ``last_task_input``.

        Returns:
            A list of candidate genomes. The caller (Orchestrator) is
            responsible for evaluating and selecting among them.
        """
        ...


@runtime_checkable
class CandidateOptimizer(Protocol):
    """Refine a candidate genome before it enters the selection step.

    Examples: structure-aware coefficient fitting (FunctionEvolve), prompt
    compression, or hyper-parameter search over tool variants.
    """

    def optimize(
        self,
        candidate: AgentGenome,
        context: dict[str, Any],
    ) -> AgentGenome:
        """Return a refined candidate.

        Args:
            candidate: A candidate genome produced by a Mutator or another
                MutatorStrategy.
            context: Runtime context, which may include ``last_task_input``,
                ``expected``, ``executor``, ``evaluator``, ``repository``.

        Returns:
            The optimized candidate. If no improvement is found, the original
            candidate should be returned.
        """
        ...


@runtime_checkable
class WeightUpdateStrategy(Protocol):
    """Update model weights of an agent, complementing harness updates.

    This interface is inspired by SIA (Self Improving AI with Harness &
    Weight Updates), which argues that scaffold-only evolution leaves domain
    intuition on the table.
    """

    def should_update_weights(
        self,
        agent: AgentGenome,
        traces: list[Any],
    ) -> bool:
        """Return True if the agent's weights should be updated now."""
        ...

    def update_weights(
        self,
        agent: AgentGenome,
        training_samples: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Perform test-time training and return weight artifact metadata.

        Returns:
            A dictionary describing the new weights, e.g.
            ``{"adapter_path": "...", "base_model": "...", "hash": "..."}``.
            This dictionary is typically stored in ``agent.meta["weight_artifacts"]``.
        """
        ...


@runtime_checkable
class SelfModificationPolicy(Protocol):
    """Gatekeeper for Gödel-Agent-style self-modification of source code.

    Implementations decide whether a proposed source-code change is allowed
    and whether to roll back on failure.
    """

    def is_allowed(
        self,
        current_source: str,
        proposed_source: str,
        context: dict[str, Any],
    ) -> bool:
        """Return True if the proposed modification may be applied."""
        ...

    def rollback_on_failure(self) -> bool:
        """Return True if a failed self-modification should trigger rollback."""
        ...
