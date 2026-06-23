"""Demo: SEMAS self-evolving math agent.

This example simulates an agent that initially fails at date-difference
calculations, triggers tool evolution, and then succeeds.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository
from semas.mutator.mutator import Mutator
from semas.orchestrator.orchestrator import Orchestrator
from semas.sandbox.sandbox import Sandbox


def demo_executor(agent: AgentGenome, task_input: dict) -> dict:
    """A toy executor that simulates LLM behavior.

    It only knows how to answer correctly if the agent has any tool available.
    Otherwise it returns a wrong answer to trigger evolution.
    """
    query: str = task_input.get("query", "")
    if "days between" in query.lower():
        if agent.tools:
            # Simulate successfully using the available tool
            return {
                "output": "7",
                "tool_used": agent.tools[0],
                "agent": agent.name,
                "version": agent.version,
            }
        else:
            # Wrong answer to trigger evolution
            return {
                "output": "6",
                "error": "Date difference off by one",
                "agent": agent.name,
                "version": agent.version,
            }
    return {"output": "unknown", "agent": agent.name, "version": agent.version}


def parse_date_diff_query(query: str) -> tuple[str, str] | None:
    """Extract two ISO dates from a query like 'How many days between A and B?'."""
    import re

    matches = re.findall(r"\d{4}-\d{2}-\d{2}", query)
    if len(matches) == 2:
        return matches[0], matches[1]
    return None


def date_diff_metric(task_result: dict, expected: dict | None) -> float:
    """Score a date-difference answer by comparing to actual day difference."""
    query = task_result.get("query", "")
    dates = parse_date_diff_query(query)
    if not dates:
        return 0.0
    start, end = dates
    actual = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    try:
        predicted = int(task_result.get("output", "0"))
    except ValueError:
        return 0.0
    return 1.0 if predicted == actual else 0.0


def main() -> None:
    # Use a temporary genome repository for the demo
    tmp_dir = Path(tempfile.mkdtemp(prefix="semas_demo_"))
    try:
        repo = GenomeRepository(tmp_dir)

        # Load initial genome from YAML and save it as v1
        yaml_path = Path(__file__).parent / "genome_v1.yaml"
        agent = repo.load_genome_from_yaml(yaml_path)
        repo.save_agent(agent)

        # Evaluator: exact date-diff correctness
        evaluator = Evaluator(threshold=1.0)
        evaluator.register_metric("date_diff_correctness", date_diff_metric)

        # Mutator and sandbox
        mutator = Mutator()
        sandbox = Sandbox(timeout=5, allowed_modules={"math", "datetime", "json", "re"})

        # Orchestrator with a short cooldown so the demo triggers evolution quickly
        orchestrator = Orchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=mutator,
            sandbox=sandbox,
            agent_name="math_solver",
            executor=demo_executor,
            cooldown_tasks=1,
        )

        task = {"query": "How many days between 2024-01-01 and 2024-01-08?"}
        expected = {"output": "7"}

        print("=" * 60)
        print("SEMAS Math Agent Evolution Demo")
        print("=" * 60)

        # First attempt: expected to fail
        print("\n[Attempt 1] Current genome v1")
        trace1 = orchestrator.run_task(task, expected)
        print(f"  Output: {trace1.task_output['output']}")
        print(f"  Passed: {trace1.evaluation.passed}")
        print(f"  Score:  {trace1.evaluation.score:.2f}")

        # Show evolution result
        latest = repo.load_agent("math_solver")
        print(f"\n[Evolution] Latest genome version: v{latest.version}")
        print(f"  Tools: {latest.tools}")
        print(f"  System prompt preview: {latest.system_prompt[:80]}...")

        # Second attempt: should succeed after tool evolution
        print("\n[Attempt 2] Using evolved genome")
        trace2 = orchestrator.run_task(task, expected)
        print(f"  Output: {trace2.task_output['output']}")
        print(f"  Passed: {trace2.evaluation.passed}")
        print(f"  Score:  {trace2.evaluation.score:.2f}")

        # Show generated tool
        if latest.tools:
            tool_name = latest.tools[-1]
            tool = repo.load_tool(tool_name)
            print(f"\n[Generated Tool] {tool_name}")
            print(tool.source_code)

        print("\n" + "=" * 60)
        print("Demo complete. Genome repository:", tmp_dir)
        print("=" * 60)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
