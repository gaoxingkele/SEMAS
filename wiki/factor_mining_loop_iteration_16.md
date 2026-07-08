---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-16, ensemble-learning, weight-methods]
sources:
  - ../china_a_share_alpha/scripts/run_factor_combination.py
  - ../china_a_share_alpha_output/factor_mining_loop/iter_16_weight_methods
related:
  - factor_mining_loop_iteration_15.md
  - factor_mining_loop_iteration_17.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 16 Chain-of-Thought

## Trigger

Test whether ensemble-learning weighting schemes improve the current best
library beyond simple equal weighting.

## Setup

- Used the iteration-12 live library (10 factors) as the fixed candidate set.
- Ran `run_factor_combination.py` with five weight methods:
  `equal`, `ic`, `sharpe`, `risk_parity`, `ridge`.
- Each run used the same train/val/test split, greedy correlation filter 0.40,
  top-N=10, and EMA smoothing span=10.
- Metrics estimated weights on the validation fold (or train if no val).

## Results

| Weight method | Val Sharpe | Test Sharpe | Test cost-adj return | Max corr |
|---|---|---|---|---|
| equal         | 1.1830 | **2.7629** | **32.47%** | 0.3744 |
| ic            | 1.3760 | 1.8546 | 19.53% | — |
| sharpe        | 1.4159 | 2.0114 | 18.82% | — |
| risk_parity   | 1.1830 | 2.7629 | 32.47% | 0.3744 |
| ridge         | 3.0559 | 0.4910 | -3.14% | — |

- `risk_parity` collapsed to equal weights because the selected factors have
  very similar long-short volatilities in this library.
- `ridge` heavily overfit the validation fold (val Sharpe 3.06, test Sharpe 0.49).

## Decision

- **Not promoted.** Equal weighting remains the best combination method for the
  current live library.
- No change to the live library.

## New knowledge

1. **Equal weight is a surprisingly strong baseline.** More sophisticated
   weighting did not improve out-of-sample performance on this candidate set.
2. **Ridge regression on factor z-scores overfits** when the candidate count is
   small relative to the number of observations.
3. **Risk-parity weights collapse to equal when volatilities are homogeneous.**
4. **Weight-method selection should be treated as a hyperparameter** and
   evaluated on a validation fold, but even the validation-best method (ridge)
  did not generalize.

## References

- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `wiki/factor_mining_loop_iteration_12.md`]
