---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-8]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_122912.md
related:
  - factor_mining_loop_iteration_7.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 8 Chain-of-Thought

## Trigger

Follow the iteration-7 post-audit recommendation: return to live-library
seeding, relax coverage to 0.50, keep the strict 0.50 correlation gate, and
increase the evolution budget.

## Setup

- Seed 1008, pop 50, gen 12, leaderboard 75.
- Seeded with iteration 5 live library.
- `min_daily_coverage` restored to 0.50.
- `max_selection_correlation_gate` kept at 0.50.
- `semantic_dedup_corr_threshold` restored to 0.95.

## Observations

- **Merge**: 58 unique expressions.
- **Clean**: 21 expressions survived.
- **Dedup**: 17 distinct expressions after semantic dedup.
  - Dropped `factor_75`, `factor_21`, `factor_20` (max |corr| ≈ 0.997).
  - Dropped `factor_32` and `high_zscore_20` (max |corr| = 1.000).
- **Gates**:
  - train_sharpe_positive: ✅ (1.3452)
  - min_cleaned_count: ✅ (17 distinct factors)
  - max_corr_ok: ❌ (max corr = 0.9204)
- **Metrics**:
  - Train Sharpe: 1.3452
  - Train cost-adj return: 17.89%
  - Test Sharpe: 2.3964
  - Test cost-adj return: 28.42%

## Decision

- **Did not promote.** The new library improved test Sharpe (2.40 vs 2.20) but
  failed the max-correlation gate and did not improve cost-adjusted return
  (28.42% vs 30.76%). The existing 7-factor live library is retained.

## New knowledge

1. **Higher evolution budget with live seeding produces stronger candidates.**
   Test Sharpe reached 2.40, the highest raw value seen.
2. **The 0.50 correlation gate is still being violated.** Even after semantic
   dedup at 0.95, the top-N selection contained factors correlated at 0.92.
3. **Sharpe and cost-adjusted return can diverge.** Iteration 8 had higher
   Sharpe but lower cost-adjusted return than iteration 5, suggesting the
   candidate took more risk or had different return distribution.
4. **Training stability improved.** Train cost-adj return was positive (17.89%),
   unlike previous candidates.

## Chain-of-thought for next iteration

- Tighten semantic dedup threshold from 0.95 to 0.80, or lower
  `max_selection_correlation_gate` to 0.40.
- Alternatively, use a decorrelated weighting method (e.g., risk parity or
  minimum-variance combination) instead of equal weight, so correlated factors
  get smaller weights.
- If the next run still cannot pass all gates, accept the iteration-5 library
  as the current best and run a production-readiness audit.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_122912.md`]
- [source: `wiki/factor_mining_loop_iteration_7.md`]
