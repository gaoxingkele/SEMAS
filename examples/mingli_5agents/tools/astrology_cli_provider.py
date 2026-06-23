"""Optional JSON-CLI provider for professional Western astrology engines."""

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


@dataclass
class AstrologyJsonCliProvider:
    """Western astrology provider backed by an external JSON-speaking command.

    The command receives a normalized birth record and fallback chart on stdin.
    It should return a JSON object with fields such as `sun`, `moon`,
    `ascendant`, `planets`, `houses`, `aspects`, and `annual_transits`.
    """

    command: list[str]
    domain: str = "astrology"
    name: str = "astrology_json_cli"
    timeout_seconds: float = 10.0

    def build_chart(self, birth: dict[str, Any], fallback_chart: dict[str, Any]) -> dict[str, Any]:
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
                    "utc_offset",
                    "latitude",
                    "longitude",
                    "house_system",
                    "annual_start_year",
                    "annual_end_year",
                }
            },
            "fallback": {
                "sun": fallback_chart.get("sun"),
                "moon": fallback_chart.get("moon"),
                "ascendant": fallback_chart.get("ascendant"),
                "annual_theme": fallback_chart.get("annual_theme"),
            },
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
            raise RuntimeError(f"Astrology provider command failed: {completed.stderr.strip()}")
        raw = json.loads(completed.stdout)
        if not isinstance(raw, dict):
            raise ValueError("Astrology provider command must return a JSON object")
        receipt = provider_request_receipt(
            domain=self.domain,
            payload=payload,
            raw_stdout=completed.stdout,
            parsed_stdout=raw,
        )
        chart = _merge_astrology_payload(fallback_chart, raw)
        chart["provider"] = self.name
        chart["provider_quality"] = "astrology_json_cli"
        chart["raw_provider_output"] = raw
        chart["provider_request_receipt"] = receipt
        chart.setdefault("context", {}).setdefault("provider", fallback_chart.get("context", {}).get("provider"))
        chart["context"]["domain_provider"] = self.name
        chart["context"]["domain_provider_quality"] = "astrology_json_cli"
        chart["context"]["domain_provider_source"] = "json_cli"
        chart["context"]["provider_request_receipt"] = receipt
        return chart


def try_build_astrology_cli_provider() -> AstrologyJsonCliProvider | None:
    """Return a JSON-CLI astrology provider from environment configuration."""
    command = os.environ.get("SEMAS_ASTROLOGY_CLI")
    if not command:
        return None
    return AstrologyJsonCliProvider(command=_split_command(command))


def _merge_astrology_payload(fallback_chart: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    chart = dict(fallback_chart)
    for key in ("sun", "moon", "ascendant", "annual_theme", "seasonal_anchor", "sign_cycle"):
        if key in raw:
            chart[key] = raw[key]
    if "planets" in raw:
        chart["ephemeris_planets"] = raw["planets"]
    if "houses" in raw:
        chart["provider_houses"] = raw["houses"]
    if "aspects" in raw:
        chart["provider_aspects"] = raw["aspects"]
    if "annual_transits" in raw:
        chart["provider_annual_transits"] = raw["annual_transits"]
    if "ephemeris" in raw:
        chart["ephemeris"] = raw["ephemeris"]
    return chart


def _split_command(command: str) -> list[str]:
    try:
        import shlex

        return shlex.split(command, posix=os.name != "nt")
    except Exception:
        return [command]
