# Solution Constraints

Hard constraints for implementable method variants. Do not relax for paper tables without documenting.

## Data & leakage

- Train / val / test folds from frozen snapshot only for paper tables.
- Factor expressions may warm up on continuous history **before** test dates; scores only on test dates.
- Positions formed on day `d` apply to returns from day `d+1` only.

## Promotion (D1)

- Candidate and live baseline evaluated on the **same in-memory panel**.
- Gate: hold Sharpe improvement ≥ `promote_hold_sharpe_threshold` (default 0.03) and absolute hold Sharpe ≥ 1.0.
- Daily-reb Sharpe never decides promotion when hold gate enabled.
- Optional secondary objective: pool IC of equal-weight / EMA ensemble (AlphaGen-style).

## Mutation regularizers (D2)

- Reject if AST subtree similarity to any live-library expression > τ (default start 0.85; tune in Stage 2).
- Reject if expression depth > `max_depth` or node count > `max_nodes`.
- Keep existing Spearman semantic dedup as a second filter, not a replacement.

## Search (D3)

- Maintain a DAG of expressions where edges are subtree / operator-edit relations.
- Parent selection: sample k neighbors of high-fitness live nodes (Bayesian or softmax by hold contribution).
- Global GP exploration budget ≤ ε of candidates (diversity insurance).

## Reporting

- Every promoted library writes: library hash, snapshot id, contract YAML, seed, candidate count.
- Invalid evaluations are failures, never zero scores.
