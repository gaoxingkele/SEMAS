"""Run the enhanced factor evolution loop on Tushare data.

Uses EnhancedFactorMutator (richer grammar) and EnhancedFactorPopulation
(Sharpe-based selection) instead of the base IC-only loop.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.evolution.enhanced_factor_mutator import EnhancedFactorMutator
from china_a_share_alpha.executor import create_factor_executor
from china_a_share_alpha.loop.enhanced_population import EnhancedFactorPopulation
from china_a_share_alpha.evaluator.metrics import combined_factor_score
from semas.evaluator.evaluator import Evaluator
from semas.genome.repository import GenomeRepository


def run_enhanced_config(cfg: dict) -> dict:
    """Run one enhanced evolution seed and return best result summary."""
    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = Path(cfg.get("repo_dir", str(output_dir / ".semas_repo")))
    repo_dir.mkdir(parents=True, exist_ok=True)

    train, test = load_tushare_data(cfg)
    repo = GenomeRepository(str(repo_dir))
    mutator = EnhancedFactorMutator(seed=cfg.get("seed", 42), mode="gp")
    evaluator = Evaluator(threshold=cfg.get("threshold", 0.1))
    evaluator.register_metric("combined_factor_score", combined_factor_score)

    population = EnhancedFactorPopulation(
        repo=repo,
        train_data=train,
        test_data=test,
        evaluator=evaluator,
        mutator=mutator,
        config=cfg,
    )
    population.seed_population()

    while not population.is_converged():
        print(f"Generation {population._generation}")
        population.run_generation()

    leaderboard = population.leaderboard(n=cfg.get("leaderboard_size", 50))
    lb_path = output_dir / "factor_loop_leaderboard.csv"
    leaderboard.to_csv(lb_path, index=False)

    history_path = output_dir / "factor_loop_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(population.history, f, indent=2, ensure_ascii=False, default=str)

    report_path = output_dir / f"factor_report_{os.path.basename(output_dir)}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best": leaderboard.iloc[0].to_dict(),
                "history": population.history,
                "config": cfg,
            },
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return {"best": leaderboard.iloc[0].to_dict(), "leaderboard_path": str(lb_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if args.output_dir:
        cfg["output_dir"] = str(args.output_dir)
    if args.seed is not None:
        cfg["seed"] = args.seed

    result = run_enhanced_config(cfg)
    print("Enhanced evolution completed.")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
