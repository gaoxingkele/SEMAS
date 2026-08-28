import pandas as pd

from china_a_share_alpha.scripts.update_tushare_snapshot import merge_incremental_rows


def test_merge_incremental_rows_uses_old_fundamentals_and_new_daily_data(monkeypatch) -> None:
    dates = pd.to_datetime(["2026-05-28", "2026-05-29"])
    index = pd.MultiIndex.from_product([["000001.SZ"], dates], names=["symbol", "date"])
    old = pd.DataFrame(
        {
            "open": [10.0, 10.1],
            "high": [10.2, 10.3],
            "low": [9.9, 10.0],
            "close": [10.1, 10.2],
            "volume": [100.0, 110.0],
            "amount": [1010.0, 1122.0],
            "roe": [8.0, 8.0],
            "sector": ["bank", "bank"],
            "return": [0.0, 0.01],
            "forward_return": [0.01, 0.0],
            "vwap": [10.1, 10.2],
        },
        index=index,
    )
    daily = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260601"],
            "open": [10.2],
            "high": [10.5],
            "low": [10.1],
            "close": [10.4],
            "vol": [120.0],
            "amount": [1248.0],
        }
    )
    basic = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260601"],
            "turnover_rate": [1.2],
            "pb": [0.8],
            "total_mv": [1000.0],
            "circ_mv": [900.0],
        }
    )
    monkeypatch.setattr(
        "china_a_share_alpha.scripts.update_tushare_snapshot.add_talib_features",
        lambda frame: frame,
    )

    result = merge_incremental_rows(
        old,
        daily,
        basic,
        pd.DataFrame(),
        pd.DataFrame(),
        {"000001.SZ"},
    )

    latest = result.loc[("000001.SZ", pd.Timestamp("2026-06-01"))]
    assert latest["close"] == 10.4
    assert latest["roe"] == 8.0
    assert latest["sector"] == "bank"
    assert latest["return"] > 0
