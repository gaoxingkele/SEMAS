"""Optional JSON-CLI provider for professional Qi Men Dun Jia engines."""

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
class QimenJsonCliProvider:
    """Qi Men provider backed by an external JSON-speaking command.

    The command receives a normalized birth record and fallback chart on stdin.
    It should return a JSON object with fields such as `duty_door`,
    `duty_star`, `spirit`, `pattern`, and optionally palace-level `door`,
    `star`, and `spirit` maps.
    """

    command: list[str]
    domain: str = "qimen"
    name: str = "qimen_json_cli"
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
                    "qimen_option",
                }
            },
            "fallback": {
                "duty_door": fallback_chart.get("duty_door"),
                "duty_star": fallback_chart.get("duty_star"),
                "spirit": fallback_chart.get("spirit"),
                "pattern": fallback_chart.get("pattern"),
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
            raise RuntimeError(f"Qi Men provider command failed: {completed.stderr.strip()}")
        raw = json.loads(completed.stdout)
        if not isinstance(raw, dict):
            raise ValueError("Qi Men provider command must return a JSON object")
        receipt = provider_request_receipt(
            domain=self.domain,
            payload=payload,
            raw_stdout=completed.stdout,
            parsed_stdout=raw,
        )
        chart = _merge_qimen_payload(fallback_chart, raw)
        chart["provider"] = self.name
        chart["provider_quality"] = "qimen_json_cli"
        chart["raw_provider_output"] = raw
        chart["provider_request_receipt"] = receipt
        chart.setdefault("context", {}).setdefault("provider", fallback_chart.get("context", {}).get("provider"))
        chart["context"]["domain_provider"] = self.name
        chart["context"]["domain_provider_quality"] = "qimen_json_cli"
        chart["context"]["domain_provider_source"] = "json_cli"
        chart["context"]["provider_request_receipt"] = receipt
        return chart


def try_build_qimen_cli_provider() -> QimenJsonCliProvider | None:
    """Return a JSON-CLI Qi Men provider from environment configuration."""
    command = os.environ.get("SEMAS_QIMEN_CLI")
    if not command:
        return None
    return QimenJsonCliProvider(command=_split_command(command))


def _merge_qimen_payload(fallback_chart: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    chart = dict(fallback_chart)
    for key in (
        "duty_door",
        "duty_star",
        "spirit",
        "pattern",
        "door_cycle",
        "star_cycle",
        "spirit_cycle",
        "time_anchor",
    ):
        if key in raw:
            chart[key] = raw[key]
    for key in ("door", "star", "spirit_map", "palaces", "annual_timing", "useful_gods"):
        if key in raw:
            chart[f"provider_{key}"] = raw[key]
    return chart


def _split_command(command: str) -> list[str]:
    try:
        import shlex

        return shlex.split(command, posix=os.name != "nt")
    except Exception:
        return [command]
