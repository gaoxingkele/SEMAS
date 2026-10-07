# Experiments

Progressive plan following `mylib/skills/experiment-design` (AI-Scientist-v2 4-stage).
Primary venue bar: **KDD** — need multi-seed, ablation, ≥2 universes, cost robustness.

## Shared evaluation contract (frozen)

- Snapshot: `china_a_share_alpha_output/tushare_snapshot_20260717` (checksum `242f762f...`)
- Promotion / report metric: 5d dynamic-trim hold Sharpe, 10 bps, EMA10, 50% coverage, T+1 returns
- Diagnostic only: daily-reb Sharpe / IC
- Seeds: ≥3 for final tables; 1 seed OK for Stage 1 smoke
- Compute budget: matched candidate evaluations per method

## Stage 1 — Initial implementation (smoke)

**Goals**
- D1: promotion decision uses ensemble hold delta vs baseline (already largely true; harden API)
- D2: AST similarity + depth/node filters in `enhanced_factor_mutator`
- D3: parent sampling from live-library expression DAG neighbors

**Dataset**: frozen CSI300 snapshot only
**Completion**: each of D1/D2/D3 runs one iteration without crash; writes metrics JSON under `evidence/runs/`

## Stage 2 — Baseline tuning

**Baselines**
- B0: current loop (iter 48 config) — production control
- B1: AlphaGen-style pool-IC reward (adapter or reimplementation on our DSL)
- B2: AlphaAgent mining path (AST gates on / off)
- B3: AlphaPROBE-style retrieval (if runnable) else our D3-only

**Tune** (architecture fixed): population size, generations, τ_AST, max_depth, neighbor_k, promote_hold_threshold
**Datasets**: CSI300 frozen; secondary quick check CSI500 config if cache allows
**Completion**: stable curves; B0 reproducible within ±0.02 hold Sharpe

## Stage 3 — Creative research

1. Joint D1+D2+D3 vs leave-one-out
2. Cross-universe transfer (CSI300 → CSI500 / unused-stock panel)
3. Cost stress 10/20/30 bps
4. Decay slopes across 2024/2025/2026 test years
5. Optional LLM mutator under same AST gates (fair vs AlphaAgent)

**Completion**: at least one setting where joint system beats B0 on hold Sharpe **and** transfer

## Stage 4 — Ablations

| Ablation | Removes |
|---|---|
| A1 | D1 synergy objective → revert to diagnostic Sharpe promote |
| A2 | D2 AST/complexity gates → correlation dedup only |
| A3 | D3 DAG neighbors → global GP seed |
| A4 | No-lookahead hold → same-day signal return (sanity / C5) |

## Metrics

| Metric | Primary? |
|---|---|
| Hold Sharpe (5d dynamic trim) | Yes |
| Hold max DD / cost-adj return | Yes |
| Pool IC / RankIC | Secondary |
| Rolling IC slope (decay) | Yes for C2 |
| Candidates evaluated to target | Yes for C3 |
| Pairwise AST / Spearman diversity | Reporting |

## Experiment IDs (to fill)

| ID | Claim | Status |
|---|---|---|
| E0 | C5 | partial (2026-07-16 audit) |
| E1 | C1 | pending |
| E2 | C2 | pending |
| E3 | C3 | pending |
| E4 | C4 | pending |
