---
date: 2026-07-06
tags: [index, meta, wiki]
source_count: 0
---

# SEMAS Wiki Index

This is the top-level index for the SEMAS project wiki. It follows the
personal-knowledge-base pattern described in
[Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):
raw sources are immutable, the wiki is a persistent compounding artifact, and
each ingest or iteration updates cross-references, entity pages, and the
chronological log.

## Active Research Threads

| Page | Summary | Last Updated |
|---|---|---|
| [Factor Evolution Complete History 1–114](factor_evolution_complete_history_1_114.md) | Canonical per-iteration ledger, promotion chain, DGM/RSI phases, paired results, and current iter-109 live state. | 2026-10-07 |
| [RSI Phase-2 Paired Selection](factor_rsi_phase2_paired_selection_20260921.md) | Three-seed parent/child controls gate reproductive eligibility. | 2026-09-21 |
| [RSI Phase-1 Causal Verifier](factor_rsi_phase1_causal_verifier_20260920.md) | Hard-gated parent eligibility, identity-bound receipts, and one-field causal credit. | 2026-09-20 |
| [DGM RSI for Factor Mining](factor_dgm_rsi_factor_mining_20260918.md) | True Recursive Self-Improvement: policy archive + empirical hold eval. | 2026-09-18 |
| [RSI anti-collapse islands](factor_dgm_rsi_anti_collapse_islands_20260920.md) | Four orthogonal surfaces + single-field mutate; frozen examiner; archive v2 eligibility. | 2026-09-20 |
| [RSI = Recursive Self-Improvement (correction)](factor_rsi_means_recursive_self_improvement_20260918.md) | Terminology correction: not Relative Strength Index. | 2026-09-18 |
| [Modern RSI Seeds + Graft Promotion](factor_rsi_modern_seeds_20260917.md) | *(misnamed / rolled back)* Relative Strength Index collateral. | 2026-09-17 |
| [Ablation A2 AST Off](factor_ablation_a2_ast_20260917.md) | Single-seed AST-off ablation matched B0 hold (2.056). | 2026-09-17 |
| [Ablation A3 DAG Off](factor_ablation_a3_dag_20260917.md) | Single-seed DAG-off ablation underperformed (1.927). | 2026-09-17 |
| [Factor Score-Bucket and Maximum-Horizon Audit](factor_score_bucket_max_horizon_audit_20260913.md) | Individual-stock 0--100 score calibration plus separate realized-return and maximum-favorable-excursion horizon rankings. | 2026-09-13 |
| [Recent All-Expression Audit](factor_recent_all_expression_audit_20260913.md) | Complete 119-expression, 6,426-row T+1 matrix with strict 2025--2026 validity gates. | 2026-09-13 |
| [Recent-Regime Factor Matching](factor_recent_regime_matching_20260911.md) | 2025--2026 walk-forward matching, factor-rank reversal diagnosis, and research-only MA20 entry gate. | 2026-09-11 |
| [CCF-A Three-Direction Paper Track](factor_ccf_a_three_direction_paper_20260904.md) | KDD-targeted ARA: synergy objective + AST gates + DAG neighborhood evolution. | 2026-09-04 |
| [Stock-to-Factor Matching Evolution](factor_stock_matching_evolution_20260831.md) | Twelve-round train/validation evolution whose frozen test rejected a concentrated, non-generalizing match policy. | 2026-08-31 |
| [T+1 Board-Aware Factor Audit](factor_t1_board_exit_full_library_audit_20260831.md) | Full-library 5d/10d/20d audit with T+1, board thresholds, queued limit exits, and forced expiry. | 2026-08-31 |
| [Factor Repository Hygiene](factor_repository_hygiene_20260828.md) | Reconcile machine state, compact receipts, and externally valid factor rankings. | 2026-08-28 |
| [Factor Mining Loop Index](factor_mining_loop_index.md) | Continuous alpha-factor discovery loop for China A-shares. | 2026-07-06 |
| [Iteration 10 Live-Library Audit](factor_mining_loop_audit_iter10.md) | Coverage and sector-neutrality analysis of the promoted 12-factor ensemble. | 2026-07-05 |
| [Multi-Horizon Audit](factor_mining_loop_multihizon_audit.md) | 5d / 10d / 20d horizon test of the final 10-factor live library. | 2026-07-06 |
| [Frozen Promotion Audit](factor_promotion_frozen_audit_20260713.md) | Checksum-verified 5d / 10d / 20d live-library audit and guarded state reconciliation. | 2026-07-13 |
| [SEMAS Evolution Ideas](semas_evolution_ideas.md) | Broader evolution experiments, including validation weighting, iterative evolution, and the factor-mining loop. | 2026-07-06 |

