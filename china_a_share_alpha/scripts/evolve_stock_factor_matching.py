"""Evolve stock-to-factor-library matching without opening the test fold."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.t1_exit_policy import run_t1_exit_backtest
from china_a_share_alpha.scripts.run_t1_full_library_audit import (
    _load_snapshot,
    build_library_signals,
    discover_libraries,
)


@dataclass(frozen=True)
class MatchingGenome:
    top_k: int
    stock_weight: float
    industry_weight: float
    market_weight: float
    temperature: float
    min_observations: int
    selection_fraction: float

    @property
    def global_weight(self) -> float:
        return max(0.0, 1.0 - self.stock_weight - self.industry_weight - self.market_weight)


def fold_forward_returns(frame: pd.DataFrame, horizon: int) -> pd.Series:
    """Create labels inside one fold so its last rows cannot cross a boundary."""
    return frame.groupby(level="symbol")["close"].transform(
        lambda values: values.pct_change(horizon, fill_method=None).shift(-horizon)
    )


def _catalog_digest(libraries: pd.DataFrame) -> str:
    payload = []
    for _, row in libraries.sort_values("library_id").iterrows():
        payload.append(row.library_id + "|" + "|".join(row.expressions))
    return hashlib.sha256("\n".join(payload).encode()).hexdigest()


def load_or_build_signal_cache(
    cache_path: Path,
    libraries: pd.DataFrame,
    panel: pd.DataFrame,
    snapshot_id: str,
    min_factor_coverage: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    manifest_path = cache_path.with_suffix(".json")
    digest = _catalog_digest(libraries)
    if cache_path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("snapshot_id") == snapshot_id and manifest.get("catalog_digest") == digest:
            print(f"SIGNAL CACHE HIT {cache_path}")
            return pd.read_parquet(cache_path), pd.DataFrame(manifest.get("errors", []))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    signals, errors = build_library_signals(
        libraries,
        panel.drop(columns="audit_fold"),
        panel.index,
        min_factor_coverage,
    )
    frame = pd.DataFrame(signals, index=panel.index).astype(np.float32)
    frame.to_parquet(cache_path, compression="zstd")
    manifest_path.write_text(
        json.dumps(
            {
                "snapshot_id": snapshot_id,
                "catalog_digest": digest,
                "libraries": int(len(libraries)),
                "errors": errors.to_dict("records"),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return frame, errors


def _corr_with_observations(
    signals: pd.DataFrame, labels: pd.Series
) -> tuple[pd.Series, pd.Series]:
    valid_labels = labels.notna()
    correlations = signals.loc[valid_labels].corrwith(labels.loc[valid_labels])
    observations = signals.loc[valid_labels].notna().sum()
    return correlations, observations


def estimate_matching_utilities(
    signals: pd.DataFrame,
    labels: pd.Series,
    metadata: pd.DataFrame,
) -> dict[str, Any]:
    """Estimate train-only stock, industry, market, and global utilities."""
    meta = metadata.rename(columns={"ts_code": "symbol"}).set_index("symbol")
    meta.index = meta.index.astype(str)
    libraries = signals.columns
    stock_rows = []
    observation_rows = []
    for symbol in signals.index.get_level_values("symbol").unique():
        block = signals.xs(symbol, level="symbol")
        target = labels.xs(symbol, level="symbol").reindex(block.index)
        corr, observations = _corr_with_observations(block, target)
        stock_rows.append(corr.rename(str(symbol)))
        observation_rows.append(observations.rename(str(symbol)))
    stock = pd.DataFrame(stock_rows).reindex(columns=libraries)
    stock_observations = pd.DataFrame(observation_rows).reindex(columns=libraries)

    long = signals.join(labels.rename("label"))
    index_frame = long.index.to_frame(index=False)
    index_frame["industry"] = index_frame["symbol"].map(meta.get("industry"))
    index_frame["market"] = index_frame["symbol"].map(meta.get("market"))
    long = long.reset_index(drop=True)
    long[["symbol", "date", "industry", "market"]] = index_frame

    def grouped_utilities(group_column: str) -> pd.DataFrame:
        rows = []
        for group_name, block in long.groupby(group_column, dropna=False):
            corr, _ = _corr_with_observations(block[libraries], block["label"])
            rows.append(corr.rename(str(group_name)))
        return pd.DataFrame(rows).reindex(columns=libraries)

    global_corr, _ = _corr_with_observations(long[libraries], long["label"])
    return {
        "stock": stock,
        "stock_observations": stock_observations,
        "industry": grouped_utilities("industry"),
        "market": grouped_utilities("market"),
        "global": global_corr.reindex(libraries),
        "metadata": meta,
    }


def matching_weights(genome: MatchingGenome, utilities: dict[str, Any]) -> pd.DataFrame:
    stock = utilities["stock"]
    observations = utilities["stock_observations"]
    meta = utilities["metadata"]
    result = pd.DataFrame(0.0, index=stock.index, columns=stock.columns)
    for symbol in stock.index:
        details = meta.reindex([symbol]).iloc[0]
        stock_score = stock.loc[symbol].where(observations.loc[symbol] >= genome.min_observations)
        industry_score = utilities["industry"].reindex([str(details.get("industry"))]).iloc[0]
        market_score = utilities["market"].reindex([str(details.get("market"))]).iloc[0]
        score = (
            genome.stock_weight * stock_score.fillna(0.0)
            + genome.industry_weight * industry_score.fillna(0.0)
            + genome.market_weight * market_score.fillna(0.0)
            + genome.global_weight * utilities["global"].fillna(0.0)
        )
        positive = score[score > 0].nlargest(genome.top_k)
        if positive.empty:
            positive = score.nlargest(genome.top_k)
        shifted = (positive - positive.max()) / max(genome.temperature, 1e-4)
        weights = np.exp(shifted.clip(-30, 0))
        result.loc[symbol, weights.index] = weights / weights.sum()
    return result


def compose_matched_signal(signals: pd.DataFrame, weights: pd.DataFrame) -> pd.Series:
    """Apply fixed train-estimated stock/library weights to one fold."""
    output = pd.Series(np.nan, index=signals.index, dtype=np.float32, name="matched_signal")
    for symbol in signals.index.get_level_values("symbol").unique():
        if symbol not in weights.index:
            continue
        block = signals.xs(symbol, level="symbol")
        weight = weights.loc[symbol].to_numpy(dtype=float)
        values = block.to_numpy(dtype=float)
        valid = np.isfinite(values) & (weight[None, :] > 0)
        denominator = (valid * weight[None, :]).sum(axis=1)
        numerator = np.nansum(values * weight[None, :], axis=1)
        matched = np.divide(
            numerator,
            denominator,
            out=np.full(len(block), np.nan),
            where=denominator > 0,
        )
        output.loc[(symbol, block.index)] = matched.astype(np.float32)
    return output


def _random_genome(rng: np.random.Generator) -> MatchingGenome:
    raw = rng.dirichlet([2.5, 2.0, 1.5, 1.0])
    return MatchingGenome(
        top_k=int(rng.integers(1, 9)),
        stock_weight=float(raw[0]),
        industry_weight=float(raw[1]),
        market_weight=float(raw[2]),
        temperature=float(rng.uniform(0.02, 0.25)),
        min_observations=int(rng.choice([80, 120, 160, 200, 240])),
        selection_fraction=float(rng.choice([0.10, 0.15, 0.20, 0.25, 0.30])),
    )


def _mutate(parent: MatchingGenome, rng: np.random.Generator) -> MatchingGenome:
    weights = np.array(
        [parent.stock_weight, parent.industry_weight, parent.market_weight, parent.global_weight]
    )
    weights = np.maximum(0.01, weights + rng.normal(0, 0.08, size=4))
    weights /= weights.sum()
    fractions = [0.10, 0.15, 0.20, 0.25, 0.30]
    fraction_index = int(np.argmin(np.abs(np.asarray(fractions) - parent.selection_fraction)))
    fraction_index = int(np.clip(fraction_index + rng.integers(-1, 2), 0, len(fractions) - 1))
    return MatchingGenome(
        top_k=int(np.clip(parent.top_k + rng.integers(-2, 3), 1, 10)),
        stock_weight=float(weights[0]),
        industry_weight=float(weights[1]),
        market_weight=float(weights[2]),
        temperature=float(np.clip(parent.temperature + rng.normal(0, 0.035), 0.01, 0.35)),
        min_observations=int(np.clip(parent.min_observations + rng.choice([-40, 0, 40]), 40, 280)),
        selection_fraction=float(fractions[fraction_index]),
    )


def _fitness(metrics: dict[str, Any], trades: pd.DataFrame) -> tuple[float, float]:
    if not metrics.get("valid") or trades.empty:
        return -100.0, 1.0
    concentration = float(trades["symbol"].value_counts(normalize=True).max())
    drawdown_penalty = max(0.0, abs(float(metrics["max_drawdown"])) - 0.20) * 2.0
    concentration_penalty = max(0.0, concentration - 0.05) * 5.0
    return float(metrics["sharpe"] - drawdown_penalty - concentration_penalty), concentration


def evolve(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    libraries = discover_libraries(Path(config["factor_output_root"]))
    panel, metadata, manifest = _load_snapshot(Path(config["snapshot_dir"]))
    signals, errors = load_or_build_signal_cache(
        Path(config["signal_cache"]),
        libraries,
        panel,
        str(manifest.get("snapshot_id")),
        float(config.get("min_factor_coverage", 0.5)),
    )
    if not errors.empty:
        errors.to_csv(output_dir / "expression_errors.csv", index=False)

    train_mask = panel["audit_fold"].eq("train")
    val_mask = panel["audit_fold"].eq("val")
    test_mask = panel["audit_fold"].eq("test")
    train_panel = panel.loc[train_mask].drop(columns="audit_fold")
    val_panel = panel.loc[val_mask].drop(columns="audit_fold")
    test_panel = panel.loc[test_mask].drop(columns="audit_fold")
    train_labels = fold_forward_returns(train_panel, int(config["horizon"]))
    utilities = estimate_matching_utilities(signals.loc[train_mask], train_labels, metadata)

    rng = np.random.default_rng(int(config.get("seed", 20260831)))
    population_size = int(config.get("population_size", 12))
    rounds = int(config.get("rounds", 12))
    elite_count = int(config.get("elite_count", 3))
    population = [_random_genome(rng) for _ in range(population_size)]
    history: list[dict[str, Any]] = []
    best: tuple[float, MatchingGenome, dict[str, Any]] | None = None

    for round_number in range(1, rounds + 1):
        scored = []
        for candidate_number, genome in enumerate(population, start=1):
            weights = matching_weights(genome, utilities)
            signal = compose_matched_signal(signals.loc[val_mask], weights)
            metrics, trades, _ = run_t1_exit_backtest(
                signal,
                val_panel,
                metadata,
                horizon=int(config["horizon"]),
                selection_fraction=genome.selection_fraction,
                transaction_cost=float(config.get("transaction_cost", 0.001)),
                slippage=float(config.get("slippage", 0.0005)),
                universe_groups={"main", "innovation", "bse"},
            )
            fitness, concentration = _fitness(metrics, trades)
            row = {
                "round": round_number,
                "candidate": candidate_number,
                "fitness": fitness,
                "max_trade_concentration": concentration,
                **asdict(genome),
                **{f"val_{key}": value for key, value in metrics.items()},
            }
            history.append(row)
            scored.append((fitness, genome, metrics))
            if best is None or fitness > best[0]:
                best = (fitness, genome, metrics)
        scored.sort(key=lambda item: item[0], reverse=True)
        leader = scored[0]
        print(
            f"ROUND {round_number}/{rounds} fitness={leader[0]:.4f} "
            f"val_sharpe={leader[2]['sharpe']:.4f} dd={leader[2]['max_drawdown']:.2%}"
        )
        elites = [item[1] for item in scored[:elite_count]]
        population = elites.copy()
        while len(population) < population_size:
            population.append(_mutate(elites[len(population) % len(elites)], rng))

    assert best is not None
    best_genome = best[1]
    best_weights = matching_weights(best_genome, utilities)
    history_frame = pd.DataFrame(history)
    history_frame.to_csv(output_dir / "evolution_history.csv", index=False)
    best_weights.to_parquet(output_dir / "best_matching_weights.parquet")

    final_rows = []
    final_trades = {}
    test_signal = compose_matched_signal(signals.loc[test_mask], best_weights)
    for universe, groups in {
        "all_stocks": {"main", "innovation", "bse"},
        "main_board": {"main"},
        "innovation": {"innovation"},
    }.items():
        metrics, trades, _ = run_t1_exit_backtest(
            test_signal,
            test_panel,
            metadata,
            horizon=int(config["horizon"]),
            selection_fraction=best_genome.selection_fraction,
            transaction_cost=float(config.get("transaction_cost", 0.001)),
            slippage=float(config.get("slippage", 0.0005)),
            universe_groups=groups,
        )
        final_rows.append({"universe": universe, **metrics})
        final_trades[universe] = trades
    final = pd.DataFrame(final_rows)
    final.to_csv(output_dir / "final_test_results.csv", index=False)
    pd.concat(
        [frame.assign(universe=name) for name, frame in final_trades.items()], ignore_index=True
    ).to_parquet(output_dir / "final_test_trades.parquet", index=False)

    all_trades = final_trades["all_stocks"]
    contribution = all_trades.groupby("symbol")["trade_return"].sum().sort_values(ascending=False)
    stress_rows = []
    for remove_count in [1, 3, 5, 10]:
        removed = set(contribution.head(remove_count).index)
        stressed_metadata = metadata[~metadata["symbol"].isin(removed)]
        metrics, _, _ = run_t1_exit_backtest(
            test_signal,
            test_panel,
            stressed_metadata,
            horizon=int(config["horizon"]),
            selection_fraction=best_genome.selection_fraction,
            transaction_cost=float(config.get("transaction_cost", 0.001)),
            slippage=float(config.get("slippage", 0.0005)),
            universe_groups={"main", "innovation", "bse"},
        )
        stress_rows.append(
            {
                "removed_top_contributors": remove_count,
                "removed_symbols": ",".join(sorted(removed)),
                **metrics,
            }
        )
    pd.DataFrame(stress_rows).to_csv(output_dir / "top_contributor_stress.csv", index=False)

    receipt = {
        "snapshot_id": manifest.get("snapshot_id"),
        "rounds": rounds,
        "population_size": population_size,
        "test_opened_after_evolution": True,
        "selection_fold": "validation",
        "best_validation_fitness": best[0],
        "best_validation_metrics": best[2],
        "best_genome": asdict(best_genome) | {"global_weight": best_genome.global_weight},
        "config": config,
    }
    (output_dir / "campaign_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return history_frame, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    evolve(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
