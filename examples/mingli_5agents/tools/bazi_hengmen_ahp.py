"""格局横门断 AHP 评分器。

该模块把《格局横门断》抽取出的“月令取格、成败救应、事实筛选”
逻辑转成可审计的层次化评分。它不声称证明命理真伪，只用于比较
不同时辰候选对已知事件的解释力。
"""

from __future__ import annotations

from typing import Any

from examples.mingli_5agents.tools.hengmen_rule_engine import score_hengmen_timing


# 权重说明：event_ten_god 只看事件类型与流年十神（日主口径），对 12 个时辰候选
# 是常数、零区分度，由 0.16 降到 0.10；palace_trigger 颗粒度粗（任意支关系落到
# 目标宫位即计分），在 11 案例回测中与参考时辰负相关，由 0.12 降到 0.06；
# success_rescue 是横门断“成败救应”核心、候选间区分度最大，由 0.18 提到 0.24；
# fact_calibration 是“事实年份筛选强断”的闸门，配合反例惩罚通道由 0.04 提到 0.10。
# 总和保持 1.0。
AHP_WEIGHTS = {
    "month_pattern": 0.18,
    "stem_root": 0.14,
    "success_rescue": 0.24,
    "event_ten_god": 0.10,
    "palace_trigger": 0.06,
    "luck_support": 0.10,
    "annual_interaction": 0.08,
    "fact_calibration": 0.10,
}


EVENT_TEN_GOD_TARGETS = {
    "study_exam": {"resource", "authority", "expression"},
    "career_launch": {"expression", "authority", "wealth"},
    "role_power": {"authority", "resource"},
    "role_transition": {"authority", "expression", "friends"},
    "business_power": {"wealth", "expression", "authority"},
    "relationship": {"wealth", "authority", "peer"},
    "movement": {"authority", "expression", "friends"},
    "public_visibility": {"expression", "authority"},
    "health_pressure": {"resource", "authority", "peer"},
    "scandal": {"authority", "expression", "peer"},
    "family": {"wealth", "resource", "peer"},
    "family_loss": {"wealth", "resource", "authority"},
    "death": {"authority", "resource", "expression"},
    "award_peak": {"authority", "resource", "expression"},
    "box_office_breakthrough": {"wealth", "expression", "authority"},
    "iconic_role": {"expression", "authority"},
    "career_reinvention": {"expression", "authority", "resource"},
    "public_scandal": {"authority", "expression", "peer"},
    "health_crisis": {"resource", "authority"},
}


EVENT_PALACE_TARGETS = {
    "study_exam": {"month", "year"},
    "career_launch": {"month", "hour"},
    "role_power": {"year", "month"},
    "role_transition": {"month", "hour"},
    "business_power": {"month", "hour"},
    "relationship": {"day", "hour"},
    "movement": {"year", "month", "hour"},
    "public_visibility": {"year", "month", "hour"},
    "health_pressure": {"day", "hour"},
    "scandal": {"year", "month", "day"},
    "family": {"year", "day", "hour"},
    "family_loss": {"year", "day", "hour"},
    "death": {"day", "hour"},
    "award_peak": {"year", "month"},
    "box_office_breakthrough": {"year", "month", "hour"},
    "iconic_role": {"year", "month", "hour"},
    "career_reinvention": {"month", "hour"},
    "public_scandal": {"year", "month", "day"},
    "health_crisis": {"day", "hour"},
}
DISRUPTIVE_EVENT_TYPES = {"family_loss", "death", "health_crisis", "health_pressure", "public_scandal", "scandal"}

AHP_CRITERIA = (
    "month_pattern", "stem_root", "success_rescue", "event_ten_god",
    "palace_trigger", "luck_support", "annual_interaction", "fact_calibration",
)

TEN_GOD_THEMES = {
    "direct_officer": "authority", "seven_killings": "authority",
    "direct_wealth": "wealth", "indirect_wealth": "wealth",
    "direct_resource": "resource", "indirect_resource": "resource",
    "food_god": "expression", "hurting_officer": "expression",
    "peer": "peer", "friends": "peer",
}


