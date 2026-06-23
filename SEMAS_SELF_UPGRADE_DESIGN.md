# SEMAS 自升级设计：用下游任务验证并进化框架本身

> 目标：把 SEMAS 框架本身当作一个“可进化的 agent”，通过一组下游任务
>（downstream benchmark）来验证其能力，并驱动框架级进化。

---

## 1. 核心思想

SEMAS 的进化机制原本是面向“业务 agent”的：给定一个 agent，它在任务上失败，
框架进化它的 prompt/tool/topology。现在我们把这个机制**反身**（reflexive）地应用
到框架自己身上：

- **被进化的对象**不再是某个业务 agent，而是 SEMAS 框架的“元配置”：
  - `Mutator` 的系统 prompt；
  - `Orchestrator` 的触发策略（cooldown、错误模式阈值）；
  - `Sandbox` 的白名单策略；
  - `Evaluator` 的默认 metric 组合；
  - 插件选择策略。

- **下游任务**是一组 mini benchmark，每个任务代表框架必须具备的一项能力。

- **验证方式**：用当前框架版本跑 benchmark，统计通过率、进化成本、回归率等
  指标。

- **进化方式**：当某个任务失败时，框架像进化业务 agent 一样进化自己的元配置，
  然后重跑 benchmark，直到通过或达到成本上限。

---

## 2. 下游任务分类

我们把任务分为六类，每类对应 SEMAS 的一个核心能力：

| 类别 | 任务示例 | 验证的能力 |
|---|---|---|
| **Tool Evolution** | 日期差计算工具进化 | `Mutator.mutate_tool` + `Sandbox` |
| **Prompt Evolution** | 分布漂移后的 prompt 自适应 | `Mutator.mutate_prompt` |
| **Few-shot Evolution** | 从失败样本生成有效 few-shot | `Mutator.mutate_few_shot` |
| **Topology Evolution** | 多智能体 reviewer 拓扑进化 | `TopologyGenome` + orchestration |
| **Regression Gate** | 进化后旧任务仍通过 | `Evaluator` regression suite |
| **Plugin Extensibility** | FunctionEvolve 插件收敛 | `PluginRegistry` + plugin pipeline |
| **Safety** | 生成危险代码被沙盒拦截 | `Sandbox` AST whitelist |

---

## 3. 下游任务定义格式

每个任务是一个 YAML 文件：

```yaml
id: math_tool_evolution_v1
category: tool_evolution
description: |
  The framework must evolve a math agent so that it correctly computes
  the number of days between two ISO dates.
setup:
  agent_name: math_solver
  initial_genome: benchmarks/semas_self_upgrade/fixtures/math_solver_v1.yaml
  executor: deterministic_math_executor  # or llm_executor
input:
  start: "2024-01-01"
  end: "2024-01-10"
expected:
  output: 9
evaluation:
  metrics:
    - exact_match
  pass_threshold: 1.0
  allow_evolution: true
  max_evolution_rounds: 5
```

`run_benchmark.py` 会加载所有任务，实例化一个 `Orchestrator`，跑任务，允许进化，
最后输出报告。

---

## 4. 框架级指标（Framework Metrics）

单个任务通过不够，我们需要框架级指标来防止“过拟合某个任务”：

| 指标 | 定义 | 目标 |
|---|---|---|
| `pass_rate` | 通过任务数 / 总任务数 | ≥ 0.9 |
| `mean_evolution_rounds` | 所有任务平均进化轮数 | ≤ 3 |
| `llm_call_cost` | 进化过程中 LLM API 调用总数 | ≤ budget |
| `regression_rate` | 进化后旧任务失败率 | 0 |
| `safety_violation_count` | 沙盒未拦截的危险代码数 | 0 |
| `convergence_rate` | 在 max_rounds 内收敛的任务比例 | ≥ 0.8 |

这些指标由 `metrics.py` 汇总。

---

## 5. 框架基因组（Framework Genome）

我们把 SEMAS 的元配置封装成一个特殊的 `AgentGenome`：

