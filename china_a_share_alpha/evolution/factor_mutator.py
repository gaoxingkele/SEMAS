"""Expression-tree mutator for factor evolution.

Heavily inspired by genetic programming / symbolic regression approaches
(e.g. gplearn, AlphaGen, AlphaPROBE) but implemented as a SEMAS Mutator.
"""

from __future__ import annotations

import copy
import random
from typing import Any

from semas.genome.genome import AgentGenome
from semas.mutator.mutator import Mutator

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

VARIABLES = [
    "open", "high", "low", "close", "volume", "vwap", "return",
    "turnover_rate", "pb", "total_mv", "circ_mv",
    "roe", "roe_dt", "netprofit_yoy", "dt_netprofit_yoy",
    "grossprofit_margin", "debt_to_assets", "ocfps", "eps",
    "net_elg_amount", "net_mf_amount", "hk_vol", "hk_ratio",
]
ROLLING_OPS = ["ts_mean", "ts_std", "ts_sum", "ts_min", "ts_max", "ts_delta", "ts_rank", "ts_argmax", "ts_argmin"]
UNARY_OPS = ["abs", "log", "sign", "neg", "cs_rank", "cs_zscore"]
BINARY_OPS = ["add", "sub", "mul", "div", "greater", "less", "if_positive"]
TERNARY_OPS = ["if_else"]
WINDOWS = [3, 5, 10, 20, 60]


def _random_variable() -> Var:
    return Var(name=random.choice(VARIABLES))


def _random_constant() -> Const:
    return Const(value=round(random.uniform(-1.0, 1.0), 3))


def _random_terminal() -> FactorExpr:
    return random.choice([_random_variable, _random_constant])()


def _is_constant(node: FactorExpr) -> bool:
    """Return True if a sub-expression evaluates to a constant (no Variables)."""
    if isinstance(node, Const):
        return True
    if isinstance(node, (UnaryOp, RollingOp)):
        return _is_constant(node.child)
    if isinstance(node, BinaryOp):
        return _is_constant(node.left) and _is_constant(node.right)
    if isinstance(node, TernaryOp):
        return (
            _is_constant(node.pred)
            and _is_constant(node.if_true)
            and _is_constant(node.if_false)
        )
    return False


def _is_degenerate_node(node: FactorExpr) -> bool:
    """Return True for structurally constant or NaN-producing sub-expressions.

    Examples include ``ts_corr(const, x)``, ``ts_mean(0.5)``, or
    ``greater(const, const)``.
    """
    if isinstance(node, (UnaryOp, RollingOp)) and _is_constant(node.child):
        return True
    if isinstance(node, RollingBinaryOp) and (
        _is_constant(node.left) or _is_constant(node.right)
    ):
        return True
    if isinstance(node, BinaryOp) and _is_constant(node.left) and _is_constant(node.right):
        return True
    if isinstance(node, TernaryOp):
        if _is_constant(node.if_true) and _is_constant(node.if_false):
            return True
        if (
            _is_constant(node.pred)
            and _is_constant(node.if_true)
            and _is_constant(node.if_false)
        ):
            return True
    return False


def is_reasonable_expression(node: FactorExpr) -> bool:
    """Recursively True if no degenerate sub-expression exists."""
    if _is_degenerate_node(node):
        return False
    if isinstance(node, (UnaryOp, RollingOp)):
        return is_reasonable_expression(node.child)
    if isinstance(node, (BinaryOp, RollingBinaryOp)):
        return is_reasonable_expression(node.left) and is_reasonable_expression(node.right)
    if isinstance(node, TernaryOp):
        return (
            is_reasonable_expression(node.pred)
            and is_reasonable_expression(node.if_true)
            and is_reasonable_expression(node.if_false)
        )
    return True


MAX_NODES = 40


def _node_count(node: FactorExpr) -> int:
    """Return number of nodes in an expression tree."""
    if isinstance(node, (UnaryOp, RollingOp)):
        return 1 + _node_count(node.child)
    if isinstance(node, (BinaryOp, RollingBinaryOp)):
        return 1 + _node_count(node.left) + _node_count(node.right)
    if isinstance(node, TernaryOp):
        return (
            1
            + _node_count(node.pred)
            + _node_count(node.if_true)
            + _node_count(node.if_false)
        )
    return 1


