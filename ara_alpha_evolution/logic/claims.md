# Claims

Each claim must be testable on frozen snapshots with fixed contracts.
Provenance tags: `user` | `ai-suggested` | `ai-executed`.

## C1 — Synergy objective beats single-factor IC promotion (D1)

**Claim**: Promoting factor libraries by improvement in **ensemble hold-Sharpe (or pool IC)** under a fixed no-lookahead contract yields higher out-of-sample hold-Sharpe than promoting by single-factor / daily-reb Sharpe thresholds alone.
**Falsify if**: On the same frozen CSI300 panel and cost schedule, synergy promotion does not improve hold-Sharpe by ≥ 0.05 over the iter-48 baseline contract after matched compute.
**Evidence plan**: E1 (ablation promotion objective).
**Provenance**: ai-suggested from AlphaGen; user requested try.

## C2 — AST originality + complexity gates reduce decay (D2)

**Claim**: Rejecting mutations with AST subtree similarity above τ or depth/nodes above caps improves rolling IC stability and reduces post-promotion decay slope vs correlation-only dedup.
**Falsify if**: Decay slope (test-year IC drift) does not improve while hold-Sharpe is no worse.
**Evidence plan**: E2 (regularizer ablation).
**Provenance**: ai-suggested from AlphaAgent.

## C3 — DAG-neighborhood search improves sample efficiency (D3)

**Claim**: Restricting GP/LLM mutation parents to Bayesian- or fitness-retrieved neighbors of live-library DAG nodes finds equal-or-better hold-Sharpe libraries with fewer evaluated candidates than global GP.
**Falsify if**: At matched candidate budget, neighborhood search underperforms global GP on hold-Sharpe.
**Evidence plan**: E3 (search-mode comparison).
**Provenance**: ai-suggested from AlphaPROBE.

## C4 — Joint system dominates any single direction

**Claim**: Enabling D1+D2+D3 together outperforms any singleton and the current production loop on hold-Sharpe and at least one transfer universe (CSI500 or unused-stock panel).
**Falsify if**: Best singleton ≥ joint system on both primary metrics.
**Evidence plan**: E4 (full factorial / leave-one-out).
**Provenance**: user requested all three; ai-suggested joint claim.

## C5 — Execution contract is necessary for honest ranking

**Claim**: Ranking libraries by same-day / overlapping daily-reb Sharpe disagrees with no-lookahead hold ranking; using the former as the promotion gate selects worse libraries under the latter.
**Falsify if**: Rank correlation between the two metrics exceeds 0.9 and selected libraries coincide.
**Evidence plan**: E0 already partially supported by 2026-07-16 no-lookahead audit (iter 26 vs iter 40 divergence).
**Provenance**: ai-executed prior work in this repo.
