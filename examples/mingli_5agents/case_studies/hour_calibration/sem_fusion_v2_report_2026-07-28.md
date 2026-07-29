# SEM 融合层第二轮迭代评估（2026-07-28）

> 第一轮（`sem_fusion_report_2026-07-24.md`）：一因子 SEM、26 指标、132 行，
> LOCO 平均参考排名 6.00，诚实失败。处方：案例内标准化、按候选间区分度
> 筛选指标、更少参数结构。本文执行该处方，目标：**LOCO 显著优于等权融合
> 基线（4.36 / top1 3 / top3 7）**。结论先行：**不含 LLM 信号的所有变体
> 仍未跑赢等权基线；含 LLM 包的 BT 变体（4.18 / 2 / 8）在平均排名与 top3
> 上小胜等权基线，但不及 LLM 信号单用（3.64 / 3 / 8），且 LLM 信号有
> 不可排除的污染风险，该结果只能读作上限估计。**

## 1. 实施的三项机制修复

### 1.1 案例内标准化

`within_case_standardize`：每个特征在案例内 12 个候选间做 z-score
（案例内零方差 → 全 0）。数据集保留原始值，评估时用中心化值。
效果见 §3：v1 模型直接套在中心化特征上（v2a）从 6.00 改善到 4.82，
是本轮单项收益最大的修复，印证了「潜变量被案例间方差主导」的诊断。

### 1.2 指标筛选 + 打包（parceling）

筛选规则（**无标签、评估前固定**）：案例内平均 spread ≥ 0.01 保留；
`hengmen_vote_palace_trigger` 依据 2026-07-24 报告的负相关证据先验剔除。
剔除：event_ten_god、fact_calibration（spread 0.000/0.009）、
chart_strategy_total（0.000）、school_{ditiansui, qiongtong_baojian,
shenfeng_tongkao}（≤0.004）、book_{yuanhai_ziping, xingping_huihai,
lixuzhong_mingshu, christian_astrology}（≤0.008）、palace_trigger。
打包为 3 个包（包内等权平均），参数量从 26+26+2 降至 3+3+1：

| 包 | 成员 |
|---|---|
| hengmen_votes | month_pattern, stem_root, success_rescue, luck_support, annual_interaction |
| schools | yuanhai_ziping, ziping_zhenquan, sanming_tonghui, hengmen |
| books | ziping_zhenquan, mingli_jicheng, yuzhao_dingzhenjing, ziwei_doushu_quanshu, geju_hengmen_duan |

### 1.3 成对比较结构模型（Bradley-Terry）

P(A优于B) = σ(w·(z_A − z_B))。**两处与任务设想的偏差，如实说明**：

1. **信息对数量**：任务设想 66 对/案例（726 观测），但两个非参考候选之间
   的优劣没有真值——有标签信息的对只有「参考 vs 每个非参考」，
   即 **11 对/案例、每折 110 对**。726 需要完整真值排序，不存在。
2. **两步 BT 与 logit 秩等价**：先 FA 提因子得分再拟合标量 β，对排序
   指标零影响（单调链接不改变任何两两顺序，首轮实现实测证实）。因此
   BT 变体采用**联合估计**：以 FA 因子得分权重初始化，直接对权重向量 w
   最大化成对似然（凸问题 + 固定 L2=1e-4，β 吸收进 w 的尺度）。
   这是 Thurstone 式排序模型：η = w·z，仍由打包指标测量。

开发过程中合成数据恢复测试抓到一处梯度符号错误（σ(m)−1 误写为
σ(−m)−1，导致优化器停在初始化点附近、退化为 FA 权重），修复后
合成数据上权重方向恢复余弦 > 0.9。另修复筛选规则中 `palace_trigger`
排除未生效的 bug。

## 2. LLM 信号包（第 4 个指标）

`llm_skill_analysis/llm_rankings_2026-07-28.json`：从 11 个 `*_analysis.md`
的「最终排序」一节提取完整 12 候选排名（一手来源），分数 = 13 − rank，
案例内 z-score 后作为第 4 个包。

**与汇总表的差异**：`summary_2026-07-28.md` 记 Bruce Lee 参考时辰（辰）
LLM 排名为 11，但分析文件最终排序辰列第 3。本数据集以分析文件为准，
故 LLM 单信号口径为 **3.64 / 3 / 8**（summary 口径 4.36 / 3 / 7）。

**污染风险**（引 summary 诚实边界）：参考时辰印在简报首部，分析者声明
未使用，但零潜意识影响无法证明。LLM 信号及一切含 LLM 的融合结果应读作
**上限估计**。

## 3. LOCO 对比总表（留一案例，sem_v2 行为各变体）

