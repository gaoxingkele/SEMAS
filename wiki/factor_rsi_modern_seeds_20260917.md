---
date: 2026-09-17
tags: [rsi, factor-mining, alpha, stage1]
related: [factor_ccf_a_three_direction_paper_20260904.md]
---

# Modern RSI Methodology Seeds for A-Share Evolution

Introduced a modern RSI-family seed library into the continuous mining loop,
following recent LLM/alpha literature that treats RSI not as a single indicator
but as a **family of level / momentum / reversion / regime transforms**.

[source: arXiv:2409.06289 Automate Strategy Finding with LLM]
[source: arXiv:2502.16789 AlphaAgent — RSI decays as a raw baseline]
[source: china_a_share_alpha/examples/rsi_modern_seed_library.csv]

## Seed families

| Family | Example |
|---|---|
| Level | `cs_rank(rsi_14)`, `cs_zscore(rsi_14)` |
| Reversion | `cs_rank(sub(100, rsi_14))`, overbought/oversold band |
| Momentum | `cs_rank(ts_delta(rsi_14, 14))`, `ts_delta(..., 5)` |
| Relative | `rsi - ts_mean(rsi, 20)`, `ts_zscore(rsi, 20)`, `ts_rank(rsi, 60)` |
| Signed vol | `sign(delta) * ts_std(rsi, 20)` |

## Frozen-panel baseline (2026-09-17)

Under the same 5d dynamic-trim / 10bps / no-lookahead contract:

| Library | n | Pool IC | Hold Sharpe | Ann. return | Max DD |
|---|---:|---:|---:|---:|---:|
| RSI seeds only | 10 | 0.0071 | **0.1317** | 0.74% | -24.60% |
| Live iter 49 | 12 | 0.0176 | **2.0560** | 36.92% | -9.12% |

Raw RSI ensembles are **not** competitive. They are seeds for D1/D2/D3
evolution, not a replacement for the promoted library.

## Wiring

- `extra_seed_libraries` in `factor_mining_loop_config.yaml`
- Merged into iter seed library before enhanced evolution
- AST / DAG gates remain enabled

## Mutator bias (2026-09-17)

Raw seeds alone were insufficient (hold Sharpe 0.13). Iter 51+ adds
**RSI-family mutation priors** in `enhanced_factor_mutator.py`
(`RSI_MUTATION_RATE=0.35`):

- level / reversion / momentum / ts_z / demean / ts_rank / band
- RSI × turnover / money-flow / ATR crosses
- leaf injection of `rsi_14` into existing trees

Evolution budget raised to population 28 × 10 generations (patience 4).

## Iter 50–52 outcome

Loop evolution alone did not beat hold 2.056 (iters 50–52 KEPT). Cleaned RSI
survivors existed but semantic dedup removed them from the combination.

Force hold audits on the frozen panel:

| Library | n | Hold Sharpe |
|---|---:|---:|
| Live iter 49 | 12 | 2.0560 |
| Live + all cleaned RSI rows | 16 | **2.269** |
| Live + 2 distinct RSI (no twins) | 14 | **2.1537** |

The distinct +2 graft was promoted (twins would overweight one signal). Receipt:
`china_a_share_alpha_output/factor_mining_loop/iter_0052_rsi_promote/`.
