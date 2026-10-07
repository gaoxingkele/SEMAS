"""AST originality and complexity gates for formulaic factor expressions.

Inspired by AlphaAgent-style regularization: reject near-duplicate or
over-complex mutations before expensive evaluation.
[source: arXiv:2502.16789]
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from china_a_share_alpha.evolution.factor_mutator import _collect_nodes, _node_count
from china_a_share_alpha.factor.expression import (
    BinaryOp,
    Const,
    FactorExpr,
    RollingBinaryOp,
    RollingOp,
    TernaryOp,
    UnaryOp,
    Var,
)
from china_a_share_alpha.factor.parser import parse_expression

DEFAULT_AST_SIMILARITY_TAU = 0.85
DEFAULT_MAX_DEPTH = 6
DEFAULT_MAX_NODES = 40


def expression_depth(node: FactorExpr) -> int:
    """Return the depth of an expression tree (leaf depth = 1)."""
    if isinstance(node, (UnaryOp, RollingOp)):
        return 1 + expression_depth(node.child)
    if isinstance(node, (BinaryOp, RollingBinaryOp)):
        return 1 + max(expression_depth(node.left), expression_depth(node.right))
    if isinstance(node, TernaryOp):
        return 1 + max(
            expression_depth(node.pred),
            expression_depth(node.if_true),
            expression_depth(node.if_false),
        )
    return 1


def complexity(node: FactorExpr) -> tuple[int, int]:
    """Return ``(depth, node_count)``."""
    return expression_depth(node), _node_count(node)


def _canonical_label(node: FactorExpr) -> str:
    """Structure-aware label that ignores floating constant magnitude."""
    if isinstance(node, Var):
        return f"Var:{node.name}"
    if isinstance(node, Const):
        return "Const"
    if isinstance(node, UnaryOp):
        return f"U:{node.op}"
    if isinstance(node, BinaryOp):
        return f"B:{node.op}"
    if isinstance(node, TernaryOp):
        return f"T:{node.op}"
    if isinstance(node, RollingOp):
        return f"R:{node.op}:{node.window}"
    if isinstance(node, RollingBinaryOp):
        return f"RB:{node.op}:{node.window}"
    return type(node).__name__


def subtree_signatures(node: FactorExpr) -> list[str]:
    """Return canonical signatures for every subtree root."""
    sigs: list[str] = []

    def walk(n: FactorExpr) -> str:
        if isinstance(n, (UnaryOp, RollingOp)):
            child = walk(n.child)
            sig = f"{_canonical_label(n)}({child})"
        elif isinstance(n, (BinaryOp, RollingBinaryOp)):
            left = walk(n.left)
            right = walk(n.right)
            sig = f"{_canonical_label(n)}({left},{right})"
        elif isinstance(n, TernaryOp):
            pred = walk(n.pred)
            t = walk(n.if_true)
            f = walk(n.if_false)
            sig = f"{_canonical_label(n)}({pred},{t},{f})"
        else:
            sig = _canonical_label(n)
        sigs.append(sig)
        return sig

    walk(node)
    return sigs


def ast_similarity(a: FactorExpr, b: FactorExpr) -> float:
    """Jaccard similarity over subtree signature multisets in ``[0, 1]``."""
    ca = Counter(subtree_signatures(a))
    cb = Counter(subtree_signatures(b))
    if not ca and not cb:
        return 1.0
    intersection = sum((ca & cb).values())
    union = sum((ca | cb).values())
    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def max_similarity_to_library(
    expr: FactorExpr,
    library: Iterable[FactorExpr | str],
) -> float:
    """Maximum AST similarity of ``expr`` against a library of expressions."""
    best = 0.0
    for item in library:
        other = parse_expression(item) if isinstance(item, str) else item
        best = max(best, ast_similarity(expr, other))
    return best


@dataclass(frozen=True)
class RegularizerConfig:
    enabled: bool = True
    similarity_tau: float = DEFAULT_AST_SIMILARITY_TAU
    max_depth: int = DEFAULT_MAX_DEPTH
    max_nodes: int = DEFAULT_MAX_NODES


@dataclass(frozen=True)
class GateResult:
    accepted: bool
    reason: str
    depth: int
    nodes: int
    max_similarity: float


def check_expression_gates(
    expr: FactorExpr,
    library: Iterable[FactorExpr | str] | None = None,
    config: RegularizerConfig | None = None,
) -> GateResult:
    """Apply complexity and AST-originality gates.

    When ``library`` is empty/None, only complexity gates run.
    """
    cfg = config or RegularizerConfig()
    depth, nodes = complexity(expr)
    if depth > cfg.max_depth:
        return GateResult(False, "max_depth", depth, nodes, 0.0)
    if nodes > cfg.max_nodes:
        return GateResult(False, "max_nodes", depth, nodes, 0.0)

    max_sim = 0.0
    if library is not None:
        lib = list(library)
        if lib:
            max_sim = max_similarity_to_library(expr, lib)
            if max_sim > cfg.similarity_tau:
                return GateResult(False, "ast_similarity", depth, nodes, max_sim)

    return GateResult(True, "ok", depth, nodes, max_sim)


def filter_library_by_ast(
    expressions: list[str],
    config: RegularizerConfig | None = None,
) -> list[str]:
    """Greedy keep-first filter: drop later expressions that are AST-near duplicates."""
    cfg = config or RegularizerConfig()
    kept: list[str] = []
    kept_exprs: list[FactorExpr] = []
    for text in expressions:
        try:
            expr = parse_expression(text)
        except Exception:
            continue
        gate = check_expression_gates(expr, kept_exprs, cfg)
        if gate.accepted:
            kept.append(text)
            kept_exprs.append(expr)
    return kept


__all__ = [
    "DEFAULT_AST_SIMILARITY_TAU",
    "DEFAULT_MAX_DEPTH",
    "DEFAULT_MAX_NODES",
    "GateResult",
    "RegularizerConfig",
    "ast_similarity",
    "check_expression_gates",
    "complexity",
    "expression_depth",
    "filter_library_by_ast",
    "max_similarity_to_library",
    "subtree_signatures",
]
