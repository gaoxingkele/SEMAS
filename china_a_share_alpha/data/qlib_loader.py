"""Optional Qlib data loader.

If `qlib` is installed, this module loads China A-share data in Qlib binary
format. Otherwise it falls back to the synthetic panel generator so tests and
demos still pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from china_a_share_alpha.data.synthetic import make_synthetic_panel


def load_data(config: dict[str, Any]) -> pd.DataFrame:
    """Load data from Qlib if available, otherwise synthetic."""
    data_source = config.get("data_source", "synthetic")
    if data_source == "qlib":
        return _load_qlib_data(config)
    return make_synthetic_panel(
        n_symbols=config.get("n_symbols", 50),
        n_days=config.get("n_days", 252),
        seed=config.get("seed", 42),
    )


def _load_qlib_data(config: dict[str, Any]) -> pd.DataFrame:
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

    fields = ["$open", "$high", "$low", "$close", "$volume", "$vwap"]
    df = D.features(instruments, fields, start_time=start_time, end_time=end_time)
    df = df.rename(
        columns={
            "$open": "open",
            "$high": "high",
            "$low": "low",
            "$close": "close",
            "$volume": "volume",
            "$vwap": "vwap",
        }
    )

    # Compute forward return using Qlib Ref operator.
    df["forward_return"] = (
        D.features(instruments, [f"Ref($close, -{forward_period}) / $close - 1"], start_time, end_time)
        .iloc[:, 0]
        .rename("forward_return")
    )

    df = df.reset_index()
    df = df.rename(columns={"instrument": "symbol"})
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index(["symbol", "date"]).sort_index().dropna()
