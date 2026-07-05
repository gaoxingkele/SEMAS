# SEMAS Wiki Log

Chronological record of wiki updates, loop runs, and key decisions.

---

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
