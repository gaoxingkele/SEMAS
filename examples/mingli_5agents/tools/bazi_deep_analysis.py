"""Structured BaZi ten-god and luck-cycle analysis helpers."""

from __future__ import annotations

import importlib
from typing import Any

from examples.mingli_5agents.tools.calendar_core import (
    BRANCH_ELEMENTS,
    BRANCH_HIDDEN_STEMS,
    CHINESE_STEM_TO_EN,
    ELEMENTS,
    MONTH_BRANCHES,
    STEM_ELEMENTS,
    STEMS,
    ganzhi,
    normalize_ganzhi_label,
)
from examples.mingli_5agents.tools.bazi_school_debate import build_bazi_school_debate
from examples.mingli_5agents.tools.classical_book_agents import build_classical_book_agent_debate
from examples.mingli_5agents.tools.hengmen_rule_engine import analyze_natal_hengmen


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
    if context.get("provider_quality") == "offline_approximation":
        enriched["hengmen_pattern_analysis"] = {
            "schema_version": "hengmen-rule-engine-v2",
            "status": "blocked_calendar_precision",
            "pattern_candidates": [],
            "summary": "Hengmen analysis is blocked because the supplied four pillars are approximate.",
            "boundary": "Use lunar_python, sxtwl, or an externally sourced exact calendar context.",
        }
    else:
        enriched["hengmen_pattern_analysis"] = analyze_natal_hengmen(pillars, day_master)
    enriched.setdefault(
        "classical_layered_methodology",
        _classical_layered_methodology(enriched, context),
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
    enriched.setdefault("classical_book_agents", build_classical_book_agent_debate(enriched, context))
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
                "method": "hengmen_pattern",
                "status": "available",
                "evidence_fields": ["hengmen_pattern_analysis", "pattern_analysis", "school_debate"],
                "summary": enriched["hengmen_pattern_analysis"]["summary"],
            },
            {
                "method": "classical_layered_bazi",
                "status": "available",
                "evidence_fields": ["classical_layered_methodology", "major_luck", "pattern_analysis"],
                "summary": enriched["classical_layered_methodology"]["summary"],
            },
            {
                "method": "classical_book_agents",
                "status": "available",
                "evidence_fields": ["classical_book_agents", "classical_layered_methodology", "school_debate"],
                "summary": enriched["classical_book_agents"]["consensus"]["synthesis_rule"],
            },
            {
                "method": "data_validation_boundary",
                "status": "governed",
                "evidence_fields": ["data_validation_analysis"],
                "summary": enriched["data_validation_analysis"]["validation_boundary"],
            },
    ]
    enriched["method_matrix"] = _merged_method_matrix(enriched.get("method_matrix"), defaults)
    enriched.setdefault("school_debate", build_bazi_school_debate(enriched, context))
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


TRINE_GROUPS = {
    "Water": {"Shen", "Zi", "Chen"},
    "Fire": {"Yin", "Wu", "Xu"},
    "Metal": {"Si", "You", "Chou"},
    "Wood": {"Hai", "Mao", "Wei"},
}

MEETING_GROUPS = {
    "Wood": {"Yin", "Mao", "Chen"},
    "Fire": {"Si", "Wu", "Wei"},
    "Metal": {"Shen", "You", "Xu"},
    "Water": {"Hai", "Zi", "Chou"},
}

HENGMEN_BENIGN_TEN_GODS = {"wealth", "authority", "resource"}
HENGMEN_ADVERSE_TEN_GODS = {"peer"}


def _hengmen_pattern_analysis(pillars: object, day_master: str) -> dict[str, Any]:
    """Compatibility entrypoint delegating to the independent Hengmen engine."""
    return analyze_natal_hengmen(pillars, day_master)


