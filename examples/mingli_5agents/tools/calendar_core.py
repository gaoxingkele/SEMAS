"""Shared calendar and symbolic chart context for mingli tools.

The calculations here are deterministic offline approximations. They are meant
to provide a coherent internal substrate for the SEMAS example and can be
replaced by astronomical/lunar-calendar libraries later without changing agent
interfaces.
"""

from __future__ import annotations

from datetime import date
import importlib
from typing import Any

from examples.mingli_5agents.tools.calendar_provider import (
    CalendarProvider,
    CalendarProviderRegistry,
)

STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
ZODIAC_ANIMALS = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]
CHINESE_STEM_TO_EN = {
    "甲": "Jia",
    "乙": "Yi",
    "丙": "Bing",
    "丁": "Ding",
    "戊": "Wu",
    "己": "Ji",
    "庚": "Geng",
    "辛": "Xin",
    "壬": "Ren",
    "癸": "Gui",
}
CHINESE_BRANCH_TO_EN = {
    "子": "Zi",
    "丑": "Chou",
    "寅": "Yin",
    "卯": "Mao",
    "辰": "Chen",
    "巳": "Si",
    "午": "Wu",
    "未": "Wei",
    "申": "Shen",
    "酉": "You",
    "戌": "Xu",
    "亥": "Hai",
}

STEM_ELEMENTS = {
    "Jia": "Wood",
    "Yi": "Wood",
    "Bing": "Fire",
    "Ding": "Fire",
    "Wu": "Earth",
    "Ji": "Earth",
    "Geng": "Metal",
    "Xin": "Metal",
    "Ren": "Water",
    "Gui": "Water",
}

BRANCH_ELEMENTS = {
    "Zi": "Water",
    "Chou": "Earth",
    "Yin": "Wood",
    "Mao": "Wood",
    "Chen": "Earth",
    "Si": "Fire",
    "Wu": "Fire",
    "Wei": "Earth",
    "Shen": "Metal",
    "You": "Metal",
    "Xu": "Earth",
    "Hai": "Water",
}

MONTH_BRANCHES = ["Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai", "Zi", "Chou"]
SEASONS = {
    12: "winter",
    1: "winter",
    2: "spring",
    3: "spring",
    4: "spring",
    5: "summer",
    6: "summer",
    7: "summer",
    8: "autumn",
    9: "autumn",
    10: "autumn",
    11: "winter",
}

SOLAR_TERMS_APPROX = [
    ("Minor Cold", (1, 6)),
    ("Start of Spring", (2, 4)),
    ("Awakening of Insects", (3, 6)),
    ("Clear and Bright", (4, 5)),
    ("Start of Summer", (5, 6)),
    ("Grain in Ear", (6, 6)),
    ("Minor Heat", (7, 7)),
    ("Start of Autumn", (8, 8)),
    ("White Dew", (9, 8)),
    ("Cold Dew", (10, 8)),
    ("Start of Winter", (11, 7)),
    ("Major Snow", (12, 7)),
]


class ApproximateCalendarProvider:
    """Deterministic offline provider used by default."""

    name = "approximate"

    def build_context(self, birth: dict[str, Any]) -> dict[str, Any]:
        """Build shared symbolic context for all specialist tools."""
        dt = date(int(birth["year"]), int(birth["month"]), int(birth["day"]))
        hour = int(birth["hour"])
        pillars = {
            "year": year_ganzhi(dt.year),
            "month": month_ganzhi(dt.year, dt.month),
            "day": day_ganzhi(dt),
            "hour": hour_ganzhi(dt, hour),
        }
        counts = element_counts(list(pillars.values()))
        dominant = dominant_element(counts)
        return {
            **_birth_metadata(birth),
            "date": dt.isoformat(),
            "hour": hour,
            "minute": int(birth.get("minute", 0)),
            "season": SEASONS[dt.month],
            "solar_term": nearest_solar_term(dt.month, dt.day),
            "hour_branch": hour_branch(hour),
            "zodiac_animal": ZODIAC_ANIMALS[(dt.year - 4) % 12],
            "pillars": pillars,
            "element_counts": counts,
            "dominant_element": dominant,
            "useful_element": useful_element_for(dominant),
            "provider": self.name,
            "provider_quality": "offline_approximation",
        }


