# Multi-Horizon Audit (5d / 10d / 20d)

## Equal-Weight Ensemble

| Horizon | Train IC | Train Sharpe | Val IC | Val Sharpe | Test IC | Test Sharpe | Cost-adj | Turnover | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| 5.0d | 0.0156 | 2.0107 | 0.0214 | 2.1198 | 0.0461 | 5.3079 | 217.77% | 0.0004 | -37.09% |
| 10.0d | 0.0143 | 2.7259 | 0.0401 | 3.9614 | 0.0620 | 7.5198 | 438.05% | 0.0004 | -50.24% |
| 20.0d | 0.0280 | 4.0437 | 0.0737 | 7.7303 | 0.0802 | 9.2050 | 824.51% | 0.0004 | -73.30% |

## Realistic H-Day Hold Backtest (ensemble)

| Horizon | Sharpe | Ann. return | Cost-adj | Max DD |
|---|---|---|---|---|
| 5.0d | 1.9694 | 50.24% | 50.24% | -17.86% |
| 10.0d | 2.0379 | 51.83% | 51.83% | -15.12% |
| 20.0d | 2.1386 | 53.85% | 53.85% | -16.92% |

## Per-Factor Test Sharpe by Horizon

| factor | 5 | 10 | 20 |
| --- | --- | --- | --- |
| factor_12 | 3.0747 | 4.7900 | 6.4703 |
| factor_16 | 3.4835 | 5.2328 | 6.8199 |
| factor_17 | 2.4978 | 3.4578 | 4.4072 |
| factor_23 | 1.4502 | 2.4843 | 2.2785 |
| factor_27 | 2.3463 | 3.2645 | 4.6389 |
| factor_31 | 0.4227 | 0.5264 | 0.1527 |
| factor_32 | 1.7711 | 2.3623 | 1.9624 |
| factor_34 | 1.6793 | 2.8194 | 4.2325 |
| factor_36 | 0.0000 | 0.0000 | 0.0000 |
| factor_37 | 0.0000 | 0.0000 | 0.0000 |
| factor_38 | 1.7313 | 2.5525 | 3.6751 |
| factor_39 | 0.0000 | 0.0000 | 0.0000 |
| factor_61 | 1.6808 | 1.2205 | 1.5897 |
| high_zscore_20 | 2.0528 | 2.8540 | 2.9653 |

Full CSV: `china_a_share_alpha_output\factor_mining_loop\multihizon_audit_iter37_cost0001\per_factor_horizon.csv`