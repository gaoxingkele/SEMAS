---
date: 2026-09-18
tags: [rsi, recursive-self-improvement, correction, factor-mining]
related: [factor_rsi_modern_seeds_20260917.md, SEMAS_SELF_UPGRADE_DESIGN.md]
---

# CORRECTION: RSI = Recursive Self-Improvement (not Relative Strength Index)

User intent for “引入 RSI 最新方法论” was **Recursive Self-Improvement**
（递归自我进化 / 反身元进化）, **not** the TA-Lib Relative Strength Index.

[source: user clarification 2026-09-18]
[source: arXiv:2410.04444 Gödel Agent]
[source: arXiv:2505.22954 Darwin Gödel Machine]
[source: arXiv:2605.27276 SIA]
[source: SEMAS_SELF_UPGRADE_DESIGN.md]

## What went wrong (2026-09-17)

The agent misread RSI as the momentum oscillator and built:

- `rsi_modern_seed_library.csv` / `rsi_hybrid_seed_library.csv`
- RSI-biased mutations in `enhanced_factor_mutator.py`
- An accidental live-library graft of two `rsi_14` expressions (hold 2.154)

That work is **orthogonal** to the requested methodology. The Relative Strength
Index artifacts remain in the tree as collateral; they must not be cited as
“RSI methodology” fulfillment.

## Correct meaning here

| Layer | Object being evolved | Fitness |
|---|---|---|
| Inner | Factor expressions / live library | Hold Sharpe under frozen contract |
| **Outer (true RSI)** | Mining-loop **policy genome** (dedup τ, AST gates, DAG parents, mutation mix, promotion rules, seed policy) | Whether the *next* inner iter improves hold / avoids known failure modes |

Failure receipts (e.g. semantic dedup dropping useful survivors, KEPT with flat hold) become **meta-gradients** that mutate the outer policy, then the inner loop re-runs — recursively.

## Next implementation target

`china_a_share_alpha/loop/recursive_self_improve.py` (+ policy genome YAML):
mirror `benchmarks/semas_self_upgrade/evolve_semas.py`, but the downstream task
is one factor-mining iteration under the frozen snapshot.
