"""Daily all-factor ranking with drawdown stop, cooldown, and re-entry.

Each factor is a separate sleeve.  It enters only when its lagged rolling
Sharpe ranks in the top fraction of all frozen factors.  A sleeve exits after
a -20% episode drawdown, waits a configurable number of trading days, and may
re-enter only if it again passes that daily cross-factor ranking.  Factor
returns are delayed by their holding horizon before ranking, preventing the
forward label from becoming a look-ahead signal.
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


def _simulate(
    returns: pd.Series, eligible: pd.Series, drawdown_limit: float, cooldown: int
) -> tuple[pd.Series, int, int]:
    """Run one sleeve with episode-local drawdown and rank-gated re-entry."""
    output = pd.Series(0.0, index=returns.index)
    active = False
    wait = 0
    episode_nav = 1.0
    episode_peak = 1.0
    entries = 0
    stops = 0
    for date, raw_return in returns.items():
        if not active:
            if wait:
                wait -= 1
                continue
            if not bool(eligible.loc[date]):
                continue
            active = True
            episode_nav = 1.0
            episode_peak = 1.0
            entries += 1
        output.loc[date] = raw_return
        episode_nav *= 1.0 + raw_return
        episode_peak = max(episode_peak, episode_nav)
        if episode_nav / episode_peak - 1.0 <= drawdown_limit:
            active = False
            wait = cooldown
            stops += 1
    return output, entries, stops


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--drawdown-limit", type=float, default=-0.20)
    parser.add_argument("--lookback", type=int, default=60)
    parser.add_argument("--minimum-history", type=int, default=40)
    parser.add_argument(
        "--ranking-method",
        choices=["rolling_sharpe", "rolling_rank_mean"],
        default="rolling_sharpe",
        help="Daily all-factor score: delayed rolling Sharpe or mean delayed daily rank.",
    )
    parser.add_argument("--top-fraction", type=float, default=0.20)
    parser.add_argument(
        "--top-n",
        type=int,
        default=0,
        help="Fixed number of daily top-ranked factors eligible to enter; overrides --top-fraction.",
    )
    parser.add_argument("--cooldowns", nargs="+", type=int, default=[5, 10, 20])
    parser.add_argument("--data-start", default="20240101")
    parser.add_argument("--evaluation-start", default="20250530")
    parser.add_argument("--evaluation-end", default="20260716")
    args = parser.parse_args()
    if not -1.0 < args.drawdown_limit < 0.0:
        raise ValueError("--drawdown-limit must be between -1 and 0.")
    if not 0.0 < args.top_fraction <= 1.0:
        raise ValueError("--top-fraction must be in (0, 1].")
    if args.top_n < 0:
        raise ValueError("--top-n must be non-negative.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = pd.read_csv(args.results)
    factors = results.loc[results["period"] == "full"].copy().reset_index(drop=True)
    membership = pd.read_csv(args.membership)
    membership["trade_date"] = pd.to_datetime(membership["trade_date"])
    panel = _active_rows(
        _load_panel(
            None,
            sorted(membership["con_code"].unique()),
            args.data_start,
            args.evaluation_end,
            args.cache_dir,
        ),
        membership,
    )
    raw_returns: dict[str, pd.Series] = {}
    horizons: dict[str, int] = {}
    for position, row in factors.iterrows():
        factor_id = str(row["factor_id"])
        signal = parse_expression(row["expression"]).eval(panel)
        labels = _labels(panel, int(row["horizon"]))
        raw_returns[factor_id] = _daily_long_short(signal, labels)
        horizons[factor_id] = int(row["horizon"])
        if (position + 1) % 25 == 0 or position + 1 == len(factors):
            print(f"RETURNS {position + 1}/{len(factors)}")
    calendar = pd.DatetimeIndex(
        sorted(set().union(*(series.index for series in raw_returns.values())))
    )
    return_frame = pd.DataFrame(
        {key: series.reindex(calendar) for key, series in raw_returns.items()}
    )
    completed_returns: dict[str, pd.Series] = {}
    for factor_id, series in return_frame.items():
        completed_returns[factor_id] = series.shift(horizons[factor_id] + 1)
    completed_frame = pd.DataFrame(completed_returns)
    if args.ranking_method == "rolling_sharpe":
        score_frame = pd.DataFrame(
            {
                factor_id: (
                    completed.rolling(args.lookback, min_periods=args.minimum_history).mean()
                    / completed.rolling(args.lookback, min_periods=args.minimum_history).std()
                    * np.sqrt(252)
                )
                for factor_id, completed in completed_returns.items()
            }
        )
        ordinal_rank = score_frame.rank(axis=1, ascending=False, method="first")
    else:
        daily_percentile_rank = completed_frame.rank(
            axis=1, ascending=False, pct=True, method="average"
        )
        score_frame = daily_percentile_rank.rolling(
            args.lookback, min_periods=args.minimum_history
        ).mean()
        ordinal_rank = score_frame.rank(axis=1, ascending=True, method="first")
    if args.top_n:
        eligibility = ordinal_rank <= args.top_n
        selection_label = f"top_{args.top_n}_{args.ranking_method}_{args.lookback}d"
    else:
        percentile_rank = ordinal_rank.rank(axis=1, ascending=True, pct=True, method="average")
        eligibility = percentile_rank <= args.top_fraction
        selection_label = (
            f"top_fraction_{args.top_fraction:g}_{args.ranking_method}_{args.lookback}d"
        )
    evaluation_dates = calendar[
        (calendar >= pd.Timestamp(args.evaluation_start))
        & (calendar <= pd.Timestamp(args.evaluation_end))
    ]
    if args.top_n:
        daily_members = pd.DataFrame(
            {
                "ranking_score": score_frame.reindex(evaluation_dates).stack(),
                "daily_rank": ordinal_rank.reindex(evaluation_dates).stack(),
            }
        ).reset_index(names=["date", "factor_id"])
        daily_members = daily_members.loc[daily_members["daily_rank"] <= args.top_n].copy()
        daily_members.insert(1, "ranking_method", args.ranking_method)
        metadata = factors[["factor_id", "horizon", "iteration", "expression"]]
        daily_members = daily_members.merge(metadata, on="factor_id", how="left")
        daily_members = daily_members.sort_values(["date", "daily_rank"])
        daily_members.to_csv(
            args.output_dir / f"daily_{selection_label}_membership.csv", index=False
        )
    rows: list[dict[str, object]] = []
    for cooldown in args.cooldowns:
        for _, row in factors.iterrows():
            factor_id = str(row["factor_id"])
            daily = return_frame[factor_id].reindex(evaluation_dates).fillna(0.0)
            active, entries, stops = _simulate(
                daily,
                eligibility[factor_id].reindex(evaluation_dates).fillna(False),
                args.drawdown_limit,
                cooldown,
            )
            metrics = _metrics(active)
            rows.append(
                {
                    "cooldown_days": cooldown,
                    "factor_id": factor_id,
                    "horizon": row["horizon"],
                    "iteration": row["iteration"],
                    "expression": row["expression"],
                    "selection_rule": selection_label,
                    "ranked_reentry_sharpe": metrics["sharpe"],
                    "ranked_reentry_annualized_return": metrics["annualized_return"],
                    "ranked_reentry_max_drawdown": metrics["max_drawdown"],
                    "entries": entries,
                    "stops": stops,
                    "active_fraction": float((active != 0.0).mean()),
                    "eligible_fraction": float(
                        eligibility[factor_id].reindex(evaluation_dates).fillna(False).mean()
                    ),
                }
            )
    audit = pd.DataFrame(rows)
    audit.to_csv(args.output_dir / "ranked_reentry_drawdown_audit.csv", index=False)
    summary = (
        audit.groupby("cooldown_days")
        .agg(
            median_sharpe=("ranked_reentry_sharpe", "median"),
            median_max_drawdown=("ranked_reentry_max_drawdown", "median"),
            mean_entries=("entries", "mean"),
            mean_stops=("stops", "mean"),
            mean_active_fraction=("active_fraction", "mean"),
        )
        .reset_index()
    )
    summary.insert(1, "selection_rule", selection_label)
    summary.to_csv(args.output_dir / "ranked_reentry_drawdown_summary.csv", index=False)
    print(summary.to_dict(orient="records"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
