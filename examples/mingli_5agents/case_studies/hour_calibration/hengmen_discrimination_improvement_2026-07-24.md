# 横门断 AHP 时辰校准区分度改进（2026-07-24）

> 对应回测报告 `book_ahp_backtest_2026-07-09.md` 的诊断：《格局横门断》
> “分高但排序拉不开”——平均分高、参考排名中游、第一数少。
> 本文记录基线、根因复核、改动清单与改进后指标。

## 1. 基线（改动前，分支 codex/mingli-book-subagents 工作树）

`py -3.14 -m examples.mingli_5agents.case_studies.hour_calibration.run_validation_batch`
（11 个公众人物案例全跑），横门断条目：

| 口径 | 平均参考排名 | 第一数 | 前三数 | 平均参考分 |
|---|---:|---:|---:|---:|
| 书籍级 geju_hengmen_duan | 5.45 | 3 | 3 | 0.6508 |
| 流派级 hengmen | 5.36 | 1 | 4 | 0.7040 |

基线逐案例明细存于 `.semas_tmp/hengmen_baseline.json`。

## 2. 根因复核（代码级确认）

1. `hengmen_rule_engine.score_hengmen_timing`：`annual_support` 基准 0.45 后
   几乎只做加法（+0.16/+0.14/+0.08，负向仅 -0.05），候选分数挤在高位窄带。
2. 证伪通道空转：11 个案例的 `counterexamples/counterexample_years`
   **覆盖率为 0**（逐案例统计：全部 0 个事件声明反例年份），
   `_counterfactual_receipt` 恒返回中性 0.5、零惩罚；且激活条件
   “任意支关系即激活”即使喂了数据也会对所有候选同罚，没有证伪力。
3. 逐维度候选敏感度分析（按事件权重聚合每候选各 AHP vote 后排序参考时辰，
   随机期望排名 6.5）：

| vote | 权重(旧) | 参考平均排名 | 候选间 spread | 说明 |
|---|---:|---:|---:|---|
| month_pattern | 0.18 | 5.45 | 0.236 | 吃时柱（透干/通根改变取格） |
| stem_root | 0.14 | 5.27 | 0.154 | 吃时柱 |
| success_rescue | 0.18 | 5.18 | 0.271 | 吃时柱，区分度最大且最对齐参考时辰 |
| event_ten_god | 0.16 | 5.45 | **0.000** | 只看事件类型+流年十神（日主口径），对候选是常数 |
| palace_trigger | 0.12 | **6.45** | 0.076 | 粗粒度，经验上与参考时辰负相关 |
| luck_support | 0.10 | 5.00 | 0.088 | 吃主格十神 |
| annual_interaction | 0.08 | 5.55 | 0.068 | 大部分分量是候选常数 |
| fact_calibration | 0.04 | 5.45 | **0.000** | 反例通道空转时为常数 |

结论：旧权重把 20% 配给零方差维度、12% 配给负相关维度，而区分度最好的
成败救应只有 18%——这就是“分高但排序拉不开”的直接原因。

4. 流派级 hengmen 另有独立实现：`bazi_school_ahp._vote_score` 的通用启发式
   与专用引擎口径分叉，常年打高分（0.704）却排名平庸，且不接收流月与
   反例证据。

## 3. 改动清单

### 3.1 `examples/mingli_5agents/tools/hengmen_rule_engine.py`

- `_counterfactual_receipt` 重构：
  - 新增派生反例路径：事件未声明反例年份、但调用方提供了派生岁运行时，
    按派生口径评估（每激活年罚 0.05、上限 0.20，状态
    `derived_counterexamples`），证据强度低于声明反例（0.08/年、上限 0.35）。
  - 激活条件收紧并与正面计分同构：十神主题（主格或事件主题）命中**且**
    存在地支引动，**或**时柱被流年直接引动（横门第二十三章“引动归时”，
    时柱为应事落点）。旧条件“任意支关系即激活”会让所有候选同罚。
  - 公共评估逻辑抽成 `_evaluate_counterexample_rows`。
- `score_hengmen_timing` 内部合成权重（只影响回执展示分）：
  annual 0.65→0.55，counterfactual 0.15→0.25，monthly 0.20 不变，保持归一。

### 3.2 `examples/mingli_5agents/case_studies/hour_calibration/hour_calibration.py`

- `_counterexample_rows` 增加派生回退：事件未声明反例时，取事件年份 ±3 年内、
  案例中无记载事件、且岁运行存在的最近 4 个年份作为派生反例行。
  依据：案例事件表声称覆盖人生大事，邻近无事件年份可作弱负样本；
  引擎侧按派生口径降权，回执状态可审计。
- `_candidate_result` 计算 `event_years`（案例内全部事件年份）传入三处调用
  （横门事件、书籍框架、流派框架）。

### 3.3 `examples/mingli_5agents/tools/bazi_hengmen_ahp.py`

- `AHP_WEIGHTS`（总和保持 1.0）：

