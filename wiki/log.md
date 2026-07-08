# SEMAS Wiki Log

Chronological record of wiki updates, loop runs, and key decisions.

---

## [2026-07-07] loop run | Iteration 22

- Added configurable `forward_period` to Tushare loader.
- Ran 5 iterations of 20d forward evolution.
- Iteration 3 promoted to `live_library_20d.csv`.
- 20d hold Sharpe: 1.98, cost-adj: 60.78%.
- Added `wiki/factor_mining_loop_iteration_22.md`.

## [2026-07-06] multi-horizon audit

- Ran 5d / 10d / 20d horizon audit on the live library.
- Ensemble test IC improved with horizon: 0.038 → 0.045 → 0.053.
- Realistic hold backtest Sharpe: 1.79 (5d), 1.58 (10d), 1.63 (20d).
- Added `wiki/factor_mining_loop_multihizon_audit.md`.

## [2026-07-06] loop run | Iteration 21 (final audit)

- Ran final production audit on the iteration-12 live library.
- Cost robustness confirmed at 10/20/30 bps.
- Per-year test Sharpe: 2.13 (2024), 2.83 (2025), 3.75 (2026).
- Sector neutrality and coverage confirmed.
- Added `wiki/factor_mining_loop_iteration_21.md`.

## [2026-07-06] loop run | Iteration 20

- Ran cost-aware evolution with 20 bps transaction cost.
- Seeded with iteration-12 live library.
- Merged 28 expressions, cleaned to 13, deduped to 12.
- Did not promote; live library retained.
- Test Sharpe: 2.2126, cost-adj: 25.76%.
- Added `wiki/factor_mining_loop_iteration_20.md`.

## [2026-07-06] loop run | Iteration 19

- Added anti-correlation factor search.
- Generated 50 candidates scored by IC minus correlation penalty.
- Top 10 merged with live library produced high turnover and poor train Sharpe.
- Did not promote.
- Test Sharpe: 1.1437, cost-adj: 10.19%.
- Added `wiki/factor_mining_loop_iteration_19.md`.

## [2026-07-06] loop run | Iteration 18

- Updated LLM mutator prompt with full DSL and money-flow variables.
- Generated 20 LLM-proposed factors seeded from the live library.
- Merged with live library and combined; failed hard gates.
- Did not promote.
- Test Sharpe: 2.3081, cost-adj: 22.61%.
- Added `wiki/factor_mining_loop_iteration_18.md`.

## [2026-07-06] loop run | Iteration 17

- Added `run_regime_combination.py` for volatility-regime switching.
- Tested high/low volatility factor selection on the live library.
- Did not improve over equal weight.
- Test Sharpe: 2.7629, cost-adj: 32.47%.
- Added `wiki/factor_mining_loop_iteration_17.md`.

## [2026-07-06] loop run | Iteration 16

- Compared five ensemble weight methods on the live library.
- Equal weight and risk parity tied for best; ridge overfit badly.
- Did not promote; equal-weight iteration-12 library retained.
- Test Sharpe: 2.7629, cost-adj: 32.47%.
- Added `wiki/factor_mining_loop_iteration_16.md`.

## [2026-07-06] loop run | Iteration 15

- Added money-flow buy/sell amount fields to the Tushare loader.
- Added `extra_seed_libraries` support to the loop runner.
- Seeded evolution with iteration-12 live library + 8 money-flow expressions
  (seed 1030).
- Merged 25 expressions, cleaned to 15, deduped to 15.
- Did not promote; current library retained.
- Test Sharpe: 2.0207, cost-adj: 16.99%.
- Added `wiki/factor_mining_loop_iteration_15.md`.

## [2026-07-06] loop run | Iteration 14

- Added high-order time-series operators: `ts_skew`, `ts_kurt`, `ts_autocorr`,
  `ts_entropy`.
- Seeded evolution with iteration-12 live library (forward_period=5, pop 30,
  gen 8, seed 1028).
- Merged 26 expressions, cleaned to 15, deduped to 12.
- Did not promote; current library retained.
- Test Sharpe: 2.4074, cost-adj: 28.48%.
- Added `wiki/factor_mining_loop_iteration_14.md`.

## [2026-07-05] loop run | Iteration 13

- Cross-market transfer: evolved on CSI500 and CSI1000, evaluated on CSI300.
- Did not promote; current library retained.
- CSI300 test Sharpe: 1.8354, cost-adj: 14.73%.
- Added `wiki/factor_mining_loop_iteration_13.md`.

## [2026-07-05] loop run | Iteration 12

- Multi-horizon evolution: parallel 5d and 10d forward-return runs.
- Merged 46 unique expressions, cleaned to 21, selected 10 with greedy corr filter.
- Promoted new live library.
- Train Sharpe: 1.3620, test Sharpe: 2.7629, cost-adj: 32.47%.
- Added `wiki/factor_mining_loop_iteration_12.md`.

