---
date: 2026-07-13
tags: [factor_mining, promotion_gate, frozen_data, audit, state]
sources:
  - china_a_share_alpha/scripts/run_frozen_promotion_audit.py
  - china_a_share_alpha/scripts/run_factor_mining_loop.py
  - china_a_share_alpha_output/factor_mining_loop/state.json
related:
  - factor_mining_loop_hold_sharpe_gate.md
  - factor_mining_loop_multihizon_batch_audit.md
  - factor_mining_loop_index.md
---

# Frozen Promotion Audit and State Reconciliation

## Result

The 5d, 10d, and 20d live libraries passed one checksum-verified frozen-data
audit [source: local frozen audit receipt]. The audit did not promote or replace
any library.

| Library | Evaluation contract | Sharpe | Annualized return | Max DD |
|---|---|---:|---:|---:|
| 5d live | dynamic trim, 5d, 10 bps | 2.4843 | 50.76% | -8.09% |
| 10d live | dynamic trim, 10d, 10 bps | 3.8514 | 84.38% | -10.97% |
| 20d live | simple hold, 20d, 10 bps | 1.3067 | 20.74% | -13.91% |

Snapshot ID:
`242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011`.
The test fold contains 203,432 rows, 354 symbols, and dates from 2024-01-02
through 2026-05-29 [source: local snapshot manifest].

## Contract Changes

- Candidate and live baseline now use the same evaluation mode, horizon,
  transaction cost, smoothing, factor-coverage threshold, and in-memory panel.
- Hold Sharpe is the promotion metric when the hold gate is enabled. The
  overlapping daily-rebalanced metrics remain diagnostic only.
- Empty or insufficient evaluations produce an invalid receipt instead of a
  numerical zero.
- Equal-weight signals require at least 50% factor availability per row instead
  of a complete-case intersection across every factor.
- Duplicate factor labels receive unique internal identities.

These rules are implemented in
`china_a_share_alpha/scripts/run_factor_mining_loop.py` and
`china_a_share_alpha/scripts/run_multihizon_audit.py` [source: local code].

## Dynamic Trim Correction

The previous implementation applied 40/60/80 percentile boundaries, repeatedly
multiplied an already-trimmed weight, and could retain an expired short after it
entered the long top-20% set. The corrected implementation uses target weights
for the intended 20/40/60 boundaries and only lets qualifying long positions
continue [source: local code]. Therefore, the earlier 2.85 and 3.02 dynamic-trim
Sharpe values are historical diagnostics and are not comparable to this audit.

## Task Decomposition

- Normalize evaluator identity and invalid-result handling.
- Repair state history and promotion baselines.
- Freeze train/validation/test panels with SHA-256 receipts.
- Audit all horizon-specific live libraries without mutation.
- Reconcile state only after library-hash and iteration checks pass.

## Agent Engineering

| Role | Input | Output | Failure boundary |
|---|---|---|---|
| Snapshot builder | data config and cache | Parquet panels and manifest | no manifest if loading or hashing fails |
| Promotion evaluator | library, frozen test panel, contract | validity-aware metric receipt | invalid receipt, never zero fallback |
| Snapshot verifier | manifest and panel files | checksum verification | blocks audit on mismatch |
| State reconciler | verified receipt and current state | updated baseline | blocks on library hash or iteration drift |

## Workflow Orchestration

The topology is sequential: freeze -> verify -> evaluate by logical horizon ->
merge receipts -> human-readable report -> guarded reconciliation. The audit
step is read-only. Reconciliation is separately invoked and uses an atomic
temporary-file replacement [source: local implementation].

## Selection Plan

- Metric: contract-specific hold Sharpe with 10 bps one-way cost.
- Absolute gate: Sharpe >= 1.0.
- Coverage gate: at least half of evaluated factors available per row.
- Rollback: retain the existing live library; no audit command performs
  promotion.
- Human gate: review the receipt before production use.

## Related pages

- [Hold-Sharpe Promotion Gate](factor_mining_loop_hold_sharpe_gate.md)
- [Batch Multi-Horizon Audit](factor_mining_loop_multihizon_batch_audit.md)
- [Factor Mining Loop Index](factor_mining_loop_index.md)

## Superseded Execution Comparison

The 2026-07-14 20d schedule review found that this audit's hold backtester
applied signal-day positions to signal-day returns. Its reported hold metrics
remain historical state-reconciliation evidence but are invalid for comparing
execution schedules. The replacement optimizer applies day `d` positions only
from day `d+1` and selected the static 20d schedule [source: local
`position_schedule_evolution_20d_recovery_20260714` receipt].

The same correction was subsequently applied to all horizons. The 2026-07-16
audit supersedes this page's 5d/10d/20d hold figures and selects 5d dynamic trim,
10d static hold, and 20d research-only [source: local
`no_lookahead_horizon_audit_20260716` receipt].
