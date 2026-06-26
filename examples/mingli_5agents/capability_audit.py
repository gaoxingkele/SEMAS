"""Capability audit for the mingli five-agent SEMAS implementation."""

from __future__ import annotations

import importlib
import hashlib
import json
import os
import shlex
import tempfile
from pathlib import Path
from typing import Any

from semas.utils.llm_client import llm_backend_status

from examples.mingli_5agents.birth_profile_review import (
    audit_birth_profile_review_manifest,
    build_birth_profile_fixture_patch_preview,
    build_birth_profile_import_preview,
    build_birth_profile_reviewed_manifest_draft_preview,
    build_birth_profile_reviewed_manifest_file_preview,
    build_birth_profile_source_cache_audit,
    build_birth_profile_source_cache_template_preview,
    build_birth_profile_source_lookup_plan,
    build_birth_profile_source_review_workplan,
)
from examples.mingli_5agents.classical_corpus_refresh import source_list_audit
from examples.mingli_5agents.classical_text_index import classical_index_audit
from examples.mingli_5agents.empirical_validation import empirical_validation_cases, outcome_dataset_audit
from examples.mingli_5agents.famous_case_validation import (
    famous_case_annual_event_calibration_receipt,
    famous_case_receipt,
    famous_case_records,
    famous_case_school_calibration_receipt,
)
from examples.mingli_5agents.industry_event_manifest import (
    audit_industry_event_manifest,
    build_industry_event_symbolic_annual_score_payload,
    build_industry_event_symbolic_scoring_readiness_payload,
    default_industry_event_manifest_path,
    industry_event_manifest_receipt,
)
from examples.mingli_5agents.industry_event_candidates import (
    audit_industry_event_candidate_cases,
    build_candidate_pool_fetch_cache_plan,
    build_candidate_pool_manifest_drafts_from_cache,
    build_industry_event_evidence_workplan_from_symbolic_score,
    default_industry_event_candidate_cases_path,
    industry_event_candidate_cases_receipt,
)
from examples.mingli_5agents.industry_event_query_plan import (
    audit_industry_event_query_plan,
    default_industry_event_query_plan_path,
    industry_event_query_plan_receipt,
)
from examples.mingli_5agents.knowledge_base import SOURCE_REGISTRY
from examples.mingli_5agents.memory import MingliFeedbackMemory
from examples.mingli_5agents.method_lineage import method_lineage_receipt
from examples.mingli_5agents.method_surface import method_surface_receipt
from examples.mingli_5agents.provider_checks import (
    JSON_CLI_CHECK_BY_DOMAIN,
    JSON_CLI_ENV_VARS,
    JSON_CLI_PROVENANCE_ENV_VARS,
    bundled_provider_example_smoke,
    provider_health_checks,
)
from examples.mingli_5agents.provider_protocols import provider_protocol_document, provider_protocol_receipt
from examples.mingli_5agents.production_gates import PRODUCTION_READINESS_GATE_IDS
from examples.mingli_5agents.reference_charts import run_reference_chart_checks
from examples.mingli_5agents.tools.calendar_core import describe_calendar_providers
from examples.mingli_5agents.tools.professional_chart_provider import describe_domain_chart_providers


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]
DEFAULT_CLASSICAL_SOURCE_LIST = BASE_DIR / "providers" / "classical_source_list_example.json"
INDUSTRY_EVENT_SOURCE_MANIFEST_EXAMPLE = default_industry_event_manifest_path()
INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE = default_industry_event_candidate_cases_path()
INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE = default_industry_event_query_plan_path()
INDUSTRY_EVENT_WIKIDATA_FILM_RESPONSE_EXAMPLE = BASE_DIR / "providers" / "wikidata_film_response_example.json"
INDUSTRY_EVENT_WIKIDATA_MUSIC_RESPONSE_EXAMPLE = BASE_DIR / "providers" / "wikidata_music_response_example.json"
INDUSTRY_EVENT_WIKIDATA_SPORTS_RESPONSE_EXAMPLE = BASE_DIR / "providers" / "wikidata_sports_response_example.json"
INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE = REPO_ROOT / ".semas_mingli_repo" / "industry_event_cache_audit_fixture"
BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE = BASE_DIR / "providers" / "birth_profile_review_manifest_example.json"


def _default_classical_source_list_path(classical_source_list_path: Path | None) -> Path | None:
    """Resolve the application-level default classical-source list."""
    if classical_source_list_path is not None:
        return classical_source_list_path
    if os.getenv("SEMAS_CLASSIC_SOURCE_LIST"):
        return None
    return DEFAULT_CLASSICAL_SOURCE_LIST if DEFAULT_CLASSICAL_SOURCE_LIST.exists() else None


