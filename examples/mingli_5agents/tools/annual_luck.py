"""Annual luck-cycle helper for structured mingli reports.

The module is intentionally deterministic and provider-neutral. It turns the
shared chart context into a year-by-year symbolic profile that downstream
agents can debate, render, benchmark, and later replace with an authoritative
calendar provider.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from examples.mingli_5agents.tools.calendar_core import (
    BRANCH_ELEMENTS,
    ELEMENTS,
    STEM_ELEMENTS,
    STEMS,
    ganzhi,
    year_ganzhi,
)
from examples.mingli_5agents.tools.bazi_deep_analysis import _approx_ten_god


CATEGORY_BY_ELEMENT = {
    "Wood": ("friends", "peer competition, network support, collaboration boundaries"),
    "Fire": ("expression", "visibility, output, reputation, study by practice"),
    "Earth": ("wealth", "finance, assets, family responsibility, resource management"),
    "Metal": ("authority", "career rules, leadership, title, compliance, pressure"),
    "Water": ("learning", "study, credentials, mobility, planning, emotional buffering"),
}

TEN_YEAR_PHASES = [
    "foundation",
    "skill formation",
    "peer expansion",
    "career entry",
    "responsibility growth",
    "wealth structuring",
    "authority pressure",
    "strategy revision",
    "relationship calibration",
    "legacy consolidation",
]


def build_annual_luck(
    birth: dict[str, Any],
    bazi_chart: dict[str, Any],
    *,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    """Build a structured annual symbolic trend table.

    Defaults to birth year through the current local year. Callers can pass an
    explicit range for tests, historical review, or UI pagination.
    """
    birth_year = int(birth["year"])
    start = int(start_year) if start_year is not None else birth_year
    end = int(end_year) if end_year is not None else date.today().year
    if start < birth_year:
        raise ValueError("annual luck start_year cannot be before birth year")
    if end < start:
        raise ValueError("annual luck end_year cannot be before start_year")

    context = bazi_chart["context"]
    natal_counts = context["element_counts"]
    dominant = context["dominant_element"]
    useful = context["useful_element"]
    deep_analysis = bazi_chart.get("deep_analysis", {}) if isinstance(bazi_chart.get("deep_analysis"), dict) else {}
    rows = [
        _annual_row(year, birth_year, natal_counts, dominant, useful, context, deep_analysis)
        for year in range(start, end + 1)
    ]
    return {
        "range": {"start_year": start, "end_year": end, "count": len(rows)},
        "basis": {
            "provider": context.get("provider"),
            "provider_quality": context.get("provider_quality"),
            "natal_pillars": context["pillars"],
            "dominant_element": dominant,
            "useful_element": useful,
        },
        "rows": rows,
        "phase_summary": _phase_summary(rows),
        "caution": "Annual rows are symbolic trend prompts, not deterministic event predictions.",
    }


def _annual_row(
    year: int,
    birth_year: int,
    natal_counts: dict[str, int],
    dominant: str,
    useful: str,
    context: dict[str, Any],
    deep_analysis: dict[str, Any],
) -> dict[str, Any]:
    label = year_ganzhi(year)
    stem, branch = _split_ganzhi(label)
    stem_element = STEM_ELEMENTS[stem]
    branch_element = BRANCH_ELEMENTS[branch]
    annual_elements = [stem_element, branch_element]
    focus = _focus_element(annual_elements, natal_counts, useful)
    category, theme = CATEGORY_BY_ELEMENT[focus]
    age = year - birth_year
    intensity = _intensity(annual_elements, dominant, useful)
    return {
        "year": year,
        "age": age,
        "ganzhi": label,
        "phase": TEN_YEAR_PHASES[min(age // 10, len(TEN_YEAR_PHASES) - 1)],
        "elements": {"stem": stem_element, "branch": branch_element, "focus": focus},
        "bazi_evidence": _bazi_evidence(year, age, label, stem, branch, focus, useful, dominant, context, deep_analysis),
        "category": category,
        "intensity": intensity,
        "finance": _finance_theme(category, intensity),
        "official_career": _official_theme(category, intensity),
        "career": _career_theme(category, intensity),
        "study": _study_theme(category, intensity),
        "relationship": _relationship_theme(category, intensity),
        "friends": _friends_theme(category, intensity),
        "leadership": _leadership_theme(category, intensity),
        "children_family": _children_theme(category, intensity),
        "theme": theme,
        "risk_notes": _risk_notes(category, intensity),
    }


def _bazi_evidence(
    year: int,
    age: int,
    label: str,
    stem: str,
    branch: str,
    focus: str,
    useful: str,
    dominant: str,
    context: dict[str, Any],
    deep_analysis: dict[str, Any],
) -> dict[str, Any]:
    """Bind each annual row to auditable BaZi factors."""
    day_master = str(deep_analysis.get("day_master") or _split_ganzhi(str(context.get("pillars", {}).get("day", "JiaZi")))[0])
    annual_ten_gods = {
        "stem": _approx_ten_god(day_master, stem),
        "branch": _approx_ten_god(day_master, _element_representative_stem(BRANCH_ELEMENTS[branch])),
    }
    active_luck = _active_major_luck(age, year, deep_analysis.get("major_luck"))
    natal_matches = _natal_matches(label, context.get("pillars", {}))
    useful_state = _useful_state(focus, [STEM_ELEMENTS[stem], BRANCH_ELEMENTS[branch]], useful, dominant)
    return {
        "annual_pillar": label,
        "annual_ten_gods": annual_ten_gods,
        "active_major_luck": active_luck,
        "useful_state": useful_state,
        "natal_pillar_matches": natal_matches,
        "interpretation_basis": [
            "annual stem/branch ten-god relationship to day master",
            "active major-luck period when available",
            "useful-element and dominant-element interaction",
            "direct natal pillar match flags",
        ],
    }


def _active_major_luck(age: int, year: int, major_luck: object) -> dict[str, Any]:
    if not isinstance(major_luck, list):
        return {}
    for item in major_luck:
        if not isinstance(item, dict):
            continue
        start_age = item.get("start_age")
        end_age = item.get("end_age")
        start_year = item.get("start_year")
        end_year = item.get("end_year")
        age_match = isinstance(start_age, int) and isinstance(end_age, int) and start_age <= age <= end_age
        year_match = isinstance(start_year, int) and isinstance(end_year, int) and start_year <= year <= end_year
        if age_match or year_match:
            return {
                "index": item.get("index"),
                "ganzhi": item.get("ganzhi", ""),
                "start_age": start_age,
                "end_age": end_age,
                "start_year": start_year,
                "end_year": end_year,
            }
    return {}


def _natal_matches(label: str, pillars: object) -> list[dict[str, str]]:
    if not isinstance(pillars, dict):
        return []
    matches = []
    for pillar, natal_label in pillars.items():
        if natal_label == label:
            matches.append(
                {
                    "pillar": str(pillar),
                    "relation": "same_ganzhi",
                    "note": "Annual pillar repeats a natal pillar; treat as an activation flag, not a certain event.",
                }
            )
    return matches


def _useful_state(focus: str, annual_elements: list[str], useful: str, dominant: str) -> str:
    if annual_elements.count(dominant) == 2:
        return "dominant_element_reinforced"
    if focus == useful:
        return "useful_element_activated"
    if useful in annual_elements:
        return "useful_element_present"
    return "neutral_or_indirect"


def _element_representative_stem(element: str) -> str:
    return next(stem for stem, stem_element in STEM_ELEMENTS.items() if stem_element == element)


def _split_ganzhi(label: str) -> tuple[str, str]:
    stem = next(candidate for candidate in STEMS if label.startswith(candidate))
    return stem, label[len(stem):]


def _focus_element(
    annual_elements: list[str],
    natal_counts: dict[str, int],
    useful: str,
) -> str:
    if useful in annual_elements:
        return useful
    return max(
        ELEMENTS,
        key=lambda element: (
            annual_elements.count(element),
            -natal_counts.get(element, 0),
            -ELEMENTS.index(element),
        ),
    )


def _intensity(annual_elements: list[str], dominant: str, useful: str) -> str:
    if annual_elements.count(dominant) == 2:
        return "high-volatility"
    if useful in annual_elements:
        return "constructive"
    if dominant in annual_elements:
        return "active"
    return "moderate"


def _finance_theme(category: str, intensity: str) -> str:
    if category == "wealth":
        return "stronger money-management and asset-allocation theme; avoid leverage."
    if intensity == "high-volatility":
        return "cash flow can move quickly; require budgets and written terms."
    return "steady finances favor planning over speculation."


def _official_theme(category: str, intensity: str) -> str:
    if category == "authority":
        return "rules, title, audits, leadership, or institutional pressure become central."
    if intensity == "constructive":
        return "authority relationships can improve through preparation and evidence."
    return "keep compliance and reporting rhythm clear."


def _career_theme(category: str, intensity: str) -> str:
    if category == "expression":
        return "output, visibility, sales, teaching, or public delivery are emphasized."
    if category == "authority":
        return "career advancement depends on discipline, contracts, and role clarity."
    if category == "wealth":
        return "career choices are tied to revenue, assets, operations, or family duties."
    if intensity == "high-volatility":
        return "career push is strong but should be paced to avoid conflict."
    return "career improves through consistent execution."


def _study_theme(category: str, intensity: str) -> str:
    if category == "learning":
        return "best suited for study, credentials, research, travel, or strategic review."
    if intensity == "constructive":
        return "learning is useful when converted into a practical system."
    return "study should support immediate work needs."


def _relationship_theme(category: str, intensity: str) -> str:
    if category == "wealth":
        return "marriage and romantic issues may connect with money, home, or duty."
    if category == "friends":
        return "peer influence is strong; protect couple boundaries from outside noise."
    if intensity == "high-volatility":
        return "direct speech can heat up conflict; slow down before decisions."
    return "relationships benefit from predictable communication."


def _friends_theme(category: str, intensity: str) -> str:
    if category == "friends":
        return "friends and partners are active; choose collaborators carefully."
    if intensity == "high-volatility":
        return "competition and comparison can increase."
    return "networking is useful when roles are explicit."


def _leadership_theme(category: str, intensity: str) -> str:
    if category == "authority":
        return "leaders, managers, clients, or regulators carry more weight."
    if category == "expression":
        return "visibility can attract support if communication stays measured."
    return "leadership ties improve through reliability."


def _children_theme(category: str, intensity: str) -> str:
    if category == "expression":
        return "children, students, juniors, or creative outputs require attention."
    if category == "wealth":
        return "family responsibility and practical support are highlighted."
    return "family ties need steady time and clear expectations."


def _risk_notes(category: str, intensity: str) -> list[str]:
    notes = ["symbolic tendency only"]
    if intensity == "high-volatility":
        notes.append("avoid impulsive commitments")
    if category == "wealth":
        notes.append("separate investment decisions from divination")
    if category == "authority":
        notes.append("verify contracts, policies, and reporting obligations")
    if category == "friends":
        notes.append("separate friendship from financial guarantees")
    return notes


def _phase_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize annual rows by life phase while preserving row-level traceability."""
    phases: list[tuple[str, list[tuple[int, dict[str, Any]]]]] = []
    for index, row in enumerate(rows):
        phase = str(row.get("phase", "unknown"))
        if not phases or phases[-1][0] != phase:
            phases.append((phase, []))
        phases[-1][1].append((index, row))
    return [_phase_summary_row(phase, indexed_rows) for phase, indexed_rows in phases]


