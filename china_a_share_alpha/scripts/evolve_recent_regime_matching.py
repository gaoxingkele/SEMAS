"""Evolve stock-to-factor matching for recent walk-forward market regimes."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.t1_exit_policy import run_t1_exit_backtest
from china_a_share_alpha.scripts.evolve_stock_factor_matching import (
    MatchingGenome,
    _mutate,
    _random_genome,
    compose_matched_signal,
    estimate_matching_utilities,
    fold_forward_returns,
    load_or_build_signal_cache,
    matching_weights,
)
from china_a_share_alpha.scripts.run_t1_full_library_audit import (
    _load_snapshot,
    discover_libraries,
)


def stable_symbol_bucket(symbol: str, bucket_count: int) -> int:
    """Assign a symbol to a deterministic stock-disjoint validation bucket."""
    digest = hashlib.sha256(str(symbol).encode()).digest()
    return int.from_bytes(digest[:4], "big") % bucket_count


def _date_mask(index: pd.Index, start: str, end: str) -> np.ndarray:
    dates = pd.to_datetime(index.get_level_values("date"))
    return np.asarray((dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end)))


def build_window_contexts(
    panel: pd.DataFrame,
    signals: pd.DataFrame,
    metadata: pd.DataFrame,
    windows: list[dict[str, str]],
    horizon: int,
    utility_lookback_days: int,
) -> list[dict[str, Any]]:
    """Build walk-forward utilities using only dates before each evaluation window."""
    all_dates = pd.DatetimeIndex(
        pd.to_datetime(panel.index.get_level_values("date")).unique()
    ).sort_values()
    contexts = []
    for window in windows:
        start = pd.Timestamp(window["start"])
        prior_dates = all_dates[all_dates < start][-utility_lookback_days:]
        if len(prior_dates) <= horizon:
            raise ValueError(f"insufficient utility history for {window['name']}")
        dates = pd.to_datetime(panel.index.get_level_values("date"))
        train_mask = dates.isin(prior_dates)
        evaluation_mask = _date_mask(panel.index, window["start"], window["end"])
        train_panel = panel.loc[train_mask].drop(columns="audit_fold")
        evaluation_panel = panel.loc[evaluation_mask].drop(columns="audit_fold")
        if evaluation_panel.empty:
            raise ValueError(f"empty evaluation window: {window['name']}")
        labels = fold_forward_returns(train_panel, horizon)
        contexts.append(
            {
                "name": window["name"],
                "start": str(evaluation_panel.index.get_level_values("date").min().date()),
                "end": str(evaluation_panel.index.get_level_values("date").max().date()),
                "utility_start": str(prior_dates.min().date()),
                "utility_end": str(prior_dates.max().date()),
                "panel": evaluation_panel,
                "signals": signals.loc[evaluation_mask],
                "utilities": estimate_matching_utilities(
                    signals.loc[train_mask], labels, metadata
                ),
            }
        )
    return contexts


def return_concentration(trades: pd.DataFrame) -> float:
    """Measure dependence on one stock's absolute aggregate trade contribution."""
    if trades.empty:
        return 1.0
    by_symbol = trades.groupby("symbol")["trade_return"].sum().abs()
    total = float(by_symbol.sum())
    return float(by_symbol.max() / total) if total > 0 else 1.0


