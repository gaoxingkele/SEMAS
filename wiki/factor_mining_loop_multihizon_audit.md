---
date: 2026-07-06
tags: [factor-mining-loop, audit, multi-horizon]
sources:
  - ../china_a_share_alpha/scripts/run_multihizon_audit.py
  - ../china_a_share_alpha_output/factor_mining_loop/multihizon_audit/ensemble_horizon.csv
  - ../china_a_share_alpha_output/factor_mining_loop/multihizon_audit/per_factor_horizon.csv
related:
  - factor_mining_loop_iteration_21.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Multi-Horizon Audit of the Live Library

## Trigger

Test the current 10-factor live library across 5-day, 10-day, and 20-day
forward returns to understand horizon sensitivity.

## Methodology

1. Loaded the same train/val/test split used in the final audit.
2. Computed H-day cumulative forward returns as
   `close.pct_change(H).shift(-H)` for H = 5, 10, 20.
3. Evaluated each factor and the equal-weight ensemble with daily rebalancing
   against the H-day forward return.
4. Also ran realistic non-overlapping H-day holding-period backtests for the
   ensemble (rebalance every H days, hold H days, top/bottom decile,
   10 bps one-way cost).

## Results — Daily-Rebalance vs H-Day Forward Return

### Ensemble

| Horizon | Train IC | Train Sharpe | Val IC | Val Sharpe | Test IC | Test Sharpe | Cost-adj | Max DD |
|---|---|---|---|---|---|---|---|---|
| 5d  | 0.0364 | 2.46 | 0.0244 | 3.04 | 0.0379 | 5.33 | 169.66% | -29.84% |
| 10d | 0.0179 | 1.55 | 0.0434 | 6.28 | 0.0453 | 6.58 | 290.52% | -49.92% |
| 20d | 0.0191 | 1.35 | 0.0569 | 8.40 | 0.0528 | 8.09 | 472.74% | -60.17% |

### Per-factor test IC ranking

#### 5d
- Top: `factor_57` (0.0181), `factor_17` (0.0156), `factor_27` (0.0155)
- Bottom: `factor_61` (0.0054), `iter12_factor_8` (0.0016), `factor_29` (0.0005)

#### 10d
- Top: `factor_57` (0.0273), `factor_17` (0.0215), `iter12_factor_26` (0.0205)
- Bottom: `factor_29` (0.0018), `factor_22` (0.0016), `factor_61` (-0.0074)

#### 20d
- Top: `factor_57` (0.0373), `iter12_factor_26` (0.0248), `factor_27` (0.0242)
- Bottom: `factor_22` (-0.0033), `factor_12` (-0.0039), `factor_61` (-0.0095)

## Results — Realistic H-Day Hold Backtest (ensemble)

| Horizon | Sharpe | Ann. return | Max drawdown |
|---|---|---|---|
| 5d  | 1.79 | 39.77% | -13.17% |
| 10d | 1.58 | 34.93% | -13.22% |
| 20d | 1.63 | 36.14% | -12.33% |

## Observations

- **IC increases with horizon.** Test IC rises from 0.038 (5d) to 0.053 (20d),
  suggesting the signal decays more slowly than noise at longer horizons.
- **Daily-rebalance Sharpe is inflated by overlapping returns.** The 5.33 / 6.58
  / 8.09 figures are not directly comparable to the original 2.76 baseline,
  which uses non-overlapping daily forward returns.
- **Realistic holding-period Sharpe is stable around 1.6–1.8.** The 5-day hold
  is slightly better than 10/20-day holds, but all remain attractive.
- **Factor_57** (`cs_zscore(div(sub(greater(eps, neg(0.033)), sub(ocfps, turnover_rate)), winsorize(total_mv)))`)
  dominates across all horizons.
- **Factor_61** (complex if-else expression) weakens as horizon lengthens,
  suggesting it captures short-term noise.

## Decision

- The live library is robust across horizons.
- For production, prefer the 5-day holding period for the best realistic
  Sharpe (1.79) and simplest execution.
- For lower-turnover strategies, the 20-day hold is a viable alternative with
  only modest degradation.

## References

- [source: `china_a_share_alpha/scripts/run_multihizon_audit.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/multihizon_audit/`]
