# China A-Share Alpha Evolver

> An evolvable, self-improving scaffold for China A-share alpha factor mining,
> built on the SEMAS framework. It is designed to work with **Qlib** data
> format/operators, while also supporting **TA-Lib** and custom formulaic
> alpha libraries such as **WorldQuant 101**.

## What it does

```text
Raw OHLCV panel (Qlib / CSV / synthetic)
       │
       ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Factor Generator │────▶│ Factor Evaluator │────▶│   SEMAS Mutator  │
│  (expression)    │     │  (IC / ICIR /    │     │ (seed / GP /     │
│                  │     │   long-short)    │     │  subtree opt)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                       Factor report (JSON/Markdown)
```

The package turns a mathematical expression (factor) into a SEMAS `AgentGenome`,
evolves it to maximize predictive power, and outputs an auditable factor report.

## Install

Core dependencies only (pandas/numpy):

```bash
pip install -e ./china_a_share_alpha
```

With Qlib and TA-Lib backends:

```bash
pip install -e "./china_a_share_alpha[all]"
```

> `pyqlib` and `TA-Lib` are optional because they can be hard to install on
> some platforms. The scaffold ships with synthetic data and pure-Pandas
> operators so it runs out of the box.

## Quick start

```bash
python -m china_a_share_alpha.demo
```

Run a full evolution experiment with report generation:

```bash
python -m china_a_share_alpha.run_factor_mining china_a_share_alpha/examples/sample_config.yaml
```

Run the continuous factor mining loop:

```bash
python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml
```

Evolve a multi-factor portfolio from a factor library:

```bash
python -m china_a_share_alpha.run_portfolio_evolution china_a_share_alpha/examples/portfolio_config.yaml
```

Run tests:

```bash
python -m pytest tests/ -q
```

Run a reproducible promotion audit by freezing the data panel first, then
evaluating all live libraries from that immutable snapshot:

```bash
python -m china_a_share_alpha.scripts.run_frozen_promotion_audit freeze \
    china_a_share_alpha/examples/enhanced_loop_config_val.yaml \
    --snapshot-dir china_a_share_alpha_output/frozen_promotion_snapshot

python -m china_a_share_alpha.scripts.run_frozen_promotion_audit audit \
    --snapshot-dir china_a_share_alpha_output/frozen_promotion_snapshot \
    --audit-config china_a_share_alpha/examples/frozen_promotion_audit.yaml \
    --output-dir china_a_share_alpha_output/frozen_promotion_audit
```

The audit verifies snapshot checksums and writes a JSON/Markdown receipt. It is
read-only. State reconciliation is a separate command and checks that both the
library hash and state iteration still match the receipt before writing:

```bash
python -m china_a_share_alpha.scripts.run_frozen_promotion_audit \
    reconcile-state \
    --receipt china_a_share_alpha_output/frozen_promotion_audit/promotion_audit_receipt.json \
    --apply
```

## Architecture

- `data/` — Qlib loader with train/test split, synthetic A-share panel with
  sector/market-cap, TA-Lib wrappers, Alpha101 baseline formulas.
- `factor/` — Factor expression tree, operator library (`ts_*`, `cs_*`), and
  a DSL parser.
- `evaluator/` — IC, RankIC, ICIR, turnover, sector/market-cap neutralization.
- `backtest/` — Quantile long-short backtest with transaction costs.
- `evolution/` — `FactorMutator` (seed/GP/crossover) and `LLMFactorMutator`
  for LLM-driven expression generation.
- `loop/` — `FactorPopulation` continuous mining loop, `PortfolioPopulation`
  multi-factor weight evolution, and alpha decay monitoring.
- `report/` — JSON/Markdown factor report generator.
- `scripts/` — Qlib data downloader and sector-template generator.
- `run_factor_mining.py` — High-level single-factor evolution runner.
- `run_factor_loop.py` — Continuous population-based factor mining loop.
- `run_portfolio_evolution.py` — Multi-factor portfolio weight evolution.
- `demo.py` — Minimal runnable demo.

## Key features

