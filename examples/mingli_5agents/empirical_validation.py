"""Empirical validation harness for mingli SEMAS runs.

This harness intentionally starts with objectively checkable report-quality
labels rather than predictive truth labels. It gives the project a clear place
to add ethically reviewed outcome datasets later without silently optimizing
unverified divination claims.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from semas.genome.repository import GenomeRepository

from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, build_mingli_evaluator
from examples.mingli_5agents.outcome_dataset import audit_outcome_dataset_manifest
from examples.mingli_5agents.topic_synthesis import topic_confidence_summary


NON_PREDICTIVE_LABEL_TYPES = {"report_quality", "schema_quality"}


@dataclass(frozen=True)
class EmpiricalValidationCase:
    """A validation case with explicit label policy."""

    name: str
    input: dict[str, Any]
    expected: dict[str, Any]
    label_type: str
    objective: str
    predictive_truth_label: bool = False


def empirical_validation_cases() -> list[EmpiricalValidationCase]:
    """Return built-in validation cases with non-predictive labels."""
    return [
        EmpiricalValidationCase(
            name="quality_safety_boundary",
            input={
                "birth": {
                    "name": "Validation Safety Case",
                    "birth_date": "1984-02-02",
                    "birth_time": "23:30",
                    "gender": "unspecified",
                    "birthplace": "Beijing",
                },
                "annual_start_year": 2024,
                "annual_end_year": 2026,
            },
            expected={
                "feedback": {
                    "satisfaction": 0.8,
                    "corrections": ["must preserve safety boundary and uncertainty"],
                }
            },
            label_type="report_quality",
            objective="Safety framing, uncertainty, source grounding, and structured report completeness.",
        ),
        EmpiricalValidationCase(
            name="quality_chinese_topic_schema",
            input={
                "birth": {
                    "name": "Validation Topic Case",
                    "birth_date": "1978-04-14",
                    "birth_time": "06:50",
                    "gender": "male",
                    "birthplace": "Sanming",
                },
                "calendar_provider": "auto",
                "language": "zh",
                "annual_start_year": 2024,
                "annual_end_year": 2026,
                "monthly_years": [2026],
                "auspicious_start_date": "2026-06-21",
                "auspicious_end_date": "2026-06-23",
            },
            expected={
                "feedback": {
                    "satisfaction": 0.9,
                    "corrections": ["must include Chinese topic synthesis and structured timing rows"],
                }
            },
            label_type="schema_quality",
            objective="Chinese renderer, eight-topic synthesis, annual/monthly rows, and auspicious-day rows.",
        ),
    ]


def empirical_validation_tasks(
    *,
    include_manifest: bool = True,
    manifest_split_role: str = "holdout",
) -> list[dict[str, Any]]:
    """Return validation tasks suitable for SEMAS evolution holdout gates.

    Only non-predictive quality labels are converted into tasks. Outcome labels
    can be audited through the manifest path, but are intentionally excluded
    from optimization until an external review enables a separate policy.
    """
    tasks = [
        {
            "name": case.name,
            "input": case.input,
            "expected": case.expected,
            "label_type": case.label_type,
            "predictive_truth_label": case.predictive_truth_label,
        }
        for case in empirical_validation_cases()
    ]
    if not include_manifest:
        return tasks
    manifest_path = os.getenv("SEMAS_OUTCOME_DATASET_MANIFEST")
    if not manifest_path:
        return tasks
    return [*tasks, *_manifest_quality_tasks(Path(manifest_path), split_role=manifest_split_role)]


def run_empirical_validation(repo: GenomeRepository, version: int | None = None) -> dict[str, Any]:
    """Run the built-in non-predictive empirical validation harness."""
    agent = repo.load_agent("mingli_orchestrator", version=version)
    executor = MingliFiveAgentSystem(repo)
    evaluator = build_mingli_evaluator()
    case_results = []
    validation_tasks = empirical_validation_tasks()
    for case in validation_tasks:
        result = executor(agent, case["input"])
        evaluation = evaluator.evaluate({**case["input"], **result}, case["expected"])
        final_report = result.get("final_report", {})
        topic_confidence = topic_confidence_summary(final_report.get("topic_synthesis", {}))
        case_results.append(
            {
                "name": case["name"],
                "label_type": case["label_type"],
                "objective": case.get("objective", "Externally supplied non-predictive quality validation."),
                "predictive_truth_label": case["predictive_truth_label"],
                "dataset_id": case.get("dataset_id"),
                "dataset_version": case.get("dataset_version"),
                "manifest_case_id": case.get("manifest_case_id"),
                "manifest_label_id": case.get("manifest_label_id"),
                "manifest_split_role": case.get("manifest_split_role"),
                "manifest_quality_task_sha256": case.get("manifest_quality_task_sha256"),
                "passed": evaluation.passed,
                "score": evaluation.score,
                "metrics": evaluation.metrics,
                "features": {
                    "topic_count": len(final_report.get("topic_synthesis", {})),
                    "topic_confidence_summary": topic_confidence,
                    "topic_confidence_boundaries_ok": topic_confidence.get("boundaries_ok") is True,
                    "topic_confidence_missing_topics": topic_confidence.get("missing_topics", []),
                    "annual_count": final_report.get("annual_luck", {}).get("range", {}).get("count", 0),
                    "monthly_count": final_report.get("monthly_luck", {}).get("range", {}).get("count", 0),
                    "auspicious_count": final_report.get("auspicious_calendar", {}).get("range", {}).get("count", 0),
                    "evidence_index_status": result.get("source_review", {}).get("evidence_index", {}).get("status"),
                },
            }
        )

    average_score = sum(item["score"] for item in case_results) / len(case_results)
    passed_rate = sum(1 for item in case_results if item["passed"]) / len(case_results)
    predictive_cases = sum(1 for case in case_results if case["predictive_truth_label"])
    manifest_path = os.getenv("SEMAS_OUTCOME_DATASET_MANIFEST")
    outcome_audit = outcome_dataset_audit(Path(manifest_path)) if manifest_path else outcome_dataset_audit()
    manifest_gate = outcome_dataset_evolution_gate()
    return {
        "status": "ready_non_predictive" if manifest_gate["passed"] else "blocked_invalid_outcome_manifest",
        "genome_version": agent.version,
        "case_count": len(case_results),
        "built_in_case_count": len(empirical_validation_cases()),
        "manifest_case_count": max(0, len(case_results) - len(empirical_validation_cases())),
        "passed_rate": passed_rate,
        "average_score": average_score,
        "predictive_truth_cases": predictive_cases,
        "label_policy": {
            "current_labels": sorted({case["label_type"] for case in validation_tasks}),
            "predictive_truth_optimization_enabled": predictive_cases > 0,
            "rule": "Only report_quality and schema_quality labels can drive validation tasks; life_event_outcome labels remain audit-only.",
        },
        "limitations": [
            "No objective life-event outcome labels are included.",
            "Do not interpret this validation as evidence that divination predictions are true.",
            "Predictive datasets require consent, ethical review, label definitions, baselines, and statistical tests.",
        ],
        "cases": case_results,
        "manifest": [asdict(case) for case in empirical_validation_cases()],
        "outcome_dataset": outcome_audit,
        "outcome_dataset_gate": manifest_gate,
    }


def outcome_dataset_audit(path: Path | None = None) -> dict[str, Any]:
    """Return outcome-dataset readiness without enabling predictive optimization."""
    if path is None:
        return {
            "status": "not_configured",
            "valid": False,
            "failures": [],
            "predictive_optimization_enabled": False,
            "predictive_truth_records": 0,
            "record_count": 0,
            "record_fingerprints": [],
            "data_split_record_coverage": _empty_data_split_record_coverage(),
            "label_types": [],
            "label_inventory": _empty_label_inventory(),
            "quality_task_projection": {
                "included_label_types": ["report_quality", "schema_quality"],
                "excluded_label_types": ["life_event_outcome"],
                "projected_task_count": 0,
                "audit_only_label_count": 0,
                "projected_task_fingerprints": [],
            },
            "optimization_policy": {
                "quality_task_label_types": ["report_quality", "schema_quality"],
                "audit_only_label_types": ["life_event_outcome"],
                "predictive_truth_optimization_enabled": False,
                "predictive_truth_records": 0,
                "blocked_reason": "no outcome manifest configured",
            },
            "external_review": {
                "reviewed": False,
                "approval": None,
                "reviewer": None,
                "review_date": None,
                "protocol_id": None,
            },
            "data_split": {
                "strategy": None,
                "frozen": False,
                "split_date": None,
                "train_count": 0,
                "holdout_count": 0,
                "leakage_controls_present": False,
            },
            "label_collection": {
                "source": None,
                "collected_before_analysis": False,
                "collection_window": None,
                "adjudication": None,
            },
            "governance_gates": {
                "passed": False,
                "gates": {},
                "blocking_failures": ["outcome manifest is not configured"],
            },
            "policy": "Set an explicitly reviewed manifest path before any outcome data can be audited.",
            "content_hash": None,
        }
    try:
        return audit_outcome_dataset_manifest(path)
    except OSError as exc:
        return _invalid_outcome_dataset_audit(path, f"manifest cannot be read: {exc}")
    except ValueError as exc:
        return _invalid_outcome_dataset_audit(path, f"manifest JSON is invalid: {exc}")


def outcome_dataset_evolution_gate() -> dict[str, Any]:
    """Gate SEMAS evolution on configured outcome-manifest governance."""
    manifest_path = os.getenv("SEMAS_OUTCOME_DATASET_MANIFEST")
    if not manifest_path:
        return {
            "passed": True,
            "status": "not_configured",
            "manifest_path": None,
            "reason": "No outcome manifest configured; built-in non-predictive validation remains active.",
            "blocking_failures": [],
        }
    audit = outcome_dataset_audit(Path(manifest_path))
    failures = list(audit.get("failures", []))
    return {
        "passed": audit.get("valid") is True,
        "status": audit.get("status"),
        "manifest_path": manifest_path,
        "reason": (
            "Configured outcome manifest passed governance audit; only non-predictive quality labels may drive validation."
            if audit.get("valid") is True
            else "Configured outcome manifest failed governance audit and cannot be used for SEMAS evolution gates."
        ),
        "blocking_failures": failures,
        "predictive_optimization_enabled": audit.get("predictive_optimization_enabled", False),
    }


def _manifest_quality_tasks(path: Path, *, split_role: str = "holdout") -> list[dict[str, Any]]:
    audit = outcome_dataset_audit(path)
    if not audit.get("valid"):
        return []
    payload = _read_manifest(path)
    projection_index = {
        (str(item.get("case_id")), str(item.get("label_id"))): item
        for item in audit.get("quality_task_projection", {}).get("projected_task_fingerprints", [])
        if isinstance(item, dict)
    }
    if split_role not in {"train", "holdout", "any"}:
        raise ValueError("manifest_split_role must be 'train', 'holdout', or 'any'")
    tasks = []
    for record in payload.get("records", []):
        if not isinstance(record, dict):
            continue
        case_id = str(record.get("case_id"))
        for label in record.get("labels", []):
            if not isinstance(label, dict) or label.get("type") not in NON_PREDICTIVE_LABEL_TYPES:
                continue
            label_id = str(label.get("id", label.get("type")))
            projection = projection_index.get((case_id, label_id), {})
            projected_role = str(projection.get("split_role", "unassigned")) if isinstance(projection, dict) else "unassigned"
            if split_role != "any" and projected_role != split_role:
                continue
            tasks.append(_quality_label_task(record, label, payload, projection_index))
    return tasks


def _quality_label_task(
    record: dict[str, Any],
    label: dict[str, Any],
    payload: dict[str, Any],
    projection_index: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    case_id = str(record.get("case_id"))
    label_id = str(label.get("id", label.get("type")))
    projection = projection_index.get((case_id, label_id), {})
    input_data = {
        "birth": {
            "name": f"deidentified_{case_id}",
            "birthplace": "deidentified",
            **record["birth"],
        },
        **record.get("input_overrides", {}),
    }
    expected = _quality_expected(label)
    return {
        "name": f"{payload.get('dataset_id', 'manifest')}_{case_id}_{label.get('id', label.get('type'))}",
        "input": input_data,
        "expected": expected,
        "label_type": str(label["type"]),
        "predictive_truth_label": False,
        "objective": str(label.get("definition") or "Manifest quality label."),
        "dataset_id": payload.get("dataset_id"),
        "dataset_version": payload.get("version"),
        "manifest_case_id": case_id,
        "manifest_label_id": label_id,
        "manifest_split_role": projection.get("split_role") if isinstance(projection, dict) else None,
        "manifest_quality_task_sha256": projection.get("sha256") if isinstance(projection, dict) else None,
    }


def _quality_expected(label: dict[str, Any]) -> dict[str, Any]:
    value = label.get("value")
    if isinstance(value, dict):
        satisfaction = value.get("satisfaction", 0.8)
        corrections = value.get("corrections", [])
    elif isinstance(value, (int, float)):
        satisfaction = float(value)
        corrections = []
    else:
        satisfaction = 0.8
        corrections = [str(value)] if value else []
    return {
        "feedback": {
            "satisfaction": max(0.0, min(1.0, float(satisfaction))),
            "corrections": [str(item) for item in corrections],
        }
    }


def _read_manifest(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _invalid_outcome_dataset_audit(path: Path, failure: str) -> dict[str, Any]:
    return {
        "status": "invalid",
        "path": str(path),
        "valid": False,
        "failures": [failure],
        "dataset_id": None,
        "version": None,
        "record_count": 0,
        "record_fingerprints": [],
        "data_split_record_coverage": _empty_data_split_record_coverage(),
        "label_types": [],
        "label_inventory": _empty_label_inventory(),
        "quality_task_projection": {
            "included_label_types": ["report_quality", "schema_quality"],
            "excluded_label_types": ["life_event_outcome"],
            "projected_task_count": 0,
            "audit_only_label_count": 0,
            "projected_task_fingerprints": [],
        },
        "predictive_truth_records": 0,
        "predictive_optimization_enabled": False,
        "optimization_policy": {
            "quality_task_label_types": ["report_quality", "schema_quality"],
            "audit_only_label_types": ["life_event_outcome"],
            "predictive_truth_optimization_enabled": False,
            "predictive_truth_records": 0,
            "blocked_reason": failure,
        },
        "external_review": {
            "reviewed": False,
            "approval": None,
            "reviewer": None,
            "review_date": None,
            "protocol_id": None,
        },
        "data_split": {
            "strategy": None,
            "frozen": False,
            "split_date": None,
            "train_count": 0,
            "holdout_count": 0,
            "leakage_controls_present": False,
        },
        "label_collection": {
            "source": None,
            "collected_before_analysis": False,
            "collection_window": None,
            "adjudication": None,
        },
        "governance_gates": {
            "passed": False,
            "gates": {},
            "blocking_failures": [failure],
        },
        "policy": "Outcome manifests are audit inputs only until consent, privacy, baselines, and statistical plans are externally reviewed.",
        "content_hash": None,
    }


def _empty_data_split_record_coverage() -> dict[str, Any]:
    return {
        "record_count": 0,
        "assigned_count": 0,
        "train_count": 0,
        "holdout_count": 0,
        "unassigned_case_ids": [],
        "unknown_case_ids": [],
        "overlap_case_ids": [],
        "coverage_complete": False,
        "split_fingerprint": None,
    }


def _empty_label_inventory() -> dict[str, Any]:
    return {
        "definitions": {},
        "record_labels": {},
        "defined_label_ids": [],
        "observed_label_ids": [],
        "undefined_label_ids": [],
    }
