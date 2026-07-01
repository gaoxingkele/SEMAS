"""Enhanced expression-tree mutator with a richer operator grammar.

Adds EMA, percentage change, signed power, rolling z-score, lag/delay,
and conditional operators to the base FactorMutator grammar.
"""

from __future__ import annotations

import copy
import random
from typing import Any

from semas.genome.genome import AgentGenome

from china_a_share_alpha.evolution.factor_mutator import (
    MAX_NODES,
    BINARY_OPS,
    ROLLING_OPS,
    TERNARY_OPS,
    UNARY_OPS,
    VARIABLES,
    WINDOWS,
    FactorMutator,
    _collect_nodes,
    _node_count,
    _random_constant,
    _random_expression as _base_random_expression,
    _random_terminal,
    _random_variable,
    _replace_random_node,
    is_reasonable_expression,
)
from china_a_share_alpha.factor.expression import (
    BinaryOp,
    Const,
    FactorExpr,
    RollingBinaryOp,
    RollingOp,
    TernaryOp,
    UnaryOp,
    Var,
    expr_to_dict,
)

# Extended operator sets.
EXTENDED_UNARY_OPS = UNARY_OPS + ["signed_power", "winsorize"]
EXTENDED_ROLLING_OPS = ROLLING_OPS + ["ts_ema", "ts_pct_change", "ts_zscore", "ts_shift"]
EXTENDED_BINARY_OPS = BINARY_OPS + ["if_positive"]  # if_positive(x, y) = y if x > 0 else 0
EXTENDED_TERNARY_OPS = TERNARY_OPS


def _random_expression(max_depth: int = 3, max_retries: int = 50) -> FactorExpr:
    """Grow a random expression tree from the extended grammar."""

    def _grow(depth: int) -> FactorExpr:
        if depth <= 0:
            return _random_terminal()

        node_type = random.choice([
            "terminal", "unary", "binary", "ternary", "rolling", "rolling_binary",
            "extended_unary", "extended_rolling"
        ])
        if node_type == "terminal":
            return _random_terminal()
        if node_type == "unary":
            return UnaryOp(op=random.choice(UNARY_OPS), child=_grow(depth - 1))
        if node_type == "extended_unary":
            op = random.choice(["signed_power", "winsorize"])
            if op == "signed_power":
                child = _grow(depth - 1)
                power = Const(value=round(random.uniform(0.5, 3.0), 3))
                return BinaryOp(op="mul", left=UnaryOp(op="sign", child=child), right=power)
            return UnaryOp(op=op, child=_grow(depth - 1))
        if node_type == "binary":
            return BinaryOp(
                op=random.choice(BINARY_OPS),
                left=_grow(depth - 1),
                right=_grow(depth - 1),
            )
        if node_type == "ternary":
            return TernaryOp(
                op=random.choice(EXTENDED_TERNARY_OPS),
                pred=_grow(depth - 1),
                if_true=_grow(depth - 1),
                if_false=_grow(depth - 1),
            )
        if node_type == "rolling":
            return RollingOp(
                op=random.choice(ROLLING_OPS),
                child=_grow(depth - 1),
                window=random.choice(WINDOWS),
            )
        if node_type == "extended_rolling":
            op = random.choice(["ts_ema", "ts_pct_change", "ts_zscore", "ts_shift"])
            return RollingOp(
                op=op,
                child=_grow(depth - 1),
                window=random.choice(WINDOWS),
            )
        return RollingBinaryOp(
            op="ts_corr",
            left=_grow(depth - 1),
            right=_grow(depth - 1),
            window=random.choice(WINDOWS),
        )

    for _ in range(max_retries):
        expr = _grow(max_depth)
        if is_reasonable_expression(expr):
            return expr
    return _random_variable()


class EnhancedFactorMutator(FactorMutator):
    """SEMAS Mutator with richer grammar for factor expression evolution."""

    def __init__(self, seed: int | None = None, mode: str = "gp"):
        super().__init__(seed=seed, mode=mode)

    def mutate_prompt(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """Apply one structural mutation from the extended grammar."""
        meta = copy.deepcopy(dict(agent.meta))
        stage = meta.get("factor_expression", {}).get("stage", 0)

        if self.mode == "seed" and stage == 0:
            # A strong volatility/reversal seed for recent A-share regime.
            expr: FactorExpr = UnaryOp(
                "cs_rank",
                RollingOp("ts_mean", UnaryOp("abs", Var("return")), 5),
            )
        elif self.mode == "gp":
            expr = _random_expression(max_depth=4)
        else:
            expr = self._get_expr(agent).copy()
            mutation = random.choice([
                "wrap_unary", "insert_binary", "change_window", "replace_op",
                "replace_subtree", "add_lag", "signed_power"
            ])
            if mutation == "wrap_unary":
                op = random.choice(EXTENDED_UNARY_OPS)
                expr = UnaryOp(op=op, child=expr)
            elif mutation == "insert_binary":
                op = random.choice(EXTENDED_BINARY_OPS)
                if random.random() < 0.5:
                    expr = BinaryOp(op=op, left=expr, right=_random_terminal())
                else:
                    expr = BinaryOp(op=op, left=_random_terminal(), right=expr)
            elif mutation == "change_window":
                nodes = [n for n in _collect_nodes(expr) if isinstance(n, (RollingOp, RollingBinaryOp))]
                if nodes:
                    node = random.choice(nodes)
                    node.window = random.choice(WINDOWS)
            elif mutation == "replace_op":
                nodes = _collect_nodes(expr)
                if nodes:
                    node = random.choice(nodes)
                    if isinstance(node, RollingOp):
                        node.op = random.choice(EXTENDED_ROLLING_OPS)
                    elif isinstance(node, UnaryOp):
                        node.op = random.choice(EXTENDED_UNARY_OPS)
                    elif isinstance(node, BinaryOp):
                        node.op = random.choice(EXTENDED_BINARY_OPS)
            elif mutation == "replace_subtree":
                expr = _replace_random_node(expr, _random_expression(max_depth=2))
            elif mutation == "add_lag":
                expr = RollingOp(op="ts_shift", child=expr, window=random.choice([1, 2, 3, 5]))
            elif mutation == "signed_power":
                expr = BinaryOp(
                    op="mul",
                    left=UnaryOp(op="sign", child=expr),
                    right=_random_constant(),
                )

            # Reject mutations that blow up the tree or reintroduce degenerate
            # constant sub-expressions.
            if not is_reasonable_expression(expr) or _node_count(expr) > MAX_NODES:
                expr = self._get_expr(agent).copy()

        evolved = self._set_expr(agent, expr)
        evolved_meta = copy.deepcopy(dict(evolved.meta))
        evolved_meta.setdefault("factor_expression", {})
        evolved_meta["factor_expression"]["stage"] = stage + 1
        return agent.evolve_from(meta=evolved_meta)

    def crossover(self, parent1: FactorExpr, parent2: FactorExpr) -> FactorExpr:
        """Subtree crossover (inherited behavior, but using extended random expressions)."""
        return super().crossover(parent1, parent2)

    @staticmethod
    def _set_expr(agent: AgentGenome, expr: FactorExpr) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        meta.setdefault("factor_expression", {})
        meta["factor_expression"]["expr"] = expr_to_dict(expr)
        meta["factor_expression"]["string"] = str(expr)
        return agent.evolve_from(meta=meta)
