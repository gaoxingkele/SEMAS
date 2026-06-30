"""Explainable single factors and multi-factor portfolios for A-share backtests.

These factors are chosen to cover distinct economic/behavioral styles:

- Momentum (20-day): stocks that performed well recently tend to keep
  performing well in China A-shares over short horizons.
- Short-term reversal (5-day): very recent winners tend to mean-revert in the
  next few days, especially among retail-heavy A-share names.
- Volume-price correlation: liquidity/volume interacting with price trends.
- Low volatility: lower realized volatility has historically been rewarded.
- Value (low PB): cheap stocks measured by price-to-book.

The multi-factor combinations blend styles across time horizons and orthogonal
sources, which improves robustness versus any single alpha.
"""

from __future__ import annotations

from china_a_share_alpha.factor.expression import (
    BinaryOp,
    RollingBinaryOp,
    RollingOp,
    UnaryOp,
    Var,
)


def momentum_factor(window: int = 20):
    """Cross-sectional rank of rolling mean returns: momentum."""
    return UnaryOp("cs_rank", RollingOp("ts_mean", Var("return"), window))


def reversal_factor(window: int = 5):
    """Negative rank of short-term rolling mean returns: mean reversion."""
    return UnaryOp("neg", UnaryOp("cs_rank", RollingOp("ts_mean", Var("return"), window)))


def volume_price_factor(window: int = 20):
    """Rank of correlation between close and volume: volume confirms trend."""
    return UnaryOp("cs_rank", RollingBinaryOp("ts_corr", Var("close"), Var("volume"), window))


def low_volatility_factor(window: int = 20):
    """Negative rank of realized volatility: low-vol anomaly."""
    return UnaryOp("neg", UnaryOp("cs_rank", RollingOp("ts_std", Var("return"), window)))


def value_factor():
    """Negative rank of price-to-book: value anomaly.

    Tushare `daily_basic` provides `pb`. Higher pb -> lower expected return.
    """
    return UnaryOp("neg", UnaryOp("cs_rank", Var("pb")))


def liquidity_factor(window: int = 20):
    """Negative rank of turnover: lower turnover -> less arbitraged alpha."""
    return UnaryOp("neg", UnaryOp("cs_rank", RollingOp("ts_mean", Var("turnover_rate"), window)))


def high_zscore_factor(window: int = 20):
    """Rolling z-score of high price: mean-reversion around recent high range."""
    return UnaryOp("cs_rank", RollingOp("ts_zscore", Var("high"), window))


SINGLE_FACTORS = {
    "momentum_20": momentum_factor(20),
    "reversal_5": reversal_factor(5),
    "volume_price_20": volume_price_factor(20),
    "low_vol_20": low_volatility_factor(20),
    "high_zscore_20": high_zscore_factor(20),
    "value_pb": value_factor(),
    "liquidity_20": liquidity_factor(20),
}


def multi_timeframe_factor():
    """Combine medium-term momentum and short-term reversal.

    Rationale: momentum and reversal operate on different horizons and are
    largely orthogonal in A-shares.
    """
    return BinaryOp(
        "add",
        UnaryOp("cs_rank", RollingOp("ts_mean", Var("return"), 20)),
        UnaryOp("neg", UnaryOp("cs_rank", RollingOp("ts_mean", Var("return"), 5))),
    )


def multi_style_equal_weight():
    """Equal-weighted combination of momentum, reversal, volume, low-vol, value."""
    from china_a_share_alpha.factor.expression import BinaryOp

    f1 = momentum_factor(20)
    f2 = reversal_factor(5)
    f3 = volume_price_factor(20)
    f4 = low_volatility_factor(20)
    f5 = value_factor()
    return BinaryOp(
        "add",
        BinaryOp("add", BinaryOp("add", BinaryOp("add", f1, f2), f3), f4),
        f5,
    )


PORTFOLIO_FACTORS = {
    "multi_timeframe": multi_timeframe_factor(),
    "multi_style_equal": multi_style_equal_weight(),
}
