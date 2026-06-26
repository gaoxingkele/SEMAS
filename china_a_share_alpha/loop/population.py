"""Population-based factor evolution loop.

Runs a genetic-programming style outer loop on top of SEMAS components:
seed an initial population, evaluate on train/test, select elites, mutate
and crossover, and stop on convergence or overfit.
"""

from __future__ import annotations

import copy
import random
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from semas.evaluator.evaluator import Evaluator
from semas.genome.genome import AgentGenome
from semas.genome.repository import GenomeRepository

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.evaluator.metrics import (
    combined_factor_score,
    ic_score,
    rank_ic_score,
    turnover_score,
)
from china_a_share_alpha.evolution.factor_mutator import FactorMutator, _random_expression
from china_a_share_alpha.executor import create_factor_executor
from china_a_share_alpha.factor.expression import (
    BinaryOp,
    RollingOp,
    UnaryOp,
    Var,
    expr_from_dict,
    expr_to_dict,
)


@dataclass
class FactorCandidate:
    """One evaluated factor agent plus its metrics."""

    agent: AgentGenome
    generation: int
    train_score: float = 0.0
    train_ic: float = 0.0
    train_rank_ic: float = 0.0
    test_ic: float = 0.0
    test_rank_ic: float = 0.0
    turnover: float = 0.0
    backtest_train: dict[str, Any] = field(default_factory=dict)
    backtest_test: dict[str, Any] = field(default_factory=dict)
    candidate_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def expression(self) -> str:
        return self.agent.meta.get("factor_expression", {}).get("string", "")


