"""Executor for factor-mining agent.

The agent stores a factor expression in its `meta["factor_expression"]`.
The executor evaluates the expression on both train and test panels and
returns `factor` (train) plus `forward_return` (train), as well as the test
series for final validation.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from semas.genome.genome import AgentGenome

from china_a_share_alpha.evaluator.neutralizer import apply_neutralization
from china_a_share_alpha.factor.expression import expr_from_dict


def create_factor_executor(
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    config: dict[str, Any],
):
    """Return an ExecutorFn that evaluates the agent's factor expression.

    Args:
        train_data: Panel used during SEMAS evolution.
        test_data: Panel held out for final report.
        config: User config; may contain `neutralize_sector` and
            `neutralize_market_cap` flags.
    """
    neutralize_sector = config.get("neutralize_sector", False)
    neutralize_market_cap = config.get("neutralize_market_cap", False)

    def executor(agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
        expr_dict = agent.meta.get("factor_expression", {}).get("expr")
        if expr_dict is None:
            raise ValueError("Agent meta must contain factor_expression.expr")

        expr = expr_from_dict(expr_dict)
        train_factor = expr.eval(train_data)
        train_factor = apply_neutralization(
            train_factor, train_data, neutralize_sector, neutralize_market_cap
        )

        test_factor = expr.eval(test_data)
        test_factor = apply_neutralization(
            test_factor, test_data, neutralize_sector, neutralize_market_cap
        )

        return {
            "factor": train_factor,
            "forward_return": train_data["forward_return"],
            "factor_test": test_factor,
            "forward_return_test": test_data["forward_return"],
            "expression_string": str(expr),
        }

    return executor
