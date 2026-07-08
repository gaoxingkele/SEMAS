# Multi-Horizon Audit (5d / 10d / 20d)

## Equal-Weight Ensemble

| Horizon | Train IC | Train Sharpe | Val IC | Val Sharpe | Test IC | Test Sharpe | Cost-adj | Turnover | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| 5.0d | 0.0192 | 2.1833 | 0.0127 | 1.3614 | 0.0507 | 5.6947 | 226.35% | 0.0004 | -37.71% |
| 10.0d | 0.0253 | 3.4423 | 0.0310 | 2.9923 | 0.0639 | 7.8445 | 442.94% | 0.0004 | -52.77% |
| 20.0d | 0.0340 | 3.7715 | 0.0624 | 6.6094 | 0.0798 | 9.9140 | 827.25% | 0.0004 | -76.25% |

## Realistic H-Day Hold Backtest (ensemble)

| Horizon | Sharpe | Ann. return | Cost-adj | Max DD |
|---|---|---|---|---|
| 5.0d | 1.9363 | 53.20% | 53.20% | -18.51% |
| 10.0d | 2.0799 | 56.23% | 56.23% | -14.66% |
| 20.0d | 2.5615 | 72.06% | 72.06% | -14.42% |

## Per-Factor Test Sharpe by Horizon

| factor | 5 | 10 | 20 |
| --- | --- | --- | --- |
| factor_10 | 2.3463 | 3.2645 | 4.6389 |
| factor_19 | 1.8669 | 2.0258 | 0.7052 |
| factor_2 | 3.0747 | 4.7900 | 6.4703 |
| factor_22 | 0.4913 | 0.8182 | 0.3444 |
| factor_23 | 1.4502 | 2.4843 | 2.2785 |
| factor_24 | 0.0000 | 0.0000 | 0.0000 |
| factor_25 | 1.6793 | 2.8194 | 4.2325 |
| factor_31 | 0.4227 | 0.5264 | 0.1527 |
| factor_32 | 1.7711 | 2.3623 | 1.9624 |
| factor_35 | 1.7313 | 2.5525 | 3.6751 |
| factor_36 | 0.0000 | 0.0000 | 0.0000 |
| factor_39 | 0.0000 | 0.0000 | 0.0000 |
| factor_5 | 3.4835 | 5.2328 | 6.8199 |
| factor_61 | 1.6808 | 1.2205 | 1.5897 |
| high_zscore_20 | 2.0528 | 2.8540 | 2.9653 |

Full CSV: `china_a_share_alpha_output\factor_mining_loop\multihizon_audit_iter24_cost20bps\per_factor_horizon.csv`