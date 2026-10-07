# Problem

## Research problem

Formulaic alpha mining for equities is stuck between three failure modes:

1. **Wrong objective**: Genetic programming and many LLM miners maximize single-factor IC or overlapping daily-rebalanced Sharpe. Real deployment uses **multi-factor ensembles** under **holding periods, costs, and next-day execution**. Optimizing the former systematically overfits the latter. [source: AlphaGen KDD 2023; Novy-Marx & Velikov 2016]

2. **Under-regularized search**: Unconstrained GP/LLM search produces deep, isomorphic, or crowded expressions that look strong in-sample then decay. Homogenization and p-hacking accelerate alpha decay. [source: AlphaAgent KDD 2025; Harvey, Liu & Zhu 2016]

3. **Structure-blind exploration**: Population search treats the expression space as an unstructured bag. After a live library exists, most useful mutations are **local edits of successful subtrees**, not global random restarts. [source: AlphaPROBE DAG navigation]

## Bottleneck diagnosis (this project)

Our SEMAS China A-share loop (`china_a_share_alpha`) already has:
- continuous seed → evolve → clean → combine → promote
- hold-Sharpe gate with dynamic trim (iter 48: hold Sharpe 1.8444)
- frozen snapshot evaluation

Remaining bottleneck for a CCF-A paper: the **search and promotion objectives are still only partially aligned** with synergistic combination (D1), structural anti-decay regularization is mostly post-hoc correlation dedup (D2 incomplete), and evolution is still largely global GP seeded by the library rather than principled on-graph navigation (D3 missing).

## Desired output

A method + system that jointly:

- mines factors **for the ensemble under an execution contract**;
- rejects mutations that are AST-near-duplicates or over-complex;
- explores preferentially in the DAG neighborhood of promoted factors;
- reports multi-seed, multi-universe, cost-robust results suitable for KDD.

## Falsification stance

If ablating D1/D2/D3 does **not** improve hold-Sharpe / decay slope / cross-universe transfer relative to the current loop baseline on frozen panels, the unified claim fails and we report negative results.
