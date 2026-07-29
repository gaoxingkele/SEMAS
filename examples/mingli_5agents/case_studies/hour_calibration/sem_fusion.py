"""SEM fusion layer for twelve-hour BaZi calibration.

Builds a (case, candidate-hour) feature dataset from the existing calibration
pipeline, fits a restrained one-factor SEM (measurement: all observed score
dimensions load on a latent "hour-fit" factor with diagonal measurement error;
structural: latent factor -> is-public-reference-hour via a logit link), and
evaluates it with leave-one-case-out (LOCO) cross-validation against three
baselines: equal-weight average, the current composite AHP (strategy_total),
and the improved Hengmen single method.

Estimation is two-step ML with numpy/scipy only:
1. ML exploratory factor analysis (one factor) on standardized indicators.
2. Logistic regression of the reference label on regression (Thomson) factor
   scores.

This keeps the parameter count small (p loadings + p uniquenesses + 2 logit
coefficients) and avoids saturated models on a 132-row sample. The model is a
fusion experiment on top of existing scores; it does not change any
hengmen/bazi_* scoring logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.case_studies.hour_calibration.hour_calibration import (  # noqa: E402
    calibrate_case,
)
from examples.mingli_5agents.case_studies.hour_calibration.run_validation_batch import (  # noqa: E402
    DEFAULT_CASES,
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = BASE_DIR / "outputs" / "sem_fusion_dataset.json"
DEFAULT_LOCO_PATH = BASE_DIR / "outputs" / "sem_fusion_loco.json"

HENGMEN_VOTE_FEATURES = [
    "month_pattern",
    "stem_root",
    "success_rescue",
    "event_ten_god",
    "palace_trigger",
    "luck_support",
    "annual_interaction",
    "fact_calibration",
]
SCHOOL_FEATURES = [
    "yuanhai_ziping",
    "ziping_zhenquan",
    "sanming_tonghui",
    "ditiansui",
    "qiongtong_baojian",
    "shenfeng_tongkao",
    "hengmen",
]
BOOK_FEATURES = [
    "yuanhai_ziping",
    "ziping_zhenquan",
    "mingli_jicheng",
    "lixuzhong_mingshu",
    "yuzhao_dingzhenjing",
    "xingping_huihai",
    "ziwei_doushu_quanshu",
    "christian_astrology",
    "geju_hengmen_duan",
]
BASE_FEATURES = ["event_fit_total", "chart_strategy_total"]

FEATURE_NAMES = (
    [f"hengmen_vote_{name}" for name in HENGMEN_VOTE_FEATURES]
    + [f"school_{name}" for name in SCHOOL_FEATURES]
    + [f"book_{name}" for name in BOOK_FEATURES]
    + BASE_FEATURES
)


# ---------------------------------------------------------------------------
# Dataset construction
# ---------------------------------------------------------------------------


def _candidate_features(candidate: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, float]:
    """Extract the fusion feature vector for one (case, candidate-hour)."""
    features: dict[str, float] = {}
    weights = np.array([float(event.get("weight", 1.0) or 1.0) for event in events], dtype=float)
    weights = np.maximum(weights, 1e-6)
    event_scores = candidate.get("event_scores", [])
    vote_matrix: dict[str, list[float]] = {name: [] for name in HENGMEN_VOTE_FEATURES}
    for event_score in event_scores:
        votes = {vote.get("id"): float(vote.get("score", 0.0)) for vote in event_score.get("hengmen_ahp", {}).get("votes", [])}
        for name in HENGMEN_VOTE_FEATURES:
            vote_matrix[name].append(votes.get(name, 0.0))
    for name in HENGMEN_VOTE_FEATURES:
        values = np.array(vote_matrix[name], dtype=float)
        features[f"hengmen_vote_{name}"] = round(float(np.dot(values, weights) / weights.sum()), 6)
    for school_id in SCHOOL_FEATURES:
        features[f"school_{school_id}"] = round(
            float(candidate.get("bazi_school_ahp_totals", {}).get(school_id, {}).get("score", 0.0)), 6
        )
    for book_id in BOOK_FEATURES:
        features[f"book_{book_id}"] = round(
            float(candidate.get("book_ahp_totals", {}).get(book_id, {}).get("score", 0.0)), 6
        )
    score = candidate.get("score", {})
    features["event_fit_total"] = round(float(score.get("event_fit_total", 0.0)), 6)
    features["chart_strategy_total"] = round(float(score.get("chart_strategy_total", 0.0)), 6)
    return features


def equal_weight_hour_scores(
    case_result: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, float]:
    """Equal-weight fusion baseline: unweighted mean of all fusion features per hour label.

    LOCO evaluation (sem_fusion_report_2026-07-24.md) found this simple
    combiner to be the strongest fusion on the 11-case corpus.
    """
    scores: dict[str, float] = {}
    for candidate in case_result.get("ranking", []):
        features = _candidate_features(candidate, events)
        if features:
            scores[str(candidate.get("hour_label", ""))] = round(float(np.mean(list(features.values()))), 6)
    return scores


def build_dataset(
    case_dir: Path | None = None,
    case_names: list[str] | None = None,
    cache_path: Path | None = DEFAULT_DATASET_PATH,
    recompute: bool = False,
) -> dict[str, Any]:
    """Build (or load cached) the (case, candidate-hour) fusion dataset.

    Each row carries the 26-dim feature vector, the strategy_total and the
    improved-Hengmen school score (kept for baseline ranking), and the binary
    label ``is_reference`` (candidate hour matches a public reference hour).
    """
    if cache_path is not None and cache_path.exists() and not recompute:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    case_dir = case_dir or (BASE_DIR / "cases")
    case_names = case_names or list(DEFAULT_CASES)
    rows: list[dict[str, Any]] = []
    for name in case_names:
        path = case_dir / name
        case = json.loads(path.read_text(encoding="utf-8"))
        events = [event for event in case.get("events", []) if isinstance(event, dict) and event.get("year") is not None]
        result = calibrate_case(case)
        reference_labels = {
            str(ref.get("label", ""))
            for ref in result.get("reference_evaluation", {}).get("references", [])
            if isinstance(ref.get("rank"), int)
        }
        for candidate in result["ranking"]:
            rows.append(
                {
                    "case_id": result["case_id"],
                    "case_name": result["name"],
                    "hour_label": candidate["hour_label"],
                    "hour_branch": candidate["hour_branch"],
                    "is_reference": candidate["hour_label"] in reference_labels,
                    "strategy_total": float(candidate["score"]["strategy_total"]),
                    "hengmen_school_score": float(
                        candidate.get("bazi_school_ahp_totals", {}).get("hengmen", {}).get("score", 0.0)
                    ),
                    "features": _candidate_features(candidate, events),
                }
            )
    dataset = {
        "schema_version": "sem-fusion-dataset-v1",
        "feature_names": list(FEATURE_NAMES),
        "case_count": len({row["case_id"] for row in rows}),
        "row_count": len(rows),
        "rows": rows,
    }
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dataset


def dataset_xy(rows: list[dict[str, Any]], feature_names: list[str] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Materialize the design matrix X (n, p) and label vector y (n,)."""
    feature_names = feature_names or list(FEATURE_NAMES)
    X = np.array([[float(row["features"][name]) for name in feature_names] for row in rows], dtype=float)
    y = np.array([1.0 if row["is_reference"] else 0.0 for row in rows], dtype=float)
    return X, y


