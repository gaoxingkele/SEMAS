# SEM 融合层时辰校准评估（2026-07-24）

> 对应 2026-07-09 回测报告的建议「让不同人物类型使用不同专家权重」：
> 本文构建一个从数据学习融合权重的一因子 SEM（结构方程模型），并用
> 留一案例交叉验证（LOCO）**诚实**对比三个基线。结论先行：**SEM 没有跑赢
> 基线**，在 132 行小样本下 LOCO 表现反而弱于等权平均与改进后横门断。
> 代码与数据集保留在管线中供后续样本扩充后复评。

## 1. 数据集

脚本：`examples/mingli_5agents/case_studies/hour_calibration/sem_fusion.py`
的 `build_dataset`（复用 `calibrate_case`，结果缓存于
`outputs/sem_fusion_dataset.json`，`--recompute` 可强制重算）。

- 形状：11 案例 × 12 候选 = **132 行**，正例 11（每案例 1 个公开参考时辰）。
- 特征（26 维，全部来自现有评分输出，未改任何 hengmen/bazi_* 逻辑）：
  - 横门 AHP 8 个 vote 维度（事件权重加权平均）：`hengmen_vote_{month_pattern,
    stem_root, success_rescue, event_ten_god, palace_trigger, luck_support,
    annual_interaction, fact_calibration}`
  - 7 个流派分：`school_{yuanhai_ziping, ziping_zhenquan, sanming_tonghui,
    ditiansui, qiongtong_baojian, shenfeng_tongkao, hengmen}`
  - 9 个书籍框架分：`book_{yuanhai_ziping, ziping_zhenquan, mingli_jicheng,
    lixuzhong_mingshu, yuzhao_dingzhenjing, xingping_huihai,
    ziwei_doushu_quanshu, christian_astrology, geju_hengmen_duan}`
  - 基础分 2 维：`event_fit_total`、`chart_strategy_total`
- 标签：`is_reference`（候选时辰 ∈ 公开参考时辰）。

## 2. 模型设定（参数克制）

- 测量模型：26 个观测指标 → 单潜变量「时辰契合度」η，Var(η)=1 定识别，
  对角测量误差（ψ 对角阵）。参数 26 载荷 + 26 独特方差。
- 结构模型：P(参考时辰) = logit⁻¹(β0 + β1·η̂)，η̂ 为 Thomson 回归因子得分。
  参数 2。
- 估计：numpy/scipy 手写两步 ML——先对标准化指标做 ML 探索性因子分析
  （L-BFGS-B，解析梯度，F = log|Σ| + tr(S·Σ⁻¹)），再对因子得分做 ML logit。
  不引入 semopy 等重依赖。

## 3. 全样本载荷表（描述性，非评估口径）

全样本 logit：β0 = -2.4148，β1 = 0.2068（弱正）。

| 特征 | 载荷 | 独特方差 |
|---|---:|---:|
| book_mingli_jicheng | 0.985 | 0.030 |
| school_ditiansui | 0.885 | 0.217 |
| book_lixuzhong_mingshu | 0.879 | 0.227 |
| book_xingping_huihai | 0.874 | 0.236 |
| book_yuzhao_dingzhenjing | 0.856 | 0.267 |
| school_sanming_tonghui | 0.847 | 0.283 |
| school_qiongtong_baojian | 0.777 | 0.397 |
| hengmen_vote_palace_trigger | 0.696 | 0.515 |
| school_yuanhai_ziping | 0.597 | 0.644 |
| book_ziwei_doushu_quanshu | 0.511 | 0.739 |
| hengmen_vote_annual_interaction | -0.444 | 0.803 |
| book_ziping_zhenquan | 0.436 | 0.810 |
| hengmen_vote_stem_root | -0.393 | 0.845 |
| school_ziping_zhenquan | 0.359 | 0.871 |
| book_yuanhai_ziping | 0.336 | 0.887 |
| school_hengmen | -0.248 | 0.939 |
| hengmen_vote_month_pattern | -0.231 | 0.947 |
| book_geju_hengmen_duan | -0.225 | 0.949 |
| hengmen_vote_luck_support | -0.210 | 0.956 |
| event_fit_total | 0.184 | 0.966 |
| hengmen_vote_fact_calibration | -0.174 | 0.970 |
| book_christian_astrology | 0.140 | 0.980 |
| school_shenfeng_tongkao | 0.110 | 0.988 |
| hengmen_vote_event_ten_god | -0.088 | 0.992 |
| hengmen_vote_success_rescue | 0.086 | 0.993 |
| chart_strategy_total | 0.000 | 0.000（Heywood 个案，见 §6） |

