---
date: 2026-07-07
tags: [factor-mining, regime-switching, state-dependent, experiment]
sources:
  - ../china_a_share_alpha/scripts/run_regime_combination.py
  - ../wiki/factor_mining_loop_iteration_17.md
related:
  - methodology_evolution_factor_mining.md
---

# Regime Switching Experiment

## Hypothesis

High-volatility and low-volatility market days favor different factors. A
volatility-regime switch should improve the ensemble by selecting factors
specifically for each regime.

## Design

- Regime label: EMA-smoothed cross-sectional median absolute return above its
  training-set median.
- For each regime, select top-N factors by in-regime training IC.
- Combine signals day-by-day using regime-specific weights.

## Result

- Top-5 per regime: overfit validation, poor test Sharpe (1.18).
- Top-10 per regime: selected the same factors in both regimes, collapsing to
  equal weight.

## Why it failed

1. The regime label (median absolute return) is noisy and not economically
   stable.
2. Equal weight is already strong; regime-specific selection adds
   overfitting risk without clear benefit.
3. Per-regime selection reduces sample size, amplifying variance.

## Updated model

For state-dependent weights to work, the regime variable must be:
- Stable and slow-moving.
- Economically interpretable (e.g., credit spread, liquidity stress, policy
  cycle).
- Have a clear theoretical link to factor payoffs.

A pure volatility split is too weak for CSI300.
