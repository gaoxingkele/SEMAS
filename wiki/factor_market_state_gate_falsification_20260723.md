# A shared drawdown date is not automatically a market-regime signal

High-Sharpe factor candidates can have clustered drawdown troughs, but a
cluster alone does not identify a tradable state variable. A gate must be
chosen on one interval and survive a later frozen interval, using only data
known at the decision date. [source: local external-validation artifact
china_a_share_alpha_output/external_unused_csi500_2025_2026/]

For the three stock-disjoint survivors, a lagged gate based on 20-day
equal-weight market volatility and 20-day trend was calibrated in 2025 and
tested unchanged in 2026. It improved drawdown slightly for only one return
shape factor, but degraded Sharpe materially and worsened the money-flow
factor's drawdown. The hypothesis is rejected; do not turn correlated loss
episodes into a generic high-volatility stop rule. [source: local
market-state-gate falsification run, 2026-07-23]
