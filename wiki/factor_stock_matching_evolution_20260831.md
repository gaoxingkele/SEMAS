---
date: 2026-08-31
tags: [china-a-share, factor-evolution, stock-matching, negative-result]
source_count: 1
---

# Stock-to-Factor Matching Needs Cross-Time and Cross-Stock Validation

## Claim

More evolutionary rounds do not by themselves make a factor library match
stocks accurately. A match policy must generalize across both unseen dates and
unseen stocks; otherwise the search can optimize a favorable validation regime
or a handful of exceptional securities.

## Experiment

The 10-day T+1 policy was used because the full-library audit ranked it highest.
For each of 54 canonical factor libraries, train-only forward-return correlation
estimated four utility levels: stock, industry, market, and global. A genome
selected the top libraries and evolved their shrinkage weights, temperature,
minimum sample count, and portfolio selection fraction over 12 rounds with 12
candidates per round. The 2023 validation fold alone determined selection; the
2024--2026 test fold remained closed until the final genome was fixed.

[source: wiki/factor_t1_board_exit_full_library_audit_20260831.md]

## Result

- Validation Sharpe: **1.722**; annualized return: **48.75%**; drawdown:
  **-11.18%**.
- Frozen all-stock test Sharpe: **0.374**; annualized return: **6.07%**;
  drawdown: **-48.55%**.
- Main-board test Sharpe: **0.775**; STAR/ChiNext test Sharpe: **0.883**.
- The best genome used seven libraries and weighted stock/industry/market/global
  utility at 0.88%/35.58%/39.81%/23.74%.
- Removing the top five stock contributors reduced annualized return to
  **-0.87%** and Sharpe to **0.185**.

The frozen test is materially worse than the static 10-day full-library audit
baseline (all-stock Sharpe 1.269). The matching genome is therefore rejected.

## Implication

The next campaign should replace one-year validation with rolling temporal
folds and stock-disjoint validation, optimize a lower-tail or median fold score,
and enforce contribution concentration and drawdown as hard gates. Evolution
should stop early when validation improvements fail to transfer between folds.
No live factor library should change until the candidate beats the static
baseline on those gates and on a final unopened test.
