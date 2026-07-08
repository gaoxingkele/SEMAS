# Factor Mining Loop State

Last run: 2026-07-08

## Best Result

- Test Sharpe (loop daily-reb): **5.9344**
- Test cost-adjusted return (loop daily-reb): **245.69%**
- Real 5d hold Sharpe: **2.3684**
- Real 5d hold annualized return: **69.55%**
- Real 5d hold max drawdown: **-17.02%**
- Live library: `china_a_share_alpha_output/factor_mining_loop/live_library.csv`
- Final audit: `china_a_share_alpha_output/factor_mining_loop/iter_0031_audit`
- Multi-horizon hold audit: `china_a_share_alpha_output/factor_mining_loop/multihizon_audit_iter24`
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
- [ ] Human review of the 5d and 20d live libraries before production use.


## Watch List

- Multi-horizon evolution improved both Sharpe and cost-adjusted return.
- Greedy correlation filter kept max selection correlation at 0.37.
- Training Sharpe is positive (1.36) but lower than iteration 10; monitor
  stability in future iterations.

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

---

Updated by `china_a_share_alpha/scripts/run_factor_mining_loop.py`.
See `LOOP.md` for loop design and gates.
