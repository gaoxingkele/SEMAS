"""Focused behavioural tests for the independent Hengmen rule engine."""

from examples.mingli_5agents.tools.hengmen_rule_engine import (
    analyze_natal_hengmen,
    score_hengmen_timing,
)
from examples.mingli_5agents.tools.bazi_hengmen_ahp import (
    build_hengmen_ahp_architecture,
    build_hengmen_chart_strategy,
    score_hengmen_event,
)
from examples.mingli_5agents.tools.mingli_book_ahp import score_book_framework_event
from examples.mingli_5agents.tools.bazi_deep_analysis import _hengmen_pattern_analysis


def test_officer_pattern_records_support_rescue_and_affection():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    selected = analysis["selected_pattern"]
    assert selected["pattern"] == "正官格"
    assert selected["state"] == "成格"
    assert "财生官" in selected["supporting_conditions"]
    assert selected["affection"]["state"] == "有情"


def test_officer_killing_mixture_is_a_failure_not_a_consensus_score():
    analysis = analyze_natal_hengmen(
        {"year": "GengShen", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    assert "官杀混杂" in analysis["selected_pattern"]["failure_conditions"]
    assert analysis["selected_pattern"]["state"] != "成格"


def test_clash_against_the_month_command_is_recorded_as_unaffection():
    analysis = analyze_natal_hengmen(
        {"year": "YiMao", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    assert analysis["selected_pattern"]["affection"]["state"] == "无情或受损"
    assert any(item["relation"] == "clash" for item in analysis["natal_relations"])


def test_monthly_evidence_and_counterexamples_are_explicit():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    event = {"type": "role_power", "month": 6, "counterexample_years": [1932, 1933]}
    annual = {
        "bazi_evidence": {
            "annual_ten_gods": {"stem": "direct_officer"},
            "active_major_luck": {"ganzhi": "GuiHai"},
            "branch_interactions": [{"relation": "combine", "pillar": "month"}],
        }
    }
    monthly = [
        {
            "month": 6,
            "bazi_evidence": {
                "monthly_pillar": "XinYou",
                "monthly_ten_gods": {"stem": "direct_officer"},
                "branch_interactions": [],
            },
        }
    ]

    result = score_hengmen_timing(
        natal, event, annual, monthly, [{**annual, "year": 1932}, {**annual, "year": 1933}]
    )

    assert result["monthly"]["status"] == "evaluated"
    assert result["counterfactual"]["status"] == "evaluated"
    assert result["counterfactual"]["penalty"] > 0


def test_counterexample_penalty_requires_rows_for_the_declared_years():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_timing(
        natal,
        {"type": "role_power", "counterexample_years": [1932, 1933]},
        {"bazi_evidence": {}},
        counterexample_rows=[{"year": 1932, "bazi_evidence": {}}],
    )

    receipt = result["counterfactual"]
    assert receipt["status"] == "counterexample_rows_missing"
    assert receipt["penalty"] == 0.0
    assert receipt["missing_years"] == [1933]


def test_derived_counterexample_rows_penalize_without_declared_years():
    # 未声明反例但提供了派生反例岁运行：按派生口径（0.05/年）惩罚，
    # 激活条件为“十神主题+地支引动”或“时柱被引动”。
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    derived_rows = [
        {
            "year": 1931,
            "bazi_evidence": {
                "annual_ten_gods": {"stem": "direct_officer"},
                "branch_interactions": [{"relation": "combine", "pillar": "hour"}],
            },
        }
    ]
    result = score_hengmen_timing(
        natal, {"type": "role_power"}, {"bazi_evidence": {}}, counterexample_rows=derived_rows
    )

    receipt = result["counterfactual"]
    assert receipt["status"] == "derived_counterexamples"
    assert receipt["activated_counterexamples"] == 1
    assert receipt["penalty"] == 0.05


def test_counterexample_activation_needs_theme_plus_interaction_or_hour_trip():
    # 旧口径“任意支关系即激活”会让所有候选同罚；新口径下，
    # 只有主题十神且存在引动、或时柱被引动才算反例激活。
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    rows = [
        {
            "year": 1931,
            "bazi_evidence": {
                "annual_ten_gods": {"stem": "indirect_resource"},
                "branch_interactions": [{"relation": "combine", "pillar": "year"}],
            },
        }
    ]
    result = score_hengmen_timing(
        natal,
        {"type": "role_power", "counterexample_years": [1931]},
        {"bazi_evidence": {}},
        counterexample_rows=rows,
    )

    receipt = result["counterfactual"]
    assert receipt["status"] == "evaluated"
    assert receipt["activated_counterexamples"] == 0
    assert receipt["penalty"] == 0.0


def test_conflicting_event_month_and_iso_date_keeps_monthly_timing_neutral():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_timing(
        natal,
        {"type": "role_power", "month": 6, "date": "1932-07-01"},
        {"bazi_evidence": {}},
        monthly_rows=[{"month": 6, "bazi_evidence": {"monthly_ten_gods": {"stem": "direct_officer"}}}],
    )

    assert result["monthly"]["status"] == "unresolved"
    assert result["monthly"]["score"] == 0.5
    assert "冲突" in result["monthly"]["reason"]


def test_event_topic_normalizes_friends_target_to_peer_evidence():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_event(
        {"type": "role_transition"},
        {"bazi_evidence": {"annual_ten_gods": {"stem": "peer"}, "branch_interactions": []}},
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
    )
    votes = {vote["id"]: vote["score"] for vote in result["votes"]}

    assert votes["event_ten_god"] == 0.78


def test_close_month_command_candidates_are_reported_and_discounted_in_ahp():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "JiaChou", "day": "JiaZi", "hour": "XinShen"}, "Jia"
    )
    strategy = build_hengmen_chart_strategy({"deep_analysis": {"hengmen_pattern_analysis": natal}})
    votes = {vote["id"]: vote["score"] for vote in strategy["votes"]}

    assert natal["pattern_selection"]["confidence"] == "low"
    assert natal["pattern_selection"]["ambiguous"] is True
    assert any(flag["id"] == "ambiguous_pattern_selection" for flag in natal["review_flags"])
    assert round(votes["month_pattern"], 4) == round(natal["selected_pattern"]["score"] - 0.08, 4)


def test_fact_calibration_combines_source_traceability_and_counterexamples():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    sourced = score_hengmen_event(
        {"type": "role_power", "year": 1932, "label": "Event", "source": "https://example.test/event"},
        {"bazi_evidence": {"annual_ten_gods": {}, "branch_interactions": []}},
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
    )
    unsourced = score_hengmen_event(
        {"type": "role_power"},
        {"bazi_evidence": {"annual_ten_gods": {}, "branch_interactions": []}},
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
    )

    sourced_fact = sourced["agent_receipts"]["fact_calibration"]
    unsourced_fact = unsourced["agent_receipts"]["fact_calibration"]
    assert sourced_fact["source_score"] == 0.82
    assert sourced_fact["score"] > unsourced_fact["score"]


def test_palace_trigger_distinguishes_event_nature_and_relation_type():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    row = {"bazi_evidence": {"annual_ten_gods": {}, "branch_interactions": [{"pillar": "month", "relation": "clash"}]}}
    positive = score_hengmen_event(
        {"type": "role_power"}, row, {"deep_analysis": {"hengmen_pattern_analysis": natal}}
    )
    disruptive = score_hengmen_event(
        {"type": "health_crisis"}, {"bazi_evidence": {"annual_ten_gods": {}, "branch_interactions": [{"pillar": "day", "relation": "clash"}]}},
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
    )
    positive_receipt = positive["agent_receipts"]["palace_trigger"]
    disruptive_receipt = disruptive["agent_receipts"]["palace_trigger"]

    assert positive_receipt["score"] == 0.62
    assert disruptive_receipt["score"] == 0.82
    assert disruptive_receipt["reason"] == "disruptive_relation_hits_event_palace"


def test_month_command_candidate_coverage_for_all_source_pattern_families():
    cases = [
        ("XinYou", "direct_officer"),
        ("JiChou", "direct_wealth"),
        ("GuiZi", "direct_resource"),
        ("BingSi", "food_god"),
        ("GengShen", "seven_killings"),
        ("DingWu", "hurting_officer"),
        ("JiaYin", "peer"),
    ]
    for month, expected_role in cases:
        analysis = analyze_natal_hengmen(
            {"year": "RenHai", "month": month, "day": "JiaZi", "hour": "WuChen"}, "Jia"
        )
        assert expected_role in {candidate["role"] for candidate in analysis["pattern_candidates"]}

    blade = analyze_natal_hengmen(
        {"year": "RenHai", "month": "JiaMao", "day": "JiaZi", "hour": "WuChen"}, "Jia"
    )
    assert blade["selected_pattern"]["special_pattern"] == "yang_blade"


def test_book_level_hengmen_profile_preserves_independent_agent_receipts():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_book_framework_event(
        "geju_hengmen_duan",
        {"type": "role_power"},
        {"bazi_evidence": {"annual_ten_gods": {"stem": "direct_officer"}, "branch_interactions": []}},
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
        {},
        {},
    )
    votes = {vote["agent_id"]: vote for vote in result["subagent_votes"]}

    assert "ahp_architecture" in result
    assert "rule_catalog" in result
    assert votes["rescue_agent"]["receipt"]["state"] == natal["selected_pattern"]["state"]
    assert "roots" in votes["stem_root_agent"]["receipt"]


def test_book_level_hengmen_profile_receives_monthly_and_counterexample_evidence():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    annual = {"bazi_evidence": {"annual_ten_gods": {"stem": "direct_officer"}, "branch_interactions": []}}
    result = score_book_framework_event(
        "geju_hengmen_duan",
        {"type": "role_power", "month": 6, "counterexample_years": [1932]},
        annual,
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
        {},
        {},
        [{"month": 6, "bazi_evidence": {"monthly_pillar": "XinYou", "monthly_ten_gods": {"stem": "direct_officer"}}}],
        [{"year": 1932, **annual}],
    )
    timing = result["rule_engine"]

    assert timing["monthly"]["status"] == "evaluated"
    assert timing["counterfactual"]["status"] == "evaluated"


def test_book_timing_agent_combines_major_luck_and_annual_monthly_votes():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    annual = {
        "bazi_evidence": {
            "annual_ten_gods": {"stem": "direct_officer"},
            "active_major_luck": {"ganzhi": "JiChou"},
            "branch_interactions": [],
        }
    }
    bazi = {"deep_analysis": {"hengmen_pattern_analysis": natal}}
    event = {"type": "role_power"}
    direct = score_hengmen_event(event, annual, bazi)
    book = score_book_framework_event("geju_hengmen_duan", event, annual, bazi, {}, {})
    direct_votes = {vote["id"]: vote["score"] for vote in direct["votes"]}
    timing_vote = next(vote for vote in book["subagent_votes"] if vote["agent_id"] == "timing_agent")
    expected = round((0.10 * direct_votes["luck_support"] + 0.08 * direct_votes["annual_interaction"]) / 0.18, 4)

    assert timing_vote["score"] == expected
    assert timing_vote["receipt"]["source_weights"] == {"luck_support": 0.10, "annual_interaction": 0.08}


def test_legacy_private_hengmen_entrypoint_delegates_to_v2_engine():
    analysis = _hengmen_pattern_analysis(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    assert analysis["schema_version"] == "hengmen-rule-engine-v2"
    assert "rule_catalog" in analysis


def test_invalid_pillar_labels_block_pattern_generation():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "JiaFoo", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    assert analysis["status"] == "invalid_pillars"
    assert analysis["invalid_pillars"] == ["month"]
    assert analysis["pattern_candidates"] == []
    assert analysis["review_flags"][0]["severity"] == "blocking"
    assert analysis["rule_catalog"]["summary"]["implemented"] == 10
    assert analysis["agent_receipts"]["blocking"]["invalid_pillars"] == ["month"]


def test_invalid_pillars_block_chart_and_event_ahp_scores():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "JiaFoo", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    bazi = {"deep_analysis": {"hengmen_pattern_analysis": natal}}
    chart = build_hengmen_chart_strategy(bazi)
    event = score_hengmen_event({"type": "role_power"}, {"bazi_evidence": {}}, bazi)

    assert chart["blocked"] is True and chart["chart_score"] == 0.0
    assert event["blocked"] is True and event["score"] == 0.0


def test_missing_event_month_stays_neutral_instead_of_selecting_best_month():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_timing(natal, {"type": "role_power"}, {"bazi_evidence": {}}, [])

    assert result["monthly"] == {
        "status": "unresolved",
        "score": 0.5,
        "reason": "事件缺少可核验月份或未提供流月行；不以最佳月份补偿。",
    }


def test_coarse_annual_ten_god_evidence_matches_precise_pattern_family():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_timing(
        natal,
        {"type": "role_power"},
        {"bazi_evidence": {"annual_ten_gods": {"stem": "authority"}, "branch_interactions": []}},
    )

    assert "流年透出或引动主格十神" in result["reasons"]


def test_storage_month_uses_all_hidden_stems_and_requires_exposure():
    analysis = analyze_natal_hengmen(
        {"year": "YiMao", "month": "WuChen", "day": "JiaZi", "hour": "XinYou"}, "Jia"
    )

    treasury = next(item for item in analysis["special_structures"]["treasuries"] if item["pillar"] == "month")
    assert treasury["hidden_stems"] == ["Wu", "Yi", "Gui"]
    assert treasury["month_command_requires_exposure"] is True
    assert "Wu" in treasury["exposed_hidden_stems"]


def test_storage_clash_is_explicit_activation_evidence_not_a_standalone_outcome():
    natal = analyze_natal_hengmen(
        {"year": "YiMao", "month": "WuChen", "day": "JiaZi", "hour": "XinYou"}, "Jia"
    )
    result = score_hengmen_timing(
        natal,
        {"type": "role_power"},
        {"bazi_evidence": {"annual_pillar": "GengXu", "annual_ten_gods": {}, "branch_interactions": []}},
    )

    opened = result["structure_activation"]["annual_opened_storages"]
    assert opened == [{"pillar": "month", "branch": "Chen", "by": "Xu"}]
    assert result["structure_activation"]["annual_delta"] == 0.03


def test_combine_direction_and_virtual_trine_remain_candidate_evidence():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    combine = analysis["special_structures"]["combine_direction"]
    virtual = analysis["special_structures"]["virtual_structures"]
    assert any(row["day_branch_combined_away_risk"] for row in combine)
    assert all(row["status"] == "candidate_only" for row in combine)
    assert any(row["status"] == "needs_corroboration" for row in virtual)


def test_head_foot_reports_supported_and_blocked_without_predicting_events():
    analysis = analyze_natal_hengmen(
        {"year": "GengYin", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )

    rows = analysis["special_structures"]["head_foot"]
    assert any(row["status"] == "supported" for row in rows)
    assert any(row["status"] == "blocked" for row in rows)


def test_yang_blade_is_not_collapsed_into_generic_peer_pattern():
    analysis = analyze_natal_hengmen(
        {"year": "GengShen", "month": "JiaMao", "day": "JiaZi", "hour": "BingYin"}, "Jia"
    )

    selected = analysis["selected_pattern"]
    coverage = analysis["rule_coverage"]
    assert selected["pattern"] == "阳刃格"
    assert selected["special_pattern"] == "yang_blade"
    assert coverage["yang_blade_month_command"] is True
    assert "yang_blade" in coverage["source_pattern_families"]


def test_non_blade_peer_month_does_not_claim_yang_blade():
    analysis = analyze_natal_hengmen(
        {"year": "GengShen", "month": "JiaYin", "day": "JiaZi", "hour": "BingYin"}, "Jia"
    )

    assert analysis["rule_coverage"]["yang_blade_month_command"] is False
    assert all(candidate.get("special_pattern") != "yang_blade" for candidate in analysis["pattern_candidates"])


def test_ahp_exposes_rule_coverage_for_audit():
    natal = analyze_natal_hengmen(
        {"year": "GengShen", "month": "JiaMao", "day": "JiaZi", "hour": "BingYin"}, "Jia"
    )
    strategy = build_hengmen_chart_strategy({"deep_analysis": {"hengmen_pattern_analysis": natal}})

    assert strategy["rule_coverage"] == natal["rule_coverage"]
    assert strategy["rule_coverage"]["yang_blade_month_command"] is True


def test_ahp_keeps_luck_annual_monthly_dimensions_separate():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_event(
        {"type": "role_power", "month": 6},
        {
            "bazi_evidence": {
                "annual_pillar": "XinYou",
                "annual_ten_gods": {"stem": "direct_officer"},
                "active_major_luck": {},
                "branch_interactions": [],
            }
        },
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
        [{"month": 6, "bazi_evidence": {"monthly_pillar": "XinYou", "monthly_ten_gods": {"stem": "direct_officer"}}}],
    )

    votes = {vote["id"]: vote["score"] for vote in result["votes"]}
    assert votes["event_ten_god"] == 0.78
    assert votes["luck_support"] == 0.42
    assert votes["annual_interaction"] == result["timing_dimensions"]["combined"]
    assert result["timing_dimensions"]["monthly"]["status"] == "evaluated"


def test_jianlu_peer_does_not_fail_merely_because_day_master_exists():
    analysis = analyze_natal_hengmen(
        {"year": "GengShen", "month": "JiaYin", "day": "JiaZi", "hour": "BingWu"}, "Jia"
    )

    peer_candidate = next(candidate for candidate in analysis["pattern_candidates"] if candidate["role"] == "peer")
    assert "食伤泄劫" in peer_candidate["supporting_conditions"]
    assert "禄劫无官财食伤承接" not in peer_candidate["failure_conditions"]
    assert "春木见火，木火通明" in peer_candidate["supporting_conditions"]


def test_jianlu_peer_records_autumn_metal_water_refinement():
    analysis = analyze_natal_hengmen(
        {"year": "RenZi", "month": "GengShen", "day": "GengChen", "hour": "RenXu"}, "Geng"
    )
    peer_candidate = next(candidate for candidate in analysis["pattern_candidates"] if candidate["role"] == "peer")

    assert "秋金见水，金水相涵" in peer_candidate["supporting_conditions"]


def test_yang_blade_requires_authority_control_and_records_failure_without_it():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "JiaMao", "day": "JiaZi", "hour": "BingYin"}, "Jia"
    )

    selected = analysis["selected_pattern"]
    assert selected["pattern"] == "阳刃格"
    assert "阳刃未见官杀制约" in selected["failure_conditions"]
    assert selected["state"] != "成格"


def test_yang_blade_records_officer_killing_control_and_companion_conditions():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "JiaMao", "day": "JiaZi", "hour": "GengShen"}, "Jia"
    )

    selected = analysis["selected_pattern"]
    assert "官杀制刃" in selected["supporting_conditions"]
    assert "财印相随官杀" not in selected["supporting_conditions"]


