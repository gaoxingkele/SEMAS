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
| [Factor Mining Loop Index](factor_mining_loop_index.md) | Continuous alpha-factor discovery loop for China A-shares. | 2026-07-06 |
| [Iteration 10 Live-Library Audit](factor_mining_loop_audit_iter10.md) | Coverage and sector-neutrality analysis of the promoted 12-factor ensemble. | 2026-07-05 |
| [Multi-Horizon Audit](factor_mining_loop_multihizon_audit.md) | 5d / 10d / 20d horizon test of the final 10-factor live library. | 2026-07-06 |
| [SEMAS Evolution Ideas](semas_evolution_ideas.md) | Broader evolution experiments, including validation weighting, iterative evolution, and the factor-mining loop. | 2026-07-06 |

## Factor Mining Loop Run Notes

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

## Mingli Research

- [Mingli Book Profiles and Hour Calibration](mingli_book_profiles_hour_calibration.md): inspectable book-level AHP profiles and evidence-bounded candidate-hour ranking (2026-07-13).