| 维度 | 旧 | 新 | 理由 |
|---|---:|---:|---|
| success_rescue | 0.18 | 0.24 | 横门断“成败救应”核心，候选间区分度最大且最对齐参考时辰 |
| event_ten_god | 0.16 | 0.10 | 对 12 个时辰候选是常数，零区分度 |
| palace_trigger | 0.12 | 0.06 | 粗粒度（任意支关系落目标宫位即计分），回测中与参考时辰负相关 |
| fact_calibration | 0.04 | 0.10 | “事实年份筛选强断”闸门，反例通道已真正生效 |
| month_pattern / stem_root / luck_support / annual_interaction | 0.18/0.14/0.10/0.08 | 不变 | — |

### 3.4 `examples/mingli_5agents/tools/mingli_book_ahp.py`

- `geju_hengmen_duan` 书籍 profile 的 subagent 权重同哲学镜像调整
  （总和保持 1.0）：rescue_agent 0.18→0.26，event_agent 0.18→0.10，
  palace_agent 0.12→0.06，fact_agent 0.06→0.12，
  month_pattern/stem_root/timing 不变。

### 3.5 `examples/mingli_5agents/tools/bazi_school_ahp.py`

- hengmen 流派的事件评分委托 `score_hengmen_event`（与书籍 profile 的做法
  一致），`score_all_bazi_schools` / `score_bazi_school_event` 增加可选
  `monthly_rows` / `counterexample_rows` 参数，其余流派走原通用启发式不变。
- hengmen 流派权重与 `AHP_WEIGHTS` 同步（success_rescue 0.24、
  event_ten_god 0.10、palace_trigger 0.06、fact_calibration 0.10）。

### 3.6 `examples/mingli_5agents/tests/test_hengmen_rule_engine.py`

- 新增 `test_derived_counterexample_rows_penalize_without_declared_years`：
  覆盖派生反例路径（状态、激活数、0.05/年惩罚）。
- 新增 `test_counterexample_activation_needs_theme_plus_interaction_or_hour_trip`：
  锁定新激活口径（主题十神+引动，或时柱引动；旧“任意支关系”不再算激活）。
- 未改动任何既有断言：权重变更不影响单 vote 分值，既有测试全部通过。

## 4. 改进后指标（11 案例回测）

| 口径 | 指标 | 基线 | 改进后 | Δ |
|---|---|---:|---:|---:|
| 书籍级 geju_hengmen_duan | 平均参考排名 | 5.45 | **5.18** | -0.27，变好 |
| 书籍级 | 第一数 | 3 | 3 | 持平 |
| 书籍级 | 前三数 | 3 | **5** | +2 |
| 书籍级 | 平均参考分 | 0.6508 | 0.6412 | -0.0096（远小于 0.05 容忍线） |
| 流派级 hengmen | 平均参考排名 | 5.36 | **5.09** | -0.27，变好 |
| 流派级 | 第一数 | 1 | **3** | +2 |
| 流派级 | 前三数 | 4 | **5** | +1 |
| 流派级 | 平均参考分 | 0.7040 | 0.6379 | -0.066，见下方说明 |

补充：整表 `strategy_total` 口径的参考命中数 0→1，前三数 5 持平。

流派级平均分下降 0.066 是**实现口径切换**的结果：旧通用启发式对所有候选
系统性打高分（0.704），委托专用引擎后分数回到与书籍级相同的量尺
（0.638），属于去掉水分而非“压低参考分假拉开”——排名改善（5.36→5.09、
第一 1→3）来自候选间相对顺序的真实变化；书籍级平均分仅降 0.0096。

逐案例书籍级参考排名对比、权重仿真实验（先离线重排仿真、后实跑验证，
仿真与实跑数字一致）见 `.semas_tmp/hengmen_after.json`、
`.semas_tmp/hengmen_baseline.json` 与 `.semas_tmp/weight_sweep.py`。

## 5. 验证命令

- `py -3.14 -m pytest examples.mingli_5agents/tests/test_hengmen_rule_engine.py -q` → 44 passed
- `py -3.14 -m pytest examples/mingli_5agents/tests -q --ignore=.../test_provider_checks.py`
  → 311 passed（全量回归）
- `py -3.14 -m examples.mingli_5agents.case_studies.hour_calibration.run_validation_batch`
  → 11 案例全跑成功

## 6. 残余风险

- 派生反例是弱负样本：案例事件表未必穷尽当年所有同主题事件，可能误罚
  “其实发生了小事”的年份；引擎已按派生口径降低惩罚单价（0.05 vs 0.08）
  与上限（0.20 vs 0.35）对冲。长期仍应在案例数据中人工声明反例年份。
- 权重调整含经验成分（11 案例语料上 palace_trigger 负相关、success_rescue
  最对齐），样本量小，存在过拟合风险；方向性论证（零方差维度降权、
  核心格局维度加权）不依赖该语料，幅度论证依赖。
- barack_obama（12）、oprah_winfrey（11）、audrey_hepburn（9）三个案例的
  参考时辰仍排在末段，拉高了平均排名；后续可针对这些案例检查公开参考
  时辰本身的可信度或事件清单覆盖度。
- 流派级委托后 `score_bazi_school_event` 对 hengmen 的计算量与书籍级相同，
  批量回测耗时略有增加（仍在分钟级）。
