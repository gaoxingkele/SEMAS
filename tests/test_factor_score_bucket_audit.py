import numpy as np
import pandas as pd

from china_a_share_alpha.scripts.run_factor_score_bucket_audit import (
    _score_profile,
    build_max_horizon_rankings,
    expected_bucket_rows,
    summarize_score_bucket,
)


def test_expected_bucket_matrix_size():
    assert expected_bucket_rows(119, 2, 3, 2, 3, 10) == 42840


def test_bucket_summary_reports_effectiveness_and_target_hit():
    trades = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "entry_signal_date": pd.to_datetime(["2026-01-01"] * 3),
            "trade_return": [0.10, -0.05, 0.02],
            "profit_activated": [True, False, False],
            "peak_return": [0.20, 0.01, 0.05],
            "max_adverse_return": [-0.01, -0.10, -0.02],
            "post_buy_days": [5, 5, 5],
            "exit_reason": ["trailing_profit", "expiry", "expiry"],
        }
    )
    summary = summarize_score_bucket(trades, 5, 9)
    assert summary["effective_rate"] == 2 / 3
    assert summary["target_hit_rate"] == 1 / 3
    assert summary["average_return"] == np.mean([0.10, -0.05, 0.02])


def test_max_horizon_ranking_uses_weighted_recent_annual_return():
    rows = []
    for horizon, annual_2025, annual_2026 in [(5, 0.50, 0.10), (10, 0.20, 0.40), (20, 0.10, 0.10)]:
        for period, annual in [("2025", annual_2025), ("2026_ytd", annual_2026)]:
            rows.append(
                {
                    "expression_id": "x",
                    "expression": "close",
                    "horizon": horizon,
                    "gate": "none",
                    "universe": "all_stocks",
                    "period": period,
                    "valid": True,
                    "annualized_return": annual,
                    "total_return": annual / 2,
                    "sharpe": 1.0,
                    "win_rate": 0.5,
                    "max_drawdown": -0.1,
                }
            )
    profiles = pd.DataFrame(
        [
            {
                "expression_id": "x",
                "expression": "close",
                "horizon": horizon,
                "gate": "none",
                "universe": "all_stocks",
                "top20_average_peak_return": peak_return,
                "bottom20_average_peak_return": 0.01,
                "top_bottom_peak_return_spread": peak_return - 0.01,
            }
            for horizon, peak_return in [(5, 0.08), (10, 0.12), (20, 0.18)]
        ]
    )
    ranking = build_max_horizon_rankings(pd.DataFrame(rows), profiles)
    assert ranking.iloc[0]["best_horizon"] == 10
    assert ranking.iloc[0]["max_peak_horizon"] == 20


def test_score_profile_keeps_realized_and_peak_return_separate():
    rows = []
    for period in ["2025", "2026_ytd"]:
        for bucket, average_return, peak_return in [(0, -0.02, 0.04), (9, 0.03, 0.12)]:
            rows.append(
                {
                    "expression_id": "x",
                    "expression": "close",
                    "horizon": 10,
                    "gate": "none",
                    "universe": "all_stocks",
                    "period": period,
                    "score_bucket": bucket,
                    "status": "ok",
                    "n_trades": 10,
                    "positive_trades": 6 if bucket == 9 else 4,
                    "target_hits": 3 if bucket == 9 else 1,
                    "average_return": average_return,
                    "average_peak_return": peak_return,
                }
            )
    profile = _score_profile(pd.DataFrame(rows)).iloc[0]
    assert np.isclose(profile["top_bottom_return_spread"], 0.05)
    assert np.isclose(profile["top20_average_peak_return"], 0.12)
    assert np.isclose(profile["top_bottom_peak_return_spread"], 0.08)
