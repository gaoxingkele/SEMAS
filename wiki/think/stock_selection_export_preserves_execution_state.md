---
date: 2026-07-16
tags: [thinking-process, stock-selection, execution-state, auditability]
sources:
  - local audited_stock_selection_20260529 receipt
related:
  - ../factor_audited_stock_selection_20260529.md
---

# Stock Selection Export Preserves Execution State

A complete selection list is not just the latest factor ranking. A dynamic
strategy must preserve the rebalance cohort, current rank, multiplier, and exit
state; otherwise an exporter silently changes the strategy into daily
rebalancing.

The 5d export therefore retains one originally selected stock with an `EXIT_0`
action, while the positive-current file omits it [source: local stock-selection
receipt]. The 10d export preserves its older static cohort even when current
ranks have moved.

Combining 5d and 10d names does not determine combined capital weights. The
union is an attribution artifact until allocation weights pass their own
development/validation audit.

## Related pages

- [Audited Stock Selection](../factor_audited_stock_selection_20260529.md)
- [Horizon Value Requires Execution Stability](horizon_value_requires_execution_stability.md)
