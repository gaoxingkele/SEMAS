---
date: 2026-07-07
tags: [factor-mining, transaction-cost, turnover, fitness]
sources:
  - ../china_a_share_alpha/scripts/run_factor_combination.py
  - ../wiki/factor_mining_loop_iteration_20.md
related:
  - methodology_evolution_factor_mining.md
  - multi_horizon_design.md
---

# Cost vs. Turnover Tradeoff

## Hypothesis

Using a higher transaction cost (20 bps) inside the evolution fitness will
naturally select lower-turnover factors, producing a more cost-robust library.

## Experiment

Iteration 20 set `transaction_cost: 0.002` in both the evolution and
combination configs. The resulting ensemble had turnover ~0.065% per day.

## Result

- Turnover dropped significantly.
- Test Sharpe (2.21) and cost-adjusted return (25.76%) did not beat the 10 bps
  library (2.76 / 32.47%).

## Why

The 10 bps library was already cost-robust. Paying a 20 bps fitness penalty
removed too many profitable but moderately high-turnover signals.

## Updated model

Transaction cost should be treated as a **scenario parameter**, not a global
optimization target. A production system can maintain multiple libraries tuned
for different cost assumptions (10 bps, 20 bps, 30 bps).

## Implication for 20d library

The 20d library has even lower turnover, so it may be particularly suitable
for higher-cost execution environments.
