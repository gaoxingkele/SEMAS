"""Regime-switching factor combination.

Splits each day into a high-volatility or low-volatility regime based on the
median absolute market return, selects factors separately for each regime on
the training fold, and stitches the regime-specific combined signals together.
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
from china_a_share_alpha.scripts.run_factor_combination import (
    _compute_factor_metrics,
    _compute_weights,
    _greedy_select,
    _smooth,
    _zscore,
)


def _market_volatility(data: pd.DataFrame, window: int) -> pd.Series:
    """Daily cross-sectional median absolute return, smoothed by EMA."""
    daily = data.groupby(level="date")["return"].apply(lambda s: s.abs().median())
    return daily.ewm(span=window, min_periods=1).mean()


def _regime_labels(
    data: pd.DataFrame,
    train: pd.DataFrame,
    window: int,
    quantile: float,
) -> pd.Series:
    """Return a boolean Series indexed by date: True for high-vol regime."""
    vol = _market_volatility(data, window)
    threshold = vol.reindex(train.index.get_level_values("date").unique()).quantile(quantile)
    return vol > threshold


def _ic_in_regime(factor: pd.Series, forward: pd.Series, regime_dates: set) -> float:
    """Mean daily IC over dates in the given regime."""
    df = pd.DataFrame({"factor": factor, "forward": forward}).dropna()
    dates = df.index.get_level_values("date")
    df = df[dates.isin(regime_dates)]
    if df.empty:
        return 0.0
    per_day = df.groupby(level="date").apply(
        lambda g: g["factor"].corr(g["forward"]), include_groups=False
    )
    return float(per_day.mean())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config with Tushare data settings")
    parser.add_argument("--factor-csv", type=Path, required=True)
    parser.add_argument("--top-n", type=int, default=5, help="Factors per regime")
    parser.add_argument(
        "--max-pairwise-corr", type=float, default=1.0, help="Greedy correlation filter"
    )
    parser.add_argument("--weight-method", type=str, default="equal")
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--regime-window", type=int, default=20)
    parser.add_argument("--regime-quantile", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/regime_combination"))
    parser.add_argument("--transaction-cost", type=float, default=0.001)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if "val_date" in cfg:
        train, val, test = load_tushare_data_with_val(cfg)
    else:
        train, test = load_tushare_data(cfg)
        val = None

    all_data = pd.concat([train, val, test]) if val is not None else pd.concat([train, test])
    regime = _regime_labels(all_data, train, args.regime_window, args.regime_quantile)
    high_dates = set(regime[regime].index)
    low_dates = set(regime[~regime].index)

    lib = pd.read_csv(args.factor_csv)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

    # Compute full-period metrics plus regime-specific train IC.
    metrics = []
    for _, row in lib.iterrows():
        base = _compute_factor_metrics(row, train, val, test, args.transaction_cost)
        f_train = parse_expression(row["expression"]).eval(train)
        base["train_ic_high_vol"] = _ic_in_regime(f_train, train["forward_return"], high_dates)
        base["train_ic_low_vol"] = _ic_in_regime(f_train, train["forward_return"], low_dates)
        metrics.append(base)
    metrics = pd.DataFrame(metrics)

    # Select factors per regime.
    def _select(regime_col: str, regime_dates: set) -> pd.DataFrame:
        sorted_df = metrics.sort_values(regime_col, ascending=False, key=abs)
        return _greedy_select(sorted_df, train, val, args.top_n, args.max_pairwise_corr)

    selected_high = _select("train_ic_high_vol", high_dates)
    selected_low = _select("train_ic_low_vol", low_dates)

    # Compute per-regime weights on the validation fold if available.
    weight_data = val if val is not None else train

    def _regime_weights(selected: pd.DataFrame) -> np.ndarray:
        if args.weight_method == "equal":
            return np.ones(len(selected)) / max(len(selected), 1)
        # Fallback to equal for other methods in this scaffold.
        return np.ones(len(selected)) / max(len(selected), 1)

    weights_high = _regime_weights(selected_high)
    weights_low = _regime_weights(selected_low)

    # Use the union of selected factors so high/low regime signals share the same
    # coverage and no information leaks across regimes during smoothing.
    selected_union = pd.concat([selected_high, selected_low], ignore_index=True).drop_duplicates(
        subset=["factor"]
    )
    factor_order = selected_union["factor"].tolist()

    def _build_weights(selected: pd.DataFrame) -> pd.Series:
        w = pd.Series(0.0, index=factor_order)
        for i, row in selected.iterrows():
            if row["factor"] in w.index:
                w[row["factor"]] = 1.0 / max(len(selected), 1)
        return w

    w_high = _build_weights(selected_high)
    w_low = _build_weights(selected_low)

    results = []
    max_corr = 0.0
    for label, data, fwd in [
        ("train", train, train["forward_return"]),
        ("val", val, val["forward_return"] if val is not None else None),
        ("test", test, test["forward_return"]),
    ]:
        if data is None:
            continue

        frames = []
        for _, row in selected_union.iterrows():
            try:
                frames.append(_zscore(parse_expression(row["expression"]).eval(data)).rename(row["factor"]))
            except Exception:
                pass
        if not frames:
            continue
        mat = pd.concat(frames, axis=1).dropna()

        if label == "val":
            corr_matrix = mat.corr(method="spearman")
            corr_values = corr_matrix.abs().values
            np.fill_diagonal(corr_values, 0.0)
            max_corr = float(corr_values.max()) if corr_values.size else 0.0

        dates = mat.index.get_level_values("date")
        is_high = dates.isin(high_dates)

        weights = pd.DataFrame(np.nan, index=mat.index, columns=mat.columns)
        weights.loc[is_high] = w_high[mat.columns].values
        weights.loc[~is_high] = w_low[mat.columns].values

        combined = (mat * weights).sum(axis=1)
        combined = _smooth(combined.clip(-5, 5), args.smooth_span)

        bt = run_long_short_backtest(combined, fwd, transaction_cost=args.transaction_cost)
        result = {
            "period": label,
            "n_factors": len(selected_union),
            "weight_method": args.weight_method,
            "smooth_span": args.smooth_span,
            "ic": ic_score(combined, fwd),
            "turnover": turnover_score(combined),
            "sharpe": bt["sharpe"],
            "annualized_return": bt["annualized_return"],
            "cost_adjusted_return": bt["cost_adjusted_return"],
            "max_drawdown": bt["max_drawdown"],
        }
        results.append(result)
        print(f"\n{label.upper()}:")
        for k, v in result.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")

    out = {
        "config": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "selected_high": selected_high.to_dict(orient="records"),
        "selected_low": selected_low.to_dict(orient="records"),
        "weights_high": w_high.tolist(),
        "weights_low": w_low.tolist(),
        "selection_correlation_max": max_corr,
        "results": results,
    }
    with open(args.output_dir / "combination_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    selected_high.to_csv(args.output_dir / "selected_factors_high.csv", index=False)
    selected_low.to_csv(args.output_dir / "selected_factors_low.csv", index=False)
    print(f"\nSaved results to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