def _legacy_hengmen_pattern_analysis(pillars: object, day_master: str) -> dict[str, Any]:
    """Model the Geju Hengmen pattern-school rules as auditable signals."""
    if not isinstance(pillars, dict):
        return {
            "schema_version": "hengmen-pattern-analysis-v1",
            "source": "examples/格局横门断.docx",
            "status": "missing_pillars",
            "summary": "格局横门断需要完整四柱后才能判断月令、透干和会支。",
            "rules": [],
        }

    month_label = str(pillars.get("month", ""))
    month_stem = _pillar_stem(month_label) if month_label else ""
    month_branch = _pillar_branch(month_label) if month_label else ""
    visible_stems = _visible_stems(pillars)
    branch_set = _branch_set(pillars)
    hidden_stems = list(BRANCH_HIDDEN_STEMS.get(month_branch, []))
    exposed_hidden = [stem for stem in hidden_stems if stem in visible_stems]
    commanding_stem = exposed_hidden[0] if exposed_hidden else (hidden_stems[0] if hidden_stems else month_stem)
    commanding_ten_god = _approx_ten_god(day_master, commanding_stem) if commanding_stem else "unknown"
    trine_changes = _group_changes(month_branch, branch_set, TRINE_GROUPS, "trine")
    meeting_changes = _group_changes(month_branch, branch_set, MEETING_GROUPS, "meeting")
    activation = "exposed" if exposed_hidden else "stored"
    use_mode = _hengmen_use_mode(commanding_ten_god, month_branch)
    purity = _hengmen_purity(commanding_ten_god, exposed_hidden, day_master)
    transformation = _hengmen_transformation(commanding_ten_god, trine_changes, meeting_changes)
    rules = [
        "先以月令为提纲，不先按日主强弱下结论。",
        "月令藏干如果透出，透出的藏干优先主事；未透则先按本气待用。",
        "善用神顺用，重在生扶保护；不善用神逆用，重在制伏化泄。",
        "会支能改变月令主气，但三会只加强力量，不解除刑冲合害破墓。",
        "地支藏干静而待用，天干、大运、流年透出后才明显应事。",
    ]
    return {
        "schema_version": "hengmen-pattern-analysis-v1",
        "source": "examples/格局横门断.docx",
        "month_pillar": month_label,
        "month_branch": month_branch,
        "month_hidden_stems": hidden_stems,
        "visible_stems": visible_stems,
        "exposed_month_hidden_stems": exposed_hidden,
        "commanding_stem": commanding_stem,
        "commanding_ten_god": commanding_ten_god,
        "hidden_stem_activation": activation,
        "use_mode": use_mode,
        "purity": purity,
        "branch_group_changes": trine_changes + meeting_changes,
        "transformation": transformation,
        "rules": rules,
        "summary": (
            f"以月令{month_branch or '未明'}为提纲，"
            f"{'透出' + '、'.join(exposed_hidden) if exposed_hidden else '藏干未透，先按本气待用'}；"
            f"主事十神为{commanding_ten_god}，取{use_mode['mode']}，格局{purity['state']}。"
        ),
        "boundary": "格局横门断用于事业、学业、项目和职位高度的结构判断；婚姻、健康和六亲仍需其它流派交叉验证。",
    }


def _visible_stems(pillars: dict[str, Any]) -> list[str]:
    stems = []
    for key in PILLAR_KEYS:
        label = str(pillars.get(key, ""))
        if label:
            stems.append(_pillar_stem(label))
    return [stem for stem in stems if stem]


def _branch_set(pillars: dict[str, Any]) -> set[str]:
    branches = set()
    for key in PILLAR_KEYS:
        label = str(pillars.get(key, ""))
        if label:
            branch = _pillar_branch(label)
            if branch:
                branches.add(branch)
    return branches


def _group_changes(
    month_branch: str,
    branches: set[str],
    groups: dict[str, set[str]],
    group_type: str,
) -> list[dict[str, Any]]:
    rows = []
    for element, members in groups.items():
        if month_branch not in members:
            continue
        present = sorted(branches & members, key=MONTH_BRANCHES.index)
        if len(present) >= 2:
            rows.append(
                {
                    "type": group_type,
                    "element": element,
                    "present_branches": present,
                    "complete": len(present) == 3,
                    "rule": "会合加强或改变月令主气；若同时有刑冲合害破，仍先论刑冲合害破。",
                }
            )
    return rows


