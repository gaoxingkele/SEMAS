"""Cross-agent topic synthesis for final mingli reports."""

from __future__ import annotations

from typing import Any


TOPICS = {
    "finance": "Financial resources and money management",
    "official_career": "Authority, title, compliance, and official pressure",
    "career": "Career direction and work execution",
    "study": "Study, credentials, and learning strategy",
    "relationship": "Marriage, romance, and intimate partnership",
    "friends": "Friends, peers, teams, and collaborators",
    "leadership": "Leadership, managers, clients, and institutions",
    "children_family": "Children, juniors, family duty, and creative output",
}

QIMEN_TOPIC_MAP = {
    "finance": "wealth",
    "official_career": "career",
    "career": "career",
    "study": "study",
    "relationship": "relationship",
    "friends": "relationship",
    "leadership": "career",
    "children_family": "health",
}

ZIWEI_PALACE_MAP = {
    "finance": "Wealth",
    "official_career": "Career",
    "career": "Career",
    "study": "Parents",
    "relationship": "Spouse",
    "friends": "Friends",
    "leadership": "Career",
    "children_family": "Children",
}

ASTRO_HOUSE_MAP = {
    "finance": {2, 8},
    "official_career": {10},
    "career": {6, 10},
    "study": {3, 9},
    "relationship": {5, 7},
    "friends": {11},
    "leadership": {10, 11},
    "children_family": {4, 5},
}


