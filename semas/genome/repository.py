"""File-system backed genome repository with versioning and rollback."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from semas.genome.genome import AgentGenome, ToolGenome, TopologyGenome


class GenomeRepository:
    """Stores genomes on disk with Git-like versioning.

    Layout:
        <base_path>/
          agents/
            <agent_name>/
              v1.json
              v2.json
              ...
          tools/
            <tool_name>/
              v1.json
              ...
          topologies/
            <topology_name>/
              v1.json
              ...
    """

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for sub in ("agents", "tools", "topologies"):
            (self.base_path / sub).mkdir(parents=True, exist_ok=True)

    def _path(self, kind: str, name: str, version: int) -> Path:
        return self.base_path / kind / name / f"v{version}.json"

    def save_agent(self, genome: AgentGenome) -> Path:
        path = self._path("agents", genome.name, genome.version)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(genome.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_agent(self, name: str, version: int | None = None) -> AgentGenome:
        if version is None:
            version = self.latest_version("agents", name)
        path = self._path("agents", name, version)
        data = json.loads(path.read_text(encoding="utf-8"))
        return AgentGenome(**data)

    def save_tool(self, genome: ToolGenome) -> Path:
        path = self._path("tools", genome.name, genome.version)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(genome.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_tool(self, name: str, version: int | None = None) -> ToolGenome:
        if version is None:
            version = self.latest_version("tools", name)
        path = self._path("tools", name, version)
        data = json.loads(path.read_text(encoding="utf-8"))
        return ToolGenome(**data)

    def save_topology(self, genome: TopologyGenome) -> Path:
        path = self._path("topologies", genome.name, genome.version)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(genome.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_topology(self, name: str, version: int | None = None) -> TopologyGenome:
        if version is None:
            version = self.latest_version("topologies", name)
        path = self._path("topologies", name, version)
        data = json.loads(path.read_text(encoding="utf-8"))
        return TopologyGenome(**data)

    def latest_version(self, kind: str, name: str) -> int:
        dir_path = self.base_path / kind / name
        if not dir_path.exists():
            raise FileNotFoundError(f"No {kind} genome named '{name}'")
        versions = [
            int(p.stem[1:])
            for p in dir_path.glob("v*.json")
            if p.stem[1:].isdigit()
        ]
        if not versions:
            raise FileNotFoundError(f"No versions found for {kind}/{name}")
        return max(versions)

    def list_versions(self, kind: str, name: str) -> list[int]:
        dir_path = self.base_path / kind / name
        if not dir_path.exists():
            return []
        return sorted(
            int(p.stem[1:])
            for p in dir_path.glob("v*.json")
            if p.stem[1:].isdigit()
        )

    def rollback_agent(self, name: str, to_version: int) -> AgentGenome:
        """Roll back to a previous version by copying it to a new latest version."""
        target = self.load_agent(name, to_version)
        latest = self.latest_version("agents", name)
        new_genome = target.evolve_from(
            version=latest + 1,
            parent_version=latest,
            meta={**target.meta, "rolled_back_from": latest},
        )
        self.save_agent(new_genome)
        return new_genome

    def load_genome_from_yaml(self, path: str | Path) -> AgentGenome:
        """Helper to bootstrap an AgentGenome from a YAML file."""
        path = Path(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return AgentGenome(**data)
