"""Optional JSON-CLI provider for professional tongshu/xuanze engines."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from examples.mingli_5agents.provider_request_receipt import (
    attach_provider_request_identity,
    provider_request_receipt,
)
from examples.mingli_5agents.tools.auspicious_calendar import ensure_xuanze_method_layers
from examples.mingli_5agents.tools.professional_chart_provider import external_payload_provenance, external_payload_receipt


@dataclass
class XuanzeJsonCliProvider:
    """Auspicious-day provider backed by an external JSON-speaking command.

    The command receives normalized birth data plus a fallback auspicious-day
    table on stdin. It must return a JSON object with at least `rows`; optional
    `basis`, `summary`, and `caution` fields override fallback metadata.
    """

    command: list[str]
    domain: str = "xuanze"
    name: str = "xuanze_json_cli"
    timeout_seconds: float = 10.0

    def build_calendar(self, birth: dict[str, Any], fallback_calendar: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "birth": {
                key: value
                for key, value in birth.items()
                if key
                in {
                    "name",
                    "birth_date",
                    "birth_time",
                    "gender",
                    "birthplace",
                    "year",
                    "month",
                    "day",
                    "hour",
                    "minute",
                    "timezone_offset",
                    "latitude",
                    "longitude",
                }
            },
            "fallback": fallback_calendar,
        }
        payload = attach_provider_request_identity(self.domain, birth, payload)
        completed = subprocess.run(
            self.command,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Xuanze provider command failed: {completed.stderr.strip()}")
        raw = json.loads(completed.stdout)
        if not isinstance(raw, dict):
            raise ValueError("Xuanze provider command must return a JSON object")
        receipt = provider_request_receipt(
            domain=self.domain,
            payload=payload,
            raw_stdout=completed.stdout,
            parsed_stdout=raw,
        )
        calendar = _merge_xuanze_payload(fallback_calendar, raw)
        calendar["provider"] = self.name
        calendar["provider_quality"] = "xuanze_json_cli"
        calendar["raw_provider_output"] = raw
        calendar["provider_request_receipt"] = receipt
        calendar.setdefault("basis", {})
        calendar["basis"]["provider"] = self.name
        calendar["basis"]["provider_quality"] = "xuanze_json_cli"
        calendar["basis"]["provider_source"] = "json_cli"
        calendar["basis"]["provider_request_receipt"] = receipt
        return ensure_xuanze_method_layers(calendar)


def try_build_xuanze_cli_provider() -> XuanzeJsonCliProvider | None:
    """Return a JSON-CLI xuanze provider from environment configuration."""
    command = os.environ.get("SEMAS_XUANZE_CLI")
    if not command:
        return None
    return XuanzeJsonCliProvider(command=_split_command(command))


def apply_xuanze_provider(birth: dict[str, Any], fallback_calendar: dict[str, Any]) -> dict[str, Any]:
    """Apply externally supplied or configured xuanze provider if present."""
    external = _external_xuanze_payload(birth)
    if external:
        calendar = _merge_xuanze_payload(fallback_calendar, external)
        calendar["provider"] = "external_structured"
        calendar["provider_quality"] = "external_xuanze"
        calendar["raw_provider_output"] = external
        calendar.setdefault("basis", {})
        calendar["basis"]["provider"] = "external_structured"
        calendar["basis"]["provider_quality"] = "external_xuanze"
        calendar["basis"]["provider_source"] = external.get("source", "user_supplied")
        calendar["basis"]["provider_provenance"] = external_payload_provenance(external)
        calendar["basis"]["external_payload_receipt"] = external_payload_receipt("xuanze", birth, external)
        return ensure_xuanze_method_layers(calendar)
    provider = try_build_xuanze_cli_provider()
    if provider is None:
        return fallback_calendar
    return provider.build_calendar(birth, fallback_calendar)


def _merge_xuanze_payload(fallback_calendar: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    calendar = dict(fallback_calendar)
    if "rows" in raw:
        calendar["rows"] = raw["rows"]
    if "summary" in raw:
        calendar["summary"] = raw["summary"]
    if "basis" in raw and isinstance(raw["basis"], dict):
        basis = dict(fallback_calendar.get("basis", {}))
        basis.update(raw["basis"])
        calendar["basis"] = basis
    if "caution" in raw:
        calendar["caution"] = raw["caution"]
    if "range" in raw and isinstance(raw["range"], dict):
        calendar["range"] = raw["range"]
    elif isinstance(calendar.get("range"), dict) and isinstance(calendar.get("rows"), list):
        calendar["range"] = {**calendar["range"], "count": len(calendar["rows"])}
    return calendar


def _split_command(command: str) -> list[str]:
    try:
        import shlex

        return shlex.split(command, posix=os.name != "nt")
    except Exception:
        return [command]


def _external_xuanze_payload(birth: dict[str, Any]) -> dict[str, Any]:
    charts = birth.get("professional_charts") or birth.get("external_charts") or {}
    payload = charts.get("xuanze", {}) if isinstance(charts, dict) else {}
    return payload if isinstance(payload, dict) else {}
