# Multi-Horizon Audit (5d / 10d / 20d)

## Equal-Weight Ensemble

| Horizon | Train IC | Train Sharpe | Val IC | Val Sharpe | Test IC | Test Sharpe | Cost-adj | Turnover | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| 5.0d | 0.0112 | 2.8688 | 0.0324 | 3.4187 | 0.0384 | 4.5361 | 181.33% | 0.0002 | -36.38% |
| 10.0d | 0.0095 | 4.1170 | 0.0504 | 4.7299 | 0.0528 | 6.0618 | 365.45% | 0.0002 | -56.28% |
| 20.0d | 0.0243 | 5.5691 | 0.0787 | 7.0355 | 0.0707 | 7.2216 | 711.88% | 0.0002 | -81.93% |

## Realistic H-Day Hold Backtest (ensemble)

| Horizon | Sharpe | Ann. return | Cost-adj | Max DD |
|---|---|---|---|---|
| 5.0d | 0.6988 | 13.75% | 13.75% | -22.16% |
| 10.0d | 1.5091 | 35.90% | 35.90% | -16.82% |
| 20.0d | 1.4853 | 35.00% | 35.00% | -18.70% |

## Per-Factor Test Sharpe by Horizon

| factor | 5 | 10 | 20 |
| --- | --- | --- | --- |
| factor_13 | 2.4978 | 3.4578 | 4.4072 |
| factor_16 | 3.1892 | 4.9494 | 6.6196 |
| factor_17 | 2.3463 | 3.2645 | 4.6389 |
| factor_2 | 3.0070 | 4.4245 | 5.7522 |
| factor_23 | 0.0000 | 0.0000 | 0.0000 |
| factor_24 | 1.8669 | 2.0258 | 0.7052 |
| factor_27 | 2.0625 | 3.3052 | 3.5835 |
| factor_29 | 0.4913 | 0.8182 | 0.3444 |
| factor_3 | 3.0747 | 4.7900 | 6.4703 |
| factor_31 | 0.4227 | 0.5264 | 0.1527 |
| factor_32 | 1.7711 | 2.3623 | 1.9624 |
| factor_34 | 1.7313 | 2.5525 | 3.6751 |
| factor_36 | 0.0000 | 0.0000 | 0.0000 |
| factor_37 | 0.0000 | 0.0000 | 0.0000 |
| factor_39 | 0.0000 | 0.0000 | 0.0000 |
| factor_6 | 3.4835 | 5.2328 | 6.8199 |
| factor_61 | 1.6808 | 1.2205 | 1.5897 |
| factor_7 | 3.0463 | 3.8977 | 4.3834 |
| factor_9 | 3.4180 | 4.5607 | 6.1548 |
| high_zscore_20 | 2.0528 | 2.8540 | 2.9653 |

Full CSV: `china_a_share_alpha_output\factor_mining_loop\multihizon_audit_iter40_cost0003\per_factor_horizon.csv`