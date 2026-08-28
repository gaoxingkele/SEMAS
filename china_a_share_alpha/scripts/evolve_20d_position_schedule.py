"""Evolve a 20-day rank-decile add/trim position schedule on frozen data."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.position_schedule import (
    PreparedFold,
    backtest_schedule,
    prepare_fold,
    rank_percentiles_to_bins,
)
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_frozen_promotion_audit import verify_snapshot
from china_a_share_alpha.scripts.run_multihizon_audit import (
    _build_equal_weight_signal,
    _zscore,
)

BASELINE_SCHEDULES = {
    "static_100pct": [1.0] * 10,
    "legacy_trim": [1.0, 1.0, 0.7, 0.7, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0],
}


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def build_library_signal(
    library: pd.DataFrame,
    panel: pd.DataFrame,
    smooth_span: int,
    min_factor_coverage: float,
) -> tuple[pd.Series, dict[str, Any]]:
    factor_frames = {}
    errors = []
    for row_index, row in library.reset_index(drop=True).iterrows():
        name = f"{row.get('factor', 'factor')}__row_{row_index + 1}"
        try:
            factor_frames[name] = _zscore(parse_expression(row["expression"]).eval(panel))
        except Exception as exc:
            errors.append({"factor": row.get("factor"), "error": str(exc)})
    signal, coverage = _build_equal_weight_signal(
        factor_frames,
        smooth_span=smooth_span,
        min_factor_coverage=min_factor_coverage,
    )
    return signal, {
        **coverage,
        "n_library_rows": int(len(library)),
        "n_factors_evaluated": int(len(factor_frames)),
        "factor_errors": errors,
    }


def normalize_schedule(
    values: np.ndarray,
    step: float,
    max_multiplier: float,
) -> np.ndarray:
    quantized = np.round(np.clip(values, 0.0, max_multiplier) / step) * step
    monotonic = np.minimum.accumulate(quantized)
    monotonic[0] = max(monotonic[0], 1.0)
    return np.round(monotonic, 10)


def _schedule_key(schedule: np.ndarray) -> tuple[int, ...]:
    return tuple(int(round(value * 10)) for value in schedule)


def training_score(metrics: dict[str, float], drawdown_limit: float) -> float:
    if not metrics["valid"]:
        return -1e9
    drawdown_penalty = max(0.0, abs(metrics["max_drawdown"]) - drawdown_limit)
    turnover_penalty = 0.01 * metrics["annualized_turnover"]
    return float(metrics["sharpe"] - 2.0 * drawdown_penalty - turnover_penalty)


def validation_score(
    train_metrics: dict[str, float],
    val_metrics: dict[str, float],
    drawdown_limit: float,
) -> float:
    if not train_metrics["valid"] or not val_metrics["valid"]:
        return -1e9
    gap_penalty = 0.25 * abs(train_metrics["sharpe"] - val_metrics["sharpe"])
    drawdown_penalty = 2.0 * max(0.0, abs(val_metrics["max_drawdown"]) - drawdown_limit)
    turnover_penalty = 0.01 * val_metrics["annualized_turnover"]
    return float(val_metrics["sharpe"] - gap_penalty - drawdown_penalty - turnover_penalty)


def strategy_verdict(
    winner: dict[str, Any],
    final_results: dict[str, dict[str, float]],
    config: dict[str, Any],
) -> str:
    if winner.get("baseline_name") == "static_100pct":
        return "STATIC_BASELINE_SELECTED"
    improvement = final_results["winner"]["sharpe"] - final_results["static_100pct"]["sharpe"]
    drawdown_degradation = (
        final_results["static_100pct"]["max_drawdown"] - final_results["winner"]["max_drawdown"]
    )
    if improvement >= float(
        config.get("min_final_sharpe_improvement", 0.1)
    ) and drawdown_degradation <= float(config.get("max_final_drawdown_degradation", 0.02)):
        return "DYNAMIC_CANDIDATE_PASSED"
    return "DYNAMIC_CANDIDATE_REJECTED_ON_FINAL"


def evolve_one_seed(
    fold: PreparedFold,
    config: dict[str, Any],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = np.random.default_rng(seed)
    population_size = int(config["population_size"])
    generations = int(config["generations"])
    elite_count = max(2, int(population_size * float(config["elite_fraction"])))
    step = float(config["multiplier_step"])
    max_multiplier = float(config["max_multiplier"])
    transaction_cost = float(config["transaction_cost"])
    drawdown_limit = float(config["drawdown_limit"])

    population = [
        normalize_schedule(rng.uniform(0.0, max_multiplier, 10), step, max_multiplier)
        for _ in range(population_size - len(BASELINE_SCHEDULES))
    ]
    population.extend(np.asarray(value, dtype=float) for value in BASELINE_SCHEDULES.values())
    cache: dict[tuple[int, ...], dict[str, Any]] = {}
    history = []

    def evaluate(schedule: np.ndarray) -> dict[str, Any]:
        key = _schedule_key(schedule)
        if key not in cache:
            metrics = backtest_schedule(fold, schedule, transaction_cost)
            cache[key] = {
                "schedule": schedule.tolist(),
                "metrics": metrics,
                "score": training_score(metrics, drawdown_limit),
            }
        return cache[key]

    for generation in range(generations):
        ranked = sorted(
            (evaluate(schedule) for schedule in population),
            key=lambda row: row["score"],
            reverse=True,
        )
        best = ranked[0]
        history.append(
            {
                "seed": seed,
                "generation": generation,
                "score": best["score"],
                "sharpe": best["metrics"]["sharpe"],
                "schedule": best["schedule"],
            }
        )
        elites = [np.asarray(row["schedule"], dtype=float) for row in ranked[:elite_count]]
        next_population = elites.copy()
        while len(next_population) < population_size:
            left = elites[int(rng.integers(0, len(elites)))]
            right = elites[int(rng.integers(0, len(elites)))]
            cut = int(rng.integers(1, 10))
            child = np.concatenate([left[:cut], right[cut:]])
            mutation_count = int(rng.integers(1, 4))
            for index in rng.choice(10, size=mutation_count, replace=False):
                child[index] += rng.choice([-2, -1, 1, 2]) * step
            next_population.append(normalize_schedule(child, step, max_multiplier))
        population = next_population

    finalists = sorted(cache.values(), key=lambda row: row["score"], reverse=True)
    return finalists[: int(config["finalists_per_seed"])], history


def run_evolution(
    snapshot_dir: Path,
    library_path: Path,
    config_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    manifest = verify_snapshot(snapshot_dir)
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    library = pd.read_csv(library_path)

    panels = {}
    signals = {}
    signal_receipts = {}
    for name in ("train", "val", "test"):
        panel = pd.read_parquet(snapshot_dir / manifest["files"][name]["file"])
        signal, signal_receipt = build_library_signal(
            library,
            panel,
            smooth_span=int(config["smooth_span"]),
            min_factor_coverage=float(config["min_factor_coverage"]),
        )
        panels[name] = panel
        signals[name] = signal
        signal_receipts[name] = signal_receipt

    if config.get("recovery_split_date"):
        split_date = pd.Timestamp(config["recovery_split_date"])
        development_panel = pd.concat([panels["train"], panels["val"]]).sort_index()
        development_signal, development_receipt = build_library_signal(
            library,
            development_panel,
            smooth_span=int(config["smooth_span"]),
            min_factor_coverage=float(config["min_factor_coverage"]),
        )
        test_dates = panels["test"].index.get_level_values("date")
        signal_dates = signals["test"].index.get_level_values("date")
        fold_inputs = {
            "development": (development_signal, development_panel),
            "audit": (
                signals["test"].loc[signal_dates < split_date],
                panels["test"].loc[test_dates < split_date],
            ),
            "final": (
                signals["test"].loc[signal_dates >= split_date],
                panels["test"].loc[test_dates >= split_date],
            ),
        }
        signal_receipts["development"] = development_receipt
        selection_contract = {
            "development": "2021-06 through 2023-12",
            "audit": f"2024-01 through {(split_date - pd.Timedelta(days=1)).date()}",
            "final": f"{split_date.date()} through 2026-05",
        }
        training_fold_name = "development"
        validation_fold_name = "audit"
        test_fold_name = "final"
    else:
        fold_inputs = {name: (signals[name], panels[name]) for name in ("train", "val", "test")}
        selection_contract = {
            "development": "train",
            "audit": "validation",
            "final": "test",
        }
        training_fold_name = "train"
        validation_fold_name = "val"
        test_fold_name = "test"

    folds = {
        name: prepare_fold(
            name,
            signal,
            panel,
            horizon=int(config["horizon"]),
            selection_fraction=float(config["selection_fraction"]),
        )
        for name, (signal, panel) in fold_inputs.items()
    }

    all_finalists = {}
    history_rows = []
    for seed in config["seeds"]:
        finalists, history = evolve_one_seed(folds[training_fold_name], config, int(seed))
        history_rows.extend(history)
        for finalist in finalists:
            schedule = np.asarray(finalist["schedule"], dtype=float)
            all_finalists[_schedule_key(schedule)] = finalist
    for name, schedule_values in BASELINE_SCHEDULES.items():
        schedule = np.asarray(schedule_values, dtype=float)
        train_metrics = backtest_schedule(
            folds[training_fold_name], schedule, float(config["transaction_cost"])
        )
        all_finalists[_schedule_key(schedule)] = {
            "schedule": schedule.tolist(),
            "metrics": train_metrics,
            "score": training_score(train_metrics, float(config["drawdown_limit"])),
            "baseline_name": name,
        }

    candidate_rows = []
    for finalist in all_finalists.values():
        schedule = np.asarray(finalist["schedule"], dtype=float)
        train_metrics = finalist["metrics"]
        val_metrics = backtest_schedule(
            folds[validation_fold_name], schedule, float(config["transaction_cost"])
        )
        candidate_rows.append(
            {
                "schedule": schedule.tolist(),
                "train": train_metrics,
                "validation": val_metrics,
                "training_score": finalist["score"],
                "selection_score": validation_score(
                    train_metrics,
                    val_metrics,
                    float(config["drawdown_limit"]),
                ),
                "baseline_name": finalist.get("baseline_name"),
            }
        )
    candidate_rows.sort(key=lambda row: row["selection_score"], reverse=True)
    winner = candidate_rows[0]

    preregistered = {
        "winner": winner["schedule"],
        **BASELINE_SCHEDULES,
    }
    audit_results = {}
    test_results = {}
    for name, schedule in preregistered.items():
        audit_results[name] = backtest_schedule(
            folds[validation_fold_name], schedule, float(config["transaction_cost"])
        )
        test_results[name] = backtest_schedule(
            folds[test_fold_name], schedule, float(config["transaction_cost"])
        )

    receipt = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_verified": True,
        "library_path": str(library_path),
        "library_sha256": _sha256_file(library_path),
        "config_path": str(config_path),
        "config_sha256": _sha256_file(config_path),
        "interpretation_contract": {
            "rank_step": "10 cross-sectional percentile points",
            "multiplier_step": config["multiplier_step"],
            "long_cohort": "top 20% selected every 20 trading days",
            "short_book": "fixed bottom 20% cohort; not evolved",
            "lookahead_rule": "positions formed at day d earn returns from day d+1",
            "selection_rule": "evolve on development, select on audit, open final once",
            "temporal_roles": selection_contract,
        },
        "signal_receipts": signal_receipts,
        "winner": winner,
        "audit_results": audit_results,
        "test_results": test_results,
        "top_validation_candidates": candidate_rows[:10],
        "search": {
            "seeds": config["seeds"],
            "population_size": config["population_size"],
            "generations": config["generations"],
            "unique_finalists": len(candidate_rows),
        },
    }
    receipt["verdict"] = strategy_verdict(winner, test_results, config)
    receipt["test_improvement_vs_static"] = {
        metric: test_results["winner"][metric] - test_results["static_100pct"][metric]
        for metric in ("sharpe", "annualized_return", "max_drawdown")
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "position_schedule_evolution_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    pd.DataFrame(history_rows).to_csv(output_dir / "evolution_history.csv", index=False)
    _write_markdown(receipt, output_dir / "position_schedule_evolution_receipt.md")
    return receipt


def _write_markdown(receipt: dict[str, Any], path: Path) -> None:
    winner = receipt["winner"]
    lines = [
        "# 20d Position-Schedule Evolution Receipt",
        "",
        f"- Snapshot: `{receipt['snapshot_id']}`",
        f"- Winner schedule: `{winner['schedule']}`",
        f"- Validation selection score: {winner['selection_score']:.4f}",
        f"- Verdict: **{receipt['verdict']}**",
        "",
        "| Strategy | Final Sharpe | Annualized return | Max DD | Annualized turnover |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, metrics in receipt["test_results"].items():
        lines.append(
            f"| {name} | {metrics['sharpe']:.4f} | {metrics['annualized_return']:.2%} | "
            f"{metrics['max_drawdown']:.2%} | {metrics['annualized_turnover']:.2f} |"
        )
    lines += [
        "",
        "The final fold was opened only after the winning schedule was selected on audit.",
        "No live configuration or library was changed by this run.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_evolution(
        args.snapshot_dir,
        args.library,
        args.config,
        args.output_dir,
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
