# Dynamic factor selection, not synthetic stops, survives the frozen period

The aggregated TOP100 source is a candidate pool, not a deployable ranking: it
mixes synthetic/demo artifacts, single-loop leaderboards, and real-data runs.
All 100 expressions were therefore re-evaluated on a stock-disjoint historical
CSI500 panel. Each expression was tested at both 5D and 10D horizons; 2025 was
used for multi-dimensional selection and 2026 was held frozen. [source: local
artifact china_a_share_alpha_output/top100_factors_by_sharpe.csv]

The first round selected 12 static variants from 112 sufficiently covered
variants using 2025 Sharpe, IC, RankIC, ICIR, cost-adjusted return, maximum
drawdown, turnover, coverage, and recurrence. It did not generalize: its 2026
long-only equal-weight portfolio had Sharpe -0.360 and max drawdown -18.33%.

The second round froze the top 50 2025 utility variants, then selected up to
12 factors daily using only each factor's completed, horizon-delayed 60-day
return Sharpe. A 2025 signal-correlation threshold of 0.70 prevented redundant
members. The 2026 frozen long-only equal-weight portfolio had Sharpe 0.934,
annualized return 21.83%, and maximum drawdown -10.85%; it used 33 variants
over 225 dates. Liquidity-filtered inverse-volatility weights and a volatility
target underperformed it (Sharpe 0.675 and 0.354).

Portfolio rules use next-day execution, a 30% long-only stock selection slice,
10bp turnover cost, a near-limit-up new-buy exclusion, and no short positions.
Position-level stop or trailing-stop claims are intentionally deferred: daily
bars cannot demonstrate A-share stop execution under T+1 and limit-down locks.
A simulation that assumes fills at stop prices would overstate implementable
performance. [source: local artifacts
china_a_share_alpha_output/top100_multidim_a_share_research/
adaptive_a_share_position_rounds.csv and research_manifest.json]
