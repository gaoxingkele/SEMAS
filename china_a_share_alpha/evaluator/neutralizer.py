"""Industry / market-cap neutralization utilities.

In production, supply sector mappings (e.g. from Qlib, Tushare, or Wind) and
market-cap data, then regress the factor against dummies + log(mktcap) and
return residuals.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def neutralize_by_sector(factor: pd.Series, sector: pd.Series) -> pd.Series:
    """Cross-sectionally demean within each sector per date."""
    df = pd.DataFrame({"factor": factor, "sector": sector})
    return df.groupby(level="date").apply(
        lambda g: g["factor"] - g.groupby("sector")["factor"].transform("mean"),
        include_groups=False,
    ).reset_index(level=0, drop=True).reindex(factor.index)


def neutralize_by_market_cap(factor: pd.Series, market_cap: pd.Series) -> pd.Series:
    """Return residuals of factor ~ log(market_cap) per date."""
    df = pd.DataFrame({"factor": factor, "log_cap": np.log(market_cap.replace(0, np.nan))}).dropna()
    residuals = df.groupby(level="date").apply(
        lambda g: g["factor"] - g["log_cap"] * (g["factor"].cov(g["log_cap"]) / g["log_cap"].var()),
        include_groups=False,
    )
    return residuals.reset_index(level=0, drop=True).reindex(factor.index)


def apply_neutralization(
    factor: pd.Series,
    data: pd.DataFrame,
    neutralize_sector: bool = False,
    neutralize_market_cap: bool = False,
) -> pd.Series:
    """Apply neutralization based on available columns."""
    if neutralize_sector and "sector" in data.columns:
        factor = neutralize_by_sector(factor, data["sector"])
    if neutralize_market_cap and "market_cap" in data.columns:
        factor = neutralize_by_market_cap(factor, data["market_cap"])
    return factor
