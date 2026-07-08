---
date: 2026-07-06
tags: [factor-mining-loop, run-note, iteration-21, final-audit, production]
sources:
  - ../china_a_share_alpha/scripts/run_final_audit.py
  - ../china_a_share_alpha_output/factor_mining_loop/iter_0021_audit/final_audit.json
related:
  - factor_mining_loop_iteration_20.md
  - factor_mining_loop_index.md
  - index.md
  - log.md
---

# Factor Mining Loop — Iteration 21 Final Production Audit

## Trigger

After completing the 10-iteration roadmap (iterations 12–21), perform a final
production audit of the promoted live library from iteration 12.

## Setup

- Ran `china_a_share_alpha/scripts/run_final_audit.py` on the live library.
- Evaluated cost robustness at 10, 20, and 30 bps one-way transaction costs.
- Computed per-year test performance, average daily coverage, and sector
  neutrality.

## Final Library

The live library retained through iterations 13–21 is the 10-factor ensemble
promoted in iteration 12.

## Audit Results

### Overall test performance

| Metric | Value |
|---|---|
| Test Sharpe | **2.7629** |
| Test annualized return | 40.78% |
| Test cost-adjusted return (10 bps) | 32.47% |
| Test max drawdown | -7.50% |
| Test IC | 0.0193 |
| Test turnover | 0.07% |
| Average daily coverage | 231 stocks |
| Sector neutrality \|Spearman corr\| | 0.0011 |

### Cost robustness

| One-way cost | Sharpe | Cost-adj return | Max drawdown |
|---|---|---|---|
| 10 bps | 2.7629 | 32.47% | -7.50% |
| 20 bps | 2.7629 | 24.15% | -7.50% |
| 30 bps | 2.7629 | 15.84% | -7.50% |

### Per-year test performance

| Year | Sharpe | Ann. return | Cost-adj return | Max drawdown | IC |
|---|---|---|---|---|---|
| 2024 | 2.1268 | 34.00% | 25.57% | -6.10% | 0.0148 |
| 2025 | 2.8328 | 38.74% | 30.48% | -7.50% | 0.0194 |
| 2026 | 3.7487 | 57.56% | 49.54% | -4.11% | 0.0265 |

## Decision

- **Production-ready baseline confirmed.** The iteration-12 library passes the
  audit across costs and years.
- No further promotion; the library remains the best discovered in the
  12–21 roadmap.

## Roadmap Synthesis

| Iteration | Idea | Promoted | Key Lesson |
|---|---|---|---|
| 12 | Multi-horizon 5d/10d | **YES** | Best source of improvement; retained. |
| 13 | Cross-market transfer | No | CSI500/1000 factors do not transfer to CSI300. |
| 14 | High-order operators | No | Grammar expanded, but one seed did not improve. |
| 15 | Money-flow data fusion | No | New fields useful, seeds did not generalize. |
| 16 | Ensemble weight methods | No | Equal weight beats IC/Sharpe/ridge on this set. |
| 17 | Volatility regime switching | No | Simple regime switch overfits or collapses. |
| 18 | LLM critic generation | No | LLM expressions are syntactically valid but weak. |
| 19 | Anti-correlation search | No | Low correlation alone is not alpha. |
| 20 | 20 bps cost-aware evolution | No | Lower turnover, but not better at 10 bps. |
| 21 | Final audit | N/A | Confirmed production baseline. |

## References

- [source: `china_a_share_alpha/scripts/run_final_audit.py`]
- [source: `wiki/factor_mining_loop_iteration_12.md`]
