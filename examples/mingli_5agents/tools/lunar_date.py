"""Lightweight calendar helper for the mingli demo.

This is not a full astronomical lunar-calendar implementation. It provides a
stable offline normalization layer so the SEMAS architecture can be exercised.
"""

from __future__ import annotations

from datetime import date

from examples.mingli_5agents.tools.birthplace_geo import normalize_birthplace_geo


def normalize_birth_input(data: dict) -> dict:
    """Return a validated, normalized birth record."""
    if data.get("birth_place") and not data.get("birthplace"):
        data = {**data, "birthplace": data["birth_place"]}
    required = ["name", "birth_date", "birth_time", "gender", "birthplace"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"Missing required birth fields: {', '.join(missing)}")

    year, month, day = [int(part) for part in data["birth_date"].split("-")]
    date(year, month, day)
    time_parts = data["birth_time"].split(":", 1)
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    if hour < 0 or hour > 23:
        raise ValueError("birth_time hour must be between 00 and 23")
    if minute < 0 or minute > 59:
        raise ValueError("birth_time minute must be between 00 and 59")

    return {
        **data,
        **normalize_birthplace_geo(data),
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "lunar_note": "offline symbolic calendar normalization",
    }
