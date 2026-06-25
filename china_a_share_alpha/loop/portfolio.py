"""Portfolio-level multi-factor evolution.

Evolves a weighted combination of alpha factors. The genome is stored inside a
SEMAS AgentGenome as a list of factor expressions and weights.
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
from china_a_share_alpha.evaluator.metrics import ic_score, rank_ic_score
from china_a_share_alpha.executor import create_factor_executor
from china_a_share_alpha.factor.expression import FactorExpr, expr_from_dict, expr_to_dict


@dataclass
class PortfolioCandidate:
    agent: AgentGenome
    generation: int
    train_ic: float = 0.0
    train_rank_ic: float = 0.0
    test_ic: float = 0.0
    test_rank_ic: float = 0.0
    train_sharpe: float = 0.0
    test_sharpe: float = 0.0
    backtest_train: dict[str, Any] = field(default_factory=dict)
    backtest_test: dict[str, Any] = field(default_factory=dict)
    candidate_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def weights(self) -> list[float]:
        return self.agent.meta.get("portfolio", {}).get("weights", [])

    @property
    def expression_strings(self) -> list[str]:
        return [f.get("string", "") for f in self.agent.meta.get("portfolio", {}).get("factors", [])]


class PortfolioPopulation:
    """Evolve weighted combinations of factors from a factor library."""

    def __init__(
        self,
        repo: GenomeRepository,
        train_data: pd.DataFrame,
        test_data: pd.DataFrame,
        evaluator: Evaluator,
        config: dict[str, Any],
        factor_library: list[FactorExpr],
    ):
        self.repo = repo
        self.train_data = train_data
        self.test_data = test_data
        self.evaluator = evaluator
        self.config = config
        self.factor_library = factor_library
        self.population: list[AgentGenome] = []
        self.archive: list[PortfolioCandidate] = []
        self.history: list[dict[str, Any]] = []
        self._executor = create_factor_executor(train_data, test_data, config)
        self._generation = 0
        self._best_test_sharpe = -1.0
        self._generations_without_improvement = 0

    def seed_population(self) -> None:
        """Create random-weighted portfolios of factors from the library."""
        pop_size = self.config.get("portfolio_population_size", 10)
        n_factors = min(self.config.get("portfolio_n_factors", 5), len(self.factor_library))
        rng = np.random.default_rng(self.config.get("seed", 42))

        for _ in range(pop_size):
            factors = rng.choice(self.factor_library, size=n_factors, replace=False).tolist()
            weights = rng.dirichlet(np.ones(n_factors)).tolist()
            self.population.append(self._make_agent(factors, weights, generation=0))

    def _make_agent(self, factors: list[FactorExpr], weights: list[float], generation: int) -> AgentGenome:
        meta = {
            "domain": "china_a_share_alpha_portfolio",
            "portfolio": {
                "factors": [{"expr": expr_to_dict(f), "string": str(f)} for f in factors],
                "weights": weights,
            },
        }
        agent = AgentGenome(
            name=f"portfolio_gen{generation}_{uuid.uuid4().hex[:6]}",
            role="portfolio",
            system_prompt="Evolve a multi-factor portfolio for China A-shares.",
            meta=meta,
        )
        self.repo.save_agent(agent)
        return agent

    def _portfolio_factors_from_agent(self, agent: AgentGenome) -> tuple[list[FactorExpr], list[float]]:
        portfolio = agent.meta.get("portfolio", {})
        factors = [expr_from_dict(f["expr"]) for f in portfolio.get("factors", [])]
        weights = portfolio.get("weights", [])
        return factors, weights

    def _evaluate_combined(self, agent: AgentGenome, data: pd.DataFrame) -> pd.Series:
        """Compute weighted-sum combined factor on `data`."""
        factors, weights = self._portfolio_factors_from_agent(agent)
        if not factors:
            return pd.Series(0.0, index=data.index)

        combined = pd.Series(0.0, index=data.index)
        for expr, w in zip(factors, weights):
            raw = expr.eval(data)
            # Cross-sectionally z-score each factor before weighting.
            normed = raw.groupby(level="date").transform(lambda s: (s - s.mean()) / (s.std() + 1e-8))
            combined = combined + w * normed
        return combined

    def evaluate(self, agent: AgentGenome) -> PortfolioCandidate:
        train_factor = self._evaluate_combined(agent, self.train_data)
        test_factor = self._evaluate_combined(agent, self.test_data)

        train_bt = run_long_short_backtest(
            train_factor,
            self.train_data["forward_return"],
            transaction_cost=self.config.get("transaction_cost", 0.001),
        )
        test_bt = run_long_short_backtest(
            test_factor,
            self.test_data["forward_return"],
            transaction_cost=self.config.get("transaction_cost", 0.001),
        )

        cand = PortfolioCandidate(
            agent=agent,
            generation=self._generation,
            train_ic=ic_score(train_factor, self.train_data["forward_return"]),
            train_rank_ic=rank_ic_score(train_factor, self.train_data["forward_return"]),
            test_ic=ic_score(test_factor, self.test_data["forward_return"]),
            test_rank_ic=rank_ic_score(test_factor, self.test_data["forward_return"]),
            train_sharpe=train_bt["sharpe"],
            test_sharpe=test_bt["sharpe"],
            backtest_train=train_bt,
            backtest_test=test_bt,
        )
        self.archive.append(cand)
        return cand

    def evaluate_population(self) -> list[PortfolioCandidate]:
        return [self.evaluate(agent) for agent in self.population]

    def _mutate_weights(self, agent: AgentGenome) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        weights = np.array(meta["portfolio"]["weights"])
        noise = np.random.normal(0, 0.1, size=len(weights))
        weights = np.clip(weights + noise, 0.0, None)
        weights = weights / (weights.sum() + 1e-8)
        meta["portfolio"]["weights"] = weights.tolist()
        return agent.evolve_from(meta=meta)

    def _add_factor(self, agent: AgentGenome) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        factors = [expr_from_dict(f["expr"]) for f in meta["portfolio"]["factors"]]
        weights = list(meta["portfolio"]["weights"])
        available = [f for f in self.factor_library if str(f) not in {str(x) for x in factors}]
        if not available:
            return agent
        new_factor = random.choice(available)
        factors.append(new_factor)
        weights = [w * 0.9 for w in weights] + [0.1]
        meta["portfolio"]["factors"] = [{"expr": expr_to_dict(f), "string": str(f)} for f in factors]
        meta["portfolio"]["weights"] = weights
        return agent.evolve_from(meta=meta)

    def _remove_factor(self, agent: AgentGenome) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        factors = [expr_from_dict(f["expr"]) for f in meta["portfolio"]["factors"]]
        weights = np.array(meta["portfolio"]["weights"])
        if len(factors) <= 2:
            return agent
        drop_idx = int(np.argmin(weights))
        factors.pop(drop_idx)
        weights = np.delete(weights, drop_idx)
        weights = weights / (weights.sum() + 1e-8)
        meta["portfolio"]["factors"] = [{"expr": expr_to_dict(f), "string": str(f)} for f in factors]
        meta["portfolio"]["weights"] = weights.tolist()
        return agent.evolve_from(meta=meta)

    def _swap_factor(self, agent: AgentGenome) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        factors = [expr_from_dict(f["expr"]) for f in meta["portfolio"]["factors"]]
        if not factors:
            return agent
        available = [f for f in self.factor_library if str(f) not in {str(x) for x in factors}]
        if not available:
            return agent
        idx = random.randrange(len(factors))
        factors[idx] = random.choice(available)
        meta["portfolio"]["factors"] = [{"expr": expr_to_dict(f), "string": str(f)} for f in factors]
        return agent.evolve_from(meta=meta)

    def _breed(self, evaluated: list[PortfolioCandidate]) -> list[AgentGenome]:
        pop_size = self.config.get("portfolio_population_size", 10)
        elite_frac = self.config.get("portfolio_elite_fraction", 0.2)
        n_elites = max(1, int(pop_size * elite_frac))

        evaluated_sorted = sorted(evaluated, key=lambda c: c.test_sharpe, reverse=True)
        elites = [c.agent for c in evaluated_sorted[:n_elites]]
        next_pop = [agent.model_copy() for agent in elites]

        while len(next_pop) < pop_size:
            parent = random.choice(elites)
            op = random.choice(["weights", "add", "remove", "swap"])
            if op == "weights":
                child = self._mutate_weights(parent)
            elif op == "add":
                child = self._add_factor(parent)
            elif op == "remove":
                child = self._remove_factor(parent)
            else:
                child = self._swap_factor(parent)
            next_pop.append(child)

        return next_pop[:pop_size]

    def run_generation(self) -> list[PortfolioCandidate]:
        evaluated = self.evaluate_population()
        best = max(evaluated, key=lambda c: c.test_sharpe)

        if best.test_sharpe > self._best_test_sharpe + 1e-6:
            self._best_test_sharpe = best.test_sharpe
            self._generations_without_improvement = 0
        else:
            self._generations_without_improvement += 1

        self.history.append(
            {
                "generation": self._generation,
                "best_train_sharpe": max(c.train_sharpe for c in evaluated),
                "best_test_sharpe": best.test_sharpe,
                "best_test_ic": best.test_ic,
                "mean_test_sharpe": float(np.mean([c.test_sharpe for c in evaluated])),
            }
        )

        self.population = self._breed(evaluated)
        self._generation += 1
        return evaluated

    def is_converged(self) -> bool:
        max_gen = self.config.get("portfolio_max_generations", 10)
        patience = self.config.get("portfolio_patience", 3)
        if self._generation >= max_gen:
            return True
        if self._generations_without_improvement >= patience:
            return True
        return False

    def leaderboard(self, n: int = 5) -> pd.DataFrame:
        best = sorted(self.archive, key=lambda c: c.test_sharpe, reverse=True)[:n]
        rows = []
        for c in best:
            rows.append(
                {
                    "candidate_id": c.candidate_id,
                    "generation": c.generation,
                    "test_ic": c.test_ic,
                    "test_rank_ic": c.test_rank_ic,
                    "test_sharpe": c.test_sharpe,
                    "test_mdd": c.backtest_test.get("max_drawdown", 0.0),
                    "n_factors": len(c.weights),
                    "weights": c.weights,
                    "expressions": " | ".join(c.expression_strings),
                }
            )
        return pd.DataFrame(rows)
