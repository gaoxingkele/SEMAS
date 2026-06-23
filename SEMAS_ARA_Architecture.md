---
artifact: semas_architecture
title: SEMAS 整体技术架构（ARA 移植版）
review_version: local-1.0
source_of_truth:
  - README.md
  - semas/genome/genome.py
  - semas/genome/repository.py
  - semas/evaluator/evaluator.py
  - semas/mutator/mutator.py
  - semas/orchestrator/orchestrator.py
  - semas/sandbox/sandbox.py
  - semas/plugins/base.py
  - semas/plugins/registry.py
  - semas/plugins/function_evolve/
  - examples/math_agents/run_demo.py
  - examples/mingli_5agents/evolution.py
  - examples/mingli_5agents/benchmark.py
  - tests/test_orchestrator.py
  - tests/test_genome.py
---

# SEMAS 整体技术架构（ARA 方法）

## 1. 一句话摘要

SEMAS（Self-Evolving Multi-Agent System）是一个在**冻结权重 LLM 之上**运行的自进化多智能体框架。它把 agent 抽象为可版本化的基因组（`AgentGenome`），通过 `Evaluator` 打分、`Mutator` 生成变异、`Sandbox` 安全验证、`Orchestrator` 执行双循环进化，实现对 **prompt、tool、topology、few-shot、memory** 的选择式进化，并支持回滚与审计。

---

## 2. 问题（Problem）

1. **大模型权重冻结后难以持续改进**：无法通过梯度下降让模型 itself 变强，必须把“进化”转移到可编辑工件上。
2. **手工 prompt/tool 难以适应分布漂移**：任务分布、生成引擎行为、用户反馈都会变化，固定策略会退化。
3. **多智能体协作结构也会过时**：节点职责、调用顺序、投票机制需要根据历史执行数据调整。
4. **进化必须可控制**：不能无限制地让 LLM 自动改写系统，否则会引入回归、安全漏洞或成本爆炸。
5. **需要可移植的架构**：不同业务场景（GEO、命理、数学、代码等）应能复用同一套进化机制，只替换领域相关的 executor、metrics 和约束。

---

## 3. 核心论断（Claims）

