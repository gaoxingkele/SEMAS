"""Shared required method surfaces for production contracts and reference charts."""

from __future__ import annotations

import hashlib
import json


REQUIRED_METHODS = {
    "bazi": {
        "ziping_pattern",
        "strength_support",
        "blind_school_workflow",
        "shensha_nayin",
        "tiaohou",
        "image_symbol_reading",
        "new_school_simplified",
        "data_validation_boundary",
    },
    "ziwei": {
        "ming_body_axis",
        "twelve_palace_theme",
        "triad_opposition",
        "four_transformations",
        "limit_annual_linkage",
    },
    "qimen": {
        "door_star_spirit",
        "heaven_earth_stem",
        "useful_god_topic_mapping",
        "pattern_risk",
        "annual_timing_activation",
    },
    "astrology": {
        "ephemeris_quality",
        "sun_moon_ascendant",
        "house_emphasis",
        "aspect_pattern",
        "transit_activation",
    },
    "xuanze": {
        "twelve_officer",
        "twenty_eight_mansion",
        "huangdao_rating",
        "recommended_hours",
        "risk_boundary",
        "provider_quality",
    },
}


def method_surface_receipt() -> dict[str, object]:
    """Return a stable receipt for the shared required-method surface."""
    material = {
        "schema_version": "method-surface-v1",
        "domains": {domain: sorted(methods) for domain, methods in sorted(REQUIRED_METHODS.items())},
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }
