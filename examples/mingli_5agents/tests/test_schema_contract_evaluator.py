"""Tests for public schema-contract evaluator gating."""

from __future__ import annotations

import json
from pathlib import Path

from examples.mingli_5agents.api_core import (
    _annual_timeline_receipt_coverage,
    _auspicious_calendar_receipt_coverage,
    _classical_latest_refresh_receipt_current,
    _classical_latest_refresh_receipt_failures,
    _classical_source_receipt_coverage,
    _external_payload_birth_match_coverage,
    _known_gap_resolution_plan_coverage,
    _known_gap_resolution_plan_coverage_from_response,
    _monthly_luck_receipt_coverage,
    _provider_action_plan_coverage,
    _readiness_deliberation_receipt_coverage,
    analyze_case,
    capability_audit,
    schema_document,
    schema_validation_errors,
)
from examples.mingli_5agents.evaluators.schema_contract_evaluator import (
    REQUIRED_ENDPOINTS,
    REQUIRED_SCHEMAS,
    _required_fields_ok,
    _response_refs_ok,
    schema_contract_score,
)


def test_schema_contract_score_accepts_current_schema():
    assert schema_contract_score({}) == 1.0


def test_analyze_response_runtime_output_matches_public_schema_contract(tmp_path: Path):
    schema = schema_document()
    task_input = json.loads(
        Path("examples/mingli_5agents/reports/lin_fan_1978_input.json").read_text(encoding="utf-8")
    )
    result = analyze_case(tmp_path / "repo", task_input)
    json_result = json.loads(json.dumps(result, ensure_ascii=False))

    errors = schema_validation_errors(
        json_result,
        schema_name="AnalyzeResponse",
        schema_doc=schema,
    )

    assert errors == []
    assert json_result["schema_validation"]["schema_name"] == "AnalyzeResponse"
    assert json_result["schema_validation"]["valid"] is True
    assert json_result["schema_validation"]["error_count"] == 0
    assert json_result["schema_validation"]["errors"] == []

    broken = dict(json_result)
    broken.pop("result")
    assert any("result: missing required" in item for item in schema_validation_errors(broken, schema_doc=schema))


def test_industry_fixture_import_runtime_output_matches_public_schema_contract(tmp_path: Path):
    schema = schema_document()
    result = capability_audit(tmp_path / "repo")
    fixture_receipt = json.loads(json.dumps(result["industry_event_cross_domain_fixture_import"], ensure_ascii=False))
    audit_material_receipt = json.loads(
        json.dumps(
            result["audit_receipt"]["material"]["industry_event_cross_domain_fixture_import"],
            ensure_ascii=False,
        )
    )

    assert schema_validation_errors(
        fixture_receipt,
        schema_name="IndustryEventCrossDomainFixtureImportReceipt",
        schema_doc=schema,
    ) == []
    assert schema_validation_errors(
        audit_material_receipt,
        schema_name="IndustryEventCrossDomainFixtureImportReceipt",
        schema_doc=schema,
    ) == []
    assert audit_material_receipt["sha256"] == fixture_receipt["sha256"]
    assert audit_material_receipt["material"]["validation_label_table_receipt_sha256"] == (
        fixture_receipt["material"]["validation_label_table_receipt_sha256"]
    )


def test_governance_schemas_do_not_expose_loose_object_properties():
    schemas = schema_document()["schemas"]
    governance_name_tokens = (
        "Receipt",
        "Readiness",
        "Release",
        "Audit",
        "Ledger",
        "Drift",
        "Coverage",
        "Summary",
        "Manifest",
        "ProviderChecks",
    )
    loose: dict[str, list[str]] = {}

    for name, spec in schemas.items():
        if not isinstance(spec, dict) or not any(token in name for token in governance_name_tokens):
            continue
        fields = []
        for field, field_schema in spec.get("properties", {}).items():
            if (
                isinstance(field_schema, dict)
                and field_schema.get("type") == "object"
                and "$ref" not in field_schema
                and "required" not in field_schema
                and "additionalProperties" not in field_schema
                and "anyOf" not in field_schema
            ):
                fields.append(field)
        if fields:
            loose[name] = fields

    assert loose == {}


def test_known_gap_resolution_plan_coverage_rejects_unknown_production_gate():
    coverage = _known_gap_resolution_plan_coverage_from_response(
        {
            "known_gap_ids": ["professional_ziwei_provider"],
            "known_gap_resolution_plan": [
                {
                    "gap_id": "professional_ziwei_provider",
                    "status": "open",
                    "verification_commands": ["python -m examples.mingli_5agents.cli provider-ledger"],
                    "production_gate_ids": ["provider_certification_ledger_complete"],
                }
            ],
            "capability_audit_receipt": {"material": {"known_gap_resolution_plan_hash": "a" * 64}},
        }
    )

    assert coverage["coverage_complete"] is False
    assert coverage["invalid_plan_gap_ids"] == ["professional_ziwei_provider"]
    assert coverage["invalid_gate_ids_by_gap"] == {
        "professional_ziwei_provider": ["provider_certification_ledger_complete"]
    }


def test_known_gap_resolution_plan_coverage_rejects_unknown_cli_command():
    coverage = _known_gap_resolution_plan_coverage_from_response(
        {
            "known_gap_ids": ["professional_ziwei_provider"],
            "known_gap_resolution_plan": [
                {
                    "gap_id": "professional_ziwei_provider",
                    "status": "open",
                    "verification_commands": ["python examples/mingli_5agents/cli.py --repo <repo> missing-command"],
                    "production_gate_ids": ["provider_profile_ready"],
                }
            ],
            "capability_audit_receipt": {"material": {"known_gap_resolution_plan_hash": "a" * 64}},
        }
    )

    assert coverage["coverage_complete"] is False
    assert coverage["command_validation_complete"] is False
    assert coverage["invalid_plan_gap_ids"] == ["professional_ziwei_provider"]
    assert "professional_ziwei_provider" in coverage["invalid_verification_commands_by_gap"]


def test_known_gap_resolution_plan_coverage_rejects_unknown_cli_option():
    coverage = _known_gap_resolution_plan_coverage_from_response(
        {
            "known_gap_ids": ["professional_ziwei_provider"],
            "known_gap_resolution_plan": [
                {
                    "gap_id": "professional_ziwei_provider",
                    "status": "open",
                    "verification_commands": [
                        "python examples/mingli_5agents/cli.py --repo <repo> provider-ledger --bad-option"
                    ],
                    "production_gate_ids": ["provider_profile_ready"],
                }
            ],
            "capability_audit_receipt": {"material": {"known_gap_resolution_plan_hash": "a" * 64}},
        }
    )

    assert coverage["coverage_complete"] is False
    assert coverage["command_validation_complete"] is False
    assert coverage["invalid_plan_gap_ids"] == ["professional_ziwei_provider"]
    assert "professional_ziwei_provider" in coverage["invalid_verification_options_by_gap"]


def test_known_gap_resolution_plan_coverage_accepts_id_alias():
    coverage = _known_gap_resolution_plan_coverage_from_response(
        {
            "known_gap_ids": ["professional_ziwei_provider"],
            "known_gap_resolution_plan": [
                {
                    "id": "professional_ziwei_provider",
                    "status": "open",
                    "verification_commands": ["python -m examples.mingli_5agents.cli provider-ledger"],
                    "production_gate_ids": ["provider_certification_ledger_covers_domains"],
                }
            ],
            "capability_audit_receipt": {"material": {"known_gap_resolution_plan_hash": "a" * 64}},
        }
    )

    assert coverage["coverage_complete"] is True
    assert coverage["command_validation_complete"] is True
    assert coverage["missing_gap_ids"] == []
    assert coverage["planned_gap_ids"] == ["professional_ziwei_provider"]
    assert coverage["command_subcommands_by_gap"]["professional_ziwei_provider"] == ["provider-ledger"]
    assert coverage["command_options_by_gap"]["professional_ziwei_provider"] == []


def test_known_gap_resolution_plan_release_fallback_matches_schema_contract():
    coverage = _known_gap_resolution_plan_coverage({})

    for key in schema_document()["schemas"]["KnownGapResolutionPlanCoverage"]["required"]:
        assert key in coverage
    assert coverage["planned_gap_ids"] == []
    assert coverage["invalid_gate_ids_by_gap"] == {}
    assert "provider_profile_ready" in coverage["valid_production_gate_ids"]
    assert "ziwei_qimen_calculation_basis_audit_contract" in coverage["valid_production_gate_ids"]
    assert "astrology_ephemeris_audit_contract" in coverage["valid_production_gate_ids"]
    assert "xuanze_rule_table_audit_contract" in coverage["valid_production_gate_ids"]
    assert "classical_source_latest_refresh_receipt_present" in coverage["valid_production_gate_ids"]
    assert "blocked_capability_coverage_complete" in coverage["valid_production_gate_ids"]
    assert "benchmark_chinese_render_quality_diagnostics" in coverage["valid_production_gate_ids"]
    assert "famous_case_source_review_routing_complete" in coverage["valid_production_gate_ids"]
    assert "famous_case_source_review_queue_aligned" in coverage["valid_production_gate_ids"]
    assert coverage["command_validation_complete"] is False
    assert coverage["invalid_verification_commands_by_gap"] == {}


def test_classical_latest_refresh_receipt_current_requires_matching_source_list_receipt():
    source_audit = {"status": "ready", "source_list_receipt": {"sha256": "a" * 64}}
    refresh_receipt = {
        "sha256": "b" * 64,
        "material": {"source_list_receipt_sha256": "a" * 64, "record_count": 2},
    }

    assert _classical_latest_refresh_receipt_current(source_audit, refresh_receipt) is True
    assert _classical_latest_refresh_receipt_failures(source_audit, refresh_receipt) == []

    stale_receipt = {
        "sha256": "c" * 64,
        "material": {"source_list_receipt_sha256": "d" * 64, "record_count": 2},
    }
    failures = _classical_latest_refresh_receipt_failures(source_audit, stale_receipt)
    assert _classical_latest_refresh_receipt_current(source_audit, stale_receipt) is False
    assert any("does not match current source_list_receipt" in failure for failure in failures)


def test_release_coverage_fallbacks_match_schema_required_fields():
    schemas = schema_document()["schemas"]
    schema = schemas["ReleaseManifestReceiptMaterial"]["properties"]
    helpers = {
        "readiness_deliberation_receipt_coverage": _readiness_deliberation_receipt_coverage,
        "annual_timeline_receipt_coverage": _annual_timeline_receipt_coverage,
        "monthly_luck_receipt_coverage": _monthly_luck_receipt_coverage,
        "auspicious_calendar_receipt_coverage": _auspicious_calendar_receipt_coverage,
        "external_payload_birth_match_coverage": _external_payload_birth_match_coverage,
        "provider_action_plan_coverage": _provider_action_plan_coverage,
        "classical_source_receipt_coverage": _classical_source_receipt_coverage,
        "known_gap_resolution_plan_coverage": _known_gap_resolution_plan_coverage,
    }

    for field, helper in helpers.items():
        coverage = helper({})
        field_schema = schema[field]
        if "$ref" in field_schema:
            field_schema = schemas[field_schema["$ref"].removeprefix("#/schemas/")]
        for key in field_schema["required"]:
            assert key in coverage, f"{field} missing fallback key {key}"


def test_classical_source_receipt_coverage_carries_refresh_receipt():
    coverage = _classical_source_receipt_coverage(
        {
            "material": {
                "classical_source_refresh": {
                    "status": "ready",
                    "valid": True,
                    "source_list_receipt_sha256": "a" * 64,
                    "source_list_receipt_material_sha256": "c" * 64,
                    "latest_refresh_receipt_sha256": "b" * 64,
                    "latest_refresh_record_count": 3,
                    "source_count": 2,
                    "locked_source_count": 2,
                }
            }
        }
    )

    assert coverage["receipt_present"] is True
    assert coverage["source_list_receipt_sha256"] == "a" * 64
    assert coverage["source_list_receipt_material_sha256"] == "c" * 64
    assert coverage["refresh_receipt_present"] is True
    assert coverage["latest_refresh_receipt_sha256"] == "b" * 64
    assert coverage["latest_refresh_record_count"] == 3


