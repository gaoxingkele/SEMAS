"""Tests for shared calendar context and specialist chart tools."""

from __future__ import annotations

from datetime import date

from examples.mingli_5agents.tools.annual_luck import build_annual_luck
from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart, sun_sign
from examples.mingli_5agents.tools.auspicious_calendar import build_auspicious_calendar
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.calendar_core import (
    build_chart_context,
    day_ganzhi,
    get_calendar_provider,
    hour_branch,
    register_calendar_provider,
    year_ganzhi,
)
from examples.mingli_5agents.tools.calendar_provider import ExternalCalendarProvider
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.monthly_luck import build_monthly_luck
from examples.mingli_5agents.tools.qimen_ju import build_qimen_chart
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart


def test_ganzhi_anchor_and_hour_branch():
    assert year_ganzhi(1984) == "JiaZi"
    assert day_ganzhi(date(1984, 2, 2)) == "JiaZi"
    assert hour_branch(23) == "Zi"
    assert hour_branch(1) == "Chou"


def test_chart_context_contains_shared_fields():
    birth = normalize_birth_input(
        {
            "name": "Context Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birth_place": "Hangzhou",
        }
    )
    assert birth["birthplace"] == "Hangzhou"
    assert birth["birthplace_normalized"] == "Hangzhou, Zhejiang, China"
    assert birth["birthplace_region"] == "China/Zhejiang/Hangzhou"
    assert birth["timezone_offset"] == "+08:00"
    assert birth["geocoding_provider"] == "offline_city_index_v1"
    assert birth["geocoding_quality"] == "city_centroid"
    context = build_chart_context(birth)
    assert set(context["pillars"]) == {"year", "month", "day", "hour"}
    assert sum(context["element_counts"].values()) == 8
    assert context["solar_term"] == "Clear and Bright"
    assert context["hour_branch"] == "Si"
    assert context["provider"] in {"auto", "professional"}
    assert context["provider_quality"] in {
        "professional_unavailable_fallback",
        "lunar_python",
        "sxtwl",
    }
    backend = get_calendar_provider("professional").available_backend()
    if backend:
        assert context["provider"] == "professional"
        assert context["provider_quality"] == backend
    else:
        assert context["provider"] == "auto"
        assert context["provider_quality"] == "professional_unavailable_fallback"
    assert birth["minute"] == 20
    assert context["birthplace_normalized"] == "Hangzhou, Zhejiang, China"
    assert context["timezone_offset"] == "+08:00"


def test_birthplace_geo_normalizes_chinese_alias_and_preserves_explicit_coordinates():
    birth = normalize_birth_input(
        {
            "name": "Geo Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "\u798f\u5efa\u7701\u4e09\u660e\u5e02",
            "latitude": 26.2,
            "longitude": 117.6,
            "timezone_offset": "+08:00",
        }
    )
    assert birth["birthplace_normalized"] == "Sanming, Fujian, China"
    assert birth["birthplace_region"] == "China/Fujian/Sanming"
    assert birth["latitude"] == 26.2
    assert birth["longitude"] == 117.6
    assert birth["timezone_offset"] == "+08:00"


def test_birthplace_geo_marks_unknown_location_as_user_input_only():
    birth = normalize_birth_input(
        {
            "name": "Unknown Geo Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Unmapped Place",
        }
    )
    assert birth["birthplace_normalized"] == "Unmapped Place"
    assert birth["birthplace_region"] == "unknown"
    assert birth["geocoding_provider"] == "user_input_only"
    assert birth["geocoding_quality"] == "unresolved"


def test_explicit_approximate_calendar_provider_remains_available():
    birth = normalize_birth_input(
        {
            "name": "Approximate Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "calendar_provider": "approximate",
        }
    )
    context = build_chart_context(birth)
    assert context["provider"] == "approximate"
    assert context["provider_quality"] == "offline_approximation"


def test_auto_calendar_provider_uses_professional_or_fallback_backend():
    birth = normalize_birth_input(
        {
            "name": "Auto Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "calendar_provider": "auto",
        }
    )
    context = build_chart_context(birth)
    assert context["provider"] in {"auto", "professional"}
    assert context["provider_quality"] in {
        "professional_unavailable_fallback",
        "lunar_python",
        "sxtwl",
    }
    assert set(context["pillars"]) == {"year", "month", "day", "hour"}


