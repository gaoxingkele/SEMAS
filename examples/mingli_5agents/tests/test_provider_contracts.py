"""Tests for shared provider production-contract checks."""

from __future__ import annotations

from examples.mingli_5agents.provider_contracts import chart_contract, raw_json_cli_contract
from examples.mingli_5agents.tests.test_professional_chart_provider import _external_bazi_payload
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.qimen_deep_analysis import PALACES
from examples.mingli_5agents.tools.ziwei_deep_analysis import PALACE_THEMES


def test_chart_contract_accepts_normalized_external_bazi():
    birth = normalize_birth_input(
        {
            "name": "Contract Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "professional_charts": {"bazi": _external_bazi_payload()},
        }
    )
    chart = build_bazi_chart(birth)

    result = chart_contract("bazi", chart)

    assert result["name"] == "bazi_normalized_production_contract"
    assert result["valid"] is True
    assert result["missing"] == []


def test_chart_contract_rejects_incomplete_bazi_deep_analysis():
    birth = normalize_birth_input(
        {
            "name": "Contract Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "professional_charts": {"bazi": _external_bazi_payload()},
        }
    )
    chart = build_bazi_chart(birth)
    chart["deep_analysis"]["major_luck"] = []

    result = chart_contract("bazi", chart)

    assert result["valid"] is False
    assert "deep_analysis.major_luck[non_empty]" in result["missing"]


def test_chart_contract_rejects_bazi_when_method_surface_drifts():
    birth = normalize_birth_input(
        {
            "name": "Contract Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "professional_charts": {"bazi": _external_bazi_payload()},
        }
    )
    chart = build_bazi_chart(birth)
    chart["deep_analysis"]["method_matrix"] = [
        item
        for item in chart["deep_analysis"]["method_matrix"]
        if item.get("method") not in {"image_symbol_reading", "new_school_simplified"}
    ]

    result = chart_contract("bazi", chart)

    assert result["valid"] is False
    assert "deep_analysis.method_matrix[required_methods]" in result["missing"]


def test_raw_json_cli_contract_accepts_complete_ziwei_payload():
    palaces = [
        {
            "index": index,
            "name": name,
            "theme": PALACE_THEMES[name],
            "primary_stars": ["Ziwei"],
        }
        for index, name in enumerate(PALACE_THEMES)
    ]
    result = raw_json_cli_contract(
        "ziwei",
        {
            "ming_palace": "Ming",
            "body_palace": "Wealth",
            "transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
            "calculation_basis": {
                "provider": "reviewed ziwei engine",
                "rule_set": "reviewed_ziwei_rules",
                "rule_set_version": "1.0",
                "rule_source": "reviewed fixture",
                "rule_source_sha256": "0" * 64,
                "license_or_review": "reviewed fixture",
                "calculation_scope": "twelve palaces, sihua, limits, annual activation",
            },
            "palaces": palaces,
            "major_limits": [{"start_year": 2020, "end_year": 2029, "palace": "Ming"}],
            "annual_activation": [{"year": 2026, "palace": "Ming"}],
        },
    )

    assert result["name"] == "ziwei_json_cli_production_contract"
    assert result["valid"] is True
    assert result["missing"] == []


