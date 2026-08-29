# Factor Mining Loop State

Last evolution state: iteration 48 (2026-08-29)

Last state reconciliation: 2026-08-29

## Current Live Result

- Current live library: `china_a_share_alpha_output/factor_mining_loop/live_library.csv` (**iter 48**, 12 factors)
- Diagnostic test Sharpe (loop daily-reb): **1.9142**
- Diagnostic test cost-adjusted return (loop daily-reb): **30.89%**
- Promotion contract: **dynamic_trim**, 5d, 10 bps, minimum 50% factor coverage
- No-lookahead hold Sharpe: **1.8444**
- No-lookahead annualized return: **34.17%**
- No-lookahead max drawdown: **-10.04%**
- Frozen snapshot: `242f762f4229bc9723b8b2a146b34dedc9d1b2d86e30f0c1bad5d7d10019e011`

> Iter 48 promoted on the frozen snapshot with hold Sharpe **1.8444**, improving
> iter 47 baseline **1.8262** by +0.018. Historical daily-rebalanced best fields
> remain in `state.json` for schema compatibility and must not be interpreted as
> the current promotion baseline.

### 2026-07-13 Unified Frozen Audit

| Library | Contract | Hold Sharpe | Annualized return | Max DD | Verdict |
|---|---|---:|---:|---:|---|
| 5d live (iter 26) | dynamic trim, 5d | **2.4843** | 50.76% | -8.09% | PASS |
| 10d live (iter 4) | dynamic trim, 10d | **3.8514** | 84.38% | -10.97% | PASS |
| 20d live (iter 5) | simple hold, 20d | **1.3067** | 20.74% | -13.91% | PASS |

All three libraries were evaluated from the same checksum-verified test panel.
The corrected dynamic-trim rank bands and coverage-aware ensemble make these
numbers a new baseline; older dynamic-trim figures are not directly comparable.
No library was promoted or replaced by this audit.

> Superseded for production comparison by the 2026-07-16 no-lookahead horizon
> audit. These figures used signal-day returns and must not be used as promotion
> baselines.

### 2026-07-14 20d Position-Schedule Evolution

The 20d long-book schedule was evolved in ten cross-sectional rank bins with
10% multiplier increments, 10 bps one-way cost, and next-day return
application. Four-seed development/audit search and a recovery run selected
the static schedule `[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`.

| Fold | Sharpe | Annualized return | Max DD |
|---|---:|---:|---:|
| Development (2021-06 to 2023-12) | 0.4165 | 4.73% | -14.75% |
| Audit (2024-2025) | 0.2367 | 2.13% | -15.05% |
| Final isolation (2026-01 to 2026-05) | 1.7582 | 23.10% | -3.86% |

No dynamic schedule was promoted. The legacy trim schedule scored -0.6092 on
the audit fold despite scoring 2.2755 on the short final fold, so adopting it
after seeing final results would be retrospective overfitting. The 2026-07-13
hold figures above used same-day signal/return application and are superseded
for execution-policy comparison by this no-lookahead review. The factor
library itself was not changed.

### 2026-07-14 20d Factor / MA Exposure

Moving-average exposure was measured as the daily cross-sectional Spearman
correlation between each factor signal and `close / trailing_MA(close, n) - 1`.
Raw moving-average price levels were not used.

| Signal, test fold | MA5 | MA10 | MA20 |
|---|---:|---:|---:|
| Raw equal-weight ensemble | 0.3802 | 0.4080 | 0.4161 |
| EMA10 ensemble | 0.1929 | 0.3109 | 0.4255 |
| `high_zscore_20` | 0.5918 | 0.7965 | 0.8847 |
| `net_mf_amount` | 0.4851 | 0.3570 | 0.2658 |

The signs and magnitudes are stable across train, validation, and test. The
library therefore has material trend/momentum exposure, dominated by
`high_zscore_20`, rather than being independent of moving averages. This is a
redundancy/style diagnostic; it does not by itself show that MA signals or the
factor predict future returns. No factor or live state was changed.

### 2026-07-14 20d MA-Neutralized Alpha

The raw and EMA10 ensembles were jointly neutralized against standardized
MA5/10/20 deviations in every daily cross-section. Original and residual
signals use the same dates and symbols. Forward labels compound returns from
day `d+1` through `d+20` within each frozen fold.

