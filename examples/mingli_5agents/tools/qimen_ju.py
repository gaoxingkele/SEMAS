"""Deterministic Qi Men Dun Jia helper for the mingli demo."""

from __future__ import annotations

from examples.mingli_5agents.tools.calendar_core import BRANCHES, build_chart_context
from examples.mingli_5agents.tools.professional_chart_provider import apply_external_chart_if_present
from examples.mingli_5agents.tools.qimen_deep_analysis import build_qimen_deep_analysis


DOORS = ["Open", "Rest", "Life", "Harm", "Delusion", "View", "Death", "Fear"]
STARS = ["Tianpeng", "Tianrui", "Tianchong", "Tianfu", "Tianqin", "Tianxin", "Tianzhu", "Tianren"]
SPIRITS = ["Chief", "Snake", "Moon", "Six Harmony", "White Tiger", "Black Tortoise", "Nine Earth", "Nine Heaven"]


def build_qimen_chart(birth: dict) -> dict:
    """Build a reproducible symbolic Qi Men chart from normalized birth input."""
    context = build_chart_context(birth)
    hour_idx = BRANCHES.index(context["hour_branch"])
    seed = int(birth["year"]) * 2 + int(birth["month"]) * 11 + int(birth["day"]) + hour_idx
    chart = {
        "context": context,
        "door_cycle": DOORS,
        "star_cycle": STARS,
        "spirit_cycle": SPIRITS,
        "duty_door": DOORS[seed % len(DOORS)],
        "duty_star": STARS[(seed + 2) % len(STARS)],
        "spirit": SPIRITS[(seed + 5) % len(SPIRITS)],
        "pattern": "stable planning" if seed % 2 else "active transition",
        "time_anchor": f"{context['hour_branch']} hour near {context['solar_term']}",
        "sources": ["qimen_plate", "qimen_door_star_spirit"],
    }
    chart = apply_external_chart_if_present("qimen", birth, chart)
    chart["deep_analysis"] = build_qimen_deep_analysis(chart, birth)
    return chart
