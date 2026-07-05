---
date: 2026-07-05
tags: [factor-mining-loop, audit, coverage, sector-neutrality]
sources:
  - ../china_a_share_alpha_output/factor_mining_loop/live_library_audit_iter10.md
  - ../china_a_share_alpha_output/factor_mining_loop/live_library_audit_iter10.json
related:
  - factor_mining_loop_iteration_10.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Live Library Audit — Iteration 10

## Scope

Audit the 12-factor live library promoted in iteration 10 for coverage and
sector-neutrality on real Tushare data.

## Method

- Load train/val/test CSI300 data via Tushare Pro.
- Evaluate each factor expression and compute daily cross-sectional z-scores.
- Report per-factor mean and minimum daily coverage.
- Build an equal-weight combined signal and compute its daily coverage and
  top-decile long turnover.
- Compute pre-neutralization sector spread using the synthetic sector labels
  already present in the dataset.

## Key findings

| Metric | Value |
|---|---|
| Factors | 12 |
| Combined mean daily coverage | 1.000 |
| Combined min daily coverage | 1.000 |
| Mean pre-neutralization sector spread | 0.296 |
| Max pre-neutralization sector spread | 0.584 |
| Dates with sector spread > 0.5 | 9 |
| Estimated top-decile long turnover | 0.5552 |

### Coverage

- Only `factor_27` has mean coverage below 0.90 (0.737).
- Several factors have min coverage 0.000 on some dates, usually because of
  fundamental-field reporting gaps.
- Because the 12 factors are diversified across data sources, the combined
  signal has full coverage every day.

### Sector neutrality

- Sector spread is moderate: 9 out of ~720 days exceed 0.5.
- The combination script sector-neutralizes the signal, but the raw ensemble is
  not fully sector-agnostic.
- Sector labels are synthetic (deterministic per symbol), so neutralization
  risk is limited but not zero.

## Risks

1. **Fundamental data gaps**: factors touching `eps`, `ocfps`, `debt_to_assets`,
   `grossprofit_margin`, etc. can be NaN on certain dates.
2. **Top-decile turnover 0.5552**: a discrete long book rebalances ~55% per day;
   this is much higher than the loop's full-weight turnover (~0.07 bps) and
   would require careful execution in live trading.
3. **Model risk**: sector labels are synthetic; real industry classification may
   differ.

## Recommendations

1. Add a `min_daily_coverage >= 0.90` gate for *individual* promoted factors if
   the strategy will trade a single-factor sub-book.
2. For the combined book, current 1.00 combined coverage is acceptable.
3. Re-run the audit with real Tushare industry codes if available.
4. Before live trading, stress-test transaction costs at 20 bps (2x current
   assumption) to ensure the strategy remains profitable.

## References

- [source: `china_a_share_alpha/scripts/run_factor_combination.py`]
- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `wiki/factor_mining_loop_iteration_10.md`]
