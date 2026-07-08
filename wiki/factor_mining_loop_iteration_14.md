---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-14, operator-expansion]
sources:
  - ../china_a_share_alpha/factor/expression.py
  - ../china_a_share_alpha/factor/parser.py
  - ../china_a_share_alpha/evolution/enhanced_factor_mutator.py
  - ../china_a_share_alpha/examples/factor_mining_loop_config_iter14.yaml
related:
  - factor_mining_loop_iteration_13.md
  - factor_mining_loop_iteration_15.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 14 Chain-of-Thought

## Trigger

Expand the expression grammar with higher-order time-series operators that
 capture distributional shape and serial dependence, beyond the existing
 first-moment and second-moment operators.

## Setup

- Added four rolling operators to the factor DSL and mutator:
  - `ts_skew(x, window)` — rolling skewness.
  - `ts_kurt(x, window)` — rolling kurtosis.
  - `ts_autocorr(x, window)` — lag-1 autocorrelation inside a rolling window.
  - `ts_entropy(x, window)` — Shannon entropy (log2) of equal-width binned
    values inside a rolling window.
- Registered the operators in `expression.py`, `parser.py`, and
  `enhanced_factor_mutator.py` (`HIGH_ORDER_ROLLING_OPS`).
- Seeded the enhanced evolution with the iteration-12 live library.
- Evolution: forward_period=5, pop 30, gen 8, seed 1028.
- Cleaning: loose thresholds, coverage ≥ 0.50.
- Combination: top 10, greedy correlation filter 0.40, equal weight.

## Why these operators?

- **Skewness / kurtosis** capture tail risk and distributional regimes that
  simple mean/std miss; A-share returns are known to be non-Gaussian.
- **Autocorrelation** directly measures momentum/reversion persistence at
  different horizons.
- **Entropy** measures recent return randomness; low-entropy windows may
  correspond to trending or compressed regimes.

## Observations

- The merged library contained 26 unique expressions.
- Cleaning retained 15 factors; semantic dedup dropped 3 near-duplicates and the
  `high_zscore_20` seed (max |corr| ≈ 0.99), leaving 12 candidates.
- The combined ensemble satisfied all hard gates (positive train Sharpe,
  ≥5 factors, max selection correlation 0.374).
- Test Sharpe (2.41) and cost-adj return (28.48%) did not beat the iteration-12
  live library (2.76 / 32.47%).

## Metrics

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 2.0089 | 27.97% | 0.00331 |
| Val   | 0.5986 | 0.76%  | 0.00074 |
| Test  | 2.4074 | 28.48% | 0.00069 |

## Decision

- **Not promoted.** The iteration-12 live library remains the best.
- High-order operators are now part of the grammar and may still appear in
  future evolutionary runs, but a single seed did not find a better ensemble.

## New knowledge

1. **High-order operators are syntactically and numerically sound** after the
   `min_periods=self.window` fix.
2. **One seed is not enough to prove operator value.** The randomly generated
   population may not have combined `ts_skew`/`ts_kurt`/`ts_autocorr`/`ts_entropy`
   with the right inputs and windows.
3. **The current live library is a strong baseline.** Improvements now require
   either more targeted search or ensemble-level diversification rather than
   pure grammar expansion.

## References

- [source: `china_a_share_alpha/factor/expression.py`]
- [source: `china_a_share_alpha/factor/parser.py`]
- [source: `china_a_share_alpha/evolution/enhanced_factor_mutator.py`]
- [source: `wiki/factor_mining_loop_iteration_12.md`]