| Fold | Signal | Version | 20d IC | Q5-Q1 | Hold Sharpe |
|---|---|---|---:|---:|---:|
| Train | raw | original | 0.0089 | 0.32% | -0.0188 |
| Train | raw | MA-neutral | 0.0216 | 0.67% | -0.2336 |
| Validation | raw | original | 0.0158 | 0.89% | -0.8346 |
| Validation | raw | MA-neutral | 0.0181 | 0.52% | -1.1379 |
| Test | raw | original | 0.0073 | 0.70% | 0.9542 |
| Test | raw | MA-neutral | 0.0095 | 0.34% | 1.0302 |
| Test | EMA10 | original | 0.0057 | 0.78% | 0.5954 |
| Test | EMA10 | MA-neutral | 0.0140 | 0.59% | 0.6578 |

MA5/10/20 jointly explain about 19.2% of daily raw-ensemble variance and 18.1%
of EMA10-ensemble variance. Positive residual IC and Q5-Q1 spreads remain in
all folds, so the library contains information beyond linear MA exposure.
However, residual hold Sharpe deteriorates in train and validation and improves
only in the aggregate test fold. The independent signal is statistically
visible but is not robustly monetized by the current fixed 20d cohort rule. No
live factor, weight, or promotion state was changed.

### 2026-07-16 No-Lookahead Horizon Decision

All live libraries were recomputed on continuous historical data and evaluated
with top/bottom 20% cohorts, day-`d+1` return application, actual target-weight
turnover, EMA10 smoothing, 50% factor coverage, and 10 bps one-way cost.
Static and fixed trim schedules were selected on the 2023 validation fold only.

| Horizon | Selected mode | Validation Sharpe | Test Sharpe | Test return | Max DD | Decision |
|---|---|---:|---:|---:|---:|---|
| 5d | dynamic trim | 0.7669 | **1.6337** | 29.17% | -12.42% | primary |
| 10d | simple hold | 0.1662 | **0.9906** | 15.58% | -17.81% | secondary, regime-sensitive |
| 20d | validation-selected trim | -0.1146 | -0.0697 | -1.59% | -21.64% | research-only |

Test-year Sharpe is 0.9391/2.0879/2.9197 for 5d, and
-0.0008/2.0663/2.4599 for 10d across 2024/2025/2026. The 10d result therefore
has value but lacks the annual consistency of 5d. The 20d static diagnostic is
positive on the aggregate test fold (Sharpe 0.5708), but static lost validation
selection and neither predefined 20d mode passed both validation and test.

Production promotion evaluation now uses the same shared no-lookahead
backtester and continuous-history warm-up. Direct production-entry verification
matches the audit candidates exactly: 5d dynamic 1.6337, 10d static 0.9906,
and 20d static 0.5708. No factor library was replaced.

### 2026-05-29 Audited Stock Cohorts

The 5d/10d selection export was generated from the final frozen date, not from
real-time July data. The 5d rebalance anchor is 2026-05-25 and the 10d anchor is
2026-05-18.

| Component | Rebalance cohort | Current positive longs | Exited longs | Shorts |
|---|---:|---:|---:|---:|
| 5d dynamic | 70 | 69 | 1 | 70 |
| 10d static | 70 | 70 | 0 | 70 |

The positive long union contains 108 stocks: 31 selected by both horizons, 38
5d-only primary names, and 39 10d-only secondary names. Component weights are
exported separately; no combined capital allocation was assigned. The cached
stock-name file is encoding-damaged, so audited outputs use exchange-qualified
stock codes rather than unreliable names.

### Best Hold-Sharpe Libraries from Batch Audit

| Rank | Iter | 5d hold Sharpe | 5d hold return | 5d max DD | Library |
|---|---:|---:|---:|---:|---|
| 1 | **26** | **2.49** | 73.70% | -11.96% | `iter_0026/combined_library.csv` |
| 2 | 33 | 2.41 | 69.93% | -9.84% | `iter_0033/combined_library.csv` |
| 3 | 36 | 2.37 | 61.27% | -12.46% | `iter_0036/combined_library.csv` |
| 4 | 27 | 2.30 | 61.73% | -11.99% | `iter_0027/combined_library.csv` |
| 5 | 39 | 2.29 | 60.29% | -13.40% | `iter_0039/combined_library.csv` |

> ⚠️ Iter 28 (previous best from single audit) now ranks lower at 5d hold Sharpe 2.25.
> The batch audit uses a fresh data load and equal-weight ensemble on
> `combined_library.csv`, which explains the small numerical shift versus earlier
> single audits.

### 2026-07-19 Frozen-Snapshot Resume (iter 46–48)

Iterations 46–48 run on snapshot `tushare_snapshot_20260717` (checksum
`242f762f...`). Promotion uses the no-lookahead dynamic-trim hold contract;
daily-rebalanced Sharpe is diagnostic only.

