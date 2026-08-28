---
date: 2026-07-14
tags: [factor-mining, 20d, neutralization, moving-average, independent-alpha]
sources:
  - local frozen snapshot 242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011
  - local ma_neutralized_alpha_20d_20260714 receipt
related:
  - factor_20d_ma_correlation_20260714.md
  - think/statistical_residual_alpha_vs_execution.md
---

# 20d MA-Neutralized Alpha

## Method

For every trading day, regress the ensemble cross-section on an intercept and
standardized MA5, MA10, and MA20 deviations. The residual is the MA-neutralized
signal. Original and residual signals are restricted to identical dates and
symbols [source: local neutralization implementation].

The comparison uses three frozen folds and three outputs:

- daily cross-sectional Spearman IC against compounded `d+1` to `d+20` returns;
- five equal-count layers and their Q5-Q1 forward-return spread;
- next-day-applied, 10 bps, non-overlapping 20d cohort backtest.

## Results

| Fold | Signal | Version | 20d IC | IC HAC t | Q5-Q1 | Spread t | Hold Sharpe |
|---|---|---|---:|---:|---:|---:|---:|
| Train | raw | original | 0.0089 | 0.64 | 0.32% | 0.68 | -0.0188 |
| Train | raw | neutral | 0.0216 | 2.67 | 0.67% | 2.70 | -0.2336 |
| Validation | raw | original | 0.0158 | 1.05 | 0.89% | 1.64 | -0.8346 |
| Validation | raw | neutral | 0.0181 | 2.01 | 0.52% | 1.94 | -1.1379 |
| Test | raw | original | 0.0073 | 0.70 | 0.70% | 2.10 | 0.9542 |
| Test | raw | neutral | 0.0095 | 1.79 | 0.34% | 2.02 | 1.0302 |
| Test | EMA10 | original | 0.0057 | 0.43 | 0.78% | 1.77 | 0.5954 |
| Test | EMA10 | neutral | 0.0140 | 1.89 | 0.59% | 2.40 | 0.6578 |

MA exposures explain a mean 19.2% of raw-ensemble variance and 18.1% of EMA10
variance [source: local receipt]. Residual IC remains positive in every fold,
and every residual Q5-Q1 spread is positive.

## Interpretation

The factor library contains independent cross-sectional ordering information
beyond linear MA5/10/20 exposure. This evidence is strongest in IC and layered
returns. It is weaker at the execution layer: neutralized hold Sharpe is worse
in train and validation, then modestly better in the aggregate test fold.

For the test EMA10 signal, neutralization raises Sharpe from 0.5954 to 0.6578
and reduces maximum drawdown from -13.21% to -6.04%, while annualized return
falls from 6.60% to 4.31%. MA exposure adds return amplitude and risk; the
residual is lower-return and lower-drawdown [source: local receipt].

## Decision

- Do not replace or promote the live signal based on this audit.
- Treat residual IC as evidence of independent information, not a finished
  execution strategy.
- The next search surface should optimize execution of the residual signal on
  development/audit folds without reopening the final fold.

## Related pages

- [20d Factor / MA Correlation](factor_20d_ma_correlation_20260714.md)
- [Statistical Residual Alpha vs Execution](think/statistical_residual_alpha_vs_execution.md)
- [20d Position-Schedule Evolution](factor_20d_position_schedule_evolution_20260714.md)