def _hengmen_use_mode(ten_god: str, month_branch: str) -> dict[str, str]:
    if ten_god in HENGMEN_BENIGN_TEN_GODS:
        return {
            "mode": "顺用",
            "principle": "善用神要生扶保护，财喜食生官护，官喜财生印护，印喜官杀生扶。",
        }
    if ten_god in HENGMEN_ADVERSE_TEN_GODS or month_branch in {"Yin", "Mao", "Si", "Wu", "Hai", "Zi"}:
        return {
            "mode": "逆用或另取财官食杀",
            "principle": "比劫、羊刃、七杀、伤官、枭印等不宜放任，须看财官食杀透干会支来制化。",
        }
    if ten_god == "expression":
        return {
            "mode": "顺逆待分",
            "principle": "食神偏顺，伤官偏逆；当前粗粒度十神无法区分正偏，需专业十神或事实校准。",
        }
    return {
        "mode": "待校准",
        "principle": "月令主事不明时，不做高强度断语。",
    }


def _hengmen_purity(commanding_ten_god: str, exposed_hidden: list[str], day_master: str) -> dict[str, Any]:
    exposed_roles = [_approx_ten_god(day_master, stem) for stem in exposed_hidden]
    mixed_pairs = {frozenset({"authority", "expression"}), frozenset({"wealth", "resource"})}
    mixed = any(frozenset({left, right}) in mixed_pairs for left in exposed_roles for right in exposed_roles)
    if mixed:
        state = "驳杂"
        reason = "月令透出角色互相牵制，先按破格或杂格审查。"
    elif exposed_roles and all(role == commanding_ten_god for role in exposed_roles):
        state = "较清"
        reason = "月令透出集中，主线较清。"
    elif exposed_roles:
        state = "有兼格"
        reason = "月令透出不止一类，要分主格和兼格。"
    else:
        state = "待透"
        reason = "月令藏干未明显透出，需看大运流年引动。"
    return {"state": state, "exposed_roles": exposed_roles, "reason": reason}


