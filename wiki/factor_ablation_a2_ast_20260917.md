---
date: 2026-09-17
tags: [ablation, stage2, ast, factor-mining]
related: [factor_ccf_a_three_direction_paper_20260904.md, factor_rsi_modern_seeds_20260917.md]
---

# Stage-2 Ablation A2 — AST Regularizer Off

Single-seed matched-compute ablation against production B0 (iter 49 live,
hold Sharpe **2.0560** under 5d dynamic-trim / 10bps).

[source: ara_alpha_evolution/logic/experiments.md]
[source: AlphaAgent arXiv:2502.16789]

## Setup

| Item | Value |
|---|---|
| Config | `factor_mining_loop_config_ablate_ast.yaml` |
| Output | `factor_mining_loop_ablate_ast/` (promotion_enabled: false) |
| Seed | 2001 |
| Extra seeds | RSI modern library |
| Diff vs B0 | `ast_regularizer_enabled: false` only |

## Result (2026-09-17)

| Run | Hold Sharpe | Pool IC | Notes |
|---|---:|---:|---|
| B0 live (iter 49) | **2.0560** | 0.0149 | AST on |
| A2 (no AST) | **2.0560** | 0.0149 | KEPT / no promote |
| Iter 51 (AST on + RSI mutator) | 2.055 | 0.0149 | KEPT |

A2 candidate matched baseline hold to three decimals. One RSI hybrid
survived cleaning: `div(less(vwap, if_positive(ts_min(rsi_14, 20), ...)))`.

## Interpretation

On this single seed, disabling AST did **not** improve or degrade hold Sharpe.
Need multi-seed (and A3 DAG ablation) before claiming AST contribution.
Do not treat A2 as evidence against AST gates.
