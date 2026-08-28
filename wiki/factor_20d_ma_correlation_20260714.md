---
date: 2026-07-14
tags: [factor-mining, 20d, moving-average, correlation, style-exposure]
sources:
  - local frozen snapshot 242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011
  - local factor_ma_correlation_20d_20260714 receipt
related:
  - factor_20d_position_schedule_evolution_20260714.md
  - think/ma_correlation_is_exposure_not_quality.md
---

# 20d Factor / MA Correlation

## Question

Does the 20d factor library contain information similar to MA5, MA10, or MA20?
Raw MA levels are price-scale dependent, so the comparable signal is
`close / trailing_MA(close, n) - 1`. Correlation is computed as daily
cross-sectional Spearman and summarized with a 20-day Newey-West t-statistic
[source: local analysis implementation].

## Ensemble Result

| Fold | Ensemble | MA5 | MA10 | MA20 |
|---|---|---:|---:|---:|
| Train, 2021-06 to 2022-12 | raw | 0.3939 | 0.4378 | 0.4442 |
| Validation, 2023 | raw | 0.3887 | 0.4223 | 0.4294 |
| Test, 2024 to 2026-05 | raw | 0.3802 | 0.4080 | 0.4161 |
| Train, 2021-06 to 2022-12 | EMA10 | 0.2001 | 0.3364 | 0.4621 |
| Validation, 2023 | EMA10 | 0.1943 | 0.3188 | 0.4407 |
| Test, 2024 to 2026-05 | EMA10 | 0.1929 | 0.3109 | 0.4255 |

All ensemble relationships keep the same sign and similar magnitude across the
three temporal folds [source: local correlation receipt].

## Attribution

The strongest test-fold exposure is `high_zscore_20`: correlations are 0.5918,
0.7965, and 0.8847 against MA5, MA10, and MA20. This is expected because the
expression ranks a 20-day high-price z-score. `net_mf_amount` also has material
positive exposure of 0.4851, 0.3570, and 0.2658. The other three factors have
small correlations, with absolute test-fold means below 0.062 [source: local
correlation receipt].

## Interpretation

- The library is not independent of trend/momentum information.
- MA20 is especially redundant with `high_zscore_20` and the smoothed ensemble.
- Adding an MA-based position overlay may double-count the same state variable.
- Correlation does not establish predictive quality; it measures exposure.
- Incremental value requires a neutralized or conditional forward-return test.

## Verification Contract

- Snapshot and library hashes are verified before analysis.
- MAs use current and prior closes only; no future prices enter the signal.
- Rolling signals are calculated on the continuous panel before temporal folds
  are sliced, preserving legitimate history at fold boundaries.
- At least 30 symbols are required for each daily cross-section.
- Factor parsing completed with zero errors and ensemble coverage was 98.81%.

## Related pages

- [20d Position-Schedule Evolution](factor_20d_position_schedule_evolution_20260714.md)
- [MA Correlation Is Exposure, Not Quality](think/ma_correlation_is_exposure_not_quality.md)
- [Frozen Evaluator Contract](think/frozen_evaluator_contract.md)
