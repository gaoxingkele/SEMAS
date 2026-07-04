# Factor Mining Loop — Iteration 3 Chain-of-Thought

> Date: 2026-07-04
> Source run: `china_a_share_alpha_output/factor_mining_loop/loop_report_20260704_071040.md`

## Trigger

After adding hard promotion gates to the loop runner, run the first iteration
with the new gates to verify behavior and record any new knowledge.

## New gates

- `min_train_sharpe_gate: 0.0` — train Sharpe must be positive.
- `min_cleaned_gate: 5` — at least 5 factors must survive cleaning.
- `max_selection_correlation_gate: 0.7` — max absolute pairwise correlation
  among selected factors must be ≤ 0.7.

## Observations

- **Evolution**: seed 1003, pop 25, gen 8, seeded with iteration 1 live library.
- **Merge**: 22 unique expressions (string-level deduplication).
- **Clean**: 6 expressions survived (up from 5 in iteration 2).
- **Train Sharpe**: 0.5927 — **positive for the first time**.
- **Test Sharpe**: 1.5771, cost-adj return 22.65% — slightly below the best.
- **Max selection correlation**: **1.0000** — gate failed.

## Why did correlation fail?

The selected factors contained semantic duplicates that survived string-level
deduplication:

- `cs_zscore(div(sub(greater(eps, -0.033), sub(ocfps, turnover_rate)), winsorize(total_mv)))`
- `cs_zscore(div(sub(greater(eps, neg(0.033)), sub(ocfps, turnover_rate)), winsorize(total_mv)))`

These two expressions are identical in value but different in syntax. Similar
pairs existed for the volume-rank factor and for `high_zscore_20` vs. an
evolved clone. The correlation matrix therefore contained 1.0 entries.

## Decision

- **Did not promote** because:
  1. Test Sharpe did not improve over the current best (1.577 vs 1.628).
  2. The max-correlation gate failed (1.0 > 0.7).
- The existing live library is retained.

## New knowledge

1. **String-level deduplication is insufficient.** The mutator can produce
   syntactically different but semantically identical expressions (e.g. `-x`
   vs `neg(x)`). A semantic deduplication step based on evaluated factor
   correlation is needed.
2. **Train Sharpe can flip positive with more search.** Iteration 3 found a
   candidate library with positive train Sharpe, suggesting the negative train
   result was not universal.
3. **The correlation gate is valuable.** Without it, the ensemble would have
   overweighted a small number of unique signals.
4. **Promotion now requires all three gates + improvement.** This makes the
   loop more conservative and less likely to promote regime-dependent or
   degenerate ensembles.

## Chain-of-thought for next iteration

- Add a semantic deduplication step after cleaning: compute pairwise
  Spearman correlation of cleaned factor values and drop one from any pair
  with `|rho| > 0.95`.
- Alternatively, deduplicate the selected top-N factors before combination.
- Then run iteration 4 and expect a cleaner ensemble that may pass all gates.

## References

- [source: `china_a_share_alpha/scripts/run_factor_mining_loop.py`]
- [source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
- [source: `wiki/factor_mining_loop_iteration_2.md`]
