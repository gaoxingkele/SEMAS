"""Deterministic Western astrology helper for the mingli demo."""

from __future__ import annotations

from examples.mingli_5agents.tools.astrology_deep_analysis import build_astrology_deep_analysis
from examples.mingli_5agents.tools.calendar_core import build_chart_context
from examples.mingli_5agents.tools.professional_chart_provider import apply_external_chart_if_present


SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SUN_SIGN_STARTS = [
    (1, 20, "Aquarius"),
    (2, 19, "Pisces"),
    (3, 21, "Aries"),
    (4, 20, "Taurus"),
    (5, 21, "Gemini"),
    (6, 21, "Cancer"),
    (7, 23, "Leo"),
    (8, 23, "Virgo"),
    (9, 23, "Libra"),
    (10, 23, "Scorpio"),
    (11, 22, "Sagittarius"),
    (12, 22, "Capricorn"),
]


def sun_sign(month: int, day: int) -> str:
    """Return common tropical Sun sign by date boundary."""
    sign = "Capricorn"
    for start_month, start_day, candidate in SUN_SIGN_STARTS:
        if (month, day) >= (start_month, start_day):
            sign = candidate
    return sign


def build_astrology_chart(birth: dict) -> dict:
    """Build a reproducible symbolic Western astrology chart."""
    context = build_chart_context(birth)
    month = int(birth["month"])
    day = int(birth["day"])
    hour = int(birth["hour"])
    sun = sun_sign(month, day)
    moon = SIGNS[(day + month) % 12]
    ascendant = SIGNS[(hour // 2 + day) % 12]
    chart = {
        "context": context,
        "sign_cycle": SIGNS,
        "sun": sun,
        "moon": moon,
        "ascendant": ascendant,
        "annual_theme": "integration" if (day + hour) % 2 else "exploration",
        "seasonal_anchor": context["season"],
        "sources": ["western_natal", "western_transit"],
    }
    chart = apply_external_chart_if_present("astrology", birth, chart)
    chart["deep_analysis"] = build_astrology_deep_analysis(chart, birth)
    return chart
