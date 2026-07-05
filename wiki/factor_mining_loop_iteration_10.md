---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-10]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_133300.md
  - ../china_a_share_alpha_output/factor_mining_loop/verification_iter_10
related:
  - factor_mining_loop_iteration_9.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 10 Chain-of-Thought

## Trigger

Implement the iteration-9 post-audit recommendation to fix the correlation-gate
failure mode by adding greedy correlation-aware selection inside the
combination script.

## Setup

- Seed 1010, pop 50, gen 12, leaderboard 75.
- Live-library seed.
- `semantic_dedup_corr_threshold: 0.80`.
- `max_pairwise_corr: 0.40` in `run_factor_combination.py`.
- `weight_method: equal`, `top_n: 10`.
- Promotion gates unchanged.

## What changed in the pipeline

- Added `--max-pairwise-corr` to `run_factor_combination.py`.
- After ranking candidates by `val_ic`, the script now greedily skips any
candidate whose absolute Spearman correlation with an already-selected factor
exceeds the threshold.
- `run_factor_mining_loop.py` passes `max_pairwise_corr` from config to the
combination command.

## Observations

- **Merge**: 56 unique expressions.
- **Clean**: 15 expressions survived.
- **Dedup**: 12 distinct expressions after semantic dedup.
- **Gates**:
  - train_sharpe_positive: ✅ (1.6861)
  - min_cleaned_count: ✅ (12 distinct factors)
  - max_corr_ok: ✅ (max corr = 0.3744)
- **Metrics**:
  - Train Sharpe: 1.6861
  - Train cost-adj return: 14.56%
  - Test Sharpe: **2.7031**
  - Test cost-adj return: **31.46%**

## Independent verification

Ran `run_factor_combination.py` directly on the promoted `live_library.csv`
with the same config:

```text
TEST: sharpe=2.7031, cost_adjusted_return=0.3146, turnover=0.0007
```

The independent backtest reproduced the loop-reported metrics exactly.

## Decision

- **Promoted** the new live library. It is the best ensemble found so far by
  both test Sharpe and cost-adjusted return, and it passes all gates.

## New knowledge

1. **Greedy correlation-aware selection is the key fix.** It prevents the
   combination from picking highly correlated siblings, satisfying the
   max-correlation gate while preserving strong alpha.
2. **Equal weight remains robust.** When paired with correlation filtering, it
   produced the best OOS result.
3. **Training stability improved.** Train Sharpe and train cost-adj return are
   both positive, reducing regime-dependence concerns.
4. **The loop can autonomously improve its own infrastructure.** The
   correlation-gate failures in iterations 6, 8, and 9 led to a code change
   that enabled iteration 10 to succeed.

## Chain-of-thought for next iteration

- Continue seeding with the new live library.
- The current config (pop 50/gen 12, dedup 0.80, max_pairwise_corr 0.40) is a
  strong baseline.
- If progress stalls, try `max_pairwise_corr 0.35` or increase the evolution
  budget further.
- Run a fresh coverage/sector-neutrality audit on the new live library before
  production use.

## References

- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_133300.md`]
- [source: `wiki/factor_mining_loop_iteration_9.md`]
