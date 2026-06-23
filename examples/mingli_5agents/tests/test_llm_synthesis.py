"""Tests for optional LLM synthesis."""

from __future__ import annotations

from semas.utils.llm_client import LLMClient, llm_backend_status

from examples.mingli_5agents.llm_synthesis import synthesize_with_llm


class FakeLLM(LLMClient):
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        assert "重大决策" in system_prompt
        assert "topic_headlines" in user_prompt
        return "这是基于结构化数据的中文综合。"


def _final_report() -> dict:
    return {
        "title": "Mingli five-agent report for Test",
        "boundaries": ["Purpose: cultural research and entertainment only."],
        "summary": ["BaZi summary"],
        "topic_synthesis": {"finance": {"headline": "finance headline"}},
        "annual_luck": {"range": {"start_year": 2024, "end_year": 2026}},
        "monthly_luck": {"range": {"years": [2026]}},
        "source_review": {"status": "pass"},
        "conflicts": [],
    }


def test_llm_synthesis_disabled_by_default():
    result = synthesize_with_llm(_final_report(), enabled=False)
    assert result["enabled"] is False
    assert result["generated"] is False
    assert result["text"] == ""


def test_llm_synthesis_stub_skips_without_backend():
    result = synthesize_with_llm(_final_report(), enabled=True)
    assert result["enabled"] is True
    assert result["generated"] is False
    assert result["provider"] == "stub"


def test_llm_synthesis_uses_injected_backend():
    result = synthesize_with_llm(_final_report(), enabled=True, llm=FakeLLM(), language="zh")
    assert result["generated"] is True
    assert result["provider"] == "FakeLLM"
    assert result["text"] == "这是基于结构化数据的中文综合。"
def test_llm_backend_status_reports_stub_without_secrets(monkeypatch):
    for key in (
        "SEMAS_LLM_API_KEY",
        "OPENAI_API_KEY",
        "KIMI_API_KEY",
        "DEEPSEEK_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    result = llm_backend_status()

    assert result["configured"] is False
    assert result["provider"] == "stub"
    assert result["client"] == "StubLLMClient"
    assert result["api_key_source"] is None
    assert result["safe_to_report"] is True


def test_llm_backend_status_reports_kimi_openai_compatible_config_without_key(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "secret-value")
    monkeypatch.setenv("KIMI_MODEL", "kimi-2.7")
    monkeypatch.setenv("KIMI_BASE_URL", "https://kimi.example/v1")
    monkeypatch.delenv("SEMAS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = llm_backend_status()

    assert result["configured"] is True
    assert result["provider"] == "kimi_openai_compatible"
    assert result["model"] == "kimi-2.7"
    assert result["base_url_configured"] is True
    assert result["api_key_source"] == "KIMI_API_KEY"
    assert "secret-value" not in str(result)
