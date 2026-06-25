"""Factor quality metrics: IC, RankIC, ICIR, long-short returns, turnover."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _common_index(factor: pd.Series, forward_return: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({"factor": factor, "forward_return": forward_return})
    return df.dropna()


def ic_score(factor: pd.Series, forward_return: pd.Series) -> float:
    """Pearson correlation between factor and forward return per date, averaged."""
    df = _common_index(factor, forward_return)
    if df.empty:
        return 0.0
    per_day = df.groupby(level="date").apply(
        lambda g: g["factor"].corr(g["forward_return"]),
        include_groups=False,
    )
    return float(per_day.mean())


def rank_ic_score(factor: pd.Series, forward_return: pd.Series) -> float:
    """Spearman correlation between factor and forward return per date, averaged."""
    df = _common_index(factor, forward_return)
    if df.empty:
        return 0.0

    def _spearman(g: pd.DataFrame) -> float:
        return g["factor"].corr(g["forward_return"], method="spearman")

    per_day = df.groupby(level="date").apply(_spearman, include_groups=False)
    return float(per_day.mean())


def icir_score(factor: pd.Series, forward_return: pd.Series) -> float:
    """Information Coefficient Information Ratio = mean(IC) / std(IC)."""
    df = _common_index(factor, forward_return)
    if df.empty:
        return 0.0
    per_day = df.groupby(level="date").apply(
        lambda g: g["factor"].corr(g["forward_return"]),
        include_groups=False,
    )
    std = per_day.std()
    return float(per_day.mean() / (std + 1e-8))


def turnover_score(factor: pd.Series) -> float:
    """Average per-symbol turnover of normalized factor weights."""
    normalized = factor.groupby(level="date").transform(lambda s: s / (s.abs().sum() + 1e-8))
    turnover = (
        normalized.groupby(level="symbol").diff().abs().groupby(level="date").mean()
    )
    return float(turnover.mean())


def long_short_return(
    factor: pd.Series,
    forward_return: pd.Series,
    quantiles: int = 5,
) -> tuple[float, float]:
    """Long-short top/bottom quantile return and Sharpe.

    Returns:
        (annualized_return, sharpe_ratio)
    """
    df = _common_index(factor, forward_return)
    if df.empty:
        return 0.0, 0.0

    df["quantile"] = df.groupby(level="date")["factor"].transform(
        lambda s: pd.qcut(s, quantiles, labels=False, duplicates="drop")
    )
    long = df[df["quantile"] == quantiles - 1].groupby(level="date")["forward_return"].mean()
    short = df[df["quantile"] == 0].groupby(level="date")["forward_return"].mean()
    ls = (long - short).fillna(0.0)
    if ls.empty:
        return 0.0, 0.0
    mean_ret = float(ls.mean())
    sharpe = float(mean_ret / (ls.std() + 1e-8))
    # Annualize assuming daily returns.
    return float(mean_ret * 252), float(sharpe * np.sqrt(252))


def combined_factor_score(
    output: dict,
    expected: dict | None = None,
) -> float:
    """SEMAS-compatible metric: weighted IC - turnover penalty.

    `output` must contain `factor` and `forward_return` Series.
    """
    factor = output.get("factor")
    forward_return = output.get("forward_return")
    if factor is None or forward_return is None:
        return 0.0

    ic = abs(ic_score(factor, forward_return))
    icir = icir_score(factor, forward_return)
    turnover = turnover_score(factor)

    # Reward IC/IR and penalize high turnover.
    score = 0.5 * ic + 0.3 * min(1.0, abs(icir)) - 0.5 * turnover
    return max(0.0, min(1.0, score))
