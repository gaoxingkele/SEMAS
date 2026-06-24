"""Prompt templates and helpers for video generation."""

from __future__ import annotations


def enhance_prompt(scene_description: str, style: str = "cinematic") -> str:
    """Add basic cinematic keywords to a scene description."""
    return f"{style} shot of {scene_description}, 4k, smooth camera motion"


CINEMATIC_KEYWORDS = [
    "dramatic lighting",
    "shallow depth of field",
    "golden hour",
    "slow motion",
    "wide angle",
    "film grain",
]
