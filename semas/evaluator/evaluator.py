"""Evaluation harness with pluggable metrics and regression tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class EvaluationResult:
    """Outcome of evaluating a single task execution."""

    score: float  # 0.0 .. 1.0
    passed: bool
    metrics: dict[str, float] = field(default_factory=dict)
    details: str = ""

    def __post_init__(self):
        self.score = max(0.0, min(1.0, float(self.score)))


MetricFn = Callable[[dict, dict | None], float]
PASS_EPSILON = 1e-9


class Evaluator:
    """Scores task outcomes and runs regression suites.

    Example reward function:
        score = completion - 0.1 * token_cost - 0.2 * latency_seconds
    """

    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.metrics: dict[str, MetricFn] = {}
        self.regression_tests: list[dict] = []

    def register_metric(self, name: str, fn: MetricFn) -> None:
        """Register a metric function: fn(task_result, expected) -> float in [0, 1]."""
        self.metrics[name] = fn

    def add_regression_test(self, name: str, input_data: dict, expected: dict) -> None:
        self.regression_tests.append(
            {"name": name, "input": input_data, "expected": expected}
        )

    def evaluate(
        self,
        task_result: dict,
        expected: dict | None = None,
        weights: dict[str, float] | None = None,
    ) -> EvaluationResult:
        """Evaluate a single result.

        Args:
            task_result: dict with at least keys like 'output', 'token_cost', 'latency'.
            expected: optional ground truth.
            weights: metric name -> weight. If None, uses equal weighting.
        """
        if not self.metrics:
            # Default: exact output match if expected provided, else 1.0
            if expected is not None and "output" in expected:
                score = 1.0 if task_result.get("output") == expected["output"] else 0.0
            else:
                score = 1.0
            return EvaluationResult(score=score, passed=score + PASS_EPSILON >= self.threshold)

        scores: dict[str, float] = {}
        for name, fn in self.metrics.items():
            try:
                scores[name] = max(0.0, min(1.0, fn(task_result, expected)))
            except Exception as exc:  # noqa: BLE001
                scores[name] = 0.0
                details = f"Metric '{name}' failed: {exc}"
                return EvaluationResult(score=0.0, passed=False, metrics=scores, details=details)

        weights = weights or {name: 1.0 / len(scores) for name in scores}
        total_weight = sum(weights.get(name, 0.0) for name in scores)
        if total_weight == 0:
            total_weight = 1.0
        final_score = sum(scores[name] * weights.get(name, 0.0) for name in scores) / total_weight

        return EvaluationResult(
            score=final_score,
            passed=final_score + PASS_EPSILON >= self.threshold,
            metrics=scores,
            details=f"Scores: {scores}",
        )

    def run_regression_suite(
        self, executor_fn: Callable[[dict], dict]
    ) -> tuple[bool, list[EvaluationResult]]:
        """Run all regression tests against an executor function.

        Returns (all_passed, results).
        """
        results: list[EvaluationResult] = []
        for test in self.regression_tests:
            result = executor_fn(test["input"])
            eval_result = self.evaluate(result, test["expected"])
            results.append(eval_result)
        return all(r.passed for r in results), results
