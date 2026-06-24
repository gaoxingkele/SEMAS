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

## LLM Wiki

Framework design ideas, absorbed papers, and their citation sources are recorded
in `wiki/` using a Karpathy-style note format. Operational changes are logged in
`OPERATION_LOG.md`. This split keeps **thinking** (wiki) separate from **doing**
(operation log).

- `wiki/semas_evolution_ideas.md` — core design and absorbed methodologies.
- `wiki/references.md` — centralized BibTeX-like reference list.

## License

MIT
