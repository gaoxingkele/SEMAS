"""Tests for reference chart provider-contract checks."""

from __future__ import annotations

from examples.mingli_5agents.evaluators.provider_contract_evaluator import (
    provider_contract_score,
    provider_report_governance_checks,
)
from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, bootstrap_repo, population_training_tasks
from examples.mingli_5agents.reference_charts import reference_chart_cases, run_reference_chart_checks


def test_reference_chart_checks_pass_and_cover_provider_contracts():
    cases = reference_chart_cases()
    assert {case.name for case in cases} == {
        "external_structured_provider_contract",
        "professional_bazi_contract",
        "xuanze_almanac_contract",
    }

    result = run_reference_chart_checks()
    assert result["passed"] is True
    assert result["passed_count"] == result["total"] == 3
    assert result["method_coverage"]["passed"] is True
    assert set(result["method_coverage"]["domains"]) == {"bazi", "ziwei", "qimen", "astrology", "xuanze"}
    for item in result["method_coverage"]["domains"].values():
        assert item["missing"] == []
        assert item["observed"] == item["required"]
    checked = {case["name"]: case for case in result["cases"]}
    assert checked["external_structured_provider_contract"]["checked_domains"] == [
        "astrology",
        "bazi",
        "qimen",
        "xuanze",
        "ziwei",
    ]
    assert checked["external_structured_provider_contract"]["method_coverage"]["bazi"]
    assert checked["external_structured_provider_contract"]["method_coverage"]["ziwei"]
    assert checked["external_structured_provider_contract"]["method_coverage"]["qimen"]
    assert checked["external_structured_provider_contract"]["method_coverage"]["astrology"]
    assert checked["external_structured_provider_contract"]["method_coverage"]["xuanze"]
    assert checked["external_structured_provider_contract"]["provenance_coverage"] == {
        "astrology": True,
        "bazi": True,
        "qimen": True,
        "xuanze": True,
        "ziwei": True,
    }
    assert checked["professional_bazi_contract"]["checked_domains"] == ["bazi"]
    assert checked["xuanze_almanac_contract"]["checked_domains"] == ["xuanze"]
    assert provider_contract_score({}, None) == 1.0


def test_provider_contract_score_checks_actual_report_governance(tmp_path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(coordinator, population_training_tasks()[0]["input"])

    checks = provider_report_governance_checks(result)
    assert checks["skipped"] is False
    assert checks["passed"] is True
    assert checks["score"] == 1.0
    assert provider_contract_score(result, None) == 1.0

    broken = {
        **result,
        "final_report": {
            **result["final_report"],
            "provider_summary": {
                **result["final_report"]["provider_summary"],
                "production_blockers": [],
                "domains": {
                    **result["final_report"]["provider_summary"]["domains"],
                    "ziwei": {
                        **result["final_report"]["provider_summary"]["domains"]["ziwei"],
                        "replacement_boundary": "",
                    },
                },
            },
        },
    }

    broken_checks = provider_report_governance_checks(broken)
    assert broken_checks["passed"] is False
    assert "ziwei.replacement_boundary required for fallback providers" in broken_checks["failures"]
    assert any("production_blockers must match fallback domains" in failure for failure in broken_checks["failures"])
    assert provider_contract_score(broken, None) < 1.0
