"""Simple quantile long-short backtest."""

from __future__ import annotations

from typing import Any

import pandas as pd


def run_long_short_backtest(
    factor: pd.Series,
    forward_return: pd.Series,
    quantiles: int = 5,
) -> dict[str, Any]:
    """Return long-short performance summary."""
    from china_a_share_alpha.evaluator.metrics import long_short_return

    ann_ret, sharpe = long_short_return(factor, forward_return, quantiles)
    df = pd.DataFrame({"factor": factor, "forward_return": forward_return}).dropna()
    if df.empty:
        return {"annualized_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0}

    df["quantile"] = df.groupby(level="date")["factor"].transform(
        lambda s: pd.qcut(s, quantiles, labels=False, duplicates="drop")
    )
    long = df[df["quantile"] == quantiles - 1].groupby(level="date")["forward_return"].mean()
    short = df[df["quantile"] == 0].groupby(level="date")["forward_return"].mean()
    ls = (long - short).fillna(0.0).sort_index()
    cum = (1 + ls).cumprod()
    mdd = float((cum / cum.cummax() - 1.0).min())

    return {
        "annualized_return": ann_ret,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "daily_long_short": ls,
    }
