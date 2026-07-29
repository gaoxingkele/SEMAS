"""Auditable rule engine for the ``Geju Hengmen Duan`` method.

The engine keeps a clear boundary: it evaluates symbolic consistency of a
candidate chart with supplied events.  It does not establish factual birth time
or make deterministic predictions.
"""

from __future__ import annotations

from datetime import date
from typing import Any


PILLAR_KEYS = ("year", "month", "day", "hour")
STEMS = ("Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui")
STEM_ELEMENTS = {
    "Jia": "Wood", "Yi": "Wood", "Bing": "Fire", "Ding": "Fire", "Wu": "Earth",
    "Ji": "Earth", "Geng": "Metal", "Xin": "Metal", "Ren": "Water", "Gui": "Water",
}
BRANCH_HIDDEN_STEMS = {
    "Zi": ("Gui",), "Chou": ("Ji", "Gui", "Xin"), "Yin": ("Jia", "Bing", "Wu"),
    "Mao": ("Yi",), "Chen": ("Wu", "Yi", "Gui"), "Si": ("Bing", "Wu", "Geng"),
    "Wu": ("Ding", "Ji"), "Wei": ("Ji", "Ding", "Yi"), "Shen": ("Geng", "Ren", "Wu"),
    "You": ("Xin",), "Xu": ("Wu", "Xin", "Ding"), "Hai": ("Ren", "Jia"),
}
GENERATES = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
CONTROLS = {"Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"}
COMBINATIONS = {frozenset(("Zi", "Chou")), frozenset(("Yin", "Hai")), frozenset(("Mao", "Xu")), frozenset(("Chen", "You")), frozenset(("Si", "Shen")), frozenset(("Wu", "Wei"))}
CLASHES = {frozenset(("Zi", "Wu")), frozenset(("Chou", "Wei")), frozenset(("Yin", "Shen")), frozenset(("Mao", "You")), frozenset(("Chen", "Xu")), frozenset(("Si", "Hai"))}
HARMS = {frozenset(("Zi", "Wei")), frozenset(("Chou", "Wu")), frozenset(("Yin", "Si")), frozenset(("Mao", "Chen")), frozenset(("Shen", "Hai")), frozenset(("You", "Xu"))}
PUNISHMENTS = {frozenset(("Zi", "Mao")), frozenset(("Yin", "Si")), frozenset(("Si", "Shen")), frozenset(("Yin", "Shen")), frozenset(("Chou", "Xu")), frozenset(("Xu", "Wei")), frozenset(("Chou", "Wei"))}
BREAKS = {frozenset(("Zi", "You")), frozenset(("Mao", "Wu")), frozenset(("Chen", "Chou")), frozenset(("Wei", "Xu")), frozenset(("Yin", "Hai")), frozenset(("Si", "Shen"))}
TRINES = {
    "Wood": {"Hai", "Mao", "Wei"}, "Fire": {"Yin", "Wu", "Xu"},
    "Metal": {"Si", "You", "Chou"}, "Water": {"Shen", "Zi", "Chen"},
}
STORAGE_BRANCHES = {"Chen", "Xu", "Chou", "Wei"}
YANG_BLADE_BRANCH = {"Jia": "Mao", "Bing": "Wu", "Wu": "Wu", "Geng": "You", "Ren": "Zi"}
SOURCE_PATTERN_COVERAGE = (
    "direct_officer", "wealth", "resource", "food_god", "seven_killings", "hurting_officer",
    "yang_blade", "peer",
)
SOURCE_RULE_CATALOG = (
    ("month_command_candidates", "月令藏干、透干与具体格局候选", "implemented", "four pillars"),
    ("success_failure_rescue", "成格、破格与救应", "implemented", "visible stems and branch roots"),
    ("yang_blade_jianlu", "阳刃、建禄月劫的制化与承接", "implemented", "visible stems and branch roots"),
    ("branch_affection", "刑冲合害与会合有情无情", "implemented", "candidate root branches"),
    ("storage_head_foot", "四库、盖头截脚", "implemented", "four pillars and event pillar"),
    ("combine_direction", "合来合去与主格根气方向", "implemented", "candidate root branches"),
    ("virtual_invitation", "虚邀拱合与重复结构", "implemented", "four pillars plus corroboration"),
    ("pattern_specific_luck", "格局专属大运喜忌", "implemented", "major luck ganzhi"),
    ("annual_monthly_timing", "流年引动与流月应期", "implemented", "annual/monthly evidence and event date"),
    ("counterexample_penalty", "反例年份惩罚", "implemented", "declared counterexamples and annual rows"),
    ("pillar_order_and_case_analogy", "干支排列先后、案例类比的细断", "partial", "full textual case context and external facts"),
    ("life_outcome_assertions", "具体人生结论与断语", "human_review", "independent factual corroboration"),
)
PATTERN_BY_ROLE = {
    "direct_officer": "正官格", "seven_killings": "七杀格", "direct_wealth": "正财格",
    "indirect_wealth": "偏财格", "direct_resource": "正印格", "indirect_resource": "偏印格",
    "food_god": "食神格", "hurting_officer": "伤官格", "peer": "建禄月劫格",
}
EVENT_ROLES = {
    "study_exam": {"direct_resource", "direct_officer", "food_god"},
    "career_launch": {"direct_officer", "seven_killings", "direct_wealth", "food_god"},
    "role_power": {"direct_officer", "seven_killings", "direct_resource"},
    "role_transition": {"direct_officer", "seven_killings", "hurting_officer", "peer"},
    "business_power": {"direct_wealth", "indirect_wealth", "food_god", "hurting_officer"},
    "relationship": {"direct_wealth", "indirect_wealth", "direct_officer", "seven_killings"},
    "movement": {"seven_killings", "hurting_officer", "peer"},
    "health_pressure": {"indirect_resource", "seven_killings", "peer"},
    "family_loss": {"seven_killings", "direct_resource", "hurting_officer"},
    "death": {"seven_killings", "hurting_officer", "indirect_resource"},
    "public_scandal": {"hurting_officer", "seven_killings", "peer"},
    "health_crisis": {"seven_killings", "indirect_resource"},
}
ROLE_FAMILIES = {
    "wealth": {"direct_wealth", "indirect_wealth"},
    "authority": {"direct_officer", "seven_killings"},
    "resource": {"direct_resource", "indirect_resource"},
    "expression": {"food_god", "hurting_officer"},
    "peer": {"peer"},
}


