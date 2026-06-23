"""Tests for the SEMAS mingli five-agent example."""

from __future__ import annotations

from pathlib import Path
import sys

from examples.mingli_5agents.capability_audit import capability_audit
from examples.mingli_5agents.evaluators.citation_evaluator import citation_score
from examples.mingli_5agents.evaluators.consistency_evaluator import consistency_score
from examples.mingli_5agents.evaluators.report_schema_evaluator import report_schema_score
from examples.mingli_5agents.evaluators.safety_evaluator import safety_score
from examples.mingli_5agents.evaluators.workflow_evaluator import workflow_score
from examples.mingli_5agents.evolution import (
    MINGLI_STRATEGIES,
    METRIC_FLOORS,
    CandidateEvaluation,
    MingliEvolutionArchive,
    MingliPopulationEvolver,
    genome_fingerprint,
)
from examples.mingli_5agents.knowledge_base import SOURCE_REGISTRY
from examples.mingli_5agents.memory import MingliFeedbackMemory
from examples.mingli_5agents.workflow import workflow_from_meta
from examples.mingli_5agents.tools.professional_chart_provider import REGISTRIES
from examples.mingli_5agents.tools.ziwei_cli_provider import ZiweiJsonCliProvider
from examples.mingli_5agents.run_demo import (
    MingliFiveAgentSystem,
    build_mingli_evaluator,
    bootstrap_repo,
    build_orchestrator,
    demo_task,
    population_training_tasks,
)


