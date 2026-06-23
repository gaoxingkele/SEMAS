"""Meta-agent orchestrator: inner execution loop + outer evolution loop."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from semas.evaluator.evaluator import EvaluationResult, Evaluator
from semas.genome.genome import AgentGenome, TopologyGenome
from semas.genome.repository import GenomeRepository
from semas.mutator.mutator import Mutator
from semas.plugins.registry import PluginRegistry
from semas.sandbox.sandbox import Sandbox


logger = logging.getLogger(__name__)


ExecutorFn = Callable[[AgentGenome, dict[str, Any]], dict[str, Any]]


@dataclass
class ExecutionTrace:
    """Record of one task execution."""

    task_input: dict[str, Any]
    task_output: dict[str, Any]
    evaluation: EvaluationResult
    genome_version: int
    expected: dict[str, Any] | None = None
    timestamp: float = field(default_factory=time.time)


class Orchestrator:
    """Runs the dual-loop SEMAS system.

    Inner loop: execute task -> evaluate -> record.
    Outer loop: if evaluation fails -> mutate -> sandbox test -> select -> commit.
    """

    def __init__(
        self,
        repository: GenomeRepository,
        evaluator: Evaluator,
        mutator: Mutator,
        sandbox: Sandbox,
        agent_name: str,
        topology_name: str | None = None,
        executor: ExecutorFn | None = None,
        cooldown_tasks: int = 5,
        max_versions_without_improvement: int = 3,
        plugin_registry: PluginRegistry | None = None,
    ):
        self.repo = repository
        self.evaluator = evaluator
        self.mutator = mutator
        self.sandbox = sandbox
        self.agent_name = agent_name
        self.topology_name = topology_name
        self.executor = executor or self._default_executor
        self.cooldown_tasks = cooldown_tasks
        self.max_versions_without_improvement = max_versions_without_improvement
        self.plugins = plugin_registry or PluginRegistry()

        self.traces: list[ExecutionTrace] = []
        self.tasks_since_evolution = 0
        self.error_patterns: set[str] = set()
        self.last_failed_pattern: str | None = None

    def run_task(
        self,
        task_input: dict[str, Any],
        expected: dict[str, Any] | None = None,
        allow_evolution: bool = True,
    ) -> ExecutionTrace:
        """Execute one task and optionally trigger evolution."""
        agent = self.repo.load_agent(self.agent_name)
        output = self.executor(agent, task_input)
        # Merge input into output so metrics can access query/context.
        merged_output = {**task_input, **output}
        eval_result = self.evaluator.evaluate(merged_output, expected)
        trace = ExecutionTrace(
            task_input=task_input,
            task_output=output,
            evaluation=eval_result,
            genome_version=agent.version,
            expected=expected,
        )
        self.traces.append(trace)
        self.tasks_since_evolution += 1

        if not eval_result.passed and allow_evolution:
            pattern = self._extract_error_pattern(output, eval_result)
            self.last_failed_pattern = pattern
            if self._should_evolve(pattern):
                self.evolve(agent, pattern)
                self.tasks_since_evolution = 0

        return trace

    def evolve(self, agent: AgentGenome, failure_pattern: str) -> AgentGenome | None:
        """Run one evolution cycle: mutate, sandbox test, select, commit."""
        failure_logs = [failure_pattern]
        # Include recent failures for richer context
        for trace in reversed(self.traces[-10:]):
            if not trace.evaluation.passed:
                failure_logs.append(trace.evaluation.details or str(trace.task_output))

        candidates: list[AgentGenome] = []

        # Prompt mutation candidate
        prompt_mutant = self.mutator.mutate_prompt(agent, failure_logs)
        candidates.append(prompt_mutant)

        # Few-shot mutation candidate
        fs_mutant = self.mutator.mutate_few_shot(agent, failure_logs)
        if fs_mutant.version != agent.version:
            candidates.append(fs_mutant)

        # Tool mutation candidate if failures look computational
        if self._looks_computational(failure_logs):
            tool = self.mutator.mutate_tool(agent, failure_logs)
            # Validate tool in sandbox
            test_call = self._infer_test_call(tool.source_code)
            sandbox_result = self.sandbox.run_tool(tool.source_code, test_call)
            if sandbox_result.success:
                self.repo.save_tool(tool)
                tool_mutant = agent.evolve_from(tools=agent.tools + [tool.name])
                candidates.append(tool_mutant)

        # Plugin pipeline
        context = self._build_plugin_context(failure_logs)

        for strategy in self.plugins.mutator_strategies:
            try:
                plugin_candidates = strategy.mutate(agent, failure_logs, context)
                candidates.extend(plugin_candidates)
            except Exception as exc:  # noqa: BLE001
                logger.warning("MutatorStrategy %s failed: %s", strategy, exc)

        # Candidate optimizers
        optimized_candidates: list[AgentGenome] = []
        for candidate in candidates:
            current = candidate
            for optimizer in self.plugins.candidate_optimizers:
                try:
                    current = optimizer.optimize(current, context)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("CandidateOptimizer %s failed: %s", optimizer, exc)
            optimized_candidates.append(current)
        candidates = optimized_candidates

        # Score candidates on the last failing task
        best_candidate = self._select_candidate(candidates, agent)
        if best_candidate and best_candidate.version != agent.version:
            # Optional weight update (SIA-style) before committing
            best_candidate = self._apply_weight_updates(best_candidate)
            self.repo.save_agent(best_candidate)
            self.error_patterns.add(failure_pattern)
            return best_candidate

        return None

    def rollback_if_regressed(self) -> AgentGenome | None:
        """If the latest version performs worse than its parent, roll back."""
        latest = self.repo.load_agent(self.agent_name)
        if latest.parent_version is None:
            return None
        parent = self.repo.load_agent(self.agent_name, latest.parent_version)

        recent_traces = [t for t in self.traces if t.genome_version == latest.version]
        parent_traces = [t for t in self.traces if t.genome_version == parent.version]
        if not recent_traces or not parent_traces:
            return None

        latest_score = sum(t.evaluation.score for t in recent_traces) / len(recent_traces)
        parent_score = sum(t.evaluation.score for t in parent_traces) / len(parent_traces)

        if latest_score < parent_score:
            rolled = self.repo.rollback_agent(self.agent_name, parent.version)
            return rolled
        return None

    def _default_executor(self, agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
        """Placeholder executor.

        Real integrations should override this with an LLM call or tool-using agent.
        The stub simply echoes the input so the loop can be exercised in tests.
        """
        return {
            "output": task_input.get("query", ""),
            "agent": agent.name,
            "version": agent.version,
        }

    def _should_evolve(self, pattern: str) -> bool:
        """Evolution trigger with cooldown and new-error filtering."""
        if self.tasks_since_evolution < self.cooldown_tasks:
            return False
        # Only evolve on new patterns to control cost
        if pattern in self.error_patterns:
            return False
        return True

    def _extract_error_pattern(self, output: dict[str, Any], evaluation: EvaluationResult) -> str:
        """Create a stable error pattern key for deduplication."""
        err = output.get("error") or evaluation.details or "unknown_error"
        # Normalize to first few words
        return " ".join(str(err).split()[:8]).lower()

    def _looks_computational(self, failure_logs: list[str]) -> bool:
        """Heuristic: does the failure mention numbers, dates, calculations?"""
        keywords = {"calculate", "compute", "date", "number", "sum", "diff", "format", "parse"}
        text = " ".join(failure_logs).lower()
        return any(kw in text for kw in keywords)

    def _infer_test_call(self, source_code: str) -> str:
        """Infer a basic test call for a newly generated tool."""
        for line in source_code.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") and stripped.endswith(":"):
                sig = stripped[4:-1]
                name = sig.split("(")[0].strip()
                args = sig.split("(", 1)[1].rsplit(")", 1)[0]
                arg_values = []
                for arg in args.split(","):
                    arg = arg.strip().split(":")[0].split("=")[0].strip()
                    if not arg:
                        continue
                    if "date" in arg.lower():
                        arg_values.append("'2024-01-01'")
                    elif "start" in arg.lower():
                        arg_values.append("'2024-01-01'")
                    elif "end" in arg.lower():
                        arg_values.append("'2024-01-10'")
                    else:
                        arg_values.append("1")
                return f"{name}({', '.join(arg_values)})"
        return "pass"

    def _select_candidate(
        self,
        candidates: list[AgentGenome],
        baseline: AgentGenome,
    ) -> AgentGenome | None:
        """Evaluate candidates against the most recent failing task; return best."""
        if not candidates:
            return None
        if not self.traces:
            return candidates[0]

        last_input = self.traces[-1].task_input
        last_expected = self.traces[-1].expected
        best: AgentGenome | None = None
        best_score = -1.0

        for candidate in candidates:
            output = {**last_input, **self.executor(candidate, last_input)}
            result = self.evaluator.evaluate(output, last_expected)
            if result.score > best_score:
                best_score = result.score
                best = candidate

        # Only commit if candidate improves over baseline on the same input
        baseline_output = {**last_input, **self.executor(baseline, last_input)}
        baseline_result = self.evaluator.evaluate(baseline_output, last_expected)
        if best and best_score > baseline_result.score and self._passes_regression_gate(best):
            return best
        return None

    def _passes_regression_gate(self, candidate: AgentGenome) -> bool:
        """Run registered regression tests before committing an evolved genome."""
        if not self.evaluator.regression_tests:
            return True

        def executor_fn(input_data: dict) -> dict:
            return {**input_data, **self.executor(candidate, input_data)}

        all_passed, _results = self.evaluator.run_regression_suite(executor_fn)
        return all_passed

    def _build_plugin_context(self, failure_logs: list[str]) -> dict[str, Any]:
        """Assemble runtime context for plugin strategies and optimizers."""
        last_trace = self.traces[-1] if self.traces else None
        return {
            "repository": self.repo,
            "evaluator": self.evaluator,
            "sandbox": self.sandbox,
            "executor": self.executor,
            "agent_name": self.agent_name,
            "failure_logs": failure_logs,
            "last_task_input": last_trace.task_input if last_trace else {},
            "last_expected": last_trace.expected if last_trace else None,
        }

    def _apply_weight_updates(self, candidate: AgentGenome) -> AgentGenome:
        """Optionally update model weights before committing a candidate."""
        for strategy in self.plugins.weight_update_strategies:
            try:
                if strategy.should_update_weights(candidate, self.traces):
                    samples = self._build_training_samples()
                    artifact = strategy.update_weights(candidate, samples)
                    candidate = candidate.model_copy(
                        update={
                            "meta": {
                                **candidate.meta,
                                "weight_artifacts": artifact,
                            }
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("WeightUpdateStrategy %s failed: %s", strategy, exc)
        return candidate

    def _build_training_samples(self) -> list[dict[str, Any]]:
        """Collect recent task traces as training material for weight updates."""
        samples: list[dict[str, Any]] = []
        for trace in self.traces[-20:]:
            samples.append(
                {
                    "input": trace.task_input,
                    "output": trace.task_output,
                    "expected": trace.expected,
                    "passed": trace.evaluation.passed,
                    "score": trace.evaluation.score,
                }
            )
        return samples
