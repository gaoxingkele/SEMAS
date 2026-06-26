"""Tushare data loader for China A-share historical backtests.

Fetches daily price, valuation, and sector data from Tushare Pro and builds a
panel DataFrame compatible with the factor expression tree and backtest modules.

Usage:
    import os
    os.environ["TUSHARE_TOKEN"] = "..."
    from china_a_share_alpha.data.tushare_loader import load_tushare_data
    train, test = load_tushare_data({"start_date": "20210601", "end_date": "20260601"})
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tushare as ts


DEFAULT_CACHE_DIR = Path("./china_a_share_alpha_output/tushare_cache")


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError(
            "TUSHARE_TOKEN environment variable is required. "
            "Set it before running the loader."
        )
    ts.set_token(token)
    return ts.pro_api()


def _fetch_csi300_constituents(pro, trade_date: str) -> list[str]:
    """Fetch CSI300 constituents for a given date."""
    df = pro.index_weight(index_code="000300.SH", start_date=trade_date, end_date=trade_date)
    if df is None or df.empty:
        # Fallback to latest available date if exact date missing.
        df = pro.index_weight(index_code="000300.SH")
    return df["con_code"].unique().tolist()


def _fetch_daily_price(pro, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    return pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)


def _fetch_daily_basic(pro, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    return pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)


def _load_or_fetch(
    pro,
    ts_code: str,
    start_date: str,
    end_date: str,
    cache_dir: Path,
) -> pd.DataFrame:
    """Load cached daily data or fetch from Tushare."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{ts_code}_{start_date}_{end_date}.parquet"

    if cache_file.exists():
        return pd.read_parquet(cache_file)

    price = _fetch_daily_price(pro, ts_code, start_date, end_date)
    if price is None or price.empty:
        return pd.DataFrame()
    basic = _fetch_daily_basic(pro, ts_code, start_date, end_date)
    if basic is not None and not basic.empty:
        price = price.merge(
            basic[["ts_code", "trade_date", "turnover_rate", "pb", "total_mv", "circ_mv"]],
            on=["ts_code", "trade_date"],
            how="left",
        )

    price.to_parquet(cache_file)
    return price


def load_tushare_data(
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load A-share panel data from Tushare.

    Args:
        config: May contain:
            - start_date, end_date (YYYYMMDD strings)
            - split_date (YYYYMMDD string or pandas-parsable date)
            - universe: "csi300" or list of ts_codes
            - cache_dir
            - tushare_token (optional; env var TUSHARE_TOKEN takes precedence)

    Returns:
        (train_df, test_df) with MultiIndex (symbol, date) and columns:
        open, high, low, close, volume, amount, turnover_rate, pb, total_mv,
        circ_mv, return, forward_return, sector.
    """
    if config.get("tushare_token"):
        os.environ["TUSHARE_TOKEN"] = config["tushare_token"]

    pro = _get_pro()
    start_date = config.get("start_date", "20210601")
    end_date = config.get("end_date", "20260601")
    split_date = pd.Timestamp(config.get("split_date", "20240101"))
    cache_dir = Path(config.get("cache_dir", DEFAULT_CACHE_DIR))

    universe = config.get("universe", "csi300")
    if universe == "csi300":
        symbols = _fetch_csi300_constituents(pro, end_date)
    else:
        symbols = list(universe)

    if not symbols:
        raise ValueError("No symbols selected.")

    all_frames = []
    for i, ts_code in enumerate(symbols):
        try:
            df = _load_or_fetch(pro, ts_code, start_date, end_date, cache_dir)
            if df.empty:
                continue
            all_frames.append(df)
            if (i + 1) % 50 == 0:
                print(f"Loaded {i + 1}/{len(symbols)} symbols")
        except Exception as exc:
            print(f"Skipping {ts_code}: {exc}")

    if not all_frames:
        raise RuntimeError("No data fetched from Tushare.")

    data = pd.concat(all_frames, ignore_index=True)
    data["trade_date"] = pd.to_datetime(data["trade_date"], format="%Y%m%d")
    data = data.rename(columns={"ts_code": "symbol", "trade_date": "date", "vol": "volume"})
    data = data.set_index(["symbol", "date"]).sort_index()

    # Compute daily return and forward return.
    data["return"] = data.groupby(level="symbol")["close"].pct_change()
    data["forward_return"] = data.groupby(level="symbol")["return"].shift(-1)

    # Add vwap proxy = amount / volume.
    data["vwap"] = data["amount"] / (data["volume"].replace(0, np.nan))

    # Sector mapping: use synthetic deterministic sector per symbol.
    from china_a_share_alpha.data.sector_mapping import load_sector_market_cap

    symbols_idx = data.index.get_level_values("symbol").unique()
    sector_df = load_sector_market_cap(symbols_idx, config)
    data = data.join(sector_df[["sector"]], on="symbol")

    # Keep only complete rows.
    required = ["open", "high", "low", "close", "volume", "amount", "forward_return"]
    data = data.dropna(subset=required)

    train = data.loc[pd.IndexSlice[:, :split_date], :]
    test = data.loc[pd.IndexSlice[:, split_date:], :]
    return train, test
