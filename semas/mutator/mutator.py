"""LLM-driven mutation of prompts, tools, and topologies."""

from __future__ import annotations

from semas.genome.genome import AgentGenome, FewShotExample, ToolGenome, TopologyGenome
from semas.utils.llm_client import LLMClient, default_llm_client


class Mutator:
    """Proposes variations of agent genomes based on failure context."""

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or default_llm_client()

    def mutate_prompt(
        self,
        genome: AgentGenome,
        failure_logs: list[str],
        instruction: str | None = None,
    ) -> AgentGenome:
        """Generate a prompt mutation for the given agent genome."""
        system = (
            "You are an expert prompt engineer. Rewrite the system prompt to fix the failures "
            "described in the logs. Keep the original role and constraints. Output only the new "
            "system prompt, no extra commentary."
        )
        user = (
            f"Agent role: {genome.role}\n\n"
            f"Current system prompt:\n{genome.system_prompt}\n\n"
            f"Failure logs:\n" + "\n".join(f"- {log}" for log in failure_logs) + "\n\n"
        )
        if instruction:
            user += f"Additional instruction: {instruction}\n\n"
        user += "Improved system prompt:"

        new_prompt = self.llm.complete(system, user, temperature=0.7).strip()
        return genome.evolve_from(system_prompt=new_prompt)

    def mutate_tool(
        self,
        agent: AgentGenome,
        failure_logs: list[str],
        tool_name: str | None = None,
    ) -> ToolGenome:
        """Generate a new Python tool based on repeated failures."""
        system = (
            "You are a senior Python engineer. Write a single, self-contained Python function "
            "that solves the recurring problem described in the failure logs. Include docstring, "
            "type hints, and minimal dependencies. Do not write example usage or imports beyond "
            "the standard library unless necessary."
        )
        user = (
            f"Agent role: {agent.role}\n\n"
            f"Agent system prompt:\n{agent.system_prompt}\n\n"
            f"Failure logs:\n" + "\n".join(f"- {log}" for log in failure_logs) + "\n\n"
            "Write the Python function:"
        )
        source_code = self.llm.complete(system, user, temperature=0.3).strip()
        # Strip markdown fences if present
        if source_code.startswith("```"):
            lines = source_code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            source_code = "\n".join(lines).strip()

        name = tool_name or "auto_generated_tool"
        # Extract first line of docstring as description
        description = f"Auto-generated tool for {agent.role}"
        for line in source_code.splitlines():
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                description = stripped.strip('"\'').strip()
                break

        return ToolGenome(
            name=name,
            description=description,
            source_code=source_code,
        )

    def mutate_topology(
        self,
        topology: TopologyGenome,
        failure_logs: list[str],
    ) -> TopologyGenome:
        """Propose a topology variation (placeholder; real implementation needs richer context)."""
        # For the template, we simply add a 'reviewer' node before terminal nodes if failures exist.
        new_nodes = list(topology.nodes)
        new_edges = list(topology.edges)
        if "reviewer" not in new_nodes:
            new_nodes.append("reviewer")
            # Find terminal nodes (no successors)
            terminals = [n for n in new_nodes if not topology.successors(n) and n != "reviewer"]
            for terminal in terminals:
                new_edges.append(("reviewer", terminal))
        return TopologyGenome(
            name=topology.name,
            nodes=new_nodes,
            edges=new_edges,
            execution_mode=topology.execution_mode,
            version=topology.version + 1,
        )

    def mutate_few_shot(
        self,
        genome: AgentGenome,
        failure_logs: list[str],
    ) -> AgentGenome:
        """Add a synthetic few-shot example derived from failure logs."""
        system = (
            "You are a helpful assistant. Given a failure log, produce one corrected example "
            "in the format:\nInput: <input>\nOutput: <output>\nReasoning: <reasoning>"
        )
        if not failure_logs:
            return genome
        user = f"Failure log:\n{failure_logs[-1]}\n\nCorrected example:"
        text = self.llm.complete(system, user, temperature=0.5)
        example = self._parse_example(text)
        if example:
            new_examples = list(genome.few_shot_examples) + [example]
            return genome.evolve_from(few_shot_examples=new_examples)
        return genome

    @staticmethod
    def _parse_example(text: str) -> FewShotExample | None:
        data = {"input": "", "output": "", "reasoning": ""}
        current_key: str | None = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("input:"):
                current_key = "input"
                data[current_key] = stripped.split(":", 1)[1].strip()
            elif stripped.lower().startswith("output:"):
                current_key = "output"
                data[current_key] = stripped.split(":", 1)[1].strip()
            elif stripped.lower().startswith("reasoning:"):
                current_key = "reasoning"
                data[current_key] = stripped.split(":", 1)[1].strip()
            elif current_key:
                data[current_key] += "\n" + stripped
        if data["input"] and data["output"]:
            return FewShotExample(**data)
        return None