def test_raw_json_cli_contract_requires_ziwei_qimen_calculation_basis_audit_metadata():
    ziwei_result = raw_json_cli_contract(
        "ziwei",
        {
            "ming_palace": "Ming",
            "body_palace": "Wealth",
            "transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
            "palaces": [
                {"index": index, "name": name, "theme": PALACE_THEMES[name], "primary_stars": ["Ziwei"]}
                for index, name in enumerate(PALACE_THEMES)
            ],
            "major_limits": [{"start_year": 2020, "end_year": 2029, "palace": "Ming"}],
            "annual_activation": [{"year": 2026, "palace": "Ming"}],
            "calculation_basis": {"provider": "opaque ziwei"},
        },
    )
    qimen_result = raw_json_cli_contract(
        "qimen",
        {
            "duty_door": "Open",
            "duty_star": "Tianxin",
            "spirit": "Nine Earth",
            "palaces": [
                {
                    **palace,
                    "door": "Open",
                    "star": "Tianxin",
                    "spirit": "Nine Earth",
                    "heaven_stem": "Jia",
                    "earth_stem": "Yi",
                }
                for palace in PALACES
            ],
            "useful_gods": {
                "career": {"palace": "Kan"},
                "wealth": {"palace": "Kun"},
                "relationship": {"palace": "Zhen"},
                "study": {"palace": "Xun"},
                "health": {"palace": "Li"},
            },
            "annual_timing": [{"year": 2026, "palace": "Kan"}],
            "calculation_basis": {"provider": "opaque qimen"},
        },
    )

    for result in (ziwei_result, qimen_result):
        assert result["valid"] is False
        assert "calculation_basis.rule_set" in result["missing"]
        assert "calculation_basis.rule_set_version" in result["missing"]
        assert "calculation_basis.rule_source" in result["missing"]
        assert "calculation_basis.rule_source_sha256|rule_receipt_sha256" in result["missing"]
        assert "calculation_basis.license_or_review" in result["missing"]
        assert "calculation_basis.calculation_scope" in result["missing"]


def test_chart_contract_rejects_normalized_ziwei_without_method_matrix():
    palaces = [
        {
            "index": index,
            "name": name,
            "theme": PALACE_THEMES[name],
            "primary_stars": ["Ziwei"],
        }
        for index, name in enumerate(PALACE_THEMES)
    ]
    chart = {
        "deep_analysis": {
            "ming_palace": "Ming",
            "body_palace": "Wealth",
            "four_transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
            "palaces": palaces,
            "major_limits": [{"start_year": 2020, "end_year": 2029, "palace": "Ming"}],
            "annual_activation": [{"year": 2026, "palace": "Ming"}],
        }
    }

    result = chart_contract("ziwei", chart)

    assert result["valid"] is False
    assert "method_matrix[non_empty]" in result["missing"]


def test_chart_contract_rejects_normalized_qimen_without_method_matrix():
    palaces = [
        {
            **palace,
            "door": "Open",
            "star": "Tianxin",
            "spirit": "Nine Earth",
            "heaven_stem": "Jia",
            "earth_stem": "Yi",
        }
        for palace in PALACES
    ]
    chart = {
        "deep_analysis": {
            "yin_yang": "yang",
            "ju_number": 1,
            "duty": {
                "door": "Open",
                "door_palace": "Kan",
                "star": "Tianxin",
                "star_palace": "Kan",
                "spirit": "Nine Earth",
            },
            "palaces": palaces,
            "useful_gods": {
                "career": {"palace": "Kan"},
                "wealth": {"palace": "Kun"},
                "relationship": {"palace": "Zhen"},
                "study": {"palace": "Xun"},
                "health": {"palace": "Li"},
            },
            "pattern_flags": [{"name": "stable planning", "palace": "Kan"}],
            "annual_timing": [{"year": 2026, "palace": "Kan"}],
        }
    }

    result = chart_contract("qimen", chart)

    assert result["valid"] is False
    assert "method_matrix[non_empty]" in result["missing"]


def test_raw_json_cli_contract_rejects_partial_astrology_payload():
    result = raw_json_cli_contract(
        "astrology",
        {
            "sun": "Aries",
            "moon": "Taurus",
            "ascendant": "Cancer",
            "planets": [{"name": "Sun"}],
            "houses": [{"number": 1}],
        },
    )

    assert result["valid"] is False
    assert "annual_transits" in result["missing"]
    assert "ephemeris" in result["missing"]
    assert "planets[>=10]" in result["missing"]
    assert "houses[12]" in result["missing"]