def test_professional_calendar_provider_reports_missing_dependency():
    provider = get_calendar_provider("professional")
    if provider.available_backend():
        return
    birth = normalize_birth_input(
        {
            "name": "Professional Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    try:
        build_chart_context(birth, provider_name="professional")
    except ImportError as exc:
        assert "No professional calendar provider installed" in str(exc)
    else:
        raise AssertionError("professional provider should require an optional backend")


def test_specialist_tools_share_context():
    birth = normalize_birth_input(
        {
            "name": "Shared Context Case",
            "birth_date": "1988-11-03",
            "birth_time": "21:10",
            "gender": "unspecified",
            "birthplace": "Chengdu",
        }
    )
    bazi = build_bazi_chart(birth)
    ziwei = build_ziwei_chart(birth)
    qimen = build_qimen_chart(birth)
    astrology = build_astrology_chart(birth)
    shared_pillars = bazi["context"]["pillars"]
    assert ziwei["context"]["pillars"] == shared_pillars
    assert qimen["context"]["pillars"] == shared_pillars
    assert astrology["context"]["pillars"] == shared_pillars
    assert len(ziwei["deep_analysis"]["palaces"]) == 12
    assert set(ziwei["deep_analysis"]["four_transformations"]) == {"lu", "quan", "ke", "ji"}
    assert ziwei["deep_analysis"]["major_limits"]
    assert bazi["sources"] == ["bazi_ziping", "bazi_sanming", "bazi_shensha"]
    assert set(bazi["deep_analysis"]["ten_gods"]) == {"year", "month", "day", "hour"}
    assert bazi["deep_analysis"]["major_luck"]
    assert len(qimen["deep_analysis"]["palaces"]) == 9
    assert {"career", "wealth", "relationship", "study", "health"}.issubset(qimen["deep_analysis"]["useful_gods"])
    assert len(astrology["deep_analysis"]["planets"]) == 10
    assert len(astrology["deep_analysis"]["houses"]) == 12
    assert "qimen_plate" in qimen["sources"]


def test_ziwei_deep_analysis_builds_palaces_limits_and_annual_activation():
    birth = normalize_birth_input(
        {
            "name": "Zi Wei Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
            "annual_start_year": 2024,
            "annual_end_year": 2026,
        }
    )
    ziwei = build_ziwei_chart(birth)
    deep = ziwei["deep_analysis"]

    assert len(deep["palaces"]) == 12
    assert deep["palaces"][0]["name"] == "Ming"
    assert len(deep["major_limits"]) == 12
    assert deep["major_limits"][0]["start_age"] == 1
    assert [row["year"] for row in deep["annual_activation"]] == [2024, 2025, 2026]
    assert all(row["palace"] for row in deep["annual_activation"])
    assert deep["life_focus"]["ming_palace"] == ziwei["ming_palace"]
    assert deep["triad_analysis"]["ming_triad"]["palaces"]
    assert len(deep["transformation_analysis"]["rows"]) == 4
    assert deep["limit_activation_analysis"]["reference_year"] == 2026
    assert {item["method"] for item in deep["method_matrix"]} == {
        "ming_body_axis",
        "twelve_palace_theme",
        "triad_opposition",
        "four_transformations",
        "limit_annual_linkage",
    }


def test_qimen_deep_analysis_builds_nine_palace_plate():
    birth = normalize_birth_input(
        {
            "name": "Qi Men Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
            "annual_start_year": 2024,
            "annual_end_year": 2026,
        }
    )
    qimen = build_qimen_chart(birth)
    deep = qimen["deep_analysis"]

    assert len(deep["palaces"]) == 9
    assert {row["number"] for row in deep["palaces"]} == set(range(1, 10))
    assert deep["duty"]["door"] == qimen["duty_door"]
    assert deep["duty"]["star"] == qimen["duty_star"]
    assert set(deep["useful_gods"]) == {"career", "wealth", "relationship", "study", "health"}
    assert [row["year"] for row in deep["annual_timing"]] == [2024, 2025, 2026]
    assert deep["pattern_flags"]
    assert deep["door_star_spirit_analysis"]["combinations"]
    assert deep["stem_relation_analysis"]["relations"]
    assert set(deep["useful_god_analysis"]["topics"]) == {"career", "wealth", "relationship", "study", "health"}
    assert deep["pattern_risk_analysis"]["risk_level"] in {"manageable", "cautious"}
    assert deep["timing_activation_analysis"]["reference_year"] == 2026
    assert {item["method"] for item in deep["method_matrix"]} == {
        "door_star_spirit",
        "heaven_earth_stem",
        "useful_god_topic_mapping",
        "pattern_risk",
        "annual_timing_activation",
    }


def test_astrology_deep_analysis_builds_planets_houses_aspects_and_transits():
    birth = normalize_birth_input(
        {
            "name": "Astrology Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
            "annual_start_year": 2024,
            "annual_end_year": 2026,
        }
    )
    astrology = build_astrology_chart(birth)
    deep = astrology["deep_analysis"]

    assert len(deep["planets"]) == 10
    assert {planet["name"] for planet in deep["planets"]} >= {"Sun", "Moon", "Mercury", "Venus", "Mars"}
    assert len(deep["houses"]) == 12
    assert deep["houses"][0]["number"] == 1
    assert isinstance(deep["aspects"], list)
    assert [row["year"] for row in deep["annual_transits"]] == [2024, 2025, 2026]
    assert all(row["activated_house"] for row in deep["annual_transits"])
    assert deep["ephemeris_quality"]["precision_level"]
    assert deep["core_identity_analysis"]["synthesis"]
    assert deep["house_emphasis_analysis"]["emphasized_houses"]
    assert "dominant_pattern" in deep["aspect_pattern_analysis"]
    assert deep["transit_activation_analysis"]["reference_year"] == 2026
    assert {item["method"] for item in deep["method_matrix"]} == {
        "ephemeris_quality",
        "sun_moon_ascendant",
        "house_emphasis",
        "aspect_pattern",
        "transit_activation",
    }


def test_professional_bazi_deep_analysis_uses_lunar_python_when_available():
    provider = get_calendar_provider("professional")
    if provider.available_backend() != "lunar_python":
        return
    birth = normalize_birth_input(
        {
            "name": "Professional BaZi Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
            "calendar_provider": "professional",
        }
    )
    bazi = build_bazi_chart(birth)
    deep = bazi["deep_analysis"]

    assert bazi["context"]["provider_quality"] == "lunar_python"
    assert bazi["pillars"] == {
        "year": "WuWu",
        "month": "BingChen",
        "day": "BingWu",
        "hour": "XinMao",
    }
    assert deep["provider"] == "lunar_python"
    assert deep["day_master"] == "Bing"
    assert deep["ten_gods"]["month"]["stem"]
    assert deep["ten_god_distribution"]
    assert deep["hidden_stem_profile"]["total_hidden_stems"] > 0
    assert deep["nayin_growth_profile"]["complete"] is True
    assert deep["strength_analysis"]["day_master"] == "Bing"
    assert deep["pattern_analysis"]["pattern"]
    assert deep["useful_god_analysis"]["useful_element"] == bazi["context"]["useful_element"]
    assert deep["tiaohou_analysis"]["adjustment"]
    assert {item["method"] for item in deep["method_matrix"]} == {
        "ziping_pattern",
        "strength_support",
        "blind_school_workflow",
        "shensha_nayin",
        "tiaohou",
        "image_symbol_reading",
        "new_school_simplified",
        "data_validation_boundary",
    }
    assert deep["image_symbol_analysis"]["boundary"]
    assert deep["new_school_simplified_analysis"]["polarity"] in {
        "strong",
        "weak_or_environment_weighted",
        "balanced",
    }
    assert deep["data_validation_analysis"]["predictive_optimization_enabled"] is False
    assert deep["major_luck"][1]["ganzhi"] == "DingSi"


def test_annual_luck_builds_structured_year_rows():
    birth = normalize_birth_input(
        {
            "name": "Annual Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
        }
    )
    bazi = build_bazi_chart(birth)
    annual = build_annual_luck(birth, bazi, start_year="2024", end_year="2026")

    assert annual["range"] == {"start_year": 2024, "end_year": 2026, "count": 3}
    assert annual["basis"]["natal_pillars"] == bazi["pillars"]
    assert [row["year"] for row in annual["rows"]] == [2024, 2025, 2026]
    assert annual["rows"][0]["bazi_evidence"]["annual_pillar"] == annual["rows"][0]["ganzhi"]
    assert set(annual["rows"][0]["bazi_evidence"]["annual_ten_gods"]) == {"stem", "branch"}
    assert annual["rows"][0]["bazi_evidence"]["useful_state"]
    assert "interpretation_basis" in annual["rows"][0]["bazi_evidence"]
    assert annual["phase_summary"]
    assert annual["phase_summary"][0]["source"] == "annual_luck.rows"
    assert annual["phase_summary"][0]["source_row_indexes"] == [0, 1, 2]
    assert annual["phase_summary"][0]["start_year"] == 2024
    assert annual["phase_summary"][0]["end_year"] == 2026
    assert annual["phase_summary"][0]["year_count"] == 3
    assert annual["phase_summary"][0]["category_counts"]
    assert annual["phase_summary"][0]["intensity_counts"]
    assert set(annual["phase_summary"][0]["topic_highlights"]) == {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }
    assert annual["phase_summary"][0]["topic_highlights"]["finance"]["source_years"]
    assert {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }.issubset(annual["rows"][0])
    assert annual["rows"][0]["risk_notes"]


def test_monthly_luck_builds_selected_year_rows():
    birth = normalize_birth_input(
        {
            "name": "Monthly Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
        }
    )
    bazi = build_bazi_chart(birth)
    monthly = build_monthly_luck(birth, bazi, years=["2025", "2026"])

    assert monthly["range"] == {"years": [2025, 2026], "months_per_year": 12, "count": 24}
    assert monthly["basis"]["dominant_element"] == bazi["dominant_element"]
    assert monthly["rows"][0]["year"] == 2025
    assert monthly["rows"][0]["month"] == 1
    assert monthly["rows"][0]["bazi_evidence"]["monthly_pillar"] == monthly["rows"][0]["ganzhi"]
    assert set(monthly["rows"][0]["bazi_evidence"]["monthly_ten_gods"]) == {"stem", "branch"}
    assert monthly["rows"][0]["bazi_evidence"]["active_major_luck"]
    assert monthly["rows"][0]["bazi_evidence"]["useful_state"]
    assert monthly["rows"][-1]["year"] == 2026
    assert monthly["rows"][-1]["month"] == 12
    assert {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }.issubset(monthly["rows"][0])


def test_auspicious_calendar_builds_xuanze_window():
    birth = normalize_birth_input(
        {
            "name": "Auspicious Case",
            "birth_date": "1978-04-14",
            "birth_time": "06:50",
            "gender": "male",
            "birthplace": "Sanming",
        }
    )
    calendar = build_auspicious_calendar(
        {**birth, "useful_element": "Earth"},
        start_date="2026-06-21",
        end_date="2026-06-23",
    )

    assert calendar["range"] == {"start_date": "2026-06-21", "end_date": "2026-06-23", "count": 3}
    assert calendar["basis"]["provider_quality"] == "offline_rule_scaffold"
    assert [row["date"] for row in calendar["rows"]] == ["2026-06-21", "2026-06-22", "2026-06-23"]
    first = calendar["rows"][0]
    assert {
        "twelve_officer",
        "twenty_eight_mansion",
        "huangdao",
        "recommended_hours",
        "risk_notes",
    }.issubset(first)
    assert first["rating"] in {"favorable", "mixed", "cautious"}
    assert isinstance(first["recommended_hours"], list)
    assert calendar["twelve_officer_analysis"]["counts"]
    assert calendar["mansion_analysis"]["mansion_sequence"]
    assert calendar["huangdao_analysis"]["rating_counts"]
    assert calendar["hour_selection_analysis"]["total_recommended_hours"] >= 0
    assert calendar["risk_boundary_analysis"]["boundary"]
    assert calendar["provider_quality_analysis"]["provider_quality"] == "offline_rule_scaffold"
    assert {item["method"] for item in calendar["method_matrix"]} == {
        "twelve_officer",
        "twenty_eight_mansion",
        "huangdao_rating",
        "recommended_hours",
        "risk_boundary",
        "provider_quality",
    }


def test_sun_sign_uses_date_boundaries():
    assert sun_sign(4, 19) == "Aries"
    assert sun_sign(4, 20) == "Taurus"
    assert sun_sign(12, 31) == "Capricorn"


def test_external_calendar_provider_can_override_context():
    birth = normalize_birth_input(
        {
            "name": "External Context Case",
            "birth_date": "2000-01-01",
            "birth_time": "06:00",
            "gender": "unspecified",
            "birthplace": "Beijing",
        }
    )
    provider = ExternalCalendarProvider(
        contexts={
            "2000-01-01 06": {
                "date": "2000-01-01",
                "hour": 6,
                "season": "winter",
                "solar_term": "External Term",
                "hour_branch": "Mao",
                "zodiac_animal": "Dragon",
                "pillars": {"year": "GengChen", "month": "DingChou", "day": "WuWu", "hour": "YiMao"},
                "element_counts": {"Wood": 2, "Fire": 2, "Earth": 3, "Metal": 1, "Water": 0},
                "dominant_element": "Earth",
                "useful_element": "Water",
            }
        },
        name="test_external",
    )
    register_calendar_provider(provider)
    context = build_chart_context(birth, provider_name="test_external")
    assert get_calendar_provider("test_external").name == "test_external"
    assert context["provider"] == "test_external"
    assert context["provider_quality"] == "external"
    assert context["solar_term"] == "External Term"
