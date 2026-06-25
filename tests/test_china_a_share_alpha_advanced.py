"""Advanced tests for china_a_share_alpha: parser, sector mapping, decay, portfolio, LLM mutator."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest
import yaml

from china_a_share_alpha.data.sector_mapping import load_sector_market_cap, merge_sector_market_cap
from china_a_share_alpha.data.synthetic import make_synthetic_panel
from china_a_share_alpha.evolution.llm_mutator import LLMFactorMutator
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.loop.decay_monitor import compute_ic_decay, decay_summary
from china_a_share_alpha.loop.portfolio import PortfolioPopulation
from china_a_share_alpha.run_portfolio_evolution import run as run_portfolio


def test_parse_expression_roundtrip():
    exprs = [
        "ts_mean(close, 5)",
        "cs_rank(ts_mean(return, 10))",
        "neg(cs_rank(ts_mean(return, 5)))",
        "div(sub(close, open), open)",
        "ts_corr(close, volume, 20)",
    ]
    for s in exprs:
        e = parse_expression(s)
        assert str(e) == s


def test_sector_mapping_synthetic():
    df = make_synthetic_panel(n_symbols=20, n_days=50, seed=1)
    df2 = merge_sector_market_cap(df, {})
    assert "sector" in df2.columns
    assert "market_cap" in df2.columns


def test_sector_mapping_csv(tmp_path):
    csv = tmp_path / "sectors.csv"
    csv.write_text("symbol,sector,market_cap\n000001.SZ,银行,1e12\n000002.SZ,房地产,5e11\n", encoding="utf-8")
    mapping = load_sector_market_cap(pd.Index(["000001.SZ", "000002.SZ", "000003.SZ"]), {"sector_csv": str(csv)})
    assert mapping.loc["000001.SZ", "sector"] == "银行"
    assert mapping.loc["000002.SZ", "market_cap"] == 5e11


def test_decay_monitor():
    history = [
        {"best_test_ic": 0.20},
        {"best_test_ic": 0.18},
        {"best_test_ic": 0.15},
        {"best_test_ic": 0.12},
    ]
    slope = compute_ic_decay(history, window=3)
    assert slope < -0.005
    summary = decay_summary(history)
    assert summary["decaying"] is True


def test_llm_mutator_fallback():
    from semas.genome.genome import AgentGenome

    agent = AgentGenome(
        name="factor_miner",
        role="factor_miner",
        system_prompt="test",
        meta={"factor_expression": {"expr": {"type": "var", "name": "close"}}},
    )
    mutator = LLMFactorMutator(seed=42)
    evolved = mutator.mutate_prompt(agent, ["low IC"])
    assert "factor_expression" in evolved.meta


def test_portfolio_population(tmp_path):
    from semas.evaluator.evaluator import Evaluator
    from semas.genome.repository import GenomeRepository

    from china_a_share_alpha.evaluator.metrics import combined_factor_score
    from china_a_share_alpha.factor.expression import Var
    from china_a_share_alpha.factor.parser import parse_expression

    train, test = make_synthetic_panel(n_symbols=30, n_days=100, seed=9, split_date="2020-04-01")
    repo = GenomeRepository(tmp_path / "portfolio_repo")
    evaluator = Evaluator(threshold=0.1)
    evaluator.register_metric("combined_factor_score", combined_factor_score)

    library = [
        parse_expression("cs_rank(ts_mean(return,5))"),
        parse_expression("neg(cs_rank(ts_mean(return,10)))"),
        parse_expression("div(sub(close,open),open)"),
        parse_expression("cs_rank(ts_std(return,5))"),
    ]
    pop = PortfolioPopulation(
        repo=repo,
        train_data=train,
        test_data=test,
        evaluator=evaluator,
        config={"portfolio_population_size": 6, "portfolio_n_factors": 3, "transaction_cost": 0.001},
        factor_library=library,
    )
    pop.seed_population()
    assert len(pop.population) == 6
    evaluated = pop.run_generation()
    assert len(evaluated) == 6
    assert all(c.test_sharpe >= -1e6 for c in evaluated)


def test_run_portfolio_evolution(tmp_path):
    cfg = {
        "data_source": "synthetic",
        "n_symbols": 40,
        "n_days": 120,
        "seed": 11,
        "split_date": "2020-04-01",
        "factor_library_csv": str(Path(__file__).parent.parent / "china_a_share_alpha" / "examples" / "sample_factor_library.csv"),
        "portfolio_library_size": 4,
        "portfolio_population_size": 6,
        "portfolio_n_factors": 3,
        "portfolio_max_generations": 2,
        "portfolio_patience": 2,
        "portfolio_elite_fraction": 0.3,
        "threshold": 0.05,
        "transaction_cost": 0.001,
        "output_dir": str(tmp_path / "portfolio_out"),
        "repo_dir": str(tmp_path / "portfolio_repo2"),
        "portfolio_leaderboard_size": 3,
    }
    config_path = tmp_path / "portfolio_config.yaml"
    config_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    result = run_portfolio(config_path)
    assert "leaderboard" in result
    assert "history" in result
