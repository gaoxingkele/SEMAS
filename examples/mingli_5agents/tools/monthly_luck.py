"""Monthly luck-cycle helper for focused annual mingli analysis."""

from __future__ import annotations

from datetime import date
from typing import Any

from examples.mingli_5agents.tools.annual_luck import (
    CATEGORY_BY_ELEMENT,
    _bazi_evidence,
    _career_theme,
    _children_theme,
    _finance_theme,
    _friends_theme,
    _intensity,
    _leadership_theme,
    _official_theme,
    _relationship_theme,
    _risk_notes,
    _study_theme,
)
from examples.mingli_5agents.tools.calendar_core import (
    BRANCH_ELEMENTS,
    MONTH_BRANCHES,
    STEM_ELEMENTS,
    STEMS,
    ELEMENTS,
)


MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def build_monthly_luck(
    birth: dict[str, Any],
    bazi_chart: dict[str, Any],
    *,
    years: list[int] | None = None,
) -> dict[str, Any]:
    """Build month-by-month symbolic rows for selected years.

    If no years are supplied, only the latest three years from the annual range
    are expanded. This keeps default reports useful without producing hundreds
    of rows for older cases.
    """
    context = bazi_chart["context"]
    deep_analysis = bazi_chart.get("deep_analysis", {}) if isinstance(bazi_chart.get("deep_analysis"), dict) else {}
    birth_year = int(birth["year"])
    current_year = date.today().year
    selected_years = years or list(range(max(birth_year, current_year - 2), current_year + 1))
    normalized_years = sorted({int(year) for year in selected_years if int(year) >= birth_year})
    rows = [
        _monthly_row(year, month, birth_year, context, deep_analysis)
        for year in normalized_years
        for month in range(1, 13)
    ]
    return {
        "range": {
            "years": normalized_years,
            "months_per_year": 12,
            "count": len(rows),
        },
        "basis": {
            "provider": context.get("provider"),
            "provider_quality": context.get("provider_quality"),
            "dominant_element": context["dominant_element"],
            "useful_element": context["useful_element"],
        },
        "rows": rows,
        "caution": "Monthly rows are symbolic refinements for selected years only.",
    }


def _monthly_row(
    year: int,
    month: int,
    birth_year: int,
    context: dict[str, Any],
    deep_analysis: dict[str, Any],
) -> dict[str, Any]:
    label = _month_ganzhi(year, month)
    stem = next(candidate for candidate in STEMS if label.startswith(candidate))
    branch = label[len(stem):]
    stem_element = STEM_ELEMENTS[stem]
    branch_element = BRANCH_ELEMENTS[branch]
    month_elements = [stem_element, branch_element]
    focus = _month_focus(month_elements, context["element_counts"], context["useful_element"])
    category, theme = CATEGORY_BY_ELEMENT[focus]
    intensity = _intensity(month_elements, context["dominant_element"], context["useful_element"])
    bazi_evidence = _monthly_bazi_evidence(
        year,
        month,
        birth_year,
        label,
        stem,
        branch,
        focus,
        context,
        deep_analysis,
    )
    topic_messages = {
        "finance": _finance_theme(category, intensity),
        "official_career": _official_theme(category, intensity),
        "career": _career_theme(category, intensity),
        "study": _study_theme(category, intensity),
        "relationship": _relationship_theme(category, intensity),
        "friends": _friends_theme(category, intensity),
        "leadership": _leadership_theme(category, intensity),
        "children_family": _children_theme(category, intensity),
    }
    return {
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES[month - 1],
        "ganzhi": label,
        "elements": {"stem": stem_element, "branch": branch_element, "focus": focus},
        "bazi_evidence": bazi_evidence,
        "category": category,
        "intensity": intensity,
        **topic_messages,
        "topics": _monthly_topic_bindings(topic_messages, category, intensity, context.get("provider_quality")),
        "theme": theme,
        "risk_notes": _risk_notes(category, intensity),
    }


def _monthly_topic_bindings(
    topic_messages: dict[str, str],
    category: str,
    intensity: str,
    provider_quality: Any,
) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "message": message,
            "category": category,
            "intensity": intensity,
            "source": "monthly_luck.rows",
            "source_field": key,
            "provider_quality": provider_quality,
            "boundary": "Symbolic monthly topic prompt; not deterministic prediction.",
        }
        for key, message in topic_messages.items()
    }


def _monthly_bazi_evidence(
    year: int,
    month: int,
    birth_year: int,
    label: str,
    stem: str,
    branch: str,
    focus: str,
    context: dict[str, Any],
    deep_analysis: dict[str, Any],
) -> dict[str, Any]:
    evidence = _bazi_evidence(
        year,
        year - birth_year,
        label,
        stem,
        branch,
        focus,
        context["useful_element"],
        context["dominant_element"],
        context,
        deep_analysis,
    )
    evidence["monthly_pillar"] = evidence.pop("annual_pillar")
    evidence["monthly_ten_gods"] = evidence.pop("annual_ten_gods")
    evidence["month"] = month
    evidence["interpretation_basis"] = [
        "monthly stem/branch ten-god relationship to day master",
        "active major-luck period when available",
        "useful-element and dominant-element interaction",
        "direct natal pillar match flags",
    ]
    return evidence


def _month_ganzhi(year: int, month: int) -> str:
    stem = STEMS[(year * 2 + month) % 10]
    branch = MONTH_BRANCHES[(month - 1) % 12]
    return f"{stem}{branch}"


def _month_focus(
    month_elements: list[str],
    natal_counts: dict[str, int],
    useful: str,
) -> str:
    if useful in month_elements:
        return useful
    return max(
        ELEMENTS,
        key=lambda element: (
            month_elements.count(element),
            -natal_counts.get(element, 0),
            -ELEMENTS.index(element),
        ),
    )
