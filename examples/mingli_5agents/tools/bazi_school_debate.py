"""Deterministic BaZi school sub-agent debate rules.

The debate layer is intentionally rule-based. It does not claim predictive
truth; it records how each BaZi school would frame the same structured chart.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


SCHOOL_AGENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "ziping_pattern_agent",
        "name": "子平格局纸智能体",
        "school": "子平格局法",
        "primary_fields": ["pattern_analysis", "ten_god_distribution", "major_luck"],
        "supports": ["月令格局", "透干十神", "大运承接"],
    },
    {
        "id": "strength_support_agent",
        "name": "旺衰扶抑纸智能体",
        "school": "旺衰扶抑法",
        "primary_fields": ["strength_analysis", "useful_god_analysis"],
        "supports": ["日主状态", "扶抑取用", "五行平衡"],
    },
    {
        "id": "tiaohou_agent",
        "name": "调候纸智能体",
        "school": "调候法",
        "primary_fields": ["tiaohou_analysis", "useful_god_analysis"],
        "supports": ["月令季节", "寒暖燥湿", "环境调节"],
    },
    {
        "id": "tiyong_circulation_agent",
        "name": "体用流通纸智能体",
        "school": "体用气势法",
        "primary_fields": ["image_symbol_analysis", "useful_god_analysis", "strength_analysis"],
        "supports": ["体用保护", "用神保护链", "五行流通断点"],
    },
    {
        "id": "blind_symbol_agent",
        "name": "盲派象法纸智能体",
        "school": "盲派象法",
        "primary_fields": ["image_symbol_analysis", "hidden_stem_profile", "ten_god_distribution"],
        "supports": ["柱位宫位", "显象落事", "刑冲合害"],
    },
    {
        "id": "shensha_nayin_agent",
        "name": "神煞纳音纸智能体",
        "school": "神煞纳音辅助法",
        "primary_fields": ["nayin_growth_profile", "hidden_stem_profile"],
        "supports": ["纳音", "长生十二运", "辅助符号"],
    },
)


def build_bazi_school_debate(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Build an auditable debate among BaZi school sub-agents."""
    votes = [_school_vote(agent, deep, context) for agent in SCHOOL_AGENTS]
    conflicts = _conflicts(votes, deep)
    consensus = _consensus(votes, conflicts)
    material = {
        "schema_version": "bazi-school-debate-v1",
        "votes": votes,
        "conflicts": conflicts,
        "consensus": consensus,
        "case_validation_hooks": _case_validation_hooks(votes),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **material,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "agent_count": len(votes),
        "supported_school_count": sum(1 for item in votes if item["stance"] == "support"),
        "requires_fact_calibration": bool(conflicts) or any(item["confidence"] < 0.7 for item in votes),
    }