| Iter | Hold Sharpe | Hold return | Max DD | Promoted |
|---:|---:|---:|---:|---|
| 46 | 1.7911 | 33.31% | -9.54% | YES |
| 47 | 1.8262 | 33.98% | -9.55% | YES |
| 48 | **1.8444** | **34.17%** | -10.04% | YES |

Iter 48 is the current promotion baseline. Iter 26 remains the best historical
batch-audit library (hold Sharpe 2.49) under an older evaluation contract.

### Cost Robustness (iter 40 library, superseded contract)

| Cost | 5d hold Sharpe | 5d hold return | 5d max DD |
|---|---:|---:|---:|
| 10 bps | 1.64 | 39.41% | -18.04% |
| 20 bps | 1.17 | 25.94% | -20.09% |
| 30 bps | 0.70 | 13.75% | -22.16% |

### Other Artifacts

- Final audit: `china_a_share_alpha_output/factor_mining_loop/iter_0041_audit`
- Multi-horizon hold audit (current): `china_a_share_alpha_output/factor_mining_loop/multihizon_audit_iter40_cost0001`
- 20d live library: `china_a_share_alpha_output/factor_mining_loop/live_library_20d.csv`
- 20d hold audit: `china_a_share_alpha_output/factor_mining_loop_20d/iter_0003/horizon_audit`

## High Priority

- [x] Run iteration 12 multi-horizon evolution (5d + 10d).
- [x] Promoted a new live library with test Sharpe 2.76 and cost-adj 32.47%.
- [x] Independently verified on real Tushare data.
- [x] Completed iterations 13–21 of the diversification roadmap.
- [x] Final production audit confirms cost robustness and sector neutrality.
- [x] Built and promoted a 20-day horizon library (`live_library_20d.csv`).
- [x] Integrated TA-Lib indicators and Alpha101 seeds (iter 22–31).
- [x] Promoted new 5d live library with realistic hold Sharpe 2.37 (vs previous 1.82).
- [x] Resumed frozen-snapshot loop at iter 46–47; current hold Sharpe **1.8262**.
- [x] Iter 48 promoted on frozen snapshot; hold Sharpe **1.8444** (12 factors).
- [ ] Human review of the 5d primary and 10d secondary libraries before production use.


## Watch List

- Current live library (iter 47) has 10 factors after semantic dedup; max
  selection correlation 0.36.
- Promotion baseline is hold Sharpe under dynamic trim, not daily-rebalanced
  Sharpe (historical best 6.34 is not comparable).
- Iter 45 failed min-count and correlation gates; hold gate now active for all
  promotions from iter 42 onward.

## Iteration History