IMPLEMENTED_REQUIREMENTS = [
    {
        "id": "five_agent_topology",
        "requirement": "One coordinator plus BaZi, Zi Wei, Qi Men, and Western astrology specialists.",
        "evidence": [
            "genomes/orchestrator_v1.yaml",
            "genomes/bazi_v1.yaml",
            "genomes/ziwei_v1.yaml",
            "genomes/qimen_v1.yaml",
            "genomes/astrology_v1.yaml",
            "run_demo.MingliFiveAgentSystem.specialist_names",
        ],
        "status": "implemented",
    },
    {
        "id": "discussion_voting_synthesis",
        "requirement": "Coordinator dispatches specialists, runs discussion, claim-level voting, conflict handling, deliberation receipt hashing, and final synthesis.",
        "evidence": [
            "run_demo.MingliFiveAgentSystem._discuss",
            "run_demo.MingliFiveAgentSystem._vote",
            "run_demo.MingliFiveAgentSystem._claim_votes",
            "run_demo.MingliFiveAgentSystem._find_conflicts",
            "run_demo.MingliFiveAgentSystem._deliberation_receipt",
            "run_demo.MingliFiveAgentSystem._build_final_report",
            "final_report.votes._claims",
            "final_report.votes._audit",
            "final_report.deliberation_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "semas_evolution",
        "requirement": "SEMAS evaluation, mutation, sandbox/regression gate, and versioned genome repository.",
        "evidence": [
            "run_demo.build_orchestrator",
            "semas.orchestrator.Orchestrator",
            "semas.sandbox.Sandbox",
            "evolution.MingliPopulationEvolver",
        ],
        "status": "implemented",
    },
    {
        "id": "multi_objective_population_evolution",
        "requirement": "Population evolution across feedback, citation, safety, workflow, schema, provider-contract, Chinese-rendering, and consistency objectives, with reproducibility and cost-governance manifests.",
        "evidence": [
            "evolution.py metric floors",
            "evolution.evolution_cost_governance",
            "evaluators/provider_contract_evaluator.py",
            "evaluators/chinese_render_evaluator.py",
            "evolution.MingliEvolutionArchive",
            "memory.MingliFeedbackMemory",
            "benchmark.py built-in cases",
        ],
        "status": "implemented",
    },
    {
        "id": "evolution_governance_integrity",
        "requirement": "Accepted genomes, archive records, rollback events, and reproducibility manifests are linked by machine-checkable lineage and hashes.",
        "evidence": [
            "evolution.MingliEvolutionArchive.integrity_report",
            "evolution.genome_fingerprint",
            "api_core.status.archive_integrity",
            "api_core.status.lineage_integrity",
            "api_core.version_history",
            "api_core.rollback_coordinator",
            "cli history",
            "cli rollback --to-version",
            "GET /history",
            "POST /rollback",
        ],
        "status": "implemented",
    },
    {
        "id": "evolution_trigger_receipt",
        "requirement": "Every SEMAS evolution run exposes a stable trigger receipt binding explicit feedback, input/task hashes, validation-task hashes, operator validation mode, and outcome-dataset gate state into the response, archive event, and accepted genome lineage.",
        "evidence": [
            "api_core.evolve_case trigger_receipt",
            "evolution.MingliPopulationEvolver.evolve trigger_receipt",
            "api_core.schema_document.EvolveResponse.trigger_receipt",
            "api_core.schema_document.EvolutionTriggerReceipt.material",
            "api_core.status.lineage_integrity",
            "tests/test_cli.py evolution-trigger-receipt-v1",
        ],
        "status": "implemented",
    },
    {
        "id": "release_manifest_evolution_trigger_binding",
        "requirement": "Release manifests bind the latest accepted genome evolution trigger receipt into the release response, release-manifest receipt material, and release ledger record so release approval can audit why the shipped genome evolved.",
        "evidence": [
            "api_core.release_manifest.evolution_trigger_receipt",
            "api_core.schema_document.ReleaseManifestResponse.evolution_trigger_receipt",
            "api_core.schema_document.ReleaseManifestReceiptMaterial.evolution_trigger_receipt",
            "api_core.release_manifest_ledger.receipt_material_binding",
            "tests/test_cli.py release evolution trigger receipt binding",
        ],
        "status": "implemented",
    },
    {
        "id": "github_comparison_receipt",
        "requirement": "State-of-art and GitHub/open-source comparison output is bound into a stable receipt covering comparison scope, reviewed date, matrix hash, candidate project hash, blocking provider capabilities, and local capability hash.",
        "evidence": [
            "capability_audit.github_comparison_receipt",
            "api_core.schema_document.CapabilityAuditResponse.github_comparison_receipt",
            "api_core.schema_document.GitHubComparisonReceipt.material",
            "tests/test_empirical_validation.py github_comparison_receipt",
            "tests/test_schema_contract_evaluator.py github_comparison_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "plan_compliance_receipt",
        "requirement": "Plan compliance output is bound into a stable receipt covering the plan source hash, section matrix hash, section-gap coverage hash, implemented count, and unresolved planned gaps.",
        "evidence": [
            "capability_audit.plan_compliance_receipt",
            "api_core.schema_document.CapabilityAuditResponse.plan_compliance_receipt",
            "api_core.schema_document.PlanComplianceReceipt.material",
            "tests/test_empirical_validation.py plan_compliance_receipt",
            "tests/test_schema_contract_evaluator.py plan_compliance_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "release_manifest_github_comparison_binding",
        "requirement": "Release manifests expose and ledger-bind the GitHub/open-source comparison receipt so release evidence packages can audit the state-of-art baseline used at approval time.",
        "evidence": [
            "api_core.release_manifest.github_comparison_receipt",
            "api_core.schema_document.ReleaseManifestResponse.github_comparison_receipt",
            "api_core.schema_document.ReleaseManifestReceiptMaterial.github_comparison_receipt",
            "api_core.release_manifest_ledger.receipt_material_binding",
            "tests/test_cli.py release github_comparison_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "release_manifest_plan_compliance_binding",
        "requirement": "Release manifests expose and ledger-bind the plan compliance receipt so release evidence packages can audit the plan_mingli5agents.md compliance baseline used at approval time.",
        "evidence": [
            "api_core.release_manifest.plan_compliance_receipt",
            "api_core.schema_document.ReleaseManifestResponse.plan_compliance_receipt",
            "api_core.schema_document.ReleaseManifestReceiptMaterial.plan_compliance_receipt",
            "api_core.release_manifest_ledger.receipt_material_binding",
        ],
        "status": "implemented",
    },
    {
        "id": "calendar_provider_boundary",
        "requirement": "Replaceable calendar provider with approximate, auto, professional, and external-provider hooks.",
        "evidence": [
            "tools/calendar_core.py",
            "tools/calendar_provider.py",
            "api_core.status.calendar_providers",
        ],
        "status": "implemented",
    },
    {
        "id": "bazi_deep_analysis",
        "requirement": "BaZi chart with ten gods, hidden stems, Na Yin, growth stages, major luck, and professional backend support.",
        "evidence": [
            "tools/bazi_deep_analysis.py",
            "tools/bazi_pai_pan.py",
            "evaluators/report_schema_evaluator.py",
        ],
        "status": "implemented",
    },
    {
        "id": "structured_reporting",
        "requirement": "Final report includes normalized birth-profile audit data, annual rows, annual phase summaries, monthly rows, auspicious-day rows, eight topic sections, evidence, boundaries, and rendered reports.",
        "evidence": [
            "tools/annual_luck.py",
            "tools/monthly_luck.py",
            "tools/auspicious_calendar.py",
            "topic_synthesis.py",
            "report_renderers.py",
            "evaluators/report_schema_evaluator.py",
            "evaluators/chinese_render_evaluator.py",
        ],
        "status": "implemented",
    },
    {
        "id": "birthplace_geocoding_provenance",
        "requirement": "Normalized birth profiles include deterministic birthplace geocoding, timezone, coordinates, provider quality, runtime report fields, and a production-readiness benchmark geocoding gate.",
        "evidence": [
            "tools/birthplace_geo.py",
            "tools.lunar_date.normalize_birth_input",
            "final_report.birth_profile.birthplace_normalized",
            "final_report.birth_profile.birthplace_region",
            "final_report.birth_profile.latitude",
            "final_report.birth_profile.longitude",
            "final_report.birth_profile.timezone_offset",
            "final_report.birth_profile.geocoding_provider",
            "final_report.birth_profile.geocoding_quality",
            "api_core._benchmark_birthplace_geocoding_failures",
        ],
        "status": "implemented",
    },
    {
        "id": "external_payload_receipts",
        "requirement": "Request-scoped professional_charts payloads produce stable receipts binding external payload hashes, provenance hashes, and normalized birth-profile hashes into specialist context and final request provenance.",
        "evidence": [
            "tools.professional_chart_provider.external_payload_receipt",
            "tools/bazi_pai_pan.py",
            "tools/xuanze_cli_provider.py",
            "run_demo.MingliFiveAgentSystem._request_provenance",
            "tests/test_professional_chart_provider.py",
        ],
        "status": "implemented",
    },
    {
        "id": "external_payload_birth_match_audit",
        "requirement": "Request-scoped external professional payloads can declare birth data, receive a birth-match audit against the normalized request profile, block production-ready status on mismatches, and surface benchmark/readiness/release coverage.",
        "evidence": [
            "tools.professional_chart_provider.external_payload_birth_match",
            "tools.professional_chart_provider.external_payload_receipt",
            "run_demo.MingliFiveAgentSystem._external_payload_birth_match_valid",
            "run_demo.MingliFiveAgentSystem._provider_row",
            "benchmark._external_payload_birth_match_statuses",
            "api_core._benchmark_external_payload_birth_match_failures",
            "api_core._external_payload_birth_match_coverage",
            "api_core.production_readiness.benchmark_external_payload_birth_matches",
            "tests/test_professional_chart_provider.py",
            "tests/test_benchmark.py",
        ],
        "status": "implemented",
    },
    {
        "id": "bazi_eight_school_method_matrix",
        "requirement": "BaZi analysis exposes the plan's eight-school method surface as auditable method-matrix layers, including Ziping pattern, strength/support, blind-school workflow, shensha/nayin, tiaohou, image-symbol reading, simplified polarity, and governed data-validation boundaries.",
        "evidence": [
            "bazi.method_matrix.eight_school_coverage",
            "tools.bazi_deep_analysis.ensure_bazi_method_layers",
            "reference_charts.REQUIRED_METHODS",
            "tests/test_calendar_tools.py",
            "tests/test_mingli_system.py",
        ],
        "status": "implemented",
    },
    {
        "id": "provider_interpretation_readiness_matrix",
        "requirement": "Final reports expose per-domain interpretation mode, confidence level, and blocking reasons so symbolic fallbacks cannot be mistaken for production-grade professional chart calculations.",
        "evidence": [
            "run_demo.MingliFiveAgentSystem._provider_readiness_matrix",
            "run_demo.MingliFiveAgentSystem._provider_blocking_reasons",
            "final_report.provider_summary.readiness_matrix",
            "final_report.provider_summary.professional_domain_count",
            "final_report.provider_summary.fallback_domain_count",
            "api_core.schema_document.ProviderDomainStatus.interpretation_mode",
            "api_core.schema_document.ProviderSummary.readiness_matrix",
            "tests/test_mingli_system.py",
            "tests/test_cli.py",
        ],
        "status": "implemented",
    },
    {
        "id": "topic_synthesis_confidence_audit",
        "requirement": "Topic synthesis carries evidence coverage, cross-agent support counts, provider-readiness downgrades, and confidence boundaries for every major life topic.",
        "evidence": [
            "topic_synthesis.build_topic_synthesis",
            "topic_synthesis._synthesis_confidence",
            "final_report.topic_synthesis.finance.synthesis_confidence",
            "api_core.schema_document.TopicSynthesisConfidence.level",
            "api_core.schema_document.TopicSynthesisItem.synthesis_confidence",
            "tests/test_mingli_system.py",
            "tests/test_cli.py",
        ],
        "status": "implemented",
    },
    {
        "id": "topic_synthesis_timing_schema_contract",
        "requirement": "Topic synthesis annual focus, monthly focus, and timing evidence use typed public schemas bound to annual/monthly BaZi evidence and ten-god timing signals so client-facing finance/career/relationship summaries remain auditable instead of loose objects.",
        "evidence": [
            "api_core.schema_document.TopicSynthesisItem.timing_refs",
            "api_core.schema_document.TopicSynthesisAnnualFocus.bazi_evidence",
            "api_core.schema_document.TopicSynthesisTimingSignal.ten_gods",
            "tests/test_schema_contract_evaluator.py topic_synthesis_timing_schema_contract",
            "tests/test_mingli_system.py topic_synthesis_timing_runtime_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "empirical_topic_confidence_gate",
        "requirement": "Benchmark and empirical validation cases project topic-synthesis confidence summaries and production readiness blocks releases when benchmark topic confidence boundaries are missing.",
        "evidence": [
            "topic_synthesis.topic_confidence_summary",
            "benchmark.topic_confidence_summary",
            "empirical_validation.topic_confidence_summary",
            "api_core._benchmark_topic_confidence_failures",
            "api_core.production_readiness.benchmark_topic_confidence_boundaries",
            "tests/test_benchmark.py",
            "tests/test_empirical_validation.py",
        ],
        "status": "implemented",
    },
    {
        "id": "api_cli_benchmark",
        "requirement": "Runnable CLI, stdlib HTTP API, schemas, benchmarks, and tests.",
        "evidence": [
            "cli.py",
            "api_core.py",
            "api_server.py",
            "benchmark.py",
            "tests/",
        ],
        "status": "implemented",
    },
    {
        "id": "reference_chart_contracts",
        "requirement": "Fixed reference-chart contract checks for provider integrations, benchmark visibility, and SEMAS evaluator gating.",
        "evidence": [
            "reference_charts.py",
            "evaluators/provider_contract_evaluator.py",
            "benchmark.BenchmarkResult.reference_charts",
            "capability_audit.capability_audit",
        ],
        "status": "implemented",
    },
    {
        "id": "provider_contract_method_surface_lock",
        "requirement": "Normalized provider production contracts use the same required method surfaces as reference charts, preventing stale provider contracts from accepting weaker BaZi, Zi Wei, Qi Men, astrology, or xuanze outputs.",
        "evidence": [
            "method_surface.REQUIRED_METHODS",
            "provider_contracts.method_surface_binding",
            "provider_contracts.REQUIRED_METHODS",
            "provider_contracts.chart_contract",
            "provider_protocols.method_surface_publication",
            "provider_protocols.provider_protocol_receipt",
            "reference_charts.REQUIRED_METHODS",
            "tests/test_provider_contracts.py",
            "tests/test_provider_protocols.py",
        ],
        "status": "implemented",
    },
    {
        "id": "classical_text_index",
        "requirement": "Source review can retrieve provenance-bearing, copyright-safe classical-method evidence and audit the loaded corpus manifest.",
        "evidence": [
            "classical_text_index.py",
            "classical_corpus_ingest.py",
            "classical_corpus_refresh.py",
            "evidence.py",
            "evaluators/evidence_provenance_evaluator.py",
            "final_report.source_review.evidence_index",
        ],
        "status": "implemented_scaffold",
    },
    {
        "id": "classical_source_refresh_pipeline",
        "requirement": "External classical-source manifests can be audited, allowlisted, rights/review-governed, cached, ingested into local JSONL evidence, exposed through CLI/API endpoints, and bound by stable source-list receipts.",
        "evidence": [
            "classical_corpus_refresh.source_list_audit",
            "classical_corpus_refresh.source_governance_metadata",
            "classical_corpus_refresh.refresh_corpus_manifests",
            "api_core.classical_sources_refresh",
            "cli classical-refresh --source-list",
            "GET /classical-refresh",
            "tests/test_evidence.py",
            "tests/test_evidence.py source governance metadata",
            "tests/test_cli.py",
        ],
        "status": "implemented_scaffold",
    },
    {
        "id": "empirical_validation_harness",
        "requirement": "Validation distinguishes objectively checkable report-quality labels from unavailable predictive truth labels and can gate SEMAS evolution on non-predictive holdout tasks, with record-level label provenance and audit-only acknowledgement for life-event labels.",
        "evidence": [
            "empirical_validation.py",
            "outcome_dataset.py",
            "outcome_dataset.external_review_gate",
            "outcome_dataset.frozen_holdout_gate",
            "outcome_dataset.label_collection_pre_analysis_gate",
            "outcome_dataset.statistical_plan_preregistration_gate",
            "outcome_dataset.record_label_provenance_gate",
            "api_core.evolve_case validation_tasks",
            "benchmark.BenchmarkResult.empirical_validation",
            "capability_audit.capability_audit",
        ],
        "status": "implemented_scaffold",
    },
    {
        "id": "xuanze_huangdao_scaffold",
        "requirement": "Coordinator emits a structured auspicious-day window with twelve officers, twenty-eight mansions, huangdao rating, and recommended hour branches.",
        "evidence": [
            "tools/auspicious_calendar.py",
            "run_demo.MingliFiveAgentSystem.__call__",
            "final_report.auspicious_calendar",
            "evaluators/report_schema_evaluator.py",
        ],
        "status": "implemented_scaffold",
    },
    {
        "id": "safety_scope",
        "requirement": "Cultural-research/entertainment boundary and high-stakes decision guardrails.",
        "evidence": [
            "evaluators/safety_evaluator.py",
            "final_report.boundaries",
            "benchmark safety_boundary_case",
        ],
        "status": "implemented",
    },
    {
        "id": "optional_llm_synthesis",
        "requirement": "Optional OpenAI-compatible LLM synthesis through semas/utils/llm_client.py without replacing structured fields.",
        "evidence": [
            "llm_synthesis.py",
            "semas/utils/llm_client.py",
            "tests/test_llm_synthesis.py",
        ],
        "status": "implemented",
    },
    {
        "id": "optional_swiss_ephemeris_provider",
        "requirement": "Optional ephemeris-backed Western astrology provider behind the domain chart-provider interface.",
        "evidence": [
            "tools/swiss_ephemeris_provider.py",
            "tools/professional_chart_provider.py",
            "tests/test_professional_chart_provider.py",
            "pyproject.toml [project.optional-dependencies].astrology",
        ],
        "status": "implemented_optional",
    },
    {
        "id": "optional_kinqimen_provider",
        "requirement": "Optional kinqimen-backed Qi Men provider behind the domain chart-provider interface.",
        "evidence": [
            "tools/kinqimen_provider.py",
            "tools/professional_chart_provider.py",
            "tests/test_kinqimen_provider.py",
            "pyproject.toml [project.optional-dependencies].qimen",
        ],
        "status": "implemented_optional",
    },
    {
        "id": "optional_qimen_json_cli_provider",
        "requirement": "Optional JSON-CLI Qi Men provider boundary for external professional engines when local native dependencies are unavailable.",
        "evidence": [
            "tools/qimen_cli_provider.py",
            "providers/qimen_json_cli_example.py",
            "tools/professional_chart_provider.py",
            "tests/test_qimen_cli_provider.py",
            "tests/test_provider_examples.py",
            "SEMAS_QIMEN_CLI environment configuration",
        ],
        "status": "implemented_optional",
    },
    {
        "id": "optional_ziwei_json_cli_provider",
        "requirement": "Optional JSON-CLI Zi Wei provider boundary for external professional engines such as iztro wrappers.",
        "evidence": [
            "tools/ziwei_cli_provider.py",
            "providers/ziwei_json_cli_example.py",
            "tools/professional_chart_provider.py",
            "tests/test_ziwei_cli_provider.py",
            "tests/test_provider_examples.py",
            "SEMAS_ZIWEI_CLI environment configuration",
        ],
        "status": "implemented_optional",
    },
    {
        "id": "optional_astrology_json_cli_provider",
        "requirement": "Optional JSON-CLI Western astrology provider boundary for external professional ephemeris engines, with raw stdout contract requirements for ephemeris source, zodiac, house system, time scale, calculation time, data source, and license/review metadata.",
        "evidence": [
            "tools/astrology_cli_provider.py",
            "providers/astrology_json_cli_example.py",
            "provider_contracts.astrology_ephemeris_audit_contract",
            "provider_protocols.astrology_ephemeris_stdout_schema",
            "tools/professional_chart_provider.py",
            "tests/test_astrology_cli_provider.py",
            "tests/test_provider_contracts.py astrology ephemeris audit metadata",
            "tests/test_provider_examples.py",
            "SEMAS_ASTROLOGY_CLI environment configuration",
        ],
        "status": "implemented_optional",
    },
    {
        "id": "optional_xuanze_json_cli_provider",
        "requirement": "Optional JSON-CLI tongshu/xuanze provider boundary for external professional almanac engines, with raw stdout contract requirements for rule-table source, version, hash or receipt hash, calculation scope, and license/review metadata.",
        "evidence": [
            "tools/xuanze_cli_provider.py",
            "providers/xuanze_json_cli_example.py",
            "provider_contracts.xuanze_rule_table_audit_contract",
            "provider_protocols.xuanze_rule_table_stdout_schema",
            "tools/auspicious_calendar.py",
            "tests/test_xuanze_cli_provider.py",
            "tests/test_provider_contracts.py xuanze rule table audit metadata",
            "tests/test_provider_examples.py",
            "SEMAS_XUANZE_CLI environment configuration",
        ],
        "status": "implemented_optional",
    },
    {
        "id": "provider_protocol_governance",
        "requirement": "Machine-readable JSON-CLI provider contracts with sample stdin/stdout, contract self-checks, runtime protocol identity handshake, provider request receipts binding stdin/stdout to birth-profile hashes, raw provider contract receipts binding stdout hashes to contract validity, reference-contract coverage receipts, stable protocol hashes, certification receipts, ledger drift checks, and stale-protocol/reference-coverage production gates.",
        "evidence": [
            "provider_protocols.provider_protocol_document",
            "provider_protocols.BIRTH_PAYLOAD_SCHEMA.protocol",
            "provider_request_receipt.provider_request_receipt",
            "reference_charts.run_reference_chart_checks",
            "tools/ziwei_cli_provider.py",
            "tools/qimen_cli_provider.py",
            "tools/astrology_cli_provider.py",
            "tools/xuanze_cli_provider.py",
            "provider_checks._json_cli_protocol_identity",
            "provider_checks._raw_provider_contract_receipt",
            "provider_checks._reference_contract_coverage",
            "provider_checks._provider_certification_receipt",
            "api_core.schema_document.ProviderRawContractReceipt",
            "api_core.provider_certification_ledger.protocol_status",
            "api_core.provider_certification_ledger.reference_contract_status",
            "api_core.provider_certification_ledger.latest_record_binding",
            "api_core.production_readiness.provider_certification_protocols_current",
            "api_core.production_readiness.provider_certification_reference_contracts_current",
            "tests/test_provider_protocols.py",
            "tests/test_provider_checks.py raw provider contract receipt",
            "tests/test_provider_checks.py protocol identity",
            "tests/test_cli.py provider ledger stale protocol case",
        ],
        "status": "implemented",
    },
    {
        "id": "provider_command_fingerprint_governance",
        "requirement": "Provider certification receipts and ledgers bind external JSON-CLI provider command/artifact fingerprints, and production readiness/drift expose command-fingerprint status.",
        "evidence": [
            "provider_checks._provider_command_fingerprint",
            "provider_checks.certify_json_cli_provider",
            "api_core.provider_certification_ledger.command_fingerprint_status",
            "api_core.production_readiness.provider_certification_command_fingerprints_current",
            "api_core._provider_certification_drift_status",
            "tests/test_provider_checks.py",
            "tests/test_cli.py",
        ],
        "status": "implemented",
    },
    {
        "id": "provider_onboarding_receipt",
        "requirement": "Real professional provider onboarding exposes machine-readable domain gaps, aggregate missing-evidence counts, protocol hashes, certification/drift commands, bundled example smoke evidence, ledger requirements, and a stable onboarding receipt.",
        "evidence": [
            "api_core.provider_onboarding",
            "provider_checks.bundled_provider_example_smoke",
            "cli provider-onboarding",
            "GET /provider-onboarding",
            "api_core.schema_document.ProviderOnboardingResponse.provider_onboarding_receipt",
            "api_core.schema_document.ProviderOnboardingReceiptMaterial.missing_evidence_by_domain",
            "api_core.schema_document.ProviderOnboardingReceiptMaterial.missing_evidence_counts",
            "tests/test_provider_examples.py provider onboarding",
            "tests/test_cli.py provider-onboarding",
        ],
        "status": "implemented",
    },
    {
        "id": "provider_production_guidance",
        "requirement": "Provider readiness exposes a top-level machine-readable production guidance object with blocked targets, required environment/provenance variables, certification/drift commands, deployment checklist, and production-readiness commands.",
        "evidence": [
            "provider_checks.provider_health_checks.production_guidance",
            "api_core.schema_document.ProviderChecksResponse.production_guidance",
            "api_core.schema_document.ProviderProductionGuidance.production_ready",
            "evaluators/schema_contract_evaluator.py",
            "tests/test_provider_checks.py production_guidance",
            "tests/test_schema_contract_evaluator.py ProviderProductionGuidance",
        ],
        "status": "implemented",
    },
    {
        "id": "annual_timeline_receipt",
        "requirement": "Per-year annual luck timelines expose stable row fingerprints, topic coverage, range metadata, and a validation boundary so retrospective feedback can bind to exact yearly claims without certifying predictive truth.",
        "evidence": [
            "run_demo.MingliFiveAgentSystem._annual_timeline_receipt",
            "api_core.schema_document.AnnualTimelineReceipt.annual_timeline_sha256",
            "api_core.schema_document.AnnualTimelineReceipt.row_fingerprints",
            "tests/test_mingli_system.py annual_timeline_receipt",
            "tests/test_schema_contract_evaluator.py annual_timeline_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "annual_timeline_topic_evidence_binding",
        "requirement": "Every per-year annual timeline topic binds its message to the source annual row, source field, provider quality, BaZi evidence hash, and symbolic boundary so yearly finance/career/relationship claims can be audited at topic granularity.",
        "evidence": [
            "run_demo.MingliFiveAgentSystem._annual_timeline.topic_evidence_binding",
            "api_core.schema_document.AnnualTimelineTopic.bazi_evidence_sha256",
            "api_core.schema_document.AnnualTimelineReceipt.topic_evidence_complete",
            "tests/test_mingli_system.py annual_timeline_topic_evidence_binding",
            "tests/test_schema_contract_evaluator.py annual_timeline_topic_evidence_binding",
        ],
        "status": "implemented",
    },
    {
        "id": "monthly_luck_receipt",
        "requirement": "Selected monthly luck rows expose stable row fingerprints, selected-year/month coverage, source rows hash, and a validation boundary so focused monthly feedback can bind to exact claims without certifying predictive truth.",
        "evidence": [
            "run_demo.MingliFiveAgentSystem._monthly_luck_receipt",
            "api_core.schema_document.MonthlyLuckReceipt.monthly_luck_rows_sha256",
            "api_core.schema_document.MonthlyLuckReceipt.row_fingerprints",
            "tests/test_mingli_system.py monthly_luck_receipt",
            "tests/test_schema_contract_evaluator.py monthly_luck_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "bazi_core_profile_schema_contract",
        "requirement": "The public BaziProfile schema exposes core strength, pattern, useful-god, and luck-start analysis as typed contracts instead of loose objects so BaZi provider output and downstream report synthesis can be audited field by field.",
        "evidence": [
            "api_core.schema_document.BaziProfile.core_analysis_refs",
            "api_core.schema_document.BaziStrengthAnalysis.element_counts",
            "api_core.schema_document.BaziUsefulGodAnalysis.rationale",
            "tests/test_schema_contract_evaluator.py bazi_core_profile_schema_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "monthly_luck_topic_evidence_binding",
        "requirement": "Every selected monthly luck topic binds its message to the source monthly row, source field, provider quality, BaZi evidence hash, and symbolic boundary so focused monthly finance/career/relationship claims can be audited at topic granularity.",
        "evidence": [
            "tools.monthly_luck._monthly_topic_bindings",
            "run_demo.MingliFiveAgentSystem._monthly_luck_with_topic_evidence",
            "api_core.schema_document.MonthlyLuckTopic.bazi_evidence_sha256",
            "api_core.schema_document.MonthlyLuckReceipt.topic_evidence_complete",
            "tests/test_mingli_system.py monthly_luck_topic_evidence_binding",
            "tests/test_schema_contract_evaluator.py monthly_luck_topic_evidence_binding",
        ],
        "status": "implemented",
    },
    {
        "id": "monthly_luck_public_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes monthly_luck as a strong MonthlyLuck contract with typed rows, monthly BaZi evidence, and topic evidence bindings instead of a loose object.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.monthly_luck_ref",
            "api_core.schema_document.MonthlyLuck.rows",
            "api_core.schema_document.MonthlyLuckRow.bazi_evidence",
            "tests/test_schema_contract_evaluator.py monthly_luck_public_schema_contract",
            "tests/test_api_server.py monthly_luck_public_schema_contract",
            "tests/test_cli.py monthly_luck_public_schema_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "astrology_profile_public_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes astrology_profile as a strong AstrologyProfile contract with typed planets, houses, aspects, annual transits, ephemeris-quality metadata, and method-matrix evidence instead of a loose object.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.astrology_profile_ref",
            "api_core.schema_document.AstrologyProfile.planets",
            "api_core.schema_document.AstrologyProfile.ephemeris_quality",
            "tests/test_schema_contract_evaluator.py astrology_profile_public_schema_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "ziwei_qimen_public_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes ziwei_profile and qimen_profile as strong profile contracts with typed palaces, limits, useful gods, pattern flags, annual timing, and method-matrix evidence instead of missing or loose profile properties.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.ziwei_qimen_profile_refs",
            "api_core.schema_document.ZiweiProfile.highlighted_palaces",
            "api_core.schema_document.QimenProfile.useful_gods",
            "tests/test_schema_contract_evaluator.py ziwei_qimen_public_schema_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "ziwei_qimen_calculation_basis_audit_contract",
        "requirement": "Ziwei and Qimen raw JSON-CLI providers must disclose auditable calculation-basis metadata: provider, rule set, rule-set version, rule source, rule-source hash or receipt hash, calculation scope, and license/review status.",
        "evidence": [
            "provider_contracts.ziwei_qimen_calculation_basis_audit_contract",
            "provider_protocols.ziwei_qimen_calculation_basis_stdout_schema",
            "tests/test_provider_contracts.py ziwei qimen calculation basis audit metadata",
            "tests/test_provider_protocols.py ziwei qimen calculation basis stdout schema",
        ],
        "status": "implemented",
    },
    {
        "id": "rendered_reports_public_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes rendered_reports as a strong RenderedReports contract with required English and Chinese report strings so clients can reliably consume multilingual report artifacts instead of a loose object.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.rendered_reports_ref",
            "api_core.schema_document.RenderedReports.en_zh",
            "tests/test_schema_contract_evaluator.py rendered_reports_public_schema_contract",
            "tests/test_mingli_system.py rendered_reports_runtime_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "final_report_runtime_metadata_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes final-report runtime metadata for optional LLM synthesis and SEMAS workflow settings as typed contracts, preserving prompt fingerprints, generation status, discussion rounds, cross-check settings, vote threshold, and conflict-preservation policy.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.final_report_runtime_metadata_refs",
            "api_core.schema_document.LLMSynthesisReport.prompt_fingerprint",
            "api_core.schema_document.WorkflowReport.preserve_conflicts",
            "tests/test_schema_contract_evaluator.py final_report_runtime_metadata_schema_contract",
            "tests/test_mingli_system.py final_report_runtime_metadata_runtime_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "source_review_public_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes source_review and evidence_summary as typed contracts with covered source/tradition lists, missing evidence, evidence-index status, source snippets, provenance, and caution fields so symbolic claims remain source-auditable.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.source_review_ref",
            "api_core.schema_document.SourceReviewReport.evidence",
            "api_core.schema_document.SourceEvidenceSnippet.provenance",
            "api_core.schema_document.EvidenceSummaryItem.caution",
            "tests/test_schema_contract_evaluator.py source_review_public_schema_contract",
            "tests/test_mingli_system.py source_review_runtime_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "final_report_metadata_schema_contract",
        "requirement": "The public AnalyzeResponse schema exposes final-report title, coordinator version, summary, safety boundaries, conflict notes, and strategy notes as required typed metadata so UI clients and auditors can rely on the same report identity and safety envelope as the renderer.",
        "evidence": [
            "api_core.schema_document.AnalyzeResponse.final_report_metadata_fields",
            "tests/test_schema_contract_evaluator.py final_report_metadata_schema_contract",
            "tests/test_mingli_system.py final_report_metadata_runtime_contract",
        ],
        "status": "implemented",
    },
    {
        "id": "analyze_response_runtime_schema_validation",
        "requirement": "A real analyze_case run is JSON-roundtripped and recursively checked against the public AnalyzeResponse schema so schema_document is enforced against runtime output, not only documented as a static contract.",
        "evidence": [
            "tests/test_schema_contract_evaluator.py analyze_response_runtime_schema_validation",
            "api_core.schema_validation_errors.AnalyzeResponse",
            "api_core.production_readiness.benchmark_analyze_response_schema_valid",
            "api_core.schema_document.ProductionReadinessAnalyzeResponseSchemaAudit",
        ],
        "status": "implemented",
    },
    {
        "id": "auspicious_calendar_receipt",
        "requirement": "Auspicious-day rows expose stable row fingerprints, method-layer hashes, provider receipt bindings, rating/officer/mansion coverage, and a validation boundary so xuanze feedback can bind to exact date-selection claims without certifying real-world outcomes.",
        "evidence": [
            "run_demo.MingliFiveAgentSystem._auspicious_calendar_receipt",
            "api_core.schema_document.AuspiciousCalendarReceipt.calendar_rows_sha256",
            "api_core.schema_document.AuspiciousCalendarReceipt.method_layers_sha256",
            "api_core.schema_document.AuspiciousCalendarReceipt.row_fingerprints",
            "tests/test_mingli_system.py auspicious_calendar_receipt",
            "tests/test_schema_contract_evaluator.py auspicious_calendar_receipt",
        ],
        "status": "implemented",
    },
    {
        "id": "release_governance_ledger",
        "requirement": "Aggregate release evidence manifests bind audit, provider onboarding receipts, provider protocol receipts, benchmark, readiness, provider ledger, external-payload birth-match coverage, provider action-plan coverage, classical source-list receipt coverage, and outcome evidence into stable receipts with hash-chain recording, drift checks, and tamper detection.",
        "evidence": [
            "api_core.release_manifest",
            "api_core._external_payload_birth_match_coverage",
            "api_core._provider_action_plan_coverage",
            "api_core._classical_source_receipt_coverage",
            "api_core.release_manifest_ledger",
            "api_core.release_manifest_ledger.latest_record_binding",
            "api_core.release_manifest_ledger.receipt_material_binding",
            "api_core.release_manifest.release_gate_checks.provider_onboarding_receipt_current",
            "api_core.release_manifest.release_gate_checks.provider_protocols_receipt_current",
            "api_core.release_manifest_drift",
            "api_core.production_readiness.release_manifest_ledger_integrity",
            "cli release-manifest --record",
            "cli release-ledger",
            "cli release-drift",
            "GET /release-manifest",
            "GET /release-ledger",
            "GET /release-drift",
            "tests/test_cli.py",
            "tests/test_api_server.py",
        ],
        "status": "implemented",
    },
    {
        "id": "release_manifest_readiness_gate_binding",
        "requirement": "Release manifest gate checks explicitly bind newly introduced production-readiness governance gates for provider audit contracts, outcome statistical-plan preregistration, and latest classical-source refresh receipts into the release approval evidence path.",
        "evidence": [
            "api_core.release_manifest.release_gate_checks.provider_audit_contract_gates_bound",
            "api_core.release_manifest.release_gate_checks.outcome_statistical_plan_preregistration_bound",
            "api_core.release_manifest.release_gate_checks.classical_latest_refresh_receipt_bound",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.provider_audit_contract_gates_bound",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.outcome_statistical_plan_preregistration_bound",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.classical_latest_refresh_receipt_bound",
            "tests/test_schema_contract_evaluator.py release readiness gate binding",
        ],
        "status": "implemented",
    },
    {
        "id": "blocked_capability_coverage_audit",
        "requirement": "Capability audit accounts for every currently false capability by mapping it to an open known gap or an explicit optional-configuration policy, preventing hidden production blockers.",
        "evidence": [
            "capability_audit._blocked_capability_coverage",
            "api_core.schema_document.BlockedCapabilityCoverage.coverage_complete",
            "api_core.schema_document.CapabilityAuditResponse.blocked_capability_coverage",
            "api_core.schema_document.CapabilityAuditReceiptMaterial.blocked_capability_coverage",
            "tests/test_capability_audit_evaluator.py blocked capability coverage",
        ],
        "status": "implemented",
    },
    {
        "id": "blocked_capability_coverage_production_gate",
        "requirement": "Production readiness and release manifests gate blocked-capability coverage so unaccounted false capabilities cannot pass into production approval.",
        "evidence": [
            "api_core.production_readiness.blocked_capability_coverage_complete",
            "api_core.release_manifest.release_gate_checks.blocked_capability_coverage_bound",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.blocked_capability_coverage_bound",
            "tests/test_schema_contract_evaluator.py blocked capability coverage production gate",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_verification_command_coverage",
        "requirement": "Known-gap verification commands are machine-checked against the current CLI subcommands so remediation runbooks do not silently drift.",
        "evidence": [
            "capability_audit.known_gap_verification_command_coverage",
            "api_core.schema_document.KnownGapResolutionPlanCoverage.command_validation_complete",
            "api_core.schema_document.KnownGapResolutionPlanCoverage.invalid_verification_commands_by_gap",
            "tests/test_schema_contract_evaluator.py known gap verification command coverage",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_command_coverage_release_binding",
        "requirement": "Release manifests explicitly bind known-gap verification command and option coverage into release gate checks.",
        "evidence": [
            "api_core.release_manifest.release_gate_checks.known_gap_command_coverage_bound",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.known_gap_command_coverage_bound",
            "tests/test_schema_contract_evaluator.py known gap command coverage release binding",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_handoff_bundle",
        "requirement": "Capability audit emits a machine-readable handoff bundle for every open known gap, binding closure conditions, owner domains, blocking scopes, verification commands, production gates, provider environment variables, external candidate projects, and blocked capabilities into a stable receipt.",
        "evidence": [
            "capability_audit._known_gap_handoff_bundle",
            "api_core.schema_document.CapabilityAuditResponse.known_gap_handoff_bundle",
            "api_core.schema_document.CapabilityAuditReceiptMaterial.known_gap_handoff_bundle",
            "tests/test_capability_audit_evaluator.py known gap handoff bundle",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_handoff_bundle_production_gate",
        "requirement": "Production readiness and release manifests gate known-gap handoff bundles so external provider/source/dataset closure remains portable before approval.",
        "evidence": [
            "api_core.production_readiness.known_gap_handoff_bundle_ready",
            "api_core.release_manifest.release_gate_checks.known_gap_handoff_bundle_bound",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.known_gap_handoff_bundle_bound",
            "tests/test_schema_contract_evaluator.py known gap handoff bundle production gate",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_handoff_export_cli_api",
        "requirement": "Known-gap handoff bundles can be exported directly through CLI and HTTP API responses with audit-receipt drift binding, so another runtime or agent can consume the closure package without parsing the full capability audit.",
        "evidence": [
            "api_core.known_gap_handoff",
            "cli known-gap-handoff",
            "GET /known-gap-handoff",
            "api_core.schema_document.KnownGapHandoffExportResponse.known_gap_handoff_bundle",
            "api_core.schema_document.KnownGapHandoffExportResponse.handoff_export_receipt",
            "tests/test_cli.py known-gap handoff export",
            "tests/test_api_server.py known-gap handoff export",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_handoff_export_verification",
        "requirement": "Known-gap handoff export JSON files can be verified through CLI and HTTP API by recomputing the bundle hash, export receipt material, export receipt hash, known-gap ID binding, and optional expected export receipt hash.",
        "evidence": [
            "api_core.verify_known_gap_handoff_export",
            "cli known-gap-handoff-verify --input",
            "POST /known-gap-handoff-verify",
            "api_core.schema_document.KnownGapHandoffExportVerificationResponse.valid",
            "tests/test_cli.py known-gap handoff export verification",
            "tests/test_api_server.py known-gap handoff verify",
        ],
        "status": "implemented",
    },
    {
        "id": "known_gap_handoff_implementation_checklist",
        "requirement": "Verified known-gap handoff exports can be transformed through CLI and HTTP API into per-gap implementation checklists with env vars, provenance vars, candidate projects, verification commands, production gates, blocked capabilities, a stable checklist receipt, and expected checklist receipt drift binding.",
        "evidence": [
            "api_core.known_gap_handoff_implementation_checklist",
            "cli known-gap-handoff-checklist --input",
            "POST /known-gap-handoff-checklist",
            "api_core.schema_document.KnownGapHandoffChecklistResponse.items",
            "api_core.schema_document.KnownGapHandoffChecklistResponse.checklist_receipt_matches_expected",
            "tests/test_cli.py known-gap handoff checklist",
            "tests/test_api_server.py known-gap handoff checklist",
        ],
        "status": "implemented",
    },
    {
        "id": "outcome_dataset_split_governance",
        "requirement": "Outcome dataset manifests must prove every record is assigned to a frozen train/holdout split, bind a stable split fingerprint into receipts, and expose readiness/release gates for that coverage.",
        "evidence": [
            "outcome_dataset.data_split_record_coverage_gate",
            "api_core.production_readiness.outcome_dataset_data_split_records_covered",
            "api_core.schema_document.OutcomeDataSplitRecordCoverage.properties.coverage_complete",
            "api_core.schema_document.ReleaseManifestGateChecks.properties.outcome_dataset_split_coverage_bound",
            "api_core.release_manifest.release_gate_checks.outcome_dataset_split_coverage_bound",
            "tests/test_empirical_validation.py",
            "tests/test_cli.py",
            "tests/test_api_server.py",
        ],
        "status": "implemented",
    },
    {
        "id": "outcome_dataset_split_aware_validation",
        "requirement": "SEMAS validation imports only holdout non-predictive quality labels from reviewed outcome manifests by default, while preserving split_role metadata for audit and allowing explicit train/any inspection.",
        "evidence": [
            "empirical_validation.empirical_validation_tasks split_role_filter",
            "api_core.schema_document.OutcomeQualityTaskFingerprint.properties.split_role",
            "tests/test_empirical_validation.py",
            "tests/test_schema_contract_evaluator.py",
        ],
        "status": "implemented",
    },
    {
        "id": "industry_event_cross_domain_fixture_import",
        "requirement": "Sports, film, and music celebrity candidate pools can be imported through an offline cached-response fixture loop that emits positive and negative validation labels, binds a receipt into capability audit, and validates the artifact across Python, HTTP, and CLI schema surfaces.",
        "evidence": [
            "capability_audit._industry_event_cross_domain_fixture_import_receipt",
            "capability_audit._cross_domain_birth_profile_completion_task_plan",
            "capability_audit._cross_domain_birth_profile_completion_workplan_summary",
            "birth_profile_review.audit_birth_profile_review_manifest",
            "birth_profile_review.build_birth_profile_import_preview",
            "birth_profile_review.build_birth_profile_fixture_patch_preview",
            "birth_profile_review.build_birth_profile_source_lookup_plan",
            "birth_profile_review.build_birth_profile_source_cache_template_preview",
            "birth_profile_review.build_birth_profile_source_cache_audit",
            "birth_profile_review.build_birth_profile_reviewed_manifest_draft_preview",
            "birth_profile_review.build_birth_profile_reviewed_manifest_file_preview",
            "birth_profile_review.build_birth_profile_source_review_workplan",
            "providers/birth_profile_review_manifest_example.json",
            "api_core.schema_document.CapabilityAuditResponse.industry_event_cross_domain_fixture_import",
            "api_core.schema_document.CapabilityAuditReceiptMaterial.industry_event_cross_domain_fixture_import",
            "api_core.schema_document.IndustryEventCrossDomainFixtureImportReceipt.material",
            "providers/wikidata_film_response_example.json",
            "providers/wikidata_music_response_example.json",
            "providers/wikidata_sports_response_example.json",
            "tests/test_empirical_validation.py",
            "tests/test_empirical_validation.py symbolic scoring readiness coverage",
            "tests/test_schema_contract_evaluator.py",
            "tests/test_api_server.py",
            "tests/test_cli.py",
        ],
        "status": "implemented",
    },
]


KNOWN_GAPS = [
    {
        "id": "professional_ziwei_provider",
        "requirement": "Authoritative Zi Wei Dou Shu pan calculation from a professional library or verified ruleset.",
        "current_state": "Current Zi Wei module has deterministic fallback, external structured injection, and an optional JSON-CLI provider boundary configured by SEMAS_ZIWEI_CLI.",
        "needed_to_close": "Connect a verified Zi Wei engine such as an iztro wrapper and add known-chart fixtures from that engine.",
        "severity": "major",
    },
    {
        "id": "professional_qimen_provider",
        "requirement": "Authoritative Qi Men Dun Jia ju calculation with verified plate construction.",
        "current_state": "Optional kinqimen and JSON-CLI Qi Men adapters exist; the current environment still falls back to symbolic mode unless kinqimen installs successfully or SEMAS_QIMEN_CLI is configured.",
        "needed_to_close": "Install kinqimen or configure SEMAS_QIMEN_CLI in production, then add reference plates from known Qi Men examples.",
        "severity": "major",
    },
    {
        "id": "astronomical_ephemeris",
        "requirement": "Precise Western astrology natal and transit calculation using astronomical ephemeris.",
        "current_state": "Optional Swiss Ephemeris and JSON-CLI astrology providers exist; the current environment has no installed/configured ephemeris backend, so runtime falls back to symbolic mode unless pyswisseph is installed or SEMAS_ASTROLOGY_CLI is configured.",
        "needed_to_close": "Install pyswisseph or configure SEMAS_ASTROLOGY_CLI in production, verify licensing/data requirements, and add reference-chart regression fixtures with real ephemeris outputs.",
        "severity": "major",
    },
    {
        "id": "external_classic_text_retrieval",
        "requirement": "Download or retrieve external classical texts and open-source references when needed.",
        "current_state": "Evidence retrieval now uses a provenance-bearing classical-text index with built-in copyright-safe seed records, optional local JSONL loading, a controlled manifest ingester, and an allowlisted manifest refresh/cache pipeline for externally curated source metadata.",
        "needed_to_close": "Configure production source allowlists, scheduled refresh jobs, and reviewed public-domain/open-license manifest feeds for classical references.",
        "severity": "medium",
    },
    {
        "id": "empirical_validation_dataset",
        "requirement": "Objective large-dataset validation for claims that are meant to drive evolution.",
        "current_state": "A non-predictive empirical validation harness now tracks report-quality labels, gates SEMAS evolution on holdout quality tasks, can import reviewed report-quality/schema-quality manifest records, records zero built-in predictive-truth cases, and includes an outcome-dataset manifest audit for consent, privacy, labels, baselines, and statistical plans; evolution still does not optimize objective life-event prediction.",
        "needed_to_close": "Configure an externally reviewed outcome dataset manifest whose frozen train/holdout split covers every record, and keep predictive optimization disabled until consent, privacy, baselines, and statistical plans pass review.",
        "severity": "major",
    },
    {
        "id": "industry_event_source_provider",
        "requirement": "Reviewed external industry-event sources for film, music, and sports event years and non-event years.",
        "current_state": "Famous-case calibration now derives industry evidence from sourced fixture event subtypes, but negative-year industry-event labels have zero coverage and fixture-industry candidate rules are blocked from promotion.",
        "needed_to_close": "Configure a reviewed industry-event manifest or provider covering releases, awards, nominations, charts, rankings, titles, records, box office, broadcasts, and explicit non-event years before using industry evidence for false-positive claims.",
        "severity": "major",
    },
    {
        "id": "celebrity_birth_profile_review",
        "requirement": "Reviewed celebrity birth profiles before industry-event labels can enter symbolic BaZi scoring.",
        "current_state": "Cross-domain celebrity event labels are importable, but eight sports/film/music cases remain blocked by a reviewed-birth-profile manifest and non-mutating import preview.",
        "needed_to_close": "Externally review birth date, birth time, gender, birthplace, source URL, source rating, and source notes before generating a fixture import patch.",
        "severity": "major",
    },
    {
        "id": "huangdao_calendar_selection",
        "requirement": "Coordinator precisely calculates professional almanac systems such as twelve officers, twenty-eight mansions, and huangdao/heiddao with verified calendrical tables.",
        "current_state": "A deterministic xuanze scaffold and optional JSON-CLI provider boundary now emit twelve officers, twenty-eight mansions, huangdao rating, and recommended hours; the current environment still uses the offline baseline unless SEMAS_XUANZE_CLI is configured.",
        "needed_to_close": "Configure a verified tongshu/xuanze provider in production, add reference almanac fixtures, and cite the selected calendrical rule tables.",
        "severity": "medium",
    },
]


EXTERNAL_INTEGRATION_CANDIDATES = [
    {
        "domain": "ziwei",
        "name": "iztro / dart_iztro family",
        "url": "https://github.com/EdwinXiang/dart_iztro",
        "fit": "Open-source Zi Wei Dou Shu astrolabe generation candidate; likely adapter work needed for Python runtime.",
        "audit_note": "Verify rule coverage, license, test fixtures, and Chinese/English field mapping before integration.",
    },
    {
        "domain": "qimen",
        "name": "kinqimen",
        "url": "https://github.com/kentang2017/kinqimen",
        "fit": "Python Qi Men Dun Jia package candidate for replacing symbolic nine-palace scaffolding.",
        "audit_note": "Verify chart modes, calendar assumptions, license, and reproducibility against known plates.",
    },
    {
        "domain": "astrology",
        "name": "pyswisseph",
        "url": "https://github.com/astrorigin/pyswisseph",
        "fit": "Python Swiss Ephemeris binding candidate for high-precision natal and transit calculations.",
        "audit_note": "AGPL/licensing and ephemeris data requirements must be reviewed before bundling.",
    },
    {
        "domain": "industry_events",
        "name": "IMDb Non-Commercial Datasets",
        "url": "https://developer.imdb.com/non-commercial-datasets/",
        "fit": "Film and television release/title metadata candidate for industry event manifests.",
        "audit_note": "Non-commercial terms, refresh cadence, title matching, awards gaps, and negative-year semantics require review.",
    },
    {
        "domain": "industry_events",
        "name": "MusicBrainz Database",
        "url": "https://musicbrainz.org/doc/MusicBrainz_Database",
        "fit": "Music release, recording, artist, label, and relationship metadata candidate for music event manifests.",
        "audit_note": "Schema, licensing, local dump/API usage, chart/award coverage gaps, and artist disambiguation require review.",
    },
    {
        "domain": "industry_events",
        "name": "Wikidata Query Service",
        "url": "https://query.wikidata.org/",
        "fit": "Cross-domain linked-data candidate for awards, roles, releases, teams, rankings, and source URLs.",
        "audit_note": "SPARQL rate limits, statement references, data completeness, and negative-year absence semantics require review.",
    },
    {
        "domain": "industry_events",
        "name": "Olympedia",
        "url": "https://www.olympedia.org/",
        "fit": "Sports/Olympic athlete and result metadata candidate for sports peak event manifests.",
        "audit_note": "Terms, sport coverage beyond Olympics, result normalization, and non-event-year coverage require review.",
    },
]


GAP_RESOLUTION_BLUEPRINTS = {
    "professional_ziwei_provider": {
        "owner_domain": "ziwei",
        "blocking_scope": "environment_configured_backends",
        "closure_condition": (
            "A reviewed Zi Wei provider is configured through SEMAS_ZIWEI_CLI or a native backend, "
            "passes provider certification and reference-contract coverage, has reference chart fixtures, and no "
            "longer reports symbolic fallback in production readiness."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> provider-protocols --domain ziwei",
            "python examples/mingli_5agents/cli.py --repo <repo> certify-provider ziwei --command \"<provider-command>\" --provenance \"provider=<provider-name>; version=<provider-version>; source=<review-source>; license_or_review=<license-or-review>\" --record",
            "python examples/mingli_5agents/cli.py --repo <repo> providers --profile production --live",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest <manifest.json> --live",
        ],
        "production_gate_ids": [
            "provider_profile_ready",
            "provider_integration_ready",
            "provider_certification_ledger_covers_domains",
            "provider_certification_protocols_current",
            "provider_certification_reference_contracts_current",
            "provider_certification_command_fingerprints_current",
            "ziwei_qimen_calculation_basis_audit_contract",
        ],
    },
    "professional_qimen_provider": {
        "owner_domain": "qimen",
        "blocking_scope": "environment_configured_backends",
        "closure_condition": (
            "kinqimen or a reviewed SEMAS_QIMEN_CLI provider is configured, certified, and validated against "
            "reference-contract Qi Men plates before production readiness can pass."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> provider-protocols --domain qimen",
            "python examples/mingli_5agents/cli.py --repo <repo> certify-provider qimen --command \"<provider-command>\" --provenance \"provider=<provider-name>; version=<provider-version>; source=<review-source>; license_or_review=<license-or-review>\" --record",
            "python examples/mingli_5agents/cli.py --repo <repo> providers --profile production --live",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest <manifest.json> --live",
        ],
        "production_gate_ids": [
            "provider_profile_ready",
            "provider_integration_ready",
            "provider_certification_ledger_covers_domains",
            "provider_certification_protocols_current",
            "provider_certification_reference_contracts_current",
            "provider_certification_command_fingerprints_current",
            "ziwei_qimen_calculation_basis_audit_contract",
        ],
    },
    "astronomical_ephemeris": {
        "owner_domain": "astrology",
        "blocking_scope": "environment_configured_backends",
        "closure_condition": (
            "pyswisseph or a reviewed SEMAS_ASTROLOGY_CLI provider is configured with reviewed licensing/data "
            "requirements, certified, and validated against ephemeris reference-contract fixtures."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> provider-protocols --domain astrology",
            "python examples/mingli_5agents/cli.py --repo <repo> certify-provider astrology --command \"<provider-command>\" --provenance \"provider=<provider-name>; version=<provider-version>; source=<review-source>; license_or_review=<license-or-review>\" --record",
            "python examples/mingli_5agents/cli.py --repo <repo> providers --profile production --live",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest <manifest.json> --live",
        ],
        "production_gate_ids": [
            "provider_profile_ready",
            "provider_integration_ready",
            "provider_certification_ledger_covers_domains",
            "provider_certification_protocols_current",
            "provider_certification_reference_contracts_current",
            "provider_certification_command_fingerprints_current",
            "astrology_ephemeris_audit_contract",
        ],
    },
    "external_classic_text_retrieval": {
        "owner_domain": "classical_sources",
        "blocking_scope": "production_source_allowlists",
        "closure_condition": (
            "Production source allowlists, scheduled refresh jobs, and reviewed public-domain/open-license "
            "manifest feeds are configured and produce stable source-list receipts."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> classical-sources --source-list <source-list.json>",
            "python examples/mingli_5agents/cli.py --repo <repo> classical-refresh --source-list <source-list.json> --cache-dir <cache-dir> --output-dir <corpus-dir>",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --classical-source-list <source-list.json> --live",
            "python examples/mingli_5agents/cli.py --repo <repo> release-manifest --classical-source-list <source-list.json>",
        ],
        "production_gate_ids": [
            "classical_source_refresh_ready",
            "classical_source_latest_refresh_receipt_present",
            "release_manifest_classical_source_receipt_coverage",
        ],
    },
    "empirical_validation_dataset": {
        "owner_domain": "outcome_dataset",
        "blocking_scope": "externally_reviewed_dataset_manifest",
        "closure_condition": (
            "An externally reviewed outcome dataset manifest with consent, privacy, frozen holdout, baselines, "
            "and statistical plan passes audit; predictive optimization remains disabled until those gates pass."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> outcome-dataset --manifest <manifest.json>",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest <manifest.json> --live",
            "python examples/mingli_5agents/cli.py --repo <repo> release-manifest --manifest <manifest.json>",
        ],
        "production_gate_ids": [
            "outcome_dataset_configured",
            "outcome_dataset_external_review_gate",
            "outcome_dataset_frozen_holdout_gate",
            "outcome_dataset_data_split_records_covered",
            "outcome_dataset_label_collection_pre_analysis_gate",
            "outcome_dataset_statistical_plan_preregistered",
            "outcome_dataset_gate_passed",
        ],
    },
    "industry_event_source_provider": {
        "owner_domain": "industry_events",
        "blocking_scope": "externally_reviewed_industry_event_manifest",
        "closure_condition": (
            "A reviewed industry-event manifest or provider covers positive and negative years for film, music, "
            "and sports domain-topic slices, exposes source/provenance fields, and passes outcome-dataset audit "
            "without enabling predictive optimization."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> outcome-dataset --manifest examples/mingli_5agents/providers/industry_event_source_manifest_example.json",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest examples/mingli_5agents/providers/industry_event_source_manifest_example.json --live",
            "python examples/mingli_5agents/cli.py --repo <repo> release-manifest --manifest examples/mingli_5agents/providers/industry_event_source_manifest_example.json",
        ],
        "production_gate_ids": [
            "outcome_dataset_configured",
            "outcome_dataset_external_review_gate",
            "outcome_dataset_frozen_holdout_gate",
            "outcome_dataset_data_split_records_covered",
            "outcome_dataset_label_collection_pre_analysis_gate",
            "outcome_dataset_statistical_plan_preregistered",
            "outcome_dataset_gate_passed",
        ],
    },
    "celebrity_birth_profile_review": {
        "owner_domain": "birth_profiles",
        "blocking_scope": "reviewed_celebrity_birth_profile_import",
        "closure_condition": (
            "Celebrity birth-profile review manifests are externally reviewed before import, and the current "
            "production readiness gate confirms unreviewed import previews remain non-mutating and blocked."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-review --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-source-review-workplan --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-source-lookup-plan --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json --cache-dir <repo>/birth_profile_source_cache",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-source-cache-template-preview --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json --cache-dir <repo>/birth_profile_source_cache",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-source-cache-audit --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json --cache-dir <repo>/birth_profile_source_cache",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-reviewed-manifest-draft-preview --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json --cache-dir <repo>/birth_profile_source_cache",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-reviewed-manifest-file-preview --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json --cache-dir <repo>/birth_profile_source_cache --target <repo>/birth_profile_review_manifest_reviewed.json",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-import-preview --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json",
            "python examples/mingli_5agents/cli.py --repo <repo> birth-profile-fixture-patch-preview --manifest examples/mingli_5agents/providers/birth_profile_review_manifest_example.json",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest <manifest.json> --live",
        ],
        "production_gate_ids": [
            "birth_profile_source_review_workplan_available",
            "birth_profile_source_lookup_plan_dry_run",
            "birth_profile_source_family_catalog_bound",
            "birth_profile_source_cache_template_preview_non_mutating",
            "birth_profile_source_family_cache_enforcement_probe",
            "birth_profile_substantive_evidence_cache_enforcement_probe",
            "birth_profile_source_cache_audit_read_only",
            "birth_profile_reviewed_manifest_draft_preview_non_mutating",
            "birth_profile_import_preview_blocked",
            "birth_profile_fixture_patch_preview_blocked",
            "production_gate_registry_current",
        ],
    },
    "huangdao_calendar_selection": {
        "owner_domain": "xuanze",
        "blocking_scope": "environment_configured_backends",
        "closure_condition": (
            "A reviewed tongshu/xuanze provider is configured through SEMAS_XUANZE_CLI, certified, and validated "
            "against reference-contract almanac fixtures and cited rule tables."
        ),
        "verification_commands": [
            "python examples/mingli_5agents/cli.py --repo <repo> provider-protocols --domain xuanze",
            "python examples/mingli_5agents/cli.py --repo <repo> certify-provider xuanze --command \"<provider-command>\" --provenance \"provider=<provider-name>; version=<provider-version>; source=<review-source>; license_or_review=<license-or-review>\" --record",
            "python examples/mingli_5agents/cli.py --repo <repo> providers --profile production --live",
            "python examples/mingli_5agents/cli.py --repo <repo> production-readiness --manifest <manifest.json> --live",
        ],
        "production_gate_ids": [
            "provider_profile_ready",
            "provider_integration_ready",
            "provider_certification_ledger_covers_domains",
            "provider_certification_protocols_current",
            "provider_certification_reference_contracts_current",
            "provider_certification_command_fingerprints_current",
            "xuanze_rule_table_audit_contract",
        ],
    },
}


def _known_gap_resolution_plan() -> list[dict[str, Any]]:
    """Return deterministic remediation instructions for every open known gap."""
    plan = []
    for gap in KNOWN_GAPS:
        blueprint = GAP_RESOLUTION_BLUEPRINTS.get(gap["id"], {})
        plan.append(
            {
                "id": gap["id"],
                "gap_id": gap["id"],
                "severity": gap["severity"],
                "status": "open",
                "requirement": gap["requirement"],
                "current_state": gap["current_state"],
                "needed_to_close": gap["needed_to_close"],
                "closure_condition": blueprint.get("closure_condition", gap["needed_to_close"]),
                "verification_commands": blueprint.get("verification_commands", []),
                "owner_domain": blueprint.get("owner_domain", "unassigned"),
                "production_gate_ids": blueprint.get("production_gate_ids", []),
                "blocking_scope": blueprint.get("blocking_scope", "unclassified"),
            }
        )
    return plan


def _known_gap_items() -> list[dict[str, Any]]:
    """Return public known-gap records with ownership and gate metadata inlined."""
    items = []
    for gap in KNOWN_GAPS:
        blueprint = GAP_RESOLUTION_BLUEPRINTS.get(gap["id"], {})
        items.append(
            {
                "id": gap["id"],
                "severity": gap["severity"],
                "status": "open",
                "owner_domain": blueprint.get("owner_domain", "unassigned"),
                "blocking_scope": blueprint.get("blocking_scope", "unclassified"),
                "requirement": gap["requirement"],
                "current_state": gap["current_state"],
                "needed_to_close": gap["needed_to_close"],
                "closure_condition": blueprint.get("closure_condition", gap["needed_to_close"]),
                "verification_commands": blueprint.get("verification_commands", []),
                "production_gate_ids": blueprint.get("production_gate_ids", []),
            }
        )
    return items


BLOCKED_CAPABILITY_ACCOUNTING = {
    "classical_source_refresh_configured": {
        "classification": "known_gap",
        "gap_ids": ["external_classic_text_retrieval"],
        "policy": "Production must configure reviewed classical source allowlists and refresh jobs.",
    },
    "professional_ziwei_provider_available": {
        "classification": "known_gap",
        "gap_ids": ["professional_ziwei_provider"],
        "policy": "Production must configure and certify a reviewed Zi Wei provider.",
    },
    "professional_qimen_provider_available": {
        "classification": "known_gap",
        "gap_ids": ["professional_qimen_provider"],
        "policy": "Production must configure and certify a reviewed Qi Men provider.",
    },
    "ephemeris_astrology_provider_available": {
        "classification": "known_gap",
        "gap_ids": ["astronomical_ephemeris"],
        "policy": "Production must configure and certify a reviewed ephemeris provider.",
    },
    "llm_backend_configured": {
        "classification": "optional_configuration",
        "gap_ids": [],
        "policy": "LLM synthesis is optional; deterministic offline synthesis remains the production-safe fallback.",
    },
}


def _blocked_capability_coverage(capabilities: dict[str, Any], known_gaps: list[dict[str, Any]]) -> dict[str, Any]:
    """Map every false capability to a known gap or explicit optional policy."""
    known_gap_by_id = {str(item.get("id")): item for item in known_gaps if isinstance(item, dict)}
    false_capabilities = sorted(key for key, value in capabilities.items() if value is not True)
    entries = []
    unaccounted = []
    for capability in false_capabilities:
        mapping = BLOCKED_CAPABILITY_ACCOUNTING.get(capability)
        gap_ids = list(mapping.get("gap_ids", [])) if isinstance(mapping, dict) else []
        missing_gap_ids = [gap_id for gap_id in gap_ids if gap_id not in known_gap_by_id]
        classification = mapping.get("classification") if isinstance(mapping, dict) else "unaccounted"
        accounted = isinstance(mapping, dict) and not missing_gap_ids
        if not accounted:
            unaccounted.append(capability)
        owner_domains = sorted(
            {
                str(known_gap_by_id[gap_id].get("owner_domain"))
                for gap_id in gap_ids
                if gap_id in known_gap_by_id and known_gap_by_id[gap_id].get("owner_domain")
            }
        )
        blocking_scopes = sorted(
            {
                str(known_gap_by_id[gap_id].get("blocking_scope"))
                for gap_id in gap_ids
                if gap_id in known_gap_by_id and known_gap_by_id[gap_id].get("blocking_scope")
            }
        )
        entries.append(
            {
                "capability": capability,
                "accounted": accounted,
                "classification": classification,
                "gap_ids": gap_ids,
                "missing_gap_ids": missing_gap_ids,
                "owner_domains": owner_domains,
                "blocking_scopes": blocking_scopes,
                "policy": mapping.get("policy", "") if isinstance(mapping, dict) else "",
            }
        )
    accounted_count = sum(1 for item in entries if item["accounted"])
    material = {
        "false_capabilities": false_capabilities,
        "accounted_capabilities": [item["capability"] for item in entries if item["accounted"]],
        "unaccounted_capabilities": unaccounted,
        "known_gap_ids": sorted(known_gap_by_id),
    }
    return {
        "status": "covered" if false_capabilities and not unaccounted else "uncovered",
        "coverage_complete": bool(false_capabilities) and not unaccounted,
        "false_capability_count": len(false_capabilities),
        "accounted_count": accounted_count,
        "unaccounted_capabilities": unaccounted,
        "entries": entries,
        "coverage_sha256": _stable_json_sha256(material),
    }


def _domain_provider_env_vars(domain: str) -> dict[str, list[str]]:
    check_name = JSON_CLI_CHECK_BY_DOMAIN.get(domain)
    if not check_name:
        return {"required_env_vars": [], "required_provenance_env_vars": []}
    env_var = JSON_CLI_ENV_VARS.get(check_name)
    provenance_env_var = JSON_CLI_PROVENANCE_ENV_VARS.get(check_name)
    return {
        "required_env_vars": [env_var] if env_var else [],
        "required_provenance_env_vars": [provenance_env_var] if provenance_env_var else [],
    }


def _known_gap_handoff_bundle(
    known_gaps: list[dict[str, Any]],
    known_gap_resolution_plan: list[dict[str, Any]],
    blocked_capability_coverage: dict[str, Any],
    external_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a portable closure package for every open known gap."""
    known_gap_by_id = {str(item.get("id")): item for item in known_gaps if isinstance(item, dict)}
    blocked_entries = blocked_capability_coverage.get("entries", [])
    if not isinstance(blocked_entries, list):
        blocked_entries = []
    items = []
    missing_handoff_gap_ids = []
    for plan_item in known_gap_resolution_plan:
        if not isinstance(plan_item, dict):
            continue
        gap_id = _known_gap_plan_item_id(plan_item)
        gap = known_gap_by_id.get(gap_id, {})
        owner_domain = str(plan_item.get("owner_domain", ""))
        domain_env = _domain_provider_env_vars(owner_domain)
        blocked_capabilities = sorted(
            str(entry.get("capability"))
            for entry in blocked_entries
            if isinstance(entry, dict) and gap_id in [str(item) for item in entry.get("gap_ids", [])]
        )
        candidate_projects = [
            {
                "name": str(candidate.get("name", "")),
                "url": str(candidate.get("url", "")),
                "fit": str(candidate.get("fit", "")),
                "audit_note": str(candidate.get("audit_note", "")),
            }
            for candidate in external_candidates
            if isinstance(candidate, dict) and str(candidate.get("domain")) == owner_domain
        ]
        verification_commands = [str(command) for command in plan_item.get("verification_commands", [])]
        production_gate_ids = [str(gate) for gate in plan_item.get("production_gate_ids", [])]
        handoff_ready = all(
            [
                bool(gap_id),
                bool(owner_domain),
                bool(plan_item.get("blocking_scope")),
                bool(plan_item.get("closure_condition")),
                bool(verification_commands),
                bool(production_gate_ids),
            ]
        )
        if not handoff_ready:
            missing_handoff_gap_ids.append(gap_id)
        items.append(
            {
                "gap_id": gap_id,
                "severity": str(plan_item.get("severity") or gap.get("severity", "")),
                "status": str(plan_item.get("status") or gap.get("status", "")),
                "owner_domain": owner_domain,
                "blocking_scope": str(plan_item.get("blocking_scope", "")),
                "requirement": str(plan_item.get("requirement") or gap.get("requirement", "")),
                "closure_condition": str(plan_item.get("closure_condition", "")),
                "required_env_vars": domain_env["required_env_vars"],
                "required_provenance_env_vars": domain_env["required_provenance_env_vars"],
                "verification_commands": verification_commands,
                "production_gate_ids": production_gate_ids,
                "external_candidate_projects": candidate_projects,
                "blocked_capabilities": blocked_capabilities,
                "handoff_ready": handoff_ready,
            }
        )
    material = {
        "bundle_version": "known-gap-handoff-v1",
        "open_gap_ids": [item["gap_id"] for item in items],
        "missing_handoff_gap_ids": sorted(set(missing_handoff_gap_ids)),
        "items": items,
    }
    return {
        "bundle_version": material["bundle_version"],
        "status": "ready" if items and not missing_handoff_gap_ids else "incomplete",
        "gap_count": len(items),
        "open_gap_ids": material["open_gap_ids"],
        "missing_handoff_gap_ids": material["missing_handoff_gap_ids"],
        "items": items,
        "bundle_sha256": _stable_json_sha256(material),
    }


def known_gap_verification_command_coverage(known_gap_resolution_plan: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate known-gap runbook commands against the current CLI subcommands."""
    valid_subcommands = _cli_subcommands()
    valid_options_by_subcommand = _cli_options_by_subcommand()
    invalid_by_gap: dict[str, list[str]] = {}
    invalid_options_by_gap: dict[str, list[str]] = {}
    subcommands_by_gap: dict[str, list[str]] = {}
    options_by_gap: dict[str, list[str]] = {}
    command_counts: dict[str, int] = {}
    for item in known_gap_resolution_plan:
        if not isinstance(item, dict):
            continue
        gap_id = _known_gap_plan_item_id(item)
        commands = item.get("verification_commands", [])
        if not isinstance(commands, list):
            invalid_by_gap[gap_id] = ["verification_commands_not_list"]
            command_counts[gap_id] = 0
            subcommands_by_gap[gap_id] = []
            options_by_gap[gap_id] = []
            continue
        command_counts[gap_id] = len(commands)
        observed_subcommands: list[str] = []
        observed_options: list[str] = []
        invalid_commands: list[str] = []
        invalid_options: list[str] = []
        for command in commands:
            command_text = str(command)
            parsed = _parse_cli_command(command_text)
            subcommand = parsed.get("subcommand") if isinstance(parsed, dict) else None
            if subcommand is None:
                invalid_commands.append(command_text)
                continue
            if subcommand not in valid_subcommands:
                invalid_commands.append(command_text)
                continue
            observed_subcommands.append(subcommand)
            valid_options = valid_options_by_subcommand.get(subcommand, set())
            for option in parsed.get("options", []):
                option_name = str(option).split("=", 1)[0]
                observed_options.append(option_name)
                if option_name != "--repo" and option_name not in valid_options:
                    invalid_options.append(f"{command_text} :: {option_name}")
        subcommands_by_gap[gap_id] = sorted(set(observed_subcommands))
        options_by_gap[gap_id] = sorted(set(observed_options))
        if invalid_commands:
            invalid_by_gap[gap_id] = invalid_commands
        if invalid_options:
            invalid_options_by_gap[gap_id] = invalid_options
    material = {
        "valid_subcommands": sorted(valid_subcommands),
        "valid_options_by_subcommand": {
            command: sorted(options) for command, options in sorted(valid_options_by_subcommand.items())
        },
        "command_counts": command_counts,
        "command_subcommands_by_gap": subcommands_by_gap,
        "command_options_by_gap": options_by_gap,
        "invalid_verification_commands_by_gap": invalid_by_gap,
        "invalid_verification_options_by_gap": invalid_options_by_gap,
    }
    return {
        **material,
        "command_validation_complete": not invalid_by_gap and not invalid_options_by_gap and bool(command_counts),
        "command_coverage_sha256": _stable_json_sha256(material),
    }


def _cli_subcommands() -> set[str]:
    from examples.mingli_5agents.cli import build_parser

    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and choices:
            return {str(item) for item in choices}
    return set()


def _cli_options_by_subcommand() -> dict[str, set[str]]:
    from examples.mingli_5agents.cli import build_parser

    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if not isinstance(choices, dict) or not choices:
            continue
        result: dict[str, set[str]] = {}
        for subcommand, subparser in choices.items():
            options = set()
            for sub_action in getattr(subparser, "_actions", []):
                for option in getattr(sub_action, "option_strings", []):
                    options.add(str(option))
            result[str(subcommand)] = options
        return result
    return {}


def _parse_cli_command(command: str) -> dict[str, Any]:
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return {"subcommand": None, "options": []}
    cli_index = None
    for index, token in enumerate(tokens):
        normalized = token.replace("\\", "/")
        if normalized.endswith("examples/mingli_5agents/cli.py") or token == "examples.mingli_5agents.cli":
            cli_index = index
            break
    if cli_index is None:
        return {"subcommand": None, "options": []}
    index = cli_index + 1
    options = []
    subcommand = None
    while index < len(tokens):
        token = tokens[index]
        if token == "--repo":
            options.append(token)
            index += 2
            continue
        if token.startswith("-"):
            options.append(token)
            index += 1
            continue
        subcommand = token
        index += 1
        break
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("-"):
            options.append(token)
        index += 1
    return {"subcommand": subcommand, "options": options}


def _stable_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


GITHUB_COMPARISON_MATRIX = [
    {
        "dimension": "multi_agent_evolution",
        "this_project": "Five-agent SEMAS orchestration with discussion, voting, feedback memory, population mutation, metric floors, and regression gates.",
        "github_baseline": "Most open-source mingli repositories focus on one calculation engine or UI component rather than self-evolving multi-agent orchestration.",
        "relative_position": "ahead_for_agentic_framework",
        "required_to_lead": "Keep provider adapters replaceable and add more independent validation cases for every evolved genome.",
    },
    {
        "dimension": "ziwei_calculation",
        "this_project": "Deterministic Zi Wei scaffold, external structured injection, and JSON-CLI adapter boundary.",
        "github_baseline": "iztro/dart_iztro style projects specialize in Zi Wei astrolabe generation and should be treated as stronger calculation engines.",
        "relative_position": "behind_specialized_engine",
        "required_to_lead": "Wrap a verified iztro-family engine, normalize fields into the existing provider contract, and add known-chart fixtures.",
    },
    {
        "dimension": "qimen_calculation",
        "this_project": "Symbolic nine-palace scaffold with optional kinqimen and JSON-CLI adapter boundaries.",
        "github_baseline": "kinqimen and newer Qi Men engines focus on professional plate construction and domain-specific rule coverage.",
        "relative_position": "behind_when_no_provider_configured",
        "required_to_lead": "Install/configure kinqimen or a verified external Qi Men provider, then gate evolution on reference-plate checks.",
    },
    {
        "dimension": "western_astrology",
        "this_project": "Symbolic Western astrology scaffold with optional Swiss Ephemeris and JSON-CLI adapter boundaries.",
        "github_baseline": "pyswisseph exposes the Swiss Ephemeris, a high-precision astrological calculation backend.",
        "relative_position": "behind_when_no_ephemeris_configured",
        "required_to_lead": "Enable pyswisseph or an equivalent ephemeris backend and add natal/transit regression fixtures.",
    },
    {
        "dimension": "calendar_and_xuanze",
        "this_project": "Approximate/auto/professional calendar boundary plus structured xuanze scaffold and JSON-CLI provider hook.",
        "github_baseline": "lunar-python covers rich Chinese calendar and almanac fields including Ganzhi, solar terms, Xiu, twelve officers, and Huangdao data.",
        "relative_position": "competitive_scaffold_provider_dependent",
        "required_to_lead": "Use a verified production almanac provider and cite exact rule tables for xuanze fields.",
    },
    {
        "dimension": "empirical_validation",
        "this_project": "Separates report-quality validation from predictive-truth validation, uses non-predictive holdouts as evolution gates, and audits/imports reviewed outcome-dataset manifests without optimizing life-event labels.",
        "github_baseline": "Open-source metaphysics projects rarely include explicit consent/privacy/baseline/statistical-plan gates.",
        "relative_position": "ahead_for_safety_and_validation_governance",
        "required_to_lead": "Add an externally reviewed, consented outcome dataset before enabling predictive optimization.",
    },
    {
        "dimension": "classical_evidence",
        "this_project": "Provenance-bearing evidence index, safe seed records, manifest ingestion, and allowlisted refresh pipeline.",
        "github_baseline": "Most calculation libraries do not provide source-grounded claim review across traditions.",
        "relative_position": "ahead_for_evidence_governance",
        "required_to_lead": "Configure reviewed public-domain/open-license feeds and scheduled production refresh.",
    },
    {
        "dimension": "provider_protocol_governance",
        "this_project": "JSON-CLI provider contracts include sample IO, self-checking raw contracts, runtime protocol identity handshakes, stable protocol hashes, certification receipts, hash-chain ledgers, drift checks, and stale-protocol production gates.",
        "github_baseline": "Most domain calculation repositories expose APIs or scripts but do not bind provider certification receipts to versioned integration contracts.",
        "relative_position": "ahead_for_provider_governance",
        "required_to_lead": "Record reviewed provider receipts for every domain in the deployment ledger.",
    },
    {
        "dimension": "release_governance",
        "this_project": "Release manifests aggregate audit, benchmark, readiness, outcome, and provider-ledger receipts into a stable top-level receipt with hash-chain ledger recording, drift comparison, and tamper blocking.",
        "github_baseline": "Most calculation or agent repositories rely on CI logs or manual release notes rather than machine-checkable release evidence ledgers.",
        "relative_position": "ahead_for_release_governance",
        "required_to_lead": "Record release manifests in production after provider receipts and external outcome datasets are complete.",
    },
]


PLAN_COMPLIANCE_SECTIONS = [
    {
        "section": "1_project_goal",
        "plan_ref": "plan_mingli5agents.md section 1",
        "requirement": "Build a SEMAS self-evolving five-agent mingli analysis system with coordinator, four specialists, discussion, voting, synthesis, and feedback-driven evolution.",
        "implemented": [
            "five_agent_topology",
            "discussion_voting_synthesis",
            "semas_evolution",
            "multi_objective_population_evolution",
            "evolution_governance_integrity",
        ],
        "gap_ids": [],
        "status": "implemented",
    },
    {
        "section": "2_llm_backend",
        "plan_ref": "plan_mingli5agents.md section 2",
        "requirement": "Use a unified LLM client abstraction with Kimi/DeepSeek/OpenAI-compatible switching.",
        "implemented": ["optional_llm_synthesis"],
        "gap_ids": [],
        "status": "implemented_optional",
    },
    {
        "section": "3_agent_architecture",
        "plan_ref": "plan_mingli5agents.md section 3",
        "requirement": "Coordinator plus BaZi, Zi Wei, Qi Men, and Western astrology agents with calculation/provider boundaries.",
        "implemented": [
            "five_agent_topology",
            "calendar_provider_boundary",
            "bazi_deep_analysis",
            "bazi_eight_school_method_matrix",
            "provider_contract_method_surface_lock",
            "optional_ziwei_json_cli_provider",
            "optional_qimen_json_cli_provider",
            "optional_astrology_json_cli_provider",
        ],
        "gap_ids": ["professional_ziwei_provider", "professional_qimen_provider", "astronomical_ephemeris"],
        "status": "implemented_with_provider_gaps",
    },
    {
        "section": "4_analysis_layers",
        "plan_ref": "plan_mingli5agents.md section 4",
        "requirement": "Every specialist emits macro, micro, annual/yearly, monthly, and uncertainty layers.",
        "implemented": ["structured_reporting", "bazi_eight_school_method_matrix", "provider_contract_method_surface_lock"],
        "gap_ids": [],
        "status": "implemented",
    },
    {
        "section": "5_collaboration_workflow",
        "plan_ref": "plan_mingli5agents.md section 5",
        "requirement": "Parallel specialist analysis, multi-round discussion, cross-agent challenge, reconciliation, voting, source review, and final synthesis.",
        "implemented": ["discussion_voting_synthesis", "classical_text_index", "classical_source_refresh_pipeline"],
        "gap_ids": ["external_classic_text_retrieval"],
        "status": "implemented_with_production_source_gap",
    },
    {
        "section": "6_evolution_mechanism",
        "plan_ref": "plan_mingli5agents.md section 6",
        "requirement": "Execution, evaluation, mutation, sandbox/regression checks, selection, rollback/archive, and feedback memory.",
        "implemented": [
            "semas_evolution",
            "multi_objective_population_evolution",
            "evolution_governance_integrity",
            "provider_protocol_governance",
            "release_governance_ledger",
            "empirical_validation_harness",
            "outcome_dataset_split_governance",
            "outcome_dataset_split_aware_validation",
        ],
        "gap_ids": ["empirical_validation_dataset"],
        "status": "implemented_non_predictive",
    },
    {
        "section": "7_classical_sources",
        "plan_ref": "plan_mingli5agents.md section 7",
        "requirement": "Classical/source evidence retrieval, source labels, provenance, and uncertainty notes.",
        "implemented": ["classical_text_index", "classical_source_refresh_pipeline"],
        "gap_ids": ["external_classic_text_retrieval"],
        "status": "implemented_scaffold",
    },
    {
        "section": "8_project_structure",
        "plan_ref": "plan_mingli5agents.md section 8",
        "requirement": "Independent examples/mingli_5agents project with genomes, tools, evaluators, CLI/API, demo, and tests.",
        "implemented": ["api_cli_benchmark", "structured_reporting", "release_governance_ledger"],
        "gap_ids": [],
        "status": "implemented",
    },
    {
        "section": "9_open_questions",
        "plan_ref": "plan_mingli5agents.md section 9",
        "requirement": "Make correctness, conflict handling, citation boundaries, legal/ethical limits, and evolution cost visible.",
        "implemented": [
            "empirical_validation_harness",
            "outcome_dataset_split_governance",
            "outcome_dataset_split_aware_validation",
            "safety_scope",
            "multi_objective_population_evolution",
        ],
        "gap_ids": ["empirical_validation_dataset"],
        "status": "managed_with_known_limitations",
    },
    {
        "section": "10_safety_note",
        "plan_ref": "plan_mingli5agents.md section 10",
        "requirement": "State cultural-research/entertainment boundary and avoid high-stakes deterministic use.",
        "implemented": ["safety_scope"],
        "gap_ids": [],
        "status": "implemented",
    },
]


def _state_of_art_summary(capabilities: dict[str, bool]) -> dict[str, Any]:
    strengths = [
        item["dimension"]
        for item in GITHUB_COMPARISON_MATRIX
        if item["relative_position"].startswith("ahead")
        or (
            item["dimension"] == "calendar_and_xuanze"
            and capabilities.get("professional_bazi_provider_available")
        )
    ]
    provider_gaps = [
        "professional_ziwei_provider_available",
        "professional_qimen_provider_available",
        "ephemeris_astrology_provider_available",
    ]
    missing_providers = [key for key in provider_gaps if not capabilities.get(key)]
    production_ready = not missing_providers and capabilities.get("reference_chart_contracts", False)
    return {
        "verdict": "advanced_agentic_framework_not_full_domain_sota" if missing_providers else "near_sota_with_configured_providers",
        "production_ready_for_professional_calculation": production_ready,
        "request_scoped_production_ready_path": bool(capabilities.get("request_scoped_full_external_provider_injection")),
        "request_scoped_provenance_required": bool(capabilities.get("request_scoped_external_provider_provenance")),
        "production_input_geocoding": bool(capabilities.get("birthplace_geocoding_provenance")),
        "birthplace_geocoding_production_gate": "benchmark_birthplaces_geocoded"
        if capabilities.get("birthplace_geocoding_production_gate")
        else "",
        "deliberation_receipt_production_gate": "benchmark_deliberation_receipts_bound"
        if capabilities.get("discussion_voting")
        else "",
        "strength_dimensions": strengths,
        "blocking_provider_capabilities": missing_providers,
        "blocking_provider_scope": "environment_configured_backends",
        "comparison_scope": "GitHub/open-source project comparison plus local capability checks.",
        "last_reviewed": "2026-06-21",
    }


def _github_comparison_receipt(
    *,
    state_of_art: dict[str, Any],
    capabilities: dict[str, bool],
    github_matrix: list[dict[str, Any]],
    external_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    material = {
        "schema_version": "github-comparison-receipt-v1",
        "comparison_scope": state_of_art.get("comparison_scope"),
        "last_reviewed": state_of_art.get("last_reviewed"),
        "verdict": state_of_art.get("verdict"),
        "matrix_sha256": _stable_json_sha256(github_matrix),
        "candidate_sha256": _stable_json_sha256(external_candidates),
        "dimension_count": len(github_matrix),
        "dimensions": [item.get("dimension") for item in github_matrix],
        "relative_positions": {
            item.get("dimension"): item.get("relative_position")
            for item in github_matrix
            if item.get("dimension")
        },
        "candidate_projects": [
            {
                "domain": item.get("domain"),
                "name": item.get("name"),
                "url": item.get("url"),
                "fit": item.get("fit"),
                "audit_note": item.get("audit_note"),
            }
            for item in external_candidates
            if str(item.get("url", "")).startswith("https://github.com/")
        ],
        "blocking_provider_capabilities": state_of_art.get("blocking_provider_capabilities", []),
        "production_ready_for_professional_calculation": state_of_art.get(
            "production_ready_for_professional_calculation"
        ),
        "request_scoped_production_ready_path": state_of_art.get("request_scoped_production_ready_path"),
        "request_scoped_provenance_required": state_of_art.get("request_scoped_provenance_required"),
        "local_capability_sha256": _stable_json_sha256(dict(sorted(capabilities.items()))),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _plan_compliance_receipt(plan_compliance: dict[str, Any]) -> dict[str, Any]:
    matrix = plan_compliance.get("matrix", [])
    section_gap_coverage = plan_compliance.get("section_gap_resolution_coverage", {})
    source_receipt = plan_compliance.get("source_receipt", {})
    material = {
        "schema_version": "plan-compliance-receipt-v1",
        "source": plan_compliance.get("source"),
        "source_receipt_sha256": source_receipt.get("sha256") if isinstance(source_receipt, dict) else None,
        "section_count": plan_compliance.get("section_count"),
        "implemented_count": plan_compliance.get("implemented_count"),
        "sections_with_gaps": plan_compliance.get("sections_with_gaps", []),
        "matrix_sha256": _stable_json_sha256(matrix),
        "section_gap_resolution_coverage_sha256": _stable_json_sha256(section_gap_coverage),
        "coverage_status": section_gap_coverage.get("status") if isinstance(section_gap_coverage, dict) else None,
        "missing_plan_gap_ids": section_gap_coverage.get("missing_plan_gap_ids", [])
        if isinstance(section_gap_coverage, dict)
        else [],
        "invalid_plan_gap_ids": section_gap_coverage.get("invalid_plan_gap_ids", [])
        if isinstance(section_gap_coverage, dict)
        else [],
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _industry_event_source_manifest_example_receipt() -> dict[str, Any]:
    audit = audit_industry_event_manifest(INDUSTRY_EVENT_SOURCE_MANIFEST_EXAMPLE)
    receipt = industry_event_manifest_receipt(audit)
    material = {
        "schema_version": "industry-event-source-manifest-example-receipt-v1",
        "path": str(INDUSTRY_EVENT_SOURCE_MANIFEST_EXAMPLE.relative_to(REPO_ROOT)),
        "exists": INDUSTRY_EVENT_SOURCE_MANIFEST_EXAMPLE.exists(),
        "readable": audit.get("valid") is True,
        "content_hash": audit.get("content_hash"),
        "manifest_schema_version": audit.get("schema_version"),
        "manifest_status": audit.get("manifest_status"),
        "production_evidence": audit.get("production_evidence"),
        "externally_reviewed": audit.get("externally_reviewed"),
        "record_count": audit.get("record_count"),
        "positive_event_count": audit.get("positive_event_count"),
        "negative_event_count": audit.get("negative_event_count"),
        "domain_count": len(audit.get("domains", [])),
        "domains": audit.get("domains", []),
        "industry_count": len(audit.get("industries", [])),
        "industries": audit.get("industries", []),
        "source_family_count": audit.get("source_family_count"),
        "source_families": audit.get("source_families", []),
        "candidate_source_count": audit.get("candidate_source_count"),
        "candidate_source_names": audit.get("candidate_source_names", []),
        "required_record_fields": audit.get("required_record_fields", []),
        "all_records_have_required_fields": audit.get("valid") is True,
        "has_positive_and_negative_examples": audit.get("has_positive_and_negative_examples"),
        "split_roles": audit.get("split_roles", []),
        "underlying_audit_receipt_sha256": receipt.get("sha256"),
        "status": "ready_example" if audit.get("valid") is True else "incomplete",
        "failures": audit.get("failures", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _famous_case_source_review_routing_complete(famous_case_annual: dict[str, Any]) -> bool:
    routing = famous_case_annual.get("source_review_routing_summary")
    if not isinstance(routing, dict):
        return False
    return (
        routing.get("routing_complete") is True
        and routing.get("global_bypassed_low_quality_topics") == []
        and routing.get("domain_bypassed_low_quality_slices") == []
        and routing.get("evolution_bypassed_low_quality_topics") == []
    )


def _famous_case_source_review_queue_aligned(famous_case_annual: dict[str, Any]) -> bool:
    queue = famous_case_annual.get("rule_refinement_queue")
    if not isinstance(queue, list) or not queue:
        return False
    source_review_items = [
        item for item in queue if isinstance(item, dict) and item.get("priority") == "source_review_first"
    ]
    if not source_review_items:
        return False
    forbidden_phrases = ("ten-god evidence", "branch interaction evidence", "strict-rule predicate")
    for item in source_review_items:
        evidence = item.get("recommended_evidence")
        if not isinstance(evidence, list) or not evidence:
            return False
        text_items = [str(value) for value in evidence]
        if not any("rated birth-time sources" in value for value in text_items):
            return False
        if any(any(phrase in value for value in text_items) for phrase in forbidden_phrases):
            return False
    return True


def _industry_event_source_query_plan_example_receipt() -> dict[str, Any]:
    audit = audit_industry_event_query_plan(INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE)
    receipt = industry_event_query_plan_receipt(audit)
    material = {
        "schema_version": "industry-event-source-query-plan-example-receipt-v1",
        "path": str(INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE.relative_to(REPO_ROOT)),
        "exists": INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE.exists(),
        "readable": audit.get("valid") is True,
        "content_hash": audit.get("content_hash"),
        "plan_schema_version": audit.get("schema_version"),
        "plan_status": audit.get("plan_status"),
        "collection_ready": audit.get("collection_ready"),
        "externally_reviewed": audit.get("externally_reviewed"),
        "live_collection_allowed": audit.get("live_collection_allowed"),
        "source_id": audit.get("source_id"),
        "endpoint_url": audit.get("endpoint_url"),
        "template_count": audit.get("template_count"),
        "domains": audit.get("domains", []),
        "event_topics": audit.get("event_topics", []),
        "required_manifest_fields_mapped": audit.get("required_manifest_fields_mapped"),
        "underlying_audit_receipt_sha256": receipt.get("sha256"),
        "status": "ready_example" if audit.get("valid") is True else "incomplete",
        "failures": audit.get("failures", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _industry_event_candidate_cases_example_receipt() -> dict[str, Any]:
    audit = audit_industry_event_candidate_cases(INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE)
    receipt = industry_event_candidate_cases_receipt(audit)
    material = {
        "schema_version": "industry-event-candidate-cases-example-receipt-v1",
        "path": str(INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE.relative_to(REPO_ROOT)),
        "exists": INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE.exists(),
        "readable": audit.get("valid") is True,
        "content_hash": audit.get("content_hash"),
        "candidate_schema_version": audit.get("schema_version"),
        "candidate_pool_status": audit.get("candidate_pool_status"),
        "production_ready": audit.get("production_ready"),
        "externally_reviewed": audit.get("externally_reviewed"),
        "candidate_count": audit.get("candidate_count"),
        "domain_counts": audit.get("domain_counts", {}),
        "domains": audit.get("domains", []),
        "split_roles": audit.get("split_roles", []),
        "person_qids": audit.get("person_qids", []),
        "required_candidate_fields": audit.get("required_candidate_fields", []),
        "underlying_audit_receipt_sha256": receipt.get("sha256"),
        "status": "ready_example" if audit.get("valid") is True else "incomplete",
        "failures": audit.get("failures", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _industry_event_cross_domain_fixture_import_receipt() -> dict[str, Any]:
    response_paths = {
        "film": INDUSTRY_EVENT_WIKIDATA_FILM_RESPONSE_EXAMPLE,
        "music": INDUSTRY_EVENT_WIKIDATA_MUSIC_RESPONSE_EXAMPLE,
        "sports": INDUSTRY_EVENT_WIKIDATA_SPORTS_RESPONSE_EXAMPLE,
    }
    failures = [
        f"missing fixture response for {domain}: {path}"
        for domain, path in response_paths.items()
        if not path.exists()
    ]
    batch_plan: dict[str, Any] = {}
    draft_import: dict[str, Any] = {}
    if not failures:
        batch_plan = build_candidate_pool_fetch_cache_plan(
            INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE,
            query_plan_path=INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE,
            cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE,
        )
        response_payloads = {domain: path.read_bytes() for domain, path in response_paths.items()}
        for plan in batch_plan.get("plans", []):
            if not isinstance(plan, dict):
                continue
            case = plan.get("case", {}) if isinstance(plan.get("case"), dict) else {}
            payload = response_payloads.get(str(case.get("domain", "")))
            if payload is None:
                failures.append(f"missing response payload for domain: {case.get('domain')}")
                continue
            for entry in plan.get("cache_entries", []):
                if not isinstance(entry, dict):
                    continue
                cache_path = Path(str(entry.get("cache_path", "")))
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(payload)
        draft_import = build_candidate_pool_manifest_drafts_from_cache(
            INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE,
            query_plan_path=INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE,
            cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE,
        )
        failures.extend(str(failure) for failure in draft_import.get("failures", []))
    label_table = draft_import.get("validation_label_table", {}) if isinstance(draft_import, dict) else {}
    symbolic_readiness_summary = _cross_domain_fixture_symbolic_readiness_summary(draft_import)
    coverage_gate = (
        label_table.get("cross_domain_coverage_gate", {})
        if isinstance(label_table.get("cross_domain_coverage_gate"), dict)
        else {}
    )
    material = {
        "schema_version": "industry-event-cross-domain-fixture-import-receipt-v1",
        "status": "ready_example" if not failures and draft_import.get("valid") is True else "incomplete",
        "candidate_path": str(INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE.relative_to(REPO_ROOT)),
        "query_plan_path": str(INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE.relative_to(REPO_ROOT)),
        "cache_dir": str(INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE.relative_to(REPO_ROOT)),
        "fixture_response_paths": {
            domain: str(path.relative_to(REPO_ROOT))
            for domain, path in sorted(response_paths.items())
        },
        "offline_only": True,
        "production_evidence": False,
        "candidate_count": draft_import.get("candidate_count", 0),
        "draft_count": draft_import.get("draft_count", 0),
        "positive_record_count": draft_import.get("positive_record_count", 0),
        "negative_record_count": draft_import.get("negative_record_count", 0),
        "record_count": draft_import.get("record_count", 0),
        "domains": draft_import.get("domains", []),
        "cross_domain_coverage_gate_passed": coverage_gate.get("passed") is True,
        "domain_coverage_summary": label_table.get("domain_coverage_summary", []),
        "symbolic_scoring_readiness_summary": symbolic_readiness_summary,
        "candidate_pool_fetch_cache_receipt_sha256": batch_plan.get("candidate_pool_fetch_cache_receipt", {}).get(
            "sha256"
        )
        if isinstance(batch_plan, dict)
        else None,
        "candidate_pool_draft_import_receipt_sha256": draft_import.get(
            "candidate_pool_draft_import_receipt", {}
        ).get("sha256")
        if isinstance(draft_import.get("candidate_pool_draft_import_receipt"), dict)
        else None,
        "validation_label_table_receipt_sha256": label_table.get("validation_label_table_receipt", {}).get("sha256")
        if isinstance(label_table.get("validation_label_table_receipt"), dict)
        else None,
        "boundary": (
            "Repository-authored offline fixture import only; it validates pipeline shape, not production source "
            "review or factual event-label completeness."
        ),
        "failures": failures,
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _cross_domain_fixture_symbolic_readiness_summary(draft_import: dict[str, Any]) -> dict[str, Any]:
    """Summarize which imported celebrity labels can enter BaZi symbolic scoring."""
    payload = draft_import.get("combined_draft_manifest", {}) if isinstance(draft_import, dict) else {}
    if not isinstance(payload, dict) or not payload:
        return {
            "status": "blocked_missing_manifest",
            "label_count": 0,
            "ready_label_count": 0,
            "blocked_label_count": 0,
            "case_count": 0,
            "ready_case_count": 0,
            "blocked_case_count": 0,
            "ready_case_ids": [],
            "blocked_case_ids": [],
            "missing_birth_profile_case_ids": [],
            "domain_topic_summary": [],
            "gates": [],
            "birth_profile_completion_task_plan": [],
            "birth_profile_completion_workplan_summary": {
                "status": "blocked_missing_workplan",
                "valid": False,
                "source_task_count": 0,
                "deferred_task_count": 0,
                "work_item_count": 0,
                "readiness_status": "blocked_missing_workplan",
                "deferred_blocked_gate_count": 0,
                "deferred_failed_integrity_check_count": 0,
                "deferred_task_summaries": [],
                "boundary": "No evidence workplan was available for birth-profile completion.",
            },
            "birth_profile_review_manifest_summary": {
                "status": "missing",
                "valid": False,
                "production_evidence": False,
                "request_count": 0,
                "case_count": 0,
                "domains": [],
                "blocked_label_count": 0,
                "ready_for_import": False,
                "domain_summary": [],
                "failures": ["birth profile review manifest audit is missing"],
                "boundary": "No birth-profile review manifest was available.",
            },
            "birth_profile_source_review_workplan_summary": {
                "status": "blocked_missing_source_review_workplan",
                "valid": False,
                "would_fetch_live_sources": False,
                "would_write_review_manifest": False,
                "request_count": 0,
                "work_item_count": 0,
                "source_review_gate_passed": False,
                "blocking_reasons": ["birth profile source review workplan is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile source review workplan was available.",
            },
            "birth_profile_source_lookup_plan_summary": {
                "status": "blocked_missing_source_lookup_plan",
                "valid": False,
                "would_fetch_live_sources": False,
                "would_write_cache": False,
                "would_write_review_manifest": False,
                "lookup_item_count": 0,
                "query_count": 0,
                "source_family_count": 0,
                "source_family_catalog_bound": False,
                "birth_time_source_policy_bound": False,
                "identity_anchor_birth_time_disallowed": False,
                "lookup_gate_passed": False,
                "blocking_reasons": ["birth profile source lookup plan is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile source lookup plan was available.",
            },
            "birth_profile_source_cache_audit_summary": {
                "status": "blocked_missing_source_cache_audit",
                "valid": False,
                "would_fetch_live_sources": False,
                "would_write_cache": False,
                "would_write_review_manifest": False,
                "would_import_profiles": False,
                "expected_cache_count": 0,
                "present_cache_count": 0,
                "missing_cache_count": 0,
                "accepted_cache_count": 0,
                "cache_audit_gate_passed": False,
                "blocking_reasons": ["birth profile source cache audit is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile source cache audit was available.",
            },
            "birth_profile_source_cache_template_preview_summary": {
                "status": "blocked_missing_source_cache_template_preview",
                "valid": False,
                "would_fetch_live_sources": False,
                "would_write_cache": False,
                "would_import_profiles": False,
                "template_count": 0,
                "template_preview_gate_passed": False,
                "blocking_reasons": ["birth profile source cache template preview is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile source cache template preview was available.",
            },
            "birth_profile_source_family_cache_enforcement_summary": {
                "status": "blocked_missing_source_family_cache_enforcement_probe",
                "valid": False,
                "probe_executed": False,
                "identity_anchor_birth_time_rejected": False,
                "accepted_cache_count_after_probe": None,
                "probe_source_family_id": "",
                "failure_contains_birth_time_policy": False,
                "failures": ["birth profile source family cache enforcement probe is missing"],
                "boundary": "No source-family cache enforcement probe was available.",
            },
            "birth_profile_substantive_evidence_cache_enforcement_summary": {
                "status": "blocked_missing_substantive_evidence_cache_enforcement_probe",
                "valid": False,
                "probe_executed": False,
                "metadata_only_reviewed_cache_rejected": False,
                "accepted_cache_count_after_probe": None,
                "probe_source_family_id": "",
                "failure_contains_substantive_birth_policy": False,
                "failures": ["birth profile substantive evidence cache enforcement probe is missing"],
                "boundary": "No substantive-evidence cache enforcement probe was available.",
            },
            "birth_profile_reviewed_manifest_draft_preview_summary": {
                "status": "blocked_missing_reviewed_manifest_draft_preview",
                "valid": False,
                "would_write_review_manifest": False,
                "would_import_profiles": False,
                "draft_ready_for_human_approval": False,
                "review_request_count": 0,
                "complete_review_request_count": 0,
                "incomplete_review_request_count": 0,
                "draft_gate_passed": False,
                "blocking_reasons": ["birth profile reviewed manifest draft preview is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile reviewed manifest draft preview was available.",
            },
            "birth_profile_reviewed_manifest_file_preview_summary": {
                "status": "blocked_missing_reviewed_manifest_file_preview",
                "valid": False,
                "would_write_file": False,
                "would_import_profiles": False,
                "write_ready_for_human_approval": False,
                "target_file": "",
                "target_file_sha256": None,
                "file_preview_gate_passed": False,
                "blocking_reasons": ["birth profile reviewed manifest file preview is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile reviewed manifest file preview was available.",
            },
            "birth_profile_import_preview_summary": {
                "status": "blocked_missing_preview",
                "valid": False,
                "would_write_file": False,
                "import_allowed": False,
                "request_count": 0,
                "blocked_request_count": 0,
                "import_ready_request_count": 0,
                "import_gate_passed": False,
                "blocking_reasons": ["birth profile import preview is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile import preview was available.",
            },
            "birth_profile_fixture_patch_preview_summary": {
                "status": "blocked_missing_patch_preview",
                "valid": False,
                "would_write_file": False,
                "patch_ready_for_review": False,
                "candidate_count": 0,
                "candidate_case_ids": [],
                "patch_gate_passed": False,
                "target_file_sha256": None,
                "patch_text_sha256": None,
                "blocking_reasons": ["birth profile fixture patch preview is missing"],
                "integrity_check_status": "missing",
                "boundary": "No birth-profile fixture patch preview was available.",
            },
            "symbolic_scoring_readiness_receipt_sha256": None,
            "symbolic_annual_score_receipt_sha256": None,
            "evidence_workplan_receipt_sha256": None,
            "birth_profile_review_manifest_receipt_sha256": None,
            "birth_profile_source_review_workplan_receipt_sha256": None,
            "birth_profile_source_lookup_plan_receipt_sha256": None,
            "birth_profile_source_cache_template_preview_receipt_sha256": None,
            "birth_profile_source_cache_audit_receipt_sha256": None,
            "birth_profile_reviewed_manifest_draft_preview_receipt_sha256": None,
            "birth_profile_reviewed_manifest_file_preview_receipt_sha256": None,
            "birth_profile_import_preview_receipt_sha256": None,
            "birth_profile_fixture_patch_preview_receipt_sha256": None,
            "boundary": "No combined draft manifest was available, so symbolic scoring readiness could not be checked.",
        }
    readiness = build_industry_event_symbolic_scoring_readiness_payload(
        payload,
        path="<cross-domain-fixture-import>",
        raw=json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
        birth_cases=famous_case_records(),
    )
    scoring = build_industry_event_symbolic_annual_score_payload(
        payload,
        path="<cross-domain-fixture-import>",
        raw=json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
        birth_cases=famous_case_records(),
    )
    workplan = build_industry_event_evidence_workplan_from_symbolic_score(
        scoring,
        candidate_path=INDUSTRY_EVENT_CANDIDATE_CASES_EXAMPLE,
        query_plan_path=INDUSTRY_EVENT_SOURCE_QUERY_PLAN_EXAMPLE,
        cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE,
    )
    birth_review = audit_birth_profile_review_manifest(BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE)
    birth_source_review_workplan = build_birth_profile_source_review_workplan(BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE)
    birth_source_lookup_plan = build_birth_profile_source_lookup_plan(
        BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
        cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE / "birth_profile_source_cache",
    )
    birth_source_cache_template_preview = build_birth_profile_source_cache_template_preview(
        BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
        cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE / "birth_profile_source_cache",
    )
    birth_source_family_cache_enforcement_probe = _cross_domain_birth_profile_source_family_cache_enforcement_probe()
    birth_substantive_evidence_cache_enforcement_probe = (
        _cross_domain_birth_profile_substantive_evidence_cache_enforcement_probe()
    )
    birth_source_cache_audit = build_birth_profile_source_cache_audit(
        BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
        cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE / "birth_profile_source_cache",
    )
    birth_reviewed_manifest_draft_preview = build_birth_profile_reviewed_manifest_draft_preview(
        BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
        cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE / "birth_profile_source_cache",
    )
    birth_reviewed_manifest_file_preview = build_birth_profile_reviewed_manifest_file_preview(
        BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
        cache_dir=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE / "birth_profile_source_cache",
        target_path=INDUSTRY_EVENT_CROSS_DOMAIN_FIXTURE_CACHE / "birth_profile_review_manifest_reviewed.json",
    )
    birth_import_preview = build_birth_profile_import_preview(BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE)
    birth_fixture_patch_preview = build_birth_profile_fixture_patch_preview(BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE)
    case_summary = readiness.get("case_summary", []) if isinstance(readiness.get("case_summary"), list) else []
    ready_case_ids = sorted(
        str(item.get("case_id"))
        for item in case_summary
        if isinstance(item, dict) and item.get("birth_profile_available") is True
    )
    blocked_case_ids = sorted(
        str(item.get("case_id"))
        for item in case_summary
        if isinstance(item, dict) and item.get("scoring_ready") is not True
    )
    missing_birth_profile_case_ids = sorted(
        str(item.get("case_id"))
        for item in case_summary
        if isinstance(item, dict) and item.get("birth_profile_available") is not True
    )
    receipt = readiness.get("symbolic_scoring_readiness_receipt", {})
    return {
        "status": readiness.get("status"),
        "label_count": readiness.get("label_count", 0),
        "ready_label_count": readiness.get("ready_label_count", 0),
        "blocked_label_count": readiness.get("blocked_label_count", 0),
        "case_count": readiness.get("case_count", 0),
        "ready_case_count": readiness.get("ready_case_count", 0),
        "blocked_case_count": readiness.get("blocked_case_count", 0),
        "ready_case_ids": ready_case_ids,
        "blocked_case_ids": blocked_case_ids,
        "missing_birth_profile_case_ids": missing_birth_profile_case_ids,
        "domain_topic_summary": readiness.get("domain_topic_summary", []),
        "gates": readiness.get("gates", []),
        "birth_profile_completion_task_plan": _cross_domain_birth_profile_completion_task_plan(scoring),
        "birth_profile_completion_workplan_summary": _cross_domain_birth_profile_completion_workplan_summary(workplan),
        "birth_profile_review_manifest_summary": _cross_domain_birth_profile_review_manifest_summary(birth_review),
        "birth_profile_source_review_workplan_summary": _cross_domain_birth_profile_source_review_workplan_summary(
            birth_source_review_workplan
        ),
        "birth_profile_source_lookup_plan_summary": _cross_domain_birth_profile_source_lookup_plan_summary(
            birth_source_lookup_plan
        ),
        "birth_profile_source_cache_template_preview_summary": (
            _cross_domain_birth_profile_source_cache_template_preview_summary(
                birth_source_cache_template_preview
            )
        ),
        "birth_profile_source_family_cache_enforcement_summary": (
            birth_source_family_cache_enforcement_probe
        ),
        "birth_profile_substantive_evidence_cache_enforcement_summary": (
            birth_substantive_evidence_cache_enforcement_probe
        ),
        "birth_profile_source_cache_audit_summary": _cross_domain_birth_profile_source_cache_audit_summary(
            birth_source_cache_audit
        ),
        "birth_profile_reviewed_manifest_draft_preview_summary": (
            _cross_domain_birth_profile_reviewed_manifest_draft_preview_summary(
                birth_reviewed_manifest_draft_preview
            )
        ),
        "birth_profile_reviewed_manifest_file_preview_summary": (
            _cross_domain_birth_profile_reviewed_manifest_file_preview_summary(
                birth_reviewed_manifest_file_preview
            )
        ),
        "birth_profile_import_preview_summary": _cross_domain_birth_profile_import_preview_summary(
            birth_import_preview
        ),
        "birth_profile_fixture_patch_preview_summary": _cross_domain_birth_profile_fixture_patch_preview_summary(
            birth_fixture_patch_preview
        ),
        "symbolic_scoring_readiness_receipt_sha256": receipt.get("sha256") if isinstance(receipt, dict) else None,
        "symbolic_annual_score_receipt_sha256": scoring.get("symbolic_annual_score_receipt", {}).get("sha256")
        if isinstance(scoring.get("symbolic_annual_score_receipt"), dict)
        else None,
        "evidence_workplan_receipt_sha256": workplan.get("evidence_workplan_receipt", {}).get("sha256")
        if isinstance(workplan.get("evidence_workplan_receipt"), dict)
        else None,
        "birth_profile_review_manifest_receipt_sha256": birth_review.get(
            "birth_profile_review_manifest_receipt", {}
        ).get("sha256")
        if isinstance(birth_review.get("birth_profile_review_manifest_receipt"), dict)
        else None,
        "birth_profile_source_review_workplan_receipt_sha256": birth_source_review_workplan.get(
            "source_review_workplan_receipt", {}
        ).get("sha256")
        if isinstance(birth_source_review_workplan.get("source_review_workplan_receipt"), dict)
        else None,
        "birth_profile_source_lookup_plan_receipt_sha256": birth_source_lookup_plan.get(
            "source_lookup_plan_receipt", {}
        ).get("sha256")
        if isinstance(birth_source_lookup_plan.get("source_lookup_plan_receipt"), dict)
        else None,
        "birth_profile_source_cache_template_preview_receipt_sha256": birth_source_cache_template_preview.get(
            "source_cache_template_preview_receipt", {}
        ).get("sha256")
        if isinstance(birth_source_cache_template_preview.get("source_cache_template_preview_receipt"), dict)
        else None,
        "birth_profile_source_cache_audit_receipt_sha256": birth_source_cache_audit.get(
            "source_cache_audit_receipt", {}
        ).get("sha256")
        if isinstance(birth_source_cache_audit.get("source_cache_audit_receipt"), dict)
        else None,
        "birth_profile_reviewed_manifest_draft_preview_receipt_sha256": (
            birth_reviewed_manifest_draft_preview.get("reviewed_manifest_draft_preview_receipt", {}).get("sha256")
            if isinstance(
                birth_reviewed_manifest_draft_preview.get("reviewed_manifest_draft_preview_receipt"), dict
            )
            else None
        ),
        "birth_profile_reviewed_manifest_file_preview_receipt_sha256": (
            birth_reviewed_manifest_file_preview.get("reviewed_manifest_file_preview_receipt", {}).get("sha256")
            if isinstance(birth_reviewed_manifest_file_preview.get("reviewed_manifest_file_preview_receipt"), dict)
            else None
        ),
        "birth_profile_import_preview_receipt_sha256": birth_import_preview.get(
            "import_preview_receipt", {}
        ).get("sha256")
        if isinstance(birth_import_preview.get("import_preview_receipt"), dict)
        else None,
        "birth_profile_fixture_patch_preview_receipt_sha256": birth_fixture_patch_preview.get(
            "fixture_patch_preview_receipt", {}
        ).get("sha256")
        if isinstance(birth_fixture_patch_preview.get("fixture_patch_preview_receipt"), dict)
        else None,
        "boundary": readiness.get("boundary", ""),
    }


def _cross_domain_birth_profile_completion_task_plan(scoring: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose blocked celebrity birth-profile work as a compact audit task plan."""
    tasks = scoring.get("evolution_task_plan", []) if isinstance(scoring, dict) else []
    if not isinstance(tasks, list):
        return []
    completion_tasks = []
    for task in tasks:
        if not isinstance(task, dict) or task.get("task_type") != "add_reviewed_birth_profiles":
            continue
        metrics = task.get("current_metrics", {}) if isinstance(task.get("current_metrics"), dict) else {}
        completion_tasks.append(
            {
                "task_id": task.get("task_id"),
                "domain": task.get("domain"),
                "symbolic_event_topic": task.get("symbolic_event_topic"),
                "priority": task.get("priority"),
                "task_type": task.get("task_type"),
                "blocked_label_count": metrics.get("blocked_label_count", 0),
                "blocked_case_count": metrics.get("blocked_case_count", 0),
                "blocked_case_ids": task.get("blocked_case_ids", []),
                "blocked_public_names": task.get("blocked_public_names", []),
                "next_evidence_to_add": task.get("next_evidence_to_add", []),
                "acceptance_criteria": task.get("acceptance_criteria", []),
                "blocking_reasons": task.get("blocking_reasons", []),
                "boundary": task.get("boundary", ""),
            }
        )
    return sorted(
        completion_tasks,
        key=lambda item: (str(item.get("domain")), str(item.get("symbolic_event_topic")), str(item.get("task_id"))),
    )


def _cross_domain_birth_profile_completion_workplan_summary(workplan: dict[str, Any]) -> dict[str, Any]:
    """Expose the reviewed-data workplan outcome without embedding every nested draft artifact."""
    if not isinstance(workplan, dict) or not workplan:
        return {
            "status": "blocked_missing_workplan",
            "valid": False,
            "source_task_count": 0,
            "deferred_task_count": 0,
            "work_item_count": 0,
            "readiness_status": "blocked_missing_workplan",
            "deferred_blocked_gate_count": 0,
            "deferred_failed_integrity_check_count": 0,
            "deferred_task_summaries": [],
            "boundary": "No evidence workplan was available for birth-profile completion.",
        }
    readiness = workplan.get("readiness_summary", {}) if isinstance(workplan.get("readiness_summary"), dict) else {}
    deferred_summaries = []
    for task in workplan.get("deferred_tasks", []):
        if not isinstance(task, dict):
            continue
        gate_summary = task.get("gate_summary", {}) if isinstance(task.get("gate_summary"), dict) else {}
        completion = (
            task.get("local_completion_work_order", {})
            if isinstance(task.get("local_completion_work_order"), dict)
            else {}
        )
        deferred_summaries.append(
            {
                "task_id": task.get("task_id"),
                "domain": task.get("domain"),
                "symbolic_event_topic": task.get("symbolic_event_topic"),
                "task_type": task.get("task_type"),
                "blocked_case_ids": task.get("blocked_case_ids", []),
                "local_birth_profile_suggestion_count": task.get("local_birth_profile_suggestion_count", 0),
                "local_birth_profile_suggestion_case_ids": [
                    str(item.get("case_id"))
                    for item in task.get("local_birth_profile_suggestions", [])
                    if isinstance(item, dict) and item.get("case_id")
                ],
                "completion_work_order_status": completion.get("status"),
                "gate_summary_status": gate_summary.get("status"),
                "blocked_gate_count": gate_summary.get("blocked_gate_count", 0),
                "failed_integrity_check_count": gate_summary.get("failed_integrity_check_count", 0),
                "next_action": task.get("next_action"),
            }
        )
    return {
        "status": workplan.get("status"),
        "valid": workplan.get("valid") is True,
        "source_task_count": workplan.get("source_task_count", 0),
        "deferred_task_count": workplan.get("deferred_task_count", 0),
        "work_item_count": workplan.get("work_item_count", 0),
        "readiness_status": readiness.get("status"),
        "deferred_blocked_gate_count": readiness.get("deferred_blocked_gate_count", 0),
        "deferred_failed_integrity_check_count": readiness.get("deferred_failed_integrity_check_count", 0),
        "deferred_task_summaries": deferred_summaries,
        "boundary": workplan.get("boundary", ""),
    }


def _cross_domain_birth_profile_review_manifest_summary(audit: dict[str, Any]) -> dict[str, Any]:
    """Summarize the reviewed-birth-profile collection worklist for audit portability."""
    if not isinstance(audit, dict) or not audit:
        return {
            "status": "missing",
            "valid": False,
            "production_evidence": False,
            "request_count": 0,
            "case_count": 0,
            "domains": [],
            "blocked_label_count": 0,
            "ready_for_import": False,
            "domain_summary": [],
            "failures": ["birth profile review manifest audit is missing"],
            "boundary": "No birth-profile review manifest was available.",
        }
    return {
        "status": audit.get("status"),
        "valid": audit.get("valid") is True,
        "production_evidence": audit.get("production_evidence") is True,
        "request_count": audit.get("request_count", 0),
        "case_count": audit.get("case_count", 0),
        "domains": audit.get("domains", []),
        "blocked_label_count": audit.get("blocked_label_count", 0),
        "ready_for_import": audit.get("ready_for_import") is True,
        "domain_summary": audit.get("domain_summary", []),
        "failures": audit.get("failures", []),
        "boundary": audit.get("boundary", ""),
    }


def _cross_domain_birth_profile_source_review_workplan_summary(workplan: dict[str, Any]) -> dict[str, Any]:
    """Summarize human source-review work items for blocked celebrity birth profiles."""
    if not isinstance(workplan, dict) or not workplan:
        return {
            "status": "blocked_missing_source_review_workplan",
            "valid": False,
            "would_fetch_live_sources": False,
            "would_write_review_manifest": False,
            "request_count": 0,
            "work_item_count": 0,
            "review_progress_summary": {},
            "field_gap_summary": {},
            "source_review_gate_passed": False,
            "blocking_reasons": ["birth profile source review workplan is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile source review workplan was available.",
        }
    gate = workplan.get("source_review_gate", {}) if isinstance(workplan.get("source_review_gate"), dict) else {}
    integrity = workplan.get("integrity_check", {}) if isinstance(workplan.get("integrity_check"), dict) else {}
    return {
        "status": workplan.get("status"),
        "valid": workplan.get("valid") is True,
        "would_fetch_live_sources": workplan.get("would_fetch_live_sources") is True,
        "would_write_review_manifest": workplan.get("would_write_review_manifest") is True,
        "request_count": workplan.get("request_count", 0),
        "work_item_count": workplan.get("work_item_count", 0),
        "review_progress_summary": workplan.get("review_progress_summary", {}),
        "field_gap_summary": workplan.get("field_gap_summary", {}),
        "source_review_gate_passed": gate.get("passed") is True,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": workplan.get("boundary", ""),
    }


def _cross_domain_birth_profile_source_lookup_plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    """Summarize dry-run source lookup tasks for blocked celebrity birth profiles."""
    if not isinstance(plan, dict) or not plan:
        return {
            "status": "blocked_missing_source_lookup_plan",
            "valid": False,
            "would_fetch_live_sources": False,
            "would_write_cache": False,
            "would_write_review_manifest": False,
            "lookup_item_count": 0,
            "query_count": 0,
            "lookup_gate_passed": False,
            "blocking_reasons": ["birth profile source lookup plan is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile source lookup plan was available.",
        }
    gate = plan.get("lookup_gate", {}) if isinstance(plan.get("lookup_gate"), dict) else {}
    integrity = plan.get("integrity_check", {}) if isinstance(plan.get("integrity_check"), dict) else {}
    source_catalog = plan.get("source_family_catalog", {}) if isinstance(plan.get("source_family_catalog"), dict) else {}
    source_family_ids = {
        str(item.get("source_family_id"))
        for item in source_catalog.get("source_families", [])
        if isinstance(item, dict) and item.get("source_family_id")
    }
    planned_queries = [
        query
        for item in plan.get("lookup_items", [])
        if isinstance(item, dict)
        for query in item.get("planned_queries", [])
        if isinstance(query, dict)
    ]
    birth_time_queries = [
        query
        for query in planned_queries
        if isinstance(query.get("source_use_policy"), dict)
        and query.get("source_use_policy", {}).get("requires_rated_birth_time_source") is True
    ]
    birth_time_source_policy_bound = bool(birth_time_queries) and all(
        "rated_birth_time_source" in query.get("source_use_policy", {}).get("birth_time_may_be_satisfied_by", [])
        and any(
            isinstance(family, dict) and family.get("source_family_id") == "rated_birth_time_source"
            for family in query.get("recommended_source_families", [])
        )
        for query in birth_time_queries
    )
    identity_anchor_birth_time_disallowed = bool(planned_queries) and all(
        "birth_time" in str(query.get("source_use_policy", {}).get("disallowed_shortcut", ""))
        for query in planned_queries
        if isinstance(query.get("source_use_policy"), dict)
    )
    required_source_families = {
        "rated_birth_time_source",
        "wikidata_identity_anchor",
        "film_identity_and_work_anchor",
        "music_identity_and_work_anchor",
        "sports_identity_and_result_anchor",
    }
    return {
        "status": plan.get("status"),
        "valid": plan.get("valid") is True,
        "would_fetch_live_sources": plan.get("would_fetch_live_sources") is True,
        "would_write_cache": plan.get("would_write_cache") is True,
        "would_write_review_manifest": plan.get("would_write_review_manifest") is True,
        "lookup_item_count": plan.get("lookup_item_count", 0),
        "query_count": plan.get("query_count", 0),
        "source_family_count": source_catalog.get("source_family_count", 0),
        "source_family_catalog_bound": required_source_families.issubset(source_family_ids)
        and isinstance(source_catalog.get("source_family_catalog_receipt", {}).get("sha256"), str)
        and len(source_catalog.get("source_family_catalog_receipt", {}).get("sha256", "")) == 64,
        "birth_time_source_policy_bound": birth_time_source_policy_bound,
        "identity_anchor_birth_time_disallowed": identity_anchor_birth_time_disallowed,
        "domain_summary": plan.get("domain_summary", []),
        "lookup_gate_passed": gate.get("passed") is True,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": plan.get("boundary", ""),
    }


def _cross_domain_birth_profile_source_cache_audit_summary(audit: dict[str, Any]) -> dict[str, Any]:
    """Summarize manual source-cache audit state for blocked celebrity birth profiles."""
    if not isinstance(audit, dict) or not audit:
        return {
            "status": "blocked_missing_source_cache_audit",
            "valid": False,
            "would_fetch_live_sources": False,
            "would_write_cache": False,
            "would_write_review_manifest": False,
            "would_import_profiles": False,
            "expected_cache_count": 0,
            "present_cache_count": 0,
            "missing_cache_count": 0,
            "accepted_cache_count": 0,
            "cache_audit_gate_passed": False,
            "blocking_reasons": ["birth profile source cache audit is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile source cache audit was available.",
        }
    gate = audit.get("cache_audit_gate", {}) if isinstance(audit.get("cache_audit_gate"), dict) else {}
    integrity = audit.get("integrity_check", {}) if isinstance(audit.get("integrity_check"), dict) else {}
    return {
        "status": audit.get("status"),
        "valid": audit.get("valid") is True,
        "would_fetch_live_sources": audit.get("would_fetch_live_sources") is True,
        "would_write_cache": audit.get("would_write_cache") is True,
        "would_write_review_manifest": audit.get("would_write_review_manifest") is True,
        "would_import_profiles": audit.get("would_import_profiles") is True,
        "expected_cache_count": audit.get("expected_cache_count", 0),
        "present_cache_count": audit.get("present_cache_count", 0),
        "missing_cache_count": audit.get("missing_cache_count", 0),
        "accepted_cache_count": audit.get("accepted_cache_count", 0),
        "cache_audit_gate_passed": gate.get("passed") is True,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": audit.get("boundary", ""),
    }


def _cross_domain_birth_profile_source_cache_template_preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
    """Summarize non-mutating manual source-cache template preview state."""
    if not isinstance(preview, dict) or not preview:
        return {
            "status": "blocked_missing_source_cache_template_preview",
            "valid": False,
            "would_fetch_live_sources": False,
            "would_write_cache": False,
            "would_import_profiles": False,
            "template_count": 0,
            "template_preview_gate_passed": False,
            "blocking_reasons": ["birth profile source cache template preview is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile source cache template preview was available.",
        }
    gate = preview.get("template_preview_gate", {}) if isinstance(preview.get("template_preview_gate"), dict) else {}
    integrity = preview.get("integrity_check", {}) if isinstance(preview.get("integrity_check"), dict) else {}
    return {
        "status": preview.get("status"),
        "valid": preview.get("valid") is True,
        "would_fetch_live_sources": preview.get("would_fetch_live_sources") is True,
        "would_write_cache": preview.get("would_write_cache") is True,
        "would_import_profiles": preview.get("would_import_profiles") is True,
        "template_count": preview.get("template_count", 0),
        "template_preview_gate_passed": gate.get("passed") is True,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": preview.get("boundary", ""),
    }


def _cross_domain_birth_profile_source_family_cache_enforcement_probe() -> dict[str, Any]:
    """Probe that identity-anchor cache payloads cannot satisfy birth_time."""
    with tempfile.TemporaryDirectory(prefix="birth_profile_source_family_probe_") as temp_dir:
        cache_dir = Path(temp_dir) / "birth_profile_source_cache"
        before = build_birth_profile_source_cache_audit(
            BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
            cache_dir=cache_dir,
            domain="film",
        )
        cache_items = before.get("cache_items", []) if isinstance(before.get("cache_items"), list) else []
        target = next(
            (
                item
                for item in cache_items
                if isinstance(item, dict) and "birth_time" in item.get("target_fields", [])
            ),
            None,
        )
        if not isinstance(target, dict):
            return {
                "status": "failed",
                "valid": False,
                "probe_executed": False,
                "identity_anchor_birth_time_rejected": False,
                "accepted_cache_count_after_probe": None,
                "probe_source_family_id": "wikidata_identity_anchor",
                "failure_contains_birth_time_policy": False,
                "failures": ["no planned birth_time cache item was available for source-family probe"],
                "boundary": "Probe did not execute because no target cache item was available.",
            }
        cache_path = Path(str(target.get("cache_path", "")))
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "query_id": target.get("query_id"),
                    "case_id": target.get("case_id"),
                    "source_family_id": "wikidata_identity_anchor",
                    "source_name": "identity-only probe source",
                    "source_url": "https://example.test/identity-only",
                    "source_rating": "identity-only",
                    "reviewer_note": "Probe payload: identity anchor must not satisfy birth_time.",
                    "review_status": "source_reviewed",
                    "birth_time": "08:00",
                },
                sort_keys=True,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        after = build_birth_profile_source_cache_audit(
            BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
            cache_dir=cache_dir,
            domain="film",
        )
        present_items = [
            item
            for item in after.get("cache_items", [])
            if isinstance(item, dict) and item.get("cache_status") == "present"
        ]
        present = present_items[0] if present_items else {}
        failures = present.get("failures", []) if isinstance(present, dict) else []
        failure_contains_policy = any(
            "birth_time evidence requires source_family_id=rated_birth_time_source" in str(item)
            for item in failures
        )
        rejected = present.get("source_evidence_acceptable") is False and failure_contains_policy
        return {
            "status": "passed" if rejected else "failed",
            "valid": rejected,
            "probe_executed": True,
            "identity_anchor_birth_time_rejected": rejected,
            "accepted_cache_count_after_probe": after.get("accepted_cache_count"),
            "probe_source_family_id": "wikidata_identity_anchor",
            "failure_contains_birth_time_policy": failure_contains_policy,
            "failures": [] if rejected else [str(item) for item in failures],
            "boundary": "Probe uses a temporary cache directory and does not write repository cache files.",
        }


def _cross_domain_birth_profile_substantive_evidence_cache_enforcement_probe() -> dict[str, Any]:
    """Probe that reviewed source metadata cannot satisfy birth-profile evidence by itself."""
    with tempfile.TemporaryDirectory(prefix="birth_profile_substantive_evidence_probe_") as temp_dir:
        cache_dir = Path(temp_dir) / "birth_profile_source_cache"
        before = build_birth_profile_source_cache_audit(
            BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
            cache_dir=cache_dir,
            domain="film",
        )
        cache_items = before.get("cache_items", []) if isinstance(before.get("cache_items"), list) else []
        target = next(
            (
                item
                for item in cache_items
                if isinstance(item, dict) and "birth_time" in item.get("target_fields", [])
            ),
            None,
        )
        if not isinstance(target, dict):
            return {
                "status": "failed",
                "valid": False,
                "probe_executed": False,
                "metadata_only_reviewed_cache_rejected": False,
                "accepted_cache_count_after_probe": None,
                "probe_source_family_id": "rated_birth_time_source",
                "failure_contains_substantive_birth_policy": False,
                "failures": ["no planned birth_time cache item was available for substantive-evidence probe"],
                "boundary": "Probe did not execute because no target cache item was available.",
            }
        cache_path = Path(str(target.get("cache_path", "")))
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "query_id": target.get("query_id"),
                    "case_id": target.get("case_id"),
                    "source_family_id": "rated_birth_time_source",
                    "source_name": "metadata-only probe source",
                    "source_url": "https://example.test/metadata-only",
                    "source_rating": "reviewed-metadata-only",
                    "reviewer_note": "Probe payload: source metadata alone must not satisfy birth evidence.",
                    "review_status": "source_reviewed",
                },
                sort_keys=True,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        after = build_birth_profile_source_cache_audit(
            BIRTH_PROFILE_REVIEW_MANIFEST_EXAMPLE,
            cache_dir=cache_dir,
            domain="film",
        )
        present_items = [
            item
            for item in after.get("cache_items", [])
            if isinstance(item, dict) and item.get("cache_status") == "present"
        ]
        present = present_items[0] if present_items else {}
        failures = present.get("failures", []) if isinstance(present, dict) else []
        failure_contains_policy = any(
            "reviewed payload does not fill any substantive birth field" in str(item)
            for item in failures
        )
        rejected = present.get("source_evidence_acceptable") is False and failure_contains_policy
        return {
            "status": "passed" if rejected else "failed",
            "valid": rejected,
            "probe_executed": True,
            "metadata_only_reviewed_cache_rejected": rejected,
            "accepted_cache_count_after_probe": after.get("accepted_cache_count"),
            "probe_source_family_id": "rated_birth_time_source",
            "failure_contains_substantive_birth_policy": failure_contains_policy,
            "failures": [] if rejected else [str(item) for item in failures],
            "boundary": "Probe uses a temporary cache directory and does not write repository cache files.",
        }


def _cross_domain_birth_profile_reviewed_manifest_draft_preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
    """Summarize non-mutating reviewed-manifest draft preview state."""
    if not isinstance(preview, dict) or not preview:
        return {
            "status": "blocked_missing_reviewed_manifest_draft_preview",
            "valid": False,
            "would_write_review_manifest": False,
            "would_import_profiles": False,
            "draft_ready_for_human_approval": False,
            "review_request_count": 0,
            "complete_review_request_count": 0,
            "incomplete_review_request_count": 0,
            "draft_gate_passed": False,
            "blocking_reasons": ["birth profile reviewed manifest draft preview is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile reviewed manifest draft preview was available.",
        }
    gate = preview.get("draft_gate", {}) if isinstance(preview.get("draft_gate"), dict) else {}
    integrity = preview.get("integrity_check", {}) if isinstance(preview.get("integrity_check"), dict) else {}
    return {
        "status": preview.get("status"),
        "valid": preview.get("valid") is True,
        "would_write_review_manifest": preview.get("would_write_review_manifest") is True,
        "would_import_profiles": preview.get("would_import_profiles") is True,
        "draft_ready_for_human_approval": preview.get("draft_ready_for_human_approval") is True,
        "review_request_count": preview.get("review_request_count", 0),
        "complete_review_request_count": preview.get("complete_review_request_count", 0),
        "incomplete_review_request_count": preview.get("incomplete_review_request_count", 0),
        "draft_gate_passed": gate.get("passed") is True,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": preview.get("boundary", ""),
    }


def _cross_domain_birth_profile_reviewed_manifest_file_preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
    """Summarize the final non-mutating reviewed-manifest file-write preview."""
    if not isinstance(preview, dict) or not preview:
        return {
            "status": "blocked_missing_reviewed_manifest_file_preview",
            "valid": False,
            "would_write_file": False,
            "would_import_profiles": False,
            "write_ready_for_human_approval": False,
            "target_file": "",
            "target_file_sha256": None,
            "file_preview_gate_passed": False,
            "blocking_reasons": ["birth profile reviewed manifest file preview is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile reviewed manifest file preview was available.",
        }
    gate = preview.get("file_preview_gate", {}) if isinstance(preview.get("file_preview_gate"), dict) else {}
    integrity = preview.get("integrity_check", {}) if isinstance(preview.get("integrity_check"), dict) else {}
    return {
        "status": preview.get("status"),
        "valid": preview.get("valid") is True,
        "would_write_file": preview.get("would_write_file") is True,
        "would_import_profiles": preview.get("would_import_profiles") is True,
        "write_ready_for_human_approval": preview.get("write_ready_for_human_approval") is True,
        "target_file": preview.get("target_file", ""),
        "target_file_sha256": preview.get("target_file_sha256"),
        "file_preview_gate_passed": gate.get("passed") is True,
        "blocking_reasons": gate.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": preview.get("boundary", ""),
    }


def _cross_domain_birth_profile_import_preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
    """Summarize the non-mutating birth-profile import preview for audit portability."""
    if not isinstance(preview, dict) or not preview:
        return {
            "status": "blocked_missing_preview",
            "valid": False,
            "would_write_file": False,
            "import_allowed": False,
            "request_count": 0,
            "blocked_request_count": 0,
            "import_ready_request_count": 0,
            "import_gate_passed": False,
            "blocking_reasons": ["birth profile import preview is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile import preview was available.",
        }
    gate = preview.get("import_gate", {}) if isinstance(preview.get("import_gate"), dict) else {}
    integrity = preview.get("integrity_check", {}) if isinstance(preview.get("integrity_check"), dict) else {}
    return {
        "status": preview.get("status"),
        "valid": preview.get("valid") is True,
        "would_write_file": preview.get("would_write_file") is True,
        "import_allowed": preview.get("import_allowed") is True,
        "request_count": preview.get("request_count", 0),
        "blocked_request_count": preview.get("blocked_request_count", 0),
        "import_ready_request_count": preview.get("import_ready_request_count", 0),
        "import_gate_passed": gate.get("passed") is True,
        "blocking_reasons": preview.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": preview.get("boundary", ""),
    }


def _cross_domain_birth_profile_fixture_patch_preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
    """Summarize the non-mutating fixture patch preview for audit portability."""
    if not isinstance(preview, dict) or not preview:
        return {
            "status": "blocked_missing_patch_preview",
            "valid": False,
            "would_write_file": False,
            "patch_ready_for_review": False,
            "candidate_count": 0,
            "candidate_case_ids": [],
            "patch_gate_passed": False,
            "target_file_sha256": None,
            "patch_text_sha256": None,
            "blocking_reasons": ["birth profile fixture patch preview is missing"],
            "integrity_check_status": "missing",
            "boundary": "No birth-profile fixture patch preview was available.",
        }
    gate = preview.get("patch_gate", {}) if isinstance(preview.get("patch_gate"), dict) else {}
    integrity = preview.get("integrity_check", {}) if isinstance(preview.get("integrity_check"), dict) else {}
    return {
        "status": preview.get("status"),
        "valid": preview.get("valid") is True,
        "would_write_file": preview.get("would_write_file") is True,
        "patch_ready_for_review": preview.get("patch_ready_for_review") is True,
        "candidate_count": preview.get("candidate_count", 0),
        "candidate_case_ids": preview.get("candidate_case_ids", []),
        "patch_gate_passed": gate.get("passed") is True,
        "target_file_sha256": preview.get("target_file_sha256"),
        "patch_text_sha256": preview.get("patch_text_sha256"),
        "blocking_reasons": preview.get("blocking_reasons", []),
        "integrity_check_status": integrity.get("status"),
        "boundary": preview.get("boundary", ""),
    }


def _capability_audit_receipt_material(response: dict[str, Any]) -> dict[str, Any]:
    evidence = response["evidence_materialization"]
    plan = response["plan_compliance"]
    protocol_governance = response["provider_protocol_governance"]
    reference_charts = response["reference_chart_checks"]
    method_surface = response["method_surface"]
    method_lineage = response["method_lineage"]
    famous_cases = response["famous_case_validation"]
    famous_case_calibration = response["famous_case_school_calibration"]
    famous_case_annual = response["famous_case_annual_event_calibration"]
    industry_event_manifest = response.get("industry_event_source_manifest_example", {})
    industry_event_query_plan = response.get("industry_event_source_query_plan_example", {})
    industry_event_candidate_cases = response.get("industry_event_candidate_cases_example", {})
    industry_event_cross_domain_fixture_import = response.get("industry_event_cross_domain_fixture_import", {})
    classical_index = response["classical_text_index"]
    classical_source_refresh = response["classical_source_refresh"]
    source_audits = classical_source_refresh.get("source_audits", [])
    if not isinstance(source_audits, list):
        source_audits = []
    empirical_validation = response["empirical_validation"]
    outcome_dataset = response["outcome_dataset"]
    provider_onboarding = response["provider_onboarding"]
    provider_guidance = response.get("provider_checks", {}).get("production_guidance", {})
    if not isinstance(provider_guidance, dict):
        provider_guidance = {}
    request_contract = response["request_scoped_provider_contract"]
    github_matrix = response["github_comparison_matrix"]
    known_gap_resolution_plan = response["known_gap_resolution_plan"]
    return {
        "schema_version": "capability-audit-receipt-v1",
        "status": response["status"],
        "is_state_of_the_art": response["is_state_of_the_art"],
        "state_of_art": response["state_of_art"],
        "github_comparison_receipt_sha256": response.get("github_comparison_receipt", {}).get("sha256")
        if isinstance(response.get("github_comparison_receipt"), dict)
        else None,
        "plan_compliance_receipt_sha256": response.get("plan_compliance_receipt", {}).get("sha256")
        if isinstance(response.get("plan_compliance_receipt"), dict)
        else None,
        "capabilities": dict(sorted(response["capabilities"].items())),
        "blocked_capability_coverage": response.get("blocked_capability_coverage", {}),
        "known_gap_handoff_bundle": response.get("known_gap_handoff_bundle", {}),
        "request_scoped_provider_contract": {
            "status": request_contract.get("status"),
            "checked_domains": request_contract.get("checked_domains", []),
            "provenance_checked_domains": request_contract.get("provenance_checked_domains", []),
            "requires_provenance_fields": request_contract.get("requires_provenance_fields", []),
            "meaning": request_contract.get("meaning", ""),
        },
        "provider_protocol_governance": {
            "status": protocol_governance.get("status"),
            "protocol_version": protocol_governance.get("protocol_version"),
            "protocol_hash": protocol_governance.get("protocol_hash"),
            "protocol_receipt_sha256": protocol_governance.get("protocol_receipt_sha256"),
            "protocol_document_sha256": protocol_governance.get("protocol_document_sha256"),
            "domain_count": protocol_governance.get("domain_count"),
            "domains": protocol_governance.get("domains", []),
            "domain_protocol_hashes": protocol_governance.get("domain_protocol_hashes", {}),
            "sample_stdout_contracts_valid": protocol_governance.get("sample_stdout_contracts_valid"),
            "runtime_identity_handshake": protocol_governance.get("runtime_identity_handshake", {}),
            "production_gate": protocol_governance.get("production_gate"),
            "receipt_material_fields": protocol_governance.get("receipt_material_fields", []),
        },
        "reference_chart_checks": {
            "passed": reference_charts.get("passed"),
            "total": reference_charts.get("total"),
            "method_coverage": reference_charts.get("method_coverage", {}),
        },
        "method_surface": {
            "schema_version": method_surface.get("schema_version"),
            "sha256": method_surface.get("sha256"),
            "domains": method_surface.get("material", {}).get("domains", {})
            if isinstance(method_surface.get("material"), dict)
            else {},
        },
        "method_lineage": {
            "schema_version": method_lineage.get("schema_version"),
            "sha256": method_lineage.get("sha256"),
            "record_count": method_lineage.get("record_count"),
            "traditions": method_lineage.get("traditions", []),
            "implemented_statuses": method_lineage.get("implemented_statuses", []),
        },
        "famous_case_validation": {
            "schema_version": famous_cases.get("schema_version"),
            "sha256": famous_cases.get("sha256"),
            "case_count": famous_cases.get("case_count"),
            "domains": famous_cases.get("domains", []),
            "ratings": famous_cases.get("ratings", []),
            "sources": famous_cases.get("sources", []),
            "domain_coverage": famous_cases.get("domain_coverage", []),
            "material": famous_cases.get("material", {}),
        },
        "famous_case_school_calibration": {
            "schema_version": famous_case_calibration.get("schema_version"),
            "sha256": famous_case_calibration.get("sha256"),
            "fixture_sha256": famous_case_calibration.get("fixture_sha256"),
            "case_count": famous_case_calibration.get("case_count"),
            "mean_topic_recall": famous_case_calibration.get("mean_topic_recall"),
            "low_coverage_cases": famous_case_calibration.get("low_coverage_cases", []),
            "school_summary": famous_case_calibration.get("school_summary", []),
            "domain_summary": famous_case_calibration.get("domain_summary", []),
            "boundary": famous_case_calibration.get("boundary"),
        },
        "famous_case_annual_event_calibration": {
            "schema_version": famous_case_annual.get("schema_version"),
            "sha256": famous_case_annual.get("sha256"),
            "fixture_sha256": famous_case_annual.get("fixture_sha256"),
            "case_count": famous_case_annual.get("case_count"),
            "event_count": famous_case_annual.get("event_count"),
            "negative_year_count": famous_case_annual.get("negative_year_count"),
            "false_positive_count": famous_case_annual.get("false_positive_count"),
            "strict_exact_hit_count": famous_case_annual.get("strict_exact_hit_count"),
            "strict_false_positive_count": famous_case_annual.get("strict_false_positive_count"),
            "exact_hit_rate": famous_case_annual.get("exact_hit_rate"),
            "window_hit_rate": famous_case_annual.get("window_hit_rate"),
            "exact_precision": famous_case_annual.get("exact_precision"),
            "false_positive_rate": famous_case_annual.get("false_positive_rate"),
            "strict_exact_hit_rate": famous_case_annual.get("strict_exact_hit_rate"),
            "strict_exact_precision": famous_case_annual.get("strict_exact_precision"),
            "strict_false_positive_rate": famous_case_annual.get("strict_false_positive_rate"),
            "low_coverage_cases": famous_case_annual.get("low_coverage_cases", []),
            "birth_source_quality_summary": famous_case_annual.get("birth_source_quality_summary", {}),
            "source_review_routing_summary": famous_case_annual.get("source_review_routing_summary", {}),
            "domain_summary": famous_case_annual.get("domain_summary", []),
            "domain_topic_summary": famous_case_annual.get("domain_topic_summary", []),
            "domain_topic_refinement_queue": famous_case_annual.get("domain_topic_refinement_queue", []),
            "domain_topic_variant_sweep": famous_case_annual.get("domain_topic_variant_sweep", []),
            "topic_summary": famous_case_annual.get("topic_summary", []),
            "industry_event_evidence_summary": famous_case_annual.get("industry_event_evidence_summary", []),
            "industry_event_source_coverage": famous_case_annual.get("industry_event_source_coverage", {}),
            "event_subtype_summary": famous_case_annual.get("event_subtype_summary", []),
            "rule_variant_sweep": famous_case_annual.get("rule_variant_sweep", []),
            "rule_refinement_queue": famous_case_annual.get("rule_refinement_queue", []),
            "evolution_task_plan": famous_case_annual.get("evolution_task_plan", []),
            "boundary": famous_case_annual.get("boundary"),
        },
        "industry_event_source_manifest_example": {
            "schema_version": industry_event_manifest.get("schema_version"),
            "sha256": industry_event_manifest.get("sha256"),
            "status": industry_event_manifest.get("material", {}).get("status")
            if isinstance(industry_event_manifest.get("material"), dict)
            else None,
            "path": industry_event_manifest.get("material", {}).get("path")
            if isinstance(industry_event_manifest.get("material"), dict)
            else None,
            "content_hash": industry_event_manifest.get("material", {}).get("content_hash")
            if isinstance(industry_event_manifest.get("material"), dict)
            else None,
            "record_count": industry_event_manifest.get("material", {}).get("record_count")
            if isinstance(industry_event_manifest.get("material"), dict)
            else None,
            "positive_event_count": industry_event_manifest.get("material", {}).get("positive_event_count")
            if isinstance(industry_event_manifest.get("material"), dict)
            else None,
            "negative_event_count": industry_event_manifest.get("material", {}).get("negative_event_count")
            if isinstance(industry_event_manifest.get("material"), dict)
            else None,
            "domains": industry_event_manifest.get("material", {}).get("domains", [])
            if isinstance(industry_event_manifest.get("material"), dict)
            else [],
            "candidate_source_names": industry_event_manifest.get("material", {}).get("candidate_source_names", [])
            if isinstance(industry_event_manifest.get("material"), dict)
            else [],
            "production_evidence": industry_event_manifest.get("material", {}).get("production_evidence")
            if isinstance(industry_event_manifest.get("material"), dict)
            else False,
            "externally_reviewed": industry_event_manifest.get("material", {}).get("externally_reviewed")
            if isinstance(industry_event_manifest.get("material"), dict)
            else False,
        },
        "industry_event_source_query_plan_example": {
            "schema_version": industry_event_query_plan.get("schema_version"),
            "sha256": industry_event_query_plan.get("sha256"),
            "status": industry_event_query_plan.get("material", {}).get("status")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else None,
            "path": industry_event_query_plan.get("material", {}).get("path")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else None,
            "content_hash": industry_event_query_plan.get("material", {}).get("content_hash")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else None,
            "source_id": industry_event_query_plan.get("material", {}).get("source_id")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else None,
            "endpoint_url": industry_event_query_plan.get("material", {}).get("endpoint_url")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else None,
            "template_count": industry_event_query_plan.get("material", {}).get("template_count")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else None,
            "domains": industry_event_query_plan.get("material", {}).get("domains", [])
            if isinstance(industry_event_query_plan.get("material"), dict)
            else [],
            "required_manifest_fields_mapped": industry_event_query_plan.get("material", {}).get(
                "required_manifest_fields_mapped"
            )
            if isinstance(industry_event_query_plan.get("material"), dict)
            else False,
            "collection_ready": industry_event_query_plan.get("material", {}).get("collection_ready")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else False,
            "externally_reviewed": industry_event_query_plan.get("material", {}).get("externally_reviewed")
            if isinstance(industry_event_query_plan.get("material"), dict)
            else False,
        },
        "industry_event_candidate_cases_example": {
            "schema_version": industry_event_candidate_cases.get("schema_version"),
            "sha256": industry_event_candidate_cases.get("sha256"),
            "status": industry_event_candidate_cases.get("material", {}).get("status")
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else None,
            "path": industry_event_candidate_cases.get("material", {}).get("path")
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else None,
            "content_hash": industry_event_candidate_cases.get("material", {}).get("content_hash")
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else None,
            "candidate_count": industry_event_candidate_cases.get("material", {}).get("candidate_count")
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else None,
            "domain_counts": industry_event_candidate_cases.get("material", {}).get("domain_counts", {})
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else {},
            "domains": industry_event_candidate_cases.get("material", {}).get("domains", [])
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else [],
            "split_roles": industry_event_candidate_cases.get("material", {}).get("split_roles", [])
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else [],
            "production_ready": industry_event_candidate_cases.get("material", {}).get("production_ready")
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else False,
            "externally_reviewed": industry_event_candidate_cases.get("material", {}).get("externally_reviewed")
            if isinstance(industry_event_candidate_cases.get("material"), dict)
            else False,
        },
        "industry_event_cross_domain_fixture_import": industry_event_cross_domain_fixture_import,
        "classical_text_index": {
            "status": classical_index.get("status"),
            "record_count": classical_index.get("record_count"),
            "content_hash": classical_index.get("content_hash"),
        },
        "classical_source_refresh": {
            "status": classical_source_refresh.get("status"),
            "source_count": classical_source_refresh.get("source_count"),
            "locked_source_count": classical_source_refresh.get("locked_source_count"),
            "source_audit_count": len(source_audits),
            "refreshable_source_count": sum(
                1 for item in source_audits if isinstance(item, dict) and item.get("refreshable") is True
            ),
            "content_hash": classical_source_refresh.get("content_hash"),
            "source_list_receipt_sha256": classical_source_refresh.get("source_list_receipt", {}).get("sha256")
            if isinstance(classical_source_refresh.get("source_list_receipt"), dict)
            else None,
            "failures": classical_source_refresh.get("failures", []),
        },
        "empirical_validation": {
            "status": empirical_validation.get("status"),
            "case_count": empirical_validation.get("case_count"),
            "predictive_truth_cases": empirical_validation.get("predictive_truth_cases"),
            "label_types": empirical_validation.get("label_types", []),
        },
        "outcome_dataset": {
            "status": outcome_dataset.get("status"),
            "valid": outcome_dataset.get("valid"),
            "record_count": outcome_dataset.get("record_count"),
            "content_hash": outcome_dataset.get("content_hash"),
            "data_split_record_coverage": outcome_dataset.get("data_split_record_coverage", {}),
            "predictive_optimization_enabled": outcome_dataset.get("predictive_optimization_enabled"),
            "external_review": outcome_dataset.get("external_review", {}),
            "data_split": outcome_dataset.get("data_split", {}),
            "label_collection": outcome_dataset.get("label_collection", {}),
            "statistical_plan": outcome_dataset.get("statistical_plan", {}),
            "label_provenance": outcome_dataset.get("label_provenance", {}),
            "governance_gate_ids": sorted(
                (outcome_dataset.get("governance_gates", {}).get("gates") or {}).keys()
            )
            if isinstance(outcome_dataset.get("governance_gates"), dict)
            else [],
        },
        "provider_onboarding": {
            "status": provider_onboarding.get("status"),
            "receipt_sha256": provider_onboarding.get("provider_onboarding_receipt", {}).get("sha256")
            if isinstance(provider_onboarding.get("provider_onboarding_receipt"), dict)
            else None,
            "domain_count": provider_onboarding.get("provider_onboarding_receipt", {})
            .get("material", {})
            .get("domain_count")
            if isinstance(provider_onboarding.get("provider_onboarding_receipt"), dict)
            else None,
            "ready_domain_count": provider_onboarding.get("provider_onboarding_receipt", {})
            .get("material", {})
            .get("ready_domain_count")
            if isinstance(provider_onboarding.get("provider_onboarding_receipt"), dict)
            else None,
            "example_provider_receipt_sha256": provider_onboarding.get("example_provider_receipt", {}).get("sha256")
            if isinstance(provider_onboarding.get("example_provider_receipt"), dict)
            else None,
            "domain_missing_evidence": {
                domain: sorted(item.get("missing_evidence", []))
                for domain, item in sorted(provider_onboarding.get("domains", {}).items())
                if isinstance(item, dict)
            }
            if isinstance(provider_onboarding.get("domains"), dict)
            else {},
            "missing_evidence_counts": provider_onboarding.get("provider_onboarding_receipt", {})
            .get("material", {})
            .get("missing_evidence_counts", {})
            if isinstance(provider_onboarding.get("provider_onboarding_receipt"), dict)
            else {},
        },
        "provider_production_guidance": {
            "production_ready": provider_guidance.get("production_ready"),
            "blocked_targets": provider_guidance.get("blocked_targets", []),
            "required_env_vars": provider_guidance.get("required_env_vars", []),
            "required_provenance_env_vars": provider_guidance.get("required_provenance_env_vars", []),
            "certification_commands": provider_guidance.get("certification_commands", []),
            "drift_commands": provider_guidance.get("drift_commands", []),
            "deployment_checklist": provider_guidance.get("deployment_checklist", []),
            "next_actions": provider_guidance.get("next_actions", []),
            "provider_onboarding_command": provider_guidance.get("provider_onboarding_command", ""),
            "provider_ledger_command": provider_guidance.get("provider_ledger_command", ""),
            "production_readiness_command": provider_guidance.get("production_readiness_command", ""),
            "smoke_command": provider_guidance.get("smoke_command", ""),
            "policy": provider_guidance.get("policy", ""),
        },
        "plan_compliance": {
            "source": plan.get("source"),
            "source_receipt": plan.get("source_receipt", {}),
            "section_count": plan.get("section_count"),
            "implemented_count": plan.get("implemented_count"),
            "sections_with_gaps": plan.get("sections_with_gaps", []),
            "section_gap_resolution_coverage": plan.get("section_gap_resolution_coverage", {}),
            "matrix": [
                {
                    "section": item.get("section"),
                    "status": item.get("status"),
                    "implemented": item.get("implemented", []),
                    "gap_ids": item.get("gap_ids", []),
                    "implemented_verified": item.get("implemented_verified"),
                    "gap_ids_verified": item.get("gap_ids_verified"),
                }
                for item in plan.get("matrix", [])
            ],
        },
        "evidence_materialization": {
            "status": evidence.get("status"),
            "total_evidence": evidence.get("total_evidence"),
            "passed_count": evidence.get("passed_count"),
            "failed_count": evidence.get("failed_count"),
            "unchecked_count": evidence.get("unchecked_count"),
        },
        "implemented_requirement_ids": sorted(item["id"] for item in response["implemented_requirements"]),
        "known_gap_ids": sorted(item["id"] for item in response["known_gaps"]),
        "known_gap_resolution_plan_hash": _stable_json_sha256(known_gap_resolution_plan),
        "known_gap_resolution_plan_coverage": response.get("known_gap_resolution_plan_coverage", {}),
        "known_gap_resolution_plan": [
            {
                "id": item.get("id") or item.get("gap_id"),
                "gap_id": item.get("gap_id"),
                "status": item.get("status"),
                "owner_domain": item.get("owner_domain"),
                "production_gate_ids": item.get("production_gate_ids", []),
                "blocking_scope": item.get("blocking_scope"),
                "verification_command_count": len(item.get("verification_commands", [])),
            }
            for item in known_gap_resolution_plan
        ],
        "github_comparison_matrix": [
            {
                "dimension": item.get("dimension"),
                "relative_position": item.get("relative_position"),
                "github_baseline": item.get("github_baseline"),
            }
            for item in github_matrix
        ],
        "external_integration_candidates": [
            {"name": item.get("name"), "domain": item.get("domain")}
            for item in response["external_integration_candidates"]
        ],
    }


def _capability_audit_receipt(response: dict[str, Any]) -> dict[str, Any]:
    material = _capability_audit_receipt_material(response)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def capability_audit(
    repo_path: Path | None = None,
    *,
    classical_source_list_path: Path | None = None,
) -> dict[str, Any]:
    """Return a machine-readable audit of implementation coverage and known gaps."""
    calendar = describe_calendar_providers()
    domain_providers = describe_domain_chart_providers()
    reference_charts = run_reference_chart_checks()
    method_surface = method_surface_receipt()
    method_lineage = method_lineage_receipt()
    famous_cases = famous_case_receipt()
    famous_case_calibration = famous_case_school_calibration_receipt()
    famous_case_annual = famous_case_annual_event_calibration_receipt()
    industry_event_manifest = _industry_event_source_manifest_example_receipt()
    industry_event_query_plan = _industry_event_source_query_plan_example_receipt()
    industry_event_candidate_cases = _industry_event_candidate_cases_example_receipt()
    industry_event_cross_domain_fixture_import = _industry_event_cross_domain_fixture_import_receipt()
    classical_index = classical_index_audit()
    resolved_classical_source_list_path = _default_classical_source_list_path(classical_source_list_path)
    classical_source_refresh = source_list_audit(resolved_classical_source_list_path)
    empirical_cases = empirical_validation_cases()
    outcome_manifest = os.getenv("SEMAS_OUTCOME_DATASET_MANIFEST")
    outcome_audit = outcome_dataset_audit(Path(outcome_manifest)) if outcome_manifest else outcome_dataset_audit()
    providers = provider_health_checks(repo_path)
    provider_example_smoke = bundled_provider_example_smoke(repo_path)
    try:
        from examples.mingli_5agents.api_core import provider_onboarding as build_provider_onboarding

        provider_onboarding = build_provider_onboarding(repo_path or Path(".semas_mingli_repo"))
    except Exception as exc:  # pragma: no cover - defensive audit boundary
        provider_onboarding = {
            "status": "unavailable",
            "domains": {},
            "example_provider_receipt": provider_example_smoke.get("example_provider_receipt", {}),
            "provider_onboarding_receipt": None,
            "failures": [str(exc)],
        }
    provider_protocols = provider_protocol_document()
    provider_protocols_receipt = provider_protocol_receipt(
        provider_protocols,
        repo=str(repo_path or Path(".semas_mingli_repo")),
    )
    llm_status = llm_backend_status()
    professional_bazi = bool(calendar.get("professional_available"))
    professional_ziwei = bool(domain_providers.get("ziwei", {}).get("installed_professional_backend"))
    professional_qimen = bool(domain_providers.get("qimen", {}).get("installed_professional_backend"))
    ephemeris_astrology = bool(domain_providers.get("astrology", {}).get("installed_professional_backend"))
    external_contract_domains = _external_structured_contract_domains(reference_charts)
    external_provenance_domains = _external_structured_provenance_domains(reference_charts)
    plan_source_receipt = _plan_source_receipt()
    memory_safety = _feedback_memory_safety_audit(repo_path)
    evidence_materialization = _implemented_evidence_materialization_audit()
    known_gaps = _known_gap_items()
    known_gap_resolution_plan = _known_gap_resolution_plan()
    known_gap_resolution_plan_coverage = _known_gap_resolution_plan_coverage(known_gap_resolution_plan)
    plan_matrix = _plan_compliance_matrix()
    section_gap_resolution_coverage = _section_gap_resolution_coverage(plan_matrix, known_gap_resolution_plan)
    protocol_domains = provider_protocols.get("domains", {})
    protocol_governance = {
        "status": "ready" if _provider_protocol_governance_ready(provider_protocols) else "incomplete",
        "protocol_version": provider_protocols.get("protocol_version"),
        "protocol_hash": provider_protocols.get("protocol_hash"),
        "protocol_receipt_sha256": provider_protocols_receipt.get("sha256"),
        "protocol_document_sha256": provider_protocols_receipt.get("material", {}).get("protocol_document_sha256")
        if isinstance(provider_protocols_receipt.get("material"), dict)
        else None,
        "domain_count": len(protocol_domains) if isinstance(protocol_domains, dict) else 0,
        "domains": sorted(protocol_domains) if isinstance(protocol_domains, dict) else [],
        "domain_protocol_hashes": {
            domain: protocol.get("protocol_hash")
            for domain, protocol in sorted(protocol_domains.items())
            if isinstance(protocol, dict)
        }
        if isinstance(protocol_domains, dict)
        else {},
        "sample_stdout_contracts_valid": all(
            isinstance(protocol, dict)
            and protocol.get("sample_stdout_contract", {}).get("valid") is True
            and isinstance(protocol.get("protocol_hash"), str)
            and len(protocol.get("protocol_hash", "")) == 64
            for protocol in protocol_domains.values()
        )
        if isinstance(protocol_domains, dict) and protocol_domains
        else False,
        "runtime_identity_handshake": _provider_protocol_identity_handshake_summary(provider_protocols),
        "production_gate": "provider_certification_protocols_current",
        "receipt_material_fields": [
            "protocol_version",
            "protocol_hash",
            "protocol_identity_matches",
            "protocol_identity",
            "protocol_failures",
            "provider_request_receipt",
            "reference_contract_coverage",
            "reference_contract_status",
            "reference_contract_covered",
            "stdin_sha256",
            "stdout_sha256",
            "birth_profile_sha256",
        ],
    }
    capabilities = {
        "five_agents": True,
        "discussion_voting": True,
        "source_review": True,
        "local_evidence_retrieval": True,
        "annual_phase_summary": True,
        "semas_orchestrator_evolution": True,
        "population_evolution": True,
        "regression_and_validation_gates": True,
        "archive_hash_chain": True,
        "genome_lineage_integrity": True,
        "version_history_lineage_view": True,
        "audited_rollback": True,
        "reproducibility_manifest_strategy_fingerprints": True,
        "evolution_trigger_receipt": True,
        "release_manifest_evolution_trigger_binding": True,
        "github_comparison_receipt": True,
        "plan_compliance_receipt": True,
        "release_manifest_github_comparison_binding": True,
        "release_manifest_plan_compliance_binding": True,
        "evolution_cost_governance_manifest": True,
        "long_term_feedback_memory": True,
        "feedback_memory_safety_quarantine": True,
        "benchmark_suite": True,
        "reference_chart_contracts": bool(reference_charts.get("passed")),
        "classical_text_index": classical_index.get("status") == "ready",
        "classical_source_refresh_governance": classical_source_refresh.get("status") in {"ready", "unconfigured"},
        "classical_source_governance_metadata": True,
        "classical_source_refresh_receipt": isinstance(classical_source_refresh.get("source_list_receipt"), dict)
        and isinstance(classical_source_refresh.get("source_list_receipt", {}).get("sha256"), str),
        "classical_source_refresh_configured": classical_source_refresh.get("status") == "ready",
        "empirical_validation_harness": True,
        "outcome_dataset_manifest_audit": True,
        "outcome_dataset_external_review_gate": True,
        "outcome_dataset_frozen_holdout_gate": True,
        "outcome_dataset_data_split_records_covered": True,
        "outcome_dataset_data_split_record_coverage_gate": True,
        "outcome_dataset_label_collection_pre_analysis_gate": True,
        "outcome_dataset_statistical_plan_preregistration_gate": True,
        "outcome_dataset_record_label_provenance_gate": True,
        "outcome_dataset_cli_api_audit": True,
        "annual_timeline_receipt": True,
        "annual_timeline_topic_evidence_binding": True,
        "bazi_core_profile_schema_contract": True,
        "bazi_school_debate": True,
        "famous_case_validation_receipt": isinstance(famous_cases.get("sha256"), str)
        and len(famous_cases.get("sha256", "")) == 64
        and int(famous_cases.get("case_count", 0)) >= 12,
        "famous_case_school_calibration_receipt": isinstance(famous_case_calibration.get("sha256"), str)
        and len(famous_case_calibration.get("sha256", "")) == 64
        and famous_case_calibration.get("fixture_sha256") == famous_cases.get("sha256")
        and int(famous_case_calibration.get("case_count", 0)) >= 12,
        "famous_case_annual_event_calibration_receipt": isinstance(famous_case_annual.get("sha256"), str)
        and len(famous_case_annual.get("sha256", "")) == 64
        and famous_case_annual.get("fixture_sha256") == famous_cases.get("sha256")
        and int(famous_case_annual.get("case_count", 0)) >= 12
        and int(famous_case_annual.get("event_count", 0)) > 0,
        "famous_case_source_review_routing_complete": _famous_case_source_review_routing_complete(
            famous_case_annual
        ),
        "famous_case_source_review_queue_aligned": _famous_case_source_review_queue_aligned(
            famous_case_annual
        ),
        "industry_event_source_manifest_example": isinstance(industry_event_manifest.get("sha256"), str)
        and len(industry_event_manifest.get("sha256", "")) == 64
        and industry_event_manifest.get("material", {}).get("status") == "ready_example",
        "industry_event_source_query_plan_example": isinstance(industry_event_query_plan.get("sha256"), str)
        and len(industry_event_query_plan.get("sha256", "")) == 64
        and industry_event_query_plan.get("material", {}).get("status") == "ready_example",
        "industry_event_candidate_cases_example": isinstance(industry_event_candidate_cases.get("sha256"), str)
        and len(industry_event_candidate_cases.get("sha256", "")) == 64
        and industry_event_candidate_cases.get("material", {}).get("status") == "ready_example"
        and industry_event_candidate_cases.get("material", {}).get("domain_counts") == {
            "film": 3,
            "music": 3,
            "sports": 3,
        },
        "industry_event_cross_domain_fixture_import": isinstance(
            industry_event_cross_domain_fixture_import.get("sha256"), str
        )
        and len(industry_event_cross_domain_fixture_import.get("sha256", "")) == 64
        and industry_event_cross_domain_fixture_import.get("material", {}).get("status") == "ready_example"
        and industry_event_cross_domain_fixture_import.get("material", {}).get("candidate_count") == 9
        and industry_event_cross_domain_fixture_import.get("material", {}).get("positive_record_count") == 9
        and int(industry_event_cross_domain_fixture_import.get("material", {}).get("negative_record_count", 0)) > 0
        and industry_event_cross_domain_fixture_import.get("material", {}).get("cross_domain_coverage_gate_passed")
        is True,
        "method_lineage_receipt": isinstance(method_lineage.get("sha256"), str)
        and len(method_lineage.get("sha256", "")) == 64,
        "monthly_luck_receipt": True,
        "monthly_luck_topic_evidence_binding": True,
        "monthly_luck_public_schema_contract": True,
        "astrology_profile_public_schema_contract": True,
        "astrology_ephemeris_audit_contract": True,
        "xuanze_rule_table_audit_contract": True,
        "ziwei_qimen_public_schema_contract": True,
        "ziwei_qimen_calculation_basis_audit_contract": True,
        "rendered_reports_public_schema_contract": True,
        "final_report_runtime_metadata_schema_contract": True,
        "source_review_public_schema_contract": True,
        "final_report_metadata_schema_contract": True,
        "analyze_response_runtime_schema_validation": True,
        "production_readiness_schema_validation_gate": True,
        "auspicious_calendar_receipt": True,
        "production_readiness_gate": True,
        "birthplace_geocoding_provenance": True,
        "birthplace_geocoding_production_gate": True,
        "provider_certification_cli_api": True,
        "provider_protocol_hash_governance": protocol_governance["status"] == "ready",
        "provider_protocol_identity_handshake": protocol_governance["runtime_identity_handshake"].get("ready") is True,
        "provider_raw_contract_receipt": True,
        "provider_ledger_protocol_stale_gate": True,
        "provider_ledger_latest_record_binding": True,
        "provider_certification_reference_contract_coverage": True,
        "provider_ledger_reference_contract_gate": True,
        "provider_certification_command_fingerprint_governance": True,
        "provider_example_protocol_smoke_receipt": isinstance(
            provider_example_smoke.get("example_provider_receipt"), dict
        )
        and isinstance(provider_example_smoke.get("example_provider_receipt", {}).get("sha256"), str),
        "provider_onboarding_receipt": isinstance(provider_onboarding.get("provider_onboarding_receipt"), dict)
        and isinstance(provider_onboarding.get("provider_onboarding_receipt", {}).get("sha256"), str),
        "provider_production_guidance": _provider_production_guidance_ready(providers.get("production_guidance")),
        "release_manifest_governance": True,
        "release_manifest_ledger_hash_chain": True,
        "release_manifest_ledger_latest_record_binding": True,
        "release_manifest_ledger_receipt_material_binding": True,
        "release_manifest_external_payload_birth_match_coverage": True,
        "release_manifest_provider_action_plan_coverage": True,
        "release_manifest_classical_source_receipt_coverage": True,
        "release_manifest_readiness_gate_binding": True,
        "known_gap_resolution_plan": len(known_gap_resolution_plan) == len(KNOWN_GAPS)
        and {item["gap_id"] for item in known_gap_resolution_plan} == {item["id"] for item in KNOWN_GAPS}
        and all(item.get("verification_commands") and item.get("production_gate_ids") for item in known_gap_resolution_plan)
        and _known_gap_resolution_plan_gate_ids_valid(known_gap_resolution_plan),
        "known_gap_resolution_plan_coverage_audit": known_gap_resolution_plan_coverage["coverage_complete"],
        "known_gap_verification_command_coverage": known_gap_resolution_plan_coverage.get(
            "command_validation_complete"
        )
        is True,
        "known_gap_command_coverage_release_binding": True,
        "release_manifest_ledger_readiness_gate": True,
        "release_manifest_drift_gate": True,
        "known_gap_handoff_export_cli_api": True,
        "known_gap_handoff_export_verification": True,
        "known_gap_handoff_implementation_checklist": True,
        "implemented_evidence_materialized": evidence_materialization["failed_count"] == 0,
        "xuanze_huangdao_scaffold": True,
        "cli": True,
        "http_api": True,
        "json_schema_document": True,
        "safety_guardrails": True,
        "professional_bazi_provider_available": professional_bazi,
        "professional_ziwei_provider_available": professional_ziwei,
        "professional_qimen_provider_available": professional_qimen,
        "ephemeris_astrology_provider_available": ephemeris_astrology,
        "external_professional_chart_injection": all(
            item.get("external_injection_supported") for item in domain_providers.values()
        ),
        "request_scoped_full_external_provider_injection": external_contract_domains
        == ["astrology", "bazi", "qimen", "xuanze", "ziwei"],
        "request_scoped_external_provider_provenance": external_provenance_domains
        == ["astrology", "bazi", "qimen", "xuanze", "ziwei"],
        "request_scoped_external_payload_receipts": True,
        "request_scoped_external_payload_birth_match_audit": True,
        "provider_interpretation_readiness_matrix": True,
        "topic_synthesis_confidence_audit": True,
        "topic_synthesis_timing_schema_contract": True,
        "empirical_topic_confidence_gate": True,
        "chinese_markdown_renderer": True,
        "topic_synthesis": True,
        "optional_llm_synthesis": True,
        "llm_backend_configured": bool(llm_status.get("configured")),
    }
    blocked_capability_coverage = _blocked_capability_coverage(capabilities, known_gaps)
    known_gap_handoff_bundle = _known_gap_handoff_bundle(
        known_gaps,
        known_gap_resolution_plan,
        blocked_capability_coverage,
        EXTERNAL_INTEGRATION_CANDIDATES,
    )
    capabilities["blocked_capability_coverage_audit"] = blocked_capability_coverage["coverage_complete"]
    capabilities["blocked_capability_coverage_production_gate"] = True
    capabilities["known_gap_handoff_bundle"] = known_gap_handoff_bundle["status"] == "ready"
    capabilities["known_gap_handoff_bundle_production_gate"] = True
    state_of_art = _state_of_art_summary(capabilities)
    github_comparison_receipt = _github_comparison_receipt(
        state_of_art=state_of_art,
        capabilities=capabilities,
        github_matrix=GITHUB_COMPARISON_MATRIX,
        external_candidates=EXTERNAL_INTEGRATION_CANDIDATES,
    )
    plan_compliance = {
        "source": "plan_mingli5agents.md",
        "source_receipt": plan_source_receipt,
        "section_count": len(plan_matrix),
        "implemented_count": sum(1 for item in plan_matrix if item["status"] == "implemented"),
        "sections_with_gaps": [item["section"] for item in plan_matrix if item.get("gap_ids")],
        "section_gap_resolution_coverage": section_gap_resolution_coverage,
        "matrix": plan_matrix,
    }
    plan_compliance_receipt = _plan_compliance_receipt(plan_compliance)
    response = {
        "status": "operational_with_known_gaps",
        "repo": str(repo_path) if repo_path is not None else None,
        "is_state_of_the_art": "partial",
        "state_of_the_art_assessment": (
            "Advanced for SEMAS-style orchestration, evolution gates, structured reporting, and safety; "
            "not yet state-of-the-art for professional Zi Wei/Qi Men/ephemeris-grade astrology calculation "
            "or empirical predictive validation."
        ),
        "calendar_providers": calendar,
        "domain_chart_providers": domain_providers,
        "source_registry": {
            "count": len(SOURCE_REGISTRY),
            "traditions": sorted({source.tradition for source in SOURCE_REGISTRY.values()}),
        },
        "reference_chart_checks": reference_charts,
        "method_surface": method_surface,
        "method_lineage": method_lineage,
        "famous_case_validation": famous_cases,
        "famous_case_school_calibration": famous_case_calibration,
        "famous_case_annual_event_calibration": famous_case_annual,
        "industry_event_source_manifest_example": industry_event_manifest,
        "industry_event_source_query_plan_example": industry_event_query_plan,
        "industry_event_candidate_cases_example": industry_event_candidate_cases,
        "industry_event_cross_domain_fixture_import": industry_event_cross_domain_fixture_import,
        "request_scoped_provider_contract": {
            "status": "ready"
            if capabilities["request_scoped_full_external_provider_injection"]
            and capabilities["request_scoped_external_provider_provenance"]
            else "incomplete",
            "checked_domains": external_contract_domains,
            "provenance_checked_domains": external_provenance_domains,
            "requires_provenance_fields": ["source", "version", "license_or_review"],
            "meaning": (
                "A caller can supply verified external payloads for every domain in one analysis request; "
                "production readiness also requires source, version, and license_or_review provenance."
            ),
        },
        "classical_text_index": classical_index,
        "classical_source_list_path": str(resolved_classical_source_list_path)
        if resolved_classical_source_list_path
        else None,
        "classical_source_refresh": classical_source_refresh,
        "empirical_validation": {
            "status": "ready_non_predictive",
            "case_count": len(empirical_cases),
            "predictive_truth_cases": sum(1 for case in empirical_cases if case.predictive_truth_label),
            "label_types": sorted({case.label_type for case in empirical_cases}),
        },
        "outcome_dataset": outcome_audit,
        "feedback_memory_safety": memory_safety,
        "provider_checks": providers,
        "provider_example_smoke": provider_example_smoke,
        "provider_onboarding": provider_onboarding,
        "provider_protocol_governance": protocol_governance,
        "llm_backend": llm_status,
        "capabilities": capabilities,
        "blocked_capability_coverage": blocked_capability_coverage,
        "known_gap_handoff_bundle": known_gap_handoff_bundle,
        "state_of_art": state_of_art,
        "github_comparison_matrix": GITHUB_COMPARISON_MATRIX,
        "github_comparison_receipt": github_comparison_receipt,
        "plan_compliance": plan_compliance,
        "plan_compliance_receipt": plan_compliance_receipt,
        "evidence_materialization": evidence_materialization,
        "implemented_requirements": IMPLEMENTED_REQUIREMENTS,
        "known_gaps": known_gaps,
        "known_gap_resolution_plan": known_gap_resolution_plan,
        "known_gap_resolution_plan_coverage": known_gap_resolution_plan_coverage,
        "external_integration_candidates": EXTERNAL_INTEGRATION_CANDIDATES,
        "next_highest_value_steps": [
            "Add a verified Zi Wei provider behind the existing tool schema.",
            "Install kinqimen or configure SEMAS_QIMEN_CLI, then validate Qi Men reference plates.",
            "Install and validate pyswisseph-backed astrology in the target runtime.",
            "Connect a verified tongshu/xuanze provider for professional auspicious-day calculation.",
            "Use request-scoped professional_charts payloads when production engines run outside this Python process.",
            "Configure an externally reviewed outcome dataset manifest before any predictive optimization.",
            "Configure production classical-source allowlists, scheduled manifest refresh jobs, and reviewed public-domain/open-license feeds.",
        ],
    }
    response["audit_receipt"] = _capability_audit_receipt(response)
    return response


def _plan_source_receipt() -> dict[str, Any]:
    plan_path = REPO_ROOT / "plan_mingli5agents.md"
    if not plan_path.exists():
        return {
            "path": "plan_mingli5agents.md",
            "exists": False,
            "readable": False,
            "encoding": "utf-8",
            "byte_count": 0,
            "sha256": "",
            "section_headings": [],
            "section_heading_count": 0,
        }
    raw = plan_path.read_bytes()
    try:
        text = raw.decode("utf-8")
        readable = True
    except UnicodeDecodeError:
        text = ""
        readable = False
    headings = [
        line.strip()
        for line in text.splitlines()
        if line.startswith("## ") and len(line.strip()) > 3
    ]
    return {
        "path": "plan_mingli5agents.md",
        "exists": True,
        "readable": readable,
        "encoding": "utf-8",
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "section_headings": headings,
        "section_heading_count": len(headings),
    }


def _plan_compliance_matrix() -> list[dict[str, Any]]:
    implemented_ids = {item["id"] for item in IMPLEMENTED_REQUIREMENTS}
    known_gap_ids = {item["id"] for item in KNOWN_GAPS}
    matrix = []
    for section in PLAN_COMPLIANCE_SECTIONS:
        implemented = list(section["implemented"])
        gap_ids = list(section["gap_ids"])
        matrix.append(
            {
                **section,
                "implemented_verified": all(item in implemented_ids for item in implemented),
                "gap_ids_verified": all(item in known_gap_ids for item in gap_ids),
            }
        )
    return matrix


def _section_gap_resolution_coverage(
    plan_matrix: list[dict[str, Any]],
    known_gap_resolution_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    plan_by_gap = {_known_gap_plan_item_id(item): item for item in known_gap_resolution_plan if _known_gap_plan_item_id(item)}
    sections = []
    missing_plan_gap_ids: list[str] = []
    invalid_plan_gap_ids: list[str] = []
    invalid_gate_ids_by_gap: dict[str, list[str]] = {}
    for section in plan_matrix:
        gap_ids = [str(item) for item in section.get("gap_ids", [])]
        planned_gap_ids = []
        production_gate_ids: list[str] = []
        verification_command_count = 0
        for gap_id in gap_ids:
            gap_plan = plan_by_gap.get(gap_id)
            if not gap_plan:
                missing_plan_gap_ids.append(gap_id)
                continue
            planned_gap_ids.append(gap_id)
            commands = gap_plan.get("verification_commands", [])
            gates = gap_plan.get("production_gate_ids", [])
            invalid_gate_ids = (
                sorted({str(gate) for gate in gates if str(gate) not in PRODUCTION_READINESS_GATE_IDS})
                if isinstance(gates, list)
                else []
            )
            if invalid_gate_ids:
                invalid_gate_ids_by_gap[gap_id] = invalid_gate_ids
            if not commands or not gates or invalid_gate_ids:
                invalid_plan_gap_ids.append(gap_id)
            verification_command_count += len(commands) if isinstance(commands, list) else 0
            if isinstance(gates, list):
                for gate in gates:
                    gate_id = str(gate)
                    if gate_id not in production_gate_ids:
                        production_gate_ids.append(gate_id)
        sections.append(
            {
                "section": section.get("section"),
                "gap_ids": gap_ids,
                "planned_gap_ids": planned_gap_ids,
                "gap_count": len(gap_ids),
                "planned_gap_count": len(planned_gap_ids),
                "all_gaps_planned": len(planned_gap_ids) == len(gap_ids),
                "verification_command_count": verification_command_count,
                "production_gate_ids": sorted(production_gate_ids),
            }
        )
    missing = sorted(set(missing_plan_gap_ids))
    invalid = sorted(set(invalid_plan_gap_ids))
    sections_with_unplanned_gaps = [
        item["section"]
        for item in sections
        if item["gap_count"] > item["planned_gap_count"] or any(gap_id in invalid for gap_id in item["gap_ids"])
    ]
    return {
        "status": "covered" if not missing and not invalid else "incomplete",
        "section_count": len(sections),
        "sections_with_gaps": [item["section"] for item in sections if item["gap_count"] > 0],
        "sections_with_unplanned_gaps": sections_with_unplanned_gaps,
        "missing_plan_gap_ids": missing,
        "invalid_plan_gap_ids": invalid,
        "invalid_gate_ids_by_gap": invalid_gate_ids_by_gap,
        "valid_production_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
        "sections": sections,
    }


def _known_gap_resolution_plan_coverage(known_gap_resolution_plan: list[dict[str, Any]]) -> dict[str, Any]:
    known_gap_ids = sorted(str(item.get("id")) for item in KNOWN_GAPS if item.get("id"))
    plan_by_gap = {_known_gap_plan_item_id(item): item for item in known_gap_resolution_plan if _known_gap_plan_item_id(item)}
    command_coverage = known_gap_verification_command_coverage(known_gap_resolution_plan)
    missing_gap_ids = [gap_id for gap_id in known_gap_ids if gap_id not in plan_by_gap]
    invalid_plan_gap_ids: list[str] = []
    invalid_gate_ids_by_gap: dict[str, list[str]] = {}
    command_counts: dict[str, int] = {}
    gate_counts: dict[str, int] = {}
    for gap_id in known_gap_ids:
        item = plan_by_gap.get(gap_id)
        if not isinstance(item, dict):
            continue
        commands = item.get("verification_commands", [])
        gates = item.get("production_gate_ids", [])
        command_count = len(commands) if isinstance(commands, list) else 0
        gate_count = len(gates) if isinstance(gates, list) else 0
        command_counts[gap_id] = command_count
        gate_counts[gap_id] = gate_count
        invalid_gate_ids = (
            sorted({str(gate) for gate in gates if str(gate) not in PRODUCTION_READINESS_GATE_IDS})
            if isinstance(gates, list)
            else ["production_gate_ids_not_list"]
        )
        if invalid_gate_ids:
            invalid_gate_ids_by_gap[gap_id] = invalid_gate_ids
        if (
            item.get("status") != "open"
            or command_count <= 0
            or gate_count <= 0
            or invalid_gate_ids
            or gap_id in command_coverage.get("invalid_verification_commands_by_gap", {})
            or gap_id in command_coverage.get("invalid_verification_options_by_gap", {})
        ):
            invalid_plan_gap_ids.append(gap_id)
    covered_count = len(known_gap_ids) - len(missing_gap_ids) - len(set(invalid_plan_gap_ids))
    coverage_material = {
        "known_gap_ids": known_gap_ids,
        "planned_gap_ids": sorted(plan_by_gap),
        "missing_gap_ids": missing_gap_ids,
        "invalid_plan_gap_ids": sorted(set(invalid_plan_gap_ids)),
        "invalid_gate_ids_by_gap": invalid_gate_ids_by_gap,
        "invalid_verification_commands_by_gap": command_coverage.get("invalid_verification_commands_by_gap", {}),
        "invalid_verification_options_by_gap": command_coverage.get("invalid_verification_options_by_gap", {}),
        "command_subcommands_by_gap": command_coverage.get("command_subcommands_by_gap", {}),
        "command_options_by_gap": command_coverage.get("command_options_by_gap", {}),
        "command_counts": command_counts,
        "gate_counts": gate_counts,
    }
    return {
        **coverage_material,
        "known_gap_count": len(known_gap_ids),
        "covered_count": covered_count,
        "coverage_complete": (
            not missing_gap_ids
            and not invalid_plan_gap_ids
            and command_coverage.get("command_validation_complete") is True
            and len(known_gap_ids) > 0
        ),
        "valid_production_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
        "valid_cli_subcommands": command_coverage.get("valid_subcommands", []),
        "valid_cli_options_by_subcommand": command_coverage.get("valid_options_by_subcommand", {}),
        "command_validation_complete": command_coverage.get("command_validation_complete") is True,
        "command_coverage_sha256": command_coverage.get("command_coverage_sha256"),
        "plan_coverage_sha256": _stable_json_sha256(coverage_material),
        "audit_plan_hash": _stable_json_sha256(known_gap_resolution_plan),
    }


def _known_gap_resolution_plan_gate_ids_valid(known_gap_resolution_plan: list[dict[str, Any]]) -> bool:
    for item in known_gap_resolution_plan:
        gates = item.get("production_gate_ids", [])
        if not isinstance(gates, list):
            return False
        if any(str(gate) not in PRODUCTION_READINESS_GATE_IDS for gate in gates):
            return False
    return True


def _known_gap_plan_item_id(item: dict[str, Any]) -> str:
    return str(item.get("gap_id") or item.get("id") or "")


def _implemented_evidence_materialization_audit() -> dict[str, Any]:
    """Check whether implemented-requirement evidence points to real local artifacts."""
    requirement_results = []
    total = 0
    passed = 0
    failed = 0
    unchecked = 0
    for requirement in IMPLEMENTED_REQUIREMENTS:
        evidence_results = [_materialize_evidence(str(item)) for item in requirement.get("evidence", [])]
        for item in evidence_results:
            total += 1
            if item["status"] == "passed":
                passed += 1
            elif item["status"] == "failed":
                failed += 1
            else:
                unchecked += 1
        requirement_results.append(
            {
                "id": requirement["id"],
                "status": "failed"
                if any(item["status"] == "failed" for item in evidence_results)
                else ("partially_checked" if any(item["status"] == "unchecked" for item in evidence_results) else "passed"),
                "evidence": evidence_results,
            }
        )
    return {
        "status": "failed" if failed else ("partially_checked" if unchecked else "passed"),
        "total_evidence": total,
        "passed_count": passed,
        "failed_count": failed,
        "unchecked_count": unchecked,
        "requirements": requirement_results,
        "policy": (
            "Local files and Python symbols are machine-checked. CLI commands, environment variables, "
            "and natural-language descriptors are reported as unchecked rather than treated as proof."
        ),
    }


def _materialize_evidence(evidence: str) -> dict[str, Any]:
    descriptor_result = _materialize_descriptor_evidence(evidence)
    if descriptor_result is not None:
        return descriptor_result
    runtime_result = _materialize_runtime_field_evidence(evidence)
    if runtime_result is not None:
        return runtime_result
    path_result = _materialize_path_evidence(evidence)
    if path_result is not None:
        return path_result
    symbol_result = _materialize_symbol_evidence(evidence)
    if symbol_result is not None:
        return symbol_result
    return {
        "evidence": evidence,
        "kind": "descriptor",
        "status": "unchecked",
        "reason": "not a local file path or importable Python symbol",
    }


def _materialize_descriptor_evidence(evidence: str) -> dict[str, Any] | None:
    if evidence.startswith("cli "):
        parts = evidence.removeprefix("cli ").split()
        command = parts[0]
        option = next((part for part in parts[1:] if part.startswith("--")), None)
        return _cli_parser_evidence(evidence, command, option)
    if evidence.startswith(("GET /", "POST /")):
        method, path = evidence.split(maxsplit=1)
        return _endpoint_schema_evidence(evidence, method, path)
    if evidence == "api_core.evolve_case validation_tasks":
        import inspect
        from examples.mingli_5agents.api_core import evolve_case

        source = inspect.getsource(evolve_case)
        passed = "validation_tasks = empirical_validation_tasks()" in source
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "evolve_case no longer initializes empirical validation tasks",
        }
    if evidence == "api_core.evolve_case trigger_receipt":
        import inspect
        from examples.mingli_5agents.api_core import _evolution_trigger_receipt, evolve_case

        source = inspect.getsource(evolve_case) + "\n" + inspect.getsource(_evolution_trigger_receipt)
        required_tokens = [
            "_evolution_trigger_receipt(",
            '"evolution-trigger-receipt-v1"',
            '"feedback_sha256"',
            '"validation_task_sha256"',
            '"outcome_dataset_gate_passed"',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "evolve_case no longer builds evolution trigger receipts",
        }
    if evidence == "capability_audit.github_comparison_receipt":
        import inspect

        from examples.mingli_5agents import capability_audit as audit_module

        source = inspect.getsource(audit_module._github_comparison_receipt) + "\n" + inspect.getsource(
            audit_module._capability_audit_receipt_material
        )
        required_tokens = [
            '"github-comparison-receipt-v1"',
            '"matrix_sha256"',
            '"candidate_sha256"',
            '"local_capability_sha256"',
            '"github_comparison_receipt_sha256"',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "capability audit no longer builds or binds GitHub comparison receipts",
        }
    if evidence == "capability_audit.plan_compliance_receipt":
        import inspect

        from examples.mingli_5agents import capability_audit as audit_module

        source = inspect.getsource(audit_module._plan_compliance_receipt) + "\n" + inspect.getsource(
            audit_module._capability_audit_receipt_material
        )
        required_tokens = [
            '"plan-compliance-receipt-v1"',
            '"source_receipt_sha256"',
            '"matrix_sha256"',
            '"section_gap_resolution_coverage_sha256"',
            '"plan_compliance_receipt_sha256"',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "capability audit no longer builds or binds plan compliance receipts",
        }
    if evidence == "run_demo.MingliFiveAgentSystem._annual_timeline.topic_evidence_binding":
        import inspect

        from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, _annual_topic_evidence_complete

        source = inspect.getsource(MingliFiveAgentSystem._annual_timeline) + "\n" + inspect.getsource(
            MingliFiveAgentSystem._annual_timeline_receipt
        ) + "\n" + inspect.getsource(_annual_topic_evidence_complete)
        required_tokens = [
            '"source": "annual_luck.rows"',
            '"source_row_index": index',
            '"source_field": key',
            '"bazi_evidence_sha256": evidence_sha256',
            '"provider_quality": provider_quality',
            '"topic_evidence_complete"',
            '"topic_evidence_missing"',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "annual timeline topics no longer bind source row, evidence hash, provider quality, and boundary",
        }
    if evidence in {
        "api_core.schema_document.AnnualTimelineTopic.bazi_evidence_sha256",
        "api_core.schema_document.AnnualTimelineReceipt.topic_evidence_complete",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        if evidence.endswith("AnnualTimelineTopic.bazi_evidence_sha256"):
            topic = schemas.get("AnnualTimelineTopic", {})
            required = topic.get("required", []) if isinstance(topic, dict) else []
            props = topic.get("properties", {}) if isinstance(topic, dict) else {}
            passed = (
                "bazi_evidence_sha256" in required
                and props.get("bazi_evidence_sha256", {}).get("pattern") == "^[0-9a-f]{64}$"
                and props.get("source", {}).get("const") == "annual_luck.rows"
                and {"source_row_index", "source_field", "provider_quality", "boundary"}.issubset(set(required))
            )
            reason = "AnnualTimelineTopic schema does not require topic evidence binding fields"
        else:
            receipt = schemas.get("AnnualTimelineReceipt", {})
            required = receipt.get("required", []) if isinstance(receipt, dict) else []
            props = receipt.get("properties", {}) if isinstance(receipt, dict) else {}
            passed = (
                "topic_evidence_complete" in required
                and "topic_evidence_missing" in required
                and props.get("topic_evidence_complete", {}).get("type") == "boolean"
                and props.get("topic_evidence_missing", {}).get("type") == "array"
            )
            reason = "AnnualTimelineReceipt schema does not expose topic evidence completeness"
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else reason,
        }
    if evidence == "tests/test_mingli_system.py annual_timeline_topic_evidence_binding":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "bazi_evidence_sha256",
            "topic_evidence_complete",
            "topic_evidence_missing",
            "source_field",
            "provider_quality",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "annual timeline topic evidence regression test is missing",
        }
    if evidence == "tests/test_schema_contract_evaluator.py annual_timeline_topic_evidence_binding":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "AnnualTimelineTopic",
            "bazi_evidence_sha256",
            "topic_evidence_complete",
            "topic_evidence_missing",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "annual timeline topic evidence schema contract test is missing",
        }
    if evidence in {
        "tools.monthly_luck._monthly_topic_bindings",
        "run_demo.MingliFiveAgentSystem._monthly_luck_with_topic_evidence",
    }:
        import inspect

        from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, _monthly_topic_evidence_complete
        from examples.mingli_5agents.tools.monthly_luck import _monthly_topic_bindings

        source = (
            inspect.getsource(_monthly_topic_bindings)
            + "\n"
            + inspect.getsource(MingliFiveAgentSystem._monthly_luck_with_topic_evidence)
            + "\n"
            + inspect.getsource(MingliFiveAgentSystem._monthly_luck_receipt)
            + "\n"
            + inspect.getsource(_monthly_topic_evidence_complete)
        )
        required_tokens = [
            '"source": "monthly_luck.rows"',
            '"source_row_index"',
            '"source_field"',
            '"bazi_evidence_sha256"',
            '"provider_quality"',
            '"topic_evidence_complete"',
            '"topic_evidence_missing"',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "monthly luck topics no longer bind source row, evidence hash, provider quality, and boundary",
        }
    if evidence in {
        "api_core.schema_document.MonthlyLuckTopic.bazi_evidence_sha256",
        "api_core.schema_document.MonthlyLuckReceipt.topic_evidence_complete",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        if evidence.endswith("MonthlyLuckTopic.bazi_evidence_sha256"):
            topic = schemas.get("MonthlyLuckTopic", {})
            required = topic.get("required", []) if isinstance(topic, dict) else []
            props = topic.get("properties", {}) if isinstance(topic, dict) else {}
            passed = (
                "bazi_evidence_sha256" in required
                and props.get("bazi_evidence_sha256", {}).get("pattern") == "^[0-9a-f]{64}$"
                and props.get("source", {}).get("const") == "monthly_luck.rows"
                and {"source_row_index", "source_field", "provider_quality", "boundary"}.issubset(set(required))
            )
            reason = "MonthlyLuckTopic schema does not require topic evidence binding fields"
        else:
            receipt = schemas.get("MonthlyLuckReceipt", {})
            required = receipt.get("required", []) if isinstance(receipt, dict) else []
            props = receipt.get("properties", {}) if isinstance(receipt, dict) else {}
            passed = (
                "topic_evidence_complete" in required
                and "topic_evidence_missing" in required
                and props.get("topic_evidence_complete", {}).get("type") == "boolean"
                and props.get("topic_evidence_missing", {}).get("type") == "array"
            )
            reason = "MonthlyLuckReceipt schema does not expose topic evidence completeness"
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else reason,
        }
    if evidence == "tests/test_mingli_system.py monthly_luck_topic_evidence_binding":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "monthly_luck",
            "bazi_evidence_sha256",
            "topic_evidence_complete",
            "topic_evidence_missing",
            "source_field",
            "provider_quality",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "monthly luck topic evidence regression test is missing",
        }
    if evidence == "tests/test_schema_contract_evaluator.py monthly_luck_topic_evidence_binding":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "MonthlyLuckTopic",
            "bazi_evidence_sha256",
            "topic_evidence_complete",
            "topic_evidence_missing",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "monthly luck topic evidence schema contract test is missing",
        }
    if evidence in {
        "api_core.schema_document.AnalyzeResponse.monthly_luck_ref",
        "api_core.schema_document.MonthlyLuck.rows",
        "api_core.schema_document.MonthlyLuckRow.bazi_evidence",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        final_report = (
            schemas.get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
            .get("properties", {})
        )
        monthly_luck = schemas.get("MonthlyLuck", {})
        monthly_row = schemas.get("MonthlyLuckRow", {})
        passed = (
            final_report.get("monthly_luck", {}).get("$ref") == "#/schemas/MonthlyLuck"
            and monthly_luck.get("properties", {}).get("rows", {}).get("items", {}).get("$ref")
            == "#/schemas/MonthlyLuckRow"
            and monthly_row.get("properties", {}).get("bazi_evidence", {}).get("$ref")
            == "#/schemas/MonthlyLuckBaziEvidence"
            and monthly_row.get("properties", {}).get("topics", {}).get("properties", {}).get("finance", {}).get("$ref")
            == "#/schemas/MonthlyLuckTopic"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "monthly_luck public schema is not strongly typed through row/evidence/topic refs",
        }
    if evidence in {
        "tests/test_schema_contract_evaluator.py monthly_luck_public_schema_contract",
        "tests/test_api_server.py monthly_luck_public_schema_contract",
        "tests/test_cli.py monthly_luck_public_schema_contract",
    }:
        filename = evidence.split()[0].removeprefix("tests/")
        test_path = BASE_DIR / "tests" / filename
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "MonthlyLuck",
            "MonthlyLuckRow",
            "MonthlyLuckBaziEvidence",
            "MonthlyLuckTopic",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "monthly_luck public schema contract regression test is missing",
        }
    if evidence in {
        "api_core.schema_document.AnalyzeResponse.astrology_profile_ref",
        "api_core.schema_document.AstrologyProfile.planets",
        "api_core.schema_document.AstrologyProfile.ephemeris_quality",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        final_report = (
            schemas.get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
            .get("properties", {})
        )
        profile = schemas.get("AstrologyProfile", {})
        props = profile.get("properties", {}) if isinstance(profile, dict) else {}
        passed = (
            final_report.get("astrology_profile", {}).get("$ref") == "#/schemas/AstrologyProfile"
            and props.get("planets", {}).get("items", {}).get("$ref") == "#/schemas/AstrologyPlanet"
            and props.get("houses", {}).get("items", {}).get("$ref") == "#/schemas/AstrologyHouse"
            and props.get("aspects", {}).get("items", {}).get("$ref") == "#/schemas/AstrologyAspect"
            and props.get("annual_transits", {}).get("items", {}).get("$ref") == "#/schemas/AstrologyAnnualTransit"
            and props.get("ephemeris_quality", {}).get("$ref") == "#/schemas/AstrologyEphemerisQuality"
            and props.get("method_matrix", {}).get("items", {}).get("$ref") == "#/schemas/AstrologyMethodMatrixItem"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "astrology_profile public schema is not strongly typed through profile row refs",
        }
    if evidence == "tests/test_schema_contract_evaluator.py astrology_profile_public_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "AstrologyProfile",
            "AstrologyPlanet",
            "AstrologyEphemerisQuality",
            "astrology_profile",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "astrology_profile public schema contract regression test is missing",
        }
    if evidence in {
        "api_core.schema_document.AnalyzeResponse.ziwei_qimen_profile_refs",
        "api_core.schema_document.ZiweiProfile.highlighted_palaces",
        "api_core.schema_document.QimenProfile.useful_gods",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        final_report = (
            schemas.get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
            .get("properties", {})
        )
        ziwei_props = schemas.get("ZiweiProfile", {}).get("properties", {})
        qimen_props = schemas.get("QimenProfile", {}).get("properties", {})
        passed = (
            final_report.get("ziwei_profile", {}).get("$ref") == "#/schemas/ZiweiProfile"
            and final_report.get("qimen_profile", {}).get("$ref") == "#/schemas/QimenProfile"
            and ziwei_props.get("highlighted_palaces", {}).get("items", {}).get("$ref")
            == "#/schemas/ZiweiPalaceSummary"
            and ziwei_props.get("major_limits", {}).get("items", {}).get("$ref")
            == "#/schemas/ZiweiMajorLimit"
            and ziwei_props.get("annual_activation", {}).get("items", {}).get("$ref")
            == "#/schemas/ZiweiAnnualActivation"
            and ziwei_props.get("method_matrix", {}).get("items", {}).get("$ref")
            == "#/schemas/AstrologyMethodMatrixItem"
            and qimen_props.get("duty", {}).get("$ref") == "#/schemas/QimenDuty"
            and qimen_props.get("useful_gods", {}).get("additionalProperties", {}).get("$ref")
            == "#/schemas/QimenUsefulGod"
            and qimen_props.get("highlighted_palaces", {}).get("items", {}).get("$ref")
            == "#/schemas/QimenPalaceSummary"
            and qimen_props.get("pattern_flags", {}).get("items", {}).get("$ref")
            == "#/schemas/QimenPatternFlag"
            and qimen_props.get("annual_timing", {}).get("items", {}).get("$ref")
            == "#/schemas/QimenAnnualTiming"
            and qimen_props.get("method_matrix", {}).get("items", {}).get("$ref")
            == "#/schemas/AstrologyMethodMatrixItem"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "ziwei/qimen public schema is not strongly typed through profile refs",
        }
    if evidence == "tests/test_schema_contract_evaluator.py ziwei_qimen_public_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "ZiweiProfile",
            "ZiweiPalaceSummary",
            "QimenProfile",
            "QimenUsefulGod",
            "ziwei_profile",
            "qimen_profile",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "ziwei/qimen public schema contract regression test is missing",
        }
    if evidence in {
        "api_core.schema_document.AnalyzeResponse.rendered_reports_ref",
        "api_core.schema_document.RenderedReports.en_zh",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        final_report = (
            schemas.get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
        )
        final_report_props = final_report.get("properties", {}) if isinstance(final_report, dict) else {}
        rendered = schemas.get("RenderedReports", {})
        rendered_props = rendered.get("properties", {}) if isinstance(rendered, dict) else {}
        rendered_required = set(rendered.get("required", [])) if isinstance(rendered, dict) else set()
        final_report_required = set(final_report.get("required", [])) if isinstance(final_report, dict) else set()
        passed = (
            final_report_props.get("rendered_reports", {}).get("$ref") == "#/schemas/RenderedReports"
            and "rendered_reports" in final_report_required
            and {"en", "zh"} <= rendered_required
            and rendered_props.get("en", {}).get("type") == "string"
            and rendered_props.get("zh", {}).get("type") == "string"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "rendered_reports public schema is not a required en/zh contract",
        }
    if evidence == "tests/test_schema_contract_evaluator.py rendered_reports_public_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "RenderedReports",
            "rendered_reports",
            "additionalProperties",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "rendered_reports public schema contract regression test is missing",
        }
    if evidence == "tests/test_mingli_system.py rendered_reports_runtime_contract":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            'rendered_reports"]["zh"',
            'rendered_reports"]["en"',
            'result["output"] == result["final_report"]["rendered_reports"]["zh"]',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "rendered_reports runtime contract regression test is missing",
        }
    if evidence in {
        "api_core.schema_document.AnalyzeResponse.final_report_runtime_metadata_refs",
        "api_core.schema_document.LLMSynthesisReport.prompt_fingerprint",
        "api_core.schema_document.WorkflowReport.preserve_conflicts",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        final_report = (
            schemas.get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
        )
        final_props = final_report.get("properties", {}) if isinstance(final_report, dict) else {}
        final_required = set(final_report.get("required", [])) if isinstance(final_report, dict) else set()
        llm = schemas.get("LLMSynthesisReport", {})
        workflow = schemas.get("WorkflowReport", {})
        passed = (
            final_props.get("llm_synthesis", {}).get("$ref") == "#/schemas/LLMSynthesisReport"
            and final_props.get("workflow", {}).get("$ref") == "#/schemas/WorkflowReport"
            and {"llm_synthesis", "workflow"} <= final_required
            and "prompt_fingerprint" in llm.get("required", [])
            and llm.get("properties", {}).get("generated", {}).get("type") == "boolean"
            and "preserve_conflicts" in workflow.get("required", [])
            and workflow.get("properties", {}).get("discussion_rounds", {}).get("type") == "integer"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "final_report runtime metadata schema contract is incomplete",
        }
    if evidence == "tests/test_schema_contract_evaluator.py final_report_runtime_metadata_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "LLMSynthesisReport",
            "WorkflowReport",
            "prompt_fingerprint",
            "preserve_conflicts",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "final_report runtime metadata schema regression test is missing",
        }
    if evidence == "tests/test_mingli_system.py final_report_runtime_metadata_runtime_contract":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            'result["final_report"]["llm_synthesis"]["prompt_fingerprint"]',
            'result["final_report"]["workflow"]["preserve_conflicts"]',
            'result["final_report"]["workflow"]["vote_threshold"]',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "final_report runtime metadata runtime regression test is missing",
        }
    if evidence in {
        "api_core.schema_document.AnalyzeResponse.source_review_ref",
        "api_core.schema_document.SourceReviewReport.evidence",
        "api_core.schema_document.SourceEvidenceSnippet.provenance",
        "api_core.schema_document.EvidenceSummaryItem.caution",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        final_report = (
            schemas.get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
        )
        final_props = final_report.get("properties", {}) if isinstance(final_report, dict) else {}
        final_required = set(final_report.get("required", [])) if isinstance(final_report, dict) else set()
        source_review = schemas.get("SourceReviewReport", {})
        source_props = source_review.get("properties", {}) if isinstance(source_review, dict) else {}
        snippet = schemas.get("SourceEvidenceSnippet", {})
        summary = schemas.get("EvidenceSummaryItem", {})
        passed = (
            final_props.get("source_review", {}).get("$ref") == "#/schemas/SourceReviewReport"
            and final_props.get("evidence_summary", {}).get("items", {}).get("$ref")
            == "#/schemas/EvidenceSummaryItem"
            and {"source_review", "evidence_summary"} <= final_required
            and source_props.get("evidence", {}).get("additionalProperties", {}).get("items", {}).get("$ref")
            == "#/schemas/SourceEvidenceSnippet"
            and "missing_evidence" in source_review.get("required", [])
            and snippet.get("properties", {}).get("provenance", {}).get("$ref")
            == "#/schemas/SourceEvidenceProvenance"
            and "provenance" in snippet.get("required", [])
            and "caution" in summary.get("required", [])
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "source_review/evidence_summary public schema contract is incomplete",
        }
    if evidence == "tests/test_schema_contract_evaluator.py source_review_public_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "SourceReviewReport",
            "SourceEvidenceSnippet",
            "SourceEvidenceProvenance",
            "EvidenceSummaryItem",
            "missing_evidence",
            "citation_policy",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "source_review public schema regression test is missing",
        }
    if evidence == "tests/test_mingli_system.py source_review_runtime_contract":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            'result["source_review"]["evidence_index"]["status"]',
            'result["source_review"]["evidence"]',
            'result["final_report"]["evidence_summary"][0]["caution"]',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "source_review runtime regression test is missing",
        }
    if evidence == "api_core.schema_document.AnalyzeResponse.final_report_metadata_fields":
        from examples.mingli_5agents.api_core import schema_document

        final_report = (
            schema_document()
            .get("schemas", {})
            .get("AnalyzeResponse", {})
            .get("properties", {})
            .get("result", {})
            .get("properties", {})
            .get("final_report", {})
        )
        props = final_report.get("properties", {}) if isinstance(final_report, dict) else {}
        required = set(final_report.get("required", [])) if isinstance(final_report, dict) else set()
        metadata_fields = {"title", "coordinator_version", "summary", "conflicts", "strategy_notes", "boundaries"}
        passed = (
            metadata_fields <= required
            and props.get("title", {}).get("type") == "string"
            and props.get("coordinator_version", {}).get("type") == "integer"
            and props.get("summary", {}).get("items", {}).get("type") == "string"
            and props.get("conflicts", {}).get("items", {}).get("type") == "string"
            and props.get("strategy_notes", {}).get("items", {}).get("type") == "string"
            and props.get("boundaries", {}).get("items", {}).get("type") == "string"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "final_report metadata fields are not required typed properties",
        }
    if evidence == "tests/test_schema_contract_evaluator.py final_report_metadata_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "coordinator_version",
            "strategy_notes",
            "boundaries",
            "_response_refs_ok(mutated) < 1.0",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "final_report metadata schema regression test is missing",
        }
    if evidence == "tests/test_mingli_system.py final_report_metadata_runtime_contract":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            'result["final_report"]["coordinator_version"]',
            'result["final_report"]["summary"]',
            'result["final_report"]["strategy_notes"]',
            'result["final_report"]["conflicts"]',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "final_report metadata runtime regression test is missing",
        }
    if evidence in {
        "tests/test_schema_contract_evaluator.py analyze_response_runtime_schema_validation",
        "api_core.schema_validation_errors.AnalyzeResponse",
        "api_core.production_readiness.benchmark_analyze_response_schema_valid",
        "api_core.schema_document.ProductionReadinessAnalyzeResponseSchemaAudit",
    }:
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        api_core_source = (BASE_DIR / "api_core.py").read_text(encoding="utf-8")
        required_tokens = [
            "test_analyze_response_runtime_output_matches_public_schema_contract",
            "analyze_case",
            "json.loads(json.dumps(result",
            'schema_name="AnalyzeResponse"',
            "schema_doc=schema",
            "schema_validation_errors",
            "assert errors == []",
        ]
        api_tokens = [
            "def schema_validation_errors(",
            "schema_name: str = \"AnalyzeResponse\"",
            "def _schema_validation_errors(",
            "\"schema_validation\":",
            "\"valid\": not errors",
            "benchmark_analyze_response_schema_valid",
            "def _benchmark_analyze_response_schema_audit(",
            "ProductionReadinessAnalyzeResponseSchemaAudit",
            "analyze_response_schema_audit",
        ]
        passed = all(token in source for token in required_tokens) and all(
            token in api_core_source for token in api_tokens
        )
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "AnalyzeResponse runtime schema validation test is missing",
        }
    if evidence in {
        "api_core.schema_document.TopicSynthesisItem.timing_refs",
        "api_core.schema_document.TopicSynthesisAnnualFocus.bazi_evidence",
        "api_core.schema_document.TopicSynthesisTimingSignal.ten_gods",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        topic_item_props = schemas.get("TopicSynthesisItem", {}).get("properties", {})
        annual_focus_props = schemas.get("TopicSynthesisAnnualFocus", {}).get("properties", {})
        monthly_focus_props = schemas.get("TopicSynthesisMonthlyFocus", {}).get("properties", {})
        timing_evidence_props = schemas.get("TopicSynthesisTimingEvidence", {}).get("properties", {})
        timing_signal_props = schemas.get("TopicSynthesisTimingSignal", {}).get("properties", {})
        passed = (
            topic_item_props.get("annual_focus", {}).get("$ref") == "#/schemas/TopicSynthesisAnnualFocus"
            and topic_item_props.get("monthly_focus", {}).get("$ref") == "#/schemas/TopicSynthesisMonthlyFocus"
            and topic_item_props.get("timing_evidence", {}).get("$ref")
            == "#/schemas/TopicSynthesisTimingEvidence"
            and annual_focus_props.get("bazi_evidence", {}).get("$ref") == "#/schemas/AnnualLuckBaziEvidence"
            and monthly_focus_props.get("bazi_evidence", {}).get("$ref") == "#/schemas/MonthlyLuckBaziEvidence"
            and timing_evidence_props.get("annual", {}).get("$ref") == "#/schemas/TopicSynthesisTimingSignal"
            and timing_evidence_props.get("monthly", {}).get("$ref") == "#/schemas/TopicSynthesisTimingSignal"
            and timing_signal_props.get("ten_gods", {}).get("$ref") == "#/schemas/AnnualLuckTenGodPair"
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "topic_synthesis timing fields are not strongly typed through schema refs",
        }
    if evidence == "tests/test_schema_contract_evaluator.py topic_synthesis_timing_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "TopicSynthesisAnnualFocus",
            "TopicSynthesisMonthlyFocus",
            "TopicSynthesisTimingEvidence",
            "TopicSynthesisTimingSignal",
            "natal_match_count",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "topic_synthesis timing schema regression test is missing",
        }
    if evidence == "tests/test_mingli_system.py topic_synthesis_timing_runtime_contract":
        test_path = BASE_DIR / "tests" / "test_mingli_system.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            'finance_topic["annual_focus"]["bazi_evidence"]',
            'finance_topic["monthly_focus"]["bazi_evidence"]',
            'finance_topic["timing_evidence"]["annual"]["ten_gods"]',
            'finance_topic["timing_evidence"]["monthly"]["natal_match_count"]',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "topic_synthesis timing runtime regression test is missing",
        }
    if evidence in {
        "api_core.schema_document.BaziProfile.core_analysis_refs",
        "api_core.schema_document.BaziStrengthAnalysis.element_counts",
        "api_core.schema_document.BaziUsefulGodAnalysis.rationale",
    }:
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        bazi_props = schemas.get("BaziProfile", {}).get("properties", {})
        strength = schemas.get("BaziStrengthAnalysis", {})
        useful = schemas.get("BaziUsefulGodAnalysis", {})
        luck_start = schemas.get("BaziLuckStart", {})
        passed = (
            bazi_props.get("strength_analysis", {}).get("$ref") == "#/schemas/BaziStrengthAnalysis"
            and bazi_props.get("pattern_analysis", {}).get("$ref") == "#/schemas/BaziPatternAnalysis"
            and bazi_props.get("useful_god_analysis", {}).get("$ref") == "#/schemas/BaziUsefulGodAnalysis"
            and bazi_props.get("luck_start", {}).get("$ref") == "#/schemas/BaziLuckStart"
            and "element_counts" in strength.get("required", [])
            and strength.get("properties", {}).get("element_counts", {}).get("additionalProperties", {}).get("type")
            == "integer"
            and "rationale" in useful.get("required", [])
            and "forward" in luck_start.get("required", [])
        )
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "BaziProfile core analysis fields are not strongly typed through schema refs",
        }
    if evidence == "tests/test_schema_contract_evaluator.py bazi_core_profile_schema_contract":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "BaziStrengthAnalysis",
            "BaziPatternAnalysis",
            "BaziUsefulGodAnalysis",
            "BaziLuckStart",
            "element_counts",
            "avoid_overweight_element",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "bazi core profile schema regression test is missing",
        }
    if evidence == "tests/test_empirical_validation.py github_comparison_receipt":
        test_path = BASE_DIR / "tests" / "test_empirical_validation.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "github_comparison_receipt",
            "github-comparison-receipt-v1",
            "matrix_sha256",
            "candidate_projects",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "GitHub comparison receipt regression test is missing",
        }
    if evidence == "tests/test_schema_contract_evaluator.py github_comparison_receipt":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "GitHubComparisonReceipt",
            "GitHubComparisonReceiptMaterial",
            "github_comparison_receipt_sha256",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "GitHub comparison schema contract test is missing",
        }
    if evidence == "tests/test_empirical_validation.py plan_compliance_receipt":
        test_path = BASE_DIR / "tests" / "test_empirical_validation.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "plan_compliance_receipt",
            "plan-compliance-receipt-v1",
            "section_gap_resolution_coverage_sha256",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "Plan compliance receipt regression test is missing",
        }
    if evidence == "tests/test_schema_contract_evaluator.py plan_compliance_receipt":
        test_path = BASE_DIR / "tests" / "test_schema_contract_evaluator.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "PlanComplianceReceipt",
            "PlanComplianceReceiptMaterial",
            "plan_compliance_receipt_sha256",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "Plan compliance schema contract test is missing",
        }
    if evidence == "evolution.MingliPopulationEvolver.evolve trigger_receipt":
        import inspect
        from examples.mingli_5agents.evolution import MingliPopulationEvolver

        source = inspect.getsource(MingliPopulationEvolver.evolve) + "\n" + inspect.getsource(
            MingliPopulationEvolver._with_evolution_lineage
        )
        required_tokens = [
            "trigger_receipt: dict[str, Any] | None = None",
            '"trigger_receipt": trigger_receipt',
            "trigger_receipt=trigger_receipt",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "evolver does not archive trigger receipts into lineage",
        }
    if evidence == "empirical_validation.empirical_validation_tasks split_role_filter":
        import inspect
        from examples.mingli_5agents.empirical_validation import (
            _manifest_quality_tasks,
            _quality_label_task,
            empirical_validation_tasks,
        )

        task_source = inspect.getsource(empirical_validation_tasks)
        manifest_source = inspect.getsource(_manifest_quality_tasks)
        label_source = inspect.getsource(_quality_label_task)
        required_tokens = [
            'manifest_split_role: str = "holdout"',
            "split_role=manifest_split_role",
            'split_role not in {"train", "holdout", "any"}',
            "projected_role != split_role",
            '"manifest_split_role"',
        ]
        joined = "\n".join([task_source, manifest_source, label_source])
        passed = all(token in joined for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "empirical validation manifest tasks are not split-role filtered",
        }
    if evidence == "provider_contracts.method_surface_binding":
        import inspect
        from examples.mingli_5agents import provider_contracts

        source = inspect.getsource(provider_contracts)
        required_tokens = [
            "from examples.mingli_5agents.method_surface import REQUIRED_METHODS",
            'REQUIRED_METHODS["bazi"]',
            'REQUIRED_METHODS["ziwei"]',
            'REQUIRED_METHODS["qimen"]',
            'REQUIRED_METHODS["astrology"]',
            'REQUIRED_METHODS["xuanze"]',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "provider contracts do not bind every domain to shared REQUIRED_METHODS",
        }
    if evidence == "provider_protocols.method_surface_publication":
        import inspect
        from examples.mingli_5agents import provider_protocols

        source = inspect.getsource(provider_protocols)
        required_tokens = [
            "from examples.mingli_5agents.method_surface import REQUIRED_METHODS",
            '"required_method_surface"',
            '"normalized_contract_requirement"',
            "sorted(REQUIRED_METHODS[domain])",
            "required_method_surface before the provider can be certified",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "source_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "provider protocol document does not publish shared method surface",
        }
    if evidence == "provider_protocols.provider_protocol_receipt":
        receipt = provider_protocol_receipt(provider_protocol_document(), repo=".semas_mingli_repo")
        passed = (
            isinstance(receipt, dict)
            and isinstance(receipt.get("sha256"), str)
            and len(receipt.get("sha256", "")) == 64
            and isinstance(receipt.get("material"), dict)
            and isinstance(receipt["material"].get("protocol_document_sha256"), str)
            and len(receipt["material"].get("protocol_document_sha256", "")) == 64
        )
        return {
            "evidence": evidence,
            "kind": "receipt_probe",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "provider protocol receipt does not expose stable hashes",
        }
    if evidence == "provider_checks.provider_health_checks.production_guidance":
        guidance = provider_health_checks().get("production_guidance", {})
        passed = (
            isinstance(guidance, dict)
            and isinstance(guidance.get("production_ready"), bool)
            and isinstance(guidance.get("blocked_targets"), list)
            and isinstance(guidance.get("required_env_vars"), list)
            and isinstance(guidance.get("required_provenance_env_vars"), list)
            and any("certify-provider" in command for command in guidance.get("certification_commands", []))
            and any("provider-drift" in command for command in guidance.get("drift_commands", []))
            and "production-readiness" in guidance.get("production_readiness_command", "")
        )
        return {
            "evidence": evidence,
            "kind": "runtime_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "provider_health_checks does not expose complete production_guidance",
        }
    if evidence == "benchmark safety_boundary_case":
        from examples.mingli_5agents.benchmark import benchmark_cases

        names = {str(case.get("name")) for case in benchmark_cases()}
        passed = "safety_boundary_case" in names
        return {
            "evidence": evidence,
            "kind": "benchmark_case",
            "status": "passed" if passed else "failed",
            "reason": "" if passed else "benchmark_cases does not include safety_boundary_case",
        }
    if evidence == "provider_protocols.BIRTH_PAYLOAD_SCHEMA.protocol":
        from examples.mingli_5agents.provider_protocols import BIRTH_PAYLOAD_SCHEMA

        protocol = BIRTH_PAYLOAD_SCHEMA.get("properties", {}).get("protocol")
        required = protocol.get("required", []) if isinstance(protocol, dict) else []
        passed = isinstance(protocol, dict) and {"version", "hash"}.issubset(set(required))
        return {
            "evidence": evidence,
            "kind": "schema_field",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "birth payload schema does not require protocol version/hash",
        }
    if evidence == "tests/test_provider_checks.py protocol identity":
        test_path = BASE_DIR / "tests" / "test_provider_checks.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "test_provider_health_checks_blocks_valid_contract_with_stale_protocol_identity",
            "protocol_identity_matches",
            "protocol.hash mismatch or missing",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "provider protocol identity regression test is missing",
        }
    if evidence == "provider_checks._raw_provider_contract_receipt":
        source = (BASE_DIR / "provider_checks.py").read_text(encoding="utf-8")
        required_tokens = [
            "def _raw_provider_contract_receipt(",
            '"provider_request_receipt_sha256"',
            '"stdout_sha256"',
            '"raw_contract_receipt"',
            "live_check.get(\"raw_contract_receipt\"",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "python_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(BASE_DIR / "provider_checks.py"),
            "reason": "" if passed else "raw provider contract receipt is missing from provider certification flow",
        }
    if evidence == "api_core.schema_document.ProviderRawContractReceipt":
        from examples.mingli_5agents.api_core import schema_document

        schemas = schema_document().get("schemas", {})
        receipt = schemas.get("ProviderRawContractReceipt", {})
        material = schemas.get("ProviderRawContractReceiptMaterial", {})
        certification = schemas.get("ProviderCertificationReceiptMaterial", {})
        required = set(material.get("required", [])) if isinstance(material, dict) else set()
        passed = (
            isinstance(receipt, dict)
            and receipt.get("properties", {}).get("material", {}).get("$ref")
            == "#/schemas/ProviderRawContractReceiptMaterial"
            and {"provider_request_receipt_sha256", "stdout_sha256", "contract_valid"}.issubset(required)
            and "raw_contract_receipt" in certification.get("required", [])
        )
        return {
            "evidence": evidence,
            "kind": "schema_contract",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "ProviderRawContractReceipt schema is missing or not required by certification receipt",
        }
    if evidence == "tests/test_provider_checks.py raw provider contract receipt":
        test_path = BASE_DIR / "tests" / "test_provider_checks.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "raw_contract_receipt",
            "provider_request_receipt_sha256",
            "stdout_sha256",
            "contract_valid",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "raw provider contract receipt regression test is missing",
        }
    if evidence == "provider_contracts.astrology_ephemeris_audit_contract":
        source = (BASE_DIR / "provider_contracts.py").read_text(encoding="utf-8")
        required_tokens = [
            "def _astrology_ephemeris_missing(",
            '"license_or_review"',
            '"data_source"',
            '"calculation_time"',
            '"julian_day_ut"',
            '"iso_utc"',
            "missing.extend(_astrology_ephemeris_missing",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "python_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(BASE_DIR / "provider_contracts.py"),
            "reason": "" if passed else "astrology raw JSON-CLI contract no longer requires auditable ephemeris metadata",
        }
    if evidence == "provider_protocols.astrology_ephemeris_stdout_schema":
        protocols = provider_protocol_document().get("domains", {})
        astrology = protocols.get("astrology", {}) if isinstance(protocols, dict) else {}
        schema = astrology.get("stdout_schema", {}) if isinstance(astrology, dict) else {}
        sample = astrology.get("sample_stdout", {}) if isinstance(astrology, dict) else {}
        ephemeris_schema = schema.get("properties", {}).get("ephemeris", {}) if isinstance(schema, dict) else {}
        required = set(ephemeris_schema.get("required", [])) if isinstance(ephemeris_schema, dict) else set()
        sample_ephemeris = sample.get("ephemeris", {}) if isinstance(sample, dict) else {}
        required_fields = {
            "source",
            "zodiac",
            "house_system",
            "time_scale",
            "calculation_time",
            "data_source",
            "license_or_review",
        }
        passed = (
            "ephemeris" in set(schema.get("required", []))
            and required_fields.issubset(required)
            and required_fields.issubset(set(sample_ephemeris))
            and "calculation_time" in sample_ephemeris
        )
        return {
            "evidence": evidence,
            "kind": "provider_protocol_schema",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "astrology provider protocol no longer requires ephemeris audit metadata",
        }
    if evidence == "tests/test_provider_contracts.py astrology ephemeris audit metadata":
        test_path = BASE_DIR / "tests" / "test_provider_contracts.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "test_raw_json_cli_contract_requires_astrology_ephemeris_audit_metadata",
            "ephemeris.house_system",
            "ephemeris.calculation_time",
            "ephemeris.license_or_review",
            "ephemeris.data_source",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "astrology ephemeris metadata contract regression test is missing",
        }
    if evidence == "provider_contracts.xuanze_rule_table_audit_contract":
        source = (BASE_DIR / "provider_contracts.py").read_text(encoding="utf-8")
        required_tokens = [
            "def _xuanze_basis_audit_missing(",
            '"rule_table_source"',
            '"rule_table_version"',
            '"license_or_review"',
            '"calculation_scope"',
            '"rule_table_sha256|rule_table_receipt_sha256"',
            "missing.extend(_xuanze_basis_audit_missing",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "python_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(BASE_DIR / "provider_contracts.py"),
            "reason": "" if passed else "xuanze raw JSON-CLI contract no longer requires auditable rule-table metadata",
        }
    if evidence == "provider_protocols.xuanze_rule_table_stdout_schema":
        protocols = provider_protocol_document().get("domains", {})
        xuanze = protocols.get("xuanze", {}) if isinstance(protocols, dict) else {}
        schema = xuanze.get("stdout_schema", {}) if isinstance(xuanze, dict) else {}
        sample = xuanze.get("sample_stdout", {}) if isinstance(xuanze, dict) else {}
        basis_schema = schema.get("properties", {}).get("basis", {}) if isinstance(schema, dict) else {}
        required = set(basis_schema.get("required", [])) if isinstance(basis_schema, dict) else set()
        sample_basis = sample.get("basis", {}) if isinstance(sample, dict) else {}
        required_fields = {
            "provider",
            "provider_quality",
            "rule_set",
            "rule_table_source",
            "rule_table_version",
            "license_or_review",
            "calculation_scope",
        }
        passed = (
            "basis" in set(schema.get("required", []))
            and required_fields.issubset(required)
            and required_fields.issubset(set(sample_basis))
            and (
                isinstance(sample_basis.get("rule_table_sha256"), str)
                or isinstance(sample_basis.get("rule_table_receipt_sha256"), str)
            )
        )
        return {
            "evidence": evidence,
            "kind": "provider_protocol_schema",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "xuanze provider protocol no longer requires rule-table audit metadata",
        }
    if evidence == "tests/test_provider_contracts.py xuanze rule table audit metadata":
        test_path = BASE_DIR / "tests" / "test_provider_contracts.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "test_raw_json_cli_contract_requires_xuanze_rule_table_audit_metadata",
            "basis.rule_table_source",
            "basis.rule_table_version",
            "basis.rule_table_sha256|rule_table_receipt_sha256",
            "basis.license_or_review",
            "basis.calculation_scope",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "xuanze rule-table metadata contract regression test is missing",
        }
    if evidence == "provider_contracts.ziwei_qimen_calculation_basis_audit_contract":
        source = (BASE_DIR / "provider_contracts.py").read_text(encoding="utf-8")
        required_tokens = [
            "def _calculation_basis_missing(",
            '"rule_set"',
            '"rule_set_version"',
            '"rule_source"',
            '"license_or_review"',
            '"calculation_scope"',
            "rule_source_sha256|rule_receipt_sha256",
            'payload.get("calculation_basis")',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "python_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(BASE_DIR / "provider_contracts.py"),
            "reason": "" if passed else "ziwei/qimen raw JSON-CLI contracts no longer require auditable calculation basis",
        }
    if evidence == "provider_protocols.ziwei_qimen_calculation_basis_stdout_schema":
        protocols = provider_protocol_document().get("domains", {})
        required_fields = {
            "provider",
            "rule_set",
            "rule_set_version",
            "rule_source",
            "license_or_review",
            "calculation_scope",
        }
        passed = True
        for domain in ("ziwei", "qimen"):
            protocol = protocols.get(domain, {}) if isinstance(protocols, dict) else {}
            schema = protocol.get("stdout_schema", {}) if isinstance(protocol, dict) else {}
            sample = protocol.get("sample_stdout", {}) if isinstance(protocol, dict) else {}
            basis_schema = schema.get("properties", {}).get("calculation_basis", {}) if isinstance(schema, dict) else {}
            required = set(basis_schema.get("required", [])) if isinstance(basis_schema, dict) else set()
            sample_basis = sample.get("calculation_basis", {}) if isinstance(sample, dict) else {}
            passed = passed and (
                "calculation_basis" in set(schema.get("required", []))
                and required_fields.issubset(required)
                and required_fields.issubset(set(sample_basis))
                and (
                    isinstance(sample_basis.get("rule_source_sha256"), str)
                    or isinstance(sample_basis.get("rule_receipt_sha256"), str)
                )
            )
        return {
            "evidence": evidence,
            "kind": "provider_protocol_schema",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "ziwei/qimen provider protocol no longer requires calculation-basis audit metadata",
        }
    if evidence == "tests/test_provider_contracts.py ziwei qimen calculation basis audit metadata":
        test_path = BASE_DIR / "tests" / "test_provider_contracts.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "test_raw_json_cli_contract_requires_ziwei_qimen_calculation_basis_audit_metadata",
            "calculation_basis.rule_set",
            "calculation_basis.rule_set_version",
            "calculation_basis.rule_source",
            "calculation_basis.rule_source_sha256|rule_receipt_sha256",
            "calculation_basis.license_or_review",
            "calculation_basis.calculation_scope",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "ziwei/qimen calculation-basis metadata regression test is missing",
        }
    if evidence == "tests/test_provider_protocols.py ziwei qimen calculation basis stdout schema":
        test_path = BASE_DIR / "tests" / "test_provider_protocols.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "stdout.calculation_basis",
            "ziwei_basis_required",
            "qimen_basis_required",
            "rule_source_sha256",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "ziwei/qimen calculation-basis stdout-schema regression test is missing",
        }
    if evidence == "classical_corpus_refresh.source_governance_metadata":
        source = (BASE_DIR / "classical_corpus_refresh.py").read_text(encoding="utf-8")
        required_tokens = [
            "REQUIRED_SOURCE_GOVERNANCE_FIELDS",
            "ALLOWED_SOURCE_REVIEW_STATUSES",
            "def _source_governance_failures(",
            '"license"',
            '"rights_basis"',
            '"review_status"',
            '"reviewed_by"',
            '"content_scope"',
            '"governance_valid"',
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "python_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(BASE_DIR / "classical_corpus_refresh.py"),
            "reason": "" if passed else "classical source-list governance metadata checks are missing",
        }
    if evidence == "tests/test_evidence.py source governance metadata":
        test_path = BASE_DIR / "tests" / "test_evidence.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "test_source_list_audit_rejects_missing_source_governance_metadata",
            "license is required for source governance",
            "governance_valid",
            "open_license_reviewed",
            "source_list_receipt",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "classical source governance metadata regression test is missing",
        }
    if evidence.startswith("SEMAS_") and " environment configuration" in evidence:
        env_var = evidence.split()[0]
        protocols = provider_protocol_document().get("domains", {})
        found = any(isinstance(protocol, dict) and protocol.get("env_var") == env_var for protocol in protocols.values())
        return {
            "evidence": evidence,
            "kind": "provider_env_var",
            "status": "passed" if found else "failed",
            "reason": "" if found else "provider protocol document does not expose this env var",
        }
    return None


def _cli_parser_evidence(evidence: str, command: str, option: str | None) -> dict[str, Any]:
    from examples.mingli_5agents.cli import build_parser

    parser = build_parser()
    subparsers_action = next((action for action in parser._actions if getattr(action, "choices", None)), None)
    choices = getattr(subparsers_action, "choices", {}) if subparsers_action is not None else {}
    subparser = choices.get(command)
    passed = subparser is not None
    if passed and option:
        passed = any(option in getattr(action, "option_strings", []) for action in subparser._actions)
    return {
        "evidence": evidence,
        "kind": "cli_parser",
        "status": "passed" if passed else "failed",
        "command": command,
        "option": option or "",
        "reason": "" if passed else "CLI parser does not expose command or required option",
    }


def _endpoint_schema_evidence(evidence: str, method: str, path: str) -> dict[str, Any]:
    from examples.mingli_5agents.api_core import schema_document

    endpoints = schema_document().get("endpoints", {})
    key = f"{method} {path}"
    passed = key in endpoints
    return {
        "evidence": evidence,
        "kind": "api_schema_endpoint",
        "status": "passed" if passed else "failed",
        "endpoint": key,
        "reason": "" if passed else "schema_document endpoints do not include endpoint",
    }


def _materialize_runtime_field_evidence(evidence: str) -> dict[str, Any] | None:
    if evidence == "bazi.method_matrix.eight_school_coverage":
        from examples.mingli_5agents.reference_charts import REQUIRED_METHODS

        report = _sample_final_report()
        method_matrix = report.get("bazi_profile", {}).get("method_matrix", [])
        observed = {
            str(item.get("method"))
            for item in method_matrix
            if isinstance(item, dict) and item.get("method")
        }
        required = set(REQUIRED_METHODS.get("bazi", set()))
        missing = sorted(required - observed)
        passed = bool(required) and not missing
        return {
            "evidence": evidence,
            "kind": "runtime_method_coverage",
            "status": "passed" if passed else "failed",
            "required": sorted(required),
            "observed": sorted(observed),
            "missing": missing,
            "reason": "" if passed else "sample final_report bazi method_matrix does not cover required methods",
        }
    if evidence.startswith("final_report."):
        report = _sample_final_report()
        field_path = evidence.removeprefix("final_report.")
        found, value = _nested_value(report, field_path.split("."))
        if not found:
            return {
                "evidence": evidence,
                "kind": "runtime_field",
                "status": "failed",
                "field_path": evidence,
                "reason": "field missing from sample final_report",
            }
        return {
            "evidence": evidence,
            "kind": "runtime_field",
            "status": "passed",
            "field_path": evidence,
            "value_type": type(value).__name__,
        }
    if evidence.startswith("api_core.schema_document."):
        from examples.mingli_5agents.api_core import schema_document

        path = evidence.removeprefix("api_core.schema_document.").split(".")
        schemas = schema_document().get("schemas", {})
        if len(path) < 2:
            found, value = False, None
        else:
            schema_name = path[0]
            schema = schemas.get(schema_name, {})
            if len(path) == 2:
                found, value = _nested_value(schema, ["properties", path[1]])
            else:
                found, value = _nested_value(schema, path[1:])
        return {
            "evidence": evidence,
            "kind": "api_schema_field",
            "status": "passed" if found else "failed",
            "field_path": evidence,
            "value_type": type(value).__name__ if found else "",
            "reason": "" if found else "schema_document field is missing",
        }
    if evidence == "api_core.status.calendar_providers":
        calendar = describe_calendar_providers()
        return {
            "evidence": evidence,
            "kind": "runtime_field",
            "status": "passed" if isinstance(calendar, dict) and "providers" in calendar else "failed",
            "field_path": evidence,
            "value_type": type(calendar).__name__,
            "reason": "" if isinstance(calendar, dict) and "providers" in calendar else "calendar provider description missing providers",
        }
    if evidence in {"api_core.status.archive_integrity", "api_core.status.lineage_integrity"}:
        status_payload = _sample_status_payload()
        field_path = evidence.removeprefix("api_core.status.")
        found, value = _nested_value(status_payload, [field_path])
        if not found:
            return {
                "evidence": evidence,
                "kind": "runtime_field",
                "status": "failed",
                "field_path": evidence,
                "reason": "field missing from sample status payload",
            }
        return {
            "evidence": evidence,
            "kind": "runtime_field",
            "status": "passed",
            "field_path": evidence,
            "value_type": type(value).__name__,
        }
    if evidence in {
        "api_core.provider_certification_ledger.protocol_status",
        "api_core.provider_certification_ledger.reference_contract_status",
        "api_core.provider_certification_ledger.command_fingerprint_status",
    }:
        from examples.mingli_5agents.api_core import _provider_certification_ledger_status

        with tempfile.TemporaryDirectory() as tmp_dir:
            ledger = _provider_certification_ledger_status(Path(tmp_dir))
        field_name = evidence.rsplit(".", 1)[-1]
        found, value = _nested_value(ledger, [field_name])
        return {
            "evidence": evidence,
            "kind": "runtime_field",
            "status": "passed" if found else "failed",
            "field_path": evidence,
            "value_type": type(value).__name__ if found else "",
            "reason": "" if found else f"provider certification ledger status missing {field_name}",
        }
    if evidence == "api_core.provider_certification_ledger.latest_record_binding":
        import inspect

        from examples.mingli_5agents.api_core import (
            _append_provider_certification_record,
            _provider_certification_ledger_status,
        )

        append_source = inspect.getsource(_append_provider_certification_record)
        status_source = inspect.getsource(_provider_certification_ledger_status)
        required_tokens = [
            'ledger["latest_record_hash"] = record["record_hash"]',
            'ledger["latest_record_index"] = record["index"]',
            '"latest_record_index"',
            "latest_record_index does not match last record",
        ]
        passed = all(token in append_source or token in status_source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "provider ledger latest hash/index binding is incomplete",
        }
    if evidence == "api_core.release_manifest_ledger.latest_record_binding":
        import inspect

        from examples.mingli_5agents.api_core import _append_release_manifest_record, _release_manifest_ledger_status

        append_source = inspect.getsource(_append_release_manifest_record)
        status_source = inspect.getsource(_release_manifest_ledger_status)
        required_tokens = [
            'ledger["latest_record_hash"] = record["record_hash"]',
            'ledger["latest_record_index"] = record["index"]',
            '"latest_record_index"',
            "latest_record_index does not match last record",
        ]
        passed = all(token in append_source or token in status_source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release ledger latest hash/index binding is incomplete",
        }
    if evidence == "api_core.release_manifest_ledger.receipt_material_binding":
        import inspect

        from examples.mingli_5agents.api_core import _release_manifest_ledger_record_failures

        source = inspect.getsource(_release_manifest_ledger_record_failures)
        required_tokens = [
            '"candidate_name"',
            '"production_readiness_status"',
            '"production_ready"',
            '"release_gate_checks"',
            '"provider_onboarding_receipt_sha256"',
            '"provider_onboarding_receipt"',
            '"provider_protocols_receipt_sha256"',
            '"provider_protocols_receipt"',
            '"github_comparison_receipt_sha256"',
            '"github_comparison_receipt"',
            '"plan_compliance_receipt_sha256"',
            '"plan_compliance_receipt"',
            '"external_payload_birth_match_coverage"',
            '"known_gap_ids"',
            '"outcome_dataset"',
            '"evolution_trigger_receipt_sha256"',
            '"evolution_trigger_receipt"',
            '"evolution_trigger_receipt_current"',
            "release_manifest_receipt",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release ledger receipt-material consistency checks are incomplete",
        }
    if evidence == "api_core.release_manifest.evolution_trigger_receipt":
        import inspect

        from examples.mingli_5agents.api_core import (
            _append_release_manifest_record,
            _release_manifest_receipt,
            release_manifest,
        )

        source = (
            inspect.getsource(release_manifest)
            + "\n"
            + inspect.getsource(_release_manifest_receipt)
            + "\n"
            + inspect.getsource(_append_release_manifest_record)
        )
        required_tokens = [
            '"evolution_trigger_receipt_sha256"',
            '"evolution_trigger_receipt"',
            '"evolution_trigger_receipt_current"',
            "latest_evolution",
            "trigger_receipt",
            "genome_lineage",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release manifest does not bind evolution trigger receipt through response, receipt, and ledger",
        }
    if evidence == "api_core.release_manifest.github_comparison_receipt":
        import inspect

        from examples.mingli_5agents.api_core import (
            _append_release_manifest_record,
            _release_manifest_receipt,
            release_manifest,
        )

        source = (
            inspect.getsource(release_manifest)
            + "\n"
            + inspect.getsource(_release_manifest_receipt)
            + "\n"
            + inspect.getsource(_append_release_manifest_record)
        )
        required_tokens = [
            '"github_comparison_receipt_sha256"',
            '"github_comparison_receipt"',
            "github_comparison_receipt",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release manifest does not bind GitHub comparison receipt through response, receipt, and ledger",
        }
    if evidence == "api_core.release_manifest.plan_compliance_receipt":
        import inspect

        from examples.mingli_5agents.api_core import (
            _append_release_manifest_record,
            _release_manifest_receipt,
            release_manifest,
        )

        source = (
            inspect.getsource(release_manifest)
            + "\n"
            + inspect.getsource(_release_manifest_receipt)
            + "\n"
            + inspect.getsource(_append_release_manifest_record)
        )
        required_tokens = [
            '"plan_compliance_receipt_sha256"',
            '"plan_compliance_receipt"',
            "plan_compliance_receipt",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release manifest does not bind plan compliance receipt through response, receipt, and ledger",
        }
    if evidence == "tests/test_cli.py release github_comparison_receipt":
        test_path = BASE_DIR / "tests" / "test_cli.py"
        source = test_path.read_text(encoding="utf-8") if test_path.exists() else ""
        required_tokens = [
            "github_comparison_receipt_sha256",
            "github_comparison_receipt",
            "dimension_count",
        ]
        passed = all(token in source for token in required_tokens)
        return {
            "evidence": evidence,
            "kind": "test_source_probe",
            "status": "passed" if passed else "failed",
            "resolved": str(test_path),
            "reason": "" if passed else "release GitHub comparison receipt regression test is missing",
        }
    if evidence in {
        "api_core.release_manifest.release_gate_checks.provider_onboarding_receipt_current",
        "api_core.release_manifest.release_gate_checks.provider_protocols_receipt_current",
    }:
        import inspect

        from examples.mingli_5agents.api_core import release_manifest

        source = inspect.getsource(release_manifest)
        token = (
            '"provider_onboarding_receipt_current"'
            if evidence.endswith("provider_onboarding_receipt_current")
            else '"provider_protocols_receipt_current"'
        )
        passed = token in source and "release_gate_checks" in source
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release gate check is not materialized in release_manifest",
        }
    if evidence in {
        "outcome_dataset.external_review_gate",
        "outcome_dataset.frozen_holdout_gate",
        "outcome_dataset.data_split_record_coverage_gate",
        "outcome_dataset.label_collection_pre_analysis_gate",
        "outcome_dataset.statistical_plan_preregistration_gate",
        "outcome_dataset.record_label_provenance_gate",
    }:
        from examples.mingli_5agents.outcome_dataset import audit_outcome_dataset_manifest

        manifest = BASE_DIR / "providers" / "outcome_dataset_manifest_example.json"
        audit = audit_outcome_dataset_manifest(manifest)
        gates = audit.get("governance_gates", {}).get("gates", {})
        gate_map = {
            "outcome_dataset.external_review_gate": "external_review_approved",
            "outcome_dataset.frozen_holdout_gate": "data_split_frozen",
            "outcome_dataset.data_split_record_coverage_gate": "data_split_records_covered",
            "outcome_dataset.label_collection_pre_analysis_gate": "label_collection_pre_analysis",
            "outcome_dataset.statistical_plan_preregistration_gate": "statistical_plan_preregistered",
            "outcome_dataset.record_label_provenance_gate": "record_label_provenance_complete",
        }
        gate_id = gate_map[evidence]
        passed = audit.get("valid") is True and isinstance(gates, dict) and gates.get(gate_id) is True
        return {
            "evidence": evidence,
            "kind": "runtime_gate",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else f"example outcome manifest did not pass {gate_id}",
        }
    if evidence in {
        "api_core.production_readiness.provider_certification_protocols_current",
        "api_core.production_readiness.provider_certification_reference_contracts_current",
        "api_core.production_readiness.provider_certification_command_fingerprints_current",
        "api_core.production_readiness.release_manifest_ledger_integrity",
        "api_core.production_readiness.outcome_dataset_data_split_records_covered",
        "api_core.production_readiness.benchmark_external_payload_birth_matches",
        "api_core.production_readiness.benchmark_topic_confidence_boundaries",
        "api_core.production_readiness.blocked_capability_coverage_complete",
        "api_core.production_readiness.known_gap_handoff_bundle_ready",
    }:
        import inspect

        from examples.mingli_5agents.api_core import production_readiness, schema_document

        gate_id = evidence.rsplit(".", 1)[-1]
        gates = schema_document().get("schemas", {}).get("ProductionReadinessResponse", {}).get("properties", {}).get("gates")
        endpoints = schema_document().get("endpoints", {})
        source = inspect.getsource(production_readiness)
        passed = isinstance(gates, dict) and "GET /production-readiness" in endpoints and gate_id in source
        return {
            "evidence": evidence,
            "kind": "runtime_gate",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else f"production readiness gate {gate_id} missing from schema, endpoint, or implementation",
        }
    if evidence == "api_core.release_manifest.release_gate_checks.outcome_dataset_split_coverage_bound":
        import inspect

        from examples.mingli_5agents.api_core import release_manifest, schema_document

        source = inspect.getsource(release_manifest)
        schema = schema_document().get("schemas", {}).get("ReleaseManifestGateChecks", {})
        required = schema.get("required", []) if isinstance(schema, dict) else []
        passed = "outcome_dataset_split_coverage_bound" in source and "outcome_dataset_split_coverage_bound" in required
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": "" if passed else "release manifest split-coverage gate is missing from implementation or schema",
        }
    if evidence in {
        "api_core.release_manifest.release_gate_checks.provider_audit_contract_gates_bound",
        "api_core.release_manifest.release_gate_checks.outcome_statistical_plan_preregistration_bound",
        "api_core.release_manifest.release_gate_checks.classical_latest_refresh_receipt_bound",
        "api_core.release_manifest.release_gate_checks.blocked_capability_coverage_bound",
        "api_core.release_manifest.release_gate_checks.known_gap_handoff_bundle_bound",
        "api_core.release_manifest.release_gate_checks.known_gap_command_coverage_bound",
    }:
        import inspect

        from examples.mingli_5agents.api_core import release_manifest, schema_document

        gate_id = evidence.rsplit(".", 1)[-1]
        source = inspect.getsource(release_manifest)
        schema = schema_document().get("schemas", {}).get("ReleaseManifestGateChecks", {})
        required = schema.get("required", []) if isinstance(schema, dict) else []
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        passed = gate_id in source and gate_id in required and gate_id in properties
        return {
            "evidence": evidence,
            "kind": "runtime_binding",
            "status": "passed" if passed else "failed",
            "field_path": evidence,
            "reason": ""
            if passed
            else f"release manifest readiness-gate binding {gate_id} is missing from implementation or schema",
        }
    return None


_RUNTIME_CACHE: dict[str, Any] = {}


def _sample_final_report() -> dict[str, Any]:
    if "final_report" not in _RUNTIME_CACHE:
        from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, bootstrap_repo, population_training_tasks

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = bootstrap_repo(Path(tmp_dir))
            coordinator = repo.load_agent("mingli_orchestrator")
            result = MingliFiveAgentSystem(repo)(coordinator, population_training_tasks()[0]["input"])
        _RUNTIME_CACHE["final_report"] = result.get("final_report", {})
    return _RUNTIME_CACHE["final_report"]


def _sample_status_payload() -> dict[str, Any]:
    if "status_payload" not in _RUNTIME_CACHE:
        from examples.mingli_5agents.api_core import status
        from examples.mingli_5agents.run_demo import bootstrap_repo

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            bootstrap_repo(repo_path)
            payload = status(repo_path)
        _RUNTIME_CACHE["status_payload"] = payload
    return _RUNTIME_CACHE["status_payload"]


def _nested_value(container: Any, path: list[str]) -> tuple[bool, Any]:
    current = container
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _materialize_path_evidence(evidence: str) -> dict[str, Any] | None:
    token = evidence.split()[0] if evidence.split() else evidence
    if not (
        "/" in token
        or "\\" in token
        or token.endswith((".py", ".yaml", ".json", ".md", ".toml"))
        or token in {"tests/"}
    ):
        return None
    candidates = [
        BASE_DIR / token,
        REPO_ROOT / token,
    ]
    for path in candidates:
        if path.exists():
            return {
                "evidence": evidence,
                "kind": "path",
                "status": "passed",
                "resolved": str(path),
            }
    return {
        "evidence": evidence,
        "kind": "path",
        "status": "failed",
        "reason": "path does not exist",
        "checked_candidates": [str(path) for path in candidates],
    }


def _materialize_symbol_evidence(evidence: str) -> dict[str, Any] | None:
    if " " in evidence or "/" in evidence or "\\" in evidence or "." not in evidence:
        return None
    if evidence.split(".", 1)[0] in {"final_report"}:
        return {
            "evidence": evidence,
            "kind": "runtime_field",
            "status": "unchecked",
            "field_path": evidence,
            "reason": "field belongs to runtime JSON/data output, not a Python symbol",
        }
    module_names = _candidate_module_names(evidence)
    for module_name, attr_parts in module_names:
        try:
            target = importlib.import_module(module_name)
        except Exception:  # noqa: BLE001 - audit should report unavailable optional imports without failing.
            continue
        resolved_attrs: list[str] = []
        missing_attr = None
        for index, attr in enumerate(attr_parts):
            dataclass_fields = getattr(target, "__dataclass_fields__", {})
            if isinstance(dataclass_fields, dict) and attr in dataclass_fields and index == len(attr_parts) - 1:
                resolved_attrs.append(attr)
                missing_attr = None
                break
            if not hasattr(target, attr):
                missing_attr = attr
                if resolved_attrs:
                    remaining = attr_parts[index:]
                    return {
                        "evidence": evidence,
                        "kind": "runtime_field",
                        "status": "unchecked",
                        "module": module_name,
                        "resolved_symbol": ".".join(resolved_attrs),
                        "field_path": ".".join(remaining),
                        "reason": "field belongs to runtime JSON/data output, not a Python symbol",
                    }
                break
            target = getattr(target, attr)
            resolved_attrs.append(attr)
        if missing_attr is None:
            return {
                "evidence": evidence,
                "kind": "python_symbol",
                "status": "passed",
                "module": module_name,
                "symbol": ".".join(attr_parts),
            }
    if module_names:
        return {
            "evidence": evidence,
            "kind": "python_symbol",
            "status": "failed",
            "reason": "symbol could not be imported",
            "checked_modules": [module for module, _attrs in module_names],
        }
    return None


def _candidate_module_names(evidence: str) -> list[tuple[str, list[str]]]:
    parts = evidence.split(".")
    candidates: list[tuple[str, list[str]]] = []
    for module_part_count in range(len(parts) - 1, 0, -1):
        raw_module = ".".join(parts[:module_part_count])
        attrs = parts[module_part_count:]
        module = raw_module if raw_module.startswith(("examples.", "semas.")) else f"examples.mingli_5agents.{raw_module}"
        candidates.append((module, attrs))
        if raw_module.startswith("semas."):
            candidates.append((raw_module, attrs))
    return candidates


def _provider_protocol_governance_ready(document: dict[str, Any]) -> bool:
    domains = document.get("domains")
    if not isinstance(domains, dict) or set(domains) != {"astrology", "qimen", "xuanze", "ziwei"}:
        return False
    if not isinstance(document.get("protocol_hash"), str) or len(document["protocol_hash"]) != 64:
        return False
    if not _provider_protocol_identity_handshake_summary(document).get("ready"):
        return False
    for protocol in domains.values():
        if not isinstance(protocol, dict):
            return False
        if not isinstance(protocol.get("protocol_hash"), str) or len(protocol["protocol_hash"]) != 64:
            return False
        if protocol.get("sample_stdout_contract", {}).get("valid") is not True:
            return False
    return True


def _provider_production_guidance_ready(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    required_lists = (
        "blocked_targets",
        "required_env_vars",
        "required_provenance_env_vars",
        "certification_commands",
        "drift_commands",
        "deployment_checklist",
        "next_actions",
    )
    if value.get("production_ready") is not False and value.get("production_ready") is not True:
        return False
    if any(not isinstance(value.get(key), list) for key in required_lists):
        return False
    if value.get("production_ready") is False and any(not value.get(key) for key in required_lists):
        return False
    required_strings = (
        "provider_onboarding_command",
        "provider_ledger_command",
        "production_readiness_command",
        "smoke_command",
        "policy",
    )
    if any(not isinstance(value.get(key), str) or not value.get(key) for key in required_strings):
        return False
    return (
        any("certify-provider" in command for command in value.get("certification_commands", []))
        and any("provider-drift" in command for command in value.get("drift_commands", []))
        and "production-readiness" in value.get("production_readiness_command", "")
        and "providers --profile production --live" in value.get("smoke_command", "")
    )


def _provider_protocol_identity_handshake_summary(document: dict[str, Any]) -> dict[str, Any]:
    domains = document.get("domains")
    if not isinstance(domains, dict):
        return {"ready": False, "domains": [], "failures": ["provider protocol domains missing"]}
    failures = []
    domain_summaries = {}
    for domain, protocol in sorted(domains.items()):
        if not isinstance(protocol, dict):
            failures.append(f"{domain}: protocol document is not an object")
            continue
        sample_protocol = protocol.get("sample_stdin", {}).get("protocol")
        stdin_protocol = protocol.get("stdin_schema", {}).get("properties", {}).get("protocol")
        production_requirements = protocol.get("production_requirements", [])
        required = stdin_protocol.get("required", []) if isinstance(stdin_protocol, dict) else []
        sample_has_identity = (
            isinstance(sample_protocol, dict)
            and sample_protocol.get("version") == document.get("protocol_version")
            and isinstance(sample_protocol.get("hash"), str)
            and len(sample_protocol.get("hash", "")) == 64
        )
        schema_requires_identity = isinstance(stdin_protocol, dict) and {"version", "hash"}.issubset(set(required))
        requires_stdout_echo = any(
            "protocol.version" in str(item) and "protocol.hash" in str(item)
            for item in production_requirements
            if isinstance(item, str)
        )
        domain_summaries[domain] = {
            "sample_stdin_has_protocol_identity": sample_has_identity,
            "stdin_schema_requires_protocol_identity": schema_requires_identity,
            "production_requires_stdout_echo": requires_stdout_echo,
        }
        if not sample_has_identity:
            failures.append(f"{domain}: sample_stdin.protocol identity missing")
        if not schema_requires_identity:
            failures.append(f"{domain}: stdin_schema.protocol does not require version/hash")
        if not requires_stdout_echo:
            failures.append(f"{domain}: production requirements do not require protocol echo")
    return {
        "ready": not failures and set(domains) == {"astrology", "qimen", "xuanze", "ziwei"},
        "domains": domain_summaries,
        "failures": failures,
    }


def _external_structured_contract_domains(reference_charts: dict[str, Any]) -> list[str]:
    for case in reference_charts.get("cases", []):
        if isinstance(case, dict) and case.get("name") == "external_structured_provider_contract":
            domains = case.get("checked_domains", [])
            return sorted(str(item) for item in domains) if isinstance(domains, list) else []
    return []


def _external_structured_provenance_domains(reference_charts: dict[str, Any]) -> list[str]:
    for case in reference_charts.get("cases", []):
        if not (isinstance(case, dict) and case.get("name") == "external_structured_provider_contract"):
            continue
        if case.get("passed") is not True:
            return []
        coverage = case.get("provenance_coverage", {})
        domains = case.get("checked_domains", [])
        if not isinstance(coverage, dict) or not isinstance(domains, list):
            return []
        return sorted(str(item) for item in domains if coverage.get(item) is True)
    return []


def _feedback_memory_safety_audit(repo_path: Path | None) -> dict[str, Any]:
    if repo_path is None:
        profile = {
            "correction_counts": {},
            "unsafe_corrections": {},
            "unsafe_feedback_count": 0,
            "strategy_priors": {},
            "total_events": 0,
        }
    else:
        profile = MingliFeedbackMemory(repo_path / "memory" / "feedback_memory.json").profile()
    unsafe_count = int(profile.get("unsafe_feedback_count", 0) or 0)
    return {
        "status": "contains_quarantined_feedback" if unsafe_count else "clean",
        "unsafe_feedback_count": unsafe_count,
        "unsafe_corrections": dict(profile.get("unsafe_corrections", {})),
        "policy": "Unsafe corrections are quarantined from ordinary correction_counts and only reinforce safety_guardrails.",
        "ordinary_correction_count": len(profile.get("correction_counts", {})),
        "safety_guardrail_prior": float(profile.get("strategy_priors", {}).get("safety_guardrails", 0.0)),
    }
