---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-7]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_114032.md
related:
  - factor_mining_loop_iteration_6.md
  - factor_mining_loop_iteration_8.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 7 Chain-of-Thought

## Trigger

Test whether an empty-seed exploration run with a larger evolution budget and
stricter gates could discover a new library independent of the current
2.20-Sharpe live library.

## Setup

- Seed 1007, pop 40, gen 10.
- Empty seed library (`--no-live-seed`).
- `min_daily_coverage` raised to 0.90.
- `max_selection_correlation_gate` tightened to 0.50.
- `min_cleaned_gate` = 5.

## Observations

- **Merge**: 37 unique expressions.
- **Clean**: only 2 expressions survived.
- **Dedup**: 3 expressions after adding `high_zscore_20`.
- **Gates**:
  - train_sharpe_positive: ❌ (-0.0696)
  - min_cleaned_count: ❌ (3 < 5)
  - max_corr_ok: ✅ (max corr = 0.0838)
- **Metrics**:
  - Train Sharpe: -0.0696
  - Train cost-adj return: -12.03%
  - Test Sharpe: 1.2424
  - Test cost-adj return: 10.91%

## Diagnosis

The cleaning stage was the bottleneck. With `min_daily_coverage=0.90`, almost
any expression touching lower-coverage fields (`hk_vol`, `ocfps`, fundamental
YoY metrics, `pb`, etc.) was discarded. Several high-test-Sharpe price/volume
candidates were lost to the coverage gate. The remaining two factors were too
weak to produce a positive train Sharpe.

## Decision

- **Did not promote.** The existing 7-factor live library (test Sharpe 2.20) is
  retained.
- Iteration 8 should return to live-library seeding, restore
  `min_daily_coverage` to 0.50, keep the 0.50 correlation gate, and increase the
  evolution budget.

## New knowledge

1. **Raising `min_daily_coverage` to 0.90 on an empty seed over-prunes.** The
   resulting library is too small and in-sample weak.
2. **Coverage and seed strategy interact strongly.** A strict coverage gate may
   be viable with a seeded run that already contains dense factors, but it is
   dangerous with random empty-seed initialization.
3. **The 0.50 max-correlation gate is healthy.** It passed easily in iteration 7
   and should be retained as an overfit guard.

## Chain-of-thought for next iteration

- Re-seed with the live library.
- Use pop 50 / gen 12 / leaderboard 75.
- Restore `min_daily_coverage=0.50`.
- Keep `max_selection_correlation_gate=0.50`.
- If this stalls, run a dedicated empty-seed exploration burn with coverage 0.50
  and `min_cleaned_gate=3` to find orthogonal signals for a later merge.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_114032.md`]
- [source: `wiki/factor_mining_loop_iteration_6.md`]
