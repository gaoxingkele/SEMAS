"""Factor expression tree and evaluation.

The design follows Qlib-style operators (ts_* for time-series, cs_* for
cross-sectional) so that expressions can be mapped to Qlib ExpressionOps or
executed directly with pandas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


class FactorExpr(ABC):
    """Base class for a factor expression node."""

    @abstractmethod
    def eval(self, data: pd.DataFrame) -> pd.Series:
        """Return a Series indexed like `data` (MultiIndex symbol/date)."""

    def to_string(self) -> str:
        """Human-readable string representation."""
        return repr(self)

    def copy(self) -> FactorExpr:
        """Deep copy of the expression tree."""
        import copy

        return copy.deepcopy(self)


@dataclass
class Var(FactorExpr):
    name: str

    def eval(self, data: pd.DataFrame) -> pd.Series:
        return data[self.name]

    def __repr__(self) -> str:
        return self.name


@dataclass
class Const(FactorExpr):
    value: float

    def eval(self, data: pd.DataFrame) -> pd.Series:
        return pd.Series(self.value, index=data.index, dtype=float)

    def __repr__(self) -> str:
        return f"{self.value:.4g}"


def _winsorize(s: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Cross-sectional winsorization by percentile."""
    q_low = s.quantile(lower)
    q_high = s.quantile(upper)
    return s.clip(lower=q_low, upper=q_high)


@dataclass
class UnaryOp(FactorExpr):
    op: str  # abs, log, sign, neg, cs_rank, cs_zscore, signed_power, winsorize
    child: FactorExpr

    def eval(self, data: pd.DataFrame) -> pd.Series:
        x = self.child.eval(data)
        if self.op == "abs":
            return x.abs()
        if self.op == "log":
            return np.log(x.replace(0, np.nan))
        if self.op == "sign":
            return np.sign(x)
        if self.op == "neg":
            return -x
        if self.op == "cs_rank":
            return x.groupby(level="date").rank(pct=True)
        if self.op == "cs_zscore":
            return x.groupby(level="date").transform(lambda s: (s - s.mean()) / (s.std() + 1e-8))
        if self.op == "signed_power":
            return np.sign(x) * (np.abs(x) ** 0.5)
        if self.op == "winsorize":
            return x.groupby(level="date").transform(_winsorize)
        raise ValueError(f"Unknown unary op: {self.op}")

    def __repr__(self) -> str:
        return f"{self.op}({self.child})"


@dataclass
class BinaryOp(FactorExpr):
    op: str  # add, sub, mul, div, greater, less
    left: FactorExpr
    right: FactorExpr

    def eval(self, data: pd.DataFrame) -> pd.Series:
        l = self.left.eval(data)
        r = self.right.eval(data)
        if self.op == "add":
            return l + r
        if self.op == "sub":
            return l - r
        if self.op == "mul":
            return l * r
        if self.op == "div":
            return l / (r.replace(0, np.nan))
        if self.op == "greater":
            return (l > r).astype(float)
        if self.op == "less":
            return (l < r).astype(float)
        if self.op == "if_positive":
            return ((l > 0).astype(float) * r).fillna(0)
        raise ValueError(f"Unknown binary op: {self.op}")

    def __repr__(self) -> str:
        return f"{self.op}({self.left}, {self.right})"


@dataclass
class TernaryOp(FactorExpr):
    """Three-operand operator, e.g. if_else(predicate, if_true, if_false)."""

    op: str  # if_else
    pred: FactorExpr
    if_true: FactorExpr
    if_false: FactorExpr

    def eval(self, data: pd.DataFrame) -> pd.Series:
        p = self.pred.eval(data)
        t = self.if_true.eval(data)
        f = self.if_false.eval(data)
        if self.op == "if_else":
            mask = p > 0
            return t.where(mask, f)
        raise ValueError(f"Unknown ternary op: {self.op}")

    def __repr__(self) -> str:
        return f"{self.op}({self.pred}, {self.if_true}, {self.if_false})"


