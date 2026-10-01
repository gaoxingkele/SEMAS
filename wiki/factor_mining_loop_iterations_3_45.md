# Factor Mining Loop — Iterations 3–45 Retrospective

> Date: 2026-09-22 (retro-capture of runs from 2026-07-04 to 2026-07-13)
> Sources: `china_a_share_alpha_output/factor_mining_loop/loop_report_*.md`,
> `china_a_share_alpha_output/factor_mining_loop_{10d,20d}/state.json`,
> `china_a_share_alpha_output/batch_multihizon_audit/FINDINGS.md`

## Trigger

`OPERATION_LOG.md` records only iterations 1–2 of the continuous factor-mining
loop (2026-07-04) and `wiki/` records only the iteration 1/2 chain-of-thought
notes. The on-disk run artifacts show 45 reported iterations in the main 5D
loop plus two later horizon branches. This note closes that documentation gap
and preserves the audit conclusion that ended the loop, before the raw
`china_a_share_alpha_output/` tree (git-ignored) is rotated away.

## Scope and iteration counts

| Loop | Iterations | Window | Final live artifact |
|---|---|---:|---|
| 5D main, `factor_mining_loop/` | 45 reports covering iterations 1–45; iteration dirs run to `iter_0046` | 2026-07-04 → 07-12 | `iter_0040` combination promoted as `live_library.csv` |
| 10D, `factor_mining_loop_10d/` | 7 recorded iterations (`iter_0001`–`iter_0007`), plus an aborted `iter_0008` on 07-12 | 2026-07-08 → 07-12 | `live_library.csv` from iteration 4 |
| 20D, `factor_mining_loop_20d/` | 12 recorded iterations (`iter_0001`–`iter_0012`) | 2026-07-06 → 07-12 | `iter_0005/combined_library.csv` (retained as baseline) |

Reported iterations in the 5D loop: 1–10, 14, 15, 20, 22–45 (37 reports).
Iterations 11–13 and 16–21 exist only as labelled variant directories
(`iter_0012_5d`, `iter_0012_10d`, `iter_0013_csi500`, `iter_0013_csi1000`,
`iter_0016*`, `iter_0017_regime*`, `iter_0018_llm`, `iter_0019_anticorr`,
`iter_0021_audit*`), i.e. they were exploratory side-runs rather than promoted
loop steps.

[source: `china_a_share_alpha_output/factor_mining_loop/loop_report_*.md`]
[source: `china_a_share_alpha_output/factor_mining_loop/iter_0046/`]
[source: `china_a_share_alpha_output/factor_mining_loop_10d/iter_0008/`]

## Promotion chain (5D main loop)

Each row is an iteration whose library replaced the live library. Everything
not listed was rejected and retained the previous library.

| Iter | Date | Seed | Merged → cleaned | Test Sharpe | Test cost-adj | Artifact |
|---:|---|---:|---:|---:|---:|---|
| 1 | 07-04 | 1001 | 21 → 2 | 1.6283 | 0.2474 | `iter_0001` |
| 4 | 07-04 | 1004 | 30 → 8 | 2.1145 | 0.3025 | `iter_0004` |
| 5 | 07-04 | 1005 | 23 → 9 | 2.2034 | 0.3076 | `iter_0005` |
| 10 | 07-05 | 1010 | 56 → 15 | 2.7031 | 0.3146 | `iter_0010` |
| 22 | 07-08 | 1046 | 33 → 10 | 5.4115 | 2.0985 | `iter_0022` |
| 24 | 07-08 | 1048 | 35 → 19 | 5.4695 | 2.1646 | `iter_0024` |
| 28 | 07-08 | 1052 | 29 → 17 | 5.9344 | 2.4569 | `iter_0028` |
| 37 | 07-09 | 1061 | 31 → 20 | 6.3436 | 2.3148 | `iter_0037` |
| 40 | 07-09 | 1064 | 34 → 25 | 5.7213 | 2.3424 | `iter_0040` (final live) |

The jump from 2.70 to 5.41 between iterations 10 and 22 came from
`cs_zscore(... / total_mv)`-style fundamental-size interactions, `ts_rank(neg(ts_rank(turnover_rate, 20)), 5)`,
and `cs_rank(ts_zscore(ts_argmin(log(pb), 3), 60))`. Iterations 23–41 refined
that population without changing its character; a mid-chain best of 2.7629
(referenced as "previous best" before iteration 22) came from the unlogged
variant runs 11–13.

