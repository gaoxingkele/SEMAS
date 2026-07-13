---
date: 2026-07-07
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
- [Iteration 8](factor_mining_loop_iteration_8.md) — Live-seed with larger
  budget (pop 50/gen 12). Test Sharpe 2.40 but max-correlation gate failed
  (0.92); retained iteration 5 library.
- [Iteration 9](factor_mining_loop_iteration_9.md) — Tightened dedup (0.80),
  top-7 selection, risk-parity weights. Test Sharpe 0.50, cost-adj -4.6%,
  max-corr gate failed (0.74); retained iteration 5 library.
- [Iteration 10](factor_mining_loop_iteration_10.md) — Added greedy
  correlation-aware selection (`max_pairwise_corr=0.40`). Promoted a 12-factor
  ensemble with test Sharpe **2.70** and cost-adj **31.46%**; independently
  verified on Tushare data.
- [Iteration 11](factor_mining_loop_iteration_11.md) — Validation iteration:
  stress-tested the promoted live library at 20 bps transaction cost. Test
  Sharpe 2.70, cost-adj 23.17%; passed.
- [Iteration 12](factor_mining_loop_iteration_12.md) — Multi-horizon evolution
  (5d + 10d forward returns). Promoted 10-factor ensemble with test Sharpe
  **2.76** and cost-adj **32.47%**.
- [Iteration 13](factor_mining_loop_iteration_13.md) — Cross-market transfer
  (CSI500/CSI1000 → CSI300). Did not improve; retained iteration 12 library.
- [Iteration 14](factor_mining_loop_iteration_14.md) — Added high-order
  time-series operators (`ts_skew`, `ts_kurt`, `ts_autocorr`, `ts_entropy`).
  Did not improve; retained iteration 12 library.
- [Iteration 15](factor_mining_loop_iteration_15.md) — Added money-flow
  buy/sell amount fields and seed library. Did not improve; retained iteration
  12 library.
- [Iteration 16](factor_mining_loop_iteration_16.md) — Compared ensemble
  weight methods (equal, IC, Sharpe, risk-parity, ridge). Equal weight remained
  best.
- [Iteration 17](factor_mining_loop_iteration_17.md) — Added volatility-regime
  switching combination. Did not improve; retained iteration 12 library.
- [Iteration 18](factor_mining_loop_iteration_18.md) — LLM critic guided factor
  generation. Did not improve; retained iteration 12 library.
- [Iteration 19](factor_mining_loop_iteration_19.md) — Anti-correlation factor
  search. Did not improve; retained iteration 12 library.
- [Iteration 20](factor_mining_loop_iteration_20.md) — Cost-aware evolution at
  20 bps. Did not improve; retained iteration 12 library.
- [Iteration 21](factor_mining_loop_iteration_21.md) — Final production audit
  of the iteration-12 live library.
- [Iteration 22](factor_mining_loop_iteration_22.md) — 20-day forward horizon
  evolution. Promoted `live_library_20d.csv` with 20d hold Sharpe **1.98** and
  cost-adj **60.78%**.

## Audits

- [Iteration 10 live-library audit](factor_mining_loop_audit_iter10.md) —
  Coverage and sector-neutrality analysis of the promoted 12-factor ensemble.
- [Iteration 21 final audit](factor_mining_loop_iteration_21.md) —
  Cost robustness, per-year performance, coverage, and sector neutrality of the
  final live library.
- [Batch multi-horizon audit](factor_mining_loop_multihizon_batch_audit.md) —
  5d / 10d / 20d evaluation of all 47 evolved iteration libraries.  Found that
  iter_26 has the best realistic 5d hold Sharpe (2.49).

## Design & Infrastructure

- [Hold-Sharpe promotion gate](factor_mining_loop_hold_sharpe_gate.md) —
  Added realistic non-overlapping hold-Sharpe gate to the loop runner to prevent
  overfitting to loop-level overlapping metrics.

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