# ---------------------------------------------------------------------------
# One-factor SEM (two-step ML: factor analysis + logit on factor scores)
# ---------------------------------------------------------------------------


def _fa_ml_objective(params: np.ndarray, S: np.ndarray) -> tuple[float, np.ndarray]:
    """ML discrepancy F = log|Sigma| + tr(S Sigma^-1) for Sigma = ll' + diag(psi)."""
    p = S.shape[0]
    loadings = params[:p]
    psi = np.clip(params[p:], 1e-4, 50.0)
    Sigma = np.outer(loadings, loadings) + np.diag(psi)
    sign, logdet = np.linalg.slogdet(Sigma)
    if sign <= 0:
        return 1e6 + 1e3 * float(np.sum(params**2)), np.zeros_like(params)
    Sigma_inv = np.linalg.inv(Sigma)
    objective = logdet + float(np.trace(S @ Sigma_inv))
    # Analytic gradient: dF = Sigma^-1 (Sigma - S) Sigma^-1 dSigma
    G = Sigma_inv @ (Sigma - S) @ Sigma_inv
    grad = np.concatenate([2.0 * G @ loadings, np.diag(G)])
    return objective, grad


def fit_one_factor_ml(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Fit a one-factor ML factor analysis on (already standardized) X.

    Returns (loadings, uniquenesses, info). Var(factor) is fixed to 1 for
    identification; the sign of the factor is fixed so sum(loadings) >= 0.
    """
    X = np.asarray(X, dtype=float)
    n, p = X.shape
    S = (X.T @ X) / max(n, 1)
    # Init: first principal component loadings (scaled), uniqueness = 1 - communality.
    eigvals, eigvecs = np.linalg.eigh(S)
    first_pc = eigvecs[:, -1] * np.sqrt(max(eigvals[-1] - 1.0, 0.2))
    init_loadings = np.clip(first_pc, -0.95, 0.95)
    init_psi = np.clip(1.0 - init_loadings**2, 0.05, 50.0)
    x0 = np.concatenate([init_loadings, init_psi])
    bounds = [(None, None)] * p + [(1e-4, 50.0)] * p
    result = minimize(
        _fa_ml_objective,
        x0,
        args=(S,),
        jac=True,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 500},
    )
    params = result.x if np.isfinite(result.fun) else x0
    loadings = params[:p]
    psi = np.clip(params[p:], 1e-4, 50.0)
    if loadings.sum() < 0:  # fix sign indeterminacy
        loadings = -loadings
    info = {
        "objective": float(result.fun),
        "converged": bool(result.success),
        "n_obs": int(n),
        "n_indicators": int(p),
    }
    return loadings, psi, info


def _fit_logit(factor_scores: np.ndarray, y: np.ndarray) -> np.ndarray:
    """ML logistic regression y ~ [1, factor_scores]. Returns [beta0, beta1]."""

    def nll(beta: np.ndarray) -> float:
        eta = beta[0] + beta[1] * factor_scores
        return float(np.sum(np.logaddexp(0.0, eta) - y * eta))

    def grad(beta: np.ndarray) -> np.ndarray:
        eta = beta[0] + beta[1] * factor_scores
        residual = 1.0 / (1.0 + np.exp(-eta)) - y
        return np.array([residual.sum(), float(residual @ factor_scores)])

    result = minimize(nll, np.zeros(2), jac=grad, method="BFGS", options={"maxiter": 500})
    return result.x if np.isfinite(result.fun) else np.zeros(2)


def fit_sem(X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """Fit the one-factor SEM: measurement (FA) + structural (logit) model."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    Z = (X - mean) / std
    loadings, psi, fa_info = fit_one_factor_ml(Z)
    sigma_inv = np.linalg.inv(np.outer(loadings, loadings) + np.diag(psi))
    score_weights = sigma_inv @ loadings  # Thomson regression factor scores
    factor_scores = Z @ score_weights
    beta = _fit_logit(factor_scores, y)
    return {
        "feature_mean": mean,
        "feature_std": std,
        "loadings": loadings,
        "uniqueness": psi,
        "factor_score_weights": score_weights,
        "logit_beta": beta,
        "fa_info": fa_info,
    }


def predict(model: dict[str, Any], X: np.ndarray) -> np.ndarray:
    """Predict P(is_reference) for rows X (n, p). Returns probabilities (n,)."""
    X = np.atleast_2d(np.asarray(X, dtype=float))
    Z = (X - model["feature_mean"]) / model["feature_std"]
    factor_scores = Z @ model["factor_score_weights"]
    beta = model["logit_beta"]
    eta = np.clip(beta[0] + beta[1] * factor_scores, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-eta))


