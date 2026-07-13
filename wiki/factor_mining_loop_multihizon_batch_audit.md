---
date: 2026-07-11
tags: [factor_mining, multi_horizon, audit, 5d, 10d, 20d, evolution]
sources:
  - china_a_share_alpha/scripts/batch_multihizon_audit.py
  - china_a_share_alpha_output/batch_multihizon_audit/FINDINGS.md
related:
  - factor_mining_loop_index.md
  - factor_mining_loop_iteration_28.md
---

# Batch Multi-Horizon Audit of All Evolved Iterations

## Why

The factor-mining loop had run 41 iterations for the 5d horizon, plus a handful
of 10d and 20d iterations, but audits were scattered and only covered selected
iterations.  A unified cross-iteration, cross-horizon evaluation was needed to
answer:

1. Which iteration library actually performs best on realistic, cost-adjusted,
   non-overlapping hold backtests?
2. Do later iterations keep improving, or do they overfit to the loop's internal
   overlapping-forward-return metric?
3. What is the current state of the 10d and 20d loops?

## What was done

Wrote `china_a_share_alpha/scripts/batch_multihizon_audit.py` [source: local]
to load the Tushare panel once and evaluate every iteration library on 5d, 10d,
and 20d forward returns.  Audited:

- 5d loop: iter_0001 – iter_0041
- 10d loop: iter_0001
- 20d loop: iter_0001 – iter_0005

Outputs are in `china_a_share_alpha_output/batch_multihizon_audit/`.

## Key results

### Best realistic hold Sharpe per loop/horizon

| Loop | Horizon | Best iter | Hold Sharpe | Hold return | Max DD |
|---|---|---:|---:|---:|---:|
| 5d | 5d | **26** | 2.49 | 73.70% | -11.96% |
| 5d | 10d | 39 | 2.31 | 60.83% | -12.12% |
| 5d | 20d | 33 | 2.43 | 67.03% | -11.65% |
| 10d | 5d | 1 | 4.43 | 79.71% | -4.81% |
| 10d | 10d | 1 | 3.13 | 49.29% | -6.51% |
| 10d | 20d | 1 | 1.91 | 24.13% | -11.85% |
| 20d | 5d | 3 | 3.53 | 147.02% | -15.61% |
| 20d | 10d | 3 | 2.39 | 78.11% | -17.78% |
| 20d | 20d | 3 | 1.81 | 53.81% | -19.09% |

### 5d loop: current live library is worse than earlier iterations

| Library | 5d Test Sharpe | 5d Hold Sharpe | Hold return | Hold DD |
|---|---:|---:|---:|---:|
| `live_library.csv` (iter 40) | 4.55 | 1.63 | 39.09% | -18.04% |
| iter_28 combined | 5.59 | 2.25 | 64.92% | -17.41% |
| iter_26 combined | 5.45 | **2.49** | **73.70%** | **-11.96%** |

### Overfitting pattern

Iterations 37–41 achieve very high loop-level Test Sharpe and cost-adjusted
return, but their realistic 5d hold Sharpe keeps declining.  The loop's
promotion criterion (overlapping daily-rebalanced Sharpe / return) diverges from
realistic non-overlapping hold performance after iter ~32.

### 10d / 20d loops are under-developed

- 10d loop has only one iteration (4 factors).
- 20d loop has five iterations but all fail the `train_sharpe_positive` gate;
  the best library contains only 2 factors.  High hold Sharpe is therefore
  fragile and likely overfit.

## Takeaways

1. **Promotion criterion should be tied to realistic hold Sharpe**, not just
   loop-level overlapping metrics.
2. **Restoring iter_26 or iter_28 as the 5d live library** is strongly supported
   by this audit.
3. **10d and 20d loops need more iterations** before a production-ready live
   library can be declared.

## Related pages

- [Factor Mining Loop Index](factor_mining_loop_index.md)
- [Iteration 28](factor_mining_loop_iteration_28.md)
