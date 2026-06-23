"""Long-term feedback memory for the mingli SEMAS example."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CORRECTION_STRATEGY_HINTS = {
    "vague": "feedback_adaptation",
    "structure": "feedback_adaptation",
    "source": "citation_precision",
    "citation": "citation_precision",
    "uncertainty": "safety_guardrails",
    "boundary": "safety_guardrails",
    "conflict": "synthesis_calibration",
    "debate": "debate_depth",
    "discussion": "debate_depth",
}

UNSAFE_FEEDBACK_TERMS = {
    "guarantee",
    "guaranteed",
    "deterministic",
    "certain prediction",
    "remove boundary",
    "no boundary",
    "without uncertainty",
    "no uncertainty",
    "medical",
    "investment",
    "legal",
    "marriage decision",
    "high-stakes",
    "高风险",
    "确定预测",
    "去掉边界",
    "不要边界",
    "不要不确定",
    "投资建议",
    "医疗建议",
    "法律建议",
    "婚姻决策",
}


@dataclass
class FeedbackMemoryEvent:
    """One normalized feedback or evolution memory event."""

    event_type: str
    feedback: dict[str, Any] = field(default_factory=dict)
    selected_strategy: str | None = None
    score_delta: float | None = None
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MingliFeedbackMemory:
    """JSON-backed long-term memory for repeated SEMAS evolution."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: FeedbackMemoryEvent) -> None:
        events = self.load()
        events.append(asdict(event))
        self.path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def remember_feedback(self, expected: dict[str, Any] | None, notes: str = "") -> None:
        """Persist user feedback from an evaluation expectation payload."""
        feedback = (expected or {}).get("feedback", {})
        if not feedback:
            return
        self.append(FeedbackMemoryEvent(event_type="feedback", feedback=feedback, notes=notes))

    def remember_evolution(
        self,
        selected_strategy: str,
        baseline_score: float,
        evolved_score: float,
    ) -> None:
        """Persist an accepted strategy and its observed improvement."""
        self.append(
            FeedbackMemoryEvent(
                event_type="accepted_strategy",
                selected_strategy=selected_strategy,
                score_delta=evolved_score - baseline_score,
            )
        )

    def profile(self) -> dict[str, Any]:
        """Summarize memory into strategy priors and recurring correction patterns."""
        correction_counts: Counter[str] = Counter()
        unsafe_corrections: Counter[str] = Counter()
        strategy_counts: Counter[str] = Counter()
        accepted_deltas: dict[str, list[float]] = {}

        for event in self.load():
            feedback = event.get("feedback") or {}
            for correction in feedback.get("corrections", []):
                normalized = str(correction).lower()
                if _unsafe_feedback(normalized):
                    unsafe_corrections[normalized] += 1
                    strategy_counts["safety_guardrails"] += 1
                    continue
                correction_counts[normalized] += 1
                for keyword, strategy in CORRECTION_STRATEGY_HINTS.items():
                    if keyword in normalized:
                        strategy_counts[strategy] += 1

            selected = event.get("selected_strategy")
            if selected:
                strategy_counts[selected] += 2
                accepted_deltas.setdefault(selected, []).append(float(event.get("score_delta") or 0.0))

        strategy_priors = {}
        for strategy, count in strategy_counts.items():
            avg_delta = 0.0
            if accepted_deltas.get(strategy):
                avg_delta = sum(accepted_deltas[strategy]) / len(accepted_deltas[strategy])
            strategy_priors[strategy] = count + max(0.0, avg_delta) * 10

        return {
            "correction_counts": dict(correction_counts),
            "unsafe_corrections": dict(unsafe_corrections),
            "unsafe_feedback_count": sum(unsafe_corrections.values()),
            "strategy_priors": strategy_priors,
            "total_events": len(self.load()),
        }

    def score_bias(self, strategy_name: str) -> float:
        """Return a bounded bonus for a strategy based on memory profile."""
        priors = self.profile()["strategy_priors"]
        if not priors:
            return 0.0
        max_prior = max(priors.values()) or 1.0
        return min(0.05, 0.05 * (priors.get(strategy_name, 0.0) / max_prior))


def _unsafe_feedback(normalized_correction: str) -> bool:
    return any(term in normalized_correction for term in UNSAFE_FEEDBACK_TERMS)
