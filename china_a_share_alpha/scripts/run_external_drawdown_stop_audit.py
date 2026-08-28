"""Stress-test all frozen external factors with a permanent drawdown stop.

When a factor's cumulative daily long-short net asset value first reaches the
configured peak-to-trough drawdown limit, its exposure is set to zero for every
remaining audit day.  This is a descriptive risk-control simulation, not a
claim that an overlapping forward-return backtest is an executable live book.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_external_unused_csi500_validation import (
    _active_rows,
    _labels,
    _load_panel,
)


def _daily_long_short(factor: pd.Series, labels: pd.Series) -> pd.Series:
    frame = pd.DataFrame({"factor": factor, "forward_return": labels}).dropna()
    frame["quantile"] = frame.groupby(level="date")["factor"].transform(
        lambda values: pd.qcut(values, 5, labels=False, duplicates="drop")
    )
    long = frame.loc[frame["quantile"] == 4].groupby(level="date")["forward_return"].mean()
    short = frame.loc[frame["quantile"] == 0].groupby(level="date")["forward_return"].mean()
    return (long - short).dropna().sort_index()


def _metrics(returns: pd.Series) -> dict[str, float]:
    if len(returns) < 2 or float(returns.std()) < 1e-12:
        return {"sharpe": 0.0, "annualized_return": 0.0, "max_drawdown": 0.0}
    nav = (1.0 + returns).cumprod()
    return {
        "sharpe": float(returns.mean() / returns.std() * np.sqrt(252)),
        "annualized_return": float(nav.iloc[-1] ** (252 / len(returns)) - 1.0),
        "max_drawdown": float((nav / nav.cummax() - 1.0).min()),
    }


def _permanent_stop(returns: pd.Series, limit: float) -> tuple[pd.Series, pd.Timestamp | pd.NaT]:
    nav = (1.0 + returns).cumprod()
    drawdown = nav / nav.cummax() - 1.0
    breached = drawdown <= limit
    if not breached.any():
        return returns.copy(), pd.NaT
    stop_date = breached[breached].index[0]
    stopped = returns.copy()
    stopped.loc[stopped.index > stop_date] = 0.0
    return stopped, stop_date


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--drawdown-limit", type=float, default=-0.20)
    parser.add_argument("--data-start", default="20240101")
    parser.add_argument("--evaluation-start", default="20250530")
    parser.add_argument("--evaluation-end", default="20260716")
    args = parser.parse_args()
    if not -1.0 < args.drawdown_limit < 0.0:
        raise ValueError("--drawdown-limit must be between -1 and 0.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = pd.read_csv(args.results)
    factors = results.loc[results["period"] == "full"].copy()
    membership = pd.read_csv(args.membership)
    membership["trade_date"] = pd.to_datetime(membership["trade_date"])
    panel = _load_panel(
        None,
        sorted(membership["con_code"].unique()),
        args.data_start,
        args.evaluation_end,
        args.cache_dir,
    )
    panel = _active_rows(panel, membership)
    start, end = pd.Timestamp(args.evaluation_start), pd.Timestamp(args.evaluation_end)
    rows: list[dict[str, object]] = []
    for position, (_, row) in enumerate(factors.iterrows(), start=1):
        try:
            signal = parse_expression(row["expression"]).eval(panel)
            labels = _labels(panel, int(row["horizon"]))
            dates = signal.index.get_level_values("date")
            mask = (dates >= start) & (dates <= end)
            daily = _daily_long_short(signal.loc[mask], labels.loc[mask])
            stopped, stop_date = _permanent_stop(daily, args.drawdown_limit)
            baseline = _metrics(daily)
            stopped_metrics = _metrics(stopped)
            rows.append(
                {
                    "factor_id": row["factor_id"],
                    "horizon": row["horizon"],
                    "iteration": row["iteration"],
                    "expression": row["expression"],
                    "baseline_sharpe": baseline["sharpe"],
                    "baseline_annualized_return": baseline["annualized_return"],
                    "baseline_max_drawdown": baseline["max_drawdown"],
                    "stopped_sharpe": stopped_metrics["sharpe"],
                    "stopped_annualized_return": stopped_metrics["annualized_return"],
                    "stopped_max_drawdown": stopped_metrics["max_drawdown"],
                    "stop_triggered": pd.notna(stop_date),
                    "stop_date": stop_date,
                    "active_days": int((stopped != 0.0).sum()),
                    "total_days": len(stopped),
                    "active_fraction": float((stopped != 0.0).mean()) if len(stopped) else 0.0,
                    "observations": row["observations"],
                }
            )
        except Exception as exc:
            rows.append(
                {"factor_id": row["factor_id"], "expression": row["expression"], "error": str(exc)}
            )
        if position % 25 == 0 or position == len(factors):
            print(f"DIAGNOSED {position}/{len(factors)}")
    audit = pd.DataFrame(rows)
    audit.to_csv(args.output_dir / "permanent_drawdown_stop_audit.csv", index=False)
    summary = {
        "factor_count": int(len(audit)),
        "drawdown_limit": args.drawdown_limit,
        "triggered_count": int(audit["stop_triggered"].fillna(False).sum()),
        "error_count": int(audit.get("error", pd.Series(dtype=object)).notna().sum()),
        "median_baseline_sharpe": float(audit["baseline_sharpe"].median()),
        "median_stopped_sharpe": float(audit["stopped_sharpe"].median()),
        "median_baseline_max_drawdown": float(audit["baseline_max_drawdown"].median()),
        "median_stopped_max_drawdown": float(audit["stopped_max_drawdown"].median()),
    }
    pd.Series(summary).to_json(args.output_dir / "permanent_drawdown_stop_summary.json", indent=2)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
