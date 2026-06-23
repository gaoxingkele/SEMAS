"""Genome data models for prompts, tools, topologies, and agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ToolGenome(BaseModel):
    """A versioned code tool that an agent can call."""

    name: str
    description: str
    source_code: str
    signature: str = ""
    dependencies: list[str] = Field(default_factory=list)
    version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, __context: Any) -> None:
        if not self.signature:
            # Naive signature extraction for Python functions
            for line in self.source_code.splitlines():
                stripped = line.strip()
                if stripped.startswith("def ") and stripped.endswith(":"):
                    self.signature = stripped[4:-1]
                    break


class TopologyGenome(BaseModel):
    """A directed acyclic graph describing agent collaboration."""

    name: str
    nodes: list[str] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)
    execution_mode: str = "serial"  # serial | parallel | hierarchical
    version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def predecessors(self, node: str) -> list[str]:
        return [src for src, dst in self.edges if dst == node]

    def successors(self, node: str) -> list[str]:
        return [dst for src, dst in self.edges if src == node]


class FewShotExample(BaseModel):
    """A single few-shot example."""

    input: str
    output: str
    reasoning: str = ""


class AgentGenome(BaseModel):
    """A versioned agent configuration — the 'DNA' of an executor."""

    name: str
    role: str
    system_prompt: str
    few_shot_examples: list[FewShotExample] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    topology: str | None = None
    version: int = 1
    parent_version: int | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    meta: dict[str, Any] = Field(default_factory=dict)

    def evolve_from(self, **changes: Any) -> "AgentGenome":
        """Create a new version of this genome with the supplied changes."""
        data = self.model_dump()
        data["parent_version"] = data.pop("version")
        data["version"] = data["parent_version"] + 1
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data.update(changes)
        return AgentGenome(**data)