def test_schema_contract_score_gates_release_governance_contracts():
    schema = schema_document()

    assert {
        "ReleaseManifestResponse",
        "ReleaseManifestLedgerResponse",
        "ReleaseManifestDriftResponse",
        "ProductionReadinessEvidenceMaterializationSummary",
        "ProductionReadinessReceipt",
        "ProductionReadinessReceiptMaterial",
        "ReleaseManifestReceipt",
        "ReleaseManifestReceiptMaterial",
        "ReleaseManifestGateChecks",
        "RenderedReports",
        "OutcomeDatasetReceiptMaterial",
        "OutcomeDataSplitRecordCoverage",
        "OutcomeGovernanceGates",
        "OutcomeLabelInventory",
        "OutcomeLabelProvenanceSummary",
        "OutcomeOptimizationPolicy",
        "OutcomeRecordFingerprint",
        "OutcomeQualityTaskFingerprint",
        "AuspiciousCalendar",
        "AuspiciousCalendarRange",
        "AuspiciousCalendarBasis",
        "AuspiciousCalendarReceipt",
        "AuspiciousCalendarReceiptRowFingerprint",
        "AuspiciousDayRow",
        "AuspiciousMethodMatrixItem",
        "AuspiciousRecommendedHour",
        "ClassicalSourcesResponse",
        "ClassicalSourceListAudit",
        "ClassicalSourceListReceipt",
        "ClassicalSourceListReceiptMaterial",
        "ClassicalSourceRefreshReceiptSummary",
        "ClassicalRefreshReceipt",
        "ClassicalRefreshReceiptMaterial",
        "ClassicalRefreshSourceReceipt",
        "AnnualLuck",
        "AnnualLuckActiveMajorLuck",
        "AnnualLuckBaziEvidence",
        "AnnualLuckRangeSummary",
        "AnnualLuckRow",
        "AnnualLuckRowElements",
        "AnnualLuckNatalPillarMatch",
        "AnnualLuckTenGodPair",
        "AnnualPhaseSummary",
        "AnnualPhaseTopicHighlight",
        "MonthlyLuckBasisSummary",
        "MonthlyLuckRangeSummary",
        "ZiweiAnnualActivation",
        "ZiweiMajorLimit",
        "ZiweiPalaceSummary",
        "ZiweiProfile",
        "QimenAnnualTiming",
        "QimenDuty",
        "QimenPalaceSummary",
        "QimenPatternFlag",
        "QimenProfile",
        "QimenUsefulGod",
        "DeliberationReceipt",
        "RequestProvenance",
        "VoteAudit",
        "VoteChallenge",
        "VoteClaim",
        "VoteRecord",
        "WorkflowReport",
        "LLMSynthesisReport",
        "KnownGapResolutionPlanItem",
        "KnownGapResolutionPlanCoverage",
        "ProductionGateRegistryAudit",
        "ProductionBlocker",
        "PlanComplianceReceipt",
        "PlanComplianceReceiptMaterial",
        "MethodSurfaceReceiptSummary",
        "ProviderExampleSmokeResponse",
        "ProviderExampleSmokeDomain",
        "ProviderCommandFingerprint",
        "ProviderCertificationReceiptMaterial",
        "ProviderProtocolIdentity",
        "ProviderReferenceContractCoverage",
        "ProviderRequestProtocolIdentity",
        "ProviderRequestReceipt",
        "ProviderProfileReadiness",
        "ProviderProfileRequiredGroup",
        "ProviderReadinessMatrixItem",
        "BaziLuckStart",
        "BaziMajorLuckAnnualPreview",
        "BaziMajorLuckPeriod",
        "BaziMethodMatrixItem",
        "BaziPatternAnalysis",
        "BaziStrengthAnalysis",
        "BaziUsefulGodAnalysis",
        "BenchmarkCaseReportFeatures",
        "BenchmarkCaseResult",
        "BenchmarkExternalPayloadBirthMatchStatus",
        "BenchmarkReceiptCaseSummary",
        "BenchmarkReceiptEmpiricalValidationSummary",
        "BenchmarkReceiptMaterial",
        "BenchmarkReceiptReferenceChartsSummary",
        "ReferenceChartCaseCheck",
        "ReferenceChartChecks",
        "ReferenceChartDomainMethodCoverage",
        "ReferenceChartMethodCoverage",
        "ProviderOnboardingDomain",
        "ProviderOnboardingAuditSummary",
        "ProviderOnboardingReceipt",
        "ProviderOnboardingReceiptMaterial",
        "ProviderOnboardingResponse",
        "CapabilityAuditReceipt",
        "CapabilityAuditReceiptMaterial",
        "CapabilityFlagMap",
        "FamousCaseAnnualEventCalibrationReceiptSummary",
        "FamousCaseValidationReceiptSummary",
        "FamousCaseSchoolCalibrationReceiptSummary",
        "GitHubComparisonReceipt",
        "GitHubComparisonReceiptMaterial",
        "RequestScopedProviderContractSummary",
        "BirthProfileFixturePatchPreviewResponse",
        "BirthProfileReviewedManifestDraftPreviewResponse",
        "BirthProfileReviewedManifestFilePreviewResponse",
        "BirthProfileSourceCacheAuditResponse",
        "BirthProfileSourceCacheTemplatePreviewResponse",
        "BirthProfileSourceLookupPlanResponse",
        "BirthProfileSourceReviewWorkplanResponse",
        "EvolutionTriggerReceipt",
        "EvolutionTriggerReceiptMaterial",
        "EvidenceSummaryItem",
        "ProviderProtocolGovernanceSummary",
        "ProviderProtocolIdentityHandshakeSummary",
        "ProviderProtocolsReceipt",
        "ProviderProtocolsReceiptMaterial",
        "ReproducibilityStrategyFingerprint",
        "SchemaValidationSummary",
        "SpecialistSource",
        "SourceEvidenceProvenance",
        "SourceEvidenceSnippet",
        "SourceReviewReport",
        "TopicSynthesisAnnualFocus",
        "TopicSynthesisCrossAgentEvidence",
        "TopicSynthesisMonthlyFocus",
        "TopicSynthesisTimingEvidence",
        "TopicSynthesisTimingSignal",
        "TopicSynthesisItem",
    }.issubset(REQUIRED_SCHEMAS)
    assert {
        "GET /release-manifest",
        "GET /release-ledger",
        "GET /release-drift",
        "GET /classical-sources",
        "GET /provider-examples",
        "GET /provider-onboarding",
        "GET /birth-profile-fixture-patch-preview",
        "GET /birth-profile-reviewed-manifest-draft-preview",
        "GET /birth-profile-reviewed-manifest-file-preview",
        "GET /birth-profile-source-cache-audit",
        "GET /birth-profile-source-cache-template-preview",
        "GET /birth-profile-source-lookup-plan",
        "GET /birth-profile-source-review-workplan",
    }.issubset(REQUIRED_ENDPOINTS)
    assert "trigger_receipt" in schema["schemas"]["EvolveResponse"]["required"]
    assert schema["schemas"]["EvolveResponse"]["properties"]["trigger_receipt"]["$ref"] == (
        "#/schemas/EvolutionTriggerReceipt"
    )
    assert schema["schemas"]["EvolutionTriggerReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/EvolutionTriggerReceiptMaterial"
    )
    assert "feedback_sha256" in schema["schemas"]["EvolutionTriggerReceiptMaterial"]["required"]
    assert "outcome_dataset_gate_passed" in schema["schemas"]["EvolutionTriggerReceiptMaterial"]["required"]
    assert "trigger_receipt" in schema["schemas"]["LatestEvolutionStatus"]["required"]
    assert "trigger_receipt" in schema["schemas"]["GenomeLineage"]["required"]
    assert "trigger_receipt_matches" in schema["schemas"]["LineageIntegrityReport"]["required"]
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["audit_receipt"]["$ref"] == (
        "#/schemas/CapabilityAuditReceipt"
    )
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["provider_protocols_receipt"]["$ref"] == (
        "#/schemas/ProviderProtocolsReceipt"
    )
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["provider_onboarding_receipt"]["$ref"] == (
        "#/schemas/ProviderOnboardingReceipt"
    )
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["readiness_receipt"]["$ref"] == (
        "#/schemas/ProductionReadinessReceipt"
    )
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["production_gate_registry_audit"]["$ref"] == (
        "#/schemas/ProductionGateRegistryAudit"
    )
    assert schema["schemas"]["ProductionReadinessReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ProductionReadinessReceiptMaterial"
    )
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["gates"]["items"]["$ref"] == (
        "#/schemas/ProductionReadinessGate"
    )
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["current_benchmark"]["$ref"] == (
        "#/schemas/ProductionReadinessBenchmarkSummary"
    )
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["capability_audit_receipt"]["$ref"] == (
        "#/schemas/ProductionReadinessCapabilityAuditReceiptSummary"
    )
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["provider_certification_ledger"][
        "$ref"
    ] == "#/schemas/ProductionReadinessProviderLedgerSummary"
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["provider_certification_drift"][
        "$ref"
    ] == "#/schemas/ProductionReadinessProviderDriftSummary"
    assert "request_provenance_audit" in schema["schemas"]["ProductionReadinessBenchmarkSummary"]["required"]
    assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["birth_profile_audit"]["$ref"] == (
        "#/schemas/ProductionReadinessBenchmarkBirthProfileAudit"
    )
    assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["request_provenance_audit"]["$ref"] == (
        "#/schemas/ProductionReadinessBenchmarkRequestProvenanceAudit"
    )
    assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["provider_action_plan_audit"]["$ref"] == (
        "#/schemas/ProductionReadinessBenchmarkProviderActionPlanAudit"
    )
    assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["topic_confidence_audit"]["$ref"] == (
        "#/schemas/ProductionReadinessBenchmarkTopicConfidenceAudit"
    )
    assert schema["schemas"]["ProductionReadinessBenchmarkBirthProfileAudit"]["properties"]["fingerprints"]["items"][
        "$ref"
    ] == "#/schemas/ProductionReadinessBenchmarkCaseSha256"
    assert schema["schemas"]["ProductionReadinessBenchmarkRequestProvenanceAudit"]["properties"][
        "annual_timeline_receipts"
    ]["items"]["$ref"] == "#/schemas/ProductionReadinessBenchmarkReceiptBindingAudit"
    assert "external_payload_birth_matches_ok" in schema["schemas"][
        "ProductionReadinessBenchmarkRequestProvenanceAudit"
    ]["required"]
    assert "coverage_complete" in schema["schemas"][
        "ProductionReadinessBenchmarkProviderActionPlanAudit"
    ]["required"]
    assert "level_counts" in schema["schemas"]["ProductionReadinessBenchmarkTopicConfidenceAudit"]["required"]
    assert "sha256" in schema["schemas"]["ProductionReadinessCapabilityAuditReceiptSummary"]["required"]
    assert "command_fingerprint_status" in schema["schemas"]["ProductionReadinessProviderLedgerSummary"]["required"]
    assert "checked_domains" in schema["schemas"]["ProductionReadinessProviderDriftSummary"]["required"]
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["evidence_materialization"]["$ref"] == (
        "#/schemas/ProductionReadinessEvidenceMaterializationSummary"
    )
    assert "failed_count" in schema["schemas"]["ProductionReadinessEvidenceMaterializationSummary"]["required"]
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["outcome_dataset"]["$ref"] == (
        "#/schemas/OutcomeDatasetReceiptMaterial"
    )
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["readiness_receipt"]["$ref"] == (
        "#/schemas/ProductionReadinessReceipt"
    )
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["release_manifest_receipt"]["$ref"] == (
        "#/schemas/ReleaseManifestReceipt"
    )
    assert "github_comparison_receipt" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "github_comparison_receipt_sha256" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["github_comparison_receipt"]["$ref"] == (
        "#/schemas/GitHubComparisonReceipt"
    )
    assert "github_comparison_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "github_comparison_receipt_sha256" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["github_comparison_receipt"]["$ref"] == (
        "#/schemas/GitHubComparisonReceipt"
    )
    assert "plan_compliance_receipt" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "plan_compliance_receipt_sha256" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["plan_compliance_receipt"]["$ref"] == (
        "#/schemas/PlanComplianceReceipt"
    )
    assert "plan_compliance_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "plan_compliance_receipt_sha256" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["plan_compliance_receipt"]["$ref"] == (
        "#/schemas/PlanComplianceReceipt"
    )
    assert "evolution_trigger_receipt_sha256" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "evolution_trigger_receipt" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "evolution_trigger_receipt_current" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["evolution_trigger_receipt"]["anyOf"][0][
        "$ref"
    ] == "#/schemas/EvolutionTriggerReceipt"
    assert "evolution_trigger_receipt_sha256" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "evolution_trigger_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "evolution_trigger_receipt_current" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["evolution_trigger_receipt"]["anyOf"][0][
        "$ref"
    ] == "#/schemas/EvolutionTriggerReceipt"
    assert "release_approval_ready" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "release_approval_status" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "release_blockers" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["release_blockers"]["items"]["$ref"] == (
        "#/schemas/ProductionBlocker"
    )
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["release_blockers"]["items"]["$ref"] == (
        "#/schemas/ProductionBlocker"
    )
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["blockers"]["items"]["$ref"] == (
        "#/schemas/ProductionBlocker"
    )
    assert schema["schemas"]["ProductionBlocker"]["required"] == ["gate", "reason", "details"]
    assert schema["schemas"]["ProviderExampleSmokeResponse"]["properties"]["example_provider_receipt"]["$ref"] == (
        "#/schemas/ProviderCertificationReceipt"
    )
    assert schema["schemas"]["ProviderOnboardingResponse"]["properties"]["provider_onboarding_receipt"]["$ref"] == (
        "#/schemas/ProviderOnboardingReceipt"
    )
    assert schema["schemas"]["ProviderOnboardingReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ProviderOnboardingReceiptMaterial"
    )
    assert "missing_evidence_by_domain" in schema["schemas"]["ProviderOnboardingReceiptMaterial"]["required"]
    assert "missing_evidence_counts" in schema["schemas"]["ProviderOnboardingReceiptMaterial"]["required"]
    assert schema["schemas"]["ProviderProtocolsResponse"]["properties"]["provider_protocols_receipt"]["$ref"] == (
        "#/schemas/ProviderProtocolsReceipt"
    )
    assert schema["schemas"]["ProviderProtocolsReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ProviderProtocolsReceiptMaterial"
    )
    provider_domain_schema = schema["schemas"]["ProviderDomainStatus"]
    assert "external_payload_birth_match_status" in provider_domain_schema["required"]
    assert "external_payload_birth_mismatch_fields" in provider_domain_schema["required"]
    assert "external_payload_declared_birth_profile_sha256" in provider_domain_schema["required"]
    assert provider_domain_schema["properties"]["external_payload_birth_mismatch_fields"]["items"]["type"] == "string"
    assert schema["schemas"]["BenchmarkResult"]["properties"]["cases"]["items"]["$ref"] == "#/schemas/BenchmarkCaseResult"
    assert schema["schemas"]["BenchmarkCaseResult"]["properties"]["report_features"]["$ref"] == (
        "#/schemas/BenchmarkCaseReportFeatures"
    )
    benchmark_features = schema["schemas"]["BenchmarkCaseReportFeatures"]["properties"]
    assert benchmark_features["chinese_render_duplicate_bullet_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_topic_evidence_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_topic_judgment_structure_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_annual_pillar_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_monthly_pillar_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_annual_ten_god_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_monthly_ten_god_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_annual_useful_state_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_monthly_useful_state_anchor_ratio"]["type"] == "number"
    assert benchmark_features["chinese_render_ascii_letter_count"]["type"] == "integer"
    assert benchmark_features["chinese_render_ascii_question_present"]["type"] == "boolean"
    assert benchmark_features["chinese_render_code_marker_present"]["type"] == "boolean"
    assert "external_payload_birth_match_statuses" in benchmark_features
    assert benchmark_features["external_payload_birth_match_statuses"]["items"]["$ref"] == (
        "#/schemas/BenchmarkExternalPayloadBirthMatchStatus"
    )
    assert "domain" in schema["schemas"]["BenchmarkExternalPayloadBirthMatchStatus"]["required"]
    assert "external_payload_birth_matches_ok" in benchmark_features
    provider_domain = schema["schemas"]["ProviderDomainStatus"]
    provider_summary = schema["schemas"]["ProviderSummary"]
    assert schema["schemas"]["ProviderChecksResponse"]["properties"]["profile_readiness"]["$ref"] == (
        "#/schemas/ProviderProfileReadiness"
    )
    assert "production_guidance" in schema["schemas"]["ProviderChecksResponse"]["required"]
    assert schema["schemas"]["ProviderChecksResponse"]["properties"]["production_guidance"]["$ref"] == (
        "#/schemas/ProviderProductionGuidance"
    )
    production_guidance_schema = schema["schemas"]["ProviderProductionGuidance"]
    assert "certification_commands" in production_guidance_schema["required"]
    assert "required_provenance_env_vars" in production_guidance_schema["required"]
    assert "production_readiness_command" in production_guidance_schema["required"]
    assert "policy" in production_guidance_schema["required"]
    assert schema["schemas"]["ProviderChecksResponse"]["properties"]["reference_chart_checks"]["$ref"] == (
        "#/schemas/ReferenceChartChecks"
    )
    assert schema["schemas"]["ReferenceChartChecks"]["properties"]["method_coverage"]["$ref"] == (
        "#/schemas/ReferenceChartMethodCoverage"
    )
    assert schema["schemas"]["ReferenceChartChecks"]["properties"]["cases"]["items"]["$ref"] == (
        "#/schemas/ReferenceChartCaseCheck"
    )
    assert schema["schemas"]["ReferenceChartMethodCoverage"]["properties"]["domains"]["additionalProperties"][
        "$ref"
    ] == "#/schemas/ReferenceChartDomainMethodCoverage"
    assert "provenance_coverage" in schema["schemas"]["ReferenceChartCaseCheck"]["required"]
    assert "observed" in schema["schemas"]["ReferenceChartDomainMethodCoverage"]["required"]
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["provider_readiness"]["$ref"] == (
        "#/schemas/ProviderProfileReadiness"
    )
    assert schema["schemas"]["ProviderProfileReadiness"]["properties"]["required_groups"]["items"]["$ref"] == (
        "#/schemas/ProviderProfileRequiredGroup"
    )
    assert "live_required" in schema["schemas"]["ProviderProfileReadiness"]["required"]
    assert "accepted_checks" in schema["schemas"]["ProviderProfileRequiredGroup"]["required"]
    assert schema["schemas"]["ProviderReadinessCheck"]["properties"]["provider_command_fingerprint"]["$ref"] == (
        "#/schemas/ProviderCommandFingerprint"
    )
    assert schema["schemas"]["ProviderCertificationResponse"]["properties"]["provider_command_fingerprint"]["$ref"] == (
        "#/schemas/ProviderCommandFingerprint"
    )
    assert schema["schemas"]["ProviderCertificationResponse"]["properties"]["reference_contract_coverage"]["$ref"] == (
        "#/schemas/ProviderReferenceContractCoverage"
    )
    assert "resolution_guidance" in schema["schemas"]["ProviderCertificationResponse"]["required"]
    assert schema["schemas"]["ProviderCertificationResponse"]["properties"]["resolution_guidance"]["$ref"] == (
        "#/schemas/ProviderCertificationResolutionGuidance"
    )
    certification_guidance_schema = schema["schemas"]["ProviderCertificationResolutionGuidance"]
    assert "ledger_record_blocker" in certification_guidance_schema["required"]
    assert "recertification_command" in certification_guidance_schema["required"]
    assert "record_policy" in certification_guidance_schema["required"]
    material_anyof = schema["schemas"]["ProviderCertificationReceipt"]["properties"]["material"]["anyOf"]
    material_refs = {item["$ref"] for item in material_anyof if "$ref" in item}
    assert "#/schemas/ProviderCertificationReceiptMaterial" in material_refs
    assert "#/schemas/BenchmarkReceiptMaterial" in material_refs
    assert schema["schemas"]["ProviderCertificationReceiptMaterial"]["properties"]["provider_command_fingerprint"][
        "$ref"
    ] == "#/schemas/ProviderCommandFingerprint"
    assert schema["schemas"]["ProviderCertificationReceiptMaterial"]["properties"]["reference_contract_coverage"][
        "$ref"
    ] == "#/schemas/ProviderReferenceContractCoverage"
    raw_contract_anyof = schema["schemas"]["ProviderCertificationReceiptMaterial"]["properties"][
        "raw_contract_receipt"
    ]["anyOf"]
    assert "#/schemas/ProviderRawContractReceipt" in {item["$ref"] for item in raw_contract_anyof if "$ref" in item}
    assert schema["schemas"]["ProviderRawContractReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ProviderRawContractReceiptMaterial"
    )
    assert "provider_request_receipt_sha256" in schema["schemas"]["ProviderRawContractReceiptMaterial"]["required"]
    assert "stdout_sha256" in schema["schemas"]["ProviderRawContractReceiptMaterial"]["required"]
    assert schema["schemas"]["ProviderRequestReceipt"]["properties"]["protocol"]["$ref"] == (
        "#/schemas/ProviderRequestProtocolIdentity"
    )
    assert schema["schemas"]["ProviderRequestReceipt"]["properties"]["schema_version"]["const"] == (
        "provider-request-receipt-v1"
    )
    assert "hash" in schema["schemas"]["ProviderRequestProtocolIdentity"]["required"]
    assert schema["schemas"]["BenchmarkReceiptMaterial"]["properties"]["cases"]["items"]["$ref"] == (
        "#/schemas/BenchmarkReceiptCaseSummary"
    )
    assert "coverage_sha256" in schema["schemas"]["ProviderReferenceContractCoverage"]["required"]
    assert "provider_request_receipt" in schema["schemas"]["ProviderCertificationReceiptMaterial"]["required"]
    assert "raw_contract_receipt" in schema["schemas"]["ProviderCertificationReceiptMaterial"]["required"]
    assert "reference_charts" in schema["schemas"]["BenchmarkReceiptMaterial"]["required"]
    assert "command_sha256" in schema["schemas"]["ProviderCommandFingerprint"]["required"]
    assert "artifact_sha256" in schema["schemas"]["ProviderCommandFingerprint"]["required"]
    assert "interpretation_mode" in provider_domain["required"]
    assert "confidence_level" in provider_domain["required"]
    assert "blocking_reasons" in provider_domain["required"]
    assert "readiness_matrix" in provider_summary["required"]
    assert provider_summary["properties"]["readiness_matrix"]["items"]["$ref"] == "#/schemas/ProviderReadinessMatrixItem"
    readiness_matrix_item = schema["schemas"]["ProviderReadinessMatrixItem"]
    assert "interpretation_mode" in readiness_matrix_item["required"]
    assert "confidence_level" in readiness_matrix_item["required"]
    assert readiness_matrix_item["properties"]["blocking_reasons"]["items"]["type"] == "string"
    assert "professional_domain_count" in provider_summary["required"]
    assert "fallback_domain_count" in provider_summary["required"]
    topic_item = schema["schemas"]["TopicSynthesisItem"]
    topic_confidence = schema["schemas"]["TopicSynthesisConfidence"]
    assert "synthesis_confidence" in topic_item["required"]
    assert topic_item["properties"]["synthesis_confidence"]["$ref"] == "#/schemas/TopicSynthesisConfidence"
    assert topic_item["properties"]["cross_agent_evidence"]["items"]["$ref"] == (
        "#/schemas/TopicSynthesisCrossAgentEvidence"
    )
    assert topic_item["properties"]["annual_focus"]["$ref"] == "#/schemas/TopicSynthesisAnnualFocus"
    assert topic_item["properties"]["monthly_focus"]["$ref"] == "#/schemas/TopicSynthesisMonthlyFocus"
    assert topic_item["properties"]["timing_evidence"]["$ref"] == "#/schemas/TopicSynthesisTimingEvidence"
    assert schema["schemas"]["TopicSynthesisAnnualFocus"]["properties"]["bazi_evidence"]["$ref"] == (
        "#/schemas/AnnualLuckBaziEvidence"
    )
    assert schema["schemas"]["TopicSynthesisMonthlyFocus"]["properties"]["bazi_evidence"]["$ref"] == (
        "#/schemas/MonthlyLuckBaziEvidence"
    )
    assert schema["schemas"]["TopicSynthesisTimingEvidence"]["properties"]["annual"]["$ref"] == (
        "#/schemas/TopicSynthesisTimingSignal"
    )
    assert schema["schemas"]["TopicSynthesisTimingSignal"]["properties"]["ten_gods"]["$ref"] == (
        "#/schemas/AnnualLuckTenGodPair"
    )
    assert "risk_notes" in schema["schemas"]["TopicSynthesisAnnualFocus"]["required"]
    assert "month" in schema["schemas"]["TopicSynthesisMonthlyFocus"]["required"]
    assert "annual" in schema["schemas"]["TopicSynthesisTimingEvidence"]["required"]
    assert "natal_match_count" in schema["schemas"]["TopicSynthesisTimingSignal"]["required"]
    assert "support" in schema["schemas"]["TopicSynthesisCrossAgentEvidence"]["required"]
    assert "downgrade_reasons" in topic_confidence["required"]
    assert "fallback_provider_count" in topic_confidence["required"]
    benchmark_features = schema["schemas"]["BenchmarkCaseReportFeatures"]["properties"]
    assert "topic_confidence_summary" in benchmark_features
    assert "topic_confidence_boundaries_ok" in benchmark_features
    assert "topic_confidence_missing_topics" in benchmark_features
    assert "topic_confidence_levels" in benchmark_features
    assert schema["schemas"]["ReleaseManifestReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ReleaseManifestReceiptMaterial"
    )
    assert schema["schemas"]["ReleaseManifestResponse"]["properties"]["release_gate_checks"]["$ref"] == (
        "#/schemas/ReleaseManifestGateChecks"
    )
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["release_gate_checks"]["$ref"] == (
        "#/schemas/ReleaseManifestGateChecks"
    )
    assert "outcome_dataset_split_coverage_bound" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "provider_onboarding_receipt_current" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "provider_protocols_receipt_current" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "provider_audit_contract_gates_bound" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert (
        "outcome_statistical_plan_preregistration_bound"
        in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    )
    assert "classical_latest_refresh_receipt_bound" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "blocked_capability_coverage_bound" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "known_gap_handoff_bundle_bound" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert "known_gap_command_coverage_bound" in schema["schemas"]["ReleaseManifestGateChecks"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["outcome_dataset"]["$ref"] == (
        "#/schemas/OutcomeDatasetReceiptMaterial"
    )
    assert (
        schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
            "auspicious_calendar"
        ]["$ref"]
        == "#/schemas/AuspiciousCalendar"
    )
    assert schema["schemas"]["AuspiciousCalendar"]["properties"]["range"]["$ref"] == (
        "#/schemas/AuspiciousCalendarRange"
    )
    assert schema["schemas"]["AuspiciousCalendar"]["properties"]["basis"]["$ref"] == (
        "#/schemas/AuspiciousCalendarBasis"
    )
    assert schema["schemas"]["AuspiciousCalendar"]["properties"]["rows"]["items"]["$ref"] == (
        "#/schemas/AuspiciousDayRow"
    )
    assert schema["schemas"]["AuspiciousCalendar"]["properties"]["method_matrix"]["items"]["$ref"] == (
        "#/schemas/AuspiciousMethodMatrixItem"
    )
    assert "auspicious_calendar_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert (
        schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
            "auspicious_calendar_receipt"
        ]["$ref"]
        == "#/schemas/AuspiciousCalendarReceipt"
    )
    assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/AuspiciousCalendarReceiptRowFingerprint"
    )
    assert "calendar_rows_sha256" in schema["schemas"]["AuspiciousCalendarReceipt"]["required"]
    assert "method_layers_sha256" in schema["schemas"]["AuspiciousCalendarReceipt"]["required"]
    assert "twelve_officer_analysis" in schema["schemas"]["AuspiciousCalendar"]["required"]
    assert "huangdao_analysis" in schema["schemas"]["AuspiciousCalendar"]["required"]
    assert "provider_quality_analysis" in schema["schemas"]["AuspiciousCalendar"]["required"]
    assert "twelve_officer" in schema["schemas"]["AuspiciousDayRow"]["required"]
    assert "twenty_eight_mansion" in schema["schemas"]["AuspiciousDayRow"]["required"]
    assert "recommended_hours" in schema["schemas"]["AuspiciousDayRow"]["required"]
    assert schema["schemas"]["AuspiciousDayRow"]["properties"]["recommended_hours"]["items"]["$ref"] == (
        "#/schemas/AuspiciousRecommendedHour"
    )
    assert "start" in schema["schemas"]["AuspiciousRecommendedHour"]["required"]
    assert "end" in schema["schemas"]["AuspiciousRecommendedHour"]["required"]
    assert "evidence_fields" in schema["schemas"]["AuspiciousMethodMatrixItem"]["required"]
    assert "readiness_deliberation_receipt_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "annual_timeline_receipt_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    annual_timeline_coverage_schema = schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "annual_timeline_receipt_coverage"
    ]
    assert "binding_complete" in annual_timeline_coverage_schema["required"]
    assert "receipt_sha256s" in annual_timeline_coverage_schema["required"]
    assert "monthly_luck_receipt_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    monthly_luck_coverage_schema = schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "monthly_luck_receipt_coverage"
    ]
    assert "binding_complete" in monthly_luck_coverage_schema["required"]
    assert "receipt_sha256s" in monthly_luck_coverage_schema["required"]
    assert "auspicious_calendar_receipt_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    auspicious_calendar_coverage_schema = schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "auspicious_calendar_receipt_coverage"
    ]
    assert "binding_complete" in auspicious_calendar_coverage_schema["required"]
    assert "receipt_sha256s" in auspicious_calendar_coverage_schema["required"]
    assert "provider_action_plan_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "classical_source_receipt_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert (
        "source_list_receipt_sha256"
        in schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["classical_source_receipt_coverage"][
            "required"
        ]
    )
    assert (
        "latest_refresh_receipt_sha256"
        in schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["classical_source_receipt_coverage"][
            "required"
        ]
    )
    assert (
        "refresh_receipt_present"
        in schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["classical_source_receipt_coverage"][
            "required"
        ]
    )
    assert "source_receipt" in schema["schemas"]["PlanCompliance"]["required"]
    assert "sha256" in schema["schemas"]["PlanCompliance"]["properties"]["source_receipt"]["required"]
    assert "section_gap_resolution_coverage" in schema["schemas"]["PlanCompliance"]["required"]
    assert schema["schemas"]["PlanCompliance"]["properties"]["section_gap_resolution_coverage"]["$ref"] == (
        "#/schemas/PlanSectionGapResolutionCoverage"
    )
    assert "plan_compliance_receipt" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["plan_compliance_receipt"]["$ref"] == (
        "#/schemas/PlanComplianceReceipt"
    )
    assert schema["schemas"]["PlanComplianceReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/PlanComplianceReceiptMaterial"
    )
    assert "matrix_sha256" in schema["schemas"]["PlanComplianceReceiptMaterial"]["required"]
    assert "section_gap_resolution_coverage_sha256" in schema["schemas"]["PlanComplianceReceiptMaterial"]["required"]
    assert "sections_with_unplanned_gaps" in schema["schemas"]["PlanSectionGapResolutionCoverage"]["required"]
    assert "all_gaps_planned" in schema["schemas"]["PlanSectionGapResolution"]["required"]
    assert "classical_source_list_path" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert "classical_source_refresh" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert "method_surface" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["method_surface"]["$ref"] == (
        "#/schemas/MethodSurfaceReceiptSummary"
    )
    assert "method_lineage" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["method_lineage"]["$ref"] == (
        "#/schemas/MethodLineageReceiptSummary"
    )
    assert schema["schemas"]["MethodLineageReceiptSummary"]["properties"]["sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert "famous_case_validation" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["famous_case_validation"]["$ref"] == (
        "#/schemas/FamousCaseValidationReceiptSummary"
    )
    assert schema["schemas"]["FamousCaseValidationReceiptSummary"]["properties"]["sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert schema["schemas"]["FamousCaseValidationReceiptSummary"]["properties"]["schema_version"]["const"] == (
        "mingli-famous-case-validation-v2"
    )
    assert "birth_source_quality" in schema["schemas"]["FamousCaseValidationReceiptSummary"]["required"]
    assert schema["schemas"]["FamousCaseValidationReceiptSummary"]["properties"]["birth_source_quality"]["type"] == (
        "object"
    )
    assert "famous_case_school_calibration" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["famous_case_school_calibration"]["$ref"] == (
        "#/schemas/FamousCaseSchoolCalibrationReceiptSummary"
    )
    assert schema["schemas"]["FamousCaseSchoolCalibrationReceiptSummary"]["properties"]["sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert schema["schemas"]["FamousCaseSchoolCalibrationReceiptSummary"]["properties"]["fixture_sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert schema["schemas"]["FamousCaseSchoolCalibrationReceiptSummary"]["properties"]["schema_version"]["const"] == (
        "mingli-famous-case-school-calibration-v1"
    )
    assert "famous_case_annual_event_calibration" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["famous_case_annual_event_calibration"]["$ref"] == (
        "#/schemas/FamousCaseAnnualEventCalibrationReceiptSummary"
    )
    assert schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["properties"]["sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert "birth_source_quality_summary" in schema["schemas"][
        "FamousCaseAnnualEventCalibrationReceiptSummary"
    ]["required"]
    assert schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["properties"][
        "birth_source_quality_summary"
    ]["type"] == "object"
    assert "source_review_routing_summary" in schema["schemas"][
        "FamousCaseAnnualEventCalibrationReceiptSummary"
    ]["required"]
    assert schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["properties"][
        "source_review_routing_summary"
    ]["type"] == "object"
    assert schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["properties"]["fixture_sha256"][
        "pattern"
    ] == "^[0-9a-f]{64}$"
    assert schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["properties"]["schema_version"][
        "const"
    ] == "mingli-famous-case-annual-event-calibration-v1"
    assert "negative_year_count" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "false_positive_count" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "exact_precision" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "false_positive_rate" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "strict_exact_hit_count" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "strict_false_positive_count" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "strict_exact_precision" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "strict_false_positive_rate" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "topic_summary" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "event_subtype_summary" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "rule_variant_sweep" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "rule_refinement_queue" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "evolution_task_plan" in schema["schemas"]["FamousCaseAnnualEventCalibrationReceiptSummary"]["required"]
    assert "provider_example_smoke" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["provider_example_smoke"]["$ref"] == (
        "#/schemas/ProviderExampleSmokeResponse"
    )
    assert "provider_onboarding" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["provider_onboarding"]["$ref"] == (
        "#/schemas/ProviderOnboardingResponse"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["capabilities"]["$ref"] == (
        "#/schemas/CapabilityFlagMap"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["request_scoped_provider_contract"]["$ref"] == (
        "#/schemas/RequestScopedProviderContractSummary"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["provider_protocol_governance"]["$ref"] == (
        "#/schemas/ProviderProtocolGovernanceSummary"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["audit_receipt"]["$ref"] == (
        "#/schemas/CapabilityAuditReceipt"
    )
    assert schema["schemas"]["CapabilityAuditReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/CapabilityAuditReceiptMaterial"
    )
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["provider_onboarding"]["$ref"] == (
        "#/schemas/ProviderOnboardingAuditSummary"
    )
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["provider_production_guidance"]["$ref"] == (
        "#/schemas/ProviderProductionGuidance"
    )
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["capabilities"]["$ref"] == (
        "#/schemas/CapabilityFlagMap"
    )
    assert "famous_case_validation" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["famous_case_validation"]["$ref"] == (
        "#/schemas/FamousCaseValidationReceiptSummary"
    )
    assert "famous_case_school_calibration" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["famous_case_school_calibration"]["$ref"] == (
        "#/schemas/FamousCaseSchoolCalibrationReceiptSummary"
    )
    assert "famous_case_annual_event_calibration" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["famous_case_annual_event_calibration"][
        "$ref"
    ] == "#/schemas/FamousCaseAnnualEventCalibrationReceiptSummary"
    assert "industry_event_cross_domain_fixture_import" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"][
        "industry_event_cross_domain_fixture_import"
    ]["$ref"] == "#/schemas/IndustryEventCrossDomainFixtureImportReceipt"
    assert "industry_event_cross_domain_fixture_import" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"][
        "industry_event_cross_domain_fixture_import"
    ]["$ref"] == "#/schemas/IndustryEventCrossDomainFixtureImportReceipt"
    assert schema["schemas"]["IndustryEventCrossDomainFixtureImportReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/IndustryEventCrossDomainFixtureImportMaterial"
    )
    assert schema["schemas"]["IndustryEventCrossDomainFixtureImportReceipt"]["properties"]["sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    fixture_material = schema["schemas"]["IndustryEventCrossDomainFixtureImportMaterial"]
    assert fixture_material["properties"]["schema_version"]["const"] == (
        "industry-event-cross-domain-fixture-import-receipt-v1"
    )
    assert "candidate_count" in fixture_material["required"]
    assert "positive_record_count" in fixture_material["required"]
    assert "negative_record_count" in fixture_material["required"]
    assert "cross_domain_coverage_gate_passed" in fixture_material["required"]
    assert "symbolic_scoring_readiness_summary" in fixture_material["required"]
    readiness_schema = fixture_material["properties"]["symbolic_scoring_readiness_summary"]
    assert "ready_label_count" in readiness_schema["required"]
    assert "missing_birth_profile_case_ids" in readiness_schema["required"]
    assert "birth_profile_completion_task_plan" in readiness_schema["required"]
    assert "birth_profile_completion_workplan_summary" in readiness_schema["required"]
    assert "birth_profile_review_manifest_summary" in readiness_schema["required"]
    assert "birth_profile_source_review_workplan_summary" in readiness_schema["required"]
    assert "birth_profile_source_lookup_plan_summary" in readiness_schema["required"]
    assert "birth_profile_source_cache_template_preview_summary" in readiness_schema["required"]
    assert "birth_profile_source_family_cache_enforcement_summary" in readiness_schema["required"]
    assert "birth_profile_substantive_evidence_cache_enforcement_summary" in readiness_schema["required"]
    assert "birth_profile_source_cache_audit_summary" in readiness_schema["required"]
    assert "birth_profile_reviewed_manifest_draft_preview_summary" in readiness_schema["required"]
    assert "birth_profile_reviewed_manifest_file_preview_summary" in readiness_schema["required"]
    assert "birth_profile_import_preview_summary" in readiness_schema["required"]
    assert "birth_profile_fixture_patch_preview_summary" in readiness_schema["required"]
    assert "symbolic_annual_score_receipt_sha256" in readiness_schema["required"]
    assert "evidence_workplan_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_review_manifest_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_source_review_workplan_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_source_lookup_plan_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_source_cache_template_preview_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_source_cache_audit_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_reviewed_manifest_draft_preview_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_reviewed_manifest_file_preview_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_import_preview_receipt_sha256" in readiness_schema["required"]
    assert "birth_profile_fixture_patch_preview_receipt_sha256" in readiness_schema["required"]
    task_plan_schema = readiness_schema["properties"]["birth_profile_completion_task_plan"]["items"]
    assert "blocked_case_ids" in task_plan_schema["required"]
    assert "acceptance_criteria" in task_plan_schema["required"]
    assert task_plan_schema["properties"]["blocked_label_count"]["type"] == "integer"
    workplan_summary_schema = readiness_schema["properties"]["birth_profile_completion_workplan_summary"]
    assert "deferred_task_summaries" in workplan_summary_schema["required"]
    assert "readiness_status" in workplan_summary_schema["required"]
    deferred_task_schema = workplan_summary_schema["properties"]["deferred_task_summaries"]["items"]
    assert "local_birth_profile_suggestion_case_ids" in deferred_task_schema["required"]
    assert "completion_work_order_status" in deferred_task_schema["required"]
    assert deferred_task_schema["properties"]["blocked_gate_count"]["type"] == "integer"
    review_manifest_schema = readiness_schema["properties"]["birth_profile_review_manifest_summary"]
    assert "request_count" in review_manifest_schema["required"]
    assert "ready_for_import" in review_manifest_schema["required"]
    assert review_manifest_schema["properties"]["blocked_label_count"]["type"] == "integer"
    source_workplan_summary_schema = readiness_schema["properties"]["birth_profile_source_review_workplan_summary"]
    assert "would_fetch_live_sources" in source_workplan_summary_schema["required"]
    assert "would_write_review_manifest" in source_workplan_summary_schema["required"]
    assert "review_progress_summary" in source_workplan_summary_schema["required"]
    assert "field_gap_summary" in source_workplan_summary_schema["required"]
    assert "source_review_gate_passed" in source_workplan_summary_schema["required"]
    assert source_workplan_summary_schema["properties"]["work_item_count"]["type"] == "integer"
    assert source_workplan_summary_schema["properties"]["review_progress_summary"]["type"] == "object"
    assert source_workplan_summary_schema["properties"]["field_gap_summary"]["type"] == "object"
    source_lookup_summary_schema = readiness_schema["properties"]["birth_profile_source_lookup_plan_summary"]
    assert "would_fetch_live_sources" in source_lookup_summary_schema["required"]
    assert "would_write_cache" in source_lookup_summary_schema["required"]
    assert "lookup_gate_passed" in source_lookup_summary_schema["required"]
    assert "source_family_count" in source_lookup_summary_schema["required"]
    assert "source_family_catalog_bound" in source_lookup_summary_schema["required"]
    assert "birth_time_source_policy_bound" in source_lookup_summary_schema["required"]
    assert "identity_anchor_birth_time_disallowed" in source_lookup_summary_schema["required"]
    assert source_lookup_summary_schema["properties"]["query_count"]["type"] == "integer"
    assert source_lookup_summary_schema["properties"]["source_family_count"]["type"] == "integer"
    assert source_lookup_summary_schema["properties"]["source_family_catalog_bound"]["type"] == "boolean"
    assert source_lookup_summary_schema["properties"]["birth_time_source_policy_bound"]["type"] == "boolean"
    assert source_lookup_summary_schema["properties"]["identity_anchor_birth_time_disallowed"]["type"] == "boolean"
    source_template_summary_schema = readiness_schema["properties"][
        "birth_profile_source_cache_template_preview_summary"
    ]
    assert "would_fetch_live_sources" in source_template_summary_schema["required"]
    assert "would_write_cache" in source_template_summary_schema["required"]
    assert "would_import_profiles" in source_template_summary_schema["required"]
    assert "template_count" in source_template_summary_schema["required"]
    assert "template_preview_gate_passed" in source_template_summary_schema["required"]
    assert source_template_summary_schema["properties"]["template_count"]["type"] == "integer"
    family_probe_schema = readiness_schema["properties"]["birth_profile_source_family_cache_enforcement_summary"]
    assert "probe_executed" in family_probe_schema["required"]
    assert "identity_anchor_birth_time_rejected" in family_probe_schema["required"]
    assert "accepted_cache_count_after_probe" in family_probe_schema["required"]
    assert "failure_contains_birth_time_policy" in family_probe_schema["required"]
    assert family_probe_schema["properties"]["identity_anchor_birth_time_rejected"]["type"] == "boolean"
    substantive_probe_schema = readiness_schema["properties"][
        "birth_profile_substantive_evidence_cache_enforcement_summary"
    ]
    assert "probe_executed" in substantive_probe_schema["required"]
    assert "metadata_only_reviewed_cache_rejected" in substantive_probe_schema["required"]
    assert "accepted_cache_count_after_probe" in substantive_probe_schema["required"]
    assert "failure_contains_substantive_birth_policy" in substantive_probe_schema["required"]
    assert substantive_probe_schema["properties"]["metadata_only_reviewed_cache_rejected"]["type"] == "boolean"
    assert substantive_probe_schema["properties"]["failure_contains_substantive_birth_policy"]["type"] == "boolean"
    source_cache_summary_schema = readiness_schema["properties"]["birth_profile_source_cache_audit_summary"]
    assert "would_fetch_live_sources" in source_cache_summary_schema["required"]
    assert "would_write_cache" in source_cache_summary_schema["required"]
    assert "would_import_profiles" in source_cache_summary_schema["required"]
    assert "cache_audit_gate_passed" in source_cache_summary_schema["required"]
    assert source_cache_summary_schema["properties"]["expected_cache_count"]["type"] == "integer"
    reviewed_draft_summary_schema = readiness_schema["properties"][
        "birth_profile_reviewed_manifest_draft_preview_summary"
    ]
    assert "would_write_review_manifest" in reviewed_draft_summary_schema["required"]
    assert "would_import_profiles" in reviewed_draft_summary_schema["required"]
    assert "draft_ready_for_human_approval" in reviewed_draft_summary_schema["required"]
    assert "draft_gate_passed" in reviewed_draft_summary_schema["required"]
    assert reviewed_draft_summary_schema["properties"]["review_request_count"]["type"] == "integer"
    reviewed_file_summary_schema = readiness_schema["properties"][
        "birth_profile_reviewed_manifest_file_preview_summary"
    ]
    assert "would_write_file" in reviewed_file_summary_schema["required"]
    assert "would_import_profiles" in reviewed_file_summary_schema["required"]
    assert "write_ready_for_human_approval" in reviewed_file_summary_schema["required"]
    assert "target_file_sha256" in reviewed_file_summary_schema["required"]
    assert "file_preview_gate_passed" in reviewed_file_summary_schema["required"]
    assert reviewed_file_summary_schema["properties"]["target_file"]["type"] == "string"
    assert reviewed_file_summary_schema["properties"]["target_file_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    import_preview_summary_schema = readiness_schema["properties"]["birth_profile_import_preview_summary"]
    assert "would_write_file" in import_preview_summary_schema["required"]
    assert "import_allowed" in import_preview_summary_schema["required"]
    assert "import_gate_passed" in import_preview_summary_schema["required"]
    assert import_preview_summary_schema["properties"]["blocked_request_count"]["type"] == "integer"
    patch_preview_summary_schema = readiness_schema["properties"]["birth_profile_fixture_patch_preview_summary"]
    assert "would_write_file" in patch_preview_summary_schema["required"]
    assert "patch_ready_for_review" in patch_preview_summary_schema["required"]
    assert "patch_gate_passed" in patch_preview_summary_schema["required"]
    assert patch_preview_summary_schema["properties"]["candidate_count"]["type"] == "integer"
    assert patch_preview_summary_schema["properties"]["target_file_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert patch_preview_summary_schema["properties"]["patch_text_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert readiness_schema["properties"]["symbolic_scoring_readiness_receipt_sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert readiness_schema["properties"]["symbolic_annual_score_receipt_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert readiness_schema["properties"]["evidence_workplan_receipt_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert (
        readiness_schema["properties"]["birth_profile_review_manifest_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_source_review_workplan_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_source_lookup_plan_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_source_cache_template_preview_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_source_cache_audit_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_reviewed_manifest_draft_preview_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_reviewed_manifest_file_preview_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_import_preview_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert (
        readiness_schema["properties"]["birth_profile_fixture_patch_preview_receipt_sha256"]["pattern"]
        == "^[0-9a-f]{64}$"
    )
    assert "BirthProfileReviewStatusResponse" in schema["schemas"]
    birth_review_response = schema["schemas"]["BirthProfileReviewStatusResponse"]
    assert "birth_profile_review_manifest_receipt" in birth_review_response["required"]
    assert "production_gate" in birth_review_response["required"]
    assert birth_review_response["properties"]["birth_profile_review_manifest_receipt"]["properties"]["sha256"][
        "pattern"
    ] == "^[0-9a-f]{64}$"
    assert birth_review_response["properties"]["production_gate"]["properties"]["id"]["const"] == (
        "birth_profile_review_manifest_ready_for_import"
    )
    assert "BirthProfileSourceReviewWorkplanResponse" in schema["schemas"]
    source_workplan_response = schema["schemas"]["BirthProfileSourceReviewWorkplanResponse"]
    assert "source_review_workplan" in source_workplan_response["required"]
    source_workplan_schema = source_workplan_response["properties"]["source_review_workplan"]
    assert "would_fetch_live_sources" in source_workplan_schema["required"]
    assert "would_write_review_manifest" in source_workplan_schema["required"]
    assert "work_item_count" in source_workplan_schema["required"]
    assert "review_progress_summary" in source_workplan_schema["required"]
    assert "field_gap_summary" in source_workplan_schema["required"]
    assert source_workplan_schema["properties"]["review_progress_summary"]["type"] == "object"
    assert source_workplan_schema["properties"]["field_gap_summary"]["type"] == "object"
    assert source_workplan_schema["properties"]["source_review_workplan_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert source_workplan_schema["properties"]["source_review_gate"]["properties"]["id"]["const"] == (
        "birth_profile_source_review_required"
    )
    assert "BirthProfileSourceLookupPlanResponse" in schema["schemas"]
    source_lookup_response = schema["schemas"]["BirthProfileSourceLookupPlanResponse"]
    assert "source_lookup_plan" in source_lookup_response["required"]
    source_lookup_schema = source_lookup_response["properties"]["source_lookup_plan"]
    assert "would_fetch_live_sources" in source_lookup_schema["required"]
    assert "would_write_cache" in source_lookup_schema["required"]
    assert "would_write_review_manifest" in source_lookup_schema["required"]
    assert "source_family_catalog" in source_lookup_schema["required"]
    assert "query_count" in source_lookup_schema["required"]
    assert source_lookup_schema["properties"]["source_lookup_plan_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert source_lookup_schema["properties"]["source_family_catalog"]["properties"]["schema_version"]["const"] == (
        "birth-profile-source-family-catalog-v1"
    )
    assert (
        source_lookup_schema["properties"]["source_family_catalog"]["properties"]["source_family_catalog_receipt"][
            "properties"
        ]["schema_version"]["const"]
        == "birth-profile-source-family-catalog-receipt-v1"
    )
    assert source_lookup_schema["properties"]["lookup_gate"]["properties"]["id"]["const"] == (
        "birth_profile_source_lookup_requires_human_execution"
    )
    assert "BirthProfileSourceCacheTemplatePreviewResponse" in schema["schemas"]
    source_cache_template_response = schema["schemas"]["BirthProfileSourceCacheTemplatePreviewResponse"]
    assert "source_cache_template_preview" in source_cache_template_response["required"]
    source_cache_template_schema = source_cache_template_response["properties"]["source_cache_template_preview"]
    assert "would_write_cache" in source_cache_template_schema["required"]
    assert "would_fetch_live_sources" in source_cache_template_schema["required"]
    assert "would_import_profiles" in source_cache_template_schema["required"]
    assert "template_count" in source_cache_template_schema["required"]
    assert source_cache_template_schema["properties"]["source_cache_template_preview_sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert source_cache_template_schema["properties"]["template_preview_gate"]["properties"]["id"]["const"] == (
        "birth_profile_source_cache_template_requires_manual_fill"
    )
    assert "BirthProfileSourceCacheAuditResponse" in schema["schemas"]
    source_cache_response = schema["schemas"]["BirthProfileSourceCacheAuditResponse"]
    assert "source_cache_audit" in source_cache_response["required"]
    source_cache_schema = source_cache_response["properties"]["source_cache_audit"]
    assert "would_fetch_live_sources" in source_cache_schema["required"]
    assert "would_write_cache" in source_cache_schema["required"]
    assert "would_write_review_manifest" in source_cache_schema["required"]
    assert "would_import_profiles" in source_cache_schema["required"]
    assert "expected_cache_count" in source_cache_schema["required"]
    assert source_cache_schema["properties"]["source_cache_audit_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert source_cache_schema["properties"]["cache_audit_gate"]["properties"]["id"]["const"] == (
        "birth_profile_source_cache_requires_reviewed_manifest_draft"
    )
    assert "BirthProfileReviewedManifestDraftPreviewResponse" in schema["schemas"]
    reviewed_draft_response = schema["schemas"]["BirthProfileReviewedManifestDraftPreviewResponse"]
    assert "reviewed_manifest_draft_preview" in reviewed_draft_response["required"]
    reviewed_draft_schema = reviewed_draft_response["properties"]["reviewed_manifest_draft_preview"]
    assert "would_write_review_manifest" in reviewed_draft_schema["required"]
    assert "would_import_profiles" in reviewed_draft_schema["required"]
    assert "draft_ready_for_human_approval" in reviewed_draft_schema["required"]
    assert "draft_manifest_sha256" in reviewed_draft_schema["required"]
    assert reviewed_draft_schema["properties"]["reviewed_manifest_draft_preview_sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert reviewed_draft_schema["properties"]["draft_gate"]["properties"]["id"]["const"] == (
        "birth_profile_reviewed_manifest_draft_requires_human_approval"
    )
    assert "BirthProfileReviewedManifestFilePreviewResponse" in schema["schemas"]
    reviewed_file_response = schema["schemas"]["BirthProfileReviewedManifestFilePreviewResponse"]
    assert "reviewed_manifest_file_preview" in reviewed_file_response["required"]
    reviewed_file_schema = reviewed_file_response["properties"]["reviewed_manifest_file_preview"]
    assert "target_file" in reviewed_file_schema["required"]
    assert "would_write_file" in reviewed_file_schema["required"]
    assert "would_import_profiles" in reviewed_file_schema["required"]
    assert "write_ready_for_human_approval" in reviewed_file_schema["required"]
    assert reviewed_file_schema["properties"]["reviewed_manifest_file_preview_sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert reviewed_file_schema["properties"]["file_preview_gate"]["properties"]["id"]["const"] == (
        "birth_profile_reviewed_manifest_file_write_requires_human_approval"
    )
    assert "BirthProfileImportPreviewResponse" in schema["schemas"]
    import_preview_response = schema["schemas"]["BirthProfileImportPreviewResponse"]
    assert "import_preview" in import_preview_response["required"]
    import_preview_schema = import_preview_response["properties"]["import_preview"]
    assert "would_write_file" in import_preview_schema["required"]
    assert "import_allowed" in import_preview_schema["required"]
    assert "candidate_profiles" in import_preview_schema["required"]
    assert import_preview_schema["properties"]["import_preview_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert import_preview_schema["properties"]["candidate_profiles"]["items"]["properties"]["birth"]["required"] == [
        "birth_date",
        "birth_time",
        "gender",
        "birthplace",
    ]
    assert import_preview_schema["properties"]["import_gate"]["properties"]["id"]["const"] == (
        "birth_profile_import_reviewed_profiles_present"
    )
    assert "BirthProfileFixturePatchPreviewResponse" in schema["schemas"]
    patch_preview_response = schema["schemas"]["BirthProfileFixturePatchPreviewResponse"]
    assert "fixture_patch_preview" in patch_preview_response["required"]
    patch_preview_schema = patch_preview_response["properties"]["fixture_patch_preview"]
    assert "target_file_sha256" in patch_preview_schema["required"]
    assert "patch_text_sha256" in patch_preview_schema["required"]
    assert "would_write_file" in patch_preview_schema["required"]
    assert patch_preview_schema["properties"]["fixture_patch_preview_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert patch_preview_schema["properties"]["patch_gate"]["properties"]["id"]["const"] == (
        "birth_profile_fixture_patch_preview_ready"
    )
    assert fixture_material["properties"]["validation_label_table_receipt_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert "blocked_capability_coverage" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["blocked_capability_coverage"]["$ref"] == (
        "#/schemas/BlockedCapabilityCoverage"
    )
    assert "blocked_capability_coverage" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["blocked_capability_coverage"]["$ref"] == (
        "#/schemas/BlockedCapabilityCoverage"
    )
    assert "known_gap_handoff_bundle" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["known_gap_handoff_bundle"]["$ref"] == (
        "#/schemas/KnownGapHandoffBundle"
    )
    assert "known_gap_handoff_bundle" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["known_gap_handoff_bundle"]["$ref"] == (
        "#/schemas/KnownGapHandoffBundle"
    )
    assert schema["schemas"]["KnownGapHandoffBundle"]["properties"]["items"]["items"]["$ref"] == (
        "#/schemas/KnownGapHandoffItem"
    )
    assert "bundle_sha256" in schema["schemas"]["KnownGapHandoffBundle"]["required"]
    assert "required_env_vars" in schema["schemas"]["KnownGapHandoffItem"]["required"]
    assert "external_candidate_projects" in schema["schemas"]["KnownGapHandoffItem"]["required"]
    assert schema["schemas"]["KnownGapHandoffItem"]["properties"]["external_candidate_projects"]["items"]["$ref"] == (
        "#/schemas/KnownGapHandoffCandidate"
    )
    assert "KnownGapHandoffExportResponse" in schema["schemas"]
    assert schema["schemas"]["KnownGapHandoffExportResponse"]["properties"]["known_gap_handoff_bundle"]["$ref"] == (
        "#/schemas/KnownGapHandoffBundle"
    )
    assert schema["schemas"]["KnownGapHandoffExportResponse"]["properties"]["handoff_export_receipt"]["$ref"] == (
        "#/schemas/KnownGapHandoffExportReceipt"
    )
    assert schema["schemas"]["KnownGapHandoffExportReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/KnownGapHandoffExportReceiptMaterial"
    )
    assert "KnownGapHandoffExportVerificationResponse" in schema["schemas"]
    assert "KnownGapHandoffExportVerificationRequest" in schema["schemas"]
    assert "KnownGapHandoffChecklistRequest" in schema["schemas"]
    assert "expected_checklist_receipt_sha256" in schema["schemas"]["KnownGapHandoffChecklistRequest"]["properties"]
    assert schema["schemas"]["KnownGapHandoffExportVerificationRequest"]["properties"]["handoff_export"]["$ref"] == (
        "#/schemas/KnownGapHandoffExportResponse"
    )
    assert "valid" in schema["schemas"]["KnownGapHandoffExportVerificationResponse"]["required"]
    assert "bundle_hash_valid" in schema["schemas"]["KnownGapHandoffExportVerificationResponse"]["required"]
    assert "receipt_hash_valid" in schema["schemas"]["KnownGapHandoffExportVerificationResponse"]["required"]
    assert "KnownGapHandoffChecklistResponse" in schema["schemas"]
    assert schema["schemas"]["KnownGapHandoffChecklistResponse"]["properties"]["items"]["items"]["$ref"] == (
        "#/schemas/KnownGapHandoffChecklistItem"
    )
    assert schema["schemas"]["KnownGapHandoffChecklistResponse"]["properties"]["checklist_receipt"]["$ref"] == (
        "#/schemas/KnownGapHandoffChecklistReceipt"
    )
    assert "checklist_receipt_matches_expected" in schema["schemas"]["KnownGapHandoffChecklistResponse"]["required"]
    assert "ready_to_implement" in schema["schemas"]["KnownGapHandoffChecklistItem"]["required"]
    assert "audit_receipt_sha256" in schema["schemas"]["KnownGapHandoffExportResponse"]["required"]
    assert "bundle_sha256" in schema["schemas"]["KnownGapHandoffExportReceiptMaterial"]["required"]
    assert "GET /known-gap-handoff" in schema["endpoints"]
    assert "POST /known-gap-handoff-verify" in schema["endpoints"]
    assert "POST /known-gap-handoff-checklist" in schema["endpoints"]
    assert "coverage_complete" in schema["schemas"]["BlockedCapabilityCoverage"]["required"]
    assert "coverage_sha256" in schema["schemas"]["BlockedCapabilityCoverage"]["required"]
    assert (
        schema["schemas"]["BlockedCapabilityCoverage"]["properties"]["entries"]["items"]["$ref"]
        == "#/schemas/BlockedCapabilityCoverageEntry"
    )
    assert "classification" in schema["schemas"]["BlockedCapabilityCoverageEntry"]["required"]
    assert "unaccounted" in schema["schemas"]["BlockedCapabilityCoverageEntry"]["properties"]["classification"]["enum"]
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["request_scoped_provider_contract"]["$ref"] == (
        "#/schemas/RequestScopedProviderContractSummary"
    )
    assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["provider_protocol_governance"]["$ref"] == (
        "#/schemas/ProviderProtocolGovernanceSummary"
    )
    assert "provider_onboarding" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert "provider_production_guidance" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert "provider_protocol_governance" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert "requires_provenance_fields" in schema["schemas"]["RequestScopedProviderContractSummary"]["required"]
    assert (
        schema["schemas"]["ProviderProtocolGovernanceSummary"]["properties"]["runtime_identity_handshake"]["$ref"]
        == "#/schemas/ProviderProtocolIdentityHandshakeSummary"
    )
    assert "protocol_document_sha256" in schema["schemas"]["ProviderProtocolGovernanceSummary"]["required"]
    assert "ready" in schema["schemas"]["ProviderProtocolIdentityHandshakeSummary"]["required"]
    assert "domain_missing_evidence" in schema["schemas"]["ProviderOnboardingAuditSummary"]["required"]
    assert "missing_evidence_counts" in schema["schemas"]["ProviderOnboardingAuditSummary"]["required"]
    assert (
        schema["schemas"]["ProviderOnboardingAuditSummary"]["properties"]["missing_evidence_counts"][
            "additionalProperties"
        ]["type"]
        == "integer"
    )
    assert "provider_protocols_receipt" in schema["schemas"]["ProviderProtocolsResponse"]["required"]
    assert "protocol_document_sha256" in schema["schemas"]["ProviderProtocolsReceiptMaterial"]["required"]
    assert schema["schemas"]["MethodSurfaceReceiptSummary"]["required"] == [
        "schema_version",
        "sha256",
        "domains",
    ]
    assert schema["schemas"]["MethodSurfaceReceiptSummary"]["properties"]["schema_version"]["const"] == (
        "method-surface-v1"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["github_comparison_matrix"]["items"]["$ref"] == (
        "#/schemas/GitHubComparisonItem"
    )
    assert "github_comparison_receipt" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["github_comparison_receipt"]["$ref"] == (
        "#/schemas/GitHubComparisonReceipt"
    )
    assert schema["schemas"]["GitHubComparisonReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/GitHubComparisonReceiptMaterial"
    )
    assert "matrix_sha256" in schema["schemas"]["GitHubComparisonReceiptMaterial"]["required"]
    assert "candidate_sha256" in schema["schemas"]["GitHubComparisonReceiptMaterial"]["required"]
    assert schema["schemas"]["GitHubComparisonReceiptMaterial"]["properties"]["candidate_projects"]["items"][
        "$ref"
    ] == "#/schemas/ExternalIntegrationCandidate"
    assert "github_comparison_receipt_sha256" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert "plan_compliance_receipt_sha256" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["implemented_requirements"]["items"]["$ref"] == (
        "#/schemas/ImplementedRequirement"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["external_integration_candidates"]["items"][
        "$ref"
    ] == "#/schemas/ExternalIntegrationCandidate"
    assert "github_baseline" in schema["schemas"]["GitHubComparisonItem"]["required"]
    assert "required_to_lead" in schema["schemas"]["GitHubComparisonItem"]["required"]
    assert "audit_note" in schema["schemas"]["ExternalIntegrationCandidate"]["required"]
    assert "evidence" in schema["schemas"]["ImplementedRequirement"]["required"]
    assert "known_gap_resolution_plan" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["known_gap_resolution_plan"]["items"]["$ref"] == (
        "#/schemas/KnownGapResolutionPlanItem"
    )
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["known_gaps"]["items"]["$ref"] == (
        "#/schemas/KnownGapItem"
    )
    assert "known_gap_resolution_plan_coverage" in schema["schemas"]["CapabilityAuditResponse"]["required"]
    assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["known_gap_resolution_plan_coverage"]["$ref"] == (
        "#/schemas/KnownGapResolutionPlanCoverage"
    )
    assert "owner_domain" in schema["schemas"]["KnownGapItem"]["required"]
    assert "blocking_scope" in schema["schemas"]["KnownGapItem"]["required"]
    assert "verification_commands" in schema["schemas"]["KnownGapItem"]["required"]
    assert "production_gate_ids" in schema["schemas"]["KnownGapItem"]["required"]
    assert "planned_gap_ids" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "id" in schema["schemas"]["KnownGapResolutionPlanItem"]["required"]
    assert "gap_id" in schema["schemas"]["KnownGapResolutionPlanItem"]["required"]
    assert "verification_commands" in schema["schemas"]["KnownGapResolutionPlanItem"]["required"]
    assert "production_gate_ids" in schema["schemas"]["KnownGapResolutionPlanItem"]["required"]
    assert "classical_source_refresh" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert "classical_refresh_receipt" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert (
        schema["schemas"]["ProductionReadinessResponse"]["properties"]["classical_refresh_receipt"]["anyOf"][0]["$ref"]
        == "#/schemas/ClassicalRefreshReceipt"
    )
    assert "known_gap_resolution_plan" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert "production_gate_registry_audit" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    registry_audit_schema = schema["schemas"]["ProductionGateRegistryAudit"]
    assert "registry_current" in registry_audit_schema["required"]
    assert "missing_from_registry" in registry_audit_schema["required"]
    assert "registry_audit_sha256" in registry_audit_schema["required"]
    assert "classical_source_list_path" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert "benchmark_analyze_response_schema" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["benchmark_analyze_response_schema"][
        "$ref"
    ] == "#/schemas/ProductionReadinessAnalyzeResponseSchemaAudit"
    analyze_schema_audit = schema["schemas"]["ProductionReadinessAnalyzeResponseSchemaAudit"]
    assert analyze_schema_audit["properties"]["schema_name"]["const"] == "AnalyzeResponse"
    assert "invalid_cases" in analyze_schema_audit["required"]
    benchmark_summary_schema = schema["schemas"]["ProductionReadinessBenchmarkSummary"]
    assert "analyze_response_schema_audit" in benchmark_summary_schema["required"]
    assert benchmark_summary_schema["properties"]["analyze_response_schema_audit"]["$ref"] == (
        "#/schemas/ProductionReadinessAnalyzeResponseSchemaReceiptSummary"
    )
    assert "classical_source_refresh" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert "known_gap_resolution_plan_coverage" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert "known_gap_handoff_bundle" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["known_gap_handoff_bundle"]["$ref"] == (
        "#/schemas/KnownGapHandoffBundle"
    )
    assert "known_gap_handoff_bundle" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["known_gap_handoff_bundle"]["$ref"] == (
        "#/schemas/KnownGapHandoffBundle"
    )
    assert "known_gap_handoff_bundle" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["known_gap_handoff_bundle"]["$ref"] == (
        "#/schemas/KnownGapHandoffBundle"
    )
    assert "production_resolution_plan_summary" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert "production_gate_registry_audit" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["production_gate_registry_audit"][
        "$ref"
    ] == "#/schemas/ProductionGateRegistryAudit"
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["known_gap_resolution_plan_coverage"][
        "$ref"
    ] == "#/schemas/KnownGapResolutionPlanCoverage"
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["production_resolution_plan_summary"][
        "$ref"
    ] == "#/schemas/ProductionResolutionPlanSummary"
    assert "known_gap_resolution_plan_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "production_gate_registry_audit" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_protocols_receipt_sha256" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_protocols_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_onboarding_receipt_sha256" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "provider_onboarding_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "method_surface" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["method_surface"]["$ref"] == (
        "#/schemas/MethodSurfaceReceiptSummary"
    )
    assert "production_resolution_plan_summary" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "release_approval_ready" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "release_approval_status" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "release_blockers" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["known_gap_resolution_plan_coverage"][
        "$ref"
    ] == "#/schemas/KnownGapResolutionPlanCoverage"
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["production_gate_registry_audit"][
        "$ref"
    ] == "#/schemas/ProductionGateRegistryAudit"
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["provider_protocols_receipt"]["$ref"] == (
        "#/schemas/ProviderProtocolsReceipt"
    )
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["provider_onboarding_receipt"]["$ref"] == (
        "#/schemas/ProviderOnboardingReceipt"
    )
    assert "external_payload_birth_match_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "coverage_complete" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "external_payload_birth_match_coverage"
    ]["required"]
    assert schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["production_resolution_plan_summary"][
        "$ref"
    ] == "#/schemas/ProductionResolutionPlanSummary"
    release_provider_ledger_schema = schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
        "provider_ledger"
    ]
    assert release_provider_ledger_schema["$ref"] == "#/schemas/ProductionReadinessProviderLedgerSummary"
    release_provider_ledger_schema = schema["schemas"]["ProductionReadinessProviderLedgerSummary"]
    assert "request_receipt_status" in release_provider_ledger_schema["required"]
    assert "reference_contract_status" in release_provider_ledger_schema["required"]
    assert "command_fingerprint_status" in release_provider_ledger_schema["required"]
    assert "reference_contract_failures" in release_provider_ledger_schema["required"]
    assert "command_fingerprint_failures" in release_provider_ledger_schema["required"]
    ledger_domain_schema = schema["schemas"]["ProviderCertificationLedgerDomainStatus"]
    assert "latest_reference_contract_method_surface_sha256" in ledger_domain_schema["required"]
    assert "current_method_surface_sha256" in ledger_domain_schema["required"]
    assert "reference_contract_method_surface_current" in ledger_domain_schema["required"]
    assert "coverage_complete" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "invalid_gate_ids_by_gap" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "invalid_verification_commands_by_gap" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "invalid_verification_options_by_gap" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "command_validation_complete" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "command_subcommands_by_gap" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "command_options_by_gap" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "valid_cli_subcommands" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "valid_cli_options_by_subcommand" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "valid_production_gate_ids" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "audit_plan_hash" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
    assert "resolution_plan_sha256" in schema["schemas"]["ProductionResolutionPlanSummary"]["required"]
    assert "category_counts" in schema["schemas"]["ProductionResolutionPlanSummary"]["required"]
    assert schema["schemas"]["ProductionResolutionPlanSummary"]["properties"]["category_counts"][
        "additionalProperties"
    ]["type"] == "integer"
    assert schema["schemas"]["ClassicalSourcesResponse"]["properties"]["audit"]["$ref"] == (
        "#/schemas/ClassicalSourceListAudit"
    )
    assert "configuration_guidance" in schema["schemas"]["ClassicalSourcesResponse"]["required"]
    assert schema["schemas"]["ClassicalSourcesResponse"]["properties"]["configuration_guidance"]["$ref"] == (
        "#/schemas/ClassicalSourcesConfigurationGuidance"
    )
    classical_guidance_schema = schema["schemas"]["ClassicalSourcesConfigurationGuidance"]
    assert "example_source_list_path" in classical_guidance_schema["required"]
    assert "cli_refresh_command" in classical_guidance_schema["required"]
    assert classical_guidance_schema["properties"]["env_var"]["const"] == "SEMAS_CLASSIC_SOURCE_LIST"
    assert schema["schemas"]["ClassicalSourceListAudit"]["properties"]["source_list_receipt"]["$ref"] == (
        "#/schemas/ClassicalSourceListReceipt"
    )
    assert schema["schemas"]["ClassicalSourceListReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ClassicalSourceListReceiptMaterial"
    )
    assert "refresh_receipt" in schema["schemas"]["ClassicalSourcesRefreshResponse"]["required"]
    assert (
        schema["schemas"]["ClassicalSourcesRefreshResponse"]["properties"]["refresh_receipt"]["anyOf"][0]["$ref"]
        == "#/schemas/ClassicalRefreshReceipt"
    )
    assert schema["schemas"]["ClassicalRefreshReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/ClassicalRefreshReceiptMaterial"
    )
    assert "source_list_receipt_sha256" in schema["schemas"]["ClassicalRefreshReceiptMaterial"]["required"]
    assert "source_list_receipt_material_sha256" in schema["schemas"]["ClassicalRefreshReceiptMaterial"]["required"]
    assert "record_count" in schema["schemas"]["ClassicalRefreshReceiptMaterial"]["required"]
    assert schema["schemas"]["ClassicalRefreshReceiptMaterial"]["properties"]["sources"]["items"]["$ref"] == (
        "#/schemas/ClassicalRefreshSourceReceipt"
    )
    refresh_source_required = schema["schemas"]["ClassicalRefreshSourceReceipt"]["required"]
    assert "ingest_content_hash" in refresh_source_required
    assert "citation_policies" in refresh_source_required
    assert "ClassicalSourceAuditEntry" in schema["schemas"]
    assert "source_audits" in schema["schemas"]["ClassicalSourceListAudit"]["required"]
    assert "source_audits" in schema["schemas"]["ClassicalSourceListReceiptMaterial"]["required"]
    assert schema["schemas"]["ClassicalSourceListAudit"]["properties"]["source_audits"]["items"]["$ref"] == (
        "#/schemas/ClassicalSourceAuditEntry"
    )
    assert "refreshable" in schema["schemas"]["ClassicalSourceAuditEntry"]["required"]
    assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["classical_source_refresh"]["$ref"] == (
        "#/schemas/ClassicalSourceRefreshReceiptSummary"
    )
    assert "source_list_receipt_sha256" in schema["schemas"]["ClassicalSourceRefreshReceiptSummary"]["required"]
    assert "source_list_receipt_material_sha256" in schema["schemas"]["ClassicalSourceRefreshReceiptSummary"]["required"]
    assert "latest_refresh_receipt_sha256" in schema["schemas"]["ClassicalSourceRefreshReceiptSummary"]["required"]
    assert "latest_refresh_record_count" in schema["schemas"]["ClassicalSourceRefreshReceiptSummary"]["required"]
    assert "classical_source_list_path" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert "schema_version" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert "governance_gate_ids" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert "data_split_record_coverage" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert "label_provenance" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert "statistical_plan" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
    assert schema["schemas"]["OutcomeDatasetReceiptMaterial"]["properties"]["data_split_record_coverage"]["$ref"] == (
        "#/schemas/OutcomeDataSplitRecordCoverage"
    )
    assert schema["schemas"]["OutcomeDatasetReceiptMaterial"]["properties"]["label_provenance"]["$ref"] == (
        "#/schemas/OutcomeLabelProvenanceSummary"
    )
    assert schema["schemas"]["OutcomeDatasetReceiptMaterial"]["properties"]["statistical_plan"]["$ref"] == (
        "#/schemas/OutcomeStatisticalPlanSummary"
    )
    assert schema["schemas"]["OutcomeDatasetReceipt"]["properties"]["material"]["$ref"] == (
        "#/schemas/OutcomeDatasetReceiptMaterial"
    )
    assert schema["schemas"]["ClassicalRefreshReceiptMaterial"]["properties"]["sources"]["items"]["$ref"] == (
        "#/schemas/ClassicalRefreshSourceReceipt"
    )
    assert "ingest_content_hash" in schema["schemas"]["ClassicalRefreshSourceReceipt"]["required"]
    assert "citation_policies" in schema["schemas"]["ClassicalRefreshSourceReceipt"]["required"]
    assert "outcome_dataset_receipt" in schema["schemas"]["OutcomeDatasetAuditResponse"]["required"]
    assert schema["schemas"]["OutcomeDatasetAuditResponse"]["properties"]["outcome_dataset_receipt"]["$ref"] == (
        "#/schemas/OutcomeDatasetReceipt"
    )
    assert "configuration_guidance" in schema["schemas"]["OutcomeDatasetAuditResponse"]["required"]
    assert schema["schemas"]["OutcomeDatasetAuditResponse"]["properties"]["configuration_guidance"]["$ref"] == (
        "#/schemas/OutcomeDatasetConfigurationGuidance"
    )
    guidance_schema = schema["schemas"]["OutcomeDatasetConfigurationGuidance"]
    assert "example_manifest_path" in guidance_schema["required"]
    assert "production_readiness_command" in guidance_schema["required"]
    assert guidance_schema["properties"]["env_var"]["const"] == "SEMAS_OUTCOME_DATASET_MANIFEST"
    assert "outcome_dataset_receipt" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["outcome_dataset_receipt"]["$ref"] == (
        "#/schemas/OutcomeDatasetReceipt"
    )
    assert "outcome_dataset_receipt_sha256" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
    assert "outcome_dataset_receipt_sha256" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
    assert "outcome_dataset_receipt" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "provider_ledger" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "production_readiness_status" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "production_ready" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert "known_gap_ids" in schema["schemas"]["ReleaseManifestResponse"]["required"]
    assert schema["schemas"]["ReleaseManifestLedgerResponse"]["properties"]["ledger"]["$ref"] == (
        "#/schemas/ReleaseManifestLedgerStatus"
    )
    assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["release_manifest_ledger"]["$ref"] == (
        "#/schemas/ReleaseManifestLedgerStatus"
    )
    assert "release_manifest_ledger" in schema["schemas"]["ProductionReadinessResponse"]["required"]
    assert "latest_record_hash" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "latest_record_index" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "command_fingerprint_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "command_fingerprint_failures" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
    assert "configuration_guidance" in schema["schemas"]["ProviderCertificationLedgerResponse"]["required"]
    assert schema["schemas"]["ProviderCertificationLedgerResponse"]["properties"]["configuration_guidance"]["$ref"] == (
        "#/schemas/ProviderLedgerConfigurationGuidance"
    )
    provider_ledger_guidance_schema = schema["schemas"]["ProviderLedgerConfigurationGuidance"]
    assert "certification_commands" in provider_ledger_guidance_schema["required"]
    assert "drift_commands" in provider_ledger_guidance_schema["required"]
    assert "domain_provenance_env_vars" in provider_ledger_guidance_schema["required"]
    assert "resolution_guidance" in schema["schemas"]["ProviderCertificationDriftResponse"]["required"]
    assert schema["schemas"]["ProviderCertificationDriftResponse"]["properties"]["resolution_guidance"]["$ref"] == (
        "#/schemas/ProviderDriftResolutionGuidance"
    )
    provider_drift_guidance_schema = schema["schemas"]["ProviderDriftResolutionGuidance"]
    assert "recertification_commands" in provider_drift_guidance_schema["required"]
    assert "blocking_failures" in provider_drift_guidance_schema["required"]
    assert "production_readiness_command" in provider_drift_guidance_schema["required"]
    assert "latest_record_index" in schema["schemas"]["ReleaseManifestLedgerStatus"]["required"]
    assert "external_review" in schema["schemas"]["OutcomeDatasetManifest"]["required"]
    assert "data_split" in schema["schemas"]["OutcomeDatasetManifest"]["required"]
    assert "label_collection" in schema["schemas"]["OutcomeDatasetManifest"]["required"]
    assert "external_review" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert "data_split" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert "data_split_record_coverage" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert "label_collection" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert "label_provenance" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert "statistical_plan" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert "optimization_policy" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["record_fingerprints"]["items"]["$ref"] == (
        "#/schemas/OutcomeRecordFingerprint"
    )
    assert "case_id" in schema["schemas"]["OutcomeRecordFingerprint"]["required"]
    assert "sha256" in schema["schemas"]["OutcomeRecordFingerprint"]["required"]
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["data_split_record_coverage"]["$ref"] == (
        "#/schemas/OutcomeDataSplitRecordCoverage"
    )
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["label_inventory"]["$ref"] == (
        "#/schemas/OutcomeLabelInventory"
    )
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["label_provenance"]["$ref"] == (
        "#/schemas/OutcomeLabelProvenanceSummary"
    )
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["statistical_plan"]["$ref"] == (
        "#/schemas/OutcomeStatisticalPlanSummary"
    )
    outcome_plan = schema["schemas"]["OutcomeStatisticalPlan"]
    assert "pre_registered" in outcome_plan["required"]
    assert "registration_id" in outcome_plan["required"]
    assert "analysis_freeze_date" in outcome_plan["required"]
    assert outcome_plan["properties"]["plan_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["optimization_policy"]["$ref"] == (
        "#/schemas/OutcomeOptimizationPolicy"
    )
    assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["governance_gates"]["$ref"] == (
        "#/schemas/OutcomeGovernanceGates"
    )
    assert "observed_label_ids" in schema["schemas"]["OutcomeLabelInventory"]["required"]
    assert "provenance_complete" in schema["schemas"]["OutcomeLabelProvenanceSummary"]["required"]
    assert "audit_only_acknowledged_count" in schema["schemas"]["OutcomeLabelProvenanceSummary"]["required"]
    assert "blocked_reason" in schema["schemas"]["OutcomeOptimizationPolicy"]["required"]
    assert "blocking_failures" in schema["schemas"]["OutcomeGovernanceGates"]["required"]
    assert schema["schemas"]["OutcomeQualityTaskProjection"]["properties"]["projected_task_fingerprints"]["items"][
        "$ref"
    ] == "#/schemas/OutcomeQualityTaskFingerprint"
    projected_task_item = schema["schemas"]["OutcomeQualityTaskFingerprint"]
    assert "split_role" in projected_task_item["required"]
    assert projected_task_item["properties"]["split_role"]["enum"] == ["train", "holdout", "unassigned"]
    split_coverage = schema["schemas"]["OutcomeDataSplitRecordCoverage"]
    assert "coverage_complete" in split_coverage["required"]
    assert "split_fingerprint" in split_coverage["required"]
    assert split_coverage["properties"]["split_fingerprint"]["pattern"] == "^[0-9a-f]{64}$"
    assert schema["schemas"]["ReleaseManifestDriftResponse"]["properties"]["drift"]["$ref"] == (
        "#/schemas/ReleaseManifestDriftStatus"
    )
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "annual_luck"
    ]["$ref"] == "#/schemas/AnnualLuck"
    assert "annual_timeline_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "annual_timeline_receipt"
    ]["$ref"] == "#/schemas/AnnualTimelineReceipt"
    assert schema["schemas"]["AnnualTimelineReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/AnnualTimelineReceiptRowFingerprint"
    )
    assert schema["schemas"]["AnnualTimelineReceipt"]["properties"]["annual_luck_range"]["$ref"] == (
        "#/schemas/AnnualLuckRangeSummary"
    )
    assert "start_year" in schema["schemas"]["AnnualLuckRangeSummary"]["required"]
    assert "annual_timeline_sha256" in schema["schemas"]["AnnualTimelineReceipt"]["required"]
    assert "topic_evidence_complete" in schema["schemas"]["AnnualTimelineReceipt"]["required"]
    assert "topic_evidence_missing" in schema["schemas"]["AnnualTimelineReceipt"]["required"]
    assert "validation_boundary" in schema["schemas"]["AnnualTimelineReceipt"]["required"]
    annual_timeline_topic = schema["schemas"]["AnnualTimelineTopic"]
    assert "bazi_evidence_sha256" in annual_timeline_topic["required"]
    assert annual_timeline_topic["properties"]["bazi_evidence_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert annual_timeline_topic["properties"]["source"]["const"] == "annual_luck.rows"
    assert "provider_quality" in annual_timeline_topic["required"]
    assert "boundary" in annual_timeline_topic["required"]
    assert "monthly_luck_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "monthly_luck"
    ]["$ref"] == "#/schemas/MonthlyLuck"
    assert schema["schemas"]["MonthlyLuck"]["properties"]["rows"]["items"]["$ref"] == "#/schemas/MonthlyLuckRow"
    assert schema["schemas"]["MonthlyLuck"]["properties"]["range"]["$ref"] == "#/schemas/MonthlyLuckRangeSummary"
    assert schema["schemas"]["MonthlyLuck"]["properties"]["basis"]["$ref"] == "#/schemas/MonthlyLuckBasisSummary"
    assert schema["schemas"]["MonthlyLuckRow"]["properties"]["bazi_evidence"]["$ref"] == (
        "#/schemas/MonthlyLuckBaziEvidence"
    )
    assert schema["schemas"]["MonthlyLuckRow"]["properties"]["topics"]["properties"]["finance"]["$ref"] == (
        "#/schemas/MonthlyLuckTopic"
    )
    assert schema["schemas"]["MonthlyLuckBaziEvidence"]["properties"]["monthly_ten_gods"]["$ref"] == (
        "#/schemas/AnnualLuckTenGodPair"
    )
    assert "monthly_ten_gods" in schema["schemas"]["MonthlyLuckBaziEvidence"]["required"]
    assert "topics" in schema["schemas"]["MonthlyLuckRow"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "monthly_luck_receipt"
    ]["$ref"] == "#/schemas/MonthlyLuckReceipt"
    assert schema["schemas"]["MonthlyLuckReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/MonthlyLuckReceiptRowFingerprint"
    )
    assert schema["schemas"]["MonthlyLuckReceipt"]["properties"]["monthly_luck_range"]["$ref"] == (
        "#/schemas/MonthlyLuckRangeSummary"
    )
    assert schema["schemas"]["MonthlyLuckReceipt"]["properties"]["monthly_luck_basis"]["$ref"] == (
        "#/schemas/MonthlyLuckBasisSummary"
    )
    assert "months_per_year" in schema["schemas"]["MonthlyLuckRangeSummary"]["required"]
    assert "provider_quality" in schema["schemas"]["MonthlyLuckBasisSummary"]["required"]
    assert "monthly_luck_rows_sha256" in schema["schemas"]["MonthlyLuckReceipt"]["required"]
    assert "topic_evidence_complete" in schema["schemas"]["MonthlyLuckReceipt"]["required"]
    assert "topic_evidence_missing" in schema["schemas"]["MonthlyLuckReceipt"]["required"]
    monthly_luck_topic = schema["schemas"]["MonthlyLuckTopic"]
    assert "bazi_evidence_sha256" in monthly_luck_topic["required"]
    assert monthly_luck_topic["properties"]["bazi_evidence_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert monthly_luck_topic["properties"]["source"]["const"] == "monthly_luck.rows"
    assert "provider_quality" in monthly_luck_topic["required"]
    assert "boundary" in monthly_luck_topic["required"]
    assert "validation_boundary" in schema["schemas"]["MonthlyLuckReceipt"]["required"]
    assert "auspicious_calendar_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "auspicious_calendar_receipt"
    ]["$ref"] == "#/schemas/AuspiciousCalendarReceipt"
    assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
        "#/schemas/AuspiciousCalendarReceiptRowFingerprint"
    )
    assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["calendar_range"]["$ref"] == (
        "#/schemas/AuspiciousCalendarRange"
    )
    assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["calendar_basis"]["$ref"] == (
        "#/schemas/AuspiciousCalendarBasis"
    )
    assert "calendar_rows_sha256" in schema["schemas"]["AuspiciousCalendarReceipt"]["required"]
    assert "method_layers_sha256" in schema["schemas"]["AuspiciousCalendarReceipt"]["required"]
    assert "validation_boundary" in schema["schemas"]["AuspiciousCalendarReceipt"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "request_provenance"
    ]["$ref"] == "#/schemas/RequestProvenance"
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "votes"
    ]["$ref"] == "#/schemas/VoteRecord"
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "deliberation_receipt"
    ]["$ref"] == "#/schemas/DeliberationReceipt"
    assert schema["schemas"]["VoteRecord"]["properties"]["_claims"]["items"]["$ref"] == "#/schemas/VoteClaim"
    assert schema["schemas"]["VoteClaim"]["properties"]["challenges"]["items"]["$ref"] == "#/schemas/VoteChallenge"
    assert "preserved_as" in schema["schemas"]["VoteChallenge"]["required"]
    assert schema["schemas"]["VoteRecord"]["properties"]["_audit"]["$ref"] == "#/schemas/VoteAudit"
    assert "minority_positions_preserved" in schema["schemas"]["VoteAudit"]["required"]
    assert "votes_sha256" in schema["schemas"]["DeliberationReceipt"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "source_review"
    ]["$ref"] == "#/schemas/SourceReviewReport"
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "evidence_summary"
    ]["items"]["$ref"] == "#/schemas/EvidenceSummaryItem"
    assert "source_review" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert "evidence_summary" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert schema["schemas"]["SourceReviewReport"]["properties"]["evidence"]["additionalProperties"]["items"][
        "$ref"
    ] == "#/schemas/SourceEvidenceSnippet"
    assert schema["schemas"]["SourceEvidenceSnippet"]["properties"]["provenance"]["$ref"] == (
        "#/schemas/SourceEvidenceProvenance"
    )
    assert "covered_sources" in schema["schemas"]["SourceReviewReport"]["required"]
    assert "missing_evidence" in schema["schemas"]["SourceReviewReport"]["required"]
    assert "provenance" in schema["schemas"]["SourceEvidenceSnippet"]["required"]
    assert "citation_policy" in schema["schemas"]["SourceEvidenceProvenance"]["required"]
    assert "caution" in schema["schemas"]["EvidenceSummaryItem"]["required"]
    assert "cost_governance" in schema["schemas"]["ReproducibilityManifest"]["required"]
    assert schema["schemas"]["ReproducibilityManifest"]["properties"]["cost_governance"]["$ref"] == (
        "#/schemas/EvolutionCostGovernance"
    )
    assert schema["schemas"]["ReproducibilityManifest"]["properties"]["strategy_fingerprints"]["items"]["$ref"] == (
        "#/schemas/ReproducibilityStrategyFingerprint"
    )
    assert "name" in schema["schemas"]["ReproducibilityStrategyFingerprint"]["required"]
    assert schema["schemas"]["ReproducibilityStrategyFingerprint"]["properties"]["prompt_sha256"]["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert "source_review_sha256" in schema["schemas"]["DeliberationReceipt"]["required"]
    assert schema["schemas"]["AnnualLuck"]["properties"]["rows"]["items"]["$ref"] == "#/schemas/AnnualLuckRow"
    assert schema["schemas"]["AnnualLuckRow"]["properties"]["elements"]["$ref"] == "#/schemas/AnnualLuckRowElements"
    assert schema["schemas"]["AnnualLuckRow"]["properties"]["event_markers"]["$ref"] == "#/schemas/AnnualEventMarkers"
    assert schema["schemas"]["AnnualLuckRow"]["properties"]["bazi_evidence"]["$ref"] == (
        "#/schemas/AnnualLuckBaziEvidence"
    )
    assert schema["schemas"]["AnnualLuckBaziEvidence"]["properties"]["annual_ten_gods"]["$ref"] == (
        "#/schemas/AnnualLuckTenGodPair"
    )
    assert schema["schemas"]["AnnualLuckBaziEvidence"]["properties"]["active_major_luck"]["$ref"] == (
        "#/schemas/AnnualLuckActiveMajorLuck"
    )
    assert schema["schemas"]["AnnualLuckBaziEvidence"]["properties"]["natal_pillar_matches"]["items"]["$ref"] == (
        "#/schemas/AnnualLuckNatalPillarMatch"
    )
    assert "finance" in schema["schemas"]["AnnualLuckRow"]["required"]
    assert "event_markers" in schema["schemas"]["AnnualLuckRow"]["required"]
    assert "career_launch" in schema["schemas"]["AnnualEventMarkers"]["required"]
    assert "role_power" in schema["schemas"]["AnnualEventMarkers"]["required"]
    assert "focus" in schema["schemas"]["AnnualLuckRowElements"]["required"]
    assert "annual_ten_gods" in schema["schemas"]["AnnualLuckBaziEvidence"]["required"]
    assert "stem" in schema["schemas"]["AnnualLuckTenGodPair"]["required"]
    assert "pillar" in schema["schemas"]["AnnualLuckNatalPillarMatch"]["required"]
    assert schema["schemas"]["AnnualLuck"]["properties"]["phase_summary"]["items"]["$ref"] == (
        "#/schemas/AnnualPhaseSummary"
    )
    assert schema["schemas"]["AnnualPhaseSummary"]["properties"]["topic_highlights"]["properties"]["finance"][
        "$ref"
    ] == "#/schemas/AnnualPhaseTopicHighlight"
    assert "bazi_evidence" in schema["schemas"]["AnnualTimelineRow"]["required"]
    bazi_profile = schema["schemas"]["BaziProfile"]
    assert "image_symbol_analysis" in bazi_profile["required"]
    assert "new_school_simplified_analysis" in bazi_profile["required"]
    assert "data_validation_analysis" in bazi_profile["required"]
    assert "school_debate" in bazi_profile["required"]
    assert bazi_profile["properties"]["image_symbol_analysis"]["type"] == "object"
    assert bazi_profile["properties"]["new_school_simplified_analysis"]["type"] == "object"
    assert bazi_profile["properties"]["data_validation_analysis"]["type"] == "object"
    assert bazi_profile["properties"]["school_debate"]["type"] == "object"
    assert bazi_profile["properties"]["strength_analysis"]["$ref"] == "#/schemas/BaziStrengthAnalysis"
    assert bazi_profile["properties"]["pattern_analysis"]["$ref"] == "#/schemas/BaziPatternAnalysis"
    assert bazi_profile["properties"]["useful_god_analysis"]["$ref"] == "#/schemas/BaziUsefulGodAnalysis"
    assert bazi_profile["properties"]["luck_start"]["$ref"] == "#/schemas/BaziLuckStart"
    assert bazi_profile["properties"]["method_matrix"]["items"]["$ref"] == "#/schemas/BaziMethodMatrixItem"
    assert bazi_profile["properties"]["major_luck"]["items"]["$ref"] == "#/schemas/BaziMajorLuckPeriod"
    assert schema["schemas"]["BaziMajorLuckPeriod"]["properties"]["annual_preview"]["items"]["$ref"] == (
        "#/schemas/BaziMajorLuckAnnualPreview"
    )
    assert "summary" in schema["schemas"]["BaziMethodMatrixItem"]["required"]
    assert "element_counts" in schema["schemas"]["BaziStrengthAnalysis"]["required"]
    assert "month_ten_god" in schema["schemas"]["BaziPatternAnalysis"]["required"]
    assert "avoid_overweight_element" in schema["schemas"]["BaziUsefulGodAnalysis"]["required"]
    assert "forward" in schema["schemas"]["BaziLuckStart"]["required"]
    assert "ganzhi" in schema["schemas"]["BaziMajorLuckPeriod"]["required"]
    assert "year" in schema["schemas"]["BaziMajorLuckAnnualPreview"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "ziwei_profile"
    ]["$ref"] == "#/schemas/ZiweiProfile"
    ziwei_profile = schema["schemas"]["ZiweiProfile"]
    assert ziwei_profile["properties"]["highlighted_palaces"]["items"]["$ref"] == "#/schemas/ZiweiPalaceSummary"
    assert ziwei_profile["properties"]["major_limits"]["items"]["$ref"] == "#/schemas/ZiweiMajorLimit"
    assert ziwei_profile["properties"]["annual_activation"]["items"]["$ref"] == "#/schemas/ZiweiAnnualActivation"
    assert ziwei_profile["properties"]["method_matrix"]["items"]["$ref"] == "#/schemas/AstrologyMethodMatrixItem"
    assert "ming_palace" in ziwei_profile["required"]
    assert "primary_stars" in schema["schemas"]["ZiweiPalaceSummary"]["required"]
    assert "start_year" in schema["schemas"]["ZiweiMajorLimit"]["required"]
    assert "age" in schema["schemas"]["ZiweiAnnualActivation"]["required"]
    assert "theme" in schema["schemas"]["ZiweiAnnualActivation"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "qimen_profile"
    ]["$ref"] == "#/schemas/QimenProfile"
    qimen_profile = schema["schemas"]["QimenProfile"]
    assert qimen_profile["properties"]["duty"]["$ref"] == "#/schemas/QimenDuty"
    assert qimen_profile["properties"]["useful_gods"]["additionalProperties"]["$ref"] == "#/schemas/QimenUsefulGod"
    assert qimen_profile["properties"]["highlighted_palaces"]["items"]["$ref"] == "#/schemas/QimenPalaceSummary"
    assert qimen_profile["properties"]["pattern_flags"]["items"]["$ref"] == "#/schemas/QimenPatternFlag"
    assert qimen_profile["properties"]["annual_timing"]["items"]["$ref"] == "#/schemas/QimenAnnualTiming"
    assert qimen_profile["properties"]["method_matrix"]["items"]["$ref"] == "#/schemas/AstrologyMethodMatrixItem"
    assert "duty" in qimen_profile["required"]
    assert "door" in schema["schemas"]["QimenDuty"]["required"]
    assert "judgment" in schema["schemas"]["QimenUsefulGod"]["required"]
    assert "heaven_stem" in schema["schemas"]["QimenPalaceSummary"]["required"]
    assert "meaning" in schema["schemas"]["QimenPatternFlag"]["required"]
    assert "year" in schema["schemas"]["QimenAnnualTiming"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "rendered_reports"
    ]["$ref"] == "#/schemas/RenderedReports"
    assert "rendered_reports" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert "en" in schema["schemas"]["RenderedReports"]["required"]
    assert "zh" in schema["schemas"]["RenderedReports"]["required"]
    assert schema["schemas"]["RenderedReports"]["additionalProperties"]["type"] == "string"
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "llm_synthesis"
    ]["$ref"] == "#/schemas/LLMSynthesisReport"
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "workflow"
    ]["$ref"] == "#/schemas/WorkflowReport"
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["schema_validation"]["$ref"] == (
        "#/schemas/SchemaValidationSummary"
    )
    assert "schema_validation" in schema["schemas"]["AnalyzeResponse"]["required"]
    assert "valid" in schema["schemas"]["SchemaValidationSummary"]["required"]
    assert "error_count" in schema["schemas"]["SchemaValidationSummary"]["required"]
    assert schema["schemas"]["SchemaValidationSummary"]["properties"]["errors"]["items"]["type"] == "string"
    final_report_schema = schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]
    for field in ("title", "coordinator_version", "summary", "conflicts", "strategy_notes", "boundaries"):
        assert field in final_report_schema["required"]
    assert final_report_schema["properties"]["title"]["type"] == "string"
    assert final_report_schema["properties"]["coordinator_version"]["type"] == "integer"
    assert final_report_schema["properties"]["summary"]["items"]["type"] == "string"
    assert final_report_schema["properties"]["boundaries"]["items"]["type"] == "string"
    assert final_report_schema["properties"]["conflicts"]["items"]["type"] == "string"
    assert final_report_schema["properties"]["strategy_notes"]["items"]["type"] == "string"
    assert "llm_synthesis" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert "workflow" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"][
        "final_report"
    ]["required"]
    assert "prompt_fingerprint" in schema["schemas"]["LLMSynthesisReport"]["required"]
    assert "generated" in schema["schemas"]["LLMSynthesisReport"]["required"]
    assert "discussion_rounds" in schema["schemas"]["WorkflowReport"]["required"]
    assert "preserve_conflicts" in schema["schemas"]["WorkflowReport"]["required"]
    assert schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
        "astrology_profile"
    ]["$ref"] == "#/schemas/AstrologyProfile"
    astrology_profile = schema["schemas"]["AstrologyProfile"]
    assert astrology_profile["properties"]["planets"]["items"]["$ref"] == "#/schemas/AstrologyPlanet"
    assert astrology_profile["properties"]["houses"]["items"]["$ref"] == "#/schemas/AstrologyHouse"
    assert astrology_profile["properties"]["aspects"]["items"]["$ref"] == "#/schemas/AstrologyAspect"
    assert astrology_profile["properties"]["annual_transits"]["items"]["$ref"] == "#/schemas/AstrologyAnnualTransit"
    assert astrology_profile["properties"]["ephemeris_quality"]["$ref"] == "#/schemas/AstrologyEphemerisQuality"
    assert astrology_profile["properties"]["method_matrix"]["items"]["$ref"] == "#/schemas/AstrologyMethodMatrixItem"
    assert "ephemeris_quality" in astrology_profile["required"]
    assert "activated_house" in schema["schemas"]["AstrologyAnnualTransit"]["required"]
    assert "focus" in schema["schemas"]["AstrologyAnnualTransit"]["required"]
    assert "absolute_degree" in schema["schemas"]["AstrologyPlanet"]["required"]
    assert "ephemeris_backed" in schema["schemas"]["AstrologyEphemerisQuality"]["required"]
    assert "evidence_fields" in schema["schemas"]["AstrologyMethodMatrixItem"]["required"]


