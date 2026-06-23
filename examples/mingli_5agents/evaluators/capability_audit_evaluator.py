"""Evaluator metric for capability audit and state-of-art transparency."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

REQUIRED_CAPABILITIES = {
    "five_agents",
    "discussion_voting",
    "semas_orchestrator_evolution",
    "population_evolution",
    "regression_and_validation_gates",
    "archive_hash_chain",
    "genome_lineage_integrity",
    "audited_rollback",
    "reproducibility_manifest_strategy_fingerprints",
    "evolution_trigger_receipt",
    "release_manifest_evolution_trigger_binding",
    "github_comparison_receipt",
    "plan_compliance_receipt",
    "release_manifest_github_comparison_binding",
    "release_manifest_plan_compliance_binding",
    "reference_chart_contracts",
    "classical_text_index",
    "classical_source_refresh_governance",
    "classical_source_governance_metadata",
    "topic_synthesis_timing_schema_contract",
    "empirical_validation_harness",
    "outcome_dataset_manifest_audit",
    "outcome_dataset_record_label_provenance_gate",
    "outcome_dataset_statistical_plan_preregistration_gate",
    "external_professional_chart_injection",
    "request_scoped_full_external_provider_injection",
    "request_scoped_external_provider_provenance",
    "request_scoped_external_payload_receipts",
    "provider_raw_contract_receipt",
    "bazi_core_profile_schema_contract",
    "annual_timeline_topic_evidence_binding",
    "monthly_luck_topic_evidence_binding",
    "monthly_luck_public_schema_contract",
    "astrology_profile_public_schema_contract",
    "astrology_ephemeris_audit_contract",
    "xuanze_rule_table_audit_contract",
    "ziwei_qimen_public_schema_contract",
    "ziwei_qimen_calculation_basis_audit_contract",
    "rendered_reports_public_schema_contract",
    "final_report_runtime_metadata_schema_contract",
    "source_review_public_schema_contract",
    "final_report_metadata_schema_contract",
    "analyze_response_runtime_schema_validation",
    "production_readiness_schema_validation_gate",
    "provider_production_guidance",
    "chinese_markdown_renderer",
    "topic_synthesis",
    "safety_guardrails",
}

REQUIRED_COMPARISON_DIMENSIONS = {
    "multi_agent_evolution",
    "ziwei_calculation",
    "qimen_calculation",
    "western_astrology",
    "calendar_and_xuanze",
    "empirical_validation",
    "classical_evidence",
}

REQUIRED_GAPS = {
    "professional_ziwei_provider",
    "professional_qimen_provider",
    "astronomical_ephemeris",
    "empirical_validation_dataset",
}

REQUIRED_PLAN_SECTIONS = {
    "1_project_goal",
    "2_llm_backend",
    "3_agent_architecture",
    "4_analysis_layers",
    "5_collaboration_workflow",
    "6_evolution_mechanism",
    "7_classical_sources",
    "8_project_structure",
    "9_open_questions",
    "10_safety_note",
}

REQUIRED_PROVIDER_TARGETS = {
    "bazi_professional_calendar",
    "ziwei_professional_engine",
    "qimen_professional_engine",
    "astrology_ephemeris_engine",
    "xuanze_almanac_engine",
}


def capability_audit_score(result: dict[str, Any], expected: dict[str, Any] | None = None) -> float:
    """Score whether the framework exposes honest capability and SOTA audit data."""
    audit = _cached_capability_audit(_env_signature())
    capabilities = audit.get("capabilities", {})
    matrix = audit.get("github_comparison_matrix", [])
    gaps = audit.get("known_gaps", [])
    state_of_art = audit.get("state_of_art", {})

    capability_score = _fraction_present_true(capabilities, REQUIRED_CAPABILITIES)
    matrix_dimensions = {item.get("dimension") for item in matrix if isinstance(item, dict)}
    matrix_score = len(REQUIRED_COMPARISON_DIMENSIONS & matrix_dimensions) / len(REQUIRED_COMPARISON_DIMENSIONS)
    gap_ids = {item.get("id") for item in gaps if isinstance(item, dict)}
    gap_score = len(REQUIRED_GAPS & gap_ids) / len(REQUIRED_GAPS)
    transparency_score = 1.0 if _state_of_art_ok(state_of_art) else 0.0
    plan_score = 1.0 if _plan_compliance_ok(audit.get("plan_compliance")) else 0.0
    provider_plan_score = 1.0 if _provider_integration_plan_ok(audit.get("provider_checks")) else 0.0
    provider_guidance_score = 1.0 if _provider_production_guidance_ok(audit.get("provider_checks")) else 0.0

    return round(
        capability_score * 0.38
        + matrix_score * 0.25
        + gap_score * 0.2
        + transparency_score * 0.1
        + plan_score * 0.04
        + provider_plan_score * 0.02
        + provider_guidance_score * 0.01,
        6,
    )


@lru_cache(maxsize=8)
def _cached_capability_audit(env_signature: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    from examples.mingli_5agents.capability_audit import capability_audit

    return capability_audit()


def _env_signature() -> tuple[tuple[str, str], ...]:
    keys = (
        "SEMAS_ASTROLOGY_CLI",
        "SEMAS_CLASSIC_CORPUS_DIR",
        "SEMAS_OUTCOME_DATASET_MANIFEST",
        "SEMAS_QIMEN_CLI",
        "SEMAS_XUANZE_CLI",
        "SEMAS_ZIWEI_CLI",
    )
    return tuple((key, os.environ.get(key, "")) for key in keys)


def _fraction_present_true(values: object, required: set[str]) -> float:
    if not isinstance(values, dict):
        return 0.0
    return sum(1 for key in required if values.get(key) is True) / len(required)


def _state_of_art_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("verdict") not in {
        "advanced_agentic_framework_not_full_domain_sota",
        "near_sota_with_configured_providers",
    }:
        return False
    blockers = value.get("blocking_provider_capabilities")
    return (
        isinstance(value.get("production_ready_for_professional_calculation"), bool)
        and isinstance(value.get("request_scoped_provenance_required"), bool)
        and isinstance(value.get("strength_dimensions"), list)
        and isinstance(blockers, list)
        and value.get("comparison_scope") == "GitHub/open-source project comparison plus local capability checks."
    )


def _plan_compliance_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    matrix = value.get("matrix")
    source_receipt = value.get("source_receipt")
    if value.get("source") != "plan_mingli5agents.md" or value.get("section_count") != len(REQUIRED_PLAN_SECTIONS):
        return False
    if not isinstance(source_receipt, dict):
        return False
    if (
        source_receipt.get("path") != "plan_mingli5agents.md"
        or source_receipt.get("exists") is not True
        or source_receipt.get("readable") is not True
        or source_receipt.get("encoding") != "utf-8"
        or source_receipt.get("section_heading_count") != len(REQUIRED_PLAN_SECTIONS)
        or not isinstance(source_receipt.get("byte_count"), int)
        or source_receipt.get("byte_count", 0) <= 0
        or not isinstance(source_receipt.get("sha256"), str)
        or len(source_receipt.get("sha256", "")) != 64
    ):
        return False
    if not isinstance(matrix, list):
        return False
    sections = {item.get("section"): item for item in matrix if isinstance(item, dict)}
    if set(sections) != REQUIRED_PLAN_SECTIONS:
        return False
    return all(
        item.get("implemented_verified") is True and item.get("gap_ids_verified") is True
        for item in sections.values()
    )


def _provider_integration_plan_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    plan = value.get("integration_plan")
    if not isinstance(plan, dict):
        return False
    targets = plan.get("targets")
    if not isinstance(targets, list):
        return False
    target_map = {item.get("name"): item for item in targets if isinstance(item, dict)}
    if set(target_map) != REQUIRED_PROVIDER_TARGETS:
        return False
    if plan.get("total_targets") != len(REQUIRED_PROVIDER_TARGETS):
        return False
    if plan.get("reference_contracts_passed") is not True:
        return False
    if plan.get("live_required_for_production") is not True:
        return False
    if not isinstance(plan.get("smoke_command"), str) or "providers --profile production --live" not in plan["smoke_command"]:
        return False
    return all(
        isinstance(item.get("contracts"), list)
        and item["contracts"]
        and isinstance(item.get("next_actions"), list)
        for item in target_map.values()
    )


def _provider_production_guidance_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    guidance = value.get("production_guidance")
    if not isinstance(guidance, dict):
        return False
    if not isinstance(guidance.get("production_ready"), bool):
        return False
    for key in (
        "blocked_targets",
        "required_env_vars",
        "required_provenance_env_vars",
        "certification_commands",
        "drift_commands",
        "deployment_checklist",
        "next_actions",
    ):
        if not isinstance(guidance.get(key), list):
            return False
    for key in (
        "provider_onboarding_command",
        "provider_ledger_command",
        "production_readiness_command",
        "smoke_command",
        "policy",
    ):
        if not isinstance(guidance.get(key), str) or not guidance.get(key):
            return False
    if not set(guidance.get("blocked_targets", [])).issubset(REQUIRED_PROVIDER_TARGETS):
        return False
    if guidance.get("production_ready") is False and not (
        any("certify-provider" in command for command in guidance.get("certification_commands", []))
        and any("provider-drift" in command for command in guidance.get("drift_commands", []))
    ):
        return False
    return (
        "production-readiness" in guidance.get("production_readiness_command", "")
        and "providers --profile production --live" in guidance.get("smoke_command", "")
    )
