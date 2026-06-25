"""Tests for the China A-Share Alpha Evolver scaffold."""

from __future__ import annotations

import pandas as pd

from china_a_share_alpha.data.synthetic import make_synthetic_panel
from china_a_share_alpha.evaluator.metrics import (
    combined_factor_score,
    ic_score,
    long_short_return,
    rank_ic_score,
)
from china_a_share_alpha.evolution.factor_mutator import FactorMutator
from china_a_share_alpha.executor import create_factor_executor
from china_a_share_alpha.factor.expression import (
    BinaryOp,
    RollingOp,
    UnaryOp,
    Var,
)
from china_a_share_alpha.run_factor_mining import run
from semas.genome.genome import AgentGenome


def test_synthetic_data_has_forward_return():
    df = make_synthetic_panel(n_symbols=20, n_days=50, seed=1)
    assert "forward_return" in df.columns
    assert not df["forward_return"].isna().all()


def test_factor_expression_evaluation():
    df = make_synthetic_panel(n_symbols=20, n_days=50, seed=1)
    expr = UnaryOp("cs_rank", RollingOp("ts_mean", Var("close"), 5))
    series = expr.eval(df)
    assert isinstance(series, pd.Series)
    assert len(series) == len(df)


def test_ic_metrics():
    df = make_synthetic_panel(n_symbols=30, n_days=100, seed=2)
    expr = UnaryOp("cs_rank", RollingOp("ts_mean", Var("close"), 5))
    factor = expr.eval(df)
    ic = ic_score(factor, df["forward_return"])
    rank_ic = rank_ic_score(factor, df["forward_return"])
    assert -1.0 <= ic <= 1.0
    assert -1.0 <= rank_ic <= 1.0


def test_combined_factor_score():
    df = make_synthetic_panel(n_symbols=30, n_days=100, seed=3)
    expr = UnaryOp("cs_rank", RollingOp("ts_mean", Var("close"), 5))
    factor = expr.eval(df)
    score = combined_factor_score({"factor": factor, "forward_return": df["forward_return"]})
    assert 0.0 <= score <= 1.0


def test_long_short_return():
    df = make_synthetic_panel(n_symbols=40, n_days=100, seed=4)
    expr = UnaryOp("cs_rank", RollingOp("ts_mean", Var("close"), 5))
    factor = expr.eval(df)
    ann_ret, sharpe = long_short_return(factor, df["forward_return"])
    assert isinstance(ann_ret, float)
    assert isinstance(sharpe, float)


def test_factor_mutator_changes_expression():
    agent = AgentGenome(
        name="factor_miner",
        role="factor_miner",
        system_prompt="Evolve factor",
        meta={
            "factor_expression": {
                "expr": {"type": "var", "name": "close"},
                "string": "close",
            }
        },
    )
    mutator = FactorMutator(seed=42)
    evolved = mutator.mutate_prompt(agent, ["low IC"])
    assert evolved.meta["factor_expression"]["string"] != "close"


def test_executor_runs_agent():
    df = make_synthetic_panel(n_symbols=20, n_days=50, seed=5)
    agent = AgentGenome(
        name="factor_miner",
        role="factor_miner",
        system_prompt="test",
        meta={
            "factor_expression": {
                "expr": {"type": "var", "name": "close"},
                "string": "close",
            }
        },
    )
    executor = create_factor_executor(df)
    out = executor(agent, {})
    assert "factor" in out
    assert "forward_return" in out


def test_run_factor_mining():
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "china_a_share_alpha" / "examples" / "sample_config.yaml"
    result = run(config_path, max_rounds=2)
    assert "final_score" in result
    assert "ic" in result
