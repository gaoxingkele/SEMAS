"""Structured Qi Men Dun Jia nine-palace analysis helpers."""

from __future__ import annotations

from typing import Any

PALACES = [
    {"number": 1, "name": "Kan", "direction": "North", "element": "Water"},
    {"number": 2, "name": "Kun", "direction": "Southwest", "element": "Earth"},
    {"number": 3, "name": "Zhen", "direction": "East", "element": "Wood"},
    {"number": 4, "name": "Xun", "direction": "Southeast", "element": "Wood"},
    {"number": 5, "name": "Center", "direction": "Center", "element": "Earth"},
    {"number": 6, "name": "Qian", "direction": "Northwest", "element": "Metal"},
    {"number": 7, "name": "Dui", "direction": "West", "element": "Metal"},
    {"number": 8, "name": "Gen", "direction": "Northeast", "element": "Earth"},
    {"number": 9, "name": "Li", "direction": "South", "element": "Fire"},
]

STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
USEFUL_GOD_BY_TOPIC = {
    "career": ["Open", "View", "Tianxin"],
    "wealth": ["Life", "Open", "Tianfu"],
    "relationship": ["Rest", "Six Harmony", "Taiyin"],
    "study": ["View", "Tianchong", "Moon"],
    "health": ["Life", "Tianrui", "Nine Earth"],
}


