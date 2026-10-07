# Factor scores need both calibration and executable-return tests

**Date:** 2026-09-13
**Status:** completed diagnostic audit

## Claim

A factor is more useful when a higher score predicts better individual-stock
outcomes, not merely when one top-quantile portfolio happened to earn money.
Factor evaluation should therefore retain two separate views:

1. calibration: the outcome distribution of each entry-time 0--100 score band;
2. execution: the realized T+1 portfolio return, Sharpe, win rate, drawdown, and
   exit behavior under the declared trading policy.

[source: wiki/factor_recent_all_expression_audit_20260913.md]

## Contract

- The signal is observed on D and entry occurs at D+1 open.
- A buy-day sale is forbidden. Board-aware cumulative stops, limit-down queues,
  trailing profit, and D+6/D+11/D+21 forced exits remain active.
- Each day's factor values are converted to cross-sectional percentile scores.
  Ten buckets cover 0--10 through 90--100.
- An effective trade has positive net return. A target hit means the applicable
  board-specific profit trigger was reached before exit.
- Realized best horizon maximizes 40% of 2025 annualized return plus 60% of 2026
  YTD annualized return. Maximum favorable excursion (MFE) is reported
  separately and is not treated as realized return.

[source: wiki/factor_t1_board_exit_full_library_audit_20260831.md]

## Observation

The complete audit contains 42,840 unique score-bucket rows for all 119 current
expressions, two recent periods, three horizons, two gates, three universes, and
ten score buckets. Of 2,124 usable score profiles, 1,783 have positive Spearman
score/return monotonicity. Where both extreme bands have observations, 1,740 of
2,020 profiles have higher average return in the top 20% than the bottom 20%.

For all-stock contracts, the best realized horizon is 5 days in 31 cases, 10
days in 122, and 20 days in 81. The MFE horizon is almost always 20 days because
a longer observation window mechanically offers more opportunity to register a
higher peak. MFE is therefore useful as a profit-taking diagnostic but is a poor
standalone ranking target.

The leading realized all-stock contract is
`cs_rank(ts_zscore(high, 20))` with the MA20 entry gate and a 10-day horizon.
Its weighted recent annualized return is 37.50%; 2025/2026-YTD Sharpe values are
1.108/2.146 and the worst recent drawdown is -9.36%. Its pooled top-20% score
trades have a 47.92% positive-return rate but a 1.45% average net return, showing
why win rate and payoff size must be read together.

## Consequence

Do not rank on maximum observed floating profit alone. Use realized return as
the primary ordering, then require score calibration, adequate bucket sample
size, cross-period Sharpe, drawdown, profit factor, and payoff diagnostics.
Equivalent expressions should also be clustered before promotion so syntactic
variants do not crowd the top of the table.

## Artifacts

- `china_a_share_alpha/scripts/run_factor_score_bucket_audit.py`
- `china_a_share_alpha/examples/factor_score_bucket_audit.yaml`
- `china_a_share_alpha_output/factor_score_bucket_audit/run_20260913/REPORT.md`
- `china_a_share_alpha_output/factor_score_bucket_audit/run_20260913/score_bucket_metrics.parquet`
- `china_a_share_alpha_output/factor_score_bucket_audit/run_20260913/factor_score_profiles.csv`
- `china_a_share_alpha_output/factor_score_bucket_audit/run_20260913/max_horizon_factor_rankings.csv`
- `china_a_share_alpha_output/factor_score_bucket_audit/run_20260913/max_peak_factor_rankings.csv`
