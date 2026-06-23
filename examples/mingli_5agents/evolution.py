"""Population-based evolution for the mingli five-agent SEMAS example."""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository
from examples.mingli_5agents.memory import MingliFeedbackMemory
from examples.mingli_5agents.workflow import evolve_workflow, workflow_from_meta


MINGLI_STRATEGIES = [
    {
        "name": "feedback_adaptation",
        "prompt": (
            "When user feedback flags vagueness, add sharper structure, explicit uncertainty, "
            "and a short response to the correction while preserving non-high-stakes boundaries."
        ),
    },
    {
        "name": "citation_precision",
        "prompt": (
            "Require every symbolic conclusion to list which tradition or source label supports it, "
            "and separate source-backed symbolism from uncertain synthesis."
        ),
    },
    {
        "name": "debate_depth",
        "prompt": (
            "Run at least two discussion rounds: first independent claims, then cross-agent challenge "
            "and reconciliation before voting."
        ),
    },
    {
        "name": "safety_guardrails",
        "prompt": (
            "Refuse deterministic or high-stakes advice. Frame outputs as cultural research, "
            "entertainment, or symbolic interpretation only."
        ),
    },
    {
        "name": "synthesis_calibration",
        "prompt": (
            "In final synthesis, rank conclusions by cross-agent support and explicitly mark conflicts "
            "instead of smoothing them away."
        ),
    },
]

METRIC_FLOORS = {
    "citation": 0.95,
    "safety": 1.0,
    "consistency": 0.8,
    "workflow": 0.8,
    "report_schema": 0.9,
    "provider_contracts": 1.0,
    "evidence_provenance": 1.0,
    "chinese_render": 1.0,
    "capability_audit": 1.0,
    "schema_contract": 1.0,
}


def reproducibility_manifest(
    *,
    run_type: str,
    train_tasks: list[dict[str, Any]],
    validation_tasks: list[dict[str, Any]] | None = None,
    genome_version: int | None = None,
) -> dict[str, Any]:
    """Return a stable manifest for reproducing evolution and benchmark runs."""
    cost_governance = evolution_cost_governance(
        train_task_count=len(train_tasks),
        validation_task_count=len(validation_tasks or []),
        candidate_count=len(MINGLI_STRATEGIES) + 1,
    )
    return {
        "schema_version": 1,
        "run_type": run_type,
        "deterministic": True,
        "random_seed": None,
        "python_version": platform.python_version(),
        "genome_version": genome_version,
        "strategy_names": [strategy["name"] for strategy in MINGLI_STRATEGIES],
        "strategy_fingerprints": strategy_fingerprints(),
        "metric_floors": METRIC_FLOORS,
        "train_task_count": len(train_tasks),
        "train_task_fingerprints": [_task_fingerprint(task) for task in train_tasks],
        "validation_task_count": len(validation_tasks or []),
        "validation_task_fingerprints": [_task_fingerprint(task) for task in (validation_tasks or [])],
        "cost_governance": cost_governance,
    }


def evolution_cost_governance(
    *,
    train_task_count: int,
    validation_task_count: int,
    candidate_count: int,
) -> dict[str, Any]:
    """Return deterministic cost and iteration-frequency controls for evolution runs."""
    baseline_evaluations = 1
    training_candidate_evaluations = max(candidate_count, 0)
    validation_evaluations = 1 if validation_task_count > 0 and candidate_count > 0 else 0
    total_candidate_task_evaluations = (
        (baseline_evaluations + training_candidate_evaluations) * max(train_task_count, 0)
        + validation_evaluations * max(validation_task_count, 0)
    )
    return {
        "schema_version": 1,
        "candidate_count": max(candidate_count, 0),
        "baseline_evaluations": baseline_evaluations,
        "training_candidate_evaluations": training_candidate_evaluations,
        "validation_evaluations": validation_evaluations,
        "train_task_count": max(train_task_count, 0),
        "validation_task_count": max(validation_task_count, 0),
        "total_candidate_task_evaluations": total_candidate_task_evaluations,
        "llm_calls_allowed": False,
        "llm_call_budget": 0,
        "remote_provider_calls_allowed": False,
        "remote_provider_call_budget": 0,
        "iteration_frequency_policy": "manual_or_feedback_triggered",
        "trigger_policy": "run only after explicit feedback, benchmark failure, or operator command",
        "stop_policy": "single population generation with deterministic metric floors and validation gate",
    }