## Factor Mining Loop Run Notes

- [20d Position-Schedule Evolution](factor_20d_position_schedule_evolution_20260714.md):
  frozen ten-bin execution search selected static sizing after dynamic schedules
  failed the later audit regime (2026-07-14).
- [20d Factor / MA Correlation](factor_20d_ma_correlation_20260714.md): stable
  MA5/10/20 exposure in the frozen library, with component-level attribution
  (2026-07-14).
- [20d MA-Neutralized Alpha](factor_20d_ma_neutralized_alpha_20260714.md):
  same-sample IC, layered returns, and costed hold comparison after removing
  linear MA5/10/20 exposure (2026-07-14).
- [No-Lookahead Horizon Audit](factor_horizon_no_lookahead_audit_20260716.md):
  unified 5d/10d/20d review and production priority decision (2026-07-16).
- [Audited Stock Selection](factor_audited_stock_selection_20260529.md): complete
  frozen 5d/10d cohorts as of 2026-05-29 (exported 2026-07-16).

| Iteration | Date | Test Sharpe | Promoted | Summary |
|---|---|---|---|---|
| [Iteration 1](factor_mining_loop_iteration_1.md) | 2026-07-04 | 1.63 | YES | Empty seed, 3-factor ensemble, negative train Sharpe. |
| [Iteration 2](factor_mining_loop_iteration_2.md) | 2026-07-04 | 1.63 | NO | Seeded with iter 1 library; no improvement. |
| [Iteration 3](factor_mining_loop_iteration_3.md) | 2026-07-04 | 1.58 | NO | First gated run; positive train Sharpe but correlation gate failed. |
| [Iteration 4](factor_mining_loop_iteration_4.md) | 2026-07-04 | 2.11 | YES | Added semantic dedup; all gates passed. |
| [Iteration 5](factor_mining_loop_iteration_5.md) | 2026-07-04 | 2.20 | YES | Incremental improvement; independently verified on Tushare data. |
| [Iteration 6](factor_mining_loop_iteration_6.md) | 2026-07-05 | 1.10 | NO | Strong train Sharpe but lower test Sharpe; includes live-library audit. |
| [Iteration 7](factor_mining_loop_iteration_7.md) | 2026-07-05 | 1.24 | NO | Empty-seed exploration over-cleaned; recommended live-seed for iter 8. |
| [Iteration 8](factor_mining_loop_iteration_8.md) | 2026-07-05 | 2.40 | NO | Live-seed with larger budget; high Sharpe but failed correlation gate. |
| [Iteration 9](factor_mining_loop_iteration_9.md) | 2026-07-05 | 0.50 | NO | Tightened dedup + risk-parity weights; negative test cost-adj return. |
| [Iteration 10](factor_mining_loop_iteration_10.md) | 2026-07-05 | **2.70** | **YES** | Greedy correlation-aware selection; new best, all gates passed, verified. |
| [Iteration 11](factor_mining_loop_iteration_11.md) | 2026-07-05 | 2.70 (20 bps) | N/A | Stress-test validation; cost-adj 23.17% at 20 bps. |
| [Iteration 12](factor_mining_loop_iteration_12.md) | 2026-07-05 | **2.76** | **YES** | Multi-horizon 5d/10d evolution; new best. |
| [Iteration 13](factor_mining_loop_iteration_13.md) | 2026-07-05 | 1.84 | NO | Cross-market transfer did not improve on CSI300. |
| [Iteration 14](factor_mining_loop_iteration_14.md) | 2026-07-06 | 2.41 | NO | High-order operators added; not promoted. |
| [Iteration 15](factor_mining_loop_iteration_15.md) | 2026-07-06 | 2.02 | NO | Money-flow fields and seed library added; not promoted. |
| [Iteration 16](factor_mining_loop_iteration_16.md) | 2026-07-06 | 2.76 | NO | Tested equal/ic/sharpe/risk-parity/ridge; equal remains best. |
| [Iteration 17](factor_mining_loop_iteration_17.md) | 2026-07-06 | 2.76 | NO | Volatility-regime switching did not improve equal weight. |
| [Iteration 18](factor_mining_loop_iteration_18.md) | 2026-07-06 | 2.31 | NO | LLM critic generated weak factors; did not promote. |
| [Iteration 19](factor_mining_loop_iteration_19.md) | 2026-07-06 | 1.14 | NO | Anti-correlation search added noise; did not promote. |
| [Iteration 20](factor_mining_loop_iteration_20.md) | 2026-07-06 | 2.21 | NO | 20 bps cost-aware evolution; viable but not promoted. |
| [Iteration 21](factor_mining_loop_iteration_21.md) | 2026-07-06 | 2.76 | N/A | Final production audit of iteration-12 live library. |
| [Iteration 22](factor_mining_loop_iteration_22.md) | 2026-07-07 | 1.98 (20d hold) | YES | 20d forward evolution; promoted `live_library_20d.csv`. |