def test_schema_contract_score_gates_required_governance_fields():
    schema = schema_document()

    assert _required_fields_ok(schema["schemas"]) == 1.0

    mutated = {
        key: {**value, "properties": dict(value.get("properties", {}))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    analyze = {
        **mutated["AnalyzeResponse"],
        "properties": dict(mutated["AnalyzeResponse"]["properties"]),
    }
    result_schema = {
        **analyze["properties"]["result"],
        "properties": dict(analyze["properties"]["result"]["properties"]),
    }
    final_report_schema = {
        **result_schema["properties"]["final_report"],
        "required": list(result_schema["properties"]["final_report"]["required"]),
    }
    final_report_schema["required"].remove("boundaries")
    result_schema["properties"]["final_report"] = final_report_schema
    analyze["properties"]["result"] = result_schema
    mutated["AnalyzeResponse"] = analyze

    assert _response_refs_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["EvolveResponse"]["required"].remove("trigger_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["EvolutionTriggerReceiptMaterial"]["required"].remove("feedback_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestResponse"]["required"].remove("evolution_trigger_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("evolution_trigger_receipt_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestResponse"]["required"].remove("github_comparison_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("github_comparison_receipt_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestResponse"]["required"].remove("plan_compliance_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("plan_compliance_receipt_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessResponse"]["required"].remove("release_manifest_ledger")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["OutcomeDatasetAudit"]["required"].remove("external_review")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["OutcomeOptimizationPolicy"]["required"].remove("blocked_reason")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["MonthlyLuckBasisSummary"]["required"].remove("provider_quality")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["MonthlyLuck"]["required"].remove("rows")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["MonthlyLuckRow"]["required"].remove("topics")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["MonthlyLuckBaziEvidence"]["required"].remove("monthly_ten_gods")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ZiweiProfile"]["required"].remove("ming_palace")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ZiweiPalaceSummary"]["required"].remove("primary_stars")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["QimenProfile"]["required"].remove("duty")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["QimenDuty"]["required"].remove("door")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["RenderedReports"]["required"].remove("zh")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["LLMSynthesisReport"]["required"].remove("prompt_fingerprint")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["WorkflowReport"]["required"].remove("preserve_conflicts")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["SourceReviewReport"]["required"].remove("missing_evidence")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["SourceEvidenceSnippet"]["required"].remove("provenance")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["TopicSynthesisAnnualFocus"]["required"].remove("risk_notes")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["TopicSynthesisTimingSignal"]["required"].remove("natal_match_count")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["AstrologyProfile"]["required"].remove("ephemeris_quality")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["AstrologyPlanet"]["required"].remove("absolute_degree")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["OutcomeDatasetReceiptMaterial"]["required"].remove("governance_gate_ids")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["VoteRecord"]["required"].remove("_claims")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["DeliberationReceipt"]["required"].remove("votes_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("readiness_deliberation_receipt_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("annual_timeline_receipt_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["AnnualTimelineReceipt"]["required"].remove("topic_evidence_complete")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["AnnualTimelineTopic"]["required"].remove("bazi_evidence_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("monthly_luck_receipt_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["MonthlyLuckReceipt"]["required"].remove("topic_evidence_complete")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["MonthlyLuckTopic"]["required"].remove("bazi_evidence_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("auspicious_calendar_receipt_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["BaziProfile"]["required"].remove("data_validation_analysis")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["BaziStrengthAnalysis"]["required"].remove("element_counts")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["BaziUsefulGodAnalysis"]["required"].remove("rationale")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("provider_action_plan_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("classical_source_receipt_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReproducibilityManifest"]["required"].remove("cost_governance")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["PlanCompliance"]["required"].remove("source_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditResponse"]["required"].remove("plan_compliance_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["PlanComplianceReceiptMaterial"]["required"].remove("matrix_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditResponse"]["required"].remove("classical_source_refresh")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditResponse"]["required"].remove("known_gap_resolution_plan")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditResponse"]["required"].remove("known_gap_resolution_plan_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["KnownGapResolutionPlanItem"]["required"].remove("verification_commands")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["KnownGapResolutionPlanItem"]["required"].remove("id")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["KnownGapResolutionPlanCoverage"]["required"].remove("planned_gap_ids")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessResponse"]["required"].remove("classical_source_refresh")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessResponse"]["required"].remove("known_gap_resolution_plan")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessResponse"]["required"].remove("production_gate_registry_audit")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessReceiptMaterial"]["required"].remove("known_gap_resolution_plan_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionGateRegistryAudit"]["required"].remove("registry_current")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("known_gap_resolution_plan_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("production_gate_registry_audit")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("provider_protocols_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestReceiptMaterial"]["required"].remove("provider_onboarding_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReleaseManifestGateChecks"]["required"].remove("provider_onboarding_receipt_current")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["KnownGapResolutionPlanCoverage"]["required"].remove("coverage_complete")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProviderOnboardingReceiptMaterial"]["required"].remove("missing_evidence_counts")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProviderCommandFingerprint"]["required"].remove("artifact_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProviderCertificationReceiptMaterial"]["required"].remove("reference_contract_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["BenchmarkReceiptMaterial"]["required"].remove("reference_charts")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProviderProfileReadiness"]["required"].remove("live_required")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ReferenceChartChecks"]["required"].remove("method_coverage")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProviderOnboardingAuditSummary"]["required"].remove("missing_evidence_counts")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditReceiptMaterial"]["required"].remove("provider_onboarding")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditReceiptMaterial"]["required"].remove("provider_protocol_governance")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["CapabilityAuditReceiptMaterial"]["required"].remove("provider_production_guidance")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["RequestScopedProviderContractSummary"]["required"].remove("requires_provenance_fields")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProviderProtocolGovernanceSummary"]["required"].remove("protocol_document_sha256")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessBenchmarkSummary"]["required"].remove("request_provenance_audit")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessBenchmarkRequestProvenanceAudit"]["required"].remove(
        "external_payload_birth_matches_ok"
    )

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessProviderLedgerSummary"]["required"].remove("command_fingerprint_status")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessEvidenceMaterializationSummary"]["required"].remove("failed_count")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ClassicalSourceListAudit"]["required"].remove("source_list_receipt")

    assert _required_fields_ok(mutated) < 1.0

    mutated = {
        key: {**value, "required": list(value.get("required", []))}
        for key, value in schema["schemas"].items()
        if isinstance(value, dict)
    }
    mutated["ProductionReadinessReceiptMaterial"]["required"].remove("classical_source_list_path")

    assert _required_fields_ok(mutated) < 1.0
