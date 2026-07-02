"""Tushare data loader for China A-share historical backtests.

Fetches daily price, valuation, and sector data from Tushare Pro and builds a
panel DataFrame compatible with the factor expression tree and backtest modules.

Usage:
    import os
    os.environ["TUSHARE_TOKEN"] = "..."
    from china_a_share_alpha.data.tushare_loader import load_tushare_data
    train, test = load_tushare_data({"start_date": "20210601", "end_date": "20260601"})

With an in-sample validation fold:

    train, val, test = load_tushare_data_with_val(
        {"start_date": "20210601", "end_date": "20260601", "val_date": "20230101"}
    )
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tushare as ts


DEFAULT_CACHE_DIR = Path("./china_a_share_alpha_output/tushare_cache")

# Columns expected in the enriched cache. If a cached file lacks any of these,
# it is re-fetched.
ENRICHED_COLUMNS = {
    "turnover_rate",
    "pb",
    "total_mv",
    "circ_mv",
    "roe",
    "roe_dt",
    "netprofit_yoy",
    "dt_netprofit_yoy",
    "grossprofit_margin",
    "debt_to_assets",
    "ocfps",
    "eps",
    "net_elg_amount",
    "net_mf_amount",
    "hk_vol",
    "hk_ratio",
}


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


def _fetch_fina_indicator(pro, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch quarterly financial indicators and keep the most useful fields."""
    cols = [
        "ts_code",
        "ann_date",
        "roe",
        "roe_dt",
        "netprofit_yoy",
        "dt_netprofit_yoy",
        "grossprofit_margin",
        "debt_to_assets",
        "ocfps",
        "eps",
    ]
    try:
        df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
    except Exception as exc:
        print(f"  fina_indicator failed for {ts_code}: {exc}")
        return pd.DataFrame(columns=cols)
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    df = df[cols].copy()
    df["ann_date"] = pd.to_datetime(df["ann_date"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["ann_date"])
    df = df.sort_values("ann_date")
    return df


def _fetch_moneyflow(pro, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch daily money-flow data and compute net elite / net mainforce amounts."""
    try:
        df = pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
    except Exception as exc:
        print(f"  moneyflow failed for {ts_code}: {exc}")
        return pd.DataFrame(columns=["ts_code", "trade_date", "net_elg_amount", "net_mf_amount"])
    if df is None or df.empty:
        return pd.DataFrame(columns=["ts_code", "trade_date", "net_elg_amount", "net_mf_amount"])
    df = df[["ts_code", "trade_date", "buy_elg_amount", "sell_elg_amount", "net_mf_amount"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d", errors="coerce")
    df["net_elg_amount"] = df["buy_elg_amount"] - df["sell_elg_amount"]
    df = df.sort_values("trade_date")
    return df[["ts_code", "trade_date", "net_elg_amount", "net_mf_amount"]]


def _fetch_hk_hold(pro, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch northbound (HK) holdings."""
    try:
        df = pro.hk_hold(ts_code=ts_code, start_date=start_date, end_date=end_date)
    except Exception as exc:
        print(f"  hk_hold failed for {ts_code}: {exc}")
        return pd.DataFrame(columns=["ts_code", "trade_date", "hk_vol", "hk_ratio"])
    if df is None or df.empty:
        return pd.DataFrame(columns=["ts_code", "trade_date", "hk_vol", "hk_ratio"])
    df = df[["ts_code", "trade_date", "vol", "ratio"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d", errors="coerce")
    df = df.rename(columns={"vol": "hk_vol", "ratio": "hk_ratio"})
    df = df.sort_values("trade_date")
    return df


def _load_or_fetch(
    pro,
    ts_code: str,
    start_date: str,
    end_date: str,
    cache_dir: Path,
) -> pd.DataFrame:
    """Load cached daily data or fetch from Tushare with enriched fields."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{ts_code}_{start_date}_{end_date}.parquet"

    if cache_file.exists():
        cached = pd.read_parquet(cache_file)
        if ENRICHED_COLUMNS.issubset(cached.columns):
            return cached
        print(f"  Cache outdated for {ts_code}, re-fetching enriched data.")

    price = _fetch_daily_price(pro, ts_code, start_date, end_date)
    if price is None or price.empty:
        return pd.DataFrame()
    price["trade_date"] = pd.to_datetime(price["trade_date"], format="%Y%m%d", errors="coerce")

    basic = _fetch_daily_basic(pro, ts_code, start_date, end_date)
    if basic is not None and not basic.empty:
        basic["trade_date"] = pd.to_datetime(basic["trade_date"], format="%Y%m%d", errors="coerce")
        price = price.merge(
            basic[["ts_code", "trade_date", "turnover_rate", "pb", "total_mv", "circ_mv"]],
            on=["ts_code", "trade_date"],
            how="left",
        )

    # Merge fundamentals by announcement date (forward-filled to trading days).
    fina = _fetch_fina_indicator(pro, ts_code, start_date, end_date)
    if not fina.empty:
        fina = fina.rename(columns={"ann_date": "trade_date"})
        price = pd.merge_asof(
            price.sort_values("trade_date"),
            fina.sort_values("trade_date"),
            on="trade_date",
            by="ts_code",
            direction="backward",
        )
        # Forward-fill fundamentals within each symbol so quarterly values apply
        # to all subsequent trading days until the next report.
        fina_cols = ["roe", "roe_dt", "netprofit_yoy", "dt_netprofit_yoy",
                     "grossprofit_margin", "debt_to_assets", "ocfps", "eps"]
        for col in fina_cols:
            if col in price.columns:
                price[col] = price.groupby("ts_code")[col].ffill()

    # Merge daily money flow.
    mf = _fetch_moneyflow(pro, ts_code, start_date, end_date)
    if not mf.empty:
        price = price.merge(
            mf[["ts_code", "trade_date", "net_elg_amount", "net_mf_amount"]],
            on=["ts_code", "trade_date"],
            how="left",
        )

    # Merge HK northbound holdings.
    hk = _fetch_hk_hold(pro, ts_code, start_date, end_date)
    if not hk.empty:
        price = price.merge(
            hk[["ts_code", "trade_date", "hk_vol", "hk_ratio"]],
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


def split_by_date(
    data: pd.DataFrame, date: str | pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a panel into (before, from) a calendar date (inclusive on both sides)."""
    ts = pd.Timestamp(date)
    before = data.loc[pd.IndexSlice[:, :ts], :]
    after = data.loc[pd.IndexSlice[:, ts:], :]
    return before, after


def load_tushare_data_with_val(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load Tushare data and split it into train / validation / test panels.

    ``val_date`` must lie between ``start_date`` and ``split_date`` in the
    config.  The validation fold is used for factor selection and weight
    estimation without leaking the final test set.
    """
    train, test = load_tushare_data(config)
    val_date = config.get("val_date")
    if not val_date:
        raise ValueError("load_tushare_data_with_val requires 'val_date' in config.")
    train_inner, val = split_by_date(train, val_date)
    return train_inner, val, test
