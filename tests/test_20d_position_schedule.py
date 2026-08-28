from __future__ import annotations

import numpy as np
import pandas as pd

from china_a_share_alpha.scripts.evolve_20d_position_schedule import (
    PreparedFold,
    backtest_schedule,
    normalize_schedule,
    rank_percentiles_to_bins,
    strategy_verdict,
)


def _fold(
    returns: list[list[float]],
    base_long: list[list[float]],
    rank_bins: list[list[int]],
    short_target: list[list[float]] | None = None,
) -> PreparedFold:
    rows = len(returns)
    columns = len(returns[0])
    return PreparedFold(
        name="tiny",
        dates=pd.date_range("2024-01-01", periods=rows, freq="B"),
        symbols=pd.Index([f"S{i}" for i in range(columns)]),
        returns=np.asarray(returns, dtype=float),
        base_long=np.asarray(base_long, dtype=float),
        rank_bins=np.asarray(rank_bins, dtype=np.int8),
        short_target=(
            np.zeros((rows, columns), dtype=float)
            if short_target is None
            else np.asarray(short_target, dtype=float)
        ),
    )


def test_rank_percentile_bins_use_closed_upper_decile_boundaries():
    values = np.asarray([[0.01, 0.10, 0.10001, 0.20, 0.999, 1.0, np.nan]])

    bins = rank_percentiles_to_bins(values)

    assert bins.tolist() == [[0, 0, 1, 1, 9, 9, -1]]


def test_schedule_normalization_quantizes_and_enforces_monotonicity():
    values = np.asarray([0.94, 1.47, 1.26, 0.83, 0.91, 0.44, 0.22, 0.31, -0.1, 0.0])

    schedule = normalize_schedule(values, step=0.1, max_multiplier=1.5)

    assert schedule[0] == 1.0
    assert np.all(np.diff(schedule) <= 0)
    assert np.allclose(schedule * 10, np.round(schedule * 10))


def test_backtest_uses_previous_day_position_without_lookahead():
    fold = _fold(
        returns=[[0.10], [0.0], [0.0]],
        base_long=[[1.0], [0.0], [0.0]],
        rank_bins=[[0], [0], [0]],
    )

    result = backtest_schedule(fold, [1.0] * 10, transaction_cost=0.0)

    assert result["total_return"] == 0.0


def test_add_position_multiplier_applies_to_next_day_return():
    fold = _fold(
        returns=[[0.0], [0.10], [0.0]],
        base_long=[[1.0], [0.0], [0.0]],
        rank_bins=[[0], [9], [9]],
    )
    schedule = [1.5, 1.4, 1.3, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2, 0.0]

    result = backtest_schedule(fold, schedule, transaction_cost=0.0)

    assert np.isclose(result["total_return"], 0.15)
    assert result["max_gross_exposure"] == 1.5


def test_transaction_cost_uses_actual_target_weight_changes():
    fold = _fold(
        returns=[[0.0], [0.0], [0.0]],
        base_long=[[1.0], [0.0], [0.0]],
        rank_bins=[[0], [0], [0]],
    )

    result = backtest_schedule(fold, [1.0] * 10, transaction_cost=0.001)

    assert np.isclose(result["total_transaction_cost"], 0.002)


def test_static_winner_produces_explicit_rollback_verdict():
    verdict = strategy_verdict(
        {"baseline_name": "static_100pct"},
        {},
        {},
    )

    assert verdict == "STATIC_BASELINE_SELECTED"


def test_dynamic_winner_must_pass_final_improvement_and_drawdown_gates():
    results = {
        "winner": {"sharpe": 1.3, "max_drawdown": -0.11},
        "static_100pct": {"sharpe": 1.0, "max_drawdown": -0.10},
    }
    config = {
        "min_final_sharpe_improvement": 0.1,
        "max_final_drawdown_degradation": 0.02,
    }

    assert strategy_verdict({}, results, config) == "DYNAMIC_CANDIDATE_PASSED"

    results["winner"]["max_drawdown"] = -0.15
    assert strategy_verdict({}, results, config) == "DYNAMIC_CANDIDATE_REJECTED_ON_FINAL"
