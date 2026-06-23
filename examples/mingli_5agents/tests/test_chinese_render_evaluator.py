"""Tests for Chinese rendered-report quality scoring."""

from __future__ import annotations

from examples.mingli_5agents.evaluators.chinese_render_evaluator import chinese_render_score
from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, bootstrap_repo, demo_task


def test_chinese_render_score_accepts_readable_report(tmp_path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(
        coordinator,
        {**demo_task(), "language": "zh", "annual_start_year": 2024, "annual_end_year": 2026},
    )

    assert chinese_render_score(result) == 1.0


def test_chinese_render_score_rejects_mojibake():
    result = {
        "final_report": {
            "rendered_reports": {
                "zh": "# Report\n## 浣跨敤杈圭晫\n## 涓婚缁煎悎\n### 璐㈣繍\n"
            }
        }
    }

    assert chinese_render_score(result) == 0.0


def test_chinese_render_score_rejects_english_template_leakage():
    result = {
        "final_report": {
            "rendered_reports": {
                "zh": "\n".join(
                    [
                        "# Mingli five-agent report",
                        "## 使用边界",
                        "文化研究，避免重大决策。",
                        "## 主题综合",
                        "### 财运",
                        "Financial resources and money management",
                        "### 事业",
                        "### 学业与学习",
                        "### 婚恋与感情",
                        "### 官运与规则压力",
                        "### 朋友与团队",
                        "### 领导、客户与机构关系",
                        "### 子女、家庭与创作输出",
                        "Do not treat symbolic finance language as investment advice.",
                        "## 结构化数据概览",
                    ]
                )
            }
        }
    }

    assert chinese_render_score(result) == 0.0
