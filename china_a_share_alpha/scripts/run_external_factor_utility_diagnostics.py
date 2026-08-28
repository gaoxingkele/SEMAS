"""Compute missing utility diagnostics for externally consistent factors.

Reads the frozen external-audit ranking, reconstructs the cached stock-disjoint
panel, and reports ICIR plus both signal and realized long-short correlations.
No candidate is added, removed, or selected by this diagnostic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from china_a_share_alpha.evaluator.metrics import icir_score
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_external_unused_csi500_validation import (
    _active_rows,
    _labels,
    _load_panel,
)


def _daily_long_short(factor: pd.Series, labels: pd.Series) -> pd.Series:
    frame = pd.DataFrame({"factor": factor, "forward_return": labels}).dropna()
    frame["quantile"] = frame.groupby(level="date")["factor"].transform(
        lambda values: pd.qcut(values, 5, labels=False, duplicates="drop")
    )
    long = frame.loc[frame["quantile"] == 4].groupby(level="date")["forward_return"].mean()
    short = frame.loc[frame["quantile"] == 0].groupby(level="date")["forward_return"].mean()
    return (long - short).dropna().sort_index()


def _window(series: pd.Series, start: str, end: str) -> pd.Series:
    dates = series.index.get_level_values("date")
    return series.loc[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data-start", default="20240101")
    parser.add_argument("--evaluation-start", default="20250530")
    parser.add_argument("--evaluation-end", default="20260716")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    ranking = pd.read_csv(args.ranking)
    factors = ranking.loc[ranking["utility_status"] == "externally_consistent"].copy()
    if factors.empty:
        raise RuntimeError("No externally_consistent factors in ranking.")
    membership = pd.read_csv(args.membership)
    membership["trade_date"] = pd.to_datetime(membership["trade_date"])
    panel = _load_panel(
        None,
        sorted(membership["con_code"].unique()),
        args.data_start,
        args.evaluation_end,
        args.cache_dir,
    )
    panel = _active_rows(panel, membership)
    start = pd.Timestamp(args.evaluation_start)
    end = pd.Timestamp(args.evaluation_end)
    factor_values: dict[str, pd.Series] = {}
    daily_returns: dict[str, pd.Series] = {}
    rows: list[dict[str, object]] = []
    for _, factor_row in factors.iterrows():
        factor = parse_expression(factor_row["expression"]).eval(panel)
        labels = _labels(panel, int(factor_row["horizon"]))
        mask = (factor.index.get_level_values("date") >= start) & (
            factor.index.get_level_values("date") <= end
        )
        factor = factor.loc[mask]
        labels = labels.loc[mask]
        factor_values[str(factor_row["factor_id"])] = factor
        daily_returns[str(factor_row["factor_id"])] = _daily_long_short(factor, labels)
        rows.append(
            {
                "factor_id": factor_row["factor_id"],
                "horizon": factor_row["horizon"],
                "iteration": factor_row["iteration"],
                "expression": factor_row["expression"],
                "sharpe": factor_row["sharpe"],
                "ic": factor_row["ic"],
                "rank_ic": factor_row["rank_ic"],
                "annualized_return": factor_row["annualized_return"],
                "cost_adjusted_return": factor_row["cost_adjusted_return"],
                "max_drawdown": factor_row["max_drawdown"],
                "turnover": factor_row["turnover"],
                "observations": factor_row["observations"],
                "icir_full": icir_score(factor, labels),
                "icir_2025": icir_score(
                    _window(factor, "2025-05-30", "2025-12-31"),
                    _window(labels, "2025-05-30", "2025-12-31"),
                ),
                "icir_2026": icir_score(
                    _window(factor, "2026-01-01", args.evaluation_end),
                    _window(labels, "2026-01-01", args.evaluation_end),
                ),
                "daily_ls_observations": len(daily_returns[str(factor_row["factor_id"])]),
            }
        )
    diagnostics = pd.DataFrame(rows).sort_values("sharpe", ascending=False)
    diagnostics.to_csv(
        args.output_dir / "externally_consistent_factor_diagnostics.csv", index=False
    )
    daily_frame = pd.DataFrame(daily_returns)
    daily_frame.corr().to_csv(args.output_dir / "daily_long_short_return_correlation.csv")
    ranks = {
        name: series.groupby(level="date").rank(pct=True) for name, series in factor_values.items()
    }
    pd.DataFrame(ranks).corr(method="spearman").to_csv(
        args.output_dir / "cross_sectional_signal_correlation.csv"
    )
    daily_frame.to_csv(args.output_dir / "externally_consistent_daily_long_short_returns.csv")
    print(f"diagnosed={len(diagnostics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