def test_wealth_pattern_distinguishes_food_god_from_hurting_officer_generation():
    food_analysis = analyze_natal_hengmen(
        {"year": "BingYin", "month": "JiChou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    hurt_analysis = analyze_natal_hengmen(
        {"year": "DingMao", "month": "JiChou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    food_wealth = next(item for item in food_analysis["pattern_candidates"] if item["role"] == "direct_wealth")
    hurt_wealth = next(item for item in hurt_analysis["pattern_candidates"] if item["role"] == "direct_wealth")

    assert "食神生财" in food_wealth["supporting_conditions"]
    assert "伤官生财待清" in hurt_wealth["failure_conditions"]
    assert "食神生财" not in hurt_wealth["supporting_conditions"]


def test_food_god_with_wealth_and_killing_records_exposed_killing_failure():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "BingSi", "day": "JiaZi", "hour": "GengShen"}, "Jia"
    )
    food = next(item for item in analysis["pattern_candidates"] if item["role"] == "food_god")

    assert "食神生财露杀" in food["failure_conditions"]
    assert "食神制杀" not in food["rescue_conditions"]


def test_killing_mixture_can_record_food_controlled_clearing_as_rescue():
    analysis = analyze_natal_hengmen(
        {"year": "XinYou", "month": "GengShen", "day": "JiaZi", "hour": "BingYin"}, "Jia"
    )
    killing = next(item for item in analysis["pattern_candidates"] if item["role"] == "seven_killings")

    assert "官杀混杂" in killing["failure_conditions"]
    assert "食制杀留官取清" in killing["rescue_conditions"]


def test_major_luck_is_scored_by_pattern_compatibility_not_mere_presence():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    supportive = score_hengmen_timing(
        natal,
        {"type": "role_power"},
        {"bazi_evidence": {"annual_ten_gods": {}, "active_major_luck": {"ganzhi": "JiChou"}}},
    )
    adverse = score_hengmen_timing(
        natal,
        {"type": "role_power"},
        {"bazi_evidence": {"annual_ten_gods": {}, "active_major_luck": {"ganzhi": "DingMao"}}},
    )

    assert supportive["major_luck"]["status"] == "evaluated"
    assert supportive["major_luck"]["score"] > adverse["major_luck"]["score"]
    assert "direct_wealth" in supportive["major_luck"]["support_hits"]
    assert "hurting_officer" in adverse["major_luck"]["adverse_hits"]


def test_combination_affection_records_what_it_brings_to_pattern_root():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "GuiZi", "day": "BingYin", "hour": "JiaChen"}, "Bing"
    )

    directed = analysis["selected_pattern"]["affection"]["directed_combinations"]
    assert any(row["effect"] == "brings_support" for row in directed)
    assert any("Water" in row["supports"] for row in directed)


