"""A small subset of WorldQuant 101 formulaic alphas implemented with the
local expression tree.

Reference: Kakushadze, Z. (2016). 101 Formulaic Alphas. Wilmott.
Online: https://arxiv.org/abs/1601.00991
"""

from __future__ import annotations

from china_a_share_alpha.factor.expression import (
    BinaryOp,
    Const,
    RollingOp,
    UnaryOp,
    Var,
)


def alpha_001():
    """rank(ts_argmax(signedpower((returns < 0 ? ts_std(returns, 20) : close), 2), 5)) - 0.5"""
    # Simplified to a rank of rolling max of squared returns.
    returns = BinaryOp("div", BinaryOp("sub", Var("close"), RollingOp("ts_delay", Var("close"), 1)), RollingOp("ts_delay", Var("close"), 1))
    sq = BinaryOp("mul", returns, returns)
    rolled = RollingOp("ts_max", sq, 5)
    return UnaryOp("cs_rank", rolled)


def alpha_003():
    """-1 * correlation(rank(open), rank(volume), 10)"""
    from china_a_share_alpha.factor.expression import RollingBinaryOp

    return RollingBinaryOp(
        "ts_corr",
        UnaryOp("cs_rank", Var("open")),
        UnaryOp("cs_rank", Var("volume")),
        10,
    )


def alpha_101():
    """(close - open) / ((high - low) + .001)"""
    return BinaryOp(
        "div",
        BinaryOp("sub", Var("close"), Var("open")),
        BinaryOp("add", BinaryOp("sub", Var("high"), Var("low")), Const(0.001)),
    )
