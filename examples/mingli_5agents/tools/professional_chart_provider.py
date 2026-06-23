"""Provider boundary for professional non-BaZi chart engines.

The built-in Zi Wei, Qi Men, and Western astrology helpers intentionally keep a
deterministic symbolic fallback. This module defines the adapter seam for
authoritative engines or externally supplied charts so downstream reports,
evaluators, and APIs do not need to change when a professional provider is
plugged in.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol

from examples.mingli_5agents.provider_request_receipt import BIRTH_PROFILE_FIELDS, birth_profile_sha256, stable_sha256


DOMAINS = ("ziwei", "qimen", "astrology")
REQUIRED_EXTERNAL_PROVENANCE_FIELDS = ("source", "version", "license_or_review")


class DomainChartProvider(Protocol):
    """Protocol implemented by professional chart providers."""

    domain: str
    name: str

    def build_chart(self, birth: dict[str, Any], fallback_chart: dict[str, Any]) -> dict[str, Any]:
        """Return a chart for one domain, optionally using fallback context."""
        raise NotImplementedError


@dataclass
class ExternalStructuredChartProvider:
    """Provider for externally supplied authoritative chart payloads.

    A birth record can include:

    {
      "professional_charts": {
        "ziwei": {"ming_palace": "...", "body_palace": "...", ...}
      }
    }

    The payload is overlaid on the fallback chart and marked as external. This
    lets tests, future UI integrations, or GitHub-derived engines inject
    verified outputs while preserving the report contract.
    """

    domain: str
    name: str = "external_structured"

    def build_chart(self, birth: dict[str, Any], fallback_chart: dict[str, Any]) -> dict[str, Any]:
        payload = _external_payload(birth, self.domain)
        if not payload:
            raise KeyError(f"No external professional chart for {self.domain}")
        chart = _deep_merge(fallback_chart, payload)
        chart["provider"] = self.name
        chart["provider_quality"] = f"external_{self.domain}"
        chart.setdefault("context", {}).setdefault("provider", fallback_chart.get("context", {}).get("provider"))
        chart["context"]["domain_provider"] = self.name
        chart["context"]["domain_provider_quality"] = f"external_{self.domain}"
        chart["context"]["domain_provider_source"] = payload.get("source", "user_supplied")
        chart["context"]["domain_provider_provenance"] = external_payload_provenance(payload)
        chart["context"]["external_payload_receipt"] = external_payload_receipt(self.domain, birth, payload)
        return chart


@dataclass
class DomainChartProviderRegistry:
    """In-process registry for one chart domain."""

    domain: str
    providers: dict[str, DomainChartProvider] = field(default_factory=dict)
    preferred_name: str | None = None

    def register(self, provider: DomainChartProvider, preferred: bool = False) -> None:
        if provider.domain != self.domain:
            raise ValueError(f"Provider domain {provider.domain} does not match registry {self.domain}")
        self.providers[provider.name] = provider
        if preferred:
            self.preferred_name = provider.name

    def get(self, name: str) -> DomainChartProvider:
        if name not in self.providers:
            raise KeyError(f"Unknown {self.domain} provider: {name}")
        return self.providers[name]

    def describe(self) -> dict[str, Any]:
        professional = [
            name
            for name in self.providers
            if name not in {"external_structured"}
        ]
        return {
            "domain": self.domain,
            "providers": sorted(self.providers),
            "default": self.preferred_name or "symbolic_scaffold",
            "installed_professional_backend": self.preferred_name,
            "professional_backends": sorted(professional),
            "external_injection_supported": "external_structured" in self.providers,
        }


REGISTRIES = {domain: DomainChartProviderRegistry(domain=domain) for domain in DOMAINS}
for _domain in DOMAINS:
    REGISTRIES[_domain].register(ExternalStructuredChartProvider(domain=_domain))

try:
    from examples.mingli_5agents.tools.swiss_ephemeris_provider import try_build_swiss_ephemeris_provider

    _swiss_provider = try_build_swiss_ephemeris_provider()
    if _swiss_provider is not None:
        REGISTRIES["astrology"].register(_swiss_provider, preferred=True)
except Exception:
    pass

try:
    from examples.mingli_5agents.tools.astrology_cli_provider import try_build_astrology_cli_provider

    _astrology_cli_provider = try_build_astrology_cli_provider()
    if _astrology_cli_provider is not None:
        REGISTRIES["astrology"].register(_astrology_cli_provider, preferred=True)
except Exception:
    pass

try:
    from examples.mingli_5agents.tools.kinqimen_provider import try_build_kinqimen_provider

    _kinqimen_provider = try_build_kinqimen_provider()
    if _kinqimen_provider is not None:
        REGISTRIES["qimen"].register(_kinqimen_provider, preferred=True)
except Exception:
    pass

try:
    from examples.mingli_5agents.tools.qimen_cli_provider import try_build_qimen_cli_provider

    _qimen_cli_provider = try_build_qimen_cli_provider()
    if _qimen_cli_provider is not None:
        REGISTRIES["qimen"].register(_qimen_cli_provider, preferred=True)
except Exception:
    pass

try:
    from examples.mingli_5agents.tools.ziwei_cli_provider import try_build_ziwei_cli_provider

    _ziwei_cli_provider = try_build_ziwei_cli_provider()
    if _ziwei_cli_provider is not None:
        REGISTRIES["ziwei"].register(_ziwei_cli_provider, preferred=True)
except Exception:
    pass


def apply_chart_provider(
    domain: str,
    birth: dict[str, Any],
    fallback_chart: dict[str, Any],
) -> dict[str, Any]:
    """Apply external or installed professional provider, otherwise mark fallback."""
    if _external_payload(birth, domain):
        return REGISTRIES[domain].get("external_structured").build_chart(birth, fallback_chart)
    registry = REGISTRIES[domain]
    if registry.preferred_name:
        return registry.get(registry.preferred_name).build_chart(birth, fallback_chart)
    fallback_chart.setdefault("provider", "symbolic_scaffold")
    fallback_chart.setdefault("provider_quality", "symbolic")
    fallback_chart.setdefault("context", {})["domain_provider"] = "symbolic_scaffold"
    fallback_chart["context"]["domain_provider_quality"] = "symbolic"
    return fallback_chart


def apply_external_chart_if_present(
    domain: str,
    birth: dict[str, Any],
    fallback_chart: dict[str, Any],
) -> dict[str, Any]:
    """Backward-compatible wrapper for provider application."""
    return apply_chart_provider(domain, birth, fallback_chart)


def describe_domain_chart_providers() -> dict[str, Any]:
    """Return registered domain provider capabilities for diagnostics."""
    return {domain: registry.describe() for domain, registry in REGISTRIES.items()}


def external_provider_present(birth: dict[str, Any], domain: str) -> bool:
    """Return whether a birth record contains an external chart for a domain."""
    return bool(_external_payload(birth, domain))


def external_payload_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    """Return machine-readable provenance status for request-scoped external payloads."""
    missing = [
        field
        for field in REQUIRED_EXTERNAL_PROVENANCE_FIELDS
        if not str(payload.get(field, "")).strip()
    ]
    return {
        "valid": not missing,
        "required_fields": list(REQUIRED_EXTERNAL_PROVENANCE_FIELDS),
        "missing_fields": missing,
        "source": payload.get("source"),
        "version": payload.get("version"),
        "license_or_review": payload.get("license_or_review"),
        "reviewed": bool(str(payload.get("license_or_review", "")).strip()),
    }


def external_payload_receipt(domain: str, birth: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return a stable receipt binding a request-scoped external payload to birth data."""
    provenance = external_payload_provenance(payload)
    birth_match = external_payload_birth_match(birth, payload)
    material = {
        "schema_version": "external-payload-receipt-v1",
        "domain": domain,
        "birth_profile_sha256": birth_profile_sha256(birth),
        "payload_sha256": stable_sha256(payload),
        "provenance_sha256": stable_sha256(provenance),
        "provenance_valid": provenance.get("valid") is True,
        "birth_match_status": birth_match["status"],
        "declared_birth_profile_sha256": birth_match["declared_birth_profile_sha256"],
        "declared_birth_fields": birth_match["declared_fields"],
        "birth_mismatch_fields": birth_match["mismatch_fields"],
        "source": provenance.get("source"),
        "version": provenance.get("version"),
        "license_or_review_sha256": hashlib.sha256(
            str(provenance.get("license_or_review", "")).encode("utf-8")
        ).hexdigest(),
    }
    return {
        **material,
        "sha256": stable_sha256(material),
    }


