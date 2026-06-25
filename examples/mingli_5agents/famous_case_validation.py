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
        "domain": "影视武术",
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
        "domain": "近代政治",
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
        "domain": "影视",
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
        "domain": "科学文化",
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
    {
        "id": "arthur_ashe",
        "name": "阿瑟阿什",
        "domain": "体育",
        "birth": {
            "birth_date": "1943-07-10",
            "birth_time": "18:40",
            "gender": "male",
            "birthplace": "美国弗吉尼亚州里士满",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Ashe,_Arthur",
            "rating": "甲甲",
            "note": "体育样本；高评级出生资料。",
        },
        "event_tags": {
            "sports_peak": [1968, 1970, 1975],
            "career_project": [1963, 1968, 1975],
            "public_fame": [1968, 1975],
            "health_risk": [1979, 1983, 1992],
        },
        "validation_use": "网球冠军、公众影响和健康风险节点清楚；适合检验体育峰值和健康风险。",
    },
    {
        "id": "mark_spitz",
        "name": "马克施皮茨",
        "domain": "体育",
        "birth": {
            "birth_date": "1950-02-10",
            "birth_time": "17:06",
            "gender": "male",
            "birthplace": "美国加利福尼亚州莫德斯托",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Spitz,_Mark",
            "rating": "甲甲",
            "note": "体育样本；高评级出生资料。",
        },
        "event_tags": {
            "sports_peak": [1968, 1972],
            "public_fame": [1972],
            "career_project": [1965, 1968, 1972],
            "transition": [1972],
        },
        "validation_use": "奥运峰值年份突出；适合检验短期爆发、名声和退役转向。",
    },
    {
        "id": "roger_federer",
        "name": "罗杰费德勒",
        "domain": "体育",
        "birth": {
            "birth_date": "1981-08-08",
            "birth_time": "08:40",
            "gender": "male",
            "birthplace": "瑞士巴塞尔",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Federer,_Roger",
            "rating": "甲",
            "note": "体育样本；较高评级，仍需保留来源不确定性。",
        },
        "event_tags": {
            "sports_peak": [2003, 2004, 2006, 2007, 2009, 2012, 2017],
            "public_fame": [2003, 2004, 2009],
            "health_risk": [2016, 2020, 2021],
            "transition": [2022],
        },
        "validation_use": "职业高峰、伤病和退役节点清楚；适合检验长期大运承接。",
    },
    {
        "id": "lucille_ball",
        "name": "露西尔鲍尔",
        "domain": "影视",
        "birth": {
            "birth_date": "1911-08-06",
            "birth_time": "17:00",
            "gender": "female",
            "birthplace": "美国纽约州詹姆斯敦",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Ball,_Lucille",
            "rating": "甲甲",
            "note": "影视样本；高评级出生资料。",
        },
        "event_tags": {
            "public_fame": [1951, 1952, 1953],
            "career_project": [1933, 1951, 1960],
            "relationship": [1940, 1960],
            "business_power": [1962],
        },
        "validation_use": "演员、制片与商业权力节点清楚；适合检验食伤、财星和官杀承接。",
    },
    {
        "id": "sean_penn",
        "name": "西恩潘",
        "domain": "影视",
        "birth": {
            "birth_date": "1960-08-17",
            "birth_time": "15:17",
            "gender": "male",
            "birthplace": "美国加利福尼亚州圣莫尼卡",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Penn,_Sean",
            "rating": "甲甲",
            "note": "影视样本；高评级出生资料。",
        },
        "event_tags": {
            "career_project": [1982, 1995, 2003, 2008],
            "public_fame": [1982, 2003, 2008],
            "relationship": [1985, 1996, 2010],
            "public_controversy": [1987, 2005],
        },
        "validation_use": "作品、奖项、关系和争议节点明显；适合检验食伤、官杀和象法。",
    },
    {
        "id": "aretha_franklin",
        "name": "艾瑞莎富兰克林",
        "domain": "歌手",
        "birth": {
            "birth_date": "1942-03-25",
            "birth_time": "22:30",
            "gender": "female",
            "birthplace": "美国田纳西州孟菲斯",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Franklin,_Aretha",
            "rating": "甲甲",
            "note": "歌手样本；高评级出生资料。",
        },
        "event_tags": {
            "public_fame": [1967, 1968, 1987],
            "career_project": [1960, 1967, 1980],
            "relationship": [1961, 1969, 1978],
            "health_risk": [2010, 2018],
        },
        "validation_use": "声音输出、公众名声、关系和健康节点清楚；适合检验食伤、印星和调候。",
    },
    {
        "id": "michael_jackson",
        "name": "迈克尔杰克逊",
        "domain": "歌手",
        "birth": {
            "birth_date": "1958-08-29",
            "birth_time": "19:33",
            "gender": "male",
            "birthplace": "美国印第安纳州加里",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Jackson,_Michael",
            "rating": "甲",
            "note": "歌手样本；较高评级，仍需保留来源不确定性。",
        },
        "event_tags": {
            "public_fame": [1969, 1979, 1982, 1983],
            "career_project": [1979, 1982, 1987],
            "public_controversy": [1993, 2005],
            "health_risk": [2009],
        },
        "validation_use": "成名、作品、争议和健康风险节点清楚；适合检验食伤、名声和危机年份。",
    },
    {
        "id": "madonna",
        "name": "麦当娜",
        "domain": "歌手",
        "birth": {
            "birth_date": "1958-08-16",
            "birth_time": "07:05",
            "gender": "female",
            "birthplace": "美国密歇根州贝城",
        },
        "source": {
            "name": "Astro-Databank",
            "url": "https://www.astro.com/astro-databank/Madonna",
            "rating": "甲",
            "note": "歌手样本；较高评级，仍需保留来源不确定性。",
        },
        "event_tags": {
            "public_fame": [1983, 1984, 1989, 1990],
            "career_project": [1983, 1984, 1998],
            "relationship": [1985, 2000, 2008],
            "public_controversy": [1989, 1992],
        },
        "validation_use": "公众名声、作品、关系和争议节点明显；适合检验食伤、财官和象法。",
    },
)


SCHOOL_TOPIC_HINTS: dict[str, set[str]] = {
    "子平格局法": {"career_power", "career_project", "public_fame", "study_exam", "sports_peak"},
    "旺衰扶抑法": {"health_risk", "study_exam", "career_project", "sports_peak"},
    "调候法": {"health_risk", "study_exam", "sports_peak"},
    "体用气势法": {"career_project", "study_exam", "migration", "transition", "sports_peak"},
    "盲派象法": {
        "migration",
        "family_relation",
        "relationship",
        "public_fame",
        "public_controversy",
    },
    "神煞纳音辅助法": {"health_risk", "relationship", "public_controversy"},
}


def famous_case_records() -> tuple[dict[str, Any], ...]:
    """Return sourced famous-person validation fixtures."""
    return FAMOUS_CASES


def famous_case_receipt() -> dict[str, Any]:
    """Return a stable receipt for the famous-case fixture set."""
    material = {
        "schema_version": "mingli-famous-case-validation-v2",
        "cases": FAMOUS_CASES,
        "school_topic_hints": {key: sorted(value) for key, value in SCHOOL_TOPIC_HINTS.items()},
        "boundary": "Use as sourced calibration fixtures, not proof of predictive validity.",
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "case_count": len(FAMOUS_CASES),
        "domains": sorted({case["domain"] for case in FAMOUS_CASES}),
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
        "case_domain": case.get("domain"),
        "source": case.get("source"),
        "rows": rows,
    }
