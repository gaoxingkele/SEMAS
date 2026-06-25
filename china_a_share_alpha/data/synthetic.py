"""Synthetic China A-share panel data for offline demo/CI."""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_synthetic_panel(
    n_symbols: int = 50,
    n_days: int = 252,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a synthetic OHLCV panel with a weak mean-reversion signal.

    The forward return is partially predictable from the 5-day rolling mean
    of the previous day's return, so an evolved `cs_rank(ts_mean(return, 5))`
    should obtain a positive IC.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n_days, freq="B")
    symbols = [f"{i:06d}.SH" if i % 2 == 0 else f"{i:06d}.SZ" for i in range(1, n_symbols + 1)]

    rows = []
    for sym in symbols:
        # Random walk with small mean-reversion component.
        ret = rng.normal(0, 0.02, size=n_days)
        signal = np.zeros(n_days)
        for t in range(5, n_days):
            signal[t] = -0.3 * ret[t - 1] - 0.2 * ret[t - 2] + rng.normal(0, 0.005)
        ret = ret + signal

        close = 10.0 * np.exp(np.cumsum(ret))
        open_ = close * (1 + rng.normal(0, 0.005, size=n_days))
        high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.02, size=n_days))
        low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.02, size=n_days))
        volume = rng.integers(1_000_000, 10_000_000, size=n_days)
        vwap = (high + low + close) / 3.0 + rng.normal(0, 0.01, size=n_days)

        rows.append(
            pd.DataFrame(
                {
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "vwap": vwap,
                    "return": ret,
                },
                index=pd.MultiIndex.from_product([[sym], dates], names=["symbol", "date"]),
            )
        )

    df = pd.concat(rows).sort_index()
    df["forward_return"] = df.groupby(level="symbol")["return"].shift(-1)
    return df.dropna()
