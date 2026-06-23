# SEMAS × SIA 整合设计：Harness + Weight 双杠杆进化

> **来源**：SIA: Self Improving AI with Harness & Weight Updates, arXiv:2605.27276, https://github.com/hexo-ai/sia

---

## 1. 为什么需要 SIA 整合

SEMAS 默认是 **harness-only** 进化：改 prompt、tool、topology、few-shot，但**不修改模型权重**。这在很多场景下已经足够，但 SIA 的实验表明：

> “Harness updates make the model agentic, while weight updates build the domain intuition that no prompt or scaffold can instil.”
> — [source: SIA paper, arXiv:2605.27276]

在需要把任务特定“直觉”内化到模型参数的场景（如法律罪名分类、GPU kernel 优化、单细胞 RNA 去噪），仅靠 scaffold 迭代会遇到天花板。因此 SEMAS 需要预留 **WeightUpdateStrategy** 插件接口，让 SIA 的权重更新机制作为可选模块接入。

---

## 2. SIA 核心架构回顾

SIA 协调三类 agent：

| Agent | 职责 |
|---|---|
| **Meta-Agent** | 读取任务描述，生成初始 Target Agent（harness + 初始权重） |
| **Target Agent** | 执行任务，记录动作与结果 |
| **Feedback Agent** | 审阅日志，决定如何改进 Target Agent，可改 harness 也可改 weights |

关键循环：

```text
Task description ──► Meta-Agent ──► Target Agent
                                         │
                                         ▼
                                  Execute on task
                                         │
                                         ▼
                                  Feedback Agent
                                  /            \
                          Harness update      Weight update
                          (prompt/tool)       (LoRA / test-time training)
                                         │
                                         ▼
                              Next-generation Target Agent
```

---

## 3. SEMAS 与 SIA 的映射

| SIA 概念 | SEMAS 概念 | 说明 |
|---|---|---|
| Meta-Agent | `Orchestrator` + `Mutator` | 由 SEMAS 的进化循环承担初始 agent 生成与后续迭代 |
| Target Agent | `AgentGenome` + `ExecutorFn` | 被进化的执行者 |
| Feedback Agent | `Mutator` + `WeightUpdateStrategy` | 决定改 harness 还是改 weights |
| Harness update | `Mutator.mutate_*` / `MutatorStrategy` | SEMAS 已具备 |
| Weight update | `WeightUpdateStrategy` | 新增插件接口 |
| Verifier | `Evaluator` + regression tests | SEMAS 已具备 |
| Training data | `ExecutionTrace` 历史 | 从 `Orchestrator.traces` 构建 |

---

## 4. 接口设计

已在 `semas/plugins/base.py` 中定义：

```python
class WeightUpdateStrategy(Protocol):
    def should_update_weights(
        self,
        agent: AgentGenome,
        traces: list[ExecutionTrace],
    ) -> bool: ...

    def update_weights(
        self,
        agent: AgentGenome,
        training_samples: list[dict[str, Any]],
    ) -> dict[str, Any]: ...
```

### 4.1 返回值约定

`update_weights` 返回一个字典，描述新的权重产物，例如：

```python
{
    "adapter_path": "<repo>/weights/agent_v5_lora",
    "base_model": "Qwen/Qwen2.5-7B-Instruct",
    "adapter_type": "lora",
    "hash": "sha256:...",
    "training_samples_hash": "sha256:...",
    "config": {
        "r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "v_proj"],
        "epochs": 2,
    },
}
```

`Orchestrator` 会把该字典写入 `agent.meta["weight_artifacts"]`，然后再 `repo.save_agent(candidate)`。

### 4.2 推荐的 SIA 插件实现草图

```python
# semas/plugins/sia/weight_update.py
class SIAWeightUpdate(WeightUpdateStrategy):
    def __init__(self, base_model: str, train_batch_size: int = 8):
        self.base_model = base_model
        self.train_batch_size = train_batch_size

    def should_update_weights(self, agent, traces) -> bool:
        # 只在 harness 更新边际收益低、且有足够失败/成功样本时触发
        recent = traces[-20:]
        if len(recent) < 10:
            return False
        pass_rate = sum(1 for t in recent if t.evaluation.passed) / len(recent)
        # 处于临界区：既不完全失败，也不完全成功
        return 0.2 < pass_rate < 0.8

    def update_weights(self, agent, training_samples) -> dict[str, Any]:
        # 1. 把 samples 写入临时 JSONL
        # 2. 调用 peft / transformers / unsloth 做 LoRA 微调
        # 3. 保存 adapter 到 <repo>/weights/<agent_name>_v<version>_lora
        # 4. 计算 hash，返回 metadata
        ...
```

---

## 5. 权重版本化与回滚

### 5.1 版本化