## [2026-07-05] loop run | Iteration 11 (validation)

- Stress-tested current live library at 20 bps transaction cost.
- Test Sharpe: 2.7031, test cost-adj return: 23.17%.
- Stress test passed; library remains cost-robust.
- Added `wiki/factor_mining_loop_iteration_11.md`.

## [2026-07-05] audit | Iteration 10 live-library audit

- Audited the promoted 12-factor live library on real Tushare data.
- Combined coverage: 1.00; most factors have mean coverage > 0.90.
- Pre-neutralization sector spread > 0.5 on only 9 days.
- Top-decile long turnover estimate: 0.56.
- Added `wiki/factor_mining_loop_audit_iter10.md`.

## [2026-07-05] loop run | Iteration 10

- Seed 1010, pop 50, gen 12, live seed.
- Added greedy correlation-aware selection (`--max-pairwise-corr 0.40`).
- Promoted new live library.
- Train Sharpe: 1.6861, test Sharpe: 2.7031, cost-adj: 31.46%.
- Max selection correlation: 0.3744 (passed gate).
- Independently verified on real Tushare data.
- Added `wiki/factor_mining_loop_iteration_10.md`.

## [2026-07-05] loop run | Iteration 9

- Seed 1009, pop 50, gen 12, live seed.
- Tightened semantic dedup to 0.80, top_n=7, risk-parity weights.
- Did not promote; existing library retained.
- Train Sharpe: 1.2923, test Sharpe: 0.4955, cost-adj: -4.60%.
- Failed max-correlation gate (max corr 0.7427).
- Added `wiki/factor_mining_loop_iteration_9.md`.

## [2026-07-05] loop run | Iteration 8

- Seed 1008, pop 50, gen 12, live seed.
- Did not promote; existing library retained.
- Train Sharpe: 1.3452, test Sharpe: 2.3964, cost-adj: 28.42%.
- Failed max-correlation gate (max corr 0.9204).
- Added `wiki/factor_mining_loop_iteration_8.md`.

## [2026-07-05] loop run | Iteration 7

- Seed 1007, pop 40, gen 10, empty seed.
- Did not promote; existing library retained.
- Train Sharpe: -0.0696, test Sharpe: 1.2424, cost-adj: 10.91%.
- Failed train-Sharpe and min-cleaned-count gates.
- Added `wiki/factor_mining_loop_iteration_7.md`.
- Recommended iteration 8: live-seed, pop 50/gen 12, coverage 0.50, corr gate 0.50.

## [2026-07-05] audit | Live-library coverage and sector neutrality

- Audited the 7-factor live library on real Tushare data.
- Combined signal coverage is 1.00, but several fundamental factors have
  intermittent coverage.
- Pre-neutralization sector spread is meaningful on 121 days.
- See `china_a_share_alpha_output/factor_mining_loop/live_library_audit.md`.

## [2026-07-05] loop run | Iteration 6

- Seed 1006, pop 25, gen 8.
- Did not promote; existing library retained.
- Train Sharpe: 1.6546, test Sharpe: 1.0963, max corr: 0.9376.
- Added `wiki/factor_mining_loop_iteration_6.md`.

## [2026-07-04] ingest | Karpathy LLM Wiki gist

- Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Action: Adopted the gist's three-layer architecture (raw sources / wiki /
  schema) for the SEMAS project wiki.
- Created `wiki/index.md` and `wiki/log.md`.
- Added YAML frontmatter and cross-references to factor-mining-loop run notes.

## [2026-07-04] loop run | Iteration 5

- Seed 1005, pop 25, gen 8.
- Promoted a 7-factor live library.
- Test Sharpe: 2.2034, cost-adj return: 30.76%.
- Independently verified on real Tushare data.
- Added `wiki/factor_mining_loop_iteration_5.md`.

## [2026-07-04] loop run | Iteration 4

- Added semantic deduplication to the loop runner.
- Promoted a 6-factor live library.
- Test Sharpe: 2.1145, cost-adj return: 30.25%.
- Added `wiki/factor_mining_loop_iteration_4.md`.

## [2026-07-04] loop run | Iteration 3

- First run with promotion gates.
- Positive train Sharpe but failed max-correlation gate.
- Added `wiki/factor_mining_loop_iteration_3.md`.

## [2026-07-04] loop run | Iteration 2

- Seeded with iteration 1 live library.
- No improvement; retained existing library.
- Added `wiki/factor_mining_loop_iteration_2.md`.

## [2026-07-04] loop run | Iteration 1

- First continuous factor-mining loop run.
- Promoted a 3-factor live library.
- Test Sharpe: 1.6283, cost-adj return: 24.75%.
- Added `wiki/factor_mining_loop_iteration_1.md`.
