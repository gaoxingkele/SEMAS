import numpy as np
import pandas as pd

from china_a_share_alpha.scripts.analyze_factor_ma_correlation import (
    daily_cross_sectional_spearman,
)
from china_a_share_alpha.scripts.analyze_ma_neutralized_alpha import (
    cross_sectional_neutralize,
    forward_compound_return,
    layer_return_summary,
)


def test_cross_sectional_neutralization_removes_linear_ma_exposure() -> None:
    dates = pd.date_range("2026-01-01", periods=3)
    symbols = [f"S{index:02d}" for index in range(40)]
    index = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    base = np.tile(np.linspace(-2.0, 2.0, len(symbols)), len(dates))
    exposure_1 = pd.Series(base, index=index)
    exposure_2 = pd.Series(np.sin(base), index=index)
    residual_component = pd.Series(np.cos(base * 3), index=index)
    signal = 2.0 * exposure_1 - exposure_2 + 0.2 * residual_component

    neutral, diagnostics = cross_sectional_neutralize(
        signal,
        {"ma5": exposure_1, "ma10": exposure_2},
        min_symbols=30,
    )

    correlations = daily_cross_sectional_spearman(neutral, exposure_1, min_symbols=30)
    assert len(diagnostics) == 3
    assert diagnostics["r_squared"].mean() > 0.99
    assert abs(correlations.mean()) < 0.05


def test_forward_compound_return_starts_on_next_day() -> None:
    dates = pd.date_range("2026-01-01", periods=4)
    index = pd.MultiIndex.from_product([dates, ["A"]], names=["date", "symbol"])
    returns = pd.Series([0.01, 0.02, 0.03, 0.04], index=index)

    result = forward_compound_return(returns, horizon=2).unstack("symbol")

    assert np.isclose(result.iloc[0]["A"], (1.02 * 1.03) - 1)
    assert np.isclose(result.iloc[1]["A"], (1.03 * 1.04) - 1)
    assert np.isnan(result.iloc[2]["A"])


def test_layer_returns_report_top_minus_bottom() -> None:
    dates = pd.date_range("2026-01-01", periods=3)
    symbols = [f"S{index:02d}" for index in range(50)]
    index = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    values = np.tile(np.arange(50, dtype=float), len(dates))
    signal = pd.Series(values, index=index)
    forward = pd.Series(values / 1000.0, index=index)

    summary = layer_return_summary(
        signal,
        forward,
        n_layers=5,
        min_symbols=30,
        hac_lag=1,
    )

    assert summary["monotonic_steps"] == 4
    assert summary["top_minus_bottom"] > 0
    assert summary["mean_forward_returns"]["q5"] > summary["mean_forward_returns"]["q1"]
