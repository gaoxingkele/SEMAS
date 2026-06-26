"""Benchmark runner for the mingli five-agent SEMAS framework."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from semas.genome.repository import GenomeRepository

from examples.mingli_5agents.empirical_validation import run_empirical_validation
from examples.mingli_5agents.evaluators.chinese_render_evaluator import (
    _tail_section_duplicate_bullet_ratio,
    _tail_section_topic_evidence_anchor_ratio,
    _tail_section_topic_judgment_structure_ratio,
)
from examples.mingli_5agents.evolution import reproducibility_manifest
from examples.mingli_5agents.reference_charts import reference_chart_cases, run_reference_chart_checks
from examples.mingli_5agents.run_demo import (
    MingliFiveAgentSystem,
    build_mingli_evaluator,
    demo_task,
    population_training_tasks,
)
from examples.mingli_5agents.topic_synthesis import topic_confidence_summary


def benchmark_cases() -> list[dict[str, Any]]:
    """Return built-in benchmark cases for regression and leaderboard checks."""
    cases = [
        {
            "name": "demo_feedback",
            "input": demo_task(),
            "expected": {
                "feedback": {
                    "satisfaction": 0.65,
                    "corrections": ["more citations"],
                }
            },
        }
    ]
    for idx, item in enumerate(population_training_tasks(), start=1):
        cases.append({"name": f"training_{idx}", **item})
    cases.append(
        {
            "name": "safety_boundary_case",
            "input": {
                "birth": {
                    "name": "Safety Case",
                    "birth_date": "1979-02-01",
                    "birth_time": "23:10",
                    "gender": "unspecified",
                    "birthplace": "Nanjing",
                }
            },
            "expected": {
                "feedback": {
                    "satisfaction": 0.7,
                    "corrections": ["keep high-stakes boundary explicit"],
                }
            },
        }
    )
    cases.append(
        {
            "name": "zh_topic_professional_auto_case",
            "input": {
                "birth": {
                    "name": "Chinese Topic Case",
                    "birth_date": "1978-04-14",
                    "birth_time": "06:50",
                    "gender": "male",
                    "birthplace": "Sanming",
                },
                "calendar_provider": "auto",
                "annual_start_year": 2024,
                "annual_end_year": 2026,
                "monthly_years": [2026],
                "language": "zh",
            },
            "expected": {
                "feedback": {
                    "satisfaction": 0.9,
                    "corrections": ["needs Chinese report and topic synthesis"],
                }
            },
        }
    )
    external_provider_birth = deepcopy(reference_chart_cases()[0].birth)
    cases.append(
        {
            "name": "production_external_provider_case",
            "input": {
                "birth": external_provider_birth,
                "annual_start_year": 2026,
                "annual_end_year": 2026,
                "monthly_years": [2026],
                "auspicious_start_date": "2026-06-21",
                "auspicious_end_date": "2026-06-21",
                "language": "zh",
            },
            "expected": {
                "feedback": {
                    "satisfaction": 0.95,
                    "corrections": ["all provider domains should be production ready"],
                }
            },
        }
    )
    return cases


@dataclass
class BenchmarkResult:
    """Aggregated benchmark result for one genome version."""

    genome_version: int
    candidate_name: str | None
    passed_rate: float
    average_score: float
    mean_metrics: dict[str, float]
    reference_charts: dict[str, Any]
    empirical_validation: dict[str, Any]
    reproducibility_manifest: dict[str, Any]
    benchmark_receipt: dict[str, Any]
    cases: list[dict[str, Any]]


def run_benchmark(repo: GenomeRepository, version: int | None = None) -> BenchmarkResult:
    """Run built-in benchmark cases against one coordinator genome version."""
    agent = repo.load_agent("mingli_orchestrator", version=version)
    executor = MingliFiveAgentSystem(repo)
    evaluator = build_mingli_evaluator()
    case_results = []
    for case in benchmark_cases():
        result = executor(agent, case["input"])
        evaluation = evaluator.evaluate({**case["input"], **result}, case.get("expected"))
        final_report = result.get("final_report", {})
        birth_profile = final_report.get("birth_profile", {})
        request_provenance = final_report.get("request_provenance", {})
        deliberation_receipt = final_report.get("deliberation_receipt", {})
        annual_timeline_receipt = final_report.get("annual_timeline_receipt", {})
        monthly_luck_receipt = final_report.get("monthly_luck_receipt", {})
        auspicious_calendar_receipt = final_report.get("auspicious_calendar_receipt", {})
        bazi_context = result.get("specialists", {}).get("bazi", {}).get("chart", {}).get("context", {})
        provider_summary = final_report.get("provider_summary", {})
        topic_confidence = topic_confidence_summary(final_report.get("topic_synthesis", {}))
        rendered_zh = final_report.get("rendered_reports", {}).get("zh", "")
        rendered_zh = rendered_zh if isinstance(rendered_zh, str) else ""
        case_results.append(
            {
                "name": case["name"],
                "passed": evaluation.passed,
                "score": evaluation.score,
                "metrics": evaluation.metrics,
                "workflow": result.get("workflow"),
                "report_features": {
                    "topic_count": len(final_report.get("topic_synthesis", {})),
                    "topic_confidence_summary": topic_confidence,
                    "topic_confidence_boundaries_ok": topic_confidence.get("boundaries_ok") is True,
                    "topic_confidence_missing_topics": topic_confidence.get("missing_topics", []),
                    "topic_confidence_levels": topic_confidence.get("levels", {}),
                    "birth_profile_present": _birth_profile_present(birth_profile),
                    "birth_profile_fingerprint": _birth_profile_fingerprint(birth_profile),
                    "birthplace_geocoded": _birthplace_geocoded(birth_profile),
                    "birthplace_geocoding_quality": birth_profile.get("geocoding_quality")
                    if isinstance(birth_profile, dict)
                    else None,
                    "request_provenance_present": _request_provenance_present(request_provenance),
                    "request_provenance_chain_sha256": request_provenance.get("chain_sha256")
                    if isinstance(request_provenance, dict)
                    else None,
                    "deliberation_receipt_present": _deliberation_receipt_present(deliberation_receipt),
                    "deliberation_receipt_sha256": deliberation_receipt.get("sha256")
                    if isinstance(deliberation_receipt, dict)
                    else None,
                    "deliberation_claim_count": deliberation_receipt.get("claim_count")
                    if isinstance(deliberation_receipt, dict)
                    else 0,
                    "annual_timeline_receipt_present": _annual_timeline_receipt_present(annual_timeline_receipt),
                    "annual_timeline_receipt_sha256": annual_timeline_receipt.get("sha256")
                    if isinstance(annual_timeline_receipt, dict)
                    else None,
                    "annual_timeline_row_count": annual_timeline_receipt.get("row_count")
                    if isinstance(annual_timeline_receipt, dict)
                    else 0,
                    "annual_timeline_receipt_bound_to_provenance": _annual_timeline_receipt_bound_to_provenance(
                        request_provenance,
                        annual_timeline_receipt,
                    ),
                    "monthly_luck_receipt_present": _monthly_luck_receipt_present(monthly_luck_receipt),
                    "monthly_luck_receipt_sha256": monthly_luck_receipt.get("sha256")
                    if isinstance(monthly_luck_receipt, dict)
                    else None,
                    "monthly_luck_row_count": monthly_luck_receipt.get("row_count")
                    if isinstance(monthly_luck_receipt, dict)
                    else 0,
                    "monthly_luck_receipt_bound_to_provenance": _monthly_luck_receipt_bound_to_provenance(
                        request_provenance,
                        monthly_luck_receipt,
                    ),
                    "auspicious_calendar_receipt_present": _auspicious_calendar_receipt_present(
                        auspicious_calendar_receipt
                    ),
                    "auspicious_calendar_receipt_sha256": auspicious_calendar_receipt.get("sha256")
                    if isinstance(auspicious_calendar_receipt, dict)
                    else None,
                    "auspicious_calendar_row_count": auspicious_calendar_receipt.get("row_count")
                    if isinstance(auspicious_calendar_receipt, dict)
                    else 0,
                    "auspicious_calendar_receipt_bound_to_provenance": (
                        _auspicious_calendar_receipt_bound_to_provenance(
                            request_provenance,
                            auspicious_calendar_receipt,
                        )
                    ),
                    "auspicious_calendar_count": final_report.get("auspicious_calendar", {}).get("range", {}).get("count", 0),
                    "has_chinese_render": "zh" in final_report.get("rendered_reports", {}),
                    "chinese_render_duplicate_bullet_ratio": _tail_section_duplicate_bullet_ratio(
                        rendered_zh,
                        section_count=2,
                    ),
                    "chinese_render_topic_evidence_anchor_ratio": _tail_section_topic_evidence_anchor_ratio(
                        rendered_zh,
                        section_count=2,
                    ),
                    "chinese_render_topic_judgment_structure_ratio": (
                        _tail_section_topic_judgment_structure_ratio(
                            rendered_zh,
                            section_count=2,
                        )
                    ),
                    "chinese_render_ascii_letter_count": sum(
                        1 for char in rendered_zh if char.isascii() and char.isalpha()
                    ),
                    "chinese_render_ascii_question_present": "?" in rendered_zh,
                    "chinese_render_code_marker_present": any(
                        marker in rendered_zh for marker in ("```", "python -m ", "SEMAS_")
                    ),
                    "provider_quality": bazi_context.get("provider_quality"),
                    "provider_summary_status": provider_summary.get("status"),
                    "provider_blocker_count": len(provider_summary.get("production_blockers", []))
                    if isinstance(provider_summary.get("production_blockers"), list)
                    else 0,
                    "provider_action_plan_count": len(provider_summary.get("action_plan", []))
                    if isinstance(provider_summary.get("action_plan"), list)
                    else 0,
                    "provider_action_plan_domains": _provider_action_plan_domains(provider_summary),
                    "provider_action_plan_covers_blockers": _provider_action_plan_covers_blockers(provider_summary),
                    "external_payload_receipt_domains": _external_payload_receipt_domains(provider_summary),
                    "external_payload_receipt_count": len(_external_payload_receipt_domains(provider_summary)),
                    "external_payload_receipts_complete": _external_payload_receipts_complete(provider_summary),
                    "external_payload_birth_match_statuses": _external_payload_birth_match_statuses(provider_summary),
                    "external_payload_birth_mismatch_count": len(_external_payload_birth_mismatches(provider_summary)),
                    "external_payload_birth_mismatch_domains": _external_payload_birth_mismatches(provider_summary),
                    "external_payload_birth_matches_ok": _external_payload_birth_matches_ok(provider_summary),
                    "output_language": "zh" if str(result.get("output", "")).startswith("# ") and "## 使用边界" in result.get("output", "") else "en",
                },
            }
        )

    average_score = sum(item["score"] for item in case_results) / len(case_results)
    passed_rate = sum(1 for item in case_results if item["passed"]) / len(case_results)
    metric_names = sorted({name for item in case_results for name in item["metrics"]})
    mean_metrics = {
        name: sum(item["metrics"].get(name, 0.0) for item in case_results) / len(case_results)
        for name in metric_names
    }
    reference_charts = run_reference_chart_checks()
    empirical_validation = run_empirical_validation(repo, version=agent.version)
    manifest = reproducibility_manifest(
        run_type="benchmark",
        train_tasks=benchmark_cases(),
        genome_version=agent.version,
    )
    result_payload = {
        "genome_version": agent.version,
        "candidate_name": agent.meta.get("candidate_name"),
        "passed_rate": passed_rate,
        "average_score": average_score,
        "mean_metrics": mean_metrics,
        "reference_charts": reference_charts,
        "empirical_validation": empirical_validation,
        "reproducibility_manifest": manifest,
        "cases": case_results,
    }
    return BenchmarkResult(
        genome_version=agent.version,
        candidate_name=agent.meta.get("candidate_name"),
        passed_rate=passed_rate,
        average_score=average_score,
        mean_metrics=mean_metrics,
        reference_charts=reference_charts,
        empirical_validation=empirical_validation,
        reproducibility_manifest=manifest,
        benchmark_receipt=_benchmark_receipt(result_payload),
        cases=case_results,
    )


def _birth_profile_present(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required_text = (
        "name",
        "birth_date",
        "birth_time",
        "gender",
        "birthplace",
        "birthplace_normalized",
        "birthplace_region",
        "geocoding_provider",
        "geocoding_quality",
    )
    required_ints = ("year", "month", "day", "hour", "minute")
    return (
        all(isinstance(value.get(key), str) and bool(value.get(key)) for key in required_text)
        and all(isinstance(value.get(key), int) for key in required_ints)
        and isinstance(value.get("timezone_offset"), (int, float, str))
        and value.get("timezone_offset") not in ("", None)
    )


def _birth_profile_fingerprint(value: Any) -> str | None:
    if not _birth_profile_present(value):
        return None
    material = {
        key: value.get(key)
        for key in (
            "name",
            "birth_date",
            "birth_time",
            "gender",
            "birthplace",
            "birthplace_normalized",
            "birthplace_region",
            "latitude",
            "longitude",
            "timezone_offset",
            "geocoding_provider",
            "geocoding_quality",
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "calendar_provider",
            "annual_start_year",
            "annual_end_year",
        )
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _birthplace_geocoded(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        isinstance(value.get("birthplace_normalized"), str)
        and bool(value.get("birthplace_normalized"))
        and isinstance(value.get("birthplace_region"), str)
        and value.get("birthplace_region") != "unknown"
        and isinstance(value.get("latitude"), (int, float))
        and isinstance(value.get("longitude"), (int, float))
        and value.get("timezone_offset") not in ("", None)
        and value.get("geocoding_quality") != "unresolved"
    )


def _external_payload_receipt_domains(provider_summary: Any) -> list[str]:
    if not isinstance(provider_summary, dict):
        return []
    domains = provider_summary.get("domains")
    if not isinstance(domains, dict):
        return []
    return sorted(
        domain
        for domain, row in domains.items()
        if isinstance(row, dict)
        and row.get("external_payload_receipt_valid") is True
        and isinstance(row.get("external_payload_receipt_sha256"), str)
        and len(row.get("external_payload_receipt_sha256", "")) == 64
    )


def _provider_action_plan_domains(provider_summary: Any) -> list[str]:
    if not isinstance(provider_summary, dict):
        return []
    action_plan = provider_summary.get("action_plan")
    if not isinstance(action_plan, list):
        return []
    return sorted(
        str(item.get("domain"))
        for item in action_plan
        if isinstance(item, dict) and item.get("domain")
    )


def _provider_action_plan_covers_blockers(provider_summary: Any) -> bool:
    if not isinstance(provider_summary, dict):
        return False
    blockers = provider_summary.get("production_blockers")
    if not isinstance(blockers, list):
        return False
    return set(str(item) for item in blockers) == set(_provider_action_plan_domains(provider_summary))


def _external_payload_receipts_complete(provider_summary: Any) -> bool:
    if not isinstance(provider_summary, dict):
        return False
    domains = provider_summary.get("domains")
    if not isinstance(domains, dict) or not domains:
        return False
    external_domains = {
        str(domain)
        for domain, row in domains.items()
        if isinstance(row, dict) and str(row.get("provider_quality", "")).startswith("external_")
    }
    return bool(external_domains) and external_domains == set(_external_payload_receipt_domains(provider_summary))


def _external_payload_birth_match_statuses(provider_summary: Any) -> list[dict[str, Any]]:
    if not isinstance(provider_summary, dict):
        return []
    domains = provider_summary.get("domains")
    if not isinstance(domains, dict):
        return []
    statuses = []
    for domain, row in domains.items():
        if not isinstance(row, dict) or not str(row.get("provider_quality", "")).startswith("external_"):
            continue
        mismatch_fields = row.get("external_payload_birth_mismatch_fields", [])
        statuses.append(
            {
                "domain": str(domain),
                "status": str(row.get("external_payload_birth_match_status") or "unknown"),
                "mismatch_fields": [str(item) for item in mismatch_fields] if isinstance(mismatch_fields, list) else [],
                "declared_birth_profile_sha256": row.get("external_payload_declared_birth_profile_sha256"),
            }
        )
    return sorted(statuses, key=lambda item: item["domain"])


def _external_payload_birth_mismatches(provider_summary: Any) -> list[str]:
    return [
        item["domain"]
        for item in _external_payload_birth_match_statuses(provider_summary)
        if item.get("status") == "mismatch"
    ]


def _external_payload_birth_matches_ok(provider_summary: Any) -> bool:
    return all(
        item.get("status") in {"matched", "not_declared"}
        for item in _external_payload_birth_match_statuses(provider_summary)
    )


def _request_provenance_present(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = ("raw_task_input_sha256", "birth_profile_sha256", "report_material_sha256", "chain_sha256")
    return value.get("schema_version") == "request-provenance-v1" and all(
        isinstance(value.get(key), str) and len(value.get(key)) == 64 for key in required
    )


def _deliberation_receipt_present(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == "deliberation-receipt-v1"
        and isinstance(value.get("sha256"), str)
        and len(value.get("sha256", "")) == 64
        and isinstance(value.get("claim_count"), int)
        and value.get("claim_count", 0) > 0
        and isinstance(value.get("discussion_count"), int)
        and value.get("discussion_count", 0) > 0
    )


def _annual_timeline_receipt_present(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == "annual-timeline-receipt-v1"
        and isinstance(value.get("sha256"), str)
        and len(value.get("sha256", "")) == 64
        and isinstance(value.get("annual_timeline_sha256"), str)
        and len(value.get("annual_timeline_sha256", "")) == 64
        and isinstance(value.get("row_count"), int)
        and value.get("row_count", 0) > 0
        and isinstance(value.get("row_fingerprints"), list)
        and len(value.get("row_fingerprints", [])) == value.get("row_count")
    )


def _annual_timeline_receipt_bound_to_provenance(
    request_provenance: Any,
    annual_timeline_receipt: Any,
) -> bool:
    if not isinstance(request_provenance, dict) or not isinstance(annual_timeline_receipt, dict):
        return False
    report_material = request_provenance.get("report_material")
    if not isinstance(report_material, dict):
        return False
    return (
        isinstance(annual_timeline_receipt.get("sha256"), str)
        and report_material.get("annual_timeline_receipt_sha256") == annual_timeline_receipt.get("sha256")
    )


def _monthly_luck_receipt_present(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == "monthly-luck-receipt-v1"
        and isinstance(value.get("sha256"), str)
        and len(value.get("sha256", "")) == 64
        and isinstance(value.get("monthly_luck_rows_sha256"), str)
        and len(value.get("monthly_luck_rows_sha256", "")) == 64
        and isinstance(value.get("row_count"), int)
        and value.get("row_count", 0) > 0
        and isinstance(value.get("row_fingerprints"), list)
        and len(value.get("row_fingerprints", [])) == value.get("row_count")
    )


def _monthly_luck_receipt_bound_to_provenance(
    request_provenance: Any,
    monthly_luck_receipt: Any,
) -> bool:
    if not isinstance(request_provenance, dict) or not isinstance(monthly_luck_receipt, dict):
        return False
    report_material = request_provenance.get("report_material")
    if not isinstance(report_material, dict):
        return False
    return (
        isinstance(monthly_luck_receipt.get("sha256"), str)
        and report_material.get("monthly_luck_receipt_sha256") == monthly_luck_receipt.get("sha256")
    )


def _auspicious_calendar_receipt_present(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == "auspicious-calendar-receipt-v1"
        and isinstance(value.get("sha256"), str)
        and len(value.get("sha256", "")) == 64
        and isinstance(value.get("calendar_rows_sha256"), str)
        and len(value.get("calendar_rows_sha256", "")) == 64
        and isinstance(value.get("method_layers_sha256"), str)
        and len(value.get("method_layers_sha256", "")) == 64
        and isinstance(value.get("row_count"), int)
        and value.get("row_count", 0) > 0
        and isinstance(value.get("row_fingerprints"), list)
        and len(value.get("row_fingerprints", [])) == value.get("row_count")
    )


def _auspicious_calendar_receipt_bound_to_provenance(
    request_provenance: Any,
    auspicious_calendar_receipt: Any,
) -> bool:
    if not isinstance(request_provenance, dict) or not isinstance(auspicious_calendar_receipt, dict):
        return False
    report_material = request_provenance.get("report_material")
    if not isinstance(report_material, dict):
        return False
    return (
        isinstance(auspicious_calendar_receipt.get("sha256"), str)
        and report_material.get("auspicious_calendar_receipt_sha256")
        == auspicious_calendar_receipt.get("sha256")
    )


def _benchmark_receipt(result: dict[str, Any]) -> dict[str, Any]:
    """Return a stable receipt for one built-in benchmark run."""
    material = {
        "schema_version": 1,
        "genome_version": result.get("genome_version"),
        "candidate_name": result.get("candidate_name"),
        "passed_rate": result.get("passed_rate"),
        "average_score": result.get("average_score"),
        "mean_metrics": result.get("mean_metrics", {}),
        "reference_charts": {
            "passed": result.get("reference_charts", {}).get("passed")
            if isinstance(result.get("reference_charts"), dict)
            else None,
            "passed_count": result.get("reference_charts", {}).get("passed_count")
            if isinstance(result.get("reference_charts"), dict)
            else None,
            "total": result.get("reference_charts", {}).get("total")
            if isinstance(result.get("reference_charts"), dict)
            else None,
        },
        "empirical_validation": {
            "status": result.get("empirical_validation", {}).get("status")
            if isinstance(result.get("empirical_validation"), dict)
            else None,
            "case_count": result.get("empirical_validation", {}).get("case_count")
            if isinstance(result.get("empirical_validation"), dict)
            else None,
            "predictive_truth_cases": result.get("empirical_validation", {}).get("predictive_truth_cases")
            if isinstance(result.get("empirical_validation"), dict)
            else None,
        },
        "reproducibility_manifest": result.get("reproducibility_manifest", {}),
        "cases": [
            {
                "name": case.get("name"),
                "passed": case.get("passed"),
                "score": case.get("score"),
                "metrics": case.get("metrics", {}),
                "report_features": case.get("report_features", {}),
            }
            for case in result.get("cases", [])
            if isinstance(case, dict)
        ],
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def compare_versions(
    repo: GenomeRepository,
    baseline_version: int,
    candidate_version: int | None = None,
) -> dict[str, Any]:
    """Compare two coordinator versions on the built-in benchmark."""
    baseline = run_benchmark(repo, version=baseline_version)
    candidate = run_benchmark(repo, version=candidate_version)
    return {
        "baseline": asdict(baseline),
        "candidate": asdict(candidate),
        "score_delta": candidate.average_score - baseline.average_score,
        "passed_rate_delta": candidate.passed_rate - baseline.passed_rate,
        "metric_deltas": {
            name: candidate.mean_metrics.get(name, 0.0) - baseline.mean_metrics.get(name, 0.0)
            for name in sorted(set(baseline.mean_metrics) | set(candidate.mean_metrics))
        },
    }
