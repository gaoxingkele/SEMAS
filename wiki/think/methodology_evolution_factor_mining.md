---
date: 2026-07-07
tags: [factor-mining, methodology, evolution, chain-of-thought]
sources:
  - ../wiki/factor_mining_loop_index.md
  - ../china_a_share_alpha_output/factor_mining_loop/STATE.md
related:
  - multi_horizon_design.md
  - cost_turnover_tradeoff.md
  - regime_switching_experiment.md
  - llm_critic_in_factor_mining.md
  - operator_expansion.md
---

# Factor Mining Methodology Evolution

This note traces the research evolution from the first loop iteration to the
promotion of a 20-day library. The goal is not to repeat operational logs, but
to capture the *thinking* that changed at each stage.

## Phase 1 — Empty seed and loose gates (iters 1–3)

**Hypothesis**: A genetic-programming loop with an empty seed will quickly
produce a small ensemble that passes all gates.

**Result**: Iteration 1 produced a 3-factor ensemble with negative train
Sharpe. Iteration 3 was the first gated run; it failed the correlation gate.

**Updated mental model**: Empty seed is too random; you need either a strong
seed library or much larger population/generations. Also, hard gates must be
enforced *before* promotion, not after.

## Phase 2 — Semantic dedup and live seed (iters 4–10)

**Hypothesis**: Removing near-duplicate expressions by Spearman correlation
will improve ensemble diversification.

**Result**: Iteration 4 promoted a library after adding semantic dedup.
Iterations 5–10 iterated on seed strategy, correlation-aware selection, and
independent verification on Tushare data.

**Updated mental model**:
- Greedy correlation filtering is more important than raw IC ranking.
- A live seed (previous best library) stabilizes evolution.
- Independent data verification catches data-leakage and cache bugs.

## Phase 3 — Multi-horizon and cross-market (iters 11–13)

**Hypothesis**: Evolving on multiple forward horizons (5d + 10d) and
aggregating results will produce a more robust library.

**Result**: Iteration 12 produced the previous best library (Sharpe 2.76).
Iteration 13 (cross-market transfer from CSI500/1000 to CSI300) failed.

**Updated mental model**:
- Multi-horizon merging helps when each horizon contributes non-overlapping
  factors.
- Cross-market transfer does not work for CSI300; in-market evolution is more
  reliable.

## Phase 4 — Grammar and data expansion (iters 14–15)

**Hypothesis**: Higher-order operators (skew, kurt, autocorr, entropy) and
money-flow data will uncover new alpha.

**Result**: Neither improved the live library in a single seed run.

**Updated mental model**:
- Expanding the grammar/data is necessary but not sufficient; the search
  process must be allowed to combine new primitives with the right windows.
- One seed run is too weak to prove operator value.

## Phase 5 — Combination heuristics (iters 16–17)

**Hypothesis**: Sophisticated ensemble weights (IC, Sharpe, risk-parity,
ridge) or volatility-regime switching will beat equal weight.

**Result**: Equal weight remained best. Ridge overfit. Regime switching either
collapsed to equal weight or overfit.

**Updated mental model**:
- Equal weight is a surprisingly strong baseline for small, curated factor
  sets.
- Regime labels must be stable and economically meaningful; median absolute
  return is too noisy.

## Phase 6 — LLM and anti-correlation (iters 18–19)

**Hypothesis**: LLM-generated expressions and anti-correlation search will add
orthogonal alpha.

**Result**: LLM expressions were syntactically valid but mostly weak.
Anti-correlation candidates were opposite-side noise with high turnover.

**Updated mental model**:
- LLM needs stronger prompts and smaller mutation scopes; random generation is
  not competitive with grammar-based evolution.
- Low correlation with the live library is not enough; candidates must also
  have sign-consistent predictive power.

## Phase 7 — Cost-aware evolution (iter 20)

**Hypothesis**: Using 20 bps transaction cost in the fitness function will
produce a lower-turnover, more cost-robust library.

**Result**: Turnover dropped, but the 10 bps-evolved library remained better at
10 bps.

**Updated mental model**: Transaction cost is a useful fitness knob for
specific execution assumptions, not a universal improvement.

## Phase 8 — 20-day horizon goal (iters 21–22)

**Hypothesis**: A dedicated 20d forward evolution, evaluated with realistic
20-day hold backtests, can beat the 5d library's 20d hold Sharpe of 1.75.

**Result**: Iteration 3 of the 20d run produced a 2-factor library with 20d
hold Sharpe 1.98 and cost-adj 60.78%.

**Updated mental model**:
- Longer-horizon evolution needs a configurable `forward_period` in the data
  loader.
- Realistic hold backtests are essential; daily-rebalance Sharpe on
  overlapping returns is misleading.
- A 20d library can be much sparser than a 5d library and still generalize.

## Open questions

1. Can we automate horizon-specific seeding (e.g., use 5d library as a seed
   for 10d/20d evolution) to accelerate convergence?
2. Should the promotion gate include realistic hold backtest by default?
3. How should we handle the sign-flip problem where val/test Sharpe is high
   but train Sharpe is negative?
