"""Tests for the ai_video_evolver scaffold."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from ai_video_evolver.bootstrap import initialize_video_repo, load_agent_from_yaml, load_tool_from_source
from ai_video_evolver.evaluator.metrics import video_quality_score
from ai_video_evolver.executor import create_video_executor
from ai_video_evolver.mutator import VideoEvolverMutator
from ai_video_evolver.run_video_evolution import run


@pytest.fixture
def repo():
    tmp = Path(tempfile.mkdtemp())
    yield initialize_video_repo(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_task_path():
    return Path(__file__).parent.parent / "ai_video_evolver" / "examples" / "sample_task.yaml"


def test_load_agent(repo):
    agent = repo.load_agent("scriptwriter")
    assert agent.name == "scriptwriter"


def test_load_tool(repo):
    tool = repo.load_tool("video_api_client")
    assert "generate_video_from_prompt" in tool.source_code


def test_executor_runs_pipeline(repo):
    from semas.genome.genome import AgentGenome

    pipeline_agent = AgentGenome(
        name="runner",
        role="runner",
        system_prompt="Run pipeline",
        topology="video_pipeline",
    )
    executor = create_video_executor(repo)
    output = executor(pipeline_agent, {"user_idea": "a cat in a garden", "captions": "test"})

    assert "final_prompt" in output
    assert "clip" in output
    assert output["clip"]["post_processed"] is True


def test_video_quality_score():
    output = {
        "final_prompt": "cinematic shot of a cat in a garden, 4k, smooth camera motion",
        "clip": {},
    }
    expected = {"user_idea": "a cat in a garden"}
    score = video_quality_score(output, expected)
    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_mutator_enables_prompt_enhancement(repo):
    from semas.genome.genome import AgentGenome

    agent = AgentGenome(
        name="video_pipeline_runner",
        role="runner",
        system_prompt="Run pipeline",
        topology="video_pipeline",
        meta={"prompt_engineering": {"use_enhancement": False}},
    )
    mutator = VideoEvolverMutator()
    evolved = mutator.mutate_prompt(agent, ["quality too low"])
    assert evolved.meta["prompt_engineering"]["use_enhancement"] is True


def test_run_video_evolution(sample_task_path):
    result = run(sample_task_path, max_rounds=3)
    assert result["final_score"] > 0.0
    assert result["final_prompt"]