def analyze_natal_hengmen(pillars: object, day_master: str) -> dict[str, Any]:
    """Generate explicit pattern candidates and natal relation evidence."""
    if not isinstance(pillars, dict):
        return {"schema_version": "hengmen-rule-engine-v2", "status": "missing_pillars", "pattern_candidates": []}
    normalized = {key: _split_pillar(str(pillars.get(key, ""))) for key in PILLAR_KEYS}
    invalid_pillars = [
        key for key, (stem, branch) in normalized.items()
        if str(pillars.get(key, "")) and (stem not in STEM_ELEMENTS or branch not in BRANCH_HIDDEN_STEMS)
    ]
    if invalid_pillars or day_master not in STEM_ELEMENTS:
        return {
            "schema_version": "hengmen-rule-engine-v2", "status": "invalid_pillars",
            "invalid_pillars": invalid_pillars, "invalid_day_master": day_master not in STEM_ELEMENTS,
            "pattern_candidates": [], "selected_pattern": _empty_candidate(),
            "review_flags": [{"id": "invalid_pillars", "severity": "blocking", "reason": "四柱或日主包含无法识别的干支。"}],
            "rule_catalog": _rule_catalog_receipt(),
            "agent_receipts": {"blocking": {"invalid_pillars": invalid_pillars, "invalid_day_master": day_master not in STEM_ELEMENTS}},
            "boundary": "Do not score a chart until invalid pillar labels are corrected.",
        }
    month_stem, month_branch = normalized["month"]
    visible = [stem for stem, _ in normalized.values() if stem]
    condition_visible = [stem for key, (stem, _) in normalized.items() if key != "day" and stem]
    condition_roles_by_pillar = {
        key: _precise_role(day_master, stem)
        for key, (stem, _) in normalized.items() if key != "day" and stem
    }
    branches = {key: branch for key, (_, branch) in normalized.items() if branch}
    month_hidden = list(BRANCH_HIDDEN_STEMS.get(month_branch, ()))
    candidate_stems = [stem for stem in month_hidden if stem in visible] or month_hidden[:1] or ([month_stem] if month_stem else [])
    candidates = [
        _pattern_candidate(
            stem, day_master, visible, condition_visible, condition_roles_by_pillar, branches, month_hidden
        )
        for stem in candidate_stems
    ]
    _promote_yang_blade_candidate(candidates, day_master, month_branch, condition_visible)
    _apply_seasonal_peer_refinement(candidates, day_master, month_branch, condition_visible)
    candidates.sort(key=lambda item: item["score"], reverse=True)
    relations = _natal_relations(branches)
    special_structures = _special_structures(normalized, day_master, relations)
    selected = candidates[0] if candidates else _empty_candidate()
    selection = _selection_receipt(candidates)
    review_flags = _review_flags(selected, selection, special_structures)
    return {
        "schema_version": "hengmen-rule-engine-v2",
        "source": "tools/格局横门断.docx -> mingli-bazi-hengmen/references/hengmen_meta_graph.md",
        "status": "ready" if candidates else "insufficient_month_command",
        "day_master": day_master,
        "month_branch": month_branch,
        "month_hidden_stems": month_hidden,
        "visible_stems": visible,
        "exposed_month_hidden_stems": [stem for stem in month_hidden if stem in visible],
        "hidden_stem_activation": "exposed" if any(stem in visible for stem in month_hidden) else "stored",
        "pattern_candidates": candidates,
        "rule_coverage": _rule_coverage(candidates, day_master, month_branch),
        "rule_catalog": _rule_catalog_receipt(),
        "review_flags": review_flags,
        "selected_pattern": selected,
        "pattern_selection": selection,
        "commanding_stem": selected.get("commanding_stem", ""),
        "commanding_ten_god": selected.get("role", "unknown"),
        "purity": {
            "state": selected.get("state", "待定"),
            "reason": selected.get("summary", ""),
        },
        "use_mode": _use_mode(selected.get("role", "unknown")),
        "natal_relations": relations,
        "special_structures": special_structures,
        "agent_receipts": {
            "month_command_pattern": {
                "month_branch": month_branch,
                "month_hidden_stems": month_hidden,
                "exposed_month_hidden_stems": [stem for stem in month_hidden if stem in visible],
                "candidate_count": len(candidates),
                "selected_pattern": selected.get("pattern", ""),
                "selection": selection,
            },
            "success_failure_rescue": {
                "supporting_conditions": selected.get("supporting_conditions", []),
                "failure_conditions": selected.get("failure_conditions", []),
                "rescue_conditions": selected.get("rescue_conditions", []),
                "ordering_evidence": selected.get("ordering_evidence", {}),
                "state": selected.get("state", ""),
            },
            "branch_affection": selected.get("affection", {}),
                "structure_evidence": special_structures,
                "review_flags": review_flags,
        },
        "summary": selected["summary"],
        "boundary": "Symbolic rule evaluation; requires independently sourced events and does not prove birth hour.",
    }


