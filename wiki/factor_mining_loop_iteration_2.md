# Factor Mining Loop — Iteration 2 Chain-of-Thought

> Date: 2026-07-04
> Source run: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260704_064238.md`

## Trigger

Continue the continuous factor-mining loop from iteration 1. The live library
from iteration 1 was promoted because it achieved test Sharpe 1.628 / cost-adj
24.75%, even though train Sharpe was negative. The goal of iteration 2 is to
seed from that live library and see whether the loop can either (a) improve the
ensemble or (b) produce a more diverse set of factors.

## Observations

- **Evolution**: seed 1002, pop 25, gen 8. Because the population was seeded
  with the live library, the search space was biased toward the already-good
  structures.
- **Merge**: 23 unique expressions after merging the new leaderboard with the
  live library (up from 21 in iteration 1).
- **Clean**: 5 expressions survived validation-aware cleaning (up from 2 in
  iteration 1). Diversity improved.
- **Combine**: equal-weight + EMA(span=10) on the top val-IC cleaned factors +
  `high_zscore_20`.
- **Metrics**: test Sharpe 1.6283, cost-adj return 24.75% — identical to
  iteration 1 within numerical precision.

## Decision

- **Did not promote** the new library. The test Sharpe did not improve, so the
  existing live library is retained.
- The identical metrics suggest the top-ranked factors in iteration 2 are the
  same (or functionally equivalent to) the factors already in the live library.
  The extra 3 cleaned expressions did not add incremental out-of-sample value.

## New knowledge

1. **Seeding with a strong live library accelerates convergence but reduces
   novelty.** The search quickly rediscovers the same high-val-IC structures.
2. **Diversity ≠ improvement.** More cleaned factors does not automatically
   translate into a better ensemble if the additional factors are redundant or
   low signal.
3. **The 1.628 Sharpe result appears to be a local optimum / ceiling for the
   current config.** Two independent seeds hit the same number.
4. **The negative train Sharpe persists.** Both iterations selected factors
   that perform well only in the 2023-2026 window, confirming regime
   dependence.

## Chain-of-thought for next iteration

- To break the local optimum, we need either:
  - a larger mutation radius / stronger novelty pressure in evolution;
  - a different objective during cleaning (e.g., require positive train Sharpe
    and low correlation to existing live-library factors);
  - a forced diversification step that rejects candidates too similar to the
    live library.
- Before promoting any future library, require:
  1. `train_sharpe > 0`;
  2. `n_cleaned >= 5`;
  3. pairwise correlation between any new factor and live-library factors
     `< 0.7`.
- If the next iteration still cannot improve, consider expanding the data
  window, adding new operators, or running a separate "exploration" loop with
  no seed library.

## Anomalies

- The combination output was bit-for-bit identical between iterations 1 and 2,
  despite 5 cleaned expressions in iteration 2. This implies the top-10 sort by
  val-IC selected exactly the same factors. We should log which factors are
  actually used in the combination to confirm.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
- [source: `wiki/factor_mining_loop_iteration_1.md`]
