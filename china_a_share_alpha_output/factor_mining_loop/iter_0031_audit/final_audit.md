# Final Production Audit — Iteration 21

## Summary (test period)

- Test Sharpe: 5.7531
- Test annualized return: 239.59%
- Test cost-adjusted return: 229.14%
- Test max drawdown: -37.71%
- Test IC: 0.0508
- Test turnover: 0.0004
- Average daily coverage: 276.2 stocks
- Sector neutrality |Spearman corr|: 0.0470

## Cost Robustness

| One-way cost | Sharpe | Cost-adj return | Max drawdown |
|---|---|---|---|
| 0.1% | 5.7531 | 234.37% | -37.71% |
| 0.2% | 5.7531 | 229.14% | -37.71% |
| 0.3% | 5.7531 | 223.91% | -37.71% |

## Per-Year Test Performance

| Year | Sharpe | Ann. return | Cost-adj return | Max drawdown | Turnover | IC |
|---|---|---|---|---|---|---|
| 2024 | 4.4642 | 190.72% | 180.26% | -24.95% | 0.0004 | 0.0357 |
| 2025 | 6.6398 | 261.71% | 251.30% | -37.71% | 0.0004 | 0.0640 |
| 2026 | 5.8784 | 267.55% | 257.28% | -26.15% | 0.0004 | 0.0428 |

## Selected Factors

- **factor_10**: `cs_zscore(div(rsi_14, winsorize(total_mv)))`
- **factor_2**: `cs_zscore(div(sub(greater(eps, neg(0.033)), sub(ocfps, turnover_rate)), winsorize(total_mv)))`
- **factor_5**: `cs_zscore(div(sub(greater(eps, winsorize(total_mv)), sub(ocfps, turnover_rate)), winsorize(total_mv)))`
- **factor_35**: `cs_zscore(div(ts_rank(neg(ts_rank(turnover_rate, 20)), 5), winsorize(total_mv)))`
- **factor_25**: `if_else(roe_dt, mul(ts_max(winsorize(eps), 3), neg(0.639)), mul(add(mul(sign(ts_mean(ts_corr(grossprofit_margin, circ_mv, 5), 10)), 0.552), net_mf_amount), 1.437))`
- **factor_22**: `log(volume)`
- **factor_19**: `adx_14`
- **factor_23**: `ts_delta(rsi_14, 20)`
- **factor_31**: `cs_rank(ts_zscore(ts_argmin(log(pb), 3), 60))`
- **factor_39**: `if_else(neg(0.272), log(volume), mul(cs_zscore(if_else(sell_md_amount, neg(0.613), macd)), ts_std(if_else(roe_dt, neg(0.714), net_elg_amount), 60)))`
- **factor_32**: `ts_delta(sell_sm_amount, 20)`
- **factor_61**: `if_else(ts_min(if_else(less(0.917, close), less(vwap, net_mf_amount), if_else(0.982, 0.224, hk_vol)), 3), neg(if_else(-0.618, sign(volume), low)), ts_mean(if_else(if_else(grossprofit_margin, net_elg_amount, 0.312), -0.762, ts_rank(open, 20)), 10))`
- **factor_36**: `ts_zscore(netprofit_yoy, 3)`
- **factor_24**: `sign(ts_shift(ts_ema(ts_pct_change(grossprofit_margin, 20), 5), 60))`
- **high_zscore_20**: `cs_rank(ts_zscore(high, 20))`

Full JSON: `china_a_share_alpha_output\factor_mining_loop\iter_0031_audit\final_audit.json`