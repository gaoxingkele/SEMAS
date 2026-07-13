"""AHP scoring profiles for major BaZi schools.

The scorer is a deterministic comparison tool. It does not claim the schools
are empirically true; it turns each book-school's decision emphasis into a
stable set of votes so case studies can compare them consistently.
"""

from __future__ import annotations

from typing import Any


SCHOOL_PROFILES: dict[str, dict[str, Any]] = {
    "yuanhai_ziping": {
        "name": "渊海子平",
        "logic": "月令立纲、十神定位、透干通根、格局清浊、岁运承接。",
        "weights": {
            "month_command": 0.22,
            "ten_god_structure": 0.20,
            "stem_root": 0.18,
            "pattern_purity": 0.14,
            "luck_continuity": 0.12,
            "annual_trigger": 0.10,
            "fact_quality": 0.04,
        },
    },
    "ziping_zhenquan": {
        "name": "子平真诠",
        "logic": "格局成败、用神清纯、忌神有制、喜神有护、运来成败转换。",
        "weights": {
            "pattern_success": 0.26,
            "useful_god_clarity": 0.20,
            "rescue_control": 0.18,
            "pattern_purity": 0.14,
            "luck_continuity": 0.10,
            "annual_trigger": 0.08,
            "fact_quality": 0.04,
        },
    },
    "sanming_tonghui": {
        "name": "三命通会",
        "logic": "格局、神煞、纳音、刑冲合害、古诀类目并看，但主次分明。",
        "weights": {
            "broad_pattern_scan": 0.18,
            "shensha_symbol": 0.14,
            "nayin_symbol": 0.10,
            "branch_relation": 0.18,
            "event_topic": 0.16,
            "luck_continuity": 0.12,
            "fact_quality": 0.12,
        },
    },
    "ditiansui": {
        "name": "滴天髓",
        "logic": "气势流通、体用保护、清浊顺逆、断点修复或反噬。",
        "weights": {
            "qi_momentum": 0.24,
            "body_use_flow": 0.22,
            "clarity_turbidity": 0.16,
            "breakpoint_repair": 0.16,
            "luck_continuity": 0.10,
            "annual_trigger": 0.08,
            "fact_quality": 0.04,
        },
    },
    "qiongtong_baojian": {
        "name": "穷通宝鉴",
        "logic": "月令气候优先，寒暖燥湿得调后再谈格局发挥。",
        "weights": {
            "season_climate": 0.28,
            "first_adjuster": 0.22,
            "adjuster_protection": 0.16,
            "state_performance": 0.14,
            "luck_climate": 0.10,
            "annual_trigger": 0.06,
            "fact_quality": 0.04,
        },
    },
    "shenfeng_tongkao": {
        "name": "神峰通考",
        "logic": "先找病点，再找药神，岁运看药到病除、病重药轻或药被冲破。",
        "weights": {
            "disease_identification": 0.24,
            "medicine_presence": 0.22,
            "medicine_protection": 0.18,
            "disease_medicine_event": 0.16,
            "luck_continuity": 0.10,
            "annual_trigger": 0.06,
            "fact_quality": 0.04,
        },
    },
    "hengmen": {
        "name": "格局横门断",
        "logic": "横向比较多种格局，用月令、透干、成败救应和事实年份筛选强断。",
        "weights": {
            "month_pattern": 0.18,
            "stem_root": 0.14,
            "success_rescue": 0.18,
            "event_ten_god": 0.16,
            "palace_trigger": 0.12,
            "luck_support": 0.10,
            "annual_interaction": 0.08,
            "fact_calibration": 0.04,
        },
    },
}


EXTENDED_BAZI_METHODS = [
    "早期禄命纳音派",
    "神煞派",
    "盲派象法",
    "宫位六亲派",
    "刑冲合害穿破派",
    "旺衰扶抑派",
    "从格专论派",
    "化气格专论派",
    "格局派",
    "调候派",
    "病药派",
    "气势流通派",
    "岁运应期派",
    "现代新派量化派",
]


