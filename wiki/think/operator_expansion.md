---
date: 2026-07-07
tags: [factor-mining, operators, grammar, high-order]
sources:
  - ../china_a_share_alpha/factor/expression.py
  - ../china_a_share_alpha/factor/parser.py
  - ../china_a_share_alpha/evolution/enhanced_factor_mutator.py
  - ../wiki/factor_mining_loop_iteration_14.md
related:
  - methodology_evolution_factor_mining.md
---

# Operator Expansion

## Motivation

The original grammar only supported first-moment and second-moment operators
(mean, std, rank, corr). Higher-order statistics (skewness, kurtosis,
autocorrelation, entropy) can capture tail risk and regime persistence that
mean/std miss.

## Added operators

- `ts_skew(x, n)` — rolling skewness.
- `ts_kurt(x, n)` — rolling kurtosis.
- `ts_autocorr(x, n)` — lag-1 autocorrelation inside a rolling window.
- `ts_entropy(x, n)` — Shannon entropy of equal-width binned values.

## Implementation detail

Used `min_periods=self.window` to avoid `min_periods > window` errors for
small windows. Entropy returns NaN for windows with fewer than 5 finite
observations or near-constant values.

## Result

A single evolution seed did not improve the live library. However, the
operators are now part of the grammar and are used in later evolutions (e.g.,
10d run produced a skew-based factor).

## Updated model

Operator expansion increases the search space. Its value depends on:
- Population size and generations (more search budget).
- Whether the target horizon matches the operator windows.
- Interaction with existing primitives (e.g., `cs_rank(ts_skew(...))`).

One seed run is insufficient to judge new operators.
