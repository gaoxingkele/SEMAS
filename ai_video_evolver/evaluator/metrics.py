"""Video quality metrics for the AI Video Evolver.

These are intentionally lightweight stubs so the scaffold can run offline.
In production, replace them with real models:

- CLIP for prompt adherence
- FVD / optical flow for temporal coherence
- Aesthetic predictors for aesthetics
- NSFW / toxicity classifiers for safety
"""

from __future__ import annotations

from ai_video_evolver.tools.critic_functions import (
    safety_check,
    score_aesthetics,
    score_prompt_adherence,
    score_temporal_coherence,
)


def video_quality_score(output: dict, expected: dict) -> float:
    """Aggregate video quality score in [0, 1]."""
    final_prompt = output.get("final_prompt", "")
    user_idea = expected.get("user_idea", "")
    clip = output.get("clip", {})

    adherence = score_prompt_adherence(final_prompt, user_idea)
    aesthetics = score_aesthetics(final_prompt)
    coherence = score_temporal_coherence(clip)
    safety = safety_check(final_prompt)

    # Safety is a hard gate.
    if safety < 1.0:
        return 0.0

    # Weighted combination.
    return 0.4 * adherence + 0.3 * aesthetics + 0.3 * coherence
