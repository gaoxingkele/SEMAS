"""Multi-round TOP100 factor and A-share long-only portfolio research.

Round 1 scores every supplied factor on a stock-disjoint 2025 panel.  Round 2
freezes the selected expressions and evaluates them in 2026.  Round 3 compares
long-only A-share-aware portfolio rules using next-day execution, liquidity and
limit-up purchase filters, inverse-volatility weights, per-name caps, and an
optional market-volatility exposure target.  This is research, not promotion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.evaluator.metrics import ic_score, icir_score, rank_ic_score
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_external_unused_csi500_validation import (
    _active_rows,
    _labels,
    _load_panel,
)


def _slice(series: pd.Series, start: str, end: str) -> pd.Series:
    dates = series.index.get_level_values("date")
    return series.loc[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))]


def _factor_metrics(signal: pd.Series, labels: pd.Series) -> dict[str, float]:
    aligned = pd.DataFrame({"signal": signal, "label": labels}).dropna()
    if aligned.empty:
        return {
            key: np.nan
            for key in (
                "ic",
                "rank_ic",
                "icir",
                "sharpe",
                "cost_adjusted_return",
                "max_drawdown",
                "turnover",
                "observations",
            )
        }
    bt = run_long_short_backtest(aligned["signal"], aligned["label"], transaction_cost=0.001)
    return {
        "ic": ic_score(aligned["signal"], aligned["label"]),
        "rank_ic": rank_ic_score(aligned["signal"], aligned["label"]),
        "icir": icir_score(aligned["signal"], aligned["label"]),
        "sharpe": float(bt["sharpe"]),
        "cost_adjusted_return": float(bt["cost_adjusted_return"]),
        "max_drawdown": float(bt["max_drawdown"]),
        "turnover": float(bt["turnover"]),
        "observations": float(len(aligned)),
    }


def _daily_long_short(signal: pd.Series, labels: pd.Series) -> pd.Series:
    frame = pd.DataFrame({"signal": signal, "label": labels}).dropna()
    frame["quantile"] = frame.groupby(level="date")["signal"].transform(
        lambda values: pd.qcut(values, 5, labels=False, duplicates="drop")
    )
    long = frame.loc[frame["quantile"] == 4].groupby(level="date")["label"].mean()
    short = frame.loc[frame["quantile"] == 0].groupby(level="date")["label"].mean()
    return (long - short).dropna().sort_index()


def _rank_score(frame: pd.DataFrame) -> pd.Series:
    """2025-only utility score; all components are cross-sectional ranks."""

    def higher(column: str) -> pd.Series:
        return frame[column].rank(pct=True, na_option="bottom")

    def lower(column: str) -> pd.Series:
        return (-frame[column]).rank(pct=True, na_option="bottom")

    return (
        0.25 * higher("sharpe_2025")
        + 0.18 * higher("ic_2025")
        + 0.14 * higher("rank_ic_2025")
        + 0.14 * higher("icir_2025")
        + 0.12 * higher("cost_adjusted_return_2025")
        + 0.08 * higher("max_drawdown_2025")
        + 0.05 * lower("turnover_2025")
        + 0.04 * higher("occurrences")
    )


def _cap_weights(raw: pd.Series, cap: float) -> pd.Series:
    weights = raw / raw.sum() if raw.sum() else raw
    for _ in range(20):
        over = weights > cap + 1e-12
        if not over.any():
            break
        excess = float((weights[over] - cap).sum())
        weights.loc[over] = cap
        under = ~over
        if not under.any() or weights.loc[under].sum() <= 0:
            break
        weights.loc[under] += excess * weights.loc[under] / weights.loc[under].sum()
    return weights


def _targets(
    composite: pd.Series,
    panel: pd.DataFrame,
    mode: str,
    selection_fraction: float = 0.30,
) -> pd.DataFrame:
    dates = composite.index.get_level_values("date").unique().sort_values()
    symbols = composite.index.get_level_values("symbol").unique().sort_values()
    score = composite.unstack("symbol").reindex(index=dates, columns=symbols)
    amount = panel["amount"].unstack("symbol").reindex(index=dates, columns=symbols)
    returns = panel["return"].unstack("symbol").reindex(index=dates, columns=symbols)
    vol = returns.rolling(20, min_periods=10).std()
    output = pd.DataFrame(0.0, index=dates, columns=symbols)
    for date in dates:
        row = score.loc[date].dropna().sort_values(ascending=False)
        count = max(1, int(len(row) * selection_fraction))
        chosen = row.head(count).index
        if mode != "equal":
            liquid = amount.loc[date, chosen].rank(pct=True) > 0.20
            # A conservative A-share constraint: do not initiate a buy after
            # an observed near-limit-up close.
            tradable = returns.loc[date, chosen].fillna(0.0) < 0.095
            chosen = chosen[liquid & tradable]
        if not len(chosen):
            continue
        if mode == "equal":
            raw = pd.Series(1.0, index=chosen)
            output.loc[date, chosen] = raw / raw.sum()
        else:
            raw = 1.0 / vol.loc[date, chosen].replace(0, np.nan)
            raw = raw.replace([np.inf, -np.inf], np.nan).dropna()
            if raw.empty:
                raw = pd.Series(1.0, index=chosen)
            output.loc[date, raw.index] = _cap_weights(raw, cap=0.15)
    if mode == "invvol_voltarget":
        market_vol = returns.mean(axis=1).rolling(20, min_periods=10).std() * np.sqrt(252)
        exposure = (0.18 / market_vol.replace(0, np.nan)).clip(lower=0.35, upper=1.0).fillna(0.35)
        output = output.mul(exposure, axis=0)
    return output


def _portfolio_metrics(targets: pd.DataFrame, panel: pd.DataFrame) -> dict[str, float]:
    returns = (
        panel["return"]
        .unstack("symbol")
        .reindex(index=targets.index, columns=targets.columns)
        .fillna(0.0)
    )
    executed = targets.shift(1).fillna(0.0)  # signal at close t applies on t+1
    turnover = (targets - targets.shift(1).fillna(0.0)).abs().sum(axis=1)
    daily = (executed * returns).sum(axis=1) - 0.001 * turnover
    daily = daily.iloc[1:]
    if len(daily) < 2 or daily.std() < 1e-12:
        return {
            "sharpe": 0.0,
            "annualized_return": 0.0,
            "max_drawdown": 0.0,
            "turnover": 0.0,
            "active_exposure": 0.0,
        }
    nav = (1 + daily).cumprod()
    return {
        "sharpe": float(daily.mean() / daily.std() * np.sqrt(252)),
        "annualized_return": float(nav.iloc[-1] ** (252 / len(daily)) - 1.0),
        "max_drawdown": float((nav / nav.cummax() - 1.0).min()),
        "turnover": float(turnover.mean()),
        "active_exposure": float(targets.sum(axis=1).mean()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top100", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data-start", default="20240101")
    parser.add_argument("--end-date", default="20260716")
    parser.add_argument("--top-n", type=int, default=12)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidates = pd.read_csv(args.top100)
    membership = pd.read_csv(args.membership)
    membership["trade_date"] = pd.to_datetime(membership["trade_date"])
    panel = _active_rows(
        _load_panel(
            None,
            sorted(membership["con_code"].unique()),
            args.data_start,
            args.end_date,
            args.cache_dir,
        ),
        membership,
    )
    panel = panel.loc[~panel.index.duplicated(keep="last")].sort_index()
    records: list[dict[str, object]] = []
    signals: dict[str, pd.Series] = {}
    for position, (_, candidate) in enumerate(candidates.iterrows(), start=1):
        expression = str(candidate["expression"])
        try:
            raw = parse_expression(expression).eval(panel)
            for horizon in (5, 10):
                labels = _labels(panel, horizon)
                train_signal = _slice(raw, "2025-05-30", "2025-12-31")
                train_labels = _slice(labels, "2025-05-30", "2025-12-31")
                test_signal = _slice(raw, "2026-01-01", "2026-07-16")
                test_labels = _slice(labels, "2026-01-01", "2026-07-16")
                train = _factor_metrics(train_signal, train_labels)
                test = _factor_metrics(test_signal, test_labels)
                key = f"{int(candidate['rank'])}_{horizon}d"
                signals[key] = raw
                records.append(
                    {
                        "candidate_rank": int(candidate["rank"]),
                        "variant_id": key,
                        "horizon": horizon,
                        "expression": expression,
                        "primary_source": candidate["primary_source"],
                        "occurrences": candidate["occurrences"],
                        **{f"{k}_2025": v for k, v in train.items()},
                        **{f"{k}_2026": v for k, v in test.items()},
                    }
                )
        except Exception as exc:
            records.append(
                {
                    "candidate_rank": int(candidate["rank"]),
                    "expression": expression,
                    "error": str(exc),
                }
            )
        if position % 20 == 0 or position == len(candidates):
            print(f"EVALUATED {position}/{len(candidates)}")
    audit = pd.DataFrame(records)
    valid = audit.dropna(subset=["sharpe_2025", "ic_2025", "observations_2025"]).copy()
    valid = valid[valid["observations_2025"] >= 1500].copy()
    valid["orientation"] = np.where(valid["ic_2025"] >= 0.0, 1.0, -1.0)
    for metric in ("sharpe", "ic", "rank_ic", "icir", "cost_adjusted_return"):
        valid[f"{metric}_2025"] *= valid["orientation"]
    valid["utility_score_2025"] = _rank_score(valid)
    valid = valid.sort_values("utility_score_2025", ascending=False)
    selected = valid.head(args.top_n).copy()
    audit.to_csv(args.output_dir / "top100_multidim_factor_audit.csv", index=False)
    selected.to_csv(args.output_dir / "selected_factors_2025_frozen.csv", index=False)

    selected_signals = []
    for _, row in selected.iterrows():
        signal = signals[row["variant_id"]] * float(row["orientation"])
        selected_signals.append(signal.groupby(level="date").rank(pct=True))
    composite = pd.concat(selected_signals, axis=1).mean(axis=1)
    composite = composite.groupby(level=["symbol", "date"]).mean().sort_index()
    portfolio_rows: list[dict[str, object]] = []
    for period, start, end in (
        ("2025_selection", "2025-05-30", "2025-12-31"),
        ("2026_frozen", "2026-01-01", "2026-07-16"),
    ):
        period_panel = panel.loc[pd.IndexSlice[:, pd.Timestamp(start) : pd.Timestamp(end)], :]
        period_signal = _slice(composite, start, end)
        for mode in ("equal", "invvol_liquid", "invvol_voltarget"):
            targets = _targets(period_signal, period_panel, mode)
            portfolio_rows.append(
                {"period": period, "mode": mode, **_portfolio_metrics(targets, period_panel)}
            )
    portfolio = pd.DataFrame(portfolio_rows)
    portfolio.to_csv(args.output_dir / "a_share_dynamic_position_rounds.csv", index=False)

    # Round 4: adaptive factor selection. The candidate pool is frozen to the
    # 50 best 2025 utility variants; 2026 daily selection uses only completed
    # factor returns and a return-correlation diversification filter.
    adaptive_pool = valid.head(50).copy()
    orientation = adaptive_pool.set_index("variant_id")["orientation"].to_dict()
    horizons = adaptive_pool.set_index("variant_id")["horizon"].astype(int).to_dict()
    adaptive_returns: dict[str, pd.Series] = {}
    adaptive_signal_ranks: dict[str, pd.Series] = {}
    for variant_id in adaptive_pool["variant_id"]:
        signal = signals[variant_id] * float(orientation[variant_id])
        horizon = int(horizons[variant_id])
        adaptive_returns[variant_id] = _daily_long_short(signal, _labels(panel, horizon))
        adaptive_signal_ranks[variant_id] = signal.groupby(level="date").rank(pct=True)
    return_frame = pd.DataFrame(adaptive_returns).sort_index()
    completed = pd.DataFrame(
        {
            variant: series.shift(int(horizons[variant]) + 1)
            for variant, series in return_frame.items()
        }
    )
    rolling_score = (
        completed.rolling(60, min_periods=40).mean() / completed.rolling(60, min_periods=40).std()
    )
    rank_signals = pd.DataFrame(adaptive_signal_ranks)
    signal_corr = rank_signals.loc[
        (rank_signals.index.get_level_values("date") >= pd.Timestamp("2025-05-30"))
        & (rank_signals.index.get_level_values("date") <= pd.Timestamp("2025-12-31"))
    ].corr(method="spearman")
    chosen_by_date: dict[pd.Timestamp, list[str]] = {}
    selection_rows: list[dict[str, object]] = []
    for date, scores in rolling_score.loc["2025-05-30":"2026-07-16"].iterrows():
        candidates_for_day = scores.dropna().sort_values(ascending=False)
        chosen: list[str] = []
        for variant_id, score in candidates_for_day.items():
            if all(abs(float(signal_corr.loc[variant_id, prior])) < 0.70 for prior in chosen):
                chosen.append(variant_id)
            if len(chosen) == args.top_n:
                break
        chosen_by_date[pd.Timestamp(date)] = chosen
        for rank, variant_id in enumerate(chosen, start=1):
            selection_rows.append(
                {
                    "date": date,
                    "rank": rank,
                    "variant_id": variant_id,
                    "rolling_completed_sharpe": scores[variant_id] * np.sqrt(252),
                }
            )
    adaptive_composite_parts: list[pd.Series] = []
    for date, chosen in chosen_by_date.items():
        if not chosen:
            continue
        day_signals = [
            adaptive_signal_ranks[variant].loc[pd.IndexSlice[:, date]] for variant in chosen
        ]
        day = pd.concat(day_signals, axis=1).mean(axis=1)
        day.index = pd.MultiIndex.from_product([day.index, [date]], names=["symbol", "date"])
        adaptive_composite_parts.append(day)
    adaptive_composite = (
        pd.concat(adaptive_composite_parts).sort_index()
        if adaptive_composite_parts
        else pd.Series(dtype=float)
    )
    pd.DataFrame(selection_rows).to_csv(
        args.output_dir / "adaptive_daily_factor_selection.csv", index=False
    )
    adaptive_rows: list[dict[str, object]] = []
    for period, start, end in (
        ("2025_adaptive_selection", "2025-05-30", "2025-12-31"),
        ("2026_adaptive_frozen", "2026-01-01", "2026-07-16"),
    ):
        period_panel = panel.loc[pd.IndexSlice[:, pd.Timestamp(start) : pd.Timestamp(end)], :]
        period_signal = _slice(adaptive_composite, start, end)
        for mode in ("equal", "invvol_liquid", "invvol_voltarget"):
            targets = _targets(period_signal, period_panel, mode)
            adaptive_rows.append(
                {"period": period, "mode": mode, **_portfolio_metrics(targets, period_panel)}
            )
    pd.DataFrame(adaptive_rows).to_csv(
        args.output_dir / "adaptive_a_share_position_rounds.csv", index=False
    )
    summary = {
        "input_candidates": len(candidates),
        "variants_evaluated": len(audit),
        "valid_variants": len(valid),
        "selected_factors": len(selected),
        "selection_period": "2025-05-30..2025-12-31",
        "frozen_validation_period": "2026-01-01..2026-07-16",
    }
    (args.output_dir / "research_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