| ID | 论断 | 状态 | 证伪条件 | 证据 | 依赖 | 标签 |
|---|---|---|---|---|---|---|
| C01 | SEMAS 提供统一的、版本化的 AgentGenome 抽象，能把 prompt、tool、topology、few-shot、meta 封装为可进化的“基因”。 | supported | 无法构造 `AgentGenome` 或 `evolve_from()` 不能产生新版本。 | E01 `semas/genome/genome.py` | - | genome, versioning |
| C02 | 框架采用**选择式进化**，不修改 LLM 权重，仅对可编辑工件做变异、评估、提交。 | supported | 发现框架要求对 LLM 做 fine-tuning 才能进化。 | E02 `README.md`, E03 `semas/mutator/mutator.py` | C01 | selection_evolution, frozen_llm |
| C03 | `Orchestrator` 实现内循环（执行→评估）和外循环（失败→变异→沙盒→选择→提交）。 | supported | `orchestrator.py` 不存在 `evolve()` 或不调用 `Mutator`/`Evaluator`。 | E04 `semas/orchestrator/orchestrator.py` | C01, C02 | dual_loop, orchestration |
| C04 | 进化触发受控：有 cooldown 间隔，且仅对新错误模式触发，防止成本爆炸和震荡。 | supported | `_should_evolve()` 永远返回 true 或没有 cooldown。 | E04 | C03 | cost_control, trigger_policy |
| C05 | `Mutator` 支持对 system prompt、few-shot、tool code、topology 四类工件做 LLM 驱动变异。 | supported | `mutator.py` 缺少任意一类变异方法。 | E03 | C02 | mutation, llm_driven |
| C06 | `Sandbox` 对生成代码做 AST 白名单、超时、进程隔离，防止不可信代码破坏环境。 | supported | `sandbox.py` 不检查 AST 或不使用 subprocess。 | E05 `semas/sandbox/sandbox.py` | C05 | safety, sandbox |
| C07 | `Evaluator` 提供可插拔 metric 和回归测试门；进化后的候选必须通过回归测试才能提交。 | supported | `Evaluator` 没有 `regression_tests` 或 `_passes_regression_gate` 不生效。 | E06 `semas/evaluator/evaluator.py` | C03 | evaluation, regression_gate |
| C08 | `GenomeRepository` 支持版本 lineage、回滚、latest_version 查询，实现可审计的进化历史。 | supported | `repository.py` 不能回滚或没有 parent_version 记录。 | E07 `semas/genome/repository.py` | C01 | lineage, rollback |
| C09 | 框架与具体 executor 解耦：用户可以注入任意 LLM 调用、工具链或确定性函数作为 `ExecutorFn`。 | supported | `Orchestrator` 强制绑定某个 LLM client 且不能替换 executor。 | E04, E08 `examples/math_agents/run_demo.py` | C03 | portability, executor |
| C10 | `examples/mingli_5agents/evolution.py` 在基础框架之上实现了种群级进化、Pareto 选择、metric floors、archive 与 feedback memory。 | supported | `evolution.py` 不存在或不使用 `MingliPopulationEvolver`。 | E09 `examples/mingli_5agents/evolution.py` | C01-C08 | population_evolution, advanced_example |
| C11 | SEMAS 的进化抽象可直接映射到 GEO 领域的 AgenticGEO（MAP-Elites archive ↔ `GenomeRepository`，critic ↔ `Evaluator`，rewriter ↔ `Mutator`）。 | supported | `../geo-benchmark/README.md` 中没有该映射表。 | E10 `../geo-benchmark/README.md`, E11 `../geo-benchmark/docs/summary.md` | C01-C09 | geo, agenticgeo |
| C12 | SEMAS 提供可插拔的进化插件层（`MutatorStrategy`、`CandidateOptimizer`、`WeightUpdateStrategy`、`SelfModificationPolicy`），允许 FunctionEvolve、SIA、Gödel Agent 等外部方法论接入而不修改核心。 | supported | `semas/plugins/` 不存在或 `Orchestrator` 不接受 `plugin_registry`。 | E14 `semas/plugins/base.py`, E15 `semas/plugins/registry.py`, E16 `semas/orchestrator/orchestrator.py` | C01-C11 | plugins, extensibility |

---

## 4. 核心概念（Concepts）