def loadings_table(model: dict[str, Any], feature_names: list[str] | None = None) -> list[dict[str, Any]]:
    """Human-readable measurement-model table (sorted by |loading|)."""
    feature_names = feature_names or list(FEATURE_NAMES)
    rows = [
        {"feature": name, "loading": round(float(load), 4), "uniqueness": round(float(psi), 4)}
        for name, load, psi in zip(feature_names, model["loadings"], model["uniqueness"])
    ]
    rows.sort(key=lambda row: -abs(row["loading"]))
    return rows


# ---------------------------------------------------------------------------
# LOCO evaluation
# ---------------------------------------------------------------------------


def _best_reference_rank(scores: np.ndarray, row_indices: list[int], rows: list[dict[str, Any]]) -> int:
    order = np.argsort(-scores, kind="stable")
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    reference_ranks = [ranks[i] for i in row_indices if rows[i]["is_reference"]]
    return int(min(reference_ranks)) if reference_ranks else 0


def loco_evaluate(dataset: dict[str, Any]) -> dict[str, Any]:
    """Leave-one-case-out evaluation of the SEM against three baselines."""
    rows = dataset["rows"]
    feature_names = dataset.get("feature_names", list(FEATURE_NAMES))
    case_ids = sorted({row["case_id"] for row in rows})
    methods = ["sem", "equal_weight", "composite_ahp", "hengmen_school"]
    per_method_ranks: dict[str, list[int]] = {method: [] for method in methods}
    per_case: list[dict[str, Any]] = []
    for held_out in case_ids:
        test_idx = [i for i, row in enumerate(rows) if row["case_id"] == held_out]
        train_rows = [row for row in rows if row["case_id"] != held_out]
        X_train, y_train = dataset_xy(train_rows, feature_names)
        test_rows = [rows[i] for i in test_idx]
        X_test, _ = dataset_xy(test_rows, feature_names)
        model = fit_sem(X_train, y_train)
        scores = {
            "sem": predict(model, X_test),
            "equal_weight": X_test.mean(axis=1),
            "composite_ahp": np.array([row["strategy_total"] for row in test_rows]),
            "hengmen_school": np.array([row["hengmen_school_score"] for row in test_rows]),
        }
        case_ranks = {method: _best_reference_rank(scores[method], list(range(len(test_rows))), test_rows) for method in methods}
        for method, rank in case_ranks.items():
            per_method_ranks[method].append(rank)
        per_case.append({"case_id": held_out, "case_name": test_rows[0]["case_name"], "ranks": case_ranks})
    summary = {}
    for method in methods:
        ranks = per_method_ranks[method]
        summary[method] = {
            "mean_reference_rank": round(sum(ranks) / len(ranks), 2),
            "top1_count": sum(1 for rank in ranks if rank == 1),
            "top3_count": sum(1 for rank in ranks if rank <= 3),
        }
    return {
        "schema_version": "sem-fusion-loco-v1",
        "case_count": len(case_ids),
        "row_count": len(rows),
        "feature_count": len(feature_names),
        "summary": summary,
        "per_case": per_case,
    }