def _phase_summary_row(phase: str, indexed_rows: list[tuple[int, dict[str, Any]]]) -> dict[str, Any]:
    rows = [row for _index, row in indexed_rows]
    category_counts = _counts(row.get("category") for row in rows)
    intensity_counts = _counts(row.get("intensity") for row in rows)
    dominant_category = _dominant_key(category_counts)
    return {
        "phase": phase,
        "start_year": rows[0].get("year"),
        "end_year": rows[-1].get("year"),
        "start_age": rows[0].get("age"),
        "end_age": rows[-1].get("age"),
        "year_count": len(rows),
        "dominant_category": dominant_category,
        "category_counts": category_counts,
        "intensity_counts": intensity_counts,
        "high_volatility_years": [row.get("year") for row in rows if row.get("intensity") == "high-volatility"],
        "constructive_years": [row.get("year") for row in rows if row.get("intensity") == "constructive"],
        "topic_highlights": _topic_highlights(indexed_rows),
        "source": "annual_luck.rows",
        "source_row_indexes": [index for index, _row in indexed_rows],
        "boundary": "Phase summaries compress symbolic annual rows; inspect source_row_indexes for year-level details.",
    }


def _topic_highlights(indexed_rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    topic_keys = [
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    ]
    highlights = {}
    for topic in topic_keys:
        message_counts = _counts(row.get(topic) for _index, row in indexed_rows)
        dominant_message = _dominant_key(message_counts)
        source_years = [
            row.get("year")
            for _index, row in indexed_rows
            if row.get(topic) == dominant_message
        ]
        highlights[topic] = {
            "dominant_message": dominant_message,
            "supporting_year_count": len(source_years),
            "source_years": source_years,
        }
    return highlights


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _dominant_key(counts: dict[str, int]) -> str:
    if not counts:
        return ""
    return min(counts, key=lambda key: (-counts[key], key))
