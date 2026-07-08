# 影视明星时辰校准验证（2026-07-06）

本轮使用最新的分层命盘策略验证 4 个影视明星案例。方法是：公开出生时辰只作为参考答案，事件拟合器先按未知时辰生成 12 个候选，再看参考时辰排名。

2026-07-07 更新：已接入《格局横门断》docx 抽取出的 AHP 层次化评分，综合分权重调整为：事件拟合 0.35、分层事件 0.20、原局策略 0.10、横门 AHP 0.35。

## 结论摘要

| 人物 | 公开参考时辰 | 算法第一名 | 参考时辰排名 | 判定 | 说明 |
|---|---|---|---:|---|---|
| Bruce Lee | 辰时，07:12 | 丑时 | 4 | 未命中但改善 | 参考辰时从第 5 升至第 4，仍未进前三。 |
| Jackie Chan | 巳时，09:45 | 巳时 | 1 | 命中 | 横门 AHP 接入后，公开参考巳时升为第一。 |
| Marilyn Monroe | 巳时，09:30 | 辰时 | 6 | 未命中但改善 | 参考巳时从第 8 升至第 6，仍偏低。 |
| Audrey Hepburn | 寅时，03:00 | 子时 | 9 | 未命中 | 参考寅时仍排第 9。 |

## 分数记录

| 人物 | 第一名分数 | 第二名差距 | 参考时辰分差 | 参考是否前三 |
|---|---:|---:|---:|---|
| Bruce Lee | 0.6531 | 0.0046 | 0.0256 | 否 |
| Jackie Chan | 0.6219 | 0.0100 | 0.0000 | 是 |
| Marilyn Monroe | 0.6549 | 0.0039 | 0.0558 | 否 |
| Audrey Hepburn | 0.5584 | 0.0104 | 0.0350 | 否 |

## 方法判断

这轮验证说明，最新策略有两个进步：

- 所有案例都没有强行给“明确命中”，领先幅度小就判为不明确。
- 输出已拆分为事件拟合、分层事件、原局策略和公开参考对比，冲突能被看见。

横门 AHP 接入后的变化：

- 成龙案例从“接近命中”变成“命中”，说明横门的月令取格、宫位落事和事实筛选对职业型明星案例有效。
- 李小龙和梦露的参考时辰排名上升，但仍没有进入前三，说明评分有改善但不够。
- 赫本案例没有改善，说明事件表缺少月份、战争童年、健康和人道主义转型的细颗粒事实。

仍然暴露三个问题：

- 事件类型太粗，影视明星的“作品爆红、奖项、转型、丑闻、健康、死亡”还需要更细标签。
- 事件年份缺少月份，无法验证具体流月和临界点。
- 跨文化案例只用八字年支冲合评分会偏硬，需要把职业作品类型、公众声量和长期形象纳入宫位事件票。

## 需要升级的评分规则

- 为影视人物新增事件类型：`award_peak`、`box_office_breakthrough`、`iconic_role`、`career_reinvention`、`public_scandal`、`health_crisis`。
- 对已知参考时辰的样本，报告必须输出：参考时辰排名、与第一名分差、是否进前三。
- 如果参考时辰进前三且分差低于 0.02，判为“接近命中”，不判失败。
- 如果所有候选领先差距低于 0.05，必须保持“不明确”，不能硬锁时辰。

## 来源

- Bruce Lee birth reference: https://astro-charts.com/persons/chart/bruce-lee/
- Jackie Chan birth reference: https://astro-charts.com/persons/chart/jackie-chan/
- Marilyn Monroe birth reference: https://astro-charts.com/persons/chart/marilyn-monroe/
- Audrey Hepburn birth reference: https://celebrity.astrosage.com/audrey-hepburn-birth-chart.asp
- Bruce Lee events: https://en.wikipedia.org/wiki/Bruce_Lee
- Jackie Chan events: https://en.wikipedia.org/wiki/Jackie_Chan
- Marilyn Monroe events: https://en.wikipedia.org/wiki/Marilyn_Monroe
- Audrey Hepburn events: https://en.wikipedia.org/wiki/Audrey_Hepburn
