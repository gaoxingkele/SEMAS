from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.scripts.run_factor_mining_loop import load_state
from china_a_share_alpha.scripts.run_frozen_promotion_audit import (
    _sha256_file,
    reconcile_states,
)
from china_a_share_alpha.scripts.run_multihizon_audit import (
    _build_equal_weight_signal,
    evaluate_library_hold,
)


def _test_panel(n_symbols: int = 30, n_days: int = 40) -> pd.DataFrame:
    symbols = [f"S{i:03d}" for i in range(n_symbols)]
    dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
    index = pd.MultiIndex.from_product([symbols, dates], names=["symbol", "date"])
    symbol_offset = np.repeat(np.linspace(-0.02, 0.02, n_symbols), n_days)
    day_cycle = np.tile(np.sin(np.arange(n_days) / 5) * 0.002, n_symbols)
    daily_return = symbol_offset / 10 + day_cycle
    close = 100 * pd.Series(1 + daily_return, index=index).groupby(level="symbol").cumprod()
    return pd.DataFrame(
        {
            "close": close,
            "high": close * 1.01,
            "volume": 1_000 + np.arange(len(index)) % 100,
            "return": daily_return,
        },
        index=index,
    )


def test_equal_weight_signal_uses_coverage_threshold_not_complete_cases():
    panel = _test_panel(n_symbols=4, n_days=10)
    dense = panel["close"]
    sparse = dense.where(np.arange(len(dense)) % 2 == 0)

    signal, receipt = _build_equal_weight_signal(
        {"dense": dense, "sparse": sparse},
        smooth_span=1,
        min_factor_coverage=0.5,
    )

    assert len(signal) == len(dense)
    assert receipt["min_required_factors"] == 1
    assert receipt["valid_row_fraction"] == 1.0


def test_library_receipt_keeps_duplicate_factor_labels_distinct():
    panel = _test_panel()
    library = pd.DataFrame(
        {
            "factor": ["duplicate", "duplicate"],
            "expression": ["close", "volume"],
        }
    )

    receipt = evaluate_library_hold(
        library,
        panel,
        horizon=5,
        transaction_cost=0.001,
        smooth_span=1,
        evaluation_mode="simple_hold",
    )

    assert receipt["valid"] is True
    assert receipt["n_factors_evaluated"] == 2
    assert receipt["n_observations"] > 1


def test_dynamic_trim_receipt_is_valid_on_dense_library():
    panel = _test_panel()
    library = pd.DataFrame({"factor": ["price", "liquidity"], "expression": ["close", "volume"]})

    receipt = evaluate_library_hold(
        library,
        panel,
        horizon=5,
        transaction_cost=0.001,
        smooth_span=1,
        evaluation_mode="dynamic_trim",
    )

    assert receipt["valid"] is True
    assert receipt["n_observations"] > 1
    assert np.isfinite(receipt["sharpe"])


def test_hold_evaluation_uses_past_history_before_test_fold():
    panel = _test_panel(n_days=40)
    cutoff = panel.index.get_level_values("date").unique()[20]
    history = panel[panel.index.get_level_values("date") < cutoff]
    test = panel[panel.index.get_level_values("date") >= cutoff]
    library = pd.DataFrame({"factor": ["price"], "expression": ["close"]})

    receipt = evaluate_library_hold(
        library,
        test,
        horizon=5,
        transaction_cost=0.001,
        smooth_span=10,
        evaluation_mode="simple_hold",
        history_data=history,
    )

    assert receipt["valid"] is True
    assert receipt["history_rows"] == len(history)
    assert receipt["n_observations"] == 20


def test_invalid_library_receipt_is_not_a_zero_score():
    panel = _test_panel()
    library = pd.DataFrame({"factor": ["bad"], "expression": ["unknown_operator(close)"]})

    receipt = evaluate_library_hold(
        library,
        panel,
        horizon=5,
        transaction_cost=0.001,
        smooth_span=1,
        evaluation_mode="dynamic_trim",
    )

    assert receipt["valid"] is False
    assert "sharpe" not in receipt
    assert receipt["n_factors_evaluated"] == 0
    assert receipt["error"] == "insufficient valid factors: 0/1; required 1"


def test_load_state_keeps_latest_entry_per_iteration(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "iteration": 45,
                "history": [
                    {"iteration": 44, "timestamp": "a"},
                    {"iteration": 45, "timestamp": "old"},
                    {"iteration": 45, "timestamp": "new"},
                ],
            }
        ),
        encoding="utf-8",
    )

    state = load_state(state_path)

    assert [entry["iteration"] for entry in state["history"]] == [44, 45]
    assert state["history"][-1]["timestamp"] == "new"
    assert state["state_schema_version"] == 2


def test_all_horizon_configs_have_explicit_promotion_contract():
    root = Path(__file__).parent.parent / "china_a_share_alpha" / "examples"
    expected = {
        "factor_mining_loop_config.yaml": (5, "dynamic_trim"),
        "factor_mining_loop_config_iter23_10d.yaml": (10, "simple_hold"),
        "factor_mining_loop_config_iter22_20d.yaml": (20, "simple_hold"),
    }
    for filename, (horizon, mode) in expected.items():
        config = yaml.safe_load((root / filename).read_text(encoding="utf-8"))
        assert config["use_hold_sharpe_gate"] is True
        assert config["hold_horizon"] == horizon
        assert config["promotion_evaluation_mode"] == mode
        assert config["min_factor_coverage"] == 0.5
    research_config = yaml.safe_load(
        (root / "factor_mining_loop_config_iter22_20d.yaml").read_text(encoding="utf-8")
    )
    assert research_config["promotion_enabled"] is False


def test_reconcile_state_requires_matching_library_and_iteration(tmp_path: Path):
    library_path = tmp_path / "live.csv"
    library_path.write_text("factor,expression\nfactor_1,close\n", encoding="utf-8")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "iteration": 2,
                "history": [
                    {"iteration": 2, "timestamp": "old"},
                    {"iteration": 2, "timestamp": "new"},
                ],
            }
        ),
        encoding="utf-8",
    )
    result = {
        "name": "test-live",
        "verdict": "PASS",
        "valid": True,
        "evaluation_mode": "simple_hold",
        "horizon": 5,
        "transaction_cost": 0.001,
        "smooth_span": 10,
        "min_factor_coverage": 0.5,
        "n_library_rows": 1,
        "n_factors_evaluated": 1,
        "valid_rows": 100,
        "valid_row_fraction": 1.0,
        "sharpe": 1.5,
        "annualized_return": 0.2,
        "cost_adjusted_return": 0.2,
        "max_drawdown": -0.1,
        "n_observations": 50,
        "library_path": str(library_path),
        "library_sha256": _sha256_file(library_path),
        "state_path": str(state_path),
        "state_iteration": 2,
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "snapshot_verified": True,
                "snapshot_id": "snapshot",
                "created_at": "2026-07-13T00:00:00+00:00",
                "results": [result],
            }
        ),
        encoding="utf-8",
    )

    actions = reconcile_states(receipt_path, apply=True)
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert actions[0]["applied"] is True
    assert len(state["history"]) == 1
    assert state["best_hold_sharpe"] == 1.5
    assert state["promotion_baseline"]["snapshot_id"] == "snapshot"
