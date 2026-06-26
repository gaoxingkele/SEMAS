"""Evaluator metric for Chinese Markdown rendering quality."""

from __future__ import annotations

import re
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

CODE_LEAKAGE_MARKERS = {
    "```",
    "python -m ",
    "def ",
    "import ",
    "from examples.",
    "SEMAS_",
    "<provider-command>",
    "<manifest.json>",
}

GENERIC_MOJIBAKE_MARKERS = {
    "�",
    "锟斤拷",
    "Ã",
    "Â",
}


def chinese_render_score(result: dict[str, Any], expected: dict[str, Any] | None = None) -> float:
    """Score whether the Chinese rendered report is readable and complete."""
    zh = result.get("final_report", {}).get("rendered_reports", {}).get("zh")
    if not isinstance(zh, str) or not zh.strip():
        return 0.0
    if any(marker in zh for marker in MOJIBAKE_MARKERS):
        return 0.0
    if any(marker in zh for marker in GENERIC_MOJIBAKE_MARKERS):
        return 0.0
    if "?" in zh:
        return 0.0
    if any(marker in zh for marker in ENGLISH_TEMPLATE_MARKERS):
        return 0.0
    if any(marker in zh for marker in CODE_LEAKAGE_MARKERS):
        return 0.0
    if _latin_letter_count(zh) > 0:
        return 0.0
    if _tail_section_duplicate_bullet_ratio(zh, section_count=2) > 0.02:
        return 0.0
    if _tail_section_topic_evidence_anchor_ratio(zh, section_count=2) < 1.0:
        return 0.0
    if _tail_section_topic_judgment_structure_ratio(zh, section_count=2) < 1.0:
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


def _latin_letter_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text))


def _tail_section_duplicate_bullet_ratio(text: str, *, section_count: int) -> float:
    bullets = _tail_section_bullets(text, section_count=section_count)
    if not bullets:
        return 0.0
    counts: dict[str, int] = {}
    for line in bullets:
        counts[line] = counts.get(line, 0) + 1
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    return duplicate_count / len(bullets)


def _tail_section_topic_evidence_anchor_ratio(text: str, *, section_count: int) -> float:
    topic_lines = _tail_section_topic_lines(text, section_count=section_count)
    required_markers = ("天干", "地支", "大运", "用神", "原局同柱")
    if not topic_lines:
        return 0.0
    bound = [
        line
        for line in topic_lines
        if all(marker in line for marker in required_markers) and ("本年" in line or "本月" in line)
    ]
    return len(bound) / len(topic_lines)


def _tail_section_topic_judgment_structure_ratio(text: str, *, section_count: int) -> float:
    topic_lines = _tail_section_topic_lines(text, section_count=section_count)
    if not topic_lines:
        return 0.0
    structured = [line for line in topic_lines if "判断：" in line and "依据：" in line]
    return len(structured) / len(topic_lines)


def _tail_section_topic_lines(text: str, *, section_count: int) -> list[str]:
    topic_labels = (
        "财运",
        "官运",
        "事业",
        "学业",
        "婚恋感情",
        "朋友团队",
        "领导客户",
        "子女家庭",
    )
    return [
        line
        for line in _tail_section_bullets(text, section_count=section_count)
        if any(line.startswith(f"- {label}：") for label in topic_labels)
    ]


def _tail_section_bullets(text: str, *, section_count: int) -> list[str]:
    sections: list[tuple[str, list[str]]] = []
    current: str | None = None
    rows: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections.append((current, rows))
            current = line
            rows = []
        elif current is not None:
            rows.append(line)
    if current is not None:
        sections.append((current, rows))
    bullets: list[str] = []
    for _, rows in sections[-section_count:]:
        bullets.extend(line.strip() for line in rows if line.startswith("- "))
    return bullets