[source: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260709_012147.md`]
[source: `china_a_share_alpha_output/factor_mining_loop/iter_0021_audit/final_audit.md`]

## The audit that ended the loop

On 2026-07-11 a batch audit re-evaluated every stored iteration library on one
shared panel (2021-06-01 → 2026-06-01, val from 2023-01-01, test from
2024-01-01) with one shared `_hold_backtest` (non-overlapping H-day rebalance,
decile long/short, 10 bps). This is the only comparison where all iterations
are measured with identical parameters, and it disagrees with the loop's own
promotion metric.

Same-standard 5-day hold results, iterations 24–41 (5D loop):

| Iter | Factors | Loop test Sharpe | Audit test Sharpe | Hold Sharpe | Hold return | Hold max DD |
|---:|---:|---:|---:|---:|---:|---:|
| 24 | 12 | 5.4695 | 5.663 | 2.117 | 59.9% | -15.3% |
| 25 | 14 | 5.4695 | 6.031 | 2.206 | 67.2% | -16.4% |
| **26** | 13 | 5.4695 | 5.447 | **2.491** | **73.7%** | **-12.0%** |
| 28 | 15 | 5.9344 | 5.592 | 2.245 | 64.9% | -17.4% |
| 33 | 21 | 5.0129 | 4.549 | 2.414 | 69.9% | -9.8% |
| 36 | 23 | 5.7696 | 5.465 | 2.369 | 61.3% | -12.5% |
| 37 | 17 | 6.3436 | 4.945 | 1.969 | 49.5% | -16.1% |
| 40 | 23 | 5.7213 | 4.552 | 1.634 | 39.1% | -18.0% |
| 41 | 26 | 4.7749 | 4.769 | 1.832 | 44.7% | -16.8% |

Live-candidate comparison (equal-weight ensemble of the stored library, not the
loop's top-N-by-val-IC combination):

| Candidate | Factors | Hold 5d | Hold 10d | Hold 20d |
|---|---:|---:|---:|---:|
| `iter_0026` | 13 | **2.491** (73.7%, -12.0%) | 1.990 (52.2%, -15.0%) | 1.981 (50.4%, -14.1%) |
| `iter_0028` | 15 | 2.245 (64.9%, -17.4%) | 2.146 (59.6%, -13.7%) | **2.382** (66.2%, -15.4%) |
| `iter_0040` (live) | 23 | 1.634 (39.1%, -18.0%) | 1.911 (48.2%, -14.7%) | 1.679 (40.6%, -17.4%) |

Three conclusions were recorded in `FINDINGS.md`:

1. The loop's promotion metric (daily overlapping forward-return Sharpe) and
   the realistic hold metric diverged after roughly iteration 32. Iteration 37
   has the highest loop Sharpe (6.34) but only 1.97 hold Sharpe; the promoted
   iteration 40 is the weakest of the late candidates on hold Sharpe.
2. Iteration 26 should have been the production library (or iteration 28 for a
   longer-horizon book), and the promotion rule should switch to realistic hold
   Sharpe.
3. The 10D and 20D branches were too small to conclude anything; 20D never
   passed a positive-train-Sharpe gate in 12 attempts.

Iteration 26 is the clearest example of the metric mismatch: its *library*
improved hold performance, but the loop's `top_n=10` selection by validation IC
plus EMA smoothing and the fixed `high_zscore_20` anchor produced exactly the
same combination metrics as iteration 24, so the loop recorded "no improvement"
and kept the older library.

[source: `china_a_share_alpha_output/batch_multihizon_audit/FINDINGS.md`]
[source: `china_a_share_alpha_output/batch_multihizon_audit/batch_audit_summary.csv`]
[source: `china_a_share_alpha_output/batch_multihizon_audit/5d/iter_0026/hold_ensemble_horizon.csv`]

## Late-loop collapse (iterations 42–46)

- Iterations 42, 43, 44, 45 were all rejected; 45's gates report
  `max_corr_ok: false (max corr = 1.0000)` with hold Sharpe 0.0 and a test
  Sharpe of 1.36 — the population had collapsed onto duplicated expressions.
- Iteration 46 started on 07-12 18:19 (seed library written, evolution agent
  snapshots present) but produced no merged/cleaned library and no report; the
  loop was never resumed afterwards.
- The 10D branch's `iter_0008` was aborted at the same time (evolution and
  merged library only).

[source: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260712_101949.md`]
[source: `china_a_share_alpha_output/factor_mining_loop/iter_0046/evolution/`]

## Horizon branches and the frozen baseline

10D loop (`factor_mining_loop_10d/state.json`): 7 iterations, only iterations 1
and 4 promoted. Best and final library is iteration 4 (5 factors including the
manual `high_zscore_20`): test Sharpe 3.9883, cost-adjusted 1.6895, hold Sharpe
2.7824, hold return 65.24%, max DD -9.28%. Iterations 5–7 reproduced the same
metrics without improving.

