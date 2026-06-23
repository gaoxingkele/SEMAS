"""Deterministic auspicious-day scaffold for the mingli coordinator.

This module is an auditable offline baseline for xuanze/huangdao style fields.
It does not replace a professional almanac. The stable schema lets a later
provider swap in verified twelve-officer, twenty-eight-mansion, and hour data
without changing coordinator or evaluator contracts.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from examples.mingli_5agents.tools.calendar_core import (
    BRANCHES,
    BRANCH_ELEMENTS,
    ELEMENTS,
    day_ganzhi,
    hour_branch,
    nearest_solar_term,
)

TWELVE_OFFICERS = [
    "Establish",
    "Remove",
    "Full",
    "Balance",
    "Settle",
    "Hold",
    "Break",
    "Danger",
    "Complete",
    "Receive",
    "Open",
    "Close",
]

AUSPICIOUS_OFFICERS = {"Remove", "Balance", "Settle", "Hold", "Complete", "Open"}

TWENTY_EIGHT_MANSIONS = [
    "Horn",
    "Neck",
    "Root",
    "Room",
    "Heart",
    "Tail",
    "Winnowing Basket",
    "Dipper",
    "Ox",
    "Girl",
    "Emptiness",
    "Rooftop",
    "Encampment",
    "Wall",
    "Stride",
    "Mound",
    "Stomach",
    "Hairy Head",
    "Net",
    "Turtle Beak",
    "Three Stars",
    "Well",
    "Ghost",
    "Willow",
    "Star",
    "Extended Net",
    "Wings",
    "Chariot",
]

AUSPICIOUS_MANSIONS = {
    "Horn",
    "Room",
    "Tail",
    "Dipper",
    "Rooftop",
    "Wall",
    "Stomach",
    "Three Stars",
    "Well",
    "Wings",
}

ACTIVITY_GUIDANCE = {
    "Establish": ["planning", "starting routines", "setting direction"],
    "Remove": ["clearing blockers", "repairs", "decluttering"],
    "Full": ["gathering resources", "social contact", "inventory"],
    "Balance": ["negotiation", "contracts review", "mediation"],
    "Settle": ["stabilizing work", "family duties", "documentation"],
    "Hold": ["implementation", "maintenance", "keeping commitments"],
    "Break": ["ending stale patterns", "risk review"],
    "Danger": ["caution", "inspection", "contingency planning"],
    "Complete": ["delivery", "public output", "closing milestones"],
    "Receive": ["collection", "learning review", "resource intake"],
    "Open": ["launches", "meetings", "travel planning"],
    "Close": ["rest", "private review", "avoid major launches"],
}

CAUTION_BY_OFFICER = {
    "Break": "Avoid irreversible commitments; use the day for review or release.",
    "Danger": "Keep safety margins and backup plans visible.",
    "Close": "Prefer closure and rest over starting major public actions.",
}


def build_auspicious_calendar(
    birth: dict[str, Any],
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 7,
) -> dict[str, Any]:
    """Build a compact auspicious-day window with almanac-style fields."""
    start = date.fromisoformat(start_date) if start_date else date.today()
    if end_date:
        end = date.fromisoformat(end_date)
    else:
        end = start + timedelta(days=max(1, days) - 1)
    if end < start:
        raise ValueError("auspicious end_date must not be before start_date")

    rows = [_build_day_row(start + timedelta(days=offset), birth) for offset in range((end - start).days + 1)]
    best = [row for row in rows if row["rating"] == "favorable"]
    cautious = [row for row in rows if row["rating"] == "cautious"]
    fallback = {
        "range": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "count": len(rows),
        },
        "basis": {
            "provider": "xuanze_offline",
            "provider_quality": "offline_rule_scaffold",
            "rule_set": "twelve_officers_twenty_eight_mansions_hour_elements",
            "replacement_boundary": "Swap with a verified almanac provider for production-grade date selection.",
        },
        "rows": rows,
        "summary": {
            "favorable_dates": [row["date"] for row in best],
            "cautious_dates": [row["date"] for row in cautious],
            "best_date": best[0]["date"] if best else None,
        },
        "caution": "Symbolic xuanze scaffold only; do not use for legal, medical, investment, or other high-stakes scheduling.",
    }
    return _apply_optional_provider(birth, ensure_xuanze_method_layers(fallback))


def ensure_xuanze_method_layers(calendar: dict[str, Any]) -> dict[str, Any]:
    """Backfill method-audit layers for offline or external xuanze payloads."""
    enriched = dict(calendar)
    rows = [row for row in enriched.get("rows", []) if isinstance(row, dict)]
    basis = enriched.setdefault("basis", {})
    provider_quality = str(basis.get("provider_quality") or enriched.get("provider_quality") or "unknown")
    officer_analysis = _twelve_officer_analysis(rows)
    mansion_analysis = _mansion_analysis(rows)
    huangdao_analysis = _huangdao_analysis(rows)
    hour_selection = _hour_selection_analysis(rows)
    risk_boundary = _risk_boundary_analysis(rows, provider_quality)
    provider_quality_analysis = {
        "provider_quality": provider_quality,
        "production_grade": provider_quality in {"xuanze_json_cli", "external_xuanze", "verified_tongshu"},
        "rule_set": basis.get("rule_set", ""),
        "replacement_boundary": basis.get(
            "replacement_boundary",
            "Swap with a verified almanac provider for production-grade date selection.",
        ),
    }
    enriched["twelve_officer_analysis"] = officer_analysis
    enriched["mansion_analysis"] = mansion_analysis
    enriched["huangdao_analysis"] = huangdao_analysis
    enriched["hour_selection_analysis"] = hour_selection
    enriched["risk_boundary_analysis"] = risk_boundary
    enriched["provider_quality_analysis"] = provider_quality_analysis
    enriched["method_matrix"] = [
        {
            "method": "twelve_officer",
            "status": "available",
            "evidence_fields": ["rows[].twelve_officer", "twelve_officer_analysis"],
            "summary": f"{len(officer_analysis.get('counts', {}))} officer types in range",
        },
        {
            "method": "twenty_eight_mansion",
            "status": "available",
            "evidence_fields": ["rows[].twenty_eight_mansion", "mansion_analysis"],
            "summary": f"{mansion_analysis.get('auspicious_count', 0)} auspicious mansion rows",
        },
        {
            "method": "huangdao_rating",
            "status": "available",
            "evidence_fields": ["rows[].huangdao", "rows[].rating", "huangdao_analysis"],
            "summary": str(huangdao_analysis.get("best_date", "")),
        },
        {
            "method": "recommended_hours",
            "status": "available",
            "evidence_fields": ["rows[].recommended_hours", "hour_selection_analysis"],
            "summary": f"{hour_selection.get('total_recommended_hours', 0)} recommended hour slots",
        },
        {
            "method": "risk_boundary",
            "status": "available",
            "evidence_fields": ["rows[].avoid", "rows[].risk_notes", "risk_boundary_analysis"],
            "summary": str(risk_boundary.get("boundary", "")),
        },
        {
            "method": "provider_quality",
            "status": "available",
            "evidence_fields": ["basis.provider_quality", "provider_quality_analysis"],
            "summary": str(provider_quality_analysis.get("provider_quality", "")),
        },
    ]
    return enriched


def _apply_optional_provider(birth: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        from examples.mingli_5agents.tools.xuanze_cli_provider import apply_xuanze_provider

        return apply_xuanze_provider(birth, fallback)
    except Exception:
        return fallback


def _build_day_row(day: date, birth: dict[str, Any]) -> dict[str, Any]:
    ganzhi = day_ganzhi(day)
    branch = _branch_from_ganzhi(ganzhi)
    month_branch = _approx_month_branch(day.month)
    officer = TWELVE_OFFICERS[(BRANCHES.index(branch) - BRANCHES.index(month_branch)) % 12]
    mansion = TWENTY_EIGHT_MANSIONS[(day - date(1984, 2, 2)).days % 28]
    rating = _rating(officer, mansion)
    branch_element = BRANCH_ELEMENTS[branch]
    useful_element = str(birth.get("useful_element") or "")
    return {
        "date": day.isoformat(),
        "weekday": day.strftime("%A"),
        "ganzhi": ganzhi,
        "solar_term": nearest_solar_term(day.month, day.day),
        "twelve_officer": officer,
        "twenty_eight_mansion": mansion,
        "huangdao": rating == "favorable",
        "rating": rating,
        "suitable": ACTIVITY_GUIDANCE[officer],
        "avoid": _avoidance(officer, rating),
        "recommended_hours": _recommended_hours(branch_element, useful_element),
        "risk_notes": [
            CAUTION_BY_OFFICER.get(officer, "Symbolic timing only; confirm practical constraints independently."),
        ],
    }


def _branch_from_ganzhi(ganzhi: str) -> str:
    for branch in BRANCHES:
        if ganzhi.endswith(branch):
            return branch
    raise ValueError(f"Unsupported ganzhi label: {ganzhi}")


def _approx_month_branch(month: int) -> str:
    return ["Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai", "Zi", "Chou"][month - 1]


def _rating(officer: str, mansion: str) -> str:
    if officer in {"Break", "Danger", "Close"}:
        return "cautious"
    if officer in AUSPICIOUS_OFFICERS and mansion in AUSPICIOUS_MANSIONS:
        return "favorable"
    return "mixed"


def _avoidance(officer: str, rating: str) -> list[str]:
    if rating == "cautious":
        return ["major launches", "large irreversible commitments", "high-stakes decisions"]
    if officer == "Full":
        return ["overexpansion", "unclear financial promises"]
    return ["treating symbolic timing as certainty"]


def _recommended_hours(day_element: str, useful_element: str) -> list[dict[str, str]]:
    target_elements = {day_element}
    if useful_element in ELEMENTS:
        target_elements.add(useful_element)
    rows = []
    for hour in range(0, 24, 2):
        branch = hour_branch(hour)
        element = BRANCH_ELEMENTS[branch]
        if element in target_elements:
            rows.append(
                {
                    "start": f"{hour:02d}:00",
                    "end": f"{(hour + 1) % 24:02d}:59",
                    "branch": branch,
                    "element": element,
                }
            )
    return rows[:3]


def _twelve_officer_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    cautious = []
    for row in rows:
        officer = str(row.get("twelve_officer", ""))
        if not officer:
            continue
        counts[officer] = counts.get(officer, 0) + 1
        if officer in CAUTION_BY_OFFICER:
            cautious.append(row.get("date"))
    return {
        "counts": counts,
        "auspicious_officer_dates": [
            row.get("date") for row in rows if row.get("twelve_officer") in AUSPICIOUS_OFFICERS
        ],
        "cautious_officer_dates": cautious,
        "use": "Twelve officers guide activity fit, not outcome certainty.",
    }


def _mansion_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    auspicious = [
        row.get("date")
        for row in rows
        if row.get("twenty_eight_mansion") in AUSPICIOUS_MANSIONS
    ]
    return {
        "auspicious_mansion_dates": auspicious,
        "auspicious_count": len(auspicious),
        "mansion_sequence": [
            {"date": row.get("date"), "mansion": row.get("twenty_eight_mansion")}
            for row in rows
        ],
        "use": "Twenty-eight mansion labels are auxiliary and must be read with the day officer.",
    }


def _huangdao_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ratings: dict[str, int] = {}
    for row in rows:
        rating = str(row.get("rating", ""))
        ratings[rating] = ratings.get(rating, 0) + 1
    best = next((row.get("date") for row in rows if row.get("rating") == "favorable"), None)
    return {
        "rating_counts": ratings,
        "huangdao_dates": [row.get("date") for row in rows if row.get("huangdao") is True],
        "cautious_dates": [row.get("date") for row in rows if row.get("rating") == "cautious"],
        "best_date": best,
    }


def _hour_selection_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0
    by_date = {}
    element_counts: dict[str, int] = {}
    for row in rows:
        hours = row.get("recommended_hours")
        if not isinstance(hours, list):
            hours = []
        total += len(hours)
        by_date[str(row.get("date", ""))] = len(hours)
        for item in hours:
            if isinstance(item, dict):
                element = str(item.get("element", ""))
                if element:
                    element_counts[element] = element_counts.get(element, 0) + 1
    return {
        "total_recommended_hours": total,
        "recommended_hour_count_by_date": by_date,
        "element_counts": element_counts,
        "use": "Recommended hours are symbolic time windows and must be checked against practical constraints.",
    }


def _risk_boundary_analysis(rows: list[dict[str, Any]], provider_quality: str) -> dict[str, Any]:
    avoid_terms = sorted(
        {
            str(term)
            for row in rows
            for term in (row.get("avoid") if isinstance(row.get("avoid"), list) else [])
        }
    )
    high_risk_dates = [
        row.get("date")
        for row in rows
        if row.get("rating") == "cautious" or any("high-stakes" in str(item) for item in row.get("avoid", []))
    ]
    return {
        "avoid_terms": avoid_terms,
        "high_risk_dates": high_risk_dates,
        "provider_quality": provider_quality,
        "boundary": "Do not use symbolic xuanze output for high-stakes scheduling without ordinary verification.",
    }
