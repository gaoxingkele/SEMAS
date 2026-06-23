"""Structured Western astrology natal and transit analysis helpers."""

from __future__ import annotations

from typing import Any


PLANETS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]
ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}
HOUSE_THEMES = {
    1: "identity and vitality",
    2: "money, values, possessions",
    3: "learning, siblings, communication",
    4: "home, roots, family",
    5: "romance, children, creativity",
    6: "work habits, health routines",
    7: "partnership and contracts",
    8: "shared resources, transformation",
    9: "higher learning, travel, worldview",
    10: "career, status, authority",
    11: "friends, groups, long-term hopes",
    12: "rest, hidden matters, spiritual digestion",
}


def build_astrology_deep_analysis(chart: dict[str, Any], birth: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic natal planet, house, aspect, and transit structures."""
    seed = int(birth["year"]) * 7 + int(birth["month"]) * 13 + int(birth["day"]) * 3 + int(birth["hour"])
    planets = _provided_planets(chart) or [_planet_row(index, name, chart, seed) for index, name in enumerate(PLANETS)]
    houses = _provided_houses(chart) or [_house_row(index + 1, chart, seed) for index in range(12)]
    aspects = _provided_rows(chart, "provider_aspects") or _aspects(planets)
    annual_transits = _provided_rows(chart, "provider_annual_transits") or _annual_transits(planets, houses, birth, seed)
    provider_quality = (
        chart.get("provider_quality")
        or chart["context"].get("domain_provider_quality")
        or chart["context"].get("provider_quality")
    )
    ephemeris_quality = _ephemeris_quality(provider_quality)
    core_identity = _core_identity_analysis(chart, planets)
    house_emphasis = _house_emphasis_analysis(planets, houses)
    aspect_patterns = _aspect_pattern_analysis(aspects)
    transit_activation = _transit_activation_analysis(annual_transits, houses, birth)
    return {
        "provider": chart.get("provider") or chart["context"].get("domain_provider") or chart["context"].get("provider"),
        "provider_quality": provider_quality,
        "zodiac": "tropical_ephemeris" if provider_quality == "swiss_ephemeris" else "tropical_symbolic",
        "planets": planets,
        "houses": houses,
        "aspects": aspects,
        "annual_transits": annual_transits,
        "ephemeris_quality": ephemeris_quality,
        "core_identity_analysis": core_identity,
        "house_emphasis_analysis": house_emphasis,
        "aspect_pattern_analysis": aspect_patterns,
        "transit_activation_analysis": transit_activation,
        "method_matrix": _method_matrix(
            ephemeris_quality,
            core_identity,
            house_emphasis,
            aspect_patterns,
            transit_activation,
        ),
        "caution": "Astrology rows are symbolic offline calculations unless backed by an astronomical ephemeris.",
    }


def _provided_planets(chart: dict[str, Any]) -> list[dict[str, Any]]:
    rows = chart.get("ephemeris_planets")
    if not isinstance(rows, list) or len(rows) < 10:
        return []
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or not {"name", "sign", "degree", "absolute_degree", "house"}.issubset(row):
            return []
        normalized.append(
            {
                **row,
                "theme": row.get("theme") or _planet_theme(str(row["name"]), int(row["house"])),
            }
        )
    return normalized


def _provided_houses(chart: dict[str, Any]) -> list[dict[str, Any]]:
    rows = chart.get("provider_houses")
    if not isinstance(rows, list) or len(rows) != 12:
        return []
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or not {"number", "cusp_sign", "ruler", "theme"}.issubset(row):
            return []
        normalized.append(dict(row))
    return normalized


def _provided_rows(chart: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = chart.get(key)
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _planet_row(index: int, name: str, chart: dict[str, Any], seed: int) -> dict[str, Any]:
    signs = chart["sign_cycle"]
    if name == "Sun":
        sign = chart["sun"]
    elif name == "Moon":
        sign = chart["moon"]
    else:
        sign = signs[(seed + index * 2) % len(signs)]
    sign_index = signs.index(sign)
    degree = (seed + index * 37) % 30
    absolute_degree = sign_index * 30 + degree
    house = absolute_degree // 30 % 12 + 1
    return {
        "name": name,
        "sign": sign,
        "degree": degree,
        "absolute_degree": absolute_degree,
        "house": house,
        "theme": _planet_theme(name, house),
    }


def _house_row(number: int, chart: dict[str, Any], seed: int) -> dict[str, Any]:
    signs = chart["sign_cycle"]
    asc_idx = signs.index(chart["ascendant"])
    cusp_sign = signs[(asc_idx + number - 1) % len(signs)]
    ruler = _ruler_for(cusp_sign)
    return {
        "number": number,
        "cusp_sign": cusp_sign,
        "ruler": ruler,
        "theme": HOUSE_THEMES[number],
        "emphasis": ["angular", "succedent", "cadent"][(number - 1) % 3],
        "cusp_degree": (seed + number * 5) % 30,
    }


def _aspects(planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for left_idx, left in enumerate(planets):
        for right in planets[left_idx + 1:]:
            diff = abs(left["absolute_degree"] - right["absolute_degree"]) % 360
            diff = min(diff, 360 - diff)
            for aspect, angle in ASPECTS.items():
                orb = abs(diff - angle)
                if orb <= 6:
                    rows.append(
                        {
                            "planet_a": left["name"],
                            "planet_b": right["name"],
                            "aspect": aspect,
                            "orb": round(orb, 2),
                            "theme": _aspect_theme(aspect),
                        }
                    )
                    break
    return rows[:12]


def _annual_transits(
    natal_planets: list[dict[str, Any]],
    houses: list[dict[str, Any]],
    birth: dict[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    birth_year = int(birth["year"])
    start = int(birth.get("annual_start_year", birth_year))
    end = int(birth.get("annual_end_year", min(start + 2, birth_year + 60)))
    rows = []
    for year in range(start, end + 1):
        transit_planet = PLANETS[(seed + year - birth_year) % len(PLANETS)]
        activated_house = houses[(year - birth_year) % len(houses)]
        natal_target = natal_planets[(year + seed) % len(natal_planets)]
        rows.append(
            {
                "year": year,
                "age": year - birth_year,
                "transit_planet": transit_planet,
                "target_natal_planet": natal_target["name"],
                "activated_house": activated_house["number"],
                "house_theme": activated_house["theme"],
                "focus": _transit_focus(transit_planet, activated_house["number"]),
            }
        )
    return rows


def _planet_theme(planet: str, house: int) -> str:
    base = {
        "Sun": "identity and life direction",
        "Moon": "emotion and habit",
        "Mercury": "thinking and communication",
        "Venus": "relationship and values",
        "Mars": "drive and conflict style",
        "Jupiter": "growth and confidence",
        "Saturn": "discipline and boundaries",
        "Uranus": "change and independence",
        "Neptune": "imagination and ambiguity",
        "Pluto": "depth and transformation",
    }[planet]
    return f"{base} through house {house}"


def _ruler_for(sign: str) -> str:
    return {
        "Aries": "Mars",
        "Taurus": "Venus",
        "Gemini": "Mercury",
        "Cancer": "Moon",
        "Leo": "Sun",
        "Virgo": "Mercury",
        "Libra": "Venus",
        "Scorpio": "Mars",
        "Sagittarius": "Jupiter",
        "Capricorn": "Saturn",
        "Aquarius": "Saturn",
        "Pisces": "Jupiter",
    }[sign]


def _aspect_theme(aspect: str) -> str:
    return {
        "conjunction": "fusion and concentration",
        "sextile": "cooperative opportunity",
        "square": "friction requiring action",
        "trine": "ease and flow",
        "opposition": "polarity and relationship mirror",
    }[aspect]


def _transit_focus(planet: str, house: int) -> str:
    if planet in {"Jupiter", "Venus"}:
        tone = "growth or ease"
    elif planet in {"Saturn", "Mars"}:
        tone = "pressure, discipline, or action"
    else:
        tone = "reflection, change, or integration"
    return f"{tone} in {HOUSE_THEMES[house]}"


def _ephemeris_quality(provider_quality: object) -> dict[str, Any]:
    quality = str(provider_quality or "")
    backed = quality in {"swiss_ephemeris", "astrology_json_cli", "external_astrology"}
    return {
        "provider_quality": quality,
        "ephemeris_backed": backed,
        "precision_level": "astronomical_or_external" if backed else "symbolic_scaffold",
        "boundary": "Use astronomical ephemeris or verified external provider for production-grade degrees.",
    }


def _core_identity_analysis(chart: dict[str, Any], planets: list[dict[str, Any]]) -> dict[str, Any]:
    lookup = {row.get("name"): row for row in planets}
    sun = lookup.get("Sun", {})
    moon = lookup.get("Moon", {})
    return {
        "sun": {"sign": chart.get("sun") or sun.get("sign"), "house": sun.get("house"), "theme": sun.get("theme")},
        "moon": {"sign": chart.get("moon") or moon.get("sign"), "house": moon.get("house"), "theme": moon.get("theme")},
        "ascendant": {"sign": chart.get("ascendant"), "theme": "presentation, body rhythm, first response"},
        "synthesis": f"Sun {chart.get('sun')} / Moon {chart.get('moon')} / Ascendant {chart.get('ascendant')}",
    }


def _house_emphasis_analysis(planets: list[dict[str, Any]], houses: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[int, int] = {}
    for planet in planets:
        house = int(planet.get("house", 0) or 0)
        if house:
            counts[house] = counts.get(house, 0) + 1
    emphasized = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    house_lookup = {int(row.get("number", 0)): row for row in houses}
    return {
        "planet_counts_by_house": {str(key): value for key, value in sorted(counts.items())},
        "emphasized_houses": [
            {
                "house": house,
                "planet_count": count,
                "theme": house_lookup.get(house, {}).get("theme", HOUSE_THEMES.get(house, "")),
            }
            for house, count in emphasized
        ],
        "angular_planet_count": sum(1 for planet in planets if int(planet.get("house", 0) or 0) in {1, 4, 7, 10}),
    }


def _aspect_pattern_analysis(aspects: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    tight = []
    for aspect in aspects:
        name = str(aspect.get("aspect", "unknown"))
        counts[name] = counts.get(name, 0) + 1
        try:
            orb = float(aspect.get("orb", 99))
        except (TypeError, ValueError):
            orb = 99
        if orb <= 2:
            tight.append(dict(aspect))
    return {
        "aspect_counts": counts,
        "tight_aspects": tight,
        "dominant_pattern": max(counts, key=counts.get) if counts else "none",
        "use": "Aspects are interpretive relationships and should be weighted by orb and planet relevance.",
    }


def _transit_activation_analysis(
    annual_transits: list[dict[str, Any]],
    houses: list[dict[str, Any]],
    birth: dict[str, Any],
) -> dict[str, Any]:
    reference_year = int(birth.get("annual_end_year") or annual_transits[-1].get("year", int(birth["year"])))
    current = next(
        (row for row in annual_transits if int(row.get("year", -1)) == reference_year),
        annual_transits[-1] if annual_transits else {},
    )
    house_number = int(current.get("activated_house", 0) or 0)
    house = next((row for row in houses if int(row.get("number", 0)) == house_number), {})
    return {
        "reference_year": reference_year,
        "current_transit": dict(current),
        "activated_house_detail": {
            "house": house_number,
            "theme": house.get("theme") or HOUSE_THEMES.get(house_number, ""),
            "cusp_sign": house.get("cusp_sign"),
            "ruler": house.get("ruler"),
        },
        "use": "Annual transit rows are timing prompts and need ephemeris-backed degrees for production precision.",
    }


def _method_matrix(
    ephemeris_quality: dict[str, Any],
    core_identity: dict[str, Any],
    house_emphasis: dict[str, Any],
    aspect_patterns: dict[str, Any],
    transit_activation: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "method": "ephemeris_quality",
            "status": "available",
            "evidence_fields": ["provider_quality", "ephemeris_quality"],
            "summary": str(ephemeris_quality.get("precision_level", "")),
        },
        {
            "method": "sun_moon_ascendant",
            "status": "available",
            "evidence_fields": ["core_identity_analysis"],
            "summary": str(core_identity.get("synthesis", "")),
        },
        {
            "method": "house_emphasis",
            "status": "available",
            "evidence_fields": ["planets", "houses", "house_emphasis_analysis"],
            "summary": f"angular planets {house_emphasis.get('angular_planet_count', 0)}",
        },
        {
            "method": "aspect_pattern",
            "status": "available",
            "evidence_fields": ["aspects", "aspect_pattern_analysis"],
            "summary": str(aspect_patterns.get("dominant_pattern", "")),
        },
        {
            "method": "transit_activation",
            "status": "available",
            "evidence_fields": ["annual_transits", "transit_activation_analysis"],
            "summary": str(transit_activation.get("use", "")),
        },
    ]
