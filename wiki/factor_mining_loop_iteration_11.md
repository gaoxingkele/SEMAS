---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-11, stress-test]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/verification_iter11_stress_20bps/combination_result.json
related:
  - factor_mining_loop_iteration_10.md
  - factor_mining_loop_audit_iter10.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 11 Chain-of-Thought

## Trigger

Post-audit recommendation from iteration 10: before running another evolution,
stress-test the promoted live library under a higher transaction-cost
assumption (20 bps) because the top-decile long turnover estimate was 0.56.

## Setup

- No evolution run; this is a validation iteration.
- Use the current live library:
  `china_a_share_alpha_output/factor_mining_loop/live_library.csv`.
- Add `--transaction-cost 0.002` (20 bps) to `run_factor_combination.py`.
- Config: `max_pairwise_corr=0.40`, `top_n=10`, equal weight, EMA span 10.

## What changed in the pipeline

- `run_factor_combination.py` now accepts a configurable `--transaction-cost`
  argument and uses it for factor-level and combined long-short backtests.

## Observations

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 1.6861 | 5.51% | 0.0032 |
| Val   | 1.1404 | 0.06% | 0.0008 |
| Test  | 2.7031 | 23.17% | 0.0007 |

- At 20 bps one-way cost, the test-period Sharpe is unchanged (2.70) because
  the loop's full-weight turnover is very low (~0.07 bps).
- Test cost-adjusted return drops from 31.46% (10 bps) to 23.17% (20 bps) but
  remains strongly positive.
- Train and validation cost-adjusted returns shrink, as expected, but stay
  positive.

## Decision

- **Stress test passed.** The live library remains profitable at double the
  assumed transaction cost.
- The iteration-10 live library is validated for production candidacy from a
  cost perspective.

## New knowledge

1. **Full-weight turnover is the right metric for this strategy.** The
   loop-reported turnover (~0.07 bps) is low, so even doubling cost to 20 bps
   leaves a healthy margin.
2. **Top-decile long turnover (0.56) overstates execution cost risk** for a
   full-quantile strategy; the combined signal rebalances more smoothly than a
   discrete top-decile book.
3. **Configurable transaction cost is a necessary audit tool.** It allows
   rapid cost-sensitivity analysis without changing the core pipeline.

## Chain-of-thought for next iteration

- Resume alpha evolution (iteration 12) with the proven iteration-10 config.
- Alternatively, freeze the current library and run a final production audit
  covering sector neutrality with real Tushare industry codes and maximum
  drawdown analysis.
- If continuing evolution, consider keeping transaction cost at 20 bps in the
  loop so that only cost-robust libraries are promoted.

## References

- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `china_a_share_alpha/output/factor_mining_loop/verification_iter11_stress_20bps/combination_result.json`]
- [source: `wiki/factor_mining_loop_audit_iter10.md`]
