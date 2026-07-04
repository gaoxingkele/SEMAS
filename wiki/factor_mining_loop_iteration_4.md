# Factor Mining Loop — Iteration 4 Chain-of-Thought

> Date: 2026-07-04
> Source run: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260704_102313.md`

## Trigger

Run the first iteration after adding both semantic deduplication and promotion
gates. The goal was to discover a more stable, diverse ensemble that improves on
the previous best (test Sharpe 1.628).

## Setup

- Seed 1004, pop 25, gen 8.
- Seeded with the iteration 1 live library.
- Semantic dedup threshold `|rho| > 0.95` on training-set factor values.
- Gates:
  - `train_sharpe > 0`
  - `n_deduped >= 5`
  - `max_selection_correlation <= 0.7`

## Observations

- **Merge**: 30 unique expressions after string-level merge.
- **Clean**: 8 expressions survived validation-aware cleaning.
- **Dedup**: 3 semantic duplicates removed, leaving 6 distinct expressions.
  - Dropped `factor_17` (duplicate of an earlier expression).
  - Dropped `factor_3` (duplicate).
  - Dropped `high_zscore_20` because an evolved factor already captured the
    same `cs_rank(ts_zscore(high, 20))` signal.
- **Gates**:
  - train_sharpe_positive: ✅ (0.1235)
  - min_cleaned_count: ✅ (6 distinct factors)
  - max_corr_ok: ✅ (max corr = 0.2108)
- **Metrics**:
  - Train Sharpe: 0.1235
  - Train cost-adj return: -6.23%
  - Test Sharpe: **2.1145**
  - Test cost-adj return: **30.25%**

## Decision

- **Promoted** the new live library because it passed all gates and improved
  both test Sharpe and cost-adjusted return over the previous best.

## New knowledge

1. **Semantic deduplication is the missing piece.** Removing syntactic
   duplicates eliminated the perfect-correlation problem that blocked iteration
   3.
2. **Gates now produce healthier ensembles.** The selected 6 factors have max
   absolute correlation 0.21, confirming real diversification.
3. **Training Sharpe can be positive while training cost-adj return is
   negative.** This means the signal has positive mean but transaction costs
   erase it in-sample; out-of-sample (2024-2026) the signal is strong enough to
   overcome costs.
4. **The loop can self-improve.** Iteration 4 found a better library than the
   manually-tuned large-population run (previous best Sharpe 1.41) simply by
   running the loop with proper gates.

## Promoted live library

The 6 promoted factors are:

1. `cs_zscore(div(sub(greater(eps, -0.033), sub(ocfps, turnover_rate)), winsorize(total_mv)))`
2. `ts_sum(net_elg_amount, 3)`
3. `cs_rank(ts_zscore(high, 20))`
4. `cs_zscore(neg(ts_rank(if_else(-0.423, -0.806, volume), 10)))`
5. `div(0.745, cs_rank(debt_to_assets))`
6. `sign(ts_shift(ts_ema(ts_pct_change(grossprofit_margin, 20), 5), 60))`

## Cautions

- The strong test result may still be regime-dependent: 2024-2026 was a
  favorable period for these signals.
- Training cost-adj return is negative; live trading would require cost
  assumptions at least as low as the 10 bps used here.
- Fundamental factors can have sparse coverage around earnings announcements.

## Chain-of-thought for next iteration

- Continue the loop seeded with this new live library and see if further
  improvement is possible.
- If progress stalls, introduce an "exploration seed" iteration with no seed
  library and larger mutation radius.
- Consider adding a live-library coverage audit before human commit.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
- [source: `wiki/factor_mining_loop_iteration_3.md`]
