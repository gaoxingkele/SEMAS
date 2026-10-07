# Contract-Aware Synergistic Alpha Evolution with Structure Regularization

> Working title (CCF-A target: **KDD** ADS / Research track).
> Artifact root: `ara_alpha_evolution/`.
> Status: research kickoff — 2026-09-04.
> Provenance: user request to try three directions + paper prep; AI-executed scaffolding.

## One-sentence claim

A continuous formulaic-alpha mining loop that (i) promotes libraries under a **combination-aware, no-lookahead hold contract**, (ii) mutates under **AST originality and complexity gates**, and (iii) searches in the **DAG neighborhood of the live library**, yields more decay-resistant and execution-faithful factor sets than GP / RL / LLM baselines that optimize single-factor IC alone.

## Contribution axes (three directions)

| ID | Inspiration | Mechanism in this work |
|---|---|---|
| **D1 Synergy** | AlphaGen (KDD 2023) | Optimize / promote by ensemble pool IC & hold Sharpe, not single-factor daily-reb Sharpe |
| **D2 Regularize** | AlphaAgent (KDD 2025) | AST subtree distance vs library + depth/node caps at mutation time |
| **D3 Navigate** | AlphaPROBE (2026) | Treat `live_library` as DAG roots; biased local evolution instead of global random GP |

Cross-cutting systems contribution: frozen-panel, T+1 no-lookahead, cost-aware dynamic-trim promotion already running in `china_a_share_alpha` (iter 48 hold Sharpe 1.8444).

## Target venues (CCF-A)

1. **KDD** — primary (AlphaGen / AlphaAgent precedent in same venue family)
2. **WWW / TKDE** — secondary if framing leans systems + longitudinal A-share study
3. Fallback CCF-B: CIKM / ICDM (only if A-track evidence incomplete)

## Artifact map

| Path | Role |
|---|---|
| `logic/problem.md` | Problem framing & bottleneck |
| `logic/claims.md` | Falsifiable claims |
| `logic/related_work.md` | Prior art + delta |
| `logic/experiments.md` | Stage-1..4 experiment plan |
| `logic/solution/constraints.md` | Method constraints / gates |
| `trace/exploration_tree.yaml` | Research DAG |
| `evidence/` | Lit search, repo pins, future tables |
| `src/environment.md` | Code / data / eval contract |

## Non-claims (boundary)

- Not a production trading recommendation.
- Not claiming AlphaAgent / AlphaGen / AlphaPROBE are reproduced end-to-end yet.
- Hold-Sharpe numbers on frozen CSI300 snapshot are research metrics under a fixed contract.