class ProfessionalCalendarProvider:
    """Optional adapter for installed professional calendar libraries.

    The provider currently supports `lunar_python` first and `sxtwl` second.
    Both are optional dependencies; callers should use `AutoCalendarProvider`
    when they want graceful fallback.
    """

    name = "professional"

    def build_context(self, birth: dict[str, Any]) -> dict[str, Any]:
        """Build shared context from an installed professional calendar library."""
        if importlib.util.find_spec("lunar_python"):
            return self._build_with_lunar_python(birth)
        if importlib.util.find_spec("sxtwl"):
            return self._build_with_sxtwl(birth)
        raise ImportError(
            "No professional calendar provider installed. Install optional dependencies "
            "such as lunar_python or sxtwl, or use calendar_provider='auto' to fall back."
        )

    def available_backend(self) -> str | None:
        """Return the selected backend name if a professional library is installed."""
        if importlib.util.find_spec("lunar_python"):
            return "lunar_python"
        if importlib.util.find_spec("sxtwl"):
            return "sxtwl"
        return None

    def _build_with_lunar_python(self, birth: dict[str, Any]) -> dict[str, Any]:
        lunar_python = importlib.import_module("lunar_python")
        solar_cls = getattr(lunar_python, "Solar", None)
        if solar_cls is None:
            solar_cls = getattr(importlib.import_module("lunar_python.Solar"), "Solar")
        solar = solar_cls(
            int(birth["year"]),
            int(birth["month"]),
            int(birth["day"]),
            int(birth["hour"]),
            int(birth.get("minute", 0)),
            0,
        )
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()
        pillars = {
            "year": normalize_ganzhi_label(eight_char.getYear()),
            "month": normalize_ganzhi_label(eight_char.getMonth()),
            "day": normalize_ganzhi_label(eight_char.getDay()),
            "hour": normalize_ganzhi_label(eight_char.getTime()),
        }
        context = _context_from_pillars(birth, pillars, provider="professional", quality="lunar_python")
        lunar_month = int(lunar.getMonth())
        context["lunar"] = {
            "year": lunar.getYear(),
            "month": abs(lunar_month),
            "day": lunar.getDay(),
            "is_leap_month": lunar_month < 0,
        }
        context["backend"] = "lunar_python"
        return context

    def _build_with_sxtwl(self, birth: dict[str, Any]) -> dict[str, Any]:
        sxtwl = importlib.import_module("sxtwl")
        day = sxtwl.fromSolar(int(birth["year"]), int(birth["month"]), int(birth["day"]))
        hour = int(birth["hour"])
        pillars = {
            "year": ganzhi_from_indices(day.getYearGZ()),
            "month": ganzhi_from_indices(day.getMonthGZ()),
            "day": ganzhi_from_indices(day.getDayGZ()),
            "hour": ganzhi_from_indices(day.getHourGZ(hour)),
        }
        context = _context_from_pillars(birth, pillars, provider="professional", quality="sxtwl")
        context["lunar"] = {
            "year": day.getLunarYear(),
            "month": day.getLunarMonth(),
            "day": day.getLunarDay(),
            "is_leap_month": bool(day.isLunarLeap()),
        }
        context["backend"] = "sxtwl"
        return context


class AutoCalendarProvider:
    """Professional provider with deterministic approximate fallback."""

    name = "auto"

    def __init__(self) -> None:
        self.professional = ProfessionalCalendarProvider()
        self.approximate = ApproximateCalendarProvider()

    def build_context(self, birth: dict[str, Any]) -> dict[str, Any]:
        """Use a professional backend when available, otherwise fall back."""
        if self.professional.available_backend():
            return self.professional.build_context(birth)
        context = self.approximate.build_context(birth)
        context["provider"] = self.name
        context["provider_quality"] = "professional_unavailable_fallback"
        context["fallback_provider"] = "approximate"
        return context


CALENDAR_PROVIDERS = CalendarProviderRegistry()
CALENDAR_PROVIDERS.register(ApproximateCalendarProvider())
CALENDAR_PROVIDERS.register(ProfessionalCalendarProvider())
CALENDAR_PROVIDERS.register(AutoCalendarProvider(), default=True)


def ganzhi(index: int) -> str:
    """Return a sexagenary stem-branch label for a zero-based cycle index."""
    return f"{STEMS[index % 10]}{BRANCHES[index % 12]}"


def year_ganzhi(year: int) -> str:
    """Return approximate year stem-branch, anchored to JiaZi 1984."""
    return ganzhi(year - 1984)


def month_ganzhi(year: int, month: int) -> str:
    """Return approximate month stem-branch using month order from Yin."""
    stem = STEMS[(year * 2 + month) % 10]
    branch = MONTH_BRANCHES[(month - 1) % 12]
    return f"{stem}{branch}"


def day_ganzhi(dt: date) -> str:
    """Return approximate day stem-branch anchored to 1984-02-02 JiaZi."""
    anchor = date(1984, 2, 2)
    return ganzhi((dt - anchor).days)


