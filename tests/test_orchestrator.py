"""Tests for the orchestrator evolution loop."""

import shutil
import tempfile
from pathlib import Path

import pytest

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository
from semas.mutator.mutator import Mutator
from semas.orchestrator.orchestrator import Orchestrator
from semas.sandbox.sandbox import Sandbox


@pytest.fixture
def fresh_repo():
    tmp = Path(tempfile.mkdtemp())
    repo = GenomeRepository(tmp)
    agent = AgentGenome(name="test_agent", role="tester", system_prompt="be correct")
    repo.save_agent(agent)
    yield repo
    shutil.rmtree(tmp, ignore_errors=True)


def test_task_passes_without_evolution(fresh_repo):
    evaluator = Evaluator(threshold=0.5)
    evaluator.register_metric("always_one", lambda r, e: 1.0)

    def executor(agent, task_input):
        return {"output": "ok"}

    orch = Orchestrator(
        repository=fresh_repo,
        evaluator=evaluator,
        mutator=Mutator(),
        sandbox=Sandbox(),
        agent_name="test_agent",
        executor=executor,
        cooldown_tasks=1,
    )
    trace = orch.run_task({"query": "hello"})
    assert trace.evaluation.passed
    assert trace.genome_version == 1


def test_cooldown_prevents_evolution(fresh_repo):
    evaluator = Evaluator(threshold=1.0)
    evaluator.register_metric("fail", lambda r, e: 0.0)

    def executor(agent, task_input):
        return {"output": "bad"}

    orch = Orchestrator(
        repository=fresh_repo,
        evaluator=evaluator,
        mutator=Mutator(),
        sandbox=Sandbox(),
        agent_name="test_agent",
        executor=executor,
        cooldown_tasks=5,
    )
    trace = orch.run_task({"query": "hello"})
    assert not trace.evaluation.passed
    latest = fresh_repo.load_agent("test_agent")
    assert latest.version == 1  # evolution not triggered due to cooldown
