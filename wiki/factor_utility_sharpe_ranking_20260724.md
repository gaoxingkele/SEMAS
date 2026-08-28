# Sharpe-first external factor utility ranking

This is a descriptive research ordering, not an automatic promotion rule. Candidates are ranked by full-period Sharpe from the frozen, stock-disjoint external CSI500 audit. [source: local artifact china_a_share_alpha_output/external_unused_csi500_2025_2026/external_validation_results.csv]

The raw ranking contains 178 frozen factors. `eligible_observations` requires at least 3,000 factor-return observations; `externally_consistent` also requires positive Sharpe and IC in both 2025 and 2026. High-Sharpe rows failing these flags remain visible but are not usable evidence of factor utility.

## Full Sharpe order

The complete machine-readable order is [`external_factor_utility_sharpe_ranking.csv`](../china_a_share_alpha_output/external_unused_csi500_2025_2026/external_factor_utility_sharpe_ranking.csv).

## Top externally consistent factors

| Eligible rank | Horizon | Iteration | Full Sharpe | 2025 | 2026 | IC | Max DD | Turnover | Expression |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 5D | 21 | 4.582 | 0.500 | 7.842 | 0.0759 | -0.431 | 0.142 | `ts_sum(ts_kurt(sign(ts_delta(willr_14, 10)), 10), 60)` |
| 2 | 10D | 4 | 3.204 | 3.622 | 2.906 | 0.0648 | -0.506 | 0.253 | `ts_mean(net_mf_amount, 20)` |
| 4 | 5D | 12 | 2.655 | 2.804 | 2.528 | 0.0386 | -0.458 | 0.888 | `ts_skew(ts_min_max_scale(return, 3), 5)` |
| 19 | 5D | 10 | 1.940 | 1.587 | 2.279 | 0.0389 | -0.610 | 0.166 | `cs_percentile(ts_mean(ts_corr(mul(sign(ts_autocorr(pb, 3)), 0.682), ts_percentile_10(ts_min_max_scale(macd_hist, 5), 10), 10), 5))` |

## Utility metrics already implemented

- **Sharpe**: primary risk-adjusted return ordering used here.
- **IC / RankIC**: linear and rank-based cross-sectional predictive association with future returns.
- **ICIR**: stability of daily IC; implemented in `evaluator/metrics.py`, though not yet persisted in this external audit CSV.
- **Annualized long-short return**: gross five-quantile spread return.
- **Cost-adjusted return**: annualized spread return after the configured transaction-cost estimate.
- **Maximum drawdown**: worst peak-to-trough cumulative spread loss.
- **Turnover**: average signal/portfolio turnover proxy, which determines cost sensitivity.
- **Cross-year stability**: 2025/2026 Sharpe and IC signs, added here as a utility-validity diagnostic.
- **Selection correlation**: existing combination workflows record the maximum selected-factor correlation to prevent redundant portfolios.

For deployment research, Sharpe must remain primary only within comparable horizons and implementation assumptions; drawdown, cost, observation coverage, year stability, and correlation are necessary constraints rather than secondary decoration.

## Diagnostics for externally consistent candidates

The following metrics were recomputed from cached daily data for the four
externally consistent candidates. ICIR is mean daily IC divided by the standard
deviation of daily IC. Correlations use the same stock-disjoint external panel.
[source: local artifact china_a_share_alpha_output/external_unused_csi500_2025_2026/externally_consistent_factor_diagnostics.csv]

| Factor ID | Full ICIR | 2025 ICIR | 2026 ICIR | Cost-adjusted return | Max DD | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| `a9a0e79c9dd76f10` | 0.394 | 0.242 | 0.561 | 2.633 | -0.431 | 0.142 |
| `477f79caa83af71e` | 0.297 | 0.437 | 0.183 | 2.734 | -0.506 | 0.253 |
| `598c04e12b4d8fa1` | 0.177 | 0.243 | 0.082 | 1.339 | -0.458 | 0.888 |
| `d6e1d28fb1323d16` | 0.124 | 0.092 | 0.172 | 1.600 | -0.610 | 0.166 |

Pairwise daily long-short return correlations range from -0.028 to 0.054;
cross-sectional signal Spearman correlations range from -0.061 to 0.069.
Within this external sample, the four candidates are therefore low-redundancy
research inputs, although this does not override their substantial drawdowns.
[source: local artifacts daily_long_short_return_correlation.csv and
cross_sectional_signal_correlation.csv]
