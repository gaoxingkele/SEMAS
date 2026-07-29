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

See `china_a_share_alpha/README.md`.

## Project Agent Skills

The repo vendors the popular open-source converter
[book-to-skill](https://github.com/virgiliojr94/book-to-skill) as a Cursor
project skill:

```text
.cursor/skills/book-to-skill/     # canonical install
.agents/skills/book-to-skill      # junction → same tree (cross-agent)
```

Use it to turn an owned PDF/EPUB/DOCX into a structured on-demand skill.
See `.cursor/skills/README.md` and `wiki/book_to_skill.md`.

## Smart Skill And Agent Topic

`Smart_SkillandAgent/` is a topic workspace for continuously improving
GitHub-origin skills and agents. Each subproject under
`Smart_SkillandAgent/projects/` maps to one upstream repository and keeps its
own source provenance, evolution records, evaluation receipts, patches, run
artifacts, and local LLM wiki.

Use `Smart_SkillandAgent/projects/_template_skill_or_agent/` when starting a
new skill or agent evolution project.

## Mingli Five-Agent Example

Exact four-pillar calculation is a required foundation for the default BaZi and
Hengmen paths. The project installs `lunar_python` as a core dependency and
`calendar_provider=auto` now fails closed when no exact provider is available;
it never silently substitutes a civil-calendar approximation. The explicit
`approximate` provider remains only for non-Hengmen demonstrations and blocks
Hengmen pattern analysis. The regression chart for Lin Fan, 1978-04-14 06:50
in Sanming, is `WuWu / BingChen / BingWu / XinMao`.

The `examples/mingli_5agents` demo now includes a governed BaZi school-debate
layer, book-level AHP profiles, and a reproducible public-figure hour
calibration harness. The BaZi analyst exposes seven sub-school votes, including the added
`格局横门断` paper agent derived from `examples/格局横门断.docx`. Its structured
layer is `hengmen_pattern_analysis`, focused on 月令提纲, 透干会支, 善顺恶逆,
藏干待用, and branch-group transformation boundaries.

The Hengmen path now uses an independent rule engine for concrete pattern
candidates, success/failure/rescue evidence, affectionate versus adverse branch
relations, annual/monthly activation, and declared counterexample penalties.
An event without a verifiable month or counterexample row remains neutral on
that dimension; the calibration does not select the best month after the fact.
Four-storage exposure, head/foot relations, combination direction, and partial
trine candidates are available as structural evidence. Only storage clash is a
small timing activation signal; candidate structures never establish an outcome
by themselves.
The output also provides a source-pattern coverage receipt, including a distinct
month-command Yang Blade candidate rather than silently treating it as a generic
peer pattern.
Its AHP receipt keeps major-luck support, annual activation, and verifiable
monthly confirmation as separate dimensions, while accepting both precise and
coarse ten-god labels for event-theme matching.
Yang Blade and Jianlu/Yuejie candidates now require their own external control
or undertaking evidence; the day master is not incorrectly counted as a
self-failing peer.
Pattern-specific rescue logic also distinguishes food-god from hurting-officer
generation in wealth patterns, food-generated wealth that exposes killing, and
food-controlled clearing of mixed authority.
Major-luck evidence is evaluated against the selected pattern's support and
failure conditions instead of receiving an unconditional active-period bonus.
Combination evidence is directed to the selected pattern's roots: it records
whether a partner branch brings support, control, or mixed evidence, and ignores
unrelated branch disruptions.
Partial-trine and virtual-invitation structures retain their repeat count and
evidence level, but never establish a pattern candidate without exposure or
independent corroboration.
Every Hengmen chart and event result now carries named subagent receipts for
pattern selection, rescue, branch affection, event topic, palace trigger,
timing, and falsification.
The independent AHP receipt also exposes all eight criteria, normalized weights,
a reciprocal pairwise matrix, and its source-method consistency status.
It also returns a full-text rule catalog that labels each area as executable,
partial, or human-review-only, so symbolic coverage is not confused with proof
of concrete life outcomes.
For ordering-sensitive patterns, the engine records the visible-stem sequence
and marks finance/resource separation as evidence requiring corroboration rather
than treating it as an automatic success condition.
Counterexample penalties are now year-matched: every declared non-event year
must have its own annual evidence row, otherwise the falsification dimension is
neutral.
Flow-month timing also remains neutral when an explicit event month conflicts
with the event's ISO date, rather than silently choosing a calendar value.
Event-theme matching normalizes equivalent peer/friends vocabulary on both the
target and annual-evidence sides.
When multiple month-command candidates are close, the result carries the margin
and runner-up and applies a bounded AHP confidence discount instead of implying
a unique pattern.
The facts-calibration dimension combines source traceability with year-matched
counterexample evidence, and exposes both components in its receipt.
Palace triggers now distinguish constructive combinations from severe relations
and score them in the context of the declared event type.
Candidate-generation tests now explicitly cover every source pattern family,
including the distinct Yang Blade promotion.
Book-level Hengmen AHP profiles preserve the same named agent receipts, rule
catalog, and AHP architecture as the underlying rule engine.
The book-level profile also receives the same monthly and counterexample rows,
so timing and falsification do not become neutral during aggregation.
Its book-level timing agent preserves both major-luck compatibility and
annual/monthly activation according to the direct AHP source weights.
Historical Hengmen private entrypoints now delegate to the same v2 rule engine,
so downstream callers cannot silently fall back to the earlier heuristics.
Candidate ambiguity, ordering-context gaps, and virtual structures are emitted
as review flags across natal, direct AHP, and book-level outputs.
Malformed pillar labels now block pattern generation with an explicit review
flag instead of producing an unknown or fallback candidate.
That blocking state now propagates into chart and event AHP scoring as explicit
zero-score responses rather than neutral fallback scores.

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
