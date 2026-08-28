---
date: 2026-07-16
tags: [factor-mining, stock-selection, 5d, 10d, frozen-export]
sources:
  - local frozen snapshot 242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011
  - local audited_stock_selection_20260529 receipt
related:
  - factor_horizon_no_lookahead_audit_20260716.md
---

# Audited 5d / 10d Stock Selection

The complete stock cohorts were exported as of 2026-05-29 from the verified
frozen snapshot. This is a reproducible historical selection, not a real-time
July list [source: local stock-selection receipt].

## Counts

| Component | Rebalance date | Long cohort | Positive current longs | Shorts |
|---|---|---:|---:|---:|
| 5d dynamic | 2026-05-25 | 70 | 69 | 70 |
| 10d static | 2026-05-18 | 70 | 70 | 70 |

The current positive long union has 108 names: 31 `CORE_5D_10D`, 38
`PRIMARY_5D`, and 39 `SECONDARY_10D`. The 5d complete cohort contains 53 full,
15 70%-multiplier, one 50%-multiplier, and one exited position [source: local
CSV exports].

## Contract

- Compute both library signals on continuous historical data with EMA10.
- Select top/bottom 20% on each horizon's frozen rebalance anchor.
- Apply current rank-decile multipliers only to the 5d long cohort.
- Keep the 10d cohort static until its next rebalance.
- Export component weights but do not infer a combined capital allocation.
- Omit cached names because their encoding is damaged; preserve exact symbols.

## Artifacts

- `combined_long_all.csv`: all 108 positive long names and source buckets.
- `5d_long_complete.csv`: all 70 rebalance names, including the exited name.
- `5d_long_current.csv`: 69 positive 5d long positions.
- `10d_long_current.csv`: all 70 static 10d long positions.
- `5d_short_current.csv` and `10d_short_current.csv`: fixed short cohorts.
- `stock_selection_complete.md`: human-readable complete long lists.

## Related pages

- [No-Lookahead Horizon Audit](factor_horizon_no_lookahead_audit_20260716.md)
- [Factor Mining Loop Index](factor_mining_loop_index.md)
