"""Tests for the continuous factor mining loop."""

from __future__ import annotations

import shutil
from pathlib import Path

from semas.evaluator.evaluator import Evaluator
from semas.genome.repository import GenomeRepository

from china_a_share_alpha.data.synthetic import make_synthetic_panel
from china_a_share_alpha.evaluator.metrics import combined_factor_score
from china_a_share_alpha.evolution.factor_mutator import FactorMutator
from china_a_share_alpha.loop.population import FactorPopulation
from china_a_share_alpha.run_factor_loop import run


def test_factor_population_seeds_and_evolve():
    train, test = make_synthetic_panel(
        n_symbols=40, n_days=120, seed=7, split_date="2020-04-01"
    )
    repo = GenomeRepository(Path(".tmp_test_loop_repo"))
    evaluator = Evaluator(threshold=0.1)
    evaluator.register_metric("combined_factor_score", combined_factor_score)
    mutator = FactorMutator(seed=7, mode="gp")

    pop = FactorPopulation(
        repo=repo,
        train_data=train,
        test_data=test,
        evaluator=evaluator,
        mutator=mutator,
        config={
            "population_size": 8,
            "transaction_cost": 0.001,
        },
    )
    pop.seed_population()
    assert len(pop.population) == 8

    evaluated = pop.run_generation()
    assert len(evaluated) == 8
    assert all(-1.0 <= c.test_ic <= 1.0 for c in evaluated)

    shutil.rmtree(".tmp_test_loop_repo", ignore_errors=True)


def test_run_factor_loop(tmp_path):
    import yaml

    cfg = {
        "data_source": "synthetic",
        "n_symbols": 40,
        "n_days": 120,
        "seed": 7,
        "split_date": "2020-04-01",
        "population_size": 6,
        "max_generations": 2,
        "patience": 2,
        "elite_fraction": 0.3,
        "crossover_fraction": 0.2,
        "mutator": "gp",
        "threshold": 0.05,
        "transaction_cost": 0.001,
        "output_dir": str(tmp_path / "loop_out"),
        "repo_dir": str(tmp_path / "loop_repo"),
        "leaderboard_size": 5,
    }
    config_path = tmp_path / "loop_config.yaml"
    config_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    result = run(config_path)
    assert "leaderboard" in result
    assert "history" in result
    assert "best" in result
    assert result["best"]["test_ic"] >= -1.0
