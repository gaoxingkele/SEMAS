# SEMAS Self-Upgrade Benchmark

This benchmark treats the SEMAS framework itself as an evolving agent. It runs
a suite of downstream tasks, measures framework-level metrics, and can drive
meta-evolution of the framework's own prompts, policies, and tools.

## Structure

```text
benchmarks/semas_self_upgrade/
  README.md                 # This file
  tasks/                    # YAML task definitions
  fixtures/                 # Initial agent/topology genomes for tasks
  framework_genome/         # SEMAS meta-configuration genome
  archive/                  # Historical framework evolution events
  deterministic_mutator.py  # Reproducible mutator for CI/benchmarking
  metrics.py                # Framework-level metric calculators
  run_benchmark.py          # Run all tasks and emit report
  evolve_semas.py           # Meta-evolution loop (Phase 3)
```

## Quick Start

Run the benchmark without meta-evolution (Phase 1 — capability baseline):

```bash
cd C:/aicoding/semas_framework
python -m benchmarks.semas_self_upgrade.run_benchmark
```

Emit only JSON (useful for the meta-evolution script):

```bash
python -m benchmarks.semas_self_upgrade.run_benchmark --json
```

Expected output: a JSON report with `pass_rate`, `mean_evolution_rounds`,
`regression_rate`, etc.

## Tasks

| Task | Category | What it validates |
|---|---|---|
| `math_tool_evolution` | tool_evolution | `Mutator` + `Sandbox` can produce a correct date-diff tool |
| `prompt_robustness` | prompt_evolution | `Mutator.mutate_prompt` adapts to a shifted instruction |
| `regression_gate` | regression | New genome still passes old tasks |
| `plugin_convergence` | plugin_extensibility | `FunctionEvolve` plugin converges to target formula |
| `sandbox_safety` | safety | Dangerous code is rejected by `Sandbox` |
| `multi_agent_topology` | topology | `TopologyGenome` is loadable and executable |

## Meta-Evolution (Phase 3)

```bash
python -m benchmarks.semas_self_upgrade.evolve_semas
```

This script loads the framework genome, runs the benchmark as the executor, and
triggers evolution of the framework's own configuration when tasks fail.

## Notes

- The benchmark uses a `BenchmarkMutator` that produces deterministic, correct
  variants. This keeps the benchmark runnable without LLM API keys while still
  exercising the full SEMAS pipeline.
- For real-world self-improvement, replace `BenchmarkMutator` with the default
  LLM-backed `Mutator` or a fine-tuned meta-mutator.
