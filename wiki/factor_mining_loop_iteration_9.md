---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-9]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_130340.md
related:
  - factor_mining_loop_iteration_8.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 9 Chain-of-Thought

## Trigger

Implement the iteration-8 post-audit recommendation: tighten semantic
deduplication to 0.80, reduce `top_n` to 7, and try `risk_parity` weighting to
see if a smaller, less-correlated ensemble can improve cost-adjusted return.

## Setup

- Seed 1009, pop 50, gen 12, leaderboard 75.
- Live-library seed.
- `semantic_dedup_corr_threshold` lowered to 0.80.
- `top_n` reduced from 10 to 7.
- `weight_method` changed to `risk_parity`.
- `max_selection_correlation_gate` kept at 0.50.

## Observations

- **Merge**: 48 unique expressions.
- **Clean**: 16 expressions survived.
- **Dedup**: 14 distinct expressions after semantic dedup.
  - Dropped `factor_30` (|corr| = 0.830), `factor_66` (|corr| = 0.899),
    and `high_zscore_20` (|corr| = 1.000).
- **Gates**:
  - train_sharpe_positive: ✅ (1.2923)
  - min_cleaned_count: ✅ (14 distinct factors)
  - max_corr_ok: ❌ (max corr = 0.7427)
- **Metrics**:
  - Train Sharpe: 1.2923
  - Train cost-adj return: 17.45%
  - Test Sharpe: 0.4955
  - Test cost-adj return: -4.60%

## Decision

- **Did not promote.** The risk-parity-weighted ensemble had poor out-of-sample
  performance and failed the max-correlation gate. The iteration-5 live library
  is retained.

## New knowledge

1. **Risk-parity weighting can amplify weak factors.** The selected top-7
   factors by `val_ic` were not all strong enough to carry risk-parity weights,
   and the resulting portfolio lost money in the test period.
2. **Tightening semantic dedup to 0.80 removes more near-duplicates**, but the
   top-7 selection still contained a pair correlated at 0.74.
3. **Equal weight remains the most robust combination method** observed so far.
   Validation-weighted methods (IC, Sharpe, ridge, risk-parity) have all
   underperformed equal weight out-of-sample.

## Chain-of-thought for next iteration

- Revert to `weight_method: equal` and `top_n: 10`.
- Keep `semantic_dedup_corr_threshold: 0.80` or tighten further to 0.70.
- Implement **correlation-aware greedy selection** inside
  `run_factor_combination.py`: after ranking by `val_ic`, skip any candidate
  whose max correlation with already-selected factors exceeds the gate.
- Alternatively, add a hard post-selection filter that drops the lower-ranked
  member of any correlated pair before computing weights.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_130340.md`]
- [source: `wiki/factor_mining_loop_iteration_8.md`]
