"""Stub FFmpeg-based post-processing pipeline."""

from __future__ import annotations


def add_captions_and_normalize(clip_metadata: dict, captions: str) -> dict:
    """Return edited clip metadata.

    In production, this would shell out to FFmpeg to burn captions, add
    transitions, and normalize audio.
    """
    edited = dict(clip_metadata)
    edited["captions"] = captions
    edited["post_processed"] = True
    return edited
