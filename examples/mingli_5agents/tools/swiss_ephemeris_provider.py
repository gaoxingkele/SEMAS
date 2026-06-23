"""Optional Swiss Ephemeris provider for Western astrology charts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PLANET_IDS = {
    "Sun": "SUN",
    "Moon": "MOON",
    "Mercury": "MERCURY",
    "Venus": "VENUS",
    "Mars": "MARS",
    "Jupiter": "JUPITER",
    "Saturn": "SATURN",
    "Uranus": "URANUS",
    "Neptune": "NEPTUNE",
    "Pluto": "PLUTO",
}

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


@dataclass
class SwissEphemerisAstrologyProvider:
    """Astrology provider backed by the optional `pyswisseph` package."""

    swe: Any
    domain: str = "astrology"
    name: str = "swiss_ephemeris"

    def build_chart(self, birth: dict[str, Any], fallback_chart: dict[str, Any]) -> dict[str, Any]:
        """Return an ephemeris-backed chart while preserving the existing schema."""
        jd_ut = self.swe.julday(
            int(birth["year"]),
            int(birth["month"]),
            int(birth["day"]),
            _utc_hour(birth),
        )
        planet_rows = [_planet_row(self.swe, jd_ut, name) for name in PLANET_IDS]
        ascendant = _ascendant(self.swe, jd_ut, birth, fallback_chart)
        chart = {
            **fallback_chart,
            "provider": self.name,
            "provider_quality": "swiss_ephemeris",
            "sun": planet_rows[0]["sign"],
            "moon": planet_rows[1]["sign"],
            "ascendant": ascendant,
            "ephemeris_planets": planet_rows,
            "ephemeris": {
                "backend": "pyswisseph",
                "source": "pyswisseph",
                "zodiac": "tropical",
                "house_system": birth.get("house_system", "P"),
                "time_scale": "UT",
                "calculation_time": {
                    "julian_day_ut": jd_ut,
                },
                "julian_day_ut": jd_ut,
                "timezone_offset_hours": _timezone_offset(birth),
                "coordinates": _coordinates(birth),
                "data_source": "Swiss Ephemeris data available to the installed pyswisseph runtime",
                "license_or_review": "Operator must review pyswisseph and Swiss Ephemeris license/data terms before production use.",
            },
        }
        chart.setdefault("context", {}).setdefault("provider", fallback_chart.get("context", {}).get("provider"))
        chart["context"]["domain_provider"] = self.name
        chart["context"]["domain_provider_quality"] = "swiss_ephemeris"
        chart["context"]["domain_provider_source"] = "pyswisseph"
        return chart


def try_build_swiss_ephemeris_provider() -> SwissEphemerisAstrologyProvider | None:
    """Return a Swiss Ephemeris provider when `swisseph` is importable."""
    try:
        import swisseph as swe  # type: ignore
    except Exception:
        return None
    return SwissEphemerisAstrologyProvider(swe=swe)


def _planet_row(swe: Any, jd_ut: float, name: str) -> dict[str, Any]:
    constant = getattr(swe, PLANET_IDS[name])
    calc_result = swe.calc_ut(jd_ut, constant)
    values = calc_result[0] if isinstance(calc_result, tuple) else calc_result
    longitude = float(values[0]) % 360
    sign_index = int(longitude // 30)
    return {
        "name": name,
        "sign": SIGNS[sign_index],
        "degree": round(longitude % 30, 6),
        "absolute_degree": round(longitude, 6),
        "house": sign_index + 1,
        "theme": f"{name} ephemeris longitude {round(longitude, 3)} degrees",
        "longitude": round(longitude, 6),
    }


def _ascendant(swe: Any, jd_ut: float, birth: dict[str, Any], fallback_chart: dict[str, Any]) -> str:
    coords = _coordinates(birth)
    if coords is None:
        return fallback_chart["ascendant"]
    lat, lon = coords
    house_system = str(birth.get("house_system", "P")).encode("ascii", errors="ignore") or b"P"
    try:
        houses_result = swe.houses(jd_ut, lat, lon, house_system)
    except Exception:
        return fallback_chart["ascendant"]
    ascmc = houses_result[1] if isinstance(houses_result, tuple) and len(houses_result) > 1 else []
    if len(ascmc) < 1:
        return fallback_chart["ascendant"]
    return SIGNS[int((float(ascmc[0]) % 360) // 30)]


def _coordinates(birth: dict[str, Any]) -> tuple[float, float] | None:
    lat = birth.get("latitude", birth.get("lat"))
    lon = birth.get("longitude", birth.get("lon"))
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def _utc_hour(birth: dict[str, Any]) -> float:
    return int(birth["hour"]) + int(birth.get("minute", 0)) / 60 - _timezone_offset(birth)


def _timezone_offset(birth: dict[str, Any]) -> float:
    value = birth.get("timezone_offset", birth.get("utc_offset", 0))
    if isinstance(value, str):
        sign = -1 if value.startswith("-") else 1
        cleaned = value.lstrip("+-")
        if ":" in cleaned:
            hours, minutes = cleaned.split(":", 1)
            return sign * (int(hours) + int(minutes) / 60)
        return float(value)
    return float(value)