def score_hengmen_timing(
    natal: dict[str, Any],
    event: dict[str, Any],
    annual_row: dict[str, Any],
    monthly_rows: list[dict[str, Any]] | None = None,
    counterexample_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate annual/monthly activation and falsification for one event."""
    selected = natal.get("selected_pattern", {}) if isinstance(natal, dict) else {}
    pattern_role = str(selected.get("role", "unknown"))
    evidence = annual_row.get("bazi_evidence", {}) if isinstance(annual_row, dict) else {}
    annual_roles = set(_roles_from_evidence(evidence.get("annual_ten_gods", {}), natal.get("day_master", "")))
    interactions = evidence.get("branch_interactions", []) if isinstance(evidence, dict) else []
    luck = evidence.get("active_major_luck", {}) if isinstance(evidence, dict) else {}
    event_roles = EVENT_ROLES.get(str(event.get("type", "")), set())
    annual_support = 0.45
    reasons: list[str] = []
    if _role_matches(pattern_role, annual_roles):
        annual_support += 0.16
        reasons.append("流年透出或引动主格十神")
    if _event_roles_match(annual_roles, event_roles):
        annual_support += 0.14
        reasons.append("流年十神与事件主题相符")
    relation_names = {str(item.get("relation", "")) for item in interactions if isinstance(item, dict)}
    if relation_names & {"clash", "punishment", "harm"}:
        annual_support += 0.08 if _is_disruptive_event(event) else -0.05
        reasons.append("流年刑冲合害与事件性质相符" if _is_disruptive_event(event) else "非危机事件出现强冲刑，降权")
    major_luck = _major_luck_compatibility(pattern_role, natal.get("day_master", ""), luck)
    annual_support += major_luck["delta"]
    if major_luck["status"] == "evaluated":
        reasons.append(major_luck["reason"])
    structure_activation = _structure_activation(natal, annual_row)
    if structure_activation["annual_opened_storages"]:
        reasons.append("流年冲动原局库支；只记为结构启动证据，不单独断应事")
    annual_support += structure_activation["annual_delta"]
    monthly = _monthly_activation(event, monthly_rows or [], pattern_role, natal)
    counterfactual = _counterfactual_receipt(event, natal, counterexample_rows or [])
    # 证伪通道从 0.15 提到 0.25（annual 0.65 降到 0.55 保持归一）：
    # 原来几乎只做加法的流年分压过反例惩罚，候选挤在高位窄带。
    total = 0.55 * _clamp(annual_support) + 0.20 * monthly["score"] + 0.25 * counterfactual["score"]
    return {
        "schema_version": "hengmen-timing-v2",
        "annual_score": round(_clamp(annual_support), 4),
        "monthly": monthly,
        "counterfactual": counterfactual,
        "structure_activation": structure_activation,
        "major_luck": major_luck,
        "agent_receipts": {
            "annual_monthly_timing": {
                "annual_score": round(_clamp(annual_support), 4),
                "monthly": monthly,
                "major_luck": major_luck,
                "structure_activation": structure_activation,
            },
            "falsification": counterfactual,
        },
        "score": round(_clamp(total), 4),
        "reasons": reasons,
    }


def _pattern_candidate(
    stem: str,
    day_master: str,
    visible: list[str],
    condition_visible: list[str],
    condition_roles_by_pillar: dict[str, str],
    branches: dict[str, str],
    month_hidden: list[str],
) -> dict[str, Any]:
    role = _precise_role(day_master, stem)
    pattern = PATTERN_BY_ROLE.get(role, "杂格待定")
    exposed = stem in visible
    roots = [pillar for pillar, branch in branches.items() if stem in BRANCH_HIDDEN_STEMS.get(branch, ())]
    visible_roles = {_precise_role(day_master, item) for item in condition_visible}
    support, failures, rescues = _pattern_conditions(role, visible_roles)
    ordering_evidence = _stem_order_evidence(role, condition_roles_by_pillar)
    relations = _natal_relations(branches)
    affection = _affection(role, stem, branches, relations)
    score = _candidate_score(exposed, roots, support, failures, rescues, affection)
    state = _candidate_state(score, failures, rescues)
    return {
        "pattern": pattern,
        "role": role,
        "commanding_stem": stem,
        "month_hidden_stems": month_hidden,
        "exposed": exposed,
        "roots": roots,
        "supporting_conditions": support,
        "failure_conditions": failures,
        "rescue_conditions": rescues,
        "ordering_evidence": ordering_evidence,
        "affection": affection,
        "state": state,
        "score": round(_clamp(score), 4),
        "summary": f"{pattern}: {state}; 透干={exposed}，根气={','.join(roots) or '无'}。",
    }


def _promote_yang_blade_candidate(
    candidates: list[dict[str, Any]], day_master: str, month_branch: str, condition_visible: list[str]
) -> None:
    """Keep a month-command Yang Blade distinct from the generic peer candidate."""
    if YANG_BLADE_BRANCH.get(day_master) != month_branch:
        return
    for candidate in candidates:
        if candidate.get("role") != "peer" or candidate.get("special_pattern") == "yang_blade":
            continue
        roles = {_precise_role(day_master, stem) for stem in condition_visible}
        support, failures, rescues = _yang_blade_conditions(roles)
        candidate["pattern"] = "阳刃格"
        candidate["special_pattern"] = "yang_blade"
        candidate["supporting_conditions"] = ["月令为日主阳刃", *support]
        candidate["failure_conditions"] = failures
        candidate["rescue_conditions"] = rescues
        candidate["score"] = round(
            _candidate_score(
                bool(candidate.get("exposed")), candidate.get("roots", []), support,
                failures, rescues, candidate.get("affection", {}),
            ),
            4,
        )
        candidate["state"] = _candidate_state(candidate["score"], failures, rescues)
        candidate["summary"] = f"阳刃格: {candidate['state']}; 月令阳刃须见官杀制约或财食承接。"
        return


def _rule_coverage(candidates: list[dict[str, Any]], day_master: str, month_branch: str) -> dict[str, Any]:
    available = {str(candidate.get("role", "")) for candidate in candidates}
    if any(candidate.get("special_pattern") == "yang_blade" for candidate in candidates):
        available.add("yang_blade")
    return {
        "source_pattern_families": list(SOURCE_PATTERN_COVERAGE),
        "available_for_month_command": sorted(available),
        "yang_blade_month_command": YANG_BLADE_BRANCH.get(day_master) == month_branch,
        "unavailable_reason": "A family is absent when the supplied month command does not support that candidate; this is not an engine omission.",
    }


def _selection_receipt(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        return {"status": "insufficient_candidates", "margin": None, "confidence": "none"}
    if len(candidates) == 1:
        return {"status": "single_candidate", "margin": None, "confidence": "structural_only"}
    margin = round(float(candidates[0]["score"]) - float(candidates[1]["score"]), 4)
    confidence = "high" if margin >= 0.12 else "moderate" if margin >= 0.06 else "low"
    return {
        "status": "ranked_candidates", "margin": margin, "confidence": confidence,
        "ambiguous": confidence == "low",
        "runner_up": {"pattern": candidates[1].get("pattern", ""), "score": candidates[1]["score"]},
    }


def _review_flags(
    selected: dict[str, Any], selection: dict[str, Any], special_structures: dict[str, Any]
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    if selection.get("ambiguous"):
        flags.append({"id": "ambiguous_pattern_selection", "severity": "review", "reason": "月令候选间距过小。"})
    ordering = selected.get("ordering_evidence", {}) if isinstance(selected, dict) else {}
    if ordering.get("status") == "needs_corroboration":
        flags.append({"id": "stem_order_context", "severity": "review", "reason": "干支先后证据需要完整命局语境。"})
    virtual = special_structures.get("virtual_structures", []) if isinstance(special_structures, dict) else []
    if any(item.get("status") in {"needs_corroboration", "repeated_candidate"} for item in virtual if isinstance(item, dict)):
        flags.append({"id": "virtual_structure", "severity": "review", "reason": "虚邀拱合不能独立立格。"})
    return flags


def _rule_catalog_receipt() -> dict[str, Any]:
    rows = [
        {"id": rule_id, "scope": scope, "status": status, "evidence_required": evidence}
        for rule_id, scope, status, evidence in SOURCE_RULE_CATALOG
    ]
    return {
        "source": "tools/格局横门断.docx",
        "rules": rows,
        "summary": {
            "implemented": sum(row["status"] == "implemented" for row in rows),
            "partial": sum(row["status"] == "partial" for row in rows),
            "human_review": sum(row["status"] == "human_review" for row in rows),
        },
        "boundary": "Implemented means the named symbolic rule has executable evidence logic; it does not validate outcome assertions.",
    }


def _apply_seasonal_peer_refinement(
    candidates: list[dict[str, Any]], day_master: str, month_branch: str, condition_visible: list[str]
) -> None:
    """Record the book's Wood-Fire and Metal-Water peer-pattern refinements."""
    day_element = STEM_ELEMENTS.get(day_master, "")
    visible_elements = {STEM_ELEMENTS.get(stem, "") for stem in condition_visible}
    label = ""
    if day_element == "Wood" and month_branch in {"Yin", "Mao"} and "Fire" in visible_elements:
        label = "春木见火，木火通明"
    elif day_element == "Metal" and month_branch in {"Shen", "You"} and "Water" in visible_elements:
        label = "秋金见水，金水相涵"
    if not label:
        return
    for candidate in candidates:
        if candidate.get("role") != "peer" or candidate.get("special_pattern") == "yang_blade":
            continue
        candidate["supporting_conditions"].append(label)
        candidate["score"] = round(
            _candidate_score(
                bool(candidate.get("exposed")), candidate.get("roots", []),
                candidate["supporting_conditions"], candidate["failure_conditions"],
                candidate["rescue_conditions"], candidate.get("affection", {}),
            ),
            4,
        )
        candidate["state"] = _candidate_state(
            candidate["score"], candidate["failure_conditions"], candidate["rescue_conditions"]
        )


def _use_mode(role: str) -> dict[str, str]:
    if role in {"direct_wealth", "indirect_wealth", "direct_officer", "direct_resource"}:
        return {"mode": "顺用", "principle": "善神需有生扶与保护，并回到成格条件验证。"}
    if role in {"seven_killings", "hurting_officer", "indirect_resource", "peer"}:
        return {"mode": "逆用", "principle": "恶神或偏神须见制化、泄秀或救应，不能因出现即强断。"}
    return {"mode": "待校准", "principle": "月令信息不足时不做高强度断语。"}


def _pattern_conditions(role: str, visible_roles: set[str]) -> tuple[list[str], list[str], list[str]]:
    support: list[str] = []
    failures: list[str] = []
    rescues: list[str] = []
    if role == "direct_officer":
        support += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "财生官")
        support += _present(visible_roles, {"direct_resource", "indirect_resource"}, "印护官")
        failures += _present(visible_roles, {"hurting_officer"}, "伤官见官")
        failures += _present(visible_roles, {"seven_killings"}, "官杀混杂")
        rescues += _present(visible_roles, {"direct_resource", "indirect_resource"}, "印可化杀护官")
    elif role in {"direct_wealth", "indirect_wealth"}:
        support += _present(visible_roles, {"food_god"}, "食神生财")
        support += _present(visible_roles, {"direct_officer", "seven_killings"}, "财可生官杀")
        failures += _present(visible_roles, {"peer"}, "比劫夺财")
        failures += _present(visible_roles, {"hurting_officer"}, "伤官生财待清")
        rescues += _present(visible_roles, {"direct_officer", "seven_killings"}, "官杀可制比劫")
    elif role in {"direct_resource", "indirect_resource"}:
        support += _present(visible_roles, {"direct_officer", "seven_killings"}, "官杀生印")
        failures += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "财破印")
        failures += _present(visible_roles, {"seven_killings"}, "杀重压印") if role == "indirect_resource" else []
        rescues += _present(visible_roles, {"food_god", "hurting_officer"}, "食伤可泄印")
    elif role == "food_god":
        support += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "食神生财")
        failures += _present(visible_roles, {"indirect_resource"}, "枭神夺食")
        if "seven_killings" in visible_roles and visible_roles & {"direct_wealth", "indirect_wealth"}:
            failures.append("食神生财露杀")
        else:
            rescues += _present(visible_roles, {"seven_killings"}, "食神制杀")
    elif role == "hurting_officer":
        support += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "伤官生财")
        support += _present(visible_roles, {"direct_resource", "indirect_resource"}, "伤官佩印")
        failures += _present(visible_roles, {"direct_officer"}, "伤官见官")
        rescues += _present(visible_roles, {"direct_resource", "indirect_resource"}, "印可制伤官")
    elif role == "seven_killings":
        failures += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "财生杀")
        failures += _present(visible_roles, {"direct_officer"}, "官杀混杂")
        rescues += _present(visible_roles, {"direct_resource", "indirect_resource"}, "杀印相生")
        rescues += _present(visible_roles, {"food_god"}, "食神制杀")
        if "direct_officer" in visible_roles and "food_god" in visible_roles:
            rescues.append("食制杀留官取清")
    else:
        support += _present(visible_roles, {"direct_officer"}, "官星制劫")
        support += _present(visible_roles, {"food_god", "hurting_officer"}, "食伤泄劫")
        rescues += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "财可化劫")
        if not (set(support) or rescues):
            failures.append("禄劫无官财食伤承接")
        if {"direct_officer", "seven_killings"} <= visible_roles:
            failures.append("官杀混杂")
    return support, failures, rescues


