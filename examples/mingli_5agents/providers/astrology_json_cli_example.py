"""Example JSON-CLI adapter for a Western astrology provider.

This script is a protocol template. It returns deterministic fixture-like data
so `providers --live` and integration wiring can be tested before connecting a
real ephemeris service.
"""

from __future__ import annotations

import json
import sys


SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    birth = payload.get("birth", {})
    fallback = payload.get("fallback", {})
    protocol = payload.get("protocol", {})
    seed = int(birth.get("year", 1990)) + int(birth.get("month", 1)) * 11 + int(birth.get("day", 1))
    planets = []
    for index, name in enumerate(PLANETS):
        sign = SIGNS[(seed + index) % len(SIGNS)]
        degree = round((seed + index * 17) % 30 + 0.25, 3)
        absolute_degree = SIGNS.index(sign) * 30 + degree
        planets.append(
            {
                "name": name,
                "sign": sign,
                "degree": degree,
                "absolute_degree": absolute_degree,
                "house": index % 12 + 1,
                "theme": f"example ephemeris {name}",
            }
        )
    houses = [
        {
            "number": number,
            "cusp_sign": SIGNS[(number - 1) % len(SIGNS)],
            "ruler": "Mars" if number == 1 else "Venus",
            "theme": f"example house {number}",
            "cusp_degree": number * 2,
        }
        for number in range(1, 13)
    ]
    result = {
        "protocol": {"version": protocol.get("version"), "hash": protocol.get("hash")},
        "sun": fallback.get("sun") or planets[0]["sign"],
        "moon": fallback.get("moon") or planets[1]["sign"],
        "ascendant": fallback.get("ascendant") or houses[0]["cusp_sign"],
        "planets": planets,
        "houses": houses,
        "aspects": [{"planet_a": "Sun", "planet_b": "Moon", "aspect": "trine", "orb": 1.5, "theme": "example aspect"}],
        "annual_transits": [{"year": 2026, "transit_planet": "Jupiter", "activated_house": 10, "focus": "example transit"}],
        "ephemeris": {
            "source": "example_json_cli",
            "zodiac": "tropical",
            "house_system": "Placidus",
            "time_scale": "UT",
            "calculation_time": {
                "julian_day_ut": round(2400000.5 + seed, 6),
                "iso_utc": f"{int(birth.get('year', 1990)):04d}-{int(birth.get('month', 1)):02d}-{int(birth.get('day', 1)):02d}T00:00:00Z",
            },
            "data_source": "example deterministic protocol fixture",
            "license_or_review": "example fixture only; replace with reviewed ephemeris license before production",
        },
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