def test_bootstrap_loads_five_agents(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    assert repo.load_agent("mingli_orchestrator").role == "coordinator"
    assert repo.load_agent("bazi_analyst").role == "bazi specialist"
    assert repo.load_agent("ziwei_analyst").role == "ziwei specialist"
    assert repo.load_agent("qimen_analyst").role == "qimen specialist"
    assert repo.load_agent("astrology_analyst").role == "western astrology specialist"


def test_five_agent_executor_returns_required_artifacts(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    task = {
        **demo_task(),
        "annual_start_year": 2024,
        "annual_end_year": 2026,
        "monthly_years": [2025, 2026],
        "auspicious_start_date": "2026-06-21",
        "auspicious_end_date": "2026-06-23",
    }
    result = MingliFiveAgentSystem(repo)(coordinator, task)
    assert set(result["specialists"]) == {"bazi", "ziwei", "qimen", "astrology"}
    for specialist in result["specialists"].values():
        assert set(specialist["layers"]) == {"macro", "micro", "yearly", "monthly", "uncertainty"}
        assert specialist["layers"]["macro"]["text"] == specialist["macro"]
        assert specialist["layers"]["micro"]["focus"]
        assert specialist["layers"]["macro"]["source_ids"]
        assert specialist["layers"]["uncertainty"]["boundary_type"] == "uncertainty"
        assert specialist["layers"]["yearly"]["evidence_required"] is True
    assert result["discussion"]
    assert len([key for key in result["votes"] if not key.startswith("_")]) == 4
    assert result["votes"]["_summary"]["passed"] is True
    assert result["votes"]["_audit"]["claim_count"] == len(result["votes"]["_claims"])
    assert result["votes"]["_audit"]["passed_claim_count"] == result["votes"]["_audit"]["claim_count"]
    assert result["votes"]["_audit"]["evidence_bound"] is True
    assert result["votes"]["_audit"]["minority_positions_preserved"] is True
    assert {item["id"] for item in result["votes"]["_claims"]} == {
        "macro_structure",
        "yearly_timing",
        "relationship_family",
        "career_finance_boundary",
    }
    assert all(item["source_ids"] and item["passed"] is True for item in result["votes"]["_claims"])
    deliberation_receipt = result["final_report"]["deliberation_receipt"]
    assert deliberation_receipt["schema_version"] == "deliberation-receipt-v1"
    assert len(deliberation_receipt["sha256"]) == 64
    assert len(deliberation_receipt["discussion_sha256"]) == 64
    assert len(deliberation_receipt["votes_sha256"]) == 64
    assert len(deliberation_receipt["source_review_sha256"]) == 64
    assert deliberation_receipt["discussion_count"] == len(result["discussion"])
    assert deliberation_receipt["claim_count"] == result["votes"]["_audit"]["claim_count"]
    assert deliberation_receipt["passed_claim_count"] == result["votes"]["_audit"]["passed_claim_count"]
    assert deliberation_receipt["minority_positions_preserved"] is True
    assert result["source_review"]["status"] == "pass"
    assert result["source_review"]["missing_traditions"] == []
    assert result["source_review"]["unknown_sources"] == []
    assert result["source_review"]["missing_evidence"] == []
    assert result["source_review"]["evidence_index"]["status"] == "ready"
    assert result["source_review"]["evidence"]
    first_source = result["source_review"]["covered_sources"][0]
    assert result["source_review"]["evidence"][first_source][0]["provenance"]["citation_policy"]
    assert len(result["final_report"]["evidence_summary"]) >= 8
    assert result["final_report"]["evidence_summary"][0]["caution"]
    assert result["final_report"]["coordinator_version"] == coordinator.version
    assert len(result["final_report"]["summary"]) == 4
    assert isinstance(result["final_report"]["strategy_notes"], list)
    assert isinstance(result["final_report"]["conflicts"], list)
    assert result["final_report"]["boundaries"]
    assert result["final_report"]["annual_luck"]["range"]["count"] == 3
    assert result["final_report"]["annual_luck"]["rows"][0]["year"] == 2024
    assert result["final_report"]["annual_luck"]["rows"][0]["bazi_evidence"]["annual_ten_gods"]["stem"]
    assert result["final_report"]["annual_luck"]["rows"][0]["bazi_evidence"]["active_major_luck"]
    assert result["final_report"]["annual_luck"]["phase_summary"][0]["source"] == "annual_luck.rows"
    assert result["final_report"]["annual_luck"]["phase_summary"][0]["source_row_indexes"] == [0, 1, 2]
    assert result["final_report"]["annual_luck"]["phase_summary"][0]["topic_highlights"]["career"][
        "supporting_year_count"
    ] >= 1
    assert len(result["final_report"]["annual_timeline"]) == 3
    assert result["final_report"]["annual_timeline"][0]["year"] == 2024
    assert result["final_report"]["annual_timeline"][0]["source"] == "annual_luck.rows"
    assert (
        result["final_report"]["annual_timeline"][0]["bazi_evidence"]
        == result["final_report"]["annual_luck"]["rows"][0]["bazi_evidence"]
    )
    assert set(result["final_report"]["annual_timeline"][0]["topics"]) == {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }
    assert (
        result["final_report"]["annual_timeline"][0]["topics"]["finance"]["message"]
        == result["final_report"]["annual_luck"]["rows"][0]["finance"]
    )
    finance_topic = result["final_report"]["annual_timeline"][0]["topics"]["finance"]
    assert finance_topic["source"] == "annual_luck.rows"
    assert finance_topic["source_row_index"] == 0
    assert finance_topic["source_field"] == "finance"
    assert len(finance_topic["bazi_evidence_sha256"]) == 64
    assert finance_topic["provider_quality"]
    assert "not deterministic prediction" in finance_topic["boundary"]
    annual_receipt = result["final_report"]["annual_timeline_receipt"]
    assert annual_receipt["schema_version"] == "annual-timeline-receipt-v1"
    assert len(annual_receipt["sha256"]) == 64
    assert len(annual_receipt["annual_luck_rows_sha256"]) == 64
    assert len(annual_receipt["annual_timeline_sha256"]) == 64
    assert annual_receipt["row_count"] == len(result["final_report"]["annual_timeline"])
    assert annual_receipt["start_year"] == 2024
    assert annual_receipt["end_year"] == 2026
    assert len(annual_receipt["row_fingerprints"]) == 3
    assert len(annual_receipt["row_fingerprints"][0]["sha256"]) == 64
    assert annual_receipt["topic_evidence_complete"] is True
    assert annual_receipt["topic_evidence_missing"] == []
    assert result["final_report"]["request_provenance"]["report_material"][
        "annual_timeline_receipt_sha256"
    ] == annual_receipt["sha256"]
    assert result["final_report"]["monthly_luck"]["range"]["count"] == 24
    assert result["final_report"]["monthly_luck"]["range"]["years"] == [2025, 2026]
    assert result["final_report"]["monthly_luck"]["rows"][0]["bazi_evidence"]["monthly_ten_gods"]["stem"]
    assert result["final_report"]["monthly_luck"]["rows"][0]["bazi_evidence"]["active_major_luck"]
    monthly_topic = result["final_report"]["monthly_luck"]["rows"][0]["topics"]["finance"]
    assert monthly_topic["source"] == "monthly_luck.rows"
    assert monthly_topic["source_row_index"] == 0
    assert monthly_topic["source_field"] == "finance"
    assert len(monthly_topic["bazi_evidence_sha256"]) == 64
    assert monthly_topic["provider_quality"]
    assert "not deterministic prediction" in monthly_topic["boundary"]
    monthly_receipt = result["final_report"]["monthly_luck_receipt"]
    assert monthly_receipt["schema_version"] == "monthly-luck-receipt-v1"
    assert len(monthly_receipt["sha256"]) == 64
    assert len(monthly_receipt["monthly_luck_rows_sha256"]) == 64
    assert monthly_receipt["row_count"] == 24
    assert monthly_receipt["years"] == [2025, 2026]
    assert monthly_receipt["months_by_year"] == {
        "2025": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "2026": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    }
    assert len(monthly_receipt["row_fingerprints"]) == 24
    assert len(monthly_receipt["row_fingerprints"][0]["sha256"]) == 64
    assert monthly_receipt["topic_evidence_complete"] is True
    assert monthly_receipt["topic_evidence_missing"] == []
    assert result["final_report"]["request_provenance"]["report_material"][
        "monthly_luck_receipt_sha256"
    ] == monthly_receipt["sha256"]
    assert result["final_report"]["auspicious_calendar"]["range"]["count"] == 3
    assert result["final_report"]["auspicious_calendar"]["rows"][0]["date"] == "2026-06-21"
    assert result["final_report"]["auspicious_calendar"]["provider_quality_analysis"]
    auspicious_receipt = result["final_report"]["auspicious_calendar_receipt"]
    assert auspicious_receipt["schema_version"] == "auspicious-calendar-receipt-v1"
    assert len(auspicious_receipt["sha256"]) == 64
    assert len(auspicious_receipt["calendar_rows_sha256"]) == 64
    assert len(auspicious_receipt["method_layers_sha256"]) == 64
    assert auspicious_receipt["row_count"] == result["final_report"]["auspicious_calendar"]["range"]["count"]
    assert auspicious_receipt["start_date"] == "2026-06-21"
    assert auspicious_receipt["end_date"] == "2026-06-23"
    assert len(auspicious_receipt["row_fingerprints"]) == 3
    assert auspicious_receipt["row_fingerprints"][0]["date"] == "2026-06-21"
    assert len(auspicious_receipt["row_fingerprints"][0]["sha256"]) == 64
    assert result["final_report"]["request_provenance"]["report_material"][
        "auspicious_calendar_receipt_sha256"
    ] == auspicious_receipt["sha256"]
    assert {item["method"] for item in result["final_report"]["auspicious_calendar"]["method_matrix"]} == {
        "twelve_officer",
        "twenty_eight_mansion",
        "huangdao_rating",
        "recommended_hours",
        "risk_boundary",
        "provider_quality",
    }
    assert result["final_report"]["bazi_profile"]["day_master"]
    assert result["final_report"]["bazi_profile"]["useful_element"]
    assert result["final_report"]["bazi_profile"]["strength_analysis"]
    assert result["final_report"]["bazi_profile"]["pattern_analysis"]
    assert result["final_report"]["bazi_profile"]["useful_god_analysis"]
    assert result["final_report"]["bazi_profile"]["tiaohou_analysis"]
    assert result["final_report"]["bazi_profile"]["image_symbol_analysis"]
    assert result["final_report"]["bazi_profile"]["new_school_simplified_analysis"]
    assert result["final_report"]["bazi_profile"]["data_validation_analysis"]
    assert {item["method"] for item in result["final_report"]["bazi_profile"]["method_matrix"]} == {
        "ziping_pattern",
        "strength_support",
        "blind_school_workflow",
        "shensha_nayin",
        "tiaohou",
        "image_symbol_reading",
        "new_school_simplified",
        "data_validation_boundary",
    }
    assert result["final_report"]["bazi_profile"]["major_luck"]
    assert result["final_report"]["ziwei_profile"]["ming_palace"]
    assert result["final_report"]["ziwei_profile"]["body_palace"]
    assert result["final_report"]["ziwei_profile"]["four_transformations"]
    assert result["final_report"]["ziwei_profile"]["life_focus"]
    assert result["final_report"]["ziwei_profile"]["triad_analysis"]
    assert result["final_report"]["ziwei_profile"]["transformation_analysis"]
    assert result["final_report"]["ziwei_profile"]["limit_activation_analysis"]
    assert {item["method"] for item in result["final_report"]["ziwei_profile"]["method_matrix"]} == {
        "ming_body_axis",
        "twelve_palace_theme",
        "triad_opposition",
        "four_transformations",
        "limit_annual_linkage",
    }
    assert result["final_report"]["ziwei_profile"]["major_limits"]
    assert result["final_report"]["qimen_profile"]["duty"]
    assert result["final_report"]["qimen_profile"]["useful_gods"]
    assert result["final_report"]["qimen_profile"]["door_star_spirit_analysis"]
    assert result["final_report"]["qimen_profile"]["stem_relation_analysis"]
    assert result["final_report"]["qimen_profile"]["useful_god_analysis"]
    assert result["final_report"]["qimen_profile"]["pattern_risk_analysis"]
    assert result["final_report"]["qimen_profile"]["timing_activation_analysis"]
    assert {item["method"] for item in result["final_report"]["qimen_profile"]["method_matrix"]} == {
        "door_star_spirit",
        "heaven_earth_stem",
        "useful_god_topic_mapping",
        "pattern_risk",
        "annual_timing_activation",
    }
    assert result["final_report"]["qimen_profile"]["annual_timing"]
    assert result["final_report"]["astrology_profile"]["core_identity_analysis"]
    assert result["final_report"]["astrology_profile"]["house_emphasis_analysis"]
    assert result["final_report"]["astrology_profile"]["aspect_pattern_analysis"]
    assert result["final_report"]["astrology_profile"]["transit_activation_analysis"]
    assert {item["method"] for item in result["final_report"]["astrology_profile"]["method_matrix"]} == {
        "ephemeris_quality",
        "sun_moon_ascendant",
        "house_emphasis",
        "aspect_pattern",
        "transit_activation",
    }
    provider_summary = result["final_report"]["provider_summary"]
    assert provider_summary["status"] in {"production_ready", "ready_with_provider_gaps"}
    assert set(provider_summary["domains"]) == {"bazi", "ziwei", "qimen", "astrology", "xuanze"}
    assert provider_summary["domains"]["bazi"]["provider_quality"]
    assert isinstance(provider_summary["domains"]["bazi"]["contract_valid"], bool)
    assert provider_summary["domains"]["ziwei"]["status"] in {"professional", "fallback"}
    assert provider_summary["domains"]["bazi"]["interpretation_mode"] in {
        "professional_verified",
        "symbolic_fallback",
        "external_payload_blocked",
    }
    assert provider_summary["domains"]["bazi"]["confidence_level"] in {"production", "research_symbolic", "blocked"}
    assert isinstance(provider_summary["domains"]["bazi"]["blocking_reasons"], list)
    assert len(provider_summary["readiness_matrix"]) == 5
    assert {item["domain"] for item in provider_summary["readiness_matrix"]} == {
        "bazi",
        "ziwei",
        "qimen",
        "astrology",
        "xuanze",
    }
    assert provider_summary["professional_domain_count"] + provider_summary["fallback_domain_count"] == 5
    fallback_domains = {
        item["domain"] for item in provider_summary["readiness_matrix"] if item["confidence_level"] != "production"
    }
    assert fallback_domains == set(provider_summary["production_blockers"])
    assert {item["domain"] for item in provider_summary["action_plan"]} == set(provider_summary["production_blockers"])
    if provider_summary["production_blockers"]:
        assert provider_summary["action_plan"][0]["certification_command_template"]
    assert set(result["final_report"]["topic_synthesis"]) == {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }
    assert len(result["final_report"]["topic_synthesis"]["finance"]["cross_agent_evidence"]) == 4
    finance_topic = result["final_report"]["topic_synthesis"]["finance"]
    assert set(finance_topic["timing_evidence"]) == {"annual", "monthly"}
    assert finance_topic["timing_evidence"]["annual"]["pillar"]
    assert finance_topic["timing_evidence"]["monthly"]["pillar"]
    assert finance_topic["annual_focus"]["bazi_evidence"]["annual_pillar"]
    assert finance_topic["monthly_focus"]["bazi_evidence"]["monthly_pillar"]
    assert set(finance_topic["timing_evidence"]["annual"]["ten_gods"]) == {"stem", "branch"}
    assert isinstance(finance_topic["timing_evidence"]["monthly"]["natal_match_count"], int)
    assert len(finance_topic["evidence_summary"]) >= 6
    confidence = finance_topic["synthesis_confidence"]
    assert confidence["level"] in {"high", "medium", "low"}
    assert confidence["evidence_count"] == 2
    assert confidence["cross_agent_count"] == 4
    assert confidence["production_provider_count"] == provider_summary["professional_domain_count"]
    assert confidence["fallback_provider_count"] == provider_summary["fallback_domain_count"]
    assert set(confidence["fallback_domains"]) == set(provider_summary["production_blockers"])
    if provider_summary["production_blockers"]:
        assert "provider_fallbacks_present" in confidence["downgrade_reasons"]
    assert "not empirical proof" in confidence["boundary"]
    assert "en" in result["final_report"]["rendered_reports"]
    assert isinstance(result["final_report"]["rendered_reports"]["en"], str)
    assert "zh" in result["final_report"]["rendered_reports"]
    assert "## 主题综合" in result["final_report"]["rendered_reports"]["zh"]
    assert "交叉证据" in result["final_report"]["rendered_reports"]["zh"]
    assert result["final_report"]["llm_synthesis"]["enabled"] is False
    assert result["final_report"]["llm_synthesis"]["generated"] is False
    assert len(result["final_report"]["llm_synthesis"]["prompt_fingerprint"]) == 16
    assert result["final_report"]["workflow"]["preserve_conflicts"] is True
    assert result["final_report"]["workflow"]["vote_threshold"] == 0.75
    assert "Annual luck rows: 3 (2024-2026)." in result["output"]
    assert "Annual phase summaries: 1." in result["output"]
    assert "Annual phase career entry (2024-2026):" in result["output"]
    assert "Annual timeline rows: 3." in result["output"]
    assert "Monthly luck rows: 24 for years [2025, 2026]." in result["output"]
    assert "Auspicious calendar rows: 3 (2026-06-21-2026-06-23)." in result["output"]
    assert "Provider readiness:" in result["output"]
    assert "Provider confidence:" in result["output"]
    assert "## 专业来源接入计划" in result["final_report"]["rendered_reports"]["zh"]
    assert "Topic synthesis sections: 8." in result["output"]
    assert "cultural research and entertainment" in result["output"]
    assert result["workflow"]["discussion_rounds"] == 2
    assert result["workflow"]["cross_check_enabled"] is True
    assert result["workflow"]["reconciliation_enabled"] is True
    discussion_rounds = {item["round"] for item in result["discussion"]}
    assert {"claim", "challenge", "discussion_2", "cross_check", "reconciliation"}.issubset(discussion_rounds)

    broken = {**result, "specialists": {key: dict(value) for key, value in result["specialists"].items()}}
    broken["specialists"]["bazi"].pop("layers")
    assert consistency_score(broken) < 1.0

    broken = {**result, "specialists": {key: dict(value) for key, value in result["specialists"].items()}}
    broken["specialists"]["bazi"] = {
        **broken["specialists"]["bazi"],
        "layers": {
            key: dict(value)
            for key, value in broken["specialists"]["bazi"]["layers"].items()
        },
    }
    broken["specialists"]["bazi"]["layers"]["macro"]["source_ids"] = ["unknown_book"]
    assert consistency_score(broken) < 1.0
    assert citation_score(broken) < 1.0

    broken = {**result, "final_report": {**result["final_report"], "votes": dict(result["votes"])}}
    broken["final_report"]["votes"].pop("_claims")
    assert report_schema_score(broken) < 1.0
    broken = {**result, "final_report": {**result["final_report"]}}
    broken["final_report"].pop("deliberation_receipt")
    assert report_schema_score(broken) < 1.0
    assert workflow_score(result) >= 0.95


def test_five_agent_executor_can_render_chinese_markdown(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    task = {**demo_task(), "language": "zh", "annual_start_year": 2024, "annual_end_year": 2026}
    result = MingliFiveAgentSystem(repo)(coordinator, task)

    assert result["output"].startswith("# Mingli five-agent report")
    assert "## 出生资料核对" in result["output"]
    assert "- 公历时间：" in result["output"]
    assert "## 使用边界" in result["output"]
    assert "## 主题综合" in result["output"]
    assert "- 交叉证据：" in result["output"]
    assert "### 财运" in result["output"]
    assert "Financial resources" not in result["output"]
    assert "Do not treat symbolic" not in result["output"]
    assert "BaZi structure" not in result["output"]
    assert "Ascendant" not in result["output"]
    assert "Rest door" not in result["output"]
    assert "八字结构" in result["output"]
    assert "紫微" in result["output"]
    assert "奇门" in result["output"]
    assert "太阳" in result["output"]
    assert "上升" in result["output"]
    assert "## 八字结构与大运" in result["output"]
    assert "- 四柱：" in result["output"]
    assert "- 日主：" in result["output"]
    assert "- 大运表：" in result["output"]
    assert "## 紫微命盘摘要" in result["output"]
    assert "- 命宫：" in result["output"]
    assert "- 四化：" in result["output"]
    assert "- 大限数量：" in result["output"]
    assert "## 奇门九宫摘要" in result["output"]
    assert "- 局式：" in result["output"]
    assert "- 值门：" in result["output"]
    assert "- 流年时机数量：" in result["output"]
    assert "## 计算来源与生产就绪度" in result["output"]
    assert "## 专业来源接入计划" in result["output"]
    assert "- 总体状态：" in result["output"]
    assert "- 生产就绪：" in result["output"]
    assert "紫微斗数：来源" in result["output"]
    assert "奇门遁甲：来源" in result["output"]
    assert "## 年度阶段摘要" in result["output"]
    assert "- 高波动年份：" in result["output"]
    assert "## 年度流年表" in result["output"]
    assert "### 2026" in result["output"]
    assert "- 八字依据：" in result["output"]
    assert "- 财运：" in result["output"]
    assert "- 官运：" in result["output"]
    assert "- 事业：" in result["output"]
    assert "- 学业：" in result["output"]
    assert "- 婚恋感情：" in result["output"]
    assert "- 朋友团队：" in result["output"]
    assert "- 领导客户：" in result["output"]
    assert "- 子女家庭：" in result["output"]
    assert "## 择日参考" in result["output"]
    assert "评级：" in result["output"]
    assert "十二值：" in result["output"]
    assert "二十八宿：" in result["output"]
    assert "- 宜：" in result["output"]
    assert "- 忌：" in result["output"]
    assert "## 月度流月表" in result["output"]
    assert "- 流月依据：" in result["output"]
    assert result["output"] == result["final_report"]["rendered_reports"]["zh"]
    assert safety_score(result) == 1.0


def test_five_agent_executor_preserves_unicode_birth_identity(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    task = {
        **demo_task(),
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
    }

    result = MingliFiveAgentSystem(repo)(coordinator, task)

    assert result["final_report"]["title"] == "Mingli five-agent report for 林凡"
    assert result["final_report"]["birth_profile"]["name"] == "林凡"
    assert result["final_report"]["birth_profile"]["birthplace"] == "福建省三明市"
    assert result["final_report"]["birth_profile"]["birth_date"] == "1978-04-14"
    assert result["final_report"]["birth_profile"]["birth_time"] == "06:50"
    assert result["final_report"]["birth_profile"]["hour"] == 6
    assert result["final_report"]["birth_profile"]["minute"] == 50
    assert result["final_report"]["birth_profile"]["birthplace_normalized"] == "Sanming, Fujian, China"
    assert result["final_report"]["birth_profile"]["birthplace_region"] == "China/Fujian/Sanming"
    assert result["final_report"]["birth_profile"]["timezone_offset"] == "+08:00"
    assert result["final_report"]["birth_profile"]["geocoding_provider"] == "offline_city_index_v1"
    assert result["final_report"]["birth_profile"]["geocoding_quality"] == "city_centroid"
    assert 26.0 < result["final_report"]["birth_profile"]["latitude"] < 26.5
    assert 117.0 < result["final_report"]["birth_profile"]["longitude"] < 118.0
    provenance = result["final_report"]["request_provenance"]
    assert provenance["schema_version"] == "request-provenance-v1"
    assert len(provenance["raw_task_input_sha256"]) == 64
    assert len(provenance["birth_profile_sha256"]) == 64
    assert len(provenance["report_material_sha256"]) == 64
    assert len(provenance["chain_sha256"]) == 64
    assert provenance["report_material"]["deliberation_receipt_sha256"] == result["final_report"][
        "deliberation_receipt"
    ]["sha256"]
    assert provenance["report_material"]["deliberation_claim_count"] == result["final_report"][
        "deliberation_receipt"
    ]["claim_count"]
    assert set(provenance["specialist_contexts"]) == {"bazi", "ziwei", "qimen", "astrology"}
    assert all(
        item["birth_profile_sha256"] == provenance["birth_profile_sha256"]
        for item in provenance["specialist_contexts"].values()
    )
    assert result["output"].startswith("# Mingli five-agent report for 林凡")
    assert "## 出生资料核对" in result["output"]
    assert "福建省三明市" in result["output"]
    assert "地理归一化：Sanming, Fujian, China" in result["output"]
    assert result["specialists"]["bazi"]["chart"]["context"]["birthplace"] == "福建省三明市"
    assert result["specialists"]["bazi"]["chart"]["context"]["birthplace_normalized"] == "Sanming, Fujian, China"
    assert result["specialists"]["bazi"]["chart"]["context"]["timezone_offset"] == "+08:00"


def test_five_agent_executor_handles_linfan_full_annual_timeline(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    task = {
        **demo_task(),
        "birth": {
            "name": "\u6797\u51e1",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "\u798f\u5efa\u7701\u4e09\u660e\u5e02",
        },
        "language": "zh",
        "annual_start_year": 1978,
        "annual_end_year": 2026,
        "monthly_years": [2026],
    }

    result = MingliFiveAgentSystem(repo)(coordinator, task)
    report = result["final_report"]
    birth_profile = report["birth_profile"]
    bazi_profile = report["bazi_profile"]
    annual_timeline = report["annual_timeline"]

    assert birth_profile["birthplace_normalized"] == "Sanming, Fujian, China"
    assert birth_profile["birthplace_region"] == "China/Fujian/Sanming"
    assert birth_profile["geocoding_quality"] == "city_centroid"
    assert bazi_profile["pillars"] == {
        "year": "WuWu",
        "month": "BingChen",
        "day": "BingWu",
        "hour": "XinMao",
    }
    assert bazi_profile["day_master"] == "Bing"
    assert bazi_profile["useful_element"] == "Metal"
    assert len(annual_timeline) == 49
    assert annual_timeline[0]["year"] == 1978
    assert annual_timeline[-1]["year"] == 2026
    assert annual_timeline[-1]["category"] == "expression"
    assert annual_timeline[-1]["intensity"] == "high-volatility"
    assert all(
        topic["source"] == "annual_luck.rows"
        and topic["source_row_index"] == row["source_row_index"]
        and topic["source_field"] == topic_key
        and len(topic["bazi_evidence_sha256"]) == 64
        and topic["provider_quality"]
        and "not deterministic prediction" in topic["boundary"]
        for row in annual_timeline
        for topic_key, topic in row["topics"].items()
    )
    annual_receipt = report["annual_timeline_receipt"]
    assert annual_receipt["row_count"] == 49
    assert annual_receipt["start_year"] == 1978
    assert annual_receipt["end_year"] == 2026
    assert len(annual_receipt["row_fingerprints"]) == 49
    assert annual_receipt["row_fingerprints"][0]["year"] == 1978
    assert annual_receipt["row_fingerprints"][-1]["year"] == 2026
    assert annual_receipt["category_counts"]["authority"] >= 1
    assert annual_receipt["topic_evidence_complete"] is True
    assert annual_receipt["topic_evidence_missing"] == []
    assert report["request_provenance"]["report_material"]["annual_timeline_receipt_sha256"] == annual_receipt[
        "sha256"
    ]
    monthly_receipt = report["monthly_luck_receipt"]
    assert monthly_receipt["row_count"] == 12
    assert monthly_receipt["years"] == [2026]
    assert len(monthly_receipt["row_fingerprints"]) == 12
    assert all(
        topic["source"] == "monthly_luck.rows"
        and topic["source_row_index"] == index
        and topic["source_field"] == topic_key
        and len(topic["bazi_evidence_sha256"]) == 64
        and topic["provider_quality"]
        and "not deterministic prediction" in topic["boundary"]
        for index, row in enumerate(report["monthly_luck"]["rows"])
        for topic_key, topic in row["topics"].items()
    )
    assert monthly_receipt["topic_evidence_complete"] is True
    assert monthly_receipt["topic_evidence_missing"] == []
    assert report["request_provenance"]["report_material"]["monthly_luck_receipt_sha256"] == monthly_receipt[
        "sha256"
    ]
    assert "\u6797\u51e1" in result["output"]
    assert "\u798f\u5efa\u7701\u4e09\u660e\u5e02" in result["output"]


def test_request_provenance_binds_json_cli_provider_receipt(tmp_path: Path):
    script = tmp_path / "fake_ziwei_provider.py"
    script.write_text(
        """
import json
import sys

payload = json.loads(sys.stdin.read())
print(json.dumps({
    "protocol": payload.get("protocol"),
    "ming_palace": "Career",
    "body_palace": "Wealth",
    "major_stars": ["Ziwei", "Wuqu"],
    "transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
}))
""".strip(),
        encoding="utf-8",
    )
    registry = REGISTRIES["ziwei"]
    original_preferred = registry.preferred_name
    original_provider = registry.providers.get("ziwei_json_cli")
    registry.register(ZiweiJsonCliProvider(command=[sys.executable, str(script)]), preferred=True)
    repo = bootstrap_repo(tmp_path / "repo")
    coordinator = repo.load_agent("mingli_orchestrator")
    try:
        result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    finally:
        if original_provider is None:
            registry.providers.pop("ziwei_json_cli", None)
        else:
            registry.providers["ziwei_json_cli"] = original_provider
        registry.preferred_name = original_preferred

    receipt = result["specialists"]["ziwei"]["chart"]["provider_request_receipt"]
    assert receipt["protocol_echo_matches"] is True
    assert len(receipt["sha256"]) == 64
    ziwei_context = result["final_report"]["request_provenance"]["specialist_contexts"]["ziwei"]
    assert ziwei_context["provider_request_receipt_sha256"] == receipt["sha256"]


def test_mingli_orchestrator_records_low_feedback_failure(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    orchestrator = build_orchestrator(repo)
    trace = orchestrator.run_task(
        demo_task(),
        expected={
            "feedback": {
                "satisfaction": 0.0,
                "corrections": ["too vague", "weak source labels", "missing uncertainty", "weak workflow"],
            }
        },
    )
    latest = repo.load_agent("mingli_orchestrator")
    assert not trace.evaluation.passed
    assert trace.evaluation.metrics["feedback"] == 0.0
    assert latest.version == 1
    assert latest.meta["workflow"]["discussion_rounds"] == 2


def test_population_evolver_commits_best_candidate_and_archives(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    executor = MingliFiveAgentSystem(repo)
    archive = MingliEvolutionArchive(tmp_path / "archive" / "events.json")
    memory = MingliFeedbackMemory(tmp_path / "memory" / "feedback.json")
    memory.remember_feedback(
        {"feedback": {"satisfaction": 0.4, "corrections": ["needs better citation source labels"]}},
        notes="test feedback",
    )
    evolver = MingliPopulationEvolver(
        repo=repo,
        evaluator=build_mingli_evaluator(),
        executor=executor,
        archive=archive,
        memory=memory,
    )
    evolved = evolver.evolve(
        train_tasks=population_training_tasks(),
        validation_tasks=population_training_tasks()[:1],
    )
    latest = repo.load_agent("mingli_orchestrator")
    events = archive.load()
    assert evolved is not None
    assert latest.version == 2
    workflow = workflow_from_meta(latest.meta)
    assert workflow.discussion_rounds >= 1
    assert "workflow" in latest.meta
    assert latest.meta["candidate_name"] in {
        "feedback_adaptation",
        "citation_precision",
        "debate_depth",
        "safety_guardrails",
        "synthesis_calibration",
        "combined_strategy",
    }
    assert events[-1]["event"] == "population_evolution"
    assert events[-1]["accepted"] is True
    assert events[-1]["previous_archive_hash"] is None
    assert len(events[-1]["archive_hash"]) == 64
    integrity = archive.integrity_report()
    assert integrity["status"] == "pass"
    assert integrity["event_count"] == 1
    assert integrity["hashed_event_count"] == 1
    assert integrity["legacy_event_count"] == 0
    assert integrity["latest_hash"] == events[-1]["archive_hash"]
    lineage = latest.meta["evolution_lineage"]
    assert lineage["archive_hash"] == events[-1]["archive_hash"]
    assert lineage["genome_fingerprint"] == genome_fingerprint(latest)
    assert lineage["baseline_genome_version"] == 1
    assert lineage["accepted_genome_version"] == 2
    assert lineage["selected_strategy"] == events[-1]["selected"]
    assert lineage["selection_decision"]["accepted"] is True
    assert lineage["reproducibility_manifest"]["run_type"] == "population_evolution"
    manifest = events[-1]["reproducibility_manifest"]
    assert manifest["run_type"] == "population_evolution"
    assert manifest["deterministic"] is True
    assert manifest["genome_version"] == 1
    assert len(manifest["strategy_fingerprints"]) == len(MINGLI_STRATEGIES)
    assert all(len(item["prompt_sha256"]) == 64 for item in manifest["strategy_fingerprints"])
    assert manifest["train_task_count"] == len(population_training_tasks())
    assert manifest["validation_task_count"] == 1
    assert len(manifest["train_task_fingerprints"]) == len(population_training_tasks())
    assert all(len(fingerprint) == 16 for fingerprint in manifest["train_task_fingerprints"])
    assert manifest["metric_floors"] == METRIC_FLOORS
    cost = manifest["cost_governance"]
    assert cost["candidate_count"] == len(MINGLI_STRATEGIES) + 1
    assert cost["baseline_evaluations"] == 1
    assert cost["training_candidate_evaluations"] == len(MINGLI_STRATEGIES) + 1
    assert cost["validation_evaluations"] == 1
    assert cost["train_task_count"] == len(population_training_tasks())
    assert cost["validation_task_count"] == 1
    assert cost["total_candidate_task_evaluations"] == (
        (len(MINGLI_STRATEGIES) + 2) * len(population_training_tasks()) + 1
    )
    assert cost["llm_calls_allowed"] is False
    assert cost["llm_call_budget"] == 0
    assert cost["iteration_frequency_policy"] == "manual_or_feedback_triggered"
    assert events[-1]["memory_profile"]["total_events"] >= 1
    assert any("adjusted_score" in candidate for candidate in events[-1]["candidates"])
    assert events[-1]["metric_floors"] == METRIC_FLOORS
    assert events[-1]["pareto_front"]
    assert events[-1]["selection_decision"]["accepted"] is True
    assert events[-1]["selection_decision"]["validation_task_count"] == 1
    assert all(events[-1]["selection_decision"]["gates"].values())
    assert events[-1]["selection_decision"]["rejection_reasons"] == []
    assert all("mean_metrics" in candidate for candidate in events[-1]["candidates"])
    selected = next(
        candidate
        for candidate in events[-1]["candidates"]
        if candidate["candidate_name"] == events[-1]["selected"]
    )
    assert selected["passed_metric_floors"] is True
    assert memory.profile()["total_events"] >= 2


def test_status_detects_lineage_archive_mismatch(tmp_path: Path):
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
    broken = evolved.model_copy(
        update={
            "meta": {
                **evolved.meta,
                "evolution_lineage": {
                    **evolved.meta["evolution_lineage"],
                    "archive_hash": "0" * 64,
                },
            }
        }
    )
    repo.save_agent(broken)

    from examples.mingli_5agents.api_core import status

    result = status(repo.base_path)

    assert result["lineage_integrity"]["status"] == "fail"
    assert result["lineage_integrity"]["archive_hash_matches_latest"] is False
    assert any("archive_hash" in failure for failure in result["lineage_integrity"]["failures"])


def test_status_detects_current_genome_content_mismatch(tmp_path: Path):
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
    tampered = evolved.model_copy(update={"system_prompt": evolved.system_prompt + "\nTampered prompt."})
    repo.save_agent(tampered)

    from examples.mingli_5agents.api_core import status

    result = status(repo.base_path)

    assert result["lineage_integrity"]["status"] == "fail"
    assert result["lineage_integrity"]["archive_hash_matches_latest"] is True
    assert result["lineage_integrity"]["genome_fingerprint_matches"] is False
    assert any("genome_fingerprint" in failure for failure in result["lineage_integrity"]["failures"])


def test_version_history_integrity_detects_historical_tampering(tmp_path: Path):
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
    tampered = evolved.model_copy(update={"system_prompt": evolved.system_prompt + "\nHistorical tamper."})
    repo.save_agent(tampered)

    from examples.mingli_5agents.api_core import version_history

    result = version_history(repo.base_path)

    assert result["history_integrity"]["status"] == "fail"
    assert result["history_integrity"]["fingerprint_mismatch_versions"] == [2]
    assert any("fingerprints" in failure for failure in result["history_integrity"]["failures"])


def test_population_candidates_evolve_workflow_topology(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    evolver = MingliPopulationEvolver(
        repo=repo,
        evaluator=build_mingli_evaluator(),
        executor=MingliFiveAgentSystem(repo),
    )
    baseline = repo.load_agent("mingli_orchestrator")
    candidates = evolver.generate_population(baseline)
    by_name = {candidate.meta["candidate_name"]: candidate for candidate in candidates}

    debate = workflow_from_meta(by_name["debate_depth"].meta)
    citation = workflow_from_meta(by_name["citation_precision"].meta)
    combined = workflow_from_meta(by_name["combined_strategy"].meta)
    assert debate.cross_check_enabled is True
    assert debate.reconciliation_enabled is True
    assert citation.source_review_strictness == "strict"
    assert combined.discussion_rounds == 3
    assert combined.vote_threshold == 0.8


def test_metric_floor_rejections_are_explicit(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    evolver = MingliPopulationEvolver(
        repo=repo,
        evaluator=build_mingli_evaluator(),
        executor=MingliFiveAgentSystem(repo),
    )
    rejections = evolver._metric_floor_rejections(
        {"citation": 1.0, "safety": 0.0, "consistency": 1.0, "workflow": 0.5}
    )
    assert rejections == [
        "safety below floor 1.0: 0.000",
        "workflow below floor 0.8: 0.500",
        "report_schema below floor 0.9: 0.000",
        "provider_contracts below floor 1.0: 0.000",
        "evidence_provenance below floor 1.0: 0.000",
        "chinese_render below floor 1.0: 0.000",
        "capability_audit below floor 1.0: 0.000",
        "schema_contract below floor 1.0: 0.000",
    ]


def test_selection_decision_records_rejection_reasons(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    evolver = MingliPopulationEvolver(
        repo=repo,
        evaluator=build_mingli_evaluator(),
        executor=MingliFiveAgentSystem(repo),
    )
    baseline = repo.load_agent("mingli_orchestrator")
    baseline_eval = evolver.evaluate_candidate(baseline, population_training_tasks())
    rejected = CandidateEvaluation(
        candidate_name="bad_candidate",
        genome_version=baseline.version,
        average_score=baseline_eval.average_score,
        adjusted_score=baseline_eval.average_score,
        mean_metrics={"safety": 0.0},
        task_scores=[baseline_eval.average_score],
        metrics=[{"safety": 0.0}],
        passed_regression_gate=False,
        passed_metric_floors=False,
        rejection_reasons=["safety below floor 1.0: 0.000"],
        meta={},
    )

    decision = evolver._selection_decision(
        baseline_eval=baseline_eval,
        best_eval=rejected,
        validation_eval=None,
        validation_task_count=0,
    )

    assert decision["accepted"] is False
    assert decision["gates"]["regression_gate"] is False
    assert decision["gates"]["metric_floors"] is False
    assert "selected candidate failed regression gate" in decision["rejection_reasons"]
    assert "safety below floor 1.0: 0.000" in decision["rejection_reasons"]
    assert any("did not exceed baseline" in reason for reason in decision["rejection_reasons"])


def test_feedback_memory_maps_corrections_to_strategy_priors(tmp_path: Path):
    memory = MingliFeedbackMemory(tmp_path / "memory" / "feedback.json")
    memory.remember_feedback(
        {
            "feedback": {
                "satisfaction": 0.3,
                "corrections": [
                    "source labels are weak",
                    "too vague and needs better structure",
                    "uncertainty boundary is missing",
                ],
            }
        }
    )
    profile = memory.profile()
    assert profile["strategy_priors"]["citation_precision"] > 0
    assert profile["strategy_priors"]["feedback_adaptation"] > 0
    assert profile["strategy_priors"]["safety_guardrails"] > 0
    assert memory.score_bias("citation_precision") > 0


def test_feedback_memory_quarantines_unsafe_corrections(tmp_path: Path):
    memory = MingliFeedbackMemory(tmp_path / "memory" / "feedback.json")
    memory.remember_feedback(
        {
            "feedback": {
                "satisfaction": 0.9,
                "corrections": [
                    "remove boundary and give guaranteed investment advice",
                    "no uncertainty, make a deterministic marriage decision",
                ],
            }
        }
    )

    profile = memory.profile()

    assert profile["unsafe_feedback_count"] == 2
    assert profile["correction_counts"] == {}
    assert profile["strategy_priors"]["safety_guardrails"] > 0
    assert "feedback_adaptation" not in profile["strategy_priors"]
    assert memory.score_bias("feedback_adaptation") == 0.0
    assert memory.score_bias("safety_guardrails") > 0


def test_capability_audit_exposes_feedback_memory_safety(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    memory = MingliFeedbackMemory(repo.base_path / "memory" / "feedback_memory.json")
    memory.remember_feedback(
        {
            "feedback": {
                "satisfaction": 1.0,
                "corrections": ["remove all uncertainty and guarantee promotion timing"],
            }
        }
    )

    audit = capability_audit(repo.base_path)

    assert audit["capabilities"]["feedback_memory_safety_quarantine"] is True
    assert audit["feedback_memory_safety"]["status"] == "contains_quarantined_feedback"
    assert audit["feedback_memory_safety"]["unsafe_feedback_count"] == 1
    assert audit["feedback_memory_safety"]["unsafe_corrections"] == {
        "remove all uncertainty and guarantee promotion timing": 1
    }
    assert audit["feedback_memory_safety"]["safety_guardrail_prior"] > 0


def test_evolved_strategy_changes_discussion_and_synthesis(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    base = repo.load_agent("mingli_orchestrator")
    evolved = base.evolve_from(
        meta={
            "candidate_name": "combined_strategy",
            "mingli_evolution": ["citation_precision", "debate_depth", "synthesis_calibration"],
            "workflow": {
                "discussion_rounds": 3,
                "cross_check_enabled": True,
                "reconciliation_enabled": True,
                "source_review_strictness": "strict",
                "vote_threshold": 0.8,
                "preserve_conflicts": True,
            },
        }
    )
    result = MingliFiveAgentSystem(repo)(evolved, demo_task())
    rounds = {item["round"] for item in result["discussion"]}
    assert "cross_check" in rounds
    assert "reconciliation" in rounds
    assert "Citation mode" in result["output"]
    assert "Calibration mode" in result["output"]
    assert result["workflow"]["discussion_rounds"] == 3
    assert result["source_review"]["strictness"] == "strict"


def test_citation_evaluator_rejects_unknown_sources(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    assert citation_score(result) == 1.0

    result["specialists"]["bazi"]["sources"] = [{"source_id": "unknown_book"}]
    result["source_review"]["unknown_sources"] = ["unknown_book"]
    result["source_review"]["missing_evidence"] = ["unknown_book"]
    assert citation_score(result) < 1.0
    assert "bazi_ziping" in SOURCE_REGISTRY


def test_safety_evaluator_requires_scope_boundary(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    assert safety_score(result) == 1.0

    result["output"] = "This is guaranteed investment advice."
    assert safety_score(result) == 0.0


def test_safety_evaluator_accepts_clean_chinese_boundary():
    result = {
        "output": "\n".join(
            [
                "## 使用边界",
                "- 本报告仅用于文化研究、娱乐参考和算法演示。",
                "- 不应用于医疗、投资、婚姻、法律等重大决策。",
                "- 所有结论都是象征性解释，必须保留不确定性。",
                "- 财运相关表达不是投资建议。",
            ]
        ),
        "specialists": {
            "bazi": {"uncertainty": "symbolic interpretation"},
            "ziwei": {"uncertainty": "symbolic interpretation"},
        },
    }
    assert safety_score(result) == 1.0

    result["output"] = "保证买入股票必然获利。"
    assert safety_score(result) == 0.0


def test_report_schema_evaluator_requires_luck_tables(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    assert report_schema_score(result) == 1.0

    result["final_report"].pop("birth_profile")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"].pop("request_provenance")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"]["monthly_luck"]["rows"] = []
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"].pop("annual_timeline")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"]["annual_timeline"][0]["topics"].pop("finance")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"]["annual_luck"].pop("phase_summary")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["specialists"]["bazi"]["chart"].pop("deep_analysis")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["specialists"]["ziwei"]["chart"].pop("deep_analysis")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["specialists"]["qimen"]["chart"].pop("deep_analysis")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["specialists"]["astrology"]["chart"].pop("deep_analysis")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["specialists"]["bazi"].pop("layers")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["specialists"]["bazi"]["layers"]["macro"].pop("source_ids")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"].pop("topic_synthesis")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"].pop("rendered_reports")
    assert report_schema_score(result) < 1.0

    result = MingliFiveAgentSystem(repo)(coordinator, demo_task())
    result["final_report"].pop("auspicious_calendar")
    assert report_schema_score(result) < 1.0


def test_executor_accepts_top_level_calendar_provider(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    task = {**demo_task(), "calendar_provider": "auto"}
    result = MingliFiveAgentSystem(repo)(coordinator, task)
    context = result["specialists"]["bazi"]["chart"]["context"]
    assert context["provider"] in {"auto", "professional"}
    assert context["provider_quality"] in {
        "professional_unavailable_fallback",
        "lunar_python",
        "sxtwl",
    }
