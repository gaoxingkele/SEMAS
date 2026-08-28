---
date: 2026-07-16
tags: [thinking-process, horizon-decay, execution-stability, no-lookahead]
sources:
  - local no_lookahead_horizon_audit_20260716 receipt
related:
  - ../factor_horizon_no_lookahead_audit_20260716.md
---

# Horizon Value Requires Execution Stability

Native-horizon IC alone does not determine the preferred trading horizon. The
5d and 10d libraries both have positive validation/test evidence, but only 5d
keeps positive execution results across every available test year [source:
local no-lookahead horizon receipt].

Historical warm-up is part of evaluator identity. Evaluating rolling factors
only inside the test partition produced different Sharpe values even though the
test returns were unchanged. The correct contract computes signals from all
past data and restricts only scoring to test dates.

The 10d horizon remains useful as a secondary diversifier, not a peer of 5d.
The 20d library retains statistical research value but its execution selection
fails validation and test. This separates signal horizon from production
priority without deleting potentially useful research artifacts.

## Related pages

- [No-Lookahead Horizon Audit](../factor_horizon_no_lookahead_audit_20260716.md)
- [Statistical Residual Alpha vs Execution](statistical_residual_alpha_vs_execution.md)
