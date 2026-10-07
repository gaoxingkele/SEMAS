---
date: 2026-09-17
tags: [ablation, stage2, dag, factor-mining]
related: [factor_ablation_a2_ast_20260917.md, factor_ccf_a_three_direction_paper_20260904.md]
---

# Stage-2 Ablation A3 — DAG Neighborhood Off

Single-seed ablation: `parent_mode: global` instead of `dag_neighbors`.

[source: AlphaPROBE] [source: ara_alpha_evolution/logic/experiments.md]

## Setup

| Item | Value |
|---|---|
| Config | `factor_mining_loop_config_ablate_dag.yaml` |
| Evolution | `factor_mining_loop_evolution_config_ablate_dag.yaml` |
| Output | `factor_mining_loop_ablate_dag/` |
| Seed | 3001 |
| Diff vs B0 | `parent_mode: global` |

## Result (2026-09-17)

| Run | Hold Sharpe | Pool IC | Verdict |
|---|---:|---:|---|
| B0 live (iter 49, DAG on) | **2.0560** | 0.0149 | baseline |
| A3 (DAG off / global parents) | **1.927** | 0.0090 | worse (−0.129) |

## Interpretation

On this seed, removing DAG neighborhood search produced a **weaker** hold
Sharpe and lower pool IC. Directionally supports D3, but still single-seed —
replicate before paper claims.