def _school_vote(agent: dict[str, Any], deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    fields = [field for field in agent["primary_fields"] if deep.get(field)]
    missing = [field for field in agent["primary_fields"] if not deep.get(field)]
    signals = _school_signals(str(agent["id"]), deep, context)
    confidence = _confidence(str(agent["id"]), deep, context, fields, missing, signals)
    stance = "support" if confidence >= 0.66 else "caution"
    return {
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "school": agent["school"],
        "stance": stance,
        "confidence": confidence,
        "claim": signals["claim"],
        "challenge": signals["challenge"],
        "evidence_fields": fields,
        "missing_fields": missing,
        "supports": agent["supports"],
        "method_rules": signals["rules"],
        "event_hypotheses": signals["event_hypotheses"],
        "calibration_questions": signals["calibration_questions"],
    }


def _confidence(
    agent_id: str,
    deep: dict[str, Any],
    context: dict[str, Any],
    fields: list[str],
    missing: list[str],
    signals: dict[str, Any],
) -> float:
    base = 0.5 + 0.07 * len(fields) - 0.05 * len(missing)
    provider = deep.get("provider") or context.get("provider")
    if provider and provider != "approximate":
        base += 0.08
    if signals.get("specific_signal_count", 0) >= 3:
        base += 0.08
    if agent_id == "shensha_nayin_agent":
        profile = deep.get("nayin_growth_profile", {})
        if isinstance(profile, dict) and profile.get("complete") is not True:
            base -= 0.12
    if agent_id == "blind_symbol_agent":
        base -= 0.03
    return max(0.1, min(0.95, round(base, 2)))


def _school_signals(agent_id: str, deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if agent_id == "ziping_pattern_agent":
        return _ziping_signals(deep)
    if agent_id == "strength_support_agent":
        return _strength_signals(deep, context)
    if agent_id == "tiaohou_agent":
        return _tiaohou_signals(deep)
    if agent_id == "tiyong_circulation_agent":
        return _tiyong_signals(deep, context)
    if agent_id == "blind_symbol_agent":
        return _blind_symbol_signals(deep)
    return _shensha_nayin_signals(deep)


def _ziping_signals(deep: dict[str, Any]) -> dict[str, Any]:
    pattern = _nested_get(deep, "pattern_analysis", "pattern") or "格局未明"
    month_ten_god = _nested_get(deep, "pattern_analysis", "month_ten_god") or "月令十神未明"
    distribution = deep.get("ten_god_distribution", {})
    leading = _leading(distribution)
    return _signal(
        claim=f"以月令和透干定主线，当前格局为{pattern}，月令重{month_ten_god}，显著十神为{leading}。",
        challenge="若真实事件和格局主线不符，应回到月令、透干、通根和大运重新定格。",
        rules=[
            "先看月令，再看透干，再看成格与破格。",
            "大运只承接或破坏原局主线，不单独创造命局。",
            "十神多不等于应事强，必须看是否透出、得令、得根。",
        ],
        event_hypotheses=[
            "格局稳定时，人生主题更容易在学历、职位、资源或输出中反复出现。",
            "格局被冲破时，常表现为阶段性换轨、身份变化或目标重置。",
        ],
        calibration_questions=["最高学历和专业方向是什么", "第一次明显转轨发生在哪一年"],
        count=3 if distribution else 2,
    )


def _strength_signals(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    strength = _nested_get(deep, "strength_analysis", "strength") or "强弱未明"
    dominant = _nested_get(deep, "strength_analysis", "dominant_element") or context.get("dominant_element", "主气未明")
    useful = _nested_get(deep, "useful_god_analysis", "useful_element") or context.get("useful_element", "用神未定")
    avoid = _nested_get(deep, "useful_god_analysis", "avoid_overweight_element") or dominant
    return _signal(
        claim=f"以旺衰扶抑看，日主状态为{strength}，主气偏{dominant}，取用倾向为{useful}，忌偏重{avoid}。",
        challenge="强弱不能单独定吉凶，必须接受体用保护、调候和事实校准约束。",
        rules=[
            "身旺重泄耗制，身弱重生扶助。",
            "用神被冲克时，顺势年份也会反复。",
            "忌神被再加强时，容易表现为情绪、健康、关系或执行过载。",
        ],
        event_hypotheses=[
            "用神到位的年份，学习、职业或资源安排更容易落地。",
            "忌神成势的年份，容易出现拖延、急躁、过劳或方向失控。",
        ],
        calibration_questions=["哪些年份明显顺利", "哪些年份身体或情绪压力最大"],
        count=3,
    )


def _tiaohou_signals(deep: dict[str, Any]) -> dict[str, Any]:
    season = _nested_get(deep, "tiaohou_analysis", "season") or "季节未明"
    bias = _nested_get(deep, "tiaohou_analysis", "climate_bias") or "气候偏性未明"
    adjustment = _nested_get(deep, "tiaohou_analysis", "adjustment") or "调候未定"
    return _signal(
        claim=f"以调候看，出生季节为{season}，气候偏性为{bias}，先取调候方向：{adjustment}。",
        challenge="调候是环境条件，不应替代格局、十神和岁运应事判断。",
        rules=[
            "夏生先看燥热，冬生先看寒湿，春秋看升降收放。",
            "调候到位，人才有稳定发挥环境。",
            "调候失衡，容易先表现为状态、睡眠、耐力和情绪。",
        ],
        event_hypotheses=[
            "调候得力时期，学习吸收和身体状态更稳。",
            "调候失衡时期，成绩或事业不一定立刻坏，但状态消耗会先出现。",
        ],
        calibration_questions=["睡眠和精力最差的年份是哪几年", "是否有季节性状态波动"],
        count=2 if season == "季节未明" else 3,
    )


def _tiyong_signals(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    useful = _nested_get(deep, "useful_god_analysis", "useful_element") or context.get("useful_element", "用神未定")
    support = _nested_get(deep, "useful_god_analysis", "supporting_element") or "保护未明"
    dominant = _nested_get(deep, "strength_analysis", "dominant_element") or context.get("dominant_element", "主气未明")
    return _signal(
        claim=f"以体用流通看，体为{dominant}，用为{useful}，保护或承接为{support}；重点看用神链是否被冲断。",
        challenge="没有具体事件时，保护链只能作为推理假设，不能当作事实。",
        rules=[
            "先定体，再定用，再查保护链。",
            "用神出现但无保护，事情容易开始而难收。",
            "忌神冲断保护链时，常见反复、延误或关系阻力。",
        ],
        event_hypotheses=[
            "保护链完整的阶段，项目、考试或职业更容易闭环。",
            "保护链断裂的阶段，常见计划变更、贵人失力或临场失误。",
        ],
        calibration_questions=["哪些年份开始顺但结尾不顺", "是否有临门失误或贵人失力的年份"],
        count=3,
    )


def _blind_symbol_signals(deep: dict[str, Any]) -> dict[str, Any]:
    image = deep.get("image_symbol_analysis", {})
    leading = image.get("leading_ten_god") if isinstance(image, dict) else "象法未明"
    pillars = image.get("pillar_images", []) if isinstance(image, dict) else []
    return _signal(
        claim=f"以象法看，显象十神为{leading}，柱位图像为{'、'.join(map(str, pillars)) or '柱象未明'}。",
        challenge="象法容易断得太满，必须保留证据字段和反例空间。",
        rules=[
            "年柱看家族环境和早年背景，月柱看学习职业环境，日柱看自我和亲密关系，时柱看长期结果。",
            "冲刑害优先落到对应柱位的人事场景。",
            "象法只负责提出场景假设，不能覆盖结构证据。",
        ],
        event_hypotheses=[
            "柱位受冲的年份，常对应环境、关系或居住学习场景变化。",
            "同一十神反复出现，常对应同类人事主题反复。",
        ],
        calibration_questions=["搬家、转学、换工作发生在哪些年份", "家庭关系明显变化在哪些年份"],
        count=2 + min(2, len(pillars)),
    )


def _shensha_nayin_signals(deep: dict[str, Any]) -> dict[str, Any]:
    profile = deep.get("nayin_growth_profile", {})
    complete = isinstance(profile, dict) and bool(profile.get("complete"))
    return _signal(
        claim="神煞纳音只作辅助标记，用来提醒特殊符号，不覆盖格局、用神和岁运主线。",
        challenge="神煞纳音权重最低，只能做补充提示，不能独立下重大断语。",
        rules=[
            "先结构后神煞，先岁运后纳音。",
            "神煞只在与格局、用神、事实三者同向时提高提示权重。",
            "资料不全时，神煞纳音不得进入主断。",
        ],
        event_hypotheses=[
            "辅助符号同向时，可作为风险或机会提示。",
            "辅助符号逆向时，优先服从结构判断。",
        ],
        calibration_questions=["是否有特殊年份反复出现同类主题", "辅助符号是否能被真实事件支持"],
        count=2 if complete else 1,
    )


def _signal(
    *,
    claim: str,
    challenge: str,
    rules: list[str],
    event_hypotheses: list[str],
    calibration_questions: list[str],
    count: int,
) -> dict[str, Any]:
    return {
        "claim": claim,
        "challenge": challenge,
        "rules": rules,
        "event_hypotheses": event_hypotheses,
        "calibration_questions": calibration_questions,
        "specific_signal_count": count,
    }


def _conflicts(votes: list[dict[str, Any]], deep: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    strength = _nested_get(deep, "strength_analysis", "strength")
    useful = _nested_get(deep, "useful_god_analysis", "useful_element")
    pattern_risk = _nested_get(deep, "pattern_analysis", "risk")
    climate = _nested_get(deep, "tiaohou_analysis", "climate_bias")
    if strength == "strong_day_master" and useful:
        conflicts.append(
            {
                "id": "strength_vs_useful_protection",
                "topic": "用神保护",
                "positions": ["旺衰派强调扶抑", "体用派强调保护链是否完整"],
                "resolution_rule": "优先检查用神是否被大运流年保护；不能只看强弱。",
            }
        )
    if pattern_risk and "validation" in str(pattern_risk):
        conflicts.append(
            {
                "id": "pattern_requires_fact_calibration",
                "topic": "事实校准",
                "positions": ["格局信号混杂", "象法可能给出强场景"],
                "resolution_rule": "要求重大年份事件回填后再提高断言强度。",
            }
        )
    if climate and strength == "balanced":
        conflicts.append(
            {
                "id": "balanced_structure_vs_climate_bias",
                "topic": "平衡与调候",
                "positions": ["结构看平衡", "调候仍提示气候偏性"],
                "resolution_rule": "结构平衡不等于状态稳定；健康、睡眠、耐力仍按调候校准。",
            }
        )
    low_confidence = [item["school"] for item in votes if item["confidence"] < 0.65]
    if low_confidence:
        conflicts.append(
            {
                "id": "low_confidence_school_votes",
                "topic": "流派置信度",
                "positions": low_confidence,
                "resolution_rule": "低置信流派只作辅助，不进入最终主断。",
            }
        )
    return conflicts


def _consensus(votes: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [
        item["school"]
        for item in votes
        if item["confidence"] >= 0.7 and item["school"] != "神煞纳音辅助法"
    ]
    auxiliary = [item["school"] for item in votes if item["school"] not in primary]
    rules = []
    for vote in votes:
        rules.extend(vote.get("method_rules", [])[:1])
    return {
        "primary_schools": primary,
        "auxiliary_schools": auxiliary,
        "conflict_count": len(conflicts),
        "decision": "needs_fact_calibration" if conflicts else "usable_symbolic_consensus",
        "rule": "主断采用高置信流派共识；冲突处保留分歧，并等待真实事件校准。",
        "synthesis_rules": rules,
    }


def _case_validation_hooks(votes: list[dict[str, Any]]) -> dict[str, Any]:
    topics = Counter()
    questions: list[str] = []
    for vote in votes:
        for item in vote.get("event_hypotheses", []):
            if "学习" in item or "考试" in item:
                topics["study_exam"] += 1
            if "职业" in item or "项目" in item:
                topics["career_project"] += 1
            if "家庭" in item or "关系" in item:
                topics["family_relation"] += 1
        questions.extend(vote.get("calibration_questions", []))
    return {
        "recommended_event_topics": dict(topics),
        "calibration_questions": list(dict.fromkeys(questions))[:10],
        "rule": "用名人或用户真实事件校验时，只比较结构化主题和年份，不把象法句子当作已验证事实。",
    }


def _leading(value: object) -> str:
    if not isinstance(value, dict) or not value:
        return "十神分布未明"
    key, count = max(value.items(), key=lambda item: int(item[1]))
    return f"{key}{count}处"


def _nested_get(value: object, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
