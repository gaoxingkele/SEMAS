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
