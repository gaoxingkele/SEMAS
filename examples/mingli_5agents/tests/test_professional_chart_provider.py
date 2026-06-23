"""Tests for external professional chart provider injection."""

from __future__ import annotations

from pathlib import Path

from examples.mingli_5agents.api_core import analyze_case, status
from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart
from examples.mingli_5agents.tools.astrology_deep_analysis import build_astrology_deep_analysis
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.professional_chart_provider import describe_domain_chart_providers
from examples.mingli_5agents.tools.swiss_ephemeris_provider import SwissEphemerisAstrologyProvider
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart


def _birth_with_external_ziwei() -> dict:
    return {
        "name": "External Provider Case",
        "birth_date": "1990-04-12",
        "birth_time": "09:20",
        "gender": "unspecified",
        "birthplace": "Hangzhou",
        "professional_charts": {
            "ziwei": {
                "source": "fixture_verified_ziwei",
                "version": "fixture-1.0",
                "license_or_review": "reviewed test fixture",
                "ming_palace": "Career",
                "body_palace": "Wealth",
                "major_stars": ["Ziwei", "Wuqu"],
                "transformations": {
                    "lu": "Wuqu",
                    "quan": "Ziwei",
                    "ke": "Tianji",
                    "ji": "Taiyin",
                },
            }
        },
    }


def _external_bazi_payload() -> dict:
    ten_gods = {
        key: {
            "stem": "resource",
            "branch": ["wealth"],
            "hidden_stems": ["Jia"],
            "na_yin": "fixture",
            "growth_stage": "fixture",
            "wu_xing": "WoodFire",
            "xun_kong": "fixture",
        }
        for key in ("year", "month", "day", "hour")
    }
    return {
        "source": "fixture_verified_bazi",
        "version": "fixture-1.0",
        "license_or_review": "reviewed test fixture",
        "pillars": {"year": "GengWu", "month": "GengChen", "day": "DingWei", "hour": "YiSi"},
        "element_counts": {"Wood": 1, "Fire": 3, "Earth": 2, "Metal": 2, "Water": 0},
        "dominant_element": "Fire",
        "useful_element": "Metal",
        "structure": "verified_external",
        "deep_analysis": {
            "provider": "fixture_bazi_engine",
            "day_master": "Ding",
            "ming_gong": "fixture",
            "shen_gong": "fixture",
            "tai_yuan": "fixture",
            "tai_xi": "fixture",
            "ten_gods": ten_gods,
            "luck_start": {"years": 7, "months": 2, "days": 0, "hours": 0, "forward": True},
            "major_luck": [
                {
                    "index": 1,
                    "start_age": 8,
                    "end_age": 17,
                    "start_year": 1998,
                    "end_year": 2007,
                    "ganzhi": "JiaZi",
                    "xun": "fixture",
                    "xun_kong": "fixture",
                    "annual_preview": [],
                }
            ],
            "caution": "fixture verified bazi",
        },
    }


def test_external_bazi_provider_overlays_chart_contract():
    birth = normalize_birth_input(
        {
            "name": "External BaZi Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "professional_charts": {"bazi": _external_bazi_payload()},
        }
    )

    chart = build_bazi_chart(birth)

    assert chart["provider"] == "external_structured"
    assert chart["provider_quality"] == "external_bazi"
    assert chart["context"]["provider"] == "external_structured"
    assert chart["context"]["provider_quality"] == "external_bazi"
    assert chart["context"]["provider_source"] == "fixture_verified_bazi"
    assert chart["context"]["provider_provenance"]["valid"] is True
    assert chart["context"]["external_payload_receipt"]["domain"] == "bazi"
    assert chart["context"]["external_payload_receipt"]["provenance_valid"] is True
    assert len(chart["context"]["external_payload_receipt"]["birth_profile_sha256"]) == 64
    assert len(chart["context"]["external_payload_receipt"]["payload_sha256"]) == 64
    assert len(chart["context"]["external_payload_receipt"]["sha256"]) == 64
    assert chart["structure"] == "verified_external"
    assert chart["deep_analysis"]["provider"] == "fixture_bazi_engine"
    assert chart["deep_analysis"]["day_master"] == "Ding"


