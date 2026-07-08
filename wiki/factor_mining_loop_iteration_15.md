---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-15, alternative-data, money-flow]
sources:
  - ../china_a_share_alpha/data/tushare_loader.py
  - ../china_a_share_alpha/evolution/factor_mutator.py
  - ../china_a_share_alpha/factor/parser.py
  - ../china_a_share_alpha/scripts/run_factor_mining_loop.py
  - ../china_a_share_alpha_output/factor_mining_loop/moneyflow_seed_library.csv
related:
  - factor_mining_loop_iteration_14.md
  - factor_mining_loop_iteration_16.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 15 Chain-of-Thought

## Trigger

Fuse alternative microstructure data into the factor library by adding
money-flow buy/sell amounts and seeding evolution with capital-flow priors.

## Setup

- Extended `tushare_loader.py` to fetch and cache additional `moneyflow` fields:
  `buy_elg_amount`, `sell_elg_amount`, `buy_lg_amount`, `sell_lg_amount`,
  `buy_md_amount`, `sell_md_amount`, `buy_sm_amount`, `sell_sm_amount`.
- Registered the new fields in `ENRICHED_COLUMNS`, `factor_mutator.VARIABLES`,
  and `parser.py`.
- Added `extra_seed_libraries` support to `run_factor_mining_loop.py` so a
  domain-specific seed library can be merged with the live library before
  evolution.
- Created `moneyflow_seed_library.csv` with 8 money-flow expressions:
  - net-main-force / total market cap rank
  - net-elite / circulating market cap rank
  - 5-day mean of net-main-force / total market cap
  - 5-day delta of net-elite / circulating market cap
  - large-order buy-sell imbalance
  - elite-to-main-force ratio
  - 10-day autocorrelation of net-main-force / total market cap
  - 20-day entropy of net-elite / circulating market cap
- Seeded the enhanced evolution with the iteration-12 live library + the
  money-flow seed library.
- Evolution: forward_period=5, pop 30, gen 8, seed 1029.

## Why money flow?

- A-share price movements are heavily driven by retail and institutional order
  flows. Buy/sell imbalance at different size tiers (small, medium, large,
  elite) can capture informed trading pressure.
- Normalizing by market cap or circulating market cap makes flows comparable
  across large and small constituents.
- Rolling statistics (mean, delta, autocorrelation, entropy) let the genetic
  program combine flow dynamics with existing price/fundamental signals.

## Observations

- The merged library contained 25 unique expressions (live library + 8
  money-flow seeds + new leaderboard).
- Cleaning retained 15 factors; semantic dedup only dropped the `high_zscore_20`
  seed, leaving 15 candidates.
- The combined ensemble passed all hard gates (positive train Sharpe,
  ≥5 factors, max selection correlation 0.348).
- Test Sharpe (2.02) and cost-adj return (16.99%) did not beat the iteration-12
  live library (2.76 / 32.47%).
- Money-flow seeds improved validation Sharpe (2.04) but did not generalize to
  the test fold.

## Metrics

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 1.6390 | 16.87% | 0.00057 |
| Val   | 2.0439 | 17.65% | 0.00057 |
| Test  | 2.0207 | 16.99% | 0.00055 |

## Decision

- **Not promoted.** The iteration-12 live library remains the current best.
- The new money-flow fields stay in the data loader and are available to future
  evolutionary runs.

## New knowledge

1. **Money-flow fields are now part of the data pipeline.** Buy/sell amounts by
   size tier are cached and usable by the expression grammar.
2. **Domain-specific seeds do not guarantee test improvement.** Validation
   Sharpe looked promising, but the test fold did not follow through.
3. **The live library is a high bar.** Further gains may require ensemble-level
   or regime-aware combination rather than more raw features.

## References

- [source: `china_a_share_alpha/data/tushare_loader.py`]
- [source: `china_a_share_alpha/evolution/factor_mutator.py`]
- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `wiki/factor_mining_loop_iteration_12.md`]
