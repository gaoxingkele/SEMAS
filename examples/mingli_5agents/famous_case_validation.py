"""Famous-person BaZi validation fixtures and scoring helpers.

The fixtures are not used as proof that BaZi is predictive. They are an audit
tool: compare school-agent claims against public, sourced life-event tags and
keep the source/rating attached to every case.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


FAMOUS_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "bruce_lee",
        "name": "李小龙",
        "birth": {
            "birth_date": "1940-11-27",
            "birth_time": "07:12",
            "gender": "male",
            "birthplace": "美国旧金山",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Lee,_Bruce",
            "rating": "甲甲",
            "note": "该站使用罗登评级；甲甲通常表示出生记录或同等强来源。",
        },
        "event_tags": {
            "career_project": [1959, 1964, 1971, 1972, 1973],
            "migration": [1941, 1959],
            "public_fame": [1966, 1971, 1972, 1973],
            "health_risk": [1973],
        },
        "validation_use": "高置信出生资料；适合检验输出、名声、迁移和健康风险标签。",
    },
    {
        "id": "chiang_kai_shek",
        "name": "蒋介石",
        "birth": {
            "birth_date": "1887-10-31",
            "birth_time": "12:00",
            "gender": "male",
            "birthplace": "浙江奉化",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Chiang_Kai-Shek",
            "rating": "乙",
            "note": "乙级资料可作研究样本，但时辰不应按铁证处理。",
        },
        "event_tags": {
            "career_power": [1925, 1926, 1928, 1943],
            "war_pressure": [1937, 1941, 1949],
            "migration": [1949],
            "family_relation": [1927, 1975],
        },
        "validation_use": "政治权力、战争压力和迁移节点明显；适合检验官杀、格局和大运承接。",
    },
    {
        "id": "marilyn_monroe",
        "name": "玛丽莲梦露",
        "birth": {
            "birth_date": "1926-06-01",
            "birth_time": "09:30",
            "gender": "female",
            "birthplace": "美国洛杉矶",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Monroe,_Marilyn",
            "rating": "甲甲",
            "note": "高评级样本；适合检验名声、情感、健康和公众形象标签。",
        },
        "event_tags": {
            "public_fame": [1953, 1954, 1955, 1959],
            "relationship": [1942, 1954, 1956, 1961],
            "health_risk": [1961, 1962],
            "career_project": [1953, 1959],
        },
        "validation_use": "公众形象和关系事件集中；适合检验食伤、财官、象法和调候。",
    },
    {
        "id": "albert_einstein",
        "name": "爱因斯坦",
        "birth": {
            "birth_date": "1879-03-14",
            "birth_time": "11:30",
            "gender": "male",
            "birthplace": "德国乌尔姆",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Einstein,_Albert",
            "rating": "甲",
            "note": "较高评级样本；仍需保留来源不确定性。",
        },
        "event_tags": {
            "study_exam": [1896, 1900, 1905],
            "career_project": [1905, 1915, 1921],
            "migration": [1895, 1933],
            "public_fame": [1919, 1921],
        },
        "validation_use": "学术、迁移和名声节点清楚；适合检验印星、食伤和迁移象。",
    },
)


SCHOOL_TOPIC_HINTS: dict[str, set[str]] = {
    "子平格局法": {"career_power", "career_project", "public_fame", "study_exam"},
    "旺衰扶抑法": {"health_risk", "study_exam", "career_project"},
    "调候法": {"health_risk", "study_exam"},
    "体用气势法": {"career_project", "study_exam", "migration"},
    "盲派象法": {"migration", "family_relation", "relationship", "public_fame"},
    "神煞纳音辅助法": {"health_risk", "relationship"},
}


def famous_case_records() -> tuple[dict[str, Any], ...]:
    """Return sourced famous-person validation fixtures."""
    return FAMOUS_CASES


def famous_case_receipt() -> dict[str, Any]:
    """Return a stable receipt for the famous-case fixture set."""
    material = {
        "schema_version": "mingli-famous-case-validation-v1",
        "cases": FAMOUS_CASES,
        "school_topic_hints": {key: sorted(value) for key, value in SCHOOL_TOPIC_HINTS.items()},
        "boundary": "Use as sourced calibration fixtures, not proof of predictive validity.",
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "case_count": len(FAMOUS_CASES),
        "sources": sorted({case["source"]["name"] for case in FAMOUS_CASES}),
        "ratings": sorted({case["source"]["rating"] for case in FAMOUS_CASES}),
        "material": material,
    }


def score_school_topics(school_debate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Score whether a school debate touches public event-tag categories."""
    event_topics = set(case.get("event_tags", {}).keys())
    rows = []
    for vote in school_debate.get("votes", []):
        school = str(vote.get("school", ""))
        expected = SCHOOL_TOPIC_HINTS.get(school, set())
        overlap = sorted(event_topics & expected)
        rows.append(
            {
                "school": school,
                "confidence": vote.get("confidence"),
                "event_topic_overlap": overlap,
                "topic_recall": round(len(overlap) / max(1, len(event_topics)), 3),
                "boundary": "Topic overlap is a weak calibration signal; it is not event prediction accuracy.",
            }
        )
    return {
        "case_id": case.get("id"),
        "case_name": case.get("name"),
        "source": case.get("source"),
        "rows": rows,
    }
