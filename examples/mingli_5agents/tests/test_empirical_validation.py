"""Tests for empirical validation harness boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from examples.mingli_5agents.capability_audit import capability_audit
from examples.mingli_5agents.birth_profile_review import (
    audit_birth_profile_review_manifest,
    build_birth_profile_fixture_patch_preview,
    birth_profile_review_manifest_receipt,
    build_birth_profile_import_preview,
    build_birth_profile_source_cache_audit,
    build_birth_profile_source_cache_template_preview,
    build_birth_profile_source_lookup_plan,
    build_birth_profile_source_review_workplan,
    build_birth_profile_reviewed_manifest_draft_preview,
    build_birth_profile_reviewed_manifest_file_preview,
    default_birth_profile_review_manifest_path,
)
from examples.mingli_5agents.api_core import (
    _production_resolution_plan,
    birth_profile_fixture_patch_preview,
    birth_profile_import_preview,
    birth_profile_source_cache_audit,
    birth_profile_source_cache_template_preview,
    birth_profile_source_lookup_plan,
    birth_profile_source_review_workplan,
    birth_profile_reviewed_manifest_draft_preview,
    birth_profile_reviewed_manifest_file_preview,
    birth_profile_review_status,
    evolve_case,
    production_readiness,
    schema_document,
    schema_validation_errors,
    industry_event_candidate_pool_draft_import,
    industry_event_candidate_pool_fetch_cache,
    industry_event_candidate_cases_status,
    industry_event_evidence_workplan,
    industry_event_manifest_status,
    industry_event_query_plan_status,
    industry_event_symbolic_annual_score,
    industry_event_symbolic_scoring_readiness,
    industry_event_validation_labels,
    outcome_dataset_manifest_status,
)
from examples.mingli_5agents.empirical_validation import (
    empirical_validation_cases,
    empirical_validation_tasks,
    outcome_dataset_evolution_gate,
    outcome_dataset_audit,
    run_empirical_validation,
)
from examples.mingli_5agents.industry_event_manifest import (
    audit_industry_event_manifest,
    build_industry_event_symbolic_annual_score,
    build_industry_event_symbolic_scoring_readiness,
    build_industry_event_validation_label_table,
    industry_event_manifest_receipt,
)
from examples.mingli_5agents.famous_case_validation import famous_case_records
from examples.mingli_5agents.industry_event_candidates import (
    audit_industry_event_candidate_cases,
    build_industry_event_evidence_workplan_from_symbolic_score,
    build_candidate_pool_fetch_cache_plan,
    build_candidate_pool_manifest_drafts_from_cache,
    industry_event_candidate_cases_receipt,
)
from examples.mingli_5agents.industry_event_query_plan import (
    audit_industry_event_query_plan,
    build_industry_event_collection_request_bundle,
    build_industry_event_fetch_cache_plan,
    build_industry_event_manifest_draft_from_wikidata_response,
    industry_event_query_plan_receipt,
)
from examples.mingli_5agents.outcome_dataset import audit_outcome_dataset_manifest
from examples.mingli_5agents.run_demo import bootstrap_repo


EXAMPLE_OUTCOME_MANIFEST = (
    Path(__file__).resolve().parents[1] / "providers" / "outcome_dataset_manifest_example.json"
)
EXAMPLE_INDUSTRY_EVENT_MANIFEST = (
    Path(__file__).resolve().parents[1] / "providers" / "industry_event_source_manifest_example.json"
)
EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN = (
    Path(__file__).resolve().parents[1] / "providers" / "industry_event_source_query_plan_example.json"
)
EXAMPLE_INDUSTRY_EVENT_CANDIDATES = (
    Path(__file__).resolve().parents[1] / "providers" / "industry_event_candidate_cases_example.json"
)
EXAMPLE_WIKIDATA_SPORTS_RESPONSE = (
    Path(__file__).resolve().parents[1] / "providers" / "wikidata_sports_response_example.json"
)
EXAMPLE_WIKIDATA_FILM_RESPONSE = (
    Path(__file__).resolve().parents[1] / "providers" / "wikidata_film_response_example.json"
)
EXAMPLE_WIKIDATA_MUSIC_RESPONSE = (
    Path(__file__).resolve().parents[1] / "providers" / "wikidata_music_response_example.json"
)


def materialize_cached_responses(batch_plan: dict, response_path: Path) -> None:
    payload = response_path.read_bytes()
    for plan in batch_plan.get("plans", []):
        for entry in plan.get("cache_entries", []):
            cache_path = Path(entry["cache_path"])
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(payload)


def materialize_cached_responses_by_domain(batch_plan: dict, response_paths: dict[str, Path]) -> None:
    payloads = {domain: path.read_bytes() for domain, path in response_paths.items()}
    for plan in batch_plan.get("plans", []):
        case = plan.get("case", {}) if isinstance(plan, dict) else {}
        domain = str(case.get("domain", ""))
        payload = payloads[domain]
        for entry in plan.get("cache_entries", []):
            cache_path = Path(entry["cache_path"])
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(payload)


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
    assert result["method_lineage"]["schema_version"] == "mingli-method-lineage-v1"
    assert len(result["method_lineage"]["sha256"]) == 64
    assert result["method_lineage"]["record_count"] >= 10
    assert "bazi" in result["method_lineage"]["traditions"]
    assert result["capabilities"]["method_lineage_receipt"] is True
    assert result["capabilities"]["bazi_school_debate"] is True
    assert result["capabilities"]["famous_case_validation_receipt"] is True
    assert result["capabilities"]["famous_case_school_calibration_receipt"] is True
    assert result["capabilities"]["famous_case_annual_event_calibration_receipt"] is True
    assert result["famous_case_validation"]["schema_version"] == "mingli-famous-case-validation-v2"
    assert len(result["famous_case_validation"]["sha256"]) == 64
    assert result["famous_case_validation"]["case_count"] >= 12
    assert {"体育", "影视", "歌手"}.issubset(set(result["famous_case_validation"]["domains"]))
    assert {"甲甲", "甲", "乙"}.issubset(set(result["famous_case_validation"]["ratings"]))
    birth_source_quality = result["famous_case_validation"]["birth_source_quality"]
    assert birth_source_quality["schema_version"] == "famous-case-birth-source-quality-v1"
    assert birth_source_quality["case_count"] == result["famous_case_validation"]["case_count"]
    assert birth_source_quality["source_counts"] == {"Astro-Databank": result["famous_case_validation"]["case_count"]}
    assert birth_source_quality["rating_counts"]["甲甲"] >= 1
    assert birth_source_quality["rating_counts"]["甲"] >= 1
    assert birth_source_quality["birth_time_format_invalid_case_ids"] == []
    assert birth_source_quality["birth_time_format_valid_count"] == result["famous_case_validation"]["case_count"]
    assert "chiang_kai_shek" in birth_source_quality["caution_case_ids"]
    assert "arthur_ashe" in birth_source_quality["hour_pillar_scoring_eligible_case_ids"]
    assert (
        result["famous_case_validation"]["material"]["birth_source_quality"]
        == result["famous_case_validation"]["birth_source_quality"]
    )
    fixture_domain_coverage = {
        item["domain"]: item for item in result["famous_case_validation"]["domain_coverage"]
    }
    for domain in ["体育", "影视", "歌手"]:
        assert fixture_domain_coverage[domain]["case_count"] >= 3
        assert fixture_domain_coverage[domain]["event_count"] >= 10
        assert fixture_domain_coverage[domain]["sources"] == ["Astro-Databank"]
        assert fixture_domain_coverage[domain]["event_topics"]
    assert {"sports_peak", "health_risk"}.issubset(
        set(fixture_domain_coverage["体育"]["event_topics"])
    )
    assert {"public_fame", "relationship"}.issubset(
        set(fixture_domain_coverage["影视"]["event_topics"])
    )
    assert {"career_project", "public_controversy"}.issubset(
        set(fixture_domain_coverage["歌手"]["event_topics"])
    )
    assert (
        result["famous_case_validation"]["material"]["domain_coverage"]
        == result["famous_case_validation"]["domain_coverage"]
    )
    assert result["famous_case_school_calibration"]["schema_version"] == "mingli-famous-case-school-calibration-v1"
    assert len(result["famous_case_school_calibration"]["sha256"]) == 64
    assert result["famous_case_school_calibration"]["fixture_sha256"] == result["famous_case_validation"]["sha256"]
    assert result["famous_case_school_calibration"]["case_count"] == result["famous_case_validation"]["case_count"]
    assert result["famous_case_school_calibration"]["mean_topic_recall"] > 0
    assert {"体育", "影视", "歌手"}.issubset(
        {item["domain"] for item in result["famous_case_school_calibration"]["domain_summary"]}
    )
    assert result["famous_case_annual_event_calibration"]["schema_version"] == (
        "mingli-famous-case-annual-event-calibration-v1"
    )
    assert len(result["famous_case_annual_event_calibration"]["sha256"]) == 64
    assert result["famous_case_annual_event_calibration"]["fixture_sha256"] == result["famous_case_validation"]["sha256"]
    assert result["famous_case_annual_event_calibration"]["case_count"] == result["famous_case_validation"]["case_count"]
    annual_birth_quality = result["famous_case_annual_event_calibration"]["birth_source_quality_summary"]
    assert annual_birth_quality["schema_version"] == "famous-case-annual-birth-source-quality-summary-v1"
    assert annual_birth_quality["case_count"] == result["famous_case_annual_event_calibration"]["case_count"]
    assert annual_birth_quality["hour_pillar_scoring_eligible_case_count"] == birth_source_quality[
        "hour_pillar_scoring_eligible_case_count"
    ]
    assert annual_birth_quality["caution_case_ids"] == birth_source_quality["caution_case_ids"]
    assert annual_birth_quality["caution_event_count"] > 0
    assert annual_birth_quality["eligible_event_count"] > annual_birth_quality["caution_event_count"]
    assert 0 < annual_birth_quality["eligible_event_rate"] <= 1
    assert result["famous_case_annual_event_calibration"]["event_count"] > 0
    assert result["famous_case_annual_event_calibration"]["negative_year_count"] > result[
        "famous_case_annual_event_calibration"
    ]["event_count"]
    assert result["famous_case_annual_event_calibration"]["false_positive_count"] >= 0
    assert result["famous_case_annual_event_calibration"]["strict_exact_hit_count"] >= 0
    assert result["famous_case_annual_event_calibration"]["strict_false_positive_count"] >= 0
    assert 0 <= result["famous_case_annual_event_calibration"]["exact_precision"] <= 1
    assert 0 <= result["famous_case_annual_event_calibration"]["false_positive_rate"] <= 1
    assert 0 <= result["famous_case_annual_event_calibration"]["strict_exact_precision"] <= 1
    assert 0 <= result["famous_case_annual_event_calibration"]["strict_false_positive_rate"] <= 1
    assert result["famous_case_annual_event_calibration"]["strict_false_positive_rate"] <= result[
        "famous_case_annual_event_calibration"
    ]["false_positive_rate"]
    assert result["famous_case_annual_event_calibration"]["window_hit_rate"] >= result[
        "famous_case_annual_event_calibration"
    ]["exact_hit_rate"]
    assert {"体育", "影视", "歌手"}.issubset(
        {item["domain"] for item in result["famous_case_annual_event_calibration"]["domain_summary"]}
    )
    domain_topic_summary = result["famous_case_annual_event_calibration"]["domain_topic_summary"]
    assert domain_topic_summary
    domain_topic_keys = {(item["domain"], item["event_topic"]) for item in domain_topic_summary}
    assert ("体育", "sports_peak") in domain_topic_keys
    assert ("影视", "relationship") in domain_topic_keys
    assert ("歌手", "public_fame") in domain_topic_keys
    sports_peak_domain = next(
        item for item in domain_topic_summary if item["domain"] == "体育" and item["event_topic"] == "sports_peak"
    )
    assert sports_peak_domain["case_count"] == 3
    assert sports_peak_domain["event_count"] >= 10
    assert 0 <= sports_peak_domain["strict_exact_precision"] <= 1
    assert 0 <= sports_peak_domain["strict_false_positive_rate"] <= 1
    assert "roger_federer" in sports_peak_domain["case_ids"]
    domain_topic_queue = result["famous_case_annual_event_calibration"]["domain_topic_refinement_queue"]
    assert domain_topic_queue
    domain_topic_task_keys = {(item["domain"], item["event_topic"]) for item in domain_topic_queue}
    assert ("影视", "public_fame") in domain_topic_task_keys
    assert ("影视", "career_project") in domain_topic_task_keys
    film_fame_task = next(
        item for item in domain_topic_queue if item["domain"] == "影视" and item["event_topic"] == "public_fame"
    )
    assert film_fame_task["task_type"] == "add_domain_specific_evidence"
    assert film_fame_task["event_count"] >= 3
    assert film_fame_task["next_evidence_to_add"]
    assert any("film-or-television release marker" in item for item in film_fame_task["next_evidence_to_add"])
    domain_topic_variant_sweep = result["famous_case_annual_event_calibration"]["domain_topic_variant_sweep"]
    assert domain_topic_variant_sweep
    assert all(item["selected"] is False for item in domain_topic_variant_sweep)
    film_fame_variants = [
        item
        for item in domain_topic_variant_sweep
        if item["domain"] == "影视" and item["event_topic"] == "public_fame"
    ]
    assert {item["variant"] for item in film_fame_variants} == {
        "current_strict",
        "expression_visibility_with_support",
        "expression_visibility_or_major_luck",
        "fixture_industry_fame_marker",
    }
    current_film_fame = next(item for item in film_fame_variants if item["variant"] == "current_strict")
    assert current_film_fame["strict_exact_hit_rate"] == 0.0
    assert current_film_fame["strict_exact_precision"] == 0.0
    industry_film_fame = next(item for item in film_fame_variants if item["variant"] == "fixture_industry_fame_marker")
    assert industry_film_fame["strict_exact_hit_rate"] == 1.0
    assert industry_film_fame["strict_exact_precision"] == 1.0
    assert industry_film_fame["strict_false_positive_rate"] == 0.0
    assert industry_film_fame["selected"] is False
    assert all("predictive validity" not in item["selection_basis"] for item in domain_topic_variant_sweep)
    assert all("cannot be promoted to prediction rules" in item["selection_basis"] for item in domain_topic_variant_sweep)
    annual_topics = {item["event_topic"] for item in result["famous_case_annual_event_calibration"]["topic_summary"]}
    assert {"sports_peak", "public_fame", "health_risk", "relationship"}.issubset(annual_topics)
    for item in result["famous_case_annual_event_calibration"]["topic_summary"]:
        assert item["event_count"] > 0
        assert 0 <= item["exact_precision"] <= 1
        assert 0 <= item["strict_exact_precision"] <= 1
    first_case_score = result["famous_case_annual_event_calibration"]["case_scores"][0]
    assert first_case_score["birth_source_quality"]["schema_version"] == "famous-case-birth-source-quality-case-v1"
    assert first_case_score["birth_source_quality"]["birth_time_format_valid"] is True
    assert first_case_score["hour_pillar_scoring_eligible"] == first_case_score["birth_source_quality"][
        "hour_pillar_scoring_eligible"
    ]
    assert "event_subtype" in first_case_score["events"][0]
    assert "industry_event_evidence" in first_case_score["events"][0]
    first_industry_evidence = first_case_score["events"][0]["industry_event_evidence"]
    assert first_industry_evidence["has_domain_specific_evidence"] is True
    assert first_industry_evidence["boundary"].endswith("calibration only.")
    first_event_evidence = first_case_score["events"][0]["event_evidence"]
    assert "ten_gods" in first_event_evidence
    assert "major_luck_active" in first_event_evidence
    assert "natal_activation" in first_event_evidence
    assert "movement_signal" in first_event_evidence
    assert "branch_clashes" in first_event_evidence
    assert "career_signal_strength" in first_event_evidence
    assert "career_launch_signal" in first_event_evidence
    assert "role_power_signal" in first_event_evidence
    assert "role_transition_signal" in first_event_evidence
    assert "event_markers" in first_event_evidence
    assert "useful_state" in first_event_evidence
    refinement_queue = result["famous_case_annual_event_calibration"]["rule_refinement_queue"]
    assert refinement_queue
    assert any(item["priority"] in {"medium", "high"} for item in refinement_queue)
    assert all(item["recommended_evidence"] for item in refinement_queue)
    variant_sweep = result["famous_case_annual_event_calibration"]["rule_variant_sweep"]
    assert variant_sweep
    assert any(item["event_topic"] == "career_project" and item["selected"] for item in variant_sweep)
    assert any(item["event_topic"] == "migration" and item["selected"] for item in variant_sweep)
    assert any(item["event_topic"] == "career_power" and item["selected"] for item in variant_sweep)
    assert any(item["event_topic"] == "study_exam" and item["selected"] for item in variant_sweep)
    migration_legacy = next(
        item for item in variant_sweep if item["event_topic"] == "migration" and item["variant"] == "legacy_any_clash"
    )
    migration_selected = next(
        item for item in variant_sweep if item["event_topic"] == "migration" and item["selected"]
    )
    assert migration_selected["strict_false_positive_rate"] <= migration_legacy["strict_false_positive_rate"]
    career_power_selected = next(
        item for item in variant_sweep if item["event_topic"] == "career_power" and item["selected"]
    )
    career_power_broad = next(
        item for item in variant_sweep if item["event_topic"] == "career_power" and item["variant"] == "broad_authority_transition"
    )
    assert career_power_selected["strict_false_positive_rate"] <= career_power_broad["strict_false_positive_rate"]
    study_exam_selected = next(
        item for item in variant_sweep if item["event_topic"] == "study_exam" and item["selected"]
    )
    study_exam_broad = next(
        item for item in variant_sweep if item["event_topic"] == "study_exam" and item["variant"] == "broad_resource_authority"
    )
    assert study_exam_selected["strict_false_positive_rate"] <= study_exam_broad["strict_false_positive_rate"]
    evolution_task_plan = result["famous_case_annual_event_calibration"]["evolution_task_plan"]
    assert evolution_task_plan
    task_topics = {item["event_topic"] for item in evolution_task_plan}
    assert {"career_power", "study_exam"}.issubset(task_topics)
    assert any(item["task_type"] == "add_specific_evidence" for item in evolution_task_plan)
    assert all(item["next_evidence_to_add"] for item in evolution_task_plan)
    assert all(item["acceptance_criteria"] for item in evolution_task_plan)
    public_fame_task = next(item for item in evolution_task_plan if item["event_topic"] == "public_fame")
    assert public_fame_task["task_type"] == "refine_precision"
    assert public_fame_task["subtype_coverage_rate"] == 1.0
    assert public_fame_task["default_subtype_count"] == 0
    relationship_task = next(item for item in evolution_task_plan if item["event_topic"] == "relationship")
    assert relationship_task["task_type"] == "refine_precision"
    assert relationship_task["subtype_coverage_rate"] == 1.0
    assert relationship_task["default_subtype_count"] == 0
    public_controversy_task = next(
        item for item in evolution_task_plan if item["event_topic"] == "public_controversy"
    )
    assert public_controversy_task["task_type"] == "add_specific_evidence"
    assert public_controversy_task["subtype_coverage_rate"] == 1.0
    assert public_controversy_task["default_subtype_count"] == 0
    sports_peak_task = next(item for item in evolution_task_plan if item["event_topic"] == "sports_peak")
    assert sports_peak_task["task_type"] == "reduce_false_positive"
    assert sports_peak_task["subtype_coverage_rate"] == 1.0
    assert sports_peak_task["default_subtype_count"] == 0
    health_risk_task = next(item for item in evolution_task_plan if item["event_topic"] == "health_risk")
    assert health_risk_task["task_type"] == "refine_precision"
    assert health_risk_task["subtype_coverage_rate"] == 1.0
    assert health_risk_task["default_subtype_count"] == 0
    if not any(item["task_type"] == "expand_subtypes" for item in evolution_task_plan):
        assert all(
            item["event_count"] < 3 or item["subtype_coverage_rate"] >= 0.5
            for item in evolution_task_plan
        )
    subtype_summary = result["famous_case_annual_event_calibration"]["event_subtype_summary"]
    assert subtype_summary
    career_power_subtypes = next(item for item in subtype_summary if item["event_topic"] == "career_power")
    assert career_power_subtypes["explicit_subtype_count"] == career_power_subtypes["event_count"]
    assert "command_succession" in career_power_subtypes["subtype_counts"]
    career_project_subtypes = next(item for item in subtype_summary if item["event_topic"] == "career_project")
    assert career_project_subtypes["subtype_coverage_rate"] >= 0.9
    assert "landmark_album_release" in career_project_subtypes["subtype_counts"]
    assert "grand_slam_title" in career_project_subtypes["subtype_counts"]
    public_fame_subtypes = next(item for item in subtype_summary if item["event_topic"] == "public_fame")
    assert public_fame_subtypes["subtype_coverage_rate"] == 1.0
    assert "landmark_album_global_fame" in public_fame_subtypes["subtype_counts"]
    assert "olympic_record_public_fame" in public_fame_subtypes["subtype_counts"]
    industry_summary = result["famous_case_annual_event_calibration"]["industry_event_evidence_summary"]
    assert industry_summary
    film_fame_industry = next(
        item for item in industry_summary if item["industry"] == "film_or_television" and item["event_topic"] == "public_fame"
    )
    assert film_fame_industry["event_count"] >= 10
    assert film_fame_industry["domain_specific_evidence_rate"] == 1.0
    assert film_fame_industry["release_marker_count"] > 0
    assert film_fame_industry["award_or_recognition_marker_count"] > 0
    film_project_industry = next(
        item
        for item in industry_summary
        if item["industry"] == "film_or_television" and item["event_topic"] == "career_project"
    )
    assert film_project_industry["domain_specific_evidence_rate"] == 1.0
    music_fame_industry = next(
        item for item in industry_summary if item["industry"] == "music" and item["event_topic"] == "public_fame"
    )
    assert music_fame_industry["commercial_or_chart_marker_count"] > 0
    sports_peak_industry = next(
        item for item in industry_summary if item["industry"] == "sports" and item["event_topic"] == "sports_peak"
    )
    assert sports_peak_industry["competition_marker_count"] == sports_peak_industry["event_count"]
    industry_source_coverage = result["famous_case_annual_event_calibration"]["industry_event_source_coverage"]
    assert industry_source_coverage["status"] == "needs_external_event_source"
    assert industry_source_coverage["positive_event_industry_evidence_source"] == "fixture_event_subtypes"
    assert industry_source_coverage["negative_year_count"] > result["famous_case_annual_event_calibration"]["event_count"]
    assert industry_source_coverage["industry_negative_label_count"] == 0
    assert industry_source_coverage["industry_negative_label_coverage_rate"] == 0.0
    assert industry_source_coverage["blocking_rule_promotion"] is True
    assert "source_url" in industry_source_coverage["provider_contract_required_fields"]
    assert any(
        item["domain"] == "影视" and item["event_topic"] == "public_fame"
        for item in industry_source_coverage["required_domain_topic_slices"]
    )
    relationship_subtypes = next(item for item in subtype_summary if item["event_topic"] == "relationship")
    assert relationship_subtypes["subtype_coverage_rate"] == 1.0
    assert "celebrity_marriage" in relationship_subtypes["subtype_counts"]
    assert "divorce_or_relationship_end" in relationship_subtypes["subtype_counts"]
    controversy_subtypes = next(item for item in subtype_summary if item["event_topic"] == "public_controversy")
    assert controversy_subtypes["subtype_coverage_rate"] == 1.0
    assert "criminal_allegation_public_controversy" in controversy_subtypes["subtype_counts"]
    assert "religious_media_controversy" in controversy_subtypes["subtype_counts"]
    sports_peak_subtypes = next(item for item in subtype_summary if item["event_topic"] == "sports_peak")
    assert sports_peak_subtypes["subtype_coverage_rate"] == 1.0
    assert "olympic_record_gold_peak" in sports_peak_subtypes["subtype_counts"]
    assert "comeback_grand_slam_title" in sports_peak_subtypes["subtype_counts"]
    health_risk_subtypes = next(item for item in subtype_summary if item["event_topic"] == "health_risk")
    assert health_risk_subtypes["subtype_coverage_rate"] == 1.0
    assert "acute_drug_related_death" in health_risk_subtypes["subtype_counts"]
    assert "sports_injury_surgery" in health_risk_subtypes["subtype_counts"]
    career_power_task = next(item for item in evolution_task_plan if item["event_topic"] == "career_power")
    assert career_power_task["selected_variant"] == "current_role_power"
    assert any(
        item.get("variant") == "authority_peer_resource"
        for item in career_power_task["rejected_variant_metrics"]
    )
    assert any(
        item.get("variant") == "role_transition_marker"
        for item in career_power_task["rejected_variant_metrics"]
    )
    assert result["audit_receipt"]["material"]["method_lineage"]["sha256"] == result["method_lineage"]["sha256"]
    assert (
        result["audit_receipt"]["material"]["famous_case_validation"]["sha256"]
        == result["famous_case_validation"]["sha256"]
    )
    assert (
        result["audit_receipt"]["material"]["famous_case_school_calibration"]["sha256"]
        == result["famous_case_school_calibration"]["sha256"]
    )
    assert (
        result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["sha256"]
        == result["famous_case_annual_event_calibration"]["sha256"]
    )
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["exact_precision"] == result[
        "famous_case_annual_event_calibration"
    ]["exact_precision"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"][
        "strict_exact_precision"
    ] == result["famous_case_annual_event_calibration"]["strict_exact_precision"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["topic_summary"] == result[
        "famous_case_annual_event_calibration"
    ]["topic_summary"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["domain_topic_summary"] == result[
        "famous_case_annual_event_calibration"
    ]["domain_topic_summary"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"][
        "domain_topic_refinement_queue"
    ] == result["famous_case_annual_event_calibration"]["domain_topic_refinement_queue"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"][
        "domain_topic_variant_sweep"
    ] == result["famous_case_annual_event_calibration"]["domain_topic_variant_sweep"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"][
        "industry_event_evidence_summary"
    ] == result["famous_case_annual_event_calibration"]["industry_event_evidence_summary"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"][
        "industry_event_source_coverage"
    ] == result["famous_case_annual_event_calibration"]["industry_event_source_coverage"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["event_subtype_summary"] == result[
        "famous_case_annual_event_calibration"
    ]["event_subtype_summary"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["rule_refinement_queue"] == result[
        "famous_case_annual_event_calibration"
    ]["rule_refinement_queue"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["rule_variant_sweep"] == result[
        "famous_case_annual_event_calibration"
    ]["rule_variant_sweep"]
    assert result["audit_receipt"]["material"]["famous_case_annual_event_calibration"]["evolution_task_plan"] == result[
        "famous_case_annual_event_calibration"
    ]["evolution_task_plan"]
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
    assert any(item["domain"] == "industry_events" for item in result["external_integration_candidates"])
    assert any(
        item["name"] == "IMDb Non-Commercial Datasets"
        for item in result["external_integration_candidates"]
    )
    assert any(item["name"] == "MusicBrainz Database" for item in result["external_integration_candidates"])
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
    assert gap_by_id["industry_event_source_provider"]["owner_domain"] == "industry_events"
    assert gap_by_id["industry_event_source_provider"]["blocking_scope"] == (
        "externally_reviewed_industry_event_manifest"
    )
    assert "outcome_dataset_external_review_gate" in gap_by_id["industry_event_source_provider"][
        "production_gate_ids"
    ]
    assert any(
        "industry_event_source_manifest_example.json" in command
        for command in gap_by_id["industry_event_source_provider"]["verification_commands"]
    )
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
    assert resolution_plan["industry_event_source_provider"]["owner_domain"] == "industry_events"
    assert "outcome_dataset_label_collection_pre_analysis_gate" in resolution_plan[
        "industry_event_source_provider"
    ]["production_gate_ids"]
    assert any(
        "industry_event_source_manifest_example.json" in command
        for command in resolution_plan["industry_event_source_provider"]["verification_commands"]
    )
    assert handoff_by_gap["industry_event_source_provider"]["owner_domain"] == "industry_events"
    assert handoff_by_gap["industry_event_source_provider"]["handoff_ready"] is True
    assert any(
        candidate["name"] == "Wikidata Query Service"
        for candidate in handoff_by_gap["industry_event_source_provider"]["external_candidate_projects"]
    )
    assert len(result["audit_receipt"]["material"]["known_gap_resolution_plan_hash"]) == 64
    assert result["audit_receipt"]["material"]["known_gap_resolution_plan"][0]["status"] == "open"


def test_industry_event_source_manifest_example_receipt():
    assert EXAMPLE_INDUSTRY_EVENT_MANIFEST.exists()
    result = capability_audit()
    receipt = result["industry_event_source_manifest_example"]
    material = receipt["material"]
    audit_material = result["audit_receipt"]["material"]["industry_event_source_manifest_example"]

    assert result["capabilities"]["industry_event_source_manifest_example"] is True
    assert receipt["schema_version"] == "industry-event-source-manifest-example-receipt-v1"
    assert len(receipt["sha256"]) == 64
    assert material["status"] == "ready_example"
    assert material["path"].endswith("industry_event_source_manifest_example.json")
    assert material["production_evidence"] is False
    assert material["externally_reviewed"] is False
    assert material["record_count"] == 6
    assert material["positive_event_count"] == 3
    assert material["negative_event_count"] == 3
    assert material["domains"] == ["film", "music", "sports"]
    assert material["industries"] == ["film_or_television", "music", "sports"]
    assert material["has_positive_and_negative_examples"] is True
    assert material["all_records_have_required_fields"] is True
    assert set(material["candidate_source_names"]) >= {
        "IMDb Non-Commercial Datasets",
        "MusicBrainz Database",
        "Olympedia",
        "Wikidata Query Service",
    }
    assert audit_material["sha256"] == receipt["sha256"]
    assert audit_material["content_hash"] == material["content_hash"]
    assert audit_material["production_evidence"] is False
    assert audit_material["externally_reviewed"] is False


def test_industry_event_source_query_plan_example_receipt():
    assert EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN.exists()
    result = capability_audit()
    receipt = result["industry_event_source_query_plan_example"]
    material = receipt["material"]
    audit_material = result["audit_receipt"]["material"]["industry_event_source_query_plan_example"]

    assert result["capabilities"]["industry_event_source_query_plan_example"] is True
    assert receipt["schema_version"] == "industry-event-source-query-plan-example-receipt-v1"
    assert len(receipt["sha256"]) == 64
    assert material["status"] == "ready_example"
    assert material["path"].endswith("industry_event_source_query_plan_example.json")
    assert material["source_id"] == "wikidata_query_service"
    assert material["endpoint_url"] == "https://query.wikidata.org/sparql"
    assert material["template_count"] == 3
    assert material["domains"] == ["film", "music", "sports"]
    assert material["required_manifest_fields_mapped"] is True
    assert material["collection_ready"] is False
    assert material["externally_reviewed"] is False
    assert audit_material["sha256"] == receipt["sha256"]
    assert audit_material["content_hash"] == material["content_hash"]
    assert audit_material["collection_ready"] is False


def test_industry_event_candidate_cases_example_receipt():
    assert EXAMPLE_INDUSTRY_EVENT_CANDIDATES.exists()
    result = capability_audit()
    receipt = result["industry_event_candidate_cases_example"]
    material = receipt["material"]
    audit_material = result["audit_receipt"]["material"]["industry_event_candidate_cases_example"]

    assert result["capabilities"]["industry_event_candidate_cases_example"] is True
    assert receipt["schema_version"] == "industry-event-candidate-cases-example-receipt-v1"
    assert len(receipt["sha256"]) == 64
    assert material["status"] == "ready_example"
    assert material["path"].endswith("industry_event_candidate_cases_example.json")
    assert material["candidate_count"] == 9
    assert material["domain_counts"] == {"film": 3, "music": 3, "sports": 3}
    assert material["domains"] == ["film", "music", "sports"]
    assert material["production_ready"] is False
    assert material["externally_reviewed"] is False
    assert audit_material["sha256"] == receipt["sha256"]
    assert audit_material["candidate_count"] == 9
    assert audit_material["domains"] == ["film", "music", "sports"]


def test_industry_event_cross_domain_fixture_import_receipt():
    result = capability_audit()
    receipt = result["industry_event_cross_domain_fixture_import"]
    material = receipt["material"]
    audit_material = result["audit_receipt"]["material"]["industry_event_cross_domain_fixture_import"]

    assert result["capabilities"]["industry_event_cross_domain_fixture_import"] is True
    assert receipt["schema_version"] == "industry-event-cross-domain-fixture-import-receipt-v1"
    assert len(receipt["sha256"]) == 64
    assert material["status"] == "ready_example"
    assert material["offline_only"] is True
    assert material["production_evidence"] is False
    assert material["candidate_count"] == 9
    assert material["draft_count"] == 9
    assert material["positive_record_count"] == 9
    assert material["negative_record_count"] == 273
    assert material["record_count"] == 282
    assert material["domains"] == ["film", "music", "sports"]
    assert material["cross_domain_coverage_gate_passed"] is True
    readiness = material["symbolic_scoring_readiness_summary"]
    assert readiness["status"] == "ready_for_symbolic_scoring"
    assert readiness["label_count"] == 282
    assert readiness["ready_label_count"] == 25
    assert readiness["blocked_label_count"] == 257
    assert readiness["case_count"] == 9
    assert readiness["ready_case_count"] == 1
    assert readiness["blocked_case_count"] == 8
    assert readiness["ready_case_ids"] == ["roger_federer"]
    assert readiness["missing_birth_profile_case_ids"] == [
        "beyonce",
        "jackie_chan",
        "jay_chou",
        "meryl_streep",
        "michael_jordan",
        "serena_williams",
        "taylor_swift",
        "tom_hanks",
    ]
    assert len(readiness["symbolic_scoring_readiness_receipt_sha256"]) == 64
    assert any(item["domain"] == "film" and item["ready_label_count"] == 0 for item in readiness["domain_topic_summary"])
    assert any(item["domain"] == "music" and item["ready_label_count"] == 0 for item in readiness["domain_topic_summary"])
    assert any(item["domain"] == "sports" and item["ready_label_count"] == 25 for item in readiness["domain_topic_summary"])
    assert len(readiness["symbolic_annual_score_receipt_sha256"]) == 64
    task_plan = readiness["birth_profile_completion_task_plan"]
    assert [item["task_id"] for item in task_plan] == [
        "industry-symbolic-film-public_fame-add_reviewed_birth_profiles",
        "industry-symbolic-music-public_fame-add_reviewed_birth_profiles",
        "industry-symbolic-sports-sports_peak-add_reviewed_birth_profiles",
    ]
    assert all(item["priority"] == "high" for item in task_plan)
    assert all(item["task_type"] == "add_reviewed_birth_profiles" for item in task_plan)
    assert task_plan[0]["blocked_case_ids"] == ["jackie_chan", "meryl_streep", "tom_hanks"]
    assert task_plan[1]["blocked_case_ids"] == ["beyonce", "jay_chou", "taylor_swift"]
    assert task_plan[2]["blocked_case_ids"] == ["michael_jordan", "serena_williams"]
    assert sum(item["blocked_label_count"] for item in task_plan) == 257
    assert all(item["acceptance_criteria"] for item in task_plan)
    assert len(readiness["evidence_workplan_receipt_sha256"]) == 64
    workplan_summary = readiness["birth_profile_completion_workplan_summary"]
    assert workplan_summary["status"] == "ready_for_review"
    assert workplan_summary["valid"] is True
    assert workplan_summary["deferred_task_count"] == 3
    assert workplan_summary["readiness_status"] == "blocked"
    assert workplan_summary["deferred_blocked_gate_count"] == 3
    assert workplan_summary["deferred_failed_integrity_check_count"] == 0
    summaries_by_domain = {item["domain"]: item for item in workplan_summary["deferred_task_summaries"]}
    assert summaries_by_domain["film"]["local_birth_profile_suggestion_case_ids"] == [
        "bruce_lee",
        "lucille_ball",
        "marilyn_monroe",
    ]
    assert summaries_by_domain["music"]["local_birth_profile_suggestion_case_ids"] == [
        "aretha_franklin",
        "madonna",
        "michael_jackson",
    ]
    assert summaries_by_domain["sports"]["local_birth_profile_suggestion_case_ids"] == [
        "arthur_ashe",
        "mark_spitz",
        "roger_federer",
    ]
    assert all(item["completion_work_order_status"] == "ready_for_human_review" for item in summaries_by_domain.values())
    assert all(item["gate_summary_status"] == "blocked" for item in summaries_by_domain.values())
    review_manifest = readiness["birth_profile_review_manifest_summary"]
    assert review_manifest["status"] == "ready_for_review"
    assert review_manifest["valid"] is True
    assert review_manifest["production_evidence"] is False
    assert review_manifest["request_count"] == 8
    assert review_manifest["case_count"] == 8
    assert review_manifest["domains"] == ["film", "music", "sports"]
    assert review_manifest["blocked_label_count"] == readiness["blocked_label_count"]
    assert review_manifest["ready_for_import"] is False
    assert review_manifest["failures"] == []
    assert len(readiness["birth_profile_review_manifest_receipt_sha256"]) == 64
    source_workplan = readiness["birth_profile_source_review_workplan_summary"]
    assert source_workplan["status"] == "ready_for_human_source_review"
    assert source_workplan["valid"] is True
    assert source_workplan["would_fetch_live_sources"] is False
    assert source_workplan["would_write_review_manifest"] is False
    assert source_workplan["request_count"] == 8
    assert source_workplan["work_item_count"] == 8
    assert source_workplan["review_progress_summary"]["review_status_counts"]["not_started"] == 8
    assert source_workplan["review_progress_summary"]["domain_work_item_counts"] == {
        "film": 3,
        "music": 3,
        "sports": 2,
    }
    assert source_workplan["field_gap_summary"]["missing_field_counts"]["birth_time"] == 8
    assert source_workplan["source_review_gate_passed"] is False
    assert source_workplan["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_source_review_workplan_receipt_sha256"]) == 64
    source_lookup = readiness["birth_profile_source_lookup_plan_summary"]
    assert source_lookup["status"] == "ready_for_manual_lookup"
    assert source_lookup["valid"] is True
    assert source_lookup["would_fetch_live_sources"] is False
    assert source_lookup["would_write_cache"] is False
    assert source_lookup["would_write_review_manifest"] is False
    assert source_lookup["lookup_item_count"] == 8
    assert source_lookup["query_count"] == 16
    assert source_lookup["source_family_count"] == 5
    assert source_lookup["source_family_catalog_bound"] is True
    assert source_lookup["birth_time_source_policy_bound"] is True
    assert source_lookup["identity_anchor_birth_time_disallowed"] is True
    assert source_lookup["lookup_gate_passed"] is False
    assert source_lookup["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_source_lookup_plan_receipt_sha256"]) == 64
    template_preview = readiness["birth_profile_source_cache_template_preview_summary"]
    assert template_preview["status"] == "ready_for_manual_cache_fill"
    assert template_preview["valid"] is True
    assert template_preview["would_fetch_live_sources"] is False
    assert template_preview["would_write_cache"] is False
    assert template_preview["would_import_profiles"] is False
    assert template_preview["template_count"] == 16
    assert template_preview["template_preview_gate_passed"] is False
    assert template_preview["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_source_cache_template_preview_receipt_sha256"]) == 64
    family_probe = readiness["birth_profile_source_family_cache_enforcement_summary"]
    assert family_probe["status"] == "passed"
    assert family_probe["valid"] is True
    assert family_probe["probe_executed"] is True
    assert family_probe["identity_anchor_birth_time_rejected"] is True
    assert family_probe["accepted_cache_count_after_probe"] == 0
    assert family_probe["probe_source_family_id"] == "wikidata_identity_anchor"
    assert family_probe["failure_contains_birth_time_policy"] is True
    substantive_probe = readiness["birth_profile_substantive_evidence_cache_enforcement_summary"]
    assert substantive_probe["status"] == "passed"
    assert substantive_probe["valid"] is True
    assert substantive_probe["probe_executed"] is True
    assert substantive_probe["metadata_only_reviewed_cache_rejected"] is True
    assert substantive_probe["accepted_cache_count_after_probe"] == 0
    assert substantive_probe["probe_source_family_id"] == "rated_birth_time_source"
    assert substantive_probe["failure_contains_substantive_birth_policy"] is True
    source_cache = readiness["birth_profile_source_cache_audit_summary"]
    assert source_cache["status"] == "waiting_for_manual_cache"
    assert source_cache["valid"] is True
    assert source_cache["would_fetch_live_sources"] is False
    assert source_cache["would_write_cache"] is False
    assert source_cache["would_write_review_manifest"] is False
    assert source_cache["would_import_profiles"] is False
    assert source_cache["expected_cache_count"] == 16
    assert source_cache["missing_cache_count"] == 16
    assert source_cache["accepted_cache_count"] == 0
    assert source_cache["cache_audit_gate_passed"] is False
    assert source_cache["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_source_cache_audit_receipt_sha256"]) == 64
    reviewed_draft = readiness["birth_profile_reviewed_manifest_draft_preview_summary"]
    assert reviewed_draft["status"] == "blocked_waiting_for_complete_source_cache"
    assert reviewed_draft["valid"] is True
    assert reviewed_draft["would_write_review_manifest"] is False
    assert reviewed_draft["would_import_profiles"] is False
    assert reviewed_draft["draft_ready_for_human_approval"] is False
    assert reviewed_draft["review_request_count"] == 8
    assert reviewed_draft["complete_review_request_count"] == 0
    assert reviewed_draft["draft_gate_passed"] is False
    assert reviewed_draft["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_reviewed_manifest_draft_preview_receipt_sha256"]) == 64
    reviewed_file = readiness["birth_profile_reviewed_manifest_file_preview_summary"]
    assert reviewed_file["status"] == "blocked_waiting_for_approved_draft"
    assert reviewed_file["valid"] is True
    assert reviewed_file["would_write_file"] is False
    assert reviewed_file["would_import_profiles"] is False
    assert reviewed_file["write_ready_for_human_approval"] is False
    assert reviewed_file["target_file"].endswith("birth_profile_review_manifest_reviewed.json")
    assert reviewed_file["target_file_sha256"] is None
    assert reviewed_file["file_preview_gate_passed"] is False
    assert reviewed_file["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_reviewed_manifest_file_preview_receipt_sha256"]) == 64
    import_preview = readiness["birth_profile_import_preview_summary"]
    assert import_preview["status"] == "blocked_not_ready_for_import"
    assert import_preview["valid"] is True
    assert import_preview["would_write_file"] is False
    assert import_preview["import_allowed"] is False
    assert import_preview["request_count"] == 8
    assert import_preview["blocked_request_count"] == 8
    assert import_preview["import_ready_request_count"] == 0
    assert import_preview["import_gate_passed"] is False
    assert import_preview["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_import_preview_receipt_sha256"]) == 64
    patch_preview = readiness["birth_profile_fixture_patch_preview_summary"]
    assert patch_preview["status"] == "blocked_not_ready_for_patch_preview"
    assert patch_preview["valid"] is True
    assert patch_preview["would_write_file"] is False
    assert patch_preview["patch_ready_for_review"] is False
    assert patch_preview["candidate_count"] == 0
    assert patch_preview["candidate_case_ids"] == []
    assert patch_preview["patch_gate_passed"] is False
    assert len(patch_preview["target_file_sha256"]) == 64
    assert len(patch_preview["patch_text_sha256"]) == 64
    assert patch_preview["integrity_check_status"] == "passed"
    assert len(readiness["birth_profile_fixture_patch_preview_receipt_sha256"]) == 64
    assert len(material["candidate_pool_fetch_cache_receipt_sha256"]) == 64
    assert len(material["candidate_pool_draft_import_receipt_sha256"]) == 64
    assert len(material["validation_label_table_receipt_sha256"]) == 64
    assert audit_material["sha256"] == receipt["sha256"]
    assert audit_material["material"]["candidate_count"] == 9
    assert audit_material["material"]["cross_domain_coverage_gate_passed"] is True
    assert audit_material["material"]["validation_label_table_receipt_sha256"] == material["validation_label_table_receipt_sha256"]
    assert audit_material["material"]["symbolic_scoring_readiness_summary"] == readiness


def test_birth_profile_review_manifest_audits_missing_cross_domain_profiles():
    audit = audit_birth_profile_review_manifest(default_birth_profile_review_manifest_path())
    receipt = birth_profile_review_manifest_receipt(audit)

    assert audit["status"] == "ready_for_review"
    assert audit["valid"] is True
    assert audit["production_evidence"] is False
    assert audit["request_count"] == 8
    assert audit["case_count"] == 8
    assert audit["domains"] == ["film", "music", "sports"]
    assert audit["blocked_label_count"] == 257
    assert audit["ready_for_import"] is False
    assert len(audit["birth_profile_review_manifest_receipt"]["sha256"]) == 64
    assert len(receipt["sha256"]) == 64
    assert receipt["material"]["request_count"] == 8
    assert receipt["material"]["ready_for_import"] is False
    by_domain = {item["domain"]: item for item in audit["domain_summary"]}
    assert by_domain["film"]["case_ids"] == ["jackie_chan", "meryl_streep", "tom_hanks"]
    assert by_domain["film"]["blocked_label_count"] == 137
    assert by_domain["music"]["case_ids"] == ["beyonce", "jay_chou", "taylor_swift"]
    assert by_domain["music"]["blocked_label_count"] == 72
    assert by_domain["sports"]["case_ids"] == ["michael_jordan", "serena_williams"]
    assert by_domain["sports"]["blocked_label_count"] == 48


def test_birth_profile_source_review_workplan_turns_requests_into_review_tasks():
    workplan = build_birth_profile_source_review_workplan(default_birth_profile_review_manifest_path())

    assert workplan["status"] == "ready_for_human_source_review"
    assert workplan["valid"] is True
    assert workplan["offline_only"] is True
    assert workplan["would_fetch_live_sources"] is False
    assert workplan["would_write_review_manifest"] is False
    assert workplan["request_count"] == 8
    assert workplan["work_item_count"] == 8
    assert workplan["review_progress_summary"]["review_status_counts"]["not_started"] == 8
    assert workplan["review_progress_summary"]["domain_work_item_counts"] == {
        "film": 3,
        "music": 3,
        "sports": 2,
    }
    assert workplan["review_progress_summary"]["domain_blocked_label_counts"] == {
        "film": 137,
        "music": 72,
        "sports": 48,
    }
    assert workplan["field_gap_summary"]["missing_field_counts"]["birth_date"] == 8
    assert workplan["field_gap_summary"]["missing_field_counts"]["birth_time"] == 8
    assert workplan["field_gap_summary"]["missing_field_counts"]["birthplace"] == 8
    assert workplan["field_gap_summary"]["missing_field_counts"]["gender"] == 8
    assert workplan["field_gap_summary"]["missing_field_counts"]["source_url"] == 8
    assert {"field": "birth_time", "count": 8} in workplan["field_gap_summary"]["highest_gap_fields"]
    assert workplan["source_review_gate"]["id"] == "birth_profile_source_review_required"
    assert workplan["source_review_gate"]["passed"] is False
    assert len(workplan["source_review_workplan_receipt"]["sha256"]) == 64
    assert len(workplan["source_review_workplan_sha256"]) == 64
    assert workplan["integrity_check"]["status"] == "passed"
    by_case = {item["case_id"]: item for item in workplan["work_items"]}
    assert by_case["jackie_chan"]["task_id"] == "birth-profile-source-review-jackie_chan"
    assert by_case["jackie_chan"]["suggested_search_queries"] == [
        "Astro-Databank Jackie Chan birth time",
        "Jackie Chan official biography birthplace",
    ]
    assert by_case["jackie_chan"]["reviewed_profile_draft"]["birth_time"] is None
    assert "build_birth_profile_import_preview reports import_allowed true" in by_case["jackie_chan"][
        "acceptance_criteria"
    ]
    assert any("source review work items require external review" in item for item in workplan["source_review_gate"]["blocking_reasons"])


def test_birth_profile_source_lookup_plan_expands_review_queries(tmp_path):
    plan = build_birth_profile_source_lookup_plan(
        default_birth_profile_review_manifest_path(),
        cache_dir=tmp_path / "birth_source_cache",
    )

    assert plan["status"] == "ready_for_manual_lookup"
    assert plan["valid"] is True
    assert plan["offline_only"] is True
    assert plan["would_fetch_live_sources"] is False
    assert plan["would_write_cache"] is False
    assert plan["would_write_review_manifest"] is False
    assert plan["selected_work_item_count"] == 8
    assert plan["lookup_item_count"] == 8
    assert plan["query_count"] == 16
    assert plan["source_family_catalog"]["source_family_count"] == 5
    assert len(plan["source_family_catalog"]["source_family_catalog_receipt"]["sha256"]) == 64
    assert plan["lookup_gate"]["id"] == "birth_profile_source_lookup_requires_human_execution"
    assert plan["lookup_gate"]["passed"] is False
    assert len(plan["source_lookup_plan_receipt"]["sha256"]) == 64
    assert len(plan["source_lookup_plan_sha256"]) == 64
    assert plan["integrity_check"]["status"] == "passed"
    by_domain = {item["domain"]: item for item in plan["domain_summary"]}
    assert by_domain["film"]["lookup_item_count"] == 3
    assert by_domain["film"]["query_count"] == 6
    assert by_domain["sports"]["lookup_item_count"] == 2
    assert by_domain["sports"]["blocked_label_count"] == 48
    jackie = {item["case_id"]: item for item in plan["lookup_items"]}["jackie_chan"]
    assert jackie["planned_queries"][0]["query"] == "Astro-Databank Jackie Chan birth time"
    assert jackie["planned_queries"][0]["would_fetch_live_source"] is False
    assert jackie["planned_queries"][0]["would_write_cache"] is False
    assert "birth_time" in jackie["planned_queries"][0]["target_fields"]
    assert jackie["planned_queries"][0]["source_use_policy"]["requires_rated_birth_time_source"] is True
    assert "rated_birth_time_source" in [
        item["source_family_id"] for item in jackie["planned_queries"][0]["recommended_source_families"]
    ]
    assert "wikidata_identity_anchor" in [
        item["source_family_id"] for item in jackie["planned_queries"][1]["recommended_source_families"]
    ]
    assert jackie["planned_queries"][1]["source_use_policy"]["requires_rated_birth_time_source"] is False


def test_birth_profile_source_lookup_plan_filters_domain(tmp_path):
    result = birth_profile_source_lookup_plan(
        tmp_path / "repo",
        cache_dir=tmp_path / "birth_source_cache",
        domain="sports",
    )
    schema = schema_document()

    plan = result["source_lookup_plan"]
    assert result["configured"] is True
    assert plan["selected_work_item_count"] == 2
    assert plan["lookup_item_count"] == 2
    assert plan["query_count"] == 4
    assert plan["source_family_catalog"]["source_family_count"] == 5
    assert [item["domain"] for item in plan["domain_summary"]] == ["sports"]
    assert all(item["domain"] == "sports" for item in plan["lookup_items"])
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileSourceLookupPlanResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_source_cache_template_preview_renders_manual_json(tmp_path):
    preview = build_birth_profile_source_cache_template_preview(
        default_birth_profile_review_manifest_path(),
        cache_dir=tmp_path / "birth_source_cache",
        domain="sports",
    )

    assert preview["status"] == "ready_for_manual_cache_fill"
    assert preview["valid"] is True
    assert preview["would_write_cache"] is False
    assert preview["would_fetch_live_sources"] is False
    assert preview["would_import_profiles"] is False
    assert preview["template_count"] == 4
    first = preview["templates"][0]
    assert first["planned_cache_path"].endswith("michael_jordan_1.json")
    assert first["template_payload"]["review_status"] == "needs_more_evidence"
    assert first["template_payload"]["source_family_id"] == ""
    assert first["template_payload"]["query_id"] == first["query_id"]
    assert first["template_payload"]["case_id"] == "michael_jordan"
    assert "source_family_id" in first["required_fields"]
    assert "source_url" in first["required_fields"]
    assert "source_reviewed" in first["review_status_options"]
    assert "rated_birth_time_source" in first["allowed_source_family_ids"]
    assert "birth_time" in first["target_fields"]
    assert len(first["template_text_sha256"]) == 64
    assert preview["template_preview_gate"]["id"] == "birth_profile_source_cache_template_requires_manual_fill"
    assert preview["template_preview_gate"]["passed"] is False
    assert len(preview["source_cache_template_preview_receipt"]["sha256"]) == 64
    assert len(preview["source_cache_template_preview_sha256"]) == 64
    assert preview["integrity_check"]["status"] == "passed"


def test_birth_profile_source_cache_template_preview_api_exposes_schema(tmp_path):
    result = birth_profile_source_cache_template_preview(
        tmp_path / "repo",
        cache_dir=tmp_path / "birth_source_cache",
        domain="film",
    )
    schema = schema_document()

    preview = result["source_cache_template_preview"]
    assert result["configured"] is True
    assert preview["status"] == "ready_for_manual_cache_fill"
    assert preview["template_count"] == 6
    assert preview["would_write_cache"] is False
    assert "birth-profile-source-cache-template-preview" in result["configuration_guidance"]["cli_command"]
    assert "GET /birth-profile-source-cache-template-preview" in result["configuration_guidance"]["http_query"]
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileSourceCacheTemplatePreviewResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_source_cache_audit_reports_missing_manual_cache(tmp_path):
    audit = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=tmp_path / "birth_source_cache",
        domain="film",
    )

    assert audit["status"] == "waiting_for_manual_cache"
    assert audit["valid"] is True
    assert audit["offline_only"] is True
    assert audit["would_fetch_live_sources"] is False
    assert audit["would_write_cache"] is False
    assert audit["would_write_review_manifest"] is False
    assert audit["would_import_profiles"] is False
    assert audit["expected_cache_count"] == 6
    assert audit["present_cache_count"] == 0
    assert audit["missing_cache_count"] == 6
    assert audit["accepted_cache_count"] == 0
    assert audit["cache_audit_gate"]["id"] == "birth_profile_source_cache_requires_reviewed_manifest_draft"
    assert audit["cache_audit_gate"]["passed"] is False
    assert len(audit["source_cache_audit_receipt"]["sha256"]) == 64
    assert len(audit["source_cache_audit_sha256"]) == 64
    assert audit["integrity_check"]["status"] == "passed"


def test_birth_profile_source_cache_audit_reads_reviewed_cache_file(tmp_path):
    cache_dir = tmp_path / "birth_source_cache"
    audit_before = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="film",
    )
    first_cache = Path(audit_before["cache_items"][0]["cache_path"])
    first_cache.parent.mkdir(parents=True, exist_ok=True)
    first_cache.write_text(
        json.dumps(
            {
                "query_id": audit_before["cache_items"][0]["query_id"],
                "case_id": audit_before["cache_items"][0]["case_id"],
                "source_family_id": "rated_birth_time_source",
                "source_name": "review fixture source",
                "source_url": "https://example.test/jackie-chan-birth",
                "source_rating": "review_fixture_only",
                "reviewer_note": "Test fixture for cache audit contract.",
                "review_status": "source_reviewed",
                "birth_time": "08:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    audit = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="film",
    )

    assert audit["status"] == "waiting_for_manual_cache"
    assert audit["present_cache_count"] == 1
    assert audit["missing_cache_count"] == 5
    assert audit["reviewed_cache_count"] == 1
    assert audit["accepted_cache_count"] == 1
    reviewed = next(item for item in audit["cache_items"] if item["cache_status"] == "present")
    assert reviewed["source_evidence_acceptable"] is True
    assert reviewed["source_family_id"] == "rated_birth_time_source"
    assert reviewed["payload_sha256"]
    assert reviewed["extracted_fields"]["birth_time"] == "08:00"
    assert audit["cache_audit_gate"]["passed"] is False


def test_birth_profile_source_cache_audit_rejects_identity_anchor_birth_time(tmp_path):
    cache_dir = tmp_path / "birth_source_cache"
    audit_before = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="film",
    )
    first_cache = Path(audit_before["cache_items"][0]["cache_path"])
    first_cache.parent.mkdir(parents=True, exist_ok=True)
    first_cache.write_text(
        json.dumps(
            {
                "query_id": audit_before["cache_items"][0]["query_id"],
                "case_id": audit_before["cache_items"][0]["case_id"],
                "source_family_id": "wikidata_identity_anchor",
                "source_name": "identity fixture source",
                "source_url": "https://example.test/identity-only",
                "source_rating": "identity-only",
                "reviewer_note": "Identity anchor must not satisfy birth_time.",
                "review_status": "source_reviewed",
                "birth_time": "08:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    audit = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="film",
    )

    reviewed = next(item for item in audit["cache_items"] if item["cache_status"] == "present")
    assert reviewed["source_evidence_acceptable"] is False
    assert any("birth_time evidence requires source_family_id=rated_birth_time_source" in item for item in reviewed["failures"])
    assert audit["accepted_cache_count"] == 0


def test_birth_profile_source_cache_audit_rejects_metadata_only_reviewed_cache(tmp_path):
    cache_dir = tmp_path / "birth_source_cache"
    audit_before = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="film",
    )
    first_cache = Path(audit_before["cache_items"][0]["cache_path"])
    first_cache.parent.mkdir(parents=True, exist_ok=True)
    first_cache.write_text(
        json.dumps(
            {
                "query_id": audit_before["cache_items"][0]["query_id"],
                "case_id": audit_before["cache_items"][0]["case_id"],
                "source_family_id": "rated_birth_time_source",
                "source_name": "metadata only fixture",
                "source_url": "https://example.test/metadata-only",
                "source_rating": "review_fixture_only",
                "reviewer_note": "Metadata alone must not satisfy a reviewed source cache.",
                "review_status": "source_reviewed",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    audit = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="film",
    )

    reviewed = next(item for item in audit["cache_items"] if item["cache_status"] == "present")
    assert reviewed["source_evidence_acceptable"] is False
    assert any("reviewed payload does not fill any substantive birth field" in item for item in reviewed["failures"])
    assert audit["accepted_cache_count"] == 0


def _write_reviewed_cache(cache_item: dict, **fields: str) -> None:
    cache_path = Path(cache_item["cache_path"])
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    source_family_id = fields.pop(
        "source_family_id",
        "rated_birth_time_source" if _present_for_test(fields.get("birth_time")) else "wikidata_identity_anchor",
    )
    payload = {
        "query_id": cache_item["query_id"],
        "case_id": cache_item["case_id"],
        "source_family_id": source_family_id,
        "source_name": fields.pop("source_name", "review fixture source"),
        "source_url": fields.pop("source_url", "https://example.test/reviewed-birth-cache"),
        "source_rating": fields.pop("source_rating", "review_fixture_only"),
        "reviewer_note": fields.pop("reviewer_note", "Test fixture for reviewed manifest draft preview."),
        "review_status": "source_reviewed",
        **fields,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _present_for_test(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def test_birth_profile_reviewed_manifest_draft_preview_blocks_until_cache_complete(tmp_path):
    preview = build_birth_profile_reviewed_manifest_draft_preview(
        default_birth_profile_review_manifest_path(),
        cache_dir=tmp_path / "birth_source_cache",
        domain="sports",
    )

    assert preview["status"] == "blocked_waiting_for_complete_source_cache"
    assert preview["valid"] is True
    assert preview["would_write_review_manifest"] is False
    assert preview["would_import_profiles"] is False
    assert preview["draft_ready_for_human_approval"] is False
    assert preview["review_request_count"] == 2
    assert preview["complete_review_request_count"] == 0
    assert preview["incomplete_review_request_count"] == 2
    assert preview["draft_gate"]["id"] == "birth_profile_reviewed_manifest_draft_requires_human_approval"
    assert preview["draft_gate"]["passed"] is False
    assert len(preview["reviewed_manifest_draft_preview_receipt"]["sha256"]) == 64
    assert len(preview["reviewed_manifest_draft_preview_sha256"]) == 64
    assert preview["integrity_check"]["status"] == "passed"


def test_birth_profile_reviewed_manifest_draft_preview_uses_accepted_cache(tmp_path):
    cache_dir = tmp_path / "birth_source_cache"
    cache_audit = build_birth_profile_source_cache_audit(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="sports",
    )
    jordan_items = [item for item in cache_audit["cache_items"] if item["case_id"] == "michael_jordan"]
    _write_reviewed_cache(
        jordan_items[0],
        birth_date="1963-02-17",
        birth_time="13:40",
        source_url="https://example.test/michael-jordan-birth-time",
        reviewer_note="Birth time reviewed from fixture source.",
    )
    _write_reviewed_cache(
        jordan_items[1],
        gender="male",
        birthplace="Brooklyn, New York, United States",
        source_url="https://example.test/michael-jordan-biography",
        reviewer_note="Birthplace reviewed from fixture source.",
    )

    preview = build_birth_profile_reviewed_manifest_draft_preview(
        default_birth_profile_review_manifest_path(),
        cache_dir=cache_dir,
        domain="sports",
    )

    by_case = {item["case_id"]: item for item in preview["draft_manifest"]["review_requests"]}
    jordan = by_case["michael_jordan"]
    assert preview["status"] == "blocked_waiting_for_complete_source_cache"
    assert preview["draft_ready_for_human_approval"] is False
    assert jordan["review_status"] == "externally_reviewed"
    assert jordan["missing_profile_fields"] == []
    assert jordan["birth_time"] == "13:40"
    assert jordan["birthplace"] == "Brooklyn, New York, United States"
    assert jordan["source_cache_item_count"] == 2
    assert len(jordan["source_cache_payload_sha256s"]) == 2
    assert by_case["serena_williams"]["missing_profile_fields"]
    assert preview["draft_gate"]["passed"] is False


def test_birth_profile_source_cache_audit_api_exposes_schema(tmp_path):
    result = birth_profile_source_cache_audit(
        tmp_path / "repo",
        cache_dir=tmp_path / "birth_source_cache",
        domain="sports",
    )
    schema = schema_document()

    audit = result["source_cache_audit"]
    assert result["configured"] is True
    assert audit["status"] == "waiting_for_manual_cache"
    assert audit["expected_cache_count"] == 4
    assert audit["missing_cache_count"] == 4
    assert audit["cache_audit_gate"]["passed"] is False
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileSourceCacheAuditResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_reviewed_manifest_draft_preview_api_exposes_schema(tmp_path):
    result = birth_profile_reviewed_manifest_draft_preview(
        tmp_path / "repo",
        cache_dir=tmp_path / "birth_source_cache",
        domain="film",
    )
    schema = schema_document()

    preview = result["reviewed_manifest_draft_preview"]
    assert result["configured"] is True
    assert preview["status"] == "blocked_waiting_for_complete_source_cache"
    assert preview["would_write_review_manifest"] is False
    assert preview["would_import_profiles"] is False
    assert preview["draft_gate"]["passed"] is False
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileReviewedManifestDraftPreviewResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_reviewed_manifest_file_preview_blocks_until_draft_ready(tmp_path):
    preview = build_birth_profile_reviewed_manifest_file_preview(
        default_birth_profile_review_manifest_path(),
        cache_dir=tmp_path / "birth_source_cache",
        domain="sports",
        target_path=tmp_path / "reviewed_birth_profiles.json",
    )

    assert preview["status"] == "blocked_waiting_for_approved_draft"
    assert preview["valid"] is True
    assert preview["target_file"] == str(tmp_path / "reviewed_birth_profiles.json")
    assert preview["target_file_exists"] is False
    assert preview["target_file_sha256"] is None
    assert preview["would_write_file"] is False
    assert preview["would_import_profiles"] is False
    assert preview["write_ready_for_human_approval"] is False
    assert preview["file_preview_gate"]["id"] == "birth_profile_reviewed_manifest_file_write_requires_human_approval"
    assert preview["file_preview_gate"]["passed"] is False
    assert len(preview["reviewed_manifest_file_preview_receipt"]["sha256"]) == 64
    assert len(preview["reviewed_manifest_file_preview_sha256"]) == 64
    assert preview["integrity_check"]["status"] == "passed"


def test_birth_profile_reviewed_manifest_file_preview_api_exposes_schema(tmp_path):
    result = birth_profile_reviewed_manifest_file_preview(
        tmp_path / "repo",
        cache_dir=tmp_path / "birth_source_cache",
        domain="music",
        target_path=tmp_path / "reviewed_birth_profiles.json",
    )
    schema = schema_document()

    preview = result["reviewed_manifest_file_preview"]
    assert result["configured"] is True
    assert preview["status"] == "blocked_waiting_for_approved_draft"
    assert preview["would_write_file"] is False
    assert preview["would_import_profiles"] is False
    assert preview["file_preview_gate"]["passed"] is False
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileReviewedManifestFilePreviewResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_review_status_exposes_non_import_gate(tmp_path):
    result = birth_profile_review_status(tmp_path / "repo")
    schema = schema_document()

    assert result["configured"] is False
    assert result["audit"]["request_count"] == 8
    assert result["audit"]["blocked_label_count"] == 257
    assert result["audit"]["ready_for_import"] is False
    assert len(result["birth_profile_review_manifest_receipt"]["sha256"]) == 64
    gate = result["production_gate"]
    assert gate["id"] == "birth_profile_review_manifest_ready_for_import"
    assert gate["passed"] is False
    assert gate["ready_for_import"] is False
    assert gate["production_evidence"] is False
    assert "birth-profile-review" in result["configuration_guidance"]["cli_command"]
    assert "GET /birth-profile-review" in result["configuration_guidance"]["http_query"]
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileReviewStatusResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_source_review_workplan_status_exposes_runtime_schema(tmp_path):
    result = birth_profile_source_review_workplan(tmp_path / "repo")
    schema = schema_document()

    assert result["configured"] is False
    assert result["source_review_workplan"]["status"] == "ready_for_human_source_review"
    assert result["source_review_workplan"]["would_fetch_live_sources"] is False
    assert result["source_review_workplan"]["would_write_review_manifest"] is False
    assert result["source_review_workplan"]["work_item_count"] == 8
    assert result["source_review_workplan"]["source_review_gate"]["passed"] is False
    assert "birth-profile-source-review-workplan" in result["configuration_guidance"]["cli_command"]
    assert "GET /birth-profile-source-review-workplan" in result["configuration_guidance"]["http_query"]
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileSourceReviewWorkplanResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_import_preview_blocks_unreviewed_manifest(tmp_path):
    preview = build_birth_profile_import_preview(default_birth_profile_review_manifest_path())

    assert preview["status"] == "blocked_not_ready_for_import"
    assert preview["valid"] is True
    assert preview["would_write_file"] is False
    assert preview["import_allowed"] is False
    assert preview["request_count"] == 8
    assert preview["blocked_request_count"] == 8
    assert preview["import_ready_request_count"] == 0
    assert preview["import_gate"]["passed"] is False
    assert "not marked ready_for_import" in " ".join(preview["blocking_reasons"])
    assert "not externally_reviewed" in " ".join(preview["blocking_reasons"])
    assert len(preview["import_preview_receipt"]["sha256"]) == 64
    assert len(preview["import_preview_sha256"]) == 64
    assert preview["integrity_check"]["status"] == "passed"
    assert preview["integrity_check"]["receipt_sha256_matches_material"] is True
    assert preview["integrity_check"]["preview_sha256_matches_material"] is True


def test_birth_profile_import_preview_accepts_reviewed_manifest_without_writing(tmp_path):
    manifest_path = tmp_path / "reviewed_birth_profiles.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "birth-profile-review-manifest-v1",
                "status": "reviewed_ready_for_import",
                "purpose": "Contract fixture for reviewed celebrity birth-profile import preview.",
                "boundary": "Reviewed contract fixture only; preview must remain non-mutating.",
                "review": {
                    "externally_reviewed": True,
                    "reviewer": "contract-test-reviewer",
                    "review_date": "2026-06-26",
                    "approval": "approved_for_birth_profile_import",
                },
                "required_profile_fields": [
                    "case_id",
                    "public_name",
                    "domain",
                    "birth_date",
                    "birth_time",
                    "gender",
                    "birthplace",
                    "source_name",
                    "source_url",
                    "source_rating",
                    "source_note",
                    "identity_source_url",
                    "review_status",
                    "collected_before_rule_change",
                ],
                "source_policy": {
                    "requires_identity_match": True,
                    "requires_birth_time_source": True,
                    "requires_source_rating": True,
                    "allowed_source_families": ["contract fixture"],
                    "minimum_review_status_for_import": "externally_reviewed",
                    "disallowed_use": "Do not import without separate fixture patch review.",
                },
                "review_requests": [
                    {
                        "case_id": "contract_sports_case",
                        "public_name": "Contract Sports Case",
                        "domain": "sports",
                        "identity_source_url": "https://www.wikidata.org/wiki/Q41421",
                        "missing_profile_fields": [],
                        "suggested_search_queries": ["contract fixture query"],
                        "blocked_symbolic_event_topics": ["sports_peak"],
                        "blocked_label_count": 1,
                        "review_status": "externally_reviewed",
                        "collected_before_rule_change": True,
                        "birth_date": "1963-02-17",
                        "birth_time": "13:40",
                        "gender": "male",
                        "birthplace": "Brooklyn, New York, United States",
                        "source_name": "Contract Fixture Source",
                        "source_url": "https://example.com/reviewed-birth-profile-contract",
                        "source_rating": "reviewed-contract",
                        "source_note": "Synthetic contract fixture used only to test reviewed manifest flow.",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    audit = audit_birth_profile_review_manifest(manifest_path)
    preview = build_birth_profile_import_preview(manifest_path)

    assert audit["status"] == "ready_for_import"
    assert audit["production_evidence"] is True
    assert audit["ready_for_import"] is True
    assert preview["status"] == "ready_for_non_mutating_import_plan"
    assert preview["would_write_file"] is False
    assert preview["import_allowed"] is True
    assert preview["import_gate"]["passed"] is True
    assert preview["blocking_reasons"] == []
    assert preview["import_ready_request_count"] == 1
    assert preview["blocked_request_count"] == 0
    assert preview["candidate_profiles"][0]["case_id"] == "contract_sports_case"
    assert preview["candidate_profiles"][0]["birth"]["birth_time"] == "13:40"
    assert preview["integrity_check"]["status"] == "passed"


def test_birth_profile_fixture_patch_preview_renders_reviewed_candidates_without_writing(tmp_path):
    manifest_path = tmp_path / "reviewed_birth_profiles.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "birth-profile-review-manifest-v1",
                "status": "reviewed_ready_for_import",
                "purpose": "Contract fixture for reviewed celebrity birth-profile patch preview.",
                "boundary": "Reviewed contract fixture only; preview must remain non-mutating.",
                "review": {
                    "externally_reviewed": True,
                    "reviewer": "contract-test-reviewer",
                    "review_date": "2026-06-26",
                    "approval": "approved_for_birth_profile_import",
                },
                "required_profile_fields": [
                    "case_id",
                    "public_name",
                    "domain",
                    "birth_date",
                    "birth_time",
                    "gender",
                    "birthplace",
                    "source_name",
                    "source_url",
                    "source_rating",
                    "source_note",
                    "identity_source_url",
                    "review_status",
                    "collected_before_rule_change",
                ],
                "source_policy": {
                    "requires_identity_match": True,
                    "requires_birth_time_source": True,
                    "requires_source_rating": True,
                    "allowed_source_families": ["contract fixture"],
                    "minimum_review_status_for_import": "externally_reviewed",
                    "disallowed_use": "Do not import without separate fixture patch review.",
                },
                "review_requests": [
                    {
                        "case_id": "contract_music_case",
                        "public_name": "Contract Music Case",
                        "domain": "music",
                        "identity_source_url": "https://www.wikidata.org/wiki/Q36153",
                        "missing_profile_fields": [],
                        "suggested_search_queries": ["contract fixture query"],
                        "blocked_symbolic_event_topics": ["public_fame"],
                        "blocked_label_count": 1,
                        "review_status": "externally_reviewed",
                        "collected_before_rule_change": True,
                        "birth_date": "1981-09-04",
                        "birth_time": "10:00",
                        "gender": "female",
                        "birthplace": "Houston, Texas, United States",
                        "source_name": "Contract Fixture Source",
                        "source_url": "https://example.com/reviewed-birth-profile-contract",
                        "source_rating": "reviewed-contract",
                        "source_note": "Synthetic contract fixture used only to test patch preview flow.",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    blocked = build_birth_profile_fixture_patch_preview(default_birth_profile_review_manifest_path())
    ready = build_birth_profile_fixture_patch_preview(manifest_path)

    assert blocked["status"] == "blocked_not_ready_for_patch_preview"
    assert blocked["would_write_file"] is False
    assert blocked["patch_ready_for_review"] is False
    assert ready["status"] == "ready_for_patch_review"
    assert ready["would_write_file"] is False
    assert ready["patch_ready_for_review"] is True
    assert ready["candidate_count"] == 1
    assert ready["candidate_case_ids"] == ["contract_music_case"]
    assert "contract_music_case" in ready["patch_text"]
    assert len(ready["target_file_sha256"]) == 64
    assert len(ready["patch_text_sha256"]) == 64
    assert ready["patch_gate"]["passed"] is True
    assert ready["integrity_check"]["status"] == "passed"


def test_birth_profile_import_preview_status_exposes_runtime_schema(tmp_path):
    result = birth_profile_import_preview(tmp_path / "repo")
    schema = schema_document()

    assert result["configured"] is False
    assert result["import_preview"]["status"] == "blocked_not_ready_for_import"
    assert result["import_preview"]["would_write_file"] is False
    assert result["import_preview"]["import_allowed"] is False
    assert result["import_preview"]["import_gate"]["passed"] is False
    assert "birth-profile-import-preview" in result["configuration_guidance"]["cli_command"]
    assert "GET /birth-profile-import-preview" in result["configuration_guidance"]["http_query"]
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileImportPreviewResponse",
        schema_doc=schema,
    ) == []


def test_birth_profile_fixture_patch_preview_status_exposes_runtime_schema(tmp_path):
    result = birth_profile_fixture_patch_preview(tmp_path / "repo")
    schema = schema_document()

    assert result["configured"] is False
    assert result["fixture_patch_preview"]["status"] == "blocked_not_ready_for_patch_preview"
    assert result["fixture_patch_preview"]["would_write_file"] is False
    assert result["fixture_patch_preview"]["patch_ready_for_review"] is False
    assert result["fixture_patch_preview"]["patch_gate"]["passed"] is False
    assert "birth-profile-fixture-patch-preview" in result["configuration_guidance"]["cli_command"]
    assert "GET /birth-profile-fixture-patch-preview" in result["configuration_guidance"]["http_query"]
    assert schema_validation_errors(
        result,
        schema_name="BirthProfileFixturePatchPreviewResponse",
        schema_doc=schema,
    ) == []


def test_production_readiness_gates_birth_profile_import_preview(tmp_path):
    result = production_readiness(tmp_path / "repo", live=False)
    source_gate = next(item for item in result["gates"] if item["id"] == "birth_profile_source_review_workplan_available")
    lookup_gate = next(item for item in result["gates"] if item["id"] == "birth_profile_source_lookup_plan_dry_run")
    source_family_gate = next(
        item for item in result["gates"] if item["id"] == "birth_profile_source_family_catalog_bound"
    )
    template_gate = next(
        item for item in result["gates"] if item["id"] == "birth_profile_source_cache_template_preview_non_mutating"
    )
    family_probe_gate = next(
        item for item in result["gates"] if item["id"] == "birth_profile_source_family_cache_enforcement_probe"
    )
    substantive_probe_gate = next(
        item for item in result["gates"]
        if item["id"] == "birth_profile_substantive_evidence_cache_enforcement_probe"
    )
    cache_gate = next(item for item in result["gates"] if item["id"] == "birth_profile_source_cache_audit_read_only")
    draft_gate = next(
        item for item in result["gates"]
        if item["id"] == "birth_profile_reviewed_manifest_draft_preview_non_mutating"
    )
    gate = next(item for item in result["gates"] if item["id"] == "birth_profile_import_preview_blocked")
    patch_gate = next(item for item in result["gates"] if item["id"] == "birth_profile_fixture_patch_preview_blocked")
    chinese_quality_gate = next(
        item for item in result["gates"] if item["id"] == "benchmark_chinese_render_quality_diagnostics"
    )

    assert source_gate["passed"] is True
    assert source_gate["details"] == []
    assert lookup_gate["passed"] is True
    assert lookup_gate["details"] == []
    assert source_family_gate["passed"] is True
    assert source_family_gate["details"] == []
    assert template_gate["passed"] is True
    assert template_gate["details"] == []
    assert family_probe_gate["passed"] is True
    assert family_probe_gate["details"] == []
    assert chinese_quality_gate["passed"] is True
    assert chinese_quality_gate["details"] == []
    assert substantive_probe_gate["passed"] is True
    assert substantive_probe_gate["details"] == []
    assert cache_gate["passed"] is True
    assert cache_gate["details"] == []
    assert draft_gate["passed"] is True
    assert draft_gate["details"] == []
    assert gate["passed"] is True
    assert gate["details"] == []
    assert patch_gate["passed"] is True
    assert patch_gate["details"] == []
    assert result["production_gate_registry_audit"]["registry_current"] is True
    assert not any(item["gate"] == "birth_profile_source_review_workplan_available" for item in result["blockers"])
    assert not any(item["gate"] == "birth_profile_source_lookup_plan_dry_run" for item in result["blockers"])
    assert not any(item["gate"] == "birth_profile_source_family_catalog_bound" for item in result["blockers"])
    assert not any(
        item["gate"] == "birth_profile_source_cache_template_preview_non_mutating"
        for item in result["blockers"]
    )
    assert not any(
        item["gate"] == "birth_profile_source_family_cache_enforcement_probe"
        for item in result["blockers"]
    )
    assert not any(
        item["gate"] == "benchmark_chinese_render_quality_diagnostics"
        for item in result["blockers"]
    )
    assert not any(
        item["gate"] == "birth_profile_substantive_evidence_cache_enforcement_probe"
        for item in result["blockers"]
    )
    assert not any(item["gate"] == "birth_profile_source_cache_audit_read_only" for item in result["blockers"])
    assert not any(
        item["gate"] == "birth_profile_reviewed_manifest_draft_preview_non_mutating"
        for item in result["blockers"]
    )
    assert not any(item["gate"] == "birth_profile_import_preview_blocked" for item in result["blockers"])
    assert not any(item["gate"] == "birth_profile_fixture_patch_preview_blocked" for item in result["blockers"])


def test_industry_event_manifest_audit_accepts_example_contract():
    audit = audit_industry_event_manifest(EXAMPLE_INDUSTRY_EVENT_MANIFEST)
    receipt = industry_event_manifest_receipt(audit)

    assert audit["valid"] is True
    assert audit["status"] == "ready_for_review"
    assert audit["production_evidence"] is False
    assert audit["externally_reviewed"] is False
    assert audit["record_count"] == 6
    assert audit["positive_event_count"] == 3
    assert audit["negative_event_count"] == 3
    assert audit["domains"] == ["film", "music", "sports"]
    assert audit["split_roles"] == ["holdout", "train"]
    assert len(audit["content_hash"]) == 64
    assert receipt["schema_version"] == "industry-event-manifest-audit-receipt-v1"
    assert receipt["material"]["content_hash"] == audit["content_hash"]
    assert receipt["material"]["production_evidence"] is False


def test_industry_event_manifest_audit_rejects_missing_negative_year_reason(tmp_path):
    payload = json.loads(EXAMPLE_INDUSTRY_EVENT_MANIFEST.read_text(encoding="utf-8"))
    payload["records"][1]["negative_year_reason"] = ""
    manifest = tmp_path / "industry_events.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    audit = audit_industry_event_manifest(manifest)

    assert audit["valid"] is False
    assert any("negative_year_reason is required" in failure for failure in audit["failures"])
    assert audit["production_evidence"] is False


def test_industry_event_validation_label_table_adapts_manifest_records(tmp_path):
    label_table = build_industry_event_validation_label_table(EXAMPLE_INDUSTRY_EVENT_MANIFEST)

    assert label_table["valid"] is True
    assert label_table["record_count"] == 6
    assert label_table["positive_label_count"] == 3
    assert label_table["negative_label_count"] == 3
    assert label_table["case_count"] == 3
    assert label_table["domains"] == ["film", "music", "sports"]
    assert label_table["event_topics"] == ["career_peak", "public_fame"]
    assert len(label_table["validation_label_table_receipt"]["sha256"]) == 64
    assert {label["label_kind"] for label in label_table["labels"]} == {"positive_year", "negative_year"}
    assert label_table["cross_domain_coverage_gate"]["passed"] is True
    assert label_table["cross_domain_coverage_gate"]["required_domains"] == ["film", "music", "sports"]
    assert label_table["domain_coverage_summary"] == [
        {
            "domain": "film",
            "label_count": 2,
            "positive_label_count": 1,
            "negative_label_count": 1,
            "case_count": 1,
            "event_topics": ["public_fame"],
            "has_positive_and_negative_labels": True,
            "year_min": 1952,
            "year_max": 1953,
        },
        {
            "domain": "music",
            "label_count": 2,
            "positive_label_count": 1,
            "negative_label_count": 1,
            "case_count": 1,
            "event_topics": ["career_peak"],
            "has_positive_and_negative_labels": True,
            "year_min": 1963,
            "year_max": 1964,
        },
        {
            "domain": "sports",
            "label_count": 2,
            "positive_label_count": 1,
            "negative_label_count": 1,
            "case_count": 1,
            "event_topics": ["career_peak"],
            "has_positive_and_negative_labels": True,
            "year_min": 2002,
            "year_max": 2003,
        },
    ]
    assert label_table["domain_topic_summary"][0]["label_count"] >= 1

    result = industry_event_validation_labels(tmp_path / "repo", EXAMPLE_INDUSTRY_EVENT_MANIFEST)
    assert result["validation_label_table"]["record_count"] == 6
    assert result["validation_label_table"]["cross_domain_coverage_gate"]["passed"] is True
    assert "industry-event-labels --manifest" in result["configuration_guidance"]["cli_command"]


def test_industry_event_symbolic_scoring_readiness_matches_birth_profiles(tmp_path):
    readiness = build_industry_event_symbolic_scoring_readiness(
        EXAMPLE_INDUSTRY_EVENT_MANIFEST,
        birth_cases=famous_case_records(),
    )

    assert readiness["valid"] is True
    assert readiness["label_count"] == 6
    assert readiness["ready_label_count"] == 4
    assert readiness["blocked_label_count"] == 2
    assert readiness["positive_ready_label_count"] == 2
    assert readiness["negative_ready_label_count"] == 2
    assert readiness["ready_case_count"] == 2
    assert readiness["blocked_case_count"] == 1
    assert len(readiness["symbolic_scoring_readiness_receipt"]["sha256"]) == 64

    case_summary = {item["case_id"]: item for item in readiness["case_summary"]}
    assert case_summary["marilyn_monroe"]["scoring_ready"] is True
    assert case_summary["roger_federer"]["scoring_ready"] is True
    assert case_summary["bob_dylan"]["scoring_ready"] is False
    assert case_summary["bob_dylan"]["blocking_reasons"] == ["missing reviewed birth profile for case_id"]

    gate_by_id = {item["id"]: item for item in readiness["gates"]}
    assert gate_by_id["validation_label_table_valid"]["passed"] is True
    assert gate_by_id["symbolic_scoring_birth_profile_coverage"]["passed"] is False
    assert gate_by_id["symbolic_scoring_positive_negative_ready_labels"]["passed"] is True

    result = industry_event_symbolic_scoring_readiness(tmp_path / "repo", EXAMPLE_INDUSTRY_EVENT_MANIFEST)
    assert result["symbolic_scoring_readiness"]["ready_label_count"] == 4
    assert "industry-event-scoring-readiness --manifest" in result["configuration_guidance"]["cli_command"]


def test_industry_event_symbolic_annual_score_scores_ready_labels(tmp_path):
    score = build_industry_event_symbolic_annual_score(
        EXAMPLE_INDUSTRY_EVENT_MANIFEST,
        birth_cases=famous_case_records(),
    )

    assert score["valid"] is True
    assert score["label_count"] == 6
    assert score["scored_label_count"] == 4
    assert score["blocked_label_count"] == 2
    assert score["positive_scored_label_count"] == 2
    assert score["negative_scored_label_count"] == 2
    assert 0 <= score["exact_hit_rate"] <= 1
    assert 0 <= score["strict_exact_hit_rate"] <= 1
    assert 0 <= score["false_positive_rate"] <= 1
    assert 0 <= score["strict_false_positive_rate"] <= 1
    assert len(score["symbolic_annual_score_receipt"]["sha256"]) == 64

    scored_by_case = {item["case_id"] for item in score["scored_labels"]}
    assert scored_by_case == {"marilyn_monroe", "roger_federer"}
    assert {item["case_id"] for item in score["symbolic_scoring_readiness"]["label_readiness"] if not item["scoring_ready"]} == {
        "bob_dylan"
    }
    roger_rows = [item for item in score["scored_labels"] if item["case_id"] == "roger_federer"]
    assert {item["symbolic_event_topic"] for item in roger_rows} == {"sports_peak"}
    assert all(item["topic_mapping_reason"].startswith("career_peak in sports") for item in roger_rows)
    assert all("annual_category" in item and "event_evidence" in item for item in score["scored_labels"])
    assert score["evidence_refinement_queue"]
    assert score["blocked_readiness_refinement_queue"]
    assert score["evolution_task_plan"]
    assert all(item["recommended_evidence"] for item in score["evidence_refinement_queue"])
    assert all(item["acceptance_criteria"] for item in score["evolution_task_plan"])
    task_ids = {item["task_id"] for item in score["evolution_task_plan"]}
    assert "industry-symbolic-film-public_fame-expand_ready_labels" in task_ids
    assert "industry-symbolic-sports-sports_peak-expand_ready_labels" in task_ids
    assert "industry-symbolic-music-career_project-add_reviewed_birth_profiles" in task_ids
    blocked_summary = score["blocked_readiness_domain_topic_summary"]
    assert blocked_summary == [
        {
            "domain": "music",
            "symbolic_event_topic": "career_project",
            "blocked_label_count": 2,
            "blocked_case_count": 1,
            "positive_blocked_label_count": 1,
            "negative_blocked_label_count": 1,
            "case_ids": ["bob_dylan"],
            "public_names": ["Bob Dylan"],
            "blocking_reasons": ["missing reviewed birth profile for case_id"],
        }
    ]
    music_task = next(
        item
        for item in score["evolution_task_plan"]
        if item["task_id"] == "industry-symbolic-music-career_project-add_reviewed_birth_profiles"
    )
    assert music_task["task_type"] == "add_reviewed_birth_profiles"
    assert music_task["blocked_case_ids"] == ["bob_dylan"]
    assert music_task["current_metrics"]["blocked_label_count"] == 2
    assert "matching reviewed birth profile" in music_task["acceptance_criteria"][0]
    film_task = next(item for item in score["evolution_task_plan"] if item["domain"] == "film")
    assert film_task["task_type"] == "expand_ready_labels"
    assert "more reviewed birth profiles" in film_task["next_evidence_to_add"][0]

    result = industry_event_symbolic_annual_score(tmp_path / "repo", EXAMPLE_INDUSTRY_EVENT_MANIFEST)
    assert result["symbolic_annual_score"]["scored_label_count"] == 4
    assert "industry-event-symbolic-score --manifest" in result["configuration_guidance"]["cli_command"]


def test_industry_event_evidence_workplan_projects_collection_commands(tmp_path):
    score = build_industry_event_symbolic_annual_score(
        EXAMPLE_INDUSTRY_EVENT_MANIFEST,
        birth_cases=famous_case_records(),
    )
    workplan = build_industry_event_evidence_workplan_from_symbolic_score(
        score,
        candidate_path=EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
    )

    assert workplan["valid"] is True
    assert workplan["source_task_count"] == 2
    assert workplan["deferred_task_count"] == 1
    assert workplan["work_item_count"] == 2
    assert workplan["planned_request_count"] == 6
    assert workplan["planned_cache_count"] == 6
    assert workplan["existing_cache_count"] == 0
    assert workplan["missing_cache_count"] == 6
    assert workplan["cache_materialization_summary"]["all_cache_files_present"] is False
    assert workplan["draft_import_ready"] is False
    assert workplan["draft_import_readiness_gate"]["passed"] is False
    assert workplan["draft_import_readiness_gate"]["missing_cache_count"] == 6
    assert "industry-event-candidate-fetch-cache" in workplan["draft_import_readiness_gate"]["next_action"]
    readiness = workplan["readiness_summary"]
    assert readiness["status"] == "blocked"
    assert readiness["draft_import_ready"] is False
    assert readiness["missing_cache_count"] == 6
    assert readiness["deferred_blocked_gate_count"] == 15
    assert readiness["deferred_failed_integrity_check_count"] == 0
    assert {item["type"] for item in readiness["blocked_summary"]} == {
        "cache_materialization",
        "deferred_review_gates",
    }
    assert len(readiness["readiness_summary_receipt"]["sha256"]) == 64
    assert len(readiness["readiness_summary_sha256"]) == 64
    assert readiness["readiness_summary_receipt"]["material"]["deferred_blocked_gate_count"] == 15
    assert readiness["integrity_check"]["status"] == "passed"
    assert readiness["integrity_check"]["readiness_summary_receipt_matches_material"] is True
    assert readiness["integrity_check"]["readiness_summary_sha256_matches_material"] is True
    assert workplan["domains"] == ["film", "sports"]
    assert workplan["deferred_tasks"][0]["task_id"] == "industry-symbolic-music-career_project-add_reviewed_birth_profiles"
    assert workplan["deferred_tasks"][0]["blocked_case_ids"] == ["bob_dylan"]
    assert workplan["deferred_tasks"][0]["local_birth_profile_suggestion_count"] == 3
    assert [item["case_id"] for item in workplan["deferred_tasks"][0]["local_birth_profile_suggestions"]] == [
        "aretha_franklin",
        "madonna",
        "michael_jackson",
    ]
    assert all(
        "career_project" in item["supported_symbolic_event_topics"]
        for item in workplan["deferred_tasks"][0]["local_birth_profile_suggestions"]
    )
    gate_summary = workplan["deferred_tasks"][0]["gate_summary"]
    assert gate_summary["status"] == "blocked"
    assert gate_summary["blocked_gate_count"] >= 6
    assert gate_summary["failed_integrity_check_count"] == 0
    assert gate_summary["integrity_check_count"] >= 4
    blocked_gate_ids = {item["id"] for item in gate_summary["blocked_gates"]}
    assert "deferred_music_birth_profile_completion_reviewed" in blocked_gate_ids
    assert "local_music_source_review_requests_template_aligned" in blocked_gate_ids
    assert "local_music_query_template_patch_reviewed" in blocked_gate_ids
    assert "resolve blocked review gates" in gate_summary["next_action"]
    assert len(gate_summary["gate_summary_receipt"]["sha256"]) == 64
    assert len(gate_summary["gate_summary_sha256"]) == 64
    assert gate_summary["gate_summary_receipt"]["material"]["blocked_gate_count"] == gate_summary["blocked_gate_count"]
    assert gate_summary["integrity_check"]["status"] == "passed"
    assert gate_summary["integrity_check"]["gate_summary_receipt_matches_material"] is True
    assert gate_summary["integrity_check"]["gate_summary_sha256_matches_material"] is True
    completion = workplan["deferred_tasks"][0]["local_completion_work_order"]
    assert completion["status"] == "ready_for_human_review"
    assert completion["acceptance_gate"]["passed"] is False
    option_ids = {item["id"] for item in completion["strategy_options"]}
    assert option_ids == {"preserve_blocked_case", "use_local_singer_fixtures"}
    local_option = next(item for item in completion["strategy_options"] if item["id"] == "use_local_singer_fixtures")
    assert local_option["suggested_case_ids"] == ["aretha_franklin", "madonna", "michael_jackson"]
    draft_plan = local_option["draft_label_plan"]
    assert draft_plan["status"] == "draft_requires_source_review"
    assert draft_plan["record_count"] == 6
    assert draft_plan["positive_record_count"] == 3
    assert draft_plan["negative_record_count"] == 3
    assert draft_plan["acceptance_gate"]["passed"] is False
    assert len(draft_plan["draft_records_sha256"]) == 64
    assert len(draft_plan["draft_label_plan_receipt"]["sha256"]) == 64
    assert draft_plan["draft_label_plan_receipt"]["material"]["record_count"] == 6
    assert draft_plan["draft_label_plan_receipt"]["material"]["acceptance_gate"]["passed"] is False
    assert draft_plan["integrity_check"]["status"] == "passed"
    assert draft_plan["integrity_check"]["receipt_sha256_matches_material"] is True
    assert draft_plan["integrity_check"]["draft_records_sha256_matches_records"] is True
    assert draft_plan["integrity_check"]["recomputed_receipt_sha256"] == draft_plan["draft_label_plan_receipt"]["sha256"]
    assert draft_plan["integrity_check"]["recomputed_draft_records_sha256"] == draft_plan["draft_records_sha256"]
    review_plan = draft_plan["source_review_request_plan"]
    assert review_plan["status"] == "requires_query_template_review"
    assert review_plan["request_count"] == 6
    assert review_plan["query_template_alignment"]["exact_event_topic_template_available"] is False
    assert review_plan["query_template_alignment"]["nearest_existing_template_id"] == "wikidata_music_public_fame_events"
    assert review_plan["acceptance_gate"]["passed"] is False
    template_draft = review_plan["query_template_draft"]
    assert template_draft["status"] == "draft_requires_query_plan_review"
    assert template_draft["template"]["template_id"] == "wikidata_music_career_project_events_draft"
    assert template_draft["template"]["event_topic"] == "career_peak"
    assert template_draft["template"]["symbolic_event_topic"] == "career_project"
    assert template_draft["missing_required_template_fields"] == []
    assert len(template_draft["template_sha256"]) == 64
    assert template_draft["integrity_check"]["status"] == "passed"
    assert template_draft["integrity_check"]["template_sha256_matches_template"] is True
    assert template_draft["integrity_check"]["required_template_fields_complete"] is True
    assert template_draft["integrity_check"]["recomputed_template_sha256"] == template_draft["template_sha256"]
    patch_plan = template_draft["query_plan_patch_plan"]
    assert patch_plan["status"] == "draft_patch_requires_review"
    assert patch_plan["operation"] == "append_query_template"
    assert patch_plan["insert_after_template_id"] == "wikidata_music_public_fame_events"
    assert patch_plan["expected_existing_template_count"] == 3
    assert patch_plan["expected_template_count_after_patch"] == 4
    assert patch_plan["template_sha256"] == template_draft["template_sha256"]
    assert len(patch_plan["patch_plan_receipt"]["sha256"]) == 64
    assert len(patch_plan["patch_plan_sha256"]) == 64
    assert patch_plan["patch_plan_receipt"]["material"]["template_sha256"] == template_draft["template_sha256"]
    assert patch_plan["integrity_check"]["status"] == "passed"
    assert patch_plan["integrity_check"]["patch_plan_receipt_matches_material"] is True
    assert patch_plan["integrity_check"]["patch_plan_sha256_matches_material"] is True
    assert patch_plan["integrity_check"]["template_sha256_matches_template_draft"] is True
    applicability = patch_plan["applicability_check"]
    assert applicability["status"] == "applicable"
    assert applicability["target_path_exists"] is True
    assert applicability["current_template_count"] == 3
    assert applicability["current_template_count_matches_expected"] is True
    assert applicability["insert_point_present"] is True
    assert applicability["template_absent_from_target"] is True
    assert applicability["execution_gate"]["passed"] is False
    preview = patch_plan["patch_preview"]
    assert preview["status"] == "preview_ready"
    assert preview["would_write_file"] is False
    assert preview["patched_template_count"] == 4
    assert preview["inserted_template_id"] == "wikidata_music_career_project_events_draft"
    assert preview["patched_template_ids"] == [
        "wikidata_film_public_fame_events",
        "wikidata_music_public_fame_events",
        "wikidata_music_career_project_events_draft",
        "wikidata_sports_peak_events",
    ]
    assert len(preview["patched_query_plan_sha256"]) == 64
    assert len(preview["patch_preview_sha256"]) == 64
    assert len(preview["patch_preview_receipt"]["sha256"]) == 64
    assert preview["patch_preview_receipt"]["material"]["patched_template_count"] == 4
    assert preview["integrity_check"]["status"] == "passed"
    assert preview["integrity_check"]["patch_preview_receipt_matches_material"] is True
    assert preview["integrity_check"]["patch_preview_sha256_matches_material"] is True
    assert preview["integrity_check"]["patched_query_plan_sha256_matches_preview"] is True
    assert preview["execution_gate"]["passed"] is False
    assert patch_plan["acceptance_gate"]["passed"] is False
    assert template_draft["acceptance_gate"]["passed"] is False
    assert {request["case_id"] for request in review_plan["requests"]} == {
        "aretha_franklin",
        "madonna",
        "michael_jackson",
    }
    assert all("record_id" in request["required_manifest_fields"] for request in review_plan["requests"])
    draft_cases = {record["case_id"] for record in draft_plan["draft_records"]}
    assert draft_cases == {"aretha_franklin", "madonna", "michael_jackson"}
    assert {record["symbolic_event_topic"] for record in draft_plan["draft_records"]} == {"career_project"}
    assert all(record["license_or_review"] == "local_fixture_requires_industry_event_source_review" for record in draft_plan["draft_records"])
    assert "positive industry-event year" in local_option["required_artifacts"][0]
    assert "reviewed birth profiles" in workplan["deferred_tasks"][0]["next_action"]
    assert len(workplan["evidence_workplan_receipt"]["sha256"]) == 64
    work_by_domain = {item["domain"]: item for item in workplan["work_items"]}
    assert work_by_domain["film"]["candidate_case_ids"] == ["jackie_chan", "meryl_streep", "tom_hanks"]
    assert work_by_domain["sports"]["candidate_case_ids"] == [
        "roger_federer",
        "serena_williams",
        "michael_jordan",
    ]
    assert work_by_domain["film"]["additional_positive_labels_needed"] == 2
    assert work_by_domain["film"]["additional_negative_labels_needed"] == 2
    assert work_by_domain["film"]["fetch_cache_plan_summary"]["total_request_count"] == 3
    assert work_by_domain["film"]["fetch_cache_plan_summary"]["total_planned_cache_count"] == 3
    assert len(work_by_domain["film"]["fetch_cache_plan_summary"]["planned_cache_paths"]) == 3
    assert work_by_domain["film"]["cache_materialization_summary"]["existing_cache_count"] == 0
    assert work_by_domain["film"]["cache_materialization_summary"]["missing_cache_count"] == 3
    assert work_by_domain["film"]["draft_import_ready"] is False
    assert work_by_domain["film"]["draft_import_readiness_gate"]["passed"] is False
    assert len(work_by_domain["film"]["draft_import_readiness_gate"]["blocking_missing_cache_paths"]) == 3
    assert len(work_by_domain["film"]["fetch_cache_plan_summary"]["candidate_pool_fetch_cache_receipt_sha256"]) == 64
    assert work_by_domain["sports"]["fetch_cache_plan_summary"]["total_request_count"] == 3
    assert work_by_domain["sports"]["fetch_cache_plan_summary"]["total_planned_cache_count"] == 3
    assert all("industry-event-candidate-fetch-cache" in item["commands"][0]["command"] for item in workplan["work_items"])
    assert all("industry-event-candidate-draft-import" in item["commands"][1]["command"] for item in workplan["work_items"])

    result = industry_event_evidence_workplan(
        tmp_path / "repo",
        manifest_path=EXAMPLE_INDUSTRY_EVENT_MANIFEST,
        candidate_path=EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
    )
    assert result["evidence_workplan"]["work_item_count"] == 2
    assert "industry-event-evidence-workplan" in result["configuration_guidance"]["cli_command"]


def test_industry_event_manifest_status_exposes_gate_and_guidance(tmp_path):
    result = industry_event_manifest_status(tmp_path / "repo", EXAMPLE_INDUSTRY_EVENT_MANIFEST)

    assert result["configured"] is True
    assert result["audit"]["valid"] is True
    assert result["production_gate"]["id"] == "industry_event_source_provider_reviewed_manifest"
    assert result["production_gate"]["passed"] is False
    assert result["industry_event_manifest_receipt"]["material"]["record_count"] == 6
    assert "industry-events --manifest" in result["configuration_guidance"]["cli_audit_command"]
    assert result["configuration_guidance"]["example_is_demonstration_only"] is True


def test_industry_event_query_plan_audit_accepts_example_contract():
    audit = audit_industry_event_query_plan(EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN)
    receipt = industry_event_query_plan_receipt(audit)

    assert audit["valid"] is True
    assert audit["status"] == "ready_for_review"
    assert audit["collection_ready"] is False
    assert audit["externally_reviewed"] is False
    assert audit["live_collection_allowed"] is False
    assert audit["source_id"] == "wikidata_query_service"
    assert audit["template_count"] == 3
    assert audit["domains"] == ["film", "music", "sports"]
    assert audit["required_manifest_fields_mapped"] is True
    assert len(audit["content_hash"]) == 64
    assert receipt["schema_version"] == "industry-event-query-plan-audit-receipt-v1"
    assert receipt["material"]["content_hash"] == audit["content_hash"]
    assert receipt["material"]["collection_ready"] is False


def test_industry_event_query_plan_audit_rejects_missing_placeholder(tmp_path):
    payload = json.loads(EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN.read_text(encoding="utf-8"))
    payload["query_templates"][0]["placeholders"] = ["PERSON_QID", "START_YEAR"]
    query_plan = tmp_path / "industry_event_queries.json"
    query_plan.write_text(json.dumps(payload), encoding="utf-8")

    audit = audit_industry_event_query_plan(query_plan)

    assert audit["valid"] is False
    assert any("placeholders must be PERSON_QID" in failure for failure in audit["failures"])
    assert audit["collection_ready"] is False


def test_industry_event_query_plan_status_exposes_gate_and_guidance(tmp_path):
    result = industry_event_query_plan_status(tmp_path / "repo", EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN)

    assert result["configured"] is True
    assert result["audit"]["valid"] is True
    assert result["collection_gate"]["id"] == "industry_event_source_query_plan_reviewed"
    assert result["collection_gate"]["passed"] is False
    assert result["industry_event_query_plan_receipt"]["material"]["template_count"] == 3
    assert "industry-event-queries --query-plan" in result["configuration_guidance"]["cli_audit_command"]
    assert result["configuration_guidance"]["example_is_demonstration_only"] is True


def test_industry_event_candidate_cases_audit_accepts_example_contract():
    audit = audit_industry_event_candidate_cases(EXAMPLE_INDUSTRY_EVENT_CANDIDATES)
    receipt = industry_event_candidate_cases_receipt(audit)

    assert audit["valid"] is True
    assert audit["candidate_count"] == 9
    assert audit["domain_counts"] == {"film": 3, "music": 3, "sports": 3}
    assert audit["domains"] == ["film", "music", "sports"]
    assert "Q238819" in audit["person_qids"]
    assert audit["production_ready"] is False
    assert len(receipt["sha256"]) == 64
    assert receipt["material"]["domain_counts"]["sports"] == 3


def test_industry_event_candidate_cases_status_exposes_gate_and_guidance(tmp_path):
    result = industry_event_candidate_cases_status(tmp_path / "repo", EXAMPLE_INDUSTRY_EVENT_CANDIDATES)

    assert result["configured"] is True
    assert result["audit"]["valid"] is True
    assert result["candidate_pool_gate"]["id"] == "industry_event_candidate_pool_reviewed"
    assert result["candidate_pool_gate"]["passed"] is False
    assert result["audit"]["candidate_count"] == 9
    assert "industry-event-candidates --candidates" in result["configuration_guidance"]["cli_audit_command"]
    assert result["configuration_guidance"]["example_is_demonstration_only"] is True


def test_candidate_pool_fetch_cache_plan_expands_selected_candidates(tmp_path):
    result = build_candidate_pool_fetch_cache_plan(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        domain="sports",
    )

    assert result["status"] == "dry_run"
    assert result["valid"] is True
    assert result["offline_only"] is True
    assert result["candidate_count"] == 3
    assert result["plan_count"] == 3
    assert result["total_request_count"] == 3
    assert result["total_planned_cache_count"] == 3
    assert result["total_cache_write_count"] == 0
    assert result["domains"] == ["sports"]
    assert result["case_ids"] == ["roger_federer", "serena_williams", "michael_jordan"]
    assert len(result["candidate_pool_fetch_cache_receipt"]["sha256"]) == 64
    assert all(plan["status"] == "dry_run" for plan in result["plans"])


def test_candidate_pool_fetch_cache_api_exposes_batch_plan(tmp_path):
    result = industry_event_candidate_pool_fetch_cache(
        tmp_path / "repo",
        candidate_path=EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        domain="music",
    )
    batch_plan = result["candidate_pool_fetch_cache_plan"]

    assert result["live_requested"] is False
    assert batch_plan["valid"] is True
    assert batch_plan["candidate_count"] == 3
    assert batch_plan["domains"] == ["music"]
    assert batch_plan["total_planned_cache_count"] == 3
    assert "industry-event-candidate-fetch-cache" in result["configuration_guidance"]["cli_command"]


def test_candidate_pool_manifest_drafts_from_cache_imports_selected_candidates(tmp_path):
    batch_plan = build_candidate_pool_fetch_cache_plan(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        domain="sports",
    )
    materialize_cached_responses(batch_plan, EXAMPLE_WIKIDATA_SPORTS_RESPONSE)

    result = build_candidate_pool_manifest_drafts_from_cache(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        domain="sports",
    )

    assert result["status"] == "ready_for_review"
    assert result["valid"] is True
    assert result["offline_only"] is True
    assert result["candidate_count"] == 3
    assert result["draft_count"] == 3
    assert result["missing_response_count"] == 0
    assert result["positive_record_count"] == 3
    assert result["negative_record_count"] == 70
    assert result["record_count"] == 73
    assert result["combined_draft_manifest_audit"]["valid"] is True
    assert result["combined_draft_manifest_audit"]["record_count"] == 73
    assert result["combined_draft_manifest_audit"]["positive_event_count"] == 3
    assert result["combined_draft_manifest_audit"]["negative_event_count"] == 70
    assert len(result["combined_draft_manifest_audit_receipt"]["sha256"]) == 64
    assert result["combined_draft_manifest"]["status"] == "draft_candidate_pool_from_cached_responses_not_production_evidence"
    assert result["validation_label_table"]["record_count"] == 73
    assert result["validation_label_table"]["positive_label_count"] == 3
    assert result["validation_label_table"]["negative_label_count"] == 70
    assert result["validation_label_table"]["domain_coverage_summary"][0]["domain"] == "sports"
    assert result["validation_label_table"]["cross_domain_coverage_gate"]["passed"] is False
    assert result["validation_label_table"]["cross_domain_coverage_gate"]["missing_domains"] == ["film", "music"]
    assert len(result["validation_label_table"]["validation_label_table_receipt"]["sha256"]) == 64
    assert len(result["candidate_pool_draft_import_receipt"]["sha256"]) == 64
    assert all(draft["manifest_valid"] is True for draft in result["drafts"])


def test_candidate_pool_manifest_drafts_from_cache_imports_all_domains(tmp_path):
    batch_plan = build_candidate_pool_fetch_cache_plan(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
    )
    materialize_cached_responses_by_domain(
        batch_plan,
        {
            "film": EXAMPLE_WIKIDATA_FILM_RESPONSE,
            "music": EXAMPLE_WIKIDATA_MUSIC_RESPONSE,
            "sports": EXAMPLE_WIKIDATA_SPORTS_RESPONSE,
        },
    )

    result = build_candidate_pool_manifest_drafts_from_cache(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
    )

    assert result["status"] == "ready_for_review"
    assert result["valid"] is True
    assert result["candidate_count"] == 9
    assert result["draft_count"] == 9
    assert result["domains"] == ["film", "music", "sports"]
    assert result["positive_record_count"] == 9
    assert result["negative_record_count"] == 273
    assert result["record_count"] == 282
    assert result["combined_manifest_valid"] is True
    assert result["combined_manifest_positive_event_count"] == 9
    assert result["combined_manifest_negative_event_count"] == 273
    label_table = result["validation_label_table"]
    assert label_table["record_count"] == 282
    assert label_table["positive_label_count"] == 9
    assert label_table["negative_label_count"] == 273
    assert label_table["cross_domain_coverage_gate"]["passed"] is True
    assert {item["domain"] for item in label_table["domain_coverage_summary"]} == {
        "film",
        "music",
        "sports",
    }
    assert {
        (item["domain"], item["positive_label_count"], item["negative_label_count"])
        for item in label_table["domain_coverage_summary"]
    } == {
        ("film", 3, 134),
        ("music", 3, 69),
        ("sports", 3, 70),
    }


def test_candidate_pool_manifest_draft_import_reports_missing_cache(tmp_path):
    result = build_candidate_pool_manifest_drafts_from_cache(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "missing-cache",
        domain="sports",
    )

    assert result["valid"] is False
    assert result["status"] == "invalid"
    assert result["draft_count"] == 0
    assert result["missing_response_count"] == 3
    assert len(result["missing_response_paths"]) == 3
    assert any("missing cached response" in failure for failure in result["failures"])


def test_candidate_pool_manifest_draft_import_api_exposes_summary(tmp_path):
    batch_plan = build_candidate_pool_fetch_cache_plan(
        EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        domain="sports",
    )
    materialize_cached_responses(batch_plan, EXAMPLE_WIKIDATA_SPORTS_RESPONSE)

    result = industry_event_candidate_pool_draft_import(
        tmp_path / "repo",
        candidate_path=EXAMPLE_INDUSTRY_EVENT_CANDIDATES,
        query_plan_path=EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        domain="sports",
    )
    draft_import = result["candidate_pool_draft_import"]

    assert draft_import["valid"] is True
    assert draft_import["draft_count"] == 3
    assert draft_import["positive_record_count"] == 3
    assert draft_import["combined_manifest_valid"] is True
    assert draft_import["combined_manifest_record_count"] == 73
    assert "industry-event-candidate-draft-import" in result["configuration_guidance"]["cli_command"]


def test_industry_event_collection_request_bundle_expands_queries_offline():
    result = build_industry_event_collection_request_bundle(
        EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        case_id="roger_federer",
        public_name="Roger Federer",
        person_qid="Q1426",
        start_year=2002,
        end_year=2004,
        split_role="holdout",
        domain="sports",
    )

    assert result["valid"] is True
    assert result["status"] == "ready_for_review"
    assert result["request_count"] == 1
    assert result["domains"] == ["sports"]
    assert result["execution_gate"]["passed"] is False
    assert result["execution_gate"]["live_execution_allowed"] is False
    request = result["requests"][0]
    assert request["template_id"] == "wikidata_sports_peak_events"
    assert "Q1426" in request["expanded_sparql"]
    assert "START_YEAR" not in request["expanded_sparql"]
    assert request["query_url"].startswith("https://query.wikidata.org/sparql?")
    assert request["manifest_record_preview"]["case_id"] == "roger_federer"
    assert request["manifest_record_preview"]["split_role"] == "holdout"
    assert len(request["request_sha256"]) == 64
    assert len(result["bundle_receipt"]["sha256"]) == 64
    assert result["bundle_receipt"]["material"]["request_sha256s"] == [request["request_sha256"]]


def test_industry_event_collection_request_bundle_rejects_bad_qid():
    result = build_industry_event_collection_request_bundle(
        EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        case_id="bad_case",
        public_name="Bad Case",
        person_qid="not-a-qid",
        start_year=2000,
        end_year=2001,
        split_role="holdout",
    )

    assert result["valid"] is False
    assert any("person_qid must look like Q123" in failure for failure in result["failures"])
    assert result["execution_gate"]["passed"] is False


def test_industry_event_fetch_cache_plan_dry_run_does_not_fetch(tmp_path):
    result = build_industry_event_fetch_cache_plan(
        EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        case_id="roger_federer",
        public_name="Roger Federer",
        person_qid="Q1426",
        start_year=2002,
        end_year=2004,
        split_role="holdout",
        domain="sports",
    )

    assert result["status"] == "dry_run"
    assert result["valid"] is True
    assert result["offline_only"] is True
    assert result["planned_cache_count"] == 1
    assert result["cache_write_count"] == 0
    assert result["execution_gate"]["passed"] is False
    assert result["cache_entries"][0]["cache_path"].endswith(".json")
    assert len(result["fetch_cache_receipt"]["sha256"]) == 64


def test_industry_event_fetch_cache_plan_live_requires_reviewed_collection_ready(tmp_path):
    result = build_industry_event_fetch_cache_plan(
        EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        cache_dir=tmp_path / "cache",
        case_id="roger_federer",
        public_name="Roger Federer",
        person_qid="Q1426",
        start_year=2002,
        end_year=2004,
        split_role="holdout",
        domain="sports",
        live=True,
    )

    assert result["status"] == "blocked"
    assert result["valid"] is False
    assert result["cache_write_count"] == 0
    assert result["execution_gate"]["passed"] is False
    assert any("live collection requires reviewed collection_ready query plan" in failure for failure in result["failures"])


def test_industry_event_manifest_draft_from_cached_response_adds_negative_years():
    result = build_industry_event_manifest_draft_from_wikidata_response(
        EXAMPLE_INDUSTRY_EVENT_QUERY_PLAN,
        EXAMPLE_WIKIDATA_SPORTS_RESPONSE,
        case_id="roger_federer",
        public_name="Roger Federer",
        person_qid="Q1426",
        start_year=2002,
        end_year=2004,
        split_role="holdout",
        domain="sports",
    )

    assert result["valid"] is True
    assert result["offline_only"] is True
    assert result["draft_manifest_audit"]["valid"] is True
    assert result["draft_manifest_audit"]["positive_event_count"] == 1
    assert result["draft_manifest_audit"]["negative_event_count"] == 2
    assert len(result["draft_receipt"]["sha256"]) == 64
    records = result["draft_manifest"]["records"]
    assert [record["year"] for record in records] == [2003, 2002, 2004]
    assert records[0]["event_present"] is True
    assert records[1]["event_present"] is False
    assert "offline response hash" in records[1]["negative_year_reason"]


def test_outcome_dataset_audit_unconfigured_boundary():
    result = outcome_dataset_audit()

    assert result["status"] == "not_configured"
    assert result["predictive_optimization_enabled"] is False
    assert result["quality_task_projection"]["projected_task_count"] == 0
    assert result["data_split_record_coverage"]["coverage_complete"] is False
