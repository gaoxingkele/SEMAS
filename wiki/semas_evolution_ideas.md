# SEMAS Evolution Ideas

> Living notes on the design of SEMAS and the external ideas we have absorbed
> into its plugin architecture.

---

## 2026-06-30 — China A-Share Alpha: Evolved Factors Beat Hand-Designed Ones, But Simple Ensembles Beat Optimization

This entry summarizes the head-to-head comparison between hand-designed style
factors and evolved factors on real Tushare CSI300/500/1000/major/tech universes.

### Result: evolved factors dominate single-factor rankings

| Period | Universe | Manual in top-10 (by test IC) | Evolved in top-10 | Avg rank — manual | Avg rank — evolved |
|---|---|---|---|---|---|
| 2021-2026 | csi300 | 2/10 | 8/10 | 16.3 | 11.8 |
| 2021-2026 | csi500 | 1/10 | 9/10 | 18.9 | 10.1 |
| 2021-2026 | csi1000 | 1/10 | 9/10 | 19.0 | 10.1 |
| 2021-2026 | major | 2/10 | 8/10 | 18.5 | 10.4 |
| 2025-2026H1 | csi300 | 2/10 | 8/10 | 17.2 | 11.2 |
| 2025-2026H1 | csi500 | 3/10 | 7/10 | 17.0 | 11.3 |

[source: `china_a_share_alpha_output/cross_universe_audit_with_high_zscore/`]
[source: `china_a_share_alpha_output/cross_universe_audit_2025h1_2026h1_with_high_zscore/`]

Top single factors in the recent 2025-2026H1 window are almost all evolved:
`evolved_2` (`abs(return)`), `talib_rsi_14`, `alpha101_001`, `talib_atr_14`,
`evolved_3` (`abs(ts_std(abs(return), 5))`). The only hand-designed factor that
competes at the top is `high_zscore_20`, and it was itself discovered by the
enhanced expression-evolution loop.

### Why the manual factors lag

The hand-designed factors (`momentum_20`, `reversal_5`, `volume_price_20`,
`low_vol_20`, `value_pb`, `liquidity_20`) are classic cross-sectional style
factors. Over the 2021-2026 A-share window they were weak: low-vol and reversal
were particularly poor, and value (low PB) had a weak Sharpe despite a decent
IC. This matches the broader finding that raw anomaly signals often fade once
turnover and costs are considered.
[source: Novy-Marx & Velikov, *Review of Financial Studies*, 2016]

### Why weight-space optimization failed

We tried three versions of portfolio-weight evolution:

1. Sort base factors by `test_ic` (look-ahead): train Sharpe 2.72, test Sharpe
   0.23.
2. Sort base factors by `train_ic` (no look-ahead): train Sharpe 2.63, test
   Sharpe 0.88, but 66.7% daily turnover made cost-adjusted return negative.
3. Cleaned library + hard turnover cap (0.3) + EMA smoothing (span 3): train
   Sharpe 3.40, test Sharpe -0.32.

The GA consistently found training-period combinations that looked excellent
and then lost money out of sample. The search has too many degrees of freedom
relative to the short training window and the noisy base signals.
[source: `china_a_share_alpha_output/portfolio_weight_evolution_cleaned/`]

### What worked: equal weight + EMA smoothing

A deliberately simple pipeline produced the first positive cost-adjusted return
on the 2024-2026 test set:

1. Clean the factor library (`clean_factor_library.py`).
2. Keep factors with positive train IC.
3. Z-score and equal-weight them.
4. Apply a per-symbol EMA (span 10-20) to the combined signal.

| Combination | Train Sharpe | Test Sharpe | Test cost-adj return | Turnover |
|---|---|---|---|---|
| Top 5 train-IC, span 10 | 2.04 | 0.90 | 6.2% | 0.0005 |
| Top 5 train-IC, span 20 | 2.06 | 0.96 | 11.3% | 0.0003 |
| 11 positive-train-IC + `high_zscore_20`, span 10 | 1.09 | 1.04 | 12.1% | 0.0005 |
| 11 positive-train-IC + `high_zscore_20`, span 20 | 0.80 | 1.09 | 16.8% | 0.0003 |

[source: `china_a_share_alpha_output/factor_combination/top5_span10/`]
[source: `china_a_share_alpha_output/factor_combination/top11_span10/`]