def _yang_blade_conditions(visible_roles: set[str]) -> tuple[list[str], list[str], list[str]]:
    support = _present(visible_roles, {"direct_officer", "seven_killings"}, "官杀制刃")
    if visible_roles & {"direct_wealth", "indirect_wealth"} and visible_roles & {"direct_resource", "indirect_resource"}:
        support.append("财印相随官杀")
    rescues = _present(visible_roles, {"food_god", "hurting_officer"}, "食伤化刃")
    rescues += _present(visible_roles, {"direct_wealth", "indirect_wealth"}, "财可承接刃气")
    failures = _present(visible_roles, {"hurting_officer"}, "伤官损官制刃")
    if not support:
        failures.append("阳刃未见官杀制约")
    if {"direct_officer", "seven_killings"} <= visible_roles:
        failures.append("官杀混杂")
    return support, failures, rescues


def _candidate_score(
    exposed: bool,
    roots: list[str],
    support: list[str],
    failures: list[str],
    rescues: list[str],
    affection: dict[str, Any],
) -> float:
    score = 0.38 + (0.18 if exposed else 0.06) + min(0.16, len(roots) * 0.05)
    score += min(0.16, len(support) * 0.05) + min(0.10, len(rescues) * 0.05)
    score -= min(0.22, len(failures) * 0.08)
    score += float(affection.get("delta", 0.0))
    return _clamp(score)


