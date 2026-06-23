"""Request receipts for JSON-CLI provider invocations."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from examples.mingli_5agents.provider_protocols import PROTOCOL_VERSION, provider_protocol_document


BIRTH_PROFILE_FIELDS = (
    "name",
    "birth_date",
    "birth_time",
    "gender",
    "birthplace",
    "birthplace_normalized",
    "birthplace_region",
    "latitude",
    "longitude",
    "timezone_offset",
    "geocoding_provider",
    "geocoding_quality",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "calendar_provider",
    "annual_start_year",
    "annual_end_year",
)


def provider_protocol_identity(domain: str) -> dict[str, str]:
    """Return the current protocol identity for one JSON-CLI provider domain."""
    protocol = provider_protocol_document()["domains"][domain]
    return {
        "version": str(protocol.get("protocol_version", PROTOCOL_VERSION)),
        "hash": str(protocol.get("protocol_hash", "")),
    }


def attach_provider_request_identity(domain: str, birth: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Attach protocol and request hashes to a JSON-CLI provider stdin payload."""
    enriched = dict(payload)
    birth_hash = birth_profile_sha256(birth)
    enriched["protocol"] = provider_protocol_identity(domain)
    enriched["request"] = {
        "birth_profile_sha256": birth_hash,
        "stdin_schema": "birth-fallback-json-cli",
    }
    return enriched


def provider_request_receipt(
    *,
    domain: str,
    payload: dict[str, Any],
    raw_stdout: str,
    parsed_stdout: Any,
) -> dict[str, Any]:
    """Return a stable receipt for one JSON-CLI provider request/response."""
    protocol = payload.get("protocol", {})
    request = payload.get("request", {})
    returned_protocol = parsed_stdout.get("protocol", {}) if isinstance(parsed_stdout, dict) else {}
    protocol_echo_matches = (
        isinstance(returned_protocol, dict)
        and returned_protocol.get("version") == protocol.get("version")
        and returned_protocol.get("hash") == protocol.get("hash")
    )
    material = {
        "schema_version": "provider-request-receipt-v1",
        "domain": domain,
        "protocol": protocol,
        "birth_profile_sha256": request.get("birth_profile_sha256"),
        "stdin_sha256": stable_sha256(payload),
        "stdout_sha256": hashlib.sha256(raw_stdout.encode("utf-8")).hexdigest(),
        "stdout_contract_type": type(parsed_stdout).__name__,
        "protocol_echo_matches": protocol_echo_matches,
    }
    return {
        **material,
        "sha256": stable_sha256(material),
    }


def birth_profile_sha256(birth: dict[str, Any]) -> str:
    material = {key: birth.get(key) for key in BIRTH_PROFILE_FIELDS}
    return stable_sha256(material)


def stable_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
