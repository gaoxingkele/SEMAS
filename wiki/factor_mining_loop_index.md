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
