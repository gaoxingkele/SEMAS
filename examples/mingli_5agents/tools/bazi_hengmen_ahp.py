"""格局横门断 AHP 评分器。

该模块把《格局横门断》抽取出的“月令取格、成败救应、事实筛选”
逻辑转成可审计的层次化评分。它不声称证明命理真伪，只用于比较
不同时辰候选对已知事件的解释力。
"""

from __future__ import annotations

from typing import Any


AHP_WEIGHTS = {
    "month_pattern": 0.18,
    "stem_root": 0.14,
    "success_rescue": 0.18,
    "event_ten_god": 0.16,
    "palace_trigger": 0.12,
    "luck_support": 0.10,
    "annual_interaction": 0.08,
    "fact_calibration": 0.04,
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


def build_hengmen_chart_strategy(bazi: dict[str, Any]) -> dict[str, Any]:
    """Score original chart structure using Hengmen AHP chart-side criteria."""
    deep = bazi.get("deep_analysis", {}) if isinstance(bazi, dict) else {}
    context = bazi.get("context", {}) if isinstance(bazi, dict) else {}
    votes = [
        _vote(
            "month_pattern",
            "月令取格",
            _month_pattern_score(deep),
            "先从月令和月令十神提出格局候选。",
        ),
        _vote(
            "stem_root",
            "透干根气",
            _stem_root_score(deep, context),
            "关键十神透出且在地支有根，才有明显应事力。",
        ),
        _vote(
            "success_rescue",
            "成败救应",
            _success_rescue_score(deep),
            "看格局是成、败，还是有制化救应。",
        ),
    ]
    chart_score = _weighted(votes, {"month_pattern", "stem_root", "success_rescue"})
    return {
        "schema_version": "hengmen-ahp-v1",
        "source": "tools/格局横门断.docx -> mingli-bazi-hengmen/references/hengmen_meta_graph.md",
        "chart_score": chart_score,
        "votes": votes,
        "rule": "月令取格、透干得力、成败救应优先于单纯旺弱。",
    }


def score_hengmen_event(
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
) -> dict[str, Any]:
    """Score one event against a candidate chart using Hengmen AHP criteria."""
    event_type = str(event.get("type", ""))
    deep = bazi.get("deep_analysis", {}) if isinstance(bazi, dict) else {}
    context = bazi.get("context", {}) if isinstance(bazi, dict) else {}
    branch_interactions = _branch_interactions(annual_row)
    annual_ten_gods = annual_row.get("bazi_evidence", {}).get("annual_ten_gods", {})
    active_luck = annual_row.get("bazi_evidence", {}).get("active_major_luck", {})
    event_votes = [
        _vote(
            "month_pattern",
            "月令取格",
            _month_pattern_score(deep),
            "事件先服从原局主格，不用孤立年份硬断。",
        ),
        _vote(
            "stem_root",
            "透干根气",
            _stem_root_score(deep, context),
            "透干、通根、得气决定事件是否能落地。",
        ),
        _vote(
            "success_rescue",
            "成败救应",
            _success_rescue_score(deep),
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
            _palace_trigger_score(event_type, branch_interactions),
            "刑冲合害必须落到对应柱位的人事场景。",
        ),
        _vote(
            "luck_support",
            "大运承接",
            _luck_support_score(active_luck, event_type),
            "大运定阶段，流年只负责触发。",
        ),
        _vote(
            "annual_interaction",
            "流年引动",
            _annual_interaction_score(branch_interactions),
            "看流年是否引动关键支、藏干和宫位。",
        ),
        _vote(
            "fact_calibration",
            "事实校准",
            _fact_score(event),
            "有明确年份和来源的事件权重更高。",
        ),
    ]
    return {
        "score": _weighted(event_votes, set(AHP_WEIGHTS)),
        "votes": event_votes,
        "rule": "横门断事件评分=原局格局+十神主题+宫位落事+岁运应期+事实校准。",
    }


def aggregate_hengmen_scores(event_scores: list[dict[str, Any]], events: list[dict[str, Any]]) -> float:
    total_weight = 0.0
    total = 0.0
    for score, event in zip(event_scores, events):
        weight = float(event.get("weight", 1.0) or 1.0)
        total += float(score.get("score", 0.0)) * weight
        total_weight += weight
    return round(total / max(total_weight, 0.001), 4)


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


def _event_ten_god_score(event_type: str, annual_ten_gods: dict[str, Any]) -> float:
    targets = EVENT_TEN_GOD_TARGETS.get(event_type, set())
    values = {str(value) for value in annual_ten_gods.values()} if isinstance(annual_ten_gods, dict) else set()
    if targets and values & targets:
        return 0.78
    if values:
        return 0.52
    return 0.42


def _palace_trigger_score(event_type: str, branch_interactions: list[dict[str, Any]]) -> float:
    if not branch_interactions:
        return 0.38
    targets = EVENT_PALACE_TARGETS.get(event_type, set())
    pillars = {str(item.get("pillar", "")) for item in branch_interactions}
    if targets and pillars & targets:
        return 0.82
    return 0.58


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