def test_external_ziwei_provider_overlays_chart_contract():
    birth = normalize_birth_input(_birth_with_external_ziwei())
    chart = build_ziwei_chart(birth)

    assert chart["ming_palace"] == "Career"
    assert chart["body_palace"] == "Wealth"
    assert chart["provider"] == "external_structured"
    assert chart["provider_quality"] == "external_ziwei"
    assert chart["context"]["domain_provider_source"] == "fixture_verified_ziwei"
    assert chart["context"]["domain_provider_provenance"]["valid"] is True
    assert chart["context"]["external_payload_receipt"]["domain"] == "ziwei"
    assert chart["context"]["external_payload_receipt"]["provenance_valid"] is True
    assert len(chart["context"]["external_payload_receipt"]["sha256"]) == 64
    assert chart["deep_analysis"]["provider_quality"] == "external_ziwei"
    assert len(chart["deep_analysis"]["palaces"]) == 12


def test_analysis_preserves_external_provider_signal(tmp_path: Path):
    result = analyze_case(
        tmp_path / "repo",
        {
            "birth": _birth_with_external_ziwei(),
            "annual_start_year": 2024,
            "annual_end_year": 2024,
            "monthly_years": [2024],
        },
    )

    ziwei = result["result"]["specialists"]["ziwei"]["chart"]
    assert ziwei["provider_quality"] == "external_ziwei"
    assert ziwei["deep_analysis"]["ming_palace"] == "Career"
    assert result["result"]["final_report"]["request_provenance"]["specialist_contexts"]["ziwei"][
        "external_payload_receipt_sha256"
    ] == ziwei["context"]["external_payload_receipt"]["sha256"]
    assert result["metrics"]["report_schema"] == 1.0


