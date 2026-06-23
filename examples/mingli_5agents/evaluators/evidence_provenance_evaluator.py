"""Evaluator metric for provenance-bearing evidence retrieval."""

from __future__ import annotations

from typing import Any


def evidence_provenance_score(result: dict[str, Any], expected: dict[str, Any] | None = None) -> float:
    """Score whether source-review evidence snippets include audit metadata."""
    evidence = result.get("source_review", {}).get("evidence", {})
    if not isinstance(evidence, dict) or not evidence:
        return 0.0

    total = 0
    passed = 0
    for snippets in evidence.values():
        if not isinstance(snippets, list):
            continue
        for snippet in snippets:
            if not isinstance(snippet, dict):
                continue
            total += 1
            provenance = snippet.get("provenance")
            if (
                isinstance(provenance, dict)
                and provenance.get("corpus")
                and provenance.get("citation_policy")
                and snippet.get("excerpt_type") == "paraphrase"
                and snippet.get("snippet_id")
            ):
                passed += 1
    if total == 0:
        return 0.0
    return round(passed / total, 6)
