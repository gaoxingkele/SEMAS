"""Deterministic BaZi school sub-agent debate scaffold."""

from __future__ import annotations

import hashlib
import json
from typing import Any


SCHOOL_AGENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "ziping_pattern_agent",
        "name": "子平格局纸智能体",
        "school": "子平格局法",
        "primary_fields": ["pattern_analysis", "ten_god_distribution", "major_luck"],
        "supports": ["格局", "十神", "大运"],
    },
    {
        "id": "strength_support_agent",
        "name": "旺衰扶抑纸智能体",
        "school": "旺衰扶抑法",
        "primary_fields": ["strength_analysis", "useful_god_analysis"],
        "supports": ["日主强弱", "用神", "五行平衡"],
    },
    {
        "id": "tiaohou_agent",
        "name": "调候纸智能体",
        "school": "调候法",
        "primary_fields": ["tiaohou_analysis", "useful_god_analysis"],
        "supports": ["月令", "寒暖燥湿", "气候调节"],
    },
    {
        "id": "tiyong_circulation_agent",
        "name": "体用流通纸智能体",
        "school": "体用气势法",
        "primary_fields": ["image_symbol_analysis", "useful_god_analysis", "strength_analysis"],
        "supports": ["体用", "保护链", "五行流通"],
    },
    {
        "id": "blind_symbol_agent",
        "name": "盲派象法纸智能体",
        "school": "盲派象法",
        "primary_fields": ["image_symbol_analysis", "hidden_stem_profile", "ten_god_distribution"],
        "supports": ["柱位", "象法", "刑冲合害"],
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
    confidence = _confidence(agent["id"], deep, context, fields, missing)
    stance = "support" if confidence >= 0.55 else "caution"
    claim = _claim(agent["id"], deep, context)
    challenge = _challenge(agent["id"], deep, context)
    return {
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "school": agent["school"],
        "stance": stance,
        "confidence": confidence,
        "claim": claim,
        "challenge": challenge,
        "evidence_fields": fields,
        "missing_fields": missing,
        "supports": agent["supports"],
    }


def _confidence(
    agent_id: str,
    deep: dict[str, Any],
    context: dict[str, Any],
    fields: list[str],
    missing: list[str],
) -> float:
    base = 0.5 + 0.08 * len(fields) - 0.06 * len(missing)
    provider = deep.get("provider") or context.get("provider")
    if provider and provider != "approximate":
        base += 0.08
    if agent_id == "shensha_nayin_agent":
        profile = deep.get("nayin_growth_profile", {})
        if isinstance(profile, dict) and profile.get("complete") is not True:
            base -= 0.12
    if agent_id == "blind_symbol_agent":
        base -= 0.04
    return max(0.1, min(0.95, round(base, 2)))


def _claim(agent_id: str, deep: dict[str, Any], context: dict[str, Any]) -> str:
    if agent_id == "ziping_pattern_agent":
        pattern = deep.get("pattern_analysis", {}).get("pattern", "格局未明")
        return f"以格局和月令为主，当前判断为：{pattern}。"
    if agent_id == "strength_support_agent":
        strength = deep.get("strength_analysis", {}).get("strength", "强弱未明")
        useful = deep.get("useful_god_analysis", {}).get("useful_element", context.get("useful_element", "未定"))
        return f"以旺衰扶抑看，日主状态为{strength}，用神假设偏{useful}。"
    if agent_id == "tiaohou_agent":
        adjustment = deep.get("tiaohou_analysis", {}).get("adjustment", "调候依据不足")
        return f"以调候看，先处理季节气候偏性：{adjustment}。"
    if agent_id == "tiyong_circulation_agent":
        useful = deep.get("useful_god_analysis", {}).get("useful_element", context.get("useful_element", "未定"))
        dominant = deep.get("strength_analysis", {}).get("dominant_element", context.get("dominant_element", "未定"))
        return f"以体用流通看，主气为{dominant}，用处偏{useful}，重点是保护链是否被冲破。"
    if agent_id == "blind_symbol_agent":
        image = deep.get("image_symbol_analysis", {}).get("summary", "象法依据不足")
        return f"以象法看，柱位和显象提示：{image}。"
    return "神煞纳音只作辅助标记，不覆盖格局、用神和岁运主线。"


def _challenge(agent_id: str, deep: dict[str, Any], context: dict[str, Any]) -> str:
    if agent_id == "ziping_pattern_agent":
        return "若真实事件与格局主线不符，应回到月令、透干和大运重新定格。"
    if agent_id == "strength_support_agent":
        return "强弱不能单独定吉凶，必须接受体用保护和事实校准约束。"
    if agent_id == "tiaohou_agent":
        return "调候是环境条件，不应替代十神、格局和岁运事件判断。"
    if agent_id == "tiyong_circulation_agent":
        return "若缺少具体事件，保护链只能作为推理假设，不能当作事实。"
    if agent_id == "blind_symbol_agent":
        return "象法容易断得太满，必须保留证据字段和反例空间。"
    return "神煞纳音权重最低，只能做补充提示。"


def _conflicts(votes: list[dict[str, Any]], deep: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    strength = deep.get("strength_analysis", {}).get("strength")
    useful = deep.get("useful_god_analysis", {}).get("useful_element")
    pattern_risk = deep.get("pattern_analysis", {}).get("risk")
    if strength == "strong_day_master" and useful:
        conflicts.append(
            {
                "id": "strength_vs_useful_protection",
                "topic": "用神保护",
                "positions": ["旺衰派强调扶抑", "体用派强调保护链是否完整"],
                "resolution_rule": "优先检查用神是否被大运流年保护；不只看强弱。",
            }
        )
    if pattern_risk and "event validation" in str(pattern_risk):
        conflicts.append(
            {
                "id": "pattern_requires_fact_calibration",
                "topic": "事实校准",
                "positions": ["格局信号混杂", "象法可能给出强断语"],
                "resolution_rule": "要求用户重大年份事件回填后再提高断言强度。",
            }
        )
    low_confidence = [item["school"] for item in votes if item["confidence"] < 0.65]
    if low_confidence:
        conflicts.append(
            {
                "id": "low_confidence_school_votes",
                "topic": "流派置信度",
                "positions": low_confidence,
                "resolution_rule": "低置信流派只能作为辅助，不进入最终主断。",
            }
        )
    return conflicts


def _consensus(votes: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [
        item["school"]
        for item in votes
        if item["confidence"] >= 0.7 and item["school"] not in {"神煞纳音辅助法"}
    ]
    auxiliary = [item["school"] for item in votes if item["school"] not in primary]
    return {
        "primary_schools": primary,
        "auxiliary_schools": auxiliary,
        "conflict_count": len(conflicts),
        "decision": "needs_fact_calibration" if conflicts else "usable_symbolic_consensus",
        "rule": "主断采用高置信流派共识；冲突处保留分歧，并等待真实事件校准。",
    }
