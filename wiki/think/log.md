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