def recent_regime_fitness(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Favor the lower tail across time and stock-disjoint cohorts."""
    valid = [row for row in rows if row["metrics"].get("valid")]
    if len(valid) != len(rows):
        return {"fitness": -100.0}
    sharpes = np.asarray([float(row["metrics"]["sharpe"]) for row in valid])
    full_sharpes = np.asarray(
        [float(row["metrics"]["sharpe"]) for row in valid if row["cohort"] == "all"]
    )
    worst_drawdown = min(float(row["metrics"]["max_drawdown"]) for row in valid)
    max_concentration = max(float(row["concentration"]) for row in valid)
    fitness = 0.40 * float(np.median(sharpes)) + 0.60 * float(full_sharpes.min())
    fitness -= max(0.0, abs(worst_drawdown) - 0.25) * 4.0
    fitness -= max(0.0, max_concentration - 0.10) * 8.0
    if full_sharpes.min() < 0:
        fitness -= 5.0
    if worst_drawdown < -0.30:
        fitness -= 5.0
    return {
        "fitness": fitness,
        "median_cohort_sharpe": float(np.median(sharpes)),
        "worst_full_sharpe": float(full_sharpes.min()),
        "worst_drawdown": worst_drawdown,
        "max_return_concentration": max_concentration,
    }


def evaluate_selection_genome(
    genome: MatchingGenome,
    contexts: list[dict[str, Any]],
    metadata: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    bucket_count = int(config.get("stock_buckets", 2))
    symbol_buckets = metadata["symbol"].astype(str).map(
        lambda symbol: stable_symbol_bucket(symbol, bucket_count)
    )
    rows = []
    for context in contexts:
        weights = matching_weights(genome, context["utilities"])
        signal = compose_matched_signal(context["signals"], weights)
        cohorts = {"all": metadata}
        cohorts.update(
            {
                f"bucket_{bucket}": metadata.loc[symbol_buckets.eq(bucket)]
                for bucket in range(bucket_count)
            }
        )
        for cohort, cohort_metadata in cohorts.items():
            metrics, trades, _ = run_t1_exit_backtest(
                signal,
                context["panel"],
                cohort_metadata,
                horizon=int(config["horizon"]),
                selection_fraction=genome.selection_fraction,
                transaction_cost=float(config.get("transaction_cost", 0.001)),
                slippage=float(config.get("slippage", 0.0005)),
                universe_groups={"main", "innovation", "bse"},
            )
            rows.append(
                {
                    "window": context["name"],
                    "cohort": cohort,
                    "metrics": metrics,
                    "concentration": return_concentration(trades),
                }
            )
    return recent_regime_fitness(rows), rows


def _diagnose(
    genome: MatchingGenome,
    contexts: list[dict[str, Any]],
    metadata: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    trade_rows = []
    universes = {
        "all_stocks": {"main", "innovation", "bse"},
        "main_board": {"main"},
        "innovation": {"innovation"},
    }
    for context in contexts:
        weights = matching_weights(genome, context["utilities"])
        signal = compose_matched_signal(context["signals"], weights)
        for universe, groups in universes.items():
            metrics, trades, _ = run_t1_exit_backtest(
                signal,
                context["panel"],
                metadata,
                horizon=int(config["horizon"]),
                selection_fraction=genome.selection_fraction,
                transaction_cost=float(config.get("transaction_cost", 0.001)),
                slippage=float(config.get("slippage", 0.0005)),
                universe_groups=groups,
            )
            metric_rows.append(
                {
                    "window": context["name"],
                    "universe": universe,
                    "return_concentration": return_concentration(trades),
                    **metrics,
                }
            )
            trade_rows.append(trades.assign(window=context["name"], universe=universe))
    return pd.DataFrame(metric_rows), pd.concat(trade_rows, ignore_index=True)


def evolve(config: dict[str, Any]) -> dict[str, Any]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    panel, metadata, manifest = _load_snapshot(Path(config["snapshot_dir"]))
    libraries = discover_libraries(Path(config["factor_output_root"]))
    signals, errors = load_or_build_signal_cache(
        Path(config["signal_cache"]),
        libraries,
        panel,
        str(manifest.get("snapshot_id")),
        float(config.get("min_factor_coverage", 0.5)),
    )
    if not errors.empty:
        errors.to_csv(output_dir / "expression_errors.csv", index=False)

    selection_contexts = build_window_contexts(
        panel,
        signals,
        metadata,
        config["selection_windows"],
        int(config["horizon"]),
        int(config.get("utility_lookback_days", 504)),
    )
    rng = np.random.default_rng(int(config.get("seed", 20260911)))
    population_size = int(config.get("population_size", 8))
    elite_count = int(config.get("elite_count", 3))
    rounds = int(config.get("rounds", 8))
    population = [_random_genome(rng) for _ in range(population_size)]
    history = []
    best: tuple[float, MatchingGenome, dict[str, float], list[dict[str, Any]]] | None = None

    for round_number in range(1, rounds + 1):
        scored = []
        for candidate_number, genome in enumerate(population, start=1):
            summary, detail = evaluate_selection_genome(
                genome, selection_contexts, metadata, config
            )
            fitness = float(summary["fitness"])
            history.append(
                {
                    "round": round_number,
                    "candidate": candidate_number,
                    **summary,
                    **asdict(genome),
                    "global_weight": genome.global_weight,
                }
            )
            scored.append((fitness, genome, summary, detail))
            if best is None or fitness > best[0]:
                best = (fitness, genome, summary, detail)
        scored.sort(key=lambda item: item[0], reverse=True)
        leader = scored[0]
        print(
            f"ROUND {round_number}/{rounds} fitness={leader[0]:.4f} "
            f"worst_selection_sharpe={leader[2].get('worst_full_sharpe', -100):.4f} "
            f"dd={leader[2].get('worst_drawdown', -1):.2%}"
        )
        elites = [item[1] for item in scored[:elite_count]]
        population = elites.copy()
        while len(population) < population_size:
            parent = elites[len(population) % len(elites)]
            population.append(_mutate(parent, rng))

    assert best is not None
    pd.DataFrame(history).to_csv(output_dir / "evolution_history.csv", index=False)
    diagnostic_contexts = build_window_contexts(
        panel,
        signals,
        metadata,
        config["diagnostic_windows"],
        int(config["horizon"]),
        int(config.get("utility_lookback_days", 504)),
    )
    diagnostic_metrics, diagnostic_trades = _diagnose(
        best[1], diagnostic_contexts, metadata, config
    )
    diagnostic_metrics.to_csv(output_dir / "diagnostic_results.csv", index=False)
    diagnostic_trades.to_parquet(output_dir / "diagnostic_trades.parquet", index=False)

    receipt = {
        "snapshot_id": manifest.get("snapshot_id"),
        "data_end": str(panel.index.get_level_values("date").max().date()),
        "selection_period": [window["name"] for window in config["selection_windows"]],
        "diagnostic_period": [window["name"] for window in config["diagnostic_windows"]],
        "diagnostic_is_blind": False,
        "rounds": rounds,
        "population_size": population_size,
        "best_fitness": best[0],
        "best_summary": best[2],
        "best_selection_detail": best[3],
        "best_genome": asdict(best[1]) | {"global_weight": best[1].global_weight},
        "window_receipts": [
            {
                key: value
                for key, value in context.items()
                if key not in {"panel", "signals", "utilities"}
            }
            for context in selection_contexts + diagnostic_contexts
        ],
        "config": config,
    }
    (output_dir / "campaign_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    evolve(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
