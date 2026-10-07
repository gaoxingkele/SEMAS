---
date: 2026-09-04
tags: [factor-mining, paper, kdd, ara, alphagen, alphaagent, alphaprobe]
related: [factor_mining_loop_index.md, semas_evolution_ideas.md, references.md]
---

# CCF-A Paper Track — Three-Direction Alpha Evolution

We opened an Agent-Native Research Artifact at
`ara_alpha_evolution/` to prepare a **KDD (CCF-A)** paper that jointly tries
three literature-inspired directions inside the existing SEMAS A-share loop.

[source: ara_alpha_evolution/PAPER.md]

## Directions

1. **D1 Synergy** — AlphaGen-style combination / pool objective for promotion.
2. **D2 Regularize** — AlphaAgent-style AST originality + complexity gates.
3. **D3 Navigate** — AlphaPROBE-style DAG neighborhood search from live library.

## Baselines cloned (local `external/`, gitignored)

| Repo | Rev |
|---|---|
| ICT-FinD-Lab/alphagen | 259687e |
| RndmVariableQ/AlphaAgent | b42cb39 |
| gta0804/AlphaPROBE | 872299d |
| QuantaAlpha/QuantaAlpha | b7ceb27 |

[source: ara_alpha_evolution/evidence/baselines/external_repos.txt]

## Literature kickoff

`paper_search` (2022–2026) surfaced AlphaGen, AlphaAgent, QuantFactor REINFORCE,
AlphaForge, Chain-of-Alpha, Alpha Jungle MCTS (AAAI 2026), QuantaAlpha, etc.
Semantic Scholar hit 429 intermittently; arXiv/OpenAlex carried the scan.

[source: ara_alpha_evolution/evidence/lit_search/paper_search_20260904.txt]

## Tentative novelty

Joint **triad + execution-faithful hold contract** is the publishable delta.
Re-implementing any single prior alone is likely scooped (Level ≤2).

## Tooling

Routed via `C:\aicoding\mylib` skills: paper-writing, paper_search,
experiment-design, venue rankings (KDD=CCF-A), plus Codex `ara-paper`.

## Stage-1 status (2026-09-09)

Modules landed and unit-tested:

- D2 `china_a_share_alpha/evolution/ast_regularizer.py`
- D1 `china_a_share_alpha/loop/synergy_objective.py`
- D3 `china_a_share_alpha/evolution/dag_neighborhood.py`

Live-library smoke: AST filter 12→11 factors; frozen test pool IC ≈ 0.0171.

**Iter 49 (2026-09-11)** with D1/D2/D3 enabled: hold Sharpe **2.0560**
(+0.212 vs iter 48), pool IC 0.0149, AST post-dedup 13→12, promoted.
Next: Stage-2 leave-one-out ablations before claiming component credit.
