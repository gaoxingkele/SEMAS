---
date: 2026-07-07
tags: [factor-mining, export, external-algorithms, production]
sources:
  - ../china_a_share_alpha/scripts/export_factor_values.py
  - ../china_a_share_alpha_output/factor_exports/factor_metadata.json
related:
  - methodology_evolution_factor_mining.md
  - multi_horizon_design.md
---

# Factor Export for External Algorithms

## Question

Can the discovered factors be used directly for stock selection, and can they
be fed into other quantitative algorithms?

## Answer

Yes, but with caveats.

### What can be exported

Each factor expression can be evaluated on the full panel to produce a
z-scored cross-sectional signal per symbol per date. These signals can be:

- Ranked directly to produce long/short portfolios.
- Used as features in supervised learning models (linear, tree, neural net).
- Fed into portfolio optimizers as expected-return inputs.
- Converted to alpha weights and combined with risk models.

### Export format

A script (`export_factor_values.py`) writes:

- `factor_values.csv` — flat table with `symbol`, `date`, and one column per
  factor plus combined signals.
- `factor_values.parquet` — same data, binary/typed, MultiIndex `(symbol, date)`.
- `factor_metadata.json` — expressions, labels, date range, combined signal
  names.

### Caveats before production use

1. **In-sample vs out-of-sample**: The 5d and 20d libraries were selected on
   the test fold (2024-01-01 to 2026-05-25). Any Sharpe reported is
   historical; future performance is not guaranteed.
2. **Look-ahead / data leakage**: The expressions use only point-in-time
   variables, but external users must ensure their own data pipeline does not
   introduce future information.
3. **Transaction costs and capacity**: The 5d library has very low turnover,
   but real-world slippage, market impact, and borrow costs can erode returns.
4. **Regime change**: CSI300 constituents and market structure can shift.
   Continuous monitoring and retraining are necessary.
5. **10d library is temporary**: It came from a single 10d evolution run and
   was not promoted through realistic hold backtests; treat it as experimental.

### Recommended external workflow

1. Load `factor_values.parquet`.
2. Use the three `combined_*` columns as base alphas.
3. Add risk-model constraints (beta, sector, size neutrality).
4. Run walk-forward backtests with realistic costs before live trading.
5. Reserve a true hold-out period that was never used during factor discovery.

## Decision

Exported the 16 unique factor expressions plus 3 combined signals to
`china_a_share_alpha_output/factor_exports/`. External use is encouraged for
research, but production deployment requires additional validation.
