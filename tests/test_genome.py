"""Tests for genome models and repository."""

import shutil
import tempfile
from pathlib import Path

import pytest

from semas.genome.genome import AgentGenome, FewShotExample, ToolGenome, TopologyGenome
from semas.genome.repository import GenomeRepository


@pytest.fixture
def repo():
    tmp = Path(tempfile.mkdtemp())
    yield GenomeRepository(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


def test_tool_genome_signature_extraction():
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    tool = ToolGenome(name="add", description="adds", source_code=code)
    assert tool.signature == "add(a: int, b: int) -> int"


def test_agent_evolve_from():
    agent = AgentGenome(
        name="test",
        role="tester",
        system_prompt="old prompt",
        version=1,
    )
    child = agent.evolve_from(system_prompt="new prompt")
    assert child.version == 2
    assert child.parent_version == 1
    assert child.system_prompt == "new prompt"


def test_repository_save_and_load_agent(repo):
    agent = AgentGenome(name="agent_a", role="r", system_prompt="sp")
    repo.save_agent(agent)
    loaded = repo.load_agent("agent_a")
    assert loaded.name == "agent_a"
    assert loaded.version == 1


def test_repository_latest_and_rollback(repo):
    v1 = AgentGenome(name="agent_a", role="r", system_prompt="v1")
    v2 = v1.evolve_from(system_prompt="v2")
    repo.save_agent(v1)
    repo.save_agent(v2)
    assert repo.latest_version("agents", "agent_a") == 2

    rolled = repo.rollback_agent("agent_a", 1)
    assert rolled.version == 3
    assert rolled.system_prompt == "v1"


def test_topology_predecessors_successors():
    topo = TopologyGenome(
        name="pipeline",
        nodes=["a", "b", "c"],
        edges=[("a", "b"), ("b", "c")],
    )
    assert topo.predecessors("b") == ["a"]
    assert topo.successors("b") == ["c"]