class FactorPopulation:
    """Outer GP loop for alpha factor discovery."""

    def __init__(
        self,
        repo: GenomeRepository,
        train_data: pd.DataFrame,
        test_data: pd.DataFrame,
        evaluator: Evaluator,
        mutator: FactorMutator,
        config: dict[str, Any],
    ):
        self.repo = repo
        self.train_data = train_data
        self.test_data = test_data
        self.evaluator = evaluator
        self.mutator = mutator
        self.config = config
        self.population: list[AgentGenome] = []
        self.archive: list[FactorCandidate] = []
        self.history: list[dict[str, Any]] = []
        self._executor = create_factor_executor(
            train_data, test_data, config
        )
        self._generation = 0
        self._best_test_ic = -1.0
        self._generations_without_improvement = 0

    def seed_population(self) -> None:
        """Create the initial population from seeds, Alpha101, and random trees."""
        pop_size = self.config.get("population_size", 20)
        seeds: list[AgentGenome] = []

        # Raw variable baselines.
        for var in ["open", "high", "low", "close", "volume", "vwap", "return"]:
            seeds.append(self._make_agent(Var(var), generation=0))

        # A few classic expressions.
        seeds.append(
            self._make_agent(
                UnaryOp("neg", UnaryOp("cs_rank", RollingOp("ts_mean", Var("return"), 5))),
                generation=0,
            )
        )
        seeds.append(
            self._make_agent(
                UnaryOp(
                    "cs_rank",
                    RollingOp("ts_mean", BinaryOp("div", BinaryOp("sub", Var("close"), Var("open")), Var("open")), 5),
                ),
                generation=0,
            )
        )

        # Random grammar-based expressions.
        random.seed(self.config.get("seed", 42))
        while len(seeds) < pop_size:
            seeds.append(self._make_agent(_random_expression(max_depth=4), generation=0))

        self.population = seeds[:pop_size]

    def evaluate(self, agent: AgentGenome) -> FactorCandidate:
        """Evaluate one agent and return a FactorCandidate."""
        output = self._executor(agent, {})
        train_factor = output["factor"]
        train_forward = output["forward_return"]
        test_factor = output["factor_test"]
        test_forward = output["forward_return_test"]

        eval_result = self.evaluator.evaluate(output)
        train_ic = ic_score(train_factor, train_forward)
        test_ic = ic_score(test_factor, test_forward)

        # Penalize constant / NaN factors so they are not selected as elites.
        if not np.isfinite(train_ic) or not np.isfinite(test_ic):
            train_score = 0.0
            train_ic = -1.0 if not np.isfinite(train_ic) else train_ic
            test_ic = -1.0 if not np.isfinite(test_ic) else test_ic
        else:
            train_score = float(eval_result.score)

        cand = FactorCandidate(
            agent=agent,
            generation=self._generation,
            train_score=train_score,
            train_ic=train_ic,
            train_rank_ic=rank_ic_score(train_factor, train_forward),
            test_ic=test_ic,
            test_rank_ic=rank_ic_score(test_factor, test_forward),
            turnover=turnover_score(train_factor),
            backtest_train=run_long_short_backtest(
                train_factor, train_forward, transaction_cost=self.config.get("transaction_cost", 0.001)
            ),
            backtest_test=run_long_short_backtest(
                test_factor, test_forward, transaction_cost=self.config.get("transaction_cost", 0.001)
            ),
        )
        self.archive.append(cand)
        return cand

    def evaluate_population(self) -> list[FactorCandidate]:
        """Evaluate all agents in the current population."""
        results = []
        for agent in self.population:
            results.append(self.evaluate(agent))
        return results

    def select_and_breed(self, evaluated: list[FactorCandidate]) -> list[AgentGenome]:
        """Select elites and produce offspring via mutation/crossover."""
        pop_size = self.config.get("population_size", 20)
        elite_frac = self.config.get("elite_fraction", 0.2)
        crossover_frac = self.config.get("crossover_fraction", 0.3)
        n_elites = max(1, int(pop_size * elite_frac))
        n_crossover = int(pop_size * crossover_frac)
        n_mutate = pop_size - n_elites - n_crossover

        # Robust selection: reward test IC only when train/test signs agree,
        # otherwise penalize the candidate to avoid unstable sign-flipping alphas.
        def _robust_ic(c: FactorCandidate) -> float:
            if not np.isfinite(c.train_ic) or not np.isfinite(c.test_ic):
                return -np.inf
            if np.sign(c.train_ic) != np.sign(c.test_ic):
                return -1.0
            return float(c.test_ic)

        evaluated_sorted = sorted(evaluated, key=_robust_ic, reverse=True)
        elites = [c.agent for c in evaluated_sorted[:n_elites] if _robust_ic(c) > -0.5]
        if not elites:
            elites = [c.agent for c in evaluated_sorted if _robust_ic(c) > -0.5][:n_elites]
        if not elites:
            elites = [self._make_agent(_random_expression(max_depth=4), generation=self._generation + 1)]

        # Build next population from elites.
        next_pop = [agent.model_copy() for agent in elites]

        # Mutation offspring.
        for _ in range(n_mutate):
            parent = random.choice(elites)
            child = self.mutator.mutate_prompt(parent, failure_logs=["loop"])
            next_pop.append(child)

        # Crossover offspring.
        for _ in range(n_crossover):
            if len(elites) >= 2:
                p1, p2 = random.sample(elites, 2)
                child_expr = self.mutator.crossover(
                    self._expr_from_agent(p1), self._expr_from_agent(p2)
                )
                next_pop.append(self._make_agent(child_expr, generation=self._generation + 1))

        # Deduplicate by expression string and truncate.
        seen: set[str] = set()
        unique: list[AgentGenome] = []
        for agent in next_pop:
            expr_str = agent.meta.get("factor_expression", {}).get("string", "")
            if expr_str not in seen:
                seen.add(expr_str)
                unique.append(agent)
            if len(unique) >= pop_size:
                break

        # Fill any shortfall with fresh random expressions.
        while len(unique) < pop_size:
            unique.append(self._make_agent(_random_expression(max_depth=4), generation=self._generation + 1))

        return unique[:pop_size]

    def run_generation(self) -> list[FactorCandidate]:
        """Run one full generation: evaluate, select, breed."""
        evaluated = self.evaluate_population()

        def _robust(c: FactorCandidate) -> float:
            if not np.isfinite(c.train_ic) or not np.isfinite(c.test_ic):
                return -np.inf
            if np.sign(c.train_ic) != np.sign(c.test_ic):
                return -1.0
            return float(c.test_ic)

        best = max(evaluated, key=_robust)

        # Convergence tracking on robust test IC (train/test sign must agree).
        robust_best = _robust(best)
        if robust_best > self._best_test_ic + 1e-6:
            self._best_test_ic = robust_best
            self._generations_without_improvement = 0
        else:
            self._generations_without_improvement += 1

        self.history.append(
            {
                "generation": self._generation,
                "best_train_ic": max(c.train_ic for c in evaluated),
                "best_test_ic": best.test_ic,
                "mean_test_ic": float(pd.Series([c.test_ic for c in evaluated]).mean()),
                "best_expression": best.expression,
            }
        )

        from china_a_share_alpha.loop.decay_monitor import decay_summary

        decay = decay_summary(self.history)
        if decay.get("decaying"):
            print(
                f"  [decay warning] test IC slope 3-gen = {decay['ic_decay_slope_3gen']:.4f}"
            )

        self.population = self.select_and_breed(evaluated)
        self._generation += 1
        return evaluated

    def is_converged(self) -> bool:
        """Stop if max generations reached or no test improvement for patience."""
        max_gen = self.config.get("max_generations", 10)
        patience = self.config.get("patience", 3)
        if self._generation >= max_gen:
            return True
        if self._generations_without_improvement >= patience:
            return True
        return False

    def leaderboard(self, n: int = 10) -> pd.DataFrame:
        """Return top-N robust candidates (train/test sign agreement)."""
        def _robust(c: FactorCandidate) -> float:
            if not np.isfinite(c.train_ic) or not np.isfinite(c.test_ic):
                return -np.inf
            if np.sign(c.train_ic) != np.sign(c.test_ic):
                return -1.0
            return float(c.test_ic)

        best = sorted(self.archive, key=_robust, reverse=True)[:n]
        rows = []
        for c in best:
            rows.append(
                {
                    "rank": 0,
                    "candidate_id": c.candidate_id,
                    "generation": c.generation,
                    "expression": c.expression,
                    "train_score": c.train_score,
                    "train_ic": c.train_ic,
                    "test_ic": c.test_ic,
                    "test_rank_ic": c.test_rank_ic,
                    "turnover": c.turnover,
                    "test_sharpe": c.backtest_test.get("sharpe", 0.0),
                    "test_mdd": c.backtest_test.get("max_drawdown", 0.0),
                }
            )
        df = pd.DataFrame(rows)
        df["rank"] = range(1, len(df) + 1)
        return df

    def _make_agent(self, expr, generation: int) -> AgentGenome:
        meta = {
            "domain": "china_a_share_alpha",
            "factor_expression": {
                "expr": expr_to_dict(expr),
                "string": str(expr),
                "stage": generation,
            },
        }
        agent = AgentGenome(
            name=f"factor_miner_gen{generation}_{uuid.uuid4().hex[:6]}",
            role="factor_miner",
            system_prompt="Evolve a formulaic alpha factor for China A-shares.",
            meta=meta,
        )
        self.repo.save_agent(agent)
        return agent

    def _expr_from_agent(self, agent: AgentGenome):
        return expr_from_dict(agent.meta["factor_expression"]["expr"])
