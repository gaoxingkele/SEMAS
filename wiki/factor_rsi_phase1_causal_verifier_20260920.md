---
date: 2026-09-20
tags: [factor-mining, recursive-self-improvement, verification, causal-credit]
related: [factor_dgm_rsi_anti_collapse_islands_20260920.md]
---

# RSI Phase 1: Feasible Parents and Causal Receipts

## Claim

Raw hold Sharpe is not archive fitness unless the candidate also passes the
frozen feasibility contract. A self-improving search needs evidence that a
specific child configuration produced a specific valid result before that
child is allowed to reproduce.

[source: arXiv:2505.22954]
[source: wiki/factor_dgm_rsi_anti_collapse_islands_20260920.md]

## Contract

1. The archive separates `proposed`, `evaluated_valid`, and
   `evaluated_invalid` states.
2. Only `eligible_parent=True` nodes enter parent sampling or best-node
   selection.
3. Verification requires explicit policy identity, finite hold Sharpe, frozen
   examiner fields, and all required gates.
4. Parent diagnosis uses that parent's own compact execution receipt, not the
   globally latest iteration.
5. A child changes exactly one functional policy field, preserving causal
   interpretability.
6. Proposal and execution receipts preserve policy ID, parent ID, mutation,
   seed, evaluation group, and configuration hashes.

[source: china_a_share_alpha/loop/recursive_self_improve.py]
[source: china_a_share_alpha/scripts/run_factor_mining_loop.py]

## Migration result

The version-1 archive was backed up and audited against iterations 50--105.
The version-2 archive contains one bootstrap node, 27 valid evaluated nodes,
29 invalid evaluated nodes, and one pending proposal. Twenty-eight nodes may
reproduce. The raw-score leader `policy_0027` is invalid because
`max_corr_ok=False`; the best eligible node is `policy_0056`, with hold Sharpe
2.3129639059.

## Boundary

Phase 1 establishes identity and hard-gate integrity. It does not yet estimate
mutation effects across multiple paired seeds. That should be the next
selection layer before policy promotion becomes statistically confident.
