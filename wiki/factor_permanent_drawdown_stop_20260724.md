# A permanent -20% drawdown stop is usually an early sample exit

All 178 frozen factors were replayed on the stock-disjoint external panel. A
factor is permanently set to cash after its cumulative daily long-short net
asset value first reaches -20% peak-to-trough drawdown. This is a deliberately
strict descriptive stress test; it uses the same overlapping 5D/10D
forward-return stream as the prior Sharpe audit and is not a live execution
claim. [source: local artifact
china_a_share_alpha_output/external_unused_csi500_2025_2026/permanent_drawdown_stop_audit.csv]

The rule triggers for 160 of 178 factors. The median maximum drawdown shrinks
from -85.44% to -21.22%, but median Sharpe changes from 0.00 to -1.20. 139
triggers occur in June–July 2025, making the rule mostly a permanent removal
from the later sample rather than a risk-controlled continuation.

Among the four externally consistent candidates, only the 5D return-shape
factor `ts_skew(ts_min_max_scale(return, 3), 5)` retains attractive utility:
Sharpe falls from 2.655 to 2.034 while maximum drawdown becomes -21.04%. The
10D money-flow factor stops on 2025-07-02 and ends with Sharpe -0.579; the
WILLR-derived factor stops on 2025-08-29 and ends at 0.318; the PB/MACD factor
stops on 2025-06-12 and ends at -1.546. A single permanent stop is therefore
rejected as the default factor-risk policy. [source: local drawdown-stop audit,
2026-07-24]
