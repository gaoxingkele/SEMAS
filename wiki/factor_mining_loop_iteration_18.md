---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-18, llm-critic]
sources:
  - ../china_a_share_alpha/evolution/llm_mutator.py
  - ../china_a_share_alpha/scripts/generate_llm_factors.py
  - ../china_a_share_alpha_output/factor_mining_loop/iter_0018_llm/llm_leaderboard.csv
related:
  - factor_mining_loop_iteration_17.md
  - factor_mining_loop_iteration_19.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 18 Chain-of-Thought

## Trigger

Use an LLM critic to generate new factor expressions guided by the current live
library, then test whether they improve the ensemble.

## Setup

- Updated `LLMFactorMutator.SYSTEM_PROMPT` to include the full DSL: high-order
  operators, conditional operators, and all money-flow/fundamental variables.
- Created `china_a_share_alpha/scripts/generate_llm_factors.py` to batch-generate
  LLM-proposed factors from seed expressions.
- Generated 20 expressions seeded from the iteration-12 live library.
- Merged the generated leaderboard with the live library (30 unique expressions)
  and ran the standard combination pipeline.

## Observations

- The LLM produced a mix of single-variable, constant, and complex nested
  expressions.
- Best single generated factor: `dt_netprofit_yoy` with test Sharpe 1.197.
- Many generated expressions were constants or had near-zero IC.
- The merged ensemble selected 10 factors but suffered from negative train
  Sharpe and high pairwise correlation.

## Metrics

| Period | Sharpe | Cost-adj return | Turnover |
|---|---|---|---|
| Train | 0.0903 | -6.63% | 0.0021 |
| Val   | 1.3450 | 11.97% | 0.0006 |
| Test  | 2.3081 | 22.61% | 0.0006 |

## Decision

- **Not promoted.** The LLM-generated library failed the train-Sharpe and
  max-correlation gates and did not beat the iteration-12 live library.
- The LLM mutator remains part of the codebase for future prompts and hybrid
  workflows.

## New knowledge

1. **LLM-generated expressions are syntactically valid but mostly weak.** The
   model tends to produce trivial or noisy expressions when asked for random
   variants.
2. **Guidance matters.** Better results may require stronger prompt templates,
   e.g., "mutate this weak factor to reduce turnover" or "combine these two
   uncorrelated factors."
3. **A pure LLM batch generator is not yet competitive with grammar-based
   evolution** for this task.

## References

- [source: `china_a_share_alpha/evolution/llm_mutator.py`]
- [source: `china_a_share_alpha/scripts/generate_llm_factors.py`]
- [source: `wiki/factor_mining_loop_iteration_17.md`]