def _task_fingerprint(task: dict[str, Any]) -> str:
    payload = json.dumps(task, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def strategy_fingerprints() -> list[dict[str, str]]:
    """Return stable hashes of evolution strategy definitions."""
    fingerprints = []
    for strategy in MINGLI_STRATEGIES:
        payload = json.dumps(strategy, ensure_ascii=False, sort_keys=True).encode("utf-8")
        fingerprints.append(
            {
                "name": str(strategy["name"]),
                "prompt_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return fingerprints


def genome_fingerprint(genome: AgentGenome) -> str:
    """Hash stable genome content while excluding lineage metadata that stores the hash."""
    payload = genome.model_dump()
    meta = dict(payload.get("meta", {}))
    meta.pop("evolution_lineage", None)
    payload["meta"] = meta
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class CandidateEvaluation:
    """Evaluation record for a single evolved candidate."""

    candidate_name: str
    genome_version: int
    average_score: float
    adjusted_score: float
    mean_metrics: dict[str, float]
    task_scores: list[float]
    metrics: list[dict[str, float]]
    passed_regression_gate: bool
    passed_metric_floors: bool
    rejection_reasons: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


class MingliEvolutionArchive:
    """Append-only archive of candidate evaluations and accepted genomes."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        events = self.load()
        previous_hash = events[-1].get("archive_hash") if events and isinstance(events[-1], dict) else None
        archived = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_archive_hash": previous_hash,
            **event,
        }
        archived["archive_hash"] = self.event_hash(archived)
        events.append(archived)
        self.path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        return archived

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def integrity_report(self) -> dict[str, Any]:
        events = self.load()
        failures = []
        legacy_events = 0
        previous_hash = None
        latest_hash = None
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                failures.append(f"event {index} is not an object")
                continue
            archive_hash = event.get("archive_hash")
            if not archive_hash:
                legacy_events += 1
                previous_hash = None
                continue
            expected_hash = self.event_hash(event)
            if archive_hash != expected_hash:
                failures.append(f"event {index} archive_hash mismatch")
            recorded_previous = event.get("previous_archive_hash")
            if recorded_previous != previous_hash:
                failures.append(f"event {index} previous_archive_hash mismatch")
            previous_hash = archive_hash
            latest_hash = archive_hash
        return {
            "status": "pass" if not failures else "fail",
            "event_count": len(events),
            "hashed_event_count": sum(1 for event in events if isinstance(event, dict) and event.get("archive_hash")),
            "legacy_event_count": legacy_events,
            "latest_hash": latest_hash,
            "failures": failures,
        }

    @staticmethod
    def event_hash(event: dict[str, Any]) -> str:
        payload = {key: value for key, value in event.items() if key != "archive_hash"}
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


ExecutorFn = Callable[[AgentGenome, dict[str, Any]], dict[str, Any]]


class MingliPopulationEvolver:
    """Evaluate a population of domain-specific genome variants before committing."""

    def __init__(
        self,
        repo: GenomeRepository,
        evaluator: Evaluator,
        executor: ExecutorFn,
        agent_name: str = "mingli_orchestrator",
        archive: MingliEvolutionArchive | None = None,
        memory: MingliFeedbackMemory | None = None,
    ):
        self.repo = repo
        self.evaluator = evaluator
        self.executor = executor
        self.agent_name = agent_name
        self.archive = archive or MingliEvolutionArchive(repo.base_path / "archives" / "mingli_evolution.json")
        self.memory = memory or MingliFeedbackMemory(repo.base_path / "memory" / "feedback_memory.json")

    def evolve(
        self,
        train_tasks: list[dict[str, Any]],
        validation_tasks: list[dict[str, Any]] | None = None,
        trigger_receipt: dict[str, Any] | None = None,
    ) -> AgentGenome | None:
        """Generate a candidate population, select on train tasks, validate, and commit."""
        baseline = self.repo.load_agent(self.agent_name)
        candidates = self.generate_population(baseline)
        baseline_eval = self.evaluate_candidate(baseline, train_tasks)
        evaluations = [self.evaluate_candidate(candidate, train_tasks) for candidate in candidates]
        pareto_evaluations = self.pareto_front(evaluations)
        eligible_pairs = [
            (evaluation, candidate)
            for evaluation, candidate in zip(evaluations, candidates)
            if evaluation.passed_regression_gate and evaluation.passed_metric_floors and evaluation in pareto_evaluations
        ]
        if not eligible_pairs:
            eligible_pairs = [
                (evaluation, candidate)
                for evaluation, candidate in zip(evaluations, candidates)
                if evaluation.passed_regression_gate and evaluation.passed_metric_floors
            ]
        if not eligible_pairs:
            eligible_pairs = list(zip(evaluations, candidates))

        best_eval, best_candidate = max(
            eligible_pairs,
            key=lambda pair: (
                pair[0].passed_regression_gate,
                pair[0].passed_metric_floors,
                pair[0].adjusted_score,
            ),
        )

        validation_eval = None
        if validation_tasks:
            validation_eval = self.evaluate_candidate(best_candidate, validation_tasks)

        selection_decision = self._selection_decision(
            baseline_eval=baseline_eval,
            best_eval=best_eval,
            validation_eval=validation_eval,
            validation_task_count=len(validation_tasks or []),
        )
        accepted = selection_decision["accepted"]

        archived_event = self.archive.append(
            {
                "event": "population_evolution",
                "reproducibility_manifest": reproducibility_manifest(
                    run_type="population_evolution",
                    train_tasks=train_tasks,
                    validation_tasks=validation_tasks,
                    genome_version=baseline.version,
                ),
                "baseline_genome_version": baseline.version,
                "accepted_genome_version": best_candidate.version if accepted else None,
                "baseline": baseline_eval.__dict__,
                "candidates": [evaluation.__dict__ for evaluation in evaluations],
                "pareto_front": [evaluation.candidate_name for evaluation in pareto_evaluations],
                "metric_floors": METRIC_FLOORS,
                "validation": validation_eval.__dict__ if validation_eval else None,
                "selection_decision": selection_decision,
                "trigger_receipt": trigger_receipt,
                "accepted": accepted,
                "selected": best_eval.candidate_name,
                "memory_profile": self.memory.profile(),
            }
        )

        if accepted:
            accepted_candidate = self._with_evolution_lineage(
                best_candidate,
                baseline_version=baseline.version,
                archived_event=archived_event,
                selection_decision=selection_decision,
                trigger_receipt=trigger_receipt,
            )
            self.repo.save_agent(accepted_candidate)
            self.memory.remember_evolution(
                selected_strategy=best_eval.candidate_name,
                baseline_score=baseline_eval.average_score,
                evolved_score=best_eval.average_score,
            )
            return accepted_candidate
        return None

    def _with_evolution_lineage(
        self,
        candidate: AgentGenome,
        *,
        baseline_version: int,
        archived_event: dict[str, Any],
        selection_decision: dict[str, Any],
        trigger_receipt: dict[str, Any] | None,
    ) -> AgentGenome:
        lineage = {
            "event": "population_evolution",
            "archive_hash": archived_event.get("archive_hash"),
            "previous_archive_hash": archived_event.get("previous_archive_hash"),
            "archive_timestamp": archived_event.get("timestamp"),
            "genome_fingerprint": genome_fingerprint(candidate),
            "baseline_genome_version": baseline_version,
            "accepted_genome_version": candidate.version,
            "selected_strategy": archived_event.get("selected"),
            "selection_decision": selection_decision,
            "trigger_receipt": trigger_receipt,
            "reproducibility_manifest": archived_event.get("reproducibility_manifest"),
        }
        return candidate.model_copy(update={"meta": {**candidate.meta, "evolution_lineage": lineage}})

    def generate_population(self, baseline: AgentGenome) -> list[AgentGenome]:
        """Create domain-specific variants from one baseline genome."""
        candidates = []
        existing = list(baseline.meta.get("mingli_evolution", []))
        current_workflow = workflow_from_meta(baseline.meta)
        for strategy in MINGLI_STRATEGIES:
            strategy_name = strategy["name"]
            workflow = evolve_workflow(current_workflow, strategy_name)
            prompt = baseline.system_prompt.rstrip() + "\n\nEvolution strategy: " + strategy["prompt"]
            candidates.append(
                baseline.evolve_from(
                    system_prompt=prompt,
                    meta={
                        **baseline.meta,
                        "mingli_evolution": sorted(set(existing + [strategy_name])),
                        "candidate_name": strategy_name,
                        "workflow": workflow.to_meta(),
                    },
                )
            )

        combined_workflow = evolve_workflow(current_workflow, "combined_strategy")
        combined_prompt = baseline.system_prompt.rstrip() + "\n\nEvolution strategy: " + " ".join(
            strategy["prompt"] for strategy in MINGLI_STRATEGIES
        )
        candidates.append(
            baseline.evolve_from(
                system_prompt=combined_prompt,
                meta={
                    **baseline.meta,
                    "mingli_evolution": [strategy["name"] for strategy in MINGLI_STRATEGIES],
                    "candidate_name": "combined_strategy",
                    "workflow": combined_workflow.to_meta(),
                },
            )
        )
        return candidates

    def evaluate_candidate(
        self,
        candidate: AgentGenome,
        tasks: list[dict[str, Any]],
    ) -> CandidateEvaluation:
        """Evaluate one candidate over tasks and the registered regression suite."""
        task_scores = []
        metrics = []
        for item in tasks:
            task_input = item["input"]
            expected = item.get("expected")
            result = {**task_input, **self.executor(candidate, task_input)}
            evaluation = self.evaluator.evaluate(result, expected)
            task_scores.append(evaluation.score)
            metrics.append(evaluation.metrics)

        passed_gate = self._passes_regression_gate(candidate)
        average = sum(task_scores) / len(task_scores) if task_scores else 0.0
        mean_metrics = self._mean_metrics(metrics)
        floor_rejections = self._metric_floor_rejections(mean_metrics)
        candidate_name = candidate.meta.get("candidate_name", candidate.name)
        adjusted = min(1.0, average + self.memory.score_bias(candidate_name))
        return CandidateEvaluation(
            candidate_name=candidate_name,
            genome_version=candidate.version,
            average_score=average,
            adjusted_score=adjusted,
            mean_metrics=mean_metrics,
            task_scores=task_scores,
            metrics=metrics,
            passed_regression_gate=passed_gate,
            passed_metric_floors=not floor_rejections,
            rejection_reasons=floor_rejections,
            meta=candidate.meta,
        )

    def pareto_front(self, evaluations: list[CandidateEvaluation]) -> list[CandidateEvaluation]:
        """Return candidates not dominated across objective metrics and adjusted score."""
        front = []
        for candidate in evaluations:
            dominated = False
            for challenger in evaluations:
                if challenger is candidate:
                    continue
                if self._dominates(challenger, candidate):
                    dominated = True
                    break
            if not dominated:
                front.append(candidate)
        return front

    def _dominates(self, left: CandidateEvaluation, right: CandidateEvaluation) -> bool:
        left_vector = self._objective_vector(left)
        right_vector = self._objective_vector(right)
        return all(l >= r for l, r in zip(left_vector, right_vector)) and any(
            l > r for l, r in zip(left_vector, right_vector)
        )

    def _objective_vector(self, evaluation: CandidateEvaluation) -> tuple[float, ...]:
        return (
            evaluation.mean_metrics.get("citation", 0.0),
            evaluation.mean_metrics.get("safety", 0.0),
            evaluation.mean_metrics.get("consistency", 0.0),
            evaluation.mean_metrics.get("workflow", 0.0),
            evaluation.mean_metrics.get("report_schema", 0.0),
            evaluation.mean_metrics.get("provider_contracts", 0.0),
            evaluation.mean_metrics.get("evidence_provenance", 0.0),
            evaluation.mean_metrics.get("chinese_render", 0.0),
            evaluation.mean_metrics.get("capability_audit", 0.0),
            evaluation.mean_metrics.get("schema_contract", 0.0),
            evaluation.mean_metrics.get("feedback", 0.0),
            evaluation.adjusted_score,
        )

    def _mean_metrics(self, metrics: list[dict[str, float]]) -> dict[str, float]:
        names = sorted({name for item in metrics for name in item})
        if not names:
            return {}
        return {
            name: sum(item.get(name, 0.0) for item in metrics) / len(metrics)
            for name in names
        }

    def _metric_floor_rejections(self, mean_metrics: dict[str, float]) -> list[str]:
        rejections = []
        for metric_name, floor in METRIC_FLOORS.items():
            value = mean_metrics.get(metric_name, 0.0)
            if value < floor:
                rejections.append(f"{metric_name} below floor {floor}: {value:.3f}")
        return rejections

    def _selection_decision(
        self,
        *,
        baseline_eval: CandidateEvaluation,
        best_eval: CandidateEvaluation,
        validation_eval: CandidateEvaluation | None,
        validation_task_count: int,
    ) -> dict[str, Any]:
        """Return named acceptance gates for audit and rollback decisions."""
        train_improvement = best_eval.average_score > baseline_eval.average_score
        validation_floor = validation_eval is None or validation_eval.passed_metric_floors
        validation_score = validation_eval is None or validation_eval.average_score >= baseline_eval.average_score
        gates = {
            "regression_gate": best_eval.passed_regression_gate,
            "metric_floors": best_eval.passed_metric_floors,
            "train_score_improved": train_improvement,
            "validation_metric_floors": validation_floor,
            "validation_score_not_regressed": validation_score,
        }
        reasons = []
        if not best_eval.passed_regression_gate:
            reasons.append("selected candidate failed regression gate")
        if not best_eval.passed_metric_floors:
            reasons.extend(best_eval.rejection_reasons or ["selected candidate failed metric floors"])
        if not train_improvement:
            reasons.append(
                f"selected train score {best_eval.average_score:.3f} did not exceed baseline {baseline_eval.average_score:.3f}"
            )
        if validation_eval is not None and not validation_eval.passed_metric_floors:
            reasons.extend(
                f"validation {reason}"
                for reason in (validation_eval.rejection_reasons or ["candidate failed validation metric floors"])
            )
        if validation_eval is not None and validation_eval.average_score < baseline_eval.average_score:
            reasons.append(
                f"validation score {validation_eval.average_score:.3f} below baseline train score {baseline_eval.average_score:.3f}"
            )
        return {
            "accepted": all(gates.values()),
            "selected": best_eval.candidate_name,
            "baseline_average_score": baseline_eval.average_score,
            "selected_average_score": best_eval.average_score,
            "selected_adjusted_score": best_eval.adjusted_score,
            "validation_average_score": validation_eval.average_score if validation_eval else None,
            "validation_task_count": validation_task_count,
            "gates": gates,
            "rejection_reasons": reasons,
        }

    def _passes_regression_gate(self, candidate: AgentGenome) -> bool:
        if not self.evaluator.regression_tests:
            return True

        def executor_fn(input_data: dict) -> dict:
            return {**input_data, **self.executor(candidate, input_data)}

        all_passed, _results = self.evaluator.run_regression_suite(executor_fn)
        return all_passed
