"""Stub video generation API client.

Replace the `generate_video_from_prompt` body with a real backend call
(Runway, Pika, Stable Video Diffusion, ComfyUI, etc.).
"""

from __future__ import annotations

import hashlib


def generate_video_from_prompt(prompt: str, seed: int = 42) -> dict:
    """Return synthetic clip metadata for a given prompt.

    In production, this function should call your video generation backend
    and return a path/URL to the generated clip plus metadata.
    """
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
    return {
        "clip_id": f"clip_{prompt_hash}",
        "prompt": prompt,
        "duration_seconds": 4.0,
        "resolution": "512x512",
        "format": "mp4",
        "seed": seed,
    }
