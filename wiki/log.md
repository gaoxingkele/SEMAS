# SEMAS Wiki Log

Chronological record of wiki updates, loop runs, and key decisions.

---

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
