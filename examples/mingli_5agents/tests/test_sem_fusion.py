"""Tests for the SEM fusion layer (sem_fusion.py).

Covers: measurement-model loadings recovery on synthetic data, the LOCO
pipeline end-to-end on a synthetic dataset, predict() output shape/range, and
per-candidate feature extraction. Uses synthetic data only; the real
calibration pipeline is not exercised here (it is covered by the batch
validation tests elsewhere).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.case_studies.hour_calibration.sem_fusion import (  # noqa: E402
    FEATURE_NAMES,
    _candidate_features,
    dataset_xy,
    fit_sem,
    loadings_table,
    loco_evaluate,
    predict,
)


def _synthetic_sem_data(n: int = 400, seed: int = 7):
    """One latent factor -> indicators (known loadings) and label (logit)."""
    rng = np.random.default_rng(seed)
    true_loadings = np.array([0.8, 0.7, 0.6, 0.5, -0.4, 0.3])
    p = len(true_loadings)
    eta = rng.normal(size=n)
    X = eta[:, None] * true_loadings[None, :] + rng.normal(size=(n, p)) * np.sqrt(1 - true_loadings**2)
    prob = 1.0 / (1.0 + np.exp(-(-1.0 + 1.5 * eta)))
    y = (rng.uniform(size=n) < prob).astype(float)
    return X, y, true_loadings


def test_loadings_recovery_on_synthetic_data():
    X, y, true_loadings = _synthetic_sem_data()
    model = fit_sem(X, y)
    estimated = np.asarray(model["loadings"])
    # Sign is fixed so sum(loadings) >= 0; recovery is judged up to that sign.
    correlation = float(np.corrcoef(estimated, true_loadings)[0, 1])
    assert correlation > 0.95
    assert np.all(np.asarray(model["uniqueness"]) > 0)
    # Structural coefficient should be positive (factor -> label is positive).
    assert model["logit_beta"][1] > 0


def test_predict_shape_and_probability_range():
    X, y, _ = _synthetic_sem_data(n=200, seed=11)
    model = fit_sem(X[:150], y[:150])
    probabilities = predict(model, X[150:])
    assert probabilities.shape == (50,)
    assert np.all(probabilities >= 0.0)
    assert np.all(probabilities <= 1.0)
    # Single row works too and stays in range.
    single = predict(model, X[150:151])
    assert single.shape == (1,)
    assert 0.0 <= single[0] <= 1.0


def _synthetic_dataset(case_count: int = 5, candidates: int = 4, seed: int = 3) -> dict:
    """Synthetic case/candidate dataset with a learnable signal."""
    rng = np.random.default_rng(seed)
    feature_names = FEATURE_NAMES[:6]  # small feature set keeps the test fast
    rows = []
    for case_index in range(case_count):
        reference_index = int(rng.integers(0, candidates))
        for candidate_index in range(candidates):
            is_reference = candidate_index == reference_index
            base = 0.25 if is_reference else 0.0
            features = {
                name: float(np.clip(rng.normal(base + 0.5, 0.08), 0.0, 1.0)) for name in feature_names
            }
            rows.append(
                {
                    "case_id": f"case_{case_index}",
                    "case_name": f"Case {case_index}",
                    "hour_label": f"hour_{candidate_index}",
                    "hour_branch": f"B{candidate_index}",
                    "is_reference": is_reference,
                    "strategy_total": features[feature_names[0]],
                    "hengmen_school_score": features[feature_names[1]],
                    "features": features,
                }
            )
    return {
        "schema_version": "sem-fusion-dataset-v1",
        "feature_names": feature_names,
        "case_count": case_count,
        "row_count": len(rows),
        "rows": rows,
    }


def test_loco_pipeline_runs_end_to_end():
    dataset = _synthetic_dataset()
    result = loco_evaluate(dataset)
    assert result["case_count"] == 5
    assert len(result["per_case"]) == 5
    for method in ("sem", "equal_weight", "composite_ahp", "hengmen_school"):
        metrics = result["summary"][method]
        assert 1.0 <= metrics["mean_reference_rank"] <= 4.0
        assert 0 <= metrics["top1_count"] <= 5
        assert metrics["top1_count"] <= metrics["top3_count"] <= 5
    for case_row in result["per_case"]:
        for rank in case_row["ranks"].values():
            assert 1 <= rank <= 4


def test_loco_sem_uses_signal_better_than_chance():
    dataset = _synthetic_dataset(case_count=8, candidates=4, seed=5)
    result = loco_evaluate(dataset)
    # With a strong planted signal, SEM LOCO mean rank should beat the random
    # expectation of (4 + 1) / 2 = 2.5 on this synthetic set.
    assert result["summary"]["sem"]["mean_reference_rank"] <= 2.5


def test_candidate_feature_extraction_schema():
    candidate = {
        "score": {"event_fit_total": 0.6, "chart_strategy_total": 0.5},
        "bazi_school_ahp_totals": {school: {"score": 0.4} for school in
                                  ["yuanhai_ziping", "ziping_zhenquan", "sanming_tonghui", "ditiansui",
                                   "qiongtong_baojian", "shenfeng_tongkao", "hengmen"]},
        "book_ahp_totals": {book: {"score": 0.3} for book in
                            ["yuanhai_ziping", "ziping_zhenquan", "mingli_jicheng", "lixuzhong_mingshu",
                             "yuzhao_dingzhenjing", "xingping_huihai", "ziwei_doushu_quanshu",
                             "christian_astrology", "geju_hengmen_duan"]},
        "event_scores": [
            {"hengmen_ahp": {"votes": [{"id": name, "score": 0.5} for name in
                                       ["month_pattern", "stem_root", "success_rescue", "event_ten_god",
                                        "palace_trigger", "luck_support", "annual_interaction",
                                        "fact_calibration"]]}},
            {"hengmen_ahp": {"votes": [{"id": name, "score": 0.7} for name in
                                       ["month_pattern", "stem_root", "success_rescue", "event_ten_god",
                                        "palace_trigger", "luck_support", "annual_interaction",
                                        "fact_calibration"]]}},
        ],
    }
    events = [{"weight": 1.0}, {"weight": 3.0}]
    features = _candidate_features(candidate, events)
    assert set(features) == set(FEATURE_NAMES)
    # Weighted mean of 0.5 (w=1) and 0.7 (w=3) = 0.65.
    assert features["hengmen_vote_month_pattern"] == 0.65
    assert features["school_hengmen"] == 0.4
    assert features["book_geju_hengmen_duan"] == 0.3
    assert features["event_fit_total"] == 0.6
    assert features["chart_strategy_total"] == 0.5


def test_dataset_xy_and_loadings_table_shapes():
    dataset = _synthetic_dataset()
    X, y = dataset_xy(dataset["rows"], dataset["feature_names"])
    assert X.shape == (20, 6)
    assert y.shape == (20,)
    assert y.sum() == 5.0
    model = fit_sem(X, y)
    table = loadings_table(model, dataset["feature_names"])
    assert len(table) == 6
    assert all(set(row) == {"feature", "loading", "uniqueness"} for row in table)


# ---------------------------------------------------------------------------
# v2: within-case standardization, screening/parceling, Bradley-Terry SEM
# ---------------------------------------------------------------------------

from examples.mingli_5agents.case_studies.hour_calibration.sem_fusion import (  # noqa: E402
    LLM_PARCEL,
    SCREEN_EXCLUDE,
    build_parcels,
    fit_sem_v2,
    load_llm_scores,
    loco_evaluate_v2,
    make_reference_pairs,
    predict_v2,
    screen_features,
    within_case_standardize,
)

V2_FEATURE_NAMES = (
    ["hengmen_vote_month_pattern", "hengmen_vote_stem_root", "hengmen_vote_success_rescue"]
    + ["school_hengmen", "school_ditiansui", "school_ziping_zhenquan"]
    + ["book_mingli_jicheng", "book_geju_hengmen_duan", "book_christian_astrology"]
)


def _v2_synthetic_dataset(case_count: int = 6, candidates: int = 6, seed: int = 17) -> dict:
    """Synthetic v2 dataset: a latent per-candidate quality drives one school,
    one book and one hengmen feature plus the reference label."""
    rng = np.random.default_rng(seed)
    rows = []
    for case_index in range(case_count):
        shift = float(rng.normal(0.0, 3.0))  # large case-level offset: centering matters
        quality = rng.normal(size=candidates)
        reference_index = int(np.argmax(quality))
        for candidate_index in range(candidates):
            q = quality[candidate_index]
            features = {
                "hengmen_vote_month_pattern": 0.5 + shift + 0.3 * q + float(rng.normal(0, 0.1)),
                "hengmen_vote_stem_root": 0.5 + shift + float(rng.normal(0, 0.15)),
                "hengmen_vote_success_rescue": 0.5 + shift + 0.2 * q + float(rng.normal(0, 0.1)),
                "school_hengmen": 0.6 + shift + 0.4 * q + float(rng.normal(0, 0.1)),
                "school_ditiansui": 0.7 + shift,  # constant within case: zero spread
                "school_ziping_zhenquan": 0.6 + shift + 0.3 * q + float(rng.normal(0, 0.1)),
                "book_mingli_jicheng": 0.55 + shift + 0.3 * q + float(rng.normal(0, 0.1)),
                "book_geju_hengmen_duan": 0.55 + shift + 0.2 * q + float(rng.normal(0, 0.1)),
                "book_christian_astrology": 0.5 + shift,  # constant within case: zero spread
            }
            rows.append(
                {
                    "case_id": f"case_{case_index}",
                    "case_name": f"Case {case_index}",
                    "hour_label": f"hour_{candidate_index}",
                    "hour_branch": f"B{candidate_index}",
                    "is_reference": candidate_index == reference_index,
                    "strategy_total": 0.5,
                    "hengmen_school_score": 0.5,
                    "features": features,
                }
            )
    return {
        "schema_version": "sem-fusion-dataset-v1",
        "feature_names": list(V2_FEATURE_NAMES),
        "case_count": case_count,
        "row_count": len(rows),
        "rows": rows,
    }


def test_within_case_standardize_properties():
    dataset = _v2_synthetic_dataset(case_count=3)
    z_rows = within_case_standardize(dataset["rows"], dataset["feature_names"])
    assert all("features_z" in row for row in z_rows)
    assert all("features" in row for row in z_rows)  # raw values preserved
    for case_index in range(3):
        case_rows = [row for row in z_rows if row["case_id"] == f"case_{case_index}"]
        for name in ("hengmen_vote_month_pattern", "school_hengmen"):
            values = np.array([row["features_z"][name] for row in case_rows])
            assert abs(float(values.mean())) < 1e-9
            assert abs(float(values.std()) - 1.0) < 1e-6
        # zero-spread feature maps to all-zero z-scores
        zeros = [row["features_z"]["school_ditiansui"] for row in case_rows]
        assert all(value == 0.0 for value in zeros)


def test_screen_features_drops_zero_spread_and_excluded():
    dataset = _v2_synthetic_dataset(case_count=3)
    parcels = screen_features(dataset["rows"], dataset["feature_names"])
    all_members = [name for members in parcels.values() for name in members]
    assert "school_ditiansui" not in all_members  # zero within-case spread
    assert "book_christian_astrology" not in all_members
    assert not any(name in SCREEN_EXCLUDE for name in all_members)
    assert "school_hengmen" in parcels["schools"]
    assert "book_mingli_jicheng" in parcels["books"]
    assert "hengmen_vote_month_pattern" in parcels["hengmen_votes"]
    assert set(parcels) == {"hengmen_votes", "schools", "books"}


def test_load_llm_scores_mapping():
    scores = load_llm_scores()
    assert len(scores) == 11
    for case_scores in scores.values():
        assert len(case_scores) == 12
        assert sorted(case_scores.values()) == list(range(1, 13))  # 13 - rank
    # mao_zedong: 辰时 ranked 1st in the analysis file -> score 12
    assert scores["mao_zedong_public_events"]["辰时"] == 12.0
    assert scores["mao_zedong_public_events"]["子时"] == 1.0


def test_build_parcels_and_llm_zscore():
    dataset = _v2_synthetic_dataset(case_count=2)
    z_rows = within_case_standardize(dataset["rows"], dataset["feature_names"])
    parcels = screen_features(dataset["rows"], dataset["feature_names"])
    llm_scores = {
        f"case_{i}": {f"hour_{j}": float(13 - (j + 1)) for j in range(6)} for i in range(2)
    }
    parcel_rows, parcel_names = build_parcels(z_rows, parcels, llm_scores)
    assert parcel_names == ["hengmen_votes", "schools", "books", LLM_PARCEL]
    case_rows = [row for row in parcel_rows if row["case_id"] == "case_0"]
    hengmen_manual = np.mean(
        [[row["features_z"][m] for m in parcels["hengmen_votes"]] for row in case_rows], axis=1
    )
    assert np.allclose([row["parcels"]["hengmen_votes"] for row in case_rows], hengmen_manual)
    llm_values = np.array([row["parcels"][LLM_PARCEL] for row in case_rows])
    assert abs(float(llm_values.mean())) < 1e-9  # within-case z-scored


def test_make_reference_pairs_counts():
    dataset = _v2_synthetic_dataset(case_count=2, candidates=6)
    pairs = make_reference_pairs(dataset["rows"][:6])
    assert len(pairs) == 5  # reference vs each non-reference within the case
    for i, j in pairs:
        assert dataset["rows"][i]["is_reference"]
        assert not dataset["rows"][j]["is_reference"]


def test_bt_joint_recovers_ranking_weights():
    """Planted linear ranking rule must be recovered by the BT joint fit."""
    rng = np.random.default_rng(23)
    true_w = np.array([2.0, 0.5, -0.3])
    rows = []
    for case_index in range(8):
        Z = rng.normal(size=(10, 3))
        quality = Z @ true_w + rng.normal(0, 0.3, size=10)
        reference = int(np.argmax(quality))
        for candidate_index in range(10):
            rows.append(
                {
                    "case_id": f"case_{case_index}",
                    "is_reference": candidate_index == reference,
                    "z": Z[candidate_index],
                }
            )
    X = np.array([row["z"] for row in rows])
    y = np.array([1.0 if row["is_reference"] else 0.0 for row in rows])
    model = fit_sem_v2(X, y, make_reference_pairs(rows), "bt")
    estimated = model["bt_weights"] / np.linalg.norm(model["bt_weights"])
    cosine = float(estimated @ (true_w / np.linalg.norm(true_w)))
    assert cosine > 0.9
    # recovered scores place the reference first in most training cases
    scores = predict_v2(model, X)
    hits = 0
    for case_index in range(8):
        case_scores = scores[case_index * 10 : (case_index + 1) * 10]
        reference = case_index * 10 + int(np.argmax([row["is_reference"] for row in rows[case_index * 10 : (case_index + 1) * 10]]))
        hits += int(np.argmax(case_scores) == reference % 10)
    assert hits >= 6




def test_loco_v2_pipeline_and_signal_recovery():
    dataset = _v2_synthetic_dataset(case_count=6, candidates=6)
    result = loco_evaluate_v2(dataset, structural="bt", use_llm=False)
    assert result["case_count"] == 6
    assert result["indicators"] == ["hengmen_votes", "schools", "books"]
    for method in ("sem_v2", "equal_weight", "composite_ahp", "hengmen_school", "equal_weight_parcel"):
        metrics = result["summary"][method]
        assert 1.0 <= metrics["mean_reference_rank"] <= 6.0
        assert metrics["top1_count"] <= metrics["top3_count"] <= 6
    # planted signal: SEM should beat the random expectation of 3.5
    assert result["summary"]["sem_v2"]["mean_reference_rank"] <= 3.5


def test_loco_v2_llm_variant_adds_llm_method():
    dataset = _v2_synthetic_dataset(case_count=4, candidates=6)
    llm_scores = {
        f"case_{i}": {f"hour_{j}": float(13 - (j + 1)) for j in range(6)} for i in range(4)
    }
    result = loco_evaluate_v2(dataset, structural="bt", use_llm=True, llm_scores=llm_scores)
    assert "llm_only" in result["summary"]
    assert result["indicators"][-1] == LLM_PARCEL
    assert 1.0 <= result["summary"]["llm_only"]["mean_reference_rank"] <= 6.0


def test_predict_v2_shape():
    dataset = _v2_synthetic_dataset(case_count=3, candidates=6)
    z_rows = within_case_standardize(dataset["rows"], dataset["feature_names"])
    parcels = screen_features(dataset["rows"], dataset["feature_names"])
    parcel_rows, parcel_names = build_parcels(z_rows, parcels)
    X = np.array([[row["parcels"][name] for name in parcel_names] for row in parcel_rows])
    y = np.array([1.0 if row["is_reference"] else 0.0 for row in parcel_rows])
    model = fit_sem_v2(X, y, make_reference_pairs(parcel_rows), "bt")
    scores = predict_v2(model, X[:6])
    assert scores.shape == (6,)
    assert np.all(np.isfinite(scores))


def test_cascade_stage1_topk_orders_by_parcel_equal_weight():
    from examples.mingli_5agents.case_studies.hour_calibration.cascade_eval import (
        parcel_equal_weight,
        stage1_topk,
    )

    rows = [
        {"hour_label": "子时", "parcels": {"hengmen_votes": 0.3, "schools": 0.3, "books": 0.3}},
        {"hour_label": "丑时", "parcels": {"hengmen_votes": 0.9, "schools": 0.9, "books": 0.9}},
        {"hour_label": "寅时", "parcels": {"hengmen_votes": 0.6, "schools": 0.6, "books": 0.6}},
    ]
    assert parcel_equal_weight(rows[1]) == 0.9
    assert [r["hour_label"] for r in stage1_topk(rows, 2)] == ["丑时", "寅时"]


def test_cascade_stage2_adjudication_and_reference_rank():
    from examples.mingli_5agents.case_studies.hour_calibration.cascade_eval import (
        cascade_rank,
        stage2_adjudicate,
    )

    topk = [{"hour_label": "丑时"}, {"hour_label": "寅时"}, {"hour_label": "子时"}]
    llm_ranking = ["寅", "卯", "丑", "子"]
    assert stage2_adjudicate(topk, llm_ranking) == ["寅", "丑", "子"]
    assert cascade_rank(topk, llm_ranking, "丑时") == 2
    assert cascade_rank(topk, llm_ranking, "寅时") == 1
