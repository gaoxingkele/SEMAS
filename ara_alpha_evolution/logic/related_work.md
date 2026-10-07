# Related Work & Scoop Axes

Literature scan date: 2026-09-04.
Sources: `paper_search` (arXiv + OpenAlex; Semantic Scholar partially rate-limited) → `evidence/lit_search/paper_search_20260904.txt`.
External code pins: `evidence/baselines/external_repos.txt`.

## Novelty decomposition (scoop-check axes)

| Axis | This work |
|---|---|
| **Problem framing** | Continuous formulaic mining for A-shares with **promotion under execution-faithful hold contracts** |
| **Core mechanism** | Joint **synergy objective (D1) + AST regularizers (D2) + DAG-neighborhood evolution (D3)** inside SEMAS loop |
| **Key insight** | Single-factor IC / daily-reb Sharpe is misaligned with deployable ensemble alpha; structure-aware search + hold promotion closes the loop |
| **Application domain** | China A-share CSI300/500 formulaic factors; frozen Tushare panels |

## Landmark priors

| Paper | Venue | Overlap axes | Delta |
|---|---|---|---|
| AlphaGen — Yu et al. | **KDD 2023** [CCF-A] arXiv:2306.12964 | framing(partial), mechanism(D1), domain | No AST decay gates; no DAG navigation; weak execution-hold contract |
| AlphaAgent — Tang et al. | **KDD 2025** [CCF-A] arXiv:2502.16789 | mechanism(D2), domain(CSI500) | LLM multi-agent focus; not combination-objective continuous promotion with frozen hold gate |
| AlphaPROBE — Guo et al. | preprint 2026 | mechanism(D3) | DAG retrieval+generation; not coupled to hold-Sharpe promotion / cost trim |
| QuantFactor REINFORCE | IEEE TSP 2025 arXiv:2409.05144 | mechanism(RL) | Variance-bounded RL for steady factors; different objective |
| AlphaForge | arXiv:2406.18394 | mechanism(combine) | Dynamic combine; less structure regularization |
| Chain-of-Alpha | arXiv:2508.06312 | LLM mining | Prompt chain; not AST+DAG+hold triad |
| Navigating the Alpha Jungle (MCTS) | AAAI 2026 / arXiv:2505.11122 | LLM+search | MCTS over formulas; different search prior |
| QuantaAlpha | arXiv:2602.07085 | LLM+evolution | Closest systems cousin; need explicit delta vs our hold contract |
| 101 Formulaic Alphas | Kakushadze 2016 arXiv:1601.00991 | domain seeds | Baseline library only |
| Harvey / Novy-Marx | RFS 2016 | evaluation philosophy | Motivate multiple-testing & cost gates |

## Tentative scoop verdict

**Level ~3–4 (partially novel)** if we deliver the **joint triad + execution contract** with strong ablations.
**Level ≤2 (scooped)** if we only re-implement one of AlphaGen / AlphaAgent / AlphaPROBE without a new measurable coupling.

Mandatory scoop hardening next:
1. Full-text deep dive AlphaPROBE & QuantaAlpha & AlphaForge.
2. Confirm no 2025–2026 paper already combines AST gates + pool objective + on-graph evolution under hold contracts.
3. Re-run `scoop_check` after D1 prototype lands.

## Cloned baselines (local)

| Repo | Path | Rev |
|---|---|---|
| AlphaGen | `external/alphagen` | 259687e |
| AlphaAgent | `external/AlphaAgent` | b42cb39 |
| AlphaPROBE | `external/AlphaPROBE` | 872299d |
| QuantaAlpha | `external/QuantaAlpha` | b7ceb27 |

Note: `RndmVariableQ/AlphaAgent` README now describes an A-share FactorZoo stack; mining entrypoints remain (`scripts/factor_mining_agentscope.py`). Treat as the KDD paper code lineage unless upstream diverges further.
