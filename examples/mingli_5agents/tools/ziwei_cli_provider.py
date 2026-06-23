"""Optional JSON-CLI provider for professional Zi Wei Dou Shu engines."""

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
class ZiweiJsonCliProvider:
    """Zi Wei provider backed by an external JSON-speaking command.

    The command receives a normalized birth record as JSON on stdin and must
    return a JSON object with fields such as `ming_palace`, `body_palace`,
    `major_stars`, `transformations`, and optionally `palaces`.
    """

    command: list[str]
    domain: str = "ziwei"
    name: str = "ziwei_json_cli"
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
                    "latitude",
                    "longitude",
                }
            },
            "fallback": {
                "ming_palace": fallback_chart.get("ming_palace"),
                "body_palace": fallback_chart.get("body_palace"),
                "major_stars": fallback_chart.get("major_stars"),
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
            raise RuntimeError(f"Zi Wei provider command failed: {completed.stderr.strip()}")
        raw = json.loads(completed.stdout)
        if not isinstance(raw, dict):
            raise ValueError("Zi Wei provider command must return a JSON object")
        receipt = provider_request_receipt(
            domain=self.domain,
            payload=payload,
            raw_stdout=completed.stdout,
            parsed_stdout=raw,
        )
        chart = _merge_ziwei_payload(fallback_chart, raw)
        chart["provider"] = self.name
        chart["provider_quality"] = "ziwei_json_cli"
        chart["raw_provider_output"] = raw
        chart["provider_request_receipt"] = receipt
        chart.setdefault("context", {}).setdefault("provider", fallback_chart.get("context", {}).get("provider"))
        chart["context"]["domain_provider"] = self.name
        chart["context"]["domain_provider_quality"] = "ziwei_json_cli"
        chart["context"]["domain_provider_source"] = "json_cli"
        chart["context"]["provider_request_receipt"] = receipt
        return chart


def try_build_ziwei_cli_provider() -> ZiweiJsonCliProvider | None:
    """Return a JSON-CLI Zi Wei provider from environment configuration."""
    command = os.environ.get("SEMAS_ZIWEI_CLI")
    if not command:
        return None
    return ZiweiJsonCliProvider(command=_split_command(command))


def _merge_ziwei_payload(fallback_chart: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    chart = dict(fallback_chart)
    for key in (
        "ming_palace",
        "body_palace",
        "major_stars",
        "transformations",
        "palace_order",
        "star_cycle",
        "seasonal_anchor",
    ):
        if key in raw:
            chart[key] = raw[key]
    if "palaces" in raw:
        chart["provider_palaces"] = raw["palaces"]
    if "major_limits" in raw:
        chart["provider_major_limits"] = raw["major_limits"]
    if "annual_activation" in raw:
        chart["provider_annual_activation"] = raw["annual_activation"]
    return chart


def _split_command(command: str) -> list[str]:
    try:
        import shlex

        return shlex.split(command, posix=os.name != "nt")
    except Exception:
        return [command]
