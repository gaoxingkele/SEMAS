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
from china_a_share_alpha.evaluator.metrics import combined_factor_score, ic_score, rank_ic_score
from china_a_share_alpha.evolution.factor_mutator import FactorMutator
from china_a_share_alpha.executor import create_factor_executor


def load_config(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(config_path: Path, max_rounds: int = 5) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="china_a_share_alpha_"))
    try:
        repo = GenomeRepository(tmp)
        cfg = load_config(config_path)
        data = load_data(cfg)

        initial_expr = cfg.get("initial_expression", {"type": "var", "name": "close"})
        agent = AgentGenome(
            name="factor_miner",
            role="factor_miner",
            system_prompt="Evolve a formulaic alpha factor for China A-shares.",
            meta={
                "domain": "china_a_share_alpha",
                "factor_expression": {"expr": initial_expr, "string": ""},
            },
        )
        repo.save_agent(agent)

        evaluator = Evaluator(threshold=cfg.get("threshold", 0.1))
        evaluator.register_metric("combined_factor_score", combined_factor_score)

        executor = create_factor_executor(data)

        orch = Orchestrator(
            repository=repo,
            evaluator=evaluator,
            mutator=FactorMutator(seed=cfg.get("seed")),
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
            print(f"Round {round_idx}: score={score:.4f}  IC={ic:.4f}  RankIC={rank_ic:.4f}  expr={trace.task_output.get('expression_string', '')}")
            if trace.evaluation.passed:
                break

        factor = best_trace.task_output["factor"]
        forward_return = best_trace.task_output["forward_return"]
        bt = run_long_short_backtest(factor, forward_return)

        return {
            "passed": best_trace.evaluation.passed,
            "final_score": best_trace.evaluation.score,
            "ic": ic_score(factor, forward_return),
            "rank_ic": rank_ic_score(factor, forward_return),
            "expression": best_trace.task_output.get("expression_string", ""),
            "backtest": {
                "annualized_return": bt["annualized_return"],
                "sharpe": bt["sharpe"],
                "max_drawdown": bt["max_drawdown"],
            },
            "rounds": round_idx,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evolve a China A-share alpha factor")
    parser.add_argument("config", type=Path, help="Path to a YAML config")
    parser.add_argument("--max-rounds", type=int, default=5, help="Max evolution rounds")
    args = parser.parse_args()

    result = run(args.config, max_rounds=args.max_rounds)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