@dataclass
class RollingOp(FactorExpr):
    op: str  # ts_mean, ts_std, ts_sum, ts_min, ts_max, ts_delta, ts_delay
    child: FactorExpr
    window: int

    def eval(self, data: pd.DataFrame) -> pd.Series:
        x = self.child.eval(data)

        def _roll(group: pd.Series) -> pd.Series:
            if self.op == "ts_mean":
                return group.rolling(self.window, min_periods=1).mean()
            if self.op == "ts_std":
                return group.rolling(self.window, min_periods=1).std()
            if self.op == "ts_sum":
                return group.rolling(self.window, min_periods=1).sum()
            if self.op == "ts_min":
                return group.rolling(self.window, min_periods=1).min()
            if self.op == "ts_max":
                return group.rolling(self.window, min_periods=1).max()
            if self.op == "ts_delta":
                return group - group.shift(self.window)
            if self.op == "ts_delay":
                return group.shift(self.window)
            if self.op == "ts_shift":
                return group.shift(self.window)
            if self.op == "ts_ema":
                return group.ewm(span=self.window, min_periods=1).mean()
            if self.op == "ts_pct_change":
                return group.pct_change(periods=self.window)
            if self.op == "ts_zscore":
                ma = group.rolling(self.window, min_periods=1).mean()
                std = group.rolling(self.window, min_periods=1).std()
                return (group - ma) / (std + 1e-8)
            if self.op == "ts_rank":
                return group.rolling(self.window, min_periods=1).rank(pct=True)
            if self.op == "ts_argmax":
                return group.rolling(self.window, min_periods=1).apply(
                    lambda s: float(s.argmax()) / max(1, len(s) - 1), raw=True
                )
            if self.op == "ts_argmin":
                return group.rolling(self.window, min_periods=1).apply(
                    lambda s: float(s.argmin()) / max(1, len(s) - 1), raw=True
                )
            raise ValueError(f"Unknown rolling op: {self.op}")

        return x.groupby(level="symbol").transform(_roll)

    def __repr__(self) -> str:
        return f"{self.op}({self.child}, {self.window})"


@dataclass
class RollingBinaryOp(FactorExpr):
    op: str  # ts_corr, ts_cov
    left: FactorExpr
    right: FactorExpr
    window: int

    def eval(self, data: pd.DataFrame) -> pd.Series:
        l = self.left.eval(data)
        r = self.right.eval(data)

        def _roll(group: pd.DataFrame) -> pd.Series:
            # If either series is constant within the rolling window, correlation/covariance
            # is mathematically undefined; return NaN to avoid spurious signals.
            if group["l"].nunique() <= 1 or group["r"].nunique() <= 1:
                return pd.Series(np.nan, index=group.index)
            if self.op == "ts_corr":
                return group["l"].rolling(self.window, min_periods=2).corr(group["r"])
            if self.op == "ts_cov":
                return group["l"].rolling(self.window, min_periods=2).cov(group["r"])
            raise ValueError(f"Unknown rolling binary op: {self.op}")

        tmp = pd.DataFrame({"l": l, "r": r}, index=data.index)
        return tmp.groupby(level="symbol").apply(_roll).reset_index(level=0, drop=True)

    def __repr__(self) -> str:
        return f"{self.op}({self.left}, {self.right}, {self.window})"


def expr_from_dict(d: dict[str, Any]) -> FactorExpr:
    """Deserialize an expression from a plain dict."""
    t = d["type"]
    if t == "var":
        return Var(name=d["name"])
    if t == "const":
        return Const(value=float(d["value"]))
    if t == "unary":
        return UnaryOp(op=d["op"], child=expr_from_dict(d["child"]))
    if t == "binary":
        return BinaryOp(op=d["op"], left=expr_from_dict(d["left"]), right=expr_from_dict(d["right"]))
    if t == "ternary":
        return TernaryOp(
            op=d["op"],
            pred=expr_from_dict(d["pred"]),
            if_true=expr_from_dict(d["if_true"]),
            if_false=expr_from_dict(d["if_false"]),
        )
    if t == "rolling":
        return RollingOp(op=d["op"], child=expr_from_dict(d["child"]), window=int(d["window"]))
    if t == "rolling_binary":
        return RollingBinaryOp(
            op=d["op"],
            left=expr_from_dict(d["left"]),
            right=expr_from_dict(d["right"]),
            window=int(d["window"]),
        )
    raise ValueError(f"Unknown node type: {t}")


def expr_to_dict(e: FactorExpr) -> dict[str, Any]:
    """Serialize an expression to a plain dict."""
    if isinstance(e, Var):
        return {"type": "var", "name": e.name}
    if isinstance(e, Const):
        return {"type": "const", "value": e.value}
    if isinstance(e, UnaryOp):
        return {"type": "unary", "op": e.op, "child": expr_to_dict(e.child)}
    if isinstance(e, BinaryOp):
        return {"type": "binary", "op": e.op, "left": expr_to_dict(e.left), "right": expr_to_dict(e.right)}
    if isinstance(e, TernaryOp):
        return {
            "type": "ternary",
            "op": e.op,
            "pred": expr_to_dict(e.pred),
            "if_true": expr_to_dict(e.if_true),
            "if_false": expr_to_dict(e.if_false),
        }
    if isinstance(e, RollingOp):
        return {"type": "rolling", "op": e.op, "child": expr_to_dict(e.child), "window": e.window}
    if isinstance(e, RollingBinaryOp):
        return {
            "type": "rolling_binary",
            "op": e.op,
            "left": expr_to_dict(e.left),
            "right": expr_to_dict(e.right),
            "window": e.window,
        }
    raise ValueError(f"Unknown node: {e}")
