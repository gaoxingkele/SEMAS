"""Walk-forward / expanding-window multi-factor combination.

Instead of a single fixed validation fold, this script rolls a fit window
through the test period. For each step it:

1. Re-estimates combination weights (or re-trains an ML meta-model) on the
   most recent ``fit_window_days`` of history.
2. Applies the weights/model to the next ``step_days`` out-of-sample chunk.
3. Concatenates the resulting signals and reports combined long-short metrics.

Supported weight/model methods:
- equal
- ic (signed validation IC weights)
- ridge (sklearn Ridge regression on factor z-scores -> forward returns)
- gbdt (sklearn GradientBoostingRegressor)
- lgbm (LightGBM regressor, if installed)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import (
    load_tushare_data,
    load_tushare_data_with_val,
)
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1:
        return s
    if s.empty:
        return s.copy()
    return s.groupby(level="symbol").transform(
        lambda x: x.ewm(span=span, min_periods=1).mean()
    )


def _ic_weights(X: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """Return signed, L1-normalised IC weights for the columns of X."""
    ics = []
    for col in X.columns:
        df = pd.DataFrame({"x": X[col], "y": y}).dropna()
        per_day = df.groupby(level="date").apply(
            lambda g: g["x"].corr(g["y"]), include_groups=False
        )
        ics.append(float(per_day.mean()))
    ics = np.array(ics)
    denom = np.abs(ics).sum() + 1e-12
    return ics / denom


def _fit_model(model_name: str, X: pd.DataFrame, y: pd.Series):
    """Fit a cross-sectional meta-model on the fit window."""
    mask = X.notna().all(axis=1) & y.notna()
    Xf = X.loc[mask]
    yf = y.loc[mask]
    if len(yf) < 10:
        return None

    if model_name == "ridge":
        from sklearn.linear_model import Ridge

        model = Ridge(alpha=1.0, fit_intercept=True)
    elif model_name == "gbdt":
        from sklearn.ensemble import GradientBoostingRegressor

        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
        )
    elif model_name == "lgbm":
        import lightgbm as lgb

        model = lgb.LGBMRegressor(
            n_estimators=100, num_leaves=15, learning_rate=0.05, random_state=42, verbose=-1
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")

    model.fit(Xf, yf)
    return model


def _predict_weights(model, X: pd.DataFrame) -> pd.Series:
    if model is None:
        return pd.Series(np.nan, index=X.index)
    mask = X.notna().all(axis=1)
    pred = pd.Series(np.nan, index=X.index)
    pred.loc[mask] = model.predict(X.loc[mask])
    return pred


def run_rolling_combination(
    cfg: dict,
    lib_path: Path,
    output_dir: Path,
    top_n: int = 10,
    fit_window_days: int = 252,
    step_days: int = 63,
    weight_method: str = "equal",
    smooth_span: int = 10,
) -> dict:
    """Run walk-forward combination and return aggregated metrics."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if "val_date" in cfg:
        train, val, test = load_tushare_data_with_val(cfg)
        history = pd.concat([train, val]).sort_index()
    else:
        train, test = load_tushare_data(cfg)
        history = train.sort_index()
    full = pd.concat([history, test]).sort_index()

    # Pre-select factors by absolute training IC.
    lib = pd.read_csv(lib_path)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")
    sort_key = "train_ic" if "train_ic" in lib.columns else "test_ic"
    lib = lib.sort_values(sort_key, ascending=False, key=abs).head(top_n)

    # Pre-evaluate selected factors on the full panel.
    factor_frames = {}
    for _, row in lib.iterrows():
        try:
            f = parse_expression(row["expression"]).eval(full)
            factor_frames[row["factor"]] = _zscore(f)
        except Exception as exc:
            print(f"Skipping {row['factor']}: {exc}")

    if len(factor_frames) < 2:
        raise RuntimeError("Not enough factors evaluated for combination.")

    mat = pd.concat(factor_frames, axis=1).dropna()
    fwd = full["forward_return"].loc[mat.index]
    dates = mat.index.get_level_values("date").unique().sort_values()

    test_start = pd.Timestamp(cfg["split_date"])
    test_end = dates[-1]

    combined_chunks = []
    fwd_chunks = []
    window_stats = []

    current_start = test_start
    while current_start <= test_end:
        current_end = min(current_start + pd.Timedelta(days=step_days - 1), test_end)

        fit_start = max(dates[0], current_start - pd.Timedelta(days=fit_window_days - 1))
        fit_idx = mat.index[mat.index.get_level_values("date") < current_start]
        fit_idx = fit_idx[fit_idx.get_level_values("date") >= fit_start]

        test_idx = mat.index[
            (mat.index.get_level_values("date") >= current_start)
            & (mat.index.get_level_values("date") <= current_end)
        ]
        if len(test_idx) == 0:
            current_start = current_end + pd.Timedelta(days=1)
            continue

        X_fit = mat.loc[fit_idx]
        y_fit = fwd.loc[fit_idx]
        X_test = mat.loc[test_idx]

        if weight_method == "equal":
            weights = np.ones(len(mat.columns)) / len(mat.columns)
            combined_test = pd.Series(X_test.values @ weights, index=X_test.index)
        elif weight_method == "ic":
            weights = _ic_weights(X_fit, y_fit)
            combined_test = pd.Series(X_test.values @ weights, index=X_test.index)
        elif weight_method in ("ridge", "gbdt", "lgbm"):
            model = _fit_model(weight_method, X_fit, y_fit)
            combined_test = _predict_weights(model, X_test)
        else:
            raise ValueError(f"Unknown weight method: {weight_method}")

        combined_test = _smooth(combined_test, smooth_span).clip(-5, 5)
        combined_chunks.append(combined_test)
        fwd_chunks.append(fwd.loc[test_idx])

        window_stats.append(
            {
                "start": str(current_start.date()),
                "end": str(current_end.date()),
                "n_fit": int(len(X_fit)),
                "n_test": int(len(X_test)),
            }
        )

        current_start = current_end + pd.Timedelta(days=1)

    combined = pd.concat(combined_chunks).sort_index()
    fwd_all = pd.concat(fwd_chunks).sort_index()

    bt = run_long_short_backtest(combined, fwd_all, transaction_cost=0.001)
    result = {
        "weight_method": weight_method,
        "top_n": top_n,
        "fit_window_days": fit_window_days,
        "step_days": step_days,
        "smooth_span": smooth_span,
        "ic": ic_score(combined, fwd_all),
        "turnover": turnover_score(combined),
        "sharpe": bt["sharpe"],
        "annualized_return": bt["annualized_return"],
        "cost_adjusted_return": bt["cost_adjusted_return"],
        "max_drawdown": bt["max_drawdown"],
    }

    out = {
        "config": cfg,
        "settings": {
            "top_n": top_n,
            "fit_window_days": fit_window_days,
            "step_days": step_days,
            "weight_method": weight_method,
            "smooth_span": smooth_span,
        },
        "selected_factors": lib.to_dict(orient="records"),
        "window_stats": window_stats,
        "result": result,
    }
    with open(output_dir / "rolling_combination_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nRolling combination ({weight_method}, top-{top_n}):")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    print(f"\nSaved to {output_dir}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config with Tushare data settings")
    parser.add_argument("--factor-csv", type=Path, required=True)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--fit-window-days", type=int, default=252)
    parser.add_argument("--step-days", type=int, default=63)
    parser.add_argument(
        "--weight-method",
        type=str,
        default="equal",
        choices=["equal", "ic", "ridge", "gbdt", "lgbm"],
    )
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("china_a_share_alpha_output/rolling_combination"),
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    run_rolling_combination(
        cfg,
        args.factor_csv,
        args.output_dir,
        args.top_n,
        args.fit_window_days,
        args.step_days,
        args.weight_method,
        args.smooth_span,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
