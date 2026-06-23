"""Structured report schema scoring for mingli outputs."""

from __future__ import annotations


ANNUAL_REQUIRED_FIELDS = {
    "year",
    "age",
    "ganzhi",
    "phase",
    "elements",
    "bazi_evidence",
    "category",
    "intensity",
    "finance",
    "official_career",
    "career",
    "study",
    "relationship",
    "friends",
    "leadership",
    "children_family",
    "risk_notes",
}

MONTHLY_REQUIRED_FIELDS = {
    "year",
    "month",
    "month_name",
    "ganzhi",
    "elements",
    "bazi_evidence",
    "category",
    "intensity",
    "finance",
    "official_career",
    "career",
    "study",
    "relationship",
    "friends",
    "leadership",
    "children_family",
    "risk_notes",
}

AUSPICIOUS_REQUIRED_FIELDS = {
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

ANNUAL_TIMELINE_TOPICS = {
    "finance",
    "official_career",
    "career",
    "study",
    "relationship",
    "friends",
    "leadership",
    "children_family",
}


def _birth_profile_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    required_text = (
        "name",
        "birth_date",
        "birth_time",
        "gender",
        "birthplace",
        "birthplace_normalized",
        "birthplace_region",
        "geocoding_provider",
        "geocoding_quality",
    )
    if any(not isinstance(value.get(key), str) or not value.get(key) for key in required_text):
        return False
    if (
        value.get("geocoding_quality") != "unresolved"
        and (not isinstance(value.get("timezone_offset"), (int, float, str)) or value.get("timezone_offset") in ("", None))
    ):
        return False
    for key in ("latitude", "longitude"):
        if value.get(key) is not None and not isinstance(value.get(key), (int, float)):
            return False
    required_ints = ("year", "month", "day", "hour", "minute")
    if any(not isinstance(value.get(key), int) for key in required_ints):
        return False
    if not (1 <= int(value["month"]) <= 12 and 1 <= int(value["day"]) <= 31):
        return False
    if not (0 <= int(value["hour"]) <= 23 and 0 <= int(value["minute"]) <= 59):
        return False
    return isinstance(value.get("calendar_provider"), str) and bool(value.get("calendar_provider"))


def _request_provenance_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("schema_version") != "request-provenance-v1":
        return False
    for key in ("raw_task_input_sha256", "birth_profile_sha256", "report_material_sha256", "chain_sha256"):
        if not _sha256_ok(value.get(key)):
            return False
    contexts = value.get("specialist_contexts")
    if not isinstance(contexts, dict) or set(contexts) != {"bazi", "ziwei", "qimen", "astrology"}:
        return False
    for item in contexts.values():
        if not isinstance(item, dict):
            return False
        if not _sha256_ok(item.get("context_sha256")) or not _sha256_ok(item.get("birth_profile_sha256")):
            return False
        if item.get("birth_profile_sha256") != value.get("birth_profile_sha256"):
            return False
    material = value.get("report_material")
    return (
        isinstance(material, dict)
        and material.get("birth_profile_sha256") == value.get("birth_profile_sha256")
        and _sha256_ok(material.get("deliberation_receipt_sha256"))
        and isinstance(material.get("deliberation_claim_count"), int)
        and material.get("deliberation_claim_count", 0) > 0
    )


def _sha256_ok(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _vote_audit_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    summary = value.get("_summary")
    audit = value.get("_audit")
    claims = value.get("_claims")
    if not isinstance(summary, dict) or summary.get("passed") is not True:
        return False
    if not isinstance(audit, dict) or audit.get("evidence_bound") is not True:
        return False
    if not isinstance(claims, list) or not claims:
        return False
    if audit.get("claim_count") != len(claims):
        return False
    passed_count = 0
    for item in claims:
        if not isinstance(item, dict):
            return False
        required = {
            "id",
            "topic",
            "claim",
            "supporters",
            "challenges",
            "support_ratio",
            "threshold",
            "passed",
            "source_ids",
            "decision",
        }
        if not required.issubset(item):
            return False
        if not isinstance(item.get("supporters"), list) or not item["supporters"]:
            return False
        if not isinstance(item.get("challenges"), list):
            return False
        if not isinstance(item.get("source_ids"), list) or not item["source_ids"]:
            return False
        if item.get("passed") is True:
            passed_count += 1
    return audit.get("passed_claim_count") == passed_count and passed_count == len(claims)


def _deliberation_receipt_ok(value: object, votes: object, source_review: object) -> bool:
    if not isinstance(value, dict):
        return False
    required_hashes = (
        "discussion_sha256",
        "votes_sha256",
        "source_review_sha256",
        "conflicts_sha256",
        "workflow_sha256",
        "sha256",
    )
    if any(not _sha256_ok(value.get(key)) for key in required_hashes):
        return False
    if value.get("schema_version") != "deliberation-receipt-v1":
        return False
    if not isinstance(votes, dict) or not isinstance(source_review, dict):
        return False
    audit = votes.get("_audit")
    return (
        isinstance(value.get("discussion_count"), int)
        and value.get("discussion_count", 0) > 0
        and isinstance(audit, dict)
        and value.get("claim_count") == audit.get("claim_count")
        and value.get("passed_claim_count") == audit.get("passed_claim_count")
        and value.get("source_review_status") == source_review.get("status")
    )


def report_schema_score(result: dict, expected: dict | None = None) -> float:
    """Score final report shape, especially annual and monthly trend artifacts."""
    final_report = result.get("final_report", {})
    if not isinstance(final_report, dict):
        return 0.0

    score = 0.0
    score += 0.06 if _list_present(final_report, "summary") else 0.0
    score += 0.07 if _list_present(final_report, "boundaries") else 0.0
    score += 0.005 if _birth_profile_ok(final_report.get("birth_profile")) else 0.0
    score += 0.005 if _request_provenance_ok(final_report.get("request_provenance")) else 0.0
    score += 0.095 if _dict_present(final_report, "source_review") else 0.0
    score += 0.08 if _vote_audit_ok(final_report.get("votes")) else 0.0
    score += 0.005 if _deliberation_receipt_ok(
        final_report.get("deliberation_receipt"),
        final_report.get("votes"),
        final_report.get("source_review"),
    ) else 0.0
    score += 0.02 if _specialist_layers_ok(result.get("specialists", {})) else 0.0

    bazi_chart = result.get("specialists", {}).get("bazi", {}).get("chart", {})
    score += 0.09 if _bazi_deep_analysis_ok(bazi_chart.get("deep_analysis")) else 0.0
    ziwei_chart = result.get("specialists", {}).get("ziwei", {}).get("chart", {})
    score += 0.075 if _ziwei_deep_analysis_ok(ziwei_chart.get("deep_analysis")) else 0.0
    qimen_chart = result.get("specialists", {}).get("qimen", {}).get("chart", {})
    score += 0.05 if _qimen_deep_analysis_ok(qimen_chart.get("deep_analysis")) else 0.0
    astrology_chart = result.get("specialists", {}).get("astrology", {}).get("chart", {})
    score += 0.055 if _astrology_deep_analysis_ok(astrology_chart.get("deep_analysis")) else 0.0
    score += 0.06 if _topic_synthesis_ok(final_report.get("topic_synthesis")) else 0.0
    score += 0.008 if _bazi_profile_ok(final_report.get("bazi_profile")) else 0.0
    score += 0.008 if _ziwei_profile_ok(final_report.get("ziwei_profile")) else 0.0
    score += 0.008 if _qimen_profile_ok(final_report.get("qimen_profile")) else 0.0
    score += 0.008 if _astrology_profile_ok(final_report.get("astrology_profile")) else 0.0
    score += 0.005 if _provider_summary_ok(final_report.get("provider_summary")) else 0.0
    score += 0.003 if _rendered_reports_ok(final_report.get("rendered_reports")) else 0.0

    annual = final_report.get("annual_luck", {})
    if _luck_table_ok(annual, ANNUAL_REQUIRED_FIELDS) and _annual_timeline_ok(
        final_report.get("annual_timeline"),
        annual,
    ) and _annual_phase_summary_ok(annual):
        score += 0.11
    elif annual:
        score += 0.09

    monthly = final_report.get("monthly_luck", {})
    if _luck_table_ok(monthly, MONTHLY_REQUIRED_FIELDS):
        score += 0.1
    elif monthly:
        score += 0.07

    auspicious = final_report.get("auspicious_calendar", {})
    if _auspicious_calendar_ok(auspicious):
        score += 0.08

    return round(min(1.0, score), 6)


def _annual_timeline_ok(value: object, annual_luck: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not isinstance(annual_luck, dict):
        return False
    rows = annual_luck.get("rows")
    range_meta = annual_luck.get("range")
    if not isinstance(rows, list) or not isinstance(range_meta, dict):
        return False
    if len(value) != len(rows) or range_meta.get("count") != len(value):
        return False
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            return False
        required = {
            "year",
            "age",
            "ganzhi",
            "phase",
            "category",
            "intensity",
            "element_focus",
            "bazi_evidence",
            "topics",
            "risk_notes",
            "source",
            "source_row_index",
            "boundary",
        }
        if not required.issubset(item):
            return False
        row = rows[index]
        if not isinstance(row, dict):
            return False
        if item.get("year") != row.get("year") or item.get("source_row_index") != index:
            return False
        if item.get("source") != "annual_luck.rows":
            return False
        if item.get("bazi_evidence") != row.get("bazi_evidence") or not isinstance(item.get("bazi_evidence"), dict):
            return False
        if not isinstance(item.get("risk_notes"), list) or not item.get("boundary"):
            return False
        topics = item.get("topics")
        if not isinstance(topics, dict) or set(topics) != ANNUAL_TIMELINE_TOPICS:
            return False
        for topic_key, topic in topics.items():
            if not isinstance(topic, dict):
                return False
            if not {"message", "category", "intensity"}.issubset(topic):
                return False
            if topic.get("message") != row.get(topic_key):
                return False
    return True


def _annual_phase_summary_ok(annual_luck: object) -> bool:
    if not isinstance(annual_luck, dict):
        return False
    rows = annual_luck.get("rows")
    summaries = annual_luck.get("phase_summary")
    if not isinstance(rows, list) or not rows or not isinstance(summaries, list) or not summaries:
        return False
    covered_indexes: list[int] = []
    required_topics = ANNUAL_TIMELINE_TOPICS
    for item in summaries:
        if not isinstance(item, dict):
            return False
        required = {
            "phase",
            "start_year",
            "end_year",
            "start_age",
            "end_age",
            "year_count",
            "dominant_category",
            "category_counts",
            "intensity_counts",
            "high_volatility_years",
            "constructive_years",
            "topic_highlights",
            "source",
            "source_row_indexes",
            "boundary",
        }
        if not required.issubset(item):
            return False
        indexes = item.get("source_row_indexes")
        if not isinstance(indexes, list) or not indexes:
            return False
        if not all(isinstance(index, int) and 0 <= index < len(rows) for index in indexes):
            return False
        if item.get("source") != "annual_luck.rows" or item.get("year_count") != len(indexes):
            return False
        if not isinstance(item.get("category_counts"), dict) or not item["category_counts"]:
            return False
        if not isinstance(item.get("intensity_counts"), dict) or not item["intensity_counts"]:
            return False
        if not isinstance(item.get("high_volatility_years"), list):
            return False
        if not isinstance(item.get("constructive_years"), list):
            return False
        topic_highlights = item.get("topic_highlights")
        if not isinstance(topic_highlights, dict) or set(topic_highlights) != required_topics:
            return False
        for topic in topic_highlights.values():
            if not isinstance(topic, dict):
                return False
            if not {"dominant_message", "supporting_year_count", "source_years"}.issubset(topic):
                return False
            if not isinstance(topic.get("source_years"), list):
                return False
        first = rows[indexes[0]]
        last = rows[indexes[-1]]
        if not isinstance(first, dict) or not isinstance(last, dict):
            return False
        if item.get("start_year") != first.get("year") or item.get("end_year") != last.get("year"):
            return False
        if item.get("start_age") != first.get("age") or item.get("end_age") != last.get("age"):
            return False
        covered_indexes.extend(indexes)
    return covered_indexes == list(range(len(rows)))


def _list_present(container: dict, key: str) -> bool:
    value = container.get(key)
    return isinstance(value, list) and bool(value)


def _dict_present(container: dict, key: str) -> bool:
    value = container.get(key)
    return isinstance(value, dict) and bool(value)


def _specialist_layers_ok(specialists: object) -> bool:
    required_agents = {"bazi", "ziwei", "qimen", "astrology"}
    required_layers = {"macro", "micro", "yearly", "monthly", "uncertainty"}
    if not isinstance(specialists, dict) or set(specialists) != required_agents:
        return False
    for report in specialists.values():
        if not isinstance(report, dict) or not required_layers.issubset(report):
            return False
        layers = report.get("layers")
        if not isinstance(layers, dict) or set(layers) != required_layers:
            return False
        for key in required_layers:
            item = layers.get(key)
            if not isinstance(item, dict) or item.get("level") != key:
                return False
            if not item.get("focus") or str(item.get("text")) != str(report.get(key)):
                return False
            if not isinstance(item.get("source_ids"), list) or not item["source_ids"]:
                return False
            if not isinstance(item.get("evidence_required"), bool):
                return False
            if not item.get("boundary_type"):
                return False
    return True


def _luck_table_ok(table: object, required_fields: set[str]) -> bool:
    if not isinstance(table, dict):
        return False
    rows = table.get("rows")
    range_meta = table.get("range")
    basis = table.get("basis")
    if not isinstance(rows, list) or not rows:
        return False
    if not isinstance(range_meta, dict) or range_meta.get("count") != len(rows):
        return False
    if not isinstance(basis, dict) or not basis.get("provider_quality"):
        return False
    return all(isinstance(row, dict) and required_fields.issubset(row) for row in rows)


def _auspicious_calendar_ok(table: object) -> bool:
    if not isinstance(table, dict):
        return False
    rows = table.get("rows")
    range_meta = table.get("range")
    basis = table.get("basis")
    summary = table.get("summary")
    if not isinstance(rows, list) or not rows:
        return False
    if not isinstance(range_meta, dict) or range_meta.get("count") != len(rows):
        return False
    if not isinstance(basis, dict) or not basis.get("provider_quality"):
        return False
    if not isinstance(summary, dict) or "favorable_dates" not in summary:
        return False
    for row in rows:
        if not isinstance(row, dict) or not AUSPICIOUS_REQUIRED_FIELDS.issubset(row):
            return False
        if row.get("rating") not in {"favorable", "mixed", "cautious"}:
            return False
        hours = row.get("recommended_hours")
        if not isinstance(hours, list):
            return False
    return _xuanze_method_layers_ok(table)


def _xuanze_method_layers_ok(value: dict[str, object]) -> bool:
    required_blocks = {
        "twelve_officer_analysis",
        "mansion_analysis",
        "huangdao_analysis",
        "hour_selection_analysis",
        "risk_boundary_analysis",
        "provider_quality_analysis",
    }
    if not all(isinstance(value.get(key), dict) and value[key] for key in required_blocks):
        return False
    method_matrix = value.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        return False
    methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
    return {
        "twelve_officer",
        "twenty_eight_mansion",
        "huangdao_rating",
        "recommended_hours",
        "risk_boundary",
        "provider_quality",
    }.issubset(methods)


def _bazi_deep_analysis_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    ten_gods = value.get("ten_gods")
    major_luck = value.get("major_luck")
    luck_start = value.get("luck_start")
    if not isinstance(ten_gods, dict) or set(ten_gods) != {"year", "month", "day", "hour"}:
        return False
    if not all(isinstance(item, dict) and {"stem", "branch"}.issubset(item) for item in ten_gods.values()):
        return False
    if not isinstance(major_luck, list) or not major_luck:
        return False
    if not isinstance(luck_start, dict) or "forward" not in luck_start:
        return False
    method_matrix = value.get("method_matrix")
    required_methods = {"ziping_pattern", "strength_support", "blind_school_workflow", "shensha_nayin", "tiaohou"}
    if not isinstance(method_matrix, list) or not method_matrix:
        return False
    methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
    if not required_methods.issubset(methods):
        return False
    required_blocks = {
        "ten_god_distribution",
        "hidden_stem_profile",
        "nayin_growth_profile",
        "strength_analysis",
        "pattern_analysis",
        "useful_god_analysis",
        "tiaohou_analysis",
    }
    if not all(isinstance(value.get(key), dict) and value[key] for key in required_blocks):
        return False
    return bool(value.get("day_master"))


def _bazi_profile_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if not {
        "pillars",
        "structure",
        "dominant_element",
        "useful_element",
        "day_master",
        "luck_start",
        "major_luck",
        "method_matrix",
        "strength_analysis",
        "pattern_analysis",
        "useful_god_analysis",
        "tiaohou_analysis",
        "image_symbol_analysis",
        "new_school_simplified_analysis",
        "data_validation_analysis",
    }.issubset(value):
        return False
    required_blocks = {
        "strength_analysis",
        "pattern_analysis",
        "useful_god_analysis",
        "tiaohou_analysis",
        "image_symbol_analysis",
        "new_school_simplified_analysis",
        "data_validation_analysis",
    }
    if not all(isinstance(value.get(key), dict) and value[key] for key in required_blocks):
        return False
    if not isinstance(value.get("pillars"), dict) or set(value["pillars"]) != {"year", "month", "day", "hour"}:
        return False
    if not isinstance(value.get("luck_start"), dict) or "forward" not in value["luck_start"]:
        return False
    major_luck = value.get("major_luck")
    method_matrix = value.get("method_matrix")
    required_methods = {
        "ziping_pattern",
        "strength_support",
        "blind_school_workflow",
        "shensha_nayin",
        "tiaohou",
        "image_symbol_reading",
        "new_school_simplified",
        "data_validation_boundary",
    }
    observed_methods = {
        item.get("method")
        for item in method_matrix
        if isinstance(item, dict)
    } if isinstance(method_matrix, list) else set()
    return (
        isinstance(major_luck, list)
        and bool(major_luck)
        and isinstance(method_matrix, list)
        and required_methods.issubset(observed_methods)
    )


def _ziwei_profile_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if not {
        "ming_palace",
        "body_palace",
        "highlighted_palaces",
        "four_transformations",
        "life_focus",
        "triad_analysis",
        "transformation_analysis",
        "limit_activation_analysis",
        "method_matrix",
        "major_limits",
        "annual_activation",
    }.issubset(value):
        return False
    if not isinstance(value.get("highlighted_palaces"), list) or not value["highlighted_palaces"]:
        return False
    transformations = value.get("four_transformations")
    if not isinstance(transformations, dict) or set(transformations) != {"lu", "quan", "ke", "ji"}:
        return False
    if not isinstance(value.get("major_limits"), list) or not value["major_limits"]:
        return False
    if not isinstance(value.get("annual_activation"), list) or not value["annual_activation"]:
        return False
    return _ziwei_method_layers_ok(value)


def _qimen_profile_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "yin_yang",
        "ju_number",
        "duty",
        "useful_gods",
        "highlighted_palaces",
        "pattern_flags",
        "door_star_spirit_analysis",
        "stem_relation_analysis",
        "useful_god_analysis",
        "pattern_risk_analysis",
        "timing_activation_analysis",
        "method_matrix",
        "annual_timing",
    }
    if not required.issubset(value):
        return False
    duty = value.get("duty")
    if not isinstance(duty, dict) or not {"door", "door_palace", "star", "star_palace", "spirit"}.issubset(duty):
        return False
    useful = value.get("useful_gods")
    if not isinstance(useful, dict) or not {"career", "wealth", "relationship", "study", "health"}.issubset(useful):
        return False
    if not isinstance(value.get("highlighted_palaces"), list) or not value["highlighted_palaces"]:
        return False
    if not isinstance(value.get("pattern_flags"), list) or not value["pattern_flags"]:
        return False
    if not isinstance(value.get("annual_timing"), list) or not value["annual_timing"]:
        return False
    return _qimen_method_layers_ok(value)


def _astrology_profile_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "zodiac",
        "sun",
        "moon",
        "ascendant",
        "planets",
        "houses",
        "aspects",
        "annual_transits",
        "ephemeris_quality",
        "core_identity_analysis",
        "house_emphasis_analysis",
        "aspect_pattern_analysis",
        "transit_activation_analysis",
        "method_matrix",
    }
    if not required.issubset(value):
        return False
    if not isinstance(value.get("planets"), list) or len(value["planets"]) < 10:
        return False
    if not isinstance(value.get("houses"), list) or len(value["houses"]) != 12:
        return False
    if not isinstance(value.get("annual_transits"), list) or not value["annual_transits"]:
        return False
    return _astrology_method_layers_ok(value)


def _provider_summary_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if not {"status", "production_ready", "domains", "production_blockers", "action_plan", "boundary"}.issubset(value):
        return False
    domains = value.get("domains")
    if not isinstance(domains, dict):
        return False
    required_domains = {"bazi", "ziwei", "qimen", "astrology", "xuanze"}
    if set(domains) != required_domains:
        return False
    for key in required_domains:
        item = domains.get(key)
        if not isinstance(item, dict):
            return False
        required = {
            "domain",
            "provider",
            "provider_quality",
            "status",
            "contract_valid",
            "provider_provenance_valid",
            "provider_provenance_missing",
            "external_payload_receipt_valid",
            "external_payload_receipt_sha256",
            "production_ready",
            "replacement_boundary",
        }
        if not required.issubset(item) or item.get("domain") != key:
            return False
        if item.get("status") not in {"professional", "fallback"}:
            return False
        if not isinstance(item.get("contract_valid"), bool):
            return False
        if not isinstance(item.get("provider_provenance_valid"), bool):
            return False
        if not isinstance(item.get("provider_provenance_missing"), list):
            return False
        if not isinstance(item.get("external_payload_receipt_valid"), bool):
            return False
        if not isinstance(item.get("production_ready"), bool):
            return False
        if str(item.get("provider_quality", "")).startswith("external_"):
            receipt_sha = item.get("external_payload_receipt_sha256")
            if not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
                return False
            if item.get("external_payload_receipt_valid") is not True:
                return False
        if item.get("production_ready") and not item.get("contract_valid"):
            return False
        if item.get("production_ready") and not item.get("provider_provenance_valid"):
            return False
    blockers = value.get("production_blockers")
    if not isinstance(blockers, list) or not all(item in required_domains for item in blockers):
        return False
    action_plan = value.get("action_plan")
    if not isinstance(action_plan, list):
        return False
    action_domains = {item.get("domain") for item in action_plan if isinstance(item, dict)}
    if action_domains != set(blockers):
        return False
    for item in action_plan:
        if not isinstance(item, dict):
            return False
        required_action = {
            "domain",
            "status",
            "current_provider",
            "provider_quality",
            "reason",
            "env_var",
            "provenance_env_var",
            "certification_command_template",
            "production_readiness_command_template",
            "deployment_checklist",
        }
        if not required_action.issubset(item):
            return False
        if item.get("domain") not in blockers or item.get("status") not in {"professional", "fallback"}:
            return False
        if not isinstance(item.get("deployment_checklist"), list):
            return False
    return True


def _ziwei_deep_analysis_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    palaces = value.get("palaces")
    transformations = value.get("four_transformations")
    major_limits = value.get("major_limits")
    annual_activation = value.get("annual_activation")
    if not isinstance(palaces, list) or len(palaces) != 12:
        return False
    if not all(isinstance(item, dict) and {"name", "theme", "primary_stars"}.issubset(item) for item in palaces):
        return False
    if not isinstance(transformations, dict) or set(transformations) != {"lu", "quan", "ke", "ji"}:
        return False
    if not isinstance(major_limits, list) or len(major_limits) < 8:
        return False
    if not isinstance(annual_activation, list) or not annual_activation:
        return False
    if not bool(value.get("ming_palace")) or not bool(value.get("body_palace")):
        return False
    return _ziwei_method_layers_ok(value)


def _ziwei_method_layers_ok(value: dict[str, object]) -> bool:
    required_blocks = {
        "life_focus",
        "triad_analysis",
        "transformation_analysis",
        "limit_activation_analysis",
    }
    if not all(isinstance(value.get(key), dict) and value[key] for key in required_blocks):
        return False
    method_matrix = value.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        return False
    methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
    return {
        "ming_body_axis",
        "twelve_palace_theme",
        "triad_opposition",
        "four_transformations",
        "limit_annual_linkage",
    }.issubset(methods)


def _qimen_deep_analysis_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    palaces = value.get("palaces")
    useful_gods = value.get("useful_gods")
    duty = value.get("duty")
    pattern_flags = value.get("pattern_flags")
    annual_timing = value.get("annual_timing")
    if not isinstance(palaces, list) or len(palaces) != 9:
        return False
    if not all(
        isinstance(item, dict) and {"name", "door", "star", "spirit", "heaven_stem", "earth_stem"}.issubset(item)
        for item in palaces
    ):
        return False
    if not isinstance(useful_gods, dict) or not {"career", "wealth", "relationship", "study", "health"}.issubset(useful_gods):
        return False
    if not isinstance(duty, dict) or not {"door", "door_palace", "star", "star_palace", "spirit"}.issubset(duty):
        return False
    if not isinstance(pattern_flags, list) or not pattern_flags:
        return False
    if not isinstance(annual_timing, list) or not annual_timing:
        return False
    if not bool(value.get("yin_yang")) or not bool(value.get("ju_number")):
        return False
    return _qimen_method_layers_ok(value)


def _qimen_method_layers_ok(value: dict[str, object]) -> bool:
    required_blocks = {
        "door_star_spirit_analysis",
        "stem_relation_analysis",
        "useful_god_analysis",
        "pattern_risk_analysis",
        "timing_activation_analysis",
    }
    if not all(isinstance(value.get(key), dict) and value[key] for key in required_blocks):
        return False
    method_matrix = value.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        return False
    methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
    return {
        "door_star_spirit",
        "heaven_earth_stem",
        "useful_god_topic_mapping",
        "pattern_risk",
        "annual_timing_activation",
    }.issubset(methods)


def _astrology_deep_analysis_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    planets = value.get("planets")
    houses = value.get("houses")
    aspects = value.get("aspects")
    transits = value.get("annual_transits")
    if not isinstance(planets, list) or len(planets) < 10:
        return False
    if not all(isinstance(item, dict) and {"name", "sign", "degree", "house"}.issubset(item) for item in planets):
        return False
    if not isinstance(houses, list) or len(houses) != 12:
        return False
    if not all(isinstance(item, dict) and {"number", "cusp_sign", "ruler", "theme"}.issubset(item) for item in houses):
        return False
    if not isinstance(aspects, list):
        return False
    if not isinstance(transits, list) or not transits:
        return False
    if not bool(value.get("zodiac")):
        return False
    return _astrology_method_layers_ok(value)


def _astrology_method_layers_ok(value: dict[str, object]) -> bool:
    required_blocks = {
        "ephemeris_quality",
        "core_identity_analysis",
        "house_emphasis_analysis",
        "aspect_pattern_analysis",
        "transit_activation_analysis",
    }
    if not all(isinstance(value.get(key), dict) and value[key] for key in required_blocks):
        return False
    method_matrix = value.get("method_matrix")
    if not isinstance(method_matrix, list) or not method_matrix:
        return False
    methods = {item.get("method") for item in method_matrix if isinstance(item, dict)}
    return {
        "ephemeris_quality",
        "sun_moon_ascendant",
        "house_emphasis",
        "aspect_pattern",
        "transit_activation",
    }.issubset(methods)


def _topic_synthesis_ok(value: object) -> bool:
    required = {
        "finance",
        "official_career",
        "career",
        "study",
        "relationship",
        "friends",
        "leadership",
        "children_family",
    }
    if not isinstance(value, dict) or set(value) != required:
        return False
    for item in value.values():
        if not isinstance(item, dict):
            return False
        if not {
            "label",
            "headline",
            "annual_focus",
            "monthly_focus",
            "timing_evidence",
            "cross_agent_evidence",
            "evidence_summary",
            "risk_boundary",
        }.issubset(item):
            return False
        evidence = item.get("cross_agent_evidence")
        if not isinstance(evidence, list) or len(evidence) != 4:
            return False
        timing = item.get("timing_evidence")
        if not isinstance(timing, dict) or not {"annual", "monthly"}.issubset(timing):
            return False
        summary = item.get("evidence_summary")
        if not isinstance(summary, list) or len(summary) < 6:
            return False
    return True


def _rendered_reports_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    en = value.get("en")
    zh = value.get("zh")
    if (
        isinstance(en, str)
        and "Mingli five-agent report" in en
        and isinstance(zh, str)
        and "## 使用边界" in zh
        and "## 主题综合" in zh
        and "## 年度阶段摘要" in zh
    ):
        return True
    if isinstance(zh, str) and "## 年度阶段摘要" not in zh:
        return False
    return (
        isinstance(en, str)
        and "Mingli five-agent report" in en
        and isinstance(zh, str)
        and "## 主题综合" in zh
        and "## 使用边界" in zh
    )
