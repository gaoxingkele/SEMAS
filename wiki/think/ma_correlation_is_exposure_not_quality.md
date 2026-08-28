---
date: 2026-07-14
tags: [thinking-process, factor-quality, correlation, moving-average]
sources:
  - local factor_ma_correlation_20d_20260714 receipt
related:
  - ../factor_20d_ma_correlation_20260714.md
---

# MA Correlation Is Exposure, Not Quality

A factor/MA correlation answers whether two signals rank the current stock
cross-section similarly. It does not answer whether either ranking predicts
future returns. This distinction prevents a style-exposure diagnostic from
being mistaken for an alpha-quality metric.

The 20d ensemble has stable positive MA exposure, but most of it is traceable
to one explicitly momentum-like component, `high_zscore_20` [source: local
correlation receipt]. Therefore an MA-based execution overlay would likely
reuse an existing signal rather than add orthogonal state information.

The next valid experiment is incremental: compare the factor's forward-return
performance before and after cross-sectional neutralization against MA5/10/20,
or evaluate MA-conditioned factor IC. That test should preserve the same frozen
folds and must not tune thresholds on the final fold.

## Related pages

- [20d Factor / MA Correlation](../factor_20d_ma_correlation_20260714.md)
- [Rank-Decile Schedule Regime Failure](rank_decile_schedule_regime_failure.md)