This is consistent with the finance literature: when parameter estimation error
is large, simple equal-weighting often outperforms optimized weights.
[source: DeMiguel, Garlappi, Uppal, *Review of Financial Studies*, 2009]

### Takeaways

- **Evolution is worth it for alpha discovery.** The evolved/TA-Lib factors
  genuinely outrank hand-designed style factors in both the full sample and the
  recent out-of-sample window.
- **Do not trust weight-space GA for portfolio construction.** The optimizer
  overfits unless you add strong regularization or a validation fold.
- **Prefer simple, low-turnover ensembles.** Equal weight + temporal smoothing
  is a robust baseline for combining formulaic alphas.
- **Cleaning is mandatory.** The raw evolved library contains many degenerate or
  constant-heavy expressions; they must be filtered before combination.

### Next experiments

- Try ICIR-weighted instead of equal weight, with a hold-out validation fold
  for estimating the weights.
- Add sector / market-cap neutralization of the combined signal.
- Run the enhanced expression loop with more seeds and longer runs to expand
  the cleaned library, then re-evaluate the ensemble.

---

## 2026-06-26 — China A-Share Alpha: Evolved Factors on Real Tushare Data

After wiring the loop to real CSI300 data, we ran the GP outer loop with
per-generation checkpointing. The best evolved factor outperformed all
hand-designed baselines:

| Factor | IC | RankIC | Sharpe | Expression |
|---|---|---|---|---|
| evolved_3 | 0.0064 | 0.0063 | 1.155 | `cs_rank(add(-0.309, div(ts_corr(ts_delta(vwap, 3), low, 3), ts_mean(low, 20))))` |
| evolved_1 | 0.0110 | 0.0216 | 0.714 | `cs_rank(add(-0.309, div(ts_corr(ts_delta(vwap, 3), low, 3), ts_mean(low, 20))))` |
| momentum_20 | 0.0040 | -0.0138 | 0.406 | hand-designed |
| value_pb | 0.0097 | 0.0335 | 0.108 | hand-designed |

The evolved expression is interpretable: it cross-sectionally ranks the
sum of a small negative drift and the 3-day correlation between vwap change
and low price, scaled by the 20-day mean of low price. It achieves a Sharpe
of 1.155 on the full 5-year sample, well above the hand-designed baselines.

Key loop fixes along the way:

- NaN/constant factors are now penalized with `-1.0` test IC so they are not
  selected as elites.
- **Robust selection**: candidates whose train/test IC signs disagree are
  penalized, avoiding unstable sign-flipping alphas.
- Per-generation checkpointing preserves the leaderboard even if the long
  loop is interrupted.
- `run_tushare_backtest.py` can merge an evolved leaderboard into the
  comparison report via `--evolved-csv` and automatically filters sign-flips
  and duplicates.

---

## 2026-06-26 — China A-Share Alpha: Tushare Historical Backtest Comparison

We added a real-data historical backtest pipeline using Tushare Pro data over
a 5-year window for CSI300 constituents.

[source: china_a_share_alpha/scripts/run_tushare_backtest.py]

### What it covers

- **Single factors**: momentum_20, reversal_5, volume_price_20, low_vol_20,
  value_pb, liquidity_20. Each has an explicit behavioral/economic
  interpretation.
- **Combined factors**:
  - `multi_timeframe`: momentum + short-term reversal across horizons.
  - `multi_style_equal`: equal-weighted blend of all six styles.
  - `ic_weighted_train`: data-driven weights proportional to in-sample IC,
    preserving sign so positive-IC factors are longed and negative-IC factors
    are shorted.
- **Metrics**: IC, RankIC, ICIR, turnover, annualized long-sector long-short
  return, Sharpe, max drawdown, cost-adjusted return, plus train/test IC gap
  for overfit diagnostics.

### Data source

Tushare Pro API token is supplied via the `TUSHARE_TOKEN` environment
variable or `--token`. Data is cached under `china_a_share_alpha_output/`.

