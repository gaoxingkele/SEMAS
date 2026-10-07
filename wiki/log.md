# SEMAS Wiki Log

Chronological record of wiki updates, loop runs, and key decisions.

---

## [2026-07-11] implemented recommendations

- Restored 5d live library to `iter_26` (realistic 5d hold Sharpe 2.49).
- Added hold-Sharpe promotion gate to `run_factor_mining_loop.py`.
- Enabled hold-Sharpe gate for 5d/10d/20d loops.
- Fixed read-only NumPy array bug in `run_factor_combination.py`.
- Fixed `factor/expression.py` to handle `None`/object-dtype/missing columns and
  prevent 20d evolution crashes.
- Created 10d loop `state.json` and started 5 more iterations.
- Relaxed 10d loop `min_train_sharpe_gate` to -2.0 and `min_cleaned_gate` to 3
  so hold-Sharpe gate dominates promotion decisions.
- Promoted 20d `iter_0005` to live library (20d hold Sharpe 1.51) and started
  3 more iterations.
- Added `wiki/factor_mining_loop_hold_sharpe_gate.md`.

## [2026-07-11] batch multi-horizon audit

- Audited all 47 evolved iteration libraries across 5d / 10d / 20d horizons.
- 5d loop best realistic 5d hold Sharpe: iter_26 (2.49, return 73.70%, DD -11.96%).
- Current `live_library.csv` (iter 40) 5d hold Sharpe: 1.63 — worse than iter_26/28.
- 10d loop has only 1 iteration; 20d loop has 5 iterations but all failed
  train-Sharpe gate.
- Added `wiki/factor_mining_loop_multihizon_batch_audit.md` and
  `china_a_share_alpha/scripts/batch_multihizon_audit.py`.

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

## [2026-07-11] 10d/20d evolution scope reduction

- Root cause: 10d/20d evolution was not hanging, just very slow
  (~30-40 min/iteration with population_size=30, max_generations=8).
- Reduced 10d and 20d evolution configs to population_size=15, max_generations=5,
  patience=2 to bring iteration time to ~10-15 minutes.
- Restarted 20d loop iter_0006 with reduced scope.

## [2026-07-11] 10d/20d loops resumed and stable

- 10d loop ran iter_0004–0006; iter_0004 promoted with 10d hold Sharpe 2.782.
- 20d loop ran iter_0006–0008; retained iter_0005 live library (20d hold Sharpe 1.512).
- Confirmed hold-Sharpe gate works for promotion decisions.

## [2026-07-11] expanded 20d evolution search

- Increased 20d population_size to 25, max_generations to 8, leaderboard_size to 50.
- Lowered 20d min_cleaned_gate to 2.
- Started 3 extended 20d iterations (iter_0009–0011).

## [2026-07-12] adjusted 20d scope to moderate budget

- Expanded 25/8 config too slow; reverted to population_size=18, max_generations=6.
- Started 2 iterations (iter_0009–0010).

## [2026-07-12] expanded 20d search results

- Ran iter_0009–0010 with population_size=18, max_generations=6.
- Best hold Sharpe: iter_0009 = 1.511 (just below existing best 1.512).
- iter_0010 hold Sharpe = 1.001.
- Existing 20d live library (iter_0005) remains best.

## [2026-07-12] expanded factor grammar

- Added ts_median, ts_percentile_90/10, ts_decay_linear, ts_min_max_scale.
- Added cs_percentile, cs_demean, cs_winsorize.
- Increased max depth to 5, max nodes to 40.
- Updated expression.py, factor_mutator.py, enhanced_factor_mutator.py.

## [2026-07-12] restarted 5d/10d/20d loops with expanded grammar

- Fixed cs_zscore/cs_rank regression from grammar expansion.
- Restarted 5d iter_0043–0044, 10d iter_0007–0008, 20d iter_0011–0012 in parallel.

## [2026-07-12] final extended evolution results

- 5d iter_0043–0044 did not beat iter_26 (2.491).
- 10d iter_0007 matched best 2.782 but did not improve; iter_0008 timed out.
- 20d iter_0011–0012 with expanded grammar did not beat iter_5 (1.512).
- Current libraries appear near local optima.

