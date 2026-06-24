"""Method-lineage map for Mingli schools, classics, and implemented surfaces."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from examples.mingli_5agents.method_surface import REQUIRED_METHODS, method_surface_receipt


METHOD_LINEAGE: tuple[dict[str, Any], ...] = (
    {
        "id": "bazi_ziping_pattern",
        "tradition": "bazi",
        "school": "子平格局法",
        "classic_sources": ["渊海子平", "三命通会"],
        "research_sources": ["Ho Peng Yoke, Chinese Mathematical Astrology"],
        "implemented_methods": ["ziping_pattern", "strength_support"],
        "implemented_status": "implemented",
        "current_use": "以四柱、月令、日主、十神和格局作为八字主轴。",
        "gap": "格局取用仍需专业排盘引擎和真实事件校准增强。",
    },
    {
        "id": "bazi_strength_useful_god",
        "tradition": "bazi",
        "school": "旺衰扶抑派",
        "classic_sources": ["渊海子平", "三命通会"],
        "research_sources": ["Ho Peng Yoke, Chinese Mathematical Astrology"],
        "implemented_methods": ["strength_support", "new_school_simplified"],
        "implemented_status": "implemented",
        "current_use": "用日主、季节、五行分布和用神假设形成基础平衡判断。",
        "gap": "不能单独作为吉凶判断，需要被体用保护和事实校准约束。",
    },
    {
        "id": "bazi_tiaohou",
        "tradition": "bazi",
        "school": "调候法",
        "classic_sources": ["穷通宝鉴", "滴天髓阐微"],
        "research_sources": ["Ho Peng Yoke, Chinese Mathematical Astrology"],
        "implemented_methods": ["tiaohou"],
        "implemented_status": "implemented_scaffold",
        "current_use": "以季节寒暖燥湿辅助判断用神和状态。",
        "gap": "报告层尚未充分展开调候断语，需要更多季节性规则表。",
    },
    {
        "id": "bazi_tiyong_circulation",
        "tradition": "bazi",
        "school": "体用气势与五行流通法",
        "classic_sources": ["滴天髓阐微"],
        "research_sources": ["user-provided bazi-hierarchical-analysis note"],
        "implemented_methods": ["image_symbol_reading", "data_validation_boundary"],
        "implemented_status": "report_renderer_extension",
        "current_use": "以体、用、保护链、五行流通和断点解释年度事件。",
        "gap": "保护链还在报告生成层，尚未提升为核心结构化字段。",
    },
    {
        "id": "bazi_blind_symbolic",
        "tradition": "bazi",
        "school": "盲派象法",
        "classic_sources": ["三命通会"],
        "research_sources": ["Handbook of Divination and Prognostication in China"],
        "implemented_methods": ["blind_school_workflow", "image_symbol_reading"],
        "implemented_status": "implemented_scaffold",
        "current_use": "用柱位、宫位、伏吟、刑冲合害和年龄阶段把符号落到生活场景。",
        "gap": "当前只做象法提示，尚未形成成熟断事规则库。",
    },
    {
        "id": "bazi_shensha_nayin",
        "tradition": "bazi",
        "school": "神煞纳音辅助法",
        "classic_sources": ["三命通会"],
        "research_sources": ["Ho Peng Yoke, Chinese Mathematical Astrology"],
        "implemented_methods": ["shensha_nayin"],
        "implemented_status": "implemented_scaffold",
        "current_use": "只作为辅助符号，不覆盖格局、用神和岁运主线。",
        "gap": "缺少可审计神煞表和权重策略。",
    },
    {
        "id": "ziwei_palace_sihua",
        "tradition": "ziwei",
        "school": "紫微斗数十二宫与四化派",
        "classic_sources": ["紫微斗数全书"],
        "research_sources": ["Handbook of Divination and Prognostication in China"],
        "implemented_methods": [
            "ming_body_axis",
            "twelve_palace_theme",
            "triad_opposition",
            "four_transformations",
            "limit_annual_linkage",
        ],
        "implemented_status": "implemented_scaffold",
        "current_use": "以命身轴、十二宫、三方四正、四化和大限流年作为交叉验证。",
        "gap": "生产级紫微 provider 未闭环，不能作为主断依据。",
    },
    {
        "id": "qimen_plate_timing",
        "tradition": "qimen",
        "school": "奇门遁甲九宫时空盘法",
        "classic_sources": ["奇门遁甲秘笈大全", "烟波钓叟歌"],
        "research_sources": ["Ho Peng Yoke, Chinese Mathematical Astrology"],
        "implemented_methods": [
            "door_star_spirit",
            "heaven_earth_stem",
            "useful_god_topic_mapping",
            "pattern_risk",
            "annual_timing_activation",
        ],
        "implemented_status": "implemented_scaffold",
        "current_use": "以门、星、神、天地盘干、用神和九宫主题辅助观察时机。",
        "gap": "生产级奇门 provider 未闭环，落宫成象仍偏简化。",
    },
    {
        "id": "xuanze_tongshu",
        "tradition": "xuanze",
        "school": "通书择日法",
        "classic_sources": ["协纪辨方书"],
        "research_sources": ["Handbook of Divination and Prognostication in China"],
        "implemented_methods": [
            "twelve_officer",
            "twenty_eight_mansion",
            "huangdao_rating",
            "recommended_hours",
            "risk_boundary",
            "provider_quality",
        ],
        "implemented_status": "implemented_scaffold",
        "current_use": "以建除十二神、二十八宿、黄道黑道和时辰建议提供择日边界。",
        "gap": "缺生产级通书规则表和版本哈希。",
    },
    {
        "id": "audit_fact_calibration",
        "tradition": "governance",
        "school": "事实校准与可审计分析",
        "classic_sources": ["不属于传统经典"],
        "research_sources": ["ReAct", "Reflexion", "SWE-agent", "SEMAS project methodology"],
        "implemented_methods": ["data_validation_boundary"],
        "implemented_status": "implemented",
        "current_use": "把命理断语绑定到来源、结构化证据、哈希收据和用户事实反馈。",
        "gap": "需要真实重大事件数据集才能做校准验证。",
    },
)


def lineage_records() -> tuple[dict[str, Any], ...]:
    """Return immutable-style method-lineage records."""
    return METHOD_LINEAGE


def method_lineage_receipt() -> dict[str, Any]:
    """Return a stable receipt binding method lineage to required method surfaces."""
    material = {
        "schema_version": "mingli-method-lineage-v1",
        "method_surface_sha256": method_surface_receipt()["sha256"],
        "records": METHOD_LINEAGE,
        "implemented_method_domains": {domain: sorted(methods) for domain, methods in sorted(REQUIRED_METHODS.items())},
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "record_count": len(METHOD_LINEAGE),
        "traditions": sorted({str(row["tradition"]) for row in METHOD_LINEAGE}),
        "implemented_statuses": sorted({str(row["implemented_status"]) for row in METHOD_LINEAGE}),
        "material": material,
    }


def lineage_by_tradition() -> dict[str, list[dict[str, Any]]]:
    """Group lineage records for report rendering and audits."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in METHOD_LINEAGE:
        grouped.setdefault(str(row["tradition"]), []).append(row)
    return grouped
