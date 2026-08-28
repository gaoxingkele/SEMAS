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
