"""Tests for the FunctionEvolve-style SEMAS plugin."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from semas.genome.genome import AgentGenome, ToolGenome
from semas.genome.repository import GenomeRepository
from semas.plugins.function_evolve.ast_tool_mutator import FunctionEvolveToolMutator
from semas.plugins.function_evolve.optimizer import FunctionEvolveToolOptimizer


@pytest.fixture
def repo():
    tmp = Path(tempfile.mkdtemp())
    yield GenomeRepository(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def agent_with_formula(repo: GenomeRepository):
    tool = ToolGenome(
        name="my_formula",
        description="formula",
        source_code="def my_formula(x):\n    return x + 1\n",
    )
    repo.save_tool(tool)
    agent = AgentGenome(
        name="agent",
        role="tester",
        system_prompt="test",
        tools=[tool.name],
    )
    repo.save_agent(agent)
    return agent


def test_mutator_generates_candidates(repo: GenomeRepository, agent_with_formula: AgentGenome):
    mutator = FunctionEvolveToolMutator(max_candidates_per_tool=3, seed=42)
    candidates = mutator.mutate(
        agent_with_formula,
        failure_logs=["formula wrong"],
        context={"repository": repo},
    )
    assert len(candidates) > 0
    for candidate in candidates:
        assert candidate.tools != agent_with_formula.tools
        assert "function_evolve" in candidate.meta


def test_optimizer_improves_constant(repo: GenomeRepository, agent_with_formula: AgentGenome):
    def fitness_fn(candidate: AgentGenome) -> float:
        tool_name = candidate.tools[0]
        tool = repo.load_tool(tool_name)
        namespace: dict = {}
        try:
            exec(tool.source_code, namespace)  # noqa: S102
        except Exception:  # noqa: BLE001
            return 0.0
        func = namespace.get("my_formula")
        if not callable(func):
            return 0.0
        # Target: 2*x + 1
        errors = [(func(x) - y) ** 2 for x, y in [(0, 1), (1, 3), (2, 5)]]
        import math

        mse = sum(errors) / len(errors)
        return 1.0 / (1.0 + math.sqrt(mse))

    optimizer = FunctionEvolveToolOptimizer(seed=42)
    optimized = optimizer.optimize(
        agent_with_formula,
        context={"repository": repo, "fitness_fn": fitness_fn},
    )

    assert optimized.tools != agent_with_formula.tools
    score_before = fitness_fn(agent_with_formula)
    score_after = fitness_fn(optimized)
    assert score_after >= score_before