```yaml
name: semas_meta_framework
role: framework_evolver
system_prompt: |
  You are the meta-evolver for the SEMAS framework. Your job is to improve
  the framework's prompts, policies, and tools based on benchmark failures.

# 框架级工具/策略配置
tools:
  - default_mutator_prompt
  - default_sandbox_policy
  - default_evolution_trigger_policy

few_shot_examples: []

meta:
  framework_components:
    mutator_prompts:
      prompt_mutation: benchmarks/semas_self_upgrade/framework_genome/prompt_mutation_v1.txt
      tool_mutation: benchmarks/semas_self_upgrade/framework_genome/tool_mutation_v1.txt
    trigger_policy:
      cooldown_tasks: 5
      max_versions_without_improvement: 3
    sandbox_policy:
      allowed_modules:
        - math
        - datetime
        - json
```

`evolve_semas.py` 会把这个 genome 加载进 `Orchestrator`，把 benchmark harness 作为
`ExecutorFn`，从而形成一个“SEMAS 进化 SEMAS”的闭环。

---

## 6. 自升级闭环

```text
┌─────────────────────────────────────────────────────────────┐
│              SEMAS Meta-Orchestrator                         │
│  (evolves the SEMAS framework genome)                        │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│           Downstream Benchmark Executor                      │
│  run_benchmark(current_framework_genome)                     │
│   ├── tool_evolution tasks                                   │
│   ├── prompt_evolution tasks                                 │
│   ├── regression_gate tasks                                  │
│   ├── plugin_convergence tasks                               │
│   └── safety tasks                                           │
└──────┬──────────────────────────────────────────────────────┘
       │ returns pass_rate, regression_rate, failing_tasks
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Meta-Evaluator                                  │
│  Score = weighted(pass_rate, cost, regression_rate)          │
└──────┬──────────────────────────────────────────────────────┘
       │ failure pattern
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Meta-Mutator                                    │
│  Evolve framework genome:                                    │
│    - rewrite mutator prompts                                 │
│    - adjust cooldown / trigger thresholds                    │
│    - extend sandbox whitelist                                │
│    - tune plugin selection policy                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 最小可行实现路线

### Phase 1: 静态 Benchmark（当前可交付）

- 定义 6 个 YAML 任务。
- 实现 `run_benchmark.py`：加载任务、跑任务、生成报告。
- 实现 `metrics.py`：计算框架级指标。
- 不启用进化，只做“当前框架能力摸底”。

### Phase 2: 框架基因组

- 把 `Mutator` 的系统 prompt、`Sandbox` 白名单、`Orchestrator` 触发参数抽象成
  `framework_genome/` 下的文件。
- 实现 `load_framework_genome()` 和 `apply_framework_genome()`。

### Phase 3: 自升级闭环

- 实现 `evolve_semas.py`：
  - 用当前 framework genome 初始化 SEMAS；
  - 把 benchmark 作为 executor；
  - 当任务失败时，进化 framework genome；
  - 重跑 benchmark；
  - 循环直到通过或耗尽 budget。

### Phase 4: 安全与审计

- 所有 framework genome 进化事件写入 `benchmarks/semas_self_upgrade/archive/`。
- 每次进化必须通过 regression suite（旧任务不能退化）。
- 设置成本上限，防止元进化失控。

---

## 8. 风险与约束

1. **递归失控**：SEMAS 进化 SEMAS 是一个递归过程，必须设置 hard budget 和
   regression gate。
2. **评估成本高**：每个 benchmark 任务本身可能调用 LLM，整体成本会放大。
   建议先用确定性 toy executor 降低验证成本。
3. **元进化过拟合**：framework genome 可能只学会通过 benchmark 而不是真正变强。
   需要保留 holdout 任务集。
4. **安全性**：自升级不能绕过 `Sandbox` 或修改 `SelfModificationPolicy`。

---

## 9. 与现有插件架构的关系

- `FunctionEvolve` 插件可用来进化 framework genome 中的数值超参数。
- 未来 `SIA` 插件可用来微调一个“framework critic”模型，预测哪些元配置会成功。
- `Gödel Agent` 模式**禁止**用于自升级，除非用户明确启用并配置严格审批门。