def test_raw_json_cli_contract_requires_astrology_ephemeris_audit_metadata():
    planets = [
        {"name": name, "sign": "Aries", "degree": index, "absolute_degree": index * 30, "house": index % 12 + 1}
        for index, name in enumerate(["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"])
    ]
    houses = [
        {"number": index, "cusp_sign": "Aries", "ruler": "Mars", "theme": f"house {index}"}
        for index in range(1, 13)
    ]
    result = raw_json_cli_contract(
        "astrology",
        {
            "sun": "Aries",
            "moon": "Taurus",
            "ascendant": "Cancer",
            "planets": planets,
            "houses": houses,
            "annual_transits": [{"year": 2026, "activated_house": 10}],
            "ephemeris": {"source": "opaque engine", "zodiac": "tropical"},
        },
    )

    assert result["valid"] is False
    assert "ephemeris.house_system" in result["missing"]
    assert "ephemeris.calculation_time" in result["missing"]
    assert "ephemeris.license_or_review" in result["missing"]
    assert "ephemeris.data_source" in result["missing"]


def test_chart_contract_rejects_normalized_astrology_without_method_matrix():
    planets = [
        {"name": name, "sign": "Aries", "degree": index, "house": index % 12 + 1}
        for index, name in enumerate(["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"])
    ]
    houses = [
        {"number": index, "cusp_sign": "Aries", "ruler": "Mars", "theme": f"house {index}"}
        for index in range(1, 13)
    ]
    chart = {
        "deep_analysis": {
            "zodiac": "tropical_ephemeris",
            "planets": planets,
            "houses": houses,
            "annual_transits": [{"year": 2026, "activated_house": 10}],
        }
    }

    result = chart_contract("astrology", chart)

    assert result["valid"] is False
    assert "method_matrix[non_empty]" in result["missing"]


def test_chart_contract_rejects_xuanze_without_method_matrix():
    calendar = {
        "range": {"start_date": "2026-06-21", "end_date": "2026-06-21", "count": 1},
        "basis": {"provider_quality": "verified_tongshu"},
        "rows": [
            {
                "date": "2026-06-21",
                "weekday": "Sunday",
                "ganzhi": "JiaZi",
                "solar_term": "Summer Solstice",
                "twelve_officer": "Open",
                "twenty_eight_mansion": "Well",
                "huangdao": True,
                "rating": "favorable",
                "suitable": ["meeting"],
                "avoid": ["high-stakes decisions"],
                "recommended_hours": [],
                "risk_notes": ["caution"],
            }
        ],
        "summary": {"favorable_dates": ["2026-06-21"], "cautious_dates": [], "best_date": "2026-06-21"},
    }

    result = chart_contract("xuanze", calendar)

    assert result["valid"] is False
    assert "method_matrix[non_empty]" in result["missing"]


def test_raw_json_cli_contract_requires_xuanze_rule_table_audit_metadata():
    result = raw_json_cli_contract(
        "xuanze",
        {
            "basis": {"provider": "opaque_tongshu", "provider_quality": "verified_tongshu"},
            "rows": [
                {
                    "date": "2026-06-21",
                    "weekday": "Sunday",
                    "ganzhi": "JiaZi",
                    "solar_term": "Summer Solstice",
                    "twelve_officer": "Open",
                    "twenty_eight_mansion": "Well",
                    "huangdao": True,
                    "rating": "favorable",
                    "suitable": ["meeting"],
                    "avoid": ["high-stakes decisions"],
                    "recommended_hours": [],
                    "risk_notes": ["caution"],
                }
            ],
            "summary": {"favorable_dates": ["2026-06-21"], "cautious_dates": [], "best_date": "2026-06-21"},
        },
    )

    assert result["valid"] is False
    assert "basis.rule_table_source" in result["missing"]
    assert "basis.rule_table_version" in result["missing"]
    assert "basis.rule_table_sha256|rule_table_receipt_sha256" in result["missing"]
    assert "basis.license_or_review" in result["missing"]
    assert "basis.calculation_scope" in result["missing"]
