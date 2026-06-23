"""Tests for the stdlib mingli HTTP API."""

from __future__ import annotations

import hashlib
import json
import sys
import threading
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from examples.mingli_5agents.api_server import serve


def _request(base_url: str, method: str, path: str, body: dict | None = None) -> dict:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        base_url + path,
        data=payload,
        method=method,
        headers={"content-type": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _source_governance_fields() -> dict[str, str]:
    return {
        "license": "CC0-1.0",
        "rights_basis": "test fixture authored for repository validation",
        "review_status": "open_license_reviewed",
        "reviewed_by": "api server test",
        "content_scope": "method metadata fixture only",
    }


def test_http_api_known_gap_handoff_export(tmp_path):
    repo = tmp_path / "repo"
    httpd = serve("127.0.0.1", 0, repo)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    base_url = f"http://{host}:{port}"
    try:
        schema = _request(base_url, "GET", "/schema")
        assert "KnownGapHandoffExportResponse" in schema["schemas"]
        assert "KnownGapHandoffExportVerificationRequest" in schema["schemas"]
        assert "KnownGapHandoffChecklistRequest" in schema["schemas"]
        assert "GET /known-gap-handoff" in schema["endpoints"]
        assert "POST /known-gap-handoff-verify" in schema["endpoints"]
        assert "POST /known-gap-handoff-checklist" in schema["endpoints"]

        result = _request(base_url, "GET", "/known-gap-handoff")

        assert result["schema_version"] == "known-gap-handoff-export-v1"
        assert result["status"] == "ready"
        assert len(result["audit_receipt_sha256"]) == 64
        assert len(result["handoff_export_receipt"]["sha256"]) == 64
        bundle = result["known_gap_handoff_bundle"]
        assert bundle["status"] == "ready"
        assert bundle["gap_count"] == len(result["known_gap_ids"])
        assert result["handoff_export_receipt"]["material"]["bundle_sha256"] == bundle["bundle_sha256"]
        by_gap = {item["gap_id"]: item for item in bundle["items"]}
        assert by_gap["professional_ziwei_provider"]["required_env_vars"] == ["SEMAS_ZIWEI_CLI"]

        verification = _request(base_url, "POST", "/known-gap-handoff-verify", {"handoff_export": result})
        assert verification["valid"] is True
        assert verification["bundle_hash_valid"] is True
        assert verification["receipt_hash_valid"] is True

        checklist = _request(base_url, "POST", "/known-gap-handoff-checklist", {"handoff_export": result})
        assert checklist["schema_version"] == "known-gap-handoff-checklist-v1"
        assert checklist["status"] == "ready"
        assert checklist["verification"]["valid"] is True
        assert checklist["item_count"] == len(result["known_gap_ids"])
        assert len(checklist["checklist_receipt"]["sha256"]) == 64

        matched_checklist = _request(
            base_url,
            "POST",
            "/known-gap-handoff-checklist",
            {
                "handoff_export": result,
                "expected_checklist_receipt_sha256": checklist["checklist_receipt"]["sha256"],
            },
        )
        assert matched_checklist["checklist_receipt_matches_expected"] is True
    finally:
        httpd.shutdown()
        thread.join(timeout=5)


def test_http_api_status_schema_analyze_and_benchmark(tmp_path):
    repo = tmp_path / "repo"
    httpd = serve("127.0.0.1", 0, repo)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    base_url = f"http://{host}:{port}"
    try:
        assert _request(base_url, "GET", "/health")["status"] == "ok"

        schema = _request(base_url, "GET", "/schema")
        assert "AnalyzeRequest" in schema["schemas"]
        assert "AnalyzeResponse" in schema["schemas"]
        assert "ArchiveIntegrityReport" in schema["schemas"]
        assert "ProviderSummary" in schema["schemas"]
        assert "ProviderActionPlanItem" in schema["schemas"]
        assert "BirthProfile" in schema["schemas"]
        assert "RequestProvenance" in schema["schemas"]
        assert "ProviderIntegrationPlan" in schema["schemas"]
        assert "ProviderChecksResponse" in schema["schemas"]
        assert "ProviderCertificationResponse" in schema["schemas"]
        assert "ProviderCertificationReceipt" in schema["schemas"]
        assert "AnnualLuck" in schema["schemas"]
        assert "AnnualPhaseSummary" in schema["schemas"]
        assert "AnnualPhaseTopicHighlight" in schema["schemas"]
        assert "ProviderCertificationLedgerStatus" in schema["schemas"]
        assert "ProviderCertificationLedgerDomainStatus" in schema["schemas"]
        assert "ProviderCertificationLedgerResponse" in schema["schemas"]
        assert "ProviderCertificationDriftCheck" in schema["schemas"]
        assert "ProviderCertificationDriftResponse" in schema["schemas"]
        assert "ProviderCertificationDriftStatus" in schema["schemas"]
        assert "ProviderProtocolsResponse" in schema["schemas"]
        assert "ProviderReadinessCheck" in schema["schemas"]
        assert "ProviderProvenanceAudit" in schema["schemas"]
        assert "ProviderProfileReadiness" in schema["schemas"]
        assert "ProviderProfileRequiredGroup" in schema["schemas"]
        assert "ReferenceChartCaseCheck" in schema["schemas"]
        assert "ReferenceChartChecks" in schema["schemas"]
        assert "ReferenceChartDomainMethodCoverage" in schema["schemas"]
        assert "ReferenceChartMethodCoverage" in schema["schemas"]
        assert "ProductionReadinessGate" in schema["schemas"]
        assert "ProductionReadinessResponse" in schema["schemas"]
        assert "ProductionResolutionPlan" in schema["schemas"]
        assert "ProductionResolutionStep" in schema["schemas"]
        assert "EvolveResponse" in schema["schemas"]
        assert "EvolutionSelectionDecision" in schema["schemas"]
        assert "CapabilityAuditResponse" in schema["schemas"]
        assert "OutcomeDatasetManifest" in schema["schemas"]
        assert "OutcomeDatasetAudit" in schema["schemas"]
        assert "OutcomeDatasetAuditResponse" in schema["schemas"]
        assert "OutcomeDatasetEvolutionGate" in schema["schemas"]
        assert "OutcomeDatasetRecord" in schema["schemas"]
        assert "OutcomeQualityTaskProjection" in schema["schemas"]
        assert "PlanCompliance" in schema["schemas"]
        assert "StateOfArtAssessment" in schema["schemas"]
        assert "SpecialistReport" in schema["schemas"]
        assert "SpecialistLayer" in schema["schemas"]
        assert "GenomeLineage" in schema["schemas"]
        assert "LineageIntegrityReport" in schema["schemas"]
        assert "StatusResponse" in schema["schemas"]
        assert "LatestEvolutionStatus" in schema["schemas"]
        assert "BenchmarkResult" in schema["schemas"]
        assert "BenchmarkResponse" in schema["schemas"]
        assert "ReleaseManifestResponse" in schema["schemas"]
        assert "ReleaseManifestLedgerResponse" in schema["schemas"]
        assert "ReleaseManifestLedgerStatus" in schema["schemas"]
        assert "ReleaseManifestDriftResponse" in schema["schemas"]
        assert "ReleaseManifestDriftStatus" in schema["schemas"]
        assert "ReproducibilityManifest" in schema["schemas"]
        assert "RollbackResponse" in schema["schemas"]
        assert (
            schema["schemas"]["ProviderChecksResponse"]["properties"]["profile_readiness"]["$ref"]
            == "#/schemas/ProviderProfileReadiness"
        )
        assert (
            schema["schemas"]["ProviderProfileReadiness"]["properties"]["required_groups"]["items"]["$ref"]
            == "#/schemas/ProviderProfileRequiredGroup"
        )
        assert "live_required" in schema["schemas"]["ProviderProfileReadiness"]["required"]
        assert "accepted_checks" in schema["schemas"]["ProviderProfileRequiredGroup"]["required"]
        assert (
            schema["schemas"]["ProviderChecksResponse"]["properties"]["reference_chart_checks"]["$ref"]
            == "#/schemas/ReferenceChartChecks"
        )
        assert (
            schema["schemas"]["ReferenceChartChecks"]["properties"]["method_coverage"]["$ref"]
            == "#/schemas/ReferenceChartMethodCoverage"
        )
        assert (
            schema["schemas"]["ReferenceChartChecks"]["properties"]["cases"]["items"]["$ref"]
            == "#/schemas/ReferenceChartCaseCheck"
        )
        assert (
            schema["schemas"]["ReferenceChartMethodCoverage"]["properties"]["domains"]["additionalProperties"]["$ref"]
            == "#/schemas/ReferenceChartDomainMethodCoverage"
        )
        assert "provenance_coverage" in schema["schemas"]["ReferenceChartCaseCheck"]["required"]
        assert "observed" in schema["schemas"]["ReferenceChartDomainMethodCoverage"]["required"]
        assert schema["schemas"]["ProviderChecksResponse"]["properties"]["integration_plan"]["$ref"] == "#/schemas/ProviderIntegrationPlan"
        assert (
            schema["schemas"]["ProviderSummary"]["properties"]["action_plan"]["items"]["$ref"]
            == "#/schemas/ProviderActionPlanItem"
        )
        assert (
            schema["schemas"]["ProviderSummary"]["properties"]["readiness_matrix"]["items"]["$ref"]
            == "#/schemas/ProviderReadinessMatrixItem"
        )
        assert schema["schemas"]["ProviderChecksResponse"]["properties"]["checks"]["additionalProperties"]["$ref"] == "#/schemas/ProviderReadinessCheck"
        assert schema["schemas"]["ProviderReadinessCheck"]["properties"]["provider_provenance_audit"]["$ref"] == "#/schemas/ProviderProvenanceAudit"
        assert schema["schemas"]["ProviderReadinessCheck"]["properties"]["provider_command_fingerprint"]["$ref"] == (
            "#/schemas/ProviderCommandFingerprint"
        )
        assert schema["schemas"]["ProviderReadinessCheck"]["properties"]["install_diagnostics"]["$ref"] == "#/schemas/ProviderInstallDiagnostics"
        assert "ProviderInstallDiagnostics" in schema["schemas"]
        assert "protocol_version" in schema["schemas"]["ProviderReadinessCheck"]["required"]
        assert "protocol_hash" in schema["schemas"]["ProviderReadinessCheck"]["required"]
        assert "install_diagnostics" in schema["schemas"]["ProviderReadinessCheck"]["required"]
        assert (
            schema["schemas"]["ProviderCertificationResponse"]["properties"]["provider_provenance_audit"]["$ref"]
            == "#/schemas/ProviderProvenanceAudit"
        )
        assert (
            schema["schemas"]["ProviderCertificationResponse"]["properties"]["certification_receipt"]["$ref"]
            == "#/schemas/ProviderCertificationReceipt"
        )
        certification_schema = schema["schemas"]["ProviderCertificationResponse"]
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
            for item in schema["schemas"]["ProviderCertificationReceipt"]["properties"]["material"]["anyOf"]
            if "$ref" in item
        }
        assert "#/schemas/ProviderCertificationReceiptMaterial" in material_refs
        assert "#/schemas/BenchmarkReceiptMaterial" in material_refs
        assert schema["schemas"]["ProviderCertificationReceiptMaterial"]["properties"][
            "provider_command_fingerprint"
        ]["$ref"] == "#/schemas/ProviderCommandFingerprint"
        assert schema["schemas"]["ProviderCertificationReceiptMaterial"]["properties"][
            "reference_contract_coverage"
        ]["$ref"] == "#/schemas/ProviderReferenceContractCoverage"
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
        assert "reference_charts" in schema["schemas"]["BenchmarkReceiptMaterial"]["required"]
        assert "command_sha256" in schema["schemas"]["ProviderCommandFingerprint"]["required"]
        assert "artifact_sha256" in schema["schemas"]["ProviderCommandFingerprint"]["required"]
        assert schema["schemas"]["EvolveResponse"]["properties"]["selection_decision"]["$ref"] == "#/schemas/EvolutionSelectionDecision"
        assert schema["schemas"]["StatusResponse"]["properties"]["memory_profile"]["$ref"] == "#/schemas/MemoryProfile"
        assert schema["schemas"]["StatusResponse"]["properties"]["archive_integrity"]["$ref"] == "#/schemas/ArchiveIntegrityReport"
        assert schema["schemas"]["StatusResponse"]["properties"]["genome_lineage"]["anyOf"][0]["$ref"] == "#/schemas/GenomeLineage"
        assert schema["schemas"]["StatusResponse"]["properties"]["lineage_integrity"]["$ref"] == "#/schemas/LineageIntegrityReport"
        assert schema["schemas"]["LatestEvolutionStatus"]["properties"]["selection_decision"]["anyOf"][0]["$ref"] == "#/schemas/EvolutionSelectionDecision"
        assert schema["schemas"]["BenchmarkResult"]["properties"]["reproducibility_manifest"]["$ref"] == "#/schemas/ReproducibilityManifest"
        assert schema["schemas"]["BenchmarkResult"]["properties"]["benchmark_receipt"]["$ref"] == "#/schemas/ProviderCertificationReceipt"
        assert "benchmark_receipt" in schema["schemas"]["BenchmarkResult"]["required"]
        assert schema["schemas"]["BenchmarkResult"]["properties"]["cases"]["items"]["$ref"] == "#/schemas/BenchmarkCaseResult"
        assert schema["schemas"]["BenchmarkCaseResult"]["properties"]["report_features"]["$ref"] == (
            "#/schemas/BenchmarkCaseReportFeatures"
        )
        benchmark_features = schema["schemas"]["BenchmarkCaseReportFeatures"]["properties"]
        assert "birthplace_geocoded" in benchmark_features
        assert "birthplace_geocoding_quality" in benchmark_features
        assert "deliberation_receipt_present" in benchmark_features
        assert "deliberation_receipt_sha256" in benchmark_features
        assert "deliberation_claim_count" in benchmark_features
        assert "annual_timeline_receipt_present" in benchmark_features
        assert "annual_timeline_receipt_sha256" in benchmark_features
        assert "annual_timeline_row_count" in benchmark_features
        assert "annual_timeline_receipt_bound_to_provenance" in benchmark_features
        assert "monthly_luck_receipt_present" in benchmark_features
        assert "monthly_luck_receipt_sha256" in benchmark_features
        assert "monthly_luck_row_count" in benchmark_features
        assert "monthly_luck_receipt_bound_to_provenance" in benchmark_features
        assert "auspicious_calendar_receipt_present" in benchmark_features
        assert "auspicious_calendar_receipt_sha256" in benchmark_features
        assert "auspicious_calendar_row_count" in benchmark_features
        assert "auspicious_calendar_receipt_bound_to_provenance" in benchmark_features
        assert "external_payload_receipt_domains" in benchmark_features
        assert "external_payload_receipt_count" in benchmark_features
        assert "external_payload_receipts_complete" in benchmark_features
        assert "external_payload_birth_match_statuses" in benchmark_features
        assert benchmark_features["external_payload_birth_match_statuses"]["items"]["$ref"] == (
            "#/schemas/BenchmarkExternalPayloadBirthMatchStatus"
        )
        assert "external_payload_birth_mismatch_count" in benchmark_features
        assert "external_payload_birth_mismatch_domains" in benchmark_features
        assert "external_payload_birth_matches_ok" in benchmark_features
        assert "provider_action_plan_count" in benchmark_features
        assert "provider_action_plan_domains" in benchmark_features
        assert "provider_action_plan_covers_blockers" in benchmark_features
        assert "expected_benchmark_receipt_sha256" in schema["schemas"]["BenchmarkResponse"]["required"]
        assert "benchmark_receipt_matches_expected" in schema["schemas"]["BenchmarkResponse"]["required"]
        assert "benchmark_receipt_mismatch_reason" in schema["schemas"]["BenchmarkResponse"]["required"]
        assert (
            schema["schemas"]["ReleaseManifestResponse"]["properties"]["audit_receipt"]["$ref"]
            == "#/schemas/CapabilityAuditReceipt"
        )
        assert (
            schema["schemas"]["CapabilityAuditReceipt"]["properties"]["material"]["$ref"]
            == "#/schemas/CapabilityAuditReceiptMaterial"
        )
        assert (
            schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["provider_onboarding"]["$ref"]
            == "#/schemas/ProviderOnboardingAuditSummary"
        )
        assert "provider_onboarding" in schema["schemas"]["CapabilityAuditReceiptMaterial"]["required"]
        assert "domain_missing_evidence" in schema["schemas"]["ProviderOnboardingAuditSummary"]["required"]
        assert "missing_evidence_counts" in schema["schemas"]["ProviderOnboardingAuditSummary"]["required"]
        assert (
            schema["schemas"]["ReleaseManifestResponse"]["properties"]["provider_protocols_receipt"]["$ref"]
            == "#/schemas/ProviderProtocolsReceipt"
        )
        assert (
            schema["schemas"]["ReleaseManifestResponse"]["properties"]["provider_onboarding_receipt"]["$ref"]
            == "#/schemas/ProviderOnboardingReceipt"
        )
        assert (
            schema["schemas"]["ReleaseManifestResponse"]["properties"]["release_manifest_receipt"]["$ref"]
            == "#/schemas/ReleaseManifestReceipt"
        )
        assert (
            schema["schemas"]["ReleaseManifestResponse"]["properties"]["readiness_receipt"]["$ref"]
            == "#/schemas/ProductionReadinessReceipt"
        )
        assert (
            schema["schemas"]["ReleaseManifestReceipt"]["properties"]["material"]["$ref"]
            == "#/schemas/ReleaseManifestReceiptMaterial"
        )
        assert (
            schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["outcome_dataset"]["$ref"]
            == "#/schemas/OutcomeDatasetReceiptMaterial"
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
        assert (
            "readiness_deliberation_receipt_coverage"
            in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        )
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
        assert (
            "auspicious_calendar_receipt_coverage"
            in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        )
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
        assert "release_manifest_receipt_matches_expected" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert "release_approval_ready" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert "release_approval_status" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert "release_blockers" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert "ledger_record_requested" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert "ledger_recorded" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert "ledger_record_hash" in schema["schemas"]["ReleaseManifestResponse"]["required"]
        assert (
            schema["schemas"]["ReleaseManifestLedgerResponse"]["properties"]["ledger"]["$ref"]
            == "#/schemas/ReleaseManifestLedgerStatus"
        )
        release_ledger_schema = schema["schemas"]["ReleaseManifestLedgerStatus"]
        assert "latest_record_index" in release_ledger_schema["required"]
        assert release_ledger_schema["properties"]["latest_record_index"]["type"] == ["integer", "null"]
        assert (
            schema["schemas"]["ReleaseManifestDriftResponse"]["properties"]["drift"]["$ref"]
            == "#/schemas/ReleaseManifestDriftStatus"
        )
        assert schema["schemas"]["RollbackResponse"]["properties"]["genome_lineage"]["$ref"] == "#/schemas/GenomeLineage"
        assert "validation_task_fingerprints" in schema["schemas"]["ReproducibilityManifest"]["required"]
        assert "strategy_fingerprints" in schema["schemas"]["ReproducibilityManifest"]["required"]
        assert "cost_governance" in schema["schemas"]["ReproducibilityManifest"]["required"]
        assert (
            schema["schemas"]["ReproducibilityManifest"]["properties"]["cost_governance"]["$ref"]
            == "#/schemas/EvolutionCostGovernance"
        )
        assert "total_candidate_task_evaluations" in schema["schemas"]["EvolutionCostGovernance"]["required"]
        assert schema["schemas"]["ProviderIntegrationPlan"]["properties"]["targets"]["items"]["$ref"] == "#/schemas/ProviderIntegrationTarget"
        assert "protocols" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert "provider_domain" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert "required_provenance_fields" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert "certification_commands" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert "drift_commands" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert "deployment_checklist" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert "bundled_example_policy" in schema["schemas"]["ProviderIntegrationTarget"]["required"]
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["gates"]["items"]["$ref"] == "#/schemas/ProductionReadinessGate"
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["resolution_plan"]["$ref"] == "#/schemas/ProductionResolutionPlan"
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["evidence_materialization"]["$ref"] == "#/schemas/EvidenceMaterialization"
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["current_benchmark"]["$ref"] == "#/schemas/BenchmarkResult"
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["readiness_receipt"]["$ref"]
            == "#/schemas/ProductionReadinessReceipt"
        )
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["provider_readiness"]["$ref"]
            == "#/schemas/ProviderProfileReadiness"
        )
        assert schema["schemas"]["ProductionReadinessReceipt"]["properties"]["material"]["$ref"] == (
            "#/schemas/ProductionReadinessReceiptMaterial"
        )
        assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["current_benchmark"]["$ref"] == (
            "#/schemas/ProductionReadinessBenchmarkSummary"
        )
        assert (
            schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["capability_audit_receipt"]["$ref"]
            == "#/schemas/ProductionReadinessCapabilityAuditReceiptSummary"
        )
        assert (
            schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["provider_certification_ledger"][
                "$ref"
            ]
            == "#/schemas/ProductionReadinessProviderLedgerSummary"
        )
        assert (
            schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["provider_certification_drift"][
                "$ref"
            ]
            == "#/schemas/ProductionReadinessProviderDriftSummary"
        )
        assert "request_provenance_audit" in schema["schemas"]["ProductionReadinessBenchmarkSummary"]["required"]
        assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["birth_profile_audit"]["$ref"] == (
            "#/schemas/ProductionReadinessBenchmarkBirthProfileAudit"
        )
        assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["request_provenance_audit"][
            "$ref"
        ] == "#/schemas/ProductionReadinessBenchmarkRequestProvenanceAudit"
        assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["provider_action_plan_audit"][
            "$ref"
        ] == "#/schemas/ProductionReadinessBenchmarkProviderActionPlanAudit"
        assert schema["schemas"]["ProductionReadinessBenchmarkSummary"]["properties"]["topic_confidence_audit"][
            "$ref"
        ] == "#/schemas/ProductionReadinessBenchmarkTopicConfidenceAudit"
        assert schema["schemas"]["ProductionReadinessBenchmarkBirthProfileAudit"]["properties"]["fingerprints"][
            "items"
        ]["$ref"] == "#/schemas/ProductionReadinessBenchmarkCaseSha256"
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
        assert (
            schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["evidence_materialization"]["$ref"]
            == "#/schemas/ProductionReadinessEvidenceMaterializationSummary"
        )
        assert "failed_count" in schema["schemas"]["ProductionReadinessEvidenceMaterializationSummary"]["required"]
        assert schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["outcome_dataset"]["$ref"] == (
            "#/schemas/OutcomeDatasetReceiptMaterial"
        )
        assert "governance_gate_ids" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
        assert "data_split_record_coverage" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
        assert "statistical_plan" in schema["schemas"]["OutcomeDatasetReceiptMaterial"]["required"]
        assert schema["schemas"]["OutcomeDatasetReceiptMaterial"]["properties"]["data_split_record_coverage"]["$ref"] == (
            "#/schemas/OutcomeDataSplitRecordCoverage"
        )
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["capability_audit_receipt"]["$ref"]
            == "#/schemas/CapabilityAuditReceipt"
        )
        assert "evidence_materialization" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "current_benchmark" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "readiness_receipt" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "capability_audit_receipt" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "expected_audit_receipt_sha256" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "audit_receipt_matches_expected" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "audit_receipt_mismatch_reason" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "expected_readiness_receipt_sha256" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "readiness_receipt_matches_expected" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "readiness_receipt_mismatch_reason" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["provider_integration_plan"]["$ref"] == "#/schemas/ProviderIntegrationPlan"
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["provider_certification_ledger"]["$ref"]
            == "#/schemas/ProviderCertificationLedgerStatus"
        )
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["release_manifest_ledger"]["$ref"]
            == "#/schemas/ReleaseManifestLedgerStatus"
        )
        assert "release_manifest_ledger" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "integrity_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "protocol_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "request_receipt_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "reference_contract_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "command_fingerprint_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "coverage_status" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "latest_record_index" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "protocol_failures" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "request_receipt_failures" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "reference_contract_failures" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        assert "command_fingerprint_failures" in schema["schemas"]["ProviderCertificationLedgerStatus"]["required"]
        ledger_domain_schema = schema["schemas"]["ProviderCertificationLedgerDomainStatus"]
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
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["provider_certification_drift"]["$ref"]
            == "#/schemas/ProviderCertificationDriftStatus"
        )
        assert (
            schema["schemas"]["ProviderCertificationDriftStatus"]["properties"]["checks"]["items"]["$ref"]
            == "#/schemas/ProviderCertificationDriftCheck"
        )
        assert "checked_domains" in schema["schemas"]["ProviderCertificationDriftStatus"]["required"]
        drift_check_schema = schema["schemas"]["ProviderCertificationDriftCheck"]
        assert "expected_provider_request_receipt_sha256" in drift_check_schema["required"]
        assert "current_provider_request_receipt_sha256" in drift_check_schema["required"]
        assert "expected_provider_command_sha256" in drift_check_schema["required"]
        assert "current_provider_command_sha256" in drift_check_schema["required"]
        assert "expected_provider_artifact_sha256" in drift_check_schema["required"]
        assert "current_provider_artifact_sha256" in drift_check_schema["required"]
        assert "provider_request_receipt_matches_expected" in drift_check_schema["required"]
        assert "provider_request_receipt_valid" in drift_check_schema["required"]
        assert "provider_command_fingerprint_matches_expected" in drift_check_schema["required"]
        assert (
            schema["schemas"]["ProviderCertificationDriftResponse"]["properties"]["drift"]["$ref"]
            == "#/schemas/ProviderCertificationDriftStatus"
        )
        assert "domain" in schema["schemas"]["ProviderCertificationDriftResponse"]["required"]
        assert "domain" in schema["schemas"]["ProviderProtocolsResponse"]["required"]
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["outcome_dataset"]["$ref"] == "#/schemas/OutcomeDatasetAuditResponse"
        assert schema["schemas"]["ProductionReadinessResponse"]["properties"]["history_integrity"]["$ref"] == "#/schemas/VersionHistoryIntegrity"
        assert "provider_provenance_valid" in schema["schemas"]["ProviderDomainStatus"]["required"]
        assert "external_payload_receipt_valid" in schema["schemas"]["ProviderDomainStatus"]["required"]
        assert "external_payload_receipt_sha256" in schema["schemas"]["ProviderDomainStatus"]["required"]
        assert "external_payload_birth_match_status" in schema["schemas"]["ProviderDomainStatus"]["required"]
        assert "external_payload_birth_mismatch_fields" in schema["schemas"]["ProviderDomainStatus"]["required"]
        assert "external_payload_declared_birth_profile_sha256" in schema["schemas"]["ProviderDomainStatus"]["required"]
        assert "request_scoped_provenance_required" in schema["schemas"]["StateOfArtAssessment"]["required"]
        assert "production_input_geocoding" in schema["schemas"]["StateOfArtAssessment"]["required"]
        assert "birthplace_geocoding_production_gate" in schema["schemas"]["StateOfArtAssessment"]["required"]
        assert "deliberation_receipt_production_gate" in schema["schemas"]["StateOfArtAssessment"]["required"]
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["state_of_art"]["$ref"] == "#/schemas/StateOfArtAssessment"
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["plan_compliance"]["$ref"] == "#/schemas/PlanCompliance"
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["capabilities"]["$ref"] == (
            "#/schemas/CapabilityFlagMap"
        )
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["request_scoped_provider_contract"]["$ref"] == (
            "#/schemas/RequestScopedProviderContractSummary"
        )
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["provider_protocol_governance"]["$ref"] == (
            "#/schemas/ProviderProtocolGovernanceSummary"
        )
        assert (
            schema["schemas"]["ProviderProtocolGovernanceSummary"]["properties"]["runtime_identity_handshake"]["$ref"]
            == "#/schemas/ProviderProtocolIdentityHandshakeSummary"
        )
        assert "requires_provenance_fields" in schema["schemas"]["RequestScopedProviderContractSummary"]["required"]
        assert "protocol_document_sha256" in schema["schemas"]["ProviderProtocolGovernanceSummary"]["required"]
        assert "ready" in schema["schemas"]["ProviderProtocolIdentityHandshakeSummary"]["required"]
        assert schema["schemas"]["CapabilityAuditReceipt"]["properties"]["material"]["$ref"] == (
            "#/schemas/CapabilityAuditReceiptMaterial"
        )
        assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["capabilities"]["$ref"] == (
            "#/schemas/CapabilityFlagMap"
        )
        assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["request_scoped_provider_contract"][
            "$ref"
        ] == "#/schemas/RequestScopedProviderContractSummary"
        assert schema["schemas"]["CapabilityAuditReceiptMaterial"]["properties"]["provider_protocol_governance"][
            "$ref"
        ] == "#/schemas/ProviderProtocolGovernanceSummary"
        assert "source_receipt" in schema["schemas"]["PlanCompliance"]["required"]
        assert "sha256" in schema["schemas"]["PlanCompliance"]["properties"]["source_receipt"]["required"]
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["evidence_materialization"]["$ref"] == "#/schemas/EvidenceMaterialization"
        assert "evidence_materialization" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert "known_gap_resolution_plan" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert (
            schema["schemas"]["CapabilityAuditResponse"]["properties"]["known_gap_resolution_plan"]["items"]["$ref"]
            == "#/schemas/KnownGapResolutionPlanItem"
        )
        assert "known_gap_resolution_plan_coverage" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert (
            schema["schemas"]["CapabilityAuditResponse"]["properties"]["known_gap_resolution_plan_coverage"]["$ref"]
            == "#/schemas/KnownGapResolutionPlanCoverage"
        )
        assert "KnownGapResolutionPlanCoverage" in schema["schemas"]
        assert "planned_gap_ids" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
        assert "invalid_gate_ids_by_gap" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
        assert "valid_production_gate_ids" in schema["schemas"]["KnownGapResolutionPlanCoverage"]["required"]
        gap_plan_schema = schema["schemas"]["KnownGapResolutionPlanItem"]
        assert "id" in gap_plan_schema["required"]
        assert "gap_id" in gap_plan_schema["required"]
        assert "closure_condition" in gap_plan_schema["required"]
        assert "verification_commands" in gap_plan_schema["required"]
        assert "production_gate_ids" in gap_plan_schema["required"]
        assert "known_gap_resolution_plan" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "known_gap_resolution_plan_coverage" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
        assert (
            schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["known_gap_resolution_plan_coverage"][
                "$ref"
            ]
            == "#/schemas/KnownGapResolutionPlanCoverage"
        )
        assert "known_gap_resolution_plan_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        assert "production_gate_registry_audit" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        assert "provider_protocols_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        assert "provider_onboarding_receipt" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        assert "external_payload_birth_match_coverage" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["required"]
        assert "coverage_complete" in schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"][
            "external_payload_birth_match_coverage"
        ]["required"]
        assert (
            schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["known_gap_resolution_plan_coverage"][
                "$ref"
            ]
            == "#/schemas/KnownGapResolutionPlanCoverage"
        )
        assert (
            schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["production_gate_registry_audit"]["$ref"]
            == "#/schemas/ProductionGateRegistryAudit"
        )
        assert (
            schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["provider_protocols_receipt"]["$ref"]
            == "#/schemas/ProviderProtocolsReceipt"
        )
        assert (
            schema["schemas"]["ReleaseManifestReceiptMaterial"]["properties"]["provider_onboarding_receipt"]["$ref"]
            == "#/schemas/ProviderOnboardingReceipt"
        )
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
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["provider_checks"]["$ref"] == "#/schemas/ProviderChecksResponse"
        assert "provider_protocol_governance" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert "classical_source_refresh" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert (
            schema["schemas"]["CapabilityAuditResponse"]["properties"]["classical_source_refresh"]["$ref"]
            == "#/schemas/ClassicalSourceListAudit"
        )
        assert "classical_source_refresh" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert (
            schema["schemas"]["ProductionReadinessResponse"]["properties"]["classical_source_refresh"]["$ref"]
            == "#/schemas/ClassicalSourceListAudit"
        )
        assert "classical_source_list_path" in schema["schemas"]["ProductionReadinessResponse"]["required"]
        assert "classical_source_refresh" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
        assert (
            schema["schemas"]["ProductionReadinessReceiptMaterial"]["properties"]["classical_source_refresh"]["$ref"]
            == "#/schemas/ClassicalSourceRefreshReceiptSummary"
        )
        assert schema["schemas"]["ClassicalSourcesResponse"]["properties"]["audit"]["$ref"] == (
            "#/schemas/ClassicalSourceListAudit"
        )
        assert schema["schemas"]["ClassicalSourceListAudit"]["properties"]["source_list_receipt"]["$ref"] == (
            "#/schemas/ClassicalSourceListReceipt"
        )
        assert "ClassicalSourceAuditEntry" in schema["schemas"]
        assert "source_audits" in schema["schemas"]["ClassicalSourceListAudit"]["required"]
        assert "source_audits" in schema["schemas"]["ClassicalSourceListReceiptMaterial"]["required"]
        assert schema["schemas"]["ClassicalSourceListAudit"]["properties"]["source_audits"]["items"]["$ref"] == (
            "#/schemas/ClassicalSourceAuditEntry"
        )
        assert "refreshable" in schema["schemas"]["ClassicalSourceAuditEntry"]["required"]
        assert "source_list_receipt_sha256" in schema["schemas"]["ClassicalSourceRefreshReceiptSummary"]["required"]
        assert "classical_source_list_path" in schema["schemas"]["ProductionReadinessReceiptMaterial"]["required"]
        assert "audit_receipt" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert "expected_audit_receipt_sha256" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert "audit_receipt_matches_expected" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert "audit_receipt_mismatch_reason" in schema["schemas"]["CapabilityAuditResponse"]["required"]
        assert (
            schema["schemas"]["CapabilityAuditResponse"]["properties"]["audit_receipt"]["$ref"]
            == "#/schemas/CapabilityAuditReceipt"
        )
        assert schema["schemas"]["CapabilityAuditReceipt"]["properties"]["schema_version"]["const"] == (
            "capability-audit-receipt-v1"
        )
        outcome_schema = schema["schemas"]["OutcomeDatasetManifest"]
        assert outcome_schema["properties"]["consent"]["$ref"] == "#/schemas/OutcomeDatasetConsent"
        assert outcome_schema["properties"]["records"]["items"]["$ref"] == "#/schemas/OutcomeDatasetRecord"
        assert "external_review" in outcome_schema["required"]
        assert "data_split" in outcome_schema["required"]
        assert "label_collection" in outcome_schema["required"]
        assert schema["schemas"]["CapabilityAuditResponse"]["properties"]["outcome_dataset"]["$ref"] == "#/schemas/OutcomeDatasetAudit"
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["quality_task_projection"]["$ref"] == "#/schemas/OutcomeQualityTaskProjection"
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["external_review"]["$ref"] == "#/schemas/OutcomeExternalReview"
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["data_split"]["$ref"] == "#/schemas/OutcomeDataSplit"
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["data_split_record_coverage"]["$ref"] == (
            "#/schemas/OutcomeDataSplitRecordCoverage"
        )
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["label_collection"]["$ref"] == "#/schemas/OutcomeLabelCollection"
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["label_inventory"]["$ref"] == "#/schemas/OutcomeLabelInventory"
        assert (
            schema["schemas"]["OutcomeDatasetAudit"]["properties"]["optimization_policy"]["$ref"]
            == "#/schemas/OutcomeOptimizationPolicy"
        )
        assert schema["schemas"]["OutcomeDatasetAudit"]["properties"]["governance_gates"]["$ref"] == "#/schemas/OutcomeGovernanceGates"
        assert "optimization_policy" in schema["schemas"]["OutcomeDatasetAudit"]["required"]
        assert "observed_label_ids" in schema["schemas"]["OutcomeLabelInventory"]["required"]
        assert "blocked_reason" in schema["schemas"]["OutcomeOptimizationPolicy"]["required"]
        assert "blocking_failures" in schema["schemas"]["OutcomeGovernanceGates"]["required"]
        assert schema["schemas"]["OutcomeDatasetAuditResponse"]["properties"]["audit"]["$ref"] == "#/schemas/OutcomeDatasetAudit"
        assert schema["schemas"]["OutcomeDatasetAuditResponse"]["properties"]["evolution_gate"]["$ref"] == "#/schemas/OutcomeDatasetEvolutionGate"
        assert schema["schemas"]["OutcomeStatisticalPlan"]["properties"]["minimum_sample_size"]["minimum"] == 30
        assert "pre_registered" in schema["schemas"]["OutcomeStatisticalPlan"]["required"]
        assert "registration_id" in schema["schemas"]["OutcomeStatisticalPlan"]["required"]
        assert schema["schemas"]["OutcomeStatisticalPlan"]["properties"]["plan_sha256"]["pattern"] == "^[0-9a-f]{64}$"
        assert schema["schemas"]["OutcomeDatasetRecord"]["properties"]["birth"]["not"] == {"required": ["name"]}
        assert schema["provider_protocols"]["domains"]["astrology"]["env_var"] == "SEMAS_ASTROLOGY_CLI"
        assert schema["provider_protocols"]["domains"]["astrology"]["provenance_env_var"] == "SEMAS_ASTROLOGY_PROVIDER_PROVENANCE"
        assert schema["provider_protocols"]["domains"]["astrology"]["production_requirements"]
        assert "certify-provider astrology" in schema["provider_protocols"]["domains"]["astrology"]["certification_command_template"]
        assert "annual_transits" in schema["provider_protocols"]["domains"]["astrology"]["stdout_schema"]["required"]
        assert "auspicious_end_date" in schema["schemas"]["AnalyzeRequest"]["properties"]
        professional_charts = schema["schemas"]["AnalyzeRequest"]["properties"]["birth"]["properties"]["professional_charts"]
        assert professional_charts["properties"]["xuanze"]["required"] == ["source", "version", "license_or_review"]
        assert "birth_profile" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "request_provenance" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "provider_summary" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "votes" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "deliberation_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "birth_profile"
            ]["$ref"]
            == "#/schemas/BirthProfile"
        )
        birth_profile_schema = schema["schemas"]["BirthProfile"]
        assert "birthplace_normalized" in birth_profile_schema["required"]
        assert "birthplace_region" in birth_profile_schema["required"]
        assert "latitude" in birth_profile_schema["required"]
        assert "longitude" in birth_profile_schema["required"]
        assert "timezone_offset" in birth_profile_schema["required"]
        assert "geocoding_provider" in birth_profile_schema["required"]
        assert "geocoding_quality" in birth_profile_schema["required"]
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "request_provenance"
            ]["$ref"]
            == "#/schemas/RequestProvenance"
        )
        request_context_props = schema["schemas"]["RequestProvenance"]["properties"]["specialist_contexts"][
            "additionalProperties"
        ]["properties"]
        assert "provider_request_receipt_sha256" in request_context_props
        assert "external_payload_receipt_sha256" in request_context_props
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "votes"
            ]["$ref"]
            == "#/schemas/VoteRecord"
        )
        assert schema["schemas"]["VoteRecord"]["properties"]["_claims"]["items"]["$ref"] == "#/schemas/VoteClaim"
        assert schema["schemas"]["VoteClaim"]["properties"]["challenges"]["items"]["$ref"] == "#/schemas/VoteChallenge"
        assert schema["schemas"]["VoteRecord"]["properties"]["_audit"]["$ref"] == "#/schemas/VoteAudit"
        assert "minority_positions_preserved" in schema["schemas"]["VoteAudit"]["required"]
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "deliberation_receipt"
            ]["$ref"]
            == "#/schemas/DeliberationReceipt"
        )
        assert "votes_sha256" in schema["schemas"]["DeliberationReceipt"]["required"]
        assert "source_review_sha256" in schema["schemas"]["DeliberationReceipt"]["required"]
        assert "annual_timeline" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "annual_timeline_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "monthly_luck_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert "auspicious_calendar_receipt" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["required"]
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "annual_luck"
            ]["$ref"]
            == "#/schemas/AnnualLuck"
        )
        assert (
            schema["schemas"]["AnnualLuck"]["properties"]["phase_summary"]["items"]["$ref"]
            == "#/schemas/AnnualPhaseSummary"
        )
        assert schema["schemas"]["AnnualLuck"]["properties"]["rows"]["items"]["$ref"] == "#/schemas/AnnualLuckRow"
        assert schema["schemas"]["AnnualLuckRow"]["properties"]["bazi_evidence"]["$ref"] == (
            "#/schemas/AnnualLuckBaziEvidence"
        )
        assert schema["schemas"]["AnnualLuckBaziEvidence"]["properties"]["annual_ten_gods"]["$ref"] == (
            "#/schemas/AnnualLuckTenGodPair"
        )
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "annual_timeline"
            ]["items"]["$ref"]
            == "#/schemas/AnnualTimelineRow"
        )
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "annual_timeline_receipt"
            ]["$ref"]
            == "#/schemas/AnnualTimelineReceipt"
        )
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "monthly_luck_receipt"
            ]["$ref"]
            == "#/schemas/MonthlyLuckReceipt"
        )
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "monthly_luck"
            ]["$ref"]
            == "#/schemas/MonthlyLuck"
        )
        assert schema["schemas"]["MonthlyLuck"]["properties"]["rows"]["items"]["$ref"] == "#/schemas/MonthlyLuckRow"
        assert schema["schemas"]["MonthlyLuckRow"]["properties"]["bazi_evidence"]["$ref"] == (
            "#/schemas/MonthlyLuckBaziEvidence"
        )
        assert schema["schemas"]["MonthlyLuckRow"]["properties"]["topics"]["properties"]["finance"]["$ref"] == (
            "#/schemas/MonthlyLuckTopic"
        )
        assert (
            schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["properties"]["final_report"]["properties"][
                "auspicious_calendar_receipt"
            ]["$ref"]
            == "#/schemas/AuspiciousCalendarReceipt"
        )
        assert schema["schemas"]["AnnualTimelineReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
            "#/schemas/AnnualTimelineReceiptRowFingerprint"
        )
        assert schema["schemas"]["AnnualTimelineReceipt"]["properties"]["annual_luck_range"]["$ref"] == (
            "#/schemas/AnnualLuckRangeSummary"
        )
        assert "start_year" in schema["schemas"]["AnnualLuckRangeSummary"]["required"]
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
        assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["row_fingerprints"]["items"]["$ref"] == (
            "#/schemas/AuspiciousCalendarReceiptRowFingerprint"
        )
        assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["calendar_range"]["$ref"] == (
            "#/schemas/AuspiciousCalendarRange"
        )
        assert schema["schemas"]["AuspiciousCalendarReceipt"]["properties"]["calendar_basis"]["$ref"] == (
            "#/schemas/AuspiciousCalendarBasis"
        )
        assert schema["schemas"]["AuspiciousDayRow"]["properties"]["recommended_hours"]["items"]["$ref"] == (
            "#/schemas/AuspiciousRecommendedHour"
        )
        assert "specialists" in schema["schemas"]["AnalyzeResponse"]["properties"]["result"]["required"]
        assert schema["schemas"]["VersionHistoryResponse"]["properties"]["versions"]["items"]["$ref"] == "#/schemas/VersionHistoryRow"
        assert schema["schemas"]["VersionHistoryResponse"]["properties"]["history_integrity"]["$ref"] == "#/schemas/VersionHistoryIntegrity"
        assert schema["schemas"]["RollbackRequest"]["required"] == ["to_version"]
        assert "reason" in schema["schemas"]["RollbackRequest"]["properties"]
        assert "rollback_reason" in schema["schemas"]["RollbackResponse"]["required"]
        assert "source_ids" in schema["schemas"]["SpecialistLayer"]["required"]
        assert schema["schemas"]["SpecialistReport"]["properties"]["sources"]["items"]["$ref"] == (
            "#/schemas/SpecialistSource"
        )
        assert "GET /certify-provider" in schema["endpoints"]
        assert "GET /provider-examples" in schema["endpoints"]
        assert "GET /provider-onboarding" in schema["endpoints"]
        assert "GET /provider-drift" in schema["endpoints"]
        assert "GET /provider-ledger" in schema["endpoints"]
        assert "GET /provider-protocols" in schema["endpoints"]
        assert (
            schema["schemas"]["ProviderOnboardingResponse"]["properties"]["provider_onboarding_receipt"]["$ref"]
            == "#/schemas/ProviderOnboardingReceipt"
        )
        assert (
            schema["schemas"]["ProviderOnboardingReceipt"]["properties"]["material"]["$ref"]
            == "#/schemas/ProviderOnboardingReceiptMaterial"
        )
        assert "missing_evidence_by_domain" in schema["schemas"]["ProviderOnboardingReceiptMaterial"]["required"]
        assert "missing_evidence_counts" in schema["schemas"]["ProviderOnboardingReceiptMaterial"]["required"]
        assert (
            schema["schemas"]["ProviderProtocolsResponse"]["properties"]["provider_protocols_receipt"]["$ref"]
            == "#/schemas/ProviderProtocolsReceipt"
        )
        assert (
            schema["schemas"]["ProviderProtocolsReceipt"]["properties"]["material"]["$ref"]
            == "#/schemas/ProviderProtocolsReceiptMaterial"
        )
        assert "GET /history" in schema["endpoints"]
        assert "GET /outcome-dataset" in schema["endpoints"]
        assert "GET /classical-sources" in schema["endpoints"]
        assert "GET /production-readiness" in schema["endpoints"]
        assert "GET /release-manifest" in schema["endpoints"]
        assert "GET /release-ledger" in schema["endpoints"]
        assert "GET /release-drift" in schema["endpoints"]
        assert "POST /analyze" in schema["endpoints"]

        status = _request(base_url, "GET", "/status")
        assert status["coordinator_version"] == 1
        assert "calendar_providers" in status
        assert status["domain_chart_providers"]["astrology"]["external_injection_supported"] is True
        assert status["llm_backend"]["safe_to_report"] is True
        assert status["archive_integrity"]["status"] == "pass"
        assert status["archive_integrity"]["event_count"] == 0
        assert status["genome_lineage"] is None
        assert status["lineage_integrity"]["status"] == "not_applicable"
        assert status["lineage_integrity"]["checked"] is False
        assert status["latest_evolution"] is None

        history = _request(base_url, "GET", "/history")
        assert history["latest_version"] == 1
        assert history["version_count"] == 1
        assert history["versions"][0]["version"] == 1
        assert history["versions"][0]["lineage_present"] is False
        assert history["archive_integrity"]["status"] == "pass"
        assert history["history_integrity"]["status"] == "pass"
        assert history["history_integrity"]["checked_versions"] == 1

        audit = _request(base_url, "GET", "/audit")
        assert audit["status"] == "operational_with_known_gaps"
        assert audit["capabilities"]["http_api"] is True
        assert audit["capabilities"]["classical_text_index"] is True
        assert audit["capabilities"]["classical_source_refresh_governance"] is True
        assert audit["capabilities"]["classical_source_refresh_receipt"] is True
        assert audit["classical_source_refresh"]["status"] == "unconfigured"
        assert "SEMAS_CLASSIC_SOURCE_LIST" in audit["classical_source_refresh"]["failures"][0]
        assert len(audit["classical_source_refresh"]["source_list_receipt"]["sha256"]) == 64
        audit_source_list = tmp_path / "audit_classical_sources.json"
        audit_source_list.write_text(
            json.dumps(
                {
                    "allowed_hosts": ["classics.example"],
                    "sources": [
                        {
                            "name": "locked-classics",
                            "url": "https://classics.example/manifest.json",
                            "sha256": "a" * 64,
                            **_source_governance_fields(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        audit_with_classical_sources = _request(
            base_url,
            "GET",
            f"/audit?classical_source_list={audit_source_list.as_posix()}",
        )
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
        assert audit["capabilities"]["empirical_validation_harness"] is True
        assert audit["capabilities"]["outcome_dataset_cli_api_audit"] is True
        assert audit["capabilities"]["outcome_dataset_external_review_gate"] is True
        assert audit["capabilities"]["outcome_dataset_frozen_holdout_gate"] is True
        assert audit["capabilities"]["outcome_dataset_data_split_records_covered"] is True
        assert audit["capabilities"]["outcome_dataset_label_collection_pre_analysis_gate"] is True
        assert audit["capabilities"]["production_readiness_gate"] is True
        assert audit["capabilities"]["birthplace_geocoding_provenance"] is True
        assert audit["capabilities"]["birthplace_geocoding_production_gate"] is True
        assert audit["capabilities"]["request_scoped_external_payload_receipts"] is True
        assert audit["state_of_art"]["production_input_geocoding"] is True
        assert audit["state_of_art"]["birthplace_geocoding_production_gate"] == "benchmark_birthplaces_geocoded"
        assert audit["state_of_art"]["deliberation_receipt_production_gate"] == (
            "benchmark_deliberation_receipts_bound"
        )
        assert audit["capabilities"]["provider_certification_cli_api"] is True
        assert audit["capabilities"]["provider_protocol_hash_governance"] is True
        assert audit["capabilities"]["provider_protocol_identity_handshake"] is True
        assert audit["capabilities"]["provider_ledger_protocol_stale_gate"] is True
        assert audit["capabilities"]["provider_ledger_latest_record_binding"] is True
        assert audit["capabilities"]["provider_certification_command_fingerprint_governance"] is True
        assert audit["capabilities"]["release_manifest_governance"] is True
        assert audit["capabilities"]["release_manifest_ledger_hash_chain"] is True
        assert audit["capabilities"]["release_manifest_ledger_latest_record_binding"] is True
        assert audit["capabilities"]["release_manifest_ledger_receipt_material_binding"] is True
        assert audit["capabilities"]["release_manifest_ledger_readiness_gate"] is True
        assert audit["capabilities"]["release_manifest_drift_gate"] is True
        assert audit["provider_protocol_governance"]["status"] == "ready"
        assert audit["provider_protocol_governance"]["runtime_identity_handshake"]["ready"] is True
        assert "protocol_identity" in audit["provider_protocol_governance"]["receipt_material_fields"]
        assert audit["audit_receipt"]["schema_version"] == "capability-audit-receipt-v1"
        assert len(audit["audit_receipt"]["sha256"]) == 64
        plan_receipt = audit["plan_compliance"]["source_receipt"]
        assert plan_receipt["path"] == "plan_mingli5agents.md"
        assert plan_receipt["exists"] is True
        assert plan_receipt["readable"] is True
        assert plan_receipt["encoding"] == "utf-8"
        assert plan_receipt["section_heading_count"] == 10
        assert len(plan_receipt["sha256"]) == 64
        assert audit["audit_receipt"]["material"]["plan_compliance"]["source_receipt"] == plan_receipt
        assert audit["expected_audit_receipt_sha256"] is None
        assert audit["audit_receipt_matches_expected"] is None
        assert audit["audit_receipt_mismatch_reason"] == ""
        assert audit["audit_receipt"]["material"]["provider_protocol_governance"]["protocol_hash"] == audit[
            "provider_protocol_governance"
        ]["protocol_hash"]
        assert (
            audit["audit_receipt"]["material"]["provider_protocol_governance"]["runtime_identity_handshake"]["ready"]
            is True
        )
        assert audit["audit_receipt"]["material"]["capabilities"]["birthplace_geocoding_provenance"] is True
        matched_audit = _request(
            base_url,
            "GET",
            f"/audit?expected_audit_receipt_sha256={audit['audit_receipt']['sha256']}",
        )
        assert matched_audit["audit_receipt_matches_expected"] is True
        matched_source_audit = _request(
            base_url,
            "GET",
            (
                f"/audit?classical_source_list={audit_source_list.as_posix()}"
                f"&expected_audit_receipt_sha256={audit_with_classical_sources['audit_receipt']['sha256']}"
            ),
        )
        assert matched_source_audit["audit_receipt_matches_expected"] is True
        assert matched_audit["audit_receipt_mismatch_reason"] == ""
        mismatched_audit = _request(base_url, "GET", f"/audit?expected_audit_receipt_sha256={'0' * 64}")
        assert mismatched_audit["audit_receipt_matches_expected"] is False
        assert mismatched_audit["audit_receipt_mismatch_reason"] == "audit receipt sha256 does not match expected value"
        assert audit["capabilities"]["version_history_lineage_view"] is True
        assert "llm_backend_configured" in audit["capabilities"]
        assert audit["llm_backend"]["client"] in {"StubLLMClient", "OpenAILLMClient"}
        assert audit["capabilities"]["xuanze_huangdao_scaffold"] is True
        assert audit["classical_text_index"]["record_count"] >= 9
        assert audit["empirical_validation"]["predictive_truth_cases"] == 0
        assert any(gap["id"] == "astronomical_ephemeris" for gap in audit["known_gaps"])

        providers = _request(base_url, "GET", "/providers")
        assert providers["reference_chart_checks"]["passed"] is True
        assert "astrology_swiss_ephemeris" in providers["checks"]
        assert "astrology_json_cli" in providers["checks"]
        assert "xuanze_json_cli" in providers["checks"]
        assert providers["integration_plan"]["total_targets"] == 5
        assert providers["integration_plan"]["reference_contracts_passed"] is True

        live_providers = _request(base_url, "GET", "/providers?live=1")
        assert live_providers["live"] is True
        assert live_providers["integration_plan"]["live_requested"] is True

        production_providers = _request(base_url, "GET", "/providers?profile=production")
        assert production_providers["profile"] == "production"
        assert production_providers["profile_readiness"]["status"] == "production_blocked"
        assert production_providers["integration_plan"]["status"] == "production_blocked"
        assert "ziwei_professional_engine" in production_providers["integration_plan"]["blocked_targets"]

        empty_ledger = _request(base_url, "GET", "/provider-ledger")
        assert empty_ledger["ledger"]["exists"] is False
        assert empty_ledger["ledger"]["integrity_status"] == "fail"
        assert empty_ledger["ledger"]["coverage_status"] == "incomplete"
        assert empty_ledger["ledger"]["record_count"] == 0
        assert empty_ledger["ledger"]["latest_record_index"] is None
        assert set(empty_ledger["ledger"]["missing_domains"]) == {"astrology", "qimen", "xuanze", "ziwei"}
        empty_drift = _request(base_url, "GET", "/provider-drift?live=0")
        assert empty_drift["drift"]["status"] == "not_checked"
        assert empty_drift["ledger"]["record_count"] == 0
        empty_ziwei_drift = _request(base_url, "GET", "/provider-drift?live=0&domain=ziwei")
        assert empty_ziwei_drift["domain"] == "ziwei"
        assert empty_ziwei_drift["drift"]["checked_domains"] == ["ziwei"]
        protocols = _request(base_url, "GET", "/provider-protocols")
        assert protocols["domain"] is None
        assert set(protocols["provider_protocols"]["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
        assert protocols["provider_protocols_receipt"]["material"]["protocol_hash"] == protocols["provider_protocols"][
            "protocol_hash"
        ]
        assert protocols["provider_protocols_receipt"]["material"]["domain_count"] == 4
        assert len(protocols["provider_protocols_receipt"]["sha256"]) == 64
        assert protocols["provider_protocols"]["domains"]["qimen"]["env_var"] == "SEMAS_QIMEN_CLI"
        assert "provider-drift --domain qimen" in protocols["provider_protocols"]["domains"]["qimen"]["drift_command_template"]
        assert protocols["provider_protocols"]["domains"]["qimen"]["sample_stdin"]["birth"]["birth_date"] == "1990-04-12"
        assert len(protocols["provider_protocols"]["domains"]["qimen"]["sample_stdout"]["palaces"]) == 9
        assert protocols["provider_protocols"]["domains"]["qimen"]["sample_stdout_contract"]["valid"] is True
        ziwei_protocols = _request(base_url, "GET", "/provider-protocols?domain=ziwei")
        assert ziwei_protocols["domain"] == "ziwei"
        assert set(ziwei_protocols["provider_protocols"]["domains"]) == {"ziwei"}
        assert ziwei_protocols["provider_protocols_receipt"]["material"]["domain"] == "ziwei"
        assert ziwei_protocols["provider_protocols_receipt"]["material"]["domain_count"] == 1
        assert set(ziwei_protocols["provider_protocols_receipt"]["material"]["domain_protocol_hashes"]) == {"ziwei"}
        assert ziwei_protocols["provider_protocols"]["domains"]["ziwei"]["env_var"] == "SEMAS_ZIWEI_CLI"
        assert ziwei_protocols["provider_protocols"]["domains"]["ziwei"]["required_provenance_fields"] == [
            "provider",
            "version",
            "source",
            "license_or_review",
        ]
        assert ziwei_protocols["provider_protocols"]["domains"]["ziwei"]["sample_stdin"]["birth"]["birth_time"] == "09:20"
        assert len(ziwei_protocols["provider_protocols"]["domains"]["ziwei"]["sample_stdout"]["palaces"]) == 12
        assert ziwei_protocols["provider_protocols"]["domains"]["ziwei"]["sample_stdout_contract"]["valid"] is True

        certification = _request(base_url, "GET", "/certify-provider?domain=qimen&live=0")
        assert certification["domain"] == "qimen"
        assert certification["status"] == "blocked"
        assert certification["env_var"] == "SEMAS_QIMEN_CLI"
        assert certification["live_requested"] is False
        assert len(certification["certification_receipt"]["sha256"]) == 64
        assert certification["expected_receipt_sha256"] is None
        assert certification["receipt_matches_expected"] is None
        assert certification["ledger_record_requested"] is False
        assert certification["ledger_recorded"] is False

        reviewed_provider = tmp_path / "reviewed_ziwei_provider.py"
        reviewed_provider.write_text(
            Path("examples/mingli_5agents/providers/ziwei_json_cli_example.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        provenance = (
            "provider=reviewed-ziwei-provider; version=1.0; "
            "source=internal review; license_or_review=licensed fixture"
        )
        certification = _request(
            base_url,
            "GET",
            "/certify-provider"
            f"?domain=ziwei&command={quote(f'{sys.executable} {reviewed_provider}')}"
            f"&provenance={quote(provenance)}",
        )
        assert certification["status"] == "certified"
        assert certification["command_override_used"] is True
        assert certification["provenance_override_used"] is True
        assert certification["live_check"]["passed"] is True
        assert certification["certification_receipt"]["material"]["certified"] is True
        receipt_sha256 = certification["certification_receipt"]["sha256"]
        certification = _request(
            base_url,
            "GET",
            "/certify-provider"
            f"?domain=ziwei&command={quote(f'{sys.executable} {reviewed_provider}')}"
            f"&provenance={quote(provenance)}"
            f"&expected_receipt_sha256={receipt_sha256}&record=1",
        )
        assert certification["receipt_matches_expected"] is True
        assert certification["receipt_mismatch_reason"] == ""
        assert certification["ledger_record_requested"] is True
        assert certification["ledger_recorded"] is True
        assert certification["ledger_record_index"] == 0
        assert len(certification["ledger_record_hash"]) == 64
        ledger = json.loads(Path(certification["ledger_record_path"]).read_text(encoding="utf-8"))
        assert ledger["latest_record_index"] == 0
        assert ledger["records"][0]["receipt_sha256"] == receipt_sha256
        ledger_status = _request(base_url, "GET", "/provider-ledger")
        assert ledger_status["ledger"]["exists"] is True
        assert ledger_status["ledger"]["integrity_status"] == "pass"
        assert ledger_status["ledger"]["protocol_status"] == "current"
        assert ledger_status["ledger"]["protocol_failures"] == []
        assert ledger_status["ledger"]["request_receipt_status"] == "current"
        assert ledger_status["ledger"]["request_receipt_failures"] == []
        assert ledger_status["ledger"]["coverage_status"] == "incomplete"
        assert ledger_status["ledger"]["record_count"] == 1
        assert ledger_status["ledger"]["latest_record_index"] == 0
        assert ledger_status["ledger"]["covered_domains"] == ["ziwei"]
        assert ledger_status["ledger"]["domains"]["ziwei"]["latest_receipt_sha256"] == receipt_sha256
        assert ledger_status["ledger"]["domains"]["ziwei"]["protocol_matches_current"] is True
        assert ledger_status["ledger"]["domains"]["ziwei"]["request_receipt_present"] is True
        assert ledger_status["ledger"]["domains"]["ziwei"]["request_receipt_valid"] is True
        assert ledger_status["ledger"]["domains"]["ziwei"]["request_receipt_protocol_echo_matches"] is True
        assert len(ledger_status["ledger"]["domains"]["ziwei"]["latest_provider_request_receipt_sha256"]) == 64
        assert len(ledger_status["ledger"]["domains"]["ziwei"]["request_receipt_birth_profile_sha256"]) == 64
        ledger_path = Path(certification["ledger_record_path"])
        provider_ledger_with_bad_index = json.loads(ledger_path.read_text(encoding="utf-8"))
        provider_ledger_with_bad_index["latest_record_index"] = 99
        ledger_path.write_text(json.dumps(provider_ledger_with_bad_index, ensure_ascii=False), encoding="utf-8")
        tampered_index_provider_ledger = _request(base_url, "GET", "/provider-ledger")
        assert tampered_index_provider_ledger["ledger"]["integrity_status"] == "fail"
        assert any(
            "latest_record_index does not match last record" in item
            for item in tampered_index_provider_ledger["ledger"]["failures"]
        )
        ledger_path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")

        outcome_unconfigured = _request(base_url, "GET", "/outcome-dataset")
        assert outcome_unconfigured["audit"]["status"] == "not_configured"
        assert outcome_unconfigured["evolution_gate"]["passed"] is True

        example_manifest = Path("examples/mingli_5agents/providers/outcome_dataset_manifest_example.json")
        outcome = _request(base_url, "GET", f"/outcome-dataset?manifest={example_manifest.as_posix()}")
        assert outcome["audit"]["status"] == "ready_for_review"
        assert outcome["audit"]["valid"] is True
        assert outcome["audit"]["quality_task_projection"]["projected_task_count"] == 1
        assert outcome["evolution_gate"]["passed"] is True
        assert outcome["evolution_gate"]["predictive_optimization_enabled"] is False
        classical_unconfigured = _request(base_url, "GET", "/classical-sources")
        assert classical_unconfigured["configured"] is False
        assert classical_unconfigured["audit"]["status"] == "unconfigured"
        assert len(classical_unconfigured["audit"]["source_list_receipt"]["sha256"]) == 64
        assert classical_unconfigured["production_gate"]["passed"] is False
        assert "SEMAS_CLASSIC_SOURCE_LIST" in classical_unconfigured["production_gate"]["details"][0]
        source_list = tmp_path / "classical_sources.json"
        source_list.write_text(
            json.dumps(
                {
                    "allowed_hosts": ["classics.example"],
                    "sources": [
                        {
                            "name": "locked-classics",
                            "url": "https://classics.example/manifest.json",
                            "sha256": "a" * 64,
                            **_source_governance_fields(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        classical_sources = _request(base_url, "GET", f"/classical-sources?source_list={source_list.as_posix()}")
        assert classical_sources["configured"] is True
        assert classical_sources["audit"]["status"] == "ready"
        assert classical_sources["audit"]["locked_source_count"] == 1
        assert classical_sources["audit"]["source_audits"][0]["refreshable"] is True
        assert classical_sources["audit"]["source_list_receipt"]["material"]["valid"] is True
        assert classical_sources["audit"]["source_list_receipt"]["material"]["source_audits"] == classical_sources[
            "audit"
        ]["source_audits"]
        assert classical_sources["production_gate"]["passed"] is True

        readiness_unconfigured = _request(base_url, "GET", "/production-readiness")
        assert readiness_unconfigured["status"] == "production_blocked"
        assert readiness_unconfigured["production_ready"] is False
        unconfigured_blockers = {item["gate"] for item in readiness_unconfigured["blockers"]}
        assert "provider_profile_ready" in unconfigured_blockers
        assert "outcome_dataset_configured" in unconfigured_blockers
        assert "provider_certification_ledger_available" not in unconfigured_blockers
        assert "provider_certification_ledger_integrity" not in unconfigured_blockers
        assert "provider_certification_protocols_current" not in unconfigured_blockers
        assert "provider_certification_request_receipts_current" not in unconfigured_blockers
        assert "provider_certification_command_fingerprints_current" not in unconfigured_blockers
        assert "provider_certification_ledger_covers_domains" in unconfigured_blockers
        assert "provider_certification_receipts_current" in unconfigured_blockers
        assert "release_manifest_ledger_integrity" not in unconfigured_blockers
        assert readiness_unconfigured["release_manifest_ledger"]["exists"] is False
        assert readiness_unconfigured["release_manifest_ledger"]["latest_record_index"] is None
        evidence_gate = next(item for item in readiness_unconfigured["gates"] if item["id"] == "implemented_evidence_materialized")
        assert evidence_gate["passed"] is True
        assert readiness_unconfigured["evidence_materialization"]["failed_count"] == 0
        benchmark_gate = next(item for item in readiness_unconfigured["gates"] if item["id"] == "current_benchmark_passed")
        assert benchmark_gate["passed"] is True
        assert readiness_unconfigured["current_benchmark"]["passed_rate"] == 1.0
        assert len(readiness_unconfigured["readiness_receipt"]["sha256"]) == 64
        assert len(readiness_unconfigured["capability_audit_receipt"]["sha256"]) == 64
        assert readiness_unconfigured["audit_receipt_matches_expected"] is None
        assert (
            readiness_unconfigured["readiness_receipt"]["material"]["capability_audit_receipt"]["sha256"]
            == readiness_unconfigured["capability_audit_receipt"]["sha256"]
        )
        assert readiness_unconfigured["provider_certification_drift"]["status"] == "not_checked"
        assert readiness_unconfigured["provider_certification_ledger"]["record_count"] == 1
        assert readiness_unconfigured["provider_certification_ledger"]["command_fingerprint_status"] == "current"
        assert readiness_unconfigured["provider_certification_ledger"]["command_fingerprint_failures"] == []
        assert (
            readiness_unconfigured["readiness_receipt"]["material"]["provider_certification_ledger"][
                "latest_record_hash"
            ]
            == readiness_unconfigured["provider_certification_ledger"]["latest_record_hash"]
        )
        assert (
            readiness_unconfigured["readiness_receipt"]["material"]["provider_certification_ledger"][
                "latest_record_index"
            ]
            == 0
        )
        assert (
            readiness_unconfigured["readiness_receipt"]["material"]["provider_certification_ledger"][
                "request_receipt_status"
            ]
            == "current"
        )
        assert readiness_unconfigured["provider_certification_ledger"]["missing_domains"] == [
            "astrology",
            "qimen",
            "xuanze",
        ]
        assert readiness_unconfigured["resolution_plan"]["status"] == "actions_required"
        assert readiness_unconfigured["classical_source_refresh"]["status"] == "unconfigured"
        assert (
            readiness_unconfigured["readiness_receipt"]["material"]["classical_source_refresh"]["status"]
            == "unconfigured"
        )
        assert any(
            item["id"] == "configure_outcome_dataset_manifest"
            for item in readiness_unconfigured["resolution_plan"]["steps"]
        )
        assert any(
            item["id"] == "configure_classical_source_refresh"
            for item in readiness_unconfigured["resolution_plan"]["steps"]
        )

        readiness = _request(
            base_url,
            "GET",
            (
                f"/production-readiness?manifest={example_manifest.as_posix()}"
                f"&classical_source_list={source_list.as_posix()}"
            ),
        )
        assert readiness["status"] == "production_blocked"
        assert readiness["production_ready"] is False
        assert readiness["outcome_dataset"]["audit"]["status"] == "ready_for_review"
        assert readiness["history_integrity"]["status"] == "pass"
        readiness_blockers = {item["gate"] for item in readiness["blockers"]}
        assert "outcome_dataset_configured" not in readiness_blockers
        assert "outcome_dataset_data_split_records_covered" not in readiness_blockers
        split_coverage_gate = next(
            item for item in readiness["gates"] if item["id"] == "outcome_dataset_data_split_records_covered"
        )
        assert split_coverage_gate["passed"] is True
        assert "provider_profile_ready" in readiness_blockers
        assert "provider_certification_ledger_integrity" not in readiness_blockers
        assert "provider_certification_protocols_current" not in readiness_blockers
        assert "provider_certification_command_fingerprints_current" not in readiness_blockers
        assert "provider_certification_ledger_covers_domains" in readiness_blockers
        assert "provider_certification_receipts_current" in readiness_blockers
        assert "release_manifest_ledger_integrity" not in readiness_blockers
        evidence_gate = next(item for item in readiness["gates"] if item["id"] == "implemented_evidence_materialized")
        assert evidence_gate["passed"] is True
        known_gap_plan_gate = next(item for item in readiness["gates"] if item["id"] == "known_gap_resolution_plan_covered")
        assert known_gap_plan_gate["passed"] is True
        assert "known_gap_resolution_plan_covered" not in readiness_blockers
        assert readiness["evidence_materialization"]["status"] == "passed"
        assert readiness["evidence_materialization"]["failed_count"] == 0
        assert readiness["evidence_materialization"]["unchecked_count"] == 0
        assert readiness["evidence_materialization"]["passed_count"] == readiness["evidence_materialization"]["total_evidence"]
        classical_gate = next(item for item in readiness["gates"] if item["id"] == "classical_source_refresh_ready")
        assert classical_gate["passed"] is True
        assert classical_gate["details"] == []
        assert "classical_source_refresh_ready" not in readiness_blockers
        assert readiness["classical_source_refresh"]["status"] == "ready"
        assert readiness["classical_source_list_path"].replace("\\", "/") == source_list.as_posix()
        assert (
            readiness["readiness_receipt"]["material"]["classical_source_refresh"]["source_list_receipt_sha256"]
            == readiness["classical_source_refresh"]["source_list_receipt"]["sha256"]
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
        assert len(registry_audit["registry_audit_sha256"]) == 64
        assert readiness["current_benchmark"]["reference_charts"]["passed"] is True
        assert len(readiness["readiness_receipt"]["sha256"]) == 64
        assert len(readiness["capability_audit_receipt"]["sha256"]) == 64
        readiness_gate_ids = {item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]}
        assert "known_gap_resolution_plan_covered" in readiness_gate_ids
        assert "blocked_capability_coverage_complete" in readiness_gate_ids
        assert "production_gate_registry_current" in readiness_gate_ids
        assert (
            readiness["readiness_receipt"]["material"]["production_gate_registry_audit"]
            == readiness["production_gate_registry_audit"]
        )
        gap_plan_coverage = readiness["readiness_receipt"]["material"]["known_gap_resolution_plan_coverage"]
        assert gap_plan_coverage["coverage_complete"] is True
        assert gap_plan_coverage["known_gap_count"] == len(readiness["known_gap_ids"])
        assert gap_plan_coverage["covered_count"] == gap_plan_coverage["known_gap_count"]
        assert gap_plan_coverage["planned_gap_ids"] == sorted(readiness["known_gap_ids"])
        assert gap_plan_coverage["invalid_gate_ids_by_gap"] == {}
        assert "provider_certification_ledger_covers_domains" in gap_plan_coverage["valid_production_gate_ids"]
        assert "ziwei_qimen_calculation_basis_audit_contract" in gap_plan_coverage["valid_production_gate_ids"]
        assert "astrology_ephemeris_audit_contract" in gap_plan_coverage["valid_production_gate_ids"]
        assert "xuanze_rule_table_audit_contract" in gap_plan_coverage["valid_production_gate_ids"]
        assert "classical_source_latest_refresh_receipt_present" in gap_plan_coverage["valid_production_gate_ids"]
        assert readiness["readiness_receipt"]["material"]["current_benchmark"]["passed_rate"] == 1.0
        birth_audit = readiness["readiness_receipt"]["material"]["current_benchmark"]["birth_profile_audit"]
        assert birth_audit["case_count"] == len(readiness["current_benchmark"]["cases"])
        assert birth_audit["covered_count"] == birth_audit["case_count"]
        assert birth_audit["geocoded_count"] == birth_audit["case_count"]
        assert birth_audit["unresolved_geocoding"] == []
        assert len(birth_audit["fingerprints"]) == birth_audit["case_count"]
        assert all(len(item["sha256"]) == 64 for item in birth_audit["fingerprints"])
        request_audit = readiness["readiness_receipt"]["material"]["current_benchmark"]["request_provenance_audit"]
        assert request_audit["case_count"] == len(readiness["current_benchmark"]["cases"])
        assert request_audit["covered_count"] == request_audit["case_count"]
        assert len(request_audit["chains"]) == request_audit["case_count"]
        assert all(len(item["sha256"]) == 64 for item in request_audit["chains"])
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
        birth_match_gate = next(
            item for item in readiness["gates"] if item["id"] == "benchmark_external_payload_birth_matches"
        )
        assert birth_match_gate["passed"] is True
        assert "benchmark_external_payload_birth_matches" in {
            item["id"] for item in readiness["readiness_receipt"]["material"]["gates"]
        }
        assert readiness["readiness_receipt"]["material"]["evidence_materialization"]["failed_count"] == 0
        assert (
            readiness["readiness_receipt"]["material"]["classical_source_refresh"]["status"]
            == readiness["classical_source_refresh"]["status"]
        )
        assert readiness["readiness_receipt"]["material"]["capability_audit_receipt"]["sha256"] == readiness[
            "capability_audit_receipt"
        ]["sha256"]
        assert (
            readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["latest_record_hash"]
            == readiness["provider_certification_ledger"]["latest_record_hash"]
        )
        assert readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["latest_record_index"] == 0
        assert readiness["provider_certification_ledger"]["command_fingerprint_status"] == "current"
        assert readiness["provider_certification_ledger"]["command_fingerprint_failures"] == []
        assert (
            readiness["readiness_receipt"]["material"]["provider_certification_ledger"]["command_fingerprint_status"]
            == "current"
        )
        readiness_outcome_material = readiness["readiness_receipt"]["material"]["outcome_dataset"]
        assert readiness_outcome_material["content_hash"] == readiness["outcome_dataset"]["audit"]["content_hash"]
        assert readiness_outcome_material["data_split_record_coverage"]["coverage_complete"] is True
        assert len(readiness_outcome_material["data_split_record_coverage"]["split_fingerprint"]) == 64
        assert readiness_outcome_material["external_review"]["reviewed"] is True
        assert readiness_outcome_material["data_split"]["frozen"] is True
        assert readiness_outcome_material["label_collection"]["collected_before_analysis"] is True
        assert "external_review_approved" in readiness_outcome_material["governance_gate_ids"]
        source_gate = next(item for item in readiness["gates"] if item["id"] == "classical_source_refresh_ready")
        assert source_gate["passed"] is True
        assert (
            readiness["readiness_receipt"]["material"]["classical_source_list_path"]
            .replace("\\", "/")
            == source_list.as_posix()
        )
        matched_readiness = _request(
            base_url,
            "GET",
            (
                f"/production-readiness?manifest={example_manifest.as_posix()}"
                f"&classical_source_list={source_list.as_posix()}"
                f"&expected_readiness_receipt_sha256={readiness['readiness_receipt']['sha256']}"
            ),
        )
        assert matched_readiness["readiness_receipt_matches_expected"] is True
        assert matched_readiness["readiness_receipt_mismatch_reason"] == ""
        matched_audit_readiness = _request(
            base_url,
            "GET",
            (
                f"/production-readiness?manifest={example_manifest.as_posix()}"
                f"&classical_source_list={source_list.as_posix()}"
                f"&expected_audit_receipt_sha256={readiness['capability_audit_receipt']['sha256']}"
            ),
        )
        assert matched_audit_readiness["audit_receipt_matches_expected"] is True
        assert matched_audit_readiness["audit_receipt_mismatch_reason"] == ""
        mismatched_audit_readiness = _request(
            base_url,
            "GET",
            f"/production-readiness?manifest={example_manifest.as_posix()}&expected_audit_receipt_sha256={'0' * 64}",
        )
        assert mismatched_audit_readiness["audit_receipt_matches_expected"] is False
        assert mismatched_audit_readiness["audit_receipt_mismatch_reason"] == (
            "audit receipt sha256 does not match expected value"
        )
        assert "capability_audit_receipt_current" in {
            item["gate"] for item in mismatched_audit_readiness["blockers"]
        }
        readiness_steps = {item["id"] for item in readiness["resolution_plan"]["steps"]}
        assert "configure_classical_source_refresh" not in readiness_steps
        assert "complete_qimen_professional_engine" in readiness_steps
        assert "record_qimen_provider_receipt" in readiness_steps

        analyze = _request(
            base_url,
            "POST",
            "/analyze",
            {
                "birth": {
                    "name": "API Person",
                    "birth_date": "1991-05-20",
                    "birth_time": "10:15",
                    "gender": "unspecified",
                    "birthplace": "Suzhou",
                },
                "annual_start_year": 2024,
                "annual_end_year": 2026,
                "monthly_years": [2026],
                "llm_synthesis": False,
            },
        )
        assert analyze["agent_version"] == 1
        assert analyze["metrics"]["report_schema"] == 1.0
        assert analyze["result"]["final_report"]["annual_luck"]["range"]["count"] == 3
        assert analyze["result"]["final_report"]["annual_luck"]["phase_summary"][0]["source"] == "annual_luck.rows"
        assert analyze["result"]["final_report"]["annual_luck"]["phase_summary"][0]["source_row_indexes"] == [0, 1, 2]
        assert len(analyze["result"]["final_report"]["annual_timeline"]) == 3
        assert analyze["result"]["final_report"]["annual_timeline"][0]["source"] == "annual_luck.rows"

        evolve = _request(
            base_url,
            "POST",
            "/evolve",
            {
                "input": {
                    "birth": {
                        "name": "API Evolve Person",
                        "birth_date": "1991-05-20",
                        "birth_time": "10:15",
                        "gender": "unspecified",
                        "birthplace": "Suzhou",
                    }
                },
                "feedback": {
                    "feedback": {
                        "satisfaction": 0.5,
                        "corrections": ["needs stronger source labels"],
                    }
                },
                "validate_on_input": True,
            },
        )
        assert evolve["accepted"] is True
        assert evolve["selection_decision"]["accepted"] is True
        assert evolve["selection_decision"]["validation_task_count"] == evolve["validation_case_count"]

        evolved_status = _request(base_url, "GET", "/status")
        assert evolved_status["coordinator_version"] == 2
        assert evolved_status["latest_evolution"]["accepted"] is True
        assert evolved_status["latest_evolution"]["selected"] == evolve["selected"]
        assert evolved_status["archive_integrity"]["status"] == "pass"
        assert evolved_status["archive_integrity"]["latest_hash"] == evolved_status["latest_evolution"]["archive_hash"]
        assert evolved_status["genome_lineage"]["archive_hash"] == evolved_status["latest_evolution"]["archive_hash"]
        assert evolved_status["genome_lineage"]["accepted_genome_version"] == 2
        assert len(evolved_status["genome_lineage"]["genome_fingerprint"]) == 64
        assert evolved_status["lineage_integrity"]["status"] == "pass"
        assert evolved_status["lineage_integrity"]["genome_fingerprint_matches"] is True
        assert evolved_status["lineage_integrity"]["selection_decision_matches"] is True
        assert evolved_status["latest_evolution"]["selection_decision"]["accepted"] is True
        assert evolved_status["latest_evolution"]["reproducibility_manifest"]["run_type"] == "population_evolution"

        evolved_history = _request(base_url, "GET", "/history")
        assert evolved_history["latest_version"] == 2
        assert [item["version"] for item in evolved_history["versions"]] == [1, 2]
        assert evolved_history["versions"][-1]["lineage_event"] == "population_evolution"
        assert evolved_history["versions"][-1]["archive_event_found"] is True
        assert evolved_history["history_integrity"]["status"] == "pass"

        benchmark = _request(base_url, "POST", "/benchmark", {})
        assert benchmark["benchmark"]["genome_version"] == 2
        assert benchmark["benchmark"]["cases"]
        assert benchmark["benchmark"]["empirical_validation"]["status"] == "ready_non_predictive"
        assert len(benchmark["benchmark"]["benchmark_receipt"]["sha256"]) == 64
        assert benchmark["benchmark"]["benchmark_receipt"]["material"]["genome_version"] == 2
        assert benchmark["benchmark"]["benchmark_receipt"]["material"]["passed_rate"] == benchmark["benchmark"]["passed_rate"]
        assert benchmark["benchmark_receipt_matches_expected"] is None
        matched_benchmark = _request(
            base_url,
            "POST",
            "/benchmark",
            {"expected_benchmark_receipt_sha256": benchmark["benchmark"]["benchmark_receipt"]["sha256"]},
        )
        assert matched_benchmark["benchmark_receipt_matches_expected"] is True
        assert matched_benchmark["benchmark_receipt_mismatch_reason"] == ""

        release = _request(base_url, "GET", f"/release-manifest?manifest={example_manifest.as_posix()}")
        assert release["status"] == "release_manifest_ready"
        assert release["release_approval_ready"] is False
        assert release["release_approval_status"] == "release_blocked"
        assert any(item["gate"] == "production_ready" for item in release["release_blockers"])
        assert release["release_manifest_receipt"]["material"]["release_approval_ready"] == release[
            "release_approval_ready"
        ]
        assert release["release_manifest_receipt"]["material"]["release_blockers"] == release["release_blockers"]
        assert release["coordinator_version"] == 2
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
        assert len(release["provider_protocols_receipt"]["sha256"]) == 64
        assert release["release_manifest_receipt"]["material"]["provider_onboarding_receipt_sha256"] == release[
            "provider_onboarding_receipt"
        ]["sha256"]
        assert release["release_manifest_receipt"]["material"]["provider_onboarding_receipt"] == release[
            "provider_onboarding_receipt"
        ]
        assert release["release_manifest_receipt"]["material"]["provider_protocols_receipt_sha256"] == release[
            "provider_protocols_receipt"
        ]["sha256"]
        assert release["release_manifest_receipt"]["material"]["provider_protocols_receipt"] == release[
            "provider_protocols_receipt"
        ]
        assert len(release["benchmark_receipt"]["sha256"]) == 64
        assert len(release["readiness_receipt"]["sha256"]) == 64
        assert len(release["release_manifest_receipt"]["sha256"]) == 64
        assert release["release_manifest_receipt"]["material"]["audit_receipt_sha256"] == release["audit_receipt"]["sha256"]
        assert release["release_manifest_receipt"]["material"]["benchmark_receipt_sha256"] == release[
            "benchmark_receipt"
        ]["sha256"]
        assert release["release_manifest_receipt"]["material"]["readiness_receipt_sha256"] == release[
            "readiness_receipt"
        ]["sha256"]
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
        assert annual_timeline_coverage["bound_count"] == readiness_request_audit[
            "annual_timeline_receipt_bound_count"
        ]
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
        assert (
            release["release_manifest_receipt"]["material"]["provider_ledger"]["latest_record_hash"]
            == release["provider_ledger"]["latest_record_hash"]
        )
        release_registry_audit = release["release_manifest_receipt"]["material"]["production_gate_registry_audit"]
        assert release_registry_audit == release["readiness_receipt"]["material"]["production_gate_registry_audit"]
        assert release_registry_audit["registry_current"] is True
        assert release_registry_audit["missing_from_registry"] == []
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
        empty_release_ledger = _request(base_url, "GET", "/release-ledger")
        assert empty_release_ledger["ledger"]["exists"] is False
        assert empty_release_ledger["ledger"]["record_count"] == 0
        assert empty_release_ledger["ledger"]["latest_record_index"] is None
        empty_release_drift = _request(base_url, "GET", f"/release-drift?manifest={example_manifest.as_posix()}")
        assert empty_release_drift["drift"]["status"] == "not_checked"
        assert empty_release_drift["drift"]["passed"] is False
        assert "ledger integrity must pass" in empty_release_drift["drift"]["failures"][0]
        matched_release = _request(
            base_url,
            "GET",
            f"/release-manifest?manifest={example_manifest.as_posix()}&expected_release_manifest_receipt_sha256={release['release_manifest_receipt']['sha256']}",
        )
        assert matched_release["release_manifest_receipt_matches_expected"] is True
        assert matched_release["release_manifest_receipt_mismatch_reason"] == ""
        mismatched_release = _request(
            base_url,
            "GET",
            f"/release-manifest?manifest={example_manifest.as_posix()}&expected_release_manifest_receipt_sha256={'0' * 64}",
        )
        assert mismatched_release["release_manifest_receipt_matches_expected"] is False
        assert mismatched_release["release_manifest_receipt_mismatch_reason"] == (
            "release manifest receipt sha256 does not match expected value"
        )
        blocked_release_record = _request(
            base_url,
            "GET",
            f"/release-manifest?manifest={example_manifest.as_posix()}&expected_release_manifest_receipt_sha256={'0' * 64}&record=1",
        )
        assert blocked_release_record["ledger_record_requested"] is True
        assert blocked_release_record["ledger_recorded"] is False
        assert blocked_release_record["ledger_record_hash"] is None
        assert blocked_release_record["ledger_record_blocker"] == (
            "release manifest receipt must match expected value before recording"
        )
        still_empty_release_ledger = _request(base_url, "GET", "/release-ledger")
        assert still_empty_release_ledger["ledger"]["exists"] is False
        assert still_empty_release_ledger["ledger"]["latest_record_index"] is None
        recorded_release = _request(
            base_url,
            "GET",
            f"/release-manifest?manifest={example_manifest.as_posix()}&expected_release_manifest_receipt_sha256={release['release_manifest_receipt']['sha256']}&record=1",
        )
        assert recorded_release["ledger_record_requested"] is True
        assert recorded_release["ledger_recorded"] is True
        assert recorded_release["ledger_record_index"] == 0
        assert len(recorded_release["ledger_record_hash"]) == 64
        release_ledger_file = json.loads(Path(recorded_release["ledger_record_path"]).read_text(encoding="utf-8"))
        assert release_ledger_file["latest_record_index"] == 0
        assert release_ledger_file["records"][0]["provider_protocols_receipt_sha256"] == release[
            "release_manifest_receipt"
        ]["material"]["provider_protocols_receipt_sha256"]
        assert release_ledger_file["records"][0]["provider_protocols_receipt"] == release["release_manifest_receipt"][
            "material"
        ]["provider_protocols_receipt"]
        assert release_ledger_file["records"][0]["provider_onboarding_receipt_sha256"] == release[
            "release_manifest_receipt"
        ]["material"]["provider_onboarding_receipt_sha256"]
        assert release_ledger_file["records"][0]["provider_onboarding_receipt"] == release[
            "release_manifest_receipt"
        ]["material"]["provider_onboarding_receipt"]
        assert release_ledger_file["records"][0]["provider_action_plan_coverage"] == release[
            "release_manifest_receipt"
        ]["material"]["provider_action_plan_coverage"]
        assert release_ledger_file["records"][0]["annual_timeline_receipt_coverage"] == release[
            "release_manifest_receipt"
        ]["material"]["annual_timeline_receipt_coverage"]
        assert release_ledger_file["records"][0]["monthly_luck_receipt_coverage"] == release[
            "release_manifest_receipt"
        ]["material"]["monthly_luck_receipt_coverage"]
        assert release_ledger_file["records"][0]["auspicious_calendar_receipt_coverage"] == release[
            "release_manifest_receipt"
        ]["material"]["auspicious_calendar_receipt_coverage"]
        assert release_ledger_file["records"][0]["external_payload_birth_match_coverage"] == release[
            "release_manifest_receipt"
        ]["material"]["external_payload_birth_match_coverage"]
        assert release_ledger_file["records"][0]["classical_source_receipt_coverage"] == release[
            "release_manifest_receipt"
        ]["material"]["classical_source_receipt_coverage"]
        assert release_ledger_file["records"][0]["outcome_dataset"] == release["release_manifest_receipt"]["material"][
            "outcome_dataset"
        ]
        release_ledger = _request(base_url, "GET", "/release-ledger")
        assert release_ledger["ledger"]["exists"] is True
        assert release_ledger["ledger"]["integrity_status"] == "pass"
        assert release_ledger["ledger"]["record_count"] == 1
        assert release_ledger["ledger"]["latest_record_index"] == 0
        assert release_ledger["ledger"]["latest_record_hash"] == recorded_release["ledger_record_hash"]
        assert release_ledger["ledger"]["latest_release_manifest_receipt_sha256"] == release[
            "release_manifest_receipt"
        ]["sha256"]
        release_drift = _request(base_url, "GET", f"/release-drift?manifest={example_manifest.as_posix()}")
        assert release_drift["drift"]["status"] == "passed"
        assert release_drift["drift"]["passed"] is True
        assert release_drift["drift"]["matches_expected"] is True
        assert release_drift["drift"]["current_release_manifest_receipt_sha256"] == release[
            "release_manifest_receipt"
        ]["sha256"]
        mismatched_release_drift = _request(base_url, "GET", "/release-drift")
        assert mismatched_release_drift["drift"]["status"] == "drift_detected"
        assert mismatched_release_drift["drift"]["passed"] is False
        assert mismatched_release_drift["drift"]["failures"] == [
            "current release manifest receipt does not match latest ledger record"
        ]
        release_ledger_path = Path(release_ledger["ledger"]["path"])
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
        tampered_summary_release_ledger["latest_record_hash"] = tampered_summary_release_ledger["records"][0][
            "record_hash"
        ]
        release_ledger_path.write_text(json.dumps(tampered_summary_release_ledger, ensure_ascii=False), encoding="utf-8")
        tampered_summary_release_ledger_status = _request(base_url, "GET", "/release-ledger")
        assert tampered_summary_release_ledger_status["ledger"]["integrity_status"] == "fail"
        assert any(
            "candidate_name does not match release manifest receipt" in item
            for item in tampered_summary_release_ledger_status["ledger"]["failures"]
        )
        release_ledger_path.write_text(json.dumps(release_ledger_file, ensure_ascii=False), encoding="utf-8")
        tampered_release_ledger = json.loads(release_ledger_path.read_text(encoding="utf-8"))
        tampered_release_ledger["records"][0]["release_manifest_receipt"]["material"]["status"] = "tampered"
        release_ledger_path.write_text(json.dumps(tampered_release_ledger, ensure_ascii=False), encoding="utf-8")
        tampered_release_ledger_status = _request(base_url, "GET", "/release-ledger")
        assert tampered_release_ledger_status["ledger"]["integrity_status"] == "fail"
        assert any(
            "release_manifest_receipt sha256 mismatch" in item
            for item in tampered_release_ledger_status["ledger"]["failures"]
        )
        release_ledger_file["latest_record_index"] = 99
        release_ledger_path.write_text(json.dumps(release_ledger_file, ensure_ascii=False), encoding="utf-8")
        tampered_index_release_ledger_status = _request(base_url, "GET", "/release-ledger")
        assert tampered_index_release_ledger_status["ledger"]["integrity_status"] == "fail"
        assert any(
            "latest_record_index does not match last record" in item
            for item in tampered_index_release_ledger_status["ledger"]["failures"]
        )
        tampered_release_drift = _request(base_url, "GET", f"/release-drift?manifest={example_manifest.as_posix()}")
        assert tampered_release_drift["drift"]["status"] == "not_checked"
        assert tampered_release_drift["drift"]["failures"] == [
            "release manifest ledger integrity must pass before drift can be checked"
        ]

        rollback = _request(
            base_url,
            "POST",
            "/rollback",
            {"to_version": 1, "reason": "api rollback after benchmark comparison"},
        )
        assert rollback["status"] == "rolled_back"
        assert rollback["before_version"] == 2
        assert rollback["after_version"] == 3
        assert rollback["rollback_reason"] == "api rollback after benchmark comparison"
        assert rollback["genome_lineage"]["event"] == "rollback"
        assert rollback["genome_lineage"]["rollback_reason"] == "api rollback after benchmark comparison"

        rolled_status = _request(base_url, "GET", "/status")
        assert rolled_status["coordinator_version"] == 3
        assert rolled_status["genome_lineage"]["event"] == "rollback"
        assert rolled_status["genome_lineage"]["rollback_reason"] == "api rollback after benchmark comparison"
        assert rolled_status["lineage_integrity"]["status"] == "pass"

        rolled_history = _request(base_url, "GET", "/history")
        assert rolled_history["latest_version"] == 3
        assert rolled_history["versions"][-1]["lineage_event"] == "rollback"
        assert rolled_history["versions"][-1]["rollback_target_version"] == 1
        assert rolled_history["versions"][-1]["rollback_reason"] == "api rollback after benchmark comparison"
        assert rolled_history["history_integrity"]["status"] == "pass"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
