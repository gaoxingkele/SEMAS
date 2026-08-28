"""No-lookahead cohort backtest for rank-based position schedules."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PreparedFold:
    name: str
    dates: pd.DatetimeIndex
    symbols: pd.Index
    returns: np.ndarray
    base_long: np.ndarray
    rank_bins: np.ndarray
    short_target: np.ndarray


def rank_percentiles_to_bins(rank_values: np.ndarray) -> np.ndarray:
    """Map percentile ranks (0, 1] to zero-based 10% bins."""
    bins = np.full(rank_values.shape, -1, dtype=np.int8)
    valid = np.isfinite(rank_values)
    bins[valid] = np.clip(
        np.ceil(rank_values[valid] * 10).astype(int) - 1,
        0,
        9,
    )
    return bins


def prepare_fold(
    name: str,
    signal: pd.Series,
    panel: pd.DataFrame,
    horizon: int,
    selection_fraction: float,
) -> PreparedFold:
    """Prepare fixed cohort and daily rank arrays for schedule evaluation."""
    dates = panel.index.get_level_values("date").unique().sort_values()
    symbols = panel.index.get_level_values("symbol").unique().sort_values()
    signal_wide = signal.unstack("symbol").reindex(index=dates, columns=symbols)
    returns_wide = panel["return"].unstack("symbol").reindex(index=dates, columns=symbols)

    ranks = signal_wide.rank(axis=1, pct=True, ascending=False)
    rank_values = ranks.to_numpy(dtype=float)
    rank_bins = rank_percentiles_to_bins(rank_values)

    base_long = np.zeros(rank_values.shape, dtype=np.float64)
    short_target = np.zeros(rank_values.shape, dtype=np.float64)
    active_longs = np.zeros(len(symbols), dtype=bool)
    active_shorts = np.zeros(len(symbols), dtype=bool)
    long_base_weight = 0.0
    short_base_weight = 0.0

    for day_index in range(len(dates)):
        if day_index % horizon == 0:
            row = signal_wide.iloc[day_index].to_numpy(dtype=float)
            valid_indices = np.flatnonzero(np.isfinite(row))
            active_longs[:] = False
            active_shorts[:] = False
            if len(valid_indices) >= 20:
                count = max(1, int(len(valid_indices) * selection_fraction))
                ordered = valid_indices[np.argsort(row[valid_indices])]
                active_shorts[ordered[:count]] = True
                active_longs[ordered[-count:]] = True
                long_base_weight = 1.0 / count
                short_base_weight = -1.0 / count
            else:
                long_base_weight = 0.0
                short_base_weight = 0.0
        base_long[day_index, active_longs] = long_base_weight
        short_target[day_index, active_shorts] = short_base_weight

    return PreparedFold(
        name=name,
        dates=pd.DatetimeIndex(dates),
        symbols=symbols,
        returns=np.nan_to_num(returns_wide.to_numpy(dtype=float), nan=0.0),
        base_long=base_long,
        rank_bins=rank_bins,
        short_target=short_target,
    )


def backtest_schedule(
    fold: PreparedFold,
    schedule: list[float] | np.ndarray,
    transaction_cost: float,
) -> dict[str, float]:
    """Apply day-d targets to day-d+1 returns and charge actual target changes."""
    schedule_array = np.asarray(schedule, dtype=float)
    if schedule_array.shape != (10,):
        raise ValueError("schedule must contain exactly 10 rank-decile multipliers")
    if np.any(schedule_array < 0):
        raise ValueError("schedule multipliers must be non-negative")

    lookup = np.concatenate([schedule_array, [0.0]])
    safe_bins = np.where(fold.rank_bins >= 0, fold.rank_bins, 10)
    long_target = fold.base_long * lookup[safe_bins]
    target = long_target + fold.short_target
    previous = np.vstack([np.zeros((1, target.shape[1])), target[:-1]])
    gross_return = (previous * fold.returns).sum(axis=1)
    turnover = np.abs(target - previous).sum(axis=1)
    net_return = gross_return - transaction_cost * turnover

    series = pd.Series(net_return, index=fold.dates).replace([np.inf, -np.inf], np.nan)
    series = series.dropna()
    if len(series) <= 1 or float(series.std()) < 1e-12:
        return {
            "valid": False,
            "sharpe": 0.0,
            "annualized_return": 0.0,
            "cost_adjusted_return": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
            "average_daily_turnover": float(np.mean(turnover)),
            "annualized_turnover": float(np.mean(turnover) * 252),
            "total_transaction_cost": float(transaction_cost * turnover.sum()),
            "n_observations": int(len(series)),
        }

    sharpe = series.mean() / series.std() * np.sqrt(252)
    annualized_return = (1 + series).prod() ** (252 / len(series)) - 1
    cumulative = (1 + series).cumprod()
    max_drawdown = (cumulative / cumulative.cummax() - 1).min()
    gross_exposure = np.abs(target).sum(axis=1)
    return {
        "valid": True,
        "sharpe": float(sharpe),
        "annualized_return": float(annualized_return),
        "cost_adjusted_return": float(annualized_return),
        "max_drawdown": float(max_drawdown),
        "total_return": float(cumulative.iloc[-1] - 1),
        "average_daily_turnover": float(np.mean(turnover)),
        "annualized_turnover": float(np.mean(turnover) * 252),
        "total_transaction_cost": float(transaction_cost * turnover.sum()),
        "average_gross_exposure": float(np.mean(gross_exposure)),
        "max_gross_exposure": float(np.max(gross_exposure)),
        "n_observations": int(len(series)),
    }
