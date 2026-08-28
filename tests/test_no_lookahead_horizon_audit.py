from china_a_share_alpha.scripts.run_no_lookahead_horizon_audit import (
    apply_stability_verdict,
    classify_horizon_value,
)


def _metrics(ic: float, spread: float, sharpe: float, annual_return: float) -> dict:
    return {
        "native_ic": {"mean_spearman": ic},
        "layers_native": {"top_minus_bottom": spread},
        "selected_hold": {"sharpe": sharpe, "annualized_return": annual_return},
    }


def test_classifies_robust_research_and_execution_value() -> None:
    metrics = _metrics(0.01, 0.005, 0.8, 0.1)
    assert classify_horizon_value(metrics, metrics) == "ROBUST_RESEARCH_AND_EXECUTION_VALUE"


def test_classifies_statistical_value_when_execution_fails() -> None:
    validation = _metrics(0.01, 0.005, -0.2, -0.03)
    test = _metrics(0.02, 0.006, 0.8, 0.1)
    assert classify_horizon_value(validation, test) == "STATISTICAL_VALUE_ONLY"


def test_classifies_no_robust_value_when_both_fail() -> None:
    validation = _metrics(-0.01, -0.005, -0.2, -0.03)
    test = _metrics(0.02, 0.006, 0.8, 0.1)
    assert classify_horizon_value(validation, test) == "NO_ROBUST_VALUE"


def test_downgrades_robust_verdict_on_annual_reversal() -> None:
    train = _metrics(0.01, 0.005, 0.8, 0.1)
    annual = {
        "2024": {"annualized_return": -0.01},
        "2025": {"annualized_return": 0.2},
    }
    assert (
        apply_stability_verdict("ROBUST_RESEARCH_AND_EXECUTION_VALUE", train, annual)
        == "RESEARCH_AND_EXECUTION_VALUE_REGIME_SENSITIVE"
    )
