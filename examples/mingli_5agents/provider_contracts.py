"""Shared production-contract checks for professional mingli providers."""

from __future__ import annotations

from typing import Any

from examples.mingli_5agents.method_surface import REQUIRED_METHODS


def chart_contract(domain: str, chart: dict[str, Any]) -> dict[str, Any]:
    """Validate normalized downstream chart/calendar shape for one domain."""
    validators = {
        "bazi": _bazi_chart_missing,
        "ziwei": _ziwei_chart_missing,
        "qimen": _qimen_chart_missing,
        "astrology": _astrology_chart_missing,
        "xuanze": _xuanze_calendar_missing,
    }
    missing = validators.get(domain, lambda _value: [f"unknown domain: {domain}"])(chart)
    return {
        "name": f"{domain}_normalized_production_contract",
        "valid": not missing,
        "missing": missing,
    }


def raw_json_cli_contract(domain: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate raw JSON-CLI provider output before downstream merge."""
    validators = {
        "ziwei": _ziwei_raw_missing,
        "qimen": _qimen_raw_missing,
        "astrology": _astrology_raw_missing,
        "xuanze": _xuanze_raw_missing,
    }
    missing = validators.get(domain, lambda _value: [f"unknown JSON-CLI domain: {domain}"])(payload)
    return {
        "name": f"{domain}_json_cli_production_contract",
        "valid": not missing,
        "missing": missing,
    }


def _bazi_chart_missing(chart: dict[str, Any]) -> list[str]:
    missing = []
    pillars = chart.get("pillars")
    if not isinstance(pillars, dict) or set(pillars) != {"year", "month", "day", "hour"}:
        missing.append("pillars[year,month,day,hour]")
    deep = chart.get("deep_analysis")
    if not isinstance(deep, dict):
        return sorted([*missing, "deep_analysis"])
    ten_gods = deep.get("ten_gods")
    if not isinstance(ten_gods, dict) or set(ten_gods) != {"year", "month", "day", "hour"}:
        missing.append("deep_analysis.ten_gods[year,month,day,hour]")
    elif not all(isinstance(item, dict) and {"stem", "branch"}.issubset(item) for item in ten_gods.values()):
        missing.append("deep_analysis.ten_gods[].stem/branch")
    luck_start = deep.get("luck_start")
    if not isinstance(luck_start, dict) or "forward" not in luck_start:
        missing.append("deep_analysis.luck_start.forward")
    if not _non_empty_list(deep.get("major_luck")):
        missing.append("deep_analysis.major_luck[non_empty]")
    if not deep.get("day_master"):
        missing.append("deep_analysis.day_master")
    method_matrix = deep.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        missing.append("deep_analysis.method_matrix[non_empty]")
    else:
        methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
        required_methods = REQUIRED_METHODS["bazi"]
        if not required_methods.issubset(methods):
            missing.append("deep_analysis.method_matrix[required_methods]")
    for key in (
        "ten_god_distribution",
        "hidden_stem_profile",
        "nayin_growth_profile",
        "strength_analysis",
        "pattern_analysis",
        "useful_god_analysis",
        "tiaohou_analysis",
    ):
        if not isinstance(deep.get(key), dict) or not deep[key]:
            missing.append(f"deep_analysis.{key}")
    return sorted(set(missing))


def _ziwei_chart_missing(chart: dict[str, Any]) -> list[str]:
    deep = chart.get("deep_analysis")
    if not isinstance(deep, dict):
        return ["deep_analysis"]
    return _ziwei_deep_missing(deep)


def _ziwei_raw_missing(payload: dict[str, Any]) -> list[str]:
    missing = _missing_keys(
        payload,
        [
            "ming_palace",
            "body_palace",
            "transformations",
            "palaces",
            "major_limits",
            "annual_activation",
            "calculation_basis",
        ],
    )
    missing.extend(_ziwei_common_missing(payload))
    missing.extend(_calculation_basis_missing(payload.get("calculation_basis"), prefix="calculation_basis"))
    return sorted(set(missing))


def _ziwei_deep_missing(deep: dict[str, Any]) -> list[str]:
    missing = _missing_keys(deep, ["ming_palace", "body_palace", "four_transformations", "palaces", "major_limits", "annual_activation"])
    common_payload = {**deep, "transformations": deep.get("four_transformations")}
    missing.extend(_ziwei_common_missing(common_payload))
    method_matrix = deep.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        missing.append("method_matrix[non_empty]")
    else:
        methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
        required_methods = REQUIRED_METHODS["ziwei"]
        if not required_methods.issubset(methods):
            missing.append("method_matrix[required_methods]")
    for key in (
        "life_focus",
        "triad_analysis",
        "transformation_analysis",
        "limit_activation_analysis",
    ):
        if not isinstance(deep.get(key), dict) or not deep[key]:
            missing.append(key)
    return sorted(set(missing))


def _ziwei_common_missing(value: dict[str, Any]) -> list[str]:
    missing = []
    transformations = value.get("transformations")
    if not isinstance(transformations, dict) or set(transformations) != {"lu", "quan", "ke", "ji"}:
        missing.append("transformations[lu,quan,ke,ji]")
    palaces = value.get("palaces")
    if not isinstance(palaces, list) or len(palaces) != 12:
        missing.append("palaces[12]")
    elif not all(isinstance(item, dict) and {"name", "theme", "primary_stars"}.issubset(item) for item in palaces):
        missing.append("palaces[].name/theme/primary_stars")
    if not _non_empty_list(value.get("major_limits")):
        missing.append("major_limits[non_empty]")
    if not _non_empty_list(value.get("annual_activation")):
        missing.append("annual_activation[non_empty]")
    if not value.get("ming_palace"):
        missing.append("ming_palace")
    if not value.get("body_palace"):
        missing.append("body_palace")
    return missing


def _qimen_chart_missing(chart: dict[str, Any]) -> list[str]:
    deep = chart.get("deep_analysis")
    if not isinstance(deep, dict):
        return ["deep_analysis"]
    missing = _qimen_common_missing(deep)
    duty = deep.get("duty")
    if not isinstance(duty, dict) or not {"door", "door_palace", "star", "star_palace", "spirit"}.issubset(duty):
        missing.append("duty.door/door_palace/star/star_palace/spirit")
    if not _non_empty_list(deep.get("pattern_flags")):
        missing.append("pattern_flags[non_empty]")
    if not deep.get("yin_yang"):
        missing.append("yin_yang")
    if not deep.get("ju_number"):
        missing.append("ju_number")
    method_matrix = deep.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        missing.append("method_matrix[non_empty]")
    else:
        methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
        required_methods = REQUIRED_METHODS["qimen"]
        if not required_methods.issubset(methods):
            missing.append("method_matrix[required_methods]")
    for key in (
        "door_star_spirit_analysis",
        "stem_relation_analysis",
        "useful_god_analysis",
        "pattern_risk_analysis",
        "timing_activation_analysis",
    ):
        if not isinstance(deep.get(key), dict) or not deep[key]:
            missing.append(key)
    return sorted(set(missing))


def _qimen_raw_missing(payload: dict[str, Any]) -> list[str]:
    missing = _missing_keys(
        payload,
        ["duty_door", "duty_star", "spirit", "palaces", "useful_gods", "annual_timing", "calculation_basis"],
    )
    missing.extend(_qimen_common_missing(payload))
    missing.extend(_calculation_basis_missing(payload.get("calculation_basis"), prefix="calculation_basis"))
    return sorted(set(missing))


def _qimen_common_missing(value: dict[str, Any]) -> list[str]:
    missing = []
    palaces = value.get("palaces")
    if not isinstance(palaces, list) or len(palaces) != 9:
        missing.append("palaces[9]")
    elif not all(
        isinstance(item, dict) and {"name", "door", "star", "spirit", "heaven_stem", "earth_stem"}.issubset(item)
        for item in palaces
    ):
        missing.append("palaces[].name/door/star/spirit/heaven_stem/earth_stem")
    useful = value.get("useful_gods")
    if not isinstance(useful, dict) or not {"career", "wealth", "relationship", "study", "health"}.issubset(useful):
        missing.append("useful_gods[career,wealth,relationship,study,health]")
    if not _non_empty_list(value.get("annual_timing")):
        missing.append("annual_timing[non_empty]")
    return missing


def _calculation_basis_missing(value: Any, *, prefix: str) -> list[str]:
    if not isinstance(value, dict):
        return [prefix]
    required = [
        "provider",
        "rule_set",
        "rule_set_version",
        "rule_source",
        "license_or_review",
        "calculation_scope",
    ]
    missing = [f"{prefix}.{field}" for field in required if not str(value.get(field, "")).strip()]
    if not any(str(value.get(field, "")).strip() for field in ("rule_source_sha256", "rule_receipt_sha256")):
        missing.append(f"{prefix}.rule_source_sha256|rule_receipt_sha256")
    return missing


def _astrology_chart_missing(chart: dict[str, Any]) -> list[str]:
    deep = chart.get("deep_analysis")
    if not isinstance(deep, dict):
        return ["deep_analysis"]
    missing = _astrology_common_missing(deep)
    if not deep.get("zodiac"):
        missing.append("zodiac")
    method_matrix = deep.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        missing.append("method_matrix[non_empty]")
    else:
        methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
        required_methods = REQUIRED_METHODS["astrology"]
        if not required_methods.issubset(methods):
            missing.append("method_matrix[required_methods]")
    for key in (
        "ephemeris_quality",
        "core_identity_analysis",
        "house_emphasis_analysis",
        "aspect_pattern_analysis",
        "transit_activation_analysis",
    ):
        if not isinstance(deep.get(key), dict) or not deep[key]:
            missing.append(key)
    return sorted(set(missing))


def _astrology_raw_missing(payload: dict[str, Any]) -> list[str]:
    missing = _missing_keys(payload, ["sun", "moon", "ascendant", "planets", "houses", "annual_transits", "ephemeris"])
    missing.extend(_astrology_common_missing(payload))
    missing.extend(_astrology_ephemeris_missing(payload.get("ephemeris")))
    return sorted(set(missing))


def _astrology_common_missing(value: dict[str, Any]) -> list[str]:
    missing = []
    planets = value.get("planets")
    if not isinstance(planets, list) or len(planets) < 10:
        missing.append("planets[>=10]")
    elif not all(isinstance(item, dict) and {"name", "sign", "degree", "house"}.issubset(item) for item in planets):
        missing.append("planets[].name/sign/degree/house")
    houses = value.get("houses")
    if not isinstance(houses, list) or len(houses) != 12:
        missing.append("houses[12]")
    elif not all(isinstance(item, dict) and {"number", "cusp_sign", "ruler", "theme"}.issubset(item) for item in houses):
        missing.append("houses[].number/cusp_sign/ruler/theme")
    if not _non_empty_list(value.get("annual_transits")):
        missing.append("annual_transits[non_empty]")
    return missing


def _astrology_ephemeris_missing(ephemeris: Any) -> list[str]:
    if not isinstance(ephemeris, dict):
        return ["ephemeris"]
    missing = _missing_keys(
        ephemeris,
        [
            "source",
            "zodiac",
            "house_system",
            "time_scale",
            "calculation_time",
            "license_or_review",
            "data_source",
        ],
    )
    calculation_time = ephemeris.get("calculation_time")
    if not isinstance(calculation_time, dict):
        missing.append("ephemeris.calculation_time")
    elif not any(calculation_time.get(key) is not None for key in ("julian_day_ut", "iso_utc")):
        missing.append("ephemeris.calculation_time[julian_day_ut|iso_utc]")
    if not str(ephemeris.get("license_or_review", "")).strip():
        missing.append("ephemeris.license_or_review")
    if not str(ephemeris.get("data_source", "")).strip():
        missing.append("ephemeris.data_source")
    return [f"ephemeris.{item}" if not item.startswith("ephemeris.") else item for item in missing]


def _xuanze_calendar_missing(calendar: dict[str, Any]) -> list[str]:
    missing = _xuanze_common_missing(calendar)
    method_matrix = calendar.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        missing.append("method_matrix[non_empty]")
    else:
        methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
        required_methods = REQUIRED_METHODS["xuanze"]
        if not required_methods.issubset(methods):
            missing.append("method_matrix[required_methods]")
    for key in (
        "twelve_officer_analysis",
        "mansion_analysis",
        "huangdao_analysis",
        "hour_selection_analysis",
        "risk_boundary_analysis",
        "provider_quality_analysis",
    ):
        if not isinstance(calendar.get(key), dict) or not calendar[key]:
            missing.append(key)
    return sorted(set(missing))


def _xuanze_raw_missing(calendar: dict[str, Any]) -> list[str]:
    missing = _xuanze_common_missing(calendar)
    missing.extend(_xuanze_basis_audit_missing(calendar.get("basis")))
    return sorted(set(missing))


def _xuanze_common_missing(calendar: dict[str, Any]) -> list[str]:
    missing = _missing_keys(calendar, ["rows", "summary"])
    rows = calendar.get("rows")
    range_meta = calendar.get("range")
    basis = calendar.get("basis")
    required = {
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
    if isinstance(range_meta, dict) and isinstance(rows, list) and range_meta.get("count") != len(rows):
        missing.append("range.count")
    if basis is not None and (not isinstance(basis, dict) or not basis.get("provider_quality")):
        missing.append("basis.provider_quality")
    if not isinstance(rows, list) or not rows:
        missing.append("rows[non_empty]")
    else:
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not required.issubset(row):
                missing.append(f"rows[{index}].required_fields")
                continue
            if row.get("rating") not in {"favorable", "mixed", "cautious"}:
                missing.append(f"rows[{index}].rating")
            if not isinstance(row.get("recommended_hours"), list):
                missing.append(f"rows[{index}].recommended_hours")
    summary = calendar.get("summary")
    if not isinstance(summary, dict) or "favorable_dates" not in summary:
        missing.append("summary.favorable_dates")
    return sorted(set(missing))


def _xuanze_basis_audit_missing(basis: Any) -> list[str]:
    if not isinstance(basis, dict):
        return ["basis"]
    missing = _missing_keys(
        basis,
        [
            "provider",
            "provider_quality",
            "rule_set",
            "rule_table_source",
            "rule_table_version",
            "license_or_review",
            "calculation_scope",
        ],
    )
    if not any(str(basis.get(key, "")).strip() for key in ("rule_table_sha256", "rule_table_receipt_sha256")):
        missing.append("rule_table_sha256|rule_table_receipt_sha256")
    return [f"basis.{item}" if not item.startswith("basis.") else item for item in missing]


def _missing_keys(value: dict[str, Any], required: list[str]) -> list[str]:
    return [key for key in required if key not in value]


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)