def test_unrelated_branch_disruption_does_not_damage_pattern_affection():
    analysis = analyze_natal_hengmen(
        {"year": "GengYin", "month": "XinYou", "day": "JiaHai", "hour": "RenShen"}, "Jia"
    )

    affection = analysis["selected_pattern"]["affection"]
    assert any(row["relation"] == "clash" for row in analysis["natal_relations"])
    assert affection["root_pillars"] == ["month"]
    assert affection["disruptions"] == []


def test_repeated_virtual_trine_is_stronger_evidence_but_not_a_pattern_candidate():
    analysis = analyze_natal_hengmen(
        {"year": "JiaYin", "month": "JiXu", "day": "JiaYin", "hour": "JiXu"}, "Jia"
    )
    virtual = next(
        item for item in analysis["special_structures"]["virtual_structures"]
        if item["element"] == "Fire"
    )

    assert virtual["pair_count"] == 4
    assert virtual["status"] == "repeated_candidate"
    assert "cannot create a pattern candidate" in virtual["candidate_boundary"]
    assert any(flag["id"] == "virtual_structure" for flag in analysis["review_flags"])


def test_named_agent_receipts_expose_each_hengmen_reasoning_layer():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    result = score_hengmen_event(
        {"type": "role_power", "month": 6},
        {"bazi_evidence": {"annual_ten_gods": {"stem": "direct_officer"}, "branch_interactions": []}},
        {"deep_analysis": {"hengmen_pattern_analysis": natal}},
        [{"month": 6, "bazi_evidence": {"monthly_pillar": "XinYou", "monthly_ten_gods": {"stem": "direct_officer"}}}],
    )

    assert {"month_command_pattern", "success_failure_rescue", "branch_affection", "structure_evidence", "review_flags"} <= set(natal["agent_receipts"])
    assert {"event_ten_god", "palace_trigger", "annual_monthly_timing", "falsification"} <= set(result["agent_receipts"])
    assert result["agent_receipts"]["annual_monthly_timing"]["monthly"]["status"] == "evaluated"


