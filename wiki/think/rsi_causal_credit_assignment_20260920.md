---
date: 2026-09-20
tags: [thinking, rsi, causal-credit, evolution]
related: [../factor_rsi_phase1_causal_verifier_20260920.md]
---

# Causal credit comes before broader RSI search

The archive previously mixed two concepts: a large observed hold Sharpe and a
valid candidate. This let a policy that failed `max_corr_ok` look like the best
stepping stone. The repair is to treat feasibility as a type boundary, not as a
soft penalty: invalid evidence remains observable but cannot reproduce.

[source: arXiv:2505.22954]

Diagnosing the globally latest run also breaks ancestry. A sampled parent must
be mutated in response to its own receipt; otherwise the child combines one
policy's genome with another policy's failure explanation. Explicit identity
and receipt binding restore that causal edge.

[source: china_a_share_alpha/loop/recursive_self_improve.py]

Finally, changing one functional field per child is not merely conservative.
It makes archive transitions interpretable enough to learn which search
surface helped. Multi-field recipes can return later as named macro-mutations,
but only after single-field evidence provides a baseline interaction model.

The next methodological step is paired replicated evaluation: parent and child
should share several deterministic seeds, with selection based on the
distribution of paired deltas rather than a single lucky run. Phase 1 records
the group and seed needed for that extension but does not claim to implement
the replication layer.
