---
date: 2026-10-08
tags: [factor-evolution, state-reconciliation, verification, git-worktree, rsi]
sources:
  - ../../china_a_share_alpha_output/factor_mining_loop/state.json
  - ../../china_a_share_alpha_output/factor_mining_loop/STATE.md
  - ../../OPERATION_LOG.md
related:
  - ../factor_evolution_complete_history_1_114.md
  - rsi_causal_credit_assignment_20260920.md
  - rsi_paired_evidence_before_reproduction_20260921.md
---

# 多事实源因子进化状态重建方法

## 核心认识

“因子进化到第几轮”不是只查一个目录名就能回答的问题。仓库同时存在 Git
分支、独立 worktree、gitignored 运行目录、机器状态、人工摘要、逐轮报告和 paired
receipt。它们可能处于不同提交点，也可能表达不同状态层。可靠结论必须先定义口径，
再做证据优先级和交叉验证。

[source: `china_a_share_alpha_output/factor_mining_loop/state.json`]
[source: `OPERATION_LOG.md`]

## Task Decomposition

- Objective：重建外层 iteration、内部 generation、live library、策略档案和 paired
  eligibility 的完整状态，并形成其他工具可直接读取的单页账本。
- Constraints：不覆盖 dirty worktree；不提交 `.env`、运行缓存或密钥；保留旧指标与
  新 hold 指标不可直接比较的边界；所有提交必须有测试和 Git 回执。
- Evidence branches：
  1. 机器状态分支：`state.json`、`live_library.csv`、`STATE.md`。
  2. 研究记录分支：`OPERATION_LOG.md`、原子 wiki、审计结论。
  3. 运行证据分支：iteration 目录、内部 history、paired receipts。
  4. 版本控制分支：当前 worktree、因子 worktree、本地 refs、远端 refs。
- Ambiguities：iteration 11 是非变异压测；早期 internal histories 已轮转；paired
  eligibility 与 production live 状态是两个不同契约。

## Agent Engineering

本次没有启动子代理；以下是用于约束工作的逻辑角色和 I/O 合约。

| Role | Inputs | Outputs | Failure mode |
|---|---|---|---|
| State auditor | `state.json`, live receipt | iteration、live、逐轮指标 | 把 baseline 当 candidate |
| History auditor | operation/wiki/runtime | 阶段、失败、方法变化 | 把 TOP 100 当 100 iterations |
| Git auditor | branches、worktrees、remote refs | dirty/ahead/behind 清单 | 只看当前 checkout |
| Synthesizer | 三类审计结果 | 1–114 单页账本 | 混用 legacy Test 与 Hold Sharpe |
| Verifier | 合成页、机器状态、Git index | 行数、缺号、引用、secret、tests | 只验证 prose 不验证 state |

## Workflow Orchestration

- Topology：scope root → 状态/历史/Git 三个独立证据分支 → 单一 synthesis → verifier
  → commit/push receipt。
- State：`state.json` 决定外层编号和 production live；paired receipt 决定 RSI
  reproduction eligibility；两者不互相覆盖。
- Verification：逐轮表必须包含 1–114 且无重复；frontmatter 必须与机器状态一致；
  `.env` 必须被忽略；代码 checkpoint 必须通过测试；远端 SHA 必须等于推送 SHA。
- Retry/recovery：权限或 daemon 中断后先重新读取 status/ref，不重做 commit/push；
  外部 worktree 的写入失败时，在可写 worktree 基于同一 commit 生成文档，再推送同一
  远端分支。
- Human gates：不强制加入 gitignored runtime tree，不把研究指标解释成实盘授权。

## Selection Plan

- Metrics：114/114 ledger rows、0 missing、0 duplicate；machine iteration 114；live
  iteration 109；Hold Sharpe 2.325596；secret scan 0 hits。
- Validation tasks：完整测试 119 passed、2 token-gated skipped；YAML frontmatter
  parse；required-source existence；`git diff --check`；远端 ref equality。
- Cost controls：只提交 compact state、live library、代码、测试和 wiki；忽略大规模
  populations、`.semas_repo` 和重复运行缓存。
- Rollback：checkpoint 与 wiki 分成两个提交；若文档错误，可单独回滚文档提交，
  不破坏 iteration 114 的代码和状态 checkpoint。

## 方法论结论

1. **分支、worktree、远端是三个状态变量。** 当前分支干净不代表另一个 worktree
   没有 60 多轮未提交进化。
2. **编号与证据层必须解耦。** 外层 114 轮、当前可核 796 个内部 generation、119 个
   审计表达式是三类统计，任何两类都不能互换。
3. **机器状态与复现资格必须分层。** iteration 109 可以保持 production live，
   同时 `policy_0060` 因 paired campaign 失败而失去繁殖资格。
4. **恢复动作必须幂等。** 每次 daemon 重启后先检查 commit、remote ref、index 和
   worktree，再决定继续点，避免重复提交或重复推送。
5. **综合页必须可验证。** YAML frontmatter、完整逐轮表、稳定来源路径和明确口径，
   比只写叙述性总结更适合跨工具长期读取。

## Related pages

- [Factor evolution complete history 1–114](../factor_evolution_complete_history_1_114.md)
- [RSI causal credit assignment](rsi_causal_credit_assignment_20260920.md)
- [RSI paired evidence before reproduction](rsi_paired_evidence_before_reproduction_20260921.md)
