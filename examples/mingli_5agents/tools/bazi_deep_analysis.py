"""Structured BaZi ten-god and luck-cycle analysis helpers."""

from __future__ import annotations

import importlib
from typing import Any

from examples.mingli_5agents.tools.calendar_core import (
    BRANCH_ELEMENTS,
    CHINESE_STEM_TO_EN,
    ELEMENTS,
    STEM_ELEMENTS,
    STEMS,
    ganzhi,
    normalize_ganzhi_label,
)


PILLAR_KEYS = ["year", "month", "day", "hour"]
RELATIONSHIP_TO_TEN_GOD = {
    "same": "peer",
    "output": "expression",
    "wealth": "wealth",
    "authority": "authority",
    "resource": "resource",
}


def build_bazi_deep_analysis(birth: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Build structured BaZi details for professional and approximate providers."""
    if context.get("backend") == "lunar_python" and importlib.util.find_spec("lunar_python"):
        return ensure_bazi_method_layers(_build_with_lunar_python(birth), context)
    return ensure_bazi_method_layers(_build_approximate(context), context)


def ensure_bazi_method_layers(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Backfill auditable BaZi method layers for native or external payloads."""
    enriched = dict(deep)
    pillars = context.get("pillars", {})
    element_counts = context.get("element_counts", {})
    day_master = str(enriched.get("day_master") or _pillar_stem(str(pillars.get("day", "JiaZi"))))
    day_element = STEM_ELEMENTS.get(day_master, context.get("dominant_element", "Wood"))
    dominant_element = str(context.get("dominant_element") or _dominant_element(element_counts))
    useful_element = str(context.get("useful_element") or _counterbalance_element(dominant_element))
    spread = _element_spread(element_counts)
    ten_gods = enriched.get("ten_gods") if isinstance(enriched.get("ten_gods"), dict) else {}

    enriched.setdefault("ten_god_distribution", _ten_god_distribution(ten_gods))
    enriched.setdefault("hidden_stem_profile", _hidden_stem_profile(ten_gods))
    enriched.setdefault("nayin_growth_profile", _nayin_growth_profile(ten_gods))
    enriched.setdefault(
        "strength_analysis",
        {
            "day_master": day_master,
            "day_master_element": day_element,
            "dominant_element": dominant_element,
            "element_counts": element_counts,
            "element_spread": spread,
            "season": context.get("season"),
            "solar_term": context.get("solar_term"),
            "strength": _strength_label(day_element, dominant_element, spread),
            "basis": "element counts, month season, day-master element, and pillar distribution",
        },
    )
    enriched.setdefault(
        "pattern_analysis",
        {
            "structure": "balanced" if spread <= 2 else "element-skewed",
            "pattern": _pattern_label(enriched["strength_analysis"], ten_gods),
            "month_ten_god": _nested_get(ten_gods, "month", "stem"),
            "risk": _pattern_risk(enriched["strength_analysis"]),
        },
    )
    enriched.setdefault(
        "useful_god_analysis",
        {
            "useful_element": useful_element,
            "supporting_element": _supporting_element(useful_element),
            "avoid_overweight_element": dominant_element,
            "rationale": "Use useful-element selection as a symbolic balancing hypothesis, then verify against life events.",
        },
    )
    enriched.setdefault(
        "tiaohou_analysis",
        {
            "season": context.get("season"),
            "solar_term": context.get("solar_term"),
            "climate_bias": _climate_bias(str(context.get("season", ""))),
            "adjustment": _tiaohou_adjustment(str(context.get("season", "")), useful_element),
        },
    )
    enriched.setdefault(
        "image_symbol_analysis",
        _image_symbol_analysis(pillars, ten_gods, dominant_element, useful_element),
    )
    enriched.setdefault(
        "new_school_simplified_analysis",
        _new_school_simplified_analysis(day_element, dominant_element, spread, useful_element),
    )
    enriched.setdefault(
        "data_validation_analysis",
        {
            "status": "governed_not_predictive",
            "validation_boundary": (
                "Large-sample validation is limited to externally reviewed report-quality/schema-quality "
                "labels until outcome-dataset consent, privacy, baseline, statistical-plan, and frozen "
                "train/holdout gates pass."
            ),
            "evidence_fields": [
                "empirical_validation",
                "outcome_dataset.data_split_record_coverage",
                "production_readiness.outcome_dataset_data_split_records_covered",
            ],
            "predictive_optimization_enabled": False,
        },
    )
    defaults = [
            {
                "method": "ziping_pattern",
                "status": "available",
                "evidence_fields": ["ten_gods", "strength_analysis", "pattern_analysis"],
                "summary": enriched["pattern_analysis"]["pattern"],
            },
            {
                "method": "strength_support",
                "status": "available",
                "evidence_fields": ["element_counts", "season", "day_master"],
                "summary": enriched["strength_analysis"]["strength"],
            },
            {
                "method": "blind_school_workflow",
                "status": "scaffolded",
                "evidence_fields": ["ten_god_distribution", "hidden_stem_profile"],
                "summary": "energy-flow hints only; requires practitioner review for production judgment",
            },
            {
                "method": "shensha_nayin",
                "status": "available" if enriched["nayin_growth_profile"]["complete"] else "partial",
                "evidence_fields": ["nayin_growth_profile"],
                "summary": "Na Yin and growth-stage markers are auxiliary, not primary decision rules",
            },
            {
                "method": "tiaohou",
                "status": "available",
                "evidence_fields": ["tiaohou_analysis", "useful_god_analysis"],
                "summary": enriched["tiaohou_analysis"]["adjustment"],
            },
            {
                "method": "image_symbol_reading",
                "status": "scaffolded",
                "evidence_fields": ["image_symbol_analysis", "pillars", "ten_gods"],
                "summary": enriched["image_symbol_analysis"]["summary"],
            },
            {
                "method": "new_school_simplified",
                "status": "scaffolded",
                "evidence_fields": ["new_school_simplified_analysis", "strength_analysis", "useful_god_analysis"],
                "summary": enriched["new_school_simplified_analysis"]["summary"],
            },
            {
                "method": "data_validation_boundary",
                "status": "governed",
                "evidence_fields": ["data_validation_analysis"],
                "summary": enriched["data_validation_analysis"]["validation_boundary"],
            },
    ]
    enriched["method_matrix"] = _merged_method_matrix(enriched.get("method_matrix"), defaults)
    return enriched


def _build_with_lunar_python(birth: dict[str, Any]) -> dict[str, Any]:
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
    day_master = _normalize_stem(eight_char.getDayGan())
    ten_gods = {
        key: {
            "stem": getattr(eight_char, f"get{_method_prefix(key)}ShiShenGan")(),
            "branch": list(getattr(eight_char, f"get{_method_prefix(key)}ShiShenZhi")()),
            "hidden_stems": list(getattr(eight_char, f"get{_method_prefix(key)}HideGan")()),
            "na_yin": getattr(eight_char, f"get{_method_prefix(key)}NaYin")(),
            "growth_stage": getattr(eight_char, f"get{_method_prefix(key)}DiShi")(),
            "wu_xing": getattr(eight_char, f"get{_method_prefix(key)}WuXing")(),
            "xun_kong": getattr(eight_char, f"get{_method_prefix(key)}XunKong")(),
        }
        for key in PILLAR_KEYS
    }
    gender_flag = _gender_flag(birth.get("gender"))
    yun = eight_char.getYun(gender_flag)
    return {
        "provider": "lunar_python",
        "day_master": day_master,
        "ming_gong": eight_char.getMingGong(),
        "shen_gong": eight_char.getShenGong(),
        "tai_yuan": eight_char.getTaiYuan(),
        "tai_xi": eight_char.getTaiXi(),
        "ten_gods": ten_gods,
        "luck_start": {
            "years": yun.getStartYear(),
            "months": yun.getStartMonth(),
            "days": yun.getStartDay(),
            "hours": yun.getStartHour(),
            "forward": bool(yun.isForward()),
        },
        "major_luck": [
            {
                "index": item.getIndex(),
                "start_age": item.getStartAge(),
                "end_age": item.getEndAge(),
                "start_year": item.getStartYear(),
                "end_year": item.getEndYear(),
                "ganzhi": normalize_ganzhi_label(item.getGanZhi()) if item.getGanZhi() else "",
                "xun": item.getXun(),
                "xun_kong": item.getXunKong(),
                "annual_preview": [
                    {
                        "year": liu_nian.getYear(),
                        "age": liu_nian.getAge(),
                        "ganzhi": normalize_ganzhi_label(liu_nian.getGanZhi()),
                    }
                    for liu_nian in item.getLiuNian()[:3]
                ],
            }
            for item in yun.getDaYun()
        ],
        "caution": "Professional BaZi details depend on the selected calendar backend and birth data precision.",
    }


def _build_approximate(context: dict[str, Any]) -> dict[str, Any]:
    pillars = context["pillars"]
    day_stem = _pillar_stem(pillars["day"])
    ten_gods = {}
    for key, label in pillars.items():
        stem = _pillar_stem(label)
        branch = _pillar_branch(label)
        ten_gods[key] = {
            "stem": _approx_ten_god(day_stem, stem),
            "branch": [_approx_ten_god(day_stem, _element_representative_stem(BRANCH_ELEMENTS[branch]))],
            "hidden_stems": [],
            "na_yin": "approximate",
            "growth_stage": "approximate",
            "wu_xing": f"{STEM_ELEMENTS[stem]}{BRANCH_ELEMENTS[branch]}",
            "xun_kong": "approximate",
        }
    start_year = int(context["date"][:4])
    return {
        "provider": "approximate",
        "day_master": day_stem,
        "ming_gong": "approximate",
        "shen_gong": "approximate",
        "tai_yuan": "approximate",
        "tai_xi": "approximate",
        "ten_gods": ten_gods,
        "luck_start": {"years": 0, "months": 0, "days": 0, "hours": 0, "forward": True},
        "major_luck": [
            {
                "index": idx,
                "start_age": idx * 10 + 1,
                "end_age": idx * 10 + 10,
                "start_year": start_year + idx * 10,
                "end_year": start_year + idx * 10 + 9,
                "ganzhi": ganzhi(start_year - 1984 + idx),
                "xun": "approximate",
                "xun_kong": "approximate",
                "annual_preview": [],
            }
            for idx in range(1, 9)
        ],
        "caution": "Approximate BaZi details are symbolic fallbacks and should be replaced by a professional backend.",
    }


def _method_prefix(key: str) -> str:
    return "Time" if key == "hour" else key.title()


def _normalize_stem(label: str) -> str:
    if label in STEMS:
        return label
    if label in CHINESE_STEM_TO_EN:
        return CHINESE_STEM_TO_EN[label]
    raise ValueError(f"Unsupported stem label: {label}")


def _gender_flag(value: object) -> int:
    text = str(value or "").strip().lower()
    return 0 if text in {"female", "f", "女", "woman"} else 1


def _pillar_stem(label: str) -> str:
    return next(stem for stem in STEMS if label.startswith(stem))


def _pillar_branch(label: str) -> str:
    stem = _pillar_stem(label)
    return label[len(stem):]


def _element_representative_stem(element: str) -> str:
    return next(stem for stem, stem_element in STEM_ELEMENTS.items() if stem_element == element)


def _approx_ten_god(day_stem: str, target_stem: str) -> str:
    day_element = STEM_ELEMENTS[day_stem]
    target_element = STEM_ELEMENTS[target_stem]
    relationship = _element_relationship(day_element, target_element)
    return RELATIONSHIP_TO_TEN_GOD[relationship]


def _element_relationship(day_element: str, target_element: str) -> str:
    if target_element == day_element:
        return "same"
    day_idx = ELEMENTS.index(day_element)
    target_idx = ELEMENTS.index(target_element)
    if target_idx == (day_idx + 1) % len(ELEMENTS):
        return "output"
    if target_idx == (day_idx + 2) % len(ELEMENTS):
        return "wealth"
    if target_idx == (day_idx - 2) % len(ELEMENTS):
        return "authority"
    return "resource"


def _element_spread(element_counts: object) -> int:
    if not isinstance(element_counts, dict) or not element_counts:
        return 0
    values = [int(value) for value in element_counts.values() if isinstance(value, int)]
    return max(values) - min(values) if values else 0


def _dominant_element(element_counts: object) -> str:
    if not isinstance(element_counts, dict) or not element_counts:
        return "Wood"
    return str(max(element_counts.items(), key=lambda item: int(item[1]))[0])


def _counterbalance_element(element: str) -> str:
    if element not in ELEMENTS:
        return "Metal"
    return ELEMENTS[(ELEMENTS.index(element) + 2) % len(ELEMENTS)]


def _supporting_element(element: str) -> str:
    if element not in ELEMENTS:
        return "Earth"
    return ELEMENTS[(ELEMENTS.index(element) - 1) % len(ELEMENTS)]


def _strength_label(day_element: str, dominant_element: str, spread: int) -> str:
    if day_element == dominant_element and spread >= 3:
        return "strong_day_master"
    if day_element != dominant_element and spread >= 3:
        return "externally_weighted"
    if spread <= 1:
        return "balanced"
    return "moderate"


def _pattern_label(strength_analysis: dict[str, Any], ten_gods: dict[str, Any]) -> str:
    strength = strength_analysis.get("strength")
    month_ten_god = _nested_get(ten_gods, "month", "stem") or "unknown"
    if strength == "strong_day_master":
        return f"strong-day-master pattern with month ten-god {month_ten_god}"
    if strength == "externally_weighted":
        return f"environment-weighted pattern with month ten-god {month_ten_god}"
    return f"balanced/moderate pattern with month ten-god {month_ten_god}"


def _pattern_risk(strength_analysis: dict[str, Any]) -> str:
    strength = strength_analysis.get("strength")
    if strength == "strong_day_master":
        return "overconfidence, heat, or overextension when output is not constrained"
    if strength == "externally_weighted":
        return "external pressure can dominate unless roles and resources are explicit"
    return "mixed signals require event validation before strong claims"


def _ten_god_distribution(ten_gods: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in ten_gods.values():
        if not isinstance(item, dict):
            continue
        labels = [item.get("stem")]
        branch = item.get("branch")
        if isinstance(branch, list):
            labels.extend(branch)
        for label in labels:
            if not label:
                continue
            key = str(label)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _hidden_stem_profile(ten_gods: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    total = 0
    for pillar, item in ten_gods.items():
        hidden = item.get("hidden_stems") if isinstance(item, dict) else None
        if isinstance(hidden, list):
            rows[str(pillar)] = hidden
            total += len(hidden)
        else:
            rows[str(pillar)] = []
    return {"total_hidden_stems": total, "by_pillar": rows}


def _nayin_growth_profile(ten_gods: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    complete = True
    for pillar, item in ten_gods.items():
        if not isinstance(item, dict):
            complete = False
            continue
        na_yin = item.get("na_yin")
        growth = item.get("growth_stage")
        if not na_yin or not growth:
            complete = False
        rows[str(pillar)] = {"na_yin": na_yin, "growth_stage": growth}
    return {"complete": complete and set(rows) == set(PILLAR_KEYS), "by_pillar": rows}


def _image_symbol_analysis(
    pillars: object,
    ten_gods: dict[str, Any],
    dominant_element: str,
    useful_element: str,
) -> dict[str, Any]:
    """Return constrained image-reading cues without turning symbols into events."""
    pillar_labels = []
    if isinstance(pillars, dict):
        pillar_labels = [str(pillars.get(key, "")) for key in PILLAR_KEYS if pillars.get(key)]
    ten_god_counts = _ten_god_distribution(ten_gods)
    leading_ten_god = max(ten_god_counts.items(), key=lambda item: item[1])[0] if ten_god_counts else "unknown"
    return {
        "pillar_images": pillar_labels,
        "dominant_symbol": dominant_element,
        "balancing_symbol": useful_element,
        "leading_ten_god": leading_ten_god,
        "summary": (
            f"read visible pillar/ten-god images as symbolic cues: dominant={dominant_element}, "
            f"balancing={useful_element}, leading_ten_god={leading_ten_god}"
        ),
        "boundary": "Image reading is descriptive symbolism and must not override structured evidence or real-world facts.",
    }


def _new_school_simplified_analysis(
    day_element: str,
    dominant_element: str,
    spread: int,
    useful_element: str,
) -> dict[str, Any]:
    if day_element == dominant_element and spread >= 2:
        polarity = "strong"
        decision_rule = "favor balancing and constraint signals"
    elif spread >= 3:
        polarity = "weak_or_environment_weighted"
        decision_rule = "favor support, role clarity, and resource signals"
    else:
        polarity = "balanced"
        decision_rule = "avoid single-factor reversal; require corroboration"
    return {
        "day_master_element": day_element,
        "dominant_element": dominant_element,
        "spread": spread,
        "polarity": polarity,
        "single_useful_element_hypothesis": useful_element,
        "decision_rule": decision_rule,
        "summary": f"{polarity}; useful-element hypothesis={useful_element}; rule={decision_rule}",
        "boundary": "Simplified polarity is a coarse audit layer, not a replacement for multi-method synthesis.",
    }


def _merged_method_matrix(current: object, defaults: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(item) for item in current if isinstance(item, dict)] if isinstance(current, list) else []
    seen = {str(item.get("method")) for item in rows if item.get("method")}
    for item in defaults:
        method = str(item.get("method"))
        if method not in seen:
            rows.append(dict(item))
            seen.add(method)
    return rows


def _nested_get(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _climate_bias(season: str) -> str:
    return {
        "spring": "wood rising; manage expansion",
        "summer": "heat and fire are emphasized",
        "autumn": "metal dryness and contraction are emphasized",
        "winter": "cold water and storage are emphasized",
    }.get(season, "seasonal adjustment requires provider verification")


def _tiaohou_adjustment(season: str, useful_element: str) -> str:
    if season == "summer":
        return f"cool, regulate, and structure the chart; useful-element hypothesis: {useful_element}"
    if season == "winter":
        return f"warm and mobilize the chart; useful-element hypothesis: {useful_element}"
    if season == "autumn":
        return f"moisten and balance dryness; useful-element hypothesis: {useful_element}"
    if season == "spring":
        return f"channel growth into structure; useful-element hypothesis: {useful_element}"
    return f"apply climate balancing cautiously; useful-element hypothesis: {useful_element}"