def build_hengmen_chart_strategy(bazi: dict[str, Any]) -> dict[str, Any]:
    """Score original chart structure using Hengmen AHP chart-side criteria."""
    deep = bazi.get("deep_analysis", {}) if isinstance(bazi, dict) else {}
    context = bazi.get("context", {}) if isinstance(bazi, dict) else {}
    natal = deep.get("hengmen_pattern_analysis", {}) if isinstance(deep, dict) else {}
    selected = natal.get("selected_pattern", {}) if isinstance(natal, dict) else {}
    if natal.get("status") == "invalid_pillars":
        return _blocked_hengmen_chart_strategy(natal)
    structure_adjustment = _stem_root_structure_adjustment(natal)
    votes = [
        _vote(
            "month_pattern",
            "月令取格",
            _month_pattern_rule_score(selected, natal, deep),
            "先从月令和月令十神提出格局候选。",
        ),
        _vote(
            "stem_root",
            "透干根气",
            min(0.9, 0.42 + len(selected.get("roots", [])) * 0.12 + (0.16 if selected.get("exposed") else 0.0) + structure_adjustment),
            "关键十神透出且在地支有根，才有明显应事力。",
        ),
        _vote(
            "success_rescue",
            "成败救应",
            _success_rescue_rule_score(selected),
            "看格局是成、败，还是有制化救应。",
        ),
    ]
    chart_score = _weighted(votes, {"month_pattern", "stem_root", "success_rescue"})
    return {
        "schema_version": "hengmen-ahp-v1",
        "source": "tools/格局横门断.docx -> mingli-bazi-hengmen/references/hengmen_meta_graph.md",
        "chart_score": chart_score,
        "votes": votes,
        "structure_evidence": natal.get("special_structures", {}),
        "rule_coverage": natal.get("rule_coverage", {}),
        "rule_catalog": natal.get("rule_catalog", {}),
        "review_flags": natal.get("review_flags", []),
        "ahp_architecture": build_hengmen_ahp_architecture(),
        "agent_receipts": {
            key: value for key, value in natal.get("agent_receipts", {}).items()
            if key in {"month_command_pattern", "success_failure_rescue", "branch_affection", "structure_evidence"}
        },
        "rule": "月令取格、透干得力、成败救应优先于单纯旺弱。",
    }


