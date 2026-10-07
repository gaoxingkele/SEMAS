---
date: 2026-10-07
tags: [factor-mining, evolution, recursive-self-improvement, china-a-share, audit]
status: current-through-iteration-114
outer_iteration: 114
live_iteration: 109
live_hold_sharpe: 2.3255961299286074
state_history_entries: 113
---

# A股因子迭代进化全史：Iteration 1–114

本文是供 LLM、IDE agent 和人工维护者读取的统一入口。它把散落在
`OPERATION_LOG.md`、机器状态、单轮 wiki、审计报告和 RSI 策略档案中的信息
压缩成一份可追溯时间线。结论以 2026-10-07 检查到的仓库状态为准。

## 当前状态

- 外层因子挖掘循环已经运行到 **iteration 114**；`state.json` 有 113 条历史记录，
  缺少的 iteration 11 是一次交易成本压力审计，不是一次会改写状态的进化运行。
- 当前 live library 来自 **iteration 109 / `policy_0060`**，包含 17 个因子；
  frozen 5D dynamic-trim Hold Sharpe 为 **2.3256**，年化收益 **41.89%**，
  最大回撤 **-9.37%**。
- iteration 110–114 都没有替换 live library。iteration 114 单次评估 Hold Sharpe
  为 2.2795；其三种子 paired campaign 最终只有 2/3 对有效、胜率 0.5，未达到
  `min_pairs`、`all_pairs_valid` 和 `win_rate` 门槛，因此 **rejected**。
- iteration 109 虽然在旧的单次运行规则下进入 live，但其后补做的 paired campaign
  没有胜出，所以 `policy_0060` 不具备在新版 RSI 档案中继续繁殖的资格。
- 当前运行目录中能核对到 69 个 `factor_loop_history.json`，合计 **796 个内部
  generation 记录**。早期运行产物曾被轮转，因此 796 是当前可核下限，不应与
  114 个外层 iteration 混为一谈。

