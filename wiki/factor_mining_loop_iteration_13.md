---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-13, cross-market-transfer]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/iter_0013_combination/combination_result.json
related:
  - factor_mining_loop_iteration_12.md
  - factor_mining_loop_iteration_14.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 13 Chain-of-Thought

## Trigger

Test cross-market transfer: evolve factors on CSI500 and CSI1000, then clean
and combine them on CSI300 to see if they add orthogonal alpha.

## Setup

- Two parallel evolutions seeded with the iteration-12 live library:
  - `iter_0013_csi500`: universe=csi500, pop 30, gen 8, seed 1301.
  - `iter_0013_csi1000`: universe=csi1000, pop 30, gen 8, seed 1302.
- Merge both leaderboards with the live library (48 unique expressions).
- Clean and evaluate all expressions on CSI300.
- Combine top 10 with greedy correlation filter 0.40 and equal weight.

## Observations

- CSI500 run: best in-market test Sharpe -4.13 (different universe).
- CSI1000 run: best in-market test Sharpe 2.67 (different universe).
- After cleaning on CSI300, 17 / 48 expressions survived.
- Combined ensemble (10 selected): max corr 0.37.

## Metrics on CSI300

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 2.5234 | 25.79% | 0.0006 |
| Val   | 1.8354 | 14.73% | 0.0006 |
| Test  | 1.8354 | 14.73% | 0.0006 |

## Decision

- **Did not promote.** The cross-market ensemble underperformed the current
  best (test Sharpe 1.84 vs 2.76, cost-adj 14.73% vs 32.47%).
- The iteration-12 live library is retained.

## New knowledge

1. **Cross-market transfer is not automatically additive.** Factors that work
   in CSI500/CSI1000 do not necessarily improve a CSI300 ensemble after
   cleaning.
2. **Different universes have different alpha structures.** CSI500/CSI1000 may
   favor smaller-cap signals that do not scale to CSI300 large caps.
3. **Cleaning on the target market is essential** but can discard most
   transferred candidates.

## Chain-of-thought for next iteration

- Return to in-market CSI300 evolution for iteration 14.
- Instead of cross-market transfer, focus on operator expansion to introduce
   new functional forms (high-order moments, entropy, autocorrelation).

## References

- [source: `china_a_share_alpha/scripts/run_enhanced_factor_loop.py`]
- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `wiki/factor_mining_loop_iteration_12.md`]