## [2026-07-12] dynamic trim hold strategy analysis

- Proposed by user: trim long positions mid-cycle based on rank deterioration.
- Tested on 5d/10d/20d live libraries.
- 5d: Sharpe 2.49 -> 2.85, DD -11.96% -> -8.84%.
- 10d: Sharpe 2.78 -> 3.02, DD -9.28% -> -8.12%.
- 20d: Sharpe 1.51 -> 0.71, DD -7.59% -> -24.91% (harmful).
- Script: `china_a_share_alpha/scripts/backtest_dynamic_hold.py`.

## [2026-07-12] integrated dynamic trim into loop promotion

- Added `_dynamic_trim_backtest` to `run_multihizon_audit.py`.
- `run_factor_mining_loop.py` now supports `use_dynamic_trim_hold` config.
- Enabled for 5d/10d, disabled for 20d.
- Started 5d iter_0045–0046 and 10d iter_0007–0008 with dynamic trim.

## [2026-07-12] fixed log-op crash and restarted loops

- `log` unary op crashed on object-dtype None values; fixed with numeric coercion.
- Fixed run_cmd log-file naming.
- Restarted 5d iter_0045–0046 and 10d iter_0008–0009.

## [2026-07-13] Mingli book profiles and hour calibration

- Added book-level AHP profiles and structured candidate-hour calibration documentation.
- Recorded the evidence boundary: rankings are conditional and narrow margins remain ambiguous.

## [2026-07-13] frozen promotion audit and state reconciliation

- Froze train/validation/test panels with SHA-256 checksums.
- Unified promotion contracts for 5d, 10d, and 20d live libraries.
- Corrected dynamic-trim rank bands and coverage-aware ensemble construction.
- All three live libraries passed the frozen audit; no library was promoted.
- Reconciled state baselines after library-hash and iteration checks passed.
## 2026-07-14 - 20d position-schedule evolution

- Added a no-lookahead, transaction-costed optimizer for ten rank-decile
  position multipliers.
- First dynamic winner failed blind review; recovery selection retained the
  static 100% schedule on the 2024-2025 audit fold.
- Opened the 2026 final fold only after selection and made no live mutation.
## 2026-07-14 - 20d factor / MA correlation audit

- Measured each 20d factor and raw/EMA10 ensembles against normalized MA5,
  MA10, and MA20 signals on the verified frozen snapshot.
- Found stable positive ensemble exposure across all temporal folds, dominated
  by `high_zscore_20`; no factor or live state changed.
## 2026-07-14 - 20d MA-neutralized alpha audit

- Jointly neutralized raw and EMA10 ensembles against MA5/10/20 deviations.
- Compared same-sample 20d IC, five-layer returns, and costed hold performance.
- Found independent ordering information but no robust execution improvement;
  no live state changed.

## 2026-07-16 - unified no-lookahead horizon audit

- Re-audited 5d, 10d, and 20d libraries with next-day returns, top/bottom 20%
  cohorts, real target turnover, and continuous-history signal warm-up.
- Selected 5d dynamic trim as primary, 10d static as regime-sensitive
  secondary, and 20d as research-only.
- Replaced the shared promotion backtester and verified production metrics
  against the independent audit path.

## 2026-07-16 - exported audited 5d/10d stock cohorts

- Exported complete 5d dynamic and 10d static long/short lists as of the frozen
  2026-05-29 date.
- Produced a 108-name positive long union with consensus and component tags.
- Preserved component weights and avoided assigning an unaudited combined weight.

## 2026-08-28 - reconciled factor research state for release

- Reconciled the human-readable state to machine iteration 47.
- Removed generated runtime logs from version control while retaining compact
  state and research receipts.
- Fixed the effective-factor boundary to sufficient observations plus positive
  2025/2026 Sharpe and IC on the stock-disjoint frozen panel.

## 2026-08-31 - audited all canonical libraries under board-aware T+1 exits

- Added D+1 entry, post-buy-day counting, close-confirmed stops, queued locked
  exits, board-specific thresholds, trailing profit, and forced expiry.
- Deduplicated 69 source libraries into 54 expression sets and completed 486
  stock backtests over 5d/10d/20d policies.
