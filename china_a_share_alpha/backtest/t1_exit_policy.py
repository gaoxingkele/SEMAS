"""T+1 long-only execution with board-aware stop and trailing-profit rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExitThresholds:
    stop_loss: float
    profit_activation: dict[int, float]
    trailing_drawdown: float
    price_limit: float


DEFAULT_THRESHOLDS = {
    "main": ExitThresholds(
        stop_loss=0.20,
        profit_activation={5: 0.15, 10: 0.25, 20: 0.35},
        trailing_drawdown=0.08,
        price_limit=0.10,
    ),
    "innovation": ExitThresholds(
        stop_loss=0.30,
        profit_activation={5: 0.25, 10: 0.40, 20: 0.55},
        trailing_drawdown=0.12,
        price_limit=0.20,
    ),
    "bse": ExitThresholds(
        stop_loss=0.40,
        profit_activation={5: 0.35, 10: 0.55, 20: 0.75},
        trailing_drawdown=0.16,
        price_limit=0.30,
    ),
    "etf": ExitThresholds(
        stop_loss=0.20,
        profit_activation={5: 0.15, 10: 0.25, 20: 0.35},
        trailing_drawdown=0.08,
        price_limit=0.10,
    ),
}


def market_group(market: str) -> str:
    """Normalize Tushare market labels into execution-policy groups."""
    value = str(market).strip().lower()
    if any(token in value for token in ("科创", "创业", "star", "chinext")):
        return "innovation"
    if any(token in value for token in ("北交", "bse")):
        return "bse"
    if "etf" in value or "基金" in value:
        return "etf"
    return "main"


def _performance(daily_returns: pd.Series) -> dict[str, float]:
    clean = daily_returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) <= 1 or float(clean.std()) < 1e-12:
        return {
            "valid": False,
            "sharpe": 0.0,
            "annualized_return": 0.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "n_observations": int(len(clean)),
        }
    nav = (1.0 + clean).cumprod()
    return {
        "valid": True,
        "sharpe": float(clean.mean() / clean.std() * np.sqrt(252)),
        "annualized_return": float(nav.iloc[-1] ** (252 / len(clean)) - 1.0),
        "total_return": float(nav.iloc[-1] - 1.0),
        "max_drawdown": float((nav / nav.cummax() - 1.0).min()),
        "n_observations": int(len(clean)),
    }


def _is_st_name(name: str) -> bool:
    upper = str(name).upper().replace(" ", "")
    return "ST" in upper or "退" in upper


def run_t1_exit_backtest(
    signal: pd.Series,
    panel: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    horizon: int,
    selection_fraction: float = 0.20,
    transaction_cost: float = 0.001,
    slippage: float = 0.0005,
    thresholds: dict[str, ExitThresholds] | None = None,
    universe_groups: set[str] | None = None,
    limit_tolerance: float = 0.002,
) -> tuple[dict[str, Any], pd.DataFrame, pd.Series]:
    """Backtest sequential factor cohorts with conservative daily-bar fills.

    A signal at D is bought at D+1 open.  The purchase day is not counted, so a
    five-day policy expires at D+6 close.  Stop/trailing signals observed at a
    close execute at the next sellable open.  A locked limit-down day queues the
    exit instead of inventing a fill.
    """
    if horizon not in {5, 10, 20}:
        raise ValueError("horizon must be one of 5, 10, or 20")
    required = {"open", "high", "low", "close", "pre_close", "volume"}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"panel is missing required columns: {sorted(missing)}")
    if not 0 < selection_fraction <= 1:
        raise ValueError("selection_fraction must be in (0, 1]")

    policies = thresholds or DEFAULT_THRESHOLDS
    meta = metadata.copy()
    if "symbol" in meta.columns:
        meta = meta.set_index("symbol")
    meta.index = meta.index.astype(str)
    meta["market_group"] = meta.get("market", "main").map(market_group)
    meta["excluded"] = meta.get("name", "").map(_is_st_name)
    if universe_groups:
        meta = meta[meta["market_group"].isin(universe_groups)]
    meta = meta[~meta["excluded"]]

    symbols = pd.Index(
        sorted(set(panel.index.get_level_values("symbol").astype(str)) & set(meta.index))
    )
    if symbols.empty:
        empty = pd.Series(dtype=float, name="return")
        return (
            {**_performance(empty), "reason": "no eligible symbols", "n_trades": 0},
            pd.DataFrame(),
            empty,
        )

    dates = panel.index.get_level_values("date").unique().sort_values()
    fields: dict[str, pd.DataFrame] = {}
    for column in required:
        fields[column] = panel[column].unstack("symbol").reindex(index=dates, columns=symbols)
    signals = signal.unstack("symbol").reindex(index=dates, columns=symbols)

    group_by_symbol = meta.reindex(symbols)["market_group"].fillna("main")
    policy_by_symbol = {symbol: policies[group_by_symbol[symbol]] for symbol in symbols}
    symbol_position = {symbol: offset for offset, symbol in enumerate(symbols)}

    cash = 1.0
    positions: dict[str, dict[str, Any]] = {}
    pending_entry: list[str] = []
    pending_signal_date: Any = None
    pending_factor_scores: dict[str, float] = {}
    trades: list[dict[str, Any]] = []
    daily_returns: list[float] = []
    blocked_entries = 0
    blocked_exits = 0
    previous_equity = 1.0

    def price_limit(symbol: str) -> float:
        return policy_by_symbol[symbol].price_limit

    def lower_bound(symbol: str, day: int) -> float:
        pre_close = float(fields["pre_close"].iat[day, symbol_position[symbol]])
        return pre_close * (1.0 - price_limit(symbol))

    def upper_bound(symbol: str, day: int) -> float:
        pre_close = float(fields["pre_close"].iat[day, symbol_position[symbol]])
        return pre_close * (1.0 + price_limit(symbol))

    def finite_quote(symbol: str, day: int, column: str) -> bool:
        value = fields[column].iat[day, symbol_position[symbol]]
        volume = fields["volume"].iat[day, symbol_position[symbol]]
        return bool(np.isfinite(value) and np.isfinite(volume) and volume > 0)

    def can_buy_open(symbol: str, day: int) -> bool:
        if not finite_quote(symbol, day, "open"):
            return False
        open_price = float(fields["open"].iat[day, symbol_position[symbol]])
        return open_price < upper_bound(symbol, day) * (1.0 - limit_tolerance)

    def can_sell(symbol: str, day: int, column: str) -> bool:
        if not finite_quote(symbol, day, column):
            return False
        price = float(fields[column].iat[day, symbol_position[symbol]])
        return price > lower_bound(symbol, day) * (1.0 + limit_tolerance)

    for day, date in enumerate(dates):
        # Pending close-generated exits execute at the next sellable open.
        for symbol in list(positions):
            position = positions[symbol]
            if not position.get("pending_reason"):
                continue
            if not can_sell(symbol, day, "open"):
                blocked_exits += 1
                position["exit_delay"] += 1
                continue
            open_price = float(fields["open"].iat[day, symbol_position[symbol]])
            fill = open_price * (1.0 - slippage)
            proceeds = position["shares"] * fill * (1.0 - transaction_cost)
            cash += proceeds
            trades.append(
                {
                    "symbol": symbol,
                    "market_group": group_by_symbol[symbol],
                    "entry_date": position["entry_date"],
                    "entry_signal_date": position["entry_signal_date"],
                    "factor_score": position["factor_score"],
                    "exit_date": date,
                    "entry_price": position["entry_price"],
                    "exit_price": fill,
                    "exit_reason": position["pending_reason"],
                    "post_buy_days": int(day - position["buy_index"]),
                    "exit_delay": int(position["exit_delay"]),
                    "profit_activated": bool(position["activated"]),
                    "peak_return": float(
                        position["peak"] / position["entry_price"] - 1.0
                    ),
                    "max_adverse_return": float(
                        position["trough"] / position["entry_price"] - 1.0
                    ),
                    "trade_return": float(
                        fill
                        * (1.0 - transaction_cost)
                        / (position["entry_price"] * (1.0 + transaction_cost))
                        - 1.0
                    ),
                }
            )
            del positions[symbol]

        # A D signal is entered at D+1 open.  No new cohort overlaps an old one.
        if pending_entry and not positions:
            buyable = [symbol for symbol in pending_entry if can_buy_open(symbol, day)]
            blocked_entries += len(pending_entry) - len(buyable)
            if buyable:
                allocation = cash / len(buyable)
                cash = 0.0
                for symbol in buyable:
                    open_price = float(fields["open"].iat[day, symbol_position[symbol]])
                    fill = open_price * (1.0 + slippage)
                    shares = allocation / (fill * (1.0 + transaction_cost))
                    residual = allocation - shares * fill * (1.0 + transaction_cost)
                    cash += residual
                    positions[symbol] = {
                        "shares": shares,
                        "entry_price": fill,
                        "entry_date": date,
                        "entry_signal_date": pending_signal_date,
                        "factor_score": pending_factor_scores.get(symbol, np.nan),
                        "buy_index": day,
                        "peak": fill,
                        "trough": fill,
                        "activated": False,
                        "pending_reason": None,
                        "exit_delay": 0,
                    }
            pending_entry = []
            pending_signal_date = None
            pending_factor_scores = {}

        # Update peak and create close-confirmed exit signals after T+1 unlocks.
        for symbol in list(positions):
            position = positions[symbol]
            offset = symbol_position[symbol]
            high = fields["high"].iat[day, offset]
            low = fields["low"].iat[day, offset]
            close = fields["close"].iat[day, offset]
            if np.isfinite(high):
                position["peak"] = max(position["peak"], float(high))
            if np.isfinite(low):
                position["trough"] = min(position["trough"], float(low))
            if day <= position["buy_index"] or not np.isfinite(close):
                continue
            policy = policy_by_symbol[symbol]
            peak_return = position["peak"] / position["entry_price"] - 1.0
            if peak_return >= policy.profit_activation[horizon]:
                position["activated"] = True
            cumulative_return = float(close) / position["entry_price"] - 1.0
            at_limit_down = float(close) <= lower_bound(symbol, day) * (1.0 + limit_tolerance)
            trailing = (
                position["activated"]
                and float(close) / position["peak"] - 1.0 <= -policy.trailing_drawdown
            )
            if cumulative_return <= -policy.stop_loss:
                position["pending_reason"] = "cumulative_stop"
            elif at_limit_down:
                position["pending_reason"] = "limit_down_stop"
            elif trailing:
                position["pending_reason"] = "trailing_profit"

        # Expiry is known in advance and executes at D+6/D+11/D+21 close.
        for symbol in list(positions):
            position = positions[symbol]
            if position.get("pending_reason") or day - position["buy_index"] < horizon:
                continue
            if not can_sell(symbol, day, "close"):
                position["pending_reason"] = "expiry"
                blocked_exits += 1
                continue
            close_price = float(fields["close"].iat[day, symbol_position[symbol]])
            fill = close_price * (1.0 - slippage)
            cash += position["shares"] * fill * (1.0 - transaction_cost)
            trades.append(
                {
                    "symbol": symbol,
                    "market_group": group_by_symbol[symbol],
                    "entry_date": position["entry_date"],
                    "entry_signal_date": position["entry_signal_date"],
                    "factor_score": position["factor_score"],
                    "exit_date": date,
                    "entry_price": position["entry_price"],
                    "exit_price": fill,
                    "exit_reason": "expiry",
                    "post_buy_days": int(day - position["buy_index"]),
                    "exit_delay": 0,
                    "profit_activated": bool(position["activated"]),
                    "peak_return": float(
                        position["peak"] / position["entry_price"] - 1.0
                    ),
                    "max_adverse_return": float(
                        position["trough"] / position["entry_price"] - 1.0
                    ),
                    "trade_return": float(
                        fill
                        * (1.0 - transaction_cost)
                        / (position["entry_price"] * (1.0 + transaction_cost))
                        - 1.0
                    ),
                }
            )
            del positions[symbol]

        close_equity = cash
        for symbol, position in positions.items():
            close = fields["close"].iat[day, symbol_position[symbol]]
            if np.isfinite(close):
                close_equity += position["shares"] * float(close)
        daily_returns.append(close_equity / previous_equity - 1.0 if previous_equity else 0.0)
        previous_equity = close_equity

        if not positions and not pending_entry and day + 1 < len(dates):
            row = signals.iloc[day].dropna()
            if len(row) >= 5:
                count = max(1, int(len(row) * selection_fraction))
                pending_entry = row.nlargest(count).index.astype(str).tolist()
                percentile = row.rank(method="average", pct=True).mul(100.0)
                pending_signal_date = date
                pending_factor_scores = {
                    symbol: float(percentile[symbol]) for symbol in pending_entry
                }

    returns = pd.Series(daily_returns, index=dates, name="return")
    trade_frame = pd.DataFrame(trades)
    metrics: dict[str, Any] = _performance(returns)
    metrics.update(
        {
            "horizon": horizon,
            "n_symbols": int(len(symbols)),
            "n_trades": int(len(trade_frame)),
            "blocked_entries": int(blocked_entries),
            "blocked_exits": int(blocked_exits),
            "open_positions_at_end": int(len(positions)),
            "average_trade_return": (
                float(trade_frame["trade_return"].mean()) if not trade_frame.empty else 0.0
            ),
            "win_rate": (
                float((trade_frame["trade_return"] > 0).mean()) if not trade_frame.empty else 0.0
            ),
        }
    )
    for reason, count in (
        trade_frame.get("exit_reason", pd.Series(dtype=str)).value_counts().items()
    ):
        metrics[f"exit_{reason}"] = int(count)
    return metrics, trade_frame, returns
