"""Tests for Tushare-based backtest (skipped if no TUSHARE_TOKEN)."""

from __future__ import annotations

import os
import shutil

import pytest

from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.examples.tushare_factors import SINGLE_FACTORS
from china_a_share_alpha.factor.expression import FactorExpr


pytestmark = pytest.mark.skipif(
    not os.environ.get("TUSHARE_TOKEN"),
    reason="TUSHARE_TOKEN not set",
)


def test_load_tushare_data():
    train, test = load_tushare_data(
        {
            "start_date": "20240101",
            "end_date": "20240501",
            "split_date": "20240301",
            "universe": "csi300",
            "cache_dir": "./china_a_share_alpha_output/tushare_cache_test",
        }
    )
    assert "forward_return" in train.columns
    assert "forward_return" in test.columns
    assert len(train) + len(test) > 0


def test_single_factors_eval_on_tushare():
    train, test = load_tushare_data(
        {
            "start_date": "20240101",
            "end_date": "20240501",
            "split_date": "20240301",
            "universe": "csi300",
            "cache_dir": "./china_a_share_alpha_output/tushare_cache_test",
        }
    )
    data = test
    for name, expr in SINGLE_FACTORS.items():
        factor = expr.eval(data)
        assert len(factor) == len(data)