def score_hengmen_event(
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
    monthly_rows: list[dict[str, Any]] | None = None,
    counterexample_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score one event against a candidate chart using Hengmen AHP criteria."""
    event_type = str(event.get("type", ""))
    deep = bazi.get("deep_analysis", {}) if isinstance(bazi, dict) else {}
    context = bazi.get("context", {}) if isinstance(bazi, dict) else {}
    branch_interactions = _branch_interactions(annual_row)
    annual_ten_gods = annual_row.get("bazi_evidence", {}).get("annual_ten_gods", {})
    active_luck = annual_row.get("bazi_evidence", {}).get("active_major_luck", {})
    natal = deep.get("hengmen_pattern_analysis", {}) if isinstance(deep, dict) else {}
    selected = natal.get("selected_pattern", {}) if isinstance(natal, dict) else {}
    if natal.get("status") == "invalid_pillars":
        return _blocked_hengmen_event(natal)
    structure_adjustment = _stem_root_structure_adjustment(natal)
    timing = score_hengmen_timing(natal, event, annual_row, monthly_rows, counterexample_rows)
    factual_calibration = _factual_calibration_score(event, timing)
    event_votes = [
        _vote(
            "month_pattern",
            "月令取格",
            _month_pattern_rule_score(selected, natal, deep),
            "事件先服从原局主格，不用孤立年份硬断。",
        ),
        _vote(
            "stem_root",
            "透干根气",
            min(0.9, 0.42 + len(selected.get("roots", [])) * 0.12 + (0.16 if selected.get("exposed") else 0.0) + structure_adjustment),
            "透干、通根、得气决定事件是否能落地。",
        ),
        _vote(
            "success_rescue",
            "成败救应",
            _success_rescue_rule_score(selected),
            "刑冲破格有救应则不作全凶。",
        ),
        _vote(
            "event_ten_god",
            "十神主题",
            _event_ten_god_score(event_type, annual_ten_gods),
            "事件类型要对应官、财、印、食伤、比劫等主题。",
        ),
        _vote(
            "palace_trigger",
            "宫位落事",
            _palace_trigger_receipt(event_type, branch_interactions)["score"],
            "刑冲合害必须落到对应柱位的人事场景。",
        ),
        _vote(
            "luck_support",
            "大运承接",
            float(timing["major_luck"]["score"]),
            "大运定阶段，流年只负责触发。",
        ),
        _vote(
            "annual_interaction",
            "流年引动",
            _annual_monthly_timing_score(timing),
            "流年定年度引动，流月只在有可核验月份时细化应期。",
        ),
        _vote(
            "fact_calibration",
            "事实校准",
            factual_calibration["score"],
            "反例年份缺失时保持中性；出现未应验的强断时施加惩罚。",
        ),
    ]
    return {
        "score": _weighted(event_votes, set(AHP_WEIGHTS)),
        "votes": event_votes,
        "rule_engine": timing,
        "structure_evidence": natal.get("special_structures", {}),
        "rule_coverage": natal.get("rule_coverage", {}),
        "rule_catalog": natal.get("rule_catalog", {}),
        "review_flags": natal.get("review_flags", []),
        "timing_dimensions": {
            "major_luck": timing["major_luck"],
            "annual": timing["annual_score"],
            "monthly": timing["monthly"],
            "combined": _annual_monthly_timing_score(timing),
        },
        "agent_receipts": {
            "month_command_pattern": natal.get("agent_receipts", {}).get("month_command_pattern", {}),
            "success_failure_rescue": natal.get("agent_receipts", {}).get("success_failure_rescue", {}),
            "branch_affection": natal.get("agent_receipts", {}).get("branch_affection", {}),
            "event_ten_god": {"event_type": event_type, "annual_ten_gods": annual_ten_gods, "score": _event_ten_god_score(event_type, annual_ten_gods)},
            "palace_trigger": _palace_trigger_receipt(event_type, branch_interactions),
            "annual_monthly_timing": timing.get("agent_receipts", {}).get("annual_monthly_timing", {}),
            "falsification": timing.get("agent_receipts", {}).get("falsification", {}),
            "fact_calibration": factual_calibration,
        },
        "ahp_architecture": build_hengmen_ahp_architecture(),
        "rule": "横门断事件评分=具体格局+十神主题+宫位落事+年/月应期+反例校准。",
    }


def aggregate_hengmen_scores(event_scores: list[dict[str, Any]], events: list[dict[str, Any]]) -> float:
    total_weight = 0.0
    total = 0.0
    for score, event in zip(event_scores, events):
        weight = float(event.get("weight", 1.0) or 1.0)
        total += float(score.get("score", 0.0)) * weight
        total_weight += weight
    return round(total / max(total_weight, 0.001), 4)


def _blocked_hengmen_chart_strategy(natal: dict[str, Any]) -> dict[str, Any]:
    votes = [
        _vote("month_pattern", "月令取格", 0.0, "四柱输入无效，阻断评分。"),
        _vote("stem_root", "透干根气", 0.0, "四柱输入无效，阻断评分。"),
        _vote("success_rescue", "成败救应", 0.0, "四柱输入无效，阻断评分。"),
    ]
    return {
        "schema_version": "hengmen-ahp-v1", "chart_score": 0.0, "votes": votes,
        "blocked": True, "review_flags": natal.get("review_flags", []),
        "rule_coverage": natal.get("rule_coverage", {}), "rule_catalog": natal.get("rule_catalog", {}),
        "agent_receipts": natal.get("agent_receipts", {}),
        "rule": "Invalid pillar input blocks Hengmen AHP scoring.",
    }


def _blocked_hengmen_event(natal: dict[str, Any]) -> dict[str, Any]:
    votes = [
        _vote(vote_id, vote_id, 0.0, "四柱输入无效，阻断评分。")
        for vote_id in AHP_CRITERIA
    ]
    return {
        "score": 0.0, "votes": votes, "blocked": True,
        "review_flags": natal.get("review_flags", []),
        "rule_engine": {"status": "invalid_pillars"},
        "agent_receipts": {"blocking": natal.get("review_flags", [])},
        "rule_coverage": natal.get("rule_coverage", {}), "rule_catalog": natal.get("rule_catalog", {}),
        "rule": "Invalid pillar input blocks Hengmen AHP scoring.",
    }


def build_hengmen_ahp_architecture() -> dict[str, Any]:
    """Expose the independently auditable AHP criterion layer.

    The pairwise matrix is derived from the normalized source-method priorities,
    so it is reciprocal and exactly consistent by construction. It is not an
    empirical fit to the evaluated event set.
    """
    weights = {criterion: AHP_WEIGHTS[criterion] for criterion in AHP_CRITERIA}
    matrix = {
        left: {right: round(weights[left] / weights[right], 8) for right in AHP_CRITERIA}
        for left in AHP_CRITERIA
    }
    return {
        "schema_version": "hengmen-ahp-architecture-v1",
        "criteria": list(AHP_CRITERIA),
        "weights": weights,
        "pairwise_matrix": matrix,
        "priority_source": "source-method priorities; not calibrated on the current candidate event set",
        "consistency": {
            "method": "ratio-derived reciprocal matrix",
            "consistency_ratio": 0.0,
            "status": "exactly_consistent",
        },
    }


def _month_pattern_score(deep: dict[str, Any]) -> float:
    pattern = _nested_get(deep, "pattern_analysis", "pattern")
    month_ten_god = _nested_get(deep, "pattern_analysis", "month_ten_god")
    if pattern and month_ten_god:
        return 0.72
    if pattern or month_ten_god:
        return 0.56
    return 0.42


def _stem_root_score(deep: dict[str, Any], context: dict[str, Any]) -> float:
    ten_gods = deep.get("ten_god_distribution") or context.get("ten_god_distribution") or {}
    hidden = deep.get("hidden_stem_profile") or {}
    count = 0
    if isinstance(ten_gods, dict):
        count += min(3, len([v for v in ten_gods.values() if v]))
    if isinstance(hidden, dict) and hidden.get("total_hidden_stems"):
        count += 2
    return min(0.82, 0.42 + count * 0.08)


def _success_rescue_score(deep: dict[str, Any]) -> float:
    debate = deep.get("school_debate", {})
    conflicts = debate.get("conflicts", []) if isinstance(debate, dict) else []
    consensus = debate.get("consensus", {}) if isinstance(debate, dict) else {}
    if conflicts:
        return 0.48
    if consensus:
        return 0.66
    return 0.56


def _success_rescue_rule_score(selected: dict[str, Any]) -> float:
    if not isinstance(selected, dict):
        return 0.42
    score = 0.52 + min(0.18, len(selected.get("rescue_conditions", [])) * 0.08)
    score -= min(0.24, len(selected.get("failure_conditions", [])) * 0.1)
    if selected.get("affection", {}).get("state") == "有情":
        score += 0.08
    if selected.get("affection", {}).get("state") == "无情或受损":
        score -= 0.1
    return max(0.2, min(0.9, score))


def _stem_root_structure_adjustment(natal: dict[str, Any]) -> float:
    """Keep head/foot evidence inside the existing stem-root dimension."""
    special = natal.get("special_structures", {}) if isinstance(natal, dict) else {}
    rows = special.get("head_foot", []) if isinstance(special, dict) else []
    supported = sum(1 for row in rows if row.get("status") == "supported")
    blocked = sum(1 for row in rows if row.get("status") == "blocked")
    return max(-0.08, min(0.06, supported * 0.02 - blocked * 0.03))


def _event_ten_god_score(event_type: str, annual_ten_gods: dict[str, Any]) -> float:
    targets = {TEN_GOD_THEMES.get(target, target) for target in EVENT_TEN_GOD_TARGETS.get(event_type, set())}
    values = _ten_god_themes(annual_ten_gods)
    if targets and values & targets:
        return 0.78
    if values:
        return 0.52
    return 0.42


def _month_pattern_rule_score(selected: dict[str, Any], natal: dict[str, Any], deep: dict[str, Any]) -> float:
    score = float(selected.get("score", _month_pattern_score(deep))) if isinstance(selected, dict) else _month_pattern_score(deep)
    selection = natal.get("pattern_selection", {}) if isinstance(natal, dict) else {}
    if isinstance(selection, dict) and selection.get("confidence") == "low":
        score -= 0.08
    elif isinstance(selection, dict) and selection.get("confidence") == "moderate":
        score -= 0.03
    return max(0.2, min(0.9, score))


def _ten_god_themes(annual_ten_gods: dict[str, Any]) -> set[str]:
    if not isinstance(annual_ten_gods, dict):
        return set()
    values = {str(value) for value in annual_ten_gods.values()}
    return {TEN_GOD_THEMES.get(value, value) for value in values}


def _annual_monthly_timing_score(timing: dict[str, Any]) -> float:
    """Preserve annual primacy while keeping a sourced event month auditable."""
    annual = float(timing.get("annual_score", 0.5))
    monthly = timing.get("monthly", {})
    monthly_score = float(monthly.get("score", 0.5)) if isinstance(monthly, dict) else 0.5
    return round(0.65 * annual + 0.35 * monthly_score, 4)


def _palace_trigger_score(event_type: str, branch_interactions: list[dict[str, Any]]) -> float:
    return float(_palace_trigger_receipt(event_type, branch_interactions)["score"])


def _palace_trigger_receipt(event_type: str, branch_interactions: list[dict[str, Any]]) -> dict[str, Any]:
    if not branch_interactions:
        return {"score": 0.38, "target_pillars": [], "relations": [], "reason": "no_branch_interactions"}
    targets = EVENT_PALACE_TARGETS.get(event_type, set())
    hits = [item for item in branch_interactions if str(item.get("pillar", "")) in targets]
    if not hits:
        return {"score": 0.58, "target_pillars": [], "relations": [], "reason": "interaction_outside_event_palace"}
    relations = {str(item.get("relation", "")) for item in hits}
    severe = relations & {"clash", "punishment", "harm", "break"}
    combined = "combine" in relations
    disruptive = event_type in DISRUPTIVE_EVENT_TYPES
    if disruptive and severe:
        score, reason = 0.82, "disruptive_relation_hits_event_palace"
    elif disruptive:
        score, reason = 0.62, "non_disruptive_relation_hits_disruptive_event_palace"
    elif severe:
        score, reason = 0.62, "severe_relation_hits_non_disruptive_event_palace"
    elif combined:
        score, reason = 0.78, "combination_hits_non_disruptive_event_palace"
    else:
        score, reason = 0.68, "other_relation_hits_event_palace"
    return {
        "score": score, "target_pillars": sorted({str(item.get("pillar", "")) for item in hits}),
        "relations": sorted(relations), "reason": reason,
    }


def _luck_support_score(active_luck: dict[str, Any], event_type: str) -> float:
    if not isinstance(active_luck, dict) or not active_luck.get("ganzhi"):
        return 0.42
    if event_type in {"career_launch", "role_power", "role_transition", "award_peak", "iconic_role"}:
        return 0.64
    return 0.56


def _annual_interaction_score(branch_interactions: list[dict[str, Any]]) -> float:
    if not branch_interactions:
        return 0.36
    severe = {"clash", "punishment", "harm"}
    relations = {str(item.get("relation", "")) for item in branch_interactions}
    if relations & severe:
        return 0.76
    return 0.6


def _fact_score(event: dict[str, Any]) -> float:
    source = str(event.get("source", ""))
    label = str(event.get("label", ""))
    year = event.get("year")
    if year and source.startswith("http") and label:
        return 0.82
    if year and label:
        return 0.62
    return 0.4


def _factual_calibration_score(event: dict[str, Any], timing: dict[str, Any]) -> dict[str, Any]:
    source_score = _fact_score(event)
    counterfactual = timing.get("counterfactual", {}) if isinstance(timing, dict) else {}
    counterexample_score = float(counterfactual.get("score", 0.5)) if isinstance(counterfactual, dict) else 0.5
    return {
        "score": round(0.45 * source_score + 0.55 * counterexample_score, 4),
        "source_score": source_score,
        "counterexample_score": counterexample_score,
        "counterexample_status": counterfactual.get("status", "unavailable") if isinstance(counterfactual, dict) else "unavailable",
        "rule": "Source traceability and counterexample evidence are separate inputs to fact calibration.",
    }


def _branch_interactions(row: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(row, dict):
        return []
    value = row.get("bazi_evidence", {}).get("branch_interactions", [])
    return value if isinstance(value, list) else []


def _weighted(votes: list[dict[str, Any]], allowed: set[str]) -> float:
    total = 0.0
    weight_sum = 0.0
    for vote in votes:
        vote_id = str(vote.get("id", ""))
        if vote_id not in allowed:
            continue
        weight = AHP_WEIGHTS.get(vote_id, 0.0)
        total += float(vote.get("score", 0.0)) * weight
        weight_sum += weight
    return round(total / max(weight_sum, 0.001), 4)


def _vote(vote_id: str, name: str, score: float, basis: str) -> dict[str, Any]:
    return {
        "id": vote_id,
        "name": name,
        "score": round(max(0.0, min(1.0, score)), 4),
        "weight": AHP_WEIGHTS[vote_id],
        "basis": basis,
    }


def _nested_get(value: object, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
