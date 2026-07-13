"""八字分层命盘策略。

该模块把“原局策略”和“事件拟合”分开处理。它不把不同流派的意见
过早压成一个总分，而是先暴露格局、调候、病药、体用流通、宫位事件
和事实校准六层判断。
"""

from __future__ import annotations

from typing import Any


LAYER_ORDER = [
    "pattern_vote",
    "tiaohou_vote",
    "disease_medicine_vote",
    "tiyong_flow_vote",
    "palace_event_vote",
    "fact_calibration_vote",
]


def build_bazi_layered_strategy(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """生成不被简单平均吞掉的分层命盘策略。"""
    layers = [
        _pattern_vote(deep),
        _tiaohou_vote(deep),
        _disease_medicine_vote(deep, context),
        _tiyong_flow_vote(deep, context),
        _palace_event_vote(deep, context),
        _fact_calibration_vote(deep),
    ]
    conflicts = _strategy_conflicts(layers, deep)
    primary = _primary_strategy(layers, conflicts)
    return {
        "schema_version": "bazi-layered-strategy-v1",
        "rule": "先看格局、调候、病药、体用流通、宫位事件、事实校准六层意见，再进入流年流月推断。",
        "layers": layers,
        "conflicts": conflicts,
        "primary_strategy": primary,
        "report_policy": {
            "use_in_reports": True,
            "annual_rule": "流年判断必须说明被触发的是哪一层；不能只凭一个冲合就下结论。",
            "monthly_rule": "流月判断必须独立检查天干、地支、五行流通、十神主题和刑冲合害关系。",
            "hour_calibration_rule": "事件拟合只领先很小时，不能直接推翻公开参考时辰，必须说明分歧来源。",
        },
    }


def _pattern_vote(deep: dict[str, Any]) -> dict[str, Any]:
    pattern = _nested_get(deep, "pattern_analysis", "pattern") or "未定"
    month_ten_god = _nested_get(deep, "pattern_analysis", "month_ten_god") or "未定"
    risk = _nested_get(deep, "pattern_analysis", "risk") or "需要事件校准"
    confidence = 0.72 if pattern != "未定" and month_ten_god != "未定" else 0.48
    return _layer(
        "pattern_vote",
        "格局票",
        confidence,
        f"以月令和透干定主线：{pattern}；月令十神为{month_ten_god}。",
        f"格局风险：{risk}。如果真实年份不吻合，先重新定格局。",
        ["pattern_analysis", "ten_god_distribution", "major_luck"],
    )


def _tiaohou_vote(deep: dict[str, Any]) -> dict[str, Any]:
    season = _nested_get(deep, "tiaohou_analysis", "season") or "未定"
    bias = _nested_get(deep, "tiaohou_analysis", "climate_bias") or "未定"
    adjustment = _nested_get(deep, "tiaohou_analysis", "adjustment") or "未定"
    confidence = 0.7 if season != "未定" else 0.45
    return _layer(
        "tiaohou_vote",
        "调候票",
        confidence,
        f"出生季节为{season}，气候偏性为{bias}。",
        f"调候方向：{adjustment}。调候决定状态和发挥条件，不单独决定富贵。",
        ["tiaohou_analysis", "useful_god_analysis", "season", "solar_term"],
    )


def _disease_medicine_vote(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    strength = _nested_get(deep, "strength_analysis", "strength") or "未定"
    dominant = _nested_get(deep, "strength_analysis", "dominant_element") or context.get("dominant_element", "未定")
    useful = _nested_get(deep, "useful_god_analysis", "useful_element") or context.get("useful_element", "未定")
    avoid = _nested_get(deep, "useful_god_analysis", "avoid_overweight_element") or dominant
    if strength in {"strong_day_master", "externally_weighted"}:
        disease = f"{dominant}偏重或结构压力过强"
    else:
        disease = "病点不能只按日主强弱确定"
    confidence = 0.68 if useful != "未定" else 0.45
    return _layer(
        "disease_medicine_vote",
        "病药票",
        confidence,
        f"病点：{disease}；药神倾向：{useful}；忌偏重：{avoid}。",
        "流年流月要看药到病除、病重药轻、药被冲破，不能只看吉凶词。",
        ["strength_analysis", "useful_god_analysis", "element_counts"],
    )


def _tiyong_flow_vote(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    dominant = _nested_get(deep, "strength_analysis", "dominant_element") or context.get("dominant_element", "未定")
    useful = _nested_get(deep, "useful_god_analysis", "useful_element") or context.get("useful_element", "未定")
    support = _nested_get(deep, "useful_god_analysis", "supporting_element") or "未定"
    confidence = 0.66 if useful != "未定" and support != "未定" else 0.45
    return _layer(
        "tiyong_flow_vote",
        "体用流通票",
        confidence,
        f"体为{dominant}，用为{useful}，保护或承接为{support}。",
        "判断成败时先看保护链是否完整，再看流年是否冲断或修复。",
        ["image_symbol_analysis", "useful_god_analysis", "strength_analysis"],
    )


def _palace_event_vote(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    pillars = context.get("pillars", {}) if isinstance(context.get("pillars"), dict) else {}
    hour = pillars.get("hour", "")
    day = pillars.get("day", "")
    confidence = 0.6 if hour and day else 0.4
    return _layer(
        "palace_event_vote",
        "宫位事件票",
        confidence,
        f"日柱主自身与婚姻近身关系，时柱主子女、晚年、长期结果；当前日柱{day}，时柱{hour}。",
        "婚姻、子女、迁移、健康事件必须看对应柱位触发，不能只看事件标签。",
        ["pillars", "hidden_stem_profile", "branch_interactions"],
    )


def _fact_calibration_vote(deep: dict[str, Any]) -> dict[str, Any]:
    status = _nested_get(deep, "data_validation_analysis", "status") or "未记录"
    return _layer(
        "fact_calibration_vote",
        "事实校准票",
        0.35,
        f"事实校准状态：{status}。",
        "没有真实事件表时，只能给结构判断；有事件表时必须记录命中、矛盾和反例年份。",
        ["data_validation_analysis", "known_events", "case_validation_hooks"],
    )


def _layer(
    layer_id: str,
    name: str,
    confidence: float,
    claim: str,
    caution: str,
    evidence_fields: list[str],
) -> dict[str, Any]:
    return {
        "id": layer_id,
        "name": name,
        "confidence": round(confidence, 2),
        "claim": claim,
        "caution": caution,
        "evidence_fields": evidence_fields,
    }


def _strategy_conflicts(layers: list[dict[str, Any]], deep: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    strength = _nested_get(deep, "strength_analysis", "strength")
    season = _nested_get(deep, "tiaohou_analysis", "season")
    useful = _nested_get(deep, "useful_god_analysis", "useful_element")
    if strength == "balanced" and season in {"winter", "summer"}:
        conflicts.append(
            {
                "id": "balanced_structure_vs_climate",
                "topic": "结构均衡与季节偏性冲突",
                "resolution": "结构均衡不等于状态均衡；冬夏生人仍需优先保留调候判断。",
            }
        )
    if useful and strength == "strong_day_master":
        conflicts.append(
            {
                "id": "useful_god_requires_protection",
                "topic": "用神出现但需要保护",
                "resolution": "旺局见用神不能直接判好，必须看用神是否被大运流年保护。",
            }
        )
    low = [item["name"] for item in layers if float(item.get("confidence", 0.0)) < 0.5]
    if low:
        conflicts.append(
            {
                "id": "low_confidence_layers",
                "topic": "低置信层",
                "layers": low,
                "resolution": "低置信层只能提出校准问题，不进入强断。",
            }
        )
    return conflicts


def _primary_strategy(layers: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    high = [item for item in layers if float(item.get("confidence", 0.0)) >= 0.66]
    return {
        "decision": "分层共识但保留冲突" if conflicts else "分层共识",
        "primary_layers": [item["id"] for item in high],
        "conflict_count": len(conflicts),
        "minimum_report_requirements": [
            "先说明格局主线，再说流年结论",
            "健康、学习和状态判断前必须说明调候",
            "强吉强凶判断前必须说明病药机制",
            "婚姻、子女、迁移、死亡等主题必须给出柱位或宫位证据",
            "缺少事实校准的预测必须降低断言强度",
        ],
    }


def _nested_get(value: object, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