20D loop (`factor_mining_loop_20d/state.json`): 12 iterations. Iteration 5
produced the headline number (test Sharpe 7.1158, cost-adjusted 3.4714) but
with **negative train Sharpe (-0.4385)** and only 4 cleaned expressions, so it
was recorded as retained rather than a clean promotion; iterations 6–12 never
beat it. The final 20D library is 5 factors: `net_mf_amount`,
`ts_corr(cs_zscore(winsorize(cs_zscore(ts_argmax(winsorize(total_mv), 10)))), ts_argmin(ts_entropy(cs_rank(close), 5), 10), 10)`,
`ts_corr(cs_zscore(open), ts_argmin(ts_entropy(cs_rank(close), 5), 10), 10)`,
`winsorize(ts_kurt(ts_autocorr(if_positive(0.082, vwap), 20), 60))`, and
`cs_rank(ts_zscore(high, 20))`.

On 2026-07-13 both branches were re-evaluated against a frozen snapshot
(`snapshot_id 242f762f...`) and the result written back into state:
10D `dynamic_trim` Sharpe 3.8514 (annualized 84.38%, 5 factors, 570
observations); 20D `simple_hold` Sharpe 1.3067 (annualized 20.74%, 5 factors,
560 observations). The referenced receipt
`china_a_share_alpha_output/frozen_promotion_audit_20260713/promotion_audit_receipt.json`
does not exist on disk today.

[source: `china_a_share_alpha_output/factor_mining_loop_10d/state.json`]
[source: `china_a_share_alpha_output/factor_mining_loop_20d/state.json`]

## Global factor ranking

The last factor artifact produced was the 2026-07-24/27 cross-run ranking:
104 source files, 3,646 candidate rows, 1,677 unique expressions, top-100
threshold test Sharpe ≥ 2.887. The most repeated structures in that population
are 5-day reversal `neg(cs_rank(ts_mean(return, 5)))` (16 sources) and raw
`turnover_rate` (21 sources); the most horizon-robust evolved factor is
`cs_zscore(div(sub(greater(eps, neg(0.033)), sub(ocfps, turnover_rate)), winsorize(total_mv)))`
with test Sharpe 3.07 / 4.79 / 6.47 at 5 / 10 / 20 days.

[source: `wiki/top100_factors_by_sharpe.md`]
[source: `china_a_share_alpha_output/factor_mining_loop/multihizon_audit_pre_iter24/multihizon_audit.md`]

## Lessons worth keeping

1. **Optimize the metric you actually trade.** Daily overlapping Sharpe kept
   rising while realistic hold Sharpe fell; the loop needs promotion on the
   hold metric (or at minimum both).
2. **A strong seed library suppresses novelty.** Iteration 2 reproduced
   iteration 1 bit-for-bit; later iterations re-derived the same structures
   until the population collapsed to correlation 1.0.
3. **Aggressive cleaning plus top-N-by-val-IC selection hides library-level
   improvements.** The best library (iteration 26) never reached the live slot
   because the selection step reproduced the previous combination exactly.
4. **Regime dependence was never solved.** All early 5D results and every 20D
   iteration had negative train-period Sharpe; the alpha lives in 2023+.
5. **Batch re-auditing is what caught the regression**, and it was run by hand
   once, not wired into the loop.

## Open items

- The 5D loop's own `state.json` and `live_library.csv` are gone from
  `china_a_share_alpha_output/factor_mining_loop/`; only
  `live_library_iter40_backup_20260711.csv` and the `iter_0046` seed copy
  remain. Reconstructing the final live library requires recomputing
  `iter_0040/combined_library.csv`.
- The loop runner that produced `state_schema_version: 2` (with `gates`,
  `improved`, `promotion_baseline`, hold backtest, and frozen-audit
  reconciliation) is not in the repository; the checked-in
  `china_a_share_alpha/scripts/run_factor_mining_loop.py` still promotes on
  test Sharpe / cost-adjusted return alone.
- The audit scripts referenced by `FINDINGS.md`
  (`china_a_share_alpha/scripts/batch_multihizon_audit.py`,
  `run_multihizon_audit.py`) are also missing, so the hold-Sharpe numbers above
  are reproducible only from the stored CSVs, not by re-running.
- Iterations 3–45 have no `OPERATION_LOG.md` entries (superseded by this note
  and the 2026-09-22 log entry).

## References

- [source: `china_a_share_alpha_output/batch_multihizon_audit/FINDINGS.md`]
- [source: `china_a_share_alpha_output/batch_multihizon_audit/batch_audit_summary.md`]
- [source: `china_a_share_alpha_output/factor_mining_loop/iter_0021_audit/final_audit.md`]
- [source: `china_a_share_alpha_output/factor_mining_loop/multihizon_audit_pre_iter24/multihizon_audit.md`]
- [source: `wiki/top100_factors_by_sharpe.md`]
- [source: `wiki/factor_mining_loop_iteration_1.md`]
- [source: `wiki/factor_mining_loop_iteration_2.md`]
- [source: `LOOP.md`]
