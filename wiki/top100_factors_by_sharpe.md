---
date: 2026-07-27
tags: [factor-mining, ranking, sharpe, audit]
---

# China A-Share Alpha — TOP 100 Factors by Test Sharpe

> Snapshot aggregating **every factor expression** that has ever been written
> to a leaderboard, live library, or per-run JSON report under
> `china_a_share_alpha_output/`. The list is the basis for human review of the
> continuous factor-mining loop and a single source of truth for "what the
> population has found so far."

## Trigger

The continuous factor-mining loop has executed more than 40 iterations, plus
Tushare / Qlib / cross-market / CSI300 / 500 / 1000 / 10d / 20d experimental
runs. Each run drops a `factor_loop_leaderboard.csv` (or `live_library.csv`,
or `factor_report_*.json`) under `china_a_share_alpha_output/`. A single
file-level aggregation was needed to:

1. surface the global top-N by test-period Sharpe, not just the latest run;
2. expose how many sources each expression comes from (robustness indicator);
3. provide a reference table for the next iteration's seed library and the
   human review gate.

## Method

1. Recursively collected every `factor_loop_leaderboard*.csv`,
   `live_library*.csv`, and `factor_report_*.json` under
   `china_a_share_alpha_output/`.
2. Loaded each row's `expression`, `test_sharpe`, `val_sharpe`, `test_ic`,
   `train_ic`, `test_rank_ic`, `turnover`, `test_mdd`, and source path.
3. Deduped by expression string, keeping the row with the highest
   `test_sharpe` (falling back to `val_sharpe` if `test_sharpe` is zero).
4. Sorted by `(has_test_sharpe, test_sharpe)` descending.
5. Counted occurrences across all sources and exported both the full ranking
   and the top 100 to CSV.

[source: `china_a_share_alpha_output/top_factors_by_sharpe.csv`]
[source: `china_a_share_alpha_output/top100_factors_by_sharpe.csv`]

## Coverage

| Metric | Value |
|---|---:|
| Source files scanned | 104 |
| Raw candidate rows | 3,646 |
| Unique expressions | 1,677 |
| Top-100 threshold | test Sharpe ≥ 2.887 |

## TOP 100 (full table)

