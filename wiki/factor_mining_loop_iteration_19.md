---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-19, anti-correlation]
sources:
  - ../china_a_share_alpha/scripts/run_anticorr_factor_search.py
  - ../china_a_share_alpha_output/factor_mining_loop/iter_0019_anticorr/anticorr_leaderboard.csv
related:
  - factor_mining_loop_iteration_18.md
  - factor_mining_loop_iteration_20.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 19 Chain-of-Thought

## Trigger

Search for factors that are deliberately uncorrelated with the current live
library combined signal, hoping to add orthogonal alpha and improve
 diversification.

## Setup

- Added `china_a_share_alpha/scripts/run_anticorr_factor_search.py`.
- Computed the live-library equal-weight combined signal on the training fold.
- Generated 50 random expressions with `EnhancedFactorMutator(mode="gp")`.
- Scored each candidate by `abs(train_ic) - 2 * abs(corr_with_live)`.
- Took the top 10 anti-correlation candidates and merged them with the live
  library, then ran the standard combination.

## Observations

- Most candidates had negative train IC and negative correlation with the live
  signal, meaning they were not orthogonal alpha but rather opposite-side noise.
- The merged ensemble selected 10 factors with very high turnover (15.9%).
- Train Sharpe was strongly negative, indicating the anti-correlation candidates
  hurt the in-sample signal.

## Metrics

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | -4.4016 | -167.67% | 0.1009 |
| Val   | — | — | — |
| Test  | 1.1437 | 10.19% | 0.1590 |

## Decision

- **Not promoted.** The anti-correlation candidates failed the train-Sharpe and
  turnover gates and did not improve test performance.
- The anti-correlation search script is retained for future experiments with
  different scoring functions.

## New knowledge

1. **Low correlation alone is not enough.** A factor uncorrelated with the live
   library can still be noise.
2. **The scoring function must also require sign consistency.** Candidates with
   negative train IC should be discarded regardless of correlation.
3. **High turnover dilutes cost-adjusted returns.** Even with positive raw
   returns, transaction costs dominate when turnover exceeds ~10%.

## References

- [source: `china_a_share_alpha/scripts/run_anticorr_factor_search.py`]
- [source: `wiki/factor_mining_loop_iteration_18.md`]
