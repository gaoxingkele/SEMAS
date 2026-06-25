"""Optional TA-Lib feature wrappers.

TA-Lib is an optional dependency. If not installed, these functions raise a
helpful error.
"""

from __future__ import annotations

from typing import Any

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
