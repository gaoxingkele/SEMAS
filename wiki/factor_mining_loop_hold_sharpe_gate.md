---
date: 2026-07-11
tags: [factor_mining, hold_sharpe, promotion_gate, evolution, overfitting]
sources:
  - china_a_share_alpha/scripts/run_factor_mining_loop.py
  - china_a_share_alpha_output/batch_multihizon_audit/FINDINGS.md
related:
  - factor_mining_loop_multihizon_batch_audit.md
  - factor_mining_loop_index.md
---

# Hold-Sharpe Promotion Gate

## Problem

The factor-mining loop promoted libraries based on loop-level **daily-rebalanced,
overlapping forward-return Sharpe and cost-adjusted return**.  After iter ~32,
later iterations kept improving these loop metrics while their **realistic
non-overlapping hold Sharpe degraded** [source: local batch audit].  This is a
classic overfit-to-the-metric pattern.

## Solution

Added an optional realistic **hold-Sharpe gate** to
`china_a_share_alpha/scripts/run_factor_mining_loop.py` [source: local].

### New config keys

| Key | Default | Meaning |
|---|---|---|
| `use_hold_sharpe_gate` | `false` | Enable the gate |
| `hold_horizon` | `5` | Days between rebalances |
| `hold_transaction_cost` | `0.001` | One-way cost |
| `min_hold_sharpe_gate` | `1.0` | Absolute minimum hold Sharpe |
| `promote_hold_sharpe_threshold` | `0.03` | Required improvement over best hold Sharpe |
| `promotion_evaluation_mode` | `simple_hold` | `simple_hold` or `dynamic_trim` |
| `min_factor_coverage` | `0.5` | Minimum available-factor fraction per row |

### Promotion rule (when enabled)

A library is promoted only if:

1. All hard gates pass (train Sharpe, min factor count, max selection
   correlation, and hold Sharpe ≥ `min_hold_sharpe_gate`).
2. Its realistic hold Sharpe improves over the live baseline by at least
   `promote_hold_sharpe_threshold` under the same evaluation contract.

Loop-level overlapping Sharpe and return remain diagnostics; they do not decide
promotion when the hold gate is enabled.

This ties the loop's objective more closely to production reality.

## Deployment

Enabled the gate for all three horizon loops:

- 5d loop: horizon=5
- 10d loop: horizon=10
- 20d loop: horizon=20

For the 10d and 20d loops, `min_train_sharpe_gate` was relaxed to `-2.0` and
`min_cleaned_gate` lowered to `3`, because these horizons currently produce
negative train Sharpe on 2021-2022.  The realistic hold-Sharpe gate now dominates
promotion decisions.

## Other fixes

- Restored 5d live library to `iter_26` (best realistic 5d hold Sharpe 2.49).
- Fixed `run_factor_combination.py` read-only NumPy array bug
  (`corr_matrix.abs().values.copy()`).
- Fixed `china_a_share_alpha/factor/expression.py` to handle `None` results,
  object-dtype Series, and missing columns during expression evaluation,
  preventing `TypeError`/`KeyError` crashes in evolved 20d expressions.
- Created missing 10d loop `state.json`.
- Promoted 20d `iter_0005` to live library (20d hold Sharpe 1.51).
- Reduced 10d/20d evolution configs to `population_size=15` and
  `max_generations=5` so iterations complete in ~10-15 minutes instead of
  30-40 minutes.

## Takeaway

Promotion criteria should match the actual trading implementation.  Loop-level
overlapping metrics are useful for search, but the final gate must be a
realistic, cost-adjusted, non-overlapping backtest.

## Related pages

The 2026-07-16 contract applies all position targets to next-day returns, uses
continuous historical warm-up, and standardizes cohorts at top/bottom 20%.
The 5d loop retains dynamic trim, the 10d loop uses simple hold, and the 20d
loop has `promotion_enabled: false` while it remains research-only [source:
local horizon audit and loop configs].

- [Frozen Promotion Audit](factor_promotion_frozen_audit_20260713.md)
- [Batch Multi-Horizon Audit](factor_mining_loop_multihizon_batch_audit.md)
- [Factor Mining Loop Index](factor_mining_loop_index.md)
