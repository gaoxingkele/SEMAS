"""Lightweight LLM client abstraction.

Users can subclass LLMClient to plug in OpenAI, Anthropic, local models, etc.
The default implementation is a stub that returns deterministic placeholder text
so the framework can run without API keys in tests.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Abstract LLM client."""

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Return a text completion for the given prompts."""
        raise NotImplementedError


class StubLLMClient(LLMClient):
    """Deterministic stub for testing and offline demos.

    Returns simple heuristics based on keywords in the prompt so that examples
    can exercise the full loop without spending tokens.
    """

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        lower = user_prompt.lower()
        if "prompt" in lower and "improve" in lower:
            return "[MUTATED] " + system_prompt + "\nAlways double-check edge cases."
        if ("tool" in lower and "python" in lower) or "write the python function" in lower:
            return (
                "def calculate_date_diff(start: str, end: str) -> int:\n"
                "    from datetime import datetime\n"
                "    fmt = '%Y-%m-%d'\n"
                "    return (datetime.strptime(end, fmt) - datetime.strptime(start, fmt)).days\n"
            )
        if "summarize" in lower or "memory" in lower:
            return "Consolidated memory: key facts extracted."
        return "No mutation proposed."


class OpenAILLMClient(LLMClient):
    """Example OpenAI-compatible client.

    Requires an OpenAI-compatible API key and optionally a base URL.
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None, base_url: str | None = None):
        import openai  # optional dependency

        self.model = model
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


def default_llm_client() -> LLMClient:
    """Return an LLM client based on environment configuration.

    If a SEMAS/OpenAI-compatible API key is set, returns OpenAILLMClient.
    Otherwise returns the stub. Kimi, DeepSeek, and similar OpenAI-compatible
    services can be selected through SEMAS_LLM_* environment variables.
    """
    config = _resolve_llm_backend_config()
    if config["api_key"]:
        return OpenAILLMClient(
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"],
        )
    return StubLLMClient()


def llm_backend_status() -> dict[str, Any]:
    """Return non-secret LLM backend configuration status."""
    config = _resolve_llm_backend_config()
    configured = bool(config["api_key"])
    return {
        "configured": configured,
        "provider": config["provider"] if configured else "stub",
        "client": "OpenAILLMClient" if configured else "StubLLMClient",
        "model": config["model"] if configured else None,
        "base_url_configured": bool(config["base_url"]) if configured else False,
        "api_key_source": config["api_key_source"] if configured else None,
        "recognized_env": {
            "generic": ["SEMAS_LLM_API_KEY", "SEMAS_LLM_MODEL", "SEMAS_LLM_BASE_URL"],
            "openai": ["OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"],
            "kimi": ["KIMI_API_KEY", "KIMI_MODEL", "KIMI_BASE_URL"],
            "deepseek": ["DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "DEEPSEEK_BASE_URL"],
        },
        "safe_to_report": True,
        "note": "API keys are intentionally not returned.",
    }


def _resolve_llm_backend_config() -> dict[str, Any]:
    if os.getenv("SEMAS_LLM_API_KEY"):
        return {
            "provider": "openai_compatible",
            "api_key": os.getenv("SEMAS_LLM_API_KEY"),
            "api_key_source": "SEMAS_LLM_API_KEY",
            "model": os.getenv("SEMAS_LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
            "base_url": os.getenv("SEMAS_LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
        }
    if os.getenv("OPENAI_API_KEY"):
        return {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "api_key_source": "OPENAI_API_KEY",
            "model": os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
            "base_url": os.getenv("OPENAI_BASE_URL"),
        }
    if os.getenv("KIMI_API_KEY"):
        return {
            "provider": "kimi_openai_compatible",
            "api_key": os.getenv("KIMI_API_KEY"),
            "api_key_source": "KIMI_API_KEY",
            "model": os.getenv("SEMAS_LLM_MODEL") or os.getenv("KIMI_MODEL") or "kimi-2.7",
            "base_url": os.getenv("SEMAS_LLM_BASE_URL") or os.getenv("KIMI_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
        }
    if os.getenv("DEEPSEEK_API_KEY"):
        return {
            "provider": "deepseek_openai_compatible",
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "api_key_source": "DEEPSEEK_API_KEY",
            "model": os.getenv("SEMAS_LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat",
            "base_url": os.getenv("SEMAS_LLM_BASE_URL")
            or os.getenv("DEEPSEEK_BASE_URL")
            or os.getenv("OPENAI_BASE_URL"),
        }
    return {
        "provider": "stub",
        "api_key": None,
        "api_key_source": None,
        "model": None,
        "base_url": None,
    }
