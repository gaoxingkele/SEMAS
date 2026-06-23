"""User-feedback scoring for the mingli demo."""

from __future__ import annotations


def feedback_score(result: dict, expected: dict | None = None) -> float:
    """Map optional user feedback into a SEMAS reward signal."""
    feedback = (expected or {}).get("feedback", {})
    if not feedback:
        return 0.75
    satisfaction = float(feedback.get("satisfaction", 0.75))
    correction_penalty = min(0.4, 0.1 * len(feedback.get("corrections", [])))
    adaptation_bonus = 0.25 if result.get("adapted_to_feedback") else 0.0
    return max(0.0, min(1.0, satisfaction - correction_penalty + adaptation_bonus))