def build_qimen_deep_analysis(chart: dict[str, Any], birth: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic nine-palace Qi Men plate from chart anchors."""
    seed = (
        int(birth["year"]) * 2
        + int(birth["month"]) * 11
        + int(birth["day"])
        + int(birth["hour"])
    )
    yin_yang = "yang" if chart["context"]["season"] in {"winter", "spring"} else "yin"
    ju_number = seed % 9 + 1
    palace_rows = _provided_palaces(chart) or [
        _palace_row(index, palace, chart, seed, ju_number)
        for index, palace in enumerate(PALACES)
    ]
    duty_palace = _find_first(palace_rows, "door", chart["duty_door"])
    star_palace = _find_first(palace_rows, "star", chart["duty_star"])
    useful_gods = _provided_dict(chart, "provider_useful_gods") or _useful_gods(palace_rows)
    annual_timing = _provided_rows(chart, "provider_annual_timing") or _annual_timing(palace_rows, birth, seed)
    pattern_flags = _pattern_flags(chart, duty_palace, useful_gods)
    door_star_spirit = _door_star_spirit_analysis(palace_rows, duty_palace, star_palace)
    stem_relations = _stem_relation_analysis(palace_rows)
    useful_analysis = _useful_god_analysis(useful_gods, palace_rows)
    pattern_risk = _pattern_risk_analysis(pattern_flags, duty_palace, useful_analysis)
    timing_activation = _timing_activation_analysis(annual_timing, palace_rows, birth)
    return {
        "provider": chart.get("provider") or chart["context"].get("domain_provider") or chart["context"].get("provider"),
        "provider_quality": (
            chart.get("provider_quality")
            or chart["context"].get("domain_provider_quality")
            or chart["context"].get("provider_quality")
        ),
        "yin_yang": yin_yang,
        "ju_number": ju_number,
        "duty": {
            "door": chart["duty_door"],
            "door_palace": duty_palace["name"],
            "star": chart["duty_star"],
            "star_palace": star_palace["name"],
            "spirit": chart["spirit"],
        },
        "palaces": palace_rows,
        "useful_gods": useful_gods,
        "pattern_flags": pattern_flags,
        "annual_timing": annual_timing,
        "door_star_spirit_analysis": door_star_spirit,
        "stem_relation_analysis": stem_relations,
        "useful_god_analysis": useful_analysis,
        "pattern_risk_analysis": pattern_risk,
        "timing_activation_analysis": timing_activation,
        "method_matrix": _method_matrix(
            door_star_spirit,
            stem_relations,
            useful_analysis,
            pattern_risk,
            timing_activation,
        ),
        "caution": "Qi Men palace rows are symbolic timing scaffolds, not tactical guarantees.",
    }


def _provided_palaces(chart: dict[str, Any]) -> list[dict[str, Any]]:
    rows = chart.get("provider_palaces")
    if not isinstance(rows, list) or len(rows) != 9:
        return []
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return []
        base = PALACES[index] if index < len(PALACES) else {}
        normalized.append(
            {
                "number": int(row.get("number", base.get("number", index + 1))),
                "name": str(row.get("name", base.get("name", f"Palace{index + 1}"))),
                "direction": str(row.get("direction", base.get("direction", ""))),
                "element": str(row.get("element", base.get("element", ""))),
                "door": str(row.get("door", "")),
                "star": str(row.get("star", "")),
                "spirit": str(row.get("spirit", "")),
                "heaven_stem": str(row.get("heaven_stem", "")),
                "earth_stem": str(row.get("earth_stem", "")),
                "theme": str(row.get("theme", "provider supplied palace")),
                "judgment": str(row.get("judgment", "provider")),
            }
        )
    return normalized


def _provided_dict(chart: dict[str, Any], key: str) -> dict[str, Any]:
    value = chart.get(key)
    return dict(value) if isinstance(value, dict) else {}


def _provided_rows(chart: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = chart.get(key)
    if not isinstance(rows, list) or not rows:
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _palace_row(
    index: int,
    palace: dict[str, Any],
    chart: dict[str, Any],
    seed: int,
    ju_number: int,
) -> dict[str, Any]:
    doors = chart["door_cycle"]
    stars = chart["star_cycle"]
    spirits = chart["spirit_cycle"]
    door = doors[(seed + index + ju_number) % len(doors)]
    star = stars[(seed + index * 2 + ju_number) % len(stars)]
    spirit = spirits[(seed + index * 3 + ju_number) % len(spirits)]
    heaven_stem = STEMS[(seed + index) % len(STEMS)]
    earth_stem = STEMS[(seed + ju_number + index) % len(STEMS)]
    return {
        **palace,
        "door": door,
        "star": star,
        "spirit": spirit,
        "heaven_stem": heaven_stem,
        "earth_stem": earth_stem,
        "theme": _theme_for(door, star),
        "judgment": _judgment_for(door, star, spirit),
    }


def _find_first(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next((row for row in rows if row.get(key) == value), rows[0])


def _useful_gods(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    useful = {}
    for topic, markers in USEFUL_GOD_BY_TOPIC.items():
        row = next(
            (
                palace
                for palace in rows
                if palace["door"] in markers or palace["star"] in markers or palace["spirit"] in markers
            ),
            rows[0],
        )
        useful[topic] = {
            "palace": row["name"],
            "direction": row["direction"],
            "door": row["door"],
            "star": row["star"],
            "spirit": row["spirit"],
            "judgment": row["judgment"],
        }
    return useful


def _pattern_flags(
    chart: dict[str, Any],
    duty_palace: dict[str, Any],
    useful_gods: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    flags = [
        {
            "name": chart["pattern"],
            "palace": duty_palace["name"],
            "meaning": "timing posture from duty door and palace context",
        }
    ]
    if useful_gods["career"]["palace"] == useful_gods["wealth"]["palace"]:
        flags.append(
            {
                "name": "career-wealth resonance",
                "palace": useful_gods["career"]["palace"],
                "meaning": "career action and money handling share one palace focus",
            }
        )
    return flags


def _annual_timing(
    rows: list[dict[str, Any]],
    birth: dict[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    birth_year = int(birth["year"])
    start = int(birth.get("annual_start_year", birth_year))
    end = int(birth.get("annual_end_year", min(start + 2, birth_year + 60)))
    return [
        {
            "year": year,
            "age": year - birth_year,
            "palace": rows[(seed + year - birth_year) % len(rows)]["name"],
            "door": rows[(seed + year - birth_year) % len(rows)]["door"],
            "judgment": rows[(seed + year - birth_year) % len(rows)]["judgment"],
        }
        for year in range(start, end + 1)
    ]


def _theme_for(door: str, star: str) -> str:
    if door in {"Open", "View"}:
        return "visibility, decision, office, communication"
    if door in {"Life", "Rest"}:
        return "resources, stability, recovery, relationship pacing"
    if star in {"Tianfu", "Tianxin"}:
        return "support, planning, leadership, orderly execution"
    return "constraint management, risk review, adaptive timing"


def _judgment_for(door: str, star: str, spirit: str) -> str:
    if door in {"Open", "Life"} and spirit not in {"White Tiger", "Black Tortoise"}:
        return "constructive"
    if door in {"Death", "Fear", "Harm"}:
        return "cautious"
    if star in {"Tianfu", "Tianxin"} or spirit in {"Nine Earth", "Nine Heaven", "Six Harmony"}:
        return "supportive"
    return "mixed"


def _door_star_spirit_analysis(
    rows: list[dict[str, Any]],
    duty_palace: dict[str, Any],
    star_palace: dict[str, Any],
) -> dict[str, Any]:
    distribution: dict[str, int] = {}
    combinations = []
    for row in rows:
        judgment = str(row.get("judgment", "mixed"))
        distribution[judgment] = distribution.get(judgment, 0) + 1
        combinations.append(
            {
                "palace": row.get("name"),
                "door": row.get("door"),
                "star": row.get("star"),
                "spirit": row.get("spirit"),
                "judgment": judgment,
                "role": _combination_role(str(row.get("door", "")), str(row.get("star", "")), str(row.get("spirit", ""))),
            }
        )
    return {
        "duty_door_palace": duty_palace.get("name"),
        "duty_star_palace": star_palace.get("name"),
        "judgment_distribution": distribution,
        "combinations": combinations,
    }


def _stem_relation_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    relations = []
    for row in rows:
        heaven = str(row.get("heaven_stem", ""))
        earth = str(row.get("earth_stem", ""))
        relations.append(
            {
                "palace": row.get("name"),
                "heaven_stem": heaven,
                "earth_stem": earth,
                "relation": _stem_relation(heaven, earth),
                "risk": _stem_relation_risk(heaven, earth),
            }
        )
    return {
        "relations": relations,
        "same_stem_count": sum(1 for item in relations if item["relation"] == "same"),
        "use": "Compare heaven and earth stems as symbolic alignment/friction, not factual causation.",
    }


def _useful_god_analysis(
    useful_gods: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    palace_lookup = {row.get("name"): row for row in rows}
    topic_rows = {}
    for topic, useful in useful_gods.items():
        palace = palace_lookup.get(useful.get("palace"), {})
        topic_rows[topic] = {
            "palace": useful.get("palace"),
            "direction": useful.get("direction"),
            "door": useful.get("door"),
            "star": useful.get("star"),
            "spirit": useful.get("spirit"),
            "judgment": useful.get("judgment"),
            "element": palace.get("element"),
            "theme": palace.get("theme"),
            "confidence": _topic_confidence(str(useful.get("judgment", ""))),
        }
    shared_palaces: dict[str, list[str]] = {}
    for topic, row in topic_rows.items():
        palace = str(row.get("palace", ""))
        shared_palaces.setdefault(palace, []).append(topic)
    return {
        "topics": topic_rows,
        "shared_palaces": {palace: topics for palace, topics in shared_palaces.items() if len(topics) > 1},
        "use": "Topic useful gods must be read with palace, direction, door, star, spirit, and judgment together.",
    }


def _pattern_risk_analysis(
    pattern_flags: list[dict[str, str]],
    duty_palace: dict[str, Any],
    useful_analysis: dict[str, Any],
) -> dict[str, Any]:
    cautious_topics = [
        topic
        for topic, row in useful_analysis.get("topics", {}).items()
        if isinstance(row, dict) and row.get("judgment") == "cautious"
    ]
    return {
        "flags": pattern_flags,
        "duty_palace": duty_palace.get("name"),
        "duty_judgment": duty_palace.get("judgment"),
        "cautious_topics": cautious_topics,
        "risk_level": "cautious" if cautious_topics or duty_palace.get("judgment") == "cautious" else "manageable",
        "boundary": "Qi Men pattern flags are planning prompts, not tactical guarantees.",
    }


def _timing_activation_analysis(
    annual_timing: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    birth: dict[str, Any],
) -> dict[str, Any]:
    reference_year = int(birth.get("annual_end_year") or annual_timing[-1].get("year", int(birth["year"])))
    current = next(
        (row for row in annual_timing if int(row.get("year", -1)) == reference_year),
        annual_timing[-1] if annual_timing else {},
    )
    palace = _find_first(rows, "name", str(current.get("palace", ""))) if rows else {}
    return {
        "reference_year": reference_year,
        "current_activation": dict(current),
        "current_palace_detail": {
            "palace": palace.get("name"),
            "direction": palace.get("direction"),
            "element": palace.get("element"),
            "door": palace.get("door"),
            "star": palace.get("star"),
            "spirit": palace.get("spirit"),
            "theme": palace.get("theme"),
        },
        "use": "Annual timing should be read through the activated palace row and topic useful gods.",
    }


def _method_matrix(
    door_star_spirit: dict[str, Any],
    stem_relations: dict[str, Any],
    useful_analysis: dict[str, Any],
    pattern_risk: dict[str, Any],
    timing_activation: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "method": "door_star_spirit",
            "status": "available",
            "evidence_fields": ["palaces", "door_star_spirit_analysis"],
            "summary": f"duty door palace {door_star_spirit.get('duty_door_palace')}",
        },
        {
            "method": "heaven_earth_stem",
            "status": "available",
            "evidence_fields": ["palaces", "stem_relation_analysis"],
            "summary": f"same-stem count {stem_relations.get('same_stem_count', 0)}",
        },
        {
            "method": "useful_god_topic_mapping",
            "status": "available",
            "evidence_fields": ["useful_gods", "useful_god_analysis"],
            "summary": useful_analysis.get("use", ""),
        },
        {
            "method": "pattern_risk",
            "status": "available",
            "evidence_fields": ["pattern_flags", "pattern_risk_analysis"],
            "summary": str(pattern_risk.get("risk_level", "")),
        },
        {
            "method": "annual_timing_activation",
            "status": "available",
            "evidence_fields": ["annual_timing", "timing_activation_analysis"],
            "summary": str(timing_activation.get("use", "")),
        },
    ]


def _combination_role(door: str, star: str, spirit: str) -> str:
    if door in {"Open", "View"}:
        return "visibility and decision"
    if door in {"Life", "Rest"}:
        return "resources and recovery"
    if star in {"Tianfu", "Tianxin"}:
        return "planning and order"
    if spirit in {"White Tiger", "Black Tortoise"}:
        return "risk containment"
    return "adaptive timing"


def _stem_relation(heaven: str, earth: str) -> str:
    if not heaven or not earth:
        return "unknown"
    if heaven == earth:
        return "same"
    heaven_idx = STEMS.index(heaven) if heaven in STEMS else -1
    earth_idx = STEMS.index(earth) if earth in STEMS else -1
    if heaven_idx < 0 or earth_idx < 0:
        return "unknown"
    if (earth_idx - heaven_idx) % len(STEMS) in {1, 2}:
        return "flowing"
    return "friction"


def _stem_relation_risk(heaven: str, earth: str) -> str:
    relation = _stem_relation(heaven, earth)
    if relation == "same":
        return "reinforcing but potentially rigid"
    if relation == "flowing":
        return "movement is easier if roles are clear"
    if relation == "friction":
        return "requires sequencing and verification"
    return "provider verification required"


def _topic_confidence(judgment: str) -> str:
    if judgment in {"constructive", "supportive"}:
        return "stronger_symbolic_support"
    if judgment == "cautious":
        return "requires_risk_control"
    return "mixed_symbolic_support"
