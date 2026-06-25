"""Multi-factor portfolio evolution runner.

Takes a factor library (e.g. the leaderboard CSV from `run_factor_loop.py`),
seeds portfolios as weighted combinations of factors, and evolves the weights
(and factor membership) to maximize out-of-sample Sharpe ratio.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from semas.evaluator.evaluator import Evaluator
from semas.genome.repository import GenomeRepository

from china_a_share_alpha.data.qlib_loader import load_data
from china_a_share_alpha.evaluator.metrics import combined_factor_score
from china_a_share_alpha.factor.expression import expr_from_dict
from china_a_share_alpha.loop.portfolio import PortfolioPopulation


def load_config(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_factor_library(config: dict[str, Any]) -> list:
    """Load top factor expressions from a CSV leaderboard."""
    library_path = config.get("factor_library_csv")
    if not library_path or not Path(library_path).exists():
        raise FileNotFoundError(
            f"Factor library CSV not found: {library_path}. "
            "Run `run_factor_loop.py` first or provide a CSV with an 'expression' column."
        )

    df = pd.read_csv(library_path)
    if "expression" not in df.columns:
        raise ValueError("Factor library CSV must contain an 'expression' column.")

    # Parse expression strings. Only keep parseable ones.
    from china_a_share_alpha.factor.parser import parse_expression

    expressions = []
    for expr_str in df["expression"].head(config.get("portfolio_library_size", 20)):
        try:
            expressions.append(parse_expression(expr_str))
        except Exception:
            continue
    if len(expressions) < 2:
        raise ValueError("Need at least 2 parseable factors in the library.")
    return expressions


def run(config_path: Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    train_data, test_data = load_data(cfg)

    factor_library = load_factor_library(cfg)

    repo_dir = Path(cfg.get("repo_dir", ".semas_portfolio_repo"))
    repo_dir.mkdir(parents=True, exist_ok=True)
    repo = GenomeRepository(repo_dir)

    evaluator = Evaluator(threshold=cfg.get("threshold", 0.1))
    evaluator.register_metric("combined_factor_score", combined_factor_score)

    pop = PortfolioPopulation(
        repo=repo,
        train_data=train_data,
        test_data=test_data,
        evaluator=evaluator,
        config=cfg,
        factor_library=factor_library,
    )
    pop.seed_population()

    while not pop.is_converged():
        evaluated = pop.run_generation()
        best = max(evaluated, key=lambda c: c.test_sharpe)
        print(
            f"Gen {pop._generation - 1:02d}: best_train_sharpe={best.train_sharpe:.3f}  "
            f"best_test_sharpe={best.test_sharpe:.3f}  n_factors={len(best.weights)}"
        )

    leaderboard = pop.leaderboard(n=cfg.get("portfolio_leaderboard_size", 5))
    output_dir = cfg.get("output_dir")
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        leaderboard_path = out / "portfolio_leaderboard.csv"
        leaderboard.to_csv(leaderboard_path, index=False)
        history_path = out / "portfolio_history.json"
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(pop.history, f, indent=2, ensure_ascii=False, default=str)
        print(f"Portfolio leaderboard: {leaderboard_path}")
        print(f"Portfolio history: {history_path}")

    return {
        "leaderboard": leaderboard.to_dict(orient="records"),
        "history": pop.history,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evolve multi-factor portfolio weights")
    parser.add_argument("config", type=Path, help="Path to a YAML config")
    args = parser.parse_args()

    result = run(args.config)
    print(json.dumps(result["leaderboard"][:1], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
