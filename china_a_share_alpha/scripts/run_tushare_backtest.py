"""Run historical backtests for single and combined A-share factors.

Uses Tushare data over the past 5 years and outputs a comparison report of
IC, long-short returns, Sharpe, max drawdown, and turnover.

Example:
    TUSHARE_TOKEN=xxx python -m china_a_share_alpha.scripts.run_tushare_backtest \
        --start-date 20210601 --end-date 20260601 --split-date 20240101
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.evaluator.metrics import ic_score, icir_score, rank_ic_score, turnover_score
from china_a_share_alpha.examples.tushare_factors import PORTFOLIO_FACTORS, SINGLE_FACTORS
from china_a_share_alpha.factor.expression import FactorExpr


def _zscore_series(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _evaluate_factor(
    name: str,
    factor: pd.Series,
    forward_return: pd.Series,
    train_ic: float | None = None,
    test_ic: float | None = None,
) -> dict[str, Any]:
    bt = run_long_short_backtest(factor, forward_return, transaction_cost=0.001)
    row = {
        "factor": name,
        "ic": ic_score(factor, forward_return),
        "rank_ic": rank_ic_score(factor, forward_return),
        "icir": icir_score(factor, forward_return),
        "turnover": turnover_score(factor),
        "ann_return": bt["annualized_return"],
        "sharpe": bt["sharpe"],
        "max_drawdown": bt["max_drawdown"],
        "cost_adjusted_return": bt["cost_adjusted_return"],
    }
    if train_ic is not None:
        row["train_ic"] = train_ic
    if test_ic is not None:
        row["test_ic"] = test_ic
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Backtest A-share factors via Tushare")
    parser.add_argument("--start-date", default="20210601")
    parser.add_argument("--end-date", default="20260601")
    parser.add_argument("--split-date", default="20240101")
    parser.add_argument("--output-dir", type=Path, default="./china_a_share_alpha_output/tushare_backtest")
    parser.add_argument("--token", default=None, help="Tushare token (or set TUSHARE_TOKEN env)")
    parser.add_argument("--max-symbols", type=int, default=None, help="Limit universe size for quick test")
    parser.add_argument("--evolved-csv", type=Path, default=None, help="Optional factor loop leaderboard CSV to include evolved factors")
    parser.add_argument("--evolved-top-n", type=int, default=20, help="Number of evolved factors to include")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "start_date": args.start_date,
        "end_date": args.end_date,
        "split_date": args.split_date,
        "universe": "csi300",
        "cache_dir": str(output_dir / "tushare_cache"),
    }
    if args.token:
        config["tushare_token"] = args.token

    print("Loading Tushare data...")
    train, test = load_tushare_data(config)
    if args.max_symbols:
        symbols = test.index.get_level_values("symbol").unique()[: args.max_symbols]
        train = train.loc[pd.IndexSlice[symbols, :], :]
        test = test.loc[pd.IndexSlice[symbols, :], :]

    # Use full data for backtest; train/test for IC overfit check.
    full = pd.concat([train, test]).sort_index().drop_duplicates()
    print(f"Full panel: {len(full)} rows, {full.index.get_level_values('symbol').nunique()} symbols, "
          f"{full.index.get_level_values('date').nunique()} dates")

    results = []
    factor_series_full: dict[str, pd.Series] = {}
    factor_series_train: dict[str, pd.Series] = {}
    factor_series_test: dict[str, pd.Series] = {}

    # Evaluate single factors.
    for name, expr in SINGLE_FACTORS.items():
        print(f"Evaluating {name} ...")
        factor_series_full[name] = expr.eval(full)
        factor_series_train[name] = expr.eval(train)
        factor_series_test[name] = expr.eval(test)
        row = _evaluate_factor(
            name,
            factor_series_full[name],
            full["forward_return"],
            train_ic=ic_score(factor_series_train[name], train["forward_return"]),
            test_ic=ic_score(factor_series_test[name], test["forward_return"]),
        )
        results.append(row)

    # Evaluate rule-based combined factors.
    for name, expr in PORTFOLIO_FACTORS.items():
        print(f"Evaluating {name} ...")
        factor_full = expr.eval(full)
        factor_train = expr.eval(train)
        factor_test = expr.eval(test)
        row = _evaluate_factor(
            name,
            factor_full,
            full["forward_return"],
            train_ic=ic_score(factor_train, train["forward_return"]),
            test_ic=ic_score(factor_test, test["forward_return"]),
        )
        results.append(row)

    # Data-driven IC-weighted combination: weights are proportional to train IC,
    # with sign preserved so positive-IC factors get positive weight and
    # negative-IC factors get negative weight (i.e. we short them).
    train_ics = {
        name: ic_score(factor_series_train[name], train["forward_return"])
        for name in SINGLE_FACTORS
    }
    weights = {name: np.sign(ic) * abs(ic) for name, ic in train_ics.items()}
    total_weight = sum(abs(w) for w in weights.values()) + 1e-8
    weights = {name: w / total_weight for name, w in weights.items()}

    print("Evaluating ic_weighted_train ...")
    combined_full = pd.Series(0.0, index=full.index)
    combined_train = pd.Series(0.0, index=train.index)
    combined_test = pd.Series(0.0, index=test.index)
    for name, w in weights.items():
        combined_full = combined_full + w * _zscore_series(factor_series_full[name])
        combined_train = combined_train + w * _zscore_series(factor_series_train[name])
        combined_test = combined_test + w * _zscore_series(factor_series_test[name])

    ic_weighted_row = _evaluate_factor(
        "ic_weighted_train",
        combined_full,
        full["forward_return"],
        train_ic=ic_score(combined_train, train["forward_return"]),
        test_ic=ic_score(combined_test, test["forward_return"]),
    )
    ic_weighted_row["weights"] = json.dumps(weights, ensure_ascii=False)
    results.append(ic_weighted_row)

    # Optionally evaluate evolved factors from a loop leaderboard.
    if args.evolved_csv and args.evolved_csv.exists():
        from china_a_share_alpha.factor.parser import parse_expression

        evolved_df = pd.read_csv(args.evolved_csv)
        # Keep only candidates whose train/test IC signs agree (avoid sign-flipping alphas).
        if "train_ic" in evolved_df.columns and "test_ic" in evolved_df.columns:
            evolved_df = evolved_df[
                evolved_df["train_ic"].notna()
                & evolved_df["test_ic"].notna()
                & (evolved_df["train_ic"] * evolved_df["test_ic"] >= 0)
            ]
        # Deduplicate identical expressions.
        evolved_df = evolved_df.drop_duplicates(subset=["expression"], keep="first")
        evolved_exprs = []
        for idx, expr_str in enumerate(evolved_df["expression"].head(args.evolved_top_n)):
            try:
                expr = parse_expression(expr_str)
                evolved_exprs.append((f"evolved_{idx + 1}", expr))
            except Exception as exc:
                print(f"Skipping evolved expression {expr_str}: {exc}")
        for name, expr in evolved_exprs:
            print(f"Evaluating {name} ...")
            factor_full = expr.eval(full)
            factor_train = expr.eval(train)
            factor_test = expr.eval(test)
            row = _evaluate_factor(
                name,
                factor_full,
                full["forward_return"],
                train_ic=ic_score(factor_train, train["forward_return"]),
                test_ic=ic_score(factor_test, test["forward_return"]),
            )
            results.append(row)

    df = pd.DataFrame(results)
    df = df.sort_values("sharpe", ascending=False)

    csv_path = output_dir / "factor_comparison.csv"
    df.to_csv(csv_path, index=False, float_format="%.4f")

    md_path = output_dir / "factor_comparison_report.md"

    # Build data-driven interpretation.
    best = df.iloc[0]
    best_ic = df.loc[df["ic"].idxmax()]
    best_train_test_gap = df.copy()
    best_train_test_gap["gap"] = (best_train_test_gap["train_ic"] - best_train_test_gap["test_ic"]).abs()
    most_stable = best_train_test_gap.loc[best_train_test_gap["gap"].idxmin()]

    lines = [
        "# A-Share Factor Backtest Comparison Report",
        "",
        f"**Date range:** {args.start_date} - {args.end_date}",
        f"**Universe:** CSI300 constituents",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Single vs Combined Factor Performance",
        "",
        df.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "### Factor styles",
        "",
        "- **momentum_20**: medium-term trend continuation (20-day mean return rank).",
        "- **reversal_5**: short-term mean reversion (negative 5-day mean return rank).",
        "- **volume_price_20**: volume confirmation of price trends (close-volume correlation rank).",
        "- **low_vol_20**: low-realized-volatility anomaly (negative 20-day return std rank).",
        "- **value_pb**: price-to-book value effect (negative PB rank).",
        "- **liquidity_20**: lower turnover preference (negative turnover rank).",
        "- **multi_timeframe**: equal combination of momentum_20 and reversal_5 across horizons.",
        "- **multi_style_equal**: equal combination of all six single style factors.",
        "- **ic_weighted_train**: data-driven combination weighted by in-sample IC,",
        "  with sign preserved (positive-IC factors longed, negative-IC factors shorted).",
        "",
        "### Empirical findings over the sample",
        "",
        f"- **Best Sharpe**: `{best['factor']}` ({best['sharpe']:.3f}), annualized return {best['ann_return']:.3f}.",
        f"- **Highest IC**: `{best_ic['factor']}` (IC {best_ic['ic']:.4f}, RankIC {best_ic['rank_ic']:.4f}).",
        f"- **Most stable train-test IC**: `{most_stable['factor']}` (gap {most_stable['gap']:.4f}).",
        "",
        "### Combination analysis",
        "",
        "The IC-weighted combination is constructed transparently from training-set",
        "performance: each factor receives weight proportional to its signed IC,",
        "so the portfolio mechanically overweights styles that were predictive in-sample.",
        f"Learned weights: `{ic_weighted_row['weights']}`.",
        "",
        "### Caveats",
        "",
        "- Results are before risk model / sector neutralization.",
        "- Transaction cost is assumed 10 bps one-way; real costs vary by turnover.",
        "- The sample period may favor certain styles; IC decay monitoring is recommended.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "date_range": f"{args.start_date}-{args.end_date}",
        "n_symbols": int(full.index.get_level_values("symbol").nunique()),
        "n_dates": int(full.index.get_level_values("date").nunique()),
        "best_factor_by_sharpe": best["factor"],
        "best_sharpe": float(best["sharpe"]),
        "best_factor_by_ic": best_ic["factor"],
        "best_ic": float(best_ic["ic"]),
        "ic_weights": weights,
    }
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nCSV: {csv_path}")
    print(f"Report: {md_path}")
    print(f"Best by Sharpe: {summary['best_factor_by_sharpe']} ({summary['best_sharpe']:.3f})")
    print(f"Best by IC: {summary['best_factor_by_ic']} ({summary['best_ic']:.4f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
