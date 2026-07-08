---
date: 2026-07-07
tags: [factor-mining, multi-horizon, evaluation, methodology]
sources:
  - ../china_a_share_alpha/data/tushare_loader.py
  - ../china_a_share_alpha/scripts/run_multihizon_audit.py
related:
  - methodology_evolution_factor_mining.md
  - cost_turnover_tradeoff.md
---

# Multi-Horizon Design

## Problem

The original `tushare_loader.py` hardcoded `forward_return` as the next-day
return. This meant that "5d" or "20d" configurations were only labels; the
actual fitness always targeted a 1-day horizon. To study horizon-specific
factors, the data layer must support a configurable `forward_period`.

## Solution

Change the forward return computation to:

```python
data["forward_return"] = (
    data.groupby(level="symbol")["close"]
    .pct_change(forward_period)
    .shift(-forward_period)
)
```

with `forward_period` defaulting to 1.

## Why this matters

- **IC scales with horizon**: For the existing 10-factor library, test IC rose
  from 0.038 (5d) to 0.053 (20d), suggesting slower signal decay than noise.
- **Sharpe does not scale linearly**: Daily-rebalance backtests against
  overlapping H-day returns produce inflated Sharpe ratios (e.g., 8.09 for
  20d). These are not comparable to non-overlapping 1-day backtests.
- **Realistic hold backtests are required**: Rebalancing every H days and
  holding H days gives stable Sharpe around 1.6–1.8 across horizons.

## Design decision

Use two evaluation modes:

1. **Daily-rebalance vs H-day forward return** — useful for factor IC ranking
   and evolution fitness.
2. **H-day hold backtest** — required for final promotion and real-world
   feasibility.

## Future work

- Add non-overlapping forward return targets for cleaner backtests.
- Study whether H-day IC is enough as a fitness proxy, or whether hold Sharpe
  should be used directly in evolution.
