# SEMAS 与 Gödel Agent / FunctionEvolve / SIA 的对比及插件化整合方案

## 0. 链接对应关系勘误

你给出的几组链接存在错位，先校正如下，避免后续讨论混淆：

| 你给出的 arXiv | 你给出的 GitHub | 实际对应关系 | 正确代码仓库 |
|---|---|---|---|
| [2410.04444](https://arxiv.org/abs/2410.04444) | [Phoinikas03/FunctionEvolve](https://github.com/Phoinikas03/FunctionEvolve) | **不匹配**。2410.04444 是 **Gödel Agent**。 | [Arvid-pku/Godel_Agent](https://github.com/Arvid-pku/Godel_Agent) |
| [2606.07704](https://arxiv.org/abs/2606.07704) | [hexo-ai/sia](https://github.com/hexo-ai/sia) | **不匹配**。2606.07704 是 **FunctionEvolve**；hexo-ai/sia 是 **SIA**。 | FunctionEvolve → [Phoinikas03/FunctionEvolve](https://github.com/Phoinikas03/FunctionEvolve)；SIA → [hexo-ai/sia](https://github.com/hexo-ai/sia) |

SIA 的正确论文是 **arXiv:2605.27276**（*SIA: Self Improving AI with Harness & Weight Updates*）。

---

## 1. 三者一句话定位

| 项目 | 核心思想 | 进化对象 | 主要优势 | 主要风险/局限 |
|---|---|---|---|---|
| **Gödel Agent** | 受 Gödel 机启发的**自指、递归自我改进**。LLM 可以读取并修改自己的运行时代码（monkey patching）。 | 自身逻辑、行为、甚至优化模块本身。 | 设计空间极大，可探索人类预定义流程之外的策略；在数学/推理/复杂 agent 任务上超越手工设计。 | 可控性差、终止性难保证、可能自我破坏、安全沙箱难做、复现/审计困难。 |
| **FunctionEvolve** | **结构引导的符号回归**。把搜索空间显式表达为 AST（表达式树），用 LLM + 确定性树编辑 + 结构感知系数优化进行进化。 | 数学/科学公式、表达式树、可符号化的函数/规则。 | 结构可见、局部编辑保留有用子结构、评分可靠；在 LLM-SRBench 上 SOTA。 | 领域较窄（科学方程发现），不直接解决通用 prompt/tool/topology 进化。 |
| **SIA** | **Harness + Weight 双杠杆更新**。Meta-Agent 生成 Target Agent，Feedback Agent 同时改写 scaffold（prompt/tool/retry/search）并对模型做 LoRA 微调。 | scaffold（harness）+ 模型权重。 | 实证收益巨大（LawBench +56.6%、GPU kernel 91.9% 提速）；把 prompt 工程做不到的“领域直觉”注入权重。 | 需要 GPU/训练 infra、权重更新使版本控制更复杂、成本高、需要 verifier。 |

---

## 2. 与 SEMAS 的对比：谁更“合理”？

### 2.1 能力维度

- **Gödel Agent > SEMAS**：它能改自己，SEMAS 只改 prompt/tool/topology/few-shot。
- **SIA > SEMAS**：它能改权重，SEMAS 不改权重。
- **FunctionEvolve ≈ SEMAS 的 Mutator 增强版**：在“生成并优化代码/符号表达式”这一局部能力上比 SEMAS 默认的 `Mutator.mutate_tool` 更精细，但不覆盖 SEMAS 的完整框架。

### 2.2 控制维度

- **SEMAS > 三者**：
  - 版本化 genome + 回归门 + Sandbox + cooldown + 错误模式去重 + 自动回滚。
  - 这是工程化、可审计、可移植的“保守型”进化。
- **Gödel Agent 最不可控**：递归自改代码，难以保证不变量。
- **SIA 中等可控**：权重更新可通过 checkpoint/LoRA adapter 版本化，但比 prompt/tool 版本化复杂。
- **FunctionEvolve 可控**：AST 空间约束强，搜索过程可追踪。

### 2.3 适用场景

| 场景 | 推荐方案 |
|---|---|
| 快速移植、安全可控、多领域复用 | **SEMAS 核心** |
| 需要把“领域直觉”内化到模型参数 | **SIA 插件** |
| 需要优化可符号化的工具/规则/公式 | **FunctionEvolve 插件** |
| 研究开放式自我改进、愿意承担风险 | **Gödel Agent 插件（加严格笼）** |

**结论**：三者不是“比 SEMAS 更合理”，而是**在不同维度上更强、也更重**。SEMAS 保持最小、最安全的进化内核；三者可以作为**可选插件/模块**接入，形成“核心 + 扩展”的分层架构。

---

## 3. 插件化整合的总体思路

SEMAS 当前已经具备可插拔的扩展点：

- `ExecutorFn`：执行逻辑可替换。
- `Evaluator`：metrics、回归测试可注入。
- `Mutator`：四类变异可覆盖。
- `Sandbox`：安全策略可配置。
- `GenomeRepository`：后端可替换。

我们在此基础上抽象出一层 **Evolution Plugin Interface（EPI）**，让 Gödel Agent / FunctionEvolve / SIA 作为可选插件注册到 `Orchestrator` 的进化链路中。

### 3.1 建议的插件接口

```python
from __future__ import annotations
from typing import Protocol
from semas.genome.genome import AgentGenome, ToolGenome
from semas.evaluator.evaluator import EvaluationResult


class MutatorStrategy(Protocol):
    """替代或增强默认 Mutator 的变异策略。"""

    def mutate(
        self,
        agent: AgentGenome,
        failure_logs: list[str],
        context: dict,
    ) -> list[AgentGenome]:
        """返回一组候选基因组。"""
        ...


class CandidateOptimizer(Protocol):
    """对 Mutator 生成的候选做后处理/精炼/评分。"""

    def optimize(
        self,
        candidate: AgentGenome | ToolGenome,
        task_input: dict,
        evaluation: EvaluationResult,
    ) -> AgentGenome | ToolGenome:
        """返回优化后的候选。"""
        ...


class WeightUpdateStrategy(Protocol):
    """在 harness 更新之外，额外对模型权重做测试时训练。"""

    def should_update_weights(
        self,
        agent: AgentGenome,
        traces: list,
    ) -> bool:
        ...

    def update_weights(
        self,
        agent: AgentGenome,
        training_samples: list[dict],
    ) -> str:
        """返回新权重 artifact 的路径/标识（如 LoRA adapter 路径）。"""
        ...


class SelfModificationPolicy(Protocol):
    """允许 agent 修改自身代码的策略（Gödel Agent 模式）。"""

    def is_allowed(
        self,
        current_source: str,
        proposed_source: str,
        sandbox_result,
    ) -> bool:
        """对自改代码做最终放行判断。"""
        ...

    def rollback_on_failure(self) -> bool:
        ...
```

### 3.2 插件在 SEMAS 双循环中的位置

```text
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│  run_task() ──► evaluate() ──► trigger?                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Evolution Plugin Pipeline                       │
│                                                              │
│  1. MutatorStrategy (可插拔)                                  │
│     ├── DefaultMutator (SEMAS 默认)                          │
│     ├── FunctionEvolveToolMutator（结构感知树编辑）            │
│     └── GodelSelfModificationMutator（自指代码修改）           │
│                                                              │
│  2. CandidateOptimizer (可插拔)                               │
│     ├── DefaultOptimizer (无操作)                            │
│     └── FunctionEvolveOptimizer（AST 系数拟合 + Pareto 选择）  │
│                                                              │
│  3. WeightUpdateStrategy (可插拔)                             │
│     ├── NoWeightUpdate (SEMAS 默认)                          │
│     └── SIAWeightUpdate（LoRA / test-time training）         │
│                                                              │
│  4. SelfModificationPolicy (可插拔，Gödel 模式专用)            │
│     └── StrictGodelPolicy（强沙箱 + 人工/回归门审批）          │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Sandbox + Evaluator(regression gate) + Repository(commit)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 每个项目如何作为 SEMAS 插件落地

### 4.1 Gödel Agent → `semas.plugins.godel`

**定位**：高风险、高上限的“开放式自改”研究插件。不建议直接用于生产，除非加多重笼锁。

**集成方式**：
- 实现 `GodelSelfModificationMutator(MutatorStrategy)`：让 LLM 读取当前 `agent_module` 源码，生成 patch，通过 `SelfModificationPolicy` 审批。
- 实现 `StrictGodelPolicy`：
  - 只允许修改白名单内的模块/函数。
  - 修改后的代码必须先通过 `Sandbox` 执行一个回归用例。
  - 禁止修改 `SelfModificationPolicy`、`Sandbox`、`Evaluator` 等元安全组件。
  - 所有修改产生新版本，旧版本保留，可随时 `rollback`。
- 在 `AgentGenome.meta` 中记录 `"self_modified": true` 及修改前后 hash。

**SEMAS 需要补强的能力**：
- 运行时源码自省（`inspect.getsource`）。
- 代码 diff 审批门（人工或自动）。
- 更强的沙箱（进程隔离、文件系统只读、网络禁用）。

### 4.2 FunctionEvolve → `semas.plugins.function_evolve`

**定位**：增强 SEMAS 的 **tool / 规则 / 公式进化能力**，尤其适合科学计算、代码生成、可符号化策略的场景。

**集成方式**：
- 实现 `FunctionEvolveToolMutator`：把 `Mutator.mutate_tool` 生成的初始函数作为种子，展开成 AST 表达式树。
- 接入 FunctionEvolve 的四个组件：
  - **Generator**：从任务描述生成多样表达式种子。
  - **Selector**：基于结构摘要 + 训练误差选择父代。
  - **Mutator**：确定性 AST 规则编辑 + LLM 引导的 ADD/SUBST。
  - **Structure-aware Optimizer**：分离线性/非线性参数，做系数拟合、简化、评分。
- 实现 `FunctionEvolveOptimizer` 作为 `CandidateOptimizer`：对候选 tool 做局部精炼和 Pareto/MDL 选择。

**适用对象**：
- 需要进化的数学/科学工具（如 GEO 中的重写策略公式、命理中的日历计算函数）。
- 不适用于 system prompt 或 topology 进化。

### 4.3 SIA → `semas.plugins.sia`

**定位**：在 SEMAS 的 harness 更新之上，增加 **权重更新** 杠杆，适合需要把领域直觉内化到模型参数的任务。

**集成方式**：
- 实现 `SIAMetaAgent`：读取任务描述，生成初始 `AgentGenome`（相当于 SIA 的 Target Agent scaffold）。
- 实现 `SIAFeedbackAgent`：在每次任务失败后，决定：
  - 是改 harness（调用 SEMAS `Mutator`），还是
  - 改权重（调用 `SIAWeightUpdate`）。
- 实现 `SIAWeightUpdate(WeightUpdateStrategy)`：
  - 收集失败/成功样本。
  - 用 `peft` / `llamafactory` / 自定义 LoRA 脚本做测试时训练。
  - 输出 LoRA adapter 路径，保存到 `AgentGenome.meta["lora_adapter"]`.weight_update 记录版本。
- `ExecutorFn` 加载 agent 时，若 `meta` 中有 LoRA 路径，则把 base LLM + LoRA 组合成实际推理模型。

**SEMAS 需要补强的能力**：
- `AgentGenome` 增加 `weight_artifacts` 字段（adapter 路径、训练数据 hash、训练配置 hash）。
- `GenomeRepository` 除了存 JSON，还要存/引用 LoRA 二进制文件。
- `rollback` 时同时回滚权重 artifact。

---

## 5. 推荐的 SEMAS 架构演进路线

### 阶段 1：抽象插件接口（保持核心最小）

在 `semas/orchestrator/` 或新增 `semas/plugins/` 中定义：

```text
semas/
  plugins/
    __init__.py
    base.py          # MutatorStrategy / CandidateOptimizer / WeightUpdateStrategy / SelfModificationPolicy
    registry.py      # 通过 entry_points 或配置文件注册插件
  orchestrator/
    orchestrator.py  # 在 evolve() 中调用插件 pipeline
```

默认不启用任何插件，SEMAS 保持现有行为。

### 阶段 2：逐个实现插件（按需启用）

优先级建议：

1. **FunctionEvolve 插件**：风险低、收益明确，先增强 tool mutation。
2. **SIA 插件**：需要训练 infra，中等风险，但能显著提升需要权重内化的任务。
3. **Gödel Agent 插件**：仅作为研究能力，最后实现，且必须配套强安全笼。

### 阶段 3：统一配置与审计

所有插件进化事件写入 `GenomeRepository` 的 archive，包含：

- 插件名称与版本。
- 输入（失败日志、任务输入）。
- 输出（候选 genome、权重 artifact、自改代码 diff）。
- 评估结果（是否通过 regression gate、metric floors）。
- 触发原因与回滚记录。

---

## 6. 对“是否更合理”的最终判断

| 维度 | SEMAS | Gödel Agent | FunctionEvolve | SIA |
|---|---|---|---|---|
| **通用性** | 高 | 极高 | 中（符号回归） | 高 |
| **可控性** | 极高 | 低 | 高 | 中 |
| **安全/审计** | 强 | 弱 | 强 | 中 |
| **权重更新** | 否 | 否 | 否 | 是 |
| **自指代码修改** | 否 | 是 | 否 | 否 |
| **结构感知优化** | 基础 | 无 | 极强 | 无 |
| **工程成本** | 低 | 高 | 中 | 高 |
| **适用生产** | 是 | 否（需大量加固） | 是（特定领域） | 是（有 GPU/verifier） |

**结论**：

- **SEMAS 仍然是最合理的基础框架**，因为它把进化问题抽象成了可控、可移植、可审计的最小集合。
- **Gödel Agent / FunctionEvolve / SIA 不应替代 SEMAS，而应作为可选插件**接入其进化链路。
- 这样既能保留 SEMAS 的安全边界，又能在需要时打开“高能力模式”。

---

## 7. 下一步可交付物建议

如果你确认这个方向，我可以继续产出：

1. **`semas/plugins/base.py`**：插件接口的正式 Protocol 定义。
2. **`semas/plugins/registry.py`**：基于 `pyproject.toml` entry points 的插件注册机制。
3. **`semas/plugins/function_evolve/`**：第一个可运行插件的最小实现。
4. **更新 `SEMAS_ARA_Architecture.md`**：把插件层纳入 ARA 架构文档。
5. **`SEMAS_SIA_Integration_Design.md`**：SIA 权重更新与 SEMAS 版本控制结合的详细设计。