# ---------------------------------------------------------------------------
# v2: within-case standardization + indicator screening/parceling +
#     pairwise (Bradley-Terry) structural model
# ---------------------------------------------------------------------------
#
# Round-2 mechanisms (see sem_fusion_v2_report_2026-07-28.md):
# 1. Within-case z-scoring: the task is ranking 12 candidates *inside* a case,
#    so every feature is centered per case before entering the SEM. Raw values
#    stay in the dataset; centering happens at evaluation time.
# 2. Label-free indicator screening (mean within-case spread >= MIN_FEATURE_SPREAD;
#    hengmen_vote_palace_trigger excluded a priori per
#    hengmen_discrimination_improvement_2026-07-24.md) + parceling into
#    hengmen-vote / school / book parcels (equal-weight means), optionally plus
#    an LLM-skill parcel. Parameters drop from 26+26+2 to ~3+3+1.
# 3. Bradley-Terry pairwise structural link: P(A beats B) = sigmoid(beta*(eta_A - eta_B))
#    over informative pairs (reference vs each non-reference candidate of the
#    same case; pairs of two non-references carry no label information).

DEFAULT_LLM_RANKINGS_PATH = BASE_DIR / "llm_skill_analysis" / "llm_rankings_2026-07-28.json"
DEFAULT_V2_LOCO_PATH = BASE_DIR / "outputs" / "sem_fusion_v2_loco.json"

