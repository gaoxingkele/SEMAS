"""Replaceable calendar provider interface for mingli chart tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class CalendarProvider(Protocol):
    """Provider protocol for building shared chart context."""

    name: str

    def build_context(self, birth: dict[str, Any]) -> dict[str, Any]:
        """Build a normalized chart context from a birth record."""
        raise NotImplementedError


@dataclass
class ExternalCalendarProvider:
    """Adapter for externally supplied professional calendar contexts.

    The `contexts` mapping is keyed by `YYYY-MM-DD HH` and lets tests or future
    integrations inject authoritative context without changing downstream tools.
    """

    contexts: dict[str, dict[str, Any]]
    name: str = "external"

    def build_context(self, birth: dict[str, Any]) -> dict[str, Any]:
        key = f"{birth['year']:04d}-{birth['month']:02d}-{birth['day']:02d} {int(birth['hour']):02d}"
        if key not in self.contexts:
            raise KeyError(f"No external calendar context for {key}")
        context = dict(self.contexts[key])
        context.setdefault("provider", self.name)
        context.setdefault("provider_quality", "external")
        return context


@dataclass
class CalendarProviderRegistry:
    """Small in-process registry for calendar providers."""

    providers: dict[str, CalendarProvider] = field(default_factory=dict)
    default_name: str = "approximate"

    def register(self, provider: CalendarProvider, default: bool = False) -> None:
        self.providers[provider.name] = provider
        if default:
            self.default_name = provider.name

    def get(self, name: str | None = None) -> CalendarProvider:
        provider_name = name or self.default_name
        if provider_name not in self.providers:
            raise KeyError(f"Unknown calendar provider: {provider_name}")
        return self.providers[provider_name]

    def describe(self) -> dict[str, Any]:
        """Return a lightweight registry description for CLIs and diagnostics."""
        return {
            "default": self.default_name,
            "providers": sorted(self.providers),
        }
