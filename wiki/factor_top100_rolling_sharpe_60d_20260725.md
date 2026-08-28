# Current TOP100 rule: 60-day completed-return rolling Sharpe

The active research definition for daily TOP100 selection is the 60-trading-day
rolling Sharpe of each factor's completed long-short returns. Factor returns
remain delayed by 6 days for 5D and 11 days for 10D factors before they enter
the score, so the ranking uses no future holding-period outcome. The TOP100 is
recomputed every eligible day; it is not a fixed library. [source: local
artifact china_a_share_alpha_output/external_unused_csi500_2025_2026/
ranked_reentry_top100/daily_top_100_membership.csv]

The 20-day mean-rank variant remains a documented comparison experiment, not
the current selection rule. Under the 60-day rolling-Sharpe TOP100 protocol,
median Sharpe is 0.902/1.300/1.228 and median maximum drawdown is
-59.53%/-55.22%/-44.59% for 5/10/20-day cooldowns. The 10-day cooldown has the
highest median Sharpe; no parameter is thereby promoted to production.
[source: local artifact
ranked_reentry_top100/ranked_reentry_drawdown_summary.csv]
