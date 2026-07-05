---
date: 2026-07-05
tags: [factor-mining-loop, run-note, iteration-6]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/loop_report_20260705_081736.md
  - ../china_a_share_alpha_output/factor_mining_loop/live_library_audit.md
related:
  - factor_mining_loop_iteration_5.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 6 Chain-of-Thought

## Trigger

Run the next iteration after fixing NaN handling in semantic deduplication, and
perform a coverage / sector-neutrality audit of the current live library.

## Setup

- Seed 1006, pop 25, gen 8.
- Seeded with iteration 5 live library.
- Tushare token: `d5386a1783719a1c704837dfd8b2de9c7490dcb5194b89940834dbbd`
- Semantic dedup with unique column names and degenerate-series handling.

## Iteration 6 observations

- **Merge**: 25 unique expressions.
- **Clean**: 16 expressions survived.
- **Dedup**: 14 distinct expressions after semantic dedup.
  - Dropped `factor_26` (max |corr| = 1.000).
  - Dropped `factor_10` and `high_zscore_20` (max |corr| = 0.989).
- **Gates**:
  - train_sharpe_positive: ✅ (1.6546)
  - min_cleaned_count: ✅ (14 distinct factors)
  - max_corr_ok: ❌ (max corr = 0.9376)
- **Metrics**:
  - Train Sharpe: 1.6546
  - Train cost-adj return: 29.09%
  - Test Sharpe: 1.0963
  - Test cost-adj return: 9.50%

## Decision

- **Did not promote.** The new library had excellent in-sample metrics but
  failed the max-correlation gate and produced a much lower test Sharpe than
  the current best. The existing 7-factor live library is retained.

## New knowledge

1. **Strong in-sample performance can hide out-of-sample degradation.**
   Iteration 6 had the best train Sharpe so far (1.65) but test Sharpe dropped
   to 1.10.
2. **The correlation gate is useful as an overfit early-warning.** A max
   correlation of 0.94 among selected factors suggests the ensemble collapsed
   onto a few common signals.
3. **Seeding with a very strong live library may cause over-optimization.**
   Future iterations may benefit from an occasional exploration seed with no
   seed library and a larger mutation radius.

## Live-library audit

Ran an independent audit on real Tushare data for the retained live library:

| Metric | Value |
|---|---|
| Factors | 7 |
| Combined mean daily coverage | 1.000 |
| Combined min daily coverage | 1.000 |
| Mean pre-neutralization sector spread | 0.373 |
| Max pre-neutralization sector spread | 1.148 |
| Dates with sector spread > 0.5 | 121 |

### Coverage findings

- `factor_12` (`sign(ts_shift(ts_ema(ts_pct_change(grossprofit_margin, 20), 5), 60))`)
  has mean coverage 0.74 and min coverage 0.00, indicating intermittent
  fundamental data.
- Other fundamental factors (`eps`, `ocfps`, `debt_to_assets`) have mean
  coverage ~0.95 but occasional min coverage of 0.00.
- Combined signal coverage is 1.00 because missing values are filled by other
  factors.

### Sector-neutrality findings

- The synthetic sector labels show meaningful pre-neutralization spread on 121
  days (max spread 1.15).
- The combination script sector-neutralizes the signal, but the raw ensemble is
  not sector-agnostic.

## Chain-of-thought for next iteration

- Consider running iteration 7 with an **empty seed library** and a larger
  population/generation budget to inject exploration.
- Alternatively, keep seeding but tighten the max-correlation gate further
  (e.g., 0.60) to avoid overfit ensembles.
- Before production use, review whether intermittent fundamental coverage is
  acceptable or whether the live library should be restricted to
  price/volume-based factors.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/live_library_audit.md`]
- [source: `wiki/factor_mining_loop_iteration_5.md`]
