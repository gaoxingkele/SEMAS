"""Generate and evaluate a batch of LLM-proposed factor expressions.

Reads an optional seed library, asks an LLM to propose variants, evaluates each
on train/test, and writes a leaderboard CSV compatible with the factor loop.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.evaluator.metrics import ic_score
from china_a_share_alpha.evolution.llm_mutator import LLMFactorMutator
from china_a_share_alpha.factor.expression import expr_to_dict
from semas.genome.genome import AgentGenome


def _load_seeds(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return ["return"]
    df = pd.read_csv(path)
    return df["expression"].dropna().unique().tolist() if "expression" in df.columns else ["return"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config")
    parser.add_argument("--seed-library", type=Path, default=None)
    parser.add_argument("--n-generate", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    train, test = load_tushare_data(cfg)
    seeds = _load_seeds(args.seed_library)

    mutator = LLMFactorMutator(seed=args.seed)
    rows = []
    for i in range(args.n_generate):
        seed_expr_str = random.choice(seeds)
        agent = AgentGenome(
            name="factor",
            role="alpha",
            system_prompt="You are a quantitative alpha factor engineer.",
            meta={
                "factor_expression": {
                    "expr": expr_to_dict(__import__(
                        "china_a_share_alpha.factor.parser", fromlist=["parse_expression"]
                    ).parse_expression(seed_expr_str)),
                    "string": seed_expr_str,
                }
            },
        )
        try:
            evolved = mutator.mutate_prompt(agent, [])
            expr_str = evolved.meta.get("factor_expression", {}).get("string")
            if not expr_str:
                continue
            expr = __import__("china_a_share_alpha.factor.parser", fromlist=["parse_expression"]).parse_expression(expr_str)
            f_train = expr.eval(train)
            f_test = expr.eval(test)
            train_ic = ic_score(f_train, train["forward_return"])
            test_ic = ic_score(f_test, test["forward_return"])
            bt = run_long_short_backtest(f_test, test["forward_return"], transaction_cost=cfg.get("transaction_cost", 0.001))
            rows.append(
                {
                    "factor": f"llm_{i}",
                    "expression": expr_str,
                    "train_ic": train_ic,
                    "test_ic": test_ic,
                    "test_sharpe": bt.get("sharpe", 0.0),
                    "test_cost_adj_return": bt.get("cost_adjusted_return", 0.0),
                }
            )
            print(f"  {i}: {expr_str} | train_ic={train_ic:.4f} test_sharpe={bt.get('sharpe',0):.3f}")
        except Exception as exc:
            print(f"  {i}: skipped ({exc})")

    if rows:
        df = pd.DataFrame(rows).sort_values("test_sharpe", ascending=False)
        df["rank"] = range(1, len(df) + 1)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} LLM-generated factors to {args.output}")
    else:
        print("No valid LLM factors generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
