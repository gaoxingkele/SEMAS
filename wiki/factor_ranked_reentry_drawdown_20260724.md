# Drawdown stops can coexist with daily factor ranking and re-entry

The permanent-stop experiment confuses a local loss-control decision with a
permanent belief that a factor is useless. A more faithful protocol treats each
factor as a sleeve: after a -20% episode drawdown, it cools down, then can
re-enter only when it passes a fresh daily ranking of all frozen factors.
[source: local ranked-reentry audit, 2026-07-24]

To prevent look-ahead, every daily ranking uses a 60-trading-day rolling Sharpe
computed only from completed factor returns. A 5D factor return is delayed by
6 trading days and a 10D return by 11 before it can affect that day's rank.
The entry threshold is the top 20% of all 178 factors. Cooldown durations of
5, 10, and 20 days are reported rather than selected after the fact. [source:
local artifact
china_a_share_alpha_output/external_unused_csi500_2025_2026/ranked_reentry_drawdown_audit.csv]

Across all factors, median maximum drawdown is -38.87%, -36.28%, and -34.49%
for 5-, 10-, and 20-day cooldowns. The individual sleeve loss is capped near
-20%, but cumulative portfolio drawdown can exceed that level after repeated
re-entries; this is expected and must not be represented as a global -20% NAV
cap.

For the four externally consistent candidates, 5-day cooldown produces the
best Sharpe for the WILLR factor (3.600), money-flow factor (3.190), and
return-shape factor (1.192). The PB/MACD factor is strongest at 10 days
(2.666). Their re-entry maximum drawdowns remain -33% to -53%, so the result
is a useful allocation/re-entry hypothesis, not completed drawdown control.
[source: local ranked-reentry audit, 2026-07-24]
