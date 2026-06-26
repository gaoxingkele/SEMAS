"""Tests for Chinese rendered-report quality scoring."""

from __future__ import annotations

from examples.mingli_5agents.evaluators.chinese_render_evaluator import (
    _tail_section_duplicate_bullet_ratio,
    _tail_section_topic_evidence_anchor_ratio,
    _tail_section_topic_judgment_structure_ratio,
    chinese_render_score,
)
from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, bootstrap_repo, demo_task


def test_chinese_render_score_accepts_readable_report(tmp_path):
    repo = bootstrap_repo(tmp_path)
    coordinator = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(
        coordinator,
        {**demo_task(), "language": "zh", "annual_start_year": 2024, "annual_end_year": 2026},
    )

    assert chinese_render_score(result) == 1.0
    zh = result["final_report"]["rendered_reports"]["zh"]
    assert "?" not in zh
    assert "python -m" not in zh
    assert "SEMAS_" not in zh
    assert not any(char.isascii() and char.isalpha() for char in zh)
    assert _tail_section_duplicate_bullet_ratio(zh, section_count=2) == 0.0
    assert _tail_section_topic_evidence_anchor_ratio(zh, section_count=2) == 1.0
    assert _tail_section_topic_judgment_structure_ratio(zh, section_count=2) == 1.0


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


def test_chinese_render_score_rejects_question_mark_and_code_leakage():
    result = {
        "final_report": {
            "rendered_reports": {
                "zh": "\n".join(
                    [
                        "# 命理报告",
                        "## 出生资料核对",
                        "这里为什么出现乱码?",
                        "## 使用边界",
                        "```python",
                        "import os",
                        "```",
                    ]
                )
            }
        }
    }

    assert chinese_render_score(result) == 0.0


def test_chinese_render_duplicate_ratio_flags_repeated_annual_monthly_lines():
    text = "\n".join(
        [
            "## section one",
            "- stable",
            "## annual",
            "- same line",
            "- same line",
            "- unique annual",
            "## monthly",
            "- same line",
            "- same line",
            "- unique monthly",
        ]
    )

    assert _tail_section_duplicate_bullet_ratio(text, section_count=2) > 0.02


def test_chinese_render_topic_evidence_anchor_ratio_rejects_unbound_topic_lines():
    text = "\n".join(
        [
            "## annual",
            "- 财运：财务宜稳，重计划胜过投机。",
            "- 官运：本年2026丙午，天干比劫、地支比劫，大运癸未，用神忌偏重，原局同柱无。",
            "## monthly",
            "- 事业：本月2026-06壬未，天干官杀、地支食伤，大运癸未，用神中性，原局同柱无。",
            "- 学业：学习宜服务当前工作需要。",
        ]
    )

    assert _tail_section_topic_evidence_anchor_ratio(text, section_count=2) == 0.5


def test_chinese_render_topic_judgment_structure_ratio_rejects_unstructured_topic_lines():
    text = "\n".join(
        [
            "## annual",
            "- 财运：判断：财务宜稳，重计划胜过投机；依据：本年2026丙午，天干比劫、地支比劫，大运癸未，用神忌偏重，原局同柱无。",
            "- 官运：本年2026丙午，天干比劫、地支比劫，大运癸未，用神忌偏重，原局同柱无。",
            "## monthly",
            "- 事业：判断：项目推进要先收口；依据：本月2026-06壬未，天干官杀、地支食伤，大运癸未，用神中性，原局同柱无。",
            "- 学业：学习宜服务当前工作需要。",
        ]
    )

    assert _tail_section_topic_judgment_structure_ratio(text, section_count=2) == 0.5