| 概念 | 记号 | 定义 | 边界条件 | 相关概念 |
|---|---|---|---|---|
| **Genome** | — | 对 agent 可编辑工件的版本化描述。 | 必须包含 `name`、`role`、`system_prompt`；可选 tools/topology/few_shot/meta。 | AgentGenome, ToolGenome, TopologyGenome |
| **AgentGenome** | `AgentGenome` | 一个执行者的完整配置，即“DNA”。 | `version` 递增，`parent_version` 记录父版本。 | Genome, ExecutorFn |
| **ToolGenome** | `ToolGenome` | 可进化的 Python 函数工具。 | `source_code` 必须通过 Sandbox AST 检查；`signature` 自动提取。 | Mutator, Sandbox |
| **TopologyGenome** | `TopologyGenome` | 多智能体协作的有向无环图。 | `execution_mode` 支持 serial / parallel / hierarchical。 | Orchestrator, AgentGenome |
| **GenomeRepository** | `GenomeRepository` | 文件系统 backed 的版本库，按 `agents/<name>/vN.json` 存储。 | 同一 name 下版本号唯一；回滚产生新版本而非删除旧版本。 | Lineage, Rollback |
| **Evaluator** | `Evaluator` | 评分器，注册 metric 并执行回归测试。 | 所有 metric 返回值 clamp 到 `[0,1]`；通过 threshold 才算 passed。 | Metric, Regression Test |
| **Metric** | `MetricFn` | `fn(task_result, expected) -> float` 的评分函数。 | 可被权重组合；异常时返回 0 并标记失败。 | Evaluator |
| **Regression Test** | `regression_tests` | 历史测试用例集合，进化候选必须全部通过。 | 未注册时回归门自动放行。 | Evaluator |
| **Mutator** | `Mutator` | 基于失败日志，调用 LLM 生成 prompt/tool/few-shot/topology 变异。 | 不保证成功，需经 Evaluator/Sandbox 过滤。 | LLMClient, AgentGenome |
| **Sandbox** | `Sandbox` | 受限子进程执行生成代码。 | AST 白名单 + 模块白名单 + 超时 + 禁止网络/文件写。 | ToolGenome |
| **Orchestrator** | `Orchestrator` | 运行双循环：内循环执行任务，外循环触发进化。 | `cooldown_tasks` 与错误模式去重控制进化频率。 | ExecutionTrace, Mutator, Evaluator |
| **ExecutionTrace** | `ExecutionTrace` | 单次任务执行的完整记录。 | 包含 input、output、evaluation、genome_version、timestamp。 | Orchestrator |
| **ExecutorFn** | `ExecutorFn` | `(AgentGenome, dict) -> dict` 的用户注入执行函数。 | 默认是 stub；真实场景替换为 LLM 调用或工具链。 | Orchestrator, AgentGenome |
| **Evolution Loop** | — | 执行→失败→变异→评估→选择→提交→（可选回滚）的闭环。 | 只有得分超过 baseline 且通过回归门才会提交。 | Orchestrator, Evaluator |
| **Population Evolution** | — | 在基础框架上预定义一组策略，批量生成候选并做 Pareto 选择。 | 需要领域相关的 `generate_population` 与 `METRIC_FLOORS`。 | MingliPopulationEvolver |
| **Error Pattern** | — | 从失败输出提取的规范化关键词，用于去重和触发判断。 | 取前 8 个单词小写。 | Orchestrator |
| **Lineage** | — | 从父版本到子版本的演化链条，包括 archive hash、selection decision。 | 存储在 `AgentGenome.meta.evolution_lineage`。 | GenomeRepository |
| **Rollback** | — | 当新版本平均得分低于父版本时，回退到父版本并产生新的 latest version。 | 不删除历史版本，保持可审计。 | GenomeRepository, Orchestrator |
| **PluginRegistry** | `PluginRegistry` | 收集并暴露进化插件。 | 支持程序化注册、entry_points、配置驱动三种加载方式。 | Orchestrator |
| **MutatorStrategy** | `MutatorStrategy` | 插件化的候选生成策略。 | 实现 `mutate(agent, failure_logs, context) -> list[AgentGenome]`。 | PluginRegistry, Orchestrator |
| **CandidateOptimizer** | `CandidateOptimizer` | 插件化的候选精炼策略。 | 实现 `optimize(candidate, context) -> AgentGenome`。 | PluginRegistry, Orchestrator |
| **WeightUpdateStrategy** | `WeightUpdateStrategy` | 插件化的权重更新策略（SIA 风格）。 | 实现 `should_update_weights()` 与 `update_weights()`。 | PluginRegistry, Orchestrator |
| **SelfModificationPolicy** | `SelfModificationPolicy` | Gödel-Agent 式自改审批策略。 | 决定自改代码是否允许、失败是否回滚。 | PluginRegistry, Orchestrator |

---

## 5. 方法 / 架构（Solution / Method）

### 5.1 总体结构