EXTENDED_SCHOOL_PROFILES: dict[str, dict[str, Any]] = {
    "early_luming_nayin": {
        "name": "早期禄命纳音派",
        "logic": "以年命、纳音、禄马、三命消息、寿夭贵贱为早期入口，重年命和五行消息。",
        "sources": [
            "李虚中命书",
            "珞琭子三命消息赋注",
            "玉照定真经",
            "命理集成",
        ],
        "weights": {
            "year_life_root": 0.22,
            "nayin_relation": 0.20,
            "lu_ma_noble": 0.16,
            "three_fate_message": 0.16,
            "five_element_life_death": 0.12,
            "annual_trigger": 0.10,
            "fact_quality": 0.04,
        },
    },
    "shensha": {
        "name": "神煞派",
        "logic": "以天乙、文昌、桃花、驿马、华盖、羊刃、灾煞等辅助定事件性质，不替代格局。",
        "sources": ["三命通会", "星平会海", "命理集成", "GitHub chxb/shensha"],
        "weights": {
            "core_shensha_hit": 0.24,
            "event_shensha_match": 0.22,
            "good_bad_balance": 0.14,
            "palace_landing": 0.14,
            "luck_activation": 0.12,
            "anti_overfit": 0.10,
            "fact_quality": 0.04,
        },
    },
    "blind_symbol": {
        "name": "盲派象法",
        "logic": "重宫位、宾主、做功、穿倒、干支象、直接落事，强调断事和应期。",
        "sources": ["现代盲派口传资料", "GitHub taibu 盲派分析实现"],
        "weights": {
            "palace_image": 0.20,
            "host_guest_work": 0.20,
            "branch_pierce_damage": 0.18,
            "direct_event_symbol": 0.18,
            "timing_response": 0.12,
            "counter_evidence": 0.08,
            "fact_quality": 0.04,
        },
    },
    "palace_kinship": {
        "name": "宫位六亲派",
        "logic": "年月日时对应祖上父母、环境事业、自己婚姻、子女晚年，事件必须落宫。",
        "sources": ["子平系宫位法", "盲派宫位法", "三命通会六亲类目"],
        "weights": {
            "pillar_palace_match": 0.28,
            "kinship_ten_god_match": 0.22,
            "branch_relation": 0.16,
            "major_luck_palace": 0.12,
            "annual_trigger": 0.10,
            "age_stage_logic": 0.08,
            "fact_quality": 0.04,
        },
    },
    "branch_relation": {
        "name": "刑冲合害穿破派",
        "logic": "专看地支合冲刑害破穿、三合三会六合六冲与宫位落事。",
        "sources": ["三命通会", "子平真诠", "GitHub 排盘项目刑冲合害实现"],
        "weights": {
            "relation_presence": 0.24,
            "relation_severity": 0.20,
            "palace_landing": 0.18,
            "hidden_stem_effect": 0.14,
            "combination_transformation": 0.10,
            "timing_response": 0.10,
            "fact_quality": 0.04,
        },
    },
    "strength_support": {
        "name": "旺衰扶抑派",
        "logic": "以日主旺衰、得令得地得助、扶抑泄耗制化判断喜忌和承载力。",
        "sources": ["现代子平旺衰法", "GitHub bazifuzugongju", "GitHub divicast bazi module"],
        "weights": {
            "day_master_strength": 0.24,
            "season_support": 0.18,
            "root_and_assist": 0.16,
            "drain_control_balance": 0.16,
            "useful_god_alignment": 0.12,
            "luck_adjustment": 0.10,
            "fact_quality": 0.04,
        },
    },
    "follow_special": {
        "name": "从格专论派",
        "logic": "判断是否弃命从势，从财、从杀、从儿、从旺等必须纯而不杂。",
        "sources": ["子平真诠", "三命通会", "现代特殊格局资料"],
        "weights": {
            "dominant_force": 0.24,
            "abandon_self_condition": 0.20,
            "purity_no_rescue": 0.18,
            "followed_god_event": 0.16,
            "luck_follow_or_break": 0.12,
            "counter_evidence": 0.06,
            "fact_quality": 0.04,
        },
    },
    "transformation_qi": {
        "name": "化气格专论派",
        "logic": "看天干五合是否有月令气势、地支会局和岁运扶成，成化则按化神论。",
        "sources": ["子平真诠", "三命通会", "现代化气格资料"],
        "weights": {
            "stem_combination": 0.20,
            "month_qi_support": 0.22,
            "branch_session_support": 0.18,
            "transformed_god_event": 0.16,
            "luck_complete_or_break": 0.12,
            "false_transformation_check": 0.08,
            "fact_quality": 0.04,
        },
    },
    "luck_timing": {
        "name": "岁运应期派",
        "logic": "大运定十年场景，流年定事件，流月定临场触发，重应期链条。",
        "sources": ["子平诸书岁运法", "三命通会", "GitHub 排盘流年流月实现"],
        "weights": {
            "major_luck_theme": 0.24,
            "annual_trigger": 0.20,
            "monthly_trigger_need": 0.14,
            "original_chart_node": 0.16,
            "event_topic_match": 0.12,
            "false_positive_control": 0.10,
            "fact_quality": 0.04,
        },
    },
    "modern_quant": {
        "name": "现代新派量化派",
        "logic": "把旺衰、五行、十神、合冲、神煞、岁运转成可复验指标，重一致性和可测试性。",
        "sources": ["GitHub bazi-calculator", "GitHub divicast", "GitHub yuhr123/bazi", "GitHub tianji"],
        "weights": {
            "feature_completeness": 0.18,
            "strength_score": 0.16,
            "relationship_score": 0.16,
            "event_classifier": 0.16,
            "timing_score": 0.14,
            "calibration_metric": 0.16,
            "fact_quality": 0.04,
        },
    },
}