def _candidate_state(score: float, failures: list[str], rescues: list[str]) -> str:
    return "成格" if score >= 0.68 and not failures else "有救待验" if rescues else "破格或待定"


def _stem_order_evidence(role: str, roles_by_pillar: dict[str, str]) -> dict[str, Any]:
    sequence = [
        {"pillar": pillar, "role": roles_by_pillar[pillar]}
        for pillar in ("year", "month", "hour") if pillar in roles_by_pillar
    ]
    wealth_pillars = [item["pillar"] for item in sequence if item["role"] in {"direct_wealth", "indirect_wealth"}]
    resource_pillars = [item["pillar"] for item in sequence if item["role"] in {"direct_resource", "indirect_resource"}]
    separated = bool(wealth_pillars and resource_pillars and set(wealth_pillars).isdisjoint(resource_pillars))
    interpretation = "no_pattern_specific_order_rule"
    status = "not_applicable"
    if role == "hurting_officer" and separated:
        interpretation = "伤官佩印见财印分列；仍需完整命局语境验证财印不碍"
        status = "needs_corroboration"
    return {
        "visible_sequence": sequence,
        "wealth_pillars": wealth_pillars,
        "resource_pillars": resource_pillars,
        "wealth_resource_separated": separated,
        "status": status,
        "interpretation": interpretation,
    }


def _affection(role: str, stem: str, branches: dict[str, str], relations: list[dict[str, Any]]) -> dict[str, Any]:
    stem_element = STEM_ELEMENTS.get(stem, "")
    trine_support = any(stem_element == element and len(set(branches.values()) & group) >= 2 for element, group in TRINES.items())
    root_pillars = {pillar for pillar, branch in branches.items() if stem in BRANCH_HIDDEN_STEMS.get(branch, ())}
    harmful = [
        item for item in relations
        if item["relation"] in {"clash", "harm", "punishment", "break"}
        and root_pillars & {item["left_pillar"], item["right_pillar"]}
    ]
    directed = _directed_combine_affection(stem, branches, relations)
    delta = (0.08 if trine_support else 0.0) + directed["delta"] - min(0.12, len(harmful) * 0.04)
    state = "有情" if delta > 0 else "无情或受损" if delta < 0 else "待验"
    return {
        "state": state, "delta": round(delta, 4), "trine_support": trine_support,
        "root_pillars": sorted(root_pillars), "disruptions": harmful,
        "directed_combinations": directed["evidence"], "role": role,
    }


