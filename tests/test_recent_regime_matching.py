import pandas as pd

from china_a_share_alpha.scripts.audit_recent_market_gate import (
    continuous_market_trend_gate,
    select_gate,
)
from china_a_share_alpha.scripts.evolve_recent_regime_matching import (
    recent_regime_fitness,
    return_concentration,
    stable_symbol_bucket,
)


def test_symbol_bucket_is_stable_and_bounded():
    first = stable_symbol_bucket("000001.SZ", 3)
    assert first == stable_symbol_bucket("000001.SZ", 3)
    assert 0 <= first < 3


def test_return_concentration_uses_aggregate_symbol_contribution():
    trades = pd.DataFrame(
        {
            "symbol": ["A", "A", "B"],
            "trade_return": [0.10, -0.04, 0.02],
        }
    )
    assert return_concentration(trades) == 0.75


def test_recent_fitness_hard_penalizes_negative_full_window():
    def row(cohort: str, sharpe: float, drawdown: float = -0.10):
        return {
            "cohort": cohort,
            "metrics": {"valid": True, "sharpe": sharpe, "max_drawdown": drawdown},
            "concentration": 0.05,
        }

    stable = recent_regime_fitness([row("all", 1.0), row("bucket_0", 0.5)])
    failed = recent_regime_fitness([row("all", -0.1), row("bucket_0", 0.5)])
    assert stable["fitness"] > 0
    assert failed["fitness"] < -4.9


def test_continuous_market_gate_uses_current_and_past_dates_only():
    dates = pd.date_range("2025-01-01", periods=5)
    index = pd.MultiIndex.from_product([["A", "B"], dates], names=["symbol", "date"])
    frame = pd.DataFrame({"return": [0.01] * 5 + [0.01] * 5}, index=index)
    before = continuous_market_trend_gate(frame, 3)
    changed = frame.copy()
    changed.loc[(slice(None), dates[-1]), "return"] = -0.50
    after = continuous_market_trend_gate(changed, 3)
    pd.testing.assert_series_equal(before.iloc[:-1], after.iloc[:-1])


def test_select_gate_uses_worst_selection_window():
    frame = pd.DataFrame(
        {
            "market_ma": [10, 10, 20, 20],
            "sharpe": [2.0, 0.5, 1.0, 1.1],
            "max_drawdown": [-0.10, -0.08, -0.12, -0.11],
        }
    )
    assert select_gate(frame) == 20
