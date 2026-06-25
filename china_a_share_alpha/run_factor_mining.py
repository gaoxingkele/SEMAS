"""High-level runner that evolves a China A-share alpha factor."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository
from semas.orchestrator.orchestrator import Orchestrator
from semas.sandbox.sandbox import Sandbox

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.qlib_loader import load_data
from china_a_share_alpha.evaluator.metrics import (
    combined_factor_score,
    ic_score,
    rank_ic_score,
)
from china_a_share_alpha.evolution.factor_mutator import FactorMutator
from china_a_share_alpha.executor import create_factor_executor
from china_a_share_alpha.report.generator import generate_report


def load_config(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(
    config_path: Path,
    max_rounds: int = 5,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="china_a_share_alpha_"))
    try:
        repo = GenomeRepository(tmp)
        cfg = load_config(config_path)
        train_data, test_data = load_data(cfg)
        output_dir = output_dir or cfg.get("output_dir")

        initial_expr = cfg.get("initial_expression", {"type": "var", "name": "close"})
        agent = AgentGenome(
            name="factor_miner",
            role="factor_miner",
            system_prompt="Evolve a formulaic alpha factor for China A-shares.",
            meta={
                "domain": "china_a_share_alpha",
                "factor_expression": {"expr": initial_expr, "string": "", "stage": 0},
            },
        )
        repo.save_agent(agent)

        evaluator = Evaluator(threshold=cfg.get("threshold", 0.1))
        evaluator.register_metric("combined_factor_score", combined_factor_score)

        executor = create_factor_executor(train_data, test_data, cfg)

        mutator_type = cfg.get("mutator", "seed")
        mutator = FactorMutator(seed=cfg.get("seed"), mode=mutator_type)

        orch = Orchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=mutator,
            sandbox=Sandbox(),
            agent_name="factor_miner",
            executor=executor,
            cooldown_tasks=0,
        )

        best_trace = None
        for round_idx in range(max_rounds + 1):
            trace = orch.run_task({})
            best_trace = trace
            score = trace.evaluation.score
            ic = ic_score(trace.task_output["factor"], trace.task_output["forward_return"])
            rank_ic = rank_ic_score(trace.task_output["factor"], trace.task_output["forward_return"])
            print(
                f"Round {round_idx}: score={score:.4f}  "
                f"train_IC={ic:.4f}  train_RankIC={rank_ic:.4f}  "
                f"expr={trace.task_output.get('expression_string', '')}"
            )
            if trace.evaluation.passed:
                break

        # Final evaluation on the held-out test set.
        test_factor = best_trace.task_output["factor_test"]
        test_forward_return = best_trace.task_output["forward_return_test"]
        test_ic = ic_score(test_factor, test_forward_return)
        test_rank_ic = rank_ic_score(test_factor, test_forward_return)

        train_factor = best_trace.task_output["factor"]
        train_forward_return = best_trace.task_output["forward_return"]
        txn_cost = cfg.get("transaction_cost", 0.001)
        train_bt = run_long_short_backtest(train_factor, train_forward_return, transaction_cost=txn_cost)
        test_bt = run_long_short_backtest(test_factor, test_forward_return, transaction_cost=txn_cost)

        return {
            "passed": best_trace.evaluation.passed,
            "final_score": best_trace.evaluation.score,
            "train_ic": ic_score(train_factor, train_forward_return),
            "train_rank_ic": rank_ic_score(train_factor, train_forward_return),
            "test_ic": test_ic,
            "test_rank_ic": test_rank_ic,
            "expression": best_trace.task_output.get("expression_string", ""),
            "train_backtest": {
                "annualized_return": train_bt["annualized_return"],
                "sharpe": train_bt["sharpe"],
                "max_drawdown": train_bt["max_drawdown"],
                "turnover": train_bt["turnover"],
                "cost": train_bt["cost"],
                "cost_adjusted_return": train_bt["cost_adjusted_return"],
            },
            "test_backtest": {
                "annualized_return": test_bt["annualized_return"],
                "sharpe": test_bt["sharpe"],
                "max_drawdown": test_bt["max_drawdown"],
                "turnover": test_bt["turnover"],
                "cost": test_bt["cost"],
                "cost_adjusted_return": test_bt["cost_adjusted_return"],
            },
            "rounds": round_idx,
        }

        if output_dir:
            report_path = generate_report(result, cfg, Path(output_dir))
            print(f"Report written to: {report_path}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evolve a China A-share alpha factor")
    parser.add_argument("config", type=Path, help="Path to a YAML config")
    parser.add_argument("--max-rounds", type=int, default=5, help="Max evolution rounds")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory to write factor report")
    args = parser.parse_args()

    result = run(args.config, max_rounds=args.max_rounds, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
