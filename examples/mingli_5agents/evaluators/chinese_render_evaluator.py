"""Evaluator metric for Chinese Markdown rendering quality."""

from __future__ import annotations

from typing import Any


REQUIRED_SECTIONS = {
    "## 出生资料核对",
    "## 使用边界",
    "## 主题综合",
    "## 八字结构与大运",
    "## 紫微命盘摘要",
    "## 奇门九宫摘要",
    "## 择日参考",
    "## 年度阶段摘要",
    "## 年度流年表",
    "## 月度流月表",
    "## 结构化数据概览",
    "## 计算来源与生产就绪度",
}

REQUIRED_TOPIC_HEADINGS = {
    "### 财运",
    "### 事业",
    "### 学业与学习",
    "### 婚恋与感情",
}

MOJIBAKE_MARKERS = {
    "娑撳",
    "娴ｈ",
    "鐠愩",
    "缂佺",
    "閸涘",
    "閺傚",
    "楠炴",
    "閺堝",
    "閹舵",
    "鏉堝",
    "浣跨敤",
    "涓婚",
    "璐㈣",
}

ENGLISH_TEMPLATE_MARKERS = {
    "Financial resources",
    "Authority, title",
    "Career direction",
    "Study, credentials",
    "Marriage, romance",
    "Friends, peers",
    "Leadership, managers",
    "Children, juniors",
    "symbolic tendency only",
    "Production reports",
    "verified provider",
    "Swap with",
    "Do not treat symbolic",
    "Use as a reflective prompt",
    "Verify contracts",
    "Taiyang",
    "Tianji",
    "Rest door",
    "Open door",
    "Ascendant",
    "Sun Aries",
    "Sun Taurus",
    "BaZi structure",
    "element-skewed",
}


def chinese_render_score(result: dict[str, Any], expected: dict[str, Any] | None = None) -> float:
    """Score whether the Chinese rendered report is readable and complete."""
    zh = result.get("final_report", {}).get("rendered_reports", {}).get("zh")
    if not isinstance(zh, str) or not zh.strip():
        return 0.0
    if any(marker in zh for marker in MOJIBAKE_MARKERS):
        return 0.0
    if any(marker in zh for marker in ENGLISH_TEMPLATE_MARKERS):
        return 0.0

    score = 0.0
    score += 0.35 if all(section in zh for section in REQUIRED_SECTIONS) else 0.0
    score += 0.25 if all(heading in zh for heading in REQUIRED_TOPIC_HEADINGS) else 0.0
    score += 0.2 if _chinese_char_count(zh) >= 80 else 0.0
    score += 0.1 if zh.count("### ") >= 8 else 0.0
    score += 0.1 if "文化研究" in zh and ("重大决策" in zh or "高风险决策" in zh) else 0.0
    return round(min(1.0, score), 6)


def _chinese_char_count(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
