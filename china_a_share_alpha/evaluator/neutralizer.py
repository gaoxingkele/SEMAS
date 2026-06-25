"""Industry / market-cap neutralization utilities.

These are stubs. In production, supply sector mappings (e.g. from Qlib or
Tushare) and market-cap data, then regress the factor against dummies + log(mktcap)
and return residuals.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def neutralize_by_sector(factor: pd.Series, sector: pd.Series) -> pd.Series:
    """Cross-sectionally demean within each sector per date."""
    df = pd.DataFrame({"factor": factor, "sector": sector})
    return df.groupby(["sector", pd.Grouper(level="date")])["factor"].transform(
        lambda s: s - s.mean()
    )


def neutralize_by_market_cap(factor: pd.Series, market_cap: pd.Series) -> pd.Series:
    """Return residuals of factor ~ log(market_cap) per date."""
    df = pd.DataFrame({"factor": factor, "log_cap": np.log(market_cap.replace(0, np.nan))}).dropna()
    residuals = df.groupby(level="date").apply(
        lambda g: g["factor"] - g["log_cap"] * (g["factor"].cov(g["log_cap"]) / g["log_cap"].var()),
        include_groups=False,
    )
    return residuals.reset_index(level=0, drop=True).reindex(factor.index, fill_value=0.0)
