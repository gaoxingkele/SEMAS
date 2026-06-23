"""Citation coverage scoring for symbolic classical-source labels."""

from __future__ import annotations

from examples.mingli_5agents.knowledge_base import SOURCE_REGISTRY


REQUIRED_TRADITIONS = {"bazi", "ziwei", "qimen", "astrology"}


def _source_ids(report: dict) -> list[str]:
    sources = report.get("sources", [])
    ids = []
    for source in sources:
        if isinstance(source, str):
            ids.append(source)
        elif isinstance(source, dict) and source.get("source_id"):
            ids.append(source["source_id"])
    return ids


def _layer_source_ids(report: dict) -> list[str]:
    layers = report.get("layers", {})
    if not isinstance(layers, dict):
        return []
    ids = []
    for layer in layers.values():
        if not isinstance(layer, dict):
            continue
        for source_id in layer.get("source_ids", []):
            if isinstance(source_id, str):
                ids.append(source_id)
    return ids


def citation_score(result: dict, expected: dict | None = None) -> float:
    """Score registry-backed source coverage across specialist reports."""
    reports = result.get("specialists", {}).values()
    if not reports:
        return 0.0

    valid_reports = 0
    covered_traditions = set()
    source_count = 0
    for report in reports:
        ids = _source_ids(report)
        layer_ids = _layer_source_ids(report)
        if not ids:
            continue
        if not layer_ids or any(source_id not in ids for source_id in layer_ids):
            continue
        source_count += len(ids)
        all_ids = ids + layer_ids
        valid_ids = [source_id for source_id in all_ids if source_id in SOURCE_REGISTRY]
        if len(valid_ids) == len(all_ids):
            valid_reports += 1
            covered_traditions.update(SOURCE_REGISTRY[source_id].tradition for source_id in valid_ids)

    report_score = valid_reports / len(list(result.get("specialists", {}))) if result.get("specialists") else 0.0
    tradition_score = len(covered_traditions & REQUIRED_TRADITIONS) / len(REQUIRED_TRADITIONS)
    review = result.get("source_review", {})
    review_score = (
        1.0
        if review.get("status") == "pass"
        and review.get("unknown_sources") == []
        and review.get("missing_evidence", []) == []
        else 0.0
    )
    density_score = min(1.0, source_count / 8)
    evidence = review.get("evidence", {})
    evidence_count = sum(1 for snippets in evidence.values() if snippets)
    evidence_score = min(1.0, evidence_count / max(1, source_count))
    score = report_score * 0.3 + tradition_score * 0.3 + review_score * 0.2 + density_score * 0.1 + evidence_score * 0.1
    return round(min(1.0, score), 6)
