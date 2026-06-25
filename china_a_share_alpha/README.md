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

## Multi-factor portfolio evolution

After running the factor loop, use the top expressions as a library and evolve
weighted portfolios:

```bash
python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml
python -m china_a_share_alpha.run_portfolio_evolution china_a_share_alpha/examples/portfolio_config.yaml
```

The portfolio runner treats each portfolio as a weighted, z-scored combination
of factors and maximizes out-of-sample Sharpe ratio.

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
