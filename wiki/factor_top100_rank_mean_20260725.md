# TOP100 should use a 20-day mean of completed factor ranks

Daily TOP100 selection should not be based on rolling Sharpe when the intended
decision variable is persistence of relative factor standing. The corrected
rule ranks each factor's completed daily long-short return across all factors,
delays the return by its 5D/10D holding horizon, and selects by the mean of
those daily percentile ranks over the preceding 20 trading days. Lower mean
rank is better. [source: local ranked-reentry TOP100 audit, 2026-07-25]

The corrected protocol produces 245 TOP100 dates (24,500 membership rows) and
155 distinct selected factors, beginning 2025-07-07. Its all-factor median
Sharpe is 1.036, 1.029, and 0.425 for 5/10/20-day cooldowns; corresponding
median drawdowns are -56.77%, -56.20%, and -52.88%. The 20-day rank mean is
more responsive than the prior 60-day Sharpe ranking but does not by itself
solve repeated-episode drawdown. [source: local artifacts
ranked_reentry_top100_rankmean20/ranked_reentry_drawdown_summary.csv and
daily_top_100_rolling_rank_mean_20d_membership.csv]
