---
date: 2026-09-18
tags: [rsi, recursive-self-improvement, dgm, hyperagents, factor-mining]
related: [factor_rsi_means_recursive_self_improvement_20260918.md]
---

# DGM-style RSI for A-Share Factor Mining

True **RSI = Recursive Self-Improvement**. The outer loop evolves the
**mining-policy genome**; the inner loop evolves factor expressions.

[source: arXiv:2505.22954 Darwin Gödel Machine]
[source: arXiv:2603.19461 HyperAgents / DGM-H]
[source: arXiv:2410.04444 Gödel Agent]
[source: SEMAS_SELF_UPGRADE_DESIGN.md]

## Mapping

| DGM / HyperAgents | This system |
|---|---|
| Coding agent codebase | `MiningPolicyGenome` (dedup τ, AST, DAG, pop/gens, diversity slots, …) |
| SWE-bench empirical eval | One `run_factor_mining_loop` iter → hold Sharpe |
| Archive of agents | `dgm_rsi/archive.json` |
| Parent sampling | fitness × 1/(1+n_children) |
| Self-modification | `mutate_policy` from failure codes + open-ended explore ops |

## Rollback (2026-09-18)

Relative Strength Index work reverted. Live = iter 49, hold **2.0560**.

## First DGM child after rollback

- Parent: `policy_0000` (baseline fitness 2.056)
- Child: `policy_0001` — relax dedup to 0.97, `keep_diversity_slots=2`, ε=0.2
- Inner eval: iter 50 under `dgm_rsi/active/loop_config.yaml`