## Key Entities

- **Live library**: `china_a_share_alpha_output/factor_mining_loop/live_library.csv`
- **Loop runner**: `china_a_share_alpha/scripts/run_factor_mining_loop.py`
- **Combination script**: `china_a_share_alpha/scripts/run_factor_combination.py`
- **Multi-horizon audit script**: `china_a_share_alpha/scripts/run_multihizon_audit.py`
- **Loop design**: [../LOOP.md](../LOOP.md)
- **Project state**: `china_a_share_alpha_output/factor_mining_loop/STATE.md`

## Sources

- [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [loop-engineering (cloned to external/loop-engineering)](../external/loop-engineering)
- Local design docs: [SEMAS_ARA_Architecture.md](../SEMAS_ARA_Architecture.md), [SEMAS_SIA_Integration_Design.md](../SEMAS_SIA_Integration_Design.md)

## Logs

See [log.md](log.md) for a chronological record of wiki updates and loop runs.

## External Factor Utility

- [Sharpe-first external factor utility ranking](factor_utility_sharpe_ranking_20260724.md): full frozen-candidate ordering with observation and cross-year stability flags (2026-07-24).
- [Permanent drawdown-stop stress test](factor_permanent_drawdown_stop_20260724.md): all-factor -20% permanent-stop analysis (2026-07-24).
- [Daily-ranked drawdown-stop re-entry](factor_ranked_reentry_drawdown_20260724.md): all-factor delayed-Sharpe ranking with 5/10/20-day cooldowns (2026-07-24).
- [Daily TOP100 factor membership](factor_daily_top100_20260725.md): auditable fixed-size daily selection list (2026-07-25).
- [TOP100 20-day mean-rank correction](factor_top100_rank_mean_20260725.md): corrected daily selection criterion (2026-07-25).
- [Current TOP100 60-day rolling-Sharpe rule](factor_top100_rolling_sharpe_60d_20260725.md): active daily selection definition (2026-07-25).
- [Latest TOP100 snapshot](factor_top100_latest_snapshot_20260726.md): ordered current daily membership (2026-07-26).
- [TOP100 multi-dimensional A-share research](top100_multidim_a_share_research_20260727.md): 2025 selection and 2026 frozen dynamic portfolio audit (2026-07-27).
- [TOP100 factor explanations](factor_top100_explained_20260726.md): all current factors with expression-structure descriptions (2026-07-26).

## Mingli Research

- [Mingli Book Profiles and Hour Calibration](mingli_book_profiles_hour_calibration.md): inspectable book-level AHP profiles and evidence-bounded candidate-hour ranking (2026-07-13).
