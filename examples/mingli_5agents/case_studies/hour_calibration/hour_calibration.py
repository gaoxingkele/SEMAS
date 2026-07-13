"""Twelve-hour BaZi calibration for public-figure case studies.

The module is intentionally deterministic. It does not prove a birth hour; it
scores which of the 12 traditional Chinese hours best explains a supplied event
timeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.tools.annual_luck import build_annual_luck
from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart
from examples.mingli_5agents.tools.bazi_hengmen_ahp import (
    aggregate_hengmen_scores,
    build_hengmen_chart_strategy,
    score_hengmen_event,
)
from examples.mingli_5agents.tools.bazi_school_ahp import (
    aggregate_school_scores,
    score_all_bazi_schools,
)
from examples.mingli_5agents.tools.mingli_book_ahp import (
    aggregate_book_scores,
    score_all_book_frameworks,
)
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart


HOUR_CANDIDATES: tuple[dict[str, Any], ...] = (
    {"branch": "Zi", "label": "子时", "time": "00:30", "window": "23:00-00:59"},
    {"branch": "Chou", "label": "丑时", "time": "02:00", "window": "01:00-02:59"},
    {"branch": "Yin", "label": "寅时", "time": "04:00", "window": "03:00-04:59"},
    {"branch": "Mao", "label": "卯时", "time": "06:00", "window": "05:00-06:59"},
    {"branch": "Chen", "label": "辰时", "time": "08:00", "window": "07:00-08:59"},
    {"branch": "Si", "label": "巳时", "time": "10:00", "window": "09:00-10:59"},
    {"branch": "Wu", "label": "午时", "time": "12:00", "window": "11:00-12:59"},
    {"branch": "Wei", "label": "未时", "time": "14:00", "window": "13:00-14:59"},
    {"branch": "Shen", "label": "申时", "time": "16:00", "window": "15:00-16:59"},
    {"branch": "You", "label": "酉时", "time": "18:00", "window": "17:00-18:59"},
    {"branch": "Xu", "label": "戌时", "time": "20:00", "window": "19:00-20:59"},
    {"branch": "Hai", "label": "亥时", "time": "22:00", "window": "21:00-22:59"},
)

EVENT_TYPE_ALIASES = {
    "scandal": ["relationship", "public_visibility", "role_transition"],
    "public_scandal": ["scandal", "public_visibility", "role_transition"],
    "family": ["relationship", "movement"],
    "death": ["health_pressure", "movement"],
    "award_peak": ["role_power", "public_visibility"],
    "box_office_breakthrough": ["public_visibility", "business_power", "career_launch"],
    "iconic_role": ["public_visibility", "career_launch"],
    "career_reinvention": ["role_transition", "public_visibility"],
    "health_crisis": ["health_pressure"],
}

EVENT_TYPE_LABELS = {
    "study_exam": "学业考试",
    "career_launch": "事业启动",
    "role_power": "权力职位",
    "role_transition": "角色转换",
    "business_power": "商业财务",
    "relationship": "婚恋关系",
    "movement": "迁移变动",
    "public_visibility": "公众曝光",
    "health_pressure": "健康压力",
    "scandal": "负面新闻",
    "family": "家庭事件",
    "death": "死亡事件",
    "award_peak": "奖项高峰",
    "box_office_breakthrough": "票房突破",
    "iconic_role": "代表角色",
    "career_reinvention": "事业再造",
    "public_scandal": "公众风波",
    "health_crisis": "健康危机",
}


def calibrate_case(case: dict[str, Any]) -> dict[str, Any]:
    events = _valid_events(case)
    if not events:
        raise ValueError("case must contain at least one event with a year")
    start_year = min(int(event["year"]) for event in events)
    end_year = max(int(event["year"]) for event in events)
    candidates = [_candidate_result(case, candidate, events, start_year, end_year) for candidate in HOUR_CANDIDATES]
    candidates.sort(key=lambda item: item["score"]["strategy_total"], reverse=True)
    return {
        "schema_version": "mingli-hour-calibration-v1",
        "case_id": case.get("case_id", ""),
        "name": case.get("name", ""),
        "birth_date": case.get("birth_date", ""),
        "birthplace": case.get("birthplace", ""),
        "public_reference_hours": case.get("public_reference_hours", []),
        "event_count": len(events),
        "event_year_range": {"start_year": start_year, "end_year": end_year},
        "method": {
            "candidate_count": len(HOUR_CANDIDATES),
            "rule": "Generate 12 hour candidates, score event fit, layered BaZi strategy, Zi Wei annual-palace, and astrology annual-house evidence separately, then rank by strategy_total.",
            "boundary": "This is historical-fit calibration, not proof of actual birth hour. Public reference hours and event-fit results must be reported separately when they disagree.",
        },
        "winner": candidates[0],
        "ranking": candidates,
        "debate": _debate(candidates),
        "reference_evaluation": _reference_evaluation(case, candidates),
    }


def _candidate_result(
    case: dict[str, Any],
    candidate: dict[str, Any],
    events: list[dict[str, Any]],
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    birth = normalize_birth_input(
        {
            "name": str(case.get("name", "")),
            "gender": str(case.get("gender", "")),
            "birth_date": str(case["birth_date"]),
            "birth_time": candidate["time"],
            "birthplace": str(case.get("birthplace", "")),
            "annual_start_year": start_year,
            "annual_end_year": end_year,
        }
    )
    bazi = build_bazi_chart(birth)
    ziwei = build_ziwei_chart(birth)
    astrology = build_astrology_chart(birth)
    annual = build_annual_luck(birth, bazi, start_year=start_year, end_year=end_year)
    rows_by_year = {row["year"]: row for row in annual["rows"]}
    ziwei_rows_by_year = {
        row["year"]: row for row in ziwei.get("deep_analysis", {}).get("annual_activation", [])
    }
    astrology_rows_by_year = {
        row["year"]: row for row in astrology.get("deep_analysis", {}).get("annual_transits", [])
    }
    event_scores = [
        _score_event(
            event,
            rows_by_year.get(int(event["year"]), {}),
            ziwei_rows_by_year.get(int(event["year"]), {}),
            astrology_rows_by_year.get(int(event["year"]), {}),
            bazi,
        )
        for event in events
    ]
    hengmen_event_scores = [
        score_hengmen_event(event, rows_by_year.get(int(event["year"]), {}), bazi)
        for event in events
    ]
    bazi_school_event_scores = [
        score_all_bazi_schools(event, rows_by_year.get(int(event["year"]), {}), bazi)
        for event in events
    ]
    book_event_scores = [
        score_all_book_frameworks(
            event,
            rows_by_year.get(int(event["year"]), {}),
            bazi,
            ziwei_rows_by_year.get(int(event["year"]), {}),
            astrology_rows_by_year.get(int(event["year"]), {}),
        )
        for event in events
    ]
    for event_score, hengmen_score in zip(event_scores, hengmen_event_scores):
        event_score["hengmen_ahp"] = hengmen_score
        event_score["hengmen_score"] = hengmen_score["score"]
    for event_score, school_scores in zip(event_scores, bazi_school_event_scores):
        event_score["bazi_school_ahp"] = school_scores
    for event_score, book_scores in zip(event_scores, book_event_scores):
        event_score["book_ahp"] = book_scores
    total_weight = sum(float(event.get("weight", 1.0) or 1.0) for event in events)
    event_fit_total = round(sum(item["weighted_score"] for item in event_scores) / max(total_weight, 0.001), 4)
    layered_event_total = round(
        sum(item["layered_weighted_score"] for item in event_scores) / max(total_weight, 0.001),
        4,
    )
    chart_strategy_total = _chart_strategy_score(bazi)
    hengmen_ahp_total = aggregate_hengmen_scores(hengmen_event_scores, events)
    hengmen_chart_strategy = build_hengmen_chart_strategy(bazi)
    ziwei_side_total = _side_total(event_scores, "ziwei_score", events)
    astrology_side_total = _side_total(event_scores, "astrology_score", events)
    bazi_school_ahp_totals = aggregate_school_scores(bazi_school_event_scores, events)
    book_ahp_totals = aggregate_book_scores(book_event_scores, events)
    strategy_total = round(
        event_fit_total * 0.3
        + layered_event_total * 0.2
        + chart_strategy_total * 0.1
        + hengmen_ahp_total * 0.3
        + ziwei_side_total * 0.05
        + astrology_side_total * 0.05,
        4,
    )
    return {
        "candidate_id": f"hour_{candidate['branch'].lower()}",
        "hour_label": candidate["label"],
        "hour_branch": candidate["branch"],
        "hour_window": candidate["window"],
        "representative_time": candidate["time"],
        "pillars": bazi["context"]["pillars"],
        "element_counts": bazi["context"]["element_counts"],
        "dominant_element": bazi["context"]["dominant_element"],
        "useful_element": bazi["context"]["useful_element"],
        "ziwei_signature": {
            "ming_palace": ziwei.get("ming_palace", ""),
            "body_palace": ziwei.get("body_palace", ""),
            "major_stars": ziwei.get("major_stars", []),
        },
        "astrology_signature": {
            "sun": astrology.get("sun", ""),
            "moon": astrology.get("moon", ""),
            "ascendant": astrology.get("ascendant", ""),
            "quality": astrology.get("deep_analysis", {}).get("ephemeris_quality", {}),
        },
        "score": {
            "total": strategy_total,
            "strategy_total": strategy_total,
            "event_fit_total": event_fit_total,
            "layered_event_total": layered_event_total,
            "chart_strategy_total": chart_strategy_total,
            "hengmen_ahp_total": hengmen_ahp_total,
            "ziwei_side_total": ziwei_side_total,
            "astrology_side_total": astrology_side_total,
            "matched_event_count": sum(1 for item in event_scores if item["score"] >= 0.75),
            "partial_event_count": sum(1 for item in event_scores if 0.25 <= item["score"] < 0.75),
            "missed_event_count": sum(1 for item in event_scores if item["score"] < 0.25),
            "method_weights": {
                "event_fit": 0.3,
                "layered_bazi_event_votes": 0.2,
                "chart_strategy": 0.1,
                "hengmen_ahp": 0.3,
                "ziwei_side_validation": 0.05,
                "astrology_side_validation": 0.05,
            },
        },
        "hengmen_chart_strategy": hengmen_chart_strategy,
        "bazi_school_ahp_totals": bazi_school_ahp_totals,
        "book_ahp_totals": book_ahp_totals,
        "event_scores": event_scores,
    }


def _score_event(
    event: dict[str, Any],
    row: dict[str, Any],
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
    bazi: dict[str, Any],
) -> dict[str, Any]:
    markers = row.get("event_markers", {}) if isinstance(row, dict) else {}
    event_type = str(event.get("type", ""))
    accepted = [event_type, *EVENT_TYPE_ALIASES.get(event_type, [])]
    direct = bool(markers.get(event_type))
    alias = next((alias for alias in accepted[1:] if markers.get(alias)), "")
    branch_interactions = row.get("bazi_evidence", {}).get("branch_interactions", []) if isinstance(row, dict) else []
    natal_matches = row.get("bazi_evidence", {}).get("natal_pillar_matches", []) if isinstance(row, dict) else []
    intensity = str(row.get("intensity", "")) if isinstance(row, dict) else ""
    category = str(row.get("category", "")) if isinstance(row, dict) else ""
    score = 0.0
    reasons = []
    if direct:
        score += 1.0
        reasons.append("事件类型直接命中年度标记")
    elif alias:
        score += 0.65
        reasons.append(f"事件类型由相邻标记支持：{alias}")
    typed_score, typed_reasons = _typed_event_score(event_type, category, intensity, markers)
    score += typed_score
    reasons.extend(typed_reasons)
    auxiliary_score, auxiliary_reasons = _auxiliary_system_score(event_type, ziwei_row, astrology_row)
    ziwei_score, ziwei_reasons = _ziwei_side_score(event_type, ziwei_row)
    astrology_score, astrology_reasons = _astrology_side_score(event_type, astrology_row)
    score += auxiliary_score
    reasons.extend(auxiliary_reasons)
    if branch_interactions:
        score += 0.15
        reasons.append("流年与原局存在刑冲合害触发")
    hour_hits = [item for item in branch_interactions if item.get("pillar") == "hour"]
    if hour_hits:
        hour_bonus = 0.18 if event_type in {"relationship", "family", "movement", "public_visibility", "scandal", "death"} else 0.08
        score += hour_bonus
        relations = "、".join(str(item.get("relation", "")) for item in hour_hits)
        reasons.append(f"流年直接触动时柱：{relations}")
    day_hits = [item for item in branch_interactions if item.get("pillar") == "day"]
    if day_hits and event_type in {"health_pressure", "death", "relationship", "family"}:
        score += 0.12
        reasons.append("流年触动日支，关系或身体层面权重上升")
    if any(item.get("pillar") == "hour" for item in natal_matches):
        score += 0.1
        reasons.append("流年干支重复时柱，时辰候选被激活")
    if intensity == "high-volatility":
        score += 0.2
        reasons.append("年度强度为高波动")
    elif intensity == "constructive" and event_type in {"career_launch", "role_power", "business_power", "study_exam"}:
        score += 0.1
        reasons.append("建设性年份支持正向成就事件")
    score = min(score, 1.0)
    weight = float(event.get("weight", 1.0) or 1.0)
    layered_votes = _layered_event_votes(
        event_type=event_type,
        row=row,
        bazi=bazi,
        ziwei_row=ziwei_row,
        astrology_row=astrology_row,
        direct=direct,
        alias=bool(alias),
        branch_interactions=branch_interactions,
        hour_hits=hour_hits,
        day_hits=day_hits,
    )
    layered_score = round(sum(float(item["score"]) for item in layered_votes) / max(len(layered_votes), 1), 3)
    return {
        "year": int(event["year"]),
        "event_type": event_type,
        "event_type_label": EVENT_TYPE_LABELS.get(event_type, event_type),
        "label": str(event.get("label", "")),
        "weight": weight,
        "score": round(score, 3),
        "weighted_score": round(score * weight, 3),
        "layered_score": layered_score,
        "layered_weighted_score": round(layered_score * weight, 3),
        "layered_votes": layered_votes,
        "annual_ganzhi": row.get("ganzhi", "") if isinstance(row, dict) else "",
        "annual_category": row.get("category", "") if isinstance(row, dict) else "",
        "annual_intensity": intensity,
        "ziwei_annual_palace": ziwei_row.get("palace", "") if isinstance(ziwei_row, dict) else "",
        "astrology_annual_house": astrology_row.get("activated_house", "") if isinstance(astrology_row, dict) else "",
        "auxiliary_score": round(auxiliary_score, 3),
        "ziwei_score": ziwei_score,
        "ziwei_reasons": ziwei_reasons,
        "astrology_score": astrology_score,
        "astrology_reasons": astrology_reasons,
        "hour_branch_hit": bool(hour_hits),
        "day_branch_hit": bool(day_hits),
        "reasons": reasons or ["未命中主要事件标记"],
        "source": str(event.get("source", "")),
    }


def _chart_strategy_score(bazi: dict[str, Any]) -> float:
    strategy = bazi.get("deep_analysis", {}).get("layered_strategy", {})
    layers = strategy.get("layers", []) if isinstance(strategy, dict) else []
    if not layers:
        return 0.5
    average = sum(float(item.get("confidence", 0.0)) for item in layers) / len(layers)
    conflict_count = len(strategy.get("conflicts", [])) if isinstance(strategy.get("conflicts"), list) else 0
    penalty = min(0.12, conflict_count * 0.03)
    return round(max(0.0, min(1.0, average - penalty)), 3)


def _side_total(event_scores: list[dict[str, Any]], key: str, events: list[dict[str, Any]]) -> float:
    total_weight = 0.0
    total = 0.0
    for event_score, event in zip(event_scores, events):
        weight = float(event.get("weight", 1.0) or 1.0)
        total += float(event_score.get(key, 0.0) or 0.0) * weight
        total_weight += weight
    return round(total / max(total_weight, 0.001), 4)


def _layered_event_votes(
    *,
    event_type: str,
    row: dict[str, Any],
    bazi: dict[str, Any],
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
    direct: bool,
    alias: bool,
    branch_interactions: list[dict[str, Any]],
    hour_hits: list[dict[str, Any]],
    day_hits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deep = bazi.get("deep_analysis", {})
    category = str(row.get("category", "")) if isinstance(row, dict) else ""
    intensity = str(row.get("intensity", "")) if isinstance(row, dict) else ""
    pattern = str(deep.get("pattern_analysis", {}).get("pattern", ""))
    season = str(deep.get("tiaohou_analysis", {}).get("season", ""))
    useful = str(deep.get("useful_god_analysis", {}).get("useful_element", ""))
    useful_hit = useful and useful in str(row.get("elements", ""))
    ziwei_palace = str(ziwei_row.get("palace", "")) if isinstance(ziwei_row, dict) else ""
    astro_house = int(astrology_row.get("activated_house", 0) or 0) if isinstance(astrology_row, dict) else 0

    pattern_score = 0.35
    if direct:
        pattern_score += 0.35
    elif alias:
        pattern_score += 0.22
    if event_type in {"role_power", "role_transition", "public_visibility"} and category in {"authority", "learning"}:
        pattern_score += 0.18
    if "pattern" in pattern or pattern:
        pattern_score += 0.08

    tiaohou_score = 0.35
    if season in {"winter", "summer"} and event_type in {"health_pressure", "death", "scandal", "study_exam"}:
        tiaohou_score += 0.18
    if intensity == "high-volatility":
        tiaohou_score += 0.12
    if useful_hit:
        tiaohou_score += 0.1

    disease_score = 0.35
    if event_type in {"scandal", "death", "health_pressure"} and intensity == "high-volatility":
        disease_score += 0.32
    if branch_interactions:
        disease_score += 0.15
    if useful_hit:
        disease_score += 0.08

    tiyong_score = 0.35
    if useful_hit:
        tiyong_score += 0.25
    if branch_interactions:
        tiyong_score += 0.12
    if event_type in {"role_power", "career_launch", "business_power"} and category in {"authority", "wealth"}:
        tiyong_score += 0.12

    palace_score = 0.35
    if hour_hits:
        palace_score += 0.18
    if day_hits:
        palace_score += 0.14
    if _topic_matches_ziwei(event_type, ziwei_palace):
        palace_score += 0.14
    if _topic_matches_astrology(event_type, astro_house):
        palace_score += 0.12

    fact_score = 0.45
    if row:
        fact_score += 0.08
    if direct or alias:
        fact_score += 0.12
    return [
        _vote("pattern_vote", "格局票", pattern_score, "事件类型是否承接原局主线"),
        _vote("tiaohou_vote", "调候票", tiaohou_score, "事件是否与寒暖燥湿和状态失衡有关"),
        _vote("disease_medicine_vote", "病药票", disease_score, "事件是否呈现病点加重或药神到位"),
        _vote("tiyong_flow_vote", "体用流通票", tiyong_score, "事件是否修复或冲断体用保护链"),
        _vote("palace_event_vote", "宫位事件票", palace_score, "事件是否触动对应柱位、紫微宫位或星座宫位"),
        _vote("fact_calibration_vote", "事实校准票", fact_score, "事件年份是否有结构化记录和来源"),
    ]


def _vote(layer_id: str, name: str, score: float, basis: str) -> dict[str, Any]:
    return {
        "id": layer_id,
        "name": name,
        "score": round(max(0.0, min(1.0, score)), 3),
        "basis": basis,
    }


def _topic_matches_ziwei(event_type: str, palace: str) -> bool:
    return palace in {
        "role_power": {"Career", "Parents", "Friends"},
        "role_transition": {"Career", "Friends", "Travel"},
        "career_launch": {"Career", "Fortune"},
        "business_power": {"Wealth", "Career"},
        "public_visibility": {"Career", "Friends", "Travel"},
        "relationship": {"Spouse", "Friends"},
        "family": {"Spouse", "Children", "Property"},
        "movement": {"Travel", "Career"},
        "study_exam": {"Parents", "Career", "Fortune"},
        "scandal": {"Friends", "Career", "Health"},
        "public_scandal": {"Friends", "Career", "Health"},
        "health_pressure": {"Health", "Fortune"},
        "health_crisis": {"Health", "Fortune"},
        "death": {"Health", "Travel", "Fortune"},
        "award_peak": {"Career", "Fortune", "Friends"},
        "box_office_breakthrough": {"Career", "Wealth", "Friends"},
        "iconic_role": {"Career", "Friends", "Fortune"},
        "career_reinvention": {"Career", "Travel", "Friends"},
    }.get(event_type, set())


def _topic_matches_astrology(event_type: str, house: int) -> bool:
    return house in {
        "role_power": {10, 11, 9},
        "role_transition": {10, 11, 9},
        "career_launch": {10, 6},
        "business_power": {2, 8, 10},
        "public_visibility": {10, 11, 9},
        "relationship": {7, 5},
        "family": {4, 5, 7},
        "movement": {9, 3, 10},
        "study_exam": {3, 9, 10},
        "scandal": {8, 12, 10},
        "public_scandal": {8, 12, 10},
        "health_pressure": {6, 8, 12},
        "health_crisis": {6, 8, 12},
        "death": {8, 12, 6},
        "award_peak": {10, 11, 9},
        "box_office_breakthrough": {10, 2, 11},
        "iconic_role": {10, 5, 11},
        "career_reinvention": {10, 9, 11},
    }.get(event_type, set())


def _ziwei_side_score(event_type: str, ziwei_row: dict[str, Any]) -> tuple[float, list[str]]:
    if not isinstance(ziwei_row, dict) or not ziwei_row:
        return 0.32, ["紫微没有形成有效年度侧证"]
    palace = str(ziwei_row.get("palace", ""))
    score = 0.45
    reasons = [f"紫微流年落{palace or '未知'}宫"]
    if _topic_matches_ziwei(event_type, palace):
        score += 0.3
        reasons.append("宫位主题与事件类型相合")
    if ziwei_row.get("four_transformation"):
        score += 0.08
        reasons.append("四化信息参与触发")
    if ziwei_row.get("major_limit"):
        score += 0.07
        reasons.append("大限与流年同看")
    return round(min(score, 1.0), 3), reasons


def _astrology_side_score(event_type: str, astrology_row: dict[str, Any]) -> tuple[float, list[str]]:
    if not isinstance(astrology_row, dict) or not astrology_row:
        return 0.32, ["星座侧证没有有效年度过境"]
    house = int(astrology_row.get("activated_house", 0) or 0)
    planet = str(astrology_row.get("transit_planet", ""))
    score = 0.45
    reasons = [f"星座年度触发第{house or '未知'}宫"]
    if _topic_matches_astrology(event_type, house):
        score += 0.3
        reasons.append("宫位主题与事件类型相合")
    if event_type in {"scandal", "public_scandal", "death", "health_pressure", "health_crisis"} and planet in {
        "Saturn",
        "Mars",
        "Pluto",
    }:
        score += 0.1
        reasons.append("压力型行星触发危机类事件")
    if event_type in {
        "role_power",
        "award_peak",
        "public_visibility",
        "box_office_breakthrough",
        "career_launch",
        "iconic_role",
    } and planet in {"Jupiter", "Venus", "Sun"}:
        score += 0.1
        reasons.append("扩张或曝光型行星触发成名类事件")
    return round(min(score, 1.0), 3), reasons


def _auxiliary_system_score(
    event_type: str,
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    ziwei_palace = str(ziwei_row.get("palace", "")) if isinstance(ziwei_row, dict) else ""
    house = int(astrology_row.get("activated_house", 0) or 0) if isinstance(astrology_row, dict) else 0
    planet = str(astrology_row.get("transit_planet", "")) if isinstance(astrology_row, dict) else ""

    ziwei_map = {
        "role_power": {"Career": 0.16, "Parents": 0.08, "Friends": 0.08},
        "role_transition": {"Career": 0.12, "Friends": 0.1, "Travel": 0.1},
        "career_launch": {"Career": 0.16, "Fortune": 0.08},
        "business_power": {"Wealth": 0.16, "Career": 0.1},
        "public_visibility": {"Career": 0.14, "Friends": 0.1, "Travel": 0.08},
        "relationship": {"Spouse": 0.16, "Friends": 0.08},
        "family": {"Spouse": 0.1, "Children": 0.14, "Property": 0.08},
        "movement": {"Travel": 0.16, "Career": 0.08},
        "study_exam": {"Parents": 0.12, "Career": 0.08, "Fortune": 0.08},
        "scandal": {"Friends": 0.12, "Career": 0.1, "Health": 0.08},
        "public_scandal": {"Friends": 0.12, "Career": 0.1, "Health": 0.08},
        "health_pressure": {"Health": 0.16, "Fortune": 0.08},
        "health_crisis": {"Health": 0.16, "Fortune": 0.08},
        "death": {"Health": 0.16, "Travel": 0.08, "Fortune": 0.06},
        "award_peak": {"Career": 0.16, "Fortune": 0.1, "Friends": 0.08},
        "box_office_breakthrough": {"Career": 0.14, "Wealth": 0.14, "Friends": 0.08},
        "iconic_role": {"Career": 0.14, "Friends": 0.1, "Fortune": 0.08},
        "career_reinvention": {"Career": 0.12, "Travel": 0.1, "Friends": 0.08},
    }
    palace_score = ziwei_map.get(event_type, {}).get(ziwei_palace, 0.0)
    if palace_score:
        score += palace_score
        reasons.append(f"紫微流年落{ziwei_palace}宫，与事件主题相扣")

    house_map = {
        "role_power": {10: 0.14, 11: 0.08, 9: 0.06},
        "role_transition": {10: 0.1, 11: 0.08, 9: 0.08},
        "career_launch": {10: 0.14, 6: 0.08},
        "business_power": {2: 0.14, 8: 0.1, 10: 0.08},
        "public_visibility": {10: 0.12, 11: 0.08, 9: 0.08},
        "relationship": {7: 0.14, 5: 0.08},
        "family": {4: 0.12, 5: 0.1, 7: 0.08},
        "movement": {9: 0.12, 3: 0.08, 10: 0.06},
        "study_exam": {3: 0.1, 9: 0.12, 10: 0.06},
        "scandal": {8: 0.12, 12: 0.1, 10: 0.08},
        "public_scandal": {8: 0.12, 12: 0.1, 10: 0.08},
        "health_pressure": {6: 0.12, 8: 0.08, 12: 0.08},
        "health_crisis": {6: 0.12, 8: 0.08, 12: 0.08},
        "death": {8: 0.14, 12: 0.1, 6: 0.08},
        "award_peak": {10: 0.14, 11: 0.1, 9: 0.08},
        "box_office_breakthrough": {10: 0.12, 2: 0.12, 11: 0.08},
        "iconic_role": {10: 0.12, 5: 0.12, 11: 0.08},
        "career_reinvention": {10: 0.1, 9: 0.1, 11: 0.08},
    }
    house_score = house_map.get(event_type, {}).get(house, 0.0)
    if house_score:
        score += house_score
        reasons.append(f"星座年度触发第{house}宫，与事件主题相扣")

    if event_type in {"scandal", "public_scandal", "death", "health_pressure", "health_crisis"} and planet in {"Saturn", "Mars", "Pluto"}:
        score += 0.06
        reasons.append(f"星座年度由{planet}触发，偏压力、冲突或深层转折")
    elif event_type in {
        "role_power",
        "award_peak",
        "public_visibility",
        "business_power",
        "career_launch",
        "box_office_breakthrough",
        "iconic_role",
    } and planet in {"Jupiter", "Venus", "Sun"}:
        score += 0.05
        reasons.append(f"星座年度由{planet}触发，偏扩张、曝光或地位提升")
    return min(score, 0.3), reasons


def _typed_event_score(event_type: str, category: str, intensity: str, markers: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if event_type == "role_power" and category == "authority":
        score += 0.45
        reasons.append("权力职位事件与官杀/规则主轴相符")
    elif event_type == "role_transition" and category in {"authority", "learning", "friends"}:
        score += 0.35
        reasons.append("角色转换事件与身份、规则或圈层变化相符")
    elif event_type == "career_launch" and category in {"expression", "authority", "wealth"}:
        score += 0.35
        reasons.append("事业启动事件与输出、职位或资源主轴相符")
    elif event_type == "business_power" and category in {"wealth", "authority"}:
        score += 0.35
        reasons.append("商业财务事件与财务或资源主轴相符")
    elif event_type == "public_visibility" and category in {"expression", "authority", "friends"}:
        score += 0.35
        reasons.append("公众曝光事件与表达、权力或圈层主轴相符")
    elif event_type == "movement" and (markers.get("movement") or intensity == "high-volatility"):
        score += 0.35
        reasons.append("迁移变动事件与移动标记或高波动相符")
    elif event_type == "relationship" and category in {"friends", "wealth"}:
        score += 0.3
        reasons.append("关系事件与同辈或财务家庭主轴相符")
    elif event_type == "family" and category in {"wealth", "friends"}:
        score += 0.25
        reasons.append("家庭事件与责任或关系主轴相符")
    elif event_type == "scandal":
        if intensity == "high-volatility":
            score += 0.35
            reasons.append("负面冲突事件与高波动年份相符")
        if category in {"friends", "expression", "authority"}:
            score += 0.2
            reasons.append("负面事件与圈层、曝光或权力主轴相符")
    elif event_type == "public_scandal":
        if intensity == "high-volatility":
            score += 0.35
            reasons.append("公众风波与高波动年份相符")
        if category in {"friends", "expression", "authority"}:
            score += 0.22
            reasons.append("公众风波与圈层、表达或权力主轴相符")
    elif event_type == "award_peak":
        if category in {"authority", "learning", "expression"}:
            score += 0.4
            reasons.append("奖项高峰与名誉、资质或作品表达主轴相符")
        if intensity == "constructive":
            score += 0.12
            reasons.append("建设性年份支持荣誉确认")
    elif event_type == "box_office_breakthrough":
        if category in {"wealth", "expression", "authority"}:
            score += 0.42
            reasons.append("票房突破与财、表达和公众地位主轴相符")
        if markers.get("public_visibility"):
            score += 0.12
            reasons.append("年度带公众曝光标记")
    elif event_type == "iconic_role":
        if category in {"expression", "authority", "friends"}:
            score += 0.38
            reasons.append("代表角色与表达、名望或圈层主轴相符")
        if markers.get("public_visibility"):
            score += 0.12
            reasons.append("代表角色需要公众曝光承接")
    elif event_type == "career_reinvention":
        if category in {"expression", "authority", "learning", "friends"}:
            score += 0.36
            reasons.append("事业再造与表达、身份或圈层转换相符")
        if intensity == "high-volatility":
            score += 0.12
            reasons.append("高波动年份容易出现路线重塑")
    elif event_type == "death":
        if intensity == "high-volatility":
            score += 0.35
            reasons.append("死亡事件与高波动年份相符")
        if markers.get("health_pressure") or markers.get("movement"):
            score += 0.3
            reasons.append("死亡事件与健康压力或终局变动标记相符")
    elif event_type == "health_pressure" and (intensity == "high-volatility" or markers.get("health_pressure")):
        score += 0.4
        reasons.append("健康压力事件与高波动或健康标记相符")
    elif event_type == "health_crisis" and (intensity == "high-volatility" or markers.get("health_pressure")):
        score += 0.42
        reasons.append("健康危机事件与高波动或健康标记相符")
    elif event_type == "study_exam" and category in {"learning", "authority"}:
        score += 0.35
        reasons.append("学业考试事件与学习或规则主轴相符")
    return score, reasons


def _valid_events(case: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for event in case.get("events", []):
        if not isinstance(event, dict) or event.get("year") is None:
            continue
        events.append(event)
    return events


def _debate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    top = candidates[:3]
    if len(top) < 2:
        margin = 0.0
    else:
        margin = round(float(top[0]["score"]["total"]) - float(top[1]["score"]["total"]), 4)
    if margin >= 0.15:
        decision = "clear_lead"
    elif margin >= 0.05:
        decision = "narrow_lead"
    else:
        decision = "ambiguous"
    return {
        "decision": decision,
        "margin_to_second": margin,
        "top_candidates": [
            {
                "candidate_id": item["candidate_id"],
                "hour_label": item["hour_label"],
                "score": item["score"]["strategy_total"],
                "event_fit_total": item["score"].get("event_fit_total"),
                "layered_event_total": item["score"].get("layered_event_total"),
                "chart_strategy_total": item["score"].get("chart_strategy_total"),
                "hengmen_ahp_total": item["score"].get("hengmen_ahp_total"),
                "matched_event_count": item["score"]["matched_event_count"],
            }
            for item in top
        ],
        "resolution_rule": "Prefer a candidate only when strategy_total lead is clear and layered-school votes agree; otherwise keep multiple possible hours and report event-fit/layer conflicts.",
    }


def _reference_evaluation(case: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    references = case.get("public_reference_hours", [])
    if not isinstance(references, list) or not references:
        return {
            "has_reference": False,
            "matches_winner": None,
            "best_reference_rank": None,
            "best_reference_margin_from_winner": None,
            "references": [],
        }
    rows = []
    for ref in references:
        if not isinstance(ref, dict):
            continue
        label = str(ref.get("label", ""))
        match = next((item for item in candidates if item.get("hour_label") == label), None)
        if match is None:
            rows.append({**ref, "rank": None, "strategy_total": None, "margin_from_winner": None})
            continue
        rank = candidates.index(match) + 1
        margin = round(float(candidates[0]["score"]["strategy_total"]) - float(match["score"]["strategy_total"]), 4)
        rows.append(
            {
                **ref,
                "rank": rank,
                "strategy_total": match["score"]["strategy_total"],
                "event_fit_total": match["score"].get("event_fit_total"),
                "layered_event_total": match["score"].get("layered_event_total"),
                "chart_strategy_total": match["score"].get("chart_strategy_total"),
                "hengmen_ahp_total": match["score"].get("hengmen_ahp_total"),
                "margin_from_winner": margin,
                "in_top_3": rank <= 3,
            }
        )
    ranked = [item for item in rows if isinstance(item.get("rank"), int)]
    best = min(ranked, key=lambda item: int(item["rank"])) if ranked else None
    return {
        "has_reference": True,
        "matches_winner": bool(best and best.get("rank") == 1),
        "best_reference_rank": best.get("rank") if best else None,
        "best_reference_margin_from_winner": best.get("margin_from_winner") if best else None,
        "references": rows,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['name']} 十二时辰校准",
        "",
        f"- 出生日期：{result['birth_date']}",
        f"- 出生地点：{result['birthplace']}",
        f"- 事件数量：{result['event_count']}",
        f"- 年份范围：{result['event_year_range']['start_year']}-{result['event_year_range']['end_year']}",
        "",
        "## 结论",
        "",
        f"- 第一候选：{result['winner']['hour_label']}（{result['winner']['hour_window']}），策略总分 {result['winner']['score']['strategy_total']}",
        f"- 事件拟合分：{result['winner']['score']['event_fit_total']}；分层事件分：{result['winner']['score']['layered_event_total']}；原局策略分：{result['winner']['score']['chart_strategy_total']}",
        f"- 辩论状态：{result['debate']['decision']}，领先第二名 {result['debate']['margin_to_second']}",
        "",
        "## 候选排序",
        "",
        "| 排名 | 时辰 | 时间段 | 策略总分 | 事件拟合 | 分层事件 | 原局策略 | 命中 | 部分 | 未命中 | 四柱 |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for index, item in enumerate(result["ranking"], start=1):
        score = item["score"]
        pillars = item["pillars"]
        pillar_text = f"{pillars.get('year')} {pillars.get('month')} {pillars.get('day')} {pillars.get('hour')}"
        lines.append(
            f"| {index} | {item['hour_label']} | {item['hour_window']} | {score['strategy_total']} | "
            f"{score['event_fit_total']} | {score['layered_event_total']} | {score['chart_strategy_total']} | "
            f"{score['matched_event_count']} | {score['partial_event_count']} | {score['missed_event_count']} | {pillar_text} |"
        )
    lines.extend(["", "## 第一候选事件匹配", ""])
    for event in result["winner"]["event_scores"]:
        reason = "；".join(event["reasons"])
        lines.append(
            f"- {event['year']} {event['event_type_label']}：{event['label']}。"
            f"得分 {event['score']}；流年 {event['annual_ganzhi']}；原因：{reason}。"
        )
    lines.extend(["", "## 边界", "", "- 结果是事件拟合排序，不是出生时辰证明。", "- 事件来源越可靠，校准才越有意义。"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run 12-hour calibration for a public figure case.")
    parser.add_argument("case_json", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "outputs")
    args = parser.parse_args(argv)
    case = json.loads(args.case_json.read_text(encoding="utf-8"))
    result = calibrate_case(case)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = str(case.get("case_id") or args.case_json.stem)
    json_path = args.out_dir / f"{stem}.hour_calibration.json"
    md_path = args.out_dir / f"{stem}.hour_calibration.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "winner": result["winner"]["hour_label"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
