---
date: 2026-09-13
tags: [china-a-share, all-factor-audit, t1, recent-regime]
source_count: 2
---

# Every Current Expression Needs Its Own Recent Execution Receipt

## Scope

The iteration-49 catalog contains 55 distinct factor libraries and 119 unique
expressions. Each expression was evaluated independently across:

- 2024 pressure, 2025 recent-primary, and 2026 YTD current-primary periods;
- 5d, 10d, and 20d T+1 exit policies;
- no market gate and a continuous-history MA20 entry gate;
- all stocks, main board, and STAR/ChiNext.

This produces exactly 119 x 3 x 3 x 2 x 3 = 6,426 stock result rows.

[source: china_a_share_alpha_output/tushare_snapshot_20260717/manifest.json]

## Completion evidence

- Matrix rows: **6,426 / 6,426**; unique contract keys: **6,426**.
- Expression cache: **119 / 119**; expression evaluation errors: **0**.
- Valid rows: **6,372**; explicitly invalid rows: **54**.
- Every expression has exactly 54 result rows.
- All valid Sharpe, return, drawdown, concentration, IC, and RankIC values are
  finite.
- BSE, ETF, and independent-index unavailability: **54 explicit receipts**.

Two expressions contain three invalid factor-period combinations. One becomes
constant in 2025 and 2026; another has only 14 cross-sectionally active days in
2026. Their tie-driven backtests were discarded. A valid signal requires at
least 50% coverage and 20 active cross-sectional days.

## Effective-factor gate

A factor-contract row is effective only when both 2025 and 2026 have positive
Sharpe and RankIC, recent drawdown is no worse than -25%, and maximum single-name
return concentration is at most 10%. Under this fixed gate:

- **38 unique factors** pass at least one contract, producing 95 effective
  factor-contract rows.
- All-stock MA20 counts are 13/32/3 for 5d/10d/20d.
- All-stock ungated counts are only 1/3/2 for 5d/10d/20d.
- Main-board MA20 counts are 4/19/4; STAR/ChiNext counts are 8/4/0.

The large gated/ungated gap confirms that recent factor usefulness depends on
market-level entry state as well as stock ordering.

[source: wiki/factor_recent_regime_matching_20260911.md]

## Leading all-stock contracts

1. `cs_rank(ts_zscore(high, 20))`, 10d MA20: 2025/2026 Sharpe 1.108/2.146,
   worst recent drawdown -9.36%.
2. `ts_delta(rsi_14, 20)`, 10d MA20: 1.501/1.597, drawdown -7.19%.
3. `sign(ts_shift(ts_ema(ts_pct_change(grossprofit_margin, 20), 5), 60))`,
   10d MA20: 2.138/0.956, drawdown -10.02%.
4. `ts_argmax(vwap, 10)`, 10d MA20: 1.310/1.338, drawdown -9.37%.
5. `ts_mean(neg(ts_entropy(low, 10)), 3)`, 5d MA20: 1.542/1.085,
   drawdown -8.45%.

Three of iteration 49's four new expressions pass at least one strict contract.
The lagged ADX/market-cap expression does not pass because its recent RankIC is
negative in its highest-return contract.

## Boundary

The complete claim applies to the frozen stock panel ending 2026-07-16. It does
not claim tests on absent BSE, ETF, or independent-index panels, nor does it turn
previously inspected dates into a blind test. No factor was promoted by this
audit alone.
