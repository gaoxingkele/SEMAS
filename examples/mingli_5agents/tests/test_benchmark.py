"""Tests for built-in mingli benchmark runner."""

from __future__ import annotations

from pathlib import Path

from examples.mingli_5agents.benchmark import benchmark_cases, compare_versions, run_benchmark
from examples.mingli_5agents.evolution import MINGLI_STRATEGIES, MingliPopulationEvolver
from examples.mingli_5agents.run_demo import (
    MingliFiveAgentSystem,
    bootstrap_repo,
    build_mingli_evaluator,
    population_training_tasks,
)


def test_run_benchmark_returns_aggregate_metrics(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    result = run_benchmark(repo)
    assert result.genome_version == 1
    assert len(result.cases) == len(benchmark_cases())
    assert result.reference_charts["passed"] is True
    assert result.reference_charts["total"] >= 2
    assert result.empirical_validation["status"] == "ready_non_predictive"
    assert result.empirical_validation["predictive_truth_cases"] == 0
    assert result.benchmark_receipt["schema_version"] == 1
    assert len(result.benchmark_receipt["sha256"]) == 64
    assert result.benchmark_receipt["material"]["genome_version"] == 1
    assert result.benchmark_receipt["material"]["passed_rate"] == result.passed_rate
    assert result.benchmark_receipt["material"]["reproducibility_manifest"] == result.reproducibility_manifest
    repeated = run_benchmark(repo)
    assert repeated.benchmark_receipt["sha256"] == result.benchmark_receipt["sha256"]
    manifest = result.reproducibility_manifest
    assert manifest["run_type"] == "benchmark"
    assert manifest["deterministic"] is True
    assert manifest["genome_version"] == 1
    assert [item["name"] for item in manifest["strategy_fingerprints"]] == [
        strategy["name"] for strategy in MINGLI_STRATEGIES
    ]
    assert all(len(item["prompt_sha256"]) == 64 for item in manifest["strategy_fingerprints"])
    assert manifest["train_task_count"] == len(benchmark_cases())
    assert manifest["validation_task_count"] == 0
    assert len(manifest["train_task_fingerprints"]) == len(benchmark_cases())
    assert all(len(fingerprint) == 16 for fingerprint in manifest["train_task_fingerprints"])
    cost = manifest["cost_governance"]
    assert cost["candidate_count"] == len(MINGLI_STRATEGIES) + 1
    assert cost["train_task_count"] == len(benchmark_cases())
    assert cost["validation_task_count"] == 0
    assert cost["total_candidate_task_evaluations"] == (len(MINGLI_STRATEGIES) + 2) * len(benchmark_cases())
    assert cost["llm_calls_allowed"] is False
    assert cost["iteration_frequency_policy"] == "manual_or_feedback_triggered"
    case_names = {case["name"] for case in result.cases}
    assert "zh_topic_professional_auto_case" in case_names
    assert "production_external_provider_case" in case_names
    assert 0.0 <= result.average_score <= 1.0
    assert {
        "citation",
        "safety",
        "workflow",
        "report_schema",
        "provider_contracts",
        "evidence_provenance",
        "chinese_render",
        "capability_audit",
        "schema_contract",
    }.issubset(result.mean_metrics)
    assert result.mean_metrics["schema_contract"] == 1.0
    zh_case = next(case for case in result.cases if case["name"] == "zh_topic_professional_auto_case")
    assert zh_case["metrics"]["safety"] == 1.0
    assert zh_case["metrics"]["report_schema"] == 1.0
    assert zh_case["metrics"]["provider_contracts"] == 1.0
    assert zh_case["metrics"]["evidence_provenance"] == 1.0
    assert zh_case["metrics"]["chinese_render"] == 1.0
    assert zh_case["metrics"]["capability_audit"] == 1.0
    assert zh_case["metrics"]["schema_contract"] == 1.0
    assert zh_case["report_features"]["topic_count"] == 8
    assert zh_case["report_features"]["birth_profile_present"] is True
    assert len(zh_case["report_features"]["birth_profile_fingerprint"]) == 64
    assert zh_case["report_features"]["birthplace_geocoded"] is True
    assert zh_case["report_features"]["birthplace_geocoding_quality"] == "city_centroid"
    assert zh_case["report_features"]["request_provenance_present"] is True
    assert len(zh_case["report_features"]["request_provenance_chain_sha256"]) == 64
    assert zh_case["report_features"]["deliberation_receipt_present"] is True
    assert len(zh_case["report_features"]["deliberation_receipt_sha256"]) == 64
    assert zh_case["report_features"]["deliberation_claim_count"] == 4
    assert zh_case["report_features"]["annual_timeline_receipt_present"] is True
    assert len(zh_case["report_features"]["annual_timeline_receipt_sha256"]) == 64
    assert zh_case["report_features"]["annual_timeline_row_count"] == 3
    assert zh_case["report_features"]["annual_timeline_receipt_bound_to_provenance"] is True
    assert zh_case["report_features"]["monthly_luck_receipt_present"] is True
    assert len(zh_case["report_features"]["monthly_luck_receipt_sha256"]) == 64
    assert zh_case["report_features"]["monthly_luck_row_count"] == 12
    assert zh_case["report_features"]["monthly_luck_receipt_bound_to_provenance"] is True
    assert zh_case["report_features"]["auspicious_calendar_receipt_present"] is True
    assert len(zh_case["report_features"]["auspicious_calendar_receipt_sha256"]) == 64
    assert zh_case["report_features"]["auspicious_calendar_row_count"] == 7
    assert zh_case["report_features"]["auspicious_calendar_receipt_bound_to_provenance"] is True
    assert zh_case["report_features"]["topic_confidence_boundaries_ok"] is True
    assert zh_case["report_features"]["topic_confidence_missing_topics"] == []
    assert set(zh_case["report_features"]["topic_confidence_levels"]) == {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }
    assert "provider_fallbacks_present" in zh_case["report_features"]["topic_confidence_summary"][
        "downgrade_reasons"
    ]
    assert zh_case["report_features"]["auspicious_calendar_count"] == 7
    assert zh_case["report_features"]["has_chinese_render"] is True
    assert zh_case["report_features"]["chinese_render_duplicate_bullet_ratio"] == 0.0
    assert zh_case["report_features"]["chinese_render_topic_evidence_anchor_ratio"] == 1.0
    assert zh_case["report_features"]["chinese_render_topic_judgment_structure_ratio"] == 1.0
    assert zh_case["report_features"]["chinese_render_ascii_letter_count"] == 0
    assert zh_case["report_features"]["chinese_render_ascii_question_present"] is False
    assert zh_case["report_features"]["chinese_render_code_marker_present"] is False
    assert zh_case["report_features"]["output_language"] == "zh"
    assert zh_case["report_features"]["provider_summary_status"] in {"production_ready", "ready_with_provider_gaps"}
    assert zh_case["report_features"]["provider_blocker_count"] >= 0
    assert zh_case["report_features"]["provider_action_plan_count"] == zh_case["report_features"]["provider_blocker_count"]
    assert set(zh_case["report_features"]["provider_action_plan_domains"])
    assert zh_case["report_features"]["provider_action_plan_covers_blockers"] is True
    assert zh_case["report_features"]["provider_quality"] in {
        "professional_unavailable_fallback",
        "lunar_python",
        "sxtwl",
    }
    assert zh_case["report_features"]["external_payload_receipt_count"] == 0
    assert zh_case["report_features"]["external_payload_receipts_complete"] is False
    assert zh_case["report_features"]["external_payload_birth_match_statuses"] == []
    assert zh_case["report_features"]["external_payload_birth_mismatch_count"] == 0
    assert zh_case["report_features"]["external_payload_birth_mismatch_domains"] == []
    assert zh_case["report_features"]["external_payload_birth_matches_ok"] is True
    production_case = next(case for case in result.cases if case["name"] == "production_external_provider_case")
    assert production_case["metrics"]["report_schema"] == 1.0
    assert production_case["metrics"]["provider_contracts"] == 1.0
    assert production_case["report_features"]["birth_profile_present"] is True
    assert len(production_case["report_features"]["birth_profile_fingerprint"]) == 64
    assert production_case["report_features"]["birthplace_geocoded"] is True
    assert production_case["report_features"]["request_provenance_present"] is True
    assert len(production_case["report_features"]["request_provenance_chain_sha256"]) == 64
    assert production_case["report_features"]["deliberation_receipt_present"] is True
    assert len(production_case["report_features"]["deliberation_receipt_sha256"]) == 64
    assert production_case["report_features"]["deliberation_claim_count"] == 4
    assert production_case["report_features"]["annual_timeline_receipt_present"] is True
    assert len(production_case["report_features"]["annual_timeline_receipt_sha256"]) == 64
    assert production_case["report_features"]["annual_timeline_row_count"] == 1
    assert production_case["report_features"]["annual_timeline_receipt_bound_to_provenance"] is True
    assert production_case["report_features"]["monthly_luck_receipt_present"] is True
    assert len(production_case["report_features"]["monthly_luck_receipt_sha256"]) == 64
    assert production_case["report_features"]["monthly_luck_row_count"] == 12
    assert production_case["report_features"]["monthly_luck_receipt_bound_to_provenance"] is True
    assert production_case["report_features"]["auspicious_calendar_receipt_present"] is True
    assert len(production_case["report_features"]["auspicious_calendar_receipt_sha256"]) == 64
    assert production_case["report_features"]["auspicious_calendar_row_count"] == 1
    assert production_case["report_features"]["auspicious_calendar_receipt_bound_to_provenance"] is True
    assert production_case["report_features"]["chinese_render_duplicate_bullet_ratio"] == 0.0
    assert production_case["report_features"]["chinese_render_topic_evidence_anchor_ratio"] == 1.0
    assert production_case["report_features"]["chinese_render_topic_judgment_structure_ratio"] == 1.0
    assert production_case["report_features"]["chinese_render_ascii_letter_count"] == 0
    assert production_case["report_features"]["chinese_render_ascii_question_present"] is False
    assert production_case["report_features"]["chinese_render_code_marker_present"] is False
    assert production_case["report_features"]["topic_confidence_boundaries_ok"] is True
    assert production_case["report_features"]["topic_confidence_missing_topics"] == []
    assert production_case["report_features"]["provider_summary_status"] == "production_ready"
    assert production_case["report_features"]["provider_blocker_count"] == 0
    assert production_case["report_features"]["provider_action_plan_count"] == 0
    assert production_case["report_features"]["provider_action_plan_domains"] == []
    assert production_case["report_features"]["provider_action_plan_covers_blockers"] is True
    assert production_case["report_features"]["provider_quality"] == "external_bazi"
    assert production_case["report_features"]["external_payload_receipt_domains"] == [
        "astrology",
        "bazi",
        "qimen",
        "xuanze",
        "ziwei",
    ]
    assert production_case["report_features"]["external_payload_receipt_count"] == 5
    assert production_case["report_features"]["external_payload_receipts_complete"] is True
    assert production_case["report_features"]["external_payload_birth_mismatch_count"] == 0
    assert production_case["report_features"]["external_payload_birth_mismatch_domains"] == []
    assert production_case["report_features"]["external_payload_birth_matches_ok"] is True
    assert {item["domain"] for item in production_case["report_features"]["external_payload_birth_match_statuses"]} == {
        "astrology",
        "bazi",
        "qimen",
        "xuanze",
        "ziwei",
    }


def test_compare_versions_after_population_evolution(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    evolver = MingliPopulationEvolver(
        repo=repo,
        evaluator=build_mingli_evaluator(),
        executor=MingliFiveAgentSystem(repo),
    )
    evolved = evolver.evolve(
        train_tasks=population_training_tasks(),
        validation_tasks=population_training_tasks()[:1],
    )
    assert evolved is not None
    comparison = compare_versions(repo, baseline_version=1)
    assert comparison["candidate"]["genome_version"] == 2
    assert len(comparison["candidate"]["benchmark_receipt"]["sha256"]) == 64
    assert comparison["candidate"]["reproducibility_manifest"]["run_type"] == "benchmark"
    assert comparison["score_delta"] > 0
    assert comparison["metric_deltas"]["workflow"] > 0
