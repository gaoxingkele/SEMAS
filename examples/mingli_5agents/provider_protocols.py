"""Machine-readable JSON-CLI provider protocol descriptions."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from examples.mingli_5agents.method_surface import REQUIRED_METHODS
from examples.mingli_5agents.provider_contracts import raw_json_cli_contract


PROTOCOL_VERSION = "json-cli-v1"
REQUIRED_PROVIDER_PROVENANCE_FIELDS = ["provider", "version", "source", "license_or_review"]

BIRTH_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": ["birth"],
    "properties": {
        "birth": {
            "type": "object",
            "required": ["name", "birth_date", "birth_time", "gender", "birthplace"],
            "properties": {
                "name": {"type": "string"},
                "birth_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "birth_time": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
                "gender": {"type": "string"},
                "birthplace": {"type": "string"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "integer"},
                "hour": {"type": "integer"},
                "minute": {"type": "integer"},
                "timezone_offset": {"type": ["number", "string"]},
                "utc_offset": {"type": ["number", "string"]},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
        },
        "protocol": {
            "type": "object",
            "required": ["version", "hash"],
            "properties": {
                "version": {"type": "string"},
                "hash": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
            },
            "description": "Runtime protocol identity supplied by the live smoke/certification check; providers must echo it in stdout.",
        },
        "fallback": {"type": "object"},
    },
}

SAMPLE_STDIN = {
    "birth": {
        "name": "protocol_fixture",
        "birth_date": "1990-04-12",
        "birth_time": "09:20",
        "gender": "unspecified",
        "birthplace": "Hangzhou",
        "year": 1990,
        "month": 4,
        "day": 12,
        "hour": 9,
        "minute": 20,
        "timezone_offset": 8,
        "latitude": 30.2741,
        "longitude": 120.1551,
    },
    "protocol": {
        "version": PROTOCOL_VERSION,
        "hash": "0" * 64,
    },
    "fallback": {},
}

ZIWEI_PALACE_NAMES = [
    "Ming",
    "Siblings",
    "Spouse",
    "Children",
    "Wealth",
    "Health",
    "Travel",
    "Friends",
    "Career",
    "Property",
    "Fortune",
    "Parents",
]

QIMEN_PALACE_NAMES = ["Kan", "Kun", "Zhen", "Xun", "Center", "Qian", "Dui", "Gen", "Li"]

ASTROLOGY_PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
ASTROLOGY_SIGNS = [
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

SAMPLE_ZIWEI_STDOUT = {
    "ming_palace": "Career",
    "body_palace": "Wealth",
    "major_stars": ["Ziwei", "Wuqu"],
    "transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
    "calculation_basis": {
        "provider": "sample ziwei provider",
        "rule_set": "sample_ziwei_rules",
        "rule_set_version": "fixture-1.0",
        "rule_source": "sample reviewed protocol fixture",
        "rule_source_sha256": "0" * 64,
        "license_or_review": "sample reviewed protocol fixture",
        "calculation_scope": "twelve palaces, major stars, sihua, major limits, annual activation",
    },
    "palaces": [
        {
            "index": index,
            "name": name,
            "theme": f"{name} sample theme",
            "primary_stars": ["Ziwei"] if index == 0 else ["Tianji"],
            "auxiliary_stars": ["Tiankui"],
            "markers": ["ming"] if name == "Career" else [],
        }
        for index, name in enumerate(ZIWEI_PALACE_NAMES)
    ],
    "major_limits": [{"start_age": 0, "end_age": 9, "palace": "Career", "theme": "foundation"}],
    "annual_activation": [{"year": 2026, "palace": "Career", "theme": "work visibility"}],
}

SAMPLE_QIMEN_STDOUT = {
    "duty_door": "Rest",
    "duty_star": "Tianfu",
    "spirit": "Nine Earth",
    "pattern": "sample qimen protocol payload",
    "calculation_basis": {
        "provider": "sample qimen provider",
        "rule_set": "sample_qimen_rules",
        "rule_set_version": "fixture-1.0",
        "rule_source": "sample reviewed protocol fixture",
        "rule_source_sha256": "0" * 64,
        "license_or_review": "sample reviewed protocol fixture",
        "calculation_scope": "nine palaces, duty door, duty star, spirits, useful gods, annual timing",
    },
    "palaces": [
        {
            "number": index + 1,
            "name": name,
            "direction": "North",
            "element": "Water",
            "door": "Rest",
            "star": "Tianfu",
            "spirit": "Nine Earth",
            "heaven_stem": "Jia",
            "earth_stem": "Yi",
            "judgment": "sample",
        }
        for index, name in enumerate(QIMEN_PALACE_NAMES)
    ],
    "useful_gods": {
        key: {"palace": "Kan", "judgment": "sample"}
        for key in ["career", "wealth", "relationship", "study", "health"]
    },
    "annual_timing": [{"year": 2026, "palace": "Kan", "theme": "planning"}],
}

SAMPLE_ASTROLOGY_STDOUT = {
    "sun": "Aries",
    "moon": "Libra",
    "ascendant": "Virgo",
    "planets": [
        {
            "name": name,
            "sign": ASTROLOGY_SIGNS[index % len(ASTROLOGY_SIGNS)],
            "degree": float(index),
            "absolute_degree": float(index * 30),
            "house": index % 12 + 1,
        }
        for index, name in enumerate(ASTROLOGY_PLANETS)
    ],
    "houses": [
        {
            "number": index + 1,
            "cusp_sign": ASTROLOGY_SIGNS[index],
            "ruler": "Mercury",
            "theme": f"house {index + 1} sample theme",
        }
        for index in range(12)
    ],
    "annual_transits": [{"year": 2026, "planet": "Jupiter", "aspect": "trine", "theme": "growth"}],
    "ephemeris": {
        "source": "sample_ephemeris_provider",
        "zodiac": "tropical",
        "house_system": "Placidus",
        "time_scale": "UT",
        "calculation_time": {"julian_day_ut": 2448000.888889, "iso_utc": "1990-04-12T01:20:00Z"},
        "data_source": "sample provider fixture",
        "license_or_review": "sample reviewed protocol fixture",
    },
}

SAMPLE_XUANZE_STDOUT = {
    "range": {"start_date": "2026-06-21", "end_date": "2026-06-21", "count": 1},
    "basis": {
        "provider": "sample tongshu provider",
        "provider_quality": "sample_verified_fixture",
        "rule_set": "sample_tongshu_rules",
        "rule_table_source": "sample reviewed protocol fixture",
        "rule_table_version": "fixture-1.0",
        "rule_table_sha256": "0" * 64,
        "license_or_review": "sample reviewed protocol fixture",
        "calculation_scope": "twelve officers, twenty-eight mansions, huangdao rating, recommended hours",
    },
    "rows": [
        {
            "date": "2026-06-21",
            "weekday": "Sunday",
            "ganzhi": "JiaZi",
            "solar_term": "Grain in Ear",
            "twelve_officer": "Hold",
            "twenty_eight_mansion": "Star",
            "huangdao": True,
            "rating": "favorable",
            "suitable": ["planning"],
            "avoid": ["conflict"],
            "recommended_hours": [{"hour": "09:00-11:00", "rating": "favorable"}],
            "risk_notes": ["sample only"],
        }
    ],
    "summary": {"favorable_dates": ["2026-06-21"], "cautious_dates": [], "best_date": "2026-06-21"},
}


def provider_protocol_document() -> dict[str, Any]:
    """Return provider integration contracts for external engine authors."""
    domains = {
        "ziwei": {
            "env_var": "SEMAS_ZIWEI_CLI",
            "provenance_env_var": "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
            "example": "python examples/mingli_5agents/providers/ziwei_json_cli_example.py",
            "production_requirements": _production_requirements("SEMAS_ZIWEI_PROVIDER_PROVENANCE"),
            **_method_surface_fields("ziwei"),
            **_deployment_fields("ziwei", "SEMAS_ZIWEI_CLI", "SEMAS_ZIWEI_PROVIDER_PROVENANCE"),
            "stdin_schema": BIRTH_PAYLOAD_SCHEMA,
            "sample_stdin": SAMPLE_STDIN,
            "sample_stdout": SAMPLE_ZIWEI_STDOUT,
            "sample_stdout_contract": raw_json_cli_contract("ziwei", SAMPLE_ZIWEI_STDOUT),
            "stdout_schema": _ziwei_stdout_schema(),
        },
        "qimen": {
            "env_var": "SEMAS_QIMEN_CLI",
            "provenance_env_var": "SEMAS_QIMEN_PROVIDER_PROVENANCE",
            "example": "python examples/mingli_5agents/providers/qimen_json_cli_example.py",
            "production_requirements": _production_requirements("SEMAS_QIMEN_PROVIDER_PROVENANCE"),
            **_method_surface_fields("qimen"),
            **_deployment_fields("qimen", "SEMAS_QIMEN_CLI", "SEMAS_QIMEN_PROVIDER_PROVENANCE"),
            "stdin_schema": BIRTH_PAYLOAD_SCHEMA,
            "sample_stdin": SAMPLE_STDIN,
            "sample_stdout": SAMPLE_QIMEN_STDOUT,
            "sample_stdout_contract": raw_json_cli_contract("qimen", SAMPLE_QIMEN_STDOUT),
            "stdout_schema": _qimen_stdout_schema(),
        },
        "astrology": {
            "env_var": "SEMAS_ASTROLOGY_CLI",
            "provenance_env_var": "SEMAS_ASTROLOGY_PROVIDER_PROVENANCE",
            "example": "python examples/mingli_5agents/providers/astrology_json_cli_example.py",
            "production_requirements": _production_requirements("SEMAS_ASTROLOGY_PROVIDER_PROVENANCE"),
            **_method_surface_fields("astrology"),
            **_deployment_fields("astrology", "SEMAS_ASTROLOGY_CLI", "SEMAS_ASTROLOGY_PROVIDER_PROVENANCE"),
            "stdin_schema": BIRTH_PAYLOAD_SCHEMA,
            "sample_stdin": SAMPLE_STDIN,
            "sample_stdout": SAMPLE_ASTROLOGY_STDOUT,
            "sample_stdout_contract": raw_json_cli_contract("astrology", SAMPLE_ASTROLOGY_STDOUT),
            "stdout_schema": _astrology_stdout_schema(),
        },
        "xuanze": {
            "env_var": "SEMAS_XUANZE_CLI",
            "provenance_env_var": "SEMAS_XUANZE_PROVIDER_PROVENANCE",
            "example": "python examples/mingli_5agents/providers/xuanze_json_cli_example.py",
            "production_requirements": _production_requirements("SEMAS_XUANZE_PROVIDER_PROVENANCE"),
            **_method_surface_fields("xuanze"),
            **_deployment_fields("xuanze", "SEMAS_XUANZE_CLI", "SEMAS_XUANZE_PROVIDER_PROVENANCE"),
            "stdin_schema": BIRTH_PAYLOAD_SCHEMA,
            "sample_stdin": SAMPLE_STDIN,
            "sample_stdout": SAMPLE_XUANZE_STDOUT,
            "sample_stdout_contract": raw_json_cli_contract("xuanze", SAMPLE_XUANZE_STDOUT),
            "stdout_schema": _xuanze_stdout_schema(),
        },
    }
    for domain, protocol in domains.items():
        protocol["protocol_version"] = PROTOCOL_VERSION
        protocol["protocol_hash"] = _stable_hash(
            {
                "domain": domain,
                "protocol_version": PROTOCOL_VERSION,
                "protocol": protocol,
            }
        )
    document = {
        "protocol_version": PROTOCOL_VERSION,
        "transport": "JSON object on stdin, JSON object on stdout, non-zero exit code signals provider failure.",
        "timeout_seconds": 10,
        "live_check": "providers --live and GET /providers?live=1 validate stdout against these output contracts.",
        "domains": domains,
    }
    document["protocol_hash"] = _stable_hash(
        {
            "protocol_version": document["protocol_version"],
            "transport": document["transport"],
            "timeout_seconds": document["timeout_seconds"],
            "live_check": document["live_check"],
            "domains": document["domains"],
        }
    )
    return document


def provider_protocol_receipt(document: dict[str, Any], *, repo: str, domain: str | None = None) -> dict[str, Any]:
    """Return a stable receipt for the provider protocol contract document."""
    domains = document.get("domains", {})
    if not isinstance(domains, dict):
        domains = {}
    material = {
        "schema_version": "provider-protocols-receipt-v1",
        "repo": repo,
        "domain": domain,
        "protocol_version": document.get("protocol_version"),
        "protocol_hash": document.get("protocol_hash"),
        "domain_count": len(domains),
        "domain_protocol_hashes": {
            name: protocol.get("protocol_hash")
            for name, protocol in sorted(domains.items())
            if isinstance(protocol, dict)
        },
        "sample_stdout_contracts_valid": all(
            isinstance(protocol, dict) and protocol.get("sample_stdout_contract", {}).get("valid") is True
            for protocol in domains.values()
        )
        if domains
        else False,
        "protocol_document_sha256": _stable_hash({"provider_protocols": document}),
    }
    return {
        "schema_version": "provider-protocols-receipt-v1",
        "sha256": _stable_hash(material),
        "material": material,
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _production_requirements(provenance_env_var: str) -> list[str]:
    return [
        "The command must be an independently reviewed provider, not a bundled *_json_cli_example.py protocol fixture.",
        (
            f"{provenance_env_var} must be JSON or semicolon key/value text containing "
            "provider, version, source, and license_or_review."
        ),
        "providers --profile production --live must pass the stdout contract smoke test.",
        "The provider stdout must echo the stdin protocol.version and protocol.hash under protocol.version/protocol.hash.",
        "The normalized provider contract must cover required_method_surface before the provider can be certified for release.",
        "Astrology providers must disclose ephemeris source, zodiac, house system, time scale, calculation time, data source, and license/review status in stdout.ephemeris.",
        "Xuanze providers must disclose rule-table source, version, hash or receipt hash, calculation scope, and license/review status in stdout.basis.",
        "Ziwei and Qimen providers must disclose rule source, rule-set version, hash or receipt hash, calculation scope, and license/review status in stdout.calculation_basis.",
    ]


def _method_surface_fields(domain: str) -> dict[str, Any]:
    required = sorted(REQUIRED_METHODS[domain])
    return {
        "required_method_surface": required,
        "normalized_contract_requirement": (
            "After provider output is merged into the framework chart/calendar, chart_contract(domain, normalized) "
            "must pass with every required_method_surface item present in method_matrix."
        ),
    }


def _deployment_fields(domain: str, env_var: str, provenance_env_var: str) -> dict[str, Any]:
    return {
        "required_provenance_fields": list(REQUIRED_PROVIDER_PROVENANCE_FIELDS),
        "certification_command_template": (
            "python -m examples.mingli_5agents.cli --repo <repo> "
            f"certify-provider {domain} --command \"<provider-command>\" "
            "--provenance \"provider=<provider-name>; version=<provider-version>; "
            "source=<review-source>; license_or_review=<license-or-review>\" --record"
        ),
        "drift_command_template": (
            f"python -m examples.mingli_5agents.cli --repo <repo> provider-drift --domain {domain}"
        ),
        "production_readiness_command_template": (
            "python -m examples.mingli_5agents.cli --repo <repo> "
            "production-readiness --manifest <manifest.json> --live"
        ),
        "deployment_checklist": [
            f"Implement a JSON-CLI provider that reads the {domain} stdin schema and returns the stdout schema.",
            f"Verify normalized output covers the {domain} required_method_surface before certification.",
            f"Set {env_var} to the reviewed provider command.",
            f"Set {provenance_env_var} with provider, version, source, and license_or_review.",
            "Run providers --profile production --live and fix stdout-contract failures.",
            f"Run certify-provider {domain} --record to write a provider certification ledger receipt.",
            f"Run provider-drift --domain {domain} after deployment and before release.",
        ],
        "bundled_example_policy": (
            "Bundled *_json_cli_example.py scripts are protocol fixtures for smoke tests and cannot certify production providers."
        ),
    }


def _ziwei_stdout_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "ming_palace",
            "body_palace",
            "transformations",
            "palaces",
            "major_limits",
            "annual_activation",
            "calculation_basis",
        ],
        "properties": {
            "ming_palace": {"type": "string"},
            "body_palace": {"type": "string"},
            "major_stars": {"type": "array", "items": {"type": "string"}},
            "transformations": {
                "type": "object",
                "required": ["lu", "quan", "ke", "ji"],
                "properties": {key: {"type": "string"} for key in ("lu", "quan", "ke", "ji")},
            },
            "palaces": {
                "type": "array",
                "minItems": 12,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "required": ["name", "theme", "primary_stars"],
                    "properties": {
                        "index": {"type": "integer"},
                        "name": {"type": "string"},
                        "theme": {"type": "string"},
                        "primary_stars": {"type": "array", "items": {"type": "string"}},
                        "auxiliary_stars": {"type": "array", "items": {"type": "string"}},
                        "markers": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "major_limits": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            "annual_activation": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            "calculation_basis": _calculation_basis_schema(),
        },
    }


def _qimen_stdout_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "duty_door",
            "duty_star",
            "spirit",
            "palaces",
            "useful_gods",
            "annual_timing",
            "calculation_basis",
        ],
        "properties": {
            "duty_door": {"type": "string"},
            "duty_star": {"type": "string"},
            "spirit": {"type": "string"},
            "pattern": {"type": "string"},
            "palaces": {
                "type": "array",
                "minItems": 9,
                "maxItems": 9,
                "items": {
                    "type": "object",
                    "required": ["name", "door", "star", "spirit", "heaven_stem", "earth_stem"],
                    "properties": {
                        "number": {"type": "integer"},
                        "name": {"type": "string"},
                        "direction": {"type": "string"},
                        "element": {"type": "string"},
                        "door": {"type": "string"},
                        "star": {"type": "string"},
                        "spirit": {"type": "string"},
                        "heaven_stem": {"type": "string"},
                        "earth_stem": {"type": "string"},
                        "judgment": {"type": "string"},
                    },
                },
            },
            "useful_gods": {
                "type": "object",
                "required": ["career", "wealth", "relationship", "study", "health"],
                "additionalProperties": {"type": "object"},
            },
            "annual_timing": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            "calculation_basis": _calculation_basis_schema(),
        },
    }


def _calculation_basis_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "provider",
            "rule_set",
            "rule_set_version",
            "rule_source",
            "license_or_review",
            "calculation_scope",
        ],
        "properties": {
            "provider": {"type": "string"},
            "rule_set": {"type": "string"},
            "rule_set_version": {"type": "string"},
            "rule_source": {"type": "string"},
            "rule_source_sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
            "rule_receipt_sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
            "license_or_review": {"type": "string"},
            "calculation_scope": {"type": "string"},
        },
        "description": "At least one of rule_source_sha256 or rule_receipt_sha256 must be present for raw contract validity.",
    }


def _astrology_stdout_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["sun", "moon", "ascendant", "planets", "houses", "annual_transits", "ephemeris"],
        "properties": {
            "sun": {"type": "string"},
            "moon": {"type": "string"},
            "ascendant": {"type": "string"},
            "planets": {
                "type": "array",
                "minItems": 10,
                "items": {
                    "type": "object",
                    "required": ["name", "sign", "degree", "absolute_degree", "house"],
                    "properties": {
                        "name": {"type": "string"},
                        "sign": {"type": "string"},
                        "degree": {"type": "number"},
                        "absolute_degree": {"type": "number"},
                        "house": {"type": "integer"},
                    },
                },
            },
            "houses": {
                "type": "array",
                "minItems": 12,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "required": ["number", "cusp_sign", "ruler", "theme"],
                    "properties": {
                        "number": {"type": "integer"},
                        "cusp_sign": {"type": "string"},
                        "ruler": {"type": "string"},
                        "theme": {"type": "string"},
                    },
                },
            },
            "annual_transits": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            "ephemeris": {
                "type": "object",
                "required": [
                    "source",
                    "zodiac",
                    "house_system",
                    "time_scale",
                    "calculation_time",
                    "data_source",
                    "license_or_review",
                ],
                "properties": {
                    "source": {"type": "string"},
                    "zodiac": {"type": "string"},
                    "house_system": {"type": "string"},
                    "time_scale": {"type": "string"},
                    "calculation_time": {
                        "type": "object",
                        "properties": {
                            "julian_day_ut": {"type": "number"},
                            "iso_utc": {"type": "string"},
                        },
                    },
                    "data_source": {"type": "string"},
                    "license_or_review": {"type": "string"},
                },
            },
        },
    }


def _xuanze_stdout_schema() -> dict[str, Any]:
    row_properties = {
        "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "weekday": {"type": "string"},
        "ganzhi": {"type": "string"},
        "solar_term": {"type": "string"},
        "twelve_officer": {"type": "string"},
        "twenty_eight_mansion": {"type": "string"},
        "huangdao": {"type": "boolean"},
        "rating": {"type": "string", "enum": ["favorable", "mixed", "cautious"]},
        "suitable": {"type": "array", "items": {"type": "string"}},
        "avoid": {"type": "array", "items": {"type": "string"}},
        "recommended_hours": {"type": "array", "items": {"type": "object"}},
        "risk_notes": {"type": "array", "items": {"type": "string"}},
    }
    return {
        "type": "object",
        "required": ["basis", "rows", "summary"],
        "properties": {
            "range": {"type": "object"},
            "basis": {
                "type": "object",
                "required": [
                    "provider",
                    "provider_quality",
                    "rule_set",
                    "rule_table_source",
                    "rule_table_version",
                    "license_or_review",
                    "calculation_scope",
                ],
                "properties": {
                    "provider": {"type": "string"},
                    "provider_quality": {"type": "string"},
                    "calendar": {"type": "string"},
                    "rule_set": {"type": "string"},
                    "rule_table_source": {"type": "string"},
                    "rule_table_version": {"type": "string"},
                    "rule_table_sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
                    "rule_table_receipt_sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
                    "license_or_review": {"type": "string"},
                    "calculation_scope": {"type": "string"},
                },
            },
            "rows": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": list(row_properties),
                    "properties": row_properties,
                },
            },
            "summary": {
                "type": "object",
                "required": ["favorable_dates"],
                "properties": {
                    "favorable_dates": {"type": "array", "items": {"type": "string"}},
                    "cautious_dates": {"type": "array", "items": {"type": "string"}},
                    "best_date": {"type": ["string", "null"]},
                },
            },
        },
    }
