---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-20, transaction-cost, cost-aware]
sources:
  - ../china_a_share_alpha/examples/factor_mining_loop_config_iter20.yaml
  - ../china_a_share_alpha_output/factor_mining_loop/iter_0020/combination/combination_result.json
related:
  - factor_mining_loop_iteration_19.md
  - factor_mining_loop_iteration_21.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 20 Chain-of-Thought

## Trigger

Run a cost-aware evolution where the fitness function and combination
backtest use a 20 bps one-way transaction cost, to see if a lower-turnover
ensemble emerges.

## Setup

- Set `transaction_cost: 0.002` in both the evolution config and the data
  config.
- Seeded evolution with the iteration-12 live library.
- Evolution: forward_period=5, pop 30, gen 8, seed 1040.
- Cleaning and combination also used 20 bps.

## Observations

- The merged library contained 28 expressions.
- Cleaning retained 13 factors; semantic dedup left 12 candidates.
- The new ensemble passed all hard gates and had low turnover (0.065%).
- Test Sharpe (2.21) and cost-adj return (25.76%) did not beat the 10 bps
  iteration-12 live library (2.76 / 32.47%).

## Metrics

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 1.7131 | 19.26% | 0.00346 |
| Val   | 0.5080 | -0.31% | 0.00068 |
| Test  | 2.2126 | 25.76% | 0.00065 |

## Decision

- **Not promoted.** The iteration-12 live library remains the best when
  evaluated at 10 bps.
- The 20 bps evolution produced a viable lower-cost ensemble but not a better
  one at the benchmark cost assumption.

## New knowledge

1. **Cost-aware evolution does reduce turnover.** The selected ensemble has
   very low turnover (~6.5 bps per day).
2. **Lower turnover does not automatically beat the existing best.** The
   10 bps-evolved library is already cost-robust.
3. **Transaction cost is a useful fitness knob** for production scenarios
   where execution costs are higher than the baseline assumption.

## References

- [source: `china_a_share_alpha/examples/factor_mining_loop_config_iter20.yaml`]
- [source: `wiki/factor_mining_loop_iteration_12.md`]
