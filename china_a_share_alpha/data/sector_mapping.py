"""Sector and market-cap mapping utilities.

In production, supply a CSV with columns:
    symbol, sector, market_cap

If no CSV is provided, the loader falls back to a deterministic synthetic
mapping keyed by symbol name so neutralization can still be demonstrated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SECTOR_NAMES = [
    "银行", "非银金融", "房地产", "医药生物", "电子", "计算机",
    "食品饮料", "电力设备", "汽车", "机械", "化工", "有色",
    "传媒", "通信", "家电", "交通运输", "建筑", "农林牧渔",
]


def _synthetic_sector_for_symbol(symbol: str, rng: np.random.Generator) -> str:
    # Deterministic sector assignment based on symbol hash.
    idx = int(hash(symbol) % len(SECTOR_NAMES))
    return SECTOR_NAMES[idx]


def _synthetic_market_cap_for_symbol(symbol: str, rng: np.random.Generator) -> float:
    # Deterministic log-normal market cap keyed by symbol hash.
    seed = abs(hash(symbol)) % (2**31)
    local_rng = np.random.default_rng(seed)
    return float(local_rng.lognormal(22, 1.2))


def load_sector_market_cap(
    symbols: pd.Index,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Return a DataFrame indexed by symbol with sector and market_cap columns.

    If `sector_csv` is provided in config, read from disk; otherwise generate
    deterministic synthetic mappings.
    """
    sector_csv = config.get("sector_csv")
    if sector_csv and Path(sector_csv).exists():
        df = pd.read_csv(sector_csv, encoding="utf-8")
        df = df.set_index("symbol")
        df = df.reindex(symbols)
        df["sector"] = df["sector"].fillna("unknown")
        df["market_cap"] = df["market_cap"].fillna(df["market_cap"].median())
        return df

    rng = np.random.default_rng(config.get("seed", 42))
    rows = []
    for sym in symbols:
        rows.append(
            {
                "sector": _synthetic_sector_for_symbol(sym, rng),
                "market_cap": _synthetic_market_cap_for_symbol(sym, rng),
            }
        )
    return pd.DataFrame(rows, index=symbols)


def merge_sector_market_cap(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Add sector / market_cap columns to a panel DataFrame if not present."""
    if "sector" in data.columns and "market_cap" in data.columns:
        return data
    symbols = data.index.get_level_values("symbol").unique()
    mapping = load_sector_market_cap(symbols, config)
    data = data.join(mapping, on="symbol")
    return data
