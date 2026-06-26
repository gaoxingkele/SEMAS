"""Continuous factor mining loop.

Seeds a population of factor expressions, evaluates them on train/test data,
backtests the leaders, and evolves the population until convergence or max
 generations. Outputs a leaderboard and per-generation history.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from semas.evaluator.evaluator import Evaluator
from semas.genome.repository import GenomeRepository

from china_a_share_alpha.data.qlib_loader import load_data
from china_a_share_alpha.evaluator.metrics import combined_factor_score
from china_a_share_alpha.evolution.factor_mutator import FactorMutator
from china_a_share_alpha.evolution.llm_mutator import LLMFactorMutator
from china_a_share_alpha.loop.population import FactorPopulation
from china_a_share_alpha.report.generator import generate_report


def load_config(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_checkpoint(output_dir: Path | None, leaderboard: pd.DataFrame, history: list[dict[str, Any]]) -> None:
    if output_dir is None:
        return
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    leaderboard.to_csv(out / "factor_loop_leaderboard.csv", index=False)
    with open(out / "factor_loop_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False, default=str)


def run(config_path: Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    output_dir = cfg.get("output_dir")
    train_data, test_data = load_data(cfg)

    repo_dir = Path(cfg.get("repo_dir", ".semas_factor_loop_repo"))
    repo_dir.mkdir(parents=True, exist_ok=True)
    repo = GenomeRepository(repo_dir)

    evaluator = Evaluator(threshold=cfg.get("threshold", 0.1))
    evaluator.register_metric("combined_factor_score", combined_factor_score)

    mutator_type = cfg.get("mutator", "gp")
    if mutator_type == "llm":
        mutator = LLMFactorMutator(seed=cfg.get("seed"))
    else:
        mutator = FactorMutator(seed=cfg.get("seed"), mode=mutator_type)

    pop = FactorPopulation(
        repo=repo,
        train_data=train_data,
        test_data=test_data,
        evaluator=evaluator,
        mutator=mutator,
        config=cfg,
    )
    pop.seed_population()

    while not pop.is_converged():
        evaluated = pop.run_generation()
        best = max(evaluated, key=lambda c: c.test_ic)
        print(
            f"Gen {pop._generation - 1:02d}: best_train_ic={best.train_ic:.4f}  "
            f"best_test_ic={best.test_ic:.4f}  expr={best.expression}"
        )
        # Checkpoint after every generation so partial results are preserved.
        _write_checkpoint(
            output_dir,
            pop.leaderboard(n=cfg.get("leaderboard_size", 10)),
            pop.history,
        )

    leaderboard = pop.leaderboard(n=cfg.get("leaderboard_size", 10))
    history = pop.history

    # Build a summary result compatible with the report generator.
    top_candidate = None
    for cand in pop.archive:
        if top_candidate is None or cand.test_ic > top_candidate.test_ic:
            top_candidate = cand

    top = leaderboard.iloc[0].to_dict() if not leaderboard.empty else {}
    result = {
        "passed": bool(top.get("test_ic", 0.0) >= cfg.get("threshold", 0.1)),
        "final_score": top.get("train_score", 0.0),
        "train_ic": top.get("train_ic", 0.0),
        "train_rank_ic": top.get("test_rank_ic", 0.0),
        "test_ic": top.get("test_ic", 0.0),
        "test_rank_ic": top.get("test_rank_ic", 0.0),
        "expression": top.get("expression", ""),
        "train_backtest": top_candidate.backtest_train if top_candidate else {},
        "test_backtest": top_candidate.backtest_test if top_candidate else {},
        "rounds": len(history),
    }

    if output_dir:
        report_path = generate_report(result, cfg, Path(output_dir))
        print(f"Leaderboard: {Path(output_dir) / 'factor_loop_leaderboard.csv'}")
        print(f"History: {Path(output_dir) / 'factor_loop_history.json'}")
        print(f"Report: {report_path}")

    return {
        "leaderboard": leaderboard.to_dict(orient="records"),
        "history": history,
        "best": top,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuous China A-share alpha factor mining loop")
    parser.add_argument("config", type=Path, help="Path to a YAML config")
    args = parser.parse_args()

    result = run(args.config)
    print(json.dumps(result["best"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
