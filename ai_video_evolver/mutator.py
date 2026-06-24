"""Deterministic mutators for the AI Video Evolver demo/CI.

These mutators produce known-good variations so the scaffold can run without
LLM API keys. In production, replace them with the standard SEMAS `Mutator`
or a fine-tuned meta-mutator.
"""

from __future__ import annotations

import copy

from semas.genome.genome import AgentGenome, ToolGenome
from semas.mutator.mutator import Mutator


class VideoEvolverMutator(Mutator):
    """Mutator tailored for the AI video generation pipeline."""

    def mutate_prompt(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """Enable prompt enhancement in the pipeline meta."""
        if agent.name == "video_pipeline_runner":
            meta = copy.deepcopy(dict(agent.meta))
            meta.setdefault("prompt_engineering", {})
            meta["prompt_engineering"]["use_enhancement"] = True
            return agent.evolve_from(meta=meta)
        return agent

    def mutate_tool(
        self,
        agent: AgentGenome,
        failure_logs: list[str],
    ) -> ToolGenome:
        """Enhance the prompt_templates tool to add more cinematic keywords."""
        return ToolGenome(
            name="prompt_templates",
            description="Enhanced prompt templates with more cinematic keywords.",
            source_code='''def enhance_prompt(scene_description: str, style: str = "cinematic") -> str:
    return (
        f"{style} shot of {scene_description}, 4k, smooth camera motion, "
        "dramatic lighting, shallow depth of field"
    )
''',
            signature="enhance_prompt(scene_description: str, style: str = \"cinematic\") -> str",
        )

    def mutate_few_shot(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """No-op for the video scaffold."""
        return agent

    def mutate_topology(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """No-op for the video scaffold."""
        return agent
