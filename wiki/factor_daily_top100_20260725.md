# TOP100 factor selection is a daily membership process

The ranked re-entry protocol now selects a fixed TOP100 from all 178 frozen
factors every eligible trading day, rather than a percentage threshold. The
membership is dynamic: 225 ranking days contain exactly 100 factors each and
cover 156 distinct factors over the full external audit. The first valid rank
is 2025-08-04 because the ranking requires completed, lagged history; earlier
dates remain uninvested rather than leaking future holding-period returns.
[source: local artifact
china_a_share_alpha_output/external_unused_csi500_2025_2026/ranked_reentry_top100/daily_top_100_membership.csv]

TOP100 increases factor availability versus the earlier top-20% rule. It
improves the all-factor median Sharpe to 0.902/1.300/1.228 for 5/10/20-day
cooldowns, but median maximum drawdown is still -59.53%/-55.22%/-44.59%.
Thus TOP100 is an auditable selection universe, not proof that risk is solved.
[source: local ranked-reentry TOP100 audit, 2026-07-25]
