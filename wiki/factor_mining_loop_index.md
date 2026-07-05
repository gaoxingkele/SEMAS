---
date: 2026-07-04
tags: [factor-mining-loop, index]
related: [index.md, log.md]
---

# Factor Mining Loop — Wiki Index

This index collects the chain-of-thought and knowledge notes produced by the
continuous factor-mining loop.

## Run Notes

- [Iteration 1](factor_mining_loop_iteration_1.md) — First loop run, empty
  seed, promoted a 3-factor ensemble with test Sharpe 1.63 but negative train
  Sharpe.
- [Iteration 2](factor_mining_loop_iteration_2.md) — Seeded with iteration 1
  live library, cleaned 5 expressions, no improvement, retained existing
  library.
- [Iteration 3](factor_mining_loop_iteration_3.md) — First run with promotion
  gates. Cleaned 6 expressions, positive train Sharpe, but failed max
  correlation gate due to semantic duplicates.
- [Iteration 4](factor_mining_loop_iteration_4.md) — Added semantic
  deduplication. All gates passed; promoted a 6-factor ensemble with test
  Sharpe **2.11** and cost-adj return **30.25%**.
- [Iteration 5](factor_mining_loop_iteration_5.md) — Seeded with iteration 4
  library. Promoted a 7-factor ensemble with test Sharpe **2.20** and
  cost-adj return **30.76%**; independently verified on Tushare data.
- [Iteration 6](factor_mining_loop_iteration_6.md) — Seeded with iteration 5
  library. Did not promote; strong train Sharpe (1.65) but test Sharpe fell to
  1.10 and max-correlation gate failed. Includes live-library audit.
- [Iteration 7](factor_mining_loop_iteration_7.md) — Empty-seed exploration
  with strict coverage (0.90) and correlation (0.50) gates. Over-cleaned to
  2 factors; failed train-Sharpe and min-count gates. Recommended returning
  to live-library seeding for iteration 8.

## Design & Infrastructure

- [Project LOOP.md](../LOOP.md) — Loop design, stages, triggers, safety gates.
- [State file](../china_a_share_alpha_output/factor_mining_loop/STATE.md) —
  Latest loop state and best result.
- [Source code](../china_a_share_alpha/scripts/run_factor_mining_loop.py) —
  Loop runner implementation.

## General Evolution Notes

- [SEMAS Evolution Ideas](semas_evolution_ideas.md) — Broader evolution
  experiments including validation weighting, iterative evolution, and the
  factor-mining loop.

## Related pages

- [Wiki index](index.md)
- [Wiki log](log.md)
