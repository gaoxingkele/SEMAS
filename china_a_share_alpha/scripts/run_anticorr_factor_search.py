"""Anti-correlation factor search.

Generates random expressions and rewards those that have decent predictive
power while being uncorrelated (or negatively correlated) with the current live
library combined signal.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.evaluator.metrics import ic_score
from china_a_share_alpha.evolution.enhanced_factor_mutator import EnhancedFactorMutator
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _live_signal(library_path: Path, data: pd.DataFrame) -> pd.Series:
    """Equal-weight combined signal from a factor library CSV."""
    df = pd.read_csv(library_path)
    frames = []
    for _, row in df.iterrows():
        try:
            f = _zscore(parse_expression(row["expression"]).eval(data))
            frames.append(f)
        except Exception:
            pass
    if not frames:
        return pd.Series(0.0, index=data.index)
    mat = pd.concat(frames, axis=1).dropna()
    return mat.mean(axis=1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config")
    parser.add_argument("--live-library", type=Path, required=True)
    parser.add_argument("--n-generate", type=int, default=100)
    parser.add_argument("--corr-penalty", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    train, test = load_tushare_data(cfg)
    live_train = _live_signal(args.live_library, train)
    live_test = _live_signal(args.live_library, test)

    mutator = EnhancedFactorMutator(seed=args.seed, mode="gp")
    rows = []
    for i in range(args.n_generate):
        try:
            agent = mutator.mutate_prompt(
                __import__("semas.genome.genome", fromlist=["AgentGenome"]).AgentGenome(
                    name="factor",
                    role="alpha",
                    system_prompt="You are a factor.",
                ),
                [],
            )
            expr_str = agent.meta.get("factor_expression", {}).get("string")
            if not expr_str:
                continue
            expr = parse_expression(expr_str)
            f_train = expr.eval(train)
            f_test = expr.eval(test)
            if f_train.std() < 1e-12 or f_test.std() < 1e-12:
                continue
            train_ic = ic_score(f_train, train["forward_return"])
            test_ic = ic_score(f_test, test["forward_return"])
            bt = run_long_short_backtest(f_test, test["forward_return"], transaction_cost=cfg.get("transaction_cost", 0.001))
            corr_train = float(f_train.corr(live_train, method="spearman"))
            score = abs(train_ic) - args.corr_penalty * abs(corr_train)
            rows.append(
                {
                    "factor": f"anticorr_{i}",
                    "expression": expr_str,
                    "train_ic": train_ic,
                    "test_ic": test_ic,
                    "corr_with_live": corr_train,
                    "score": score,
                    "test_sharpe": bt.get("sharpe", 0.0),
                    "test_cost_adj_return": bt.get("cost_adjusted_return", 0.0),
                }
            )
            print(f"  {i}: score={score:.4f} train_ic={train_ic:.4f} corr={corr_train:.3f} test_sharpe={bt.get('sharpe',0):.3f}")
        except Exception as exc:
            print(f"  {i}: skipped ({exc})")

    if rows:
        df = pd.DataFrame(rows).sort_values("score", ascending=False)
        df["rank"] = range(1, len(df) + 1)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} anti-correlation candidates to {args.output}")
    else:
        print("No valid candidates generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
