"""Bootstrap a SEMAS repository with AI Video Evolver agents, tools, and topology."""

from __future__ import annotations

from pathlib import Path

import yaml

from semas.genome.genome import AgentGenome, ToolGenome, TopologyGenome
from semas.genome.repository import GenomeRepository


PACKAGE_DIR = Path(__file__).parent


def load_agent_from_yaml(name: str) -> AgentGenome:
    path = PACKAGE_DIR / "agents" / f"{name}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AgentGenome(**data)


def load_tool_from_source(name: str) -> ToolGenome:
    source_path = PACKAGE_DIR / "tools" / f"{name}.py"
    source = source_path.read_text(encoding="utf-8")
    return ToolGenome(
        name=name,
        description=f"Tool source for {name}",
        source_code=source,
    )


def load_topology_from_yaml(name: str) -> TopologyGenome:
    path = PACKAGE_DIR / "topologies" / f"{name}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return TopologyGenome(**data)


def initialize_video_repo(repo_path: Path) -> GenomeRepository:
    """Create a SEMAS repo populated with the AI Video Evolver artifacts."""
    repo = GenomeRepository(repo_path)

    # Save tools
    tool_names = [
        "video_api_client",
        "ffmpeg_pipeline",
        "prompt_templates",
        "critic_functions",
    ]
    for tool_name in tool_names:
        repo.save_tool(load_tool_from_source(tool_name))

    # Save agents
    agent_names = [
        "scriptwriter",
        "prompt_engineer",
        "asset_generator",
        "editor",
        "critic",
    ]
    for agent_name in agent_names:
        repo.save_agent(load_agent_from_yaml(agent_name))

    # Save topology
    repo.save_topology(load_topology_from_yaml("video_pipeline"))

    return repo
