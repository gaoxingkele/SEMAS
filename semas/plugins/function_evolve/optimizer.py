"""Structure-aware constant optimizer inspired by FunctionEvolve.

For a tool whose return expression contains numeric constants, this optimizer
tries small perturbations of each constant and keeps the variant that scores
best against the most recent task (or a user-supplied fitness function).
"""

from __future__ import annotations

import ast
import copy
import random
from typing import Any

from semas.evaluator.evaluator import EvaluationResult
from semas.genome.genome import AgentGenome, ToolGenome
from semas.genome.repository import GenomeRepository
from semas.plugins.base import CandidateOptimizer


class _ConstantCollector(ast.NodeVisitor):
    """Collect numeric Constant nodes in an expression."""

    def __init__(self) -> None:
        self.constants: list[ast.Constant] = []

    def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802
        if isinstance(node.value, (int, float)):
            self.constants.append(node)
        self.generic_visit(node)


class FunctionEvolveToolOptimizer(CandidateOptimizer):
    """Optimize numeric constants inside an evolved tool.

    When running inside the Orchestrator, the optimizer uses the last task's
    input/expected output and the executor to score variants. When used
    standalone, a fitness function can be passed via ``context["fitness_fn"]``.
    """

    def __init__(
        self,
        perturbations: tuple[float, ...] = (0.9, 1.1, 0.5, 2.0, -0.5),
        seed: int | None = None,
    ) -> None:
        self.perturbations = perturbations
        if seed is not None:
            random.seed(seed)

    def optimize(
        self,
        candidate: AgentGenome,
        context: dict[str, Any],
    ) -> AgentGenome:
        repo = context.get("repository")
        if not isinstance(repo, GenomeRepository):
            return candidate

        fitness_fn = context.get("fitness_fn")
        executor = context.get("executor")
        evaluator = context.get("evaluator")
        task_input = context.get("last_task_input")
        expected = context.get("last_expected")

        if fitness_fn is None and (executor is None or evaluator is None):
            return candidate

        best_candidate = candidate
        best_score = self._score_candidate(
            candidate,
            fitness_fn=fitness_fn,
            executor=executor,
            evaluator=evaluator,
            task_input=task_input,
            expected=expected,
        )

        for tool_name in candidate.tools:
            try:
                tool = repo.load_tool(tool_name)
            except FileNotFoundError:
                continue

            if not self._has_numeric_constants(tool.source_code):
                continue

            for perturb in self.perturbations:
                new_source = self._perturb_constants(tool.source_code, perturb)
                if new_source == tool.source_code:
                    continue

                new_tool = ToolGenome(
                    name=f"{tool.name}_opt_{perturb}",
                    description=tool.description,
                    source_code=new_source,
                    signature=tool.signature,
                    dependencies=tool.dependencies,
                )
                repo.save_tool(new_tool)

                new_tools = list(candidate.tools)
                new_tools[new_tools.index(tool_name)] = new_tool.name
                trial = candidate.evolve_from(
                    tools=new_tools,
                    meta={
                        **candidate.meta,
                        "function_evolve_optimization": {
                            "parent_tool": tool.name,
                            "optimized_tool": new_tool.name,
                            "perturbation": perturb,
                        },
                    },
                )

                score = self._score_candidate(
                    trial,
                    fitness_fn=fitness_fn,
                    executor=executor,
                    evaluator=evaluator,
                    task_input=task_input,
                    expected=expected,
                )
                if score is not None and (best_score is None or score > best_score):
                    best_score = score
                    best_candidate = trial

        return best_candidate

    @staticmethod
    def _score_candidate(
        candidate: AgentGenome,
        fitness_fn: Any,
        executor: Any,
        evaluator: Any,
        task_input: Any,
        expected: Any,
    ) -> float | None:
        if fitness_fn is not None:
            try:
                return float(fitness_fn(candidate))
            except Exception:  # noqa: BLE001
                return None

        if executor is None or evaluator is None or task_input is None:
            return None

        try:
            output = {**task_input, **executor(candidate, task_input)}
            result: EvaluationResult = evaluator.evaluate(output, expected)
            return float(result.score)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _has_numeric_constants(source_code: str) -> bool:
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return False
        collector = _ConstantCollector()
        collector.visit(tree)
        return bool(collector.constants)

    @staticmethod
    def _perturb_constants(source_code: str, factor: float) -> str:
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return source_code

        new_tree = copy.deepcopy(tree)
        collector = _ConstantCollector()
        collector.visit(new_tree)

        for node in collector.constants:
            if isinstance(node.value, (int, float)):
                if factor < 0:
                    node.value = node.value + factor
                else:
                    node.value = node.value * factor

        return ast.unparse(new_tree)