def score_all_bazi_schools(
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        school_id: score_bazi_school_event(school_id, event, annual_row, bazi)
        for school_id in SCHOOL_PROFILES
    }


def extended_bazi_method_catalog() -> dict[str, dict[str, Any]]:
    """Return second-batch BaZi method profiles for library/orchestration use."""
    return EXTENDED_SCHOOL_PROFILES


def score_bazi_school_event(
    school_id: str,
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
) -> dict[str, Any]:
    profile = SCHOOL_PROFILES[school_id]
    votes = [
        _vote(vote_id, _vote_score(vote_id, event, annual_row, bazi), _vote_basis(vote_id))
        for vote_id in profile["weights"]
    ]
    score = _weighted(votes, profile["weights"])
    return {
        "school_id": school_id,
        "school_name": profile["name"],
        "logic": profile["logic"],
        "score": score,
        "votes": votes,
    }


def aggregate_school_scores(
    school_event_scores: list[dict[str, dict[str, Any]]],
    events: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for school_id, profile in SCHOOL_PROFILES.items():
        total = 0.0
        total_weight = 0.0
        for event_scores, event in zip(school_event_scores, events):
            weight = float(event.get("weight", 1.0) or 1.0)
            total += float(event_scores[school_id]["score"]) * weight
            total_weight += weight
        totals[school_id] = {
            "school_name": profile["name"],
            "score": round(total / max(total_weight, 0.001), 4),
            "logic": profile["logic"],
        }
    return totals


def _vote(vote_id: str, score: float, basis: str) -> dict[str, Any]:
    return {
        "id": vote_id,
        "score": round(max(0.0, min(1.0, score)), 4),
        "basis": basis,
    }


def _weighted(votes: list[dict[str, Any]], weights: dict[str, float]) -> float:
    total = 0.0
    weight_sum = 0.0
    for vote in votes:
        weight = weights[str(vote["id"])]
        total += float(vote["score"]) * weight
        weight_sum += weight
    return round(total / max(weight_sum, 0.001), 4)


def _vote_score(vote_id: str, event: dict[str, Any], annual_row: dict[str, Any], bazi: dict[str, Any]) -> float:
    deep = bazi.get("deep_analysis", {}) if isinstance(bazi, dict) else {}
    context = bazi.get("context", {}) if isinstance(bazi, dict) else {}
    event_type = str(event.get("type", ""))
    category = str(annual_row.get("category", "")) if isinstance(annual_row, dict) else ""
    intensity = str(annual_row.get("intensity", "")) if isinstance(annual_row, dict) else ""
    markers = annual_row.get("event_markers", {}) if isinstance(annual_row, dict) else {}
    evidence = annual_row.get("bazi_evidence", {}) if isinstance(annual_row, dict) else {}
    interactions = evidence.get("branch_interactions", []) if isinstance(evidence, dict) else []
    annual_ten_gods = evidence.get("annual_ten_gods", {}) if isinstance(evidence, dict) else {}
    luck = evidence.get("active_major_luck", {}) if isinstance(evidence, dict) else {}

    if vote_id in {"month_command", "month_pattern", "season_climate"}:
        return _month_or_season_score(deep, context)
    if vote_id in {"ten_god_structure", "event_ten_god", "event_topic"}:
        return _event_topic_score(event_type, category, annual_ten_gods, markers)
    if vote_id == "stem_root":
        return _stem_root_score(deep, context)
    if vote_id in {"pattern_purity", "pattern_success", "success_rescue", "rescue_control", "broad_pattern_scan"}:
        return _pattern_success_score(deep)
    if vote_id in {"useful_god_clarity", "first_adjuster", "adjuster_protection", "medicine_presence", "medicine_protection"}:
        return _useful_or_medicine_score(deep, annual_row)
    if vote_id in {"luck_continuity", "luck_support", "luck_climate"}:
        return 0.64 if isinstance(luck, dict) and luck.get("ganzhi") else 0.42
    if vote_id in {"annual_trigger", "annual_interaction", "branch_relation", "palace_trigger"}:
        return _interaction_score(event_type, interactions)
    if vote_id in {"fact_quality", "fact_calibration"}:
        return _fact_score(event)
    if vote_id in {"qi_momentum", "body_use_flow", "clarity_turbidity", "breakpoint_repair"}:
        return _flow_score(deep, annual_row)
    if vote_id in {"disease_identification", "disease_medicine_event"}:
        return _disease_score(event_type, intensity, markers, interactions)
    if vote_id in {"state_performance"}:
        return _state_performance_score(event_type, intensity, category)
    if vote_id in {"shensha_symbol", "nayin_symbol"}:
        return 0.52 if interactions else 0.42
    return 0.5


def _month_or_season_score(deep: dict[str, Any], context: dict[str, Any]) -> float:
    pattern = _nested_get(deep, "pattern_analysis", "pattern")
    month_ten_god = _nested_get(deep, "pattern_analysis", "month_ten_god")
    season = _nested_get(deep, "tiaohou_analysis", "season")
    if pattern and month_ten_god and season:
        return 0.76
    if pattern or month_ten_god or season:
        return 0.58
    if context.get("month_pillar"):
        return 0.5
    return 0.42


def _event_topic_score(event_type: str, category: str, annual_ten_gods: dict[str, Any], markers: dict[str, Any]) -> float:
    topic_categories = {
        "study_exam": {"learning", "authority"},
        "career_launch": {"expression", "authority", "wealth"},
        "role_power": {"authority"},
        "role_transition": {"authority", "expression", "friends", "learning"},
        "business_power": {"wealth", "authority"},
        "relationship": {"friends", "wealth"},
        "movement": {"friends", "authority", "expression"},
        "public_visibility": {"expression", "authority", "friends"},
        "award_peak": {"authority", "learning", "expression"},
        "box_office_breakthrough": {"wealth", "expression", "authority"},
        "iconic_role": {"expression", "authority", "friends"},
        "career_reinvention": {"expression", "authority", "learning", "friends"},
        "public_scandal": {"friends", "expression", "authority"},
        "health_crisis": {"resource", "authority"},
        "health_pressure": {"resource", "authority"},
        "death": {"resource", "authority", "expression"},
    }
    if category in topic_categories.get(event_type, set()):
        return 0.78
    values = {str(value) for value in annual_ten_gods.values()} if isinstance(annual_ten_gods, dict) else set()
    if values:
        return 0.56
    if markers.get(event_type):
        return 0.72
    return 0.42


def _stem_root_score(deep: dict[str, Any], context: dict[str, Any]) -> float:
    ten_gods = deep.get("ten_god_distribution") or context.get("ten_god_distribution") or {}
    hidden = deep.get("hidden_stem_profile") or {}
    count = 0
    if isinstance(ten_gods, dict):
        count += min(3, len([value for value in ten_gods.values() if value]))
    if isinstance(hidden, dict) and hidden.get("total_hidden_stems"):
        count += 2
    return min(0.82, 0.42 + count * 0.08)


def _pattern_success_score(deep: dict[str, Any]) -> float:
    debate = deep.get("school_debate", {})
    conflicts = debate.get("conflicts", []) if isinstance(debate, dict) else []
    consensus = debate.get("consensus", {}) if isinstance(debate, dict) else {}
    pattern = _nested_get(deep, "pattern_analysis", "pattern")
    if conflicts:
        return 0.48
    if consensus and pattern:
        return 0.72
    if consensus or pattern:
        return 0.62
    return 0.52


def _useful_or_medicine_score(deep: dict[str, Any], annual_row: dict[str, Any]) -> float:
    useful = _nested_get(deep, "useful_god_analysis", "useful_element")
    row_text = str(annual_row)
    if useful and useful in row_text:
        return 0.74
    if useful:
        return 0.58
    return 0.44


def _interaction_score(event_type: str, interactions: list[dict[str, Any]]) -> float:
    if not interactions:
        return 0.38
    event_pillars = {
        "relationship": {"day", "hour"},
        "family": {"year", "day", "hour"},
        "death": {"day", "hour"},
        "health_crisis": {"day", "hour"},
        "public_scandal": {"year", "month", "day"},
        "career_launch": {"month", "hour"},
        "role_power": {"year", "month"},
        "award_peak": {"year", "month"},
        "box_office_breakthrough": {"year", "month", "hour"},
        "iconic_role": {"year", "month", "hour"},
    }.get(event_type, {"year", "month", "day", "hour"})
    pillars = {str(item.get("pillar", "")) for item in interactions}
    severe = {"clash", "punishment", "harm"}
    relations = {str(item.get("relation", "")) for item in interactions}
    score = 0.56
    if pillars & event_pillars:
        score += 0.18
    if relations & severe:
        score += 0.08
    return min(score, 0.84)


def _flow_score(deep: dict[str, Any], annual_row: dict[str, Any]) -> float:
    useful = _nested_get(deep, "useful_god_analysis", "useful_element")
    pattern = _nested_get(deep, "pattern_analysis", "pattern")
    if useful and useful in str(annual_row):
        return 0.74
    if useful and pattern:
        return 0.62
    if useful or pattern:
        return 0.54
    return 0.44


def _disease_score(event_type: str, intensity: str, markers: dict[str, Any], interactions: list[dict[str, Any]]) -> float:
    crisis = event_type in {"death", "health_crisis", "health_pressure", "public_scandal", "scandal"}
    if crisis and (intensity == "high-volatility" or markers.get("health_pressure")):
        return 0.78
    if crisis and interactions:
        return 0.66
    if intensity == "high-volatility":
        return 0.58
    return 0.46


def _state_performance_score(event_type: str, intensity: str, category: str) -> float:
    if event_type in {"study_exam", "health_crisis", "health_pressure"} and intensity:
        return 0.68
    if event_type in {"career_launch", "award_peak", "public_visibility"} and category in {"authority", "expression"}:
        return 0.64
    return 0.5


def _fact_score(event: dict[str, Any]) -> float:
    source = str(event.get("source", ""))
    label = str(event.get("label", ""))
    year = event.get("year")
    if year and source.startswith("http") and label:
        return 0.82
    if year and label:
        return 0.62
    return 0.4


def _vote_basis(vote_id: str) -> str:
    return {
        "month_command": "以月令立纲，看主气是否能统领全局。",
        "ten_god_structure": "看十神是否对应事件主题，而不是只看名称。",
        "stem_root": "看关键力量是否透干、通根、能落地。",
        "pattern_purity": "看格局是否清纯，混杂冲破则降权。",
        "luck_continuity": "看大运是否承接原局主线。",
        "annual_trigger": "看流年是否真正触发关键节点。",
        "fact_quality": "看事件年份和来源是否可靠。",
        "pattern_success": "看格局成败，而不是只看身强身弱。",
        "useful_god_clarity": "看用神是否清楚、喜忌是否有层次。",
        "rescue_control": "看破格处是否有制化救应。",
        "broad_pattern_scan": "广谱检查格局、神煞、纳音和特殊配置。",
        "shensha_symbol": "神煞只作辅助象，不作主裁判。",
        "nayin_symbol": "纳音只作辅助象，不作主裁判。",
        "branch_relation": "刑冲合害必须落到宫位和事件。",
        "event_topic": "事件主题要能被命局结构解释。",
        "qi_momentum": "看五行气势是否顺畅。",
        "body_use_flow": "看体用保护链是否通。",
        "clarity_turbidity": "看清浊顺逆。",
        "breakpoint_repair": "看岁运修复还是冲断流通。",
        "season_climate": "看寒暖燥湿是否得调。",
        "first_adjuster": "看第一调候用神是否出现。",
        "adjuster_protection": "看调候之神是否被保护。",
        "state_performance": "看状态发挥、健康和学业是否得气。",
        "luck_climate": "看大运是否改善气候平衡。",
        "disease_identification": "看命局病点是否明确。",
        "medicine_presence": "看药神是否出现。",
        "medicine_protection": "看药神是否被护。",
        "disease_medicine_event": "看事件是药到病除还是病重药轻。",
        "month_pattern": "横门先从月令取格。",
        "success_rescue": "横门重成败救应。",
        "event_ten_god": "横门事件要落十神。",
        "palace_trigger": "横门事件要落宫位。",
        "luck_support": "横门看大运是否承接。",
        "annual_interaction": "横门看流年引动。",
        "fact_calibration": "横门用事实筛格。",
    }.get(vote_id, vote_id)


def _nested_get(value: object, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
