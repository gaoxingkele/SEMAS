"""Executor for factor-mining agent.

The agent stores a factor expression in its `meta["factor_expression"]`.
The executor evaluates the expression on the loaded data panel and returns
`factor` plus `forward_return`.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from semas.genome.genome import AgentGenome

from china_a_share_alpha.factor.expression import expr_from_dict


def create_factor_executor(data: pd.DataFrame):
    """Return an ExecutorFn that evaluates the agent's factor expression."""

    def executor(agent: AgentGenome, task_input: dict[str, Any]) -> dict[str, Any]:
        expr_dict = agent.meta.get("factor_expression", {}).get("expr")
        if expr_dict is None:
            raise ValueError("Agent meta must contain factor_expression.expr")

        expr = expr_from_dict(expr_dict)
        factor = expr.eval(data)

        return {
            "factor": factor,
            "forward_return": data["forward_return"],
            "expression_string": str(expr),
        }

    return executor