def _directed_combine_affection(
    stem: str, branches: dict[str, str], relations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Classify a combination by what it brings to a branch rooting the pattern stem."""
    candidate_element = STEM_ELEMENTS.get(stem, "")
    delta = 0.0
    evidence: list[dict[str, Any]] = []
    for item in relations:
        if item["relation"] != "combine":
            continue
        left, right = item["left_pillar"], item["right_pillar"]
        for rooted, partner in ((left, right), (right, left)):
            if stem not in BRANCH_HIDDEN_STEMS.get(branches[rooted], ()):
                continue
            partner_elements = {STEM_ELEMENTS[hidden] for hidden in BRANCH_HIDDEN_STEMS[branches[partner]]}
            brings = {
                "supports": sorted(element for element in partner_elements if element == candidate_element or GENERATES.get(element) == candidate_element),
                "controls": sorted(element for element in partner_elements if CONTROLS.get(element) == candidate_element),
            }
            effect = "mixed"
            if brings["supports"] and not brings["controls"]:
                effect, change = "brings_support", 0.03
            elif brings["controls"] and not brings["supports"]:
                effect, change = "brings_control", -0.03
            else:
                change = 0.0
            delta += change
            evidence.append({"root_pillar": rooted, "partner_pillar": partner, "effect": effect, "delta": change, **brings})
    return {"delta": round(max(-0.08, min(0.08, delta)), 4), "evidence": evidence}


def _natal_relations(branches: dict[str, str]) -> list[dict[str, Any]]:
    keys = list(branches)
    rows: list[dict[str, Any]] = []
    for index, left_key in enumerate(keys):
        for right_key in keys[index + 1:]:
            pair = frozenset((branches[left_key], branches[right_key]))
            relation = (
                "combine" if pair in COMBINATIONS else "clash" if pair in CLASHES
                else "harm" if pair in HARMS else "punishment" if pair in PUNISHMENTS
                else "break" if pair in BREAKS else ""
            )
            if relation:
                rows.append({"left_pillar": left_key, "right_pillar": right_key, "relation": relation, "branches": sorted(pair)})
    return rows


def _special_structures(
    normalized: dict[str, tuple[str, str]], day_master: str, relations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Return auditable structural signals, without turning symbols into outcomes."""
    branches = {key: branch for key, (_, branch) in normalized.items() if branch}
    visible = [stem for stem, _ in normalized.values() if stem]
    treasuries = []
    for pillar, branch in branches.items():
        if branch not in STORAGE_BRANCHES:
            continue
        hidden = list(BRANCH_HIDDEN_STEMS[branch])
        treasuries.append(
            {
                "pillar": pillar,
                "branch": branch,
                "hidden_stems": hidden,
                "exposed_hidden_stems": [stem for stem in hidden if stem in visible],
                "month_command_requires_exposure": pillar == "month",
            }
        )
    return {
        "treasuries": treasuries,
        "head_foot": _head_foot_signals(normalized),
        "combine_direction": _combine_direction(branches, day_master, relations),
        "virtual_structures": _virtual_structures(branches),
        "boundary": "These are chart-structure observations. They require event and timing corroboration."
    }


def _head_foot_signals(normalized: dict[str, tuple[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pillar, (stem, branch) in normalized.items():
        primary = next(iter(BRANCH_HIDDEN_STEMS.get(branch, ())), "")
        stem_element = STEM_ELEMENTS.get(stem, "")
        branch_element = STEM_ELEMENTS.get(primary, "")
        stem_to_branch = _element_relation(stem_element, branch_element)
        branch_to_stem = _element_relation(branch_element, stem_element)
        status = "mixed"
        if stem_to_branch == "controls" or branch_to_stem == "controls":
            status = "blocked"
        elif stem_to_branch in {"same", "generates"} or branch_to_stem in {"same", "generates"}:
            status = "supported"
        rows.append(
            {
                "pillar": pillar,
                "stem": stem,
                "branch": branch,
                "branch_primary_hidden_stem": primary,
                "stem_to_branch": stem_to_branch,
                "branch_to_stem": branch_to_stem,
                "status": status,
            }
        )
    return rows


def _combine_direction(
    branches: dict[str, str], day_master: str, relations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in relations:
        if relation["relation"] != "combine":
            continue
        left, right = str(relation["left_pillar"]), str(relation["right_pillar"])
        left_branch, right_branch = branches[left], branches[right]
        incoming_to_left = [_precise_role(day_master, stem) for stem in BRANCH_HIDDEN_STEMS[right_branch]]
        incoming_to_right = [_precise_role(day_master, stem) for stem in BRANCH_HIDDEN_STEMS[left_branch]]
        rows.append(
            {
                "pillars": [left, right],
                "branches": [left_branch, right_branch],
                "incoming_roles": {left: incoming_to_left, right: incoming_to_right},
                "day_branch_combined_away_risk": "day" in {left, right},
                "status": "candidate_only",
            }
        )
    return rows


def _virtual_structures(branches: dict[str, str]) -> list[dict[str, Any]]:
    present = set(branches.values())
    rows: list[dict[str, Any]] = []
    for element, group in TRINES.items():
        matched = sorted(present & group)
        if len(matched) == 2:
            pair_count = sum(1 for branch in branches.values() if branch == matched[0]) * sum(
                1 for branch in branches.values() if branch == matched[1]
            )
            rows.append(
                {
                    "kind": "partial_trine_candidate",
                    "element": element,
                    "present_branches": matched,
                    "missing_branch": next(iter(group - set(matched))),
                    "pair_count": pair_count,
                    "status": "repeated_candidate" if pair_count >= 2 else "needs_corroboration",
                    "weight": "low" if pair_count == 1 else "medium_low",
                    "candidate_boundary": "Virtual invitation is evidence only; it cannot create a pattern candidate without exposure or independent corroboration.",
                }
            )
    return rows


def _structure_activation(natal: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    special = natal.get("special_structures", {}) if isinstance(natal, dict) else {}
    treasuries = special.get("treasuries", []) if isinstance(special, dict) else []
    evidence = row.get("bazi_evidence", {}) if isinstance(row, dict) else {}
    pillar = str(evidence.get("annual_pillar") or evidence.get("monthly_pillar") or "")
    _, active_branch = _split_pillar(pillar)
    opened = [
        {"pillar": item["pillar"], "branch": item["branch"], "by": active_branch}
        for item in treasuries if active_branch and frozenset((item["branch"], active_branch)) in CLASHES
    ]
    return {
        "active_pillar": pillar,
        "annual_opened_storages": opened,
        "annual_delta": 0.03 if opened else 0.0,
        "boundary": "A storage clash is activation evidence only; repeated clashes may also damage the structure.",
    }


def _major_luck_compatibility(pattern_role: str, day_master: str, luck: object) -> dict[str, Any]:
    if not isinstance(luck, dict) or not luck.get("ganzhi"):
        return {"status": "unavailable", "score": 0.42, "delta": 0.0, "roles": [], "reason": "无可用大运干支，不以阶段承接加分"}
    stem, branch = _split_pillar(str(luck.get("ganzhi", "")))
    roles = {_precise_role(day_master, stem)} if stem else set()
    roles.update(_precise_role(day_master, hidden) for hidden in BRANCH_HIDDEN_STEMS.get(branch, ()))
    supportive, adverse = _luck_roles_for_pattern(pattern_role)
    support_hits = roles & supportive
    adverse_hits = roles & adverse
    score = _clamp(0.54 + min(0.18, len(support_hits) * 0.09) - min(0.22, len(adverse_hits) * 0.11))
    if support_hits and not adverse_hits:
        reason = "大运十神承接主格"
    elif adverse_hits and not support_hits:
        reason = "大运十神触及主格破败条件"
    else:
        reason = "大运与主格关系混合或中性"
    return {
        "status": "evaluated", "score": round(score, 4), "delta": round(score - 0.54, 4),
        "ganzhi": luck["ganzhi"], "roles": sorted(roles), "support_hits": sorted(support_hits),
        "adverse_hits": sorted(adverse_hits), "reason": reason,
    }


def _luck_roles_for_pattern(role: str) -> tuple[set[str], set[str]]:
    if role == "direct_officer":
        return ({"direct_wealth", "indirect_wealth", "direct_resource", "indirect_resource"}, {"hurting_officer", "seven_killings"})
    if role in {"direct_wealth", "indirect_wealth"}:
        return ({"food_god", "direct_officer", "seven_killings"}, {"peer", "hurting_officer"})
    if role in {"direct_resource", "indirect_resource"}:
        return ({"direct_officer", "seven_killings"}, {"direct_wealth", "indirect_wealth"})
    if role == "food_god":
        return ({"direct_wealth", "indirect_wealth", "seven_killings"}, {"indirect_resource"})
    if role == "seven_killings":
        return ({"direct_resource", "indirect_resource", "food_god"}, {"direct_wealth", "indirect_wealth"})
    if role == "hurting_officer":
        return ({"direct_wealth", "indirect_wealth", "direct_resource", "indirect_resource"}, {"direct_officer"})
    return ({"direct_officer", "seven_killings", "direct_wealth", "indirect_wealth", "food_god"}, {"hurting_officer"})


def _element_relation(source: str, target: str) -> str:
    if not source or not target:
        return "unknown"
    if source == target:
        return "same"
    if GENERATES.get(source) == target:
        return "generates"
    if CONTROLS.get(source) == target:
        return "controls"
    return "drained_or_controlled"


def _monthly_activation(
    event: dict[str, Any], rows: list[dict[str, Any]], pattern_role: str, natal: dict[str, Any]
) -> dict[str, Any]:
    month_resolution = _event_month_resolution(event)
    target_month = month_resolution["month"]
    if not rows or month_resolution["status"] != "resolved":
        reason = month_resolution.get("reason", "事件缺少可核验月份")
        if month_resolution["status"] == "missing":
            reason = "事件缺少可核验月份或未提供流月行；不以最佳月份补偿。"
        if not rows:
            reason = reason if month_resolution["status"] == "missing" else f"{reason}；未提供流月行，不以最佳月份补偿。"
        return {"status": "unresolved", "score": 0.5, "reason": reason}
    row = next((item for item in rows if int(item.get("month", 0) or 0) == target_month), {})
    evidence = row.get("bazi_evidence", {}) if isinstance(row, dict) else {}
    roles = set(_roles_from_evidence(evidence.get("monthly_ten_gods", {}), ""))
    interactions = evidence.get("branch_interactions", []) if isinstance(evidence, dict) else []
    score = 0.44 + (0.20 if _role_matches(pattern_role, roles) else 0.0) + (0.14 if _event_roles_match(roles, EVENT_ROLES.get(str(event.get("type", "")), set())) else 0.0)
    if interactions and _is_disruptive_event(event):
        score += 0.10
    activation = _structure_activation(natal, row)
    score += activation["annual_delta"]
    return {
        "status": "evaluated", "score": round(_clamp(score), 4), "month": target_month,
        "monthly_pillar": evidence.get("monthly_pillar", ""), "roles": sorted(roles),
        "opened_storages": activation["annual_opened_storages"],
    }


def _counterfactual_receipt(
    event: dict[str, Any], natal: dict[str, Any], counterexample_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    counterexamples = event.get("counterexamples", event.get("counterexample_years", []))
    if not isinstance(counterexamples, list) or not counterexamples:
        if counterexample_rows:
            # 未声明反例、但调用方提供了派生反例岁运行（案例窗口内的邻近无事件年份）：
            # 证据强度低于声明反例，按更低单价与上限施加惩罚。
            return _evaluate_counterexample_rows(
                event, natal, counterexample_rows,
                per_year_penalty=0.05, penalty_cap=0.20, status="derived_counterexamples",
            )
        return {"status": "missing_counterexamples", "score": 0.5, "penalty": 0.0, "reason": "没有反例年份，不能把事实来源完整度当作命中证据。"}
    requested_years = {_counterexample_year(item) for item in counterexamples}
    requested_years.discard(None)
    if len(requested_years) != len(counterexamples):
        return {
            "status": "invalid_counterexample_years", "score": 0.5, "penalty": 0.0,
            "reason": "反例年份必须是可解析的独立年份，暂不据此施加惩罚。",
        }
    rows_by_year = {
        _counterexample_year(row.get("year")): row for row in counterexample_rows
        if isinstance(row, dict) and _counterexample_year(row.get("year")) is not None
    }
    missing_years = sorted(requested_years - set(rows_by_year))
    if missing_years:
        return {
            "status": "counterexample_rows_missing", "score": 0.5, "penalty": 0.0,
            "counterexample_count": len(requested_years), "missing_years": missing_years,
            "reason": "已声明反例年份，但缺少同年份岁运行；暂不制造惩罚。",
        }
    receipt = _evaluate_counterexample_rows(
        event, natal, [rows_by_year[year] for year in sorted(rows_by_year)],
        per_year_penalty=0.08, penalty_cap=0.35, status="evaluated",
    )
    receipt["counterexample_count"] = len(counterexamples)
    return receipt


def _evaluate_counterexample_rows(
    event: dict[str, Any],
    natal: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    per_year_penalty: float,
    penalty_cap: float,
    status: str,
) -> dict[str, Any]:
    """对反例年份逐行判定“同主题结构是否再次出现”，出现则惩罚。

    激活条件与正面计分同构：十神主题（主格或事件主题）与地支引动同时成立，
    或时柱被流年直接引动（横门第二十三章“引动归时”，时柱为应事落点）。
    旧条件“任意支关系即激活”几乎年年触发、对所有候选同罚，失去证伪力。
    """
    selected_role = str(natal.get("selected_pattern", {}).get("role", ""))
    target_roles = EVENT_ROLES.get(str(event.get("type", "")), set())
    activated = 0
    for row in rows:
        evidence = row.get("bazi_evidence", {}) if isinstance(row, dict) else {}
        roles = set(_roles_from_evidence(evidence.get("annual_ten_gods", {}), natal.get("day_master", "")))
        interactions = evidence.get("branch_interactions", []) if isinstance(evidence, dict) else []
        theme_fire = _role_matches(selected_role, roles) or _event_roles_match(roles, target_roles)
        hour_trip = any(
            isinstance(item, dict) and str(item.get("pillar", "")) == "hour" for item in interactions
        )
        if (theme_fire and interactions) or hour_trip:
            activated += 1
    misses = activated
    penalty = min(penalty_cap, misses * per_year_penalty)
    return {
        "status": status, "score": round(0.7 - penalty, 4), "penalty": round(penalty, 4),
        "counterexample_count": len(rows), "activated_counterexamples": activated,
        "reason": "反例年份对出现相同结构、却未发生对应事件的强断施加惩罚。",
    }


def _counterexample_year(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1 <= year <= 9999 else None


def _precise_role(day_master: str, stem: str) -> str:
    source_element = STEM_ELEMENTS.get(day_master, "")
    target_element = STEM_ELEMENTS.get(stem, "")
    if not source_element or not target_element:
        return "unknown"
    same_polarity = STEMS.index(day_master) % 2 == STEMS.index(stem) % 2
    if target_element == source_element:
        return "peer"
    if GENERATES[source_element] == target_element:
        return "food_god" if same_polarity else "hurting_officer"
    if CONTROLS[source_element] == target_element:
        return "indirect_wealth" if same_polarity else "direct_wealth"
    if CONTROLS[target_element] == source_element:
        return "seven_killings" if same_polarity else "direct_officer"
    return "indirect_resource" if same_polarity else "direct_resource"


def _roles_from_evidence(values: object, day_master: str) -> list[str]:
    if not isinstance(values, dict):
        return []
    roles: list[str] = []
    for value in values.values():
        text = str(value)
        if text in PATTERN_BY_ROLE:
            roles.append(text)
        elif text in {"wealth", "authority", "resource", "expression", "peer"}:
            roles.append(text)
        elif day_master and text in STEM_ELEMENTS:
            roles.append(_precise_role(day_master, text))
    return roles


def _role_matches(expected: str, observed: set[str]) -> bool:
    if expected in observed:
        return True
    return any(expected in ROLE_FAMILIES.get(role, set()) for role in observed)


def _event_roles_match(observed: set[str], targets: set[str]) -> bool:
    return any(_role_matches(target, observed) for target in targets)


def _event_month_resolution(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("month")
    explicit = value if isinstance(value, int) and 1 <= value <= 12 else None
    dated: int | None = None
    for key in ("date", "event_date"):
        raw = str(event.get(key, ""))
        try:
            dated = date.fromisoformat(raw[:10]).month
            break
        except ValueError:
            continue
    if explicit is not None and dated is not None and explicit != dated:
        return {"status": "conflict", "month": None, "reason": "事件月份与 ISO 日期月份冲突，无法判定流月历法。"}
    if explicit is not None:
        return {"status": "resolved", "month": explicit, "source": "event.month"}
    if dated is not None:
        return {"status": "resolved", "month": dated, "source": "iso_date"}
    return {"status": "missing", "month": None, "reason": "事件缺少可核验月份。"}


def _present(roles: set[str], targets: set[str], label: str) -> list[str]:
    return [label] if roles & targets else []


def _split_pillar(label: str) -> tuple[str, str]:
    for stem in STEMS:
        if label.startswith(stem):
            return stem, label[len(stem):]
    return "", ""


def _is_disruptive_event(event: dict[str, Any]) -> bool:
    return str(event.get("type", "")) in {"family_loss", "death", "health_crisis", "health_pressure", "public_scandal"}


def _empty_candidate() -> dict[str, Any]:
    return {"pattern": "未定格", "role": "unknown", "state": "待定", "score": 0.42, "summary": "月令信息不足，不能强定格局。"}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