def hour_branch(hour: int) -> str:
    """Return the traditional two-hour branch."""
    if hour == 23:
        return "Zi"
    return BRANCHES[((hour + 1) // 2) % 12]


def hour_ganzhi(dt: date, hour: int) -> str:
    """Return approximate hour stem-branch from day stem and hour branch."""
    anchor = date(1984, 2, 2)
    day_index = (dt - anchor).days
    stem = STEMS[(day_index * 2 + BRANCHES.index(hour_branch(hour))) % 10]
    return f"{stem}{hour_branch(hour)}"


def element_counts(labels: list[str]) -> dict[str, int]:
    """Count five-element occurrences across stem-branch labels."""
    counts = {element: 0 for element in ELEMENTS}
    for label in labels:
        stem = next((candidate for candidate in STEMS if label.startswith(candidate)), "")
        branch = label[len(stem):]
        if stem:
            counts[STEM_ELEMENTS[stem]] += 1
        if branch in BRANCH_ELEMENTS:
            counts[BRANCH_ELEMENTS[branch]] += 1
    return counts


def normalize_ganzhi_label(label: str) -> str:
    """Normalize Chinese or English stem-branch labels to internal English form."""
    if any(label.startswith(stem) for stem in STEMS):
        return label
    if len(label) < 2:
        raise ValueError(f"Invalid ganzhi label: {label}")
    stem = CHINESE_STEM_TO_EN.get(label[0])
    branch = CHINESE_BRANCH_TO_EN.get(label[1])
    if not stem or not branch:
        raise ValueError(f"Unsupported ganzhi label: {label}")
    return f"{stem}{branch}"


def ganzhi_from_indices(value: Any) -> str:
    """Convert sxtwl-style tg/dz objects into an internal stem-branch label."""
    return f"{STEMS[int(value.tg) % 10]}{BRANCHES[int(value.dz) % 12]}"


def _context_from_pillars(
    birth: dict[str, Any],
    pillars: dict[str, str],
    *,
    provider: str,
    quality: str,
) -> dict[str, Any]:
    dt = date(int(birth["year"]), int(birth["month"]), int(birth["day"]))
    hour = int(birth["hour"])
    counts = element_counts(list(pillars.values()))
    dominant = dominant_element(counts)
    return {
        **_birth_metadata(birth),
        "date": dt.isoformat(),
        "hour": hour,
        "minute": int(birth.get("minute", 0)),
        "season": SEASONS[dt.month],
        "solar_term": nearest_solar_term(dt.month, dt.day),
        "hour_branch": hour_branch(hour),
        "zodiac_animal": ZODIAC_ANIMALS[(BRANCHES.index(pillars["year"][len(next(stem for stem in STEMS if pillars["year"].startswith(stem))):]))],
        "pillars": pillars,
        "element_counts": counts,
        "dominant_element": dominant,
        "useful_element": useful_element_for(dominant),
        "provider": provider,
        "provider_quality": quality,
    }


def _birth_metadata(birth: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "name": str(birth.get("name", "")),
        "gender": str(birth.get("gender", "")),
        "birthplace": str(birth.get("birthplace", "")),
    }
    for key in (
        "birthplace_normalized",
        "birthplace_region",
        "latitude",
        "longitude",
        "timezone_offset",
        "utc_offset",
        "geocoding_provider",
        "geocoding_quality",
    ):
        if birth.get(key) is not None:
            metadata[key] = birth[key]
    return metadata


def dominant_element(counts: dict[str, int]) -> str:
    """Return the most represented element with stable tie-breaking."""
    return max(ELEMENTS, key=lambda element: (counts.get(element, 0), -ELEMENTS.index(element)))


def useful_element_for(dominant: str) -> str:
    """Return a balancing element in the generating/control cycle approximation."""
    return ELEMENTS[(ELEMENTS.index(dominant) + 2) % len(ELEMENTS)]


def nearest_solar_term(month: int, day: int) -> str:
    """Return the latest approximate solar term not after the given month-day."""
    current = "Major Snow"
    for name, (term_month, term_day) in SOLAR_TERMS_APPROX:
        if (month, day) >= (term_month, term_day):
            current = name
    return current


def register_calendar_provider(provider: CalendarProvider, default: bool = False) -> None:
    """Register a calendar provider for chart tools."""
    CALENDAR_PROVIDERS.register(provider, default=default)


def get_calendar_provider(name: str | None = None) -> CalendarProvider:
    """Return a registered calendar provider."""
    return CALENDAR_PROVIDERS.get(name)


def describe_calendar_providers() -> dict[str, Any]:
    """Return registered providers and optional professional backend status."""
    professional = get_calendar_provider("professional")
    backend = professional.available_backend() if hasattr(professional, "available_backend") else None
    return {
        **CALENDAR_PROVIDERS.describe(),
        "professional_backend": backend,
        "professional_available": backend is not None,
    }


def build_chart_context(
    birth: dict[str, Any],
    provider_name: str | None = None,
) -> dict[str, Any]:
    """Build shared symbolic context via a registered calendar provider."""
    selected_provider = provider_name or birth.get("calendar_provider")
    return get_calendar_provider(selected_provider).build_context(birth)
