# References

> Centralized citation list for the SEMAS LLM Wiki. Every `[source: ...]` link
> in the wiki should resolve to an entry here.

## SEMAS Framework

- SEMAS — Self-Evolving Multi-Agent System Framework
  - Local source: `README.md`, `semas/`
  - Core idea: frozen-weight LLM + selection-based evolution over prompts,
    tools, topologies, and memory.

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
