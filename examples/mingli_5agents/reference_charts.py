"""Reference chart fixtures and contract checks for provider integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from examples.mingli_5agents.method_surface import REQUIRED_METHODS
from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart
from examples.mingli_5agents.tools.auspicious_calendar import build_auspicious_calendar
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.qimen_ju import build_qimen_chart
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart


XUANZE_ROW_FIELDS = {
    "date",
    "weekday",
    "ganzhi",
    "solar_term",
    "twelve_officer",
    "twenty_eight_mansion",
    "huangdao",
    "rating",
    "suitable",
    "avoid",
    "recommended_hours",
    "risk_notes",
}

@dataclass(frozen=True)
class ReferenceChartCase:
    """One fixed chart-contract fixture."""

    name: str
    birth: dict[str, Any]
    expected: dict[str, Any]


def reference_chart_cases() -> list[ReferenceChartCase]:
    """Return fixed provider contract fixtures used by benchmark and audit."""
    return [
        ReferenceChartCase(
            name="external_structured_provider_contract",
            birth={
                "name": "Reference Provider Case",
                "birth_date": "1990-04-12",
                "birth_time": "09:20",
                "gender": "unspecified",
                "birthplace": "Hangzhou",
                "timezone_offset": "+08:00",
                "latitude": 30.25,
                "longitude": 120.16,
                "professional_charts": {
                    "bazi": {
                        "source": "reference_bazi_fixture",
                        "version": "reference-1.0",
                        "license_or_review": "reviewed reference fixture",
                        "pillars": {
                            "year": "GengWu",
                            "month": "GengChen",
                            "day": "DingWei",
                            "hour": "YiSi",
                        },
                        "element_counts": {"Wood": 1, "Fire": 3, "Earth": 2, "Metal": 2, "Water": 0},
                        "dominant_element": "Fire",
                        "useful_element": "Metal",
                        "structure": "reference_external",
                        "deep_analysis": {
                            "provider": "reference_bazi_engine",
                            "day_master": "Ding",
                            "ten_gods": {
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
                            },
                            "luck_start": {"years": 7, "months": 2, "days": 0, "hours": 0, "forward": True},
                            "major_luck": [
                                {
                                    "index": 1,
                                    "start_age": 8,
                                    "end_age": 17,
                                    "start_year": 1998,
                                    "end_year": 2007,
                                    "ganzhi": "JiaZi",
                                }
                            ],
                        },
                    },
                    "ziwei": {
                        "source": "reference_ziwei_fixture",
                        "version": "reference-1.0",
                        "license_or_review": "reviewed reference fixture",
                        "ming_palace": "Career",
                        "body_palace": "Wealth",
                        "major_stars": ["Ziwei", "Wuqu"],
                        "transformations": {
                            "lu": "Wuqu",
                            "quan": "Ziwei",
                            "ke": "Tianji",
                            "ji": "Taiyin",
                        },
                    },
                    "qimen": {
                        "source": "reference_qimen_fixture",
                        "version": "reference-1.0",
                        "license_or_review": "reviewed reference fixture",
                        "duty_door": "Open",
                        "duty_star": "Tianxin",
                        "spirit": "Nine Heaven",
                        "pattern": "reference verified plate",
                    },
                    "astrology": {
                        "source": "reference_astrology_fixture",
                        "version": "reference-1.0",
                        "license_or_review": "reviewed reference fixture",
                        "sun": "Aries",
                        "moon": "Cancer",
                        "ascendant": "Libra",
                        "annual_theme": "reference ephemeris overlay",
                    },
                    "xuanze": {
                        "source": "reference_xuanze_fixture",
                        "version": "reference-1.0",
                        "license_or_review": "reviewed reference fixture",
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
                                "suitable": ["reference launch"],
                                "avoid": ["reference avoid"],
                                "recommended_hours": [
                                    {"start": "09:00", "end": "10:59", "branch": "Si", "element": "Fire"}
                                ],
                                "risk_notes": ["reference caution"],
                            }
                        ],
                        "summary": {
                            "favorable_dates": ["2026-06-21"],
                            "cautious_dates": [],
                            "best_date": "2026-06-21",
                        },
                    },
                },
            },
            expected={
                "bazi": {
                    "provider_quality": "external_bazi",
                    "context_provider_source": "reference_bazi_fixture",
                    "provider_provenance_valid": True,
                    "pillar_keys": ["year", "month", "day", "hour"],
                    "deep_sections": ["ten_gods", "major_luck", "luck_start"],
                    "method_names": sorted(REQUIRED_METHODS["bazi"]),
                },
                "ziwei": {
                    "provider_quality": "external_ziwei",
                    "provider_provenance_valid": True,
                    "ming_palace": "Career",
                    "body_palace": "Wealth",
                    "deep_provider_quality": "external_ziwei",
                    "palace_count": 12,
                    "method_names": sorted(REQUIRED_METHODS["ziwei"]),
                },
                "qimen": {
                    "provider_quality": "external_qimen",
                    "provider_provenance_valid": True,
                    "duty_door": "Open",
                    "duty_star": "Tianxin",
                    "deep_provider_quality": "external_qimen",
                    "palace_count": 9,
                    "method_names": sorted(REQUIRED_METHODS["qimen"]),
                },
                "astrology": {
                    "provider_quality": "external_astrology",
                    "provider_provenance_valid": True,
                    "sun": "Aries",
                    "moon": "Cancer",
                    "ascendant": "Libra",
                    "deep_provider_quality": "external_astrology",
                    "planet_count": 10,
                    "method_names": sorted(REQUIRED_METHODS["astrology"]),
                },
                "xuanze": {
                    "provider_quality": "external_xuanze",
                    "basis_provider_source": "reference_xuanze_fixture",
                    "provider_provenance_valid": True,
                    "row_count": 1,
                    "all_rows_have_required_fields": True,
                    "all_rows_have_recommended_hours": True,
                    "ratings_valid": True,
                    "summary_dates_consistent": True,
                    "method_names": sorted(REQUIRED_METHODS["xuanze"]),
                },
            },
        ),
        ReferenceChartCase(
            name="professional_bazi_contract",
            birth={
                "name": "Reference BaZi Case",
                "birth_date": "1978-04-14",
                "birth_time": "06:50",
                "gender": "male",
                "birthplace": "Sanming",
                "calendar_provider": "auto",
            },
            expected={
                "bazi": {
                    "pillar_keys": ["year", "month", "day", "hour"],
                    "deep_sections": ["ten_gods", "major_luck", "luck_start"],
                    "method_names": sorted(REQUIRED_METHODS["bazi"]),
                }
            },
        ),
        ReferenceChartCase(
            name="xuanze_almanac_contract",
            birth={
                "name": "Reference Xuanze Case",
                "birth_date": "1978-04-14",
                "birth_time": "06:50",
                "gender": "male",
                "birthplace": "Sanming",
                "calendar_provider": "auto",
                "useful_element": "Metal",
            },
            expected={
                "xuanze": {
                    "range_start": "2026-06-21",
                    "range_end": "2026-06-23",
                    "range_count": 3,
                    "row_count": 3,
                    "basis_provider_quality_present": True,
                    "all_rows_have_required_fields": True,
                    "all_rows_have_recommended_hours": True,
                    "ratings_valid": True,
                    "summary_dates_consistent": True,
                    "caution_present": True,
                    "method_names": sorted(REQUIRED_METHODS["xuanze"]),
                }
            },
        ),
    ]


def run_reference_chart_checks() -> dict[str, Any]:
    """Run provider contract checks and return a benchmark-friendly summary."""
    case_results = [_run_case(case) for case in reference_chart_cases()]
    passed = sum(1 for item in case_results if item["passed"])
    return {
        "passed": passed == len(case_results),
        "passed_count": passed,
        "total": len(case_results),
        "method_coverage": _method_coverage(case_results),
        "cases": case_results,
    }


def _run_case(case: ReferenceChartCase) -> dict[str, Any]:
    birth = normalize_birth_input(case.birth)
    failures: list[str] = []
    charts = {
        "bazi": build_bazi_chart(birth),
        "ziwei": build_ziwei_chart(birth),
        "qimen": build_qimen_chart(birth),
        "astrology": build_astrology_chart(birth),
        "xuanze": build_auspicious_calendar(
            birth,
            start_date="2026-06-21",
            end_date="2026-06-23",
        ),
    }
    for domain, expected in case.expected.items():
        failures.extend(_check_domain(domain, charts[domain], expected))
    return {
        "name": case.name,
        "passed": not failures,
        "failures": failures,
        "checked_domains": sorted(case.expected),
        "method_coverage": {
            domain: _actual_value(domain, charts[domain], "method_names")
            for domain in sorted(case.expected)
        },
        "provenance_coverage": {
            domain: _actual_value(domain, charts[domain], "provider_provenance_valid")
            for domain in sorted(case.expected)
        },
    }


def _check_domain(domain: str, chart: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures = []
    for key, value in expected.items():
        actual = _actual_value(domain, chart, key)
        if actual != value:
            failures.append(f"{domain}.{key}: expected {value!r}, got {actual!r}")
    return failures


def _actual_value(domain: str, chart: dict[str, Any], key: str) -> Any:
    deep = chart.get("deep_analysis", {})
    if key == "deep_provider_quality":
        return deep.get("provider_quality")
    if key == "palace_count":
        return len(deep.get("palaces", []))
    if key == "planet_count":
        return len(deep.get("planets", []))
    if key == "pillar_keys":
        return list(chart.get("pillars", {}).keys())
    if key == "deep_sections":
        return [item for item in ["ten_gods", "major_luck", "luck_start"] if item in deep]
    if key == "method_names":
        return _method_names(chart if domain == "xuanze" else deep)
    if key == "context_provider_source":
        return chart.get("context", {}).get("provider_source")
    if domain == "xuanze":
        return _actual_xuanze_value(chart, key)
    if key == "provider_provenance_valid":
        context = chart.get("context", {})
        provenance = context.get("provider_provenance") or context.get("domain_provider_provenance")
        return isinstance(provenance, dict) and provenance.get("valid") is True
    if domain == "qimen" and key in {"duty_door", "duty_star"}:
        return chart.get(key)
    return chart.get(key)


def _actual_xuanze_value(chart: dict[str, Any], key: str) -> Any:
    rows = chart.get("rows", [])
    range_meta = chart.get("range", {})
    basis = chart.get("basis", {})
    summary = chart.get("summary", {})
    if key == "provider_quality":
        return chart.get("provider_quality")
    if key == "basis_provider_source":
        return basis.get("provider_source") if isinstance(basis, dict) else None
    if key == "provider_provenance_valid":
        provenance = basis.get("provider_provenance") if isinstance(basis, dict) else None
        return isinstance(provenance, dict) and provenance.get("valid") is True
    if key == "range_start":
        return range_meta.get("start_date")
    if key == "range_end":
        return range_meta.get("end_date")
    if key == "range_count":
        return range_meta.get("count")
    if key == "row_count":
        return len(rows) if isinstance(rows, list) else 0
    if key == "basis_provider_quality_present":
        return bool(isinstance(basis, dict) and basis.get("provider_quality"))
    if key == "all_rows_have_required_fields":
        return bool(rows) and all(isinstance(row, dict) and XUANZE_ROW_FIELDS.issubset(row) for row in rows)
    if key == "all_rows_have_recommended_hours":
        return bool(rows) and all(isinstance(row.get("recommended_hours"), list) and row["recommended_hours"] for row in rows)
    if key == "ratings_valid":
        return bool(rows) and all(row.get("rating") in {"favorable", "mixed", "cautious"} for row in rows)
    if key == "summary_dates_consistent":
        if not isinstance(summary, dict) or not isinstance(rows, list):
            return False
        row_dates = {row.get("date") for row in rows if isinstance(row, dict)}
        favorable = set(summary.get("favorable_dates", []))
        cautious = set(summary.get("cautious_dates", []))
        best = summary.get("best_date")
        return favorable.issubset(row_dates) and cautious.issubset(row_dates) and (best is None or best in row_dates)
    if key == "caution_present":
        return bool(chart.get("caution"))
    return chart.get(key)


def _method_names(container: dict[str, Any]) -> list[str]:
    matrix = container.get("method_matrix")
    if not isinstance(matrix, list):
        return []
    return sorted(
        str(item.get("method"))
        for item in matrix
        if isinstance(item, dict) and item.get("method")
    )


def _method_coverage(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    observed: dict[str, set[str]] = {domain: set() for domain in REQUIRED_METHODS}
    for case in case_results:
        coverage = case.get("method_coverage", {})
        if not isinstance(coverage, dict):
            continue
        for domain, methods in coverage.items():
            if domain in observed and isinstance(methods, list):
                observed[domain].update(str(item) for item in methods)
    per_domain = {
        domain: {
            "required": sorted(required),
            "observed": sorted(observed[domain]),
            "missing": sorted(required - observed[domain]),
            "passed": required.issubset(observed[domain]),
        }
        for domain, required in REQUIRED_METHODS.items()
    }
    return {
        "passed": all(item["passed"] for item in per_domain.values()),
        "domains": per_domain,
    }
