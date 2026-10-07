# RSI 反塌陷：正交搜索面 + 单字段突变

Date: 2026-09-20

## 问题

DGM 外环在 iter73 之后长期未晋升。档案里绝大多数策略 notes 塌成同一配方：

`relax_dedup+diversity,expand_search+dag,shrink_top_n,+explore_*`

根因：`mutate_policy` 对每次诊断**叠满所有修复算子**（aggressive_dedup → 放宽去重；hold_regression → 扩搜索+强制 dag；selection_corr_gate → 缩小 top_n）。失败模式高度重复，于是策略空间塌成单一吸引子。

[source: arXiv:2505.22954 Darwin Gödel Machine]

## 设计原则

1. **搜索策略 ≠ 考官**：`promote_hold_sharpe_threshold` 与 `max_selection_correlation_gate` 冻结，禁止自改评分器来“变好看”。
2. **一次只改一个功能字段**：杜绝叠满修复。
3. **正交搜索面（四岛）**，每次 propose 只落在一个面：
   - `search_budget`：`population_size` / `max_generations` / `patience`
   - `parent_selection`：`parent_mode` / `global_epsilon` / `dag_edge_similarity`
   - `diversity`：`semantic_dedup_corr_threshold` / `keep_diversity_slots` / `top_n`
   - `structure`：`ast_regularizer_enabled` / `ast_similarity_tau`
4. **父代采样混合**：fitness 35% + underexplored 25% + novelty 25% + uniform 15%，并对过热 island 降权；岛选择 40% underused / 40% diagnosis-preferred / 20% uniform。
5. **档案 v2 资格**：仅 `eligible_parent=True`（门控通过 + 冻结考官一致）可繁殖；v1 档案经 `--audit-existing` 迁移。

## 落地验证（2026-09-20）

- Archive audit：bootstrap 1 + valid 27 + invalid 29（多因 `max_corr_ok` 失败）→ 28 个可繁殖父代
- `policy_0056`（iter105，hold 2.313，近失 +0.021）记为 `evaluated_valid`
- `policy_0057` propose：parent=`policy_0054`，`surface=structure`，单字段 `ast_regularizer_enabled True→False`；考官仍为 0.03 / 0.7

## 预期

相关门失败偏向 `diversity` 调 top_n/去重，而不是永远 shrink；近失走 diversity/parent_selection；结构探索走 `structure`；搜索预算走 `search_budget`。不再出现三件套叠满 notes。
