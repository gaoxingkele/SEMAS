"""Deterministic BaZi chart helper for the mingli demo."""

from __future__ import annotations

from typing import Any

from examples.mingli_5agents.tools.bazi_deep_analysis import build_bazi_deep_analysis, ensure_bazi_method_layers
from examples.mingli_5agents.tools.calendar_core import build_chart_context
from examples.mingli_5agents.tools.professional_chart_provider import external_payload_provenance, external_payload_receipt


def build_bazi_chart(birth: dict) -> dict:
    """Build a reproducible symbolic BaZi chart from normalized birth input."""
    context = build_chart_context(birth)
    max_count = max(context["element_counts"].values())
    min_count = min(context["element_counts"].values())
    spread = max_count - min_count
    chart = {
        "context": context,
        "pillars": context["pillars"],
        "element_counts": context["element_counts"],
        "dominant_element": context["dominant_element"],
        "useful_element": context["useful_element"],
        "structure": "balanced" if spread <= 2 else "element-skewed",
        "seasonal_adjustment": f"{context['season']} season near {context['solar_term']}",
        "deep_analysis": build_bazi_deep_analysis(birth, context),
        "sources": ["bazi_ziping", "bazi_sanming", "bazi_shensha"],
    }
    return _apply_external_bazi_if_present(birth, chart)


def _apply_external_bazi_if_present(birth: dict[str, Any], fallback_chart: dict[str, Any]) -> dict[str, Any]:
    payload = _external_bazi_payload(birth)
    if not payload:
        return fallback_chart
    chart = _deep_merge(fallback_chart, payload)
    chart["provider"] = "external_structured"
    chart["provider_quality"] = "external_bazi"
    chart.setdefault("context", {})
    chart["context"]["provider"] = "external_structured"
    chart["context"]["provider_quality"] = "external_bazi"
    chart["context"]["provider_source"] = payload.get("source", "user_supplied")
    chart["context"]["provider_provenance"] = external_payload_provenance(payload)
    chart["context"]["external_payload_receipt"] = external_payload_receipt("bazi", birth, payload)
    if isinstance(chart.get("pillars"), dict):
        chart["context"]["pillars"] = chart["pillars"]
    if isinstance(chart.get("element_counts"), dict):
        chart["context"]["element_counts"] = chart["element_counts"]
    if chart.get("dominant_element"):
        chart["context"]["dominant_element"] = chart["dominant_element"]
    if chart.get("useful_element"):
        chart["context"]["useful_element"] = chart["useful_element"]
    if isinstance(chart.get("deep_analysis"), dict):
        chart["deep_analysis"].setdefault("provider", "external_structured")
        chart["deep_analysis"].setdefault(
            "caution",
            "External BaZi payload supplied by a caller; verify source and rule set before production use.",
        )
        chart["deep_analysis"] = ensure_bazi_method_layers(chart["deep_analysis"], chart["context"])
    return chart


def _external_bazi_payload(birth: dict[str, Any]) -> dict[str, Any]:
    charts = birth.get("professional_charts") or birth.get("external_charts") or {}
    payload = charts.get("bazi", {}) if isinstance(charts, dict) else {}
    return payload if isinstance(payload, dict) else {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