| Feature | Status | Notes |
|---|---|---|
| Train / test split | ✅ | `load_data()` returns `(train, test)`; OOS IC reported |
| Neutralization | ✅ | Sector / market-cap neutralization stubs wired in |
| Transaction costs | ✅ | Long-short backtest with turnover-based cost |
| Deterministic seed mutator | ✅ | Fast demo/CI |
| Open GP mutator | ✅ | `mutator: gp` for grammar-based random search |
| LLM-driven mutator | ✅ | `mutator: llm` via SEMAS LLM client |
| Report generator | ✅ | JSON + Markdown reports |
| Real Qlib data | ✅ | Optional loader + downloader script |
| Multi-factor portfolio evolution | ✅ | `run_portfolio_evolution.py` |
| Alpha decay monitoring | ✅ | Tracks IC slope and warns on decay |

## Continuous factor mining loop

The loop runner seeds a population of expressions, evaluates them on
train/test sets, breeds elites via mutation and crossover, and stops on
convergence or `max_generations`.

```bash
python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml
```

Outputs:

- `factor_loop_leaderboard.csv` — top factors by test IC.
- `factor_loop_history.json` — per-generation best/mean test IC.
- `factor_report_*.json` / `factor_report_*.md` — full report on the best factor.

Key loop parameters:

```yaml
population_size: 16
max_generations: 8
patience: 3                  # early stop if test IC not improving
elite_fraction: 0.25
crossover_fraction: 0.25
mutator: gp                  # "seed" | "gp"
```

### Frozen-snapshot 5D / 10D campaign

Use the dual-horizon campaign to run a durable 30-round experiment for each
horizon. It recomputes each fold's forward-return label inside that fold, uses
validation metrics to decide the next research seed, and keeps test metrics out
of the selection decision.

```bash
python -m china_a_share_alpha.scripts.run_dual_horizon_campaign \
  china_a_share_alpha/examples/dual_horizon_30round_campaign.yaml
```

The campaign writes separate `5d/` and `10d/` checkpoints under its output
directory, plus a single `campaign_history.json` for progress monitoring.

## Multi-factor portfolio evolution

After running the factor loop, use the top expressions as a library and evolve
weighted portfolios:

```bash
python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml
python -m china_a_share_alpha.run_portfolio_evolution china_a_share_alpha/examples/portfolio_config.yaml
```

The portfolio runner treats each portfolio as a weighted, z-scored combination
of factors and maximizes out-of-sample Sharpe ratio.

## Tushare historical backtest comparison

Run a real-data 5-year backtest comparing single factors and combined factors
on CSI300 constituents:

```bash
export TUSHARE_TOKEN=your_token
python -m china_a_share_alpha.scripts.run_tushare_backtest \
    --start-date 20210601 --end-date 20260601 --split-date 20240101
```

Outputs:

- `factor_comparison.csv` — IC, ICIR, Sharpe, max drawdown, turnover for each
  single and combined factor.
- `factor_comparison_report.md` — data-driven interpretation of results.
- `summary.json` — best factor by Sharpe/IC and learned IC weights.

Single factors cover momentum, short-term reversal, volume-price correlation,
low-volatility, PB value, and liquidity. Combinations include a rule-based
multi-timeframe factor, an equal-weighted multi-style factor, and an
IC-weighted composite trained on the in-sample period.

## LLM-driven factor mutation

Set `mutator: llm` in any factor config to let a language model propose new
expressions. The prompt uses the same DSL (`ts_*`, `cs_*`, arithmetic). If the
LLM response is not parseable, the mutator falls back to random GP mutation.

Supported LLM backends are configured via SEMAS environment variables:
`SEMAS_LLM_API_KEY`, `SEMAS_LLM_MODEL`, `SEMAS_LLM_BASE_URL` (or OpenAI / Kimi /
DeepSeek equivalents). Without an API key, the SEMAS stub client is used and
falls back to GP.

## Alpha decay monitoring

The loop tracks per-generation best test IC and computes a rolling slope. When
the slope turns negative, it prints a decay warning so you can trigger
re-evolution or retire the factor.

## 20-day position-schedule evolution

The 20-day execution optimizer searches monotone long-position multipliers in
10-percentile rank bins and 10% weight increments. It charges 10 bps on actual
target-weight changes and enforces that positions formed on day `d` earn
returns beginning on day `d+1`.

```bash
python -m china_a_share_alpha.scripts.evolve_20d_position_schedule \
  china_a_share_alpha/examples/position_schedule_evolution_20d_recovery.yaml
```

