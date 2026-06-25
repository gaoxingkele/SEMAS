# SEMAS Evolution Ideas

> Living notes on the design of SEMAS and the external ideas we have absorbed
> into its plugin architecture.

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

- `data/` — Qlib loader, synthetic A-share panel, TA-Lib wrappers, Alpha101
  baseline formulas.
- `factor/` — Expression tree with Qlib-style operators (`ts_*`, `cs_*`),
  serializable to/from dict.
- `evaluator/` — IC, RankIC, ICIR, turnover, long-short backtest metrics.
- `backtest/` — Simple quantile long-short backtest.
- `evolution/` — `FactorMutator` (tree crossover / point mutation) that works
  as a SEMAS `Mutator`.
- `run_factor_mining.py` / `demo.py` — end-to-end evolution runner.

### Demo result

Starting from raw `close`, one SEMAS evolution round produces
`neg(cs_rank(ts_mean(return, 5)))` with IC ≈ 0.23 on the synthetic
mean-reversion panel.

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