def _hengmen_transformation(
    commanding_ten_god: str,
    group_changes: list[dict[str, Any]],
    meeting_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    changes = group_changes + meeting_changes
    if not changes:
        return {
            "state": "no_branch_group_change",
            "rule": "未见会支改变月令主气，先以透干和本气判断。",
        }
    complete = [item for item in changes if item.get("complete")]
    state = "complete_group_change" if complete else "partial_group_pressure"
    return {
        "state": state,
        "commanding_ten_god_before_change": commanding_ten_god,
        "changed_elements": [str(item.get("element", "")) for item in changes],
        "rule": "会支可能使月令用神变化；变化后要再审善用神是否受生、恶用神是否受制。",
    }


def _classical_layered_methodology(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Return a source-aware BaZi methodology stack from local classical scans."""
    pattern = deep.get("pattern_analysis", {}) if isinstance(deep.get("pattern_analysis"), dict) else {}
    hengmen = deep.get("hengmen_pattern_analysis", {}) if isinstance(deep.get("hengmen_pattern_analysis"), dict) else {}
    strength = deep.get("strength_analysis", {}) if isinstance(deep.get("strength_analysis"), dict) else {}
    useful = deep.get("useful_god_analysis", {}) if isinstance(deep.get("useful_god_analysis"), dict) else {}
    return {
        "schema_version": "classical-layered-bazi-methodology-v1",
        "source_policy": "local scans are source evidence; exact textual rules require OCR and edition review before promotion",
        "source_cards": [
            {
                "source_id": "bazi_sanming_tonghui",
                "title": "三命通会",
                "role": "classical synthesis layer for pillars, pattern, ten-god, luck-cycle, and auxiliary-marker debate",
                "local_files": [
                    "san_ming_tong_hui_juan_1_ia.pdf",
                    "san_ming_tong_hui_juan_2_ia.pdf",
                    "san_ming_tong_hui_juan_3_ia.pdf",
                    "san_ming_tong_hui_juan_4_ia.pdf",
                    "san_ming_tong_hui_juan_5_ia.pdf",
                    "san_ming_tong_hui_juan_6_ia.pdf",
                    "san_ming_tong_hui_juan_7_ia.pdf",
                    "san_ming_tong_hui_juan_8_ia.pdf",
                    "san_ming_tong_hui_juan_9_ia.pdf",
                    "san_ming_tong_hui_juan_10_ia.pdf",
                    "san_ming_tong_hui_juan_11_ia.pdf",
                    "san_ming_tong_hui_juan_12_ia.pdf",
                ],
                "rule_status": "paraphrased_method_card",
            },
            {
                "source_id": "bazi_early_sanming",
                "title": "李虚中命书、珞琭子三命消息赋注",
                "role": "early lineage layer for staged natal-luck framing and historical boundary setting",
                "local_files": ["li_xu_zhong_ming_shu_luo_lu_zi_ia.pdf"],
                "rule_status": "lineage_comparison_card",
            },
            {
                "source_id": "bazi_tianbu_zhenyuan",
                "title": "天步真原人命部",
                "role": "historical comparison layer; keeps star-fate/cosmological framing separate from operational BaZi rules",
                "local_files": ["tian_bu_zhen_yuan_ren_ming_bu_ia.pdf"],
                "rule_status": "historical_comparison_card",
            },
        ],
        "layers": [
            {
                "level": 1,
                "name": "整体命盘",
                "question": "先看四柱、月令、日主、五行偏向、格局主轴和可用保护链。",
                "evidence_fields": ["pillars", "strength_analysis", "pattern_analysis", "hengmen_pattern_analysis"],
                "current_signal": {
                    "pattern": pattern.get("pattern"),
                    "month_axis": hengmen.get("month_branch"),
                    "commanding_ten_god": hengmen.get("commanding_ten_god"),
                    "strength": strength.get("strength"),
                    "useful_element": useful.get("useful_element"),
                },
            },
            {
                "level": 2,
                "name": "大运阶段",
                "question": "大运不重新造命，主要承接、放大、压制或改写原局主轴。",
                "evidence_fields": ["major_luck", "classical_layered_methodology"],
                "current_signal": "compare major-luck pillar with natal pattern, useful element, and branch interactions",
            },
            {
                "level": 3,
                "name": "流年触发",
                "question": "流年判断具体年度主题：先看本年干支十神，再看五行流通、用神状态、原局和大运互动。",
                "evidence_fields": ["annual_ten_gods", "element_flow", "luck_pillar_interactions", "interaction_pressure_summary"],
                "current_signal": "annual rows must carry a classical timing trace",
            },
            {
                "level": 4,
                "name": "流月落事",
                "question": "流月负责把年度主题落到具体月份，必须绑定节气边界、月柱来源和大运互动。",
                "evidence_fields": ["monthly_ten_gods", "solar_term_window", "monthly_pillar_source", "interaction_pressure_summary"],
                "current_signal": "monthly rows must not reuse annual text without recalculating month pillar evidence",
            },
            {
                "level": 5,
                "name": "事实校准",
                "question": "古籍规则只能提出结构假设，必须用真实年份事件校准强弱和取象。",
                "evidence_fields": ["school_debate", "case_validation_hooks", "known_life_events"],
                "current_signal": "low-quality or unverified events cannot promote a rule",
            },
        ],
        "annual_monthly_protocol": [
            "整体命盘定主线，不让流年流月脱离原局。",
            "大运定十年背景，判断资源、压力、财官、输出哪一类主题被长期放大。",
            "流年定年度主题，必须独立计算干支、十神、五行、藏干、地支关系和压力排序。",
            "流月定应期细节，必须按节气月和月柱重新计算，不能套用年度句子。",
            "若流年或流月与原局、大运出现冲刑害破，先看压力排序，再看是否伤及格局主轴或保护机制。",
        ],
        "summary": "古籍层采用整体命盘、大运、流年、流月、事实校准五层法；三命通会主综合框架，早期三命材料主源流边界，天步真原只作历史比较。",
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