- `AgentGenome.meta["weight_artifacts"]` 记录当前版本使用的权重产物。
- 权重产物文件（LoRA adapter、训练配置、训练数据 hash）存放在 `<repo>/weights/<agent_name>/v<N>/`。
- `GenomeRepository` 的 JSON 只存 metadata 路径，不存二进制权重，避免版本库膨胀。

### 5.2 回滚

当 `rollback_if_regressed()` 触发时：

1. 加载父版本 `AgentGenome`。
2. 复制父版本的权重产物目录到新版本目录（或软链接）。
3. 生成新的 `AgentGenome`（`evolve_from`），其 `meta["weight_artifacts"]` 指向父版本产物。
4. `repo.save_agent(rolled)`。

这样即使权重被更新过，也能恢复到之前的有效权重。

### 5.3 训练样本隔离

- 训练样本只能从 `ExecutionTrace` 中提取，且必须带有 `passed` 标签。
- 默认只用最近 20 条 trace，防止旧数据主导。
- 可选：`training_samples_hash` 保证可复现性。

---

## 6. 配置示例

```python
from semas.plugins import PluginRegistry
from semas.plugins.sia import SIAWeightUpdate

plugins = PluginRegistry()
plugins.register_weight_update_strategy(
    SIAWeightUpdate(base_model="Qwen/Qwen2.5-7B-Instruct")
)

orch = Orchestrator(
    repository=repo,
    evaluator=evaluator,
    mutator=mutator,
    sandbox=sandbox,
    agent_name="legal_classifier",
    executor=llm_executor,
    plugin_registry=plugins,
)
```

entry_points 方式：

```toml
[project.entry-points."semas.weight_update_strategy"]
sia = "semas.plugins.sia:SIAWeightUpdate"
```

---

## 7. Executor 侧加载权重

`ExecutorFn` 在实例化 LLM 时需要读取 `AgentGenome.meta["weight_artifacts"]`：

```python
def llm_executor(agent: AgentGenome, task_input: dict) -> dict:
    weight = agent.meta.get("weight_artifacts")
    if weight:
        model = load_base_model(weight["base_model"])
        model = load_lora_adapter(model, weight["adapter_path"])
    else:
        model = load_base_model(DEFAULT_BASE_MODEL)

    response = model.generate(task_input["query"])
    return {"output": response}
```

如果权重产物不存在，则回退到 base model，保持兼容性。

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 权重训练成本极高 | 可能一次进化消耗大量 GPU/Token | `should_update_weights` 只在必要时触发；设置训练样本上限 |
| 权重更新导致灾难性遗忘 | 新权重在旧任务上变差 | 必须用 regression suite 验证；失败则拒绝提交 |
| 权重文件过大，版本库膨胀 | 存储成本、传输成本 | JSON 只存 metadata，二进制权重存外部目录；rollback 时复制/链接 |
| 训练数据泄露 | 用测试集训练会导致过拟合 | 严格区分 train/holdout；`ExecutionTrace` 标记 split |
| 多权重产物依赖混乱 | 不知道哪个版本用哪个 adapter | `weight_artifacts` 中存 hash + base_model + config；CI 校验 hash |

---

## 9. 实施路线图

1. **Phase 1（已完成）**：在 `semas/plugins/base.py` 中定义 `WeightUpdateStrategy` 接口；在 `Orchestrator` 中加入 `_apply_weight_updates` 调用点。
2. **Phase 2**：实现 `semas.plugins.sia.SIAWeightUpdate` 的最小可用版本（依赖 `peft`/`transformers`）。
3. **Phase 3**：扩展 `GenomeRepository` 支持 `weights/<agent_name>/v<N>/` 目录的保存与回滚。
4. **Phase 4**：在 `examples/` 中增加一个需要权重内化的端到端 demo（如法律罪名分类或数学推理）。
5. **Phase 5**：把 SIA 插件纳入 `SEMAS_ARA_Architecture.md` 的证据索引与回归测试。

---

## 10. 与 FunctionEvolve 插件的协同

- **FunctionEvolve 插件**负责进化“可符号化的代码结构”（如公式、规则）。
- **SIA 插件**负责把“无法符号化的领域直觉”压入模型权重。
- 两者可以在同一个 `Orchestrator` 中同时启用：
  - `MutatorStrategy` 生成结构候选；
  - `WeightUpdateStrategy` 在结构候选上训练 LoRA；
  - `Evaluator` 统一打分，选出最优组合。

---

## 11. 引用

```bibtex
@article{hebbar2026sia,
  title={SIA: Self Improving AI with Harness \& Weight Updates},
  author={Hebbar, Prannay and Manawat, Yogendra and Verboomen, Samuel and Ivanova, Alesia and Palanimalai, Selvam and Bhatia, Kunal and Baskaran, Vignesh},
  journal={arXiv preprint arXiv:2605.27276},
  year={2026},
  url={https://arxiv.org/abs/2605.27276},
  code={https://github.com/hexo-ai/sia}
}
```