def build_topic_synthesis(
    reports: dict[str, dict[str, Any]],
    annual_luck: dict[str, Any],
    monthly_luck: dict[str, Any],
    provider_summary: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build topic-level synthesis from the four specialist artifacts."""
    synthesis = {}
    provider_summary = provider_summary if isinstance(provider_summary, dict) else {}
    for topic, label in TOPICS.items():
        annual_focus = _latest_annual_row(annual_luck, topic)
        monthly_focus = _latest_monthly_row(monthly_luck, topic)
        qimen_focus = _qimen_focus(reports, topic)
        ziwei_focus = _ziwei_focus(reports, topic)
        astrology_focus = _astrology_focus(reports, topic)
        bazi_focus = _bazi_focus(reports)
        timing_evidence = _timing_evidence(annual_focus, monthly_focus)
        cross_agent_evidence = [bazi_focus, ziwei_focus, qimen_focus, astrology_focus]
        confidence = _synthesis_confidence(timing_evidence, cross_agent_evidence, provider_summary)
        synthesis[topic] = {
            "label": label,
            "headline": _headline(topic, annual_focus, qimen_focus, ziwei_focus, astrology_focus),
            "annual_focus": annual_focus,
            "monthly_focus": monthly_focus,
            "timing_evidence": timing_evidence,
            "cross_agent_evidence": cross_agent_evidence,
            "synthesis_confidence": confidence,
            "evidence_summary": _evidence_summary(timing_evidence, cross_agent_evidence),
            "risk_boundary": _risk_boundary(topic),
        }
    return synthesis


def _latest_annual_row(annual_luck: dict[str, Any], topic: str) -> dict[str, Any]:
    rows = annual_luck.get("rows", [])
    if not rows:
        return {}
    row = rows[-1]
    return {
        "year": row.get("year"),
        "category": row.get("category"),
        "intensity": row.get("intensity"),
        "message": row.get(topic, row.get("theme")),
        "bazi_evidence": row.get("bazi_evidence", {}),
        "risk_notes": row.get("risk_notes", []),
    }


def _latest_monthly_row(monthly_luck: dict[str, Any], topic: str) -> dict[str, Any]:
    rows = monthly_luck.get("rows", [])
    if not rows:
        return {}
    row = rows[-1]
    return {
        "year": row.get("year"),
        "month": row.get("month"),
        "category": row.get("category"),
        "intensity": row.get("intensity"),
        "message": row.get(topic, row.get("theme")),
        "bazi_evidence": row.get("bazi_evidence", {}),
    }


def _bazi_focus(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    chart = reports["bazi"]["chart"]
    deep = chart.get("deep_analysis", {})
    current_luck = next(
        (
            item
            for item in deep.get("major_luck", [])
            if item.get("start_year", 0) <= _latest_year_from_chart(chart) <= item.get("end_year", 0)
        ),
        {},
    )
    return {
        "agent": "bazi",
        "signal": f"day master {deep.get('day_master')} with useful element {chart.get('useful_element')}",
        "support": current_luck.get("ganzhi") or "major luck listed",
    }


def _ziwei_focus(reports: dict[str, dict[str, Any]], topic: str) -> dict[str, Any]:
    deep = reports["ziwei"]["chart"].get("deep_analysis", {})
    palace_name = ZIWEI_PALACE_MAP[topic]
    palace = next((item for item in deep.get("palaces", []) if item.get("name") == palace_name), {})
    return {
        "agent": "ziwei",
        "signal": f"{palace_name} palace",
        "support": {
            "primary_stars": palace.get("primary_stars", []),
            "theme": palace.get("theme"),
        },
    }


def _qimen_focus(reports: dict[str, dict[str, Any]], topic: str) -> dict[str, Any]:
    deep = reports["qimen"]["chart"].get("deep_analysis", {})
    useful = deep.get("useful_gods", {}).get(QIMEN_TOPIC_MAP[topic], {})
    return {
        "agent": "qimen",
        "signal": f"{QIMEN_TOPIC_MAP[topic]} useful god",
        "support": useful,
    }


def _astrology_focus(reports: dict[str, dict[str, Any]], topic: str) -> dict[str, Any]:
    deep = reports["astrology"]["chart"].get("deep_analysis", {})
    houses = ASTRO_HOUSE_MAP[topic]
    transit = next(
        (item for item in reversed(deep.get("annual_transits", [])) if item.get("activated_house") in houses),
        (deep.get("annual_transits") or [{}])[-1],
    )
    return {
        "agent": "astrology",
        "signal": f"houses {sorted(houses)}",
        "support": transit,
    }


def _headline(
    topic: str,
    annual_focus: dict[str, Any],
    qimen_focus: dict[str, Any],
    ziwei_focus: dict[str, Any],
    astrology_focus: dict[str, Any],
) -> str:
    topic_label = TOPICS[topic]
    year = annual_focus.get("year", "selected year")
    intensity = annual_focus.get("intensity", "symbolic")
    qimen_palace = qimen_focus.get("support", {}).get("palace", "unknown palace")
    ziwei_signal = ziwei_focus.get("signal", "Zi Wei palace")
    astro_house = astrology_focus.get("support", {}).get("activated_house", "selected house")
    return (
        f"{topic_label}: {year} reads as {intensity}; Qi Men points to {qimen_palace}, "
        f"Zi Wei checks {ziwei_signal}, and astrology watches house {astro_house}."
    )


def _timing_evidence(annual_focus: dict[str, Any], monthly_focus: dict[str, Any]) -> dict[str, Any]:
    return {
        "annual": _compact_bazi_timing(annual_focus.get("bazi_evidence", {}), "annual"),
        "monthly": _compact_bazi_timing(monthly_focus.get("bazi_evidence", {}), "monthly"),
    }


def _compact_bazi_timing(evidence: object, level: str) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        return {}
    ten_gods_key = "monthly_ten_gods" if level == "monthly" else "annual_ten_gods"
    pillar_key = "monthly_pillar" if level == "monthly" else "annual_pillar"
    active_luck = evidence.get("active_major_luck") if isinstance(evidence.get("active_major_luck"), dict) else {}
    matches = evidence.get("natal_pillar_matches") if isinstance(evidence.get("natal_pillar_matches"), list) else []
    branch_interactions = (
        evidence.get("branch_interactions") if isinstance(evidence.get("branch_interactions"), list) else []
    )
    return {
        "level": level,
        "pillar": evidence.get(pillar_key),
        "ten_gods": evidence.get(ten_gods_key, {}),
        "active_major_luck": active_luck.get("ganzhi"),
        "useful_state": evidence.get("useful_state"),
        "natal_match_count": len(matches),
        "branch_interactions": branch_interactions,
    }


def _evidence_summary(timing_evidence: dict[str, Any], cross_agent_evidence: list[dict[str, Any]]) -> list[str]:
    summary = []
    annual = timing_evidence.get("annual", {})
    monthly = timing_evidence.get("monthly", {})
    if isinstance(annual, dict) and annual:
        summary.append(
            f"BaZi annual {annual.get('pillar')} ten-gods {annual.get('ten_gods')} useful-state {annual.get('useful_state')}"
        )
    if isinstance(monthly, dict) and monthly:
        summary.append(
            f"BaZi monthly {monthly.get('pillar')} ten-gods {monthly.get('ten_gods')} useful-state {monthly.get('useful_state')}"
        )
    for item in cross_agent_evidence:
        if not isinstance(item, dict):
            continue
        summary.append(f"{item.get('agent')}: {item.get('signal')}")
    return summary


def _synthesis_confidence(
    timing_evidence: dict[str, Any],
    cross_agent_evidence: list[dict[str, Any]],
    provider_summary: dict[str, Any],
) -> dict[str, Any]:
    """Score topic synthesis confidence from evidence coverage and provider readiness."""
    evidence_count = 0
    for value in timing_evidence.values():
        if isinstance(value, dict) and value.get("pillar"):
            evidence_count += 1
    agent_count = sum(1 for item in cross_agent_evidence if isinstance(item, dict) and item.get("support"))
    matrix = provider_summary.get("readiness_matrix", [])
    if not isinstance(matrix, list):
        matrix = []
    production_domains = [
        str(item.get("domain"))
        for item in matrix
        if isinstance(item, dict) and item.get("confidence_level") == "production"
    ]
    fallback_domains = [
        str(item.get("domain"))
        for item in matrix
        if isinstance(item, dict) and item.get("confidence_level") != "production"
    ]
    blocked_domains = [
        str(item.get("domain"))
        for item in matrix
        if isinstance(item, dict) and item.get("confidence_level") == "blocked"
    ]
    downgrades = []
    if evidence_count < 2:
        downgrades.append("incomplete_timing_evidence")
    if agent_count < 4:
        downgrades.append("incomplete_cross_agent_evidence")
    if fallback_domains:
        downgrades.append("provider_fallbacks_present")
    if blocked_domains:
        downgrades.append("blocked_provider_payloads_present")
    if not downgrades and len(production_domains) >= 4:
        level = "high"
    elif evidence_count >= 2 and agent_count >= 4 and not blocked_domains:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "evidence_count": evidence_count,
        "cross_agent_count": agent_count,
        "production_provider_count": len(production_domains),
        "fallback_provider_count": len(fallback_domains),
        "blocked_provider_count": len(blocked_domains),
        "production_domains": production_domains,
        "fallback_domains": fallback_domains,
        "blocked_domains": blocked_domains,
        "downgrade_reasons": downgrades,
        "boundary": "Confidence rates evidence coverage and provider readiness; it is not empirical proof of prediction accuracy.",
    }


def topic_confidence_summary(topic_synthesis: Any) -> dict[str, Any]:
    """Summarize topic confidence for benchmark and empirical validation gates."""
    expected_topics = set(TOPICS)
    if not isinstance(topic_synthesis, dict):
        return {
            "topic_count": 0,
            "missing_topics": sorted(expected_topics),
            "levels": {},
            "downgrade_reasons": [],
            "fallback_provider_counts": {},
            "boundaries_ok": False,
        }
    levels: dict[str, str] = {}
    downgrade_reasons: set[str] = set()
    fallback_provider_counts: dict[str, int] = {}
    boundaries_ok = True
    for topic, item in topic_synthesis.items():
        if not isinstance(item, dict):
            boundaries_ok = False
            continue
        confidence = item.get("synthesis_confidence")
        if not isinstance(confidence, dict):
            boundaries_ok = False
            continue
        levels[str(topic)] = str(confidence.get("level") or "unknown")
        fallback_provider_counts[str(topic)] = int(confidence.get("fallback_provider_count") or 0)
        boundary = confidence.get("boundary")
        if not isinstance(boundary, str) or "not empirical proof" not in boundary:
            boundaries_ok = False
        reasons = confidence.get("downgrade_reasons", [])
        if isinstance(reasons, list):
            downgrade_reasons.update(str(reason) for reason in reasons)
    return {
        "topic_count": len(topic_synthesis),
        "missing_topics": sorted(expected_topics - set(topic_synthesis)),
        "levels": levels,
        "downgrade_reasons": sorted(downgrade_reasons),
        "fallback_provider_counts": fallback_provider_counts,
        "boundaries_ok": boundaries_ok and expected_topics.issubset(set(topic_synthesis)),
    }


def _risk_boundary(topic: str) -> str:
    if topic == "finance":
        return "Do not treat symbolic finance language as investment advice."
    if topic in {"relationship", "children_family"}:
        return "Do not treat symbolic relationship or family language as a decision rule."
    if topic in {"official_career", "leadership"}:
        return "Verify contracts, policy, and workplace obligations through ordinary channels."
    return "Use as a reflective prompt, not as a deterministic prediction."


def _latest_year_from_chart(chart: dict[str, Any]) -> int:
    date_text = chart.get("context", {}).get("date", "0")
    return int(str(date_text).split("-", 1)[0])
