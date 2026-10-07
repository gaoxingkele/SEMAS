"""Combination-aware (synergy) objectives for factor libraries.

AlphaGen-style pool metrics: evaluate the equal-weight ensemble rather than
only single-factor IC when deciding what to keep / report.
[source: arXiv:2306.12964]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from china_a_share_alpha.evaluator.metrics import ic_score, rank_ic_score
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-8)
    )


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1 or s.empty:
        return s
    return s.groupby(level="symbol").transform(
        lambda x: x.ewm(span=span, min_periods=1).mean()
    )


def build_ensemble_signal(
    expressions: list[str],
    panel: pd.DataFrame,
    *,
    smooth_span: int = 10,
    min_factor_coverage: float = 0.5,
) -> tuple[pd.Series, dict[str, Any]]:
    """Equal-weight cross-sectional ensemble of parsed factor expressions."""
    frames: list[pd.Series] = []
    errors: list[str] = []
    for text in expressions:
        try:
            series = parse_expression(text).eval(panel)
            frames.append(_zscore(pd.to_numeric(series, errors="coerce")))
        except Exception as exc:  # noqa: BLE001 — keep one bad factor from aborting
            errors.append(f"{text[:80]}: {exc}")

    receipt: dict[str, Any] = {
        "n_requested": len(expressions),
        "n_evaluated": len(frames),
        "errors": errors,
        "smooth_span": smooth_span,
        "min_factor_coverage": min_factor_coverage,
    }
    if not frames:
        empty = pd.Series(np.nan, index=panel.index, dtype=float)
        receipt["valid"] = False
        receipt["reason"] = "no_valid_factors"
        return empty, receipt

    stacked = pd.concat(frames, axis=1)
    coverage = stacked.notna().sum(axis=1) / float(len(frames))
    mean_signal = stacked.mean(axis=1, skipna=True)
    mean_signal = mean_signal.where(coverage >= min_factor_coverage)
    mean_signal = _smooth(mean_signal, smooth_span)
    receipt["valid"] = bool(mean_signal.notna().any())
    receipt["mean_coverage"] = float(coverage.mean())
    return mean_signal, receipt


def pool_ic_metrics(
    expressions: list[str],
    panel: pd.DataFrame,
    *,
    forward_col: str = "forward_return",
    smooth_span: int = 10,
    min_factor_coverage: float = 0.5,
) -> dict[str, Any]:
    """Compute pool IC / RankIC for an equal-weight ensemble on one panel."""
    signal, receipt = build_ensemble_signal(
        expressions,
        panel,
        smooth_span=smooth_span,
        min_factor_coverage=min_factor_coverage,
    )
    if not receipt.get("valid"):
        return {
            "valid": False,
            "pool_ic": float("nan"),
            "pool_rank_ic": float("nan"),
            "receipt": receipt,
        }
    forward = panel[forward_col]
    return {
        "valid": True,
        "pool_ic": float(ic_score(signal, forward)),
        "pool_rank_ic": float(rank_ic_score(signal, forward)),
        "receipt": receipt,
    }


def load_expressions_from_csv(path: Path | str, top_n: int | None = None) -> list[str]:
    """Load expression column from a factor library CSV."""
    df = pd.read_csv(path)
    if "expression" not in df.columns:
        return []
    exprs = df["expression"].dropna().astype(str).tolist()
    if top_n is not None:
        exprs = exprs[:top_n]
    return exprs


def compare_pool_ic(
    candidate_csv: Path | str,
    baseline_csv: Path | str,
    panel: pd.DataFrame,
    *,
    top_n: int = 10,
    smooth_span: int = 10,
    min_factor_coverage: float = 0.5,
) -> dict[str, Any]:
    """Compare candidate vs baseline library pool IC on the same panel."""
    cand = load_expressions_from_csv(candidate_csv, top_n=top_n)
    base = load_expressions_from_csv(baseline_csv, top_n=top_n)
    cand_m = pool_ic_metrics(
        cand, panel, smooth_span=smooth_span, min_factor_coverage=min_factor_coverage
    )
    base_m = pool_ic_metrics(
        base, panel, smooth_span=smooth_span, min_factor_coverage=min_factor_coverage
    )
    delta = None
    if cand_m["valid"] and base_m["valid"]:
        delta = cand_m["pool_ic"] - base_m["pool_ic"]
    return {
        "candidate": cand_m,
        "baseline": base_m,
        "delta_pool_ic": delta,
        "improved": bool(delta is not None and delta > 0),
    }


__all__ = [
    "build_ensemble_signal",
    "compare_pool_ic",
    "load_expressions_from_csv",
    "pool_ic_metrics",
]
