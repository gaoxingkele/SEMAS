"""Deterministic mutator for the SEMAS self-upgrade benchmark.

This mutator removes the LLM dependency so that the benchmark can run in CI.
It produces known-good variants based on failure context keywords.
"""

from __future__ import annotations

from semas.genome.genome import AgentGenome, ToolGenome
from semas.mutator.mutator import Mutator


class BenchmarkMutator(Mutator):
    """A mutator that returns pre-defined correct variants for benchmark tasks."""

    def mutate_prompt(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """Improve the prompt for geography capital tasks."""
        new_prompt = agent.system_prompt
        if agent.name == "prompt_solver" and "capital" not in agent.system_prompt.lower():
            new_prompt = (
                "You are a helpful assistant. When asked for a country, "
                "respond with the capital city only."
            )
        return agent.evolve_from(system_prompt=new_prompt)

    def mutate_few_shot(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """No-op for the benchmark; keep the genome unchanged."""
        return agent

    def mutate_tool(
        self,
        agent: AgentGenome,
        failure_logs: list[str],
    ) -> ToolGenome:
        """Return a correct date-diff tool for the math benchmark agent."""
        if agent.name == "math_solver" or agent.meta.get("domain") == "date_arithmetic":
            return ToolGenome(
                name="calculate_date_diff",
                description="Calculate days between two ISO dates.",
                source_code="""from datetime import datetime

def calculate_date_diff(start: str, end: str) -> int:
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
""",
                signature="calculate_date_diff(start: str, end: str) -> int",
            )
        # Fallback: a generic numeric adder
        return ToolGenome(
            name="add",
            description="Add two numbers.",
            source_code="def add(a: float, b: float) -> float:\n    return a + b\n",
            signature="add(a: float, b: float) -> float",
        )

    def mutate_topology(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """Add a reviewer node to the topology."""
        from semas.genome.genome import TopologyGenome

        topology = TopologyGenome(
            name="review_pipeline",
            nodes=["writer", "reviewer"],
            edges=[["writer", "reviewer"]],
            execution_mode="serial",
        )
        return agent.evolve_from(topology=topology)
