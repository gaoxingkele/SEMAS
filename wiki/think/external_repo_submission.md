---
date: 2026-07-07
tags: [factor-mining, external-repo, dissemination, production]
sources:
  - https://github.com/gaoxingkele/Stock_benchmark
  - ../china_a_share_alpha/scripts/export_factor_values.py
related:
  - factor_export_for_external_algorithms.md
  - methodology_evolution_factor_mining.md
---

# External Repo Submission

## Motivation

Make the discovered alpha factors portable and usable outside the SEMAS
framework by contributing them to a separate benchmark repository.

## Constraints

- One-time submission only.
- Must not affect the local SEMAS repository.
- The external repo should receive a self-contained `factors/` folder with
  expressions, evaluator, and documentation.

## Process

1. Cloned `https://github.com/gaoxingkele/Stock_benchmark` to a temporary
   directory outside the SEMAS repo.
2. Extracted the self-contained parser/expression modules from SEMAS.
3. Created `factors/` containing:
   - `expressions.json` — 16 unique factor expressions + metadata.
   - `evaluate_factors.py` — standalone evaluator.
   - `semas_expression.py` / `semas_parser.py` — DSL support.
   - `README.md` — usage, performance, caveats.
   - `config.yaml` — key hyper-parameters.
   - `example.py` — minimal usage example.
4. Verified the evaluator on synthetic data.
5. Committed and pushed to the external repo.

## Result

- Commit: `8c63cd4`
- Remote: `https://github.com/gaoxingkele/Stock_benchmark`
- Local SEMAS repo remained untouched.

## Lessons

- Parser/expression modules are cleanly separable from the rest of SEMAS.
- Providing both JSON metadata and runnable code lowers the barrier for
  external users.
- README caveats are essential because historical Sharpe can be misused as a
  forward promise.
