import numpy as np
import pandas as pd

from china_a_share_alpha.scripts.analyze_factor_ma_correlation import (
    build_ma_deviation,
    daily_cross_sectional_spearman,
    newey_west_mean_t,
    summarize_correlations,
)


def _panel(closes: dict[str, list[float]]) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=len(next(iter(closes.values()))))
    index = pd.MultiIndex.from_product([dates, list(closes)], names=["date", "symbol"])
    values = [closes[symbol][day] for day in range(len(dates)) for symbol in closes]
    return pd.DataFrame({"close": values}, index=index)


def test_ma_deviation_uses_trailing_values_only() -> None:
    panel = _panel({"A": [1.0, 2.0, 100.0], "B": [2.0, 2.0, 2.0]})

    result = build_ma_deviation(panel, window=2).unstack("symbol")

    assert np.isnan(result.iloc[0]["A"])
    assert np.isclose(result.iloc[1]["A"], 2.0 / 1.5 - 1.0)
    assert np.isclose(result.iloc[2]["A"], 100.0 / 51.0 - 1.0)


def test_daily_spearman_is_cross_sectional() -> None:
    dates = pd.date_range("2026-01-01", periods=2)
    index = pd.MultiIndex.from_product([dates, ["A", "B", "C"]], names=["date", "symbol"])
    factor = pd.Series([1, 2, 3, 3, 2, 1], index=index, dtype=float)
    ma = pd.Series([10, 20, 30, 10, 20, 30], index=index, dtype=float)

    result = daily_cross_sectional_spearman(factor, ma, min_symbols=3)

    assert result.tolist() == [1.0, -1.0]


def test_summary_reports_hac_t_and_positive_fraction() -> None:
    sample = pd.Series([0.1, 0.2, 0.3, -0.1, 0.2])

    standard_error, t_stat = newey_west_mean_t(sample, max_lag=2)
    summary = summarize_correlations(sample, hac_lag=2)

    assert standard_error > 0
    assert np.isfinite(t_stat)
    assert summary["n_dates"] == 5
    assert np.isclose(summary["positive_fraction"], 0.8)
    assert np.isclose(summary["hac_t_stat"], t_stat)
