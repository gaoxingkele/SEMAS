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
- [Iterations 3–45 Retrospective](factor_mining_loop_iterations_3_45.md) —
  Promotion chain, the 2026-07-11 same-standard hold-Sharpe audit that
  invalidated the live library, the 10D/20D branches, and the late collapse.

## Design & Infrastructure

- [Project LOOP.md](../LOOP.md) — Loop design, stages, triggers, safety gates.
- Loop state (git-ignored runtime output):
  `china_a_share_alpha_output/factor_mining_loop_10d/state.json` and
  `.../factor_mining_loop_20d/state.json`. The 5D loop's own `state.json`,
  `live_library.csv`, and `STATE.md` no longer exist; see the retrospective's
  Open items.
- [Batch multi-horizon audit findings](../china_a_share_alpha_output/batch_multihizon_audit/FINDINGS.md) —
  the realistic-hold comparison across every stored iteration.
- [TOP 100 factors by test Sharpe](top100_factors_by_sharpe.md) — cross-run
  aggregation of every expression the loop ever produced.
- [Source code](../china_a_share_alpha/scripts/run_factor_mining_loop.py) —
  Loop runner implementation. Note: the runs after iteration 20 used a newer
  runner (state schema v2 with gates and hold backtest) that is not checked in.

## General Evolution Notes

- [SEMAS Evolution Ideas](semas_evolution_ideas.md) — Broader evolution
  experiments including validation weighting, iterative evolution, and the
  factor-mining loop.
