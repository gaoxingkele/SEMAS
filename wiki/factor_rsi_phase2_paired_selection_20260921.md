---
date: 2026-09-21
tags: [factor-mining, recursive-self-improvement, paired-evaluation, selection]
related: [factor_rsi_phase1_causal_verifier_20260920.md]
---

# RSI Phase 2: Paired Multi-Seed Policy Selection

## Problem

Explicit identity and single-field mutations make one result attributable, but
one seed can still make a neutral or harmful mutation look beneficial. Policy
selection therefore needs matched parent/child replications before a child may
reproduce.

[source: arXiv:2505.22954]
[source: wiki/think/rsi_causal_credit_assignment_20260920.md]

## Evaluation contract

For each deterministic seed, parent and child:

1. start from the same checksum-frozen pre-child factor library;
2. use the same data snapshot, evaluator, and random seed;
3. run in separate state/output directories with promotion disabled;
4. pass train, cleaned-count, correlation, hold-validity, and minimum-hold gates;
5. contribute a within-seed `child_hold_sharpe - parent_hold_sharpe` delta.

The child is selected only if all requested pairs are valid, at least three
pairs exist, mean and median deltas are positive, the win rate is at least 2/3,
and the worst delta is no lower than -0.10.

[source: china_a_share_alpha/loop/paired_policy_evaluation.py]
[source: china_a_share_alpha/scripts/run_paired_policy_evaluation.py]

## State transition

`proposed -> evaluated_valid_pair_pending -> evaluated_valid_pair_selected`

A rejected pair transitions to `paired_rejected`, loses parent eligibility,
and receives zero archive fitness. Pair-pending nodes block the next proposal,
so the outer loop cannot evade replication by moving on to another child.

[source: china_a_share_alpha/loop/recursive_self_improve.py]

## Cost control and recovery

The campaign reuses a completed production child run only when policy identity
and seed match. Every isolated arm is resumable from its own state receipt, so
an interrupted campaign reruns only missing arms. The frozen input checksum
prevents a live-library promotion from silently changing later pairs.
