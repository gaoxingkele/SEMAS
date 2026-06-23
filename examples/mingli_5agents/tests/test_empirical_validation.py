"""Tests for empirical validation harness boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from examples.mingli_5agents.capability_audit import capability_audit
from examples.mingli_5agents.api_core import _production_resolution_plan, evolve_case, outcome_dataset_manifest_status
from examples.mingli_5agents.empirical_validation import (
    empirical_validation_cases,
    empirical_validation_tasks,
    outcome_dataset_evolution_gate,
    outcome_dataset_audit,
    run_empirical_validation,
)
from examples.mingli_5agents.outcome_dataset import audit_outcome_dataset_manifest
from examples.mingli_5agents.run_demo import bootstrap_repo


EXAMPLE_OUTCOME_MANIFEST = (
    Path(__file__).resolve().parents[1] / "providers" / "outcome_dataset_manifest_example.json"
)


def test_empirical_validation_cases_are_non_predictive():
    cases = empirical_validation_cases()
    assert cases
    assert all(case.predictive_truth_label is False for case in cases)
    assert {case.label_type for case in cases} == {"report_quality", "schema_quality"}


def test_run_empirical_validation_reports_label_policy(tmp_path):
    repo = bootstrap_repo(tmp_path)
    result = run_empirical_validation(repo)

    assert result["status"] == "ready_non_predictive"
    assert result["case_count"] == len(empirical_validation_cases())
    assert result["predictive_truth_cases"] == 0
    assert result["label_policy"]["predictive_truth_optimization_enabled"] is False
    assert 0.0 <= result["average_score"] <= 1.0
    assert all(case["features"]["evidence_index_status"] == "ready" for case in result["cases"])
    assert all(case["features"]["topic_confidence_boundaries_ok"] is True for case in result["cases"])
    assert all(case["features"]["topic_confidence_missing_topics"] == [] for case in result["cases"])
    assert all(
        "provider_fallbacks_present" in case["features"]["topic_confidence_summary"]["downgrade_reasons"]
        for case in result["cases"]
    )


def _valid_outcome_manifest():
    return {
        "dataset_id": "reviewed_quality_dataset",
        "version": "2026.06",
        "purpose": "quality validation only",
        "consent": {
            "documented": True,
            "scope": "quality_validation",
            "withdrawal_process": "email data steward",
        },
        "privacy": {
            "deidentified": True,
            "direct_identifiers_removed": True,
            "retention_policy": "bounded_archive",
        },
        "external_review": {
            "reviewed": True,
            "reviewer": "independent data steward",
            "review_date": "2026-06-01",
            "approval": "approved_for_quality_validation",
            "protocol_id": "quality-validation-protocol-v1",
        },
        "data_split": {
            "strategy": "pre_registered_holdout",
            "frozen": True,
            "split_date": "2026-06-01",
            "train_case_ids": [],
            "holdout_case_ids": ["case_001"],
            "leakage_controls": "Holdout labels are not used for prompt or genome mutation.",
        },
        "label_collection": {
            "source": "mixed",
            "collected_before_analysis": True,
            "collection_window": "2024-01-01/2024-12-31",
            "adjudication": "Data steward resolves record disputes before manifest publication.",
        },
        "labels": [
            {
                "id": "career_change",
                "type": "life_event_outcome",
                "definition": "Self-reported job change in the measurement window.",
                "measurement_window": "2024-01-01/2024-12-31",
            },
            {
                "id": "report_completeness",
                "type": "report_quality",
                "definition": "Report preserves structure, uncertainty, and boundary language.",
                "measurement_window": "2024-01-01/2024-12-31",
            }
        ],
        "baselines": [{"name": "base_rate", "method": "label base-rate comparison"}],
        "statistical_plan": {
            "hypotheses": ["No predictive lift over base rate unless externally reviewed."],
            "metrics": ["calibration", "base_rate_delta"],
            "minimum_sample_size": 200,
            "holdout_strategy": "pre-registered holdout split",
            "pre_registered": True,
            "registration_id": "quality-validation-plan-v1",
            "registered_at": "2026-06-01",
            "analysis_freeze_date": "2026-06-01",
            "plan_sha256": "0" * 64,
        },
        "records": [
            {
                "case_id": "case_001",
                "birth": {
                    "birth_date": "1980-01-02",
                    "birth_time": "08:30",
                    "gender": "unspecified",
                    "birthplace_region": "province_only",
                },
                "labels": [
                    {
                        "id": "career_change",
                        "type": "life_event_outcome",
                        "value": False,
                        "provenance": {
                            "source": "self_report",
                            "collected_at": "2025-01-15",
                            "collected_before_analysis": True,
                            "reviewer_or_method": "independent data steward",
                            "audit_only_acknowledged": True,
                        },
                    },
                    {
                        "id": "report_completeness",
                        "type": "report_quality",
                        "value": {
                            "satisfaction": 0.85,
                            "corrections": ["must include uncertainty boundary"],
                        },
                        "provenance": {
                            "source": "reviewer_scored",
                            "collected_at": "2025-01-20",
                            "collected_before_analysis": True,
                            "reviewer_or_method": "rubric-v1",
                        },
                    }
                ],
            }
        ],
    }


def test_outcome_dataset_manifest_audit_accepts_review_ready_manifest(tmp_path):
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(_valid_outcome_manifest()), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["status"] == "ready_for_review"
    assert result["valid"] is True
    assert result["predictive_truth_records"] == 1
    assert result["predictive_optimization_enabled"] is False
    assert result["governance_gates"]["passed"] is True
    assert result["governance_gates"]["gates"]["record_labels_defined"] is True
    assert result["governance_gates"]["gates"]["external_review_approved"] is True
    assert result["governance_gates"]["gates"]["data_split_frozen"] is True
    assert result["governance_gates"]["gates"]["holdout_case_ids_present"] is True
    assert result["governance_gates"]["gates"]["data_split_records_covered"] is True
    assert result["governance_gates"]["gates"]["label_collection_pre_analysis"] is True
    assert result["governance_gates"]["gates"]["record_label_provenance_complete"] is True
    assert result["governance_gates"]["gates"]["statistical_plan_preregistered"] is True
    assert result["external_review"]["protocol_id"] == "quality-validation-protocol-v1"
    assert result["data_split"]["holdout_count"] == 1
    assert result["label_collection"]["collected_before_analysis"] is True
    assert result["statistical_plan"]["preregistration_complete"] is True
    assert result["statistical_plan"]["registration_id"] == "quality-validation-plan-v1"
    assert len(result["record_fingerprints"]) == 1
    assert len(result["record_fingerprints"][0]["sha256"]) == 64
    split_coverage = result["data_split_record_coverage"]
    assert split_coverage["coverage_complete"] is True
    assert split_coverage["record_count"] == 1
    assert split_coverage["assigned_count"] == 1
    assert split_coverage["holdout_count"] == 1
    assert len(split_coverage["split_fingerprint"]) == 64
    projection = result["quality_task_projection"]
    assert projection["projected_task_count"] == 1
    assert projection["audit_only_label_count"] == 1
    assert projection["included_label_types"] == ["report_quality", "schema_quality"]
    assert projection["excluded_label_types"] == ["life_event_outcome"]
    assert projection["projected_task_fingerprints"][0]["label_id"] == "report_completeness"
    assert projection["projected_task_fingerprints"][0]["split_role"] == "holdout"
    assert len(projection["projected_task_fingerprints"][0]["sha256"]) == 64
    assert result["label_inventory"]["record_labels"]["life_event_outcome"] == 1
    assert result["label_inventory"]["record_labels"]["report_quality"] == 1
    assert result["label_provenance"]["provenance_complete"] is True
    assert result["label_provenance"]["audit_only_acknowledged_count"] == 1
    assert result["optimization_policy"]["predictive_truth_optimization_enabled"] is False
    assert result["optimization_policy"]["audit_only_label_types"] == ["life_event_outcome"]


def test_outcome_dataset_manifest_status_exposes_stable_receipt(tmp_path):
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(_valid_outcome_manifest()), encoding="utf-8")

    result = outcome_dataset_manifest_status(tmp_path / "repo", manifest_path=manifest)
    repeated = outcome_dataset_manifest_status(tmp_path / "repo", manifest_path=manifest)

    receipt = result["outcome_dataset_receipt"]
    assert receipt["schema_version"] == 1
    assert len(receipt["sha256"]) == 64
    assert repeated["outcome_dataset_receipt"]["sha256"] == receipt["sha256"]
    assert receipt["material"]["schema_version"] == 1
    assert receipt["material"]["status"] == result["audit"]["status"]
    assert receipt["material"]["content_hash"] == result["audit"]["content_hash"]
    assert receipt["material"]["data_split_record_coverage"] == result["audit"]["data_split_record_coverage"]
    assert receipt["material"]["label_provenance"] == result["audit"]["label_provenance"]
    assert receipt["material"]["statistical_plan"] == result["audit"]["statistical_plan"]
    assert "external_review_approved" in receipt["material"]["governance_gate_ids"]
    assert "statistical_plan_preregistered" in receipt["material"]["governance_gate_ids"]
    assert result["evolution_gate"]["passed"] is True
    guidance = result["configuration_guidance"]
    assert guidance["configured"] is True
    assert guidance["env_var"] == "SEMAS_OUTCOME_DATASET_MANIFEST"
    assert guidance["current_manifest_path"] == str(manifest)
    assert guidance["example_is_demonstration_only"] is True
    assert "outcome-dataset --manifest" in guidance["cli_audit_command"]
    assert "production-readiness --manifest" in guidance["production_readiness_command"]


def test_outcome_dataset_manifest_status_exposes_unconfigured_guidance(tmp_path):
    result = outcome_dataset_manifest_status(tmp_path / "repo")

    guidance = result["configuration_guidance"]
    assert result["manifest_path"] is None
    assert result["evolution_gate"]["passed"] is True
    assert guidance["configured"] is False
    assert guidance["current_manifest_path"] is None
    assert guidance["env_var"] == "SEMAS_OUTCOME_DATASET_MANIFEST"
    assert guidance["example_manifest_path"].endswith("outcome_dataset_manifest_example.json")
    assert guidance["example_is_demonstration_only"] is True
    assert "<manifest.json>" in guidance["cli_audit_command"]
    assert "<manifest.json>" in guidance["production_readiness_command"]
    assert guidance["http_query"] == "GET /outcome-dataset?manifest=<manifest.json>"
    assert "must not be treated as production evidence" in guidance["policy"]


def test_outcome_dataset_manifest_example_is_review_ready(monkeypatch):
    result = audit_outcome_dataset_manifest(EXAMPLE_OUTCOME_MANIFEST)

    assert result["status"] == "ready_for_review"
    assert result["valid"] is True
    assert result["dataset_id"] == "example_reviewed_quality_dataset"
    assert result["predictive_truth_records"] == 1
    assert result["predictive_optimization_enabled"] is False

    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(EXAMPLE_OUTCOME_MANIFEST))
    manifest_tasks = [
        task for task in empirical_validation_tasks() if task.get("dataset_id") == "example_reviewed_quality_dataset"
    ]

    assert len(manifest_tasks) == 1
    assert manifest_tasks[0]["label_type"] == "report_quality"
    assert manifest_tasks[0]["predictive_truth_label"] is False
    assert manifest_tasks[0]["expected"]["feedback"]["satisfaction"] == 0.86
    projection = result["quality_task_projection"]["projected_task_fingerprints"][0]
    assert manifest_tasks[0]["dataset_version"] == "2026.06-example"
    assert manifest_tasks[0]["manifest_case_id"] == projection["case_id"]
    assert manifest_tasks[0]["manifest_label_id"] == projection["label_id"]
    assert manifest_tasks[0]["manifest_split_role"] == "holdout"
    assert manifest_tasks[0]["manifest_quality_task_sha256"] == projection["sha256"]
    assert len(manifest_tasks[0]["manifest_quality_task_sha256"]) == 64


def test_empirical_validation_tasks_import_only_non_predictive_manifest_labels(tmp_path, monkeypatch):
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(_valid_outcome_manifest()), encoding="utf-8")
    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(manifest))

    tasks = empirical_validation_tasks()
    manifest_tasks = [task for task in tasks if task.get("dataset_id") == "reviewed_quality_dataset"]

    assert len(manifest_tasks) == 1
    assert manifest_tasks[0]["label_type"] == "report_quality"
    assert manifest_tasks[0]["predictive_truth_label"] is False
    assert manifest_tasks[0]["expected"]["feedback"]["satisfaction"] == 0.85
    assert manifest_tasks[0]["input"]["birth"]["name"].startswith("deidentified_")
    assert manifest_tasks[0]["dataset_version"] == "2026.06"
    assert manifest_tasks[0]["manifest_case_id"] == "case_001"
    assert manifest_tasks[0]["manifest_label_id"] == "report_completeness"
    assert manifest_tasks[0]["manifest_split_role"] == "holdout"
    assert len(manifest_tasks[0]["manifest_quality_task_sha256"]) == 64


def test_empirical_validation_tasks_use_holdout_manifest_split_only(tmp_path, monkeypatch):
    payload = _valid_outcome_manifest()
    payload["data_split"]["train_case_ids"] = ["case_train"]
    payload["data_split"]["holdout_case_ids"] = ["case_001"]
    train_record = json.loads(json.dumps(payload["records"][0]))
    train_record["case_id"] = "case_train"
    train_record["labels"][1]["value"]["satisfaction"] = 0.42
    payload["records"].append(train_record)
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(manifest))

    audit = audit_outcome_dataset_manifest(manifest)
    tasks = empirical_validation_tasks()
    all_manifest_tasks = empirical_validation_tasks(manifest_split_role="any")

    projection_roles = {
        (item["case_id"], item["label_id"]): item["split_role"]
        for item in audit["quality_task_projection"]["projected_task_fingerprints"]
    }
    manifest_tasks = [task for task in tasks if task.get("dataset_id") == "reviewed_quality_dataset"]
    all_dataset_tasks = [task for task in all_manifest_tasks if task.get("dataset_id") == "reviewed_quality_dataset"]

    assert audit["data_split_record_coverage"]["coverage_complete"] is True
    assert projection_roles[("case_001", "report_completeness")] == "holdout"
    assert projection_roles[("case_train", "report_completeness")] == "train"
    assert [task["manifest_case_id"] for task in manifest_tasks] == ["case_001"]
    assert manifest_tasks[0]["manifest_split_role"] == "holdout"
    assert {task["manifest_split_role"] for task in all_dataset_tasks} == {"train", "holdout"}


def test_run_empirical_validation_includes_reviewed_manifest_quality_cases(tmp_path, monkeypatch):
    repo = bootstrap_repo(tmp_path / "repo")
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(_valid_outcome_manifest()), encoding="utf-8")
    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(manifest))

    result = run_empirical_validation(repo)

    assert result["case_count"] == len(empirical_validation_cases()) + 1
    assert result["manifest_case_count"] == 1
    assert result["predictive_truth_cases"] == 0
    assert result["outcome_dataset"]["predictive_truth_records"] == 1
    assert result["outcome_dataset"]["quality_task_projection"]["projected_task_count"] == 1
    assert result["label_policy"]["predictive_truth_optimization_enabled"] is False
    assert result["outcome_dataset_gate"]["passed"] is True
    projection = result["outcome_dataset"]["quality_task_projection"]["projected_task_fingerprints"][0]
    manifest_case = next(case for case in result["cases"] if case.get("dataset_id") == "reviewed_quality_dataset")
    assert manifest_case["dataset_version"] == "2026.06"
    assert manifest_case["manifest_case_id"] == projection["case_id"] == "case_001"
    assert manifest_case["manifest_label_id"] == projection["label_id"] == "report_completeness"
    assert manifest_case["manifest_split_role"] == "holdout"
    assert manifest_case["manifest_quality_task_sha256"] == projection["sha256"]
    assert len(manifest_case["manifest_quality_task_sha256"]) == 64


def test_invalid_configured_outcome_manifest_blocks_empirical_gate(tmp_path, monkeypatch):
    repo = bootstrap_repo(tmp_path / "repo")
    payload = _valid_outcome_manifest()
    payload["statistical_plan"]["minimum_sample_size"] = 12
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(manifest))

    gate = outcome_dataset_evolution_gate()
    result = run_empirical_validation(repo)

    assert gate["passed"] is False
    assert gate["status"] == "invalid"
    assert result["status"] == "blocked_invalid_outcome_manifest"
    assert result["outcome_dataset_gate"]["passed"] is False
    assert "minimum_sample_size" in result["outcome_dataset_gate"]["blocking_failures"][0]


def test_evolve_case_blocks_invalid_configured_outcome_manifest(tmp_path, monkeypatch):
    payload = _valid_outcome_manifest()
    payload["records"][0]["birth"]["name"] = "Unsafe Name"
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(manifest))

    result = evolve_case(
        tmp_path / "repo",
        {
            "birth": {
                "name": "Gate Case",
                "birth_date": "1990-01-01",
                "birth_time": "08:00",
                "gender": "unspecified",
                "birthplace": "Nanjing",
            }
        },
        {"feedback": {"satisfaction": 0.9, "corrections": ["keep governance gate strict"]}},
    )

    assert result["accepted"] is False
    assert result["blocked"] is True
    assert result["before_version"] == result["after_version"]
    assert result["validation_case_count"] == 0
    assert result["validation_gate"]["passed"] is False
    assert result["selection_decision"]["accepted"] is False
    assert result["selection_decision"]["gates"]["outcome_dataset_gate"] is False
    assert "birth.name must be omitted" in result["validation_gate"]["blocking_failures"][0]
    assert "birth.name must be omitted" in result["selection_decision"]["rejection_reasons"][0]


def test_outcome_dataset_manifest_audit_rejects_identifiers(tmp_path):
    payload = _valid_outcome_manifest()
    payload["records"][0]["birth"]["name"] = "Unsafe Name"
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert any("birth.name must be omitted" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_rejects_undefined_record_label(tmp_path):
    payload = _valid_outcome_manifest()
    payload["records"][0]["labels"].append({"id": "undefined_label", "type": "report_quality", "value": 0.7})
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert result["governance_gates"]["gates"]["record_labels_defined"] is False
    assert "undefined_label" in result["label_inventory"]["undefined_label_ids"]
    assert any("has no label definition" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_rejects_label_type_mismatch(tmp_path):
    payload = _valid_outcome_manifest()
    payload["records"][0]["labels"][0]["type"] = "report_quality"
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert any("does not match definition" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_rejects_missing_label_provenance(tmp_path):
    payload = _valid_outcome_manifest()
    payload["records"][0]["labels"][1].pop("provenance")
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert result["label_provenance"]["provenance_complete"] is False
    assert result["governance_gates"]["gates"]["record_label_provenance_complete"] is False
    assert any("label report_completeness provenance must be an object" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_requires_audit_only_ack_for_life_event_labels(tmp_path):
    payload = _valid_outcome_manifest()
    payload["records"][0]["labels"][0]["provenance"]["audit_only_acknowledged"] = False
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert result["label_provenance"]["provenance_complete"] is False
    assert any("audit_only_acknowledged must be true" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_rejects_invalid_minimum_sample_size(tmp_path):
    payload = _valid_outcome_manifest()
    payload["statistical_plan"]["minimum_sample_size"] = 12
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert result["governance_gates"]["gates"]["minimum_sample_size_declared"] is False
    assert any("minimum_sample_size must be an integer >= 30" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_rejects_unregistered_statistical_plan(tmp_path):
    payload = _valid_outcome_manifest()
    payload["statistical_plan"].pop("plan_sha256")
    payload["statistical_plan"]["pre_registered"] = False
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert result["governance_gates"]["gates"]["statistical_plan_preregistered"] is False
    assert result["statistical_plan"]["preregistration_complete"] is False
    assert "statistical_plan.pre_registered must be true" in result["failures"]
    assert (
        "statistical_plan.plan_sha256 or statistical_plan.plan_receipt_sha256 is required"
        in result["failures"]
    )


def test_outcome_dataset_manifest_rejects_unreviewed_or_unfrozen_data(tmp_path):
    payload = _valid_outcome_manifest()
    payload["external_review"]["reviewed"] = False
    payload["data_split"]["frozen"] = False
    payload["label_collection"]["collected_before_analysis"] = False
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    gates = result["governance_gates"]["gates"]
    assert gates["external_review_approved"] is False
    assert gates["data_split_frozen"] is False
    assert gates["label_collection_pre_analysis"] is False
    assert any("external_review.reviewed must be true" in failure for failure in result["failures"])
    assert any("data_split.frozen must be true" in failure for failure in result["failures"])
    assert any("label_collection.collected_before_analysis must be true" in failure for failure in result["failures"])


def test_outcome_dataset_manifest_rejects_unassigned_records(tmp_path):
    payload = _valid_outcome_manifest()
    payload["records"].append(
        {
            "case_id": "case_002",
            "birth": {
                "birth_date": "1985-03-04",
                "birth_time": "11:20",
                "gender": "unspecified",
                "birthplace_region": "province_only",
            },
            "labels": [
                {
                    "id": "report_completeness",
                    "type": "report_quality",
                    "value": {
                        "satisfaction": 0.8,
                        "corrections": ["must preserve source boundaries"],
                    },
                }
            ],
        }
    )
    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = audit_outcome_dataset_manifest(manifest)

    assert result["valid"] is False
    assert result["data_split_record_coverage"]["coverage_complete"] is False
    assert result["data_split_record_coverage"]["unassigned_case_ids"] == ["case_002"]
    assert result["governance_gates"]["gates"]["data_split_records_covered"] is False
    assert any("does not assign all record case_ids" in failure for failure in result["failures"])


def test_production_resolution_plan_keeps_split_specific_outcome_step(tmp_path):
    plan = _production_resolution_plan(
        repo_path=tmp_path / "repo",
        manifest_path=tmp_path / "outcomes.json",
        live=False,
        providers={},
        outcome={
            "evolution_gate": {
                "blocking_failures": ["data_split does not assign all record case_ids: case_002"],
            },
            "audit": {
                "data_split_record_coverage": {
                    "record_count": 2,
                    "assigned_count": 1,
                    "train_count": 0,
                    "holdout_count": 1,
                    "unassigned_case_ids": ["case_002"],
                    "unknown_case_ids": [],
                    "overlap_case_ids": [],
                    "coverage_complete": False,
                    "split_fingerprint": "a" * 64,
                }
            },
        },
        provider_ledger={},
        provider_drift={},
        release_ledger={},
        evidence_materialization={},
        classical_source_refresh={},
        current_benchmark={},
        benchmark_analyze_response_schema={},
        blockers=[
            {"gate": "outcome_dataset_gate_passed"},
            {"gate": "outcome_dataset_data_split_records_covered"},
            {"gate": "outcome_dataset_statistical_plan_preregistered"},
        ],
    )

    step_ids = {step["id"] for step in plan["steps"]}
    assert "repair_outcome_dataset_manifest" in step_ids
    assert "repair_outcome_dataset_split_coverage" in step_ids
    assert "preregister_outcome_statistical_plan" in step_ids
    split_step = next(step for step in plan["steps"] if step["id"] == "repair_outcome_dataset_split_coverage")
    assert any("unassigned case_ids: case_002" in diagnostic for diagnostic in split_step["diagnostics"])


def test_capability_audit_reports_outcome_dataset_configuration(tmp_path, monkeypatch):
    assert capability_audit()["outcome_dataset"]["status"] == "not_configured"

    manifest = tmp_path / "outcomes.json"
    manifest.write_text(json.dumps(_valid_outcome_manifest()), encoding="utf-8")
    monkeypatch.setenv("SEMAS_OUTCOME_DATASET_MANIFEST", str(manifest))

    result = capability_audit()

    assert result["capabilities"]["outcome_dataset_manifest_audit"] is True
    assert result["capabilities"]["outcome_dataset_external_review_gate"] is True
    assert result["capabilities"]["outcome_dataset_frozen_holdout_gate"] is True
    assert result["capabilities"]["outcome_dataset_data_split_records_covered"] is True
    assert result["capabilities"]["outcome_dataset_label_collection_pre_analysis_gate"] is True
    assert result["outcome_dataset"]["status"] == "ready_for_review"
    assert result["outcome_dataset"]["quality_task_projection"]["projected_task_count"] == 1
    assert result["outcome_dataset"]["predictive_optimization_enabled"] is False
    assert result["outcome_dataset"]["external_review"]["reviewed"] is True
    assert result["outcome_dataset"]["data_split"]["frozen"] is True
    assert result["outcome_dataset"]["label_collection"]["collected_before_analysis"] is True
    assert result["outcome_dataset"]["label_provenance"]["provenance_complete"] is True
    assert result["outcome_dataset"]["statistical_plan"]["preregistration_complete"] is True
    assert result["audit_receipt"]["material"]["outcome_dataset"]["external_review"]["protocol_id"] == (
        "quality-validation-protocol-v1"
    )
    assert result["audit_receipt"]["material"]["outcome_dataset"]["label_provenance"]["provenance_complete"] is True
    assert result["audit_receipt"]["material"]["outcome_dataset"]["statistical_plan"][
        "preregistration_complete"
    ] is True
    assert result["audit_receipt"]["material"]["outcome_dataset"]["statistical_plan"][
        "preregistration_complete"
    ] is True
    assert "external_review_approved" in result["audit_receipt"]["material"]["outcome_dataset"]["governance_gate_ids"]


def test_capability_audit_reports_github_state_of_art_comparison():
    result = capability_audit()
    repeat = capability_audit()

    assert result["state_of_art"]["verdict"] == "advanced_agentic_framework_not_full_domain_sota"
    assert result["state_of_art"]["comparison_scope"] == "GitHub/open-source project comparison plus local capability checks."
    assert result["state_of_art"]["request_scoped_production_ready_path"] is True
    assert result["state_of_art"]["request_scoped_provenance_required"] is True
    assert result["github_comparison_receipt"]["schema_version"] == "github-comparison-receipt-v1"
    assert len(result["github_comparison_receipt"]["sha256"]) == 64
    assert result["github_comparison_receipt"] == repeat["github_comparison_receipt"]
    comparison_material = result["github_comparison_receipt"]["material"]
    assert comparison_material["matrix_sha256"] == repeat["github_comparison_receipt"]["material"]["matrix_sha256"]
    assert comparison_material["dimension_count"] == len(result["github_comparison_matrix"])
    assert comparison_material["candidate_projects"]
    assert all(item["url"].startswith("https://github.com/") for item in comparison_material["candidate_projects"])
    assert "professional_ziwei_provider_available" in comparison_material["blocking_provider_capabilities"]
    assert result["audit_receipt"]["material"]["github_comparison_receipt_sha256"] == result[
        "github_comparison_receipt"
    ]["sha256"]
    assert result["capabilities"]["request_scoped_full_external_provider_injection"] is True
    assert result["capabilities"]["request_scoped_external_provider_provenance"] is True
    assert result["capabilities"]["request_scoped_external_payload_birth_match_audit"] is True
    assert result["capabilities"]["provider_interpretation_readiness_matrix"] is True
    assert result["capabilities"]["topic_synthesis_confidence_audit"] is True
    assert result["capabilities"]["empirical_topic_confidence_gate"] is True
    assert result["capabilities"]["archive_hash_chain"] is True
    assert result["capabilities"]["genome_lineage_integrity"] is True
    assert result["capabilities"]["audited_rollback"] is True
    assert result["capabilities"]["evolution_cost_governance_manifest"] is True
    assert result["request_scoped_provider_contract"]["status"] == "ready"
    assert result["request_scoped_provider_contract"]["requires_provenance_fields"] == [
        "source",
        "version",
        "license_or_review",
    ]
    assert result["capabilities"]["classical_source_refresh_governance"] is True
    assert result["capabilities"]["classical_source_refresh_receipt"] is True
    assert result["classical_source_refresh"]["status"] == "ready"
    assert result["classical_source_refresh"]["source_count"] == 1
    assert result["classical_source_refresh"]["locked_source_count"] == 1
    assert result["capabilities"]["classical_source_refresh_configured"] is True
    assert len(result["classical_source_refresh"]["source_list_receipt"]["sha256"]) == 64
    requirement_ids = {item["id"] for item in result["implemented_requirements"]}
    assert "evolution_governance_integrity" in requirement_ids
    assert "release_governance_ledger" in requirement_ids
    assert "external_payload_birth_match_audit" in requirement_ids
    assert "provider_interpretation_readiness_matrix" in requirement_ids
    assert "topic_synthesis_confidence_audit" in requirement_ids
    assert "empirical_topic_confidence_gate" in requirement_ids
    assert "outcome_dataset_split_governance" in requirement_ids
    assert "provider_onboarding_receipt" in requirement_ids
    assert "annual_timeline_receipt" in requirement_ids
    assert "annual_timeline_topic_evidence_binding" in requirement_ids
    assert "bazi_core_profile_schema_contract" in requirement_ids
    assert "monthly_luck_receipt" in requirement_ids
    assert "monthly_luck_topic_evidence_binding" in requirement_ids
    assert "monthly_luck_public_schema_contract" in requirement_ids
    assert "astrology_profile_public_schema_contract" in requirement_ids
    assert "ziwei_qimen_public_schema_contract" in requirement_ids
    assert "rendered_reports_public_schema_contract" in requirement_ids
    assert "final_report_runtime_metadata_schema_contract" in requirement_ids
    assert "source_review_public_schema_contract" in requirement_ids
    assert "final_report_metadata_schema_contract" in requirement_ids
    assert "analyze_response_runtime_schema_validation" in requirement_ids
    assert "topic_synthesis_timing_schema_contract" in requirement_ids
    assert "auspicious_calendar_receipt" in requirement_ids
    assert "plan_compliance_receipt" in requirement_ids
    assert result["plan_compliance"]["source"] == "plan_mingli5agents.md"
    assert result["plan_compliance"]["section_count"] == 10
    assert result["plan_compliance_receipt"]["schema_version"] == "plan-compliance-receipt-v1"
    assert result["plan_compliance_receipt"] == repeat["plan_compliance_receipt"]
    assert len(result["plan_compliance_receipt"]["sha256"]) == 64
    plan_receipt = result["plan_compliance"]["source_receipt"]
    assert plan_receipt["path"] == "plan_mingli5agents.md"
    assert plan_receipt["exists"] is True
    assert plan_receipt["readable"] is True
    assert plan_receipt["encoding"] == "utf-8"
    assert plan_receipt["section_heading_count"] == 10
    assert len(plan_receipt["sha256"]) == 64
    plan_compliance_material = result["plan_compliance_receipt"]["material"]
    assert plan_compliance_material["source_receipt_sha256"] == plan_receipt["sha256"]
    assert len(plan_compliance_material["matrix_sha256"]) == 64
    assert len(plan_compliance_material["section_gap_resolution_coverage_sha256"]) == 64
    assert plan_compliance_material["section_count"] == result["plan_compliance"]["section_count"]
    assert plan_compliance_material["coverage_status"] == "covered"
    assert result["audit_receipt"]["material"]["plan_compliance"]["source_receipt"] == plan_receipt
    assert result["audit_receipt"]["material"]["plan_compliance_receipt_sha256"] == result[
        "plan_compliance_receipt"
    ]["sha256"]
    assert "3_agent_architecture" in result["plan_compliance"]["sections_with_gaps"]
    assert "6_evolution_mechanism" in result["plan_compliance"]["sections_with_gaps"]
    section_gap_coverage = result["plan_compliance"]["section_gap_resolution_coverage"]
    assert section_gap_coverage["status"] == "covered"
    assert section_gap_coverage["sections_with_unplanned_gaps"] == []
    assert section_gap_coverage["missing_plan_gap_ids"] == []
    assert section_gap_coverage["invalid_plan_gap_ids"] == []
    assert (
        result["audit_receipt"]["material"]["plan_compliance"]["section_gap_resolution_coverage"]
        == section_gap_coverage
    )
    assert result["capabilities"]["implemented_evidence_materialized"] is True
    assert result["capabilities"]["outcome_dataset_external_review_gate"] is True
    assert result["capabilities"]["outcome_dataset_frozen_holdout_gate"] is True
    assert result["capabilities"]["outcome_dataset_data_split_records_covered"] is True
    assert result["capabilities"]["outcome_dataset_label_collection_pre_analysis_gate"] is True
    assert result["capabilities"]["annual_timeline_receipt"] is True
    assert result["capabilities"]["annual_timeline_topic_evidence_binding"] is True
    assert result["capabilities"]["bazi_core_profile_schema_contract"] is True
    assert result["capabilities"]["monthly_luck_receipt"] is True
    assert result["capabilities"]["monthly_luck_topic_evidence_binding"] is True
    assert result["capabilities"]["monthly_luck_public_schema_contract"] is True
    assert result["capabilities"]["astrology_profile_public_schema_contract"] is True
    assert result["capabilities"]["ziwei_qimen_public_schema_contract"] is True
    assert result["capabilities"]["rendered_reports_public_schema_contract"] is True
    assert result["capabilities"]["final_report_runtime_metadata_schema_contract"] is True
    assert result["capabilities"]["source_review_public_schema_contract"] is True
    assert result["capabilities"]["final_report_metadata_schema_contract"] is True
    assert result["capabilities"]["analyze_response_runtime_schema_validation"] is True
    assert result["capabilities"]["topic_synthesis_timing_schema_contract"] is True
    assert result["capabilities"]["auspicious_calendar_receipt"] is True
    assert result["capabilities"]["release_manifest_governance"] is True
    assert result["capabilities"]["release_manifest_ledger_hash_chain"] is True
    assert result["capabilities"]["provider_protocol_identity_handshake"] is True
    assert result["capabilities"]["provider_ledger_latest_record_binding"] is True
    assert result["capabilities"]["provider_certification_reference_contract_coverage"] is True
    assert result["capabilities"]["provider_ledger_reference_contract_gate"] is True
    assert result["capabilities"]["provider_certification_command_fingerprint_governance"] is True
    assert result["capabilities"]["provider_example_protocol_smoke_receipt"] is True
    assert result["capabilities"]["provider_onboarding_receipt"] is True
    assert result["capabilities"]["release_manifest_ledger_latest_record_binding"] is True
    assert result["capabilities"]["release_manifest_ledger_receipt_material_binding"] is True
    assert result["capabilities"]["release_manifest_external_payload_birth_match_coverage"] is True
    assert result["capabilities"]["release_manifest_provider_action_plan_coverage"] is True
    assert result["capabilities"]["release_manifest_classical_source_receipt_coverage"] is True
    assert result["capabilities"]["release_manifest_readiness_gate_binding"] is True
    assert result["capabilities"]["blocked_capability_coverage_audit"] is True
    assert result["capabilities"]["blocked_capability_coverage_production_gate"] is True
    assert result["capabilities"]["known_gap_resolution_plan"] is True
    assert result["capabilities"]["known_gap_resolution_plan_coverage_audit"] is True
    assert result["capabilities"]["known_gap_verification_command_coverage"] is True
    assert result["capabilities"]["known_gap_command_coverage_release_binding"] is True
    assert result["capabilities"]["known_gap_handoff_bundle"] is True
    assert result["capabilities"]["known_gap_handoff_bundle_production_gate"] is True
    assert result["capabilities"]["release_manifest_ledger_readiness_gate"] is True
    assert result["capabilities"]["release_manifest_drift_gate"] is True
    assert result["evidence_materialization"]["status"] == "passed"
    assert result["evidence_materialization"]["failed_count"] == 0
    assert result["evidence_materialization"]["unchecked_count"] == 0
    assert result["evidence_materialization"]["passed_count"] == result["evidence_materialization"]["total_evidence"]
    plan_sections = {item["section"]: item for item in result["plan_compliance"]["matrix"]}
    assert plan_sections["1_project_goal"]["implemented_verified"] is True
    assert plan_sections["3_agent_architecture"]["gap_ids_verified"] is True
    assert "evolution_governance_integrity" in plan_sections["6_evolution_mechanism"]["implemented"]
    assert "release_governance_ledger" in plan_sections["6_evolution_mechanism"]["implemented"]
    assert plan_sections["6_evolution_mechanism"]["implemented_verified"] is True
    section_gap_by_section = {item["section"]: item for item in section_gap_coverage["sections"]}
    assert section_gap_by_section["3_agent_architecture"]["all_gaps_planned"] is True
    assert section_gap_coverage["invalid_gate_ids_by_gap"] == {}
    assert "provider_certification_reference_contracts_current" in section_gap_by_section["3_agent_architecture"][
        "production_gate_ids"
    ]
    assert "provider_certification_ledger_covers_domains" in section_gap_by_section["3_agent_architecture"][
        "production_gate_ids"
    ]
    assert section_gap_by_section["7_classical_sources"]["planned_gap_ids"] == ["external_classic_text_retrieval"]
    gap_plan_coverage = result["known_gap_resolution_plan_coverage"]
    assert gap_plan_coverage["coverage_complete"] is True
    assert gap_plan_coverage["known_gap_count"] == len(result["known_gaps"])
    assert gap_plan_coverage["covered_count"] == gap_plan_coverage["known_gap_count"]
    assert gap_plan_coverage["missing_gap_ids"] == []
    assert gap_plan_coverage["invalid_plan_gap_ids"] == []
    assert gap_plan_coverage["invalid_gate_ids_by_gap"] == {}
    assert gap_plan_coverage["command_validation_complete"] is True
    assert gap_plan_coverage["invalid_verification_commands_by_gap"] == {}
    assert gap_plan_coverage["invalid_verification_options_by_gap"] == {}
    assert "provider_certification_ledger_covers_domains" in gap_plan_coverage["valid_production_gate_ids"]
    assert "release-manifest" in gap_plan_coverage["valid_cli_subcommands"]
    assert "--manifest" in gap_plan_coverage["valid_cli_options_by_subcommand"]["release-manifest"]
    assert len(gap_plan_coverage["plan_coverage_sha256"]) == 64
    assert len(gap_plan_coverage["command_coverage_sha256"]) == 64
    assert len(gap_plan_coverage["audit_plan_hash"]) == 64
    assert result["audit_receipt"]["material"]["known_gap_resolution_plan_coverage"] == gap_plan_coverage
    handoff_bundle = result["known_gap_handoff_bundle"]
    assert result["audit_receipt"]["material"]["known_gap_handoff_bundle"] == handoff_bundle
    assert handoff_bundle["status"] == "ready"
    assert handoff_bundle["gap_count"] == len(result["known_gaps"])
    assert handoff_bundle["missing_handoff_gap_ids"] == []
    handoff_by_gap = {item["gap_id"]: item for item in handoff_bundle["items"]}
    assert handoff_by_gap["astronomical_ephemeris"]["required_env_vars"] == ["SEMAS_ASTROLOGY_CLI"]
    assert handoff_by_gap["huangdao_calendar_selection"]["required_provenance_env_vars"] == [
        "SEMAS_XUANZE_PROVIDER_PROVENANCE"
    ]
    assert any(
        candidate["name"] == "pyswisseph"
        for candidate in handoff_by_gap["astronomical_ephemeris"]["external_candidate_projects"]
    )
    assert "ephemeris_astrology_provider_available" in handoff_by_gap["astronomical_ephemeris"][
        "blocked_capabilities"
    ]
    assert "release_governance_ledger" in plan_sections["8_project_structure"]["implemented"]
    assert plan_sections["8_project_structure"]["implemented_verified"] is True
    assert plan_sections["10_safety_note"]["status"] == "implemented"
    matrix = {item["dimension"]: item for item in result["github_comparison_matrix"]}
    assert matrix["multi_agent_evolution"]["relative_position"] == "ahead_for_agentic_framework"
    assert matrix["ziwei_calculation"]["relative_position"] == "behind_specialized_engine"
    assert matrix["qimen_calculation"]["relative_position"] == "behind_when_no_provider_configured"
    assert matrix["western_astrology"]["relative_position"] == "behind_when_no_ephemeris_configured"
    assert "runtime protocol identity" in matrix["provider_protocol_governance"]["this_project"]
    assert matrix["release_governance"]["relative_position"] == "ahead_for_release_governance"
    assert "iztro" in matrix["ziwei_calculation"]["github_baseline"]
    assert "kinqimen" in matrix["qimen_calculation"]["github_baseline"]
    assert "pyswisseph" in matrix["western_astrology"]["github_baseline"]
    assert result["audit_receipt"]["schema_version"] == "capability-audit-receipt-v1"
    assert len(result["audit_receipt"]["sha256"]) == 64
    assert result["audit_receipt"]["sha256"] == repeat["audit_receipt"]["sha256"]
    assert result["audit_receipt"]["material"]["status"] == result["status"]
    assert result["method_surface"]["schema_version"] == "method-surface-v1"
    assert len(result["method_surface"]["sha256"]) == 64
    assert len(result["method_surface"]["material"]["domains"]["bazi"]) == 8
    assert result["audit_receipt"]["material"]["method_surface"]["sha256"] == result["method_surface"]["sha256"]
    assert result["audit_receipt"]["material"]["method_surface"]["domains"]["bazi"] == sorted(
        result["method_surface"]["material"]["domains"]["bazi"]
    )
    assert "data_split_record_coverage" in result["audit_receipt"]["material"]["outcome_dataset"]
    assert result["audit_receipt"]["material"]["provider_protocol_governance"]["protocol_hash"] == result[
        "provider_protocol_governance"
    ]["protocol_hash"]
    assert (
        result["audit_receipt"]["material"]["provider_protocol_governance"]["runtime_identity_handshake"]["ready"]
        is True
    )
    assert result["audit_receipt"]["material"]["evidence_materialization"]["passed_count"] == result[
        "evidence_materialization"
    ]["passed_count"]
    assert result["provider_example_smoke"]["status"] == "passed"
    assert result["provider_example_smoke"]["production_certification_allowed"] is False
    assert result["provider_onboarding"]["status"] == "actions_required"
    assert len(result["provider_onboarding"]["provider_onboarding_receipt"]["sha256"]) == 64
    assert result["provider_onboarding"]["provider_onboarding_receipt"]["material"]["domain_count"] == 4
    assert result["provider_onboarding"]["provider_onboarding_receipt"]["material"]["ready_domain_count"] == 0
    assert result["provider_onboarding"]["provider_onboarding_receipt"]["material"]["missing_evidence_counts"][
        "certified_provider_ledger_record"
    ] == 4
    assert result["audit_receipt"]["material"]["provider_onboarding"]["receipt_sha256"] == result[
        "provider_onboarding"
    ]["provider_onboarding_receipt"]["sha256"]
    assert result["audit_receipt"]["material"]["provider_onboarding"]["missing_evidence_counts"] == result[
        "provider_onboarding"
    ]["provider_onboarding_receipt"]["material"]["missing_evidence_counts"]
    assert all(
        {"dimension", "this_project", "github_baseline", "relative_position", "required_to_lead"} <= set(item)
        for item in result["github_comparison_matrix"]
    )
    assert all({"id", "requirement", "evidence", "status"} <= set(item) for item in result["implemented_requirements"])
    assert all(
        {"domain", "name", "url", "fit", "audit_note"} <= set(item)
        for item in result["external_integration_candidates"]
    )
    assert any(item["name"] == "pyswisseph" for item in result["external_integration_candidates"])
    assert "certified_provider_ledger_record" in result["audit_receipt"]["material"]["provider_onboarding"][
        "domain_missing_evidence"
    ]["ziwei"]
    assert "professional_qimen_provider" in result["audit_receipt"]["material"]["known_gap_ids"]
    gap_by_id = {item["id"]: item for item in result["known_gaps"]}
    gap_ids = set(gap_by_id)
    resolution_plan = {item["gap_id"]: item for item in result["known_gap_resolution_plan"]}
    assert set(resolution_plan) == gap_ids
    assert gap_by_id["professional_qimen_provider"]["status"] == "open"
    assert gap_by_id["professional_qimen_provider"]["owner_domain"] == "qimen"
    assert gap_by_id["professional_qimen_provider"]["blocking_scope"] == "environment_configured_backends"
    assert "provider_certification_ledger_covers_domains" in gap_by_id["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "ziwei_qimen_calculation_basis_audit_contract" in gap_by_id["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert any("certify-provider qimen" in command for command in gap_by_id["professional_qimen_provider"]["verification_commands"])
    assert gap_by_id["empirical_validation_dataset"]["owner_domain"] == "outcome_dataset"
    assert "outcome_dataset_data_split_records_covered" in gap_by_id["empirical_validation_dataset"][
        "production_gate_ids"
    ]
    assert "outcome_dataset_statistical_plan_preregistered" in gap_by_id["empirical_validation_dataset"][
        "production_gate_ids"
    ]
    assert all(item["id"] == item["gap_id"] for item in result["known_gap_resolution_plan"])
    assert resolution_plan["professional_qimen_provider"]["owner_domain"] == "qimen"
    assert "provider_certification_ledger_covers_domains" in resolution_plan["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_reference_contracts_current" in resolution_plan["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_command_fingerprints_current" in resolution_plan["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "ziwei_qimen_calculation_basis_audit_contract" in resolution_plan["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_reference_contracts_current" in resolution_plan["astronomical_ephemeris"][
        "production_gate_ids"
    ]
    assert "astrology_ephemeris_audit_contract" in resolution_plan["astronomical_ephemeris"][
        "production_gate_ids"
    ]
    assert "xuanze_rule_table_audit_contract" in resolution_plan["huangdao_calendar_selection"][
        "production_gate_ids"
    ]
    assert any("certify-provider qimen" in command for command in resolution_plan["professional_qimen_provider"]["verification_commands"])
    assert "classical_source_refresh_ready" in resolution_plan["external_classic_text_retrieval"][
        "production_gate_ids"
    ]
    assert "classical_source_latest_refresh_receipt_present" in resolution_plan["external_classic_text_retrieval"][
        "production_gate_ids"
    ]
    assert any(
        "classical-sources --source-list" in command
        for command in resolution_plan["external_classic_text_retrieval"]["verification_commands"]
    )
    assert "outcome_dataset_external_review_gate" in resolution_plan["empirical_validation_dataset"][
        "production_gate_ids"
    ]
    assert "outcome_dataset_data_split_records_covered" in resolution_plan["empirical_validation_dataset"][
        "production_gate_ids"
    ]
    assert "outcome_dataset_statistical_plan_preregistered" in resolution_plan["empirical_validation_dataset"][
        "production_gate_ids"
    ]
    assert any(
        "outcome-dataset --manifest" in command
        for command in resolution_plan["empirical_validation_dataset"]["verification_commands"]
    )
    assert len(result["audit_receipt"]["material"]["known_gap_resolution_plan_hash"]) == 64
    assert result["audit_receipt"]["material"]["known_gap_resolution_plan"][0]["status"] == "open"


def test_outcome_dataset_audit_unconfigured_boundary():
    result = outcome_dataset_audit()

    assert result["status"] == "not_configured"
    assert result["predictive_optimization_enabled"] is False
    assert result["quality_task_projection"]["projected_task_count"] == 0
    assert result["data_split_record_coverage"]["coverage_complete"] is False
