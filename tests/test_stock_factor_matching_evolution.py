from __future__ import annotations

import pandas as pd

from china_a_share_alpha.scripts.evolve_stock_factor_matching import (
    MatchingGenome,
    fold_forward_returns,
    matching_weights,
)


def test_fold_forward_returns_do_not_cross_fold_boundary() -> None:
    dates = pd.date_range("2026-01-01", periods=5, freq="B")
    index = pd.MultiIndex.from_product([["000001.SZ"], dates], names=["symbol", "date"])
    panel = pd.DataFrame({"close": [10, 11, 12, 13, 14]}, index=index)
    labels = fold_forward_returns(panel, 2)
    assert labels.iloc[-2:].isna().all()


def test_matching_weights_are_normalized_and_top_k_bounded() -> None:
    libraries = ["a", "b", "c"]
    utilities = {
        "stock": pd.DataFrame([[0.3, 0.2, -0.1]], index=["000001.SZ"], columns=libraries),
        "stock_observations": pd.DataFrame(
            [[200, 200, 200]], index=["000001.SZ"], columns=libraries
        ),
        "industry": pd.DataFrame([[0.2, 0.1, 0.0]], index=["银行"], columns=libraries),
        "market": pd.DataFrame([[0.1, 0.2, 0.0]], index=["主板"], columns=libraries),
        "global": pd.Series([0.1, 0.1, 0.1], index=libraries),
        "metadata": pd.DataFrame(
            {"industry": ["银行"], "market": ["主板"]}, index=["000001.SZ"]
        ),
    }
    genome = MatchingGenome(2, 0.5, 0.2, 0.2, 0.1, 100, 0.2)
    weights = matching_weights(genome, utilities)
    assert (weights.loc["000001.SZ"] > 0).sum() == 2
    assert weights.loc["000001.SZ"].sum() == 1.0
