"""Tests for modern RSI seed library used in Stage-1+ paper track."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from china_a_share_alpha.factor.parser import parse_expression

SEED_CSV = Path("china_a_share_alpha/examples/rsi_modern_seed_library.csv")


def test_rsi_modern_seed_library_parses():
    assert SEED_CSV.exists()
    df = pd.read_csv(SEED_CSV)
    assert "expression" in df.columns
    assert len(df) >= 8
    for text in df["expression"].astype(str):
        expr = parse_expression(text)
        assert "rsi" in str(expr).lower() or "rsi_14" in text
