---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-17, regime-switching]
sources:
  - ../china_a_share_alpha/scripts/run_regime_combination.py
  - ../china_a_share_alpha_output/factor_mining_loop/iter_17_regime_top10
related:
  - factor_mining_loop_iteration_16.md
  - factor_mining_loop_iteration_18.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 17 Chain-of-Thought

## Trigger

Test whether a volatility-regime switch improves the ensemble by selecting
different factors for high-vol and low-vol market days.

## Setup

- Added `china_a_share_alpha/scripts/run_regime_combination.py`.
- Market regime: high volatility when the EMA-smoothed cross-sectional median
  absolute return exceeds its training-set median; otherwise low volatility.
- For each regime, selected the top-N factors by in-regime training IC and
  applied a greedy correlation filter.
- Built a single combined signal from the union of selected factors, applying
  the regime-specific equal weights day by day.
- Ran two configurations on the live library:
  - top-N = 5 per regime with corr filter 0.40.
  - top-N = 10 per regime (all factors, no filter).

## Results

| Config | Val Sharpe | Test Sharpe | Test cost-adj return | Factors |
|---|---|---|---|---|
| top-5 per regime | 2.8904 | 1.1782 | 0.37% | 8 |
| top-10 per regime | 1.1830 | 2.7629 | 32.47% | 10 |

The top-10 configuration collapses to equal weighting because the same factors
are selected in both regimes, so there is no effective state switch. The top-5
configuration overfits the validation fold and fails on the test fold.

## Decision

- **Not promoted.** The simple volatility-regime switch does not improve the
  current equal-weight live library.
- The `run_regime_combination.py` script remains available for future regime
  experiments.

## New knowledge

1. **Regime labels must be stable and economically meaningful.** Median absolute
   return is noisy and produces regime-specific selections that do not
   generalize.
2. **Equal weight is hard to beat.** When the same factors are selected across
   regimes, the best achievable result is the equal-weight benchmark.
3. **Per-regime selection is prone to overfit.** A strong validation result
   (top-5) did not carry into the test period.

## References

- [source: `china_a_share_alpha/scripts/run_regime_combination.py`]
- [source: `wiki/factor_mining_loop_iteration_16.md`]
