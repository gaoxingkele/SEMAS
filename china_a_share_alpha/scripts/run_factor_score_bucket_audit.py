"""Profile individual-stock outcomes by factor percentile score bucket."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.t1_exit_policy import run_t1_exit_backtest
from china_a_share_alpha.scripts.audit_recent_market_gate import (
    continuous_market_trend_gate,
)
from china_a_share_alpha.scripts.run_recent_all_factor_audit import (
    _period_mask,
    build_expression_catalog,
    catalog_digest,
    signal_quality,
)
from china_a_share_alpha.scripts.run_t1_full_library_audit import (
    _load_snapshot,
    discover_libraries,
)


_PANEL: pd.DataFrame | None = None
_METADATA: pd.DataFrame | None = None
_CONFIG: dict[str, Any] | None = None
_GATES: dict[str, pd.Series] | None = None


def expected_bucket_rows(
    expressions: int,
    periods: int,
    horizons: int,
    gates: int,
    universes: int,
    buckets: int,
) -> int:
    return expressions * periods * horizons * gates * universes * buckets


def _wilson_interval(successes: int, observations: int) -> tuple[float, float]:
    if observations <= 0:
        return np.nan, np.nan
    z = 1.959963984540054
    rate = successes / observations
    denominator = 1.0 + z * z / observations
    center = (rate + z * z / (2.0 * observations)) / denominator
    radius = (
        z
        * np.sqrt(
            rate * (1.0 - rate) / observations
            + z * z / (4.0 * observations * observations)
        )
        / denominator
    )
    return float(center - radius), float(center + radius)


def summarize_score_bucket(
    trades: pd.DataFrame,
    horizon: int,
    bucket: int,
) -> dict[str, Any]:
    if trades.empty:
        return {
            "status": "no_trades",
            "n_trades": 0,
            "n_symbols": 0,
            "n_cohorts": 0,
            "positive_trades": 0,
            "target_hits": 0,
            "effective_rate": np.nan,
            "target_hit_rate": np.nan,
            "effective_rate_ci_low": np.nan,
            "effective_rate_ci_high": np.nan,
            "average_return": np.nan,
            "median_return": np.nan,
            "return_std": np.nan,
            "cohort_sharpe": np.nan,
            "cohort_total_return": np.nan,
            "cohort_max_drawdown": np.nan,
            "profit_factor": np.nan,
            "average_win": np.nan,
            "average_loss": np.nan,
            "payoff_ratio": np.nan,
            "average_peak_return": np.nan,
            "average_adverse_return": np.nan,
            "average_post_buy_days": np.nan,
        }
    returns = trades["trade_return"].astype(float)
    positive = returns.gt(0)
    positive_count = int(positive.sum())
    target_hits = int(trades["profit_activated"].astype(bool).sum())
    ci_low, ci_high = _wilson_interval(positive_count, len(trades))
    cohort_returns = trades.groupby("entry_signal_date")["trade_return"].mean().sort_index()
    cohort_std = float(cohort_returns.std())
    cohort_sharpe = (
        float(cohort_returns.mean() / cohort_std * np.sqrt(252 / horizon))
        if len(cohort_returns) > 1 and cohort_std > 1e-12
        else np.nan
    )
    cohort_nav = (1.0 + cohort_returns).cumprod()
    gains = float(returns.loc[positive].sum())
    losses = float(-returns.loc[~positive].sum())
    average_win = float(returns.loc[positive].mean()) if positive.any() else np.nan
    average_loss = float(returns.loc[~positive].mean()) if (~positive).any() else np.nan
    result = {
        "status": "ok",
        "n_trades": int(len(trades)),
        "n_symbols": int(trades["symbol"].nunique()),
        "n_cohorts": int(len(cohort_returns)),
        "positive_trades": positive_count,
        "target_hits": target_hits,
        "effective_rate": float(positive.mean()),
        "target_hit_rate": float(target_hits / len(trades)),
        "effective_rate_ci_low": ci_low,
        "effective_rate_ci_high": ci_high,
        "average_return": float(returns.mean()),
        "median_return": float(returns.median()),
        "return_std": float(returns.std()),
        "cohort_sharpe": cohort_sharpe,
        "cohort_total_return": float(cohort_nav.iloc[-1] - 1.0),
        "cohort_max_drawdown": float((cohort_nav / cohort_nav.cummax() - 1.0).min()),
        "profit_factor": gains / losses if losses > 0 else np.nan,
        "average_win": average_win,
        "average_loss": average_loss,
        "payoff_ratio": average_win / abs(average_loss)
        if np.isfinite(average_win) and np.isfinite(average_loss) and average_loss != 0
        else np.nan,
        "average_peak_return": float(trades["peak_return"].mean()),
        "average_adverse_return": float(trades["max_adverse_return"].mean()),
        "average_post_buy_days": float(trades["post_buy_days"].mean()),
    }
    reason_rates = trades["exit_reason"].value_counts(normalize=True)
    for reason in ("expiry", "trailing_profit", "limit_down_stop", "cumulative_stop"):
        result[f"exit_{reason}_rate"] = float(reason_rates.get(reason, 0.0))
    return result


def _init_worker(snapshot_dir: str, config: dict[str, Any]) -> None:
    global _PANEL, _METADATA, _CONFIG, _GATES
    _PANEL, _METADATA, _ = _load_snapshot(Path(snapshot_dir))
    _CONFIG = config
    _GATES = {}
    for window in config.get("market_ma_windows", [20]):
        _GATES[f"ma{int(window)}"] = continuous_market_trend_gate(_PANEL, int(window))


def _apply_gate(signal: pd.Series, name: str) -> pd.Series:
    if name == "none":
        return signal
    assert _GATES is not None
    dates = pd.to_datetime(signal.index.get_level_values("date"))
    return signal.where(_GATES[name].reindex(dates).fillna(False).to_numpy())


def _empty_bucket_rows(
    task: dict[str, str],
    period: dict[str, str],
    horizon: int,
    gate: str,
    quality: dict[str, Any],
    bucket_count: int,
) -> list[dict[str, Any]]:
    rows = []
    for universe in ("all_stocks", "main_board", "innovation"):
        for bucket in range(bucket_count):
            rows.append(
                {
                    "expression_id": task["expression_id"],
                    "expression": task["expression"],
                    "period": period["name"],
                    "horizon": horizon,
                    "gate": gate,
                    "universe": universe,
                    "score_bucket": bucket,
                    "score_low": bucket * 100 / bucket_count,
                    "score_high": (bucket + 1) * 100 / bucket_count,
                    "signal_status": quality["signal_status"],
                    **summarize_score_bucket(pd.DataFrame(), horizon, bucket),
                }
            )
    return rows


def _audit_expression(task: dict[str, str]) -> list[dict[str, Any]]:
    assert _PANEL is not None
    assert _METADATA is not None
    assert _CONFIG is not None
    signal = pd.read_parquet(task["signal_path"])["signal"].reindex(_PANEL.index)
    bucket_count = int(_CONFIG.get("score_bucket_count", 10))
    gate_names = ["none"] + [
        f"ma{int(value)}" for value in _CONFIG.get("market_ma_windows", [20])
    ]
    rows = []
    for period in _CONFIG["periods"]:
        mask = _period_mask(_PANEL.index, period["start"], period["end"])
        period_panel = _PANEL.loc[mask].drop(columns="audit_fold")
        period_signal = signal.loc[mask]
        quality = signal_quality(
            period_signal,
            float(_CONFIG.get("min_factor_coverage", 0.5)),
            int(_CONFIG.get("min_signal_active_days", 20)),
        )
        for horizon in _CONFIG["horizons"]:
            for gate in gate_names:
                if not quality["signal_valid"]:
                    rows.extend(
                        _empty_bucket_rows(
                            task, period, int(horizon), gate, quality, bucket_count
                        )
                    )
                    continue
                _, trades, _ = run_t1_exit_backtest(
                    _apply_gate(period_signal, gate),
                    period_panel,
                    _METADATA,
                    horizon=int(horizon),
                    selection_fraction=1.0,
                    transaction_cost=float(_CONFIG.get("transaction_cost", 0.001)),
                    slippage=float(_CONFIG.get("slippage", 0.0005)),
                    universe_groups={"main", "innovation", "bse"},
                )
                if not trades.empty:
                    trades = trades.copy()
                    trades["score_bucket"] = pd.cut(
                        trades["factor_score"],
                        bins=np.linspace(0.0, 100.0, bucket_count + 1),
                        labels=False,
                        include_lowest=True,
                    ).astype("Int64")
                for universe, groups in {
                    "all_stocks": {"main", "innovation", "bse"},
                    "main_board": {"main"},
                    "innovation": {"innovation"},
                }.items():
                    universe_trades = (
                        trades.loc[trades["market_group"].isin(groups)]
                        if not trades.empty
                        else trades
                    )
                    for bucket in range(bucket_count):
                        block = (
                            universe_trades.loc[universe_trades["score_bucket"].eq(bucket)]
                            if not universe_trades.empty
                            else universe_trades
                        )
                        rows.append(
                            {
                                "expression_id": task["expression_id"],
                                "expression": task["expression"],
                                "period": period["name"],
                                "horizon": int(horizon),
                                "gate": gate,
                                "universe": universe,
                                "score_bucket": bucket,
                                "score_low": bucket * 100 / bucket_count,
                                "score_high": (bucket + 1) * 100 / bucket_count,
                                "signal_status": quality["signal_status"],
                                **summarize_score_bucket(block, int(horizon), bucket),
                            }
                        )
    return rows


def _score_profile(bucket_results: pd.DataFrame) -> pd.DataFrame:
    keys = ["expression_id", "expression", "horizon", "gate", "universe"]
    rows = []
    for values, block in bucket_results.groupby(keys, sort=False):
        recent = block.loc[block["period"].isin(["2025", "2026_ytd"])]
        valid = recent.loc[recent["status"].eq("ok") & recent["n_trades"].gt(0)]
        if valid.empty:
            continue
        grouped = valid.groupby("score_bucket").agg(
            n_trades=("n_trades", "sum"),
            positive_trades=("positive_trades", "sum"),
            target_hits=("target_hits", "sum"),
        )
        return_sum = valid.assign(
            value=valid["average_return"] * valid["n_trades"]
        ).groupby("score_bucket")["value"].sum()
        peak_sum = valid.assign(
            value=valid["average_peak_return"] * valid["n_trades"]
        ).groupby("score_bucket")["value"].sum()
        grouped["average_return"] = return_sum / grouped["n_trades"]
        grouped["average_peak_return"] = peak_sum / grouped["n_trades"]
        grouped["effective_rate"] = grouped["positive_trades"] / grouped["n_trades"]
        grouped["target_hit_rate"] = grouped["target_hits"] / grouped["n_trades"]
        top = grouped.loc[grouped.index >= 8]
        bottom = grouped.loc[grouped.index <= 1]

        def pooled(frame: pd.DataFrame, column: str) -> float:
            total = float(frame["n_trades"].sum())
            if total <= 0:
                return np.nan
            if column in {"average_return", "average_peak_return"}:
                return float((frame[column] * frame["n_trades"]).sum() / total)
            numerator = "positive_trades" if column == "effective_rate" else "target_hits"
            return float(frame[numerator].sum() / total)

        monotonicity = float(
            pd.Series(grouped["average_return"].values).corr(
                pd.Series(grouped.index.to_numpy(dtype=float)), method="spearman"
            )
        )
        best_bucket = int(grouped["average_return"].idxmax())
        rows.append(
            {
                **dict(zip(keys, values)),
                "top20_n_trades": int(top["n_trades"].sum()),
                "top20_effective_rate": pooled(top, "effective_rate"),
                "top20_target_hit_rate": pooled(top, "target_hit_rate"),
                "top20_average_return": pooled(top, "average_return"),
                "top20_average_peak_return": pooled(top, "average_peak_return"),
                "bottom20_effective_rate": pooled(bottom, "effective_rate"),
                "bottom20_average_return": pooled(bottom, "average_return"),
                "bottom20_average_peak_return": pooled(bottom, "average_peak_return"),
                "top_bottom_return_spread": pooled(top, "average_return")
                - pooled(bottom, "average_return"),
                "top_bottom_peak_return_spread": pooled(top, "average_peak_return")
                - pooled(bottom, "average_peak_return"),
                "score_return_monotonicity": monotonicity,
                "best_score_bucket": best_bucket,
                "best_bucket_average_return": float(grouped.loc[best_bucket, "average_return"]),
                "best_bucket_effective_rate": float(
                    grouped.loc[best_bucket, "effective_rate"]
                ),
            }
        )
    return pd.DataFrame(rows)


def build_max_horizon_rankings(
    aggregate_results: pd.DataFrame,
    profiles: pd.DataFrame,
) -> pd.DataFrame:
    recent = aggregate_results.loc[
        aggregate_results["period"].isin(["2025", "2026_ytd"])
        & aggregate_results["valid"]
    ]
    rows = []
    keys = ["expression_id", "expression", "gate", "universe"]
    for values, block in recent.groupby(keys, sort=False):
        by_period = block.set_index(["horizon", "period"])
        candidates = []
        for horizon in (5, 10, 20):
            if (horizon, "2025") not in by_period.index or (
                horizon,
                "2026_ytd",
            ) not in by_period.index:
                continue
            row_2025 = by_period.loc[(horizon, "2025")]
            row_2026 = by_period.loc[(horizon, "2026_ytd")]
            score = 0.40 * float(row_2025["annualized_return"]) + 0.60 * float(
                row_2026["annualized_return"]
            )
            candidates.append((score, horizon, row_2025, row_2026))
        if not candidates:
            continue
        score, horizon, row_2025, row_2026 = max(candidates, key=lambda item: item[0])
        result = {
            **dict(zip(keys, values)),
            "best_horizon": horizon,
            "max_weighted_annualized_return": score,
            "annualized_return_2025": float(row_2025["annualized_return"]),
            "annualized_return_2026_ytd": float(row_2026["annualized_return"]),
            "total_return_2025": float(row_2025["total_return"]),
            "total_return_2026_ytd": float(row_2026["total_return"]),
            "sharpe_2025": float(row_2025["sharpe"]),
            "sharpe_2026_ytd": float(row_2026["sharpe"]),
            "win_rate_2025": float(row_2025["win_rate"]),
            "win_rate_2026_ytd": float(row_2026["win_rate"]),
            "worst_recent_drawdown": min(
                float(row_2025["max_drawdown"]), float(row_2026["max_drawdown"])
            ),
            "worst_recent_sharpe": min(
                float(row_2025["sharpe"]), float(row_2026["sharpe"])
            ),
        }
        profile = pd.DataFrame()
        if not profiles.empty:
            profile = profiles.loc[
                profiles["expression_id"].eq(values[0])
                & profiles["horizon"].eq(horizon)
                & profiles["gate"].eq(values[2])
                & profiles["universe"].eq(values[3])
            ]
        if not profile.empty:
            for column in profile.columns:
                if column not in keys + ["horizon"]:
                    result[column] = profile.iloc[0][column]
        peak_profiles = (
            profiles.loc[
                profiles["expression_id"].eq(values[0])
                & profiles["gate"].eq(values[2])
                & profiles["universe"].eq(values[3])
            ]
            if not profiles.empty
            else pd.DataFrame()
        )
        if not peak_profiles.empty:
            peak_profiles = peak_profiles.loc[
                peak_profiles["top20_average_peak_return"].notna()
            ]
        if not peak_profiles.empty:
            peak_profile = peak_profiles.loc[
                peak_profiles["top20_average_peak_return"].idxmax()
            ]
            result.update(
                {
                    "max_peak_horizon": int(peak_profile["horizon"]),
                    "max_top20_average_peak_return": float(
                        peak_profile["top20_average_peak_return"]
                    ),
                    "max_peak_bottom20_average_peak_return": float(
                        peak_profile["bottom20_average_peak_return"]
                    ),
                    "max_peak_score_spread": float(
                        peak_profile["top_bottom_peak_return_spread"]
                    ),
                }
            )
        rows.append(result)
    ranking = pd.DataFrame(rows)
    if ranking.empty:
        return ranking
    return ranking.sort_values(
        ["max_weighted_annualized_return", "worst_recent_sharpe"], ascending=False
    ).reset_index(drop=True)


def render_report(
    rankings: pd.DataFrame,
    profiles: pd.DataFrame,
    receipt: dict[str, Any],
) -> str:
    lines = [
        "# Factor score-bucket and maximum-horizon audit",
        "",
        "## Scope and definitions",
        "",
        f"- Expressions: {receipt['expression_count']}.",
        "- Periods: 2025 and 2026 YTD through the frozen snapshot end date.",
        "- Horizons: D+6, D+11, and D+21 exits for 5/10/20 post-entry days.",
        "- Score: daily cross-sectional percentile, reported in ten 0--100 buckets.",
        "- Effective trade: net trade return greater than zero.",
        "- Target hit: the board-specific profit trigger was activated before exit.",
        "- Maximum-return horizon: highest 40% 2025 plus 60% 2026 YTD annualized return.",
        "",
        "The best horizon is selected in-sample from three alternatives. Treat it as a ranking",
        "diagnostic, not an unbiased estimate of future performance. The CSV retains both",
        "years, worst recent Sharpe, drawdown, and score-bucket diagnostics for review.",
        "",
        "## Completion",
        "",
        f"- Bucket rows: {receipt['actual_bucket_rows']:,} / "
        f"{receipt['expected_bucket_rows']:,}.",
        f"- Score profiles: {len(profiles):,}.",
        f"- Maximum-horizon ranking contracts: {len(rankings):,}.",
        "",
        "## Leading all-stock contracts",
        "",
        "| Rank | Factor | Gate | Best horizon | Weighted annual return | "
        "2025 / 2026 YTD Sharpe | Top-20% effective rate | Top-bottom return spread | "
        "MFE horizon / top-20% MFE |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    leaders = rankings.loc[rankings["universe"].eq("all_stocks")].head(20)
    for rank, row in enumerate(leaders.itertuples(index=False), start=1):
        lines.append(
            f"| {rank} | `{row.expression}` | {row.gate} | {row.best_horizon} | "
            f"{row.max_weighted_annualized_return:.2%} | {row.sharpe_2025:.2f} / "
            f"{row.sharpe_2026_ytd:.2f} | "
            f"{getattr(row, 'top20_effective_rate', np.nan):.2%} | "
            f"{getattr(row, 'top_bottom_return_spread', np.nan):.2%} | "
            f"{getattr(row, 'max_peak_horizon', np.nan):.0f} / "
            f"{getattr(row, 'max_top20_average_peak_return', np.nan):.2%} |"
        )
    lines.extend(
        [
            "",
            "Detailed outputs: `score_bucket_metrics.parquet`, "
            "`factor_score_profiles.csv`, `max_horizon_factor_rankings.csv`, and "
            "`max_peak_factor_rankings.csv`.",
            "",
        ]
    )
    return "\n".join(lines)


def run_audit(config: dict[str, Any]) -> dict[str, Any]:
    source_dir = Path(config["source_audit_dir"])
    output_dir = Path(config["output_dir"])
    fragment_dir = output_dir / "fragments"
    signal_dir = Path(config["expression_signal_cache"])
    output_dir.mkdir(parents=True, exist_ok=True)
    fragment_dir.mkdir(parents=True, exist_ok=True)
    libraries = discover_libraries(Path(config["factor_output_root"]))
    catalog = build_expression_catalog(libraries)
    source_receipt = json.loads(
        (source_dir / "completion_receipt.json").read_text(encoding="utf-8")
    )
    if catalog_digest(catalog) != source_receipt["catalog_digest"]:
        raise RuntimeError("current catalog differs from source all-factor audit")

    tasks = []
    for row in catalog.itertuples(index=False):
        fragment = fragment_dir / f"{row.expression_id}.csv"
        if not fragment.exists():
            tasks.append(
                {
                    "expression_id": row.expression_id,
                    "expression": row.expression,
                    "signal_path": str(signal_dir / f"{row.expression_id}.parquet"),
                    "fragment_path": str(fragment),
                }
            )
    print(f"SCORE BUCKET pending={len(tasks)} complete={len(catalog)-len(tasks)}", flush=True)
    with ProcessPoolExecutor(
        max_workers=int(config.get("workers", 3)),
        initializer=_init_worker,
        initargs=(str(config["snapshot_dir"]), config),
    ) as executor:
        future_tasks = {executor.submit(_audit_expression, task): task for task in tasks}
        completed = len(catalog) - len(tasks)
        for future in as_completed(future_tasks):
            task = future_tasks[future]
            pd.DataFrame(future.result()).to_csv(task["fragment_path"], index=False)
            completed += 1
            print(f"SCORE BUCKET EXPRESSIONS {completed}/{len(catalog)}", flush=True)

    bucket_results = pd.concat(
        [pd.read_csv(path) for path in sorted(fragment_dir.glob("*.csv"))],
        ignore_index=True,
    )
    bucket_results.to_parquet(output_dir / "score_bucket_metrics.parquet", index=False)
    profiles = _score_profile(bucket_results)
    profiles.to_csv(output_dir / "factor_score_profiles.csv", index=False)
    aggregate_results = pd.read_parquet(source_dir / "all_factor_results.parquet")
    rankings = build_max_horizon_rankings(aggregate_results, profiles)
    rankings.to_csv(output_dir / "max_horizon_factor_rankings.csv", index=False)
    peak_rankings = rankings.sort_values(
        ["max_top20_average_peak_return", "max_weighted_annualized_return"],
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)
    peak_rankings.to_csv(output_dir / "max_peak_factor_rankings.csv", index=False)
    gate_count = 1 + len(config.get("market_ma_windows", [20]))
    expected = expected_bucket_rows(
        len(catalog),
        len(config["periods"]),
        len(config["horizons"]),
        gate_count,
        3,
        int(config.get("score_bucket_count", 10)),
    )
    receipt = {
        "source_catalog_digest": source_receipt["catalog_digest"],
        "expression_count": int(len(catalog)),
        "expected_bucket_rows": expected,
        "actual_bucket_rows": int(len(bucket_results)),
        "matrix_complete": bool(len(bucket_results) == expected),
        "profile_rows": int(len(profiles)),
        "ranking_rows": int(len(rankings)),
        "peak_ranking_rows": int(len(peak_rankings)),
        "score_definition": "daily cross-sectional percentile from 0 to 100",
        "effective_rate_definition": "trade_return > 0",
        "target_hit_definition": "board-specific profit activation reached before exit",
        "best_horizon_definition": (
            "maximum 0.40*2025 annualized return + 0.60*2026 YTD annualized return"
        ),
        "config": config,
    }
    (output_dir / "REPORT.md").write_text(
        render_report(rankings, profiles, receipt), encoding="utf-8"
    )
    (output_dir / "completion_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if not receipt["matrix_complete"]:
        raise RuntimeError(f"incomplete score-bucket matrix: {len(bucket_results)} != {expected}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    run_audit(yaml.safe_load(args.config.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
