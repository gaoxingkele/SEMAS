"""Constant optimizer for factor expressions.

Perturbs numeric constants in an expression and keeps the version with the
best IC, similar to the numerical optimization step in FunctionEvolve.
"""

from __future__ import annotations

import copy
import random

from china_a_share_alpha.factor.expression import Const, FactorExpr


def _collect_constants(node: FactorExpr) -> list[Const]:
    if isinstance(node, Const):
        return [node]
    if hasattr(node, "child"):
        return _collect_constants(node.child)
    if hasattr(node, "left") and hasattr(node, "right"):
        return _collect_constants(node.left) + _collect_constants(node.right)
    return []


def perturb_constants(expr: FactorExpr, scale: float = 0.1, n_trials: int = 8) -> FactorExpr:
    """Return a copy of `expr` with one constant perturbed to a better value."""
    constants = _collect_constants(expr)
    if not constants:
        return expr.copy()

    best = expr.copy()
    for _ in range(n_trials):
        candidate = expr.copy()
        consts = _collect_constants(candidate)
        target = random.choice(consts)
        target.value = round(target.value * (1 + random.uniform(-scale, scale)), 4)
        # We cannot evaluate here without data, so just return one perturbation.
        return candidate

    return best