def external_payload_birth_match(birth: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Audit optional payload-declared birth data against the normalized request birth profile."""
    declared = payload.get("birth_profile")
    if not isinstance(declared, dict):
        declared = payload.get("birth")
    if not isinstance(declared, dict):
        return {
            "status": "not_declared",
            "declared_birth_profile_sha256": None,
            "declared_fields": [],
            "mismatch_fields": [],
        }
    declared_material = {field: declared.get(field) for field in BIRTH_PROFILE_FIELDS}
    declared_fields = [field for field in BIRTH_PROFILE_FIELDS if field in declared]
    mismatch_fields = [
        field
        for field in declared_fields
        if not _birth_value_matches(birth.get(field), declared.get(field))
    ]
    return {
        "status": "matched" if not mismatch_fields else "mismatch",
        "declared_birth_profile_sha256": stable_sha256(declared_material),
        "declared_fields": declared_fields,
        "mismatch_fields": mismatch_fields,
    }


def _external_payload(birth: dict[str, Any], domain: str) -> dict[str, Any]:
    charts = birth.get("professional_charts") or birth.get("external_charts") or {}
    payload = charts.get(domain, {}) if isinstance(charts, dict) else {}
    return payload if isinstance(payload, dict) else {}


def _birth_value_matches(left: Any, right: Any) -> bool:
    if left == right:
        return True
    if left is None or right is None:
        return left is right
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return str(left).strip() == str(right).strip()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
