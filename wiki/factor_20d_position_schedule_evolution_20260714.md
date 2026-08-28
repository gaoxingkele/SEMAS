---
date: 2026-07-14
tags: [factor-mining, 20d, position-sizing, evolution, frozen-audit]
sources:
  - local frozen snapshot 242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011
  - local position_schedule_evolution_20d_recovery_20260714 receipt
related:
  - factor_promotion_frozen_audit_20260713.md
  - think/rank_decile_schedule_regime_failure.md
---

# 20d Position-Schedule Evolution

## Result

The robust winner is the identity schedule: all ten rank-decile multipliers
remain at 1.0. No dynamic add/reduce schedule passed the frozen audit fold
[source: local `position_schedule_evolution_20d_recovery_20260714` receipt].

| Fold | Sharpe | Annualized return | Max DD |
|---|---:|---:|---:|
| Development, 2021-06 to 2023-12 | 0.4165 | 4.73% | -14.75% |
| Audit, 2024-2025 | 0.2367 | 2.13% | -15.05% |
| Final isolation, 2026-01 to 2026-05 | 1.7582 | 23.10% | -3.86% |

The first search selected `[1.0, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3,
0.3]` on 2021-2023 but failed the 2024-2026 blind fold with Sharpe -0.5719,
versus 0.3643 for static. The recovery run reassigned 2024-2025 as audit and
kept 2026 isolated. Static then won before the final fold was opened.

## Contract

- Ten cross-sectional percentile bins; multiplier increments of 0.1.
- Monotone multipliers from stronger to weaker current rank, bounded 0.0-1.5.
- Top-20% long cohort refreshed every 20 trading days; short book fixed.
- Positions formed at day `d` earn returns from day `d+1`.
- Charge 10 bps one-way on actual target-weight changes.
- Freeze factors, data, horizon, cohort selection, and short-book behavior.

## Task Decomposition

- Prepare checksum-verified temporal folds and factor signals.
- Search quantized schedules over multiple seeds.
- Select only on the audit fold, with static and legacy baselines included.
- Open the final isolation fold once and emit an immutable receipt.
- Promote only if a dynamic schedule clears improvement and drawdown gates.

## Agent Engineering

| Role | Input | Output | Failure boundary |
|---|---|---|---|
| Genome generator | bounds and seed | monotone schedule | rejects off-grid schedules |
| Backtest verifier | schedule and fold | costed metrics | blocks same-day return use |
| Audit selector | finalists and baselines | one pre-final winner | static rollback is valid |
| Final verifier | selected winner only | final receipt | cannot change selection |

## Workflow Orchestration

The workflow is development search -> audit selection -> final verification ->
promotion verdict. The failed first run triggered one recovery cycle that
changed temporal role assignment rather than tuning against opened final
metrics [source: local evolution configs and receipts].

## Selection Plan

- Primary metric: audit Sharpe after 10 bps costs.
- Dynamic promotion gate: final Sharpe improvement at least 0.10 versus static.
- Risk gate: maximum drawdown may not degrade by more than 0.02.
- Rollback: select static 100% multipliers.
- Human gate: no live configuration or library mutation by the optimizer.

## Related pages

- [Frozen Promotion Audit](factor_promotion_frozen_audit_20260713.md)
- [Rank-Decile Schedule Regime Failure](think/rank_decile_schedule_regime_failure.md)
- [Factor Mining Loop Index](factor_mining_loop_index.md)
