# LOOP.md — Continuous Factor Mining Loop

This file defines the self-improving loop that mines new China A-share alpha
factors. It follows the loop-engineering pattern: durable state, scheduled or
manual triggers, sub-process evolution, verification, and a human gate before
committing a new genome.

## Goal

Continuously discover, evaluate, and promote cross-sectional alpha factors
without manual intervention in the search phase. Human review remains the final
gate before a new factor library is committed to the repository.

## Trigger

- **Manual**: `python -m china_a_share_alpha.scripts.run_factor_mining_loop china_a_share_alpha/examples/factor_mining_loop_config.yaml`
- **Scheduled**: GitHub Actions cron or local task scheduler (recommended daily
  or weekly after market close).

## Loop Stages

```text
STATE (state.json + live_library.csv)
    │
    ▼
EVOLVE  ── run one seed of enhanced_factor_loop, seeded with live library
    │
    ▼
MERGE   ── merge new leaderboard with live library
    │
    ▼
CLEAN   ── validation-aware cleaning (density, sign agreement, Sharpe)
    │
    ▼
COMBINE ── equal-weight + EMA of top-N cleaned factors + high_zscore_20
    │
    ▼
DECIDE  ── compare candidate and live baseline under one hold contract
    │
    ▼
REPORT  ── write loop_report_*.md; update STATE.md
```

## State

- `china_a_share_alpha_output/factor_mining_loop/state.json`
- `china_a_share_alpha_output/factor_mining_loop/live_library.csv`
- `china_a_share_alpha_output/factor_mining_loop/STATE.md`

The live library is the durable memory across iterations. Each iteration seeds
from it, so good structures persist and are refined.

The promotion contract is explicit per horizon: 5d uses dynamic trim, 10d uses
simple hold, and 20d is retained for research rather than promotion. Candidate
and live baseline are evaluated
on the same in-memory test panel, with the same horizon, costs, smoothing, and
factor-coverage threshold. Daily-rebalanced Sharpe and return remain diagnostic
metrics and no longer decide promotion when the hold gate is enabled.

## Human Gates

1. **Review live_library.csv** before committing.
2. **Inspect the loop report** for overfit or degenerate factors.
3. **Update OPERATION_LOG.md** with the iteration results.
4. **Do not auto-merge** without human approval.

## Safety

- No git mutations inside the loop.
- Promotion threshold requires a clear out-of-sample improvement.
- Invalid or empty evaluations are recorded as failures, never as a zero score.
- Frozen audits verify panel and library hashes before state reconciliation.
- Execution backtests apply positions formed on day `d` only to returns from
  day `d+1`; same-day signal/return evaluation is invalid for promotion.
- Factor expressions and smoothing use continuous past history before the test
  fold, while scoring remains restricted to test dates.
- All horizon hold comparisons use top/bottom 20% cohorts and charge actual
  target-weight changes.
- Each iteration runs in its own `iter_NNNN/` directory for auditability.

## Files

- `china_a_share_alpha/scripts/run_factor_mining_loop.py` — loop runner.
- `china_a_share_alpha/examples/factor_mining_loop_config.yaml` — loop config.
- `china_a_share_alpha/examples/factor_mining_loop_evolution_config.yaml` —
  evolution sub-config.

## Evolution

See `wiki/semas_evolution_ideas.md` for absorbed ideas and references.