MIN_FEATURE_SPREAD = 0.01
SCREEN_EXCLUDE = {"hengmen_vote_palace_trigger"}
PARCEL_PREFIXES = (("hengmen_votes", "hengmen_vote_"), ("schools", "school_"), ("books", "book_"))
LLM_PARCEL = "llm_skill"


def load_llm_scores(path: Path | None = None) -> dict[str, dict[str, float]]:
    """Load LLM-skill rankings -> {case_id: {hour_label: 13 - rank}}."""
    path = path or DEFAULT_LLM_RANKINGS_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    scores: dict[str, dict[str, float]] = {}
    for case_id, ranking in payload["rankings"].items():
        scores[case_id] = {f"{branch}时": float(13 - rank) for rank, branch in enumerate(ranking, start=1)}
    return scores


def within_case_standardize(
    rows: list[dict[str, Any]], feature_names: list[str] | None = None
) -> list[dict[str, Any]]:
    """Add ``features_z``: per-case z-score of each feature across its 12 candidates.

    Zero-variance features inside a case map to all-zero z-scores. Raw
    ``features`` are preserved untouched.
    """
    feature_names = feature_names or list(FEATURE_NAMES)
    by_case: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], []).append(row)
    z_by_id: dict[int, dict[str, float]] = {}
    for case_rows in by_case.values():
        for name in feature_names:
            values = np.array([row["features"][name] for row in case_rows], dtype=float)
            std = float(values.std())
            for row, value in zip(case_rows, values):
                z = (value - float(values.mean())) / std if std > 1e-12 else 0.0
                z_by_id.setdefault(id(row), {})[name] = float(z)
    return [dict(row, features_z=z_by_id[id(row)]) for row in rows]


def screen_features(
    rows: list[dict[str, Any]],
    feature_names: list[str] | None = None,
    min_spread: float = MIN_FEATURE_SPREAD,
    exclude: set[str] | None = None,
) -> dict[str, list[str]]:
    """Label-free screening; returns {parcel_name: kept member features}.

    A feature is kept when its mean within-case standard deviation (candidate
    spread) reaches ``min_spread`` and it is not in ``exclude``. Features not
    matching any parcel prefix (e.g. base scores) are dropped from parcels.
    """
    feature_names = feature_names or list(FEATURE_NAMES)
    exclude = SCREEN_EXCLUDE if exclude is None else exclude
    spread = {name: float(np.std([row["features"][name] for row in rows])) for name in feature_names}
    # mean within-case spread (pooled std conflates case-level shifts)
    by_case: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], []).append(row)
    mean_within_spread = {}
    for name in feature_names:
        mean_within_spread[name] = float(
            np.mean([np.std([row["features"][name] for row in case_rows]) for case_rows in by_case.values()])
        )
    del spread  # pooled std intentionally unused
    parcels: dict[str, list[str]] = {}
    for parcel_name, prefix in PARCEL_PREFIXES:
        members = [
            name
            for name in feature_names
            if name.startswith(prefix) and mean_within_spread[name] >= min_spread and name not in exclude
        ]
        if members:
            parcels[parcel_name] = members
    return parcels


