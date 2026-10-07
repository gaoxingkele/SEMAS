"""Unit tests for D1/D2/D3 Stage-1 paper-track modules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from china_a_share_alpha.evolution.ast_regularizer import (
    RegularizerConfig,
    ast_similarity,
    check_expression_gates,
    complexity,
    filter_library_by_ast,
)
from china_a_share_alpha.evolution.dag_neighborhood import build_dag_from_library
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.loop.synergy_objective import (
    build_ensemble_signal,
    pool_ic_metrics,
)


def test_ast_similarity_identical_and_distinct():
    a = parse_expression("cs_rank(ts_zscore(high, 20))")
    b = parse_expression("cs_rank(ts_zscore(high, 20))")
    c = parse_expression("ts_mean(volume, 5)")
    assert ast_similarity(a, b) == 1.0
    assert ast_similarity(a, c) < 0.5


def test_complexity_and_depth_gates():
    expr = parse_expression("cs_rank(ts_mean(return, 5))")
    depth, nodes = complexity(expr)
    assert depth >= 2
    assert nodes >= 3
    gate = check_expression_gates(
        expr,
        library=[],
        config=RegularizerConfig(max_depth=1, max_nodes=40),
    )
    assert gate.accepted is False
    assert gate.reason == "max_depth"


def test_ast_library_filter_drops_near_duplicates():
    exprs = [
        "cs_rank(ts_zscore(high, 20))",
        "cs_rank(ts_zscore(high, 20))",  # exact duplicate structure
        "ts_mean(volume, 5)",
    ]
    kept = filter_library_by_ast(
        exprs, RegularizerConfig(similarity_tau=0.9, max_depth=8, max_nodes=40)
    )
    assert kept[0] == exprs[0]
    assert "ts_mean(volume, 5)" in kept
    assert len(kept) == 2


def test_dag_neighborhood_samples_parents():
    exprs = [
        "cs_rank(ts_zscore(high, 20))",
        "cs_rank(ts_mean(return, 5))",
        "ts_mean(volume, 5)",
        "neg(cs_rank(ts_mean(return, 5)))",
    ]
    dag = build_dag_from_library(exprs, fitnesses=[1.0, 0.5, 0.1, 0.8])
    assert len(dag) == 4
    parents = dag.sample_parents(k=3, global_epsilon=0.0)
    assert len(parents) == 3
    assert all(p in exprs for p in parents)


def test_pool_ic_on_synthetic_panel():
    symbols = [f"S{i}" for i in range(8)]
    dates = pd.date_range("2024-01-01", periods=20, freq="B")
    index = pd.MultiIndex.from_product([symbols, dates], names=["symbol", "date"])
    rng = np.random.default_rng(0)
    close = pd.Series(100 + rng.normal(0, 1, len(index)).cumsum(), index=index)
    ret = close.groupby(level="symbol").pct_change().fillna(0.0)
    forward = ret.groupby(level="symbol").shift(-1)
    high = close * 1.01
    volume = pd.Series(1000 + rng.integers(0, 100, len(index)), index=index, dtype=float)
    panel = pd.DataFrame(
        {
            "close": close,
            "high": high,
            "volume": volume,
            "return": ret,
            "forward_return": forward,
        },
        index=index,
    ).dropna()

    exprs = ["cs_rank(ts_zscore(high, 5))", "ts_mean(volume, 3)"]
    signal, receipt = build_ensemble_signal(exprs, panel, smooth_span=1)
    assert receipt["n_evaluated"] == 2
    assert signal.notna().any()
    metrics = pool_ic_metrics(exprs, panel, smooth_span=1)
    assert metrics["valid"] is True
    assert np.isfinite(metrics["pool_ic"])
