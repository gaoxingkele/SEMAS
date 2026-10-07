from __future__ import annotations

import numpy as np
import pandas as pd

from china_a_share_alpha.backtest.t1_exit_policy import market_group, run_t1_exit_backtest


def _fixture(
    closes: list[float], highs: list[float] | None = None
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2026-01-01", periods=len(closes), freq="B")
    symbols = [f"00000{i}.SZ" for i in range(1, 6)]
    rows = []
    for symbol_offset, symbol in enumerate(symbols):
        scale = 1.0 + symbol_offset * 0.01
        for index, (date, close) in enumerate(zip(dates, closes, strict=True)):
            value = close * scale
            pre_close = closes[index - 1] * scale if index else value
            high = (highs[index] if highs else close) * scale
            rows.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "open": value,
                    "high": high,
                    "low": value,
                    "close": value,
                    "pre_close": pre_close,
                    "volume": 1000.0,
                }
            )
    panel = pd.DataFrame(rows).set_index(["symbol", "date"]).sort_index()
    signal = (
        pd.Series(
            np.tile(np.arange(1, 6, dtype=float), len(dates)),
            index=pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"]),
        )
        .reorder_levels(["symbol", "date"])
        .sort_index()
    )
    metadata = pd.DataFrame({"symbol": symbols, "name": symbols, "market": "主板"})
    return signal, panel, metadata


def test_market_groups_cover_innovation_and_bse() -> None:
    assert market_group("主板") == "main"
    assert market_group("创业板") == "innovation"
    assert market_group("科创板") == "innovation"
    assert market_group("北交所") == "bse"


def test_five_day_expiry_is_d_plus_six() -> None:
    signal, panel, metadata = _fixture([10.0] * 9)
    metrics, trades, _ = run_t1_exit_backtest(
        signal, panel, metadata, horizon=5, selection_fraction=0.2, transaction_cost=0, slippage=0
    )
    first = trades.iloc[0]
    assert first.entry_signal_date == pd.Timestamp("2026-01-01")
    assert first.factor_score == 100.0
    assert first.entry_date == pd.Timestamp("2026-01-02")
    assert first.exit_date == pd.Timestamp("2026-01-09")
    assert first.post_buy_days == 5
    assert first.exit_reason == "expiry"
    assert not first.profit_activated
    assert first.peak_return == 0.0
    assert first.max_adverse_return == 0.0
    assert metrics["n_trades"] >= 1


def test_trailing_profit_is_close_confirmed_and_next_open_executed() -> None:
    closes = [10.0, 10.0, 11.6, 10.6, 10.5, 10.5, 10.5]
    signal, panel, metadata = _fixture(closes, highs=[10.0, 10.0, 11.6, 11.6, 10.5, 10.5, 10.5])
    _, trades, _ = run_t1_exit_backtest(
        signal, panel, metadata, horizon=5, selection_fraction=0.2, transaction_cost=0, slippage=0
    )
    first = trades.iloc[0]
    assert first.exit_reason == "trailing_profit"
    assert first.exit_date == pd.Timestamp("2026-01-07")


def test_limit_down_exit_waits_for_a_sellable_open() -> None:
    signal, panel, metadata = _fixture([10.0, 10.0, 9.0, 8.1, 8.2, 8.3, 8.4])
    _, trades, _ = run_t1_exit_backtest(
        signal, panel, metadata, horizon=5, selection_fraction=0.2, transaction_cost=0, slippage=0
    )
    first = trades.iloc[0]
    assert first.exit_reason == "limit_down_stop"
    assert first.exit_date == pd.Timestamp("2026-01-07")
    assert first.exit_delay == 1
