# Thinking-Process Log

Chronological record of methodological insights, failed hypotheses, and
absorbed ideas.

---

## [2026-07-07] Established `wiki/think/`

- Created independent thinking-process wiki.
- Defined schema, index, log, references, and paper queue.
- Wrote initial atomic notes covering factor-mining methodology evolution.

## [2026-07-07] Multi-horizon evaluation insight

- Realized that daily-rebalance vs overlapping H-day forward returns inflates
  Sharpe and is not comparable across horizons.
- Adopted realistic non-overlapping hold backtests for 5d/10d/20d evaluation.

## [2026-07-07] 20d library promotion

- The 20d-evolved library that passed realistic hold gates contained only 2
  factors, one of which was a manual seed (`high_zscore_20`).
- This raises the hypothesis that short-horizon seeds can bootstrap
  longer-horizon ensembles if the target return is stable.


## [2026-07-07] Thinking-process wiki formalized

- `AGENTS.md` updated to require automatic extraction of valuable thinking
  after each interaction and extraction of core value from papers/articles.
- Added `paper_ideas_queue.md` and `references.md` to track external sources.

## [2026-07-07] Factor export for external algorithms

- Exported 16 unique factor expressions and 3 combined signals to
  `china_a_share_alpha_output/factor_exports/`.
- Documented caveats: in-sample selection, lookahead risk, transaction costs,
  regime change, and the experimental status of the 10d library.

## [2026-07-07] Submitted factor library to external repo

- Cloned `https://github.com/gaoxingkele/Stock_benchmark` to a temporary
  directory outside the SEMAS repo.
- Created `factors/` with 16 expressions, standalone evaluator, parser,
  README, and config.
- Committed and pushed as a one-time contribution; local SEMAS repo unchanged.

## [2026-07-07] Pushed full SEMAS project to remote

- Commit `2ac47d4` pushed to https://github.com/gaoxingkele/SEMAS.git.
- Included 91 files: code, configs, wiki/think, and key live libraries.
- Local SEMAS repo now in sync with remote.

## [2026-07-08] TA-Lib + Alpha101 integration and 10-iteration evolution

- Added 15 TA-Lib indicators as raw variables.
- Added Alpha101 (alpha_001, alpha_003, alpha_101) as seed expressions.
- Started 10 iterations of 5d evolution in background.

## [2026-07-08] TA-Lib/Alpha101 10-iteration results

- 10 iterations completed; new live library promoted at iter 28.
- Loop best: test Sharpe 5.93 / cost-adj return 245.7%.
- Real 5d hold: Sharpe 2.37 / return 69.5% / max DD -17.0%.
- Previous 5d hold: Sharpe 1.82 / return 41.9%.
- Key new raw variables used: rsi_14, adx_14, macd, ts_delta(rsi_14,20).
- Caveat: loop metrics inflated by overlapping returns; hold audit is the production benchmark.

## [2026-07-08] Cost robustness and second 10-iteration run

- Hold audit at 20bps: 5d Sharpe 1.94 / return 53.2%.
- Hold audit at 30bps: 5d Sharpe 1.50 / return 38.4%.
- Alpha remains positive even at 60bps round-trip.
- Started next 10 iterations (iter_0032–iter_0041) in background.

## [2026-07-09] Iter 32-41: loop metrics up, hold Sharpe down

- Iter 37 promoted: loop Sharpe 6.34.
- Iter 40 promoted: loop Sharpe 5.72 but higher cost-adj return.
- Current live library (iter40) real 5d hold: Sharpe 1.64 / return 39.4% / DD -18.0%.
- Best hold-Sharpe remains iter28: 5d hold Sharpe 2.37 / return 69.6% / DD -17.0%.
- Lesson: loop-level return threshold can overfit to overlapping forward returns.

## [2026-07-13] Mingli book profiles and hour calibration

- Separated book-method votes from public-event fit scoring and retained ambiguity for narrow candidate-hour margins.

## [2026-07-13] metric identity and frozen evaluator contract

- A hold metric is comparable only when strategy, horizon, costs, coverage, and data hash match.
- Invalid evaluation is missing evidence, not a zero score.
- Persist structured promotion baselines and verify state before reconciliation.

## [2026-07-14] rank-decile schedule regime failure

- A 20d dynamic schedule won development but reversed on the later audit regime.
- Retained the identity schedule and prohibited selection after opening final data.
- Next research must use a new state variable and a new holdout.

## [2026-07-14] MA correlation is exposure, not quality

- The 20d ensemble has stable MA exposure, mostly from `high_zscore_20`.
- Treat MA correlation as a redundancy/style diagnostic, not predictive proof.
- Test incremental quality through MA-neutralized IC or conditional returns.

## [2026-07-14] statistical residual alpha versus execution

- MA-neutralized IC and Q5-Q1 spreads remain positive across all folds.
- Fixed 20d cohort Sharpe does not improve consistently across folds.
- Preserve the distinction between independent information and tradable policy.

## [2026-07-16] horizon value requires execution stability

- 5d remains positive across folds and test years under no-lookahead execution.
- 10d has value but reverses in train IC and 2024 execution.
- 20d remains research-only; historical warm-up is now evaluator identity.

## [2026-07-16] stock selection export preserves execution state

- Dynamic picks require rebalance cohort, current multiplier, and explicit exits.
- Static 10d picks remain the rebalance cohort rather than today's top ranks.
- A name union does not authorize unaudited cross-strategy capital weights.

## [2026-09-20] RSI causal credit assignment

- Feasibility is now a parent-eligibility boundary rather than a soft score.
- Parent diagnosis is bound to the sampled parent's own receipt.
- One-field mutation makes policy effects interpretable; paired multi-seed
  evaluation is the next layer, not a completed capability.

## [2026-09-21] paired evidence before RSI reproduction

- Matching parent and child on deterministic seeds reduces search-noise
  confounding without changing the evaluator.
- Single-run validity authenticates evidence; paired validity grants
  reproductive eligibility.
- Borderline mutations should receive more matched seeds, not softer gates.

## [2026-10-08] reconciled factor evolution across state and Git layers

- Treated machine state, runtime receipts, research notes, and Git refs as
  independent evidence branches before synthesis.
- Distinguished 114 outer iterations, at least 796 recoverable internal
  generations, and 119 audited expressions.
- Preserved production live state separately from paired reproductive
  eligibility and made the final ledger mechanically verifiable.
- Recorded an idempotent daemon-recovery rule: inspect commits, refs, index,
  and every worktree before retrying a mutation or push.
