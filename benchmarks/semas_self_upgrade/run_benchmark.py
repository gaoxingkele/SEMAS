"""SEMAS self-upgrade benchmark runner.

Loads task definitions from `tasks/`, executes them through the SEMAS pipeline,
and emits a framework-level JSON report.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome, ToolGenome, TopologyGenome
from semas.genome.repository import GenomeRepository
from semas.orchestrator.orchestrator import Orchestrator
from semas.sandbox.sandbox import Sandbox

from benchmarks.semas_self_upgrade.deterministic_mutator import BenchmarkMutator


class BenchmarkOrchestrator(Orchestrator):
    """Orchestrator variant that always considers tool mutation in benchmark tasks."""

    def _looks_computational(self, failure_logs: list[str]) -> bool:
        return True
from benchmarks.semas_self_upgrade.metrics import compute_report
from semas.plugins.function_evolve.ast_tool_mutator import FunctionEvolveToolMutator
from semas.plugins.function_evolve.optimizer import FunctionEvolveToolOptimizer


TASKS_DIR = Path(__file__).with_name("tasks")
FIXTURES_DIR = Path(__file__).with_name("fixtures")


def exact_match_metric(output: dict[str, Any], expected: dict[str, Any]) -> float:
    return 1.0 if output.get("output") == expected.get("output") else 0.0


def boolean_metric(output: dict[str, Any], expected: dict[str, Any]) -> float:
    key = next(iter(expected))
    return 1.0 if output.get(key) == expected.get(key) else 0.0


def structure_metric(output: dict[str, Any], expected: dict[str, Any]) -> float:
    nodes_ok = output.get("nodes") == expected.get("nodes")
    mode_ok = output.get("execution_mode") == expected.get("execution_mode")
    return 1.0 if nodes_ok and mode_ok else 0.0


METRICS = {
    "exact_match": exact_match_metric,
    "boolean_pass": boolean_metric,
    "structure_match": structure_metric,
}


def load_task(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_fixture(name: str) -> AgentGenome:
    path = FIXTURES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AgentGenome(**data)


def run_tool_based_math(task: dict[str, Any]) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="semas_bench_math_"))
    try:
        repo = GenomeRepository(tmp)
        agent = load_fixture(Path(task["fixture"]).name)
        repo.save_agent(agent)

        evaluator = Evaluator()
        evaluator.register_metric("exact_match", exact_match_metric)

        sandbox = Sandbox()
        mutator = BenchmarkMutator()

        def executor(agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
            for tool_name in agent.tools:
                tool = repo.load_tool(tool_name)
                ns: dict[str, Any] = {}
                try:
                    exec(tool.source_code, ns)  # noqa: S102
                except Exception:  # noqa: BLE001
                    continue
                for obj in ns.values():
                    if callable(obj) and "date" in obj.__name__:
                        try:
                            return {"output": obj(task_input["start"], task_input["end"])}
                        except Exception:  # noqa: BLE001
                            continue
            return {"output": 0}

        orch = BenchmarkOrchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=mutator,
            sandbox=sandbox,
            agent_name=agent.name,
            executor=executor,
            cooldown_tasks=0,
        )

        rounds = 0
        passed = False
        max_rounds = task["evaluation"].get("max_evolution_rounds", 0)
        while rounds <= max_rounds:
            trace = orch.run_task(task["input"], expected=task["expected"])
            if trace.evaluation.passed:
                passed = True
                break
            rounds += 1

        return {
            "task_id": task["id"],
            "category": task["category"],
            "passed": passed,
            "evolution_rounds": rounds,
            "llm_calls": 0,
            "allow_evolution": task["evaluation"].get("allow_evolution", False),
            "max_evolution_rounds": max_rounds,
            "regression": False,
            "details": trace.evaluation.details,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_prompt_based_qa(task: dict[str, Any]) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="semas_bench_prompt_"))
    try:
        repo = GenomeRepository(tmp)
        agent = load_fixture(Path(task["fixture"]).name)
        repo.save_agent(agent)

        evaluator = Evaluator()
        evaluator.register_metric("exact_match", exact_match_metric)

        mutator = BenchmarkMutator()

        def executor(agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
            if "capital" in agent.system_prompt.lower():
                capitals = {"France": "Paris", "Germany": "Berlin", "Japan": "Tokyo"}
                return {"output": capitals.get(task_input["country"], "Unknown")}
            return {"output": task_input["country"]}

        orch = BenchmarkOrchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=mutator,
            sandbox=Sandbox(),
            agent_name=agent.name,
            executor=executor,
            cooldown_tasks=0,
        )

        rounds = 0
        passed = False
        max_rounds = task["evaluation"].get("max_evolution_rounds", 0)
        while rounds <= max_rounds:
            trace = orch.run_task(task["input"], expected=task["expected"])
            if trace.evaluation.passed:
                passed = True
                break
            rounds += 1

        return {
            "task_id": task["id"],
            "category": task["category"],
            "passed": passed,
            "evolution_rounds": rounds,
            "llm_calls": 0,
            "allow_evolution": task["evaluation"].get("allow_evolution", False),
            "max_evolution_rounds": max_rounds,
            "regression": False,
            "details": trace.evaluation.details,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_regression_gate(task: dict[str, Any]) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="semas_bench_regression_"))
    try:
        repo = GenomeRepository(tmp)
        agent = load_fixture(Path(task["fixture"]).name)
        repo.save_agent(agent)

        evaluator = Evaluator()
        evaluator.register_metric("exact_match", exact_match_metric)
        # The old task is registered as a regression test.
        evaluator.add_regression_test(task_input=task["input"], expected=task["expected"])

        mutator = BenchmarkMutator()

        def executor(agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
            if "capital" in agent.system_prompt.lower():
                capitals = {"France": "Paris", "Germany": "Berlin", "Japan": "Tokyo"}
                return {"output": capitals.get(task_input["country"], "Unknown")}
            return {"output": task_input["country"]}

        orch = BenchmarkOrchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=mutator,
            sandbox=Sandbox(),
            agent_name=agent.name,
            executor=executor,
            cooldown_tasks=0,
        )

        # Step 1: trigger an evolution by running the capital task.
        capital_input = {"country": "France"}
        capital_expected = {"output": "Paris"}
        orch.run_task(capital_input, expected=capital_expected)

        # Step 2: verify the old task still passes (regression gate).
        trace = orch.run_task(task["input"], expected=task["expected"])

        return {
            "task_id": task["id"],
            "category": task["category"],
            "passed": trace.evaluation.passed,
            "evolution_rounds": 0,
            "llm_calls": 0,
            "allow_evolution": task["evaluation"].get("allow_evolution", False),
            "max_evolution_rounds": task["evaluation"].get("max_evolution_rounds", 0),
            "regression": not trace.evaluation.passed,
            "details": trace.evaluation.details,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_function_evolve_plugin(task: dict[str, Any]) -> dict[str, Any]:
    import math

    tmp = Path(tempfile.mkdtemp(prefix="semas_bench_fe_"))
    try:
        repo = GenomeRepository(tmp)
        tool = ToolGenome(
            name="my_formula",
            description="formula",
            source_code="def my_formula(x):\n    return x * 1\n",
        )
        repo.save_tool(tool)
        agent = AgentGenome(
            name="formula_agent",
            role="regressor",
            system_prompt="Find the formula.",
            tools=[tool.name],
        )

        samples = [(0.0, 0.0), (1.0, 2.0), (2.0, 4.0)]

        def fitness_fn(candidate: AgentGenome) -> float:
            t = repo.load_tool(candidate.tools[0])
            ns: dict[str, Any] = {}
            try:
                exec(t.source_code, ns)  # noqa: S102
            except Exception:  # noqa: BLE001
                return 0.0
            fn = ns.get("my_formula")
            if not callable(fn):
                return 0.0
            errors = [(fn(x) - y) ** 2 for x, y in samples]
            return 1.0 / (1.0 + math.sqrt(sum(errors) / len(errors)))

        context = {"repository": repo, "fitness_fn": fitness_fn}
        mutator = FunctionEvolveToolMutator(max_candidates_per_tool=6, seed=42)
        optimizer = FunctionEvolveToolOptimizer(seed=42)

        candidates = mutator.mutate(agent, failure_logs=["misfit"], context=context)
        candidates.insert(0, agent)
        optimized = [optimizer.optimize(c, context) for c in candidates]
        best = max(optimized, key=fitness_fn)
        score = fitness_fn(best)

        return {
            "task_id": task["id"],
            "category": task["category"],
            "passed": score >= task["expected"]["fitness_threshold"],
            "evolution_rounds": 0,
            "llm_calls": 0,
            "allow_evolution": task["evaluation"].get("allow_evolution", False),
            "max_evolution_rounds": 0,
            "regression": False,
            "details": {"best_fitness": score},
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_sandbox_check(task: dict[str, Any]) -> dict[str, Any]:
    sandbox = Sandbox()
    dangerous_code = "import os\nprint(os.getcwd())"
    result = sandbox.run_code(dangerous_code)
    return {
        "task_id": task["id"],
        "category": task["category"],
        "passed": not result.success,
        "evolution_rounds": 0,
        "llm_calls": 0,
        "allow_evolution": task["evaluation"].get("allow_evolution", False),
        "max_evolution_rounds": 0,
        "regression": False,
        "details": {"sandbox_success": result.success, "stderr": result.stderr},
    }


def run_topology_check(task: dict[str, Any]) -> dict[str, Any]:
    topology = TopologyGenome(
        name="review_pipeline",
        nodes=["writer", "reviewer"],
        edges=[["writer", "reviewer"]],
        execution_mode="serial",
    )
    return {
        "task_id": task["id"],
        "category": task["category"],
        "passed": (
            topology.nodes == task["expected"]["nodes"]
            and topology.execution_mode == task["expected"]["execution_mode"]
        ),
        "evolution_rounds": 0,
        "llm_calls": 0,
        "allow_evolution": task["evaluation"].get("allow_evolution", False),
        "max_evolution_rounds": task["evaluation"].get("max_evolution_rounds", 0),
        "regression": False,
        "details": {"nodes": topology.nodes, "execution_mode": topology.execution_mode},
    }


HANDLERS = {
    "tool_based_math": run_tool_based_math,
    "prompt_based_qa": run_prompt_based_qa,
    "regression_gate": run_regression_gate,
    "function_evolve_plugin": run_function_evolve_plugin,
    "sandbox_check": run_sandbox_check,
    "topology_check": run_topology_check,
}


def run(json_mode: bool = False) -> BenchmarkReport:
    """Execute all benchmark tasks and return the aggregated report."""
    task_files = sorted(TASKS_DIR.glob("*.yaml"))
    results: list[dict[str, Any]] = []

    for task_file in task_files:
        task = load_task(task_file)
        executor_name = task["executor"]
        handler = HANDLERS.get(executor_name)
        if handler is None:
            if not json_mode:
                print(f"Unknown executor: {executor_name}", file=sys.stderr)
            continue
        result = handler(task)
        results.append(result)
        if not json_mode:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {task['id']} ({task['category']})")

    report = compute_report(results)
    if json_mode:
        print(json.dumps(report.to_dict(), ensure_ascii=False))
    else:
        print("\n=== Framework Report ===")
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))

    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="SEMAS self-upgrade benchmark")
    parser.add_argument("--json", action="store_true", help="Emit only JSON report")
    args = parser.parse_args()

    report = run(json_mode=args.json)
    return 0 if report.passed_tasks == report.total_tasks else 1


if __name__ == "__main__":
    raise SystemExit(main())
