"""Optional LLM synthesis layer for mingli final reports."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from semas.utils.llm_client import LLMClient, StubLLMClient, default_llm_client


def synthesize_with_llm(
    final_report: dict[str, Any],
    *,
    language: str = "zh",
    llm: LLMClient | None = None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Return optional LLM-generated synthesis without replacing structured data."""
    prompt_payload = _prompt_payload(final_report)
    prompt = json.dumps(prompt_payload, ensure_ascii=False, indent=2)
    fingerprint = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    if not enabled:
        return {
            "enabled": False,
            "generated": False,
            "language": language,
            "prompt_fingerprint": fingerprint,
            "text": "",
        }

    client = llm or default_llm_client()
    if isinstance(client, StubLLMClient):
        return {
            "enabled": True,
            "generated": False,
            "language": language,
            "provider": "stub",
            "prompt_fingerprint": fingerprint,
            "text": "LLM synthesis skipped because no external LLM backend is configured.",
        }

    system_prompt = _system_prompt(language)
    user_prompt = (
        "Use the following structured mingli report to write a concise synthesis. "
        "Do not add deterministic predictions or high-stakes advice.\n\n"
        f"{prompt}"
    )
    text = client.complete(system_prompt, user_prompt, temperature=0.4, max_tokens=1200).strip()
    return {
        "enabled": True,
        "generated": bool(text),
        "language": language,
        "provider": client.__class__.__name__,
        "prompt_fingerprint": fingerprint,
        "text": text,
    }


def _prompt_payload(final_report: dict[str, Any]) -> dict[str, Any]:
    topics = final_report.get("topic_synthesis", {})
    return {
        "title": final_report.get("title"),
        "boundaries": final_report.get("boundaries"),
        "summary": final_report.get("summary"),
        "topic_headlines": {
            key: value.get("headline")
            for key, value in topics.items()
            if isinstance(value, dict)
        },
        "annual_range": final_report.get("annual_luck", {}).get("range"),
        "monthly_range": final_report.get("monthly_luck", {}).get("range"),
        "source_review": final_report.get("source_review", {}).get("status"),
        "conflicts": final_report.get("conflicts", []),
    }


def _system_prompt(language: str) -> str:
    if language == "zh":
        return (
            "你是命理多智能体系统的最终文字综合器。只基于给定结构化数据写中文摘要；"
            "必须保留文化研究/娱乐参考边界，不得给出医疗、投资、婚姻、法律等重大决策建议；"
            "不得把象征性趋势写成确定预言。"
        )
    return (
        "You are the final prose synthesizer for a multi-agent mingli framework. "
        "Use only the supplied structured report. Preserve cultural/entertainment boundaries, "
        "avoid high-stakes advice, and do not turn symbolic trends into deterministic predictions."
    )
