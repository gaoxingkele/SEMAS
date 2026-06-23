"""Deterministic Zi Wei chart helper for the mingli demo."""

from __future__ import annotations

from examples.mingli_5agents.tools.calendar_core import build_chart_context
from examples.mingli_5agents.tools.professional_chart_provider import apply_external_chart_if_present
from examples.mingli_5agents.tools.ziwei_deep_analysis import build_ziwei_deep_analysis


PALACES = ["Ming", "Siblings", "Spouse", "Children", "Wealth", "Health", "Travel", "Friends", "Career", "Property", "Fortune", "Parents"]
STARS = ["Ziwei", "Tianfu", "Taiyang", "Taiyin", "Wuqu", "Tiantong", "Lianzhen", "Tianji"]


def build_ziwei_chart(birth: dict) -> dict:
    """Build a reproducible symbolic Zi Wei chart from normalized birth input."""
    context = build_chart_context(birth)
    seed = (
        int(birth["year"])
        + int(birth["month"])
        + int(birth["day"])
        + int(birth["hour"])
        + PALACES.index("Ming")
    )
    ming_idx = seed % len(PALACES)
    transformations = {
        "lu": STARS[(seed + 1) % len(STARS)],
        "quan": STARS[(seed + 2) % len(STARS)],
        "ke": STARS[(seed + 4) % len(STARS)],
        "ji": STARS[(seed + 6) % len(STARS)],
    }
    chart = {
        "context": context,
        "palace_order": PALACES,
        "star_cycle": STARS,
        "ming_palace": PALACES[ming_idx],
        "body_palace": PALACES[(ming_idx + 4) % len(PALACES)],
        "major_stars": [STARS[seed % len(STARS)], STARS[(seed + 3) % len(STARS)]],
        "transformations": transformations,
        "seasonal_anchor": context["solar_term"],
        "sources": ["ziwei_palace", "ziwei_four_transformations"],
    }
    chart = apply_external_chart_if_present("ziwei", birth, chart)
    chart["deep_analysis"] = build_ziwei_deep_analysis(chart, birth)
    return chart
