"""Simple quantile long-short backtest with transaction costs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def run_long_short_backtest(
    factor: pd.Series,
    forward_return: pd.Series,
    quantiles: int = 5,
    transaction_cost: float = 0.001,
) -> dict[str, Any]:
    """Return long-short performance summary.

    Args:
        factor: Cross-sectional signal.
        forward_return: Forward return per symbol/date.
        quantiles: Number of quantile buckets.
        transaction_cost: One-way cost as a fraction (e.g. 0.001 = 10 bps).
    """
    from china_a_share_alpha.evaluator.metrics import long_short_return

    ann_ret, sharpe = long_short_return(factor, forward_return, quantiles)
    df = pd.DataFrame({"factor": factor, "forward_return": forward_return}).dropna()
    if df.empty:
        return {
            "annualized_return": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "turnover": 0.0,
            "cost_adjusted_return": 0.0,
        }

    df["quantile"] = df.groupby(level="date")["factor"].transform(
        lambda s: pd.qcut(s, quantiles, labels=False, duplicates="drop")
    )
    long = df[df["quantile"] == quantiles - 1].groupby(level="date")["forward_return"].mean()
    short = df[df["quantile"] == 0].groupby(level="date")["forward_return"].mean()
    ls = (long - short).fillna(0.0).sort_index()

    # Turnover: sum of absolute weight changes per day.
    normalized = factor.groupby(level="date").transform(lambda s: s / (s.abs().sum() + 1e-8))
    daily_turnover = normalized.groupby(level="symbol").diff().abs().groupby(level="date").sum()
    avg_turnover = float(daily_turnover.mean())

    # Cost = 2 * one-way cost * turnover (long-short rebalanced daily).
    cost = 2 * transaction_cost * avg_turnover
    cost_adjusted = ls - cost

    cum = (1 + ls).cumprod()
    mdd = float((cum / cum.cummax() - 1.0).min())

    return {
        "annualized_return": ann_ret,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "turnover": avg_turnover,
        "cost": cost,
        "cost_adjusted_return": float(cost_adjusted.mean() * 252),
        "daily_long_short": ls,
    }
