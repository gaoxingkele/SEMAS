---
date: 2026-07-16
tags: [factor-mining, 5d, 10d, 20d, no-lookahead, horizon-decay]
sources:
  - local frozen snapshot 242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011
  - local no_lookahead_horizon_audit_20260716 receipt
related:
  - factor_promotion_frozen_audit_20260713.md
  - think/horizon_value_requires_execution_stability.md
---

# No-Lookahead 5d / 10d / 20d Audit

## Decision

| Horizon | Execution selected on validation | Validation Sharpe | Test Sharpe | Verdict |
|---|---|---:|---:|---|
| 5d | fixed dynamic trim | 0.7669 | 1.6337 | primary |
| 10d | static hold | 0.1662 | 0.9906 | secondary, regime-sensitive |
| 20d | fixed dynamic trim | -0.1146 | -0.0697 | research-only |

The 5d strategy is positive in train, validation, test, and each test calendar
year. The 10d strategy is positive in aggregate validation/test but has negative
train IC and a slightly negative 2024 return. The 20d selected execution is
negative in both validation and test [source: local audit receipt].

## Test IC Horizon Curve

| Library | 1d | 5d | 10d | 20d |
|---|---:|---:|---:|---:|
| 5d | 0.0091 | 0.0243 | 0.0287 | 0.0243 |
| 10d | 0.0008 | 0.0149 | 0.0230 | 0.0163 |
| 20d | -0.0012 | 0.0053 | 0.0070 | 0.0057 |

The 5d library carries the strongest and broadest signal. The 10d library peaks
at its native horizon and decays by 20d. The 20d library is weak across every
forward horizon [source: local `ic_decay.csv`].

## Task Decomposition

- Verify snapshot and all three library hashes.
- Build each ensemble on continuous historical data.
- Compare static and fixed trim on train/validation without test selection.
- Open test for the validation-selected mode and split results by year.
- Cross-check production promotion entry points against the audit result.

## Agent Engineering

| Role | Input | Output | Failure boundary |
|---|---|---|---|
| Signal builder | library and continuous panel | coverage-aware EMA10 signal | invalid on insufficient factors |
| Horizon evaluator | signal and frozen fold | IC, layers, static/trim metrics | blocks same-day return use |
| Validation selector | two predefined schedules | one execution mode | cannot inspect test metrics |
| Production verifier | promotion API and history panel | independent metric receipt | blocks on mismatch |

## Workflow Orchestration

The topology is verify -> continuous signal build -> train/validation branches
-> validation selection -> test and annual audit -> independent production API
recalculation. A mismatch in the first production recalculation exposed missing
historical warm-up; the recovery loop fixed the shared evaluator and repeated
the cross-check until metrics matched exactly [source: local implementation and
execution receipts].

## Selection Plan

- Primary evidence: native IC, Q5-Q1 spread, costed hold Sharpe, annual signs.
- Schedule selection: validation Sharpe only.
- Cost control: 10 bps on actual target changes.
- Stability downgrade: any train or test-year sign reversal prevents a robust label.
- Rollback: preserve all libraries; change only horizon priority and evaluator contract.

## Related pages

- [Frozen Promotion Audit](factor_promotion_frozen_audit_20260713.md)
- [20d MA-Neutralized Alpha](factor_20d_ma_neutralized_alpha_20260714.md)
- [Horizon Value Requires Execution Stability](think/horizon_value_requires_execution_stability.md)