[source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
[source: `china_a_share_alpha_output/factor_mining_loop/STATE.md`]
[source: local runtime `dgm_rsi/paired/policy_0060/paired_evaluation_receipt.json`]
[source: local runtime `dgm_rsi/paired/policy_0065/paired_evaluation_receipt.json`]

## 计数口径

| 名称 | 含义 | 当前值 |
|---|---|---:|
| Outer iteration | 一次完整的 seed → 内部进化 → 清洗 → 去重 → 组合 → gate → 晋级判断 | 114 |
| State history entry | `state.json.history` 中持久化的一次外层运行 | 113 |
| Inner generation | 单个 outer iteration 内部的种群代数 | 当前可核 796 |
| DGM policy | 修改挖掘策略本身的外层 genome；iteration 50 对应 `policy_0001` | 65 |
| Paired campaign | 同一种子、同一冻结库上的 parent/child 三种子对照 | 已有 0060、0062、0065 收据 |
| Factor count/ranking | 候选表达式数量或 TOP 100 排名，不是 iteration 数 | 119 个近期审计表达式 |

因此，“100 多轮”指外层 iteration 时是正确的：当前为 114；若按内部 generation
统计，则当前磁盘上能核对的记录已经接近 800。

## 事实源优先级

1. `state.json`：迭代编号、逐轮指标、gate、晋级、当前 baseline 的机器事实源。
2. paired receipt：新版 RSI parent/child 复现实验的最终选择事实源。
3. `STATE.md`：面向人的当前状态摘要。
4. `OPERATION_LOG.md`：运行原因、实施过程、验证和已知边界。
5. `wiki/` 单项笔记：思想吸收、失败解释和研究假设。

若旧报告与 `state.json` 冲突，以机器状态为准；若 single-run 状态与后来的 paired
receipt 冲突，生产 live 状态仍按 `state.json`，但繁殖资格按 paired receipt。

## 阶段总览

| 阶段 | Iterations | 主要变化 | 结果 |
|---|---:|---|---|
| 初始连续挖掘 | 1–10 | 空种子、live seeding、语义去重、相关性选择 | 1/4/5/10 晋级，test Sharpe 到 2.7031 |
| 稳健性与多周期 | 11–21 | 20 bps 压测、5D/10D、跨市场、高阶算子、资金流、LLM critic | 12 晋级；其余主要为审计或失败实验 |
| 扩展搜索 | 22–41 | TA-Lib/Alpha101、更多算子和种群 | 22/24/28/37/40 晋级，但后续 hold 审计揭示指标错配 |
| Hold gate 过渡 | 42–45 | 把 no-lookahead Hold Sharpe 加入晋级判断 | 全部拒绝；45 出现重复表达式坍缩 |
| 冻结快照恢复 | 46–48 | 固定快照、dynamic-trim、10 bps、覆盖率门槛 | 连续晋级至 Hold Sharpe 1.8444 |
| D1/D2/D3 | 49 | pool synergy、AST regularizer、DAG parent neighborhood | 晋级至 2.0560 |
| DGM/RSI 搜索 | 50–105 | 策略 genome 自改进；后期加入四岛与防坍缩 | 69、73 晋级；105 为 2.3130 近失候选 |
| 可归因 RSI | 106–109 | verified parents、单字段 mutation、冻结 examiner | 109 晋级至 2.3256 |
| Paired RSI | 110–114 | parent/child 同种子三重复、阻断 single-valid 直接繁殖 | 无新晋级；现有 paired campaigns 均未选中 child |

[source: `OPERATION_LOG.md` factor-mining entries dated 2026-07-04 through 2026-09-22]
[source: `wiki/factor_rsi_phase1_causal_verifier_20260920.md`]
[source: `wiki/factor_rsi_phase2_paired_selection_20260921.md`]

## 晋级链

早期 1–40 的“晋级”主要由 daily-rebalanced test Sharpe/return 驱动，不能直接与
46 以后冻结 no-lookahead hold contract 的结果横比。iteration 26 虽未按旧规则
晋级，却在后来的统一 hold 审计中得到 2.49，说明旧目标发生了明显指标错配。

| Iter | 晋级指标 | 候选值 | 晋级后角色 |
|---:|---|---:|---|
| 1 | legacy test Sharpe | 1.6283 | 首个 live library |
| 4 | legacy test Sharpe | 2.1145 | 语义去重后晋级 |
| 5 | legacy test Sharpe | 2.2034 | 增量晋级 |
| 10 | legacy test Sharpe | 2.7031 | 相关性约束选择 |
| 12 | legacy test Sharpe | 2.7629 | 5D/10D 多周期 |
| 22 | legacy test Sharpe | 5.4115 | TA-Lib/Alpha101 阶段 |
| 24 | legacy test Sharpe | 5.4695 | 扩展搜索 |
| 28 | legacy test Sharpe | 5.9344 | 扩展搜索 |
| 37 | legacy test Sharpe | 6.3436 | 旧口径峰值 |
| 40 | legacy return gate | 5.7213 | 旧口径最终 live，后被 hold 审计判定回归 |
| 46 | Hold Sharpe | 1.7911 | 冻结快照恢复 |
| 47 | Hold Sharpe | 1.8262 | 冻结快照晋级 |
| 48 | Hold Sharpe | 1.8444 | frozen baseline |
| 49 | Hold Sharpe | 2.0560 | D1/D2/D3 baseline |
| 69 | Hold Sharpe | 2.1591 | DGM `policy_0020` |
| 73 | Hold Sharpe | 2.2918 | DGM `policy_0024` |
| 109 | Hold Sharpe | **2.3256** | 当前 live，`policy_0060` |

[source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
[source: `wiki/factor_mining_loop_multihizon_batch_audit.md`]

## 完整逐轮账本

`Hold` 是候选在 no-lookahead dynamic-trim 合约下的 Sharpe；`Test` 是循环内部
daily-rebalanced 诊断 Sharpe。`Factors` 优先使用去重后的表达式数。iteration 11
是压测，所以不在机器 history 中。iteration 50–105 的 policy 编号按已迁移档案的
连续映射记录：`policy_id = iteration - 49`。

| Iter | Phase/policy | Hold | Test | Factors | Promoted | Decision / mutation |
|---:|---|---:|---:|---:|---|---|
| 1 | legacy 5D | - | 1.6283 | 2 | YES | promoted |
| 2 | legacy 5D | - | 1.6283 | 5 | NO | kept baseline |
| 3 | legacy 5D | - | 1.5771 | 6 | NO | fail: max correlation |
| 4 | legacy 5D | - | 2.1145 | 6 | YES | promoted |
| 5 | legacy 5D | - | 2.2034 | 7 | YES | promoted |
| 6 | legacy 5D | - | 1.0963 | 14 | NO | fail: max correlation |
| 7 | legacy 5D | - | 1.2424 | 3 | NO | fail: train Sharpe, minimum count |
| 8 | legacy 5D | - | 2.3964 | 17 | NO | fail: max correlation |
| 9 | legacy 5D | - | 0.4955 | 14 | NO | fail: max correlation |
| 10 | legacy 5D | - | 2.7031 | 12 | YES | promoted |
| 11 | stress audit | - | 2.7031 @ 20 bps | - | N/A | no state mutation |
| 12 | legacy 5D | - | 2.7629 | 10 | YES | promoted |
| 13 | legacy 5D | - | 1.8354 | 10 | NO | kept baseline |
| 14 | legacy 5D | - | 2.4074 | 12 | NO | kept baseline |
| 15 | legacy 5D | - | 2.0207 | 15 | NO | kept baseline |
| 16 | legacy 5D | - | 2.7629 | 10 | NO | equal best |
| 17 | legacy 5D | - | 2.7629 | 10 | NO | equal best |
| 18 | legacy 5D | - | 2.3081 | 10 | NO | fail: train Sharpe, correlation |
| 19 | legacy 5D | - | 1.1437 | 10 | NO | fail: train Sharpe, correlation |
| 20 | legacy 5D | - | 2.2126 | 12 | NO | kept baseline |
| 21 | production audit | - | 2.7629 | 10 | N/A | audit only |
| 22 | legacy 5D | - | 5.4115 | 10 | YES | promoted |
| 23 | legacy 5D | - | 4.8574 | 14 | NO | kept baseline |
| 24 | legacy 5D | - | 5.4695 | 12 | YES | promoted |
| 25 | legacy 5D | - | 5.4695 | 14 | NO | equal best |
| 26 | legacy 5D | - | 5.4695 | 13 | NO | later hold audit winner |
| 27 | legacy 5D | - | 5.3938 | 14 | NO | kept baseline |
| 28 | legacy 5D | - | 5.9344 | 15 | YES | promoted |
| 29 | legacy 5D | - | 5.9392 | 17 | NO | gate/equality policy retained baseline |
| 30 | legacy 5D | - | 4.3496 | 17 | NO | kept baseline |
| 31 | legacy 5D | - | 4.3490 | 18 | NO | kept baseline |
| 32 | legacy 5D | - | 5.9344 | 18 | NO | equal best |
| 33 | legacy 5D | - | 5.0129 | 21 | NO | kept baseline |
| 34 | legacy 5D | - | 5.9344 | 16 | NO | equal best |
| 35 | legacy 5D | - | 4.4980 | 19 | NO | kept baseline |
| 36 | legacy 5D | - | 5.7696 | 23 | NO | kept baseline |
| 37 | legacy 5D | - | 6.3436 | 17 | YES | promoted |
| 38 | legacy 5D | - | 4.8953 | 20 | NO | kept baseline |
| 39 | legacy 5D | - | 6.3436 | 20 | NO | equal best |
| 40 | legacy 5D | - | 5.7213 | 23 | YES | return gate promoted |
| 41 | legacy 5D | - | 4.7749 | 26 | NO | kept baseline |
| 42 | hold transition | 1.9517 | 2.3489 | 10 | NO | kept baseline |
| 43 | hold transition | 1.9517 | 2.3489 | 10 | NO | kept baseline |
| 44 | hold transition | 2.2354 | 1.5727 | 12 | NO | kept baseline |
| 45 | hold transition | 0.0000 | 1.3614 | 0 | NO | count/correlation/hold failed |
| 46 | frozen hold | 1.7911 | 2.0512 | 8 | YES | promoted |
| 47 | frozen hold | 1.8262 | 2.3505 | 10 | YES | promoted |
| 48 | frozen hold | 1.8444 | 1.9142 | 12 | YES | promoted |
| 49 | D1/D2/D3 | 2.0560 | 2.0549 | 12 | YES | promoted |
| 50 | `policy_0001` | 1.6390 | 1.7919 | 17 | NO | correlation failed |
| 51 | `policy_0002` | 1.8160 | 1.7215 | 17 | NO | correlation failed |
| 52 | `policy_0003` | 2.0098 | 1.6948 | 15 | NO | below baseline |
| 53 | `policy_0004` | 1.3992 | 1.5104 | 16 | NO | correlation failed |
| 54 | `policy_0005` | 1.5242 | 1.5760 | 15 | NO | below baseline |
| 55 | `policy_0006` | 1.4498 | 1.5929 | 14 | NO | correlation failed |
| 56 | `policy_0007` | 1.6949 | 1.6613 | 13 | NO | correlation failed |
| 57 | `policy_0008` | 1.8186 | 1.6595 | 15 | NO | correlation failed |
| 58 | `policy_0009` | 1.9124 | 1.5549 | 15 | NO | below baseline |
| 59 | `policy_0010` | 1.9706 | 1.7731 | 15 | NO | correlation failed |
| 60 | `policy_0011` | 1.6013 | 1.6567 | 14 | NO | below baseline |
| 61 | `policy_0012` | 1.6553 | 1.6075 | 17 | NO | correlation failed |
| 62 | `policy_0013` | 1.5502 | 1.6990 | 18 | NO | below baseline |
| 63 | `policy_0014` | 1.5798 | 1.7392 | 14 | NO | correlation failed |
| 64 | `policy_0015` | 1.9034 | 1.5549 | 14 | NO | below baseline |
| 65 | `policy_0016` | 2.0560 | 1.7387 | 12 | NO | equal baseline |
| 66 | `policy_0017` | 1.6608 | 1.6852 | 15 | NO | correlation failed |
| 67 | `policy_0018` | 1.4784 | 1.6518 | 18 | NO | below baseline |
| 68 | `policy_0019` | 1.7032 | 1.6276 | 17 | NO | below baseline |
| 69 | `policy_0020` | 2.1591 | 1.5549 | 14 | YES | promoted |
| 70 | `policy_0021` | 1.9791 | 1.5549 | 18 | NO | below baseline |
| 71 | `policy_0022` | 1.8810 | 1.6613 | 17 | NO | correlation failed |
| 72 | `policy_0023` | 1.9418 | 1.6527 | 17 | NO | below baseline |
| 73 | `policy_0024` | 2.2918 | 1.6214 | 16 | YES | promoted |
| 74 | `policy_0025` | 2.2829 | 1.6214 | 17 | NO | below baseline |
| 75 | `policy_0026` | 2.0907 | 1.6324 | 16 | NO | correlation failed |
| 76 | `policy_0027` | 2.3357 | 1.7457 | 19 | NO | raw leader rejected by correlation gate |
| 77 | `policy_0028` | 2.2829 | 1.5549 | 17 | NO | below baseline |
| 78 | `policy_0029` | 2.1793 | 1.7390 | 17 | NO | correlation failed |
| 79 | `policy_0030` | 2.1263 | 1.8734 | 17 | NO | correlation failed |
| 80 | `policy_0031` | 2.0502 | 1.5884 | 15 | NO | correlation failed |
| 81 | `policy_0032` | 2.2270 | 1.5549 | 15 | NO | below baseline |
| 82 | `policy_0033` | 2.2880 | 1.5549 | 18 | NO | below baseline |
| 83 | `policy_0034` | 2.0631 | 1.6425 | 17 | NO | correlation failed |
| 84 | `policy_0035` | 2.0572 | 1.7171 | 15 | NO | correlation failed |
| 85 | `policy_0036` | 2.0502 | 1.6911 | 15 | NO | correlation failed |
| 86 | `policy_0037` | 2.2150 | 1.5549 | 18 | NO | below baseline |
| 87 | `policy_0038` | 2.0579 | 1.7390 | 17 | NO | correlation failed |
| 88 | `policy_0039` | 2.2682 | 1.8059 | 18 | NO | below baseline |
| 89 | `policy_0040` | 2.0883 | 1.5937 | 18 | NO | correlation failed |
| 90 | `policy_0041` | 2.3057 | 1.7112 | 18 | NO | below baseline |
| 91 | `policy_0042` | 2.0940 | 1.6324 | 16 | NO | correlation failed |
| 92 | `policy_0043` | 2.0895 | 1.6338 | 17 | NO | correlation failed |
| 93 | `policy_0044` | 2.2270 | 1.6214 | 15 | NO | below baseline |
| 94 | `policy_0045` | 2.1080 | 1.6159 | 16 | NO | correlation failed |
| 95 | `policy_0046` | 2.1160 | 1.6338 | 18 | NO | correlation failed |
| 96 | `policy_0047` | 2.0325 | 1.5549 | 17 | NO | below baseline |
| 97 | `policy_0048` | 2.0221 | 1.7292 | 18 | NO | correlation failed |
| 98 | `policy_0049` | 2.2829 | 1.6214 | 17 | NO | below baseline |
| 99 | `policy_0050` | 2.0872 | 1.7390 | 16 | NO | correlation failed |
| 100 | `policy_0051` | 2.3005 | 1.5549 | 17 | NO | below baseline |
| 101 | `policy_0052` | 2.2880 | 1.5549 | 18 | NO | below baseline |
| 102 | `policy_0053` | 2.1001 | 1.7719 | 17 | NO | correlation failed |
| 103 | `policy_0054` | 2.1406 | 1.5602 | 16 | NO | below baseline |
| 104 | `policy_0055` | 2.0966 | 1.7879 | 16 | NO | correlation failed |
| 105 | `policy_0056` | 2.3130 | 1.5549 | 18 | NO | valid near miss |
| 106 | `policy_0057` | 2.2298 | 1.7364 | 21 | NO | structure / AST regularizer |
| 107 | `policy_0058` | 2.3232 | 1.7238 | 20 | NO | structure / AST regularizer |
| 108 | `policy_0059` | 2.2206 | 1.5527 | 20 | NO | parent selection / parent mode; correlation failed |
| 109 | `policy_0060` | **2.3256** | 1.6214 | 17 | YES | diversity / top-N; current live |
| 110 | `policy_0061` | 2.2348 | 1.5969 | 21 | NO | search budget / population size |
| 111 | `policy_0062` | 2.2300 | 1.8388 | 15 | NO | parent selection / DAG similarity |
| 112 | `policy_0063` | 2.3159 | 1.6804 | 19 | NO | diversity / dedup threshold |
| 113 | `policy_0064` | 2.2723 | 1.5527 | 19 | NO | search budget / patience |
| 114 | `policy_0065` | 2.2795 | 1.7133 | 20 | NO | parent selection / global epsilon; paired rejected |

[source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
[source: `OPERATION_LOG.md`, archive migration and iter109 resume entries]

## Paired campaigns

| Child | Parent | Valid pairs | Mean delta | Win rate | Selected | 主要失败门槛 |
|---|---|---:|---:|---:|---|---|
| `policy_0060` | archived parent | 3/3 | 0.0000 | 0.000 | NO | mean、median、win rate |
| `policy_0062` | archived parent | 0/3 | N/A | 0.000 | NO | pair validity and all performance gates |
| `policy_0065` | `policy_0011` | 2/3 | +0.0358 | 0.500 | NO | min pairs、all valid、win rate |

这些 paired 结果不回滚 iteration 109 的现有 live 文件；它们限制的是新版 RSI
档案中的 parent eligibility，防止单次幸运运行继续产生后代。

[source: `wiki/factor_rsi_phase2_paired_selection_20260921.md`]
[source: local runtime `dgm_rsi/paired/*/paired_evaluation_receipt.json`]

## 平行分支与非编号实验

- 10D 分支完成 7 次正式 iteration，第 8 次中断；iteration 4 是最终基线。
- 20D 分支完成 12 次；iteration 5 是保留基线，但训练期 Sharpe 为负，不能视为
  干净晋级。
- T+1 全库审计把 69 个来源库压缩为 54 个不同集合，评估 115 个表达式；旧 live
  在新执行合约下不再占优。
- stock-to-factor matching 做了 12 轮，validation Sharpe 1.722，但冻结 test Sharpe
  只有 0.374，未晋级。
- 两个 recent-regime matching campaign 各做 8 轮；MA20 gate 改善已观察区间，
  但因为不是盲测且主板仍弱，只保留为研究结论。
- iteration 49 后的全表达式审计覆盖 119 个表达式和 6,426 个合约行；38 个表达式
  至少通过一个严格近期合约。
- score-bucket 审计产生 42,840 个桶级结果；最大有利波动与可实现收益被明确分开。
- 2026-09-18 曾误把 RSI 理解成 Relative Strength Index 并做 graft；相关 live 修改
  已回滚到 iteration 49。此后 RSI 只表示 Recursive Self-Improvement。

[source: `wiki/factor_t1_board_exit_full_library_audit_20260831.md`]
[source: `wiki/factor_stock_matching_evolution_20260831.md`]
[source: `wiki/factor_recent_regime_matching_20260911.md`]
[source: `wiki/factor_recent_all_expression_audit_20260913.md`]
[source: `wiki/factor_score_bucket_max_horizon_audit_20260913.md`]
[source: `wiki/factor_rsi_means_recursive_self_improvement_20260918.md`]

## 关键教训

1. **优化交易合约，而不是代理指标。** iteration 37 的 legacy Test Sharpe 最高，
   但 realistic hold 排名更差；iteration 26 的库在统一 hold 审计中反而更好。
2. **高分不等于可晋级。** iteration 76 的 Hold Sharpe 2.3357 高于当时 live，
   但相关性 gate 失败，因此正确地没有进入 live。
3. **外层策略也会坍缩。** iteration 73 后，DGM 逐渐重复相似配方；四岛 mutation、
   单字段变异和 verified-parent archive 是为解决这一问题加入的。
4. **单次胜利不能证明可遗传改进。** iteration 109 进入 live，但 paired campaign
   未胜出，因此不能继续作为可繁殖 child。
5. **状态层必须分开。** `live_library.csv` 表示当前生产候选；policy archive 表示
   哪些自改进策略允许繁殖；paired receipt 表示因果复现是否通过。三者不可互相替代。

## 下一步

- 保持 iteration 109 live library 不变，除非新候选同时通过 frozen single-run gates
  和三种子 paired selection。
- 将 paired receipt 的最终结果同步进 `state.json`/`STATE.md`，避免“campaign running”
  与本地已完成收据不一致。
- 把目前 gitignored 的最小 paired receipts 提炼成可提交、内容寻址的证据包；不要提交
  整个运行缓存或 `.semas_repo` 种群快照。
- 新数据到来后建立真正未观察的 forward snapshot；当前 2026-07-16 之前的数据已经被
  多次查看，不能继续充当新的盲测集。

## References

- [source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
- [source: `china_a_share_alpha_output/factor_mining_loop/STATE.md`]
- [source: `china_a_share_alpha_output/factor_mining_loop/live_library.csv`]
- [source: `OPERATION_LOG.md`]
- [source: `wiki/factor_mining_loop_index.md`]
- [source: `wiki/factor_mining_loop_multihizon_batch_audit.md`]
- [source: `wiki/factor_dgm_rsi_factor_mining_20260918.md`]
- [source: `wiki/factor_dgm_rsi_anti_collapse_islands_20260920.md`]
- [source: `wiki/factor_rsi_phase1_causal_verifier_20260920.md`]
- [source: `wiki/factor_rsi_phase2_paired_selection_20260921.md`]