def test_ahp_architecture_is_reciprocal_and_explicitly_consistent():
    architecture = build_hengmen_ahp_architecture()
    matrix = architecture["pairwise_matrix"]

    assert round(sum(architecture["weights"].values()), 8) == 1.0
    assert architecture["consistency"]["consistency_ratio"] == 0.0
    assert round(matrix["month_pattern"]["stem_root"] * matrix["stem_root"]["month_pattern"], 7) == 1.0


def test_rule_catalog_distinguishes_executable_rules_from_human_review():
    natal = analyze_natal_hengmen(
        {"year": "JiChou", "month": "XinYou", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    catalog = natal["rule_catalog"]
    statuses = {row["id"]: row["status"] for row in catalog["rules"]}

    assert catalog["summary"] == {"implemented": 10, "partial": 1, "human_review": 1}
    assert statuses["annual_monthly_timing"] == "implemented"
    assert statuses["life_outcome_assertions"] == "human_review"


def test_hurting_officer_records_stem_order_without_overclaiming_finance_resource_harmony():
    analysis = analyze_natal_hengmen(
        {"year": "JiChou", "month": "DingWu", "day": "JiaZi", "hour": "RenShen"}, "Jia"
    )
    hurting = next(item for item in analysis["pattern_candidates"] if item["role"] == "hurting_officer")
    ordering = hurting["ordering_evidence"]

    assert ordering["wealth_resource_separated"] is True
    assert ordering["status"] == "needs_corroboration"
    assert "完整命局语境" in ordering["interpretation"]
