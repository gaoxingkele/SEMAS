---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-12, multi-horizon]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/iter_0012_combination/combination_result.json
  - ../china_a_share_alpha_output/factor_mining_loop/verification_iter_12
related:
  - factor_mining_loop_iteration_11.md
  - factor_mining_loop_iteration_13.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 12 Chain-of-Thought

## Trigger

Diversify factor mining ideas by exploring multi-time-horizon signals: evolve
factors for 5-day and 10-day forward returns, then combine with the existing
live library.

## Setup

- Two parallel evolution runs seeded with the iteration-10 live library:
  - `iter_0012_5d`: forward_period=5, pop 30, gen 8, seed 1201.
  - `iter_0012_10d`: forward_period=10, pop 30, gen 8, seed 1202.
- Merge both leaderboards with the live library (46 unique expressions).
- Clean with loose thresholds (coverage ≥ 0.50), keep 21 factors.
- Combine top 10 with greedy correlation filter 0.40 and equal weight.

## Observations

- 5-day run produced 40 candidates; best test Sharpe ~0.72.
- 10-day run produced 40 candidates; best test Sharpe ~0.80.
- Merged + cleaned library: 21 factors.
- Combined ensemble (10 selected): max corr 0.3744.

## Metrics

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 1.3620 | 15.91% | 0.0012 |
| Val   | 1.1830 | 9.64% | 0.0008 |
| Test  | 2.7629 | 32.47% | 0.0007 |

## Decision

- **Promoted** the new 10-factor live library.
- New best: test Sharpe 2.76, cost-adj 32.47%.
- Independent verification reproduced the metrics exactly.

## New knowledge

1. **Multi-horizon evolution adds orthogonal signals.** 5-day and 10-day
   forward-return objectives produced different expressions that improved the
   combined ensemble.
2. **Greedy correlation filtering remains essential.** The selected 10 factors
   had max correlation 0.37, satisfying the diversity gate.
3. **Seeding with live library + running parallel objectives** is an efficient
   way to explore without losing good existing structures.

## References

- [source: `china_a_share_alpha/scripts/run_enhanced_factor_loop.py`]
- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `wiki/factor_mining_loop_iteration_11.md`]
