"""Local evidence retrieval for mingli source records."""

from __future__ import annotations

from typing import Any

from examples.mingli_5agents.classical_text_index import retrieve_classical_passages


def retrieve_evidence(source_id: str, query: str = "", limit: int = 2) -> list[dict[str, Any]]:
    """Retrieve provenance-bearing evidence snippets for one source ID."""
    return retrieve_classical_passages(source_id, query=query, limit=limit)


def retrieve_many(source_ids: list[str], query: str = "") -> dict[str, list[dict[str, Any]]]:
    """Retrieve evidence snippets for multiple source IDs."""
    return {source_id: retrieve_evidence(source_id, query=query) for source_id in source_ids}