- Found 10d strongest overall and invalidated transfer of the iter-48 live
  library's old promotion score to the new execution contract.

## 2026-08-31 - rejected stock-to-factor matching after frozen test

- Evolved 12 generations of 10d library matching using train-only stock,
  industry, market, and global utilities and 2023 validation selection.
- Validation Sharpe rose to 1.722, but the once-opened 2024--2026 test produced
  0.374 Sharpe and -48.55% maximum drawdown.
- The genome assigned only 0.88% to stock-specific utility, and removing the
  five largest contributors made test annualized return negative.
- Classified the candidate as validation overfit; no live factor state changed.

## 2026-09-11 - refocused matching on the 2025--2026 market regime

- Split recent history into 2025 half-years and 2026 subperiods and recomputed
  each window's matching utility from its preceding 504 trading days.
- Ran two additional eight-round campaigns with temporal lower-tail,
  stock-disjoint, drawdown, and return-concentration objectives.
- Diagnosed a sharp 2026 Q1 factor-ranking reversal and failure of ungated
  long-only matching in April--July 2026.
- Selected an MA20 market entry gate on 2025 H2 and 2026 Q1 only; it improved
  the latest all-stock diagnostic to Sharpe 1.027 and -7.13% drawdown.
- Retained the result as research-only because the diagnostic was previously
  observed, data stop at 2026-07-16, and main-board Sharpe remained negative.

## 2026-09-13 - completed the current all-expression audit

- Froze 55 canonical libraries into 119 unique expressions, including all four
  expressions added by iteration 49.
- Completed all 6,426 requested stock rows over three periods, three holding
  horizons, two entry modes, and three stock universes.
- Replaced infinite signal values with missing values and explicitly rejected
  three factor-period combinations with fewer than 20 cross-sectionally active
  days instead of accepting tie-driven portfolios.
- Found 38 unique factors passing at least one strict recent contract; MA20 10d
  all-stock has the broadest coverage with 32 effective factors.
- Recorded 54 unavailable BSE/ETF/index contract receipts; no proxy results were
  fabricated and no live library was promoted.

## 2026-09-13 - calibrated factor scores and ranked maximum horizons

- Completed 42,840 unique score-bucket rows for 119 expressions across two
  recent periods, three horizons, two gates, three universes, and ten buckets.
- Measured positive-trade and target-hit rates, realized and peak returns,
  cohort Sharpe/drawdown, payoff, holding time, and exit-reason distributions.
- Produced 702 comparable maximum-realized-return contracts; 10 days is the
  most frequent best horizon among all-stock contracts.
- Kept maximum favorable excursion separate because the 20-day window wins
  mechanically for nearly every factor and does not represent executable return.

## 2026-09-20 - added the RSI phase-1 causal verifier

- Migrated the DGM policy archive to a hard-gated v2 eligibility contract.
- Bound every new policy to its parent receipt, mutation field, evaluation seed,
  and explicit execution identity.
- Isolated 29 historical gate failures from parent sampling; retained 28
  verified eligible parents and one pending proposal.
- Documented why single-field mutations are required before paired replicated
  evaluation.

## 2026-09-21 - added paired multi-seed RSI selection

- Added isolated, resumable parent/child arms on identical seeds and a frozen
  seed-library checksum.
- Added mean, median, win-rate, worst-regression, validity, and minimum-pair
  selection gates.
- Made single-valid/pair-pending children ineligible and blocking until their
  paired receipt is selected or rejected.

## 2026-10-07 - consolidated factor evolution through iteration 114

- Reconciled the 113 machine-history entries plus iteration-11 stress audit
  into one outer-loop ledger covering iterations 1–114.
- Recorded iteration 109 / `policy_0060` as the current live library at Hold
  Sharpe 2.3256 and documented why iterations 110–114 did not replace it.
- Distinguished 114 outer iterations from at least 796 currently recoverable
  inner-generation records and from the separate TOP-factor counts.
- Captured paired-campaign outcomes for policies 0060, 0062, and 0065 and
  corrected the human state from “paired running” to “paired rejected” for
  policy 0065.
- Added `factor_evolution_complete_history_1_114.md` as the canonical entry for
  LLMs and other coding tools.
