---
date: 2026-09-11
tags: [china-a-share, recent-regime, factor-matching, market-gate]
source_count: 2
---

# Recent Factor Matching Needs Both Stock and Market-Regime Selection

## Observation

The earlier matching policy's combined 2024--2026 result concealed a temporal
break: yearly Sharpe was about 1.437 in 2024, 1.097 in 2025, and -0.724 in 2026
through July 16. The local frozen panel contains no data after that date.

[source: china_a_share_alpha_output/tushare_snapshot_20260717/manifest.json]

The equal-weight universe changed from roughly +44.7% annualized return in 2025
H2 to -5.0% in 2026 Q1 and -6.0% from 2026 Q2 through July 16. Average daily
cross-sectional dispersion rose from 2.19% to 2.82%, while positive-stock breadth
fell from 47.8% to 45.7%. Factor-library IC rankings also reversed: their vector
correlation was -0.786 between 2025 H2 and 2026 Q1, then +0.888 between 2025 H2
and 2026 Q2--July. The first quarter was therefore a transient reversal rather
than a stable new factor ordering.

## Walk-forward result

Each window estimated stock, industry, market, and global utilities from the
preceding 504 trading days. Two deterministic stock buckets prevented a few
names from deciding selection. Across two additional eight-round campaigns,
the current-regime genome used two libraries, 26.36% stock utility, 11.98%
industry, 52.25% market, and 9.41% global utility. Its minimum full-universe
selection Sharpe was 1.263, but its April--July diagnostic Sharpe was -1.594
with -37.80% drawdown.

[source: wiki/factor_stock_matching_evolution_20260831.md]

## Market gate

A market gate is computed continuously from the equal-weight universe curve at
D close and only controls new D+1 entries; existing positions retain all T+1
stop, profit, and expiry rules. MA5, MA10, and MA20 were compared using 2025 H2
and 2026 Q1 only. MA20 had the best worst-window Sharpe (2.462) and satisfied the
25% drawdown gate.

Applying that predeclared selection rule to April--July 2026 produced:

- All stocks: Sharpe **1.027**, annualized return **17.94%**, drawdown **-7.13%**.
- Main board: Sharpe **-0.064**, annualized return **-2.26%**.
- STAR/ChiNext: Sharpe **0.899**, annualized return **19.06%**.
- Maximum all-stock return contribution concentration: **4.59%**.

Without the gate, the same matching policy had Sharpe -1.594 and -37.80%
drawdown in that window.

## Boundary

The diagnostic is not blind: the research process had already inspected the
2026 period before the reproducible gate-selection audit was finalized. The
result identifies a candidate architecture--stock matching plus market-level
cash control--but is not promotion evidence. Main-board performance also shows
that board-specific matching remains necessary. A refreshed snapshot after
2026-07-16 must be the next untouched confirmation interval.
