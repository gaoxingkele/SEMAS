"""Optional Qlib data loader with train/test split.

If `qlib` is installed, this module loads China A-share data in Qlib binary
format. Otherwise it falls back to the synthetic panel generator so tests and
demos still pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from china_a_share_alpha.data.sector_mapping import merge_sector_market_cap
from china_a_share_alpha.data.synthetic import make_synthetic_panel
from china_a_share_alpha.data.tushare_loader import load_tushare_data


def load_data(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load train/test data from synthetic, Qlib, or Tushare."""
    data_source = config.get("data_source", "synthetic")
    if data_source == "qlib":
        return _load_qlib_data(config)
    if data_source == "tushare":
        return load_tushare_data(config)
    return make_synthetic_panel(
        n_symbols=config.get("n_symbols", 50),
        n_days=config.get("n_days", 252),
        seed=config.get("seed", 42),
        split_date=config.get("split_date", "2020-07-01"),
    )


def _load_qlib_data(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        import qlib
        from qlib.data import D
    except ImportError as exc:
        raise RuntimeError(
            "Qlib is not installed. Install with `pip install pyqlib` "
            "or use data_source: synthetic."
        ) from exc

    data_dir = config.get("data_dir", "~/.qlib/qlib_data/cn_data")
    qlib.init(provider_uri=str(Path(data_dir).expanduser()))

    instruments = config.get("instruments", "csi300")
    start_time = config.get("start_time", "2018-01-01")
    end_time = config.get("end_time", "2023-12-31")
    forward_period = config.get("forward_period", 5)
    split_date = pd.Timestamp(config.get("split_date", "2021-01-04"))

    # Core OHLCV fields.
    fields = ["$open", "$high", "$low", "$close", "$volume", "$vwap"]
    # Optional neutralization fields if your Qlib data includes them.
    if config.get("load_sector", False):
        fields.append("$sector")  # user must ensure this field exists
    if config.get("load_market_cap", False):
        fields.append("$market_cap")

    df = D.features(instruments, fields, start_time=start_time, end_time=end_time)
    rename = {
        "$open": "open",
        "$high": "high",
        "$low": "low",
        "$close": "close",
        "$volume": "volume",
        "$vwap": "vwap",
    }
    if "$sector" in df.columns:
        rename["$sector"] = "sector"
    if "$market_cap" in df.columns:
        rename["$market_cap"] = "market_cap"
    df = df.rename(columns=rename)

    # Compute forward return using Qlib Ref operator.
    df["forward_return"] = (
        D.features(instruments, [f"Ref($close, -{forward_period}) / $close - 1"], start_time, end_time)
        .iloc[:, 0]
        .rename("forward_return")
    )

    df = df.reset_index()
    df = df.rename(columns={"instrument": "symbol"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index(["symbol", "date"]).sort_index().dropna()

    df = merge_sector_market_cap(df, config)

    train = df.loc[pd.IndexSlice[:, :split_date], :]
    test = df.loc[pd.IndexSlice[:, split_date:], :]
    return train, test
