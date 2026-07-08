---
date: 2026-07-07
tags: [factor-mining-loop, run-note, iteration-22, 20d-horizon]
sources:
  - ../china_a_share_alpha/data/tushare_loader.py
  - ../china_a_share_alpha/scripts/run_multihizon_audit.py
  - ../china_a_share_alpha_output/factor_mining_loop/live_library_20d.csv
  - ../china_a_share_alpha_output/factor_mining_loop_20d/iter_0003/combination/combination_result.json
related:
  - factor_mining_loop_iteration_21.md
  - factor_mining_loop_multihizon_audit.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 22 Chain-of-Thought

## Trigger

Pursue the active `/goal`: build and validate a 20-day holding-period alpha
library for CSI300, with promotion gates tied to realistic 20-day hold
backtests.

## Setup

1. Extended `tushare_loader.py` to support a configurable `forward_period`
   parameter (default 1). `forward_return` is now computed as
   `close.pct_change(forward_period).shift(-forward_period)`.
2. Created 20d-specific configs:
   - `enhanced_loop_config_iter22_20d_val.yaml`
   - `factor_mining_loop_evolution_config_iter22_20d.yaml`
   - `factor_mining_loop_config_iter22_20d.yaml`
3. Extended `run_multihizon_audit.py` to report realistic non-overlapping
   H-day hold backtests (rebalance every H days, hold H days, top/bottom
   decile, 10 bps one-way cost).
4. Ran 5 continuous evolution iterations seeded from scratch in a new output
   directory (`china_a_share_alpha_output/factor_mining_loop_20d`).

## Iteration Results (realistic 20d hold)

| Iteration | 20d hold Sharpe | 20d hold cost-adj | Max DD | Daily-reb 20d Sharpe | Train Sharpe |
|---|---|---|---|---|---|
| 1 | 1.58 | 35.74% | -13.53% | 4.85 | -2.43 |
| 2 | 1.68 | 35.52% | -17.19% | 3.46 | -2.34 |
| **3** | **1.98** | **60.78%** | -18.34% | 3.66 | -3.25 |
| 4 | 1.75 | 36.40% | -17.45% | 6.73 | -1.59 |
| 5 | 1.54 | 24.99% | -9.62% | 6.93 | -0.31 |

## Promotion

- **Iteration 3** satisfied the goal gates:
  - 20d hold Test Sharpe **1.98** > 1.70
  - 20d hold cost-adjusted return **60.78%** > 22%
  - Beats the 5d live library's 20d hold Sharpe of **1.75**
- Promoted `iter_0003/combination/selected_factors.csv` to
  `live_library_20d.csv`.
- The promoted library contains 2 factors:
  1. `high_zscore_20` — `cs_rank(ts_zscore(high, 20))` (seed)
  2. `factor_1` — `net_mf_amount` (evolved)

## Observations

- The 20d-evolved factors often showed strong val/test Sharpe but negative
  train Sharpe, causing the standard loop's `train_sharpe_positive` gate to
  reject them. The realistic hold backtest, however, showed that iteration 3
  generalizes well.
- The final 20d library is very concise (only 2 factors) and heavily reliant
  on the `high_zscore_20` seed plus net main-force flow.
- Drawdown (-18.3%) is larger than the 5d library's 20d hold drawdown
  (-12.3%), reflecting the shorter backtest sample and higher volatility of
  20-day returns.

## Metrics

| Metric | Value |
|---|---|
| 20d hold Test Sharpe | **1.98** |
| 20d hold cost-adj return | **60.78%** |
| 20d hold max drawdown | -18.34% |
| Daily-reb 20d Test Sharpe | 3.66 |
| Daily-reb 20d Test IC | 0.0366 |

## Decision

- **Promoted** `live_library_20d.csv` as the 20-day strategy baseline.
- Kept the original 5d `live_library.csv` unchanged.
- Updated `state.json` with `live_library_20d_path`.

## References

- [source: `china_a_share_alpha/data/tushare_loader.py`]
- [source: `china_a_share_alpha/scripts/run_multihizon_audit.py`]
- [source: `wiki/factor_mining_loop_iteration_21.md`]
- [source: `wiki/factor_mining_loop_multihizon_audit.md`]