| 变体 | 平均参考排名 | Top1 | Top3 |
|---|---:|---:|---:|
| v1（原始分，26 指标，logit，2026-07-24） | 6.00 | 1 | 3 |
| v2a 案例内标准化（26 指标，logit） | 4.82 | 2 | 5 |
| v2b +筛选打包（3 包，logit） | 5.00 | 2 | 5 |
| v2c +成对 BT（3 包，联合估计） | 5.27 | 1 | 4 |
| v2d +LLM 包（4 包，logit） | 5.09 | 2 | 5 |
| **v2e +LLM 包（4 包，BT）** | **4.18** | 2 | **8** |
| 基线：等权融合（原始 26 维） | 4.36 | **3** | 7 |
| 基线：综合 AHP（strategy_total） | 5.45 | 1 | 5 |
| 基线：改进后横门断 | 5.09 | **3** | 5 |
| 参考线：打包等权（3 包，无学习） | **3.82** | 1 | **8** |
| 参考线：LLM 单信号（有污染风险） | **3.64** | **3** | **8** |

v2e 逐案例：Jolie 2、Hepburn 7、Obama 3、Bruce Lee 1、Trump 12、
Jackie Chan 1、Mao 3、Monroe 2、MJ 2、Oprah 11、Taylor 2。
失败案例与 LLM 信号高度同构（Trump 12 完全复制 LLM 的失败；
Oprah 上 LLM 单用为 2 但留一折训练后融合权重将其拉到 11）。

## 4. 全样本载荷与结构系数（描述性）

FA 测量载荷（4 指示符变体）：books 0.981、schools 0.846、
hengmen_votes 0.171、llm_skill 0.147（books 独特方差贴 0，Heywood 型
退化解，3~4 指示符小样本下常见）。

BT 联合权重 w（成对似然驱动，与 FA 载荷口径完全不同）：

| 变体 | hengmen_votes | schools | books | llm_skill |
|---|---:|---:|---:|---:|
| 不含 LLM | 0.372 | **0.761** | -0.177 | — |
| 含 LLM | 0.151 | 0.494 | 0.143 | **0.731** |

FA 载荷反映「包间共识」（books/schools 互相高度相关），BT 权重反映
「对参考排序的预测力」——两者错位再次确认第一轮诊断：共识方差 ≠
候选区分信号。含 LLM 时权重收敛到 LLM 主导，与 v2e 逐案例排名和
llm_only 高度同构一致。

## 5. 诚实结论

1. **不含 LLM：本轮目标未达成。** 最好的无 LLM 变体是 v2a（4.82），
   仍弱于等权基线 4.36；打包（v2b 5.00）与成对 BT（v2c 5.27）单独
   应用反而变差。案例内标准化是有效修复（6.00→4.82），打包与成对
   结构在该样本上没有提供额外增益——3 包等权（3.82，无学习）已经
   很难被打败，再次说明 11 正例支撑不起权重学习。
2. **含 LLM：v2e（4.18/2/8）在平均排名和 top3 上小胜等权基线
   （4.36/3/7），但 top1 仍少 1 个；且 (a) 弱于 LLM 信号单用
   （3.64/3/8），(b) 弱于 3 包等权 + LLM 的简单平均没有测——融合本身
   未证明比「信号并列展示」更有价值，(c) LLM 信号有污染风险。**
   因此 v2e 的「跑赢」只能记为有条件的、上限口径的小胜，不能宣称
   SEM 融合层目标达成。
3. 与 2026-07-28 知识库报告的「两级级联」建议一致：两路信号失败案例
   互补（等权修好 Trump/Oprah，LLM 修好 Obama/Oprah），下一轮更有
   前途的方向是级联/混合而非单一 SEM 权重学习。
4. 纪律声明：5 个变体规格在跑 LOCO 前固定（V2_VARIANTS 常量），
   未逐折调参；修复的两个 bug（筛选排除未生效、BT 梯度符号）由单元
   测试和合成恢复测试驱动，不是看着 LOCO 结果调出来的。

## 6. 限制与残余风险

- LLM 信号污染不可排除；含 LLM 的一切数字是上限估计。
- BT 联合估计每折 110 个信息对、4 个参数，仍可能过拟合折内共识
  （不含 LLM 时权重压向 schools 0.76，LOCO 反而变差）。
- 成对信息对只有 11/案例，结构模型「解决正例稀缺」的期望在小样本下
  未兑现——稀缺的是标签（1 正例/案例），不是参数化形式。
- books 包 Heywood 退化；FA 载荷与 BT 权重错位提示「单潜变量同时承担
  共识测量与排序预测」本身可能不是正确架构。
- LLM 排名为单次运行、无方差估计；Bruce Lee 案例汇总表与分析文件
  不一致（本报告以分析文件为准并已在数据文件中注明）。
- 数据集缓存在上游评分逻辑变更后需 `--recompute` 重建。

## 7. 验证命令

- `py -3.14 -m examples.mingli_5agents.case_studies.hour_calibration.sem_fusion --v2`
  → 5 变体 LOCO，输出 `outputs/sem_fusion_v2_loco.json`
- `py -3.14 -m pytest examples/mingli_5agents/tests/test_sem_fusion.py -q` → 15 passed
- `py -3.14 -m pytest examples/mingli_5agents/tests -q` → 339 passed（330 + 新增 9）