def _random_expression(max_depth: int = 3, max_retries: int = 50) -> FactorExpr:
    """Grow a random expression tree from the operator grammar."""

    def _grow(depth: int) -> FactorExpr:
        if depth <= 0:
            return _random_terminal()

        node_type = random.choice(
            ["terminal", "unary", "binary", "ternary", "rolling", "rolling_binary"]
        )
        if node_type == "terminal":
            return _random_terminal()
        if node_type == "unary":
            return UnaryOp(op=random.choice(UNARY_OPS), child=_grow(depth - 1))
        if node_type == "binary":
            return BinaryOp(
                op=random.choice(BINARY_OPS),
                left=_grow(depth - 1),
                right=_grow(depth - 1),
            )
        if node_type == "ternary":
            return TernaryOp(
                op=random.choice(TERNARY_OPS),
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
        return RollingBinaryOp(
            op="ts_corr",
            left=_grow(depth - 1),
            right=_grow(depth - 1),
            window=random.choice(WINDOWS),
        )

    for _ in range(max_retries):
        expr = _grow(max_depth)
        if is_reasonable_expression(expr) and _node_count(expr) <= MAX_NODES:
            return expr
    # Fallback to a simple variable if random trees keep being degenerate.
    return _random_variable()


def _collect_nodes(node: FactorExpr) -> list[FactorExpr]:
    """Return all sub-nodes (including the root)."""
    nodes = [node]
    if isinstance(node, (UnaryOp, RollingOp)):
        nodes.extend(_collect_nodes(node.child))
    elif isinstance(node, (BinaryOp, RollingBinaryOp)):
        nodes.extend(_collect_nodes(node.left))
        nodes.extend(_collect_nodes(node.right))
    elif isinstance(node, TernaryOp):
        nodes.extend(_collect_nodes(node.pred))
        nodes.extend(_collect_nodes(node.if_true))
        nodes.extend(_collect_nodes(node.if_false))
    return nodes


def _replace_random_node(root: FactorExpr, new_node: FactorExpr) -> FactorExpr:
    """Replace a random non-root node with `new_node`."""
    nodes = _collect_nodes(root)
    if len(nodes) <= 1:
        return new_node
    target = random.choice(nodes[:-1])  # exclude root to keep structure

    def _walk(node: FactorExpr) -> FactorExpr:
        if node is target:
            return new_node
        if isinstance(node, UnaryOp):
            return UnaryOp(op=node.op, child=_walk(node.child))
        if isinstance(node, RollingOp):
            return RollingOp(op=node.op, child=_walk(node.child), window=node.window)
        if isinstance(node, BinaryOp):
            return BinaryOp(op=node.op, left=_walk(node.left), right=_walk(node.right))
        if isinstance(node, TernaryOp):
            return TernaryOp(
                op=node.op,
                pred=_walk(node.pred),
                if_true=_walk(node.if_true),
                if_false=_walk(node.if_false),
            )
        if isinstance(node, RollingBinaryOp):
            return RollingBinaryOp(
                op=node.op,
                left=_walk(node.left),
                right=_walk(node.right),
                window=node.window,
            )
        return node

    return _walk(root)


class FactorMutator(Mutator):
    """SEMAS Mutator that evolves a factor expression stored in agent.meta."""

    def __init__(self, seed: int | None = None, mode: str = "seed"):
        """Args:
            seed: Random seed for reproducibility.
            mode: 'seed' uses a deterministic known-good first mutation;
                  'gp' uses random grammar-based expression generation.
        """
        if seed is not None:
            random.seed(seed)
        self.mode = mode

    @staticmethod
    def _get_expr(agent: AgentGenome) -> FactorExpr:
        expr_dict = agent.meta.get("factor_expression", {}).get("expr")
        if expr_dict is None:
            return _random_terminal()
        from china_a_share_alpha.factor.expression import expr_from_dict

        return expr_from_dict(expr_dict)

    @staticmethod
    def _set_expr(agent: AgentGenome, expr: FactorExpr) -> AgentGenome:
        meta = copy.deepcopy(dict(agent.meta))
        meta.setdefault("factor_expression", {})
        meta["factor_expression"]["expr"] = expr_to_dict(expr)
        meta["factor_expression"]["string"] = str(expr)
        return agent.evolve_from(meta=meta)

    def mutate_prompt(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """Apply one structural mutation to the stored factor."""
        meta = copy.deepcopy(dict(agent.meta))
        stage = meta.get("factor_expression", {}).get("stage", 0)

        if self.mode == "seed" and stage == 0:
            # Known-good seed expression for the synthetic mean-reversion panel.
            # The synthetic forward return is negatively correlated with the
            # past 5-day return, so we negate the ranked rolling mean.
            expr: FactorExpr = UnaryOp(
                "neg",
                UnaryOp("cs_rank", RollingOp("ts_mean", Var("return"), 5)),
            )
        elif self.mode == "gp":
            # Random grammar-based expression; SEMAS selection retains the best.
            expr = _random_expression(max_depth=4)
        else:
            expr = self._get_expr(agent).copy()
            mutation = random.choice(
                ["wrap_unary", "insert_binary", "change_window", "replace_op", "replace_subtree"]
            )
            if mutation == "wrap_unary":
                expr = UnaryOp(op=random.choice(UNARY_OPS), child=expr)
            elif mutation == "insert_binary":
                op = random.choice(BINARY_OPS)
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
                        node.op = random.choice(ROLLING_OPS)
                    elif isinstance(node, UnaryOp):
                        node.op = random.choice(UNARY_OPS)
                    elif isinstance(node, BinaryOp):
                        node.op = random.choice(BINARY_OPS)
            elif mutation == "replace_subtree":
                expr = _replace_random_node(expr, _random_expression(max_depth=2))

            # Reject mutations that blow up the tree or reintroduce degenerate
            # constant sub-expressions.
            if not is_reasonable_expression(expr) or _node_count(expr) > MAX_NODES:
                expr = self._get_expr(agent).copy()

        evolved = self._set_expr(agent, expr)
        evolved_meta = copy.deepcopy(dict(evolved.meta))
        evolved_meta.setdefault("factor_expression", {})
        evolved_meta["factor_expression"]["stage"] = stage + 1
        return agent.evolve_from(meta=evolved_meta)

    def mutate_tool(self, agent: AgentGenome, failure_logs: list[str]) -> Any:
        """No-op for this scaffold; factor is not a tool."""
        return None

    def mutate_few_shot(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """No-op."""
        return agent

    def crossover(self, parent1: FactorExpr, parent2: FactorExpr) -> FactorExpr:
        """Return a child by swapping a random subtree between parents."""
        child = parent1.copy()
        nodes = _collect_nodes(child)
        if len(nodes) <= 1:
            return parent2.copy()
        target = random.choice(nodes[:-1])
        donor = random.choice(_collect_nodes(parent2.copy()))

        def _walk(node: FactorExpr) -> FactorExpr:
            if node is target:
                return donor.copy()
            if isinstance(node, UnaryOp):
                return UnaryOp(op=node.op, child=_walk(node.child))
            if isinstance(node, RollingOp):
                return RollingOp(op=node.op, child=_walk(node.child), window=node.window)
            if isinstance(node, BinaryOp):
                return BinaryOp(op=node.op, left=_walk(node.left), right=_walk(node.right))
            if isinstance(node, TernaryOp):
                return TernaryOp(
                    op=node.op,
                    pred=_walk(node.pred),
                    if_true=_walk(node.if_true),
                    if_false=_walk(node.if_false),
                )
            if isinstance(node, RollingBinaryOp):
                return RollingBinaryOp(
                    op=node.op,
                    left=_walk(node.left),
                    right=_walk(node.right),
                    window=node.window,
                )
            return node

        child = _walk(child)
        if not is_reasonable_expression(child) or _node_count(child) > MAX_NODES:
            return parent1.copy()
        return child

    def mutate_topology(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """No-op."""
        return agent
