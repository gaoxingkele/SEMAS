"""Workflow-topology scoring for mingli SEMAS evolution."""

from __future__ import annotations


def workflow_score(result: dict, expected: dict | None = None) -> float:
    """Score collaboration topology quality from runtime artifacts."""
    workflow = result.get("workflow", {})
    rounds = int(workflow.get("discussion_rounds", 1))
    discussion = result.get("discussion", [])
    source_review = result.get("source_review", {})
    votes = result.get("votes", {})
    vote_summary = votes.get("_summary", {})
    vote_audit = votes.get("_audit", {})

    score = 0.15
    score += min(0.2, rounds * 0.075)
    score += 0.2 if workflow.get("cross_check_enabled") and any(item.get("round") == "cross_check" for item in discussion) else 0.0
    score += 0.15 if workflow.get("reconciliation_enabled") and any(item.get("round") == "reconciliation" for item in discussion) else 0.0
    score += 0.15 if source_review.get("strictness") == "strict" and source_review.get("status") == "pass" else 0.0
    score += 0.15 if vote_summary.get("passed") and vote_summary.get("threshold", 0) >= 0.75 else 0.0
    score += 0.05 if _claim_vote_audit_ok(vote_audit) else 0.0
    score += 0.1 if workflow.get("preserve_conflicts", True) else 0.0
    return min(1.0, score)


def _claim_vote_audit_ok(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("claim_count"), int)
        and value.get("claim_count", 0) > 0
        and value.get("passed_claim_count") == value.get("claim_count")
        and value.get("evidence_bound") is True
        and value.get("minority_positions_preserved") is True
    )
