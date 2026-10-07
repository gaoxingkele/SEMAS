# References

> Centralized citation list for the SEMAS LLM Wiki. Every `[source: ...]` link
> in the wiki should resolve to an entry here.

## Mingli Source Leads

- **Yuanhai Ziping / Ziping Zhenquan scan**
  - Wikimedia Commons / National Library of China scan
  - https://commons.wikimedia.org/wiki/File:NLC416-15jh007754-99036_%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE.pdf
  - [source: Wikimedia Commons NLC scan]

## SEMAS Framework

- SEMAS — Self-Evolving Multi-Agent System Framework
  - Local source: `README.md`, `semas/`
  - Core idea: frozen-weight LLM + selection-based evolution over prompts,
    tools, topologies, and memory.

- SEMAS Smart_SkillandAgent Topic
  - Local source: `Smart_SkillandAgent/README.md`
  - Core idea: one GitHub-origin skill or agent repository per subproject, with
    source provenance, evolution records, evaluation receipts, and a local LLM
    wiki preserved inside that subproject boundary.

- Loop Engineering
  - GitHub: https://github.com/cobusgreyling/loop-engineering
  - Local source: `Smart_SkillandAgent/projects/cobusgreyling_loop-engineering/`
  - License: MIT
  - Selected revision: `015ad4a57f210bafac1497fd5305d67bf728a21f`

- Patent Disclosure Skill
  - GitHub: https://github.com/handsomestWei/patent-disclosure-skill
  - Local source: `Smart_SkillandAgent/projects/handsomestWei_patent-disclosure-skill/`
  - License: MIT
  - Selected revision: `c4b843e2037376ce65a63f8db09b0cf635002b8f`

- Skill-MAS
  - Paper: arXiv:2606.18837, https://arxiv.org/abs/2606.18837
  - GitHub: https://github.com/linhh29/Skill-MAS
  - Canonical GitHub path after redirect: https://github.com/linhh29/Skill_MAS
  - Project page: https://linhh29.github.io/blog/Skill-MAS/index.html
  - Demo: https://skill-mas-demo.hehailin.life/
  - Local source: `Smart_SkillandAgent/projects/linhh29_Skill_MAS/`
  - License: Apache-2.0
  - Selected revision: `b55d47ee7a08b34afda420bb3c5f2ca53efa64a4`

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

- **AlphaGen — Generating Synergistic Formulaic Alpha Collections via RL**
  - Yu et al., KDD 2023 [CCF-A]
  - arXiv:2306.12964, https://doi.org/10.1145/3580305.3599831
  - Code: https://github.com/ICT-FinD-Lab/alphagen (local `external/alphagen`)

- **AlphaAgent — LLM-Driven Alpha Mining with Regularized Exploration**
  - Tang et al., KDD 2025 [CCF-A]
  - arXiv:2502.16789, https://doi.org/10.1145/3711896.3736838
  - Code: https://github.com/RndmVariableQ/AlphaAgent (local `external/AlphaAgent`)

- **AlphaPROBE — Principled Retrieval and On-graph Biased Evolution**
  - Guo et al., 2026
  - Code: https://github.com/gta0804/AlphaPROBE (local `external/AlphaPROBE`)

- **Automate Strategy Finding with LLM in Quant Investment**
  - Kou et al., 2024
  - arXiv:2409.06289
  - Used as inspiration for RSI-family seed / mutation priors in the China
    A-share factor loop (`wiki/factor_rsi_modern_seeds_20260917.md`).

- **QuantaAlpha — Evolutionary Framework for LLM-Driven Alpha Mining**
  - Han et al., 2026
  - arXiv:2602.07085
  - Code: https://github.com/QuantaAlpha/QuantaAlpha (local `external/QuantaAlpha`)

- **QuantFactor REINFORCE**
  - Zhao et al., IEEE TSP 2025
  - arXiv:2409.05144

- **Navigating the Alpha Jungle (LLM-MCTS)**
  - Shi, Duan, Li; AAAI 2026 / arXiv:2505.11122

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

- **Tushare Pro index constituent weights**
  - https://tushare.pro/document/2?doc_id=96
  - Key: historical index constituent records used to construct the stock-disjoint
    CSI500 external-validation universe.

- **Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents**
  - Zhang et al., 2025
  - arXiv:2505.22954, https://arxiv.org/abs/2505.22954
  - Key: open-ended self-improving agents; archive + empirical validation.
  - Applied here as the outer mining-policy archive
    (`wiki/factor_dgm_rsi_factor_mining_20260918.md`).

- **HyperAgents (DGM-Hyperagents)**
  - Meta / Clune et al., 2026
  - arXiv:2603.19461
  - Key: editable meta-level self-modification beyond coding domains.

- **Hyperagents**
  - Zhang et al., 2026
  - arXiv:2603.19461, https://arxiv.org/abs/2603.19461

- **AI Scientist**
  - Lu et al., 2024
  - Key: automated scientific discovery agent.
