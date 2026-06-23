"""Tests for the optional astrology JSON-CLI provider."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart
from examples.mingli_5agents.tools.astrology_cli_provider import AstrologyJsonCliProvider
from examples.mingli_5agents.tools.astrology_deep_analysis import build_astrology_deep_analysis
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input


def test_astrology_json_cli_provider_maps_ephemeris_payload(tmp_path: Path):
    script = tmp_path / "fake_astrology_provider.py"
    script.write_text(
        """
import json
import sys

payload = json.loads(sys.stdin.read())
planets = [
    {
        "name": name,
        "sign": "Aries",
        "degree": idx + 0.5,
        "absolute_degree": idx * 30 + 0.5,
        "house": idx % 12 + 1,
        "theme": f"verified {name}",
    }
    for idx, name in enumerate(["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"])
]
houses = [
    {"number": idx + 1, "cusp_sign": "Aries", "ruler": "Mars", "theme": f"verified house {idx + 1}", "cusp_degree": idx}
    for idx in range(12)
]
print(json.dumps({
    "protocol": payload.get("protocol"),
    "sun": "Aries",
    "moon": "Aries",
    "ascendant": "Aries",
    "planets": planets,
    "houses": houses,
    "aspects": [{"planet_a": "Sun", "planet_b": "Moon", "aspect": "trine", "orb": 1.0, "theme": "verified"}],
    "annual_transits": [{"year": 2026, "transit_planet": "Jupiter", "activated_house": 10, "focus": "verified transit"}],
    "ephemeris": {
        "source": "verified fixture",
        "zodiac": "tropical",
        "house_system": "Placidus",
        "time_scale": "UT",
        "calculation_time": {"julian_day_ut": 2448000.888889, "iso_utc": "1990-04-12T01:20:00Z"},
        "data_source": "reviewed test fixture",
        "license_or_review": "unit test review"
    }
}))
""".strip(),
        encoding="utf-8",
    )
    birth = normalize_birth_input(
        {
            "name": "Astrology CLI Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    fallback = build_astrology_chart(birth)
    chart = AstrologyJsonCliProvider(command=[sys.executable, str(script)]).build_chart(birth, fallback)
    deep = build_astrology_deep_analysis(chart, birth)

    assert chart["provider_quality"] == "astrology_json_cli"
    assert chart["raw_provider_output"]["ephemeris"]["source"] == "verified fixture"
    assert chart["raw_provider_output"]["ephemeris"]["license_or_review"] == "unit test review"
    assert chart["context"]["domain_provider_source"] == "json_cli"
    assert chart["provider_request_receipt"]["domain"] == "astrology"
    assert chart["provider_request_receipt"]["protocol_echo_matches"] is True
    assert len(chart["provider_request_receipt"]["birth_profile_sha256"]) == 64
    assert len(chart["provider_request_receipt"]["sha256"]) == 64
    assert chart["context"]["provider_request_receipt"]["sha256"] == chart["provider_request_receipt"]["sha256"]
    assert deep["provider_quality"] == "astrology_json_cli"
    assert deep["planets"][0]["theme"] == "verified Sun"
    assert deep["houses"][0]["theme"] == "verified house 1"
    assert deep["aspects"][0]["theme"] == "verified"
    assert deep["annual_transits"][0]["focus"] == "verified transit"
