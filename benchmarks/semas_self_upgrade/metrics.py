"""Framework-level metric calculators for the SEMAS self-upgrade benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkReport:
    """Aggregated report across all benchmark tasks."""

    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    mean_evolution_rounds: float
    total_llm_calls: int
    regression_count: int
    safety_violation_count: int
    convergence_rate: float
    task_results: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "pass_rate": self.passed_tasks / self.total_tasks if self.total_tasks else 0.0,
            "mean_evolution_rounds": self.mean_evolution_rounds,
            "total_llm_calls": self.total_llm_calls,
            "regression_count": self.regression_count,
            "safety_violation_count": self.safety_violation_count,
            "convergence_rate": self.convergence_rate,
            "task_results": self.task_results,
        }


def compute_report(task_results: list[dict[str, Any]]) -> BenchmarkReport:
    """Aggregate per-task results into a framework-level report."""
    total = len(task_results)
    passed = sum(1 for r in task_results if r.get("passed", False))
    rounds = [r.get("evolution_rounds", 0) for r in task_results if r.get("allow_evolution", False)]
    mean_rounds = sum(rounds) / len(rounds) if rounds else 0.0
    llm_calls = sum(r.get("llm_calls", 0) for r in task_results)
    regressions = sum(1 for r in task_results if r.get("regression", False))
    safety_violations = sum(
        1 for r in task_results if r.get("category") == "safety" and not r.get("passed", False)
    )
    converged = sum(
        1
        for r in task_results
        if r.get("allow_evolution", False) and r.get("evolution_rounds", 0) < r.get("max_evolution_rounds", 999)
    )
    convergence_rate = converged / len(rounds) if rounds else 1.0

    return BenchmarkReport(
        total_tasks=total,
        passed_tasks=passed,
        failed_tasks=total - passed,
        mean_evolution_rounds=mean_rounds,
        total_llm_calls=llm_calls,
        regression_count=regressions,
        safety_violation_count=safety_violations,
        convergence_rate=convergence_rate,
        task_results=task_results,
    )
