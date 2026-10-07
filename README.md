# SEMAS — Self-Evolving Multi-Agent System Framework

A minimal, reusable framework for building self-evolving multi-agent systems on top of frozen-weight LLMs.

> **Core idea:** When the LLM weights are frozen, evolution must happen on editable artifacts — prompts, tools, topology, and memory — via selection-based variation rather than gradient descent.

## Design Overview

```text
semas_framework/
  semas/
    genome/         # Versioned agent "genomes": prompt + tools + topology
    evaluator/      # Reward functions, regression tests, pass/fail scoring
    mutator/        # LLM-driven mutation of prompts and tool code
    sandbox/        # Isolated execution of generated code
    orchestrator/   # Meta-agent that selects topology and triggers evolution
    plugins/        # Optional evolution plugins (FunctionEvolve, SIA, etc.)
    utils/          # Shared utilities (LLM client, logging, etc.)
  examples/         # Reference implementations
  tests/            # Unit tests
  wiki/             # Karpathy-style LLM Wiki for ideas and citations
```

## Key Concepts

1. **Genome**: A versioned JSON/YAML description of an agent or team of agents.
2. **Genome Repository**: A file-system-backed version store for genomes.
3. **Evaluator**: Scores task outcomes using deterministic + LLM-based metrics.
4. **Mutator**: Proposes prompt/tool/topology variations based on failure logs.
5. **Sandbox**: Safely executes generated code in a restricted subprocess.
6. **Orchestrator**: Runs the dual-loop system — inner execution loop + outer evolution loop.

## Quick Start

```bash
pip install -e .
cd examples/math_agents
python run_demo.py
```

## Evolution Loop

1. **Execute**: Agents run a task using the current genome version.
2. **Evaluate**: The evaluator scores the result.
3. **Trigger**: If the score is below threshold, the orchestrator asks the mutator for variations.
4. **Sandbox**: Each variation is tested in isolation.
5. **Select**: The best-performing variation is committed as the next genome version.
6. **Rollback**: If a new version regresses, the repository can roll back to the previous version.

## Safety & Cost Controls

- **Evolution cooldown**: Minimum number of tasks between evolutions.
- **New-error trigger**: Evolution only fires on previously unseen failure patterns.
- **Sandbox isolation**: Generated code runs in a restricted subprocess with timeout.
- **Regression suite**: Every prompt/tool change must pass historical test cases.
- **Max rollback**: Automatic revert if a new genome version performs worse.

## Optional Evolution Plugins

SEMAS core stays minimal. Advanced self-evolution methodologies can be plugged in
via `semas.plugins`:

- `MutatorStrategy` — custom candidate generation (e.g. FunctionEvolve AST edits).
- `CandidateOptimizer` — refine candidates before selection (e.g. constant fitting).
- `WeightUpdateStrategy` — test-time model weight updates (e.g. SIA-style LoRA).
- `SelfModificationPolicy` — gate Gödel-Agent-style self-modification.

Example:

```python
from semas.plugins import PluginRegistry
from semas.plugins.function_evolve import (
    FunctionEvolveToolMutator,
    FunctionEvolveToolOptimizer,
)

plugins = PluginRegistry()
plugins.register_mutator_strategy(FunctionEvolveToolMutator())
plugins.register_candidate_optimizer(FunctionEvolveToolOptimizer())

orch = Orchestrator(..., plugin_registry=plugins)
```

See `SEMAS_ARA_Architecture.md` §5.7, `SEMAS_SIA_Integration_Design.md`, and
`semas/plugins/function_evolve/demo.py` for details.

## Self-Upgrade Benchmark

SEMAS can also be validated and improved through a reflexive benchmark:

```bash
python -m benchmarks.semas_self_upgrade.run_benchmark
python -m benchmarks.semas_self_upgrade.evolve_semas
```

See `SEMAS_SELF_UPGRADE_DESIGN.md` and `benchmarks/semas_self_upgrade/README.md`.

## AI Video Evolver

A standalone subpackage demonstrating an evolvable, end-to-end AI video
generation pipeline built on SEMAS:

```bash
python -m ai_video_evolver.demo
```

See `ai_video_evolver/README.md`.

## China A-Share Alpha Evolver

A standalone subpackage for evolvable China A-share alpha factor mining,
built on SEMAS and compatible with Qlib data/operators and TA-Lib:

```bash
python -m china_a_share_alpha.demo
```

Production promotion audits use a frozen train/validation/test snapshot and an
explicit horizon-specific evaluation contract. See the subpackage README for
the snapshot, audit, and state-reconciliation commands.

The 20d execution optimizer also searches 10-percentile, 10%-increment
add/reduce schedules with next-day execution. Its frozen 2026-07-14 audit
retained static sizing; no dynamic schedule was promoted.