The frozen 2026-07-14 review selected the static schedule
`[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`; no dynamic schedule
passed the 2024-2025 audit fold. The machine-readable selection is in
`examples/position_schedule_20d_best.yaml`. A static winner is an explicit
rollback result, not an omitted optimization outcome.

To measure whether the 20d library duplicates moving-average information, run
the frozen cross-sectional correlation audit:

```bash
python -m china_a_share_alpha.scripts.analyze_factor_ma_correlation \
  --snapshot-dir china_a_share_alpha_output/frozen_promotion_snapshot_20260713 \
  --library china_a_share_alpha_output/factor_mining_loop_20d/live_library.csv \
  --output-dir china_a_share_alpha_output/factor_ma_correlation_20d_20260714
```

The audit correlates each factor and the ensemble with
`close / trailing_MA(close, n) - 1` using daily cross-sectional Spearman
statistics. Raw MA price levels are intentionally not used because their scale
would make cross-stock comparisons misleading.

To test the alpha remaining after removing MA exposure:

```bash
python -m china_a_share_alpha.scripts.analyze_ma_neutralized_alpha \
  --snapshot-dir china_a_share_alpha_output/frozen_promotion_snapshot_20260713 \
  --library china_a_share_alpha_output/factor_mining_loop_20d/live_library.csv \
  --output-dir china_a_share_alpha_output/ma_neutralized_alpha_20d_20260714
```

This jointly regresses the ensemble on standardized MA5/10/20 deviations in
each daily cross-section. It compares same-sample 20d rank IC, five-layer
forward returns, and a next-day, 10 bps hold backtest before and after
neutralization.

## No-lookahead horizon audit

Audit the live 5d, 10d, and 20d libraries under the same cohort, cost, history,
and next-day execution contract:

```bash
python -m china_a_share_alpha.scripts.run_no_lookahead_horizon_audit \
  --snapshot-dir china_a_share_alpha_output/frozen_promotion_snapshot_20260713 \
  --library-5d china_a_share_alpha_output/factor_mining_loop/live_library.csv \
  --library-10d china_a_share_alpha_output/factor_mining_loop_10d/live_library.csv \
  --library-20d china_a_share_alpha_output/factor_mining_loop_20d/live_library.csv \
  --output-dir china_a_share_alpha_output/no_lookahead_horizon_audit_20260716
```

The audit computes signals on continuous historical data, then scores only the
requested fold. Its frozen result makes 5d dynamic trim the primary contract,
10d static hold a regime-sensitive secondary contract, and 20d research-only.
See `examples/horizon_priority_20260716.yaml` for the machine-readable decision.

Export the complete audited stock cohorts from the frozen snapshot:

```bash
python -m china_a_share_alpha.scripts.export_audited_horizon_picks \
  --snapshot-dir china_a_share_alpha_output/frozen_promotion_snapshot_20260713 \
  --library-5d china_a_share_alpha_output/factor_mining_loop/live_library.csv \
  --library-10d china_a_share_alpha_output/factor_mining_loop_10d/live_library.csv \
  --output-dir china_a_share_alpha_output/audited_stock_selection_20260529
```

The export includes complete rebalance cohorts, current positive positions,
fixed short cohorts, and a combined long union tagged as 5d/10d consensus,
5d-primary, or 10d-secondary. It does not invent an unaudited cross-strategy
capital weight.

## T+1 board-aware full-library audit

Audit every canonical live/combined/research factor library under a long-only
T+1 execution contract:

```bash
python -m china_a_share_alpha.scripts.run_t1_full_library_audit \
  china_a_share_alpha/examples/t1_full_library_audit.yaml
```

Signals formed at D enter at D+1 open. The purchase day is excluded from the
holding count, so 5d/10d/20d expiry occurs at D+6/D+11/D+21 close. Close-based
stop and trailing-profit signals execute at the next sellable open; locked
limit-down securities remain queued. ST names are excluded. Main-board,
STAR/ChiNext, and BSE policies use progressively wider loss, profit-activation,
trailing-drawdown, and price-limit thresholds. The runner deduplicates identical
libraries, evaluates every unique expression once on continuous history, and
reports unavailable universes instead of fabricating index or ETF results.

## Stock-to-factor-library matching evolution

Evolve a per-stock factor-library mixture while keeping the final test fold
closed during selection:

```bash
python -m china_a_share_alpha.scripts.evolve_stock_factor_matching \
  china_a_share_alpha/examples/stock_factor_matching_evolution.yaml
```

The matching genome searches the number of selected libraries, stock/industry/
market/global shrinkage weights, utility temperature, minimum observations,
and portfolio selection fraction. Forward labels are calculated separately
inside each temporal fold. Train data estimate matching utilities, the 2023
validation fold selects the genome, and the 2024--2026 test fold is opened once
after evolution. The first 12-round campaign improved validation Sharpe to
1.722 but achieved only 0.374 test Sharpe with -48.55% maximum drawdown. Removing
the five largest test contributors made annualized return negative, so this
candidate was rejected and no live library was changed.

For the changed 2025--2026 regime, run walk-forward matching and the separate
market-gate audit:

```bash
python -m china_a_share_alpha.scripts.evolve_recent_regime_matching \
  china_a_share_alpha/examples/current_regime_matching_evolution.yaml
python -m china_a_share_alpha.scripts.audit_recent_market_gate \
  china_a_share_alpha/examples/recent_market_gate_audit.yaml
```

Each evaluation window estimates matching utility from the preceding 504
trading days. Evolution uses 2025 H2 and 2026 Q1 plus two deterministic,
stock-disjoint cohorts; April--16 July 2026 is diagnostic only. The ungated
candidate failed that recent window (Sharpe -1.594, drawdown -37.80%). A
continuous-history MA20 market gate, selected on the earlier windows, improved
the all-stock diagnostic to Sharpe 1.027 and drawdown -7.13%. Main-board Sharpe
remained -0.064 while STAR/ChiNext reached 0.899, so the gate is not promoted.
The snapshot ends on 2026-07-16 and the diagnostic is not blind.

## Recent all-expression audit

Audit every currently discovered expression independently rather than treating
each multi-factor library as one averaged signal:

```bash
python -m china_a_share_alpha.scripts.run_recent_all_factor_audit \
  china_a_share_alpha/examples/recent_all_factor_audit.yaml
```

The resumable runner freezes a 55-library/119-expression catalog, caches each
expression separately, and evaluates 2024, 2025, and 2026 YTD across 5d/10d/20d
T+1 exits, ungated/MA20 entries, and all-stock/main-board/STAR-ChiNext universes.
The completed matrix contains 6,426 unique rows: 6,372 valid rows and 54 rows
explicitly invalidated for insufficient cross-sectional variation. Thirty-eight
unique expressions pass at least one strict contract requiring positive 2025
and 2026 Sharpe and RankIC, no worse than -25% recent drawdown, and no more than
10% single-stock return concentration. BSE, ETF, and independent-index gaps are
recorded as unavailable rather than imputed.

## Factor score-bucket and maximum-horizon audit

Profile individual-stock efficacy by the factor score available on the signal
day and rank each factor by its best realized 5d/10d/20d contract:

```bash
python -m china_a_share_alpha.scripts.run_factor_score_bucket_audit \
  china_a_share_alpha/examples/factor_score_bucket_audit.yaml
```

The audit preserves D-signal/D+1-open execution and all board-aware stop,
trailing-profit, limit-down queue, and forced-expiry rules. Each daily
cross-section is converted to a 0--100 percentile and summarized in ten score
buckets. Outputs include trade effectiveness and target-hit rates with sample
counts, average/median realized return, cohort Sharpe and drawdown, profit
factor, payoff ratio, favorable/adverse excursion, holding time, and exit-reason
rates. The best realized horizon maximizes `0.40 * 2025 annualized return + 0.60
* 2026 YTD annualized return`; maximum floating profit and its horizon are
reported separately. Because three horizons are compared on already observed
data, this is a diagnostic ranking and not a blind estimate of future return.

## Recursive Self-Improvement policy archive

The DGM-style outer loop evolves factor-mining policy rather than model weights.
Its archive uses four orthogonal mutation surfaces: search budget, parent
selection, diversity, and structure. A proposal changes exactly one functional
field; the hold-Sharpe threshold and maximum-correlation gate are frozen
examiner fields and are never mutated.

Parent eligibility is a hard contract. A node may reproduce only when its own
execution receipt has the expected policy identity, a finite hold Sharpe, the
same frozen evaluator, and every required gate set to true. Failed evaluations
retain their receipts but receive zero archive fitness. The loop also refuses a
new proposal while another child is pending.

