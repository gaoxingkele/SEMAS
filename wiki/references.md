# References

@software{lunar_python_1_4_8,
  title = {lunar-python},
  version = {1.4.8},
  note = {Exact Chinese calendar backend used for the default four-pillar provider}
}

> Centralized citation list for the SEMAS LLM Wiki. Every `[source: ...]` link
> in the wiki should resolve to an entry here.

## Mingli Source Leads

- **格局横门断**
  - Local DOCX reference used to derive the independent Hengmen rule graph.
  - [source: `tools/格局横门断.docx`]

- **Yuanhai Ziping / Ziping Zhenquan scan**
  - Wikimedia Commons / National Library of China scan
  - https://commons.wikimedia.org/wiki/File:NLC416-15jh007754-99036_%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE.pdf
  - [source: Wikimedia Commons NLC scan]

## Agent Skills Tooling

- **book-to-skill** (virgiliojr94)
  - https://github.com/virgiliojr94/book-to-skill
  - Converts owned books/docs into structured Agent Skills (`SKILL.md`).
  - Local install: `.cursor/skills/book-to-skill/` (junction: `.agents/skills/book-to-skill`)
  - [source: https://github.com/virgiliojr94/book-to-skill]

## SEMAS Framework

- SEMAS — Self-Evolving Multi-Agent System Framework
  - Local source: `README.md`, `semas/`
  - Core idea: frozen-weight LLM + selection-based evolution over prompts,
    tools, topologies, and memory.

## China A-Share Alpha Factor Mining

- Local operational record: `OPERATION_LOG.md` (entries 2026-06-24 through
  2026-06-30).
- Local code:
  - `china_a_share_alpha/scripts/clean_factor_library.py`
  - `china_a_share_alpha/scripts/run_factor_combination.py`
  - `china_a_share_alpha/scripts/run_portfolio_weight_evolution.py`

- **WorldQuant 101 Formulaic Alphas**
  - Kakushadze, "101 Formulaic Alphas", 2016
  - arXiv:1601.00991, https://arxiv.org/abs/1601.00991

- **TA-Lib — Technical Analysis Library**
  - https://ta-lib.org/

- **Optimal versus Naive Diversification: How Inefficient is the 1/N Portfolio
  Strategy?**
  - DeMiguel, Garlappi, Uppal, *Review of Financial Studies*, 2009
  - https://academic.oup.com/rofs/article/22/5/1915/1578602
  - Key insight: sample-based mean-variance optimization often loses to a simple
    equal-weighted portfolio because estimation error dominates.

- **A Taxonomy of Anomalies and Their Trading Costs**
  - Novy-Marx & Velikov, *Review of Financial Studies*, 2016
  - https://academic.oup.com/rofs/article/29/2/397/1843824
  - Key insight: transaction costs and turnover can eliminate or even reverse
    the apparent profitability of many cross-sectional anomalies.

- **... and the Cross-Section of Expected Returns**
  - Harvey, Campbell R., Liu, Yan, and Zhu, Heqing, *Review of Financial
    Studies*, 2016
  - https://academic.oup.com/rfs/article/29/1/5/1843824
  - Key insight: after accounting for multiple testing, many claimed anomalies
    disappear; simple, diversified, and robustly selected signals tend to
    outperform complex optimization in noisy cross-sections.

- **Homemade Foreign Trading**
  - He, Zhiguo, et al., BFI Working Paper 2022-170 / 2026
  - https://bfi.uchicago.edu/wp-content/uploads/2023/01/BFI_WP_2022-170.pdf
  - Key insight: northbound Stock Connect flows in A-shares predict future
    returns, especially before the 2018 investor-identification reform; the
    predictive power is heterogeneous across custodian types.

## GEO / AgenticGEO

- **GEO: Generative Engine Optimization**
  - Aggarwal et al., KDD 2024
  - arXiv:2311.09735, https://arxiv.org/abs/2311.09735
  - Code: https://github.com/GEO-optim/GEO
  - [source: ../geo-benchmark/README.md]

- **AgenticGEO: A Self-Evolving Agentic System for GEO**
  - Yuan et al., 2026
  - arXiv:2603.20213, https://arxiv.org/abs/2603.20213
  - Code: https://github.com/AIcling/agentic_geo
  - Key: MAP-Elites archive + co-evolving critic + multi-turn rewriting.
  - [source: ../geo-benchmark/code/agenticgeo/README.md]

- **AutoGEO**
  - Wu et al., ICLR 2026
  - arXiv:2510.11438, https://arxiv.org/abs/2510.11438
  - Code: https://github.com/cxcscmu/AutoGEO
  - Key: rule extraction + prompt-based/RL rewriter.

- **E-GEO: A Testbed for GEO in E-Commerce**
  - Bagga et al., 2025
  - arXiv:2511.20867, https://arxiv.org/abs/2511.20867
  - Code: https://github.com/psbagga17/E-GEO
  - Key: iterative prompt meta-optimization.

- **Multi-Agent GEO via Reusable Strategy Learning**
  - Bian et al., ACL 2026 Findings
  - arXiv:2604.19516, https://arxiv.org/abs/2604.19516
  - Key: experience-to-skill transfer across agents.

- **Think Before Writing: Feature-Level Multi-Objective Optimization (FeatGEO)**
  - Liu & Xu, 2026
  - arXiv:2604.19113, https://arxiv.org/abs/2604.19113
  - Key: NSGA-II over interpretable feature space.

## Self-Improving / Self-Referential Agents

- **Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement**
  - Yin et al., ACL 2025
  - arXiv:2410.04444, https://arxiv.org/abs/2410.04444
  - Code: https://github.com/Arvid-pku/Godel_Agent
  - Key: recursive self-modification via runtime memory inspection/monkey patching.

- **FunctionEvolve: Structure-Guided Symbolic Regression with LLMs**
  - Xia et al., 2026
  - arXiv:2606.07704, https://arxiv.org/abs/2606.07704
  - Code: https://github.com/Phoinikas03/FunctionEvolve
  - Key: AST expression-tree search + LLM-guided mutations + structure-aware
    coefficient optimizer.

- **SIA: Self Improving AI with Harness & Weight Updates**
  - Hebbar et al., 2026
  - arXiv:2605.27276, https://arxiv.org/abs/2605.27276
  - Code: https://github.com/hexo-ai/sia
  - Key: Meta-Agent / Target Agent / Feedback Agent loop; updates both harness
    and model weights (LoRA).

## Related Surveys / Frameworks

- **Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents**
  - Zhang et al., 2025
  - arXiv:2505.22954, https://arxiv.org/abs/2505.22954
  - Key: open-ended self-improving agents.

- **Hyperagents**
  - Zhang et al., 2026
  - arXiv:2603.19461, https://arxiv.org/abs/2603.19461

- **AI Scientist**
  - Lu et al., 2024
  - Key: automated scientific discovery agent.

## Mingli Primary Sources

- **《三命通会》（明·万民英，四库全书本）**
  - Kanripo 校勘电子文本 KR3g0042, https://github.com/kanripo/KR3g0042
  - Local: `external/mingli_books/bazi/extended/text_sources/sanming_tonghui_kanripo/`
  - Key: 百科型古法综合；月令为纲、财官为本；十神正格（卷五）为主、
    神煞纳音为辅；卷十《看命口訣》为总法。

- **《穷通宝鉴》（栏江网/造化元钥）**
  - Skill: `mingli-bazi-qiongtong-baojian`（tiaohou_table.md 录各篇末「喜用提要」）
  - Key: 调候用神体系；时辰校准中作格局之外的独立侧证（如三月癸水"专用辛，忌戊"）。

- **《命理集成》**
  - Skill: `mingli-jicheng`（shensha_index.md 54 节 / pattern_index.md 28 格局）
  - Key: 神煞广谱扫描底稿；总纲"神煞无定局，因喜忌而异"决定其只能微调、
    不可对冲格局成败。
