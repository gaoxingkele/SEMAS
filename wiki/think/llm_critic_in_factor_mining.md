---
date: 2026-07-07
tags: [factor-mining, llm, critic, generation, experiment]
sources:
  - ../china_a_share_alpha/evolution/llm_mutator.py
  - ../china_a_share_alpha/scripts/generate_llm_factors.py
  - ../wiki/factor_mining_loop_iteration_18.md
related:
  - methodology_evolution_factor_mining.md
---

# LLM Critic in Factor Mining

## Hypothesis

An LLM can propose new factor expressions by mutating existing ones, acting as
a critic/operator that explores the grammar in directions grammar-based
mutation misses.

## Experiment

- Updated `LLMFactorMutator.SYSTEM_PROMPT` to include the full DSL and all
  variables.
- Generated 20 expressions seeded from the live library.
- Evaluated and merged them.

## Result

- Many generated expressions were trivial (single variables, constants, or
  nested noise).
- Best single factor test Sharpe ~1.2, far below the live library.
- The merged ensemble diluted performance and failed hard gates.

## Why it failed

1. The prompt asked for *random* variants rather than targeted improvements.
2. The LLM has no access to in-sample IC/turnover statistics, so it cannot
  act as a true critic.
3. Arithmetic expressions are a low-bandwidth way to convey factor ideas.

## Updated model

LLM factor generation is more promising as a **targeted assistant** than a
**random generator**:
- "Mutate factor X to reduce turnover while keeping IC."
- "Combine factors A and B into a single expression."
- "Propose a sector-neutral version of factor Y."

A true LLM critic would need access to factor metrics and the ability to
propose edits conditioned on those metrics.