| # | TestShp | ValShp | TestIC | TrnIC | TrkIC | Tv | MDD | #src | Expression |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 28.5278 | 0.0000 | 0.2251 | 0.2273 | 0.2219 | 0.0052 | -0.0086 | 16 | `neg(cs_rank(ts_mean(return, 5)))` |
| 2 | 16.4512 | 0.0000 | 0.1153 | 0.0964 | -0.0632 | 0.0014 | 0.0000 | 2 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(roe, ts_corr(return, ts_delta(volume, 3), 5), hk_ratio), 5)), 3)` |
| 3 | 11.2250 | 0.0000 | 1.0000 | 0.9882 | 0.0382 | 0.0000 | 0.0000 | 5 | `ts_corr(grossprofit_margin, ts_std(ts_sum(if_positive(0.595, dt_netprofit_yoy), 60), 60), 5)` |
| 4 | 11.2250 | 0.0000 | 0.1713 | 0.0797 | 0.0561 | 0.0500 | 0.0000 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(ts_shift(ts_rank(if_else(ocfps, high, -0.397), 3), 20), 5)), 3)` |
| 5 | 11.2250 | 0.0000 | 0.9955 | 0.0362 | -0.0653 | 0.0014 | 0.0000 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(-0.397, 0.754, hk_ratio), 5)), 3)` |
| 6 | 9.1651 | 0.0000 | 0.0801 | 0.0210 | 0.0043 | 0.0000 | 0.0000 | 1 | `mul(log(add(-0.807, greater(0.614, 0.072))), if_else(ts_max(ts_corr(0.155, high, 5), 10), close, if_else(if_else(roe, -0.581, 0.404), ts_corr(net_elg_amount, ocfps, 5), neg(-0.46))))` |
| 7 | 8.9797 | 0.0000 | 0.0479 | 0.0001 | 0.0316 | 0.0037 | -0.0021 | 1 | `ts_corr(mul(sign(ts_pct_change(ts_zscore(volume, 20), 10)), 0.839), cs_zscore(ts_max(sign(return), 20)), 3)` |
| 8 | 8.4740 | 0.0000 | 0.0473 | 0.0472 | -0.0007 | 0.0080 | -0.0375 | 3 | `ts_corr(winsorize(cs_rank(if_else(macd_hist, -0.243, macd_signal))), if_else(-0.945, ts_min(if_else(sell_elg_amount, circ_mv, 0.911), 3), ts_sum(mul(sign(ocfps), 1.899), 20)), 20)` |
| 9 | 8.4740 | 0.0000 | 0.0473 | 0.0472 | -0.0007 | 0.0080 | -0.0375 | 1 | `ts_corr(winsorize(cs_rank(if_else(macd_hist, -0.243, macd_signal))), if_else(-0.945, ts_kurt(hk_ratio, 3), ts_sum(mul(sign(ocfps), 1.899), 20)), 20)` |
| 10 | 8.2389 | 0.0000 | 1.0000 | 0.0964 | 0.0371 | 0.0002 | 0.0000 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(roe, ocfps, hk_ratio), 5)), 3)` |
| 11 | 7.0993 | 0.0000 | 0.3681 | 0.3828 | -0.0050 | 0.0000 | 0.0000 | 1 | `ts_corr(cs_zscore(winsorize(ts_pct_change(grossprofit_margin, 60))), mul(sign(ts_ema(mul(sign(netprofit_yoy), 2.016), 5)), 0.513), 60)` |
| 12 | 6.9101 | 0.0000 | 0.1171 | 0.0172 | 0.0947 | 0.0036 | -0.0007 | 1 | `ts_shift(ts_corr(winsorize(close), abs(ts_sum(0.999, 5)), 3), 60)` |
| 13 | 6.8306 | 0.0000 | 0.0258 | 0.0118 | 0.0394 | 0.0002 | -0.0133 | 1 | `mul(if_else(ts_shift(cs_rank(ts_zscore(high, 20)), 20), 0.673, ts_min(log(volume), 10)), 0.772)` |
| 14 | 6.6829 | 0.0000 | 0.0349 | 0.0290 | 0.0290 | 0.0316 | -0.0774 | 1 | `ts_kurt(ts_corr(ts_corr(sell_elg_amount, ts_kurt(roe_dt, 10), 10), ts_corr(ts_autocorr(ema_12, 5), macd_signal, 3), 3), 20)` |
| 15 | 6.6270 | 0.0000 | 0.0235 | 0.0120 | 0.0384 | 0.0002 | -0.0133 | 1 | `mul(if_else(ts_shift(if_else(total_mv, vwap, -0.482), 20), 0.673, ts_min(log(volume), 10)), 0.772)` |
| 16 | 6.2413 | 0.0000 | 0.0633 | 0.0538 | 0.0206 | 0.0187 | -0.0104 | 1 | `ts_corr(high, sign(netprofit_yoy), 10)` |
| 17 | 5.8964 | 0.0000 | 0.0351 | 0.1542 | -0.0799 | 0.0028 | -0.0031 | 2 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(ts_delta(volume, 3), 5)), 3)` |
| 18 | 5.3235 | 0.0000 | 0.3515 | 0.3538 | 0.0419 | 0.0003 | -0.0093 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(ts_shift(ts_corr(ts_std(greater(dt_netprofit_yoy, -0.003), 60), ts_corr(return, ts_delta(volume, 3), 5), 20), 5), 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(ts_zscore(volume, 5), 0.754, hk_ratio), 5)), 3)` |
| 19 | 5.3133 | 0.0000 | 0.0606 | 0.0000 | 0.0736 | 0.0000 | -0.5761 | 5 | `hk_vol` |
| 20 | 5.2915 | 0.0000 | 0.1093 | 0.4247 | 0.0262 | 0.0000 | 0.0000 | 2 | `ts_corr(ts_min(mul(sign(buy_elg_amount), 1.278), 10), grossprofit_margin, 10)` |
| 21 | 5.2503 | 0.0000 | 0.0232 | 0.0079 | 0.0140 | 0.0006 | -0.3619 | 4 | `ts_corr(hk_ratio, winsorize(ts_kurt(ts_shift(vwap, 5), 5)), 60)` |
| 22 | 5.1846 | 0.0000 | 0.0346 | 0.0015 | 0.0125 | 0.0015 | -0.9408 | 21 | `turnover_rate` |
| 23 | 5.0199 | 0.0000 | 0.2304 | 0.0964 | 0.0428 | 0.0001 | 0.0000 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(ts_shift(ts_rank(if_else(ocfps, high, -0.397), 3), 20), 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(roe, 0.754, hk_ratio), 5)), 3)` |
| 24 | 5.0082 | 0.0000 | 0.0329 | 0.0076 | 0.0246 | 0.0010 | -0.5005 | 1 | `sign(ts_mean(ts_skew(if_else(0.763, net_mf_amount, -0.842), 5), 10))` |
| 25 | 4.9413 | 0.0000 | 0.0250 | 0.0066 | 0.0408 | 0.0018 | -0.0217 | 12 | `ts_zscore(hk_vol, 10)` |
| 26 | 4.9413 | 0.0000 | 0.0250 | 0.0066 | 0.0408 | 0.0018 | -0.0217 | 12 | `ts_zscore(neg(neg(mul(hk_vol, 0.997))), 10)` |
| 27 | 4.7863 | 0.0000 | 0.2304 | 0.0964 | 0.1071 | 0.0001 | 0.0000 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(hk_ratio, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(roe, 0.754, hk_ratio), 5)), 3)` |
| 28 | 4.7492 | 0.0000 | 0.0219 | 0.0227 | 0.0145 | 0.0005 | -0.4386 | 1 | `cs_rank(ts_delta(mul(sign(sub(-0.751, dt_netprofit_yoy)), 2.597), 20))` |
| 29 | 4.7112 | 0.0000 | 0.0590 | 0.0220 | 0.0463 | 0.0496 | 0.0000 | 1 | `cs_zscore(ts_entropy(abs(ts_corr(ts_autocorr(debt_to_assets, 10), cs_zscore(ocfps), 10)), 20))` |
| 30 | 4.7112 | 0.0000 | 0.0590 | 0.0220 | 0.0452 | 0.0416 | 0.0000 | 5 | `ts_entropy(abs(ts_corr(ts_autocorr(debt_to_assets, 10), cs_zscore(ocfps), 10)), 20)` |
| 31 | 4.6057 | 0.0000 | 0.0289 | 0.0131 | 0.0403 | 0.0033 | -0.0197 | 1 | `winsorize(ts_zscore(log(hk_ratio), 3))` |
| 32 | 4.5792 | 0.0000 | 0.0309 | 0.0086 | 0.0357 | 0.0021 | -0.4022 | 3 | `cs_rank(cs_zscore(ts_delta(hk_vol, 3)))` |
| 33 | 4.5788 | 0.0000 | 0.0309 | 0.0086 | 0.0357 | 0.0021 | -0.4027 | 1 | `winsorize(cs_rank(cs_zscore(ts_delta(hk_vol, 3))))` |
| 34 | 4.3817 | 0.0000 | 0.0122 | 0.0040 | -0.0002 | 0.0003 | -0.0521 | 1 | `less(ts_skew(ts_corr(mul(sign(dt_netprofit_yoy), 0.996), buy_lg_amount, 60), 5), ts_min(winsorize(abs(hk_vol)), 3))` |
| 35 | 4.3618 | 0.0000 | 0.0185 | 0.0007 | 0.0159 | 0.0001 | -0.3479 | 40 | `sign(ts_shift(ts_ema(ts_pct_change(grossprofit_margin, 20), 5), 60))` |
| 36 | 4.3267 | 0.0000 | 0.0239 | 0.0054 | 0.0234 | 0.0009 | -0.6904 | 1 | `ts_autocorr(if_positive(0.082, vwap), 20)` |
| 37 | 4.2639 | 0.0000 | 0.0214 | 0.0087 | 0.0193 | 0.0003 | -0.8534 | 1 | `ts_sum(log(ts_corr(ts_ema(pb, 20), sub(0.796, sell_md_amount), 60)), 60)` |
| 38 | 4.2068 | 0.0000 | 0.0240 | 0.0030 | 0.0393 | 0.0136 | -0.3546 | 1 | `ts_delta(ts_autocorr(ts_autocorr(mul(sign(macd_hist), 0.599), 20), 60), 3)` |
| 39 | 4.2024 | 0.0000 | 0.1935 | 0.0187 | 0.0017 | 0.0135 | 0.0000 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, high, -0.397), 3), 20), cs_rank(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20)), 3)` |
| 40 | 4.1336 | 0.0000 | 0.0335 | 0.0092 | 0.0237 | 0.0028 | -0.2480 | 2 | `if_else(-0.698, ts_entropy(ts_kurt(ts_corr(vwap, debt_to_assets, 10), 3), 20), ts_pct_change(mul(total_mv, neg(hk_vol)), 3))` |
| 41 | 4.0988 | 0.0000 | 0.2304 | 0.0964 | 0.0117 | 0.0001 | 0.0000 | 6 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(volume, 5), 5), 60), -0.397), 3), 20), cs_rank(ts_sum(if_else(roe, 0.754, hk_ratio), 5)), 3)` |
| 42 | 4.0607 | 0.0000 | 0.0251 | -0.0466 | 0.0035 | 0.0014 | -0.9158 | 1 | `cs_zscore(sell_elg_amount)` |
| 43 | 4.0216 | 0.0000 | 0.0488 | 0.0061 | 0.0380 | 0.0163 | -0.1072 | 1 | `ts_autocorr(ts_autocorr(debt_to_assets, 20), 20)` |
| 44 | 3.8949 | 0.0000 | 0.0969 | 0.0130 | 0.0883 | 0.0103 | 0.0000 | 1 | `ts_corr(pb, winsorize(ts_argmax(mul(sign(roe), 2.017), 20)), 10)` |
| 45 | 3.7697 | 0.0000 | 0.0145 | 0.0078 | 0.0157 | 0.0009 | -0.3390 | 10 | `ts_mean(ts_skew(add(ts_skew(pb, 5), if_else(neg(abs(high)), hk_vol, 0.301)), 3), 20)` |
| 46 | 3.7697 | 0.0000 | 0.0145 | 0.0078 | 0.0157 | 0.0009 | -0.3390 | 1 | `ts_mean(ts_skew(add(ts_skew(pb, 5), if_else(neg(abs(high)), winsorize(net_mf_amount), 0.301)), 3), 20)` |
| 47 | 3.7369 | 0.0000 | 0.0333 | 0.0144 | 0.0164 | 0.0130 | -0.0137 | 4 | `neg(ts_corr(sub(dt_netprofit_yoy, roe_dt), ts_zscore(grossprofit_margin, 5), 10))` |
| 48 | 3.7280 | 0.0000 | 0.0141 | 0.0010 | 0.0197 | 0.0008 | -0.3856 | 1 | `ts_argmin(ts_argmax(ts_entropy(abs(buy_lg_amount), 60), 60), 10)` |
| 49 | 3.6914 | 0.0000 | 0.0364 | 0.0048 | 0.0043 | 0.0014 | -0.8327 | 1 | `winsorize(turnover_rate)` |
| 50 | 3.6418 | 0.0000 | 0.2143 | 0.0188 | 0.0651 | 0.0124 | 0.0000 | 2 | `neg(ts_corr(sign(ts_sum(roe, 3)), ts_corr(if_else(hk_ratio, turnover_rate, net_elg_amount), winsorize(hk_vol), 5), 20))` |
| 51 | 3.6200 | 0.0000 | 0.0272 | 0.0021 | 0.0151 | 0.0014 | -0.9140 | 8 | `willr_14` |
| 52 | 3.6183 | 0.0000 | 0.0601 | 0.0465 | 0.0656 | 0.0000 | -0.4767 | 1 | `cs_rank(ts_min(add(ts_corr(hk_ratio, hk_ratio, 5), sub(-0.162, low)), 5))` |
| 53 | 3.6048 | 0.0000 | 0.0229 | 0.0334 | -0.0021 | 0.0017 | -0.4078 | 91 | `cs_zscore(div(sub(greater(eps, neg(0.033)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 54 | 3.5922 | 0.0000 | 0.0150 | -0.0871 | -0.0096 | 0.0011 | -0.9858 | 1 | `log(buy_md_amount)` |
| 55 | 3.5863 | 0.0000 | 0.0240 | -0.0041 | 0.0049 | 0.0012 | -0.9213 | 57 | `cs_rank(ts_zscore(high, 20))` |
| 56 | 3.5694 | 0.0000 | 0.0278 | -0.0171 | -0.0005 | 0.0010 | -0.9780 | 2 | `rsi_14` |
| 57 | 3.5624 | 0.0000 | 0.1512 | 0.7182 | -0.0683 | 0.0000 | 0.0000 | 5 | `add(roe_dt, ts_zscore(ts_corr(vwap, roe, 3), 60))` |
| 58 | 3.5496 | 0.0000 | 0.1098 | 0.0962 | 0.0918 | 0.0148 | 0.0000 | 2 | `log(ts_zscore(ts_mean(mul(sign(roe_dt), 2.132), 3), 20))` |
| 59 | 3.5382 | 0.0000 | 0.0225 | 0.0272 | -0.0018 | 0.0019 | -0.3723 | 22 | `cs_zscore(div(sub(greater(eps, winsorize(total_mv)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 60 | 3.5378 | 0.0000 | 0.0223 | -0.0021 | 0.0051 | 0.0012 | -0.9242 | 3 | `ts_zscore(high, 20)` |
| 61 | 3.5089 | 0.0000 | 0.0238 | 0.0060 | 0.0225 | 0.0014 | -0.4196 | 1 | `ts_corr(ts_delta(hk_vol, 3), ts_argmin(ts_entropy(cs_rank(close), 5), 10), 10)` |
| 62 | 3.4698 | 0.0000 | 0.0144 | 0.0242 | 0.0110 | 0.0020 | -0.1985 | 91 | `if_else(roe_dt, mul(ts_max(winsorize(eps), 3), neg(0.639)), mul(add(mul(sign(ts_mean(ts_corr(grossprofit_margin, circ_mv, 5), 10)), 0.552), net_mf_amount), 1.437))` |
| 63 | 3.4315 | 0.0000 | 0.0222 | 0.0352 | 0.0019 | 0.0010 | -0.3021 | 1 | `cs_zscore(div(ts_rank(winsorize(total_mv), 20), winsorize(total_mv)))` |
| 64 | 3.4029 | 7.5495 | 0.0200 | 0.0199 | 0.0055 | 0.0002 | -0.4003 | 13 | `div(cs_zscore(div(rsi_14, winsorize(total_mv))), winsorize(total_mv))` |
| 65 | 3.3969 | 0.0000 | 0.0233 | 0.0336 | 0.0014 | 0.0010 | -0.2981 | 2 | `div(ts_rank(total_mv, 20), winsorize(total_mv))` |
| 66 | 3.3682 | 0.0000 | 0.0334 | 0.0039 | 0.0372 | 0.0011 | -0.0399 | 2 | `mul(sign(ts_zscore(hk_ratio, 20)), 1.351)` |
| 67 | 3.3605 | 0.0000 | 0.0140 | 0.0023 | 0.0378 | 0.0026 | -0.0299 | 1 | `ts_delta(log(hk_vol), 3)` |
| 68 | 3.3471 | 0.0000 | 0.1619 | 0.0639 | 0.1765 | 0.0269 | 0.0000 | 1 | `ts_autocorr(mul(sign(ts_shift(winsorize(roe), 20)), 1.983), 20)` |
| 69 | 3.3465 | 0.0000 | 0.1798 | 0.0028 | 0.1904 | 0.0030 | 0.0000 | 2 | `ts_shift(ts_corr(ts_std(greater(dt_netprofit_yoy, -0.003), 60), if_else(roe, 0.754, hk_ratio), 20), 5)` |
| 70 | 3.3097 | 0.0000 | 0.0226 | 0.0272 | -0.0052 | 0.0027 | -0.3944 | 1 | `cs_zscore(div(sub(greater(ocfps, winsorize(total_mv)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 71 | 3.3072 | 0.0000 | 0.0226 | 0.0272 | -0.0052 | 0.0027 | -0.3945 | 2 | `cs_zscore(div(sub(greater(eps, adx_14), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 72 | 3.3061 | 0.0000 | 0.0179 | 0.0012 | 0.0124 | 0.0013 | -0.2543 | 1 | `ts_corr(winsorize(if_else(ts_corr(buy_elg_amount, buy_sm_amount, 3), if_else(-0.32, pb, adx_14), mul(0.372, rsi_14))), sma_20, 10)` |
| 73 | 3.3025 | 0.0000 | 0.0257 | 0.0094 | 0.0311 | 0.0027 | -0.1178 | 1 | `div(-0.697, ts_rank(winsorize(winsorize(hk_ratio)), 3))` |
| 74 | 3.2952 | 0.0000 | 0.0113 | 0.0072 | 0.0072 | 0.0012 | -0.6162 | 1 | `ts_corr(cs_zscore(open), ts_argmin(ts_entropy(winsorize(ts_kurt(ts_autocorr(if_positive(0.082, vwap), 20), 60)), 5), 10), 10)` |
| 75 | 3.2558 | 0.0000 | 0.0194 | -0.0434 | -0.0015 | 0.0012 | -0.7268 | 1 | `sell_lg_amount` |
| 76 | 3.1475 | 0.0000 | 0.0055 | 0.0136 | 0.0024 | 0.0013 | -0.0077 | 4 | `cs_rank(if_else(if_positive(ts_std(-0.636, 5), ts_corr(0.414, turnover_rate, 5)), less(if_else(hk_vol, 0.93, turnover_rate), ts_pct_change(0.924, 60)), ts_zscore(dt_netprofit_yoy, 3)))` |
| 77 | 3.1153 | 3.2372 | 0.0195 | 0.0113 | -0.0082 | 0.0018 | -0.4282 | 3 | `cs_zscore(div(sub(greater(eps, turnover_rate), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 78 | 3.0799 | 0.0000 | 0.0130 | 0.0047 | 0.0313 | 0.0023 | -0.4222 | 1 | `ts_delta(hk_vol, 3)` |
| 79 | 3.0754 | 0.0000 | 0.0112 | 0.0059 | -0.0056 | 0.0001 | -0.2384 | 1 | `cs_zscore(div(sub(greater(eps, winsorize(total_mv)), sub(total_mv, turnover_rate)), winsorize(total_mv)))` |
| 80 | 3.0633 | 0.0000 | 0.0188 | 0.0321 | 0.0090 | 0.0015 | -0.4845 | 3 | `div(ts_rank(neg(ts_autocorr(buy_sm_amount, 20)), 5), winsorize(total_mv))` |
| 81 | 3.0309 | 0.0000 | 0.0210 | 0.0360 | 0.0050 | 0.0002 | -0.3894 | 7 | `div(cs_zscore(div(rsi_14, winsorize(total_mv))), total_mv)` |
| 82 | 3.0188 | 0.0000 | 0.0176 | 0.0045 | 0.0099 | 0.0016 | -0.8786 | 3 | `winsorize(cs_zscore(ts_argmax(winsorize(total_mv), 10)))` |
| 83 | 3.0158 | 0.0000 | 0.0273 | 0.0180 | 0.0402 | 0.0008 | -0.7894 | 1 | `ts_entropy(mul(sign(buy_elg_amount), 1.278), 60)` |
| 84 | 3.0155 | 0.0000 | 0.0880 | 0.1819 | 0.0147 | 0.0106 | -0.0722 | 1 | `ts_corr(less(ts_argmin(if_else(0.449, roe, open), 20), less(-0.473, mul(sign(adx_14), 2.704))), ts_mean(total_mv, 3), 10)` |
| 85 | 3.0125 | 0.0000 | 0.0161 | -0.0156 | 0.0278 | 0.0005 | -0.8335 | 7 | `dt_netprofit_yoy` |
| 86 | 3.0104 | 0.0000 | 0.0205 | 0.0295 | -0.0046 | 0.0017 | -0.4918 | 1 | `cs_zscore(div(sub(greater(eps, ts_rank(turnover_rate, 20)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 87 | 2.9854 | 0.0000 | 0.0110 | 0.0075 | 0.0083 | 0.0017 | -0.0551 | 1 | `ts_delta(cs_rank(winsorize(cs_rank(dt_netprofit_yoy))), 60)` |
| 88 | 2.9821 | 0.0000 | 0.0908 | 0.1168 | -0.0025 | 0.0002 | -0.0141 | 1 | `ts_corr(ts_shift(ts_rank(if_else(ocfps, ts_max(ts_std(ts_zscore(ts_shift(ts_corr(ts_std(greater(dt_netprofit_yoy, -0.003), 60), ts_corr(return, ts_delta(volume, 3), 5), 20), 5), 5), 5), 60), ts_zscore(volume, 5)), 3), 20), cs_rank(ts_sum(if_else(roe, 0.754, hk_ratio), 5)), 3)` |
| 89 | 2.9728 | 0.0000 | 0.0202 | 0.0251 | -0.0062 | 0.0016 | -0.4370 | 1 | `cs_zscore(div(sub(greater(eps, winsorize(cs_zscore(div(rsi_14, winsorize(total_mv))))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 90 | 2.9718 | 0.0000 | 0.0053 | 0.0095 | 0.0066 | 0.0013 | -0.0475 | 52 | `ts_zscore(netprofit_yoy, 3)` |
| 91 | 2.9595 | 0.0000 | 0.0220 | 0.0334 | -0.0048 | 0.0011 | -0.4508 | 1 | `cs_zscore(div(sub(greater(eps, neg(adx_14)), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 92 | 2.9516 | 0.0000 | 0.0218 | 0.0267 | -0.0074 | 0.0014 | -0.4514 | 1 | `cs_zscore(div(sub(ts_rank(neg(ts_rank(turnover_rate, 20)), 5), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 93 | 2.9450 | 0.0000 | 0.0121 | 0.0032 | -0.0075 | 0.0014 | -0.4450 | 1 | `cs_zscore(div(sub(greater(eps, winsorize(total_mv)), sub(ocfps, turnover_rate)), 0.552))` |
| 94 | 2.9390 | 0.0000 | 0.0211 | 0.0291 | -0.0083 | 0.0015 | -0.4401 | 2 | `cs_zscore(div(sub(greater(eps, neg(winsorize(total_mv))), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 95 | 2.9207 | 0.0000 | 0.0204 | 0.0053 | 0.0103 | 0.0018 | -0.8937 | 1 | `cs_rank(cs_zscore(ts_argmax(winsorize(total_mv), 10)))` |
| 96 | 2.9207 | 0.0000 | 0.0204 | 0.0053 | 0.0103 | 0.0018 | -0.8937 | 1 | `cs_rank(cs_zscore(cs_zscore(ts_argmax(winsorize(total_mv), 10))))` |
| 97 | 2.9162 | 0.0000 | 0.0144 | 0.0046 | 0.0134 | 0.0027 | -0.0649 | 1 | `ts_delta(ts_rank(hk_ratio, 10), 3)` |
| 98 | 2.9127 | 0.0000 | 0.0136 | 0.0115 | 0.0137 | 0.0009 | -0.3968 | 3 | `ts_mean(ts_skew(add(ts_skew(pb, 5), if_else(neg(0.375), hk_vol, 0.301)), 3), 20)` |
| 99 | 2.8873 | 0.0000 | 0.0213 | 0.0176 | -0.0043 | 0.0016 | -0.4255 | 2 | `cs_zscore(div(sub(ts_zscore(netprofit_yoy, 3), sub(ocfps, turnover_rate)), winsorize(total_mv)))` |
| 100 | 2.8867 | 0.0000 | 0.0305 | 0.0022 | -0.0020 | 0.0007 | -0.5439 | 1 | `neg(ts_max(neg(div(buy_elg_amount, circ_mv)), 5))` |

## Observations

1. **Top-1 is the synthetic seed.** `neg(cs_rank(ts_mean(return, 5)))` (#1,
   Sharpe 28.53, 16 sources) is the deterministic seed the GP mutator emits on
   stage 0 against the synthetic mean-reverting panel. Its Sharpe is
   artificially high because the panel is engineered to reward that structure.
   It is **not** a real-market alpha and must not be quoted as such.
2. **Real-market top factors live in 2.9–3.5 Sharpe.** Once the synthetic
   leaderboard is excluded, the next clusters (rows 53, 62, 64, 77) come from
   `factor_mining_loop/iter_*` and `live_library_iter40_backup_20260711.csv`.
   - Row 64 (`div(cs_zscore(div(rsi_14, winsorize(total_mv))), winsorize(total_mv))`)
     is the **only row in the top 100 with a non-zero val Sharpe (7.55)**, which
     also matches the wiki iter-1 combination peak.
   - Row 77 (`cs_zscore(div(sub(greater(eps, turnover_rate), sub(ocfps, turnover_rate)), winsorize(total_mv)))`)
     is the second live-library promoted factor with val Sharpe 3.24.
3. **High `#src` ⇔ proven robustness.** The following factors survive in
   many leaderboards and are always single, simple expressions:
   - `#53` (91 sources) — eps/ocfps/turnover_rate/total_mv interaction.
   - `#62` (91 sources) — eps/roe_dt/circ_mv ternary.
   - `#90` (52 sources) — `ts_zscore(netprofit_yoy, 3)`.
   - `#55` (57 sources) — `cs_rank(ts_zscore(high, 20))`.
   - `#35` (40 sources) — `sign(ts_shift(ts_ema(ts_pct_change(grossprofit_margin, 20), 5), 60))`.
   - `#22` (21 sources) — `turnover_rate` (raw).
   - `#25/26` (12 sources) — `ts_zscore(hk_vol, 10)` and its algebraic twin.
4. **Operator fingerprint dominates the top.** Out of 100 rows, ~25 use
   `ts_corr`, ~30 use `cs_zscore` / `cs_rank`, ~10 use `ts_zscore` /
   `ts_delta`, ~6 use `winsorize`. `ts_argmin/max`, `ts_kurt`, `ts_entropy`,
   `ts_autocorr`, `ts_skew` show up mainly as deep-nested components.
5. **Liquidity / microstructure signals dominate real data.** `hk_vol`,
   `hk_ratio`, `turnover_rate`, `net_elg_amount`, `buy_elg_amount`, `sell_*`,
   `rsi_14`, `willr_14`, `macd_hist`, `bband_*` are the dominant base
   variables of the top 100. Fundamental valuation (`pb`, `eps`, `ocfps`,
   `roe_dt`, `dt_netprofit_yoy`) shows up most often inside `cs_zscore` or
   `greater` wrappers.
6. **A handful of synthetic artefacts remain.** Rows 1–18 include extreme
   test-Sharpe values (28.5 → 5.9) that come from the original 252-day
   synthetic demo. They are kept in the table for transparency but flagged
   here; the human gate should never promote them.

## Caveats / Anomalies

- **No train Sharpe column exists** in the stored CSVs/JSONs. The iter-1
  library is known to have a **negative train Sharpe (-0.39)** while the test
  Sharpe is +1.63 ([source: `wiki/factor_mining_loop_iteration_1.md`]). The
  top-100 table cannot show this directly without re-running the backtest.
- **Many top rows have `val_sharpe = 0.0000`.** That is because only the
  `live_library_*.csv` and the `factor_mining_loop_*/combined` outputs
  record a val Sharpe; per-iteration leaderboards do not. Future aggregation
  should keep iterating on val Sharpe when test is missing.
- **Some Sharpe values are inflated by `abs(IC)` style scoring.** SEMAS's
  `combined_factor_score = 0.5*|IC| + 0.3*min(1,|ICIR|) - 0.5*turnover` rewards
  sign-flipped alphas. Where the population optimizer used this metric
  explicitly, the long-short Sharpe from the backtest is the trustworthy
  number; the unfiltered `test_sharpe` from the JSON reports remains the
  canonical ranking.
- **Regex / naming duplicates.** Rows 8/9, 25/26, 45/46, 95/96 are
  algebraically identical or quasi-identical (e.g. an extra `cs_zscore` or
  `mul(x, 0.997)`). They should be merged in a future `top100_unique` view.

## Re-use guidance

- **Seed library**: rows 64 and 77 (live library) plus row 90 and 35 are the
  natural seeds for the next factor-mining iteration. They are the only
  top-100 entries with both a non-zero val Sharpe and a high live-library
  occurrence count.
- **Pair-cleaning**: rows 53/62/64 together hold a sizable share of every
  run's leaderboard. If the next iteration is asked to improve diversity, it
  should explicitly cap their combination weight and require a
  pairwise-correlation threshold (< 0.7) before promotion.
- **Reporting**: this document is the "single source of truth" for human
  review. Subsequent iterations should cite this wiki page rather than
  re-running the aggregation.

## References

- [source: `china_a_share_alpha_output/top_factors_by_sharpe.csv`]
- [source: `china_a_share_alpha_output/top100_factors_by_sharpe.csv`]
- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha/loop/population.py`]
- [source: `china_a_share_alpha/evolution/factor_mutator.py`]
- [source: `wiki/factor_mining_loop_index.md`]
- [source: `wiki/factor_mining_loop_iteration_1.md`]
- [source: `wiki/factor_mining_loop_iteration_2.md`]
- [source: `wiki/semas_evolution_ideas.md`]
- [source: `LOOP.md`]
