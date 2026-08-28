# Research state and repository state must agree

A reproducible factor result needs two kinds of cleanliness: the evaluator must
freeze its data and execution contract, and the repository must identify the
exact code, configuration, state, and research note that produced the result.
Generated console logs and large market snapshots do not provide that identity;
they should remain local while compact receipts and state summaries are kept in
version control. [source: local repository audit 2026-08-28]

The machine-readable loop state is authoritative for the current iteration.
Human-readable summaries must be reconciled to it before release. In this
cleanup, `state.json` identifies iteration 47 as the current live library, so
the older iteration-45 / iter-26 heading in `STATE.md` was corrected rather
than preserving two conflicting notions of "current." [source: local artifact
china_a_share_alpha_output/factor_mining_loop/state.json]

Factor rankings also require an explicit validity boundary. The published
effective-factor list includes only candidates with sufficient observations
and positive Sharpe and IC in both 2025 and 2026 on the frozen stock-disjoint
external panel. It is ordered by full-period Sharpe, but drawdown, turnover,
and horizon remain visible because Sharpe alone is not deployment approval.
[source: local artifact
china_a_share_alpha_output/external_unused_csi500_2025_2026/external_factor_utility_sharpe_ranking.csv]
