# Dual-horizon 30-round campaign completion

The useful distinction in this campaign is between a score that selects a
lineage and a score that evaluates it. The 5D and 10D research lineages used
validation Sharpe for every promotion, while the test fold was held aside for
the completed-lineage audit. [source: SEMAS_ARA_Architecture.md, frozen-snapshot evaluation]

The campaign completed all 60 planned rounds: 30 for 5D and 30 for 10D. It
produced nine strict validation-Sharpe promotions at 5D and eight at 10D.
The best validation Sharpe values were 6.4191 (5D) and 7.7895 (10D). [source: china_a_share_alpha_output/dual_horizon_30round_campaign/campaign_history.json]

The final independent test results remained positive, with Sharpe 4.0395 and
IC 0.0389 for 5D, and Sharpe 3.4117 and IC 0.0336 for 10D. This supports the
claim that the search generated nontrivial candidates beyond the 1.5 Sharpe
observation threshold, but it is not deployment evidence: final test maximum
drawdowns were -47.66% and -72.15%. The validation-selected parent was
iteration 27 for 5D and iteration 29 for 10D; later unpromoted candidates are
not part of this audit. [source: china_a_share_alpha_output/dual_horizon_30round_campaign/{5d/iter_0027,10d/iter_0029}/combination/combination_result.json]

The 10D lineage's late improvement matters because it occurred in round 29,
raising validation Sharpe from 7.7860 to 7.7895 before the held-out audit.
This is evidence of continued search movement, not evidence that small
validation increments will survive every future regime. [source: china_a_share_alpha_output/dual_horizon_30round_campaign/campaign_history.json]