def build_parcels(
    rows: list[dict[str, Any]],
    parcels: dict[str, list[str]],
    llm_scores: dict[str, dict[str, float]] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Attach parcel values (equal-weight means of within-case z-features).

    Requires rows produced by within_case_standardize. The LLM parcel is
    z-scored within case like the other parcels. Returns (rows, parcel_names).
    """
    parcel_names = list(parcels) + ([LLM_PARCEL] if llm_scores else [])
    out = []
    for row in rows:
        values = {
            name: float(np.mean([row["features_z"][member] for member in members]))
            for name, members in parcels.items()
        }
        if llm_scores:
            values[LLM_PARCEL] = float(llm_scores.get(row["case_id"], {}).get(row["hour_label"], 0.0))
        out.append(dict(row, parcels=values))
    if llm_scores:  # within-case z-score for the LLM parcel
        by_case: dict[str, list[dict[str, Any]]] = {}
        for row in out:
            by_case.setdefault(row["case_id"], []).append(row)
        for case_rows in by_case.values():
            values = np.array([row["parcels"][LLM_PARCEL] for row in case_rows], dtype=float)
            std = float(values.std())
            for row, value in zip(case_rows, values):
                row["parcels"][LLM_PARCEL] = float((value - values.mean()) / std) if std > 1e-12 else 0.0
    return out, parcel_names


def make_reference_pairs(rows: list[dict[str, Any]]) -> list[tuple[int, int]]:
    """Informative Bradley-Terry pairs (i, j): reference i beats same-case non-reference j.

    Pairs of two non-reference candidates have unknown outcomes and are
    excluded; that yields 11 pairs per case (not C(12,2)=66).
    """
    pairs = []
    for i, row in enumerate(rows):
        if not row["is_reference"]:
            continue
        for j, other in enumerate(rows):
            if other["case_id"] == row["case_id"] and not other["is_reference"]:
                pairs.append((i, j))
    return pairs


def _fit_bradley_terry(
    Z: np.ndarray, pairs: list[tuple[int, int]], init_w: np.ndarray, l2: float = 1e-4
) -> np.ndarray:
    """Joint pairwise (Bradley-Terry) fit of the measurement weights.

    A two-step BT (fit FA first, then a scalar beta on the factor scores) is
    rank-equivalent to the logit variant — a single monotone link cannot
    change any pairwise ordering. The pairwise structural link only does real
    work when it feeds back into the measurement weights, so here we maximize
    the pairwise likelihood sum log sigmoid(w . (z_i - z_j)) over the weight
    vector w directly (scale absorbed into w, i.e. beta = 1), initialized
    from the FA factor-score weights with a small fixed L2 penalty. This is a
    Thurstonian ranking model: eta = w.z measured by the parcels.
    """
    if not pairs:
        return np.asarray(init_w, dtype=float)
    diffs = np.array([Z[i] - Z[j] for i, j in pairs], dtype=float)

    def nll(w: np.ndarray) -> float:
        return float(np.sum(np.logaddexp(0.0, -(diffs @ w))) + l2 * float(w @ w))

    def grad(w: np.ndarray) -> np.ndarray:
        margin = diffs @ w
        coeff = expit(margin) - 1.0  # d/dw log(1 + exp(-d.w)) = (sigmoid(d.w) - 1) * d
        return diffs.T @ coeff + 2.0 * l2 * w

    result = minimize(nll, np.asarray(init_w, dtype=float), jac=grad, method="BFGS", options={"maxiter": 500})
    return result.x if np.isfinite(result.fun) else np.asarray(init_w, dtype=float)


def fit_sem_v2(
    X: np.ndarray,
    y: np.ndarray | None = None,
    pairs: list[tuple[int, int]] | None = None,
    structural: str = "bt",
) -> dict[str, Any]:
    """Fit the v2 one-factor SEM on parcel indicators.

    Measurement model: ML one-factor analysis (same estimator as v1).
    Structural model: ``bt`` -> Bradley-Terry pairwise link over ``pairs``
    (1 parameter); ``logit`` -> binary logit on ``y`` (2 parameters).
    """
    X = np.asarray(X, dtype=float)
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    Z = (X - mean) / std
    loadings, psi, fa_info = fit_one_factor_ml(Z)
    sigma_inv = np.linalg.inv(np.outer(loadings, loadings) + np.diag(psi))
    score_weights = sigma_inv @ loadings
    factor_scores = Z @ score_weights
    model: dict[str, Any] = {
        "feature_mean": mean,
        "feature_std": std,
        "loadings": loadings,
        "uniqueness": psi,
        "factor_score_weights": score_weights,
        "structural": structural,
        "fa_info": fa_info,
    }
    if structural == "bt":
        model["bt_weights"] = _fit_bradley_terry(Z, pairs or [], score_weights)
        model["factor_score_weights"] = model["bt_weights"]
    elif structural == "logit":
        model["logit_beta"] = _fit_logit(factor_scores, np.asarray(y, dtype=float))
    else:
        raise ValueError(f"unknown structural model: {structural}")
    return model


def predict_v2(model: dict[str, Any], X: np.ndarray) -> np.ndarray:
    """Latent hour-fit scores eta for rows X (n, p); higher = better candidate."""
    X = np.atleast_2d(np.asarray(X, dtype=float))
    Z = (X - model["feature_mean"]) / model["feature_std"]
    return Z @ model["factor_score_weights"]


def _parcels_xy(rows: list[dict[str, Any]], parcel_names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    X = np.array([[row["parcels"][name] for name in parcel_names] for row in rows], dtype=float)
    y = np.array([1.0 if row["is_reference"] else 0.0 for row in rows], dtype=float)
    return X, y


def loco_evaluate_v2(
    dataset: dict[str, Any],
    *,
    structural: str = "bt",
    use_llm: bool = False,
    full_features: bool = False,
    llm_scores: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """LOCO evaluation of a v2 variant.

    ``full_features=True`` keeps all 26 within-case z-scored indicators with
    the v1 logit model (isolates the centering effect); otherwise screened
    parcels are used with the requested structural link. Baselines are
    recomputed on the same folds: equal-weight (raw features), composite AHP,
    improved Hengmen, parcel equal-weight, and (when use_llm) LLM-only.
    """
    rows = dataset["rows"]
    feature_names = dataset.get("feature_names", list(FEATURE_NAMES))
    if use_llm and llm_scores is None:
        llm_scores = load_llm_scores()
    z_rows = within_case_standardize(rows, feature_names)
    if full_features:
        parcel_rows, parcel_names = z_rows, feature_names
    else:
        parcels = screen_features(rows, feature_names)
        parcel_rows, parcel_names = build_parcels(z_rows, parcels, llm_scores if use_llm else None)
    case_ids = sorted({row["case_id"] for row in rows})
    methods = ["sem_v2", "equal_weight", "composite_ahp", "hengmen_school", "equal_weight_parcel"]
    if use_llm:
        methods.append("llm_only")
    per_method_ranks: dict[str, list[int]] = {method: [] for method in methods}
    per_case: list[dict[str, Any]] = []
    last_model: dict[str, Any] | None = None
    for held_out in case_ids:
        train_rows = [row for row in parcel_rows if row["case_id"] != held_out]
        test_rows = [row for row in parcel_rows if row["case_id"] == held_out]
        if full_features:
            X_train, y_train = dataset_xy(train_rows, feature_names)  # raw for baselines only
            Xz_train = np.array([[row["features_z"][name] for name in feature_names] for row in train_rows])
            Xz_test = np.array([[row["features_z"][name] for name in feature_names] for row in test_rows])
            model = fit_sem(Xz_train, y_train)
            sem_scores = predict(model, Xz_test)
        else:
            X_train, y_train = _parcels_xy(train_rows, parcel_names)
            X_test, _ = _parcels_xy(test_rows, parcel_names)
            model = fit_sem_v2(X_train, y_train, make_reference_pairs(train_rows), structural)
            sem_scores = predict_v2(model, X_test)
        last_model = model
        raw_test = [row for row in rows if row["case_id"] == held_out]
        scores = {
            "sem_v2": np.asarray(sem_scores, dtype=float),
            "equal_weight": np.array([np.mean([row["features"][name] for name in feature_names]) for row in raw_test]),
            "composite_ahp": np.array([row["strategy_total"] for row in raw_test]),
            "hengmen_school": np.array([row["hengmen_school_score"] for row in raw_test]),
            "equal_weight_parcel": np.array(
                [np.mean([row["parcels"][name] for name in parcel_names if name != LLM_PARCEL]) for row in test_rows]
            )
            if not full_features
            else np.array([np.mean(list(row["features_z"].values())) for row in test_rows]),
        }
        if use_llm:
            scores["llm_only"] = np.array([row["parcels"][LLM_PARCEL] for row in test_rows])
        case_ranks = {method: _best_reference_rank(scores[method], list(range(len(test_rows))), test_rows) for method in methods}
        for method, rank in case_ranks.items():
            per_method_ranks[method].append(rank)
        per_case.append({"case_id": held_out, "case_name": test_rows[0]["case_name"], "ranks": case_ranks})
    summary = {}
    for method in methods:
        ranks = per_method_ranks[method]
        summary[method] = {
            "mean_reference_rank": round(sum(ranks) / len(ranks), 2),
            "top1_count": sum(1 for rank in ranks if rank == 1),
            "top3_count": sum(1 for rank in ranks if rank <= 3),
        }
    return {
        "schema_version": "sem-fusion-v2-loco-v1",
        "variant": {
            "structural": structural,
            "use_llm": use_llm,
            "full_features": full_features,
            "indicator_count": len(parcel_names),
        },
        "indicators": list(parcel_names),
        "case_count": len(case_ids),
        "summary": summary,
        "per_case": per_case,
    }


V2_VARIANTS = {
    "v2a_centered_full26_logit": {"full_features": True, "structural": "logit", "use_llm": False},
    "v2b_parcels_logit": {"full_features": False, "structural": "logit", "use_llm": False},
    "v2c_parcels_bt": {"full_features": False, "structural": "bt", "use_llm": False},
    "v2d_parcels_logit_llm": {"full_features": False, "structural": "logit", "use_llm": True},
    "v2e_parcels_bt_llm": {"full_features": False, "structural": "bt", "use_llm": True},
}


def run_v2_variants(dataset: dict[str, Any]) -> dict[str, Any]:
    """Run all pre-registered v2 variants and full-sample fits for reporting."""
    llm_scores = load_llm_scores()
    results = {name: loco_evaluate_v2(dataset, llm_scores=llm_scores, **spec) for name, spec in V2_VARIANTS.items()}
    # Full-sample parcel fit (descriptive loadings / structural coefficient).
    rows = dataset["rows"]
    feature_names = dataset.get("feature_names", list(FEATURE_NAMES))
    z_rows = within_case_standardize(rows, feature_names)
    parcels = screen_features(rows, feature_names)
    full: dict[str, Any] = {"screened_parcels": parcels}
    for label, use_llm in (("without_llm", False), ("with_llm", True)):
        parcel_rows, parcel_names = build_parcels(z_rows, parcels, llm_scores if use_llm else None)
        X, y = _parcels_xy(parcel_rows, parcel_names)
        model = fit_sem_v2(X, y, make_reference_pairs(parcel_rows), "bt")
        full[label] = {
            "indicators": parcel_names,
            "loadings": loadings_table(model, parcel_names),
            "bt_weights": {
                name: round(float(w), 4) for name, w in zip(parcel_names, model["bt_weights"])
            },
            "fa_info": model["fa_info"],
        }
    return {"schema_version": "sem-fusion-v2-variants-v1", "variants": results, "full_sample_fit": full}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SEM fusion for hour calibration (LOCO evaluation).")
    parser.add_argument("--recompute", action="store_true", help="Re-run calibrate_case instead of using the cached dataset.")
    parser.add_argument("--v2", action="store_true", help="Run the v2 variants (centering/parcels/Bradley-Terry, with/without LLM parcel).")
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--loco-path", type=Path, default=DEFAULT_LOCO_PATH)
    parser.add_argument("--v2-loco-path", type=Path, default=DEFAULT_V2_LOCO_PATH)
    args = parser.parse_args(argv)
    dataset = build_dataset(cache_path=args.dataset_path, recompute=args.recompute)
    if args.v2:
        report_v2 = run_v2_variants(dataset)
        args.v2_loco_path.write_text(json.dumps(report_v2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        compact = {
            name: {"indicators": result["indicators"], "summary": result["summary"]}
            for name, result in report_v2["variants"].items()
        }
        compact["full_sample_fit"] = report_v2["full_sample_fit"]
        print(json.dumps(compact, ensure_ascii=False, indent=2))
        return 0
    loco = loco_evaluate(dataset)
    args.loco_path.write_text(json.dumps(loco, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Full-sample fit for the loadings report (descriptive only, not evaluation).
    X, y = dataset_xy(dataset["rows"], dataset.get("feature_names"))
    model = fit_sem(X, y)
    report = {
        "dataset": {"case_count": dataset["case_count"], "row_count": dataset["row_count"]},
        "loco": loco["summary"],
        "loadings": loadings_table(model),
        "logit_beta": [round(float(b), 4) for b in model["logit_beta"]],
        "fa_info": model["fa_info"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
