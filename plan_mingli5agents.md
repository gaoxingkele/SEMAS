# 五智能体命理分析系统设计方案

## 1. 项目目标

基于 SEMAS 自进化多智能体框架，构建一个由 1 个总调度智能体和 4 个专业分析智能体组成的命理分析系统。系统通过排盘、独立分析、多轮讨论、交叉质疑、投票、古籍/资料源校验和最终综合，输出结构化命理分析报告，并支持基于用户反馈、报告质量、资料证据、provider 契约和回归测试的持续进化。

本项目目标不是证明命理预测有效，而是构建一个工程上严谨、可审计、可替换 provider、可进化的文化研究和算法演示框架。所有生产级声明必须绑定来源、证据、边界和不确定性。

## 2. 大模型后端

- 默认通过 `semas/utils/llm_client.py` 统一封装 OpenAI-compatible LLM 调用。
- 支持 Kimi、DeepSeek、OpenAI-compatible 服务或本地兼容网关。
- LLM 只用于可选综合表达，不替代结构化排盘、provider 输出、审计字段和安全边界。
- 运行环境未配置 LLM 时，系统必须保持 deterministic/offline-friendly，可通过结构化规则和测试 fixtures 完成分析。

## 3. 智能体架构

### 3.1 总调度智能体 Agent #1

职责：

- 接收出生年月日时、性别、出生地、分析范围等输入。
- 规范化出生资料，完成地点、时区、历法 provider 和 request provenance 记录。
- 协调八字、紫微、奇门、西占四个专业智能体并保留 provider quality。
- 组织讨论、质疑、冲突保留、投票和最终综合。
- 审核各智能体输出是否有资料来源、方法边界和不确定性说明。
- 输出结构化 JSON 报告和 Markdown 渲染报告。
- 维护生产就绪度：不能把 symbolic scaffold 伪装成专业 provider 结果。

知识要求：

- 阴阳五行、天干地支、先天/后天八卦、十神、用神、十二长生。
- 十二值日、二十八宿、黄道/黑道、择日基础。
- 资料源引用、开源 provider 许可、数据集治理和高风险决策边界。

### 3.2 八字命理智能体 Agent #2

职责：

- 基于出生资料生成四柱、十神、藏干、纳音、十二长生、大运、流年和流月结构。
- 优先使用可审计的专业历法 provider；无 provider 时明确降级。
- 综合运用以下八类方法，并在报告中输出 method matrix：

| 流派/方法 | 计算特点 |
| --- | --- |
| 子平格局法 | 月令定格，取格局、用神，讨论成败高低。 |
| 旺衰扶抑法 | 以日主为中心，量化得令、得地、得势，判断扶抑。 |
| 盲派做功法 | 宾主/体用定位，观察刑冲合害与能量做功方式。 |
| 神煞纳音法 | 查询神煞、纳音五行和组合象义，作为辅助层。 |
| 形象读象法 | 从干支组合、十神关系和类象进行象征性推演。 |
| 调候禄命法 | 根据月令寒暖燥湿判断调候优先级。 |
| 新派简化法 | 使用简化强弱/虚实/反断等规则，但必须标注边界。 |
| 数据验证法 | 只在合规数据集和冻结 holdout 通过后用于模型评估，不直接制造预测确定性。 |

输出：

- 八字结构、喜忌倾向、格局/强弱/调候/神煞/象法摘要。
- 大运、逐年流年、重点年份流月。
- 财运、官运、事业、学习、婚恋、朋友、领导客户、子女家庭等主题映射。

### 3.3 紫微斗数智能体 Agent #3

职责：

- 根据出生资料生成或接入紫微斗数命盘。
- 分析命宫、身宫、十二宫位、主星辅星、四化、大限、流年和流月主题。
- 默认 symbolic scaffold 只能用于结构演示；生产级输出必须接入经审查的专业 provider，例如 iztro 系列 wrapper 或 JSON-CLI provider。

输出：

- 命宫/身宫/十二宫摘要、四化牵动、大限和流年激活。
- provider provenance、reference contract coverage 和 fallback 边界。

### 3.4 奇门遁甲智能体 Agent #4

职责：

- 根据求测时间或出生上下文起奇门局。
- 分析九宫、天盘、地盘、人盘、神盘、门星神、用神落宫和格局风险。
- 默认 symbolic scaffold 只能用于结构演示；生产级输出必须接入 kinqimen 或经审查 JSON-CLI provider。

输出：

- 九宫格局、值符值使、门星神组合、用神主题映射、年度时机提示。
- provider provenance、reference contract coverage 和 fallback 边界。

### 3.5 西方占星智能体 Agent #5

职责：

- 根据出生资料生成本命盘、太阳/月亮/上升、行星、宫位和相位。
- 对流年 transit 进行结构化补充分析。
- 默认 symbolic scaffold 只能用于结构演示；生产级输出必须接入 Swiss Ephemeris、pyswisseph 或经审查 JSON-CLI provider。

输出：

- 本命星盘摘要、宫位/相位重点、年度 transit 激活。
- provider provenance、ephemeris quality、reference fixtures 和 fallback 边界。

## 4. 分析层次

每个专业智能体都必须覆盖以下层次：

1. 宏观层：整体命盘结构、人生阶段、先天资源和长期主题。
2. 微观层：宫位、十神、星曜、用神、门星神、相位等细节。
3. 流年层：按年份推演机会、压力、关系和风险。
4. 流月层：对重点年份细化到月份。
5. 主题层：财运、官运、事业、学业、婚恋、朋友、领导客户、子女家庭。
6. 边界层：每条结论必须标注证据、provider 质量和不确定性，不输出确定性命令。