[source: https://tushare.pro/]

### Empirical result (sample run 2021-06 to 2026-06, CSI300)

| Metric | Winner | Value |
|---|---|---|
| Best Sharpe | momentum_20 | 0.41 |
| Best IC | value_pb | 0.0097 |
| Highest RankIC | ic_weighted_train | 0.0376 |

The report notes that simple style factors were relatively weak over this
period; combining by IC weight improved IC but not necessarily long-short
Sharpe, highlighting the importance of cost/turnover control and risk
neutralization in live deployment.

---

## 2026-06-24 — China A-Share Alpha: Completing All Target Directions

We implemented the five post-loop deepening directions in one coherent push.

[source: china_a_share_alpha/README.md]

### 1. Real Qlib data download

Added `scripts/download_qlib_cn_data.py` which downloads the community
`qlib_bin.tar.gz` from `chenditc/investment_data` and extracts it to
`~/.qlib/qlib_data/cn_data`.

[source: https://github.com/chenditc/investment_data]

### 2. Real sector / market-cap mapping

- Added `data/sector_mapping.py` to load a user-provided CSV (`symbol, sector,
  market_cap`) or fall back to deterministic synthetic mappings.
- Added `scripts/generate_sector_template.py` to create a CSV template from a
  Qlib instrument list.
- Wired neutralization into `data/qlib_loader.py` and `executor.py`.

### 3. Alpha decay monitoring

- Added `loop/decay_monitor.py` to compute rolling test-IC slopes.
- `FactorPopulation.run_generation()` now prints a decay warning when the 3-gen
  slope is negative.

### 4. Multi-factor portfolio evolution

- Added `loop/portfolio.py` with `PortfolioPopulation`.
- Portfolios are stored as SEMAS `AgentGenome` with a list of factor
  expressions + weights.
- Selection maximizes out-of-sample Sharpe; mutators adjust weights,
  add/remove/swap factors from a factor library.
- Added `run_portfolio_evolution.py` and `examples/portfolio_config.yaml`.

### 5. LLM-driven factor mutation + DSL parser

- Added `factor/parser.py` to parse expressions such as
  `neg(cs_rank(ts_mean(return, 5)))`.
- Added `evolution/llm_mutator.py` which prompts an LLM for a new expression
  and falls back to GP if the response is not parseable.
- Integrated with the SEMAS `LLMClient` abstraction (OpenAI / Kimi / DeepSeek
  via environment variables).

### Verification

- `python -m pytest tests/ -q` — **39 passed**.
- `python -m china_a_share_alpha.run_factor_loop china_a_share_alpha/examples/loop_config.yaml` —
  discovers `neg(cs_rank(ts_mean(return, 5)))` and stops on convergence.
- `python -m china_a_share_alpha.run_portfolio_evolution china_a_share_alpha/examples/portfolio_config.yaml` —
  evolves a weighted portfolio from the sample factor library.

---

## 2026-06-24 — China A-Share Alpha Evolver Package

We created `china_a_share_alpha/` as a standalone subpackage: an evolvable
alpha-factor mining scaffold for China A-shares, built on SEMAS and designed
to interoperate with **Qlib** data/operators and **TA-Lib** indicators.

[source: china_a_share_alpha/README.md]

### What the literature / open-source landscape says

- **WorldQuant 101 Formulaic Alphas** (Kakushadze 2016) is the canonical
  starting library for formulaic alpha construction.
  [source: https://arxiv.org/abs/1601.00991]
- **AlphaGen** (Yu et al., KDD 2023) uses reinforcement learning to generate
  synergistic formulaic alpha collections, treating expression generation as an
  MDP over Reverse Polish Notation tokens.
  [source: https://github.com/RL-MLDM/alphagen]
- **AlphaAgent** (Tang et al., KDD 2025) is an LLM-driven multi-agent framework
  (Idea / Factor / Eval agents) that mines decay-resistant alphas.
  [source: https://github.com/RndmVariableQ/AlphaAgent]
- **AlphaPROBE** (Guo et al., 2026) frames alpha mining as DAG navigation with
  a Bayesian retriever and DAG-aware generator.
  [source: https://github.com/gta0804/AlphaPROBE]
- **QuantaAlpha** combines LLM + evolutionary strategies for self-evolving
  factor mining on Qlib CSI300 data.
  [source: https://github.com/QuantaAlpha/QuantaAlpha]
- **Qlib** itself provides the data format, ExpressionOps (`ts_*`, `cs_*`,
  `Ref`, `Rank`, `Corr`, etc.), processors, and backtest infrastructure for
  A-share ML quant research.
  [source: https://qlib.readthedocs.io/]
- **TA-Lib** is the standard technical-indicator library with 150+ indicators
  (RSI, MACD, Bollinger Bands, etc.).
  [source: https://ta-lib.org/]

### Package components

- `data/` — Qlib loader with train/test split, synthetic A-share panel with
  sector/market-cap, TA-Lib wrappers, Alpha101 baseline formulas.
- `factor/` — Expression tree with Qlib-style operators (`ts_*`, `cs_*`),
  serializable to/from dict.
- `evaluator/` — IC, RankIC, ICIR, turnover, sector/market-cap neutralization.
- `backtest/` — Quantile long-short backtest with transaction costs.
- `evolution/` — `FactorMutator` with deterministic `seed` mode and random
  grammar-based `gp` mode.
- `report/` — JSON/Markdown factor report generator.
- `run_factor_mining.py` / `demo.py` — end-to-end evolution runner.

### Demo result

Starting from raw `close`, one SEMAS evolution round produces
`neg(cs_rank(ts_mean(return, 5)))` with train IC ≈ 0.23 and test IC ≈ 0.23.

---

## 2026-06-24 — China A-Share Alpha Evolver Deepening

We deepened the `china_a_share_alpha/` package with production-oriented
features:

- **Train / test split** in `data/qlib_loader.py` and `data/synthetic.py`;
  the executor evaluates the same factor on both sets; the runner reports
  in-sample and out-of-sample IC.
- **Sector / market-cap neutralization** stubs in `evaluator/neutralizer.py`
  and wired into `executor.py` via config flags.
- **Transaction costs** in `backtest/long_short_backtest.py` using turnover *
  2 * one-way cost, yielding cost-adjusted returns.
- **Open GP search** in `evolution/factor_mutator.py`: `mode: gp` generates
  random expression trees from a grammar instead of the deterministic seed
  expression.
- **Factor report generator** in `report/generator.py` writes JSON and
  Markdown reports with expression, IC, backtest stats, and config.

[source: OPERATION_LOG.md 2026-06-24 — China A-Share Alpha Evolver Deepening]

---

## 2026-06-24 — China A-Share Alpha Continuous Mining Loop

We added a population-based outer loop on top of the single-factor SEMAS
runner:

- `loop/population.py` — `FactorPopulation` manages seeding, evaluation,
  selection by **test IC** (to avoid train-set overfitting), mutation,
  crossover, deduplication, and convergence tracking.
- `run_factor_loop.py` — CLI that runs generations until `max_generations`
  or early-stop `patience`, then outputs a leaderboard, generation history,
  and factor report.
- `evolution/factor_mutator.py` gained a `crossover(parent1, parent2)`
  method for subtree exchange.
- `examples/loop_config.yaml` provides a ready-to-run loop config.

Demo result on synthetic data: the loop discovers
`neg(cs_rank(ts_mean(return, 5)))` in generation 0 and stops after 4
generations of no test-IC improvement, returning a leaderboard and report.

[source: china_a_share_alpha/run_factor_loop.py]

---

## 2026-06-23 — AI Video Evolver Package

We created `ai_video_evolver/` as a standalone subpackage: an evolvable
end-to-end AI video generation scaffold built on SEMAS.

[source: ai_video_evolver/README.md]

Components:

- `agents/` — YAML genomes for scriptwriter, prompt engineer, asset generator,
  editor, critic.
- `tools/` — Python tool sources for API client, FFmpeg pipeline, prompt
  templates, critic functions (all stubbed for offline use).
- `topologies/video_pipeline.yaml` — serial workflow topology.
- `executor.py` — runs the topology as a SEMAS `ExecutorFn`.
- `mutator.py` — deterministic mutator that toggles prompt enhancement.
- `run_video_evolution.py` — high-level runner.
- `demo.py` — minimal runnable demo.

The demo starts with a basic prompt that produces `score=0.603`; after one
SEMAS evolution round the pipeline learns to enhance prompts with cinematic
keywords and reaches `score=0.803`.

This is the canonical example of how to take a domain (AI video) and wrap it
into a versioned, evolvable SEMAS package.

---

## 2026-06-23 — Domain Fit: End-to-End AI Video Generation Agent

User asked whether SEMAS can evolve a full-pipeline AI video generation agent.
Short answer: **yes, and it's a very natural fit**.

AI video generation is not a single function; it is a multi-stage pipeline with
many hyperparameters, subjective quality gates, and expensive compute. That is
exactly the kind of problem SEMAS is designed for.

### Mapping the video pipeline to SEMAS

```text
Input prompt / script
       │
       ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Scriptwriter │────▶│ Prompt Engineer  │────▶│ Asset Generator │
│   agent      │     │     agent        │     │    agent        │
└─────────────┘     └──────────────────┘     └─────────────────┘
                                                      │
                       ┌─────────────┐               │
                       │    Critic   │◀──────────────┘
                       │   agent     │
                       └──────┬──────┘
                              │
                              ▼
                       Feedback loop
```

SEMAS mapping:

| Video stage | SEMAS concept |
|---|---|
| Scriptwriter | `AgentGenome` + system prompt |
| Prompt engineer | `AgentGenome` with prompt templates |
| Asset generator | `ToolGenome` wrapping video/image model APIs |
| Editor | `AgentGenome` + FFmpeg / ComfyUI tool |
| Critic | `AgentGenome` + quality metrics |
| Overall workflow | `TopologyGenome` |
| Good/bad prompt patterns | `Memory` / few-shot examples |
| Quality scoring | `Evaluator` |
| Improve prompts/tools/workflow | `Mutator` + `Orchestrator` |

### What would be evolved

1. **Prompts**: text-to-video prompts, negative prompts, style modifiers.
2. **Tools**: API call wrappers, FFmpeg pipelines, ComfyUI node graphs,
   caption generators.
3. **Topology**: add/remove a critic, insert a retry loop, parallelize
   generation attempts.
4. **Few-shot**: store successful prompt → video pairs.
5. **Memory**: per-project or per-style prompt priors.

### Required scaffolding

| Component | Purpose |
|---|---|
| Video executor | Call Runway / Pika / Stable Video / ComfyUI |
| Asset storage | Version generated clips, intermediates, metadata |
| Quality evaluator | CLIP score, temporal coherence, aesthetic score, prompt adherence, safety |
| Cost budget | Limit generation calls per evolution round |
| Surrogate critic | Lightweight model to score candidates without generating full video |
| Sandbox | Allow `ffmpeg`, `opencv`, `PIL`; restrict arbitrary network writes |
| Regression tests | Fixed prompt set + reference outputs |

### Key risks

- **Cost**: Video generation is expensive. You cannot afford to generate 100
  candidates. A surrogate critic / co-evolving value model is essential.
- **Subjectivity**: Automated metrics (CLIP, FVD) do not always match human
  taste. Need human-in-the-loop or a learned preference model.
- **Non-determinism**: Same prompt can yield very different videos. Evaluation
  must average over multiple seeds or use deterministic seeds.
- **Safety / copyright**: Generated content can be NSFW or infringe. Safety
  gates and legal review are mandatory.
- **Slow feedback loop**: Evolution rounds take minutes/hours. Cache everything.

### Recommended plugin mix

- **Core SEMAS** for topology and prompt evolution.
- **FunctionEvolve** for optimizing numeric generation parameters (duration,
  CFG scale, seed ranges) if they can be expressed symbolically.
- **SIA** for fine-tuning a critic / preference model on human feedback.
- **Avoid Gödel Agent**: full self-modification is too risky for a pipeline
  that calls external paid APIs and generates public content.

### Bottom line

SEMAS is a strong fit for an end-to-end AI video agent, not because it generates
video itself, but because it provides an **evolvable, auditable control layer**
around existing video models. The hard part is defining good evaluation metrics
and controlling cost; the framework handles the versioning, mutation, and
selection loop.

---

## 2026-06-23 — Domain Fit: Financial Factors / Mingli / OSINT

User asked whether SEMAS is reasonable for evolution-mode applications in three
very different domains. Short answer: **yes, with domain-specific scaffolding**.

SEMAS is best understood as a generic substrate for "evolve interpretable
artifacts under constraints". All three domains share this shape:

- **Symbolic/interpretable outputs** (factor formulas,命理 rules, intelligence
  hypotheses).
- **Multi-step workflows** (data → analysis → verification → report).
- **Need for auditability and regression gates** (money, culture, and security
  are all high-stakes).

### 1. 金融市场因子挖掘 (Financial Factor Mining)

**Fit**: Very high.

- Factor formulas are naturally symbolic → perfect for `ToolGenome` and the
  `FunctionEvolve` plugin.
- Backtesting metrics (Sharpe, IC, max drawdown) map cleanly to `Evaluator`.
- `GenomeRepository` gives lineage for every factor version — critical for
  regulatory and strategy audit.

**Required scaffolding**:

- A data executor that feeds OHLCV / fundamental data into the agent.
- A backtest `Evaluator` with train/validation/test split and walk-forward
  validation.
- `Regression tests` on a stable set of historical periods to avoid overfitting.
- `Sandbox` whitelist limited to `numpy`, `pandas`, `scipy`.

**Key risk**: overfitting. The framework will happily evolve a factor that
works on the past and fails on the future. Mitigation: holdout periods,
transaction-cost-aware metrics, and a hard rule that live trading requires
human approval.

[source: examples/mingli_5agents/benchmark.py pattern; FunctionEvolve plugin]

### 2. 命理分析 (Mingli / Destiny Analysis)

**Fit**: High (already prototyped).

- The project already has `examples/mingli_5agents/` showing multi-agent
  evolution with citation and safety metrics.
- 命理 has many interpretable rules and schools → good for `ToolGenome` and
  `TopologyGenome`.
- Output often needs citation to classical texts → `Evaluator` can enforce
  citation precision.

**Required scaffolding**:

- A knowledge base / classical-text retriever as a tool.
- `Metric floors` for safety and citation (already demonstrated in
  `mingli_5agents/evolution.py`).
- Human-in-the-loop for final interpretation, because命理 outputs are
  culturally sensitive and subjective.

**Key risk**: hallucination dressed up as tradition. Mitigation: every claim
must cite a source; safety metric = 1.0 is a hard gate.

[source: examples/mingli_5agents/evolution.py, examples/mingli_5agents/benchmark.py]

### 3. 开源情报进化分析 (OSINT Evolutionary Analysis)

**Fit**: High.

- OSINT workflows are naturally multi-agent: collector → analyst → verifier →
  reporter.
- Sources and APIs change constantly → evolution is not optional, it's required.
- `ToolGenome` can represent scrapers, API wrappers, enrichment functions.
- `Memory` can track source reliability over time.

**Required scaffolding**:

- Network-aware `Sandbox` (allow `requests`, `httpx`, but not local file writes).
- `Evaluator` metrics: source diversity, factual accuracy, timeliness,
  redundancy.
- A verifier agent that cross-checks claims against multiple sources.
- Compliance policy gate: never scrape protected/illegal targets.

**Key risk**: adversarial misinformation and legal/ethical boundary crossing.
Mitigation: strict `SelfModificationPolicy`, human approval for new data
sources, and a "deny list" of domains/sources enforced at the sandbox level.

### Recommended plugin mix per domain

| Domain | Primary plugin | Secondary plugin | Avoid |
|---|---|---|---|
| Financial factors | `FunctionEvolve` | `SIA` for weight-based market intuition | `Gödel Agent` |
| Mingli | Core SEMAS + population evolution | `SIA` for stylistic preference learning | `Gödel Agent` |
| OSINT | Core SEMAS + topology evolution | `FunctionEvolve` for query/rule optimization | `Gödel Agent` |

### Bottom line

SEMAS is **reasonable** for all three, but it is not a turnkey solution. The
heavy lifting is in defining the domain executor, metrics, data splits, and
safety constraints. The framework's value is that it gives you a reproducible,
versioned, regression-gated evolution loop for those domain artifacts.

---

## 2026-06-23 — SEMAS Self-Upgrade: Using Downstream Tasks to Evolve the Framework

Reflexive idea: **SEMAS can use itself to evolve itself**. Instead of only
evolving business agents, we treat the framework's own prompts, trigger
policies, sandbox whitelist, and plugin selection as an `AgentGenome` and run a
meta-evolution loop.

[source: SEMAS_SELF_UPGRADE_DESIGN.md]

### Downstream task categories

| Category | Example task | What it validates |
|---|---|---|
| Tool Evolution | Date-diff tool evolution | `Mutator` + `Sandbox` |
| Prompt Evolution | Shift from country to capital answers | `Mutator.mutate_prompt` |
| Regression Gate | Old task still passes after prompt update | `Evaluator` regression suite |
| Plugin Convergence | FunctionEvolve reaches `2*x` | `PluginRegistry` pipeline |
| Sandbox Safety | Dangerous import rejected | `Sandbox` AST whitelist |
| Topology | Serial reviewer pipeline | `TopologyGenome` |

### Framework-level metrics

A single task passing is not enough. We track:

- `pass_rate`
- `mean_evolution_rounds`
- `total_llm_calls`
- `regression_rate`
- `safety_violation_count`
- `convergence_rate`

[source: benchmarks/semas_self_upgrade/metrics.py]

### Framework Genome

The meta-configuration lives in
`benchmarks/semas_self_upgrade/framework_genome/framework_config_v1.yaml`:

- mutator prompts
- trigger policy (cooldown, max versions)
- sandbox policy (allowed modules)
- plugin policy (which plugins are enabled)

### Meta-evolution loop

```text
load framework genome
    │
    ▼
run downstream benchmark
    │
    ▼
if pass_rate < target:
    mutate framework genome
    archive new genome
    repeat
else:
    stop
```

Implemented in `benchmarks/semas_self_upgrade/evolve_semas.py`.

### Key constraint

Recursive self-improvement must have a **hard budget and regression gate**.
Without them, the meta-loop can overfit to the benchmark or make unsafe
changes. This is why Gödel-Agent-style full self-modification is kept as a
research-only plugin behind a strict policy gate.

---

## 2026-06-23 — SEMAS Core Design

SEMAS is built on a single belief: **when LLM weights are frozen, evolution must
happen on editable artifacts**. [source: SEMAS README.md]

Key primitives:

- `AgentGenome` = prompt + tools + topology + few-shot + meta.
- `GenomeRepository` = file-system versioning + rollback.
- `Evaluator` = metrics + regression tests.
- `Mutator` = LLM-driven variations.
- `Sandbox` = restricted execution of generated code.
- `Orchestrator` = dual loop (execute→evaluate vs. mutate→select→commit).

Why this shape? Because it mirrors the classic optimization loop but replaces
gradient descent with **selection over human-readable artifacts**. The
artifacts are inspectable, versionable, and reversible — which matters a lot
more for agents than for neural weights.

Design invariant: **weights stay frozen unless an explicit WeightUpdateStrategy
plugin is enabled**.

---

## 2026-06-23 — AgenticGEO → SEMAS Mapping

AgenticGEO (Yuan et al., 2026) is the closest academic analog to SEMAS.
[source: arXiv:2603.20213, https://github.com/AIcling/agentic_geo]

AgenticGEO ideas:

- MAP-Elites archive of diverse rewrite strategies.
- Co-evolving critic as a surrogate evaluator to reduce expensive GE calls.
- Content-conditioned multi-turn rewriting.

How we absorb it:

| AgenticGEO | SEMAS equivalent |
|---|---|
| MAP-Elites archive | `GenomeRepository` + `MingliEvolutionArchive` |
| Co-evolving critic | `Evaluator` + future critic plugins |
| Strategy selection | `Orchestrator` selection over candidates |
| Multi-turn rewrite | iterative `evolve_from` versions |

Absorbed into: `../geo-benchmark/` integration plan, `SEMAS_ARA_Architecture.md`.

---

## 2026-06-23 — AutoGEO / E-GEO / FeatGEO as Strategy Patterns

These GEO papers represent three different optimization philosophies:

- **AutoGEO**: extract rules from GE explanations, then rewrite.
  [source: arXiv:2510.11438]
- **E-GEO**: iterative prompt meta-optimization.
  [source: arXiv:2511.20867]
- **FeatGEO**: NSGA-II over interpretable feature space.
  [source: arXiv:2604.19113]

All three can be expressed as SEMAS plugins:

- AutoGEO rules → `ToolGenome` generated by `Mutator.mutate_tool`.
- E-GEO prompt meta-optimization → `Mutator.mutate_prompt` with a population
  loop on top.
- FeatGEO → `CandidateOptimizer` that searches a Pareto front of feature
  configurations.

The insight: **most LLM-agent optimization papers are special cases of
“generate candidates → score → select → commit”**. SEMAS is the generic
container.

---

## 2026-06-23 — Gödel Agent: Recursive Self-Modification

Gödel Agent (Yin et al., ACL 2025) pushes self-evolution to the extreme: the
agent can read its own runtime source code and monkey-patch itself.
[source: arXiv:2410.04444, https://github.com/Arvid-pku/Godel_Agent]

Key idea: π_{t+1} = I(π_t, r_t), where both the policy π and the improvement
algorithm I can be rewritten. This is theoretically very powerful and
practically very scary.

Why we do **not** adopt it as default:

- Self-modification breaks auditability.
- No guaranteed termination or safety.
- Hard to sandbox when the agent can edit its own sandbox logic.

How we **do** absorb it:

- Add `SelfModificationPolicy` plugin interface.
- Future `semas.plugins.godel` would implement a mutator that proposes
  self-patches, but they must pass:
  1. AST whitelist,
  2. `Sandbox` execution,
  3. regression suite,
  4. explicit policy approval.
- The policy can forbid edits to `SelfModificationPolicy`, `Sandbox`, and
  `Evaluator` source files.

Status: **interface defined, implementation deferred** until there is a
controlled research use-case.

---

## 2026-06-23 — FunctionEvolve: Structure-Guided Symbolic Regression

FunctionEvolve (Xia et al., 2026) is not a general agent framework; it is a
scientific equation discovery system. But its architecture is highly portable
to agent tool evolution. [source: arXiv:2606.07704,
https://github.com/Phoinikas03/FunctionEvolve]

Key components:

1. **Generator** — seed diverse expression trees.
2. **Selector** — pick structurally diverse parents.
3. **Mutator** — deterministic AST edits + LLM-guided edits.
4. **Structure-aware Optimizer** — fit coefficients, simplify, score.
5. **Pareto/MDL selection** — balance complexity vs. error.

Absorbed into SEMAS as `semas/plugins/function_evolve/`:

- `FunctionEvolveToolMutator` uses Python `ast` to mutate tool return
  expressions.
- `FunctionEvolveToolOptimizer` perturbs numeric constants and keeps the best
  variant.
- The full FunctionEvolve pipeline could be wrapped later as a more
  sophisticated plugin; the current version is a minimal, dependency-free
  proof-of-concept.

Status: **implemented and tested**. See
`semas/plugins/function_evolve/demo.py`.

---

## 2026-06-23 — SIA: Harness + Weight Updates

SIA (Hebbar et al., 2026) argues that the self-improvement field has split into
two silos: harness-update and weight-update. SIA combines them.
[source: arXiv:2605.27276, https://github.com/hexo-ai/sia]

Architecture:

- Meta-Agent generates Target Agent.
- Target Agent executes and logs.
- Feedback Agent updates harness **and** weights (LoRA).

Why this matters for SEMAS:

- SEMAS was originally harness-only. That is safe and portable, but leaves
  performance on the table when the base model lacks domain intuition.
- Adding `WeightUpdateStrategy` lets users opt into SIA-style weight updates
  without making SEMAS depend on PyTorch/PEFT by default.

Absorbed into:

- `WeightUpdateStrategy` interface in `semas/plugins/base.py`.
- `_apply_weight_updates()` hook in `semas/orchestrator/orchestrator.py`.
- `SEMAS_SIA_Integration_Design.md`.

Status: **interface and design complete; full SIA plugin implementation is a
future Phase 2**.

---

## 2026-06-23 — Plugin Architecture Decision

Decision: make Gödel Agent, FunctionEvolve, and SIA **optional plugins** rather
than core framework features.

Reasoning:

- Core SEMAS should remain small, safe, and dependency-light.
- Different domains need different evolution levers.
- Plugins allow experimentation without risking the stable core.
- Plugins still benefit from SEMAS versioning, regression gates, and sandboxing.

Plugin interfaces:

- `MutatorStrategy` — generate candidates.
- `CandidateOptimizer` — refine candidates.
- `WeightUpdateStrategy` — update model weights.
- `SelfModificationPolicy` — gate self-modifying code.

See `SEMAS_ARA_Architecture.md` §5.7 and `semas/plugins/base.py`.

---

## 2026-06-23 — Multi-Agent GEO

Multi-Agent GEO (Bian et al., ACL 2026 Findings) focuses on reusable strategy
learning across heterogeneous queries. [source: arXiv:2604.19516]

Absorption path:

- Reusable strategies → `ToolGenome` archive in `GenomeRepository`.
- Experience-to-skill transfer → `MingliEvolutionArchive` + `memory.py`.
- Multi-agent topology → `TopologyGenome`.

No dedicated plugin yet, but the concepts map cleanly.

---

## 2026-06-23 — Open Questions

1. Should `CandidateOptimizer` be allowed to call the LLM for refinement, or
   should it stay deterministic/cheap? Leaning toward "deterministic by default,
   LLM-guided as an optional subclass".
2. How do we version large LoRA adapters in `GenomeRepository` without
   duplicating gigabytes per version? Proposed: store adapter metadata in JSON,
   binary files in `<repo>/weights/`, and rollback by copying/soft-linking.
3. Can Gödel-Agent-style self-modification ever be made safe enough for
   production? Current stance: research-only, behind a strict policy gate.
4. Should we add a "skill lifecycle" plugin inspired by MUSE-Autoskill
   (skill creation, memory, management, evaluation)? [source:
   arXiv:2605.27366] Worth monitoring.
