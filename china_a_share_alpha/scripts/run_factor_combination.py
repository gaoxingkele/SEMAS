"""Build a robust multi-factor combination from a cleaned factor library.

This script deliberately avoids the overfitting risk of weight-space genetic
algorithms.  Instead it:

1. Selects the top-K factors by training-set IC (or ICIR).
2. Z-scores each factor cross-sectionally.
3. Averages them with equal weights.
4. Optionally smooths the combined signal with a per-symbol EMA.
5. Reports train and test long-short backtest metrics.

Equal weight + smoothing is a strong, under-fitted baseline: it keeps the
benefits of diversification without fitting noisy relative weights to the
training period.
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
    return s.groupby(level="symbol").transform(
        lambda x: x.ewm(span=span, min_periods=1).mean()
    )


def _icir(factor: pd.Series, forward: pd.Series) -> float:
    df = pd.DataFrame({"factor": factor, "forward": forward}).dropna()
    per_day = df.groupby(level="date").apply(
        lambda g: g["factor"].corr(g["forward"]), include_groups=False
    )
    return float(per_day.mean() / (per_day.std() + 1e-8))


def _compute_factor_metrics(row, train, val, test):
    """Return dict of train/val/test metrics for a single factor."""
    expr = parse_expression(row["expression"])
    f_train = expr.eval(train)
    train_ic = ic_score(f_train, train["forward_return"])
    out = {"factor": row.get("factor"), "expression": row["expression"], "train_ic": train_ic}

    if val is not None:
        f_val = expr.eval(val)
        val_ic = ic_score(f_val, val["forward_return"])
        val_bt = run_long_short_backtest(f_val, val["forward_return"], transaction_cost=0.001)
        out.update(
            {
                "val_ic": val_ic,
                "val_sharpe": val_bt.get("sharpe", 0.0),
                "val_cost_adj_return": val_bt.get("cost_adjusted_return", 0.0),
            }
        )

    f_test = expr.eval(test)
    test_ic = ic_score(f_test, test["forward_return"])
    test_bt = run_long_short_backtest(f_test, test["forward_return"], transaction_cost=0.001)
    out.update(
        {
            "test_ic": test_ic,
            "test_sharpe": test_bt.get("sharpe", 0.0),
            "test_cost_adj_return": test_bt.get("cost_adjusted_return", 0.0),
        }
    )
    return out


def _compute_weights(mat: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    """Combine columns of `mat` using ``weights``."""
    return pd.Series(mat.values @ weights, index=mat.index)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config with Tushare data settings")
    parser.add_argument("--factor-csv", type=Path, required=True, help="Input factor library CSV")
    parser.add_argument("--top-n", type=int, default=5, help="Number of factors to combine")
    parser.add_argument(
        "--sort-by",
        type=str,
        default="auto",
        choices=["auto", "train_ic", "train_icir", "val_ic", "val_sharpe", "test_ic"],
    )
    parser.add_argument(
        "--weight-method",
        type=str,
        default="equal",
        choices=["equal", "ic", "sharpe", "risk_parity"],
        help="How to weight selected factors",
    )
    parser.add_argument("--smooth-span", type=int, default=10, help="EMA span for smoothing (1 = none)")
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/factor_combination"))
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if "val_date" in cfg:
        train, val, test = load_tushare_data_with_val(cfg)
    else:
        train, test = load_tushare_data(cfg)
        val = None

    lib = pd.read_csv(args.factor_csv)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

    # Compute metrics for every candidate.
    metrics = []
    for _, row in lib.iterrows():
        try:
            metrics.append(_compute_factor_metrics(row, train, val, test))
        except Exception as exc:
            print(f"Skipping {row.get('factor')}: {exc}")
    metrics = pd.DataFrame(metrics)

    # Compute train ICIR if requested.
    if args.sort_by == "train_icir":
        icirs = []
        for _, row in lib.iterrows():
            try:
                f = parse_expression(row["expression"]).eval(train)
                icirs.append(_icir(f, train["forward_return"]))
            except Exception:
                icirs.append(np.nan)
        metrics["train_icir"] = icirs

    # Default sort uses validation IC when a validation fold is available.
    sort_by = args.sort_by
    if sort_by == "auto":
        sort_by = "val_ic" if val is not None else "train_ic"

    metrics = metrics.sort_values(sort_by, ascending=False, key=abs if sort_by.endswith("_ic") else lambda x: x)
    selected = metrics.head(args.top_n).copy()

    # Evaluate selected factors on each period and build a z-scored matrix.
    period_results = {}
    period_mats = {}
    for label, data, fwd in [
        ("train", train, train["forward_return"]),
        ("val", val, val["forward_return"] if val is not None else None),
        ("test", test, test["forward_return"]),
    ]:
        if data is None:
            continue
        frames = []
        for _, row in selected.iterrows():
            try:
                f = parse_expression(row["expression"]).eval(data)
                frames.append(_zscore(f).rename(row["factor"]))
            except Exception as exc:
                print(f"Skipping {row['factor']} on {label}: {exc}")
        mat = pd.concat(frames, axis=1).dropna()
        period_mats[label] = mat
        period_results[label] = fwd.loc[mat.index] if fwd is not None else None

    # Estimate weights on the validation fold if available, otherwise on train.
    weight_period = "val" if "val" in period_mats else "train"
    weight_mat = period_mats[weight_period]

    if args.weight_method == "equal":
        weights = np.ones(len(selected)) / max(len(selected), 1)
    elif args.weight_method == "ic":
        ic_vals = selected["val_ic"].values if "val_ic" in selected.columns else selected["train_ic"].values
        abs_ic = np.abs(ic_vals)
        weights = ic_vals / (abs_ic.sum() + 1e-12)
        if np.abs(weights.sum()) < 1e-6:
            weights = np.ones(len(selected)) / len(selected)
    elif args.weight_method == "sharpe":
        sharpe_vals = selected["val_sharpe"].values if "val_sharpe" in selected.columns else selected["test_sharpe"].values
        sign = np.sign(selected["val_ic"].values if "val_ic" in selected.columns else selected["train_ic"].values)
        signed = sign * sharpe_vals
        abs_sum = np.abs(signed).sum() + 1e-12
        weights = signed / abs_sum
        if np.abs(weights.sum()) < 1e-6:
            weights = np.ones(len(selected)) / len(selected)
    elif args.weight_method == "risk_parity":
        # Use inverse volatility of each factor's long-short daily return.
        inv_vols = []
        for _, row in selected.iterrows():
            try:
                f = parse_expression(row["expression"]).eval(
                    val if val is not None else train
                )
                bt = run_long_short_backtest(f, (val if val is not None else train)["forward_return"], transaction_cost=0.001)
                daily = bt.get("daily_long_short", pd.Series(dtype=float))
                vol = float(daily.std()) + 1e-12
                inv_vols.append(1.0 / vol)
            except Exception:
                inv_vols.append(0.0)
        inv_vols = np.array(inv_vols)
        sign = np.sign(selected["val_ic"].values if "val_ic" in selected.columns else selected["train_ic"].values)
        signed = sign * inv_vols
        abs_sum = np.abs(signed).sum() + 1e-12
        weights = signed / abs_sum
        if np.abs(weights.sum()) < 1e-6:
            weights = np.ones(len(selected)) / len(selected)
    else:
        raise ValueError(f"Unknown weight method: {args.weight_method}")

    selected["weight"] = weights

    results = []
    for label in ["train", "val", "test"]:
        if label not in period_mats:
            continue
        mat = period_mats[label]
        fwd = period_results[label]
        combined = _smooth(_compute_weights(mat, weights), args.smooth_span)
        combined = combined.clip(-5, 5)

        bt = run_long_short_backtest(combined, fwd, transaction_cost=0.001)
        result = {
            "period": label,
            "n_factors": len(selected),
            "weight_method": args.weight_method,
            "sort_by": sort_by,
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
        "weights": {row["factor"]: float(row["weight"]) for _, row in selected.iterrows()},
        "selected_factors": selected.to_dict(orient="records"),
        "results": results,
    }
    with open(args.output_dir / "combination_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    selected.to_csv(args.output_dir / "selected_factors.csv", index=False)
    print(f"\nSaved results to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