| Iter | Seed | Merged | Cleaned | Deduped | Train Sharpe | Test Sharpe | Cost-adj | Promoted | Gates |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1001 | 21 | 2 | - | -0.389 | 1.6283 | 24.75% | YES | - |
| 2 | 1002 | 23 | 5 | - | -0.389 | 1.6283 | 24.75% | NO | - |
| 3 | 1003 | 22 | 6 | - | 0.593 | 1.5771 | 22.65% | NO | corr failed |
| 4 | 1004 | 30 | 8 | 6 | 0.123 | 2.1145 | 30.25% | YES | all✓ |
| 5 | 1005 | 23 | 9 | 7 | 0.118 | 2.2034 | 30.76% | YES | all✓ |
| 6 | 1006 | 25 | 16 | 14 | 1.655 | 1.0963 | 9.50% | NO | corr failed |
| 7 | 1007 | 37 | 2 | 3 | -0.070 | 1.2424 | 10.91% | NO | train/count |
| 8 | 1008 | 58 | 21 | 17 | 1.345 | 2.3964 | 28.42% | NO | corr failed |
| 9 | 1009 | 48 | 16 | 14 | 1.292 | 0.4955 | -4.60% | NO | corr failed |
| 10 | 1010 | 56 | 15 | 12 | 1.686 | 2.7031 | 31.46% | YES | all✓ |
| 11 | - | - | - | - | 1.69 (20 bps) | 2.7031 (20 bps) | 23.17% | N/A | stress test |
| 12 | 1201/1202 | 46 | 21 | 10 | 1.362 | **2.7629** | **32.47%** | YES | all✓ |
| 13 | 1301/1302 | 48 | 17 | 10 | 2.523 | 1.8354 | 14.73% | NO | not improved |
| 14 | 1014 | 26 | 15 | 12 | 2.009 | 2.4074 | 28.48% | NO | not improved |
| 15 | 1030 | 25 | 15 | 15 | 1.639 | 2.0207 | 16.99% | NO | not improved |
| 16 | 1016 | 10 | 10 | 10 | 1.773 | 2.7629 | 32.47% | NO | equal best |
| 17 | 1017 | 10 | 10 | 10 | 1.773 | 2.7629 | 32.47% | NO | equal best |
| 18 | 1018 | 30 | 30 | 10 | 0.090 | 2.3081 | 22.61% | NO | gates failed |
| 19 | 1019 | 20 | 20 | 10 | -4.402 | 1.1437 | 10.19% | NO | gates failed |
| 20 | 1040 | 28 | 13 | 12 | 1.713 | 2.2126 | 25.76% | NO | not improved |
| 21 | 1021 | 10 | 10 | 10 | 1.773 | 2.7629 | 32.47% | N/A | final audit |
| 22 | 1025 | 35 | 1 | 2 | -3.251 | 3.663 (20d) | 60.78% (20d hold) | YES | 20d hold Sharpe 1.98 |
| 22 | 1046 | 33 | 10 | 10 | 2.175 | 5.4115 | 209.85% | YES | TA-Lib + Alpha101 seeds |
| 23 | 1047 | 31 | 18 | 14 | 1.424 | 4.8574 | 180.75% | NO | not improved |
| 24 | 1048 | 35 | 19 | 12 | 2.273 | 5.4695 | 216.46% | YES | all✓ |
| 25 | 1049 | 28 | 13 | 14 | 2.273 | 5.4695 | 216.46% | NO | equal best |
| 26 | 1050 | 22 | 13 | 13 | 2.273 | 5.4695 | 216.46% | NO | equal best |
| 27 | 1051 | 26 | 18 | 14 | 3.185 | 5.3938 | 196.59% | NO | not improved |
| 28 | 1052 | 29 | 17 | 15 | 1.899 | **5.9344** | **245.69%** | YES | all✓ |
| 29 | 1053 | 29 | 18 | 17 | 1.902 | 5.9392 | 245.91% | NO | equal best |
| 30 | 1054 | 30 | 24 | 17 | 0.319 | 4.3496 | 163.44% | NO | not improved |
| 31 | 1055 | 26 | 19 | 18 | 2.743 | 4.3490 | 166.79% | NO | not improved |
| 32 | 1056 | 28 | 20 | 18 | 1.899 | 5.9344 | 245.69% | NO | equal best |
| 33 | 1057 | 31 | 23 | 21 | 2.896 | 5.0129 | 170.69% | NO | not improved |
| 34 | 1058 | 28 | 18 | 16 | 1.899 | 5.9344 | 245.69% | NO | equal best |
| 35 | 1059 | 33 | 19 | 19 | 2.860 | 4.4980 | 170.22% | NO | not improved |
| 36 | 1060 | 33 | 26 | 23 | 1.987 | 5.7696 | 238.38% | NO | not improved |
| 37 | 1061 | 31 | 20 | 17 | 2.148 | **6.3436** | 231.48% | YES | all✓ |
| 38 | 1062 | 31 | 25 | 20 | 1.914 | 4.8953 | 176.45% | NO | not improved |
| 39 | 1063 | 32 | 22 | 20 | 2.148 | 6.3436 | 231.48% | NO | equal best |
| 40 | 1064 | 34 | 25 | 23 | 1.889 | 5.7213 | 234.24% | YES | promoted by return |
| 41 | 1065 | 29 | 29 | 26 | 1.875 | 4.7750 | 185.77% | NO | not improved |
| 42 | 1042 | 13 | 10 | 10 | 1.217 | 2.3489 | 35.88% | NO | hold 1.95 |
| 43 | 1043 | 29 | 10 | 10 | 1.217 | 2.3489 | 35.88% | NO | hold 1.95 |
| 44 | 1044 | 27 | 17 | 12 | 1.250 | 1.5727 | 26.06% | NO | hold 2.24 |
| 45 | 1045 | 26 | 15 | 0 | 2.178 | 1.3614 | 15.27% | NO | gates failed |
| 46 | 1046 | 21 | 10 | 8 | 0.449 | 2.0512 | 34.30% | YES | hold **1.79** |
| 47 | 1047 | 18 | 16 | 10 | 1.162 | 2.3505 | 39.30% | YES | hold **1.83** |
| 48 | 1048 | 20 | 14 | 12 | 2.381 | 1.9142 | 30.89% | YES | hold **1.84** |

> Rows 42–47: **Cost-adj** is loop daily-reb diagnostic return. **Gates** column
> shows no-lookahead hold Sharpe when the hold gate was active.

---

Updated by `china_a_share_alpha/scripts/run_factor_mining_loop.py`.
See `LOOP.md` for loop design and gates.
