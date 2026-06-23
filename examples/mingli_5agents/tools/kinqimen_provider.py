"""Optional kinqimen-backed provider for Qi Men Dun Jia charts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class KinqimenProvider:
    """Qi Men provider backed by the optional `kinqimen` package.

    The upstream package returns a Chinese dictionary whose exact keys can vary
    with encoding and version. This adapter preserves the raw payload and maps
    stable high-level fields only when they can be identified safely.
    """

    qimen_class: Any
    domain: str = "qimen"
    name: str = "kinqimen"
    option: int = 2

    def build_chart(self, birth: dict[str, Any], fallback_chart: dict[str, Any]) -> dict[str, Any]:
        raw = self.qimen_class(
            int(birth["year"]),
            int(birth["month"]),
            int(birth["day"]),
            int(birth["hour"]),
            int(birth.get("minute", 0)),
        ).pan(int(birth.get("qimen_option", self.option)))
        if not isinstance(raw, dict):
            raise ValueError("kinqimen provider did not return a dictionary plate")

        door_map = _find_mapping(raw, ["door", "門", "门", "闁"])
        star_map = _find_mapping(raw, ["star", "星", "鏄"])
        spirit_map = _find_mapping(raw, ["god", "spirit", "神", "绁"])
        duty = _find_mapping(raw, ["zhifu", "值符", "值使", "鍊"])
        chart = {
            **fallback_chart,
            "provider": self.name,
            "provider_quality": "kinqimen",
            "raw_provider_output": raw,
            "raw_provider_keys": sorted(str(key) for key in raw),
            "pattern": str(raw.get("pattern") or raw.get("局") or raw.get("鎺掑眬") or "kinqimen professional plate"),
        }
        if door_map:
            chart["door_cycle"] = _ordered_unique([str(value) for value in door_map.values()]) or chart["door_cycle"]
            chart["duty_door"] = _first_value(door_map, fallback_chart["duty_door"])
        if star_map:
            chart["star_cycle"] = _ordered_unique([str(value) for value in star_map.values()]) or chart["star_cycle"]
            chart["duty_star"] = _first_value(star_map, fallback_chart["duty_star"])
        if spirit_map:
            chart["spirit_cycle"] = _ordered_unique([str(value) for value in spirit_map.values()]) or chart["spirit_cycle"]
            chart["spirit"] = _first_value(spirit_map, fallback_chart["spirit"])
        if duty:
            chart["provider_duty"] = duty

        chart.setdefault("context", {}).setdefault("provider", fallback_chart.get("context", {}).get("provider"))
        chart["context"]["domain_provider"] = self.name
        chart["context"]["domain_provider_quality"] = "kinqimen"
        chart["context"]["domain_provider_source"] = "kinqimen"
        return chart


def try_build_kinqimen_provider() -> KinqimenProvider | None:
    """Return a kinqimen provider when the optional package is importable."""
    try:
        from kinqimen import kinqimen as kinqimen_module  # type: ignore
    except Exception:
        return None
    qimen_class = getattr(kinqimen_module, "Qimen", None)
    if qimen_class is None:
        return None
    return KinqimenProvider(qimen_class=qimen_class)


def _find_mapping(raw: dict[str, Any], fragments: list[str]) -> dict[Any, Any]:
    for key, value in raw.items():
        key_text = str(key).lower()
        if any(fragment.lower() in key_text for fragment in fragments) and isinstance(value, dict):
            return value
    return {}


def _first_value(mapping: dict[Any, Any], fallback: str) -> str:
    for value in mapping.values():
        if value is not None:
            return str(value)
    return fallback


def _ordered_unique(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
