"""Enhanced factor population with Sharpe/IR-based fitness and turnover penalty."""

from __future__ import annotations

from typing import Any

import numpy as np

from china_a_share_alpha.loop.population import FactorCandidate, FactorPopulation


class EnhancedFactorPopulation(FactorPopulation):
    """Factor population that selects on risk-adjusted returns, not just IC."""

    def _fitness(self, c: FactorCandidate) -> float:
        """Robust fitness combining test Sharpe, IC consistency, and turnover penalty."""
        if not np.isfinite(c.train_ic) or not np.isfinite(c.test_ic):
            return -np.inf
        if np.sign(c.train_ic) != np.sign(c.test_ic):
            return -1.0

        test_sharpe = c.backtest_test.get("sharpe", 0.0)
        test_return = c.backtest_test.get("cost_adjusted_return", 0.0)
        mdd = c.backtest_test.get("max_drawdown", 0.0)
        turnover = c.turnover

        if not np.isfinite(test_sharpe):
            test_sharpe = 0.0
        if not np.isfinite(test_return):
            test_return = 0.0
        if not np.isfinite(mdd):
            mdd = 0.0

        # Sharpe is primary; IC consistency is required but secondary;
        # penalize high turnover and deep drawdowns.
        score = (
            0.45 * test_sharpe
            + 0.25 * test_return
            + 0.20 * abs(c.test_ic)
            + 0.10 * abs(c.test_rank_ic)
            - 0.15 * max(0.0, -mdd)
            - 0.10 * min(turnover, 2.0)
        )
        return float(score)

    def select_and_breed(self, evaluated: list[FactorCandidate]) -> list[Any]:
        """Select elites on risk-adjusted fitness and breed."""
        pop_size = self.config.get("population_size", 20)
        elite_frac = self.config.get("elite_fraction", 0.2)
        crossover_frac = self.config.get("crossover_fraction", 0.3)
        n_elites = max(1, int(pop_size * elite_frac))
        n_crossover = int(pop_size * crossover_frac)
        n_mutate = pop_size - n_elites - n_crossover

        evaluated_sorted = sorted(evaluated, key=self._fitness, reverse=True)
        elites = [c.agent for c in evaluated_sorted[:n_elites] if self._fitness(c) > -0.5]
        if not elites:
            elites = [c.agent for c in evaluated_sorted if self._fitness(c) > -0.5][:n_elites]
        if not elites:
            from china_a_share_alpha.evolution.enhanced_factor_mutator import _random_expression
            elites = [self._make_agent(_random_expression(max_depth=4), generation=self._generation + 1)]

        next_pop = [agent.model_copy() for agent in elites]

        for _ in range(n_mutate):
            parent = np.random.choice(elites)
            child = self.mutator.mutate_prompt(parent, failure_logs=["loop"])
            next_pop.append(child)

        for _ in range(n_crossover):
            if len(elites) >= 2:
                p1, p2 = np.random.choice(elites, size=2, replace=False)
                child_expr = self.mutator.crossover(
                    self._expr_from_agent(p1), self._expr_from_agent(p2)
                )
                next_pop.append(self._make_agent(child_expr, generation=self._generation + 1))

        seen: set[str] = set()
        unique: list[Any] = []
        for agent in next_pop:
            expr_str = agent.meta.get("factor_expression", {}).get("string", "")
            if expr_str not in seen:
                seen.add(expr_str)
                unique.append(agent)
            if len(unique) >= pop_size:
                break

        while len(unique) < pop_size:
            from china_a_share_alpha.evolution.enhanced_factor_mutator import _random_expression
            unique.append(self._make_agent(_random_expression(max_depth=4), generation=self._generation + 1))

        return unique[:pop_size]

    def run_generation(self) -> list[FactorCandidate]:
        """Run one generation tracking Sharpe-based best."""
        evaluated = self.evaluate_population()
        best = max(evaluated, key=self._fitness)
        best_fitness = self._fitness(best)

        if best_fitness > self._best_test_ic + 1e-6:
            # Reuse field name for convergence logic; it now stores best fitness.
            self._best_test_ic = best_fitness
            self._generations_without_improvement = 0
        else:
            self._generations_without_improvement += 1

        self.history.append(
            {
                "generation": self._generation,
                "best_train_ic": max(c.train_ic for c in evaluated),
                "best_test_ic": best.test_ic,
                "best_test_sharpe": best.backtest_test.get("sharpe", 0.0),
                "mean_test_ic": float(np.mean([c.test_ic for c in evaluated])),
                "best_expression": best.expression,
            }
        )

        from china_a_share_alpha.loop.decay_monitor import decay_summary

        decay = decay_summary(self.history)
        if decay.get("decaying"):
            print(f"  [decay warning] test IC slope 3-gen = {decay['ic_decay_slope_3gen']:.4f}")

        self.population = self.select_and_breed(evaluated)
        self._generation += 1
        return evaluated
