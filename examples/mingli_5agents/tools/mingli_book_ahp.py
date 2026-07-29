"""AHP frameworks derived from locally available mingli book files.

Each profile represents one book-level framework. A framework contains several
sub-agents; each sub-agent owns one judgement module and returns an independent
vote. The implementation is deterministic so the public-figure calibration
cases can be rerun and compared.
"""

from __future__ import annotations

from typing import Any

from examples.mingli_5agents.tools.bazi_hengmen_ahp import score_hengmen_event


BOOK_AHP_PROFILES: dict[str, dict[str, Any]] = {
    "yuanhai_ziping": {
        "title": "渊海子平",
        "local_files": ["external/mingli_books/bazi/yuanhai_ziping_ziping_zhenquan.pdf"],
        "domain": "bazi",
        "logic": "以月令立纲，十神定事，透干通根辨真假，格局清浊定层次，岁运承接定应期。",
        "subagents": {
            "month_command_agent": {"weight": 0.20, "role": "月令立纲"},
            "ten_god_agent": {"weight": 0.20, "role": "十神定事"},
            "stem_root_agent": {"weight": 0.18, "role": "透干通根"},
            "pattern_purity_agent": {"weight": 0.16, "role": "格局清浊"},
            "luck_agent": {"weight": 0.14, "role": "大运流年承接"},
            "fact_agent": {"weight": 0.12, "role": "事实校准"},
        },
    },
    "ziping_zhenquan": {
        "title": "子平真诠",
        "local_files": ["external/mingli_books/bazi/yuanhai_ziping_ziping_zhenquan.pdf"],
        "domain": "bazi",
        "logic": "先论格局成败，再论用神清纯，破格要看救应，运来决定成败转换。",
        "subagents": {
            "pattern_success_agent": {"weight": 0.24, "role": "格局成败"},
            "useful_god_agent": {"weight": 0.20, "role": "用神清纯"},
            "rescue_agent": {"weight": 0.18, "role": "破格救应"},
            "purity_agent": {"weight": 0.14, "role": "混杂降权"},
            "luck_agent": {"weight": 0.14, "role": "岁运成败转换"},
            "fact_agent": {"weight": 0.10, "role": "事实校准"},
        },
    },
    "mingli_jicheng": {
        "title": "命理集成",
        "local_files": [
            "external/mingli_books/bazi/extended/mingli_jicheng_13jh001663.pdf",
            "external/mingli_books/bazi/extended/mingli_jicheng_16002983.pdf",
        ],
        "domain": "bazi",
        "logic": "综合古法类书，适合做格局、神煞、纳音、六亲、岁运、特殊格局的广谱检查。",
        "subagents": {
            "pattern_catalog_agent": {"weight": 0.18, "role": "格局类目"},
            "shensha_agent": {"weight": 0.16, "role": "神煞定象"},
            "nayin_agent": {"weight": 0.14, "role": "纳音辅助"},
            "kinship_agent": {"weight": 0.14, "role": "六亲宫位"},
            "relation_agent": {"weight": 0.16, "role": "刑冲合害"},
            "timing_agent": {"weight": 0.12, "role": "岁运应期"},
            "fact_agent": {"weight": 0.10, "role": "事实校准"},
        },
    },
    "lixuzhong_mingshu": {
        "title": "李虚中命书",
        "local_files": [
            "external/mingli_books/bazi/extended/text_sources/lixuzhong_mingshu_wikisource.html",
            "external/mingli_books/bazi/extended/text_sources/lixuzhong_mingshu_ctext.html",
        ],
        "domain": "luming",
        "logic": "早期禄命法，重年命、纳音、禄马、五行生死、贵贱寿夭与三命消息。",
        "subagents": {
            "year_life_agent": {"weight": 0.24, "role": "年命根基"},
            "nayin_agent": {"weight": 0.20, "role": "纳音关系"},
            "lu_ma_agent": {"weight": 0.16, "role": "禄马贵人"},
            "life_death_agent": {"weight": 0.16, "role": "五行生死"},
            "timing_agent": {"weight": 0.12, "role": "岁运触发"},
            "fact_agent": {"weight": 0.12, "role": "事实校准"},
        },
    },
    "yuzhao_dingzhenjing": {
        "title": "玉照定真经",
        "local_files": ["external/mingli_books/bazi/extended/text_sources/yuzhao_dingzhenjing_ctext.html"],
        "domain": "luming",
        "logic": "早期禄命断语系统，重干支象、纳音、神煞、刑冲和贵贱寿夭类断。",
        "subagents": {
            "stem_branch_image_agent": {"weight": 0.22, "role": "干支象"},
            "nayin_agent": {"weight": 0.18, "role": "纳音象"},
            "shensha_agent": {"weight": 0.16, "role": "神煞象"},
            "relation_agent": {"weight": 0.18, "role": "刑冲合害"},
            "event_phrase_agent": {"weight": 0.14, "role": "断语落事"},
            "fact_agent": {"weight": 0.12, "role": "事实校准"},
        },
    },
    "xingping_huihai": {
        "title": "星平会海",
        "local_files": ["external/mingli_books/bazi/extended/text_sources/xingping_huihai_ctext.html"],
        "domain": "xingping",
        "logic": "星命与子平合参，重星曜象、神煞、格局、宫度和人生主题综合。",
        "subagents": {
            "bazi_pattern_agent": {"weight": 0.18, "role": "子平格局"},
            "star_symbol_agent": {"weight": 0.18, "role": "星命象"},
            "shensha_agent": {"weight": 0.16, "role": "神煞辅助"},
            "palace_agent": {"weight": 0.16, "role": "宫度落事"},
            "timing_agent": {"weight": 0.14, "role": "岁运触发"},
            "fact_agent": {"weight": 0.18, "role": "事实校准"},
        },
    },
    "ziwei_doushu_quanshu": {
        "title": "紫微斗数全书",
        "local_files": ["external/mingli_books/ziwei/ziwei_doushu_quanshu_text.pdf"],
        "domain": "ziwei",
        "logic": "命身宫、十二宫、三方四正、四化、大限流年联动。",
        "subagents": {
            "ming_body_agent": {"weight": 0.18, "role": "命身轴"},
            "palace_agent": {"weight": 0.22, "role": "十二宫主题"},
            "triad_agent": {"weight": 0.16, "role": "三方四正"},
            "four_transform_agent": {"weight": 0.18, "role": "四化"},
            "limit_agent": {"weight": 0.16, "role": "大限流年"},
            "fact_agent": {"weight": 0.10, "role": "事实校准"},
        },
    },
    "christian_astrology": {
        "title": "Christian Astrology",
        "local_files": ["external/mingli_books/xingzuo/william_lilly_christian_astrology_1647.pdf"],
        "domain": "western_astrology",
        "logic": "行星、宫位、相位、尊贵失势、过境触发与事件主题对应。",
        "subagents": {
            "planet_agent": {"weight": 0.18, "role": "行星主事"},
            "house_agent": {"weight": 0.22, "role": "宫位主题"},
            "aspect_agent": {"weight": 0.18, "role": "相位关系"},
            "dignity_agent": {"weight": 0.14, "role": "尊贵失势"},
            "transit_agent": {"weight": 0.16, "role": "过境触发"},
            "fact_agent": {"weight": 0.12, "role": "事实校准"},
        },
    },
    "geju_hengmen_duan": {
        "title": "格局横门断",
        "local_files": ["tools/格局横门断.docx"],
        "domain": "bazi",
        "logic": "横向比较格局，月令取格，透干根气，成败救应，事实年份筛选。",
        # 权重与 bazi_hengmen_ahp.AHP_WEIGHTS 同哲学：event_agent 对时辰候选零方差
        # （0.18->0.10），palace_agent 粗粒度且在本语料上与参考时辰负相关（0.12->0.06），
        # 权重移给成败救应（横门断核心、候选间区分度最大）与事实筛选（反例通道已生效）。
        "subagents": {
            "month_pattern_agent": {"weight": 0.20, "role": "月令取格"},
            "stem_root_agent": {"weight": 0.16, "role": "透干根气"},
            "rescue_agent": {"weight": 0.26, "role": "成败救应"},
            "event_agent": {"weight": 0.10, "role": "十神事件"},
            "palace_agent": {"weight": 0.06, "role": "宫位落事"},
            "timing_agent": {"weight": 0.10, "role": "岁运触发"},
            "fact_agent": {"weight": 0.12, "role": "事实筛选"},
        },
    },
}


