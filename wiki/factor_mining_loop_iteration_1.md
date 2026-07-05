---
date: 2026-07-04
tags: ['factor-mining-loop', 'run-note', 'iteration-1']
sources: ['../china_a_share_alpha_output/factor_mining_loop/loop_report_20260704_011353.md']
---
# Factor Mining Loop — Iteration 1 Chain-of-Thought

> Date: 2026-07-04
> Source run: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260704_011353.md`

## Trigger

Implement and run the first iteration of the continuous factor-mining loop,
following the loop-engineering pattern. The live library starts empty, so the
iteration begins from scratch with a small population (pop 25, gen 8) to keep
runtime manageable.

## Observations

- **Evolution**: seed 1001, pop 25, gen 8, no seed library.
- **Merge**: 21 unique expressions after merging the new leaderboard with the
  (empty) live library.
- **Clean**: only 2 expressions survived validation-aware cleaning with the
  loose thresholds set for the first run.
- **Combine**: added `high_zscore_20` and ran equal-weight + EMA(span=10) on
  top val-IC factors.
- **Metrics**:
  - Train Sharpe: -0.389
  - Test Sharpe: 1.6283
  - Test cost-adjusted return: 24.75%

## Decision

- **Promoted** the new library because it improved over the empty baseline.
- Wrote `live_library.csv` with the 2 cleaned expressions plus the manual
  `high_zscore_20` factor.

## New knowledge

1. **A tiny ensemble can produce a high test Sharpe.** Three factors (2
   evolved + 1 manual) achieved Sharpe 1.63 on the test set.
2. **High test Sharpe does not imply stability.** The same ensemble had a
   negative train-period Sharpe, meaning the alpha is concentrated in the
   2023-2026 window (validation + test) and fails in 2021-2022.
3. **The cleaning pipeline is very aggressive.** With `min_daily_coverage=0.5`
   and loose IC thresholds, only 2 of 21 expressions survived. Many candidates
   are either sparse (fundamental-based) or do not hold out-of-sample.
4. **Live-library seeding works mechanically.** The script successfully seeded
   the next iteration from the promoted library.

## Chain-of-thought for next iteration

- Keep the live library as the seed but expect rapid convergence to similar
  structures.
- If the next iteration does not improve, introduce a train-Sharpe gate and a
  diversity gate before promotion.
- Investigate why the first factor uses `eps`, `ocfps`, `turnover_rate`, and
  `total_mv` — it may be a size/profitability interaction that only worked in
  the recent regime.
- Consider lowering the weight of `high_zscore_20` or replacing it with a
  stronger manual alpha once more evolved factors are available.

## Anomalies

- Train Sharpe negative while test Sharpe is strongly positive. This is the
  classic sign of a regime shift or selection bias through the validation fold.
  It should be treated as a red flag, not a reason to celebrate.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
- [source: `LOOP.md`]

## Related pages

- [factor_mining_loop_iteration_2](factor_mining_loop_iteration_2.md)
- [factor_mining_loop_index](factor_mining_loop_index.md)
- [index](index.md)
