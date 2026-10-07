import pandas as pd

from china_a_share_alpha.scripts.run_recent_all_factor_audit import (
    build_expression_catalog,
    build_rankings,
    expected_result_rows,
    expression_id,
    invalid_backtest_metrics,
    signal_quality,
)


def test_expression_catalog_deduplicates_and_tracks_sources():
    libraries = pd.DataFrame(
        [
            {
                "library_id": "a",
                "source_paths": ["one.csv"],
                "expressions": ("close", "open"),
            },
            {
                "library_id": "b",
                "source_paths": ["two.csv"],
                "expressions": ("close",),
            },
        ]
    )
    catalog = build_expression_catalog(libraries).set_index("expression")
    assert len(catalog) == 2
    assert catalog.loc["close", "library_count"] == 2
    assert catalog.loc["open", "expression_id"] == expression_id("open")


def test_expected_result_rows_matches_full_contract():
    assert expected_result_rows(119, 3, 3, 2, 3) == 6426


def test_rankings_require_both_recent_periods_to_pass():
    rows = []
    for factor, values in {"good": [0.5, 1.0, 0.8], "bad": [0.5, 1.0, -0.1]}.items():
        for period, sharpe in zip(["2024", "2025", "2026_ytd"], values):
            rows.append(
                {
                    "expression_id": factor,
                    "expression": factor,
                    "horizon": 10,
                    "gate": "none",
                    "universe": "all_stocks",
                    "period": period,
                    "sharpe": sharpe,
                    "max_drawdown": -0.10,
                    "return_concentration": 0.05,
                    "rank_ic_mean": 0.01,
                    "valid": True,
                }
            )
    ranked = build_rankings(pd.DataFrame(rows)).set_index("expression_id")
    assert bool(ranked.loc["good", "effective"])
    assert not bool(ranked.loc["bad", "effective"])


def test_invalid_backtest_metrics_do_not_report_performance():
    metrics = invalid_backtest_metrics(10, 243)
    assert not metrics["valid"]
    assert pd.isna(metrics["sharpe"])
    assert metrics["n_trades"] == 0


def test_signal_quality_rejects_constant_cross_section():
    index = pd.MultiIndex.from_product(
        [["A", "B"], pd.date_range("2026-01-01", periods=25)],
        names=["symbol", "date"],
    )
    quality = signal_quality(pd.Series(1.0, index=index), 0.5, 20)
    assert not quality["signal_valid"]
    assert quality["signal_status"] == "insufficient_cross_sectional_variation"