def score_all_book_frameworks(
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
    ziwei_row: dict[str, Any] | None = None,
    astrology_row: dict[str, Any] | None = None,
    monthly_rows: list[dict[str, Any]] | None = None,
    counterexample_rows: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        book_id: score_book_framework_event(
            book_id, event, annual_row, bazi, ziwei_row or {}, astrology_row or {}, monthly_rows, counterexample_rows
        )
        for book_id in BOOK_AHP_PROFILES
    }


def score_book_framework_event(
    book_id: str,
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
    monthly_rows: list[dict[str, Any]] | None = None,
    counterexample_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    profile = BOOK_AHP_PROFILES[book_id]
    if book_id == "geju_hengmen_duan":
        return _score_hengmen_book_profile(profile, event, annual_row, bazi, monthly_rows, counterexample_rows)
    votes = []
    for agent_id, agent in profile["subagents"].items():
        votes.append(
            {
                "agent_id": agent_id,
                "role": agent["role"],
                "weight": agent["weight"],
                "score": round(_score_agent(agent_id, event, annual_row, bazi, ziwei_row, astrology_row), 4),
                "basis": _agent_basis(agent_id),
            }
        )
    score = round(sum(vote["score"] * vote["weight"] for vote in votes), 4)
    return {
        "book_id": book_id,
        "title": profile["title"],
        "domain": profile["domain"],
        "logic": profile["logic"],
        "local_files": profile["local_files"],
        "score": score,
        "subagent_votes": votes,
    }


def _score_hengmen_book_profile(
    profile: dict[str, Any], event: dict[str, Any], annual_row: dict[str, Any], bazi: dict[str, Any],
    monthly_rows: list[dict[str, Any]] | None = None, counterexample_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Keep the Hengmen book profile independent from generic book heuristics."""
    result = score_hengmen_event(event, annual_row, bazi, monthly_rows, counterexample_rows)
    votes_by_id = {str(vote.get("id")): vote for vote in result.get("votes", [])}
    agent_to_vote = {
        "month_pattern_agent": "month_pattern",
        "stem_root_agent": "stem_root",
        "rescue_agent": "success_rescue",
        "event_agent": "event_ten_god",
        "palace_agent": "palace_trigger",
        "timing_agent": "annual_interaction",
        "fact_agent": "fact_calibration",
    }
    agent_to_receipt = {
        "month_pattern_agent": "month_command_pattern",
        "rescue_agent": "success_failure_rescue",
        "event_agent": "event_ten_god",
        "palace_agent": "palace_trigger",
        "timing_agent": "annual_monthly_timing",
        "fact_agent": "fact_calibration",
    }
    votes = []
    for agent_id, agent in profile["subagents"].items():
        source_vote = votes_by_id.get(agent_to_vote[agent_id], {})
        receipt = result.get("agent_receipts", {}).get(agent_to_receipt.get(agent_id, ""), {})
        score = round(float(source_vote.get("score", 0.42)), 4)
        basis = source_vote.get("basis", "横门规则引擎未提供该维度。")
        if agent_id == "timing_agent":
            luck_vote = votes_by_id.get("luck_support", {})
            annual_vote = votes_by_id.get("annual_interaction", {})
            luck_score = float(luck_vote.get("score", 0.42))
            annual_score = float(annual_vote.get("score", 0.42))
            score = round((0.10 * luck_score + 0.08 * annual_score) / 0.18, 4)
            basis = "大运承接与流年/流月引动按横门直接 AHP 原权重合成。"
            receipt = {
                "major_luck": result.get("timing_dimensions", {}).get("major_luck", {}),
                "annual_monthly": result.get("agent_receipts", {}).get("annual_monthly_timing", {}),
                "source_weights": {"luck_support": 0.10, "annual_interaction": 0.08},
            }
        if agent_id == "stem_root_agent":
            selected = bazi.get("deep_analysis", {}).get("hengmen_pattern_analysis", {}).get("selected_pattern", {})
            receipt = {
                "exposed": selected.get("exposed"), "roots": selected.get("roots", []),
                "ordering_evidence": selected.get("ordering_evidence", {}),
            }
        votes.append(
            {
                "agent_id": agent_id,
                "role": agent["role"],
                "weight": agent["weight"],
                "score": score,
                "basis": basis,
                "receipt": receipt,
            }
        )
    return {
        "book_id": "geju_hengmen_duan",
        "title": profile["title"],
        "domain": profile["domain"],
        "logic": profile["logic"],
        "local_files": profile["local_files"],
        "score": round(sum(vote["score"] * vote["weight"] for vote in votes), 4),
        "subagent_votes": votes,
        "rule_engine": result.get("rule_engine", {}),
        "agent_receipts": result.get("agent_receipts", {}),
        "rule_catalog": result.get("rule_catalog", {}),
        "review_flags": result.get("review_flags", []),
        "ahp_architecture": result.get("ahp_architecture", {}),
    }


def aggregate_book_scores(
    book_event_scores: list[dict[str, dict[str, Any]]],
    events: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for book_id, profile in BOOK_AHP_PROFILES.items():
        total = 0.0
        total_weight = 0.0
        for event_scores, event in zip(book_event_scores, events):
            weight = float(event.get("weight", 1.0) or 1.0)
            total += float(event_scores[book_id]["score"]) * weight
            total_weight += weight
        totals[book_id] = {
            "title": profile["title"],
            "domain": profile["domain"],
            "score": round(total / max(total_weight, 0.001), 4),
            "logic": profile["logic"],
            "local_files": profile["local_files"],
        }
    return totals


def book_ahp_catalog() -> dict[str, dict[str, Any]]:
    return BOOK_AHP_PROFILES


def _score_agent(
    agent_id: str,
    event: dict[str, Any],
    annual_row: dict[str, Any],
    bazi: dict[str, Any],
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
) -> float:
    event_type = str(event.get("type", ""))
    category = str(annual_row.get("category", "")) if isinstance(annual_row, dict) else ""
    intensity = str(annual_row.get("intensity", "")) if isinstance(annual_row, dict) else ""
    evidence = annual_row.get("bazi_evidence", {}) if isinstance(annual_row, dict) else {}
    interactions = evidence.get("branch_interactions", []) if isinstance(evidence, dict) else []
    markers = annual_row.get("event_markers", {}) if isinstance(annual_row, dict) else {}
    deep = bazi.get("deep_analysis", {}) if isinstance(bazi, dict) else {}

    if agent_id in {"month_command_agent", "month_pattern_agent"}:
        return _month_score(deep)
    if agent_id in {"ten_god_agent", "event_agent", "event_phrase_agent"}:
        return _event_topic_score(event_type, category, markers)
    if agent_id in {"stem_root_agent"}:
        return _stem_root_score(deep, bazi.get("context", {}))
    if agent_id in {"pattern_purity_agent", "pattern_success_agent", "purity_agent", "pattern_catalog_agent", "bazi_pattern_agent"}:
        return _pattern_score(deep)
    if agent_id in {"useful_god_agent", "rescue_agent"}:
        return _useful_score(deep, annual_row)
    if agent_id in {"luck_agent", "timing_agent", "limit_agent", "transit_agent"}:
        return _timing_score(event_type, evidence, interactions, ziwei_row, astrology_row)
    if agent_id in {"fact_agent"}:
        return _fact_score(event)
    if agent_id in {"shensha_agent", "lu_ma_agent"}:
        return 0.62 if interactions or markers else 0.46
    if agent_id in {"nayin_agent", "year_life_agent", "life_death_agent"}:
        return 0.58 if annual_row else 0.42
    if agent_id in {"kinship_agent", "palace_agent"}:
        return _palace_score(event_type, interactions, ziwei_row, astrology_row)
    if agent_id in {"relation_agent", "stem_branch_image_agent"}:
        return _relation_score(event_type, interactions, intensity)
    if agent_id in {"star_symbol_agent", "planet_agent", "house_agent", "aspect_agent", "dignity_agent"}:
        return _astrology_symbol_score(event_type, astrology_row)
    if agent_id in {"ming_body_agent", "triad_agent", "four_transform_agent"}:
        return _ziwei_symbol_score(event_type, ziwei_row)
    return 0.5


def _month_score(deep: dict[str, Any]) -> float:
    pattern = deep.get("pattern_analysis", {}).get("pattern")
    season = deep.get("tiaohou_analysis", {}).get("season")
    if pattern and season:
        return 0.74
    if pattern or season:
        return 0.58
    return 0.44


def _event_topic_score(event_type: str, category: str, markers: dict[str, Any]) -> float:
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
    if markers.get(event_type):
        return 0.72
    return 0.46


def _stem_root_score(deep: dict[str, Any], context: dict[str, Any]) -> float:
    ten_gods = deep.get("ten_god_distribution") or context.get("ten_god_distribution") or {}
    hidden = deep.get("hidden_stem_profile") or {}
    count = 0
    if isinstance(ten_gods, dict):
        count += min(3, len([value for value in ten_gods.values() if value]))
    if isinstance(hidden, dict) and hidden.get("total_hidden_stems"):
        count += 2
    return min(0.82, 0.42 + count * 0.08)


def _pattern_score(deep: dict[str, Any]) -> float:
    pattern = deep.get("pattern_analysis", {}).get("pattern")
    debate = deep.get("school_debate", {})
    conflicts = debate.get("conflicts", []) if isinstance(debate, dict) else []
    if pattern and not conflicts:
        return 0.7
    if pattern:
        return 0.58
    return 0.48


def _useful_score(deep: dict[str, Any], annual_row: dict[str, Any]) -> float:
    useful = deep.get("useful_god_analysis", {}).get("useful_element")
    if useful and useful in str(annual_row):
        return 0.74
    if useful:
        return 0.58
    return 0.44


def _timing_score(
    event_type: str,
    evidence: dict[str, Any],
    interactions: list[dict[str, Any]],
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
) -> float:
    score = 0.42
    if isinstance(evidence.get("active_major_luck"), dict) and evidence["active_major_luck"].get("ganzhi"):
        score += 0.14
    if interactions:
        score += 0.16
    if ziwei_row:
        score += 0.06
    if astrology_row:
        score += 0.06
    if event_type in {"death", "health_crisis", "public_scandal"}:
        score += 0.04
    return min(score, 0.84)


def _palace_score(
    event_type: str,
    interactions: list[dict[str, Any]],
    ziwei_row: dict[str, Any],
    astrology_row: dict[str, Any],
) -> float:
    target_pillars = {
        "relationship": {"day", "hour"},
        "family": {"year", "day", "hour"},
        "death": {"day", "hour"},
        "health_crisis": {"day", "hour"},
        "role_power": {"year", "month"},
        "career_launch": {"month", "hour"},
        "award_peak": {"year", "month"},
    }.get(event_type, {"year", "month", "day", "hour"})
    pillars = {str(item.get("pillar", "")) for item in interactions}
    score = 0.42
    if pillars & target_pillars:
        score += 0.24
    if ziwei_row:
        score += 0.08
    if astrology_row:
        score += 0.06
    return min(score, 0.82)


def _relation_score(event_type: str, interactions: list[dict[str, Any]], intensity: str) -> float:
    if not interactions:
        return 0.4
    severe = {"clash", "punishment", "harm"}
    relations = {str(item.get("relation", "")) for item in interactions}
    score = 0.58
    if relations & severe:
        score += 0.14
    if intensity == "high-volatility":
        score += 0.08
    return min(score, 0.84)


def _ziwei_symbol_score(event_type: str, ziwei_row: dict[str, Any]) -> float:
    if not ziwei_row:
        return 0.38
    palace = str(ziwei_row.get("palace", ""))
    matches = {
        "role_power": {"Career", "Parents", "Friends"},
        "career_launch": {"Career", "Fortune"},
        "public_visibility": {"Career", "Friends", "Travel"},
        "relationship": {"Spouse", "Friends"},
        "family": {"Spouse", "Children", "Property"},
        "death": {"Health", "Travel", "Fortune"},
        "health_crisis": {"Health", "Fortune"},
    }
    return 0.72 if palace in matches.get(event_type, set()) else 0.5


def _astrology_symbol_score(event_type: str, astrology_row: dict[str, Any]) -> float:
    if not astrology_row:
        return 0.38
    house = int(astrology_row.get("activated_house", 0) or 0)
    matches = {
        "role_power": {10, 11, 9},
        "career_launch": {10, 6},
        "public_visibility": {10, 11, 9},
        "relationship": {7, 5},
        "family": {4, 5, 7},
        "death": {8, 12, 6},
        "health_crisis": {6, 8, 12},
    }
    return 0.72 if house in matches.get(event_type, set()) else 0.5


def _fact_score(event: dict[str, Any]) -> float:
    source = str(event.get("source", ""))
    label = str(event.get("label", ""))
    year = event.get("year")
    if year and source.startswith("http") and label:
        return 0.82
    if year and label:
        return 0.62
    return 0.4


def _agent_basis(agent_id: str) -> str:
    return {
        "month_command_agent": "从月令确定命局主线。",
        "month_pattern_agent": "横向取格先看月令。",
        "ten_god_agent": "用十神把现实事件落类。",
        "stem_root_agent": "透干通根决定力量能否落地。",
        "pattern_purity_agent": "格局清浊影响层次。",
        "pattern_success_agent": "判断成格、败格、破格。",
        "useful_god_agent": "看用神是否清楚有护。",
        "rescue_agent": "破格处看是否有救应。",
        "luck_agent": "大运流年承接原局。",
        "timing_agent": "岁运流年触发应期。",
        "limit_agent": "紫微大限流年触发。",
        "transit_agent": "西方占星过境触发。",
        "fact_agent": "事实年份与来源质量。",
    }.get(agent_id, "该子智能体按本书对应模块独立出票。")