A companion frozen audit measures factor exposure to normalized MA5/10/20
signals with daily cross-sectional rank correlations and HAC uncertainty.
The residual-alpha audit then compares same-sample IC, layered returns, and
costed 20d holding performance after jointly neutralizing those exposures.
The unified no-lookahead horizon audit now designates 5d as primary, 10d as a
regime-sensitive secondary horizon, and 20d as research-only.

A board-aware full-library audit additionally supports D+1 open entry,
D+6/D+11/D+21 forced expiry, queued limit-down exits, cumulative stops, and
peak-drawdown trailing profit for main-board, STAR/ChiNext, and BSE policy tiers.
Missing BSE, index, or ETF frozen panels are reported as unavailable rather
than imputed.

A subsequent 12-round stock-to-library matching experiment selected factor
mixtures from train-only stock, industry, market, and global utility estimates.
Its 2023 validation Sharpe reached 1.722, but the unopened 2024--2026 test
Sharpe was only 0.374 with a -48.55% drawdown. The candidate was rejected as
non-generalizing and did not replace any live factor library.

Recent-regime research now isolates 2025 half-years and 2026 subperiods,
re-estimates matching utilities from trailing history, and validates across
stock-disjoint buckets. A continuous-history market trend gate can suspend new
long entries while leaving T+1 exits active. The first MA20-gated candidate
improved the April--July 2026 diagnostic, but remains research-only because the
period was already observed and main-board performance stayed slightly negative.

The current 55-library catalog has also been expanded into 119 unique
expressions and audited one expression at a time. The complete recent matrix
contains 6,426 rows across 2024/2025/2026 YTD, 5d/10d/20d exits, ungated/MA20
entry, and all/main/innovation universes. Thirty-eight expressions pass at least
one strict 2025--2026 contract; two expressions have explicitly invalid periods
because their cross-sectional variation is insufficient.

A companion individual-stock audit now maps every entry-time factor percentile
into ten 0--100 score buckets and compares realized return, win rate, target-hit
rate, cohort Sharpe, payoff, drawdown, and maximum favorable excursion. It also
reports each factor's best realized 5d/10d/20d horizon separately from its best
peak-return horizon so that temporary floating profit is not presented as an
executable strategy return.

The Recursive Self-Improvement (RSI) outer loop now uses a verified policy
archive. Only nodes that pass every frozen evaluation gate may reproduce;
failed or unevaluated high-return nodes cannot become parents. Each child
changes exactly one field on one of four search surfaces, is diagnosed from its
own parent's receipt, and carries an explicit policy identity and evaluation
seed into the inner-loop receipt. This makes policy credit assignment auditable
and prevents the search from improving its score by changing the examiner.
New children must additionally pass a three-seed parent/child evaluation before
they can reproduce. Every pair starts from the same frozen seed library and
uses the same random seed; production writes are disabled in research arms.

The outer factor loop is recorded through iteration 114. The current live
library is iteration 109 (`policy_0060`), with frozen 5-day dynamic-trim Hold
Sharpe 2.3256; iterations 110–114 did not replace it. The canonical
LLM-readable history, including every iteration, gate, promotion, DGM policy,
paired campaign, and the distinction between outer iterations and inner
generations, is `wiki/factor_evolution_complete_history_1_114.md`.

See `china_a_share_alpha/README.md`.

## Mingli Five-Agent Example

The `examples/mingli_5agents` demo now includes a governed BaZi school-debate
layer, book-level AHP profiles, and a reproducible public-figure hour
calibration harness. The BaZi analyst exposes seven sub-school votes, including the added
`格局横门断` paper agent derived from `examples/格局横门断.docx`. Its structured
layer is `hengmen_pattern_analysis`, focused on 月令提纲, 透干会支, 善顺恶逆,
藏干待用, and branch-group transformation boundaries.

Operational verification for this upgrade:

```bash
pytest examples/mingli_5agents/tests/test_mingli_system.py::test_five_agent_executor_returns_required_artifacts examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q
pytest examples/mingli_5agents/tests/test_reference_charts.py examples/mingli_5agents/tests/test_schema_contract_evaluator.py::test_schema_contract_score_gates_release_governance_contracts -q
pytest examples/mingli_5agents/tests/test_benchmark.py -q
```

## LLM Wiki

Framework design ideas, absorbed papers, and their citation sources are recorded
in `wiki/` using a Karpathy-style note format. Operational changes are logged in
`OPERATION_LOG.md`. This split keeps **thinking** (wiki) separate from **doing**
(operation log).

- `wiki/semas_evolution_ideas.md` — core design and absorbed methodologies.
- `wiki/references.md` — centralized BibTeX-like reference list.

## License

MIT
