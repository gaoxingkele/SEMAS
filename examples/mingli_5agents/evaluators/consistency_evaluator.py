"""Internal consistency scoring for multi-agent mingli reports."""

from __future__ import annotations

from examples.mingli_5agents.knowledge_base import SOURCE_REGISTRY


def consistency_score(result: dict, expected: dict | None = None) -> float:
    """Score whether all specialist reports and voting artifacts are present."""
    specialists = result.get("specialists", {})
    required = {"bazi", "ziwei", "qimen", "astrology"}
    if set(specialists) != required:
        return 0.0
    sections_ok = all(_specialist_layers_ok(report) for report in specialists.values())
    votes_ok = bool(result.get("votes")) and bool(result.get("discussion"))
    conflicts = len(result.get("conflicts", []))
    penalty = min(0.3, conflicts * 0.1)
    return max(0.0, (1.0 if sections_ok and votes_ok else 0.4) - penalty)


def _specialist_layers_ok(report: dict) -> bool:
    required = {"macro", "micro", "yearly", "monthly", "uncertainty"}
    if not required.issubset(report):
        return False
    layers = report.get("layers")
    if not isinstance(layers, dict) or set(layers) != required:
        return False
    for key in required:
        item = layers.get(key)
        if not isinstance(item, dict):
            return False
        if item.get("level") != key:
            return False
        if not item.get("focus") or not item.get("text"):
            return False
        if str(item.get("text")) != str(report.get(key)):
            return False
        source_ids = item.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            return False
        if any(source_id not in SOURCE_REGISTRY for source_id in source_ids):
            return False
        if not isinstance(item.get("evidence_required"), bool):
            return False
        if not item.get("boundary_type"):
            return False
    return True
