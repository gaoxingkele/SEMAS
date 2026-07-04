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
    BRANCH_HIDDEN_STEM_WEIGHTS,
    BRANCHES,
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

ELEMENT_GENERATES = {
    "Wood": "Fire",
    "Fire": "Earth",
    "Earth": "Metal",
    "Metal": "Water",
    "Water": "Wood",
}

ELEMENT_CONTROLS = {
    "Wood": "Earth",
    "Earth": "Water",
    "Water": "Fire",
    "Fire": "Metal",
    "Metal": "Wood",
}

BRANCH_SEASONS = {
    "Yin": "spring",
    "Mao": "spring",
    "Chen": "spring",
    "Si": "summer",
    "Wu": "summer",
    "Wei": "summer",
    "Shen": "autumn",
    "You": "autumn",
    "Xu": "autumn",
    "Hai": "winter",
    "Zi": "winter",
    "Chou": "winter",
}

SEASON_ELEMENTS = {
    "spring": "Wood",
    "summer": "Fire",
    "autumn": "Metal",
    "winter": "Water",
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

BRANCH_INTERACTION_PAIRS = {
    "clash": {
        ("Zi", "Wu"),
        ("Chou", "Wei"),
        ("Yin", "Shen"),
        ("Mao", "You"),
        ("Chen", "Xu"),
        ("Si", "Hai"),
    },
    "combine": {
        ("Zi", "Chou"),
        ("Yin", "Hai"),
        ("Mao", "Xu"),
        ("Chen", "You"),
        ("Si", "Shen"),
        ("Wu", "Wei"),
    },
    "harm": {
        ("Zi", "Wei"),
        ("Chou", "Wu"),
        ("Yin", "Si"),
        ("Mao", "Chen"),
        ("Shen", "Hai"),
        ("You", "Xu"),
    },
    "break": {
        ("Zi", "You"),
        ("Chou", "Chen"),
        ("Yin", "Hai"),
        ("Mao", "Wu"),
        ("Si", "Shen"),
        ("Wei", "Xu"),
    },
    "punishment": {
        ("Zi", "Mao"),
        ("Yin", "Si"),
        ("Si", "Shen"),
        ("Yin", "Shen"),
        ("Chou", "Xu"),
        ("Xu", "Wei"),
        ("Chou", "Wei"),
        ("Chen", "Chen"),
        ("Wu", "Wu"),
        ("You", "You"),
        ("Hai", "Hai"),
    },
}

BRANCH_INTERACTION_SEVERITY = {
    "clash": 5,
    "punishment": 4,
    "harm": 3,
    "break": 2,
    "combine": 1,
}


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
    phase = TEN_YEAR_PHASES[min(age // 10, len(TEN_YEAR_PHASES) - 1)]
    bazi_evidence = _bazi_evidence(year, age, label, stem, branch, focus, useful, dominant, context, deep_analysis)
    event_markers = _event_markers(category, intensity, age, phase, bazi_evidence)
    return {
        "year": year,
        "age": age,
        "ganzhi": label,
        "phase": phase,
        "elements": {"stem": stem_element, "branch": branch_element, "focus": focus},
        "bazi_evidence": bazi_evidence,
        "event_markers": event_markers,
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
    branch_interactions = _branch_interactions(branch, context.get("pillars", {}))
    useful_state = _useful_state(focus, [STEM_ELEMENTS[stem], BRANCH_ELEMENTS[branch]], useful, dominant)
    elements = {"stem": STEM_ELEMENTS[stem], "branch": BRANCH_ELEMENTS[branch], "focus": focus}
    element_flow = _element_flow(elements, useful, dominant)
    hidden_stem_flow = _hidden_stem_flow(branch, useful, dominant)
    luck_pillar_interactions = _luck_pillar_interactions(label, stem, branch, active_luck)
    interaction_pressure_summary = _interaction_pressure_summary(branch_interactions, luck_pillar_interactions)
    classical_timing_trace = _classical_timing_trace(
        level="annual",
        current_pillar=label,
        active_luck=active_luck,
        useful_state=useful_state,
        pressure_summary=interaction_pressure_summary,
        deep_analysis=deep_analysis,
    )
    return {
        "annual_pillar": label,
        "annual_ten_gods": annual_ten_gods,
        "elements": elements,
        "element_flow": element_flow,
        "hidden_stem_flow": hidden_stem_flow,
        "active_major_luck": active_luck,
        "luck_pillar_interactions": luck_pillar_interactions,
        "interaction_pressure_summary": interaction_pressure_summary,
        "classical_timing_trace": classical_timing_trace,
        "useful_state": useful_state,
        "natal_pillar_matches": natal_matches,
        "branch_interactions": branch_interactions,
        "interpretation_basis": [
            "annual stem/branch ten-god relationship to day master",
            "active major-luck period when available",
            "useful-element and dominant-element interaction",
            "five-element flow relation to useful and dominant elements",
            "hidden-stem flow relation to useful and dominant elements",
            "current pillar interaction with active major-luck pillar",
            "ranked pressure summary across natal and major-luck branch interactions",
            "classical layered timing trace from natal chart to major luck and current pillar",
            "direct natal pillar match and branch-interaction flags",
        ],
    }


def _classical_timing_trace(
    *,
    level: str,
    current_pillar: str,
    active_luck: dict[str, Any],
    useful_state: str,
    pressure_summary: dict[str, Any],
    deep_analysis: dict[str, Any],
) -> dict[str, Any]:
    methodology = deep_analysis.get("classical_layered_methodology")
    if not isinstance(methodology, dict):
        methodology = {}
    pressure_level = str(pressure_summary.get("pressure_level") or "none") if isinstance(pressure_summary, dict) else "none"
    active_luck_pillar = str(active_luck.get("ganzhi") or "") if isinstance(active_luck, dict) else ""
    return {
        "schema_version": "classical-timing-trace-v1",
        "level": level,
        "current_pillar": current_pillar,
        "methodology_source": methodology.get("schema_version", ""),
        "source_ids": ["bazi_sanming_tonghui", "bazi_early_sanming", "bazi_tianbu_zhenyuan"],
        "natal_layer": "overall chart sets the structural baseline",
        "major_luck_layer": active_luck_pillar or "no active major-luck pillar available",
        "current_layer": (
            "annual trigger" if level == "annual" else "monthly implementation"
        ),
        "useful_state": useful_state,
        "pressure_level": pressure_level,
        "decision_rule": (
            "first preserve the natal pattern baseline, then read major-luck background, "
            "then judge the current pillar's ten-god, element flow, useful-state, and ranked interactions"
        ),
        "boundary": "Classical timing trace is a structured interpretive scaffold, not a deterministic event guarantee.",
    }


def _element_flow(elements: dict[str, str], useful: str, dominant: str) -> list[dict[str, str]]:
    targets = [("useful_element", useful), ("dominant_element", dominant)]
    rows: list[dict[str, str]] = []
    for source_slot in ("stem", "branch", "focus"):
        source = elements.get(source_slot, "")
        if source not in ELEMENTS:
            continue
        for target_role, target in targets:
            if target not in ELEMENTS:
                continue
            rows.append(
                {
                    "source_slot": source_slot,
                    "source_element": source,
                    "target_role": target_role,
                    "target_element": target,
                    "relation": _element_relation(source, target),
                }
            )
    return rows


def _element_relation(source: str, target: str) -> str:
    if source == target:
        return "same"
    if ELEMENT_GENERATES.get(source) == target:
        return "generate"
    if ELEMENT_GENERATES.get(target) == source:
        return "drain"
    if ELEMENT_CONTROLS.get(source) == target:
        return "control"
    if ELEMENT_CONTROLS.get(target) == source:
        return "consume"
    return "neutral"


def _hidden_stem_flow(branch: str, useful: str, dominant: str) -> list[dict[str, Any]]:
    targets = [("useful_element", useful), ("dominant_element", dominant)]
    rows: list[dict[str, str]] = []
    for hidden in BRANCH_HIDDEN_STEM_WEIGHTS.get(branch, []):
        hidden_stem = str(hidden.get("stem", ""))
        source = STEM_ELEMENTS.get(hidden_stem, "")
        if source not in ELEMENTS:
            continue
        seasonal = _seasonal_strength(branch, source)
        base_weight = float(hidden.get("weight", 0.0) or 0.0)
        for target_role, target in targets:
            if target not in ELEMENTS:
                continue
            rows.append(
                {
                    "branch": branch,
                    "hidden_stem": hidden_stem,
                    "hidden_stem_role": str(hidden.get("role", "")),
                    "weight": base_weight,
                    "season": seasonal["season"],
                    "seasonal_phase": seasonal["phase"],
                    "seasonal_factor": seasonal["factor"],
                    "adjusted_weight": round(base_weight * float(seasonal["factor"]), 3),
                    "source_element": source,
                    "target_role": target_role,
                    "target_element": target,
                    "relation": _element_relation(source, target),
                }
            )
    return rows


def _seasonal_strength(branch: str, element: str) -> dict[str, Any]:
    season = BRANCH_SEASONS.get(branch, "")
    season_element = SEASON_ELEMENTS.get(season, "")
    if branch in {"Chen", "Wei", "Xu", "Chou"} and element == "Earth":
        return {"season": season, "phase": "prosperous", "factor": 1.2}
    if element == season_element:
        return {"season": season, "phase": "prosperous", "factor": 1.2}
    if season_element and ELEMENT_GENERATES.get(season_element) == element:
        return {"season": season, "phase": "supporting", "factor": 1.1}
    if season_element and ELEMENT_GENERATES.get(element) == season_element:
        return {"season": season, "phase": "resting", "factor": 0.9}
    if season_element and ELEMENT_CONTROLS.get(element) == season_element:
        return {"season": season, "phase": "confined", "factor": 0.8}
    if season_element and ELEMENT_CONTROLS.get(season_element) == element:
        return {"season": season, "phase": "weak", "factor": 0.7}
    return {"season": season, "phase": "neutral", "factor": 1.0}


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


def _luck_pillar_interactions(
    current_label: str,
    current_stem: str,
    current_branch: str,
    active_luck: dict[str, Any],
) -> dict[str, Any]:
    luck_label = str(active_luck.get("ganzhi") or "")
    if not luck_label:
        return {
            "current_pillar": current_label,
            "major_luck_pillar": "",
            "active": False,
            "stem_relation": {},
            "branch_relations": [],
            "summary": "no_active_major_luck",
        }
    luck_stem, luck_branch = _split_ganzhi(luck_label)
    current_stem_element = STEM_ELEMENTS.get(current_stem, "")
    luck_stem_element = STEM_ELEMENTS.get(luck_stem, "")
    stem_relation = {
        "current_stem": current_stem,
        "current_stem_element": current_stem_element,
        "major_luck_stem": luck_stem,
        "major_luck_stem_element": luck_stem_element,
        "relation_to_major_luck": _element_relation(current_stem_element, luck_stem_element),
        "relation_from_major_luck": _element_relation(luck_stem_element, current_stem_element),
    }
    branch_relations = []
    for relation, pairs in BRANCH_INTERACTION_PAIRS.items():
        if _branch_pair(current_branch, luck_branch) in pairs:
            branch_relations.append(
                {
                    "current_branch": current_branch,
                    "major_luck_branch": luck_branch,
                    "relation": relation,
                    "severity": BRANCH_INTERACTION_SEVERITY.get(relation, 0),
                }
            )
    summary = "branch_interaction" if branch_relations else "stem_only_or_neutral"
    return {
        "current_pillar": current_label,
        "major_luck_pillar": luck_label,
        "active": True,
        "stem_relation": stem_relation,
        "branch_relations": branch_relations,
        "summary": summary,
    }


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


def _branch_interactions(branch: str, pillars: object) -> list[dict[str, str]]:
    if not branch or not isinstance(pillars, dict):
        return []
    interactions = []
    for pillar, natal_label in pillars.items():
        natal_branch = _branch_from_ganzhi(str(natal_label))
        if not natal_branch:
            continue
        for relation, pairs in BRANCH_INTERACTION_PAIRS.items():
            if _branch_pair(branch, natal_branch) not in pairs:
                continue
            interactions.append(
                {
                    "pillar": str(pillar),
                    "annual_branch": branch,
                    "natal_branch": natal_branch,
                    "relation": relation,
                    "severity": BRANCH_INTERACTION_SEVERITY.get(relation, 0),
                }
            )
    return interactions


def _interaction_pressure_summary(
    natal_branch_interactions: list[dict[str, Any]],
    luck_pillar_interactions: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in natal_branch_interactions:
        rows.append(
            {
                "source": "natal",
                "relation": item.get("relation", ""),
                "severity": int(item.get("severity", 0) or 0),
                "target": item.get("pillar", ""),
            }
        )
    luck_branch_relations = (
        luck_pillar_interactions.get("branch_relations", [])
        if isinstance(luck_pillar_interactions, dict)
        else []
    )
    if isinstance(luck_branch_relations, list):
        for item in luck_branch_relations:
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "source": "major_luck",
                    "relation": item.get("relation", ""),
                    "severity": int(item.get("severity", 0) or 0),
                    "target": item.get("major_luck_branch", ""),
                }
            )
    rows.sort(key=lambda item: (-int(item.get("severity", 0) or 0), str(item.get("source", ""))))
    max_severity = int(rows[0].get("severity", 0) or 0) if rows else 0
    pressure_level = (
        "high" if max_severity >= 5 else "elevated" if max_severity >= 4 else "moderate" if max_severity >= 3 else "low" if rows else "none"
    )
    return {
        "schema_version": "interaction-pressure-summary-v1",
        "max_severity": max_severity,
        "pressure_level": pressure_level,
        "interaction_count": len(rows),
        "major_luck_interaction_count": sum(1 for item in rows if item.get("source") == "major_luck"),
        "natal_interaction_count": sum(1 for item in rows if item.get("source") == "natal"),
        "top_interactions": rows[:5],
    }


def _branch_pair(left: str, right: str) -> tuple[str, str]:
    if left == right:
        return left, right
    return tuple(sorted((left, right), key=BRANCHES.index))  # type: ignore[return-value]


def _branch_from_ganzhi(label: str) -> str:
    stem = next((candidate for candidate in STEMS if label.startswith(candidate)), "")
    branch = label[len(stem) :] if stem else ""
    return branch if branch in BRANCHES else ""


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


def _event_markers(
    category: str,
    intensity: str,
    age: int,
    phase: str,
    bazi_evidence: dict[str, Any],
) -> dict[str, Any]:
    ten_gods_raw = bazi_evidence.get("annual_ten_gods", {}) if isinstance(bazi_evidence, dict) else {}
    ten_gods = set(ten_gods_raw.values()) if isinstance(ten_gods_raw, dict) else set()
    useful_state = str(bazi_evidence.get("useful_state", "")) if isinstance(bazi_evidence, dict) else ""
    active_luck = bazi_evidence.get("active_major_luck", {}) if isinstance(bazi_evidence, dict) else {}
    natal_matches = bazi_evidence.get("natal_pillar_matches", []) if isinstance(bazi_evidence, dict) else []
    supported = useful_state in {"useful_element_activated", "useful_element_present"}
    pressured = useful_state == "dominant_element_reinforced"
    activated = bool(active_luck) or bool(natal_matches)
    career_launch = category == "expression" and "expression" in ten_gods and (supported or activated or phase == "career entry")
    role_power = category == "authority" and "authority" in ten_gods and (supported or pressured or activated)
    role_transition = (
        category in {"friends", "learning", "wealth"}
        and bool({"authority", "peer", "resource"} & ten_gods)
        and activated
        and age >= 18
    )
    business_power = category == "wealth" and "wealth" in ten_gods and (supported or activated)
    relationship = (
        category in {"friends", "wealth"}
        and bool({"peer", "wealth"} & ten_gods)
        and (intensity in {"active", "high-volatility"} or activated)
    )
    movement = (phase in {"strategy revision", "career entry"} and activated) or (intensity == "high-volatility" and activated)
    return {
        "career_launch": career_launch,
        "role_power": role_power,
        "role_transition": role_transition,
        "business_power": business_power,
        "relationship": relationship,
        "movement": movement,
        "study_exam": (
            category in {"learning", "authority"}
            and bool({"resource", "authority"} & ten_gods)
            and (supported or intensity in {"constructive", "active"})
        ),
        "public_visibility": category == "expression" and "expression" in ten_gods,
        "health_pressure": intensity == "high-volatility" and pressured,
        "adult_career_stage": age >= 18,
        "basis": [
            "annual category",
            "annual intensity",
            "annual ten-god pair",
            "useful-state",
            "major-luck activity",
            "natal-pillar activation",
            "ten-year life phase",
            "age-stage boundary",
        ],
    }


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
