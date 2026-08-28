---
date: 2026-07-14
tags: [thinking-process, residual-alpha, execution, neutralization]
sources:
  - local ma_neutralized_alpha_20d_20260714 receipt
related:
  - ../factor_20d_ma_neutralized_alpha_20260714.md
---

# Statistical Residual Alpha vs Execution

Positive IC and layer spreads can survive style neutralization while a discrete
holding strategy still fails. The former measures daily ordering information;
the latter also depends on cohort timing, turnover, long/short construction,
path dependence, and costs.

The MA-neutralized 20d ensemble demonstrates this separation. Residual IC is
positive in every fold, but fixed-cohort hold Sharpe deteriorates in train and
validation [source: local neutralized-alpha receipt]. Therefore the correct
claim is "independent information remains," not "the residual strategy is
production-ready."

Future execution work should preserve the residual signal and mutate only the
execution surface. It needs a new development/audit split because the current
test fold has now been opened for diagnosis.

## Related pages

- [20d MA-Neutralized Alpha](../factor_20d_ma_neutralized_alpha_20260714.md)
- [MA Correlation Is Exposure, Not Quality](ma_correlation_is_exposure_not_quality.md)
