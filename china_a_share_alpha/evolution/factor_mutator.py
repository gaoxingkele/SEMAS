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
    UnaryOp,
    Var,
    expr_to_dict,
)

VARIABLES = ["open", "high", "low", "close", "volume", "vwap", "return"]
ROLLING_OPS = ["ts_mean", "ts_std", "ts_sum", "ts_min", "ts_max", "ts_delta"]
UNARY_OPS = ["abs", "log", "sign", "neg", "cs_rank", "cs_zscore"]
BINARY_OPS = ["add", "sub", "mul", "div"]
WINDOWS = [3, 5, 10, 20, 60]


def _random_variable() -> Var:
    return Var(name=random.choice(VARIABLES))


def _random_constant() -> Const:
    return Const(value=round(random.uniform(-1.0, 1.0), 3))


def _random_terminal() -> FactorExpr:
    return random.choice([_random_variable, _random_constant])()


def _random_expression(max_depth: int = 3) -> FactorExpr:
    """Grow a random expression tree from the operator grammar."""
    if max_depth <= 0:
        return _random_terminal()

    node_type = random.choice(["terminal", "unary", "binary", "rolling", "rolling_binary"])
    if node_type == "terminal":
        return _random_terminal()
    if node_type == "unary":
        return UnaryOp(op=random.choice(UNARY_OPS), child=_random_expression(max_depth - 1))
    if node_type == "binary":
        return BinaryOp(
            op=random.choice(BINARY_OPS),
            left=_random_expression(max_depth - 1),
            right=_random_expression(max_depth - 1),
        )
    if node_type == "rolling":
        return RollingOp(
            op=random.choice(ROLLING_OPS),
            child=_random_expression(max_depth - 1),
            window=random.choice(WINDOWS),
        )
    return RollingBinaryOp(
        op="ts_corr",
        left=_random_expression(max_depth - 1),
        right=_random_expression(max_depth - 1),
        window=random.choice(WINDOWS),
    )


def _collect_nodes(node: FactorExpr) -> list[FactorExpr]:
    """Return all sub-nodes (including the root)."""
    nodes = [node]
    if isinstance(node, (UnaryOp, RollingOp)):
        nodes.extend(_collect_nodes(node.child))
    elif isinstance(node, (BinaryOp, RollingBinaryOp)):
        nodes.extend(_collect_nodes(node.left))
        nodes.extend(_collect_nodes(node.right))
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
                op = random.choice(UNARY_OPS)
                expr = UnaryOp(op=op, child=expr)
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
            if isinstance(node, RollingBinaryOp):
                return RollingBinaryOp(
                    op=node.op,
                    left=_walk(node.left),
                    right=_walk(node.right),
                    window=node.window,
                )
            return node

        return _walk(child)

    def mutate_topology(self, agent: AgentGenome, failure_logs: list[str]) -> AgentGenome:
        """No-op."""
        return agent