```text
┌─────────────────────────────────────────────────────────────┐
│                      User Application                        │
│  (examples/math_agents, examples/mingli_5agents, GEO, ...)   │
└──────────────────────┬──────────────────────────────────────┘
                       │ defines ExecutorFn, metrics, constraints
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       Orchestrator                           │
│  • run_task(): inner loop (execute → evaluate → record)      │
│  • evolve(): outer loop (mutate → sandbox → select → commit) │
│  • rollback_if_regressed()                                   │
└──────┬─────────────────────┬────────────────┬───────────────┘
       │                     │                │
       ▼                     ▼                ▼
┌─────────────┐      ┌─────────────┐   ┌─────────────┐
│   Executor  │      │  Evaluator  │   │   Mutator   │
│  (injectable)│      │  • metrics  │   │  • prompt   │
│             │      │  • regression│   │  • few-shot │
└─────────────┘      │  • threshold │   │  • tool     │
                     └──────┬──────┘   │  • topology │
                            │          └──────┬──────┘
                            │                 │
                            ▼                 ▼
                    ┌─────────────┐    ┌─────────────┐
                    │   Sandbox   │    │  LLMClient  │
                    │  (tool exec)│    │  (variation)│
                    └─────────────┘    └─────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   GenomeRepository                           │
│  agents/<name>/v1.json, v2.json ...                         │
│  tools/<name>/v1.json ...                                   │
│  topologies/<name>/v1.json ...                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 组件职责

| 组件 | 核心职责 | 关键类/函数 | 可移植性 |
|---|---|---|---|
| Genome | 定义“什么可以被进化” | `AgentGenome`, `ToolGenome`, `TopologyGenome`, `FewShotExample` | 通用，直接复用 |
| Repository | 持久化、版本化、回滚 | `GenomeRepository.save_agent/load_agent/rollback_agent` | 通用，可替换为 DB |
| Evaluator | 评分与回归门 | `Evaluator.register_metric`, `evaluate`, `run_regression_suite` | 通用，领域 metric 需注入 |
| Mutator | 基于失败生成变异 | `mutate_prompt`, `mutate_few_shot`, `mutate_tool`, `mutate_topology` | 通用，prompt 可定制 |
| Sandbox | 安全执行生成代码 | `Sandbox.run_code`, `run_tool`, `_is_safe_ast` | 通用，策略可配置 |
| Orchestrator | 进化主循环与触发策略 | `run_task`, `evolve`, `_should_evolve`, `rollback_if_regressed` | 通用，参数可调 |
| LLMClient | 为 Mutator 提供文本生成 | `semas/utils/llm_client.py` | 可替换为任意 OpenAI-compatible 接口 |

### 5.3 数据模型

**AgentGenome**（简化）：

```yaml
name: math_solver
role: date_and_math_assistant
system_prompt: "You are a precise math assistant..."
few_shot_examples:
  - input: "..."
    output: "..."
    reasoning: "..."
tools: []
topology: null
version: 1
parent_version: null
meta:
  domain: date_arithmetic
```

**ToolGenome**（自动生成示例）：

```python
name: calculate_date_diff
description: Calculates days between two ISO dates
source_code: |
  from datetime import datetime
  def calculate_date_diff(start: str, end: str) -> int:
      return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
signature: calculate_date_diff(start: str, end: str) -> int
version: 1
```

**TopologyGenome** 用于表达多智能体协作：

```yaml
name: review_pipeline
nodes: [planner, writer, reviewer]
edges:
  - [planner, writer]
  - [writer, reviewer]
