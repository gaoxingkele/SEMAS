"""Structured Zi Wei Dou Shu palace and cycle analysis helpers."""

from __future__ import annotations

from typing import Any


PALACE_THEMES = {
    "Ming": "identity, temperament, core life posture",
    "Siblings": "siblings, peer support, close competitors",
    "Spouse": "marriage, partnership, intimate commitments",
    "Children": "children, students, creativity, juniors",
    "Wealth": "money flow, assets, resource handling",
    "Health": "body rhythm, habits, vulnerability signals",
    "Travel": "movement, relocation, external environment",
    "Friends": "friends, teams, social allies",
    "Career": "profession, office, leadership, public role",
    "Property": "home, real estate, stored resources",
    "Fortune": "inner life, enjoyment, long-term blessing",
    "Parents": "parents, elders, documents, institutions",
}

FOUR_TRANSFORMATION_KEYS = ["lu", "quan", "ke", "ji"]


def build_ziwei_deep_analysis(chart: dict[str, Any], birth: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic Zi Wei structure for palace, major, and annual cycles."""
    palaces = list(chart["palace_order"])
    ming_idx = palaces.index(chart["ming_palace"])
    body_idx = palaces.index(chart["body_palace"])
    seed = int(birth["year"]) + int(birth["month"]) * 3 + int(birth["day"]) * 5 + int(birth["hour"])
    palace_map = _provided_palaces(chart) or [
        _palace_record(index, name, chart, seed, ming_idx, body_idx)
        for index, name in enumerate(palaces)
    ]
    transformation_map = _transformation_map(chart, palace_map)
    major_limits = _provided_rows(chart, "provider_major_limits") or _major_limits(palace_map, birth, ming_idx)
    annual_activation = _provided_rows(chart, "provider_annual_activation") or _annual_activation(palace_map, birth, ming_idx)
    focus = _life_focus(palace_map, chart["ming_palace"], chart["body_palace"])
    triads = _triad_analysis(palace_map, ming_idx, body_idx)
    transformation_analysis = _transformation_analysis(transformation_map, palace_map)
    limit_activation = _limit_activation_analysis(major_limits, annual_activation, birth)
    return {
        "provider": chart.get("provider") or chart["context"].get("domain_provider") or chart["context"].get("provider"),
        "provider_quality": (
            chart.get("provider_quality")
            or chart["context"].get("domain_provider_quality")
            or chart["context"].get("provider_quality")
        ),
        "ming_palace": chart["ming_palace"],
        "body_palace": chart["body_palace"],
        "palaces": palace_map,
        "four_transformations": transformation_map,
        "major_limits": major_limits,
        "annual_activation": annual_activation,
        "life_focus": focus,
        "triad_analysis": triads,
        "transformation_analysis": transformation_analysis,
        "limit_activation_analysis": limit_activation,
        "method_matrix": _method_matrix(focus, triads, transformation_analysis, limit_activation),
        "caution": "Zi Wei rows are structured symbolic scaffolds unless backed by a professional Zi Wei provider.",
    }


def _provided_palaces(chart: dict[str, Any]) -> list[dict[str, Any]]:
    rows = chart.get("provider_palaces")
    if not isinstance(rows, list) or len(rows) != 12:
        return []
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return []
        name = row.get("name")
        if not name:
            return []
        normalized.append(
            {
                "index": int(row.get("index", index)),
                "name": str(name),
                "theme": str(row.get("theme", PALACE_THEMES.get(str(name), "provider supplied palace"))),
                "primary_stars": list(row.get("primary_stars") or row.get("stars") or []),
                "auxiliary_stars": list(row.get("auxiliary_stars") or []),
                "markers": list(row.get("markers") or []),
                "strength": str(row.get("strength", "provider")),
            }
        )
    return normalized


def _provided_rows(chart: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = chart.get(key)
    if not isinstance(rows, list) or not rows:
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _palace_record(
    index: int,
    name: str,
    chart: dict[str, Any],
    seed: int,
    ming_idx: int,
    body_idx: int,
) -> dict[str, Any]:
    stars = chart["star_cycle"]
    primary = stars[(seed + index * 2) % len(stars)]
    secondary = stars[(seed + index * 2 + 5) % len(stars)]
    markers = []
    if index == ming_idx:
        markers.append("ming")
    if index == body_idx:
        markers.append("body")
    return {
        "index": index,
        "name": name,
        "theme": PALACE_THEMES[name],
        "primary_stars": [primary, secondary],
        "auxiliary_stars": [stars[(seed + index + 1) % len(stars)]],
        "markers": markers,
        "strength": _strength(seed, index, markers),
    }


def _transformation_map(chart: dict[str, Any], palaces: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    transformations = chart["transformations"]
    result = {}
    for offset, key in enumerate(FOUR_TRANSFORMATION_KEYS):
        star = transformations.get(key) or chart["star_cycle"][offset]
        palace = palaces[(chart["star_cycle"].index(star) + offset) % len(palaces)]
        result[key] = {
            "star": star,
            "palace": palace["name"],
            "theme": palace["theme"],
        }
    return result


def _major_limits(
    palaces: list[dict[str, Any]],
    birth: dict[str, Any],
    ming_idx: int,
) -> list[dict[str, Any]]:
    birth_year = int(birth["year"])
    return [
        {
            "index": idx,
            "start_age": idx * 10 + 1,
            "end_age": idx * 10 + 10,
            "start_year": birth_year + idx * 10,
            "end_year": birth_year + idx * 10 + 9,
            "palace": palaces[(ming_idx + idx) % len(palaces)]["name"],
            "theme": palaces[(ming_idx + idx) % len(palaces)]["theme"],
        }
        for idx in range(0, 12)
    ]


def _annual_activation(
    palaces: list[dict[str, Any]],
    birth: dict[str, Any],
    ming_idx: int,
) -> list[dict[str, Any]]:
    birth_year = int(birth["year"])
    end_year = birth.get("annual_end_year")
    if end_year is None:
        end_year = birth_year + 60
    start_year = int(birth.get("annual_start_year", birth_year))
    end = min(int(end_year), start_year + 60)
    return [
        {
            "year": year,
            "age": year - birth_year,
            "palace": palaces[(ming_idx + year - birth_year) % len(palaces)]["name"],
            "theme": palaces[(ming_idx + year - birth_year) % len(palaces)]["theme"],
        }
        for year in range(start_year, end + 1)
    ]


def _strength(seed: int, index: int, markers: list[str]) -> str:
    if "ming" in markers or "body" in markers:
        return "primary"
    return ["supporting", "variable", "latent"][(seed + index) % 3]


def _life_focus(palaces: list[dict[str, Any]], ming_palace: str, body_palace: str) -> dict[str, Any]:
    ming = _palace_by_name(palaces, ming_palace)
    body = _palace_by_name(palaces, body_palace)
    return {
        "ming_palace": ming_palace,
        "ming_theme": ming.get("theme", ""),
        "ming_stars": list(ming.get("primary_stars", [])),
        "body_palace": body_palace,
        "body_theme": body.get("theme", ""),
        "body_stars": list(body.get("primary_stars", [])),
        "focus": f"{ming_palace} identity frame with {body_palace} embodied-priority frame",
    }


def _triad_analysis(palaces: list[dict[str, Any]], ming_idx: int, body_idx: int) -> dict[str, Any]:
    return {
        "ming_triad": _triad_record(palaces, ming_idx),
        "body_triad": _triad_record(palaces, body_idx),
        "opposition": {
            "ming_opposite": palaces[(ming_idx + 6) % len(palaces)]["name"],
            "body_opposite": palaces[(body_idx + 6) % len(palaces)]["name"],
            "use": "Compare core palace, opposite palace, and trine palaces before making topic claims.",
        },
    }


def _triad_record(palaces: list[dict[str, Any]], index: int) -> dict[str, Any]:
    triad_indexes = [index, (index + 4) % len(palaces), (index + 8) % len(palaces)]
    rows = [palaces[item] for item in triad_indexes]
    return {
        "palaces": [row["name"] for row in rows],
        "themes": [row.get("theme", "") for row in rows],
        "primary_stars": [star for row in rows for star in row.get("primary_stars", [])],
        "strengths": [row.get("strength", "") for row in rows],
    }


def _transformation_analysis(
    transformations: dict[str, dict[str, str]],
    palaces: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for key in FOUR_TRANSFORMATION_KEYS:
        item = transformations.get(key, {})
        palace = _palace_by_name(palaces, str(item.get("palace", "")))
        rows.append(
            {
                "type": key,
                "star": item.get("star", ""),
                "palace": item.get("palace", ""),
                "theme": item.get("theme") or palace.get("theme", ""),
                "interpretive_role": _transformation_role(key),
            }
        )
    return {
        "rows": rows,
        "priority_order": FOUR_TRANSFORMATION_KEYS,
        "use": "Read Lu/Quan/Ke/Ji as movement labels and preserve Ji as friction, not certainty.",
    }


def _limit_activation_analysis(
    major_limits: list[dict[str, Any]],
    annual_activation: list[dict[str, Any]],
    birth: dict[str, Any],
) -> dict[str, Any]:
    end_year = int(birth.get("annual_end_year") or annual_activation[-1].get("year", int(birth["year"])))
    current_limit = next(
        (
            row
            for row in major_limits
            if int(row.get("start_year", 0)) <= end_year <= int(row.get("end_year", 0))
        ),
        major_limits[0] if major_limits else {},
    )
    current_annual = next(
        (row for row in annual_activation if int(row.get("year", -1)) == end_year),
        annual_activation[-1] if annual_activation else {},
    )
    return {
        "reference_year": end_year,
        "current_major_limit": dict(current_limit),
        "current_annual_activation": dict(current_annual),
        "linked_palace": current_annual.get("palace") or current_limit.get("palace"),
        "use": "Annual palace should be interpreted inside the active major-limit context.",
    }


def _method_matrix(
    focus: dict[str, Any],
    triads: dict[str, Any],
    transformations: dict[str, Any],
    limit_activation: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "method": "ming_body_axis",
            "status": "available",
            "evidence_fields": ["life_focus"],
            "summary": str(focus.get("focus", "")),
        },
        {
            "method": "twelve_palace_theme",
            "status": "available",
            "evidence_fields": ["palaces"],
            "summary": "twelve palace rows carry topic themes, markers, stars, and strength labels",
        },
        {
            "method": "triad_opposition",
            "status": "available",
            "evidence_fields": ["triad_analysis"],
            "summary": ", ".join(triads.get("ming_triad", {}).get("palaces", [])),
        },
        {
            "method": "four_transformations",
            "status": "available",
            "evidence_fields": ["four_transformations", "transformation_analysis"],
            "summary": transformations.get("use", ""),
        },
        {
            "method": "limit_annual_linkage",
            "status": "available",
            "evidence_fields": ["major_limits", "annual_activation", "limit_activation_analysis"],
            "summary": str(limit_activation.get("use", "")),
        },
    ]


def _palace_by_name(palaces: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next((row for row in palaces if row.get("name") == name), {})


def _transformation_role(key: str) -> str:
    return {
        "lu": "gain, resource, attraction",
        "quan": "authority, action, pressure",
        "ke": "reputation, study, mediation",
        "ji": "friction, blockage, caution",
    }.get(key, "movement label")