解读注意：公共因子主要吸收的是**书籍/流派分之间的共识方差**（彼此高度
相关、候选间区分度低），而回测中区分度最好的横门 vote（success_rescue
等）载荷接近零——潜变量量尺与「能拉开候选排序的信号」错位，这是 LOCO
失败的机制性解释。

## 4. LOCO 评估（留一案例，每次 10 案例 120 行训练）

| 方法 | 平均参考排名 | Top1 命中 | Top3 命中 |
|---|---:|---:|---:|
| **SEM 融合** | **6.00** | 1 | 3 |
| 等权平均 | **4.36** | **3** | **7** |
| 综合 AHP（strategy_total） | 5.45 | 1 | 5 |
| 改进后横门断（school hengmen） | 5.09 | **3** | 5 |

逐案例参考排名（SEM / 等权 / 综合AHP / 横门）：

| 案例 | SEM | 等权 | 综合AHP | 横门 |
|---|---:|---:|---:|---:|
| angelina_jolie | 8 | 3 | 4 | 2 |
| audrey_hepburn | 5 | 8 | 9 | 9 |
| barack_obama | **1** | 12 | 12 | 12 |
| bruce_lee | 7 | 1 | 5 | 3 |
| donald_trump | 3 | 3 | 3 | 6 |
| jackie_chan | 5 | 2 | 3 | 4 |
| mao_zedong | 12 | 1 | 2 | 1 |
| marilyn_monroe | 7 | 4 | 9 | 6 |
| michael_jackson | 8 | 2 | 3 | 1 |
| oprah_winfrey | 7 | 11 | 9 | 11 |
| taylor_swift | 3 | 1 | 1 | 1 |

注：综合 AHP 此处为 5.45（改进后管线重算口径），与旧报告的 6.36 不同，
属预期差异。

## 5. 结论（诚实版）

- **SEM 融合没有跑赢任何有意义的基线**：LOCO 平均参考排名 6.00，接近随机
  期望 6.5，弱于等权平均（4.36）、改进后横门断（5.09）和综合 AHP（5.45）。
  Top1 仅 1 例（barack_obama，恰是三个基线全部垫底的案例）。
- 等权平均（26 维原始分简单求均值）反而成为最强基线，说明在该样本上
  「融合」的价值主要来自降低单一方法的特异噪声，而**学习权重**在 11 个
  正例上估不稳：每折只有 10 个正例训练 logit，β1 对折间扰动极敏感。
- 未做任何过拟合调参：模型规格（一因子 + 对角误差 + logit 链接）在拿到
  LOCO 结果前即固定，结果差也如实报告。
- 2026-07-09 报告「不同人物类型用不同专家权重」的方向**未被证伪**，但
  132 行 × 11 正例的样本量不足以支撑逐案例权重学习；需要更多案例或改为
  案例级特征（如人物类型先验分桶）+ 更少参数的混合模型。

## 6. 限制与残余风险

- `chart_strategy_total` 出现 Heywood 个案（独特方差贴 0 下界、载荷 0），
  是小样本 ML 因子分析的典型退化解；未做特殊处理，仅记录。
- 两步估计（先 FA 后 logit）忽略因子得分的不确定性，结构系数的标准误
  被低估；本报告不依赖推断显著性，影响可控。
- 潜变量主要吸收书籍/流派共识方差，与候选区分信号错位（§3）；若后续
  重试，应先按「候选间区分度」筛选指标再入 SEM，而不是全量 26 维。
- 派生反例、参考时辰可信度等上游数据问题与横门断改进报告 §6 相同，
  本层不重复解决。
- 数据集缓存 `outputs/sem_fusion_dataset.json` 由当前评分代码生成；
  上游评分逻辑变更后需 `--recompute` 重算。

## 7. 验证命令

- `py -3.14 -m examples.mingli_5agents.case_studies.hour_calibration.sem_fusion --recompute`
  → 重建 132 行数据集 + LOCO，输出 `outputs/sem_fusion_loco.json`
- `py -3.14 -m pytest examples/mingli_5agents/tests/test_sem_fusion.py -q` → 6 passed
- `py -3.14 -m pytest examples/mingli_5agents/tests -q` → 330 passed（含新增 6 个）
