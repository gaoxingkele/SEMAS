"""DAG neighborhood parent sampling for live-library-guided evolution.

Treats promoted expressions as DAG nodes; edges connect expressions that
share a subtree signature or differ by a shallow structural edit.
[source: AlphaPROBE on-graph biased evolution]
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from china_a_share_alpha.evolution.ast_regularizer import (
    ast_similarity,
    subtree_signatures,
)
from china_a_share_alpha.factor.expression import FactorExpr
from china_a_share_alpha.factor.parser import parse_expression


@dataclass
class DagNode:
    expression: str
    expr: FactorExpr
    fitness: float = 0.0
    signatures: frozenset[str] = field(default_factory=frozenset)


class ExpressionDag:
    """Undirected neighborhood graph over formulaic expressions."""

    def __init__(self, edge_similarity: float = 0.35):
        self.edge_similarity = edge_similarity
        self.nodes: list[DagNode] = []
        self._adj: list[list[int]] = []

    def __len__(self) -> int:
        return len(self.nodes)

    def add(self, expression: str, fitness: float = 0.0) -> int:
        expr = parse_expression(expression)
        node = DagNode(
            expression=expression,
            expr=expr,
            fitness=float(fitness),
            signatures=frozenset(subtree_signatures(expr)),
        )
        idx = len(self.nodes)
        self.nodes.append(node)
        self._adj.append([])
        for j, other in enumerate(self.nodes[:-1]):
            if self._should_link(node, other):
                self._adj[idx].append(j)
                self._adj[j].append(idx)
        return idx

    def _should_link(self, a: DagNode, b: DagNode) -> bool:
        if a.signatures & b.signatures:
            return True
        return ast_similarity(a.expr, b.expr) >= self.edge_similarity

    def neighbors(self, index: int) -> list[int]:
        return list(self._adj[index])

    def sample_parents(
        self,
        k: int = 3,
        temperature: float = 1.0,
        global_epsilon: float = 0.15,
        rng: random.Random | None = None,
    ) -> list[str]:
        """Sample parent expression strings from high-fitness neighborhoods.

        With probability ``global_epsilon`` each draw is uniform over all nodes
        (diversity insurance); otherwise softmax over fitness among a seed node
        and its neighbors.
        """
        if not self.nodes or k <= 0:
            return []
        rng = rng or random.Random()
        out: list[str] = []
        for _ in range(k):
            if rng.random() < global_epsilon or not any(self._adj):
                choice = rng.choice(self.nodes)
                out.append(choice.expression)
                continue
            seed_idx = self._softmax_index(
                [n.fitness for n in self.nodes], temperature, rng
            )
            pool_idx = [seed_idx] + self._adj[seed_idx]
            if not pool_idx:
                pool_idx = list(range(len(self.nodes)))
            weights = [self.nodes[i].fitness for i in pool_idx]
            pick = pool_idx[self._softmax_index(weights, temperature, rng)]
            out.append(self.nodes[pick].expression)
        return out

    @staticmethod
    def _softmax_index(
        values: list[float], temperature: float, rng: random.Random
    ) -> int:
        if not values:
            raise ValueError("empty softmax")
        t = max(temperature, 1e-6)
        shifted = [(v if math.isfinite(v) else 0.0) / t for v in values]
        m = max(shifted)
        exps = [math.exp(v - m) for v in shifted]
        total = sum(exps) or 1.0
        probs = [e / total for e in exps]
        r = rng.random()
        acc = 0.0
        for i, p in enumerate(probs):
            acc += p
            if r <= acc:
                return i
        return len(values) - 1


def build_dag_from_library(
    expressions: list[str],
    fitnesses: list[float] | None = None,
    edge_similarity: float = 0.35,
) -> ExpressionDag:
    """Build a DAG from expression strings and optional fitness scores."""
    dag = ExpressionDag(edge_similarity=edge_similarity)
    fitnesses = fitnesses or [0.0] * len(expressions)
    for text, fit in zip(expressions, fitnesses):
        try:
            dag.add(text, fitness=fit)
        except Exception:
            continue
    return dag


__all__ = ["DagNode", "ExpressionDag", "build_dag_from_library"]
