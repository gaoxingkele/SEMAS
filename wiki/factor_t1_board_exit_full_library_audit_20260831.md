# T+1 exits change which factor libraries survive

The execution contract uses a D close signal, D+1 open entry, no sale on the
purchase day, and D+6/D+11/D+21 expiry for 5d/10d/20d strategies. Stop-loss and
trailing-profit signals are close-confirmed and execute at the next sellable
open. Limit-down locks queue rather than fabricate a fill. [source: local code
china_a_share_alpha/backtest/t1_exit_policy.py]

Policy thresholds are board-aware. Main-board loss/profit/trailing thresholds
are 20%, 15/25/35%, and 8%; STAR/ChiNext use 30%, 25/40/55%, and 12%; BSE uses
40%, 35/55/75%, and 16%. ST names are excluded. [source: local config
china_a_share_alpha/examples/t1_full_library_audit.yaml]

The frozen 2024-01-02 to 2026-07-16 audit deduplicated 69 canonical source
files into 54 distinct libraries containing 115 unique expressions. All
expressions evaluated successfully. It completed 486 stock backtests and
recorded 162 BSE combinations as unavailable because the CSI300-derived frozen
snapshot contains no BSE securities. Independent index and ETF panels were
also absent and were not imputed. [source: local artifact
china_a_share_alpha_output/t1_full_library_audit_20260830/audit_manifest.json]

The strongest all-stock result was the 10d policy on library
`c463e55d2a9ad794`: Sharpe 1.269, annualized return 36.71%, and maximum drawdown
-16.79%, versus an equal-weight universe benchmark Sharpe of 0.781. The best
all-stock 5d policy barely exceeded that benchmark (0.791 versus 0.781), while
the best main-board 5d policy underperformed its benchmark (0.578 versus
0.695). [source: local artifact
china_a_share_alpha_output/t1_full_library_audit_20260830/library_strategy_results.csv]

The iteration-48 live library no longer leads under the new contract. Its
all-stock 5d/10d/20d Sharpes were 0.128/0.756/0.577; its 5d annualized return
was -1.64%. This invalidates any assumption that the previous dynamic-hold
promotion transfers unchanged to board-aware T+1 stop/trailing execution.
[source: local artifact
china_a_share_alpha_output/t1_full_library_audit_20260830/library_strategy_results.csv]

Across 1,250,622 replicated library/universe/horizon trade receipts, ordinary
expiry dominated. There were 6,170 cumulative-stop exits, 21,236 limit-down
stop exits, and 31,716 trailing-profit exits. Normal expiry medians were exactly
5/10/20 post-buy trading days; delayed sellability extended some exits to
24/30/38 days. [source: local artifact
china_a_share_alpha_output/t1_full_library_audit_20260830/trade_receipts.parquet]

This is a frozen daily-bar research audit, not deployment approval. Historical
ST status and listing-age history are not available in the compact snapshot,
and daily bars cannot prove queue priority or intraday path ordering. ETF,
independent index, and BSE conclusions require dedicated frozen panels.
