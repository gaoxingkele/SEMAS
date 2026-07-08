"""Optional TA-Lib feature wrappers.

TA-Lib is an optional dependency. If not installed, these functions raise a
helpful error.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _require_talib() -> Any:
    try:
        import talib

        return talib
    except ImportError as exc:
        raise RuntimeError(
            "TA-Lib is not installed. Install with `pip install TA-Lib` "
            "or use the core operator set."
        ) from exc


def add_rsi(df: pd.DataFrame, timeperiod: int = 14) -> pd.Series:
    """Relative Strength Index computed per symbol."""
    talib = _require_talib()
    return df.groupby(level="symbol")["close"].transform(lambda s: talib.RSI(s.values, timeperiod))


def add_macd(df: pd.DataFrame, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> pd.DataFrame:
    """MACD computed per symbol; returns a DataFrame with macd, signal, hist."""
    talib = _require_talib()

    def _macd(s: pd.Series) -> pd.DataFrame:
        macd, signal, hist = talib.MACD(s.values, fastperiod, slowperiod, signalperiod)
        return pd.DataFrame(
            {"macd": macd, "macd_signal": signal, "macd_hist": hist},
            index=s.index,
        )

    return df.groupby(level="symbol")["close"].apply(_macd).droplevel(0)


def add_bbands(df: pd.DataFrame, timeperiod: int = 20, nbdevup: int = 2, nbdevdn: int = 2) -> pd.DataFrame:
    """Bollinger Bands computed per symbol."""
    talib = _require_talib()

    def _bands(s: pd.Series) -> pd.DataFrame:
        upper, middle, lower = talib.BBANDS(s.values, timeperiod, nbdevup, nbdevdn)
        return pd.DataFrame(
            {"bband_upper": upper, "bband_middle": middle, "bband_lower": lower},
            index=s.index,
        )

    return df.groupby(level="symbol")["close"].apply(_bands).droplevel(0)


def add_talib_features(df: pd.DataFrame, include: list[str] | None = None) -> pd.DataFrame:
    """Add a standard set of TA-Lib indicators to a panel DataFrame.

    The panel is expected to have a MultiIndex (symbol, date) and contain
    ``open``, ``high``, ``low``, ``close``, ``volume`` columns. New columns are
    added in-place and the updated DataFrame is returned.

    Parameters
    ----------
    df : pd.DataFrame
        Input panel.
    include : list[str] | None
        Subset of indicator names to compute. If None, all supported indicators
        are computed.

    Returns
    -------
    pd.DataFrame
        Panel with additional TA-Lib feature columns.
    """
    talib = _require_talib()
    out = df.copy()

    # Ensure columns are float64 for TA-Lib.
    required_price = ["open", "high", "low", "close"]
    for col in required_price:
        if col in out.columns:
            out[col] = out[col].astype(np.float64)
    if "volume" in out.columns:
        out["volume"] = out["volume"].astype(np.float64)

    all_indicators = {
        "rsi_14", "macd", "macd_signal", "macd_hist",
        "bband_upper", "bband_middle", "bband_lower",
        "cci_20", "adx_14", "willr_14", "atr_14",
        "mom_10", "sma_20", "ema_12", "ema_26",
    }
    indicators = set(include) if include else all_indicators

    def _group_apply_close(func, *args, **kwargs) -> pd.Series:
        return out.groupby(level="symbol")["close"].transform(
            lambda s: pd.Series(func(s.values.astype(np.float64), *args, **kwargs), index=s.index)
        )

    def _group_apply_hlc(func, **kwargs) -> pd.Series:
        def _apply(g: pd.DataFrame) -> pd.Series:
            h = g["high"].values.astype(np.float64)
            l = g["low"].values.astype(np.float64)
            c = g["close"].values.astype(np.float64)
            return pd.Series(func(h, l, c, **kwargs), index=g.index)
        return out.groupby(level="symbol")[required_price].apply(_apply).droplevel(0)

    if "rsi_14" in indicators:
        out["rsi_14"] = _group_apply_close(talib.RSI, 14)
    if {"macd", "macd_signal", "macd_hist"} & indicators:
        macd_df = add_macd(out)
        for col in ["macd", "macd_signal", "macd_hist"]:
            if col in indicators:
                out[col] = macd_df[col]
    if {"bband_upper", "bband_middle", "bband_lower"} & indicators:
        bbands_df = add_bbands(out)
        for col in ["bband_upper", "bband_middle", "bband_lower"]:
            if col in indicators:
                out[col] = bbands_df[col]
    if "cci_20" in indicators:
        out["cci_20"] = _group_apply_hlc(talib.CCI, timeperiod=20)
    if "adx_14" in indicators:
        out["adx_14"] = _group_apply_hlc(talib.ADX, timeperiod=14)
    if "willr_14" in indicators:
        out["willr_14"] = _group_apply_hlc(talib.WILLR, timeperiod=14)
    if "atr_14" in indicators:
        out["atr_14"] = _group_apply_hlc(talib.ATR, timeperiod=14)
    if "mom_10" in indicators:
        out["mom_10"] = _group_apply_close(talib.MOM, 10)
    if "sma_20" in indicators:
        out["sma_20"] = _group_apply_close(talib.SMA, 20)
    if "ema_12" in indicators:
        out["ema_12"] = _group_apply_close(talib.EMA, 12)
    if "ema_26" in indicators:
        out["ema_26"] = _group_apply_close(talib.EMA, 26)

    return out


TALIB_FEATURE_COLUMNS = [
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "bband_upper",
    "bband_middle",
    "bband_lower",
    "cci_20",
    "adx_14",
    "willr_14",
    "atr_14",
    "mom_10",
    "sma_20",
    "ema_12",
    "ema_26",
]
