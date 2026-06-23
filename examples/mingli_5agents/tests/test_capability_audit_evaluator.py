"""Tests for capability-audit evaluator gating."""

from __future__ import annotations

from examples.mingli_5agents.capability_audit import capability_audit
from examples.mingli_5agents.evaluators.capability_audit_evaluator import capability_audit_score


def test_capability_audit_score_accepts_current_audit():
    assert capability_audit_score({}) == 1.0


def test_capability_audit_binds_provider_production_guidance():
    audit = capability_audit()

    assert audit["capabilities"]["provider_production_guidance"] is True
    assert audit["capabilities"]["evolution_trigger_receipt"] is True
    assert audit["capabilities"]["release_manifest_evolution_trigger_binding"] is True
    assert audit["capabilities"]["github_comparison_receipt"] is True
    assert audit["capabilities"]["plan_compliance_receipt"] is True
    assert audit["capabilities"]["release_manifest_github_comparison_binding"] is True
    assert audit["capabilities"]["release_manifest_plan_compliance_binding"] is True
    assert audit["capabilities"]["release_manifest_readiness_gate_binding"] is True
    assert audit["capabilities"]["blocked_capability_coverage_audit"] is True
    assert audit["capabilities"]["blocked_capability_coverage_production_gate"] is True
    assert audit["capabilities"]["known_gap_verification_command_coverage"] is True
    assert audit["capabilities"]["known_gap_command_coverage_release_binding"] is True
    assert audit["capabilities"]["known_gap_handoff_bundle"] is True
    assert audit["capabilities"]["known_gap_handoff_bundle_production_gate"] is True
    assert audit["capabilities"]["known_gap_handoff_export_cli_api"] is True
    assert audit["capabilities"]["known_gap_handoff_export_verification"] is True
    assert audit["capabilities"]["known_gap_handoff_implementation_checklist"] is True
    assert audit["capabilities"]["classical_source_governance_metadata"] is True
    assert audit["capabilities"]["outcome_dataset_record_label_provenance_gate"] is True
    assert audit["capabilities"]["outcome_dataset_statistical_plan_preregistration_gate"] is True
    assert audit["capabilities"]["annual_timeline_topic_evidence_binding"] is True
    assert audit["capabilities"]["bazi_core_profile_schema_contract"] is True
    assert audit["capabilities"]["monthly_luck_topic_evidence_binding"] is True
    assert audit["capabilities"]["monthly_luck_public_schema_contract"] is True
    assert audit["capabilities"]["astrology_profile_public_schema_contract"] is True
    assert audit["capabilities"]["astrology_ephemeris_audit_contract"] is True
    assert audit["capabilities"]["xuanze_rule_table_audit_contract"] is True
    assert audit["capabilities"]["ziwei_qimen_public_schema_contract"] is True
    assert audit["capabilities"]["ziwei_qimen_calculation_basis_audit_contract"] is True
    assert audit["capabilities"]["rendered_reports_public_schema_contract"] is True
    assert audit["capabilities"]["final_report_runtime_metadata_schema_contract"] is True
    assert audit["capabilities"]["source_review_public_schema_contract"] is True
    assert audit["capabilities"]["final_report_metadata_schema_contract"] is True
    assert audit["capabilities"]["analyze_response_runtime_schema_validation"] is True
    assert audit["capabilities"]["provider_raw_contract_receipt"] is True
    assert audit["capabilities"]["topic_synthesis_timing_schema_contract"] is True
    implemented_ids = {item["id"] for item in audit["implemented_requirements"]}
    assert "provider_production_guidance" in implemented_ids
    assert "evolution_trigger_receipt" in implemented_ids
    assert "release_manifest_evolution_trigger_binding" in implemented_ids
    assert "github_comparison_receipt" in implemented_ids
    assert "plan_compliance_receipt" in implemented_ids
    assert "release_manifest_github_comparison_binding" in implemented_ids
    assert "release_manifest_plan_compliance_binding" in implemented_ids
    assert "release_manifest_readiness_gate_binding" in implemented_ids
    assert "blocked_capability_coverage_audit" in implemented_ids
    assert "blocked_capability_coverage_production_gate" in implemented_ids
    assert "known_gap_verification_command_coverage" in implemented_ids
    assert "known_gap_command_coverage_release_binding" in implemented_ids
    assert "known_gap_handoff_bundle" in implemented_ids
    assert "known_gap_handoff_bundle_production_gate" in implemented_ids
    assert "known_gap_handoff_export_cli_api" in implemented_ids
    assert "known_gap_handoff_export_verification" in implemented_ids
    assert "known_gap_handoff_implementation_checklist" in implemented_ids
    assert "classical_source_refresh_pipeline" in implemented_ids
    assert "empirical_validation_harness" in implemented_ids
    assert "annual_timeline_topic_evidence_binding" in implemented_ids
    assert "bazi_core_profile_schema_contract" in implemented_ids
    assert "monthly_luck_topic_evidence_binding" in implemented_ids
    assert "monthly_luck_public_schema_contract" in implemented_ids
    assert "astrology_profile_public_schema_contract" in implemented_ids
    assert "optional_astrology_json_cli_provider" in implemented_ids
    assert "optional_xuanze_json_cli_provider" in implemented_ids
    assert "ziwei_qimen_public_schema_contract" in implemented_ids
    assert "ziwei_qimen_calculation_basis_audit_contract" in implemented_ids
    assert "rendered_reports_public_schema_contract" in implemented_ids
    assert "final_report_runtime_metadata_schema_contract" in implemented_ids
    assert "source_review_public_schema_contract" in implemented_ids
    assert "final_report_metadata_schema_contract" in implemented_ids
    assert "analyze_response_runtime_schema_validation" in implemented_ids
    assert "topic_synthesis_timing_schema_contract" in implemented_ids
    provider_governance = next(item for item in audit["implemented_requirements"] if item["id"] == "provider_protocol_governance")
    assert "raw provider contract receipts" in provider_governance["requirement"]
    assert "provider_checks._raw_provider_contract_receipt" in provider_governance["evidence"]
    assert "api_core.schema_document.ProviderRawContractReceipt" in provider_governance["evidence"]
    astrology_provider = next(item for item in audit["implemented_requirements"] if item["id"] == "optional_astrology_json_cli_provider")
    assert "ephemeris source" in astrology_provider["requirement"]
    assert "provider_contracts.astrology_ephemeris_audit_contract" in astrology_provider["evidence"]
    assert "provider_protocols.astrology_ephemeris_stdout_schema" in astrology_provider["evidence"]
    xuanze_provider = next(item for item in audit["implemented_requirements"] if item["id"] == "optional_xuanze_json_cli_provider")
    assert "rule-table source" in xuanze_provider["requirement"]
    assert "provider_contracts.xuanze_rule_table_audit_contract" in xuanze_provider["evidence"]
    assert "provider_protocols.xuanze_rule_table_stdout_schema" in xuanze_provider["evidence"]
    calculation_basis = next(
        item for item in audit["implemented_requirements"] if item["id"] == "ziwei_qimen_calculation_basis_audit_contract"
    )
    assert "calculation-basis metadata" in calculation_basis["requirement"]
    assert "provider_contracts.ziwei_qimen_calculation_basis_audit_contract" in calculation_basis["evidence"]
    assert "provider_protocols.ziwei_qimen_calculation_basis_stdout_schema" in calculation_basis["evidence"]
    classical_refresh = next(item for item in audit["implemented_requirements"] if item["id"] == "classical_source_refresh_pipeline")
    assert "rights/review-governed" in classical_refresh["requirement"]
    assert "classical_corpus_refresh.source_governance_metadata" in classical_refresh["evidence"]
    assert "tests/test_evidence.py source governance metadata" in classical_refresh["evidence"]
    empirical_validation = next(item for item in audit["implemented_requirements"] if item["id"] == "empirical_validation_harness")
    assert "record-level label provenance" in empirical_validation["requirement"]
    assert "outcome_dataset.record_label_provenance_gate" in empirical_validation["evidence"]
    assert "outcome_dataset.statistical_plan_preregistration_gate" in empirical_validation["evidence"]
    release_gate_binding = next(
        item for item in audit["implemented_requirements"] if item["id"] == "release_manifest_readiness_gate_binding"
    )
    assert "provider audit contracts" in release_gate_binding["requirement"]
    assert (
        "api_core.release_manifest.release_gate_checks.provider_audit_contract_gates_bound"
        in release_gate_binding["evidence"]
    )
    assert (
        "api_core.release_manifest.release_gate_checks.outcome_statistical_plan_preregistration_bound"
        in release_gate_binding["evidence"]
    )
    assert (
        "api_core.release_manifest.release_gate_checks.classical_latest_refresh_receipt_bound"
        in release_gate_binding["evidence"]
    )
    blocked_coverage = audit["blocked_capability_coverage"]
    assert blocked_coverage["coverage_complete"] is True
    assert blocked_coverage == audit["audit_receipt"]["material"]["blocked_capability_coverage"]
    assert blocked_coverage["unaccounted_capabilities"] == []
    coverage_by_capability = {item["capability"]: item for item in blocked_coverage["entries"]}
    assert coverage_by_capability["professional_ziwei_provider_available"]["gap_ids"] == [
        "professional_ziwei_provider"
    ]
    assert coverage_by_capability["llm_backend_configured"]["classification"] == "optional_configuration"
    assert len(blocked_coverage["coverage_sha256"]) == 64
    blocked_requirement = next(
        item for item in audit["implemented_requirements"] if item["id"] == "blocked_capability_coverage_audit"
    )
    assert "false capability" in blocked_requirement["requirement"]
    assert "capability_audit._blocked_capability_coverage" in blocked_requirement["evidence"]
    blocked_gate_requirement = next(
        item for item in audit["implemented_requirements"]
        if item["id"] == "blocked_capability_coverage_production_gate"
    )
    assert "Production readiness" in blocked_gate_requirement["requirement"]
    assert "api_core.production_readiness.blocked_capability_coverage_complete" in blocked_gate_requirement["evidence"]
    assert (
        "api_core.release_manifest.release_gate_checks.blocked_capability_coverage_bound"
        in blocked_gate_requirement["evidence"]
    )
    command_requirement = next(
        item for item in audit["implemented_requirements"] if item["id"] == "known_gap_verification_command_coverage"
    )
    assert "current CLI subcommands" in command_requirement["requirement"]
    assert "capability_audit.known_gap_verification_command_coverage" in command_requirement["evidence"]
    gap_coverage = audit["known_gap_resolution_plan_coverage"]
    assert gap_coverage["command_validation_complete"] is True
    assert gap_coverage["invalid_verification_commands_by_gap"] == {}
    assert gap_coverage["invalid_verification_options_by_gap"] == {}
    assert "provider-protocols" in gap_coverage["valid_cli_subcommands"]
    assert "--domain" in gap_coverage["valid_cli_options_by_subcommand"]["provider-protocols"]
    assert "production-readiness" in gap_coverage["command_subcommands_by_gap"]["professional_ziwei_provider"]
    assert "--live" in gap_coverage["command_options_by_gap"]["professional_ziwei_provider"]
    command_release_binding = next(
        item for item in audit["implemented_requirements"]
        if item["id"] == "known_gap_command_coverage_release_binding"
    )
    assert "Release manifests" in command_release_binding["requirement"]
    assert (
        "api_core.release_manifest.release_gate_checks.known_gap_command_coverage_bound"
        in command_release_binding["evidence"]
    )
    handoff_bundle = audit["known_gap_handoff_bundle"]
    assert handoff_bundle == audit["audit_receipt"]["material"]["known_gap_handoff_bundle"]
    assert handoff_bundle["status"] == "ready"
    assert handoff_bundle["gap_count"] == len(audit["known_gaps"])
    assert handoff_bundle["missing_handoff_gap_ids"] == []
    assert len(handoff_bundle["bundle_sha256"]) == 64
    handoff_by_gap = {item["gap_id"]: item for item in handoff_bundle["items"]}
    assert handoff_by_gap["professional_ziwei_provider"]["required_env_vars"] == ["SEMAS_ZIWEI_CLI"]
    assert handoff_by_gap["professional_ziwei_provider"]["required_provenance_env_vars"] == [
        "SEMAS_ZIWEI_PROVIDER_PROVENANCE"
    ]
    assert handoff_by_gap["professional_ziwei_provider"]["blocked_capabilities"] == [
        "professional_ziwei_provider_available"
    ]
    assert any(
        candidate["name"] == "iztro / dart_iztro family"
        for candidate in handoff_by_gap["professional_ziwei_provider"]["external_candidate_projects"]
    )
    assert handoff_by_gap["external_classic_text_retrieval"]["required_env_vars"] == []
    assert all(item["handoff_ready"] is True for item in handoff_bundle["items"])
    handoff_requirement = next(
        item for item in audit["implemented_requirements"] if item["id"] == "known_gap_handoff_bundle"
    )
    assert "machine-readable handoff bundle" in handoff_requirement["requirement"]
    assert "capability_audit._known_gap_handoff_bundle" in handoff_requirement["evidence"]
    handoff_gate_requirement = next(
        item for item in audit["implemented_requirements"] if item["id"] == "known_gap_handoff_bundle_production_gate"
    )
    assert "Production readiness" in handoff_gate_requirement["requirement"]
    assert "api_core.production_readiness.known_gap_handoff_bundle_ready" in handoff_gate_requirement["evidence"]
    assert (
        "api_core.release_manifest.release_gate_checks.known_gap_handoff_bundle_bound"
        in handoff_gate_requirement["evidence"]
    )
    handoff_export_requirement = next(
        item for item in audit["implemented_requirements"] if item["id"] == "known_gap_handoff_export_cli_api"
    )
    assert "exported directly through CLI and HTTP API" in handoff_export_requirement["requirement"]
    assert "api_core.known_gap_handoff" in handoff_export_requirement["evidence"]
    assert "cli known-gap-handoff" in handoff_export_requirement["evidence"]
    assert "GET /known-gap-handoff" in handoff_export_requirement["evidence"]
    handoff_verification_requirement = next(
        item for item in audit["implemented_requirements"] if item["id"] == "known_gap_handoff_export_verification"
    )
    assert "verified through CLI and HTTP API" in handoff_verification_requirement["requirement"]
    assert "api_core.verify_known_gap_handoff_export" in handoff_verification_requirement["evidence"]
    assert "cli known-gap-handoff-verify --input" in handoff_verification_requirement["evidence"]
    handoff_checklist_requirement = next(
        item for item in audit["implemented_requirements"]
        if item["id"] == "known_gap_handoff_implementation_checklist"
    )
    assert "through CLI and HTTP API into per-gap implementation checklists" in handoff_checklist_requirement[
        "requirement"
    ]
    assert "expected checklist receipt drift binding" in handoff_checklist_requirement["requirement"]
    assert "api_core.known_gap_handoff_implementation_checklist" in handoff_checklist_requirement["evidence"]
    assert "cli known-gap-handoff-checklist --input" in handoff_checklist_requirement["evidence"]
    assert (
        "api_core.schema_document.KnownGapHandoffChecklistResponse.checklist_receipt_matches_expected"
        in handoff_checklist_requirement["evidence"]
    )
    guidance = audit["provider_checks"]["production_guidance"]
    receipt_guidance = audit["audit_receipt"]["material"]["provider_production_guidance"]
    assert receipt_guidance == guidance
    assert "SEMAS_ZIWEI_CLI" in guidance["required_env_vars"]
    assert "SEMAS_ZIWEI_PROVIDER_PROVENANCE" in guidance["required_provenance_env_vars"]
    assert any("certify-provider ziwei" in command for command in guidance["certification_commands"])
    assert "production-readiness" in guidance["production_readiness_command"]
