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

Run tests:

```bash
python -m pytest tests/test_china_a_share_alpha.py -q
```

## Architecture

- `data/` — Qlib loader with train/test split, TA-Lib wrappers, Alpha101
  baseline formulas, synthetic A-share panel with sector/market-cap.
- `factor/` — Factor expression tree and operator library (Qlib-style
  `ts_*`, `cs_*`, arithmetic).
- `evaluator/` — IC, RankIC, ICIR, turnover, neutralization.
- `backtest/` — Quantile long-short backtest with transaction costs.
- `evolution/` — `FactorMutator` supporting deterministic seed mode and
  random grammar-based (GP) mode.
- `report/` — JSON/Markdown factor report generator.
- `run_factor_mining.py` — High-level evolution runner.
- `demo.py` — Minimal runnable demo.

## Key features

| Feature | Status | Notes |
|---|---|---|
| Train / test split | ✅ | `load_data()` returns `(train, test)`; OOS IC reported |
| Neutralization | ✅ | Sector / market-cap neutralization stubs wired in |
| Transaction costs | ✅ | Long-short backtest with turnover-based cost |
| Deterministic seed mutator | ✅ | Fast demo/CI |
| Open GP mutator | ✅ | `mutator: gp` for grammar-based random search |
| Report generator | ✅ | JSON + Markdown reports |
| Real Qlib data | ✅ | Optional loader; falls back to synthetic |

## Using real Qlib data

1. Download community Qlib A-share data, e.g.
   [chenditc/investment_data](https://github.com/chenditc/investment_data).
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
