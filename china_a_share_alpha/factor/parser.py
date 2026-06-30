"""Parse factor expression strings into FactorExpr trees.

The DSL uses function-call syntax:

    ts_mean(close, 5)
    cs_rank(ts_mean(return, 10))
    neg(cs_rank(ts_mean(return, 5)))
    add(close, open)
    div(sub(close, open), open)

Supported functions:
- Unary: abs, log, sign, neg, cs_rank, cs_zscore
- Binary: add, sub, mul, div, greater, less
- Rolling (time-series): ts_mean, ts_std, ts_sum, ts_min, ts_max, ts_delta, ts_delay
- Rolling binary: ts_corr, ts_cov

Variables: open, high, low, close, volume, vwap, return
"""

from __future__ import annotations

import ast
from typing import Any

from china_a_share_alpha.factor.expression import (
    BinaryOp,
    Const,
    FactorExpr,
    RollingBinaryOp,
    RollingOp,
    UnaryOp,
    Var,
)

UNARY_FUNCS = {"abs", "log", "sign", "neg", "cs_rank", "cs_zscore", "signed_power", "winsorize"}
BINARY_FUNCS = {"add", "sub", "mul", "div", "greater", "less", "if_positive"}
ROLLING_FUNCS = {"ts_mean", "ts_std", "ts_sum", "ts_min", "ts_max", "ts_delta", "ts_delay", "ts_shift", "ts_ema", "ts_pct_change", "ts_zscore"}
ROLLING_BINARY_FUNCS = {"ts_corr", "ts_cov"}
ALL_FUNCS = UNARY_FUNCS | BINARY_FUNCS | ROLLING_FUNCS | ROLLING_BINARY_FUNCS


def _norm_name(name: str) -> str:
    if name == "_ret_":
        return "return"
    return name


def _parse_node(node: ast.AST) -> FactorExpr:
    if isinstance(node, ast.Constant):
        return Const(value=float(node.value))

    if isinstance(node, ast.Name):
        name = _norm_name(node.id)
        if name in ALL_FUNCS:
            raise ValueError(f"Function '{name}' must be called with arguments")
        return Var(name=name)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are supported")
        func_name = node.func.id

        if func_name in UNARY_FUNCS:
            if len(node.args) != 1:
                raise ValueError(f"{func_name} expects 1 argument, got {len(node.args)}")
            return UnaryOp(op=func_name, child=_parse_node(node.args[0]))

        if func_name in BINARY_FUNCS:
            if len(node.args) != 2:
                raise ValueError(f"{func_name} expects 2 arguments, got {len(node.args)}")
            return BinaryOp(
                op=func_name,
                left=_parse_node(node.args[0]),
                right=_parse_node(node.args[1]),
            )

        if func_name in ROLLING_FUNCS:
            if len(node.args) != 2:
                raise ValueError(f"{func_name} expects 2 arguments, got {len(node.args)}")
            return RollingOp(
                op=func_name,
                child=_parse_node(node.args[0]),
                window=int(ast.literal_eval(node.args[1])),
            )

        if func_name in ROLLING_BINARY_FUNCS:
            if len(node.args) != 3:
                raise ValueError(f"{func_name} expects 3 arguments, got {len(node.args)}")
            return RollingBinaryOp(
                op=func_name,
                left=_parse_node(node.args[0]),
                right=_parse_node(node.args[1]),
                window=int(ast.literal_eval(node.args[2])),
            )

        raise ValueError(f"Unknown function: {func_name}")

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # Allow `-x` as shorthand for neg(x)
        return UnaryOp(op="neg", child=_parse_node(node.operand))

    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def parse_expression(expr_str: str) -> FactorExpr:
    """Parse a DSL expression string into a FactorExpr tree."""
    # `return` is a Python keyword; substitute it for parsing.
    safe = expr_str.replace("return", "_ret_")
    tree = ast.parse(safe, mode="eval")
    return _parse_node(tree.body)


def expression_to_string(expr: FactorExpr) -> str:
    """Convert a FactorExpr tree back to DSL string."""
    return str(expr)
