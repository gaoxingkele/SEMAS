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
│  (expression)    │     │  (IC / ICIR /    │     │ (tree crossover, │
│                  │     │   long-short)    │     │  constant opt)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                       Factor library / report
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

Run a full evolution experiment:

```bash
python -m china_a_share_alpha.run_factor_mining china_a_share_alpha/examples/sample_config.yaml
```

Run tests:

```bash
python -m pytest tests/test_china_a_share_alpha.py -q
```

## Architecture

- `data/` — Qlib loader, TA-Lib wrappers, Alpha101 baseline formulas.
- `factor/` — Factor expression tree and operator library (Qlib-style
  `ts_*`, `cs_*`, arithmetic).
- `evaluator/` — IC, RankIC, ICIR, turnover, neutralization.
- `backtest/` — Simple quantile long-short backtest.
- `evolution/` — Expression-tree mutator + constant optimizer.
- `run_factor_mining.py` — High-level evolution runner.
- `demo.py` — Minimal deterministic demo.

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
forward_period: 5
```

## References

- Kakushadze, Z. (2016). 101 Formulaic Alphas. *Wilmott*.
- Yu et al. (2023). Generating Synergistic Formulaic Alpha Collections via
  Reinforcement Learning. *KDD 2023*.
- Tang et al. (2025). AlphaAgent: LLM-Driven Alpha Mining with Regularized
  Exploration to Counteract Alpha Decay. *KDD 2025*.
- Guo et al. (2026). AlphaPROBE: Alpha Mining via Principled Retrieval and
  On-graph Biased Evolution.
- Microsoft Qlib documentation: https://qlib.readthedocs.io/
- TA-Lib: https://ta-lib.org/
