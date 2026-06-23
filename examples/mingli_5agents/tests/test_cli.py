"""Tests for the persistent mingli SEMAS CLI."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

from examples.mingli_5agents.api_core import _provider_recertification_commands
from examples.mingli_5agents.cli import main


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def read_stdout_json(capsys) -> dict:
    captured = capsys.readouterr()
    return json.loads(captured.out)


def source_governance_fields() -> dict[str, str]:
    return {
        "license": "CC0-1.0",
        "rights_basis": "test fixture authored for repository validation",
        "review_status": "open_license_reviewed",
        "reviewed_by": "cli test",
        "content_scope": "method metadata fixture only",
    }


def test_provider_recertification_commands_are_domain_specific(tmp_path: Path):
    commands = _provider_recertification_commands(
        tmp_path / "repo",
        [
            "qimen latest certification is missing provider request receipt",
            "astrology latest certification is missing reference contract coverage",
            "qimen latest certification is missing reference contract coverage",
        ],
    )

    assert any("certify-provider astrology --command" in command and "--record" in command for command in commands)
    assert any("certify-provider qimen --command" in command and "--record" in command for command in commands)
    assert not any("certify-provider ziwei --command" in command for command in commands)
    assert commands[-1].endswith("provider-ledger")


def test_cli_provider_examples_emits_protocol_receipt(tmp_path: Path, capsys):
    repo = tmp_path / "repo"

    assert main(["--repo", str(repo), "provider-examples"]) == 0
    result = read_stdout_json(capsys)

    assert result["status"] == "passed"
    assert result["production_certification_allowed"] is False
    assert set(result["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert all(item["live_passed"] is True for item in result["domains"].values())
    assert all(item["command_is_bundled_example"] is True for item in result["domains"].values())
    assert len(result["example_provider_receipt"]["sha256"]) == 64


def test_cli_provider_onboarding_emits_gap_receipt(tmp_path: Path, capsys):
    repo = tmp_path / "repo"

    assert main(["--repo", str(repo), "provider-onboarding"]) == 0
    result = read_stdout_json(capsys)

    assert result["status"] == "actions_required"
    assert set(result["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert result["provider_onboarding_receipt"]["material"]["ready_domain_count"] == 0
    assert result["provider_onboarding_receipt"]["material"]["missing_evidence_by_domain"]["ziwei"] == result[
        "domains"
    ]["ziwei"]["missing_evidence"]
    assert result["provider_onboarding_receipt"]["material"]["missing_evidence_counts"][
        "certified_provider_ledger_record"
    ] == 4
    assert len(result["provider_onboarding_receipt"]["sha256"]) == 64
    assert len(result["example_provider_receipt"]["sha256"]) == 64
    ziwei = result["domains"]["ziwei"]
    assert ziwei["env_var"] == "SEMAS_ZIWEI_CLI"
    assert "production_provider_provenance" in ziwei["missing_evidence"]
    assert "certified_provider_ledger_record" in ziwei["missing_evidence"]
    assert "certify-provider ziwei" in ziwei["certification_command"]
    assert ziwei["bundled_example_smoke"]["live_passed"] is True
    assert ziwei["bundled_example_smoke"]["production_certification_allowed"] is False


def test_cli_known_gap_handoff_exports_portable_bundle(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    export_path = tmp_path / "handoff.json"

    assert main(["--repo", str(repo), "known-gap-handoff"]) == 0
    result = read_stdout_json(capsys)

    assert result["schema_version"] == "known-gap-handoff-export-v1"
    assert result["status"] == "ready"
    assert result["audit_receipt_matches_expected"] is None
    assert len(result["audit_receipt_sha256"]) == 64
    assert len(result["handoff_export_receipt"]["sha256"]) == 64
    assert result["handoff_export_receipt"]["material"]["bundle_sha256"] == result["known_gap_handoff_bundle"][
        "bundle_sha256"
    ]
    assert result["handoff_export_receipt"]["material"]["audit_receipt_sha256"] == result["audit_receipt_sha256"]
    bundle = result["known_gap_handoff_bundle"]
    assert bundle["status"] == "ready"
    assert bundle["gap_count"] == len(result["known_gap_ids"])
    assert len(bundle["bundle_sha256"]) == 64
    by_gap = {item["gap_id"]: item for item in bundle["items"]}
    assert by_gap["professional_ziwei_provider"]["required_env_vars"] == ["SEMAS_ZIWEI_CLI"]
    assert by_gap["professional_qimen_provider"]["required_provenance_env_vars"] == [
        "SEMAS_QIMEN_PROVIDER_PROVENANCE"
    ]
    assert any(
        candidate["name"] == "kinqimen"
        for candidate in by_gap["professional_qimen_provider"]["external_candidate_projects"]
    )
    write_json(export_path, result)

    assert main(["--repo", str(repo), "known-gap-handoff-verify", "--input", str(export_path)]) == 0
    verification = read_stdout_json(capsys)
    assert verification["schema_version"] == "known-gap-handoff-export-verification-v1"
    assert verification["valid"] is True
    assert verification["failures"] == []
    assert verification["bundle_hash_valid"] is True
    assert verification["receipt_hash_valid"] is True
    assert verification["receipt_material_valid"] is True
    assert verification["known_gap_ids_match_bundle"] is True

    assert main(
        [
            "--repo",
            str(repo),
            "known-gap-handoff-verify",
            "--input",
            str(export_path),
            "--expected-handoff-export-receipt-sha256",
            result["handoff_export_receipt"]["sha256"],
        ]
    ) == 0
    matched = read_stdout_json(capsys)
    assert matched["handoff_export_receipt_matches_expected"] is True

    tampered = json.loads(export_path.read_text(encoding="utf-8"))
    tampered["known_gap_handoff_bundle"]["items"][0]["owner_domain"] = "tampered"
    write_json(export_path, tampered)
    assert main(["--repo", str(repo), "known-gap-handoff-verify", "--input", str(export_path)]) == 0
    tampered_verification = read_stdout_json(capsys)
    assert tampered_verification["valid"] is False
    assert tampered_verification["bundle_hash_valid"] is False
    assert "known_gap_handoff_bundle.bundle_sha256 does not match bundle content" in tampered_verification["failures"]

    export_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-16")
    assert main(["--repo", str(repo), "known-gap-handoff-verify", "--input", str(export_path)]) == 0
    utf16_verification = read_stdout_json(capsys)
    assert utf16_verification["valid"] is True

    write_json(export_path, result)
    assert main(["--repo", str(repo), "known-gap-handoff-checklist", "--input", str(export_path)]) == 0
    checklist = read_stdout_json(capsys)
    assert checklist["schema_version"] == "known-gap-handoff-checklist-v1"
    assert checklist["status"] == "ready"
    assert checklist["verification"]["valid"] is True
    assert checklist["item_count"] == len(result["known_gap_ids"])
    assert checklist["ready_item_count"] == checklist["item_count"]
    assert checklist["expected_checklist_receipt_sha256"] is None
    assert checklist["checklist_receipt_matches_expected"] is None
    assert checklist["checklist_receipt_mismatch_reason"] == ""
    assert len(checklist["checklist_receipt"]["sha256"]) == 64
    assert checklist["checklist_receipt"]["material"]["handoff_export_receipt_sha256"] == result[
        "handoff_export_receipt"
    ]["sha256"]
    checklist_by_gap = {item["gap_id"]: item for item in checklist["items"]}
    assert checklist_by_gap["professional_ziwei_provider"]["required_env_vars"] == ["SEMAS_ZIWEI_CLI"]
    assert "Run every verification command after implementation." in checklist_by_gap["professional_ziwei_provider"][
        "checklist"
    ]

    assert main(
        [
            "--repo",
            str(repo),
            "known-gap-handoff-checklist",
            "--input",
            str(export_path),
            "--expected-checklist-receipt-sha256",
            checklist["checklist_receipt"]["sha256"],
        ]
    ) == 0
    matched_checklist = read_stdout_json(capsys)
    assert matched_checklist["checklist_receipt_matches_expected"] is True
    assert matched_checklist["checklist_receipt_mismatch_reason"] == ""

    assert main(
        [
            "--repo",
            str(repo),
            "known-gap-handoff-checklist",
            "--input",
            str(export_path),
            "--expected-checklist-receipt-sha256",
            "0" * 64,
        ]
    ) == 0
    mismatched_checklist = read_stdout_json(capsys)
    assert mismatched_checklist["checklist_receipt_matches_expected"] is False
    assert "does not match expected_checklist_receipt_sha256" in mismatched_checklist[
        "checklist_receipt_mismatch_reason"
    ]


def test_cli_classical_refresh_ingests_file_source(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    remote_manifest = tmp_path / "remote_manifest.json"
    write_json(
        remote_manifest,
        {
            "records": [
                {
                    "source_id": "ziwei_palace",
                    "passage_id": "cli_refresh_case",
                    "title": "CLI refresh case",
                    "tradition": "ziwei",
                    "keywords": ["cli", "refresh"],
                    "summary": "CLI refresh fixture.",
                    "caution": "Fixture only.",
                    "source_url": "https://example.org/cli-refresh",
                    "license": "CC0-1.0",
                    "citation_policy": "paraphrase_only",
                }
            ]
        },
    )
    source_list = tmp_path / "sources.json"
    write_json(
        source_list,
        {
            "allow_file_urls": True,
            "sources": [{"name": "cli-refresh-fixture", "url": remote_manifest.as_uri(), **source_governance_fields()}],
        },
    )

    assert (
        main(
            [
                "--repo",
                str(repo),
                "classical-refresh",
                "--source-list",
                str(source_list),
                "--cache-dir",
                str(tmp_path / "cache"),
                "--output-dir",
                str(tmp_path / "corpus"),
            ]
        )
        == 0
    )
    result = read_stdout_json(capsys)

    assert result["status"] == "refreshed"
    assert result["refreshed"] is True
    assert result["refresh"]["record_count"] == 1
    assert result["source_list_path"] == str(source_list)
    assert len(result["source_list_receipt"]["sha256"]) == 64
    assert (tmp_path / "cache" / "cli-refresh-fixture.manifest.json").exists()
    assert any((tmp_path / "corpus").glob("*.jsonl"))


def test_cli_init_analyze_evolve_status(tmp_path: Path, capsys, monkeypatch):
    repo = tmp_path / "repo"
    birth_path = tmp_path / "birth.json"
    feedback_path = tmp_path / "feedback.json"
    write_json(
        birth_path,
        {
            "birth": {
                "name": "CLI Person",
                "birth_date": "1991-05-20",
                "birth_time": "10:15",
                "gender": "unspecified",
                "birthplace": "Suzhou",
            }
        },
    )
    write_json(
        feedback_path,
        {
            "feedback": {
                "satisfaction": 0.5,
                "corrections": ["too vague", "weak source labels", "needs uncertainty boundary"],
            }
        },
    )

    assert main(["--repo", str(repo), "init"]) == 0
    init_result = read_stdout_json(capsys)
    assert init_result["status"] == "initialized"
    assert init_result["coordinator_version"] == 1

    assert main(["--repo", str(repo), "analyze", "--input", str(birth_path)]) == 0
    analyze_result = read_stdout_json(capsys)
    assert analyze_result["agent_version"] == 1
    assert analyze_result["metrics"]["citation"] == 1.0
    assert analyze_result["result"]["source_review"]["status"] == "pass"

    assert main(
        [
            "--repo",
            str(repo),
            "evolve",
            "--input",
            str(birth_path),
            "--feedback",
            str(feedback_path),
            "--validate-on-input",
        ]
    ) == 0
    evolve_result = read_stdout_json(capsys)
    assert evolve_result["accepted"] is True
    assert evolve_result["after_version"] == 2
    assert evolve_result["selected"]
    assert evolve_result["trigger_receipt"]["schema_version"] == "evolution-trigger-receipt-v1"
    assert len(evolve_result["trigger_receipt"]["sha256"]) == 64
    assert "explicit_feedback" in evolve_result["trigger_receipt"]["material"]["trigger_reasons"]
    assert "operator_requested_input_validation" in evolve_result["trigger_receipt"]["material"]["trigger_reasons"]
    assert evolve_result["trigger_receipt"]["material"]["feedback_present"] is True
    assert evolve_result["trigger_receipt"]["material"]["feedback_correction_count"] == 3
    assert evolve_result["trigger_receipt"]["material"]["validate_on_input"] is True
    assert evolve_result["validation_case_count"] >= 2
    assert evolve_result["trigger_receipt"]["material"]["validation_task_count"] == evolve_result["validation_case_count"]
    assert evolve_result["archive_events"] == 1
    assert evolve_result["memory_profile"]["total_events"] >= 2
    assert evolve_result["memory_profile"]["unsafe_feedback_count"] == 0
    assert evolve_result["selection_decision"]["accepted"] is True
    assert evolve_result["selection_decision"]["validation_task_count"] == evolve_result["validation_case_count"]
    assert all(evolve_result["selection_decision"]["gates"].values())

    assert main(["--repo", str(repo), "status"]) == 0
    status_result = read_stdout_json(capsys)
    assert status_result["coordinator_version"] == 2
    assert status_result["genome_lineage"]["accepted_genome_version"] == 2
    assert status_result["genome_lineage"]["archive_hash"] == status_result["latest_evolution"]["archive_hash"]
    assert len(status_result["genome_lineage"]["genome_fingerprint"]) == 64
    assert status_result["genome_lineage"]["selection_decision"]["accepted"] is True
    assert status_result["genome_lineage"]["trigger_receipt"] == evolve_result["trigger_receipt"]
    assert status_result["lineage_integrity"]["status"] == "pass"
    assert status_result["lineage_integrity"]["archive_hash_matches_latest"] is True
    assert status_result["lineage_integrity"]["genome_fingerprint_matches"] is True
    assert status_result["lineage_integrity"]["trigger_receipt_matches"] is True
    assert status_result["lineage_integrity"]["reproducibility_manifest_matches"] is True
    assert status_result["archive_events"] == 1
    assert status_result["calendar_providers"]["default"] == "auto"
    assert "auto" in status_result["calendar_providers"]["providers"]
    assert "professional" in status_result["calendar_providers"]["providers"]
    assert status_result["domain_chart_providers"]["ziwei"]["external_injection_supported"] is True
    assert status_result["llm_backend"]["provider"] in {"stub", "openai", "openai_compatible", "kimi_openai_compatible", "deepseek_openai_compatible"}
    assert status_result["llm_backend"]["safe_to_report"] is True
    assert status_result["memory_profile"]["total_events"] >= 2
    assert status_result["memory_profile"]["unsafe_feedback_count"] == 0
    assert status_result["archive_integrity"]["status"] == "pass"
    assert status_result["archive_integrity"]["hashed_event_count"] == 1
    assert status_result["latest_evolution"]["event"] == "population_evolution"
    assert status_result["latest_evolution"]["accepted"] is True
    assert len(status_result["latest_evolution"]["archive_hash"]) == 64
    assert status_result["latest_evolution"]["selection_decision"]["accepted"] is True
    assert status_result["latest_evolution"]["trigger_receipt"] == evolve_result["trigger_receipt"]
    assert status_result["latest_evolution"]["reproducibility_manifest"]["run_type"] == "population_evolution"

    assert main(["--repo", str(repo), "history"]) == 0
    history_result = read_stdout_json(capsys)
    assert history_result["agent_name"] == "mingli_orchestrator"
    assert history_result["latest_version"] == 2
    assert history_result["version_count"] == 2
    assert history_result["archive_integrity"]["status"] == "pass"
    assert history_result["history_integrity"]["status"] == "pass"
    assert history_result["history_integrity"]["checked_versions"] == 2
    assert history_result["history_integrity"]["version_sequence_contiguous"] is True
    assert [item["version"] for item in history_result["versions"]] == [1, 2]
    assert history_result["versions"][0]["lineage_present"] is False
    assert history_result["versions"][0]["lineage_fingerprint_matches"] is True
    assert history_result["versions"][1]["lineage_event"] == "population_evolution"
    assert history_result["versions"][1]["trigger_receipt_sha256"] == evolve_result["trigger_receipt"]["sha256"]
    assert history_result["versions"][1]["archive_event_found"] is True
    assert history_result["versions"][1]["lineage_fingerprint_matches"] is True

    assert main(["--repo", str(repo), "audit"]) == 0
    audit_result = read_stdout_json(capsys)
    assert audit_result["status"] == "operational_with_known_gaps"
    assert audit_result["is_state_of_the_art"] == "partial"
    assert audit_result["state_of_art"]["verdict"] == "advanced_agentic_framework_not_full_domain_sota"
    assert audit_result["state_of_art"]["production_ready_for_professional_calculation"] is False
    assert audit_result["state_of_art"]["request_scoped_production_ready_path"] is True
    assert audit_result["state_of_art"]["request_scoped_provenance_required"] is True
    assert audit_result["state_of_art"]["production_input_geocoding"] is True
    assert audit_result["state_of_art"]["birthplace_geocoding_production_gate"] == "benchmark_birthplaces_geocoded"
    assert audit_result["state_of_art"]["deliberation_receipt_production_gate"] == (
        "benchmark_deliberation_receipts_bound"
    )
    assert audit_result["state_of_art"]["blocking_provider_scope"] == "environment_configured_backends"
    assert "professional_ziwei_provider_available" in audit_result["state_of_art"]["blocking_provider_capabilities"]
    assert audit_result["capabilities"]["feedback_memory_safety_quarantine"] is True
    assert audit_result["capabilities"]["archive_hash_chain"] is True
    assert audit_result["capabilities"]["genome_lineage_integrity"] is True
    assert audit_result["capabilities"]["version_history_lineage_view"] is True
    assert audit_result["capabilities"]["audited_rollback"] is True
    assert audit_result["capabilities"]["reproducibility_manifest_strategy_fingerprints"] is True
    assert audit_result["capabilities"]["evolution_cost_governance_manifest"] is True
    assert audit_result["feedback_memory_safety"]["status"] == "clean"
    assert audit_result["feedback_memory_safety"]["unsafe_feedback_count"] == 0
    comparison_dimensions = {item["dimension"] for item in audit_result["github_comparison_matrix"]}
    assert {
        "multi_agent_evolution",
        "ziwei_calculation",
        "qimen_calculation",
        "western_astrology",
        "calendar_and_xuanze",
        "empirical_validation",
        "classical_evidence",
        "provider_protocol_governance",
        "release_governance",
    }.issubset(comparison_dimensions)
    assert audit_result["capabilities"]["five_agents"] is True
    assert audit_result["capabilities"]["classical_source_refresh_governance"] is True
    assert audit_result["capabilities"]["classical_source_refresh_receipt"] is True
    assert any(item["id"] == "classical_source_refresh_pipeline" for item in audit_result["implemented_requirements"])
    assert audit_result["classical_source_refresh"]["status"] == "ready"
    assert audit_result["classical_source_refresh"]["source_count"] == 1
    assert audit_result["classical_source_refresh"]["locked_source_count"] == 1
    assert audit_result["classical_source_list_path"].endswith("classical_source_list_example.json")
    assert audit_result["capabilities"]["classical_source_refresh_configured"] is True
    assert len(audit_result["classical_source_refresh"]["source_list_receipt"]["sha256"]) == 64
    audit_source_list = tmp_path / "audit_classical_sources.json"
    write_json(
        audit_source_list,
        {
            "allowed_hosts": ["classics.example"],
            "sources": [
                {
                    "name": "locked-classics",
                    "url": "https://classics.example/manifest.json",
                    "sha256": "a" * 64,
                    **source_governance_fields(),
                }
            ],
        },
    )
    assert main(["--repo", str(repo), "audit", "--classical-source-list", str(audit_source_list)]) == 0
    audit_with_classical_sources = read_stdout_json(capsys)
    assert audit_with_classical_sources["classical_source_refresh"]["status"] == "ready"
    assert audit_with_classical_sources["classical_source_refresh"]["locked_source_count"] == 1
    assert len(audit_with_classical_sources["classical_source_refresh"]["source_list_receipt"]["sha256"]) == 64
    assert audit_with_classical_sources["capabilities"]["classical_source_refresh_configured"] is True
    assert (
        audit_with_classical_sources["audit_receipt"]["material"]["classical_source_refresh"]["status"]
        == "ready"
    )
    assert (
        audit_with_classical_sources["audit_receipt"]["material"]["classical_source_refresh"][
            "source_list_receipt_sha256"
        ]
        == audit_with_classical_sources["classical_source_refresh"]["source_list_receipt"]["sha256"]
    )
    assert audit_with_classical_sources["audit_receipt"]["material"]["classical_source_refresh"][
        "source_audit_count"
    ] == 1
    assert audit_with_classical_sources["audit_receipt"]["material"]["classical_source_refresh"][
        "refreshable_source_count"
    ] == 1
    assert (
        main(
            [
                "--repo",
                str(repo),
                "audit",
                "--classical-source-list",
                str(audit_source_list),
                "--expected-audit-receipt-sha256",
                audit_with_classical_sources["audit_receipt"]["sha256"],
            ]
        )
        == 0
    )
    matched_source_audit = read_stdout_json(capsys)
    assert matched_source_audit["audit_receipt_matches_expected"] is True
    assert audit_result["plan_compliance"]["section_count"] == 10
    plan_receipt = audit_result["plan_compliance"]["source_receipt"]
    assert plan_receipt["path"] == "plan_mingli5agents.md"
    assert plan_receipt["exists"] is True
    assert plan_receipt["readable"] is True
    assert plan_receipt["encoding"] == "utf-8"
    assert plan_receipt["section_heading_count"] == 10
    assert len(plan_receipt["sha256"]) == 64
    assert audit_result["audit_receipt"]["material"]["plan_compliance"]["source_receipt"] == plan_receipt
    assert "5_collaboration_workflow" in audit_result["plan_compliance"]["sections_with_gaps"]
    section_gap_coverage = audit_result["plan_compliance"]["section_gap_resolution_coverage"]
    assert section_gap_coverage["status"] == "covered"
    assert section_gap_coverage["sections_with_unplanned_gaps"] == []
    assert audit_result["audit_receipt"]["material"]["plan_compliance"]["section_gap_resolution_coverage"] == (
        section_gap_coverage
    )
    section_gap_by_section = {item["section"]: item for item in section_gap_coverage["sections"]}
    assert section_gap_by_section["5_collaboration_workflow"]["planned_gap_ids"] == ["external_classic_text_retrieval"]
    assert section_gap_by_section["6_evolution_mechanism"]["planned_gap_ids"] == ["empirical_validation_dataset"]
    assert audit_result["capabilities"]["reference_chart_contracts"] is True
    assert audit_result["capabilities"]["request_scoped_full_external_provider_injection"] is True
    assert audit_result["capabilities"]["request_scoped_external_provider_provenance"] is True
    assert audit_result["capabilities"]["request_scoped_external_payload_receipts"] is True
    assert audit_result["capabilities"]["request_scoped_external_payload_birth_match_audit"] is True
    assert audit_result["capabilities"]["provider_interpretation_readiness_matrix"] is True
    assert audit_result["capabilities"]["topic_synthesis_confidence_audit"] is True
    assert audit_result["capabilities"]["empirical_topic_confidence_gate"] is True
    assert audit_result["request_scoped_provider_contract"]["status"] == "ready"
    assert audit_result["request_scoped_provider_contract"]["checked_domains"] == [
        "astrology",
        "bazi",
        "qimen",
        "xuanze",
        "ziwei",
    ]
    assert audit_result["request_scoped_provider_contract"]["provenance_checked_domains"] == [
        "astrology",
        "bazi",
        "qimen",
        "xuanze",
        "ziwei",
    ]
    assert audit_result["request_scoped_provider_contract"]["requires_provenance_fields"] == [
        "source",
        "version",
        "license_or_review",
    ]
    assert audit_result["capabilities"]["classical_text_index"] is True
    assert audit_result["capabilities"]["empirical_validation_harness"] is True
    assert audit_result["capabilities"]["outcome_dataset_cli_api_audit"] is True
    assert audit_result["capabilities"]["outcome_dataset_external_review_gate"] is True
    assert audit_result["capabilities"]["outcome_dataset_frozen_holdout_gate"] is True
    assert audit_result["capabilities"]["outcome_dataset_data_split_records_covered"] is True
    assert audit_result["capabilities"]["outcome_dataset_label_collection_pre_analysis_gate"] is True
    assert audit_result["capabilities"]["production_readiness_gate"] is True
    assert audit_result["capabilities"]["birthplace_geocoding_provenance"] is True
    assert audit_result["capabilities"]["birthplace_geocoding_production_gate"] is True
    assert audit_result["capabilities"]["provider_certification_cli_api"] is True
    assert audit_result["capabilities"]["provider_protocol_hash_governance"] is True
    assert audit_result["capabilities"]["provider_protocol_identity_handshake"] is True
    assert audit_result["capabilities"]["provider_ledger_protocol_stale_gate"] is True
    assert audit_result["capabilities"]["provider_ledger_latest_record_binding"] is True
    assert audit_result["capabilities"]["provider_certification_reference_contract_coverage"] is True
    assert audit_result["capabilities"]["provider_ledger_reference_contract_gate"] is True
    assert audit_result["capabilities"]["release_manifest_governance"] is True
    assert audit_result["capabilities"]["release_manifest_ledger_hash_chain"] is True
    assert audit_result["capabilities"]["release_manifest_ledger_latest_record_binding"] is True
    assert audit_result["capabilities"]["release_manifest_ledger_receipt_material_binding"] is True
    assert audit_result["capabilities"]["release_manifest_external_payload_birth_match_coverage"] is True
    assert audit_result["capabilities"]["release_manifest_provider_action_plan_coverage"] is True
    assert audit_result["capabilities"]["release_manifest_classical_source_receipt_coverage"] is True
    assert audit_result["capabilities"]["known_gap_resolution_plan"] is True
    assert audit_result["capabilities"]["known_gap_resolution_plan_coverage_audit"] is True
    assert audit_result["capabilities"]["release_manifest_ledger_readiness_gate"] is True
    assert audit_result["capabilities"]["release_manifest_drift_gate"] is True
    assert audit_result["capabilities"]["implemented_evidence_materialized"] is True
    assert audit_result["evidence_materialization"]["status"] == "passed"
    assert audit_result["evidence_materialization"]["failed_count"] == 0
    assert audit_result["evidence_materialization"]["unchecked_count"] == 0
    assert audit_result["evidence_materialization"]["passed_count"] == audit_result["evidence_materialization"]["total_evidence"]
    assert audit_result["provider_protocol_governance"]["status"] == "ready"
    assert audit_result["provider_protocol_governance"]["protocol_version"] == "json-cli-v1"
    assert len(audit_result["provider_protocol_governance"]["protocol_hash"]) == 64
    assert audit_result["provider_protocol_governance"]["sample_stdout_contracts_valid"] is True
    assert audit_result["provider_protocol_governance"]["runtime_identity_handshake"]["ready"] is True
    assert audit_result["provider_protocol_governance"]["runtime_identity_handshake"]["failures"] == []
    assert audit_result["provider_protocol_governance"]["production_gate"] == "provider_certification_protocols_current"
    assert "protocol_identity_matches" in audit_result["provider_protocol_governance"]["receipt_material_fields"]
    assert audit_result["audit_receipt"]["schema_version"] == "capability-audit-receipt-v1"
    assert len(audit_result["audit_receipt"]["sha256"]) == 64
    assert audit_result["expected_audit_receipt_sha256"] is None
    assert audit_result["audit_receipt_matches_expected"] is None
    assert audit_result["audit_receipt_mismatch_reason"] == ""
    assert audit_result["audit_receipt"]["material"]["provider_protocol_governance"]["protocol_hash"] == audit_result[
        "provider_protocol_governance"
    ]["protocol_hash"]
    assert (
        audit_result["audit_receipt"]["material"]["provider_protocol_governance"]["runtime_identity_handshake"]["ready"]
        is True
    )
    assert audit_result["audit_receipt"]["material"]["evidence_materialization"]["failed_count"] == 0
    assert "external_review" in audit_result["audit_receipt"]["material"]["outcome_dataset"]
    assert "data_split" in audit_result["audit_receipt"]["material"]["outcome_dataset"]
    assert "data_split_record_coverage" in audit_result["audit_receipt"]["material"]["outcome_dataset"]
    assert "label_collection" in audit_result["audit_receipt"]["material"]["outcome_dataset"]
    assert len(audit_result["audit_receipt"]["material"]["known_gap_resolution_plan_hash"]) == 64
    gap_plan_coverage = audit_result["known_gap_resolution_plan_coverage"]
    assert gap_plan_coverage["coverage_complete"] is True
    assert gap_plan_coverage["known_gap_count"] == len(audit_result["known_gaps"])
    assert gap_plan_coverage["covered_count"] == gap_plan_coverage["known_gap_count"]
    assert gap_plan_coverage["missing_gap_ids"] == []
    assert gap_plan_coverage["invalid_plan_gap_ids"] == []
    assert gap_plan_coverage["invalid_gate_ids_by_gap"] == {}
    assert len(gap_plan_coverage["plan_coverage_sha256"]) == 64
    assert len(gap_plan_coverage["audit_plan_hash"]) == 64
    assert audit_result["audit_receipt"]["material"]["known_gap_resolution_plan_coverage"] == gap_plan_coverage
    assert "llm_backend" in audit_result
    assert "llm_backend_configured" in audit_result["capabilities"]
    assert audit_result["reference_chart_checks"]["passed"] is True
    assert audit_result["classical_text_index"]["status"] == "ready"
    assert audit_result["empirical_validation"]["predictive_truth_cases"] == 0
    assert audit_result["capabilities"]["professional_ziwei_provider_available"] is False
    assert any(gap["id"] == "professional_qimen_provider" for gap in audit_result["known_gaps"])
    plan_by_gap = {item["gap_id"]: item for item in audit_result["known_gap_resolution_plan"]}
    assert set(plan_by_gap) == {gap["id"] for gap in audit_result["known_gaps"]}
    assert all(item["id"] == item["gap_id"] for item in audit_result["known_gap_resolution_plan"])
    assert any(
        "provider-protocols --domain ziwei" in command
        for command in plan_by_gap["professional_ziwei_provider"]["verification_commands"]
    )
    assert "provider_certification_protocols_current" in plan_by_gap["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_ledger_covers_domains" in plan_by_gap["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_reference_contracts_current" in plan_by_gap["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_command_fingerprints_current" in plan_by_gap["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "ziwei_qimen_calculation_basis_audit_contract" in plan_by_gap["professional_ziwei_provider"][
        "production_gate_ids"
    ]
    assert "ziwei_qimen_calculation_basis_audit_contract" in plan_by_gap["professional_qimen_provider"][
        "production_gate_ids"
    ]
    assert "provider_certification_reference_contracts_current" in plan_by_gap["huangdao_calendar_selection"][
        "production_gate_ids"
    ]
    assert "astrology_ephemeris_audit_contract" in plan_by_gap["astronomical_ephemeris"][
        "production_gate_ids"
    ]
    assert "xuanze_rule_table_audit_contract" in plan_by_gap["huangdao_calendar_selection"][
        "production_gate_ids"
    ]
    assert "classical_source_refresh_ready" in plan_by_gap["external_classic_text_retrieval"]["production_gate_ids"]
    assert (
        "classical_source_latest_refresh_receipt_present"
        in plan_by_gap["external_classic_text_retrieval"]["production_gate_ids"]
    )
    assert any(
        "classical-refresh --source-list" in command
        for command in plan_by_gap["external_classic_text_retrieval"]["verification_commands"]
    )
    assert any(
        "outcome-dataset --manifest" in command
        for command in plan_by_gap["empirical_validation_dataset"]["verification_commands"]
    )
    assert any(item["id"] == "optional_kinqimen_provider" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "optional_qimen_json_cli_provider" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "optional_ziwei_json_cli_provider" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "optional_astrology_json_cli_provider" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "optional_xuanze_json_cli_provider" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "provider_protocol_governance" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "birthplace_geocoding_provenance" for item in audit_result["implemented_requirements"])
    assert any(item["id"] == "external_payload_receipts" for item in audit_result["implemented_requirements"])
    birth_match_audit = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "external_payload_birth_match_audit"
    )
    assert "birth-match audit" in birth_match_audit["requirement"]
    assert "api_core.production_readiness.benchmark_external_payload_birth_matches" in birth_match_audit["evidence"]
    assert "api_core._external_payload_birth_match_coverage" in birth_match_audit["evidence"]
    readiness_matrix = next(
        item
        for item in audit_result["implemented_requirements"]
        if item["id"] == "provider_interpretation_readiness_matrix"
    )
    assert "confidence level" in readiness_matrix["requirement"]
    assert "final_report.provider_summary.readiness_matrix" in readiness_matrix["evidence"]
    assert "api_core.schema_document.ProviderDomainStatus.interpretation_mode" in readiness_matrix["evidence"]
    topic_confidence = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "topic_synthesis_confidence_audit"
    )
    assert "provider-readiness downgrades" in topic_confidence["requirement"]
    assert "final_report.topic_synthesis.finance.synthesis_confidence" in topic_confidence["evidence"]
    assert "api_core.schema_document.TopicSynthesisConfidence.level" in topic_confidence["evidence"]
    empirical_topic_gate = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "empirical_topic_confidence_gate"
    )
    assert "production readiness blocks releases" in empirical_topic_gate["requirement"]
    assert "api_core.production_readiness.benchmark_topic_confidence_boundaries" in empirical_topic_gate["evidence"]
    assert any(item["id"] == "release_governance_ledger" for item in audit_result["implemented_requirements"])
    split_governance = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "outcome_dataset_split_governance"
    )
    assert "frozen train/holdout split" in split_governance["requirement"]
    assert "outcome_dataset.data_split_record_coverage_gate" in split_governance["evidence"]
    assert "api_core.production_readiness.outcome_dataset_data_split_records_covered" in split_governance["evidence"]
    assert "api_core.release_manifest.release_gate_checks.outcome_dataset_split_coverage_bound" in split_governance[
        "evidence"
    ]
    empirical_governance = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "empirical_validation_harness"
    )
    assert "outcome_dataset.external_review_gate" in empirical_governance["evidence"]
    assert "outcome_dataset.frozen_holdout_gate" in empirical_governance["evidence"]
    assert "outcome_dataset.label_collection_pre_analysis_gate" in empirical_governance["evidence"]
    population_evolution = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "multi_objective_population_evolution"
    )
    assert "cost-governance manifests" in population_evolution["requirement"]
    assert "evolution.evolution_cost_governance" in population_evolution["evidence"]
    release_governance = next(item for item in audit_result["implemented_requirements"] if item["id"] == "release_governance_ledger")
    assert "external-payload birth-match coverage" in release_governance["requirement"]
    assert "provider action-plan coverage" in release_governance["requirement"]
    assert "classical source-list receipt coverage" in release_governance["requirement"]
    assert "api_core._external_payload_birth_match_coverage" in release_governance["evidence"]
    assert "api_core._provider_action_plan_coverage" in release_governance["evidence"]
    assert "api_core._classical_source_receipt_coverage" in release_governance["evidence"]
    assert "api_core.production_readiness.release_manifest_ledger_integrity" in release_governance["evidence"]
    assert "api_core.release_manifest_ledger.latest_record_binding" in release_governance["evidence"]
    assert "api_core.release_manifest_ledger.receipt_material_binding" in release_governance["evidence"]
    provider_governance = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "provider_protocol_governance"
    )
    assert "api_core.provider_certification_ledger.latest_record_binding" in provider_governance["evidence"]
    assert "provider_checks._reference_contract_coverage" in provider_governance["evidence"]
    assert "api_core.provider_certification_ledger.reference_contract_status" in provider_governance["evidence"]
    assert "api_core.production_readiness.provider_certification_reference_contracts_current" in provider_governance[
        "evidence"
    ]
    assert "provider_checks._json_cli_protocol_identity" in provider_governance["evidence"]
    method_surface_lock = next(
        item for item in audit_result["implemented_requirements"] if item["id"] == "provider_contract_method_surface_lock"
    )
    assert "provider_protocols.provider_protocol_receipt" in method_surface_lock["evidence"]
    assert len(audit_result["provider_protocol_governance"]["protocol_receipt_sha256"]) == 64
    assert len(audit_result["provider_protocol_governance"]["protocol_document_sha256"]) == 64
    assert any(candidate["name"] == "pyswisseph" for candidate in audit_result["external_integration_candidates"])
    assert "provider_checks" in audit_result

    audit_receipt_sha256 = audit_result["audit_receipt"]["sha256"]
    assert main(["--repo", str(repo), "audit", "--expected-audit-receipt-sha256", audit_receipt_sha256]) == 0
    matched_audit = read_stdout_json(capsys)
    assert matched_audit["expected_audit_receipt_sha256"] == audit_receipt_sha256
    assert matched_audit["audit_receipt_matches_expected"] is True
    assert matched_audit["audit_receipt_mismatch_reason"] == ""
    assert matched_audit["audit_receipt"]["sha256"] == audit_receipt_sha256

    wrong_audit_sha = "0" * 64
    assert main(["--repo", str(repo), "audit", "--expected-audit-receipt-sha256", wrong_audit_sha]) == 0
    mismatched_audit = read_stdout_json(capsys)
    assert mismatched_audit["expected_audit_receipt_sha256"] == wrong_audit_sha
    assert mismatched_audit["audit_receipt_matches_expected"] is False
    assert mismatched_audit["audit_receipt_mismatch_reason"] == "audit receipt sha256 does not match expected value"

    assert main(["--repo", str(repo), "providers"]) == 0
    provider_result = read_stdout_json(capsys)
    assert provider_result["profile"] == "development"
    assert provider_result["reference_chart_checks"]["passed"] is True
    assert "qimen_kinqimen" in provider_result["checks"]
    assert "qimen_json_cli" in provider_result["checks"]
    assert "astrology_json_cli" in provider_result["checks"]
    assert "xuanze_json_cli" in provider_result["checks"]

    assert main(["--repo", str(repo), "providers", "--live"]) == 0
    live_provider_result = read_stdout_json(capsys)
    assert live_provider_result["live"] is True

    assert main(["--repo", str(repo), "providers", "--profile", "production"]) == 0
    production_provider_result = read_stdout_json(capsys)
    assert production_provider_result["profile"] == "production"
    assert production_provider_result["profile_readiness"]["status"] == "production_blocked"

    assert main(["--repo", str(repo), "provider-ledger"]) == 0
    empty_ledger = read_stdout_json(capsys)
    assert empty_ledger["ledger"]["exists"] is False
    assert empty_ledger["ledger"]["integrity_status"] == "fail"
    assert empty_ledger["ledger"]["coverage_status"] == "incomplete"
    assert empty_ledger["ledger"]["record_count"] == 0
    assert empty_ledger["ledger"]["latest_record_index"] is None
    assert set(empty_ledger["ledger"]["missing_domains"]) == {"astrology", "qimen", "xuanze", "ziwei"}
    assert main(["--repo", str(repo), "provider-drift", "--no-live"]) == 0
    empty_drift = read_stdout_json(capsys)
    assert empty_drift["drift"]["status"] == "not_checked"
    assert empty_drift["ledger"]["record_count"] == 0
    assert main(["--repo", str(repo), "provider-protocols"]) == 0
    protocols_result = read_stdout_json(capsys)
    assert protocols_result["domain"] is None
    assert set(protocols_result["provider_protocols"]["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert protocols_result["provider_protocols_receipt"]["material"]["protocol_hash"] == protocols_result[
        "provider_protocols"
    ]["protocol_hash"]
    assert protocols_result["provider_protocols_receipt"]["material"]["domain_count"] == 4
    assert len(protocols_result["provider_protocols_receipt"]["material"]["protocol_document_sha256"]) == 64
    assert len(protocols_result["provider_protocols_receipt"]["sha256"]) == 64
    assert protocols_result["provider_protocols"]["domains"]["ziwei"]["env_var"] == "SEMAS_ZIWEI_CLI"
    assert "certify-provider ziwei" in protocols_result["provider_protocols"]["domains"]["ziwei"]["certification_command_template"]
    assert "provider-drift --domain ziwei" in protocols_result["provider_protocols"]["domains"]["ziwei"]["drift_command_template"]
    assert protocols_result["provider_protocols"]["domains"]["ziwei"]["sample_stdin"]["birth"]["birth_date"] == "1990-04-12"
    assert len(protocols_result["provider_protocols"]["domains"]["ziwei"]["sample_stdout"]["palaces"]) == 12
    assert protocols_result["provider_protocols"]["domains"]["ziwei"]["sample_stdout_contract"]["valid"] is True
    assert main(["--repo", str(repo), "provider-protocols", "--domain", "qimen"]) == 0
    qimen_protocols_result = read_stdout_json(capsys)
    assert qimen_protocols_result["domain"] == "qimen"
    assert set(qimen_protocols_result["provider_protocols"]["domains"]) == {"qimen"}
    assert qimen_protocols_result["provider_protocols_receipt"]["material"]["domain"] == "qimen"
    assert qimen_protocols_result["provider_protocols_receipt"]["material"]["domain_count"] == 1
    assert set(qimen_protocols_result["provider_protocols_receipt"]["material"]["domain_protocol_hashes"]) == {
        "qimen"
    }
    assert qimen_protocols_result["provider_protocols"]["domains"]["qimen"]["env_var"] == "SEMAS_QIMEN_CLI"
    assert qimen_protocols_result["provider_protocols"]["domains"]["qimen"]["required_provenance_fields"] == [
        "provider",
        "version",
        "source",
        "license_or_review",
    ]
    assert qimen_protocols_result["provider_protocols"]["domains"]["qimen"]["sample_stdin"]["birth"]["birth_time"] == "09:20"
    assert len(qimen_protocols_result["provider_protocols"]["domains"]["qimen"]["sample_stdout"]["palaces"]) == 9
    assert qimen_protocols_result["provider_protocols"]["domains"]["qimen"]["sample_stdout_contract"]["valid"] is True

    assert main(["--repo", str(repo), "certify-provider", "qimen", "--no-live"]) == 0
    certification_result = read_stdout_json(capsys)
    assert certification_result["domain"] == "qimen"
    assert certification_result["status"] == "blocked"
    assert certification_result["env_var"] == "SEMAS_QIMEN_CLI"
    assert certification_result["live_requested"] is False
    assert certification_result["reference_contract_coverage"]["domain"] == "qimen"
    assert certification_result["reference_contract_coverage"]["passed"] is True
    assert len(certification_result["reference_contract_coverage"]["coverage_sha256"]) == 64
    assert certification_result["certification_receipt"]["material"]["reference_contract_coverage"] == certification_result[
        "reference_contract_coverage"
    ]
    assert len(certification_result["certification_receipt"]["sha256"]) == 64
    assert certification_result["expected_receipt_sha256"] is None
    assert certification_result["receipt_matches_expected"] is None
    assert certification_result["ledger_record_requested"] is False
    assert certification_result["ledger_recorded"] is False

    reviewed_provider = tmp_path / "reviewed_ziwei_provider.py"
    reviewed_provider.write_text(
        Path("examples/mingli_5agents/providers/ziwei_json_cli_example.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assert main(
        [
            "--repo",
            str(repo),
            "certify-provider",
            "ziwei",
            "--command",
            f"{sys.executable} {reviewed_provider}",
            "--provenance",
            "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
        ]
    ) == 0
    override_certification = read_stdout_json(capsys)
    assert override_certification["status"] == "certified"
    assert override_certification["command_override_used"] is True
    assert override_certification["provenance_override_used"] is True
    assert override_certification["live_check"]["passed"] is True
    assert override_certification["certification_receipt"]["material"]["certified"] is True
    assert override_certification["certification_receipt"]["material"]["reference_contract_coverage"]["passed"] is True
    assert len(override_certification["provider_command_fingerprint"]["command_sha256"]) == 64
    assert len(override_certification["provider_command_fingerprint"]["artifact_sha256"]) == 64
    assert (
        override_certification["certification_receipt"]["material"]["provider_command_fingerprint"]
        == override_certification["provider_command_fingerprint"]
    )
    receipt_sha256 = override_certification["certification_receipt"]["sha256"]
    assert main(
        [
            "--repo",
            str(repo),
            "certify-provider",
            "ziwei",
            "--command",
            f"{sys.executable} {reviewed_provider}",
            "--provenance",
            "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
            "--expected-receipt-sha256",
            receipt_sha256,
            "--record",
        ]
    ) == 0
    matched_certification = read_stdout_json(capsys)
    assert matched_certification["receipt_matches_expected"] is True
    assert matched_certification["receipt_mismatch_reason"] == ""
    assert matched_certification["ledger_record_requested"] is True
    assert matched_certification["ledger_recorded"] is True
    assert matched_certification["ledger_record_index"] == 0
    assert len(matched_certification["ledger_record_hash"]) == 64
    ledger = json.loads(Path(matched_certification["ledger_record_path"]).read_text(encoding="utf-8"))
    assert ledger["latest_record_index"] == 0
    assert ledger["records"][0]["receipt_sha256"] == receipt_sha256
    assert ledger["records"][0]["reference_contract_coverage"] == matched_certification["reference_contract_coverage"]
    assert ledger["records"][0]["provider_command_fingerprint"] == matched_certification["provider_command_fingerprint"]
    assert ledger["records"][0]["record_hash"] == matched_certification["ledger_record_hash"]
    assert main(["--repo", str(repo), "provider-ledger"]) == 0
    ledger_status = read_stdout_json(capsys)
    assert ledger_status["ledger"]["exists"] is True
    assert ledger_status["ledger"]["integrity_status"] == "pass"
    assert ledger_status["ledger"]["protocol_status"] == "current"
    assert ledger_status["ledger"]["reference_contract_status"] == "current"
    assert ledger_status["ledger"]["command_fingerprint_status"] == "current"
    assert ledger_status["ledger"]["protocol_failures"] == []
    assert ledger_status["ledger"]["reference_contract_failures"] == []
    assert ledger_status["ledger"]["command_fingerprint_failures"] == []
    assert ledger_status["ledger"]["coverage_status"] == "incomplete"
    assert ledger_status["ledger"]["record_count"] == 1
    assert ledger_status["ledger"]["latest_record_index"] == 0
    assert ledger_status["ledger"]["covered_domains"] == ["ziwei"]
    assert ledger_status["ledger"]["domains"]["ziwei"]["latest_receipt_sha256"] == receipt_sha256
    assert ledger_status["ledger"]["domains"]["ziwei"]["protocol_matches_current"] is True
    assert ledger_status["ledger"]["domains"]["ziwei"]["latest_protocol_hash"] == matched_certification["protocol_hash"]
    assert ledger_status["ledger"]["domains"]["ziwei"]["reference_contract_covered"] is True
    assert ledger_status["ledger"]["domains"]["ziwei"]["provider_command_fingerprint_present"] is True
    assert len(ledger_status["ledger"]["domains"]["ziwei"]["latest_provider_command_sha256"]) == 64
    assert len(ledger_status["ledger"]["domains"]["ziwei"]["latest_provider_artifact_sha256"]) == 64
    assert len(ledger_status["ledger"]["domains"]["ziwei"]["latest_reference_contract_coverage_sha256"]) == 64
    assert len(ledger_status["ledger"]["domains"]["ziwei"]["latest_reference_contract_method_surface_sha256"]) == 64
    assert (
        ledger_status["ledger"]["domains"]["ziwei"]["latest_reference_contract_method_surface_sha256"]
        == matched_certification["reference_contract_coverage"]["method_surface_sha256"]
    )
    assert ledger_status["ledger"]["domains"]["ziwei"]["current_method_surface_sha256"] == matched_certification[
        "reference_contract_coverage"
    ]["method_surface_sha256"]
    assert ledger_status["ledger"]["domains"]["ziwei"]["reference_contract_method_surface_current"] is True
    assert ledger_status["ledger"]["domains"]["ziwei"]["reference_contract_method_count"] > 0
    assert ledger_status["ledger"]["domains"]["ziwei"]["reference_contract_case_count"] > 0
    ledger_path = Path(matched_certification["ledger_record_path"])
    provider_ledger_with_bad_index = json.loads(ledger_path.read_text(encoding="utf-8"))
    provider_ledger_with_bad_index["latest_record_index"] = 99
    ledger_path.write_text(json.dumps(provider_ledger_with_bad_index, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "provider-ledger"]) == 0
    tampered_index_provider_ledger = read_stdout_json(capsys)
    assert tampered_index_provider_ledger["ledger"]["integrity_status"] == "fail"
    assert any(
        "latest_record_index does not match last record" in item
        for item in tampered_index_provider_ledger["ledger"]["failures"]
    )
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("SEMAS_ZIWEI_CLI", f"{sys.executable} {reviewed_provider}")
    monkeypatch.setenv(
        "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
        "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
    )
    assert main(["--repo", str(repo), "provider-drift"]) == 0
    provider_drift = read_stdout_json(capsys)
    ziwei_provider_drift = next(item for item in provider_drift["drift"]["checks"] if item["domain"] == "ziwei")
    assert ziwei_provider_drift["status"] == "match"
    assert ziwei_provider_drift["matches_expected"] is True
    assert ziwei_provider_drift["provider_command_fingerprint_matches_expected"] is True
    assert len(ziwei_provider_drift["expected_provider_command_sha256"]) == 64
    assert len(ziwei_provider_drift["current_provider_command_sha256"]) == 64
    assert len(ziwei_provider_drift["expected_provider_artifact_sha256"]) == 64
    assert len(ziwei_provider_drift["current_provider_artifact_sha256"]) == 64
    assert "qimen has no recorded certification receipt" in provider_drift["drift"]["failures"]
    assert main(["--repo", str(repo), "provider-drift", "--domain", "ziwei"]) == 0
    ziwei_only_drift = read_stdout_json(capsys)
    assert ziwei_only_drift["domain"] == "ziwei"
    assert ziwei_only_drift["drift"]["checked_domains"] == ["ziwei"]
    assert [item["domain"] for item in ziwei_only_drift["drift"]["checks"]] == ["ziwei"]
    assert ziwei_only_drift["drift"]["status"] == "passed"

    assert main(["--repo", str(repo), "outcome-dataset"]) == 0
    unconfigured_outcome = read_stdout_json(capsys)
    assert unconfigured_outcome["audit"]["status"] == "not_configured"
    assert unconfigured_outcome["evolution_gate"]["passed"] is True
    assert unconfigured_outcome["evolution_gate"]["manifest_path"] is None

    example_manifest = Path("examples/mingli_5agents/providers/outcome_dataset_manifest_example.json")
    assert main(["--repo", str(repo), "outcome-dataset", "--manifest", str(example_manifest)]) == 0
    outcome_result = read_stdout_json(capsys)
    assert outcome_result["manifest_path"] == str(example_manifest)
    assert outcome_result["audit"]["status"] == "ready_for_review"
    assert outcome_result["audit"]["valid"] is True
    assert outcome_result["audit"]["quality_task_projection"]["projected_task_count"] == 1
    assert outcome_result["evolution_gate"]["passed"] is True
    assert outcome_result["evolution_gate"]["predictive_optimization_enabled"] is False

    assert main(["--repo", str(repo), "classical-sources"]) == 0
    unconfigured_classical_sources = read_stdout_json(capsys)
    assert unconfigured_classical_sources["configured"] is False
    assert unconfigured_classical_sources["audit"]["status"] == "unconfigured"
    assert len(unconfigured_classical_sources["audit"]["source_list_receipt"]["sha256"]) == 64
    assert unconfigured_classical_sources["production_gate"]["passed"] is False
    assert "SEMAS_CLASSIC_SOURCE_LIST" in unconfigured_classical_sources["production_gate"]["details"][0]
    source_list = tmp_path / "classical_sources.json"
    write_json(
        source_list,
        {
            "allowed_hosts": ["classics.example"],
            "sources": [
                {
                    "name": "locked-classics",
                    "url": "https://classics.example/manifest.json",
                    "sha256": "a" * 64,
                    **source_governance_fields(),
                }
            ],
        },
    )
    assert main(["--repo", str(repo), "classical-sources", "--source-list", str(source_list)]) == 0
    classical_sources = read_stdout_json(capsys)
    assert classical_sources["configured"] is True
    assert classical_sources["source_list_path"] == str(source_list)
    assert classical_sources["audit"]["status"] == "ready"
    assert classical_sources["audit"]["locked_source_count"] == 1
    assert classical_sources["audit"]["source_audits"][0]["refreshable"] is True
    assert classical_sources["audit"]["source_list_receipt"]["material"]["valid"] is True
    assert classical_sources["audit"]["source_list_receipt"]["material"]["source_audits"] == classical_sources["audit"]["source_audits"]
    assert classical_sources["production_gate"]["passed"] is True

    assert main(["--repo", str(repo), "production-readiness"]) == 0
    readiness_unconfigured = read_stdout_json(capsys)
    assert readiness_unconfigured["status"] == "production_blocked"
    assert readiness_unconfigured["production_ready"] is False
    assert readiness_unconfigured["provider_integration_plan"]["status"] == "production_blocked"
    blocker_gates = {item["gate"] for item in readiness_unconfigured["blockers"]}
    assert "provider_profile_ready" in blocker_gates
    assert "outcome_dataset_configured" in blocker_gates
    assert "provider_certification_ledger_available" not in blocker_gates
    assert "provider_certification_ledger_integrity" not in blocker_gates
    assert "provider_certification_ledger_covers_domains" in blocker_gates
    assert "provider_certification_protocols_current" not in blocker_gates
    assert "provider_certification_request_receipts_current" not in blocker_gates
    assert "provider_certification_reference_contracts_current" not in blocker_gates
    assert "provider_certification_command_fingerprints_current" not in blocker_gates
    assert "provider_certification_receipts_current" in blocker_gates
    assert "release_manifest_ledger_integrity" not in blocker_gates
    assert readiness_unconfigured["release_manifest_ledger"]["exists"] is False
    assert readiness_unconfigured["release_manifest_ledger"]["latest_record_index"] is None
    evidence_gate = next(item for item in readiness_unconfigured["gates"] if item["id"] == "implemented_evidence_materialized")
    assert evidence_gate["passed"] is True
    assert readiness_unconfigured["evidence_materialization"]["failed_count"] == 0
    benchmark_gate = next(item for item in readiness_unconfigured["gates"] if item["id"] == "current_benchmark_passed")
    assert benchmark_gate["passed"] is True
    assert readiness_unconfigured["current_benchmark"]["passed_rate"] == 1.0
    assert readiness_unconfigured["current_benchmark"]["mean_metrics"]["provider_contracts"] == 1.0
    assert len(readiness_unconfigured["capability_audit_receipt"]["sha256"]) == 64
    assert readiness_unconfigured["expected_audit_receipt_sha256"] is None
    assert readiness_unconfigured["audit_receipt_matches_expected"] is None
    assert readiness_unconfigured["audit_receipt_mismatch_reason"] == ""
    assert len(readiness_unconfigured["readiness_receipt"]["sha256"]) == 64
    assert readiness_unconfigured["readiness_receipt"]["material"]["current_benchmark"]["passed_rate"] == 1.0
    assert readiness_unconfigured["readiness_receipt"]["material"]["evidence_materialization"]["failed_count"] == 0
    assert readiness_unconfigured["classical_source_refresh"]["status"] == "unconfigured"
    assert readiness_unconfigured["readiness_receipt"]["material"]["classical_source_refresh"]["status"] == "unconfigured"
    assert (
        readiness_unconfigured["readiness_receipt"]["material"]["capability_audit_receipt"]["sha256"]
        == readiness_unconfigured["capability_audit_receipt"]["sha256"]
    )
    assert readiness_unconfigured["provider_certification_drift"]["status"] == "not_checked"
    assert readiness_unconfigured["provider_certification_ledger"]["record_count"] == 1
    assert readiness_unconfigured["provider_certification_ledger"]["command_fingerprint_status"] == "current"
    assert readiness_unconfigured["provider_certification_ledger"]["command_fingerprint_failures"] == []
    assert (
        readiness_unconfigured["readiness_receipt"]["material"]["provider_certification_ledger"]["latest_record_hash"]
        == readiness_unconfigured["provider_certification_ledger"]["latest_record_hash"]
    )
    assert readiness_unconfigured["readiness_receipt"]["material"]["provider_certification_ledger"]["latest_record_index"] == 0
    assert readiness_unconfigured["provider_certification_ledger"]["missing_domains"] == [
        "astrology",
        "qimen",
        "xuanze",
    ]
    assert readiness_unconfigured["resolution_plan"]["status"] == "actions_required"
    unconfigured_steps = {item["id"] for item in readiness_unconfigured["resolution_plan"]["steps"]}
    assert "configure_outcome_dataset_manifest" in unconfigured_steps
    assert "configure_classical_source_refresh" in unconfigured_steps
    assert "complete_qimen_professional_engine" in unconfigured_steps
    step_by_id = {item["id"]: item for item in readiness_unconfigured["resolution_plan"]["steps"]}
    assert any(
        "certify-provider qimen --command" in command and "--record" in command
        for command in step_by_id["record_qimen_provider_receipt"]["commands"]
    )

    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest)]) == 0
    readiness = read_stdout_json(capsys)
    assert readiness["status"] == "production_blocked"
    assert readiness["production_ready"] is False
    assert readiness["outcome_dataset"]["audit"]["status"] == "ready_for_review"
    assert readiness["history_integrity"]["status"] == "pass"
    blocker_gates = {item["gate"] for item in readiness["blockers"]}
    assert "outcome_dataset_configured" not in blocker_gates
    assert "outcome_dataset_data_split_records_covered" not in blocker_gates
    split_coverage_gate = next(
        item for item in readiness["gates"] if item["id"] == "outcome_dataset_data_split_records_covered"
    )
    assert split_coverage_gate["passed"] is True
    assert "provider_profile_ready" in blocker_gates
    assert "provider_certification_ledger_integrity" not in blocker_gates
    assert "provider_certification_ledger_covers_domains" in blocker_gates
    assert "provider_certification_protocols_current" not in blocker_gates
    assert "provider_certification_command_fingerprints_current" not in blocker_gates
    assert "provider_certification_receipts_current" in blocker_gates
    assert "release_manifest_ledger_integrity" not in blocker_gates
    evidence_gate = next(item for item in readiness["gates"] if item["id"] == "implemented_evidence_materialized")
    assert evidence_gate["passed"] is True
    known_gap_plan_gate = next(item for item in readiness["gates"] if item["id"] == "known_gap_resolution_plan_covered")
    assert known_gap_plan_gate["passed"] is True
    assert "known_gap_resolution_plan_covered" not in blocker_gates
    assert readiness["evidence_materialization"]["status"] == "passed"
    assert readiness["evidence_materialization"]["failed_count"] == 0
    assert readiness["evidence_materialization"]["unchecked_count"] == 0
    assert readiness["evidence_materialization"]["passed_count"] == readiness["evidence_materialization"]["total_evidence"]
    classical_gate = next(item for item in readiness["gates"] if item["id"] == "classical_source_refresh_ready")
    assert classical_gate["passed"] is False
    assert "SEMAS_CLASSIC_SOURCE_LIST" in classical_gate["details"][0]
    assert "classical_source_refresh_ready" in blocker_gates
    assert readiness["classical_source_refresh"]["status"] == "unconfigured"
    assert (
        readiness["readiness_receipt"]["material"]["classical_source_refresh"]["status"]
        == readiness["classical_source_refresh"]["status"]
    )
    benchmark_gate = next(item for item in readiness["gates"] if item["id"] == "current_benchmark_passed")
    assert benchmark_gate["passed"] is True
    geocoding_gate = next(item for item in readiness["gates"] if item["id"] == "benchmark_birthplaces_geocoded")
    assert geocoding_gate["passed"] is True
    deliberation_gate = next(
        item for item in readiness["gates"] if item["id"] == "benchmark_deliberation_receipts_bound"
    )
    assert deliberation_gate["passed"] is True
    annual_timeline_gate = next(
        item for item in readiness["gates"] if item["id"] == "benchmark_annual_timeline_receipts_bound"
    )
    assert annual_timeline_gate["passed"] is True
    monthly_luck_gate = next(
        item for item in readiness["gates"] if item["id"] == "benchmark_monthly_luck_receipts_bound"
    )
    assert monthly_luck_gate["passed"] is True
    auspicious_calendar_gate = next(
        item for item in readiness["gates"] if item["id"] == "benchmark_auspicious_calendar_receipts_bound"
    )
    assert auspicious_calendar_gate["passed"] is True
    analyze_schema_gate = next(
        item for item in readiness["gates"] if item["id"] == "benchmark_analyze_response_schema_valid"
    )
    assert analyze_schema_gate["passed"] is True
    assert readiness["benchmark_analyze_response_schema"]["coverage_complete"] is True
    assert readiness["benchmark_analyze_response_schema"]["invalid_cases"] == []
    registry_gate = next(item for item in readiness["gates"] if item["id"] == "production_gate_registry_current")
    assert registry_gate["passed"] is True
    registry_audit = readiness["production_gate_registry_audit"]
    assert registry_audit["registry_current"] is True
    assert registry_audit["missing_from_registry"] == []
    assert "benchmark_annual_timeline_receipts_bound" in registry_audit["registry_gate_ids"]
    assert "benchmark_monthly_luck_receipts_bound" in registry_audit["registry_gate_ids"]
    assert "benchmark_auspicious_calendar_receipts_bound" in registry_audit["registry_gate_ids"]
    assert "benchmark_analyze_response_schema_valid" in registry_audit["registry_gate_ids"]
    assert "production_gate_registry_current" in registry_audit["actual_gate_ids"]
    assert len(registry_audit["registry_audit_sha256"]) == 64
    assert readiness["current_benchmark"]["passed_rate"] == 1.0
    assert readiness["current_benchmark"]["reference_charts"]["passed"] is True
    assert len(readiness["capability_audit_receipt"]["sha256"]) == 64
    assert readiness["audit_receipt_matches_expected"] is None
    assert len(readiness["readiness_receipt"]["sha256"]) == 64
    assert readiness["readiness_receipt"]["material"]["status"] == "production_blocked"
    assert readiness["readiness_receipt"]["material"]["capability_audit_receipt"]["sha256"] == readiness[
        "capability_audit_receipt"
    ]["sha256"]
    assert "current_benchmark_passed" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    assert "capability_audit_receipt_current" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    assert "release_manifest_ledger_integrity" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    assert "known_gap_resolution_plan_covered" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    assert "blocked_capability_coverage_complete" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    assert (
        readiness["readiness_receipt"]["material"]["current_benchmark"]["analyze_response_schema_audit"][
            "coverage_complete"
        ]
        is True
    )
    assert (
        readiness["readiness_receipt"]["material"]["production_gate_registry_audit"]
        == readiness["production_gate_registry_audit"]
    )
    assert (
        readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["latest_record_hash"]
        == readiness["provider_certification_ledger"]["latest_record_hash"]
    )
    assert readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["latest_record_index"] == 0
    gap_plan_coverage = readiness["readiness_receipt"]["material"]["known_gap_resolution_plan_coverage"]
    assert gap_plan_coverage["known_gap_count"] == len(readiness["known_gap_ids"])
    assert gap_plan_coverage["covered_count"] == gap_plan_coverage["known_gap_count"]
    assert gap_plan_coverage["coverage_complete"] is True
    assert gap_plan_coverage["planned_gap_ids"] == sorted(readiness["known_gap_ids"])
    assert gap_plan_coverage["missing_gap_ids"] == []
    assert gap_plan_coverage["invalid_plan_gap_ids"] == []
    assert gap_plan_coverage["invalid_gate_ids_by_gap"] == {}
    assert "provider_certification_ledger_covers_domains" in gap_plan_coverage["valid_production_gate_ids"]
    assert "outcome_dataset_data_split_records_covered" in gap_plan_coverage["valid_production_gate_ids"]
    assert "ziwei_qimen_calculation_basis_audit_contract" in gap_plan_coverage["valid_production_gate_ids"]
    assert "astrology_ephemeris_audit_contract" in gap_plan_coverage["valid_production_gate_ids"]
    assert "xuanze_rule_table_audit_contract" in gap_plan_coverage["valid_production_gate_ids"]
    assert "classical_source_latest_refresh_receipt_present" in gap_plan_coverage["valid_production_gate_ids"]
    assert len(gap_plan_coverage["plan_coverage_sha256"]) == 64
    assert len(gap_plan_coverage["audit_plan_hash"]) == 64
    assert gap_plan_coverage["command_counts"]["professional_qimen_provider"] > 0
    assert gap_plan_coverage["gate_counts"]["empirical_validation_dataset"] > 0
    resolution_plan_summary = readiness["readiness_receipt"]["material"]["production_resolution_plan_summary"]
    assert resolution_plan_summary["status"] == readiness["resolution_plan"]["status"]
    assert resolution_plan_summary["step_count"] == readiness["resolution_plan"]["step_count"]
    assert "complete_qimen_professional_engine" in resolution_plan_summary["step_ids"]
    assert resolution_plan_summary["category_counts"]["provider_integration"] >= 1
    assert resolution_plan_summary["category_counts"]["provider_ledger"] >= 1
    assert resolution_plan_summary["command_count"] >= len(readiness["resolution_plan"]["steps"])
    assert len(resolution_plan_summary["resolution_plan_sha256"]) == 64
    birth_audit = readiness["readiness_receipt"]["material"]["current_benchmark"]["birth_profile_audit"]
    assert birth_audit["geocoded_count"] == birth_audit["case_count"]
    assert birth_audit["unresolved_geocoding"] == []
    request_audit = readiness["readiness_receipt"]["material"]["current_benchmark"]["request_provenance_audit"]
    assert request_audit["deliberation_receipt_covered_count"] == request_audit["case_count"]
    assert len(request_audit["deliberation_receipts"]) == request_audit["case_count"]
    assert all(len(item["sha256"]) == 64 for item in request_audit["deliberation_receipts"])
    assert all(item["claim_count"] == 4 for item in request_audit["deliberation_receipts"])
    assert request_audit["annual_timeline_receipt_covered_count"] == request_audit["case_count"]
    assert request_audit["annual_timeline_receipt_bound_count"] == request_audit["case_count"]
    assert len(request_audit["annual_timeline_receipts"]) == request_audit["case_count"]
    assert request_audit["annual_timeline_unbound_cases"] == []
    assert all(len(item["sha256"]) == 64 for item in request_audit["annual_timeline_receipts"])
    assert all(item["row_count"] > 0 for item in request_audit["annual_timeline_receipts"])
    assert all(item["bound_to_provenance"] is True for item in request_audit["annual_timeline_receipts"])
    assert request_audit["monthly_luck_receipt_covered_count"] == request_audit["case_count"]
    assert request_audit["monthly_luck_receipt_bound_count"] == request_audit["case_count"]
    assert len(request_audit["monthly_luck_receipts"]) == request_audit["case_count"]
    assert request_audit["monthly_luck_unbound_cases"] == []
    assert all(len(item["sha256"]) == 64 for item in request_audit["monthly_luck_receipts"])
    assert all(item["row_count"] > 0 for item in request_audit["monthly_luck_receipts"])
    assert all(item["bound_to_provenance"] is True for item in request_audit["monthly_luck_receipts"])
    assert request_audit["auspicious_calendar_receipt_covered_count"] == request_audit["case_count"]
    assert request_audit["auspicious_calendar_receipt_bound_count"] == request_audit["case_count"]
    assert len(request_audit["auspicious_calendar_receipts"]) == request_audit["case_count"]
    assert request_audit["auspicious_calendar_unbound_cases"] == []
    assert all(len(item["sha256"]) == 64 for item in request_audit["auspicious_calendar_receipts"])
    assert all(item["row_count"] > 0 for item in request_audit["auspicious_calendar_receipts"])
    assert all(item["bound_to_provenance"] is True for item in request_audit["auspicious_calendar_receipts"])
    assert request_audit["external_payload_receipt_case_count"] >= 1
    assert request_audit["external_payload_receipt_domains"] == [
        "astrology",
        "bazi",
        "qimen",
        "xuanze",
        "ziwei",
    ]
    assert any(item["complete"] is True for item in request_audit["external_payload_receipt_cases"])
    assert request_audit["external_payload_birth_match_case_count"] >= 1
    assert request_audit["external_payload_birth_mismatch_domains"] == []
    assert request_audit["external_payload_birth_matches_ok"] is True
    assert any(item["matches_ok"] is True for item in request_audit["external_payload_birth_match_cases"])
    provider_action_audit = readiness["readiness_receipt"]["material"]["current_benchmark"][
        "provider_action_plan_audit"
    ]
    assert provider_action_audit["case_count"] == len(readiness["current_benchmark"]["cases"])
    assert provider_action_audit["coverage_complete"] is True
    assert provider_action_audit["unresolved"] == []
    topic_confidence_audit = readiness["readiness_receipt"]["material"]["current_benchmark"][
        "topic_confidence_audit"
    ]
    assert topic_confidence_audit["case_count"] == len(readiness["current_benchmark"]["cases"])
    assert topic_confidence_audit["coverage_complete"] is True
    assert topic_confidence_audit["boundary_failures"] == []
    assert topic_confidence_audit["missing_topics"] == {}
    assert readiness["provider_certification_ledger"]["request_receipt_status"] == "current"
    assert readiness["provider_certification_ledger"]["request_receipt_failures"] == []
    assert readiness["provider_certification_ledger"]["reference_contract_status"] == "current"
    assert readiness["provider_certification_ledger"]["reference_contract_failures"] == []
    assert readiness["provider_certification_ledger"]["command_fingerprint_status"] == "current"
    assert readiness["provider_certification_ledger"]["command_fingerprint_failures"] == []
    birth_match_gate = next(item for item in readiness["gates"] if item["id"] == "benchmark_external_payload_birth_matches")
    assert birth_match_gate["passed"] is True
    assert "benchmark_external_payload_birth_matches" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    topic_confidence_gate = next(
        item for item in readiness["gates"] if item["id"] == "benchmark_topic_confidence_boundaries"
    )
    assert topic_confidence_gate["passed"] is True
    assert "benchmark_topic_confidence_boundaries" in {
        item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
    }
    assert readiness["provider_certification_ledger"]["domains"]["ziwei"]["request_receipt_valid"] is True
    assert readiness["provider_certification_ledger"]["domains"]["ziwei"]["reference_contract_covered"] is True
    assert readiness["provider_certification_ledger"]["domains"]["ziwei"]["provider_command_fingerprint_present"] is True
    assert len(
        readiness["provider_certification_ledger"]["domains"]["ziwei"]["latest_provider_request_receipt_sha256"]
    ) == 64
    assert len(
        readiness["provider_certification_ledger"]["domains"]["ziwei"]["latest_provider_command_sha256"]
    ) == 64
    assert len(
        readiness["provider_certification_ledger"]["domains"]["ziwei"]["latest_provider_artifact_sha256"]
    ) == 64
    assert len(
        readiness["provider_certification_ledger"]["domains"]["ziwei"]["latest_reference_contract_coverage_sha256"]
    ) == 64
    assert (
        readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["request_receipt_status"]
        == "current"
    )
    assert (
        readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["reference_contract_status"]
        == "current"
    )
    assert (
        readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["command_fingerprint_status"]
        == "current"
    )
    assert (
        readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["command_fingerprint_failures"]
        == []
    )
    readiness_outcome_material = readiness["readiness_receipt"]["material"]["outcome_dataset"]
    assert readiness_outcome_material["content_hash"] == readiness["outcome_dataset"]["audit"]["content_hash"]
    assert readiness_outcome_material["data_split_record_coverage"]["coverage_complete"] is True
    assert len(readiness_outcome_material["data_split_record_coverage"]["split_fingerprint"]) == 64
    assert readiness_outcome_material["external_review"]["reviewed"] is True
    assert readiness_outcome_material["data_split"]["frozen"] is True
    assert readiness_outcome_material["label_collection"]["collected_before_analysis"] is True
    assert "external_review_approved" in readiness_outcome_material["governance_gate_ids"]
    assert (
        main(
            [
                "--repo",
                str(repo),
                "production-readiness",
                "--manifest",
                str(example_manifest),
                "--classical-source-list",
                str(source_list),
            ]
        )
        == 0
    )
    readiness_with_classical_sources = read_stdout_json(capsys)
    source_gate = next(
        item for item in readiness_with_classical_sources["gates"] if item["id"] == "classical_source_refresh_ready"
    )
    assert source_gate["passed"] is True
    assert "classical_source_refresh_ready" not in {
        item["gate"] for item in readiness_with_classical_sources["blockers"]
    }
    assert readiness_with_classical_sources["classical_source_list_path"] == str(source_list)
    assert readiness_with_classical_sources["classical_source_refresh"]["status"] == "ready"
    assert (
        readiness_with_classical_sources["readiness_receipt"]["material"]["classical_source_refresh"][
            "source_list_receipt_sha256"
        ]
        == readiness_with_classical_sources["classical_source_refresh"]["source_list_receipt"]["sha256"]
    )
    assert (
        readiness_with_classical_sources["readiness_receipt"]["material"]["classical_source_list_path"]
        == str(source_list)
    )
    audit_receipt_sha256 = readiness["capability_audit_receipt"]["sha256"]
    readiness_receipt_sha256 = readiness["readiness_receipt"]["sha256"]
    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest)]) == 0
    repeated_readiness = read_stdout_json(capsys)
    assert repeated_readiness["readiness_receipt"]["sha256"] == readiness_receipt_sha256
    assert repeated_readiness["expected_readiness_receipt_sha256"] is None
    assert repeated_readiness["readiness_receipt_matches_expected"] is None
    assert main(
        [
            "--repo",
            str(repo),
            "production-readiness",
            "--manifest",
            str(example_manifest),
            "--expected-readiness-receipt-sha256",
            readiness_receipt_sha256,
        ]
    ) == 0
    matched_readiness = read_stdout_json(capsys)
    assert matched_readiness["expected_readiness_receipt_sha256"] == readiness_receipt_sha256
    assert matched_readiness["readiness_receipt_matches_expected"] is True
    assert matched_readiness["readiness_receipt_mismatch_reason"] == ""
    assert main(
        [
            "--repo",
            str(repo),
            "production-readiness",
            "--manifest",
            str(example_manifest),
            "--expected-audit-receipt-sha256",
            audit_receipt_sha256,
        ]
    ) == 0
    matched_audit_readiness = read_stdout_json(capsys)
    assert matched_audit_readiness["expected_audit_receipt_sha256"] == audit_receipt_sha256
    assert matched_audit_readiness["audit_receipt_matches_expected"] is True
    assert matched_audit_readiness["audit_receipt_mismatch_reason"] == ""
    audit_gate = next(
        item for item in matched_audit_readiness["gates"] if item["id"] == "capability_audit_receipt_current"
    )
    assert audit_gate["passed"] is True
    assert main(
        [
            "--repo",
            str(repo),
            "production-readiness",
            "--manifest",
            str(example_manifest),
            "--expected-audit-receipt-sha256",
            "0" * 64,
        ]
    ) == 0
    mismatched_audit_readiness = read_stdout_json(capsys)
    assert mismatched_audit_readiness["audit_receipt_matches_expected"] is False
    assert mismatched_audit_readiness["audit_receipt_mismatch_reason"] == (
        "audit receipt sha256 does not match expected value"
    )
    assert "capability_audit_receipt_current" in {
        item["gate"] for item in mismatched_audit_readiness["blockers"]
    }
    assert main(
        [
            "--repo",
            str(repo),
            "production-readiness",
            "--manifest",
            str(example_manifest),
            "--expected-readiness-receipt-sha256",
            "0" * 64,
        ]
    ) == 0
    mismatched_readiness = read_stdout_json(capsys)
    assert mismatched_readiness["readiness_receipt_matches_expected"] is False
    assert mismatched_readiness["readiness_receipt_mismatch_reason"] == (
        "production readiness receipt sha256 does not match expected value"
    )
    assert readiness["provider_certification_drift"]["failures"] == [
        "run production-readiness with --live to compare current provider receipts"
    ]
    step_ids = {item["id"] for item in readiness["resolution_plan"]["steps"]}
    assert "configure_outcome_dataset_manifest" not in step_ids
    assert "configure_classical_source_refresh" in step_ids
    assert "complete_qimen_professional_engine" in step_ids
    assert "record_qimen_provider_receipt" in step_ids
    assert "check_provider_receipt_drift" in step_ids
    qimen_step = next(item for item in readiness["resolution_plan"]["steps"] if item["id"] == "complete_qimen_professional_engine")
    assert any("certify-provider qimen" in command for command in qimen_step["commands"])
    assert any("provider-drift --domain qimen" in command for command in qimen_step["commands"])
    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest), "--live"]) == 0
    live_readiness = read_stdout_json(capsys)
    live_drift = live_readiness["provider_certification_drift"]
    ziwei_drift = next(item for item in live_drift["checks"] if item["domain"] == "ziwei")
    assert ziwei_drift["status"] == "match"
    assert ziwei_drift["matches_expected"] is True
    assert ziwei_drift["expected_receipt_sha256"] == receipt_sha256
    assert ziwei_drift["provider_request_receipt_valid"] is True
    assert ziwei_drift["provider_request_receipt_matches_expected"] is True
    assert len(ziwei_drift["expected_provider_request_receipt_sha256"]) == 64
    assert ziwei_drift["current_provider_request_receipt_sha256"] == ziwei_drift[
        "expected_provider_request_receipt_sha256"
    ]
    assert "qimen has no recorded certification receipt" in live_drift["failures"]

    ledger_path = Path(readiness["provider_certification_ledger"]["path"])
    missing_request_receipt_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    request_receipt_source_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    missing_request_receipt_ledger["records"][0]["certification_receipt"]["material"].pop(
        "provider_request_receipt",
        None,
    )
    missing_request_receipt_ledger["records"][0]["certification_receipt"]["material"][
        "provider_request_receipt_valid"
    ] = False
    missing_request_receipt_ledger["records"][0]["certification_receipt"]["sha256"] = hashlib.sha256(
        json.dumps(
            missing_request_receipt_ledger["records"][0]["certification_receipt"]["material"],
            sort_keys=True,
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    missing_request_receipt_ledger["records"][0]["receipt_sha256"] = missing_request_receipt_ledger["records"][0][
        "certification_receipt"
    ]["sha256"]
    missing_request_receipt_material = {
        key: value for key, value in missing_request_receipt_ledger["records"][0].items() if key != "record_hash"
    }
    missing_request_receipt_ledger["records"][0]["record_hash"] = hashlib.sha256(
        json.dumps(missing_request_receipt_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    missing_request_receipt_ledger["latest_record_hash"] = missing_request_receipt_ledger["records"][0]["record_hash"]
    ledger_path.write_text(json.dumps(missing_request_receipt_ledger, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest)]) == 0
    missing_request_receipt_readiness = read_stdout_json(capsys)
    missing_request_receipt_blockers = {item["gate"] for item in missing_request_receipt_readiness["blockers"]}
    assert missing_request_receipt_readiness["provider_certification_ledger"]["integrity_status"] == "pass"
    assert missing_request_receipt_readiness["provider_certification_ledger"]["request_receipt_status"] == "missing"
    assert "provider_certification_request_receipts_current" in missing_request_receipt_blockers
    assert missing_request_receipt_readiness["provider_certification_ledger"]["domains"]["ziwei"][
        "request_receipt_valid"
    ] is False
    assert any(
        item["id"] == "recertify_provider_request_receipts"
        for item in missing_request_receipt_readiness["resolution_plan"]["steps"]
    )
    ledger_path.write_text(json.dumps(request_receipt_source_ledger, ensure_ascii=False), encoding="utf-8")

    stale_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    stale_ledger["records"][0]["protocol_hash"] = "1" * 64
    stale_ledger["records"][0]["certification_receipt"]["material"]["protocol_hash"] = "1" * 64
    stale_ledger["records"][0]["certification_receipt"]["sha256"] = hashlib.sha256(
        json.dumps(
            stale_ledger["records"][0]["certification_receipt"]["material"],
            sort_keys=True,
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    stale_ledger["records"][0]["receipt_sha256"] = stale_ledger["records"][0]["certification_receipt"]["sha256"]
    stale_material = {key: value for key, value in stale_ledger["records"][0].items() if key != "record_hash"}
    stale_ledger["records"][0]["record_hash"] = hashlib.sha256(
        json.dumps(stale_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    stale_ledger["latest_record_hash"] = stale_ledger["records"][0]["record_hash"]
    ledger_path.write_text(json.dumps(stale_ledger, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest)]) == 0
    stale_readiness = read_stdout_json(capsys)
    stale_blocker_gates = {item["gate"] for item in stale_readiness["blockers"]}
    assert stale_readiness["provider_certification_ledger"]["integrity_status"] == "pass"
    assert stale_readiness["provider_certification_ledger"]["protocol_status"] == "stale"
    assert "provider_certification_protocols_current" in stale_blocker_gates
    assert stale_readiness["provider_certification_ledger"]["domains"]["ziwei"]["protocol_matches_current"] is False

    tampered_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    tampered_ledger["records"][0]["domain"] = "qimen"
    tampered_ledger["records"][0]["certification_receipt"]["material"]["domain"] = "qimen"
    tampered_material = {key: value for key, value in tampered_ledger["records"][0].items() if key != "record_hash"}
    tampered_ledger["records"][0]["record_hash"] = hashlib.sha256(
        json.dumps(tampered_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    tampered_ledger["latest_record_hash"] = tampered_ledger["records"][0]["record_hash"]
    ledger_path.write_text(json.dumps(tampered_ledger, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest)]) == 0
    tampered_readiness = read_stdout_json(capsys)
    tampered_blocker_gates = {item["gate"] for item in tampered_readiness["blockers"]}
    assert "provider_certification_ledger_integrity" in tampered_blocker_gates
    assert tampered_readiness["provider_certification_ledger"]["integrity_status"] == "fail"
    assert any(
        "certification_receipt sha256 mismatch" in item
        for item in tampered_readiness["provider_certification_ledger"]["failures"]
    )

    release_ledger_path = Path(readiness["release_manifest_ledger"]["path"])
    release_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    release_ledger_path.write_text("{not valid json", encoding="utf-8")
    assert main(["--repo", str(repo), "production-readiness", "--manifest", str(example_manifest)]) == 0
    release_ledger_tampered_readiness = read_stdout_json(capsys)
    release_ledger_blocker_gates = {item["gate"] for item in release_ledger_tampered_readiness["blockers"]}
    assert "release_manifest_ledger_integrity" in release_ledger_blocker_gates
    assert release_ledger_tampered_readiness["release_manifest_ledger"]["exists"] is True
    assert release_ledger_tampered_readiness["release_manifest_ledger"]["integrity_status"] == "fail"
    assert any(
        item["id"] == "repair_release_manifest_ledger_integrity"
        for item in release_ledger_tampered_readiness["resolution_plan"]["steps"]
    )
    release_ledger_path.unlink()

    assert main(["--repo", str(repo), "benchmark", "--baseline-version", "1"]) == 0
    benchmark_result = read_stdout_json(capsys)
    benchmark = benchmark_result["benchmark"]
    assert benchmark["baseline"]["genome_version"] == 1
    assert benchmark["candidate"]["genome_version"] == 2
    assert benchmark["candidate"]["empirical_validation"]["status"] == "ready_non_predictive"
    assert benchmark["candidate"]["reproducibility_manifest"]["run_type"] == "benchmark"
    benchmark_receipt_sha256 = benchmark["candidate"]["benchmark_receipt"]["sha256"]
    assert len(benchmark_receipt_sha256) == 64
    assert benchmark_result["expected_benchmark_receipt_sha256"] is None
    assert benchmark_result["benchmark_receipt_matches_expected"] is None
    assert benchmark["score_delta"] > 0
    assert main(
        [
            "--repo",
            str(repo),
            "benchmark",
            "--baseline-version",
            "1",
            "--expected-benchmark-receipt-sha256",
            benchmark_receipt_sha256,
        ]
    ) == 0
    matched_benchmark = read_stdout_json(capsys)
    assert matched_benchmark["expected_benchmark_receipt_sha256"] == benchmark_receipt_sha256
    assert matched_benchmark["benchmark_receipt_matches_expected"] is True
    assert matched_benchmark["benchmark_receipt_mismatch_reason"] == ""
    assert main(
        [
            "--repo",
            str(repo),
            "benchmark",
            "--baseline-version",
            "1",
            "--expected-benchmark-receipt-sha256",
            "0" * 64,
        ]
    ) == 0
    mismatched_benchmark = read_stdout_json(capsys)
    assert mismatched_benchmark["benchmark_receipt_matches_expected"] is False
    assert mismatched_benchmark["benchmark_receipt_mismatch_reason"] == "benchmark receipt sha256 does not match expected value"

    assert main(["--repo", str(repo), "release-manifest", "--manifest", str(example_manifest)]) == 0
    release = read_stdout_json(capsys)
    assert release["status"] == "release_manifest_ready"
    assert release["release_approval_ready"] is False
    assert release["release_approval_status"] == "release_blocked"
    assert any(item["gate"] == "production_ready" for item in release["release_blockers"])
    assert release["release_manifest_receipt"]["material"]["release_approval_ready"] == release["release_approval_ready"]
    assert release["release_manifest_receipt"]["material"]["release_approval_status"] == release[
        "release_approval_status"
    ]
    assert release["release_manifest_receipt"]["material"]["release_blockers"] == release["release_blockers"]
    assert release["production_readiness_status"] == "production_blocked"
    assert release["production_ready"] is False
    assert release["release_gate_checks"]["history_integrity_passed"] is True
    assert release["release_gate_checks"]["audit_receipt_current"] is True
    assert release["release_gate_checks"]["provider_onboarding_receipt_current"] is True
    assert release["release_gate_checks"]["provider_protocols_receipt_current"] is True
    assert release["release_gate_checks"]["benchmark_receipt_current"] is True
    assert release["release_gate_checks"]["outcome_dataset_split_coverage_bound"] is True
    assert release["release_gate_checks"]["provider_audit_contract_gates_bound"] is True
    assert release["release_gate_checks"]["outcome_statistical_plan_preregistration_bound"] is True
    assert release["release_gate_checks"]["classical_latest_refresh_receipt_bound"] is True
    assert release["release_gate_checks"]["blocked_capability_coverage_bound"] is True
    assert release["release_gate_checks"]["known_gap_handoff_bundle_bound"] is True
    assert release["release_gate_checks"]["known_gap_command_coverage_bound"] is True
    assert release["readiness_receipt"]["material"]["known_gap_handoff_bundle"]["status"] == "ready"
    assert release["release_manifest_receipt"]["material"]["known_gap_handoff_bundle"] == release[
        "readiness_receipt"
    ]["material"]["known_gap_handoff_bundle"]
    assert release["release_manifest_receipt"]["material"]["release_gate_checks"] == release["release_gate_checks"]
    assert len(release["audit_receipt"]["sha256"]) == 64
    assert len(release["provider_onboarding_receipt"]["sha256"]) == 64
    assert release["provider_onboarding_receipt"]["material"]["domain_count"] == 4
    assert len(release["provider_protocols_receipt"]["sha256"]) == 64
    assert release["provider_protocols_receipt"]["material"]["domain_count"] == 4
    assert len(release["benchmark_receipt"]["sha256"]) == 64
    assert len(release["readiness_receipt"]["sha256"]) == 64
    assert len(release["release_manifest_receipt"]["sha256"]) == 64
    assert release["release_manifest_receipt"]["material"]["audit_receipt_sha256"] == release["audit_receipt"]["sha256"]
    assert release["release_manifest_receipt"]["material"]["provider_protocols_receipt_sha256"] == release[
        "provider_protocols_receipt"
    ]["sha256"]
    assert release["release_manifest_receipt"]["material"]["provider_protocols_receipt"] == release[
        "provider_protocols_receipt"
    ]
    assert release["release_manifest_receipt"]["material"]["provider_onboarding_receipt_sha256"] == release[
        "provider_onboarding_receipt"
    ]["sha256"]
    assert release["release_manifest_receipt"]["material"]["provider_onboarding_receipt"] == release[
        "provider_onboarding_receipt"
    ]
    assert release["github_comparison_receipt_sha256"] == release["github_comparison_receipt"]["sha256"]
    assert release["release_manifest_receipt"]["material"]["github_comparison_receipt_sha256"] == release[
        "github_comparison_receipt_sha256"
    ]
    assert release["release_manifest_receipt"]["material"]["github_comparison_receipt"] == release[
        "github_comparison_receipt"
    ]
    assert release["github_comparison_receipt"]["material"]["dimension_count"] == len(
        release["audit_receipt"]["material"]["github_comparison_matrix"]
    )
    assert release["plan_compliance_receipt_sha256"] == release["plan_compliance_receipt"]["sha256"]
    assert release["release_manifest_receipt"]["material"]["plan_compliance_receipt_sha256"] == release[
        "plan_compliance_receipt_sha256"
    ]
    assert release["release_manifest_receipt"]["material"]["plan_compliance_receipt"] == release[
        "plan_compliance_receipt"
    ]
    assert release["plan_compliance_receipt"]["material"]["section_count"] == release["audit_receipt"]["material"][
        "plan_compliance"
    ]["section_count"]
    assert release["release_manifest_receipt"]["material"]["benchmark_receipt_sha256"] == release["benchmark_receipt"]["sha256"]
    assert release["release_manifest_receipt"]["material"]["readiness_receipt_sha256"] == release["readiness_receipt"]["sha256"]
    assert release["release_manifest_receipt"]["material"]["evolution_trigger_receipt_sha256"] == release[
        "evolution_trigger_receipt_sha256"
    ]
    assert release["release_manifest_receipt"]["material"]["evolution_trigger_receipt"] == release[
        "evolution_trigger_receipt"
    ]
    assert release["release_manifest_receipt"]["material"]["evolution_trigger_receipt_current"] == release[
        "evolution_trigger_receipt_current"
    ]
    if release["evolution_trigger_receipt"] is None:
        assert release["evolution_trigger_receipt_sha256"] is None
        assert release["evolution_trigger_receipt_current"] is True
    else:
        assert release["evolution_trigger_receipt_sha256"] == release["evolution_trigger_receipt"]["sha256"]
        assert release["evolution_trigger_receipt_current"] is True
    assert release["release_manifest_receipt"]["material"]["method_surface"]["sha256"] == release["audit_receipt"][
        "material"
    ]["method_surface"]["sha256"]
    assert len(release["release_manifest_receipt"]["material"]["method_surface"]["domains"]["bazi"]) == 8
    release_deliberation_coverage = release["release_manifest_receipt"]["material"][
        "readiness_deliberation_receipt_coverage"
    ]
    readiness_request_audit = release["readiness_receipt"]["material"]["current_benchmark"]["request_provenance_audit"]
    assert release_deliberation_coverage["case_count"] == readiness_request_audit["case_count"]
    assert release_deliberation_coverage["covered_count"] == readiness_request_audit[
        "deliberation_receipt_covered_count"
    ]
    assert release_deliberation_coverage["coverage_complete"] is True
    assert release_deliberation_coverage["receipt_count"] == release_deliberation_coverage["case_count"]
    assert set(release_deliberation_coverage["claim_counts"]) == {4}
    assert len(release_deliberation_coverage["receipt_sha256s"]) == release_deliberation_coverage["case_count"]
    assert all(len(item) == 64 for item in release_deliberation_coverage["receipt_sha256s"])
    annual_timeline_coverage = release["release_manifest_receipt"]["material"]["annual_timeline_receipt_coverage"]
    assert annual_timeline_coverage["case_count"] == readiness_request_audit["case_count"]
    assert annual_timeline_coverage["covered_count"] == readiness_request_audit[
        "annual_timeline_receipt_covered_count"
    ]
    assert annual_timeline_coverage["bound_count"] == readiness_request_audit["annual_timeline_receipt_bound_count"]
    assert annual_timeline_coverage["coverage_complete"] is True
    assert annual_timeline_coverage["binding_complete"] is True
    assert annual_timeline_coverage["receipt_count"] == annual_timeline_coverage["case_count"]
    assert annual_timeline_coverage["unbound_cases"] == []
    assert len(annual_timeline_coverage["receipt_sha256s"]) == annual_timeline_coverage["case_count"]
    assert all(len(item) == 64 for item in annual_timeline_coverage["receipt_sha256s"])
    assert all(item > 0 for item in annual_timeline_coverage["row_counts"])
    monthly_luck_coverage = release["release_manifest_receipt"]["material"]["monthly_luck_receipt_coverage"]
    assert monthly_luck_coverage["case_count"] == readiness_request_audit["case_count"]
    assert monthly_luck_coverage["covered_count"] == readiness_request_audit["monthly_luck_receipt_covered_count"]
    assert monthly_luck_coverage["bound_count"] == readiness_request_audit["monthly_luck_receipt_bound_count"]
    assert monthly_luck_coverage["coverage_complete"] is True
    assert monthly_luck_coverage["binding_complete"] is True
    assert monthly_luck_coverage["receipt_count"] == monthly_luck_coverage["case_count"]
    assert monthly_luck_coverage["unbound_cases"] == []
    assert len(monthly_luck_coverage["receipt_sha256s"]) == monthly_luck_coverage["case_count"]
    assert all(len(item) == 64 for item in monthly_luck_coverage["receipt_sha256s"])
    assert all(item > 0 for item in monthly_luck_coverage["row_counts"])
    auspicious_calendar_coverage = release["release_manifest_receipt"]["material"][
        "auspicious_calendar_receipt_coverage"
    ]
    assert auspicious_calendar_coverage["case_count"] == readiness_request_audit["case_count"]
    assert auspicious_calendar_coverage["covered_count"] == readiness_request_audit[
        "auspicious_calendar_receipt_covered_count"
    ]
    assert auspicious_calendar_coverage["bound_count"] == readiness_request_audit[
        "auspicious_calendar_receipt_bound_count"
    ]
    assert auspicious_calendar_coverage["coverage_complete"] is True
    assert auspicious_calendar_coverage["binding_complete"] is True
    assert auspicious_calendar_coverage["receipt_count"] == auspicious_calendar_coverage["case_count"]
    assert auspicious_calendar_coverage["unbound_cases"] == []
    assert len(auspicious_calendar_coverage["receipt_sha256s"]) == auspicious_calendar_coverage["case_count"]
    assert all(len(item) == 64 for item in auspicious_calendar_coverage["receipt_sha256s"])
    assert all(item > 0 for item in auspicious_calendar_coverage["row_counts"])
    birth_match_coverage = release["release_manifest_receipt"]["material"]["external_payload_birth_match_coverage"]
    assert birth_match_coverage["case_count"] == readiness_request_audit["case_count"]
    assert birth_match_coverage["match_case_count"] == readiness_request_audit[
        "external_payload_birth_match_case_count"
    ]
    assert birth_match_coverage["coverage_complete"] is True
    assert birth_match_coverage["mismatch_domains"] == []
    assert birth_match_coverage["match_cases"] == readiness_request_audit["external_payload_birth_match_cases"]
    provider_action_plan_coverage = release["release_manifest_receipt"]["material"]["provider_action_plan_coverage"]
    readiness_provider_action_plan_audit = release["readiness_receipt"]["material"]["current_benchmark"][
        "provider_action_plan_audit"
    ]
    assert provider_action_plan_coverage["case_count"] == readiness_provider_action_plan_audit["case_count"]
    assert provider_action_plan_coverage["covered_count"] == readiness_provider_action_plan_audit["covered_count"]
    assert provider_action_plan_coverage["coverage_complete"] is True
    assert provider_action_plan_coverage["unresolved"] == []
    assert provider_action_plan_coverage["action_plan_counts"] == readiness_provider_action_plan_audit[
        "action_plan_counts"
    ]
    classical_source_receipt_coverage = release["release_manifest_receipt"]["material"][
        "classical_source_receipt_coverage"
    ]
    readiness_classical_source = release["readiness_receipt"]["material"]["classical_source_refresh"]
    assert classical_source_receipt_coverage["status"] == readiness_classical_source["status"]
    assert classical_source_receipt_coverage["valid"] == readiness_classical_source["valid"]
    assert classical_source_receipt_coverage["receipt_present"] is True
    assert (
        classical_source_receipt_coverage["source_list_receipt_sha256"]
        == readiness_classical_source["source_list_receipt_sha256"]
    )
    release_gap_plan_coverage = release["release_manifest_receipt"]["material"]["known_gap_resolution_plan_coverage"]
    assert release_gap_plan_coverage == release["readiness_receipt"]["material"]["known_gap_resolution_plan_coverage"]
    assert release_gap_plan_coverage["coverage_complete"] is True
    release_registry_audit = release["release_manifest_receipt"]["material"]["production_gate_registry_audit"]
    assert release_registry_audit == release["readiness_receipt"]["material"]["production_gate_registry_audit"]
    assert release_registry_audit["registry_current"] is True
    assert release_registry_audit["missing_from_registry"] == []
    assert "production_gate_registry_current" in release_registry_audit["actual_gate_ids"]
    assert release["release_manifest_receipt"]["material"]["production_resolution_plan_summary"] == release[
        "readiness_receipt"
    ]["material"]["production_resolution_plan_summary"]
    assert (
        release["release_manifest_receipt"]["material"]["provider_ledger"]["latest_record_hash"]
        == release["provider_ledger"]["latest_record_hash"]
    )
    assert release["release_manifest_receipt"]["material"]["provider_ledger"]["latest_record_index"] == 0
    assert (
        release["release_manifest_receipt"]["material"]["provider_ledger"]["request_receipt_status"]
        == release["provider_ledger"]["request_receipt_status"]
    )
    assert (
        release["release_manifest_receipt"]["material"]["provider_ledger"]["reference_contract_status"]
        == release["provider_ledger"]["reference_contract_status"]
    )
    assert (
        release["release_manifest_receipt"]["material"]["provider_ledger"]["command_fingerprint_status"]
        == release["provider_ledger"]["command_fingerprint_status"]
    )
    assert (
        release["release_manifest_receipt"]["material"]["provider_ledger"]["reference_contract_failures"]
        == release["provider_ledger"]["reference_contract_failures"]
    )
    assert (
        release["release_manifest_receipt"]["material"]["provider_ledger"]["command_fingerprint_failures"]
        == release["provider_ledger"]["command_fingerprint_failures"]
    )
    release_outcome_material = release["release_manifest_receipt"]["material"]["outcome_dataset"]
    assert release_outcome_material["content_hash"] == release["outcome_dataset"]["content_hash"]
    assert release_outcome_material["data_split_record_coverage"]["coverage_complete"] is True
    assert len(release_outcome_material["data_split_record_coverage"]["split_fingerprint"]) == 64
    assert release_outcome_material["external_review"]["reviewed"] is True
    assert release_outcome_material["data_split"]["frozen"] is True
    assert release_outcome_material["label_collection"]["collected_before_analysis"] is True
    assert "data_split_frozen" in release_outcome_material["governance_gate_ids"]
    assert release["ledger_record_requested"] is False
    assert release["ledger_recorded"] is False
    release_receipt_sha256 = release["release_manifest_receipt"]["sha256"]
    assert main(["--repo", str(repo), "release-ledger"]) == 0
    empty_release_ledger = read_stdout_json(capsys)
    assert empty_release_ledger["ledger"]["exists"] is False
    assert empty_release_ledger["ledger"]["integrity_status"] == "fail"
    assert empty_release_ledger["ledger"]["record_count"] == 0
    assert empty_release_ledger["ledger"]["latest_record_index"] is None
    assert main(["--repo", str(repo), "release-drift", "--manifest", str(example_manifest)]) == 0
    empty_release_drift = read_stdout_json(capsys)
    assert empty_release_drift["drift"]["status"] == "not_checked"
    assert empty_release_drift["drift"]["passed"] is False
    assert "ledger integrity must pass" in empty_release_drift["drift"]["failures"][0]
    assert main(
        [
            "--repo",
            str(repo),
            "release-manifest",
            "--manifest",
            str(example_manifest),
            "--expected-release-manifest-receipt-sha256",
            release_receipt_sha256,
        ]
    ) == 0
    matched_release = read_stdout_json(capsys)
    assert matched_release["release_manifest_receipt_matches_expected"] is True
    assert matched_release["release_manifest_receipt_mismatch_reason"] == ""
    assert main(
        [
            "--repo",
            str(repo),
            "release-manifest",
            "--manifest",
            str(example_manifest),
            "--expected-release-manifest-receipt-sha256",
            "0" * 64,
        ]
    ) == 0
    mismatched_release = read_stdout_json(capsys)
    assert mismatched_release["release_manifest_receipt_matches_expected"] is False
    assert mismatched_release["release_manifest_receipt_mismatch_reason"] == (
        "release manifest receipt sha256 does not match expected value"
    )
    assert main(
        [
            "--repo",
            str(repo),
            "release-manifest",
            "--manifest",
            str(example_manifest),
            "--expected-release-manifest-receipt-sha256",
            "0" * 64,
            "--record",
        ]
    ) == 0
    blocked_release_record = read_stdout_json(capsys)
    assert blocked_release_record["ledger_record_requested"] is True
    assert blocked_release_record["ledger_recorded"] is False
    assert blocked_release_record["ledger_record_hash"] is None
    assert blocked_release_record["ledger_record_blocker"] == (
        "release manifest receipt must match expected value before recording"
    )
    assert main(["--repo", str(repo), "release-ledger"]) == 0
    still_empty_release_ledger = read_stdout_json(capsys)
    assert still_empty_release_ledger["ledger"]["exists"] is False
    assert still_empty_release_ledger["ledger"]["latest_record_index"] is None
    assert main(
        [
            "--repo",
            str(repo),
            "release-manifest",
            "--manifest",
            str(example_manifest),
            "--expected-release-manifest-receipt-sha256",
            release_receipt_sha256,
            "--record",
        ]
    ) == 0
    recorded_release = read_stdout_json(capsys)
    assert recorded_release["ledger_record_requested"] is True
    assert recorded_release["ledger_recorded"] is True
    assert recorded_release["ledger_record_index"] == 0
    assert len(recorded_release["ledger_record_hash"]) == 64
    release_ledger = json.loads(Path(recorded_release["ledger_record_path"]).read_text(encoding="utf-8"))
    assert release_ledger["latest_record_index"] == 0
    assert release_ledger["records"][0]["release_manifest_receipt_sha256"] == release_receipt_sha256
    assert release_ledger["records"][0]["record_hash"] == recorded_release["ledger_record_hash"]
    assert release_ledger["records"][0]["provider_protocols_receipt_sha256"] == release["release_manifest_receipt"][
        "material"
    ]["provider_protocols_receipt_sha256"]
    assert release_ledger["records"][0]["provider_protocols_receipt"] == release["release_manifest_receipt"][
        "material"
    ]["provider_protocols_receipt"]
    assert release_ledger["records"][0]["provider_onboarding_receipt_sha256"] == release["release_manifest_receipt"][
        "material"
    ]["provider_onboarding_receipt_sha256"]
    assert release_ledger["records"][0]["provider_onboarding_receipt"] == release["release_manifest_receipt"][
        "material"
    ]["provider_onboarding_receipt"]
    assert release_ledger["records"][0]["github_comparison_receipt_sha256"] == release["release_manifest_receipt"][
        "material"
    ]["github_comparison_receipt_sha256"]
    assert release_ledger["records"][0]["github_comparison_receipt"] == release["release_manifest_receipt"][
        "material"
    ]["github_comparison_receipt"]
    assert release_ledger["records"][0]["plan_compliance_receipt_sha256"] == release["release_manifest_receipt"][
        "material"
    ]["plan_compliance_receipt_sha256"]
    assert release_ledger["records"][0]["plan_compliance_receipt"] == release["release_manifest_receipt"][
        "material"
    ]["plan_compliance_receipt"]
    assert release_ledger["records"][0]["provider_action_plan_coverage"] == release["release_manifest_receipt"][
        "material"
    ]["provider_action_plan_coverage"]
    assert release_ledger["records"][0]["annual_timeline_receipt_coverage"] == release["release_manifest_receipt"][
        "material"
    ]["annual_timeline_receipt_coverage"]
    assert release_ledger["records"][0]["monthly_luck_receipt_coverage"] == release["release_manifest_receipt"][
        "material"
    ]["monthly_luck_receipt_coverage"]
    assert release_ledger["records"][0]["auspicious_calendar_receipt_coverage"] == release[
        "release_manifest_receipt"
    ]["material"]["auspicious_calendar_receipt_coverage"]
    assert release_ledger["records"][0]["external_payload_birth_match_coverage"] == release[
        "release_manifest_receipt"
    ]["material"]["external_payload_birth_match_coverage"]
    assert release_ledger["records"][0]["classical_source_receipt_coverage"] == release["release_manifest_receipt"][
        "material"
    ]["classical_source_receipt_coverage"]
    assert release_ledger["records"][0]["known_gap_resolution_plan_coverage"] == release["release_manifest_receipt"][
        "material"
    ]["known_gap_resolution_plan_coverage"]
    assert release_ledger["records"][0]["production_gate_registry_audit"] == release["release_manifest_receipt"][
        "material"
    ]["production_gate_registry_audit"]
    assert release_ledger["records"][0]["production_resolution_plan_summary"] == release["release_manifest_receipt"][
        "material"
    ]["production_resolution_plan_summary"]
    assert release_ledger["records"][0]["release_approval_ready"] == release["release_manifest_receipt"]["material"][
        "release_approval_ready"
    ]
    assert release_ledger["records"][0]["release_blockers"] == release["release_manifest_receipt"]["material"][
        "release_blockers"
    ]
    assert release_ledger["records"][0]["outcome_dataset"] == release["release_manifest_receipt"]["material"]["outcome_dataset"]
    assert release_ledger["records"][0]["evolution_trigger_receipt_sha256"] == release[
        "release_manifest_receipt"
    ]["material"]["evolution_trigger_receipt_sha256"]
    assert release_ledger["records"][0]["evolution_trigger_receipt"] == release["release_manifest_receipt"][
        "material"
    ]["evolution_trigger_receipt"]
    assert release_ledger["records"][0]["evolution_trigger_receipt_current"] == release["release_manifest_receipt"][
        "material"
    ]["evolution_trigger_receipt_current"]
    assert main(["--repo", str(repo), "release-ledger"]) == 0
    release_ledger_status = read_stdout_json(capsys)
    assert release_ledger_status["ledger"]["exists"] is True
    assert release_ledger_status["ledger"]["integrity_status"] == "pass"
    assert release_ledger_status["ledger"]["record_count"] == 1
    assert release_ledger_status["ledger"]["latest_record_index"] == 0
    assert release_ledger_status["ledger"]["latest_record_hash"] == recorded_release["ledger_record_hash"]
    assert release_ledger_status["ledger"]["latest_release_manifest_receipt_sha256"] == release_receipt_sha256
    assert main(["--repo", str(repo), "release-drift", "--manifest", str(example_manifest)]) == 0
    release_drift = read_stdout_json(capsys)
    assert release_drift["drift"]["status"] == "passed"
    assert release_drift["drift"]["passed"] is True
    assert release_drift["drift"]["matches_expected"] is True
    assert release_drift["drift"]["expected_release_manifest_receipt_sha256"] == release_receipt_sha256
    assert release_drift["drift"]["current_release_manifest_receipt_sha256"] == release_receipt_sha256
    assert main(["--repo", str(repo), "release-drift"]) == 0
    mismatched_release_drift = read_stdout_json(capsys)
    assert mismatched_release_drift["drift"]["status"] == "drift_detected"
    assert mismatched_release_drift["drift"]["passed"] is False
    assert mismatched_release_drift["drift"]["matches_expected"] is False
    assert mismatched_release_drift["drift"]["failures"] == [
        "current release manifest receipt does not match latest ledger record"
    ]
    release_ledger_path = Path(release_ledger_status["ledger"]["path"])
    tampered_summary_release_ledger = json.loads(release_ledger_path.read_text(encoding="utf-8"))
    tampered_summary_release_ledger["records"][0]["candidate_name"] = "tampered-candidate"
    tampered_summary_material = {
        key: value
        for key, value in tampered_summary_release_ledger["records"][0].items()
        if key != "record_hash"
    }
    tampered_summary_release_ledger["records"][0]["record_hash"] = hashlib.sha256(
        json.dumps(tampered_summary_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    tampered_summary_release_ledger["latest_record_hash"] = tampered_summary_release_ledger["records"][0]["record_hash"]
    release_ledger_path.write_text(json.dumps(tampered_summary_release_ledger, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "release-ledger"]) == 0
    tampered_summary_release_ledger_status = read_stdout_json(capsys)
    assert tampered_summary_release_ledger_status["ledger"]["integrity_status"] == "fail"
    assert any(
        "candidate_name does not match release manifest receipt" in item
        for item in tampered_summary_release_ledger_status["ledger"]["failures"]
    )
    release_ledger_path.write_text(json.dumps(release_ledger, ensure_ascii=False), encoding="utf-8")
    tampered_release_ledger = json.loads(release_ledger_path.read_text(encoding="utf-8"))
    tampered_release_ledger["records"][0]["release_manifest_receipt"]["material"]["status"] = "tampered"
    release_ledger_path.write_text(json.dumps(tampered_release_ledger, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "release-ledger"]) == 0
    tampered_release_ledger_status = read_stdout_json(capsys)
    assert tampered_release_ledger_status["ledger"]["integrity_status"] == "fail"
    assert any(
        "release_manifest_receipt sha256 mismatch" in item
        for item in tampered_release_ledger_status["ledger"]["failures"]
    )
    tampered_release_ledger = release_ledger
    tampered_release_ledger["latest_record_index"] = 99
    release_ledger_path.write_text(json.dumps(tampered_release_ledger, ensure_ascii=False), encoding="utf-8")
    assert main(["--repo", str(repo), "release-ledger"]) == 0
    tampered_index_release_ledger_status = read_stdout_json(capsys)
    assert tampered_index_release_ledger_status["ledger"]["integrity_status"] == "fail"
    assert any(
        "latest_record_index does not match last record" in item
        for item in tampered_index_release_ledger_status["ledger"]["failures"]
    )
    assert any("record 0 hash mismatch" in item for item in tampered_release_ledger_status["ledger"]["failures"])
    assert main(["--repo", str(repo), "release-drift", "--manifest", str(example_manifest)]) == 0
    tampered_release_drift = read_stdout_json(capsys)
    assert tampered_release_drift["drift"]["status"] == "not_checked"
    assert tampered_release_drift["drift"]["passed"] is False
    assert tampered_release_drift["drift"]["failures"] == [
        "release manifest ledger integrity must pass before drift can be checked"
    ]

    assert main(["--repo", str(repo), "schema"]) == 0
    schema_result = read_stdout_json(capsys)
    assert "AnalyzeRequest" in schema_result["schemas"]
    assert "AnalyzeResponse" in schema_result["schemas"]
    assert "BirthProfile" in schema_result["schemas"]
    assert "RequestProvenance" in schema_result["schemas"]
    assert "ArchiveIntegrityReport" in schema_result["schemas"]
    assert "AnnualTimelineRow" in schema_result["schemas"]
    assert "AnnualTimelineTopic" in schema_result["schemas"]
    assert "AnnualLuck" in schema_result["schemas"]
    assert "AnnualLuckActiveMajorLuck" in schema_result["schemas"]
    assert "AnnualLuckBaziEvidence" in schema_result["schemas"]
    assert "AnnualLuckRow" in schema_result["schemas"]
    assert "AnnualLuckRowElements" in schema_result["schemas"]
    assert "AnnualLuckNatalPillarMatch" in schema_result["schemas"]
    assert "AnnualLuckTenGodPair" in schema_result["schemas"]
    assert "AnnualPhaseSummary" in schema_result["schemas"]
    assert "AnnualPhaseTopicHighlight" in schema_result["schemas"]
    assert "BaziMajorLuckAnnualPreview" in schema_result["schemas"]
    assert "BaziMajorLuckPeriod" in schema_result["schemas"]
    assert "BaziMethodMatrixItem" in schema_result["schemas"]
    assert "BenchmarkResult" in schema_result["schemas"]
    assert "BenchmarkCaseResult" in schema_result["schemas"]
    assert "BenchmarkCaseReportFeatures" in schema_result["schemas"]
    assert "BenchmarkExternalPayloadBirthMatchStatus" in schema_result["schemas"]
    assert "BenchmarkResponse" in schema_result["schemas"]
    assert "ReleaseManifestResponse" in schema_result["schemas"]
    assert "ReleaseManifestLedgerResponse" in schema_result["schemas"]
    assert "ReleaseManifestLedgerStatus" in schema_result["schemas"]
    assert "ReleaseManifestDriftResponse" in schema_result["schemas"]
    assert "ReleaseManifestDriftStatus" in schema_result["schemas"]
    assert "ProviderSummary" in schema_result["schemas"]
    assert "ProviderIntegrationPlan" in schema_result["schemas"]
    assert "ProviderIntegrationTarget" in schema_result["schemas"]
    assert "StatusResponse" in schema_result["schemas"]
    assert "VersionHistoryResponse" in schema_result["schemas"]
    assert "VersionHistoryIntegrity" in schema_result["schemas"]
    assert "VersionHistoryRow" in schema_result["schemas"]
    assert "LatestEvolutionStatus" in schema_result["schemas"]
    assert "EvolveResponse" in schema_result["schemas"]
    assert "EvolutionSelectionDecision" in schema_result["schemas"]
    assert "MemoryProfile" in schema_result["schemas"]
    assert "FeedbackMemorySafetyAudit" in schema_result["schemas"]
    assert "GenomeLineage" in schema_result["schemas"]
    assert "LineageIntegrityReport" in schema_result["schemas"]
    assert "ProviderChecksResponse" in schema_result["schemas"]
    assert "ProviderCertificationResponse" in schema_result["schemas"]
    assert "ProviderCertificationReceipt" in schema_result["schemas"]
    assert "ProviderCertificationLedgerStatus" in schema_result["schemas"]
    assert "ProviderCertificationLedgerDomainStatus" in schema_result["schemas"]
    assert "ProviderCertificationLedgerResponse" in schema_result["schemas"]
    assert "ProviderCertificationDriftCheck" in schema_result["schemas"]
    assert "ProviderCertificationDriftResponse" in schema_result["schemas"]
    assert "ProviderCertificationDriftStatus" in schema_result["schemas"]
    assert "ProviderProtocolsResponse" in schema_result["schemas"]
    assert "CapabilityAuditResponse" in schema_result["schemas"]
    assert "ProviderReadinessCheck" in schema_result["schemas"]
    assert "ProviderReadinessMatrixItem" in schema_result["schemas"]
    assert "ProviderProvenanceAudit" in schema_result["schemas"]
    assert "ProductionReadinessGate" in schema_result["schemas"]
    assert "ProductionReadinessResponse" in schema_result["schemas"]
    assert "ProductionResolutionPlan" in schema_result["schemas"]
    assert "ProductionResolutionStep" in schema_result["schemas"]
    assert "OutcomeDatasetManifest" in schema_result["schemas"]
    assert "OutcomeDatasetAudit" in schema_result["schemas"]
    assert "OutcomeDatasetAuditResponse" in schema_result["schemas"]
    assert "OutcomeDatasetEvolutionGate" in schema_result["schemas"]
    assert "OutcomeDatasetReceiptMaterial" in schema_result["schemas"]
    assert "OutcomeDatasetRecord" in schema_result["schemas"]
    assert "OutcomeRecordLabel" in schema_result["schemas"]
    assert "OutcomeQualityTaskProjection" in schema_result["schemas"]
    assert "ProductionReadinessReceipt" in schema_result["schemas"]
    assert "ProductionReadinessReceiptMaterial" in schema_result["schemas"]
    assert "ReleaseManifestReceipt" in schema_result["schemas"]
    assert "ReleaseManifestReceiptMaterial" in schema_result["schemas"]
    assert "PlanCompliance" in schema_result["schemas"]
    assert "PlanComplianceSection" in schema_result["schemas"]
    assert "StateOfArtAssessment" in schema_result["schemas"]
    assert "ReproducibilityManifest" in schema_result["schemas"]
    assert "ReproducibilityStrategyFingerprint" in schema_result["schemas"]
    assert "RollbackResponse" in schema_result["schemas"]
    assert "RollbackRequest" in schema_result["schemas"]
    assert "SpecialistReport" in schema_result["schemas"]
    assert "SpecialistLayer" in schema_result["schemas"]
    assert "SpecialistSource" in schema_result["schemas"]
    assert "AuspiciousRecommendedHour" in schema_result["schemas"]
    assert "TopicSynthesisItem" in schema_result["schemas"]
    assert "TopicSynthesisConfidence" in schema_result["schemas"]
    assert "TopicSynthesisCrossAgentEvidence" in schema_result["schemas"]
    assert "VoteChallenge" in schema_result["schemas"]
    assert set(schema_result["provider_protocols"]["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert schema_result["provider_protocols"]["domains"]["ziwei"]["env_var"] == "SEMAS_ZIWEI_CLI"
    assert schema_result["provider_protocols"]["domains"]["ziwei"]["provenance_env_var"] == "SEMAS_ZIWEI_PROVIDER_PROVENANCE"
    assert schema_result["provider_protocols"]["domains"]["ziwei"]["production_requirements"]
    assert "certify-provider ziwei" in schema_result["provider_protocols"]["domains"]["ziwei"]["certification_command_template"]
    assert "palaces" in schema_result["provider_protocols"]["domains"]["qimen"]["stdout_schema"]["required"]
    assert "language" in schema_result["schemas"]["AnalyzeRequest"]["properties"]
    assert "llm_synthesis" in schema_result["schemas"]["AnalyzeRequest"]["properties"]
    assert "auspicious_start_date" in schema_result["schemas"]["AnalyzeRequest"]["properties"]
    assert "professional_charts" in schema_result["schemas"]["AnalyzeRequest"]["properties"]["birth"]["properties"]
    professional_chart_properties = schema_result["schemas"]["AnalyzeRequest"]["properties"]["birth"]["properties"]["professional_charts"]["properties"]
    assert "bazi" in professional_chart_properties
    assert "xuanze" in professional_chart_properties
    assert professional_chart_properties["bazi"]["required"] == ["source", "version", "license_or_review"]
    provider_summary_schema = schema_result["schemas"]["ProviderSummary"]
    provider_action_schema = schema_result["schemas"]["ProviderActionPlanItem"]
    provider_domain_schema = schema_result["schemas"]["ProviderDomainStatus"]
    provider_checks_schema = schema_result["schemas"]["ProviderChecksResponse"]
    provider_plan_schema = schema_result["schemas"]["ProviderIntegrationPlan"]
    provider_target_schema = schema_result["schemas"]["ProviderIntegrationTarget"]
    audit_schema = schema_result["schemas"]["CapabilityAuditResponse"]
    assert "action_plan" in provider_summary_schema["required"]
    assert "readiness_matrix" in provider_summary_schema["required"]
    assert "professional_domain_count" in provider_summary_schema["required"]
    assert "fallback_domain_count" in provider_summary_schema["required"]
    assert provider_summary_schema["properties"]["action_plan"]["items"]["$ref"] == "#/schemas/ProviderActionPlanItem"
    assert provider_summary_schema["properties"]["readiness_matrix"]["items"]["$ref"] == (
        "#/schemas/ProviderReadinessMatrixItem"
    )
    readiness_matrix_schema = schema_result["schemas"]["ProviderReadinessMatrixItem"]
    assert "interpretation_mode" in readiness_matrix_schema["required"]
    assert "confidence_level" in readiness_matrix_schema["required"]
    assert readiness_matrix_schema["properties"]["blocking_reasons"]["items"]["type"] == "string"
    assert "certification_command_template" in provider_action_schema["required"]
    assert "production_readiness_command_template" in provider_action_schema["required"]
    assert "deployment_checklist" in provider_action_schema["required"]
    assert "contract_valid" in provider_domain_schema["required"]
    assert "provider_provenance_valid" in provider_domain_schema["required"]
    assert "external_payload_receipt_valid" in provider_domain_schema["required"]
    assert "external_payload_receipt_sha256" in provider_domain_schema["required"]
    assert "external_payload_birth_match_status" in provider_domain_schema["required"]
    assert "external_payload_birth_mismatch_fields" in provider_domain_schema["required"]
    assert "external_payload_declared_birth_profile_sha256" in provider_domain_schema["required"]
    assert "interpretation_mode" in provider_domain_schema["required"]
    assert "confidence_level" in provider_domain_schema["required"]
    assert "blocking_reasons" in provider_domain_schema["required"]
    assert provider_domain_schema["properties"]["contract_valid"]["type"] == "boolean"
    assert "symbolic_fallback" in provider_domain_schema["properties"]["interpretation_mode"]["enum"]
    assert "research_symbolic" in provider_domain_schema["properties"]["confidence_level"]["enum"]
    assert provider_domain_schema["properties"]["blocking_reasons"]["items"]["type"] == "string"
    assert provider_domain_schema["properties"]["provider_provenance_missing"]["items"]["type"] == "string"
    assert provider_domain_schema["properties"]["external_payload_birth_mismatch_fields"]["items"]["type"] == "string"
    assert provider_checks_schema["properties"]["profile_readiness"]["$ref"] == "#/schemas/ProviderProfileReadiness"
    assert provider_checks_schema["properties"]["integration_plan"]["$ref"] == "#/schemas/ProviderIntegrationPlan"
    assert provider_checks_schema["properties"]["checks"]["additionalProperties"]["$ref"] == "#/schemas/ProviderReadinessCheck"
    assert schema_result["schemas"]["ProviderProfileReadiness"]["properties"]["required_groups"]["items"]["$ref"] == (
        "#/schemas/ProviderProfileRequiredGroup"
    )
    assert "live_required" in schema_result["schemas"]["ProviderProfileReadiness"]["required"]
    assert "accepted_checks" in schema_result["schemas"]["ProviderProfileRequiredGroup"]["required"]
    assert provider_checks_schema["properties"]["reference_chart_checks"]["$ref"] == "#/schemas/ReferenceChartChecks"
    assert schema_result["schemas"]["ReferenceChartChecks"]["properties"]["method_coverage"]["$ref"] == (
        "#/schemas/ReferenceChartMethodCoverage"
    )
    assert schema_result["schemas"]["ReferenceChartChecks"]["properties"]["cases"]["items"]["$ref"] == (
        "#/schemas/ReferenceChartCaseCheck"
    )
    assert schema_result["schemas"]["ReferenceChartMethodCoverage"]["properties"]["domains"]["additionalProperties"][
        "$ref"
    ] == "#/schemas/ReferenceChartDomainMethodCoverage"
    assert "provenance_coverage" in schema_result["schemas"]["ReferenceChartCaseCheck"]["required"]
    assert "observed" in schema_result["schemas"]["ReferenceChartDomainMethodCoverage"]["required"]
    assert "provider_domain" in provider_target_schema["required"]
    assert "required_provenance_fields" in provider_target_schema["required"]
    assert "certification_commands" in provider_target_schema["required"]
    assert "drift_commands" in provider_target_schema["required"]
    assert "deployment_checklist" in provider_target_schema["required"]
    assert "bundled_example_policy" in provider_target_schema["required"]
    provider_readiness_schema = schema_result["schemas"]["ProviderReadinessCheck"]
    assert provider_readiness_schema["properties"]["provider_provenance_audit"]["$ref"] == "#/schemas/ProviderProvenanceAudit"
    assert provider_readiness_schema["properties"]["provider_command_fingerprint"]["$ref"] == (
        "#/schemas/ProviderCommandFingerprint"
    )
    assert provider_readiness_schema["properties"]["install_diagnostics"]["$ref"] == "#/schemas/ProviderInstallDiagnostics"
    assert "ProviderInstallDiagnostics" in schema_result["schemas"]
    assert "protocol_version" in provider_readiness_schema["required"]
    assert "protocol_hash" in provider_readiness_schema["required"]
    assert "install_diagnostics" in provider_readiness_schema["required"]
    assert (
        schema_result["schemas"]["ProviderCertificationResponse"]["properties"]["provider_provenance_audit"]["$ref"]
        == "#/schemas/ProviderProvenanceAudit"
    )
    assert (
        schema_result["schemas"]["ProviderCertificationResponse"]["properties"]["certification_receipt"]["$ref"]
        == "#/schemas/ProviderCertificationReceipt"
    )
    assert (
        schema_result["schemas"]["ProviderProtocolsResponse"]["properties"]["provider_protocols_receipt"]["$ref"]
        == "#/schemas/ProviderProtocolsReceipt"
    )
    assert (
        schema_result["schemas"]["ProviderProtocolsReceipt"]["properties"]["material"]["$ref"]
        == "#/schemas/ProviderProtocolsReceiptMaterial"
    )
    certification_schema = schema_result["schemas"]["ProviderCertificationResponse"]
    assert "command_override_used" in certification_schema["required"]
    assert "provenance_override_used" in certification_schema["required"]
    assert "certification_receipt" in certification_schema["required"]
    assert "protocol_version" in certification_schema["required"]
    assert "protocol_hash" in certification_schema["required"]
    assert "expected_receipt_sha256" in certification_schema["required"]
    assert "receipt_matches_expected" in certification_schema["required"]
    assert "receipt_mismatch_reason" in certification_schema["required"]
    assert "ledger_record_requested" in certification_schema["required"]
    assert "ledger_recorded" in certification_schema["required"]
    assert "ledger_record_hash" in certification_schema["required"]
    assert "reference_contract_coverage" in certification_schema["required"]
    assert "provider_command_fingerprint" in certification_schema["required"]
    assert certification_schema["properties"]["reference_contract_coverage"]["$ref"] == (
        "#/schemas/ProviderReferenceContractCoverage"
    )
    assert certification_schema["properties"]["provider_command_fingerprint"]["$ref"] == (
        "#/schemas/ProviderCommandFingerprint"
    )
    material_refs = {
        item["$ref"]
        for item in schema_result["schemas"]["ProviderCertificationReceipt"]["properties"]["material"]["anyOf"]
        if "$ref" in item
    }
    assert "#/schemas/ProviderCertificationReceiptMaterial" in material_refs
    assert "#/schemas/BenchmarkReceiptMaterial" in material_refs
    assert schema_result["schemas"]["ProviderCertificationReceiptMaterial"]["properties"][
        "provider_command_fingerprint"
    ]["$ref"] == "#/schemas/ProviderCommandFingerprint"
    assert schema_result["schemas"]["ProviderCertificationReceiptMaterial"]["properties"][
        "reference_contract_coverage"
    ]["$ref"] == "#/schemas/ProviderReferenceContractCoverage"
    assert schema_result["schemas"]["ProviderRequestReceipt"]["properties"]["protocol"]["$ref"] == (
        "#/schemas/ProviderRequestProtocolIdentity"
    )
    assert schema_result["schemas"]["ProviderRequestReceipt"]["properties"]["schema_version"]["const"] == (
        "provider-request-receipt-v1"
    )
    assert "hash" in schema_result["schemas"]["ProviderRequestProtocolIdentity"]["required"]
    assert schema_result["schemas"]["BenchmarkReceiptMaterial"]["properties"]["cases"]["items"]["$ref"] == (
        "#/schemas/BenchmarkReceiptCaseSummary"
    )
    assert "coverage_sha256" in schema_result["schemas"]["ProviderReferenceContractCoverage"]["required"]
    assert "reference_charts" in schema_result["schemas"]["BenchmarkReceiptMaterial"]["required"]
    assert "command_sha256" in schema_result["schemas"]["ProviderCommandFingerprint"]["required"]
    assert "artifact_sha256" in schema_result["schemas"]["ProviderCommandFingerprint"]["required"]
    assert {"valid", "missing", "fields"}.issubset(schema_result["schemas"]["ProviderProvenanceAudit"]["required"])
    assert schema_result["schemas"]["StatusResponse"]["properties"]["memory_profile"]["$ref"] == "#/schemas/MemoryProfile"
    assert schema_result["schemas"]["StatusResponse"]["properties"]["archive_integrity"]["$ref"] == "#/schemas/ArchiveIntegrityReport"
    assert schema_result["schemas"]["VersionHistoryResponse"]["properties"]["versions"]["items"]["$ref"] == "#/schemas/VersionHistoryRow"
    assert schema_result["schemas"]["VersionHistoryResponse"]["properties"]["archive_integrity"]["$ref"] == "#/schemas/ArchiveIntegrityReport"
    assert schema_result["schemas"]["VersionHistoryResponse"]["properties"]["history_integrity"]["$ref"] == "#/schemas/VersionHistoryIntegrity"
    assert "fingerprint_mismatch_versions" in schema_result["schemas"]["VersionHistoryIntegrity"]["required"]
    assert schema_result["schemas"]["StatusResponse"]["properties"]["genome_lineage"]["anyOf"][0]["$ref"] == "#/schemas/GenomeLineage"
    assert schema_result["schemas"]["StatusResponse"]["properties"]["lineage_integrity"]["$ref"] == "#/schemas/LineageIntegrityReport"
    lineage_schema = schema_result["schemas"]["GenomeLineage"]
    assert "genome_fingerprint" in lineage_schema["required"]
    assert lineage_schema["properties"]["selection_decision"]["anyOf"][0]["$ref"] == "#/schemas/EvolutionSelectionDecision"
    assert lineage_schema["properties"]["reproducibility_manifest"]["anyOf"][0]["$ref"] == "#/schemas/ReproducibilityManifest"
    rollback_schema = schema_result["schemas"]["RollbackResponse"]
    assert rollback_schema["properties"]["genome_lineage"]["$ref"] == "#/schemas/GenomeLineage"
    assert rollback_schema["properties"]["archive_integrity"]["$ref"] == "#/schemas/ArchiveIntegrityReport"
    assert "rollback_reason" in rollback_schema["required"]
    assert schema_result["schemas"]["RollbackRequest"]["required"] == ["to_version"]
    assert "reason" in schema_result["schemas"]["RollbackRequest"]["properties"]
    assert "genome_fingerprint_matches" in schema_result["schemas"]["LineageIntegrityReport"]["required"]
    latest_schema = schema_result["schemas"]["LatestEvolutionStatus"]
    assert "archive_hash" in latest_schema["required"]
    assert latest_schema["properties"]["selection_decision"]["anyOf"][0]["$ref"] == "#/schemas/EvolutionSelectionDecision"
    assert latest_schema["properties"]["reproducibility_manifest"]["anyOf"][0]["$ref"] == "#/schemas/ReproducibilityManifest"
    assert schema_result["schemas"]["EvolveRequest"]["properties"]["input"]["$ref"] == "#/schemas/AnalyzeRequest"
    assert schema_result["schemas"]["EvolveResponse"]["properties"]["selection_decision"]["$ref"] == "#/schemas/EvolutionSelectionDecision"
    assert schema_result["schemas"]["EvolveResponse"]["properties"]["memory_profile"]["$ref"] == "#/schemas/MemoryProfile"
    assert provider_plan_schema["properties"]["targets"]["items"]["$ref"] == "#/schemas/ProviderIntegrationTarget"
    assert "production_credential_passed" in provider_target_schema["required"]
    assert "protocols" in provider_target_schema["required"]
    assert audit_schema["properties"]["capabilities"]["$ref"] == "#/schemas/CapabilityFlagMap"
    assert audit_schema["properties"]["request_scoped_provider_contract"]["$ref"] == (
        "#/schemas/RequestScopedProviderContractSummary"
    )
    assert audit_schema["properties"]["provider_protocol_governance"]["$ref"] == (
        "#/schemas/ProviderProtocolGovernanceSummary"
    )
    assert (
        schema_result["schemas"]["ProviderProtocolGovernanceSummary"]["properties"]["runtime_identity_handshake"][
            "$ref"
        ]
        == "#/schemas/ProviderProtocolIdentityHandshakeSummary"
    )
    assert "requires_provenance_fields" in schema_result["schemas"]["RequestScopedProviderContractSummary"]["required"]
    assert "protocol_document_sha256" in schema_result["schemas"]["ProviderProtocolGovernanceSummary"]["required"]
    assert "ready" in schema_result["schemas"]["ProviderProtocolIdentityHandshakeSummary"]["required"]
    assert audit_schema["properties"]["provider_checks"]["$ref"] == "#/schemas/ProviderChecksResponse"
    assert "provider_protocol_governance" in audit_schema["required"]
    assert "audit_receipt" in audit_schema["required"]
    assert audit_schema["properties"]["audit_receipt"]["$ref"] == "#/schemas/CapabilityAuditReceipt"
    assert "expected_audit_receipt_sha256" in audit_schema["required"]
    assert "audit_receipt_matches_expected" in audit_schema["required"]
    assert "audit_receipt_mismatch_reason" in audit_schema["required"]
    assert schema_result["schemas"]["CapabilityAuditReceipt"]["properties"]["schema_version"]["const"] == (
        "capability-audit-receipt-v1"
    )
    assert schema_result["schemas"]["CapabilityAuditReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/CapabilityAuditReceiptMaterial"
    )
    assert schema_result["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["capabilities"]["$ref"] == (
        "#/schemas/CapabilityFlagMap"
    )
    assert schema_result["schemas"]["CapabilityAuditReceiptMaterial"]["properties"][
        "request_scoped_provider_contract"
    ]["$ref"] == "#/schemas/RequestScopedProviderContractSummary"
    assert schema_result["schemas"]["CapabilityAuditReceiptMaterial"]["properties"][
        "provider_protocol_governance"
    ]["$ref"] == "#/schemas/ProviderProtocolGovernanceSummary"
    assert audit_schema["properties"]["plan_compliance"]["$ref"] == "#/schemas/PlanCompliance"
    assert audit_schema["properties"]["state_of_art"]["$ref"] == "#/schemas/StateOfArtAssessment"
    assert audit_schema["properties"]["evidence_materialization"]["$ref"] == "#/schemas/EvidenceMaterialization"
    assert "evidence_materialization" in audit_schema["required"]
    assert audit_schema["properties"]["feedback_memory_safety"]["$ref"] == "#/schemas/FeedbackMemorySafetyAudit"
    assert audit_schema["properties"]["outcome_dataset"]["$ref"] == "#/schemas/OutcomeDatasetAudit"
    assert "unsafe_feedback_count" in schema_result["schemas"]["MemoryProfile"]["required"]
    assert "source_receipt" in schema_result["schemas"]["PlanCompliance"]["required"]
    assert "classical_source_refresh" in schema_result["schemas"]["CapabilityAuditResponse"]["required"]
    assert (
        schema_result["schemas"]["CapabilityAuditResponse"]["properties"]["classical_source_refresh"]["$ref"]
        == "#/schemas/ClassicalSourceListAudit"
    )
    assert "known_gap_resolution_plan_coverage" in schema_result["schemas"]["CapabilityAuditResponse"]["required"]
    assert (
        schema_result["schemas"]["CapabilityAuditResponse"]["properties"]["known_gap_resolution_plan_coverage"]["$ref"]
        == "#/schemas/KnownGapResolutionPlanCoverage"
    )
    assert "classical_source_refresh" in schema_result["schemas"]["ProductionReadinessResponse"]["required"]
    assert "known_gap_resolution_plan" in schema_result["schemas"]["ProductionReadinessResponse"]["required"]
    assert "id" in schema_result["schemas"]["KnownGapResolutionPlanItem"]["required"]
    assert "gap_id" in schema_result["schemas"]["KnownGapResolutionPlanItem"]["required"]
    assert (
        schema_result["schemas"]["ProductionReadinessResponse"]["properties"]["classical_source_refresh"]["$ref"]
        == "#/schemas/ClassicalSourceListAudit"
    )
    assert "classical_source_list_path" in schema_result["schemas"]["ProductionReadinessResponse"]["required"]
    assert "classical_source_refresh" in schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert (
        "known_gap_resolution_plan_coverage"
        in schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"][
            "known_gap_resolution_plan_coverage"
        ]["$ref"]
        == "#/schemas/KnownGapResolutionPlanCoverage"
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["classical_source_refresh"]["$ref"]
        == "#/schemas/ClassicalSourceRefreshReceiptSummary"
    )
    assert (
        schema_result["schemas"]["ClassicalSourcesResponse"]["properties"]["audit"]["$ref"]
        == "#/schemas/ClassicalSourceListAudit"
    )
    assert (
        schema_result["schemas"]["ClassicalSourceListAudit"]["properties"]["source_list_receipt"]["$ref"]
        == "#/schemas/ClassicalSourceListReceipt"
    )
    assert "ClassicalSourceAuditEntry" in schema_result["schemas"]
    assert "source_audits" in schema_result["schemas"]["ClassicalSourceListAudit"]["required"]
    assert "source_audits" in schema_result["schemas"]["ClassicalSourceListReceiptMaterial"]["required"]
    assert schema_result["schemas"]["ClassicalSourceListAudit"]["properties"]["source_audits"]["items"]["$ref"] == (
        "#/schemas/ClassicalSourceAuditEntry"
    )
    assert "refreshable" in schema_result["schemas"]["ClassicalSourceAuditEntry"]["required"]
    assert "source_list_receipt_sha256" in schema_result["schemas"]["ClassicalSourceRefreshReceiptSummary"]["required"]
    assert "classical_source_list_path" in schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    plan_source_receipt_schema = schema_result["schemas"]["PlanCompliance"]["properties"]["source_receipt"]
    assert "sha256" in plan_source_receipt_schema["required"]
    assert "section_heading_count" in plan_source_receipt_schema["required"]
    assert "request_scoped_provenance_required" in schema_result["schemas"]["StateOfArtAssessment"]["required"]
    assert "production_input_geocoding" in schema_result["schemas"]["StateOfArtAssessment"]["required"]
    assert "birthplace_geocoding_production_gate" in schema_result["schemas"]["StateOfArtAssessment"]["required"]
    assert "deliberation_receipt_production_gate" in schema_result["schemas"]["StateOfArtAssessment"]["required"]
    outcome_schema = schema_result["schemas"]["OutcomeDatasetManifest"]
    assert outcome_schema["properties"]["labels"]["items"]["$ref"] == "#/schemas/OutcomeLabelDefinition"
    assert outcome_schema["properties"]["records"]["items"]["$ref"] == "#/schemas/OutcomeDatasetRecord"
    assert "external_review" in outcome_schema["required"]
    assert "data_split" in outcome_schema["required"]
    assert "label_collection" in outcome_schema["required"]
    assert outcome_schema["properties"]["data_split"]["properties"]["holdout_case_ids"]["minItems"] == 1
    outcome_audit_schema = schema_result["schemas"]["OutcomeDatasetAudit"]
    assert outcome_audit_schema["properties"]["quality_task_projection"]["$ref"] == "#/schemas/OutcomeQualityTaskProjection"
    assert outcome_audit_schema["properties"]["external_review"]["$ref"] == "#/schemas/OutcomeExternalReview"
    assert outcome_audit_schema["properties"]["data_split"]["$ref"] == "#/schemas/OutcomeDataSplit"
    assert outcome_audit_schema["properties"]["data_split_record_coverage"]["$ref"] == (
        "#/schemas/OutcomeDataSplitRecordCoverage"
    )
    assert outcome_audit_schema["properties"]["label_collection"]["$ref"] == "#/schemas/OutcomeLabelCollection"
    assert outcome_audit_schema["properties"]["label_inventory"]["$ref"] == "#/schemas/OutcomeLabelInventory"
    assert outcome_audit_schema["properties"]["optimization_policy"]["$ref"] == "#/schemas/OutcomeOptimizationPolicy"
    assert outcome_audit_schema["properties"]["governance_gates"]["$ref"] == "#/schemas/OutcomeGovernanceGates"
    assert "external_review" in outcome_audit_schema["required"]
    assert "data_split" in outcome_audit_schema["required"]
    assert "data_split_record_coverage" in outcome_audit_schema["required"]
    assert "label_collection" in outcome_audit_schema["required"]
    assert "optimization_policy" in outcome_audit_schema["required"]
    assert "observed_label_ids" in schema_result["schemas"]["OutcomeLabelInventory"]["required"]
    assert "blocked_reason" in schema_result["schemas"]["OutcomeOptimizationPolicy"]["required"]
    assert "blocking_failures" in schema_result["schemas"]["OutcomeGovernanceGates"]["required"]
    outcome_response_schema = schema_result["schemas"]["OutcomeDatasetAuditResponse"]
    assert outcome_response_schema["properties"]["audit"]["$ref"] == "#/schemas/OutcomeDatasetAudit"
    assert outcome_response_schema["properties"]["evolution_gate"]["$ref"] == "#/schemas/OutcomeDatasetEvolutionGate"
    readiness_schema = schema_result["schemas"]["ProductionReadinessResponse"]
    assert readiness_schema["properties"]["gates"]["items"]["$ref"] == "#/schemas/ProductionReadinessGate"
    assert readiness_schema["properties"]["resolution_plan"]["$ref"] == "#/schemas/ProductionResolutionPlan"
    assert readiness_schema["properties"]["evidence_materialization"]["$ref"] == "#/schemas/EvidenceMaterialization"
    assert readiness_schema["properties"]["current_benchmark"]["$ref"] == "#/schemas/BenchmarkResult"
    assert readiness_schema["properties"]["readiness_receipt"]["$ref"] == "#/schemas/ProductionReadinessReceipt"
    assert readiness_schema["properties"]["provider_readiness"]["$ref"] == "#/schemas/ProviderProfileReadiness"
    assert readiness_schema["properties"]["known_gap_resolution_plan"]["items"]["$ref"] == (
        "#/schemas/KnownGapResolutionPlanItem"
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceipt"]["properties"]["material"]["$ref"]
        == "#/schemas/ProductionReadinessReceiptMaterial"
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["current_benchmark"]["$ref"]
        == "#/schemas/ProductionReadinessBenchmarkSummary"
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["capability_audit_receipt"]["$ref"]
        == "#/schemas/ProductionReadinessCapabilityAuditReceiptSummary"
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"][
            "provider_certification_ledger"
        ]["$ref"]
        == "#/schemas/ProductionReadinessProviderLedgerSummary"
    )
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"][
            "provider_certification_drift"
        ]["$ref"]
        == "#/schemas/ProductionReadinessProviderDriftSummary"
    )
    assert "request_provenance_audit" in schema_result["schemas"]["ProductionReadinessBenchmarkSummary"]["required"]
    assert schema_result["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["birth_profile_audit"]["$ref"] == (
        "#/schemas/ProductionReadinessBenchmarkBirthProfileAudit"
    )
    assert schema_result["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["request_provenance_audit"][
        "$ref"
    ] == "#/schemas/ProductionReadinessBenchmarkRequestProvenanceAudit"
    assert schema_result["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["provider_action_plan_audit"][
        "$ref"
    ] == "#/schemas/ProductionReadinessBenchmarkProviderActionPlanAudit"
    assert schema_result["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["topic_confidence_audit"][
        "$ref"
    ] == "#/schemas/ProductionReadinessBenchmarkTopicConfidenceAudit"
    assert schema_result["schemas"]["ProductionReadinessBenchmarkBirthProfileAudit"]["properties"]["fingerprints"][
        "items"
    ]["$ref"] == "#/schemas/ProductionReadinessBenchmarkCaseSha256"
    assert schema_result["schemas"]["ProductionReadinessBenchmarkRequestProvenanceAudit"]["properties"][
        "annual_timeline_receipts"
    ]["items"]["$ref"] == "#/schemas/ProductionReadinessBenchmarkReceiptBindingAudit"
    assert "external_payload_birth_matches_ok" in schema_result["schemas"][
        "ProductionReadinessBenchmarkRequestProvenanceAudit"
    ]["required"]
    assert "coverage_complete" in schema_result["schemas"][
        "ProductionReadinessBenchmarkProviderActionPlanAudit"
    ]["required"]
    assert "level_counts" in schema_result["schemas"]["ProductionReadinessBenchmarkTopicConfidenceAudit"]["required"]
    assert "sha256" in schema_result["schemas"]["ProductionReadinessCapabilityAuditReceiptSummary"]["required"]
    assert (
        "command_fingerprint_status"
        in schema_result["schemas"]["ProductionReadinessProviderLedgerSummary"]["required"]
    )
    assert "checked_domains" in schema_result["schemas"]["ProductionReadinessProviderDriftSummary"]["required"]
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["evidence_materialization"][
            "$ref"
        ]
        == "#/schemas/ProductionReadinessEvidenceMaterializationSummary"
    )
    assert "failed_count" in schema_result["schemas"]["ProductionReadinessEvidenceMaterializationSummary"]["required"]
    assert (
        schema_result["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["outcome_dataset"]["$ref"]
        == "#/schemas/OutcomeDatasetReceiptMaterial"
    )
    assert "governance_gate_ids" in schema_result["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert "data_split_record_coverage" in schema_result["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert "statistical_plan" in schema_result["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert schema_result["schemas"]["OutcomeDatasetReceiptMaterial"]["properties"]["data_split_record_coverage"][
        "$ref"
    ] == "#/schemas/OutcomeDataSplitRecordCoverage"
    assert readiness_schema["properties"]["capability_audit_receipt"]["$ref"] == "#/schemas/CapabilityAuditReceipt"
    assert "evidence_materialization" in readiness_schema["required"]
    assert "current_benchmark" in readiness_schema["required"]
    assert "capability_audit_receipt" in readiness_schema["required"]
    assert "expected_audit_receipt_sha256" in readiness_schema["required"]
    assert "audit_receipt_matches_expected" in readiness_schema["required"]
    assert "audit_receipt_mismatch_reason" in readiness_schema["required"]
    assert "readiness_receipt" in readiness_schema["required"]
    assert "expected_readiness_receipt_sha256" in readiness_schema["required"]
    assert "readiness_receipt_matches_expected" in readiness_schema["required"]
    assert "readiness_receipt_mismatch_reason" in readiness_schema["required"]
    assert readiness_schema["properties"]["provider_integration_plan"]["$ref"] == "#/schemas/ProviderIntegrationPlan"
    assert (
        readiness_schema["properties"]["provider_certification_ledger"]["$ref"]
        == "#/schemas/ProviderCertificationLedgerStatus"
    )
    assert (
        readiness_schema["properties"]["release_manifest_ledger"]["$ref"]
        == "#/schemas/ReleaseManifestLedgerStatus"
    )
    assert "release_manifest_ledger" in readiness_schema["required"]
    assert (
        readiness_schema["properties"]["provider_certification_drift"]["$ref"]
        == "#/schemas/ProviderCertificationDriftStatus"
    )
    assert (
        schema_result["schemas"]["ProviderCertificationDriftStatus"]["properties"]["checks"]["items"]["$ref"]
        == "#/schemas/ProviderCertificationDriftCheck"
    )
    assert "checked_domains" in schema_result["schemas"]["ProviderCertificationDriftStatus"]["required"]
    drift_check_schema = schema_result["schemas"]["ProviderCertificationDriftCheck"]
    assert "expected_provider_request_receipt_sha256" in drift_check_schema["required"]
    assert "current_provider_request_receipt_sha256" in drift_check_schema["required"]
    assert "expected_provider_command_sha256" in drift_check_schema["required"]
    assert "current_provider_command_sha256" in drift_check_schema["required"]
    assert "expected_provider_artifact_sha256" in drift_check_schema["required"]
    assert "current_provider_artifact_sha256" in drift_check_schema["required"]
    assert "provider_request_receipt_matches_expected" in drift_check_schema["required"]
    assert "provider_request_receipt_valid" in drift_check_schema["required"]
    assert "provider_command_fingerprint_matches_expected" in drift_check_schema["required"]
    assert "domain" in schema_result["schemas"]["ProviderCertificationDriftResponse"]["required"]
    assert "domain" in schema_result["schemas"]["ProviderProtocolsResponse"]["required"]
    assert "integrity_status" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "protocol_status" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "request_receipt_status" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "reference_contract_status" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "command_fingerprint_status" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "coverage_status" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "latest_record_index" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "protocol_failures" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "request_receipt_failures" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "reference_contract_failures" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "command_fingerprint_failures" in schema_result["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    ledger_domain_schema = schema_result["schemas"]["ProviderCertificationLedgerDomainStatus"]
    assert "latest_provider_request_receipt_sha256" in ledger_domain_schema["required"]
    assert "latest_provider_command_sha256" in ledger_domain_schema["required"]
    assert "latest_provider_artifact_sha256" in ledger_domain_schema["required"]
    assert "provider_command_fingerprint_present" in ledger_domain_schema["required"]
    assert "request_receipt_valid" in ledger_domain_schema["required"]
    assert "latest_reference_contract_coverage_sha256" in ledger_domain_schema["required"]
    assert "latest_reference_contract_method_surface_sha256" in ledger_domain_schema["required"]
    assert "current_method_surface_sha256" in ledger_domain_schema["required"]
    assert "reference_contract_method_surface_current" in ledger_domain_schema["required"]
    assert "reference_contract_covered" in ledger_domain_schema["required"]
    assert readiness_schema["properties"]["outcome_dataset"]["$ref"] == "#/schemas/OutcomeDatasetAuditResponse"
    assert readiness_schema["properties"]["history_integrity"]["$ref"] == "#/schemas/VersionHistoryIntegrity"
    assert "record_fingerprints" in outcome_audit_schema["required"]
    assert "data_split_record_coverage" in outcome_audit_schema["required"]
    assert "projected_task_fingerprints" in schema_result["schemas"]["OutcomeQualityTaskProjection"]["required"]
    outcome_plan_schema = schema_result["schemas"]["OutcomeStatisticalPlan"]
    assert outcome_plan_schema["properties"]["minimum_sample_size"]["minimum"] == 30
    assert "pre_registered" in outcome_plan_schema["required"]
    assert "registration_id" in outcome_plan_schema["required"]
    assert outcome_plan_schema["properties"]["plan_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    outcome_record_schema = schema_result["schemas"]["OutcomeDatasetRecord"]
    assert outcome_record_schema["properties"]["birth"]["not"] == {"required": ["name"]}
    assert set(provider_summary_schema["properties"]["domains"]["required"]) == {
        "bazi",
        "ziwei",
        "qimen",
        "astrology",
        "xuanze",
    }
    analyze_response = schema_result["schemas"]["AnalyzeResponse"]
    result_schema = analyze_response["properties"]["result"]
    assert "specialists" in result_schema["required"]
    assert set(result_schema["properties"]["specialists"]["required"]) == {"bazi", "ziwei", "qimen", "astrology"}
    specialist_schema = schema_result["schemas"]["SpecialistReport"]
    assert {"layers", "sources", "macro", "micro", "yearly", "monthly", "uncertainty"}.issubset(
        specialist_schema["required"]
    )
    assert specialist_schema["properties"]["sources"]["items"]["$ref"] == "#/schemas/SpecialistSource"
    assert "source_id" in schema_result["schemas"]["SpecialistSource"]["required"]
    layer_schema = schema_result["schemas"]["SpecialistLayer"]
    assert {"source_ids", "evidence_required", "boundary_type"}.issubset(layer_schema["required"])
    final_report_schema = analyze_response["properties"]["result"]["properties"]["final_report"]
    assert "birth_profile" in final_report_schema["required"]
    assert "request_provenance" in final_report_schema["required"]
    assert "provider_summary" in final_report_schema["required"]
    assert "topic_synthesis" in final_report_schema["required"]
    assert "votes" in final_report_schema["required"]
    assert "deliberation_receipt" in final_report_schema["required"]
    assert final_report_schema["properties"]["birth_profile"]["$ref"] == "#/schemas/BirthProfile"
    assert final_report_schema["properties"]["topic_synthesis"]["properties"]["finance"]["$ref"] == (
        "#/schemas/TopicSynthesisItem"
    )
    bazi_profile_schema = schema_result["schemas"]["BaziProfile"]
    assert "image_symbol_analysis" in bazi_profile_schema["required"]
    assert "new_school_simplified_analysis" in bazi_profile_schema["required"]
    assert "data_validation_analysis" in bazi_profile_schema["required"]
    assert bazi_profile_schema["properties"]["image_symbol_analysis"]["type"] == "object"
    assert bazi_profile_schema["properties"]["new_school_simplified_analysis"]["type"] == "object"
    assert bazi_profile_schema["properties"]["data_validation_analysis"]["type"] == "object"
    assert bazi_profile_schema["properties"]["method_matrix"]["items"]["$ref"] == "#/schemas/BaziMethodMatrixItem"
    assert bazi_profile_schema["properties"]["major_luck"]["items"]["$ref"] == "#/schemas/BaziMajorLuckPeriod"
    assert schema_result["schemas"]["BaziMajorLuckPeriod"]["properties"]["annual_preview"]["items"]["$ref"] == (
        "#/schemas/BaziMajorLuckAnnualPreview"
    )
    topic_item_schema = schema_result["schemas"]["TopicSynthesisItem"]
    topic_confidence_schema = schema_result["schemas"]["TopicSynthesisConfidence"]
    assert "synthesis_confidence" in topic_item_schema["required"]
    assert topic_item_schema["properties"]["synthesis_confidence"]["$ref"] == "#/schemas/TopicSynthesisConfidence"
    assert topic_item_schema["properties"]["cross_agent_evidence"]["items"]["$ref"] == (
        "#/schemas/TopicSynthesisCrossAgentEvidence"
    )
    assert "downgrade_reasons" in topic_confidence_schema["required"]
    assert "provider_fallbacks_present" not in topic_confidence_schema["properties"]["level"]["enum"]
    birth_profile_schema = schema_result["schemas"]["BirthProfile"]
    assert "birthplace_normalized" in birth_profile_schema["required"]
    assert "birthplace_region" in birth_profile_schema["required"]
    assert "latitude" in birth_profile_schema["required"]
    assert "longitude" in birth_profile_schema["required"]
    assert "timezone_offset" in birth_profile_schema["required"]
    assert "geocoding_provider" in birth_profile_schema["required"]
    assert "geocoding_quality" in birth_profile_schema["required"]
    assert final_report_schema["properties"]["request_provenance"]["$ref"] == "#/schemas/RequestProvenance"
    request_context_props = schema_result["schemas"]["RequestProvenance"]["properties"]["specialist_contexts"][
        "additionalProperties"
    ]["properties"]
    assert "provider_request_receipt_sha256" in request_context_props
    assert "external_payload_receipt_sha256" in request_context_props
    assert final_report_schema["properties"]["votes"]["$ref"] == "#/schemas/VoteRecord"
    assert schema_result["schemas"]["VoteRecord"]["properties"]["_claims"]["items"]["$ref"] == "#/schemas/VoteClaim"
    assert schema_result["schemas"]["VoteClaim"]["properties"]["challenges"]["items"]["$ref"] == "#/schemas/VoteChallenge"
    assert schema_result["schemas"]["VoteRecord"]["properties"]["_audit"]["$ref"] == "#/schemas/VoteAudit"
    assert "minority_positions_preserved" in schema_result["schemas"]["VoteAudit"]["required"]
    assert final_report_schema["properties"]["deliberation_receipt"]["$ref"] == "#/schemas/DeliberationReceipt"
    assert "votes_sha256" in schema_result["schemas"]["DeliberationReceipt"]["required"]
    assert "source_review_sha256" in schema_result["schemas"]["DeliberationReceipt"]["required"]
    assert "annual_timeline" in final_report_schema["required"]
    assert "annual_timeline_receipt" in final_report_schema["required"]
    assert "monthly_luck_receipt" in final_report_schema["required"]
    assert "auspicious_calendar_receipt" in final_report_schema["required"]
    assert final_report_schema["properties"]["annual_luck"]["$ref"] == "#/schemas/AnnualLuck"
    assert final_report_schema["properties"]["provider_summary"]["$ref"] == "#/schemas/ProviderSummary"
    assert final_report_schema["properties"]["annual_timeline"]["items"]["$ref"] == "#/schemas/AnnualTimelineRow"
    assert final_report_schema["properties"]["annual_timeline_receipt"]["$ref"] == "#/schemas/AnnualTimelineReceipt"
    assert final_report_schema["properties"]["monthly_luck"]["$ref"] == "#/schemas/MonthlyLuck"
    assert schema_result["schemas"]["MonthlyLuck"]["properties"]["rows"]["items"]["$ref"] == "#/schemas/MonthlyLuckRow"
    assert schema_result["schemas"]["MonthlyLuckRow"]["properties"]["bazi_evidence"]["$ref"] == (
        "#/schemas/MonthlyLuckBaziEvidence"
    )
    assert schema_result["schemas"]["MonthlyLuckRow"]["properties"]["topics"]["properties"]["finance"]["$ref"] == (
        "#/schemas/MonthlyLuckTopic"
    )
    assert final_report_schema["properties"]["monthly_luck_receipt"]["$ref"] == "#/schemas/MonthlyLuckReceipt"
    assert final_report_schema["properties"]["auspicious_calendar_receipt"]["$ref"] == (
        "#/schemas/AuspiciousCalendarReceipt"
    )
    assert schema_result["schemas"]["AnnualTimelineReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/AnnualTimelineReceiptRowFingerprint"
    )
    assert schema_result["schemas"]["AnnualTimelineReceipt"]["properties"]["annual_luck_range"]["$ref"] == (
        "#/schemas/AnnualLuckRangeSummary"
    )
    assert "start_year" in schema_result["schemas"]["AnnualLuckRangeSummary"]["required"]
    assert schema_result["schemas"]["MonthlyLuckReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/MonthlyLuckReceiptRowFingerprint"
    )
    assert schema_result["schemas"]["MonthlyLuckReceipt"]["properties"]["monthly_luck_range"]["$ref"] == (
        "#/schemas/MonthlyLuckRangeSummary"
    )
    assert schema_result["schemas"]["MonthlyLuckReceipt"]["properties"]["monthly_luck_basis"]["$ref"] == (
        "#/schemas/MonthlyLuckBasisSummary"
    )
    assert "months_per_year" in schema_result["schemas"]["MonthlyLuckRangeSummary"]["required"]
    assert "provider_quality" in schema_result["schemas"]["MonthlyLuckBasisSummary"]["required"]
    assert schema_result["schemas"]["AuspiciousCalendarReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/AuspiciousCalendarReceiptRowFingerprint"
    )
    assert schema_result["schemas"]["AuspiciousCalendarReceipt"]["properties"]["calendar_range"]["$ref"] == (
        "#/schemas/AuspiciousCalendarRange"
    )
    assert schema_result["schemas"]["AuspiciousCalendarReceipt"]["properties"]["calendar_basis"]["$ref"] == (
        "#/schemas/AuspiciousCalendarBasis"
    )
    annual_luck_schema = schema_result["schemas"]["AnnualLuck"]
    assert "phase_summary" in annual_luck_schema["required"]
    assert annual_luck_schema["properties"]["rows"]["items"]["$ref"] == "#/schemas/AnnualLuckRow"
    assert schema_result["schemas"]["AnnualLuckRow"]["properties"]["elements"]["$ref"] == "#/schemas/AnnualLuckRowElements"
    assert schema_result["schemas"]["AnnualLuckRow"]["properties"]["bazi_evidence"]["$ref"] == (
        "#/schemas/AnnualLuckBaziEvidence"
    )
    assert schema_result["schemas"]["AnnualLuckBaziEvidence"]["properties"]["annual_ten_gods"]["$ref"] == (
        "#/schemas/AnnualLuckTenGodPair"
    )
    assert schema_result["schemas"]["AnnualLuckBaziEvidence"]["properties"]["natal_pillar_matches"]["items"]["$ref"] == (
        "#/schemas/AnnualLuckNatalPillarMatch"
    )
    assert annual_luck_schema["properties"]["phase_summary"]["items"]["$ref"] == "#/schemas/AnnualPhaseSummary"
    phase_schema = schema_result["schemas"]["AnnualPhaseSummary"]
    assert phase_schema["properties"]["topic_highlights"]["properties"]["finance"]["$ref"] == "#/schemas/AnnualPhaseTopicHighlight"
    auspicious_day_schema = schema_result["schemas"]["AuspiciousDayRow"]
    assert auspicious_day_schema["properties"]["recommended_hours"]["items"]["$ref"] == (
        "#/schemas/AuspiciousRecommendedHour"
    )
    assert "branch" in schema_result["schemas"]["AuspiciousRecommendedHour"]["required"]
    timeline_schema = schema_result["schemas"]["AnnualTimelineRow"]
    assert timeline_schema["properties"]["topics"]["properties"]["finance"]["$ref"] == "#/schemas/AnnualTimelineTopic"
    assert "children_family" in timeline_schema["properties"]["topics"]["required"]
    assert "bazi_evidence" in timeline_schema["required"]
    benchmark_schema = schema_result["schemas"]["BenchmarkResult"]
    benchmark_response_schema = schema_result["schemas"]["BenchmarkResponse"]
    assert "reproducibility_manifest" in benchmark_schema["required"]
    assert "benchmark_receipt" in benchmark_schema["required"]
    assert benchmark_schema["properties"]["reproducibility_manifest"]["$ref"] == "#/schemas/ReproducibilityManifest"
    assert benchmark_schema["properties"]["benchmark_receipt"]["$ref"] == "#/schemas/ProviderCertificationReceipt"
    assert benchmark_schema["properties"]["cases"]["items"]["$ref"] == "#/schemas/BenchmarkCaseResult"
    assert schema_result["schemas"]["BenchmarkCaseResult"]["properties"]["report_features"]["$ref"] == (
        "#/schemas/BenchmarkCaseReportFeatures"
    )
    benchmark_features = schema_result["schemas"]["BenchmarkCaseReportFeatures"]["properties"]
    assert benchmark_features["external_payload_birth_match_statuses"]["items"]["$ref"] == (
        "#/schemas/BenchmarkExternalPayloadBirthMatchStatus"
    )
    assert "expected_benchmark_receipt_sha256" in benchmark_response_schema["required"]
    assert "benchmark_receipt_matches_expected" in benchmark_response_schema["required"]
    assert "benchmark_receipt_mismatch_reason" in benchmark_response_schema["required"]
    release_schema = schema_result["schemas"]["ReleaseManifestResponse"]
    assert release_schema["properties"]["audit_receipt"]["$ref"] == "#/schemas/CapabilityAuditReceipt"
    assert (
        schema_result["schemas"]["CapabilityAuditReceipt"]["properties"]["material"]["$ref"]
        == "#/schemas/CapabilityAuditReceiptMaterial"
    )
    assert (
        schema_result["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["provider_onboarding"]["$ref"]
        == "#/schemas/ProviderOnboardingAuditSummary"
    )
    assert "provider_onboarding" in schema_result["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert "domain_missing_evidence" in schema_result["schemas"]["ProviderOnboardingAuditSummary"]["required"]
    assert "missing_evidence_counts" in schema_result["schemas"]["ProviderOnboardingAuditSummary"]["required"]
    assert release_schema["properties"]["benchmark_receipt"]["$ref"] == "#/schemas/ProviderCertificationReceipt"
    assert release_schema["properties"]["readiness_receipt"]["$ref"] == "#/schemas/ProductionReadinessReceipt"
    assert release_schema["properties"]["release_manifest_receipt"]["$ref"] == "#/schemas/ReleaseManifestReceipt"
    assert (
        schema_result["schemas"]["ReleaseManifestReceipt"]["properties"]["material"]["$ref"]
        == "#/schemas/ReleaseManifestReceiptMaterial"
    )
    assert (
        release_schema["properties"]["release_gate_checks"]["$ref"]
        == "#/schemas/ReleaseManifestGateChecks"
    )
    assert (
        schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["release_gate_checks"]["$ref"]
        == "#/schemas/ReleaseManifestGateChecks"
    )
    assert "outcome_dataset_split_coverage_bound" in schema_result["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "provider_onboarding_receipt_current" in schema_result["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "provider_protocols_receipt_current" in schema_result["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "known_gap_handoff_bundle_bound" in schema_result["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert (
        schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["outcome_dataset"]["$ref"]
        == "#/schemas/OutcomeDatasetReceiptMaterial"
    )
    assert (
        "readiness_deliberation_receipt_coverage"
        in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    )
    assert "annual_timeline_receipt_coverage" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    annual_timeline_coverage_schema = schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "annual_timeline_receipt_coverage"
    ]
    assert "binding_complete" in annual_timeline_coverage_schema["required"]
    assert "receipt_sha256s" in annual_timeline_coverage_schema["required"]
    assert "monthly_luck_receipt_coverage" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    monthly_luck_coverage_schema = schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "monthly_luck_receipt_coverage"
    ]
    assert "binding_complete" in monthly_luck_coverage_schema["required"]
    assert "receipt_sha256s" in monthly_luck_coverage_schema["required"]
    assert (
        "auspicious_calendar_receipt_coverage"
        in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    )
    auspicious_calendar_coverage_schema = schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "auspicious_calendar_receipt_coverage"
    ]
    assert "binding_complete" in auspicious_calendar_coverage_schema["required"]
    assert "receipt_sha256s" in auspicious_calendar_coverage_schema["required"]
    assert "provider_action_plan_coverage" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "classical_source_receipt_coverage" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert (
        "known_gap_resolution_plan_coverage"
        in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    )
    assert "production_gate_registry_audit" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_onboarding_receipt_sha256" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_onboarding_receipt" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_protocols_receipt" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert (
        schema_result["schemas"]["ReleaseManifestResponse"]["properties"]["provider_onboarding_receipt"]["$ref"]
        == "#/schemas/ProviderOnboardingReceipt"
    )
    assert (
        schema_result["schemas"]["ReleaseManifestResponse"]["properties"]["provider_protocols_receipt"]["$ref"]
        == "#/schemas/ProviderProtocolsReceipt"
    )
    assert "external_payload_birth_match_coverage" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"][
        "required"
    ]
    assert "coverage_complete" in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "external_payload_birth_match_coverage"
    ]["required"]
    assert (
        schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
            "known_gap_resolution_plan_coverage"
        ]["$ref"]
        == "#/schemas/KnownGapResolutionPlanCoverage"
    )
    assert (
        schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["production_gate_registry_audit"][
            "$ref"
        ]
        == "#/schemas/ProductionGateRegistryAudit"
    )
    assert (
        schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["provider_protocols_receipt"]["$ref"]
        == "#/schemas/ProviderProtocolsReceipt"
    )
    assert (
        schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["provider_onboarding_receipt"]["$ref"]
        == "#/schemas/ProviderOnboardingReceipt"
    )
    assert "coverage_complete" in schema_result["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "planned_gap_ids" in schema_result["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "invalid_gate_ids_by_gap" in schema_result["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "valid_production_gate_ids" in schema_result["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    release_provider_ledger_schema = schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "provider_ledger"
    ]
    assert release_provider_ledger_schema["$ref"] == "#/schemas/ProductionReadinessProviderLedgerSummary"
    release_provider_ledger_schema = schema_result["schemas"]["ProductionReadinessProviderLedgerSummary"]
    assert "request_receipt_status" in release_provider_ledger_schema["required"]
    assert "reference_contract_status" in release_provider_ledger_schema["required"]
    assert "command_fingerprint_status" in release_provider_ledger_schema["required"]
    assert "reference_contract_failures" in release_provider_ledger_schema["required"]
    assert "command_fingerprint_failures" in release_provider_ledger_schema["required"]
    assert (
        "source_list_receipt_sha256"
        in schema_result["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
            "classical_source_receipt_coverage"
        ]["required"]
    )
    assert "release_gate_checks" in release_schema["required"]
    assert "expected_release_manifest_receipt_sha256" in release_schema["required"]
    assert "release_manifest_receipt_matches_expected" in release_schema["required"]
    assert "release_manifest_receipt_mismatch_reason" in release_schema["required"]
    assert "ledger_record_requested" in release_schema["required"]
    assert "ledger_recorded" in release_schema["required"]
    assert "ledger_record_hash" in release_schema["required"]
    assert schema_result["schemas"]["ReleaseManifestLedgerResponse"]["properties"]["ledger"]["$ref"] == (
        "#/schemas/ReleaseManifestLedgerStatus"
    )
    release_ledger_schema = schema_result["schemas"]["ReleaseManifestLedgerStatus"]
    assert "latest_record_index" in release_ledger_schema["required"]
    assert release_ledger_schema["properties"]["latest_record_index"]["type"] == ["integer", "null"]
    assert schema_result["schemas"]["ReleaseManifestDriftResponse"]["properties"]["drift"]["$ref"] == (
        "#/schemas/ReleaseManifestDriftStatus"
    )
    assert schema_result["schemas"]["ReleaseManifestDriftStatus"]["properties"]["status"]["enum"] == [
        "passed",
        "drift_detected",
        "not_checked",
    ]
    manifest_schema = schema_result["schemas"]["ReproducibilityManifest"]
    assert "train_task_fingerprints" in manifest_schema["required"]
    assert "strategy_fingerprints" in manifest_schema["required"]
    assert "cost_governance" in manifest_schema["required"]
    assert manifest_schema["properties"]["cost_governance"]["$ref"] == "#/schemas/EvolutionCostGovernance"
    cost_schema = schema_result["schemas"]["EvolutionCostGovernance"]
    assert "total_candidate_task_evaluations" in cost_schema["required"]
    assert "iteration_frequency_policy" in cost_schema["required"]
    assert manifest_schema["properties"]["strategy_fingerprints"]["items"]["$ref"] == (
        "#/schemas/ReproducibilityStrategyFingerprint"
    )
    strategy_schema = schema_result["schemas"]["ReproducibilityStrategyFingerprint"]
    assert strategy_schema["properties"]["prompt_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert manifest_schema["properties"]["run_type"]["enum"] == ["population_evolution", "benchmark"]
    assert "provider_summary_status" in benchmark_features
    assert "birth_profile_present" in benchmark_features
    assert "birth_profile_fingerprint" in benchmark_features
    assert "birthplace_geocoded" in benchmark_features
    assert (
        "birthplace_geocoding_quality"
        in benchmark_features
    )
    assert "request_provenance_present" in benchmark_features
    assert "request_provenance_chain_sha256" in benchmark_features
    assert (
        "deliberation_receipt_present"
        in benchmark_features
    )
    assert (
        "deliberation_receipt_sha256"
        in benchmark_features
    )
    assert (
        "deliberation_claim_count"
        in benchmark_features
    )
    assert (
        "annual_timeline_receipt_present"
        in benchmark_features
    )
    assert (
        "annual_timeline_receipt_sha256"
        in benchmark_features
    )
    assert (
        "annual_timeline_row_count"
        in benchmark_features
    )
    assert (
        "annual_timeline_receipt_bound_to_provenance"
        in benchmark_features
    )
    assert (
        "monthly_luck_receipt_present"
        in benchmark_features
    )
    assert (
        "monthly_luck_receipt_sha256"
        in benchmark_features
    )
    assert (
        "monthly_luck_row_count"
        in benchmark_features
    )
    assert (
        "monthly_luck_receipt_bound_to_provenance"
        in benchmark_features
    )
    assert (
        "auspicious_calendar_receipt_present"
        in benchmark_features
    )
    assert (
        "auspicious_calendar_receipt_sha256"
        in benchmark_features
    )
    assert (
        "auspicious_calendar_row_count"
        in benchmark_features
    )
    assert (
        "auspicious_calendar_receipt_bound_to_provenance"
        in benchmark_features
    )
    assert (
        "external_payload_receipt_domains"
        in benchmark_features
    )
    assert (
        "external_payload_receipt_count"
        in benchmark_features
    )
    assert (
        "external_payload_receipts_complete"
        in benchmark_features
    )
    assert (
        "external_payload_birth_match_statuses"
        in benchmark_features
    )
    assert (
        "external_payload_birth_mismatch_count"
        in benchmark_features
    )
    assert (
        "external_payload_birth_mismatch_domains"
        in benchmark_features
    )
    assert (
        "external_payload_birth_matches_ok"
        in benchmark_features
    )
    assert (
        "provider_action_plan_count"
        in benchmark_features
    )
    assert (
        "provider_action_plan_domains"
        in benchmark_features
    )
    assert (
        "provider_action_plan_covers_blockers"
        in benchmark_features
    )
    assert "GET /audit" in schema_result["endpoints"]
    assert "GET /certify-provider" in schema_result["endpoints"]
    assert "GET /provider-drift" in schema_result["endpoints"]
    assert "GET /provider-ledger" in schema_result["endpoints"]
    assert "GET /provider-protocols" in schema_result["endpoints"]
    assert "GET /history" in schema_result["endpoints"]
    assert "GET /outcome-dataset" in schema_result["endpoints"]
    assert "GET /classical-refresh" in schema_result["endpoints"]
    assert "GET /classical-sources" in schema_result["endpoints"]
    assert "GET /production-readiness" in schema_result["endpoints"]
    assert "GET /release-manifest" in schema_result["endpoints"]
    assert "GET /release-ledger" in schema_result["endpoints"]
    assert "GET /release-drift" in schema_result["endpoints"]
    assert "GET /providers" in schema_result["endpoints"]
    assert "POST /analyze" in schema_result["endpoints"]
    assert "POST /rollback" in schema_result["endpoints"]


def test_cli_analyze_preserves_utf8_birth_identity(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    birth_path = tmp_path / "birth_zh.json"
    write_json(
        birth_path,
        {
            "birth": {
                "name": "林凡",
                "birth_date": "1978-04-14",
                "birth_time": "06:50",
                "gender": "male",
                "birthplace": "福建省三明市",
            },
            "language": "zh",
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )

    assert main(["--repo", str(repo), "analyze", "--input", str(birth_path)]) == 0
    result = read_stdout_json(capsys)

    final_report = result["result"]["final_report"]
    context = result["result"]["specialists"]["bazi"]["chart"]["context"]
    assert final_report["title"] == "Mingli five-agent report for 林凡"
    assert final_report["birth_profile"]["name"] == "林凡"
    assert final_report["birth_profile"]["birthplace"] == "福建省三明市"
    assert final_report["birth_profile"]["birthplace_normalized"] == "Sanming, Fujian, China"
    assert final_report["birth_profile"]["hour"] == 6
    assert final_report["birth_profile"]["minute"] == 50
    assert result["result"]["output"].startswith("# Mingli five-agent report for 林凡")
    assert "## 出生资料核对" in result["result"]["output"]
    assert context["name"] == "林凡"
    assert context["birthplace"] == "福建省三明市"


def test_cli_subprocess_emits_utf8_json_for_chinese_identity(tmp_path: Path):
    repo = tmp_path / "repo"
    birth_path = tmp_path / "birth_zh.json"
    write_json(
        birth_path,
        {
            "birth": {
                "name": "林凡",
                "birth_date": "1978-04-14",
                "birth_time": "06:50",
                "gender": "male",
                "birthplace": "福建省三明市",
            },
            "language": "zh",
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )
    env = os.environ.copy()
    env.pop("PYTHONIOENCODING", None)
    env["PYTHONUTF8"] = "0"

    completed = subprocess.run(
        [
            sys.executable,
            "examples/mingli_5agents/cli.py",
            "--repo",
            str(repo),
            "analyze",
            "--input",
            str(birth_path),
        ],
        cwd=Path(__file__).resolve().parents[3],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    result = json.loads(completed.stdout.decode("utf-8"))

    final_report = result["result"]["final_report"]
    assert final_report["birth_profile"]["name"] == "林凡"
    assert final_report["birth_profile"]["birthplace"] == "福建省三明市"
    assert final_report["birth_profile"]["birthplace_normalized"] == "Sanming, Fujian, China"
    assert result["result"]["output"].startswith("# Mingli five-agent report for 林凡")


def test_cli_analyze_accepts_utf8_bom_json_input(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    birth_path = tmp_path / "birth_bom.json"
    birth_path.write_text(
        json.dumps(
            {
                "birth": {
                    "name": "BOM Person",
                    "birth_date": "1991-05-20",
                    "birth_time": "10:15",
                    "gender": "unspecified",
                    "birthplace": "Suzhou",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8-sig",
    )

    assert main(["--repo", str(repo), "analyze", "--input", str(birth_path)]) == 0
    result = read_stdout_json(capsys)

    assert result["passed"] is True
    assert result["result"]["final_report"]["title"] == "Mingli five-agent report for BOM Person"


def test_cli_rollback_writes_audited_lineage(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    birth_path = tmp_path / "birth.json"
    feedback_path = tmp_path / "feedback.json"
    write_json(
        birth_path,
        {
            "birth": {
                "name": "Rollback Person",
                "birth_date": "1991-05-20",
                "birth_time": "10:15",
                "gender": "unspecified",
                "birthplace": "Suzhou",
            }
        },
    )
    write_json(
        feedback_path,
        {"feedback": {"satisfaction": 0.5, "corrections": ["needs stronger source labels"]}},
    )

    assert main(["--repo", str(repo), "init"]) == 0
    read_stdout_json(capsys)
    assert main(["--repo", str(repo), "evolve", "--input", str(birth_path), "--feedback", str(feedback_path)]) == 0
    read_stdout_json(capsys)

    assert main(
        [
            "--repo",
            str(repo),
            "rollback",
            "--to-version",
            "1",
            "--reason",
            "restore stable baseline after provider regression",
        ]
    ) == 0
    rollback = read_stdout_json(capsys)

    assert rollback["status"] == "rolled_back"
    assert rollback["before_version"] == 2
    assert rollback["target_version"] == 1
    assert rollback["after_version"] == 3
    assert rollback["rollback_reason"] == "restore stable baseline after provider regression"
    assert rollback["archive_integrity"]["status"] == "pass"
    assert rollback["genome_lineage"]["event"] == "rollback"
    assert rollback["genome_lineage"]["rollback_target_version"] == 1
    assert rollback["genome_lineage"]["rollback_reason"] == "restore stable baseline after provider regression"
    assert rollback["genome_lineage"]["selection_decision"] is None

    assert main(["--repo", str(repo), "status"]) == 0
    status_result = read_stdout_json(capsys)
    assert status_result["coordinator_version"] == 3
    assert status_result["genome_lineage"]["event"] == "rollback"
    assert status_result["genome_lineage"]["rollback_reason"] == "restore stable baseline after provider regression"
    assert status_result["latest_evolution"]["event"] == "rollback"
    assert status_result["lineage_integrity"]["status"] == "pass"

    assert main(["--repo", str(repo), "history"]) == 0
    history = read_stdout_json(capsys)
    assert history["latest_version"] == 3
    assert history["history_integrity"]["status"] == "pass"
    assert [item["version"] for item in history["versions"]] == [1, 2, 3]
    assert history["versions"][-1]["lineage_event"] == "rollback"
    assert history["versions"][-1]["rollback_target_version"] == 1
    assert history["versions"][-1]["rollback_reason"] == "restore stable baseline after provider regression"
    assert history["versions"][-1]["archive_event_found"] is True
    assert history["versions"][-1]["lineage_fingerprint_matches"] is True