execution_mode: serial
```

### 5.4 双循环生命周期

**内循环（`Orchestrator.run_task`）**：

1. 从 `GenomeRepository` 加载当前最新 `AgentGenome`。
2. 调用用户注入的 `ExecutorFn(agent, task_input)` 得到 `task_output`。
3. `Evaluator.evaluate({**task_input, **task_output}, expected)` 得到 `EvaluationResult`。
4. 记录 `ExecutionTrace`。
5. 若未通过且允许进化，提取 `error_pattern`，判断是否满足 `_should_evolve(pattern)`。

**外循环（`Orchestrator.evolve`）**：

1. 收集最近 10 条失败日志。
2. 生成候选：
   - prompt 变异（必做）
   - few-shot 变异（如果有失败日志）
   - tool 变异（若失败看起来是计算/解析类，且 sandbox 通过）
3. 对最近失败任务逐一执行候选，用 `Evaluator` 评分。
4. 选择得分最高且超过 baseline 的候选。
5. 运行 `_passes_regression_gate(candidate)` 回归测试。
6. 全部通过后 `repo.save_agent(best_candidate)`，并记录错误模式。
7. 后续可调用 `rollback_if_regressed()` 比较新版本与父版本的平均得分，必要时回滚。

### 5.5 变异策略细节

| 变异类型 | 输入 | 输出 | 关键约束 |
|---|---|---|---|
| Prompt | `AgentGenome` + failure logs | 新 `AgentGenome`（system_prompt 改变） | 保持 role 与约束，仅输出新 prompt |
| Few-shot | `AgentGenome` + 最近失败日志 | 新 `AgentGenome`（追加一个 FewShotExample） | 必须能解析 Input/Output/Reasoning |
| Tool | `AgentGenome` + failure logs | 新 `ToolGenome` + 新 `AgentGenome`（tools 列表追加） | 代码必须通过 `Sandbox` 测试调用 |
| Topology | `TopologyGenome` + failure logs | 新 `TopologyGenome` | 当前默认策略：加入 reviewer 节点 |

### 5.6 扩展点（方便移植时替换）

1. **ExecutorFn**：把 `semas/orchestrator/orchestrator.py` 里的 `_default_executor` 替换为你的 LLM 调用、ReAct 循环、确定性函数或外部 API。
2. **Metrics**：通过 `Evaluator.register_metric(name, fn)` 注入领域评分函数（如 GEO 的 PAWC、命理的 citation/safety、数学的正确率）。
3. **Mutation Prompts**：继承 `Mutator` 并覆盖系统 prompt，以适配不同领域的生成规范。
4. **Sandbox Policy**：调整 `allowed_modules`、`FORBIDDEN_MODULES`、`timeout`，允许或禁止特定库。
5. **Population Evolution**：参考 `MingliPopulationEvolver`，定义自己的 `generate_population`、Pareto 目标向量和 `METRIC_FLOORS`。
6. **Repository Backend**：实现接口等价的 `GenomeRepository`（如 SQLite/PostgreSQL 版本）即可替换文件系统存储。

### 5.7 插件层（Plugin Layer）

为了在不修改 SEMAS 核心代码的前提下吸纳 FunctionEvolve、SIA、Gödel Agent 等外部进化方法论，框架新增 `semas/plugins/` 层。

#### 插件接口

| 接口 | 作用 | 典型实现 |
|---|---|---|
| `MutatorStrategy` | 替代或增强默认 `Mutator` 的候选生成 | `FunctionEvolveToolMutator`（AST 树编辑）、未来 `GodelSelfModificationMutator` |
| `CandidateOptimizer` | 对候选做精炼后再进入选择 | `FunctionEvolveToolOptimizer`（常量局部搜索） |
| `WeightUpdateStrategy` | 在 harness 更新之外更新模型权重 | `SIAWeightUpdate`（LoRA 测试时训练） |
| `SelfModificationPolicy` | 审批 Gödel-Agent 式自改代码 | `StrictGodelPolicy`（白名单 + 沙盒 + 人工门） |

#### 插件注册方式

1. **程序化注册**：
   ```python
   from semas.plugins import PluginRegistry
   from semas.plugins.function_evolve import FunctionEvolveToolMutator

   plugins = PluginRegistry()
   plugins.register_mutator_strategy(FunctionEvolveToolMutator())
   ```

2. **entry_points 自动发现**：
   ```toml
   [project.entry-points."semas.mutator_strategy"]
   function_evolve = "semas.plugins.function_evolve:FunctionEvolveToolMutator"
   ```

3. **配置文件驱动**：
   ```python
   plugins.load_from_config({
       "mutator_strategies": ["semas.plugins.function_evolve:FunctionEvolveToolMutator"],
       "candidate_optimizers": ["semas.plugins.function_evolve:FunctionEvolveToolOptimizer"],
   })
   ```

#### 插件在 Orchestrator 中的运行位置

```text
Orchestrator.evolve()
├── 默认 Mutator 生成候选
├── 每个 MutatorStrategy 生成额外候选
├── 每个 CandidateOptimizer 精炼候选
├── _select_candidate() 选择最优
├── 每个 WeightUpdateStrategy 可选地更新权重
└── 通过 Regression Gate 后提交
```

所有插件候选与默认候选走同样的 `Evaluator` / `Sandbox` / `Regression Gate`，因此插件能力虽强，但仍受 SEMAS 安全边界的约束。

---

## 6. 约束与不变量（Constraints）

1. **权重冻结不变量**：SEMAS 不修改任何 LLM 权重；所有进化发生在 prompt、tool、topology、few-shot、memory 上。
2. **版本只增不减**：`GenomeRepository` 不删除旧版本，回滚产生新版本，保证 lineage 完整。
3. **进化必须通过回归门**：`_passes_regression_gate` 失败则候选不会被提交。
4. **工具代码必须通过沙盒**：`Mutator.mutate_tool` 生成的代码必须经 `Sandbox.run_tool` 成功执行。
5. **成本控制**：进化受 `cooldown_tasks` 与错误模式去重双重限制，避免 LLM 调用爆炸。
6. **失败模式稳定化**：错误模式只取前 8 个单词并小写，用于去重；相同模式不会重复触发进化。
7. **Metric 值域**：所有 metric 返回值被 clamp 到 `[0, 1]`，便于加权组合与阈值判断。
8. **可离线运行**：`examples/math_agents` 和 `tests/` 无需外部 API 即可完成核心进化循环验证。

---

## 7. 实验 / 验证（Experiments）

### 7.1 单元测试

| 测试文件 | 验证内容 | 运行方式 |
|---|---|---|
| `tests/test_genome.py` | Genome 创建、evolve_from、Repository 存取/回滚、Topology 前后继 | `pytest tests/test_genome.py` |
| `tests/test_orchestrator.py` | 任务通过时不进化、cooldown 阻止进化、失败时触发进化 | `pytest tests/test_orchestrator.py` |

### 7.2 最小可运行 demo

```bash
cd examples/math_agents
python run_demo.py
```

预期行为：
- 第一次执行：agent 没有 tool，回答错误（date diff off by one）。
- 触发 evolution：`Mutator` 生成一个 `calculate_date_diff` 工具，`Sandbox` 验证通过。
- 第二次执行：使用进化后的 genome，回答正确。

### 7.3 种群级进化示例

```bash
cd examples/mingli_5agents
python run_demo.py
# 或
python cli.py --repo .semas_mingli_repo evolve --input birth.json --feedback feedback.json --validate-on-input
python cli.py --repo .semas_mingli_repo benchmark
```

验证维度：
- `MingliPopulationEvolver.generate_population` 产生 6 个候选。
- 每个候选在训练任务上评估，计算平均得分、mean metrics、Pareto front。
- 应用 `METRIC_FLOORS`（citation ≥0.95、safety=1.0 等）。
- 通过回归测试后提交；进化事件写入 `archives/mingli_evolution.json`。

### 7.4 GEO 集成验证

```bash
cd ../geo-benchmark/semas-integration
python run_semas_geo.py --dataset geo-bench --max_samples 100 --evolutions 5
```

用于验证 SEMAS 进化机制是否能迁移到 GEO 领域：把 GEO rewrite 方法作为 `ToolGenome`，把可见性指标作为 `Evaluator` metric。

---

## 8. 相关技术（Related Work）

| 外部技术 | 核心思想 | SEMAS 映射 |
|---|---|---|
| **AgenticGEO** | MAP-Elites 策略档案 + Co-evolving Critic + 多轮重写 | 策略档案 ↔ `GenomeRepository` + `MingliEvolutionArchive`；Critic ↔ `Evaluator`；重写策略 ↔ `Mutator` |
| **AutoGEO** | 规则抽取 + prompt/RL 重写 | 规则可封装为 `ToolGenome`；RL 部分可替换为选择式进化 |
| **Multi-Agent GEO** | 多智能体可复用策略学习 | `TopologyGenome` 表达多智能体；策略复用通过 archive 实现 |
| **FeatGEO** | NSGA-II 特征级多目标优化 | `MingliPopulationEvolver` 的 Pareto front 选择提供同构能力 |
| **E-GEO** | 迭代式 prompt 元优化 | 对应 `Mutator.mutate_prompt` + `Orchestrator` 外循环 |

---

## 9. 移植指南（Porting Guide）

### 9.1 最小移植步骤

1. **引入核心模块**
   - 复制 `semas/genome/`、`semas/evaluator/`、`semas/mutator/`、`semas/sandbox/`、`semas/orchestrator/`、`semas/utils/llm_client.py` 到你的项目。
   - 安装依赖：`pydantic`, `pyyaml`，可选 `openai`/`httpx`。

2. **定义领域 Genome**
   - 继承或直接复用 `AgentGenome`。
   - 在 `meta` 里放置领域特定字段（如 GEO 的 `visibility_target`，命理的 `tradition_sources`）。

3. **实现 ExecutorFn**
   - `def my_executor(agent: AgentGenome, task_input: dict) -> dict:`
   - 返回 dict 必须包含可被 metric 读取的字段（如 `output`、`tool_used`、`sources` 等）。

4. **注册 Evaluator Metrics**
   - `evaluator.register_metric("domain_score", my_metric_fn)`
   - 添加历史回归测试：`evaluator.add_regression_test(...)`

5. **配置 Mutator（可选覆盖 prompt）**
   - 默认 `Mutator` 已可用；如需特定风格，可继承并覆盖系统 prompt。

6. **配置 Sandbox**
   - 允许业务需要的模块：`Sandbox(allowed_modules={"math", "datetime", "json", "re", "my_domain_lib"})`

7. **实例化 Orchestrator 并运行**
   ```python
   orch = Orchestrator(
       repository=repo,
       evaluator=evaluator,
       mutator=mutator,
       sandbox=sandbox,
       agent_name="my_agent",
       executor=my_executor,
       cooldown_tasks=5,
   )
   trace = orch.run_task({"query": "..."}, expected={"output": "..."})
   ```

8. **（可选）实现 Population Evolution**
   - 参考 `examples/mingli_5agents/evolution.py` 实现 `MyPopulationEvolver`。
   - 定义 `generate_population`、`METRIC_FLOORS`、archive 路径。

### 9.2 不必须迁移的内容

- `examples/mingli_5agents/` 是命理领域示例，移植时可根据需要保留或删除。
- `../geo-benchmark/` 是 GEO 研究基准，只有在目标领域是 GEO 时才需要。
- `.tmp_*` 目录是临时探测数据，不应纳入生产代码。

### 9.3 常见陷阱

- **默认 executor 是 stub**：如果不注入真实 executor，框架只会回显输入，无法验证领域效果。
- **Sandbox 模块白名单过严**：生成 tool 需要第三方库时，务必加入 `allowed_modules`。
- **metric 没有 clamp**：虽然 `Evaluator` 会 clamp，但建议自定义 metric 内部也做边界处理。
- **cooldown 过短导致进化太频繁**：生产环境建议 `cooldown_tasks >= 10`。

---

## 10. 证据索引（Evidence）

| 证据 ID | 文件路径 | 说明 | 支撑的论断 |
|---|---|---|---|
| E01 | `semas/genome/genome.py` | `AgentGenome`, `ToolGenome`, `TopologyGenome`, `evolve_from` | C01, C08 |
| E02 | `README.md` | 框架定位、进化循环、核心概念 | C02 |
| E03 | `semas/mutator/mutator.py` | prompt/few-shot/tool/topology 变异 | C02, C05 |
| E04 | `semas/orchestrator/orchestrator.py` | 双循环、触发策略、选择、回滚 | C03, C04, C09 |
| E05 | `semas/sandbox/sandbox.py` | AST 检查、子进程隔离、超时 | C06 |
| E06 | `semas/evaluator/evaluator.py` | metric 注册、加权评分、回归测试 | C07 |
| E07 | `semas/genome/repository.py` | 版本化存储、latest、rollback | C08 |
| E08 | `examples/math_agents/run_demo.py` | 最小端到端进化 demo | C09 |
| E09 | `examples/mingli_5agents/evolution.py` | 种群级进化、Pareto、metric floors、archive | C10 |
| E10 | `../geo-benchmark/README.md` | SEMAS 与 GEO 的映射 | C11 |
| E11 | `../geo-benchmark/docs/summary.md` | AgenticGEO 与 SEMAS 的对应关系 | C11 |
| E12 | `tests/test_genome.py` | Genome 与 Repository 的自动化验证 | C01, C08 |
| E13 | `tests/test_orchestrator.py` | Orchestrator 触发与 cooldown 的自动化验证 | C03, C04 |
| E14 | `semas/plugins/base.py` | 插件接口 Protocol 定义 | C12 |
| E15 | `semas/plugins/registry.py` | 插件注册、entry_points、配置驱动加载 | C12 |
| E16 | `semas/orchestrator/orchestrator.py` | Orchestrator 调用插件 pipeline | C12 |
| E17 | `semas/plugins/function_evolve/` | FunctionEvolve 插件实现（AST mutator + optimizer） | C12 |
| E18 | `semas/plugins/function_evolve/tests/test_function_evolve_plugin.py` | 插件自动化测试 | C12 |

---

## 11. 探索树 / 架构演进（Trace）

```text
问题：冻结权重 LLM 如何持续改进？
├── 方案 A：Fine-tuning / RLHF
│   └── 排除：成本高、需要训练数据、与 SEMAS“frozen-weight”定位冲突
├── 方案 B：人工迭代 prompt/tool
│   └── 排除：无法自动适应分布漂移
└── 方案 C：对可编辑工件做选择式进化
    ├── C1：需要版本化基因表示 → AgentGenome / ToolGenome / TopologyGenome
    ├── C2：需要持久化与回滚 → GenomeRepository
    ├── C3：需要评分机制 → Evaluator + metrics + regression tests
    ├── C4：需要安全执行生成代码 → Sandbox
    ├── C5：需要自动生成变异 → Mutator (LLM-driven)
    ├── C6：需要编排进化闭环 → Orchestrator (dual loop)
    └── C7：需要种群级高级用法 → MingliPopulationEvolver
```

---

## 12. Level-2 自评（Self Assessment）

| 维度 | 得分 | 说明 |
|---|---|---|
| D1 Evidence Relevance | 4/5 | 每个论断都映射到具体源码或示例。 |
| D2 Falsifiability | 4/5 | 可通过单元测试、demo、benchmark 直接证伪。 |
| D3 Scope Calibration | 4/5 | 明确区分框架通用层与领域示例层。 |
| D4 Argument Coherence | 5/5 | 问题-论断-概念-方法-证据-移植指南形成闭环。 |
| D5 Exploration Integrity | 4/5 | 探索树展示了关键设计决策与排除项。 |
| D6 Methodological Rigor | 4/5 | 提供了单元测试、回归门、沙盒、版本控制等工程约束。 |

**总体评级**：Accept（可作为 SEMAS 移植与二次开发的参考架构文档）。