## 5. 协作流程

```text
用户输入出生资料
  -> 总调度智能体规范化输入、地点、时区、历法和 provenance
  -> 并行分发给八字、紫微、奇门、西占四个专业智能体
  -> 各智能体独立完成多层次分析
  -> Discussion Round:
       - 各智能体陈述核心观点
       - 对冲突点进行质疑和补充
       - 保留无法消解的冲突与 provider 降级原因
  -> Voting Round:
       - 对关键综合结论进行 claim-level 投票
       - 记录支持者、反对者、弃权、阈值和理由
  -> Source Review:
       - 检索本地或外部允许的经典资料 metadata
       - 检查每个结论是否有来源、方法或 provider 依据
  -> 总调度综合输出最终报告
```

协作产物必须包括 deliberation receipt：绑定讨论记录、投票记录、资料审查、冲突列表和 workflow 设置的哈希，便于回归测试和发布审计。

## 6. 持续进化机制

系统通过 SEMAS 框架持续优化智能体 genome 和工作流：

1. 执行：用当前 genome 运行完整分析流程。
2. 评估：综合用户反馈、结构化 schema、中文渲染、资料证据、provider 契约、安全边界、一致性、topic confidence 和 benchmark 表现。
3. 触发：当分数低于阈值、出现新失败模式、provider contract 漂移或 release gate 失败时触发进化。
4. 变异：mutator 可修改 system prompt、few-shot、工具参数、讨论轮数、投票阈值、source review 策略、报告渲染策略。
5. 沙箱测试：候选 genome 必须在隔离环境运行 benchmark 和回归测试。
6. 选择与回滚：只有通过 metric floors 和回归门禁的候选才能被接受；失败时保持旧版本并保留 archive 证据。
7. 证据归档：每次接受、回滚、benchmark、release manifest 都必须保留 hash-chain 或 receipt。

进化不得直接优化未经同意、未经审查、未冻结 holdout 的人生事件预测标签。预测类标签只能在 outcome dataset 的 consent、privacy、external review、baseline、statistical plan、frozen split 全部通过后进入受控研究流程。

## 7. 古籍文献与源码参考

系统需要具备资料源校验能力，但必须遵守版权和来源边界：

- 内置资料只保存 copyright-safe 摘要、metadata、来源 ID、关键词和 citation policy。
- 外部古籍或开源资料通过 allowlisted manifest feed 接入，先审计 source list，再下载、缓存、hash 校验和 JSONL 入库。
- 远程 manifest 必须 host allowlist，并尽量使用 SHA-256 pinning。
- 支持 `classical-sources` 审计和 `classical-refresh` 刷新命令。
- 资料源可参考《三命通会》《滴天髓》《子平真诠》、紫微斗数典籍、奇门典籍和开源排盘项目，但不得复制受版权保护全文。
- 所有引用必须说明来源、证据类型、方法边界和不确定性。

## 8. 项目目录结构

推荐结构：

```text
examples/mingli_5agents/
  README.md
  cli.py
  api_core.py
  api_server.py
  run_demo.py
  benchmark.py
  capability_audit.py
  genomes/
    orchestrator_v1.yaml
    bazi_v1.yaml
    ziwei_v1.yaml
    qimen_v1.yaml
    astrology_v1.yaml
  tools/
    bazi_pai_pan.py
    bazi_deep_analysis.py
    ziwei_pai_pan.py
    ziwei_deep_analysis.py
    qimen_ju.py
    qimen_deep_analysis.py
    astrology_chart.py
    astrology_deep_analysis.py
    lunar_date.py
    calendar_provider.py
    professional_chart_provider.py
  evaluators/
    consistency_evaluator.py
    feedback_evaluator.py
    citation_evaluator.py
    report_schema_evaluator.py
    provider_contract_evaluator.py
    safety_evaluator.py
  tests/
    test_mingli_system.py
    test_cli.py
    test_api_server.py
```

## 9. 需要解决的问题

- 如何客观量化命理分析的“正确性”，并避免把主观反馈误当事实标签。
- 如何处理不同流派、不同 provider 和不同智能体之间的结论冲突。
- 如何界定古籍引用、开源 provider、外部资料和预测断言之间的边界。
- 如何在用户反馈、隐私、数据同意、法律责任和伦理边界之间保持可审计治理。
- 如何平衡 LLM 调用成本、进化迭代频率和可复现性。
- 如何接入并认证生产级紫微、奇门、西占、择日 provider，使 symbolic scaffold 不再承担专业计算职责。
- 如何构建经过外部审查、冻结 train/holdout split 的 outcome dataset。

## 10. 备注

本方案仅用于文化研究、娱乐参考和算法演示，不构成医疗、投资、婚姻、法律或其他重大决策建议。系统必须在报告、API、CLI、README、benchmark 和 release manifest 中持续暴露这一边界。

验收标准：

- 五智能体拓扑、讨论投票、source review、deliberation receipt 和结构化报告可运行。
- SEMAS 进化具有 benchmark、metric floors、archive、rollback、release manifest 和 drift 检查。
- provider 体系支持 professional backend、JSON-CLI、request-scoped external payload 和 certification ledger。
- 生产 readiness 对缺失 provider、缺失 outcome dataset、缺失资料源 allowlist 等问题给出明确 blockers。
- 所有已实现能力在 capability audit 中有 machine-checkable evidence，所有未完成能力在 known gaps 中有 resolution plan 和 production gates。
