"""Evolve optimal combination weights over a set of existing alpha factors.

This searches the *portfolio-weight space* rather than the expression space.
Each candidate is a vector of weights; the objective is Sharpe of the combined
long-short portfolio, with turnover and drawdown penalties.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


class WeightCandidate:
    """One weight vector plus its evaluated metrics."""

    def __init__(self, weights: np.ndarray, generation: int = 0):
        self.weights = weights
        self.generation = generation
        self.fitness = -np.inf
        self.sharpe = 0.0
        self.ic = 0.0
        self.mdd = 0.0
        self.turnover = 0.0
        self.cost_adj_return = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "weights": self.weights.tolist(),
            "generation": self.generation,
            "fitness": self.fitness,
            "sharpe": self.sharpe,
            "ic": self.ic,
            "mdd": self.mdd,
            "turnover": self.turnover,
            "cost_adj_return": self.cost_adj_return,
        }


def evaluate_weights(
    weights: np.ndarray,
    factor_matrix: pd.DataFrame,
    forward: pd.Series,
    generation: int = 0,
) -> WeightCandidate:
    """Evaluate one weight vector on train data."""
    cand = WeightCandidate(weights, generation)

    # Combine z-scored factors with weights.
    combined = pd.Series(0.0, index=factor_matrix.index)
    for i, col in enumerate(factor_matrix.columns):
        combined = combined + weights[i] * _zscore(factor_matrix[col])

    # Avoid extreme concentration.
    combined = combined.clip(-5, 5)

    from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score

    cand.ic = ic_score(combined, forward)
    cand.turnover = turnover_score(combined)
    bt = run_long_short_backtest(combined, forward, transaction_cost=0.001)
    cand.sharpe = bt.get("sharpe", 0.0)
    cand.mdd = bt.get("max_drawdown", 0.0)
    cand.cost_adj_return = bt.get("cost_adjusted_return", 0.0)

    # Fitness: Sharpe primary, cost-adjusted return secondary, penalize turnover/mdd.
    if not np.isfinite(cand.sharpe):
        cand.sharpe = 0.0
    cand.fitness = (
        0.5 * cand.sharpe
        + 0.25 * cand.cost_adj_return
        + 0.15 * abs(cand.ic)
        - 0.05 * cand.turnover
        - 0.05 * max(0.0, -cand.mdd)
    )
    return cand


def _random_weights(n: int) -> np.ndarray:
    """Random normalized weights in [-1, 1]."""
    w = np.random.uniform(-1, 1, size=n)
    norm = np.sum(np.abs(w)) + 1e-8
    return w / norm


def _mutate_weights(weights: np.ndarray, scale: float = 0.2) -> np.ndarray:
    """Perturb a few weights and re-normalize."""
    w = weights.copy()
    n = len(w)
    n_mutate = max(1, int(n * 0.3))
    idx = np.random.choice(n, size=n_mutate, replace=False)
    w[idx] = w[idx] + np.random.normal(0, scale, size=n_mutate)
    # Sparsity: randomly zero out small weights.
    w[np.abs(w) < 0.05] = 0.0
    norm = np.sum(np.abs(w)) + 1e-8
    return w / norm


def _crossover_weights(w1: np.ndarray, w2: np.ndarray) -> np.ndarray:
    """BLX-alpha style crossover."""
    alpha = 0.3
    low = np.minimum(w1, w2) - alpha * np.abs(w1 - w2)
    high = np.maximum(w1, w2) + alpha * np.abs(w1 - w2)
    child = np.random.uniform(low, high)
    norm = np.sum(np.abs(child)) + 1e-8
    return child / norm


def run_weight_evolution(
    cfg: dict[str, Any],
    factor_matrix_train: pd.DataFrame,
    forward_train: pd.Series,
) -> dict[str, Any]:
    """Run a genetic algorithm in weight space."""
    n_factors = factor_matrix_train.shape[1]
    pop_size = cfg.get("population_size", 50)
    max_gen = cfg.get("max_generations", 30)
    patience = cfg.get("patience", 5)
    elite_frac = cfg.get("elite_fraction", 0.2)
    crossover_frac = cfg.get("crossover_fraction", 0.4)

    n_elites = max(1, int(pop_size * elite_frac))
    n_crossover = int(pop_size * crossover_frac)
    n_mutate = pop_size - n_elites - n_crossover

    random.seed(cfg.get("seed", 42))
    np.random.seed(cfg.get("seed", 42))

    population = [evaluate_weights(_random_weights(n_factors), factor_matrix_train, forward_train, 0) for _ in range(pop_size)]
    archive = population[:]

    best_fitness = -np.inf
    gens_without_improvement = 0
    history = []

    for gen in range(max_gen):
        population.sort(key=lambda c: c.fitness, reverse=True)
        elites = population[:n_elites]

        if elites[0].fitness > best_fitness + 1e-6:
            best_fitness = elites[0].fitness
            gens_without_improvement = 0
        else:
            gens_without_improvement += 1

        history.append({
            "generation": gen,
            "best_fitness": elites[0].fitness,
            "best_sharpe": elites[0].sharpe,
            "best_ic": elites[0].ic,
            "mean_fitness": float(np.mean([c.fitness for c in population])),
        })
        print(
            f"Gen {gen:02d}: best_fitness={elites[0].fitness:.4f} "
            f"sharpe={elites[0].sharpe:.4f} ic={elites[0].ic:.4f} "
            f"turnover={elites[0].turnover:.4f}"
        )

        next_pop = elites[:]

        # Mutate elites.
        for _ in range(n_mutate):
            parent = random.choice(elites)
            child_w = _mutate_weights(parent.weights)
            next_pop.append(evaluate_weights(child_w, factor_matrix_train, forward_train, gen + 1))

        # Crossover among elites.
        for _ in range(n_crossover):
            if len(elites) >= 2:
                p1, p2 = random.sample(elites, 2)
                child_w = _crossover_weights(p1.weights, p2.weights)
                next_pop.append(evaluate_weights(child_w, factor_matrix_train, forward_train, gen + 1))

        population = next_pop[:pop_size]
        archive.extend(population)

        if gens_without_improvement >= patience:
            print(f"Converged after {gen + 1} generations.")
            break

    archive.sort(key=lambda c: c.fitness, reverse=True)
    best = archive[0]

    return {
        "best": best.to_dict(),
        "factor_names": factor_matrix_train.columns.tolist(),
        "history": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config path")
    parser.add_argument("--factor-csv", type=Path, required=True, help="CSV with columns factor,expression,group")
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/portfolio_weight_evolution"))
    parser.add_argument("--top-n", type=int, default=10, help="Use top N factors from CSV")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load data.
    train, test = load_tushare_data(cfg)

    # Load factor library and pick top N by test_ic.
    lib = pd.read_csv(args.factor_csv)
    lib = lib.sort_values("test_ic", ascending=False).head(args.top_n)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")
    if "group" not in lib.columns:
        lib["group"] = "evolved"

    # Evaluate each base factor on train data.
    factor_frames = []
    for _, row in lib.iterrows():
        expr = parse_expression(row["expression"])
        try:
            f_train = expr.eval(train)
            factor_frames.append(f_train.rename(row["factor"]))
        except Exception as exc:
            print(f"Skipping {row['factor']}: {exc}")

    factor_matrix_train = pd.concat(factor_frames, axis=1)
    factor_matrix_train = factor_matrix_train.dropna()
    forward_train = train["forward_return"].loc[factor_matrix_train.index]

    # Run evolution.
    result = run_weight_evolution(cfg, factor_matrix_train, forward_train)

    # Save outputs.
    with open(args.output_dir / "weight_evolution_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    weights = pd.DataFrame({
        "factor": result["factor_names"],
        "weight": result["best"]["weights"],
    })
    weights = weights[weights["weight"].abs() > 0.001].sort_values("weight", ascending=False)
    weights.to_csv(args.output_dir / "weights.csv", index=False)
    print("\nTop weights:")
    print(weights.to_string(index=False))

    # Test-set evaluation of best combination.
    factor_frames_test = []
    for _, row in lib.iterrows():
        expr = parse_expression(row["expression"])
        try:
            f_test = expr.eval(test)
            factor_frames_test.append(f_test.rename(row["factor"]))
        except Exception as exc:
            print(f"Skipping test {row['factor']}: {exc}")
    factor_matrix_test = pd.concat(factor_frames_test, axis=1).dropna()
    forward_test = test["forward_return"].loc[factor_matrix_test.index]

    best_w = np.array(result["best"]["weights"])
    combined_test = pd.Series(0.0, index=factor_matrix_test.index)
    for i, col in enumerate(factor_matrix_test.columns):
        combined_test = combined_test + best_w[i] * _zscore(factor_matrix_test[col])
    combined_test = combined_test.clip(-5, 5)
    bt_test = run_long_short_backtest(combined_test, forward_test, transaction_cost=0.001)
    print("\nTest-set backtest:")
    print(json.dumps(bt_test, indent=2, ensure_ascii=False, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
