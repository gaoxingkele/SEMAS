"""Offline birthplace normalization for deterministic chart requests."""

from __future__ import annotations

from typing import Any


CITY_GEO_INDEX: dict[str, dict[str, Any]] = {
    "beijing": {
        "birthplace_normalized": "Beijing, China",
        "birthplace_region": "China/Beijing",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone_offset": "+08:00",
    },
    "chengdu": {
        "birthplace_normalized": "Chengdu, Sichuan, China",
        "birthplace_region": "China/Sichuan/Chengdu",
        "latitude": 30.5728,
        "longitude": 104.0668,
        "timezone_offset": "+08:00",
    },
    "hangzhou": {
        "birthplace_normalized": "Hangzhou, Zhejiang, China",
        "birthplace_region": "China/Zhejiang/Hangzhou",
        "latitude": 30.2741,
        "longitude": 120.1551,
        "timezone_offset": "+08:00",
    },
    "nanjing": {
        "birthplace_normalized": "Nanjing, Jiangsu, China",
        "birthplace_region": "China/Jiangsu/Nanjing",
        "latitude": 32.0603,
        "longitude": 118.7969,
        "timezone_offset": "+08:00",
    },
    "sanming": {
        "birthplace_normalized": "Sanming, Fujian, China",
        "birthplace_region": "China/Fujian/Sanming",
        "latitude": 26.2634,
        "longitude": 117.6389,
        "timezone_offset": "+08:00",
    },
    "shanghai": {
        "birthplace_normalized": "Shanghai, China",
        "birthplace_region": "China/Shanghai",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "timezone_offset": "+08:00",
    },
    "suzhou": {
        "birthplace_normalized": "Suzhou, Jiangsu, China",
        "birthplace_region": "China/Jiangsu/Suzhou",
        "latitude": 31.2989,
        "longitude": 120.5853,
        "timezone_offset": "+08:00",
    },
}

CITY_ALIASES = {
    "北京": "beijing",
    "北京市": "beijing",
    "beijing": "beijing",
    "chengdu": "chengdu",
    "成都": "chengdu",
    "成都市": "chengdu",
    "hangzhou": "hangzhou",
    "杭州": "hangzhou",
    "杭州市": "hangzhou",
    "nanjing": "nanjing",
    "南京": "nanjing",
    "南京市": "nanjing",
    "sanming": "sanming",
    "三明": "sanming",
    "三明市": "sanming",
    "福建三明": "sanming",
    "福建省三明市": "sanming",
    "shanghai": "shanghai",
    "上海": "shanghai",
    "上海市": "shanghai",
    "suzhou": "suzhou",
    "苏州": "suzhou",
    "苏州市": "suzhou",
}


def normalize_birthplace_geo(data: dict[str, Any]) -> dict[str, Any]:
    """Attach deterministic geodata for known birthplaces without overriding explicit inputs."""
    birthplace = str(data.get("birthplace") or data.get("birth_place") or "").strip()
    if not birthplace:
        return {}
    key = CITY_ALIASES.get(birthplace) or CITY_ALIASES.get(birthplace.lower())
    if not key:
        return {
            "birthplace_normalized": birthplace,
            "birthplace_region": "unknown",
            "geocoding_provider": "user_input_only",
            "geocoding_quality": "unresolved",
        }
    resolved = dict(CITY_GEO_INDEX[key])
    resolved["geocoding_provider"] = "offline_city_index_v1"
    resolved["geocoding_quality"] = "city_centroid"
    for field in ("latitude", "longitude", "timezone_offset", "utc_offset"):
        if data.get(field) is not None:
            resolved[field] = data[field]
    return resolved
