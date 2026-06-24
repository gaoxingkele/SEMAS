"""Stub critic scoring functions for video quality."""

from __future__ import annotations


def score_prompt_adherence(final_prompt: str, user_idea: str) -> float:
    """Mock prompt adherence: overlap of words between final prompt and user idea."""
    idea_words = set(user_idea.lower().split())
    prompt_words = set(final_prompt.lower().split())
    if not idea_words:
        return 0.0
    overlap = len(idea_words & prompt_words)
    return min(1.0, overlap / len(idea_words))


def score_aesthetics(final_prompt: str) -> float:
    """Mock aesthetic score based on presence of cinematic keywords."""
    keywords = {"4k", "cinematic", "lighting", "smooth", "dramatic", "film"}
    words = set(final_prompt.lower().split())
    matches = len(words & keywords)
    return min(1.0, matches / 3.0)


def score_temporal_coherence(_clip_metadata: dict) -> float:
    """Mock temporal coherence. In production, use optical flow or FVD."""
    return 0.9


def safety_check(final_prompt: str) -> float:
    """Mock safety check. Returns 1.0 if no forbidden words present."""
    forbidden = {"nsfw", "violence", "gore", "explicit"}
    words = set(final_prompt.lower().split())
    return 0.0 if words & forbidden else 1.0