Audit or migrate an existing archive before continuing:

```bash
python -m china_a_share_alpha.loop.recursive_self_improve \
  --audit-existing --baseline-iteration 49
```

The phase-1 archive migration initially contained 28 eligible parents, 29
invalid nodes, and pending `policy_0057`. The loop subsequently ran through
iteration 114. Iteration 109 / `policy_0060` is the current live library with
Hold Sharpe 2.3256; iterations 110–114 did not replace it. Proposal metadata
records the policy/parent IDs, mutation field, evaluation group, seed, and
config hashes. New children must pass a resumable paired-seed campaign before
becoming eligible parents:

```bash
python -m china_a_share_alpha.scripts.run_paired_policy_evaluation \
  --child-id policy_XXXX \
  --seeds N N+1 N+2 \
  --baseline-library \
  china_a_share_alpha_output/factor_mining_loop/iter_NNNN/seed_library.csv
```

The paired campaign isolates every arm from production state, disables
promotion writes, and freezes the pre-child seed library by checksum. Selection
requires at least three valid pairs, positive mean and median paired hold-Sharpe
deltas, a win rate of at least two thirds, and no single-seed regression worse
than 0.10 Sharpe. A single-run-valid child remains ineligible while this receipt
is pending. Do not launch a paired campaign for a child that already failed its
single-run hard gates.

The complete per-iteration ledger and the latest paired-selection outcomes are
maintained in `../wiki/factor_evolution_complete_history_1_114.md`.

## Downloading real Qlib data

A helper script downloads and extracts the community Qlib A-share dataset:

```bash
python -m china_a_share_alpha.scripts.download_qlib_cn_data --target ~/.qlib/qlib_data/cn_data
```

> The tarball is large; use `--dry-run` to verify the URL first.

## Sector / market-cap mapping

For real neutralization, provide a CSV with columns `symbol, sector, market_cap`
and set `sector_csv: path/to/sectors.csv` in the config. Generate a template
from a Qlib instrument list:

```bash
python -m china_a_share_alpha.scripts.generate_sector_template --instrument csi300 --output sectors.csv
```

If no CSV is provided, a deterministic synthetic mapping is used for demo
purposes.

## Using real Qlib data

1. Download community Qlib A-share data with the script above (or manually from
   [chenditc/investment_data](https://github.com/chenditc/investment_data)).
2. Point `data_dir` in your config to the `cn_data` folder.
3. Set `data_source: qlib` in the config.

Example:

```yaml
data_source: qlib
data_dir: ~/.qlib/qlib_data/cn_data
instruments: csi300
start_time: "2018-01-01"
end_time: "2023-12-31"
split_date: "2021-01-04"
forward_period: 5
mutator: gp
threshold: 0.02
neutralize_sector: true
neutralize_market_cap: true
output_dir: ./alpha_reports
```

## Configuration options

```yaml
data_source: synthetic          # or "qlib"
n_symbols: 80
n_days: 252
seed: 42
split_date: "2020-07-01"       # train/test boundary
initial_expression: {type: var, name: close}
threshold: 0.25                # SEMAS evolution pass threshold
mutator: seed                  # "seed" | "gp"
neutralize_sector: false
neutralize_market_cap: false
forward_period: 1
transaction_cost: 0.001        # 10 bps one-way
output_dir: ./china_a_share_alpha_output
```

## References

- Kakushadze, Z. (2016). 101 Formulaic Alphas. *Wilmott*.
  https://arxiv.org/abs/1601.00991
- Yu et al. (2023). Generating Synergistic Formulaic Alpha Collections via
  Reinforcement Learning. *KDD 2023*. https://github.com/RL-MLDM/alphagen
- Tang et al. (2025). AlphaAgent: LLM-Driven Alpha Mining with Regularized
  Exploration to Counteract Alpha Decay. *KDD 2025*.
  https://github.com/RndmVariableQ/AlphaAgent
- Guo et al. (2026). AlphaPROBE: Alpha Mining via Principled Retrieval and
  On-graph Biased Evolution. https://github.com/gta0804/AlphaPROBE
- QuantaAlpha. https://github.com/QuantaAlpha/QuantaAlpha
- Microsoft Qlib documentation: https://qlib.readthedocs.io/
- TA-Lib: https://ta-lib.org/