def test_analysis_preserves_external_bazi_provider_signal(tmp_path: Path):
    result = analyze_case(
        tmp_path / "repo",
        {
            "birth": {
                "name": "External BaZi Provider Case",
                "birth_date": "1990-04-12",
                "birth_time": "09:20",
                "gender": "unspecified",
                "birthplace": "Hangzhou",
                "professional_charts": {"bazi": _external_bazi_payload()},
            },
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )

    bazi = result["result"]["specialists"]["bazi"]["chart"]
    provider_summary = result["result"]["final_report"]["provider_summary"]
    assert bazi["provider_quality"] == "external_bazi"
    assert bazi["context"]["provider_source"] == "fixture_verified_bazi"
    assert len(bazi["context"]["external_payload_receipt"]["sha256"]) == 64
    assert result["result"]["final_report"]["request_provenance"]["specialist_contexts"]["bazi"][
        "external_payload_receipt_sha256"
    ] == bazi["context"]["external_payload_receipt"]["sha256"]
    assert provider_summary["domains"]["bazi"]["contract_valid"] is True
    assert provider_summary["domains"]["bazi"]["provider_provenance_valid"] is True
    assert provider_summary["domains"]["bazi"]["external_payload_receipt_valid"] is True
    assert provider_summary["domains"]["bazi"]["external_payload_receipt_sha256"] == bazi["context"][
        "external_payload_receipt"
    ]["sha256"]
    assert provider_summary["domains"]["bazi"]["external_payload_birth_match_status"] == "not_declared"
    assert provider_summary["domains"]["bazi"]["external_payload_birth_mismatch_fields"] == []
    assert provider_summary["domains"]["bazi"]["production_ready"] is True
    assert "bazi" not in provider_summary["production_blockers"]
    assert result["metrics"]["report_schema"] == 1.0


def test_external_bazi_with_matching_declared_birth_is_production_ready(tmp_path: Path):
    payload = _external_bazi_payload()
    payload["birth_profile"] = {
        "birth_date": "1990-04-12",
        "birth_time": "09:20",
        "gender": "unspecified",
        "birthplace": "Hangzhou",
        "year": 1990,
        "month": 4,
        "day": 12,
        "hour": 9,
        "minute": 20,
    }

    result = analyze_case(
        tmp_path / "repo",
        {
            "birth": {
                "name": "Matching Declared Birth Case",
                "birth_date": "1990-04-12",
                "birth_time": "09:20",
                "gender": "unspecified",
                "birthplace": "Hangzhou",
                "professional_charts": {"bazi": payload},
            },
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )

    bazi = result["result"]["specialists"]["bazi"]["chart"]
    bazi_status = result["result"]["final_report"]["provider_summary"]["domains"]["bazi"]
    receipt = bazi["context"]["external_payload_receipt"]
    assert receipt["birth_match_status"] == "matched"
    assert receipt["birth_mismatch_fields"] == []
    assert len(receipt["declared_birth_profile_sha256"]) == 64
    assert bazi_status["external_payload_birth_match_status"] == "matched"
    assert bazi_status["external_payload_declared_birth_profile_sha256"] == receipt[
        "declared_birth_profile_sha256"
    ]
    assert bazi_status["production_ready"] is True


def test_external_bazi_declared_birth_mismatch_is_not_production_ready(tmp_path: Path):
    payload = _external_bazi_payload()
    payload["birth_profile"] = {
        "birth_date": "1991-04-12",
        "birth_time": "09:20",
        "gender": "unspecified",
        "birthplace": "Hangzhou",
    }

    result = analyze_case(
        tmp_path / "repo",
        {
            "birth": {
                "name": "Mismatched Declared Birth Case",
                "birth_date": "1990-04-12",
                "birth_time": "09:20",
                "gender": "unspecified",
                "birthplace": "Hangzhou",
                "professional_charts": {"bazi": payload},
            },
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )

    bazi = result["result"]["specialists"]["bazi"]["chart"]
    provider_summary = result["result"]["final_report"]["provider_summary"]
    bazi_status = provider_summary["domains"]["bazi"]
    receipt = bazi["context"]["external_payload_receipt"]
    assert receipt["birth_match_status"] == "mismatch"
    assert receipt["birth_mismatch_fields"] == ["birth_date"]
    assert bazi_status["external_payload_receipt_valid"] is False
    assert bazi_status["external_payload_birth_match_status"] == "mismatch"
    assert bazi_status["external_payload_birth_mismatch_fields"] == ["birth_date"]
    assert bazi_status["production_ready"] is False
    assert bazi_status["interpretation_mode"] == "external_payload_blocked"
    assert bazi_status["confidence_level"] == "blocked"
    assert "external_payload_receipt_invalid" in bazi_status["blocking_reasons"]
    assert "external_payload_birth_mismatch" in bazi_status["blocking_reasons"]
    assert "bazi" in provider_summary["production_blockers"]
    bazi_matrix = next(item for item in provider_summary["readiness_matrix"] if item["domain"] == "bazi")
    assert bazi_matrix["interpretation_mode"] == "external_payload_blocked"
    assert bazi_matrix["confidence_level"] == "blocked"


def test_malformed_external_bazi_payload_is_not_production_ready(tmp_path: Path):
    malformed_payload = _external_bazi_payload()
    malformed_payload["deep_analysis"]["major_luck"] = []

    result = analyze_case(
        tmp_path / "repo",
        {
            "birth": {
                "name": "Malformed External BaZi Provider Case",
                "birth_date": "1990-04-12",
                "birth_time": "09:20",
                "gender": "unspecified",
                "birthplace": "Hangzhou",
                "professional_charts": {"bazi": malformed_payload},
            },
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )

    provider_summary = result["result"]["final_report"]["provider_summary"]
    bazi_status = provider_summary["domains"]["bazi"]
    assert bazi_status["provider_quality"] == "external_bazi"
    assert bazi_status["contract_valid"] is False
    assert bazi_status["production_ready"] is False
    assert "bazi" in provider_summary["production_blockers"]


def test_external_bazi_without_provenance_is_not_production_ready(tmp_path: Path):
    payload = _external_bazi_payload()
    payload.pop("version")
    payload.pop("license_or_review")

    result = analyze_case(
        tmp_path / "repo",
        {
            "birth": {
                "name": "Incomplete External BaZi Provenance Case",
                "birth_date": "1990-04-12",
                "birth_time": "09:20",
                "gender": "unspecified",
                "birthplace": "Hangzhou",
                "professional_charts": {"bazi": payload},
            },
            "annual_start_year": 2026,
            "annual_end_year": 2026,
        },
    )

    bazi_status = result["result"]["final_report"]["provider_summary"]["domains"]["bazi"]
    assert bazi_status["contract_valid"] is True
    assert bazi_status["provider_provenance_valid"] is False
    assert bazi_status["provider_provenance_missing"] == ["version", "license_or_review"]
    assert bazi_status["production_ready"] is False
    bazi = result["result"]["specialists"]["bazi"]["chart"]
    assert bazi["context"]["external_payload_receipt"]["provenance_valid"] is False
    assert len(bazi["context"]["external_payload_receipt"]["sha256"]) == 64
    assert bazi_status["external_payload_receipt_valid"] is False
    assert bazi_status["external_payload_receipt_sha256"] == bazi["context"]["external_payload_receipt"]["sha256"]


def test_analysis_preserves_external_xuanze_provider_signal(tmp_path: Path):
    payload = {
        "birth": {
            "name": "External Xuanze Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "professional_charts": {
                "xuanze": {
                    "source": "fixture_verified_tongshu",
                    "version": "fixture-1.0",
                    "license_or_review": "reviewed test fixture",
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
                            "suitable": ["verified launch"],
                            "avoid": ["verified avoid"],
                            "recommended_hours": [
                                {"start": "09:00", "end": "10:59", "branch": "Si", "element": "Fire"}
                            ],
                            "risk_notes": ["verified caution"],
                        }
                    ],
                    "summary": {
                        "favorable_dates": ["2026-06-21"],
                        "cautious_dates": [],
                        "best_date": "2026-06-21",
                    },
                }
            },
        },
        "annual_start_year": 2026,
        "annual_end_year": 2026,
        "auspicious_start_date": "2026-06-21",
        "auspicious_end_date": "2026-06-21",
    }

    result = analyze_case(tmp_path / "repo", payload)

    calendar = result["result"]["final_report"]["auspicious_calendar"]
    provider_summary = result["result"]["final_report"]["provider_summary"]
    assert calendar["provider_quality"] == "external_xuanze"
    assert calendar["basis"]["provider_source"] == "fixture_verified_tongshu"
    assert calendar["basis"]["provider_provenance"]["valid"] is True
    assert calendar["basis"]["external_payload_receipt"]["domain"] == "xuanze"
    assert calendar["basis"]["external_payload_receipt"]["provenance_valid"] is True
    assert len(calendar["basis"]["external_payload_receipt"]["sha256"]) == 64
    assert result["result"]["final_report"]["request_provenance"]["report_material"][
        "xuanze_external_payload_receipt_sha256"
    ] == calendar["basis"]["external_payload_receipt"]["sha256"]
    assert calendar["rows"][0]["suitable"] == ["verified launch"]
    assert provider_summary["domains"]["xuanze"]["contract_valid"] is True
    assert provider_summary["domains"]["xuanze"]["provider_provenance_valid"] is True
    assert provider_summary["domains"]["xuanze"]["external_payload_receipt_valid"] is True
    assert provider_summary["domains"]["xuanze"]["external_payload_receipt_sha256"] == calendar["basis"][
        "external_payload_receipt"
    ]["sha256"]
    assert provider_summary["domains"]["xuanze"]["production_ready"] is True
    assert "xuanze" not in provider_summary["production_blockers"]
    assert result["metrics"]["report_schema"] == 1.0


def test_domain_provider_diagnostics_are_exposed(tmp_path: Path):
    providers = describe_domain_chart_providers()
    assert providers["ziwei"]["external_injection_supported"] is True
    assert providers["qimen"]["external_injection_supported"] is True
    assert providers["astrology"]["external_injection_supported"] is True

    repo_status = status(tmp_path / "repo")
    assert repo_status["domain_chart_providers"]["ziwei"]["default"] == "symbolic_scaffold"


def test_swiss_ephemeris_provider_maps_planets_into_deep_analysis():
    birth = normalize_birth_input(
        {
            "name": "Swiss Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "timezone_offset": "+08:00",
            "latitude": 30.25,
            "longitude": 120.16,
        }
    )
    fallback = build_astrology_chart(birth)
    chart = SwissEphemerisAstrologyProvider(FakeSwissEphemeris()).build_chart(birth, fallback)
    deep = build_astrology_deep_analysis(chart, birth)

    assert chart["provider_quality"] == "swiss_ephemeris"
    assert chart["sun"] == "Aries"
    assert chart["moon"] == "Taurus"
    assert chart["ascendant"] == "Cancer"
    assert deep["zodiac"] == "tropical_ephemeris"
    assert deep["planets"][0]["absolute_degree"] == 15.0
    assert deep["planets"][1]["sign"] == "Taurus"
    assert len(deep["planets"]) == 10


class FakeSwissEphemeris:
    SUN = 0
    MOON = 1
    MERCURY = 2
    VENUS = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6
    URANUS = 7
    NEPTUNE = 8
    PLUTO = 9

    def julday(self, year: int, month: int, day: int, hour: float) -> float:
        return year * 10000 + month * 100 + day + hour / 24

    def calc_ut(self, jd_ut: float, planet_id: int):
        longitude = 15.0 + planet_id * 30.0
        return ((longitude, 0.0, 0.0, 0.0, 0.0, 0.0), 0)

    def houses(self, jd_ut: float, lat: float, lon: float, house_system: bytes):
        return ([0.0] * 12, [95.0, 0.0, 0.0, 0.0])
