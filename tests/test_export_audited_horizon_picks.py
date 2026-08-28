import numpy as np
import pandas as pd

from china_a_share_alpha.scripts.export_audited_horizon_picks import (
    build_combined_long_list,
    build_horizon_selection,
)


def test_build_horizon_selection_includes_exited_dynamic_longs() -> None:
    dates = pd.date_range("2026-01-01", periods=6, freq="B")
    symbols = [f"S{index:02d}" for index in range(20)]
    index = pd.MultiIndex.from_product([symbols, dates], names=["symbol", "date"])
    panel = pd.DataFrame({"return": 0.0}, index=index)
    values = []
    for symbol_index in range(20):
        for day_index in range(6):
            value = float(symbol_index)
            if day_index == 5 and symbol_index >= 16:
                value = float(-symbol_index)
            values.append(value)
    signal = pd.Series(values, index=index)
    schedule = np.array([1, 1, 0.7, 0.7, 0.5, 0.5, 0, 0, 0, 0], dtype=float)

    longs, shorts, metadata = build_horizon_selection(signal, panel, horizon=10, schedule=schedule)

    assert metadata["cohort_size"] == 4
    assert len(longs) == 4
    assert len(shorts) == 4
    assert (longs["action"] == "EXIT_0").any()


def test_combined_list_marks_consensus_and_component_only_names() -> None:
    long_5d = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "target_weight": [0.1, 0.1],
            "current_rank": [1, 2],
            "position_multiplier": [1.0, 0.7],
        }
    )
    long_10d = pd.DataFrame(
        {
            "symbol": ["B", "C"],
            "target_weight": [0.1, 0.1],
            "current_rank": [3, 4],
            "position_multiplier": [1.0, 1.0],
        }
    )

    combined = build_combined_long_list(long_5d, long_10d).set_index("symbol")

    assert combined.loc["B", "bucket"] == "CORE_5D_10D"
    assert combined.loc["A", "bucket"] == "PRIMARY_5D"
    assert combined.loc["C", "bucket"] == "SECONDARY_10D"
