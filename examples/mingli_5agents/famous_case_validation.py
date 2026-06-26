"""Famous-person BaZi validation fixtures and scoring helpers.

The fixtures are not used as proof that BaZi is predictive. They are an audit
tool: compare school-agent claims against public, sourced life-event tags and
keep the source/rating attached to every case.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart
from examples.mingli_5agents.tools.annual_luck import build_annual_luck
from examples.mingli_5agents.tools.calendar_core import BRANCHES, STEMS


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
            "birth_time": "12:55",
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

EVENT_TOPIC_ANNUAL_SIGNALS: dict[str, dict[str, set[str]]] = {
    "business_power": {"categories": {"wealth", "authority"}, "intensities": {"constructive", "active"}},
    "career_power": {"categories": {"authority", "wealth"}, "intensities": {"constructive", "active"}},
    "career_project": {"categories": {"expression", "authority", "wealth"}, "intensities": {"constructive", "active"}},
    "family_relation": {"categories": {"wealth", "friends"}, "intensities": {"active", "high-volatility"}},
    "health_risk": {"categories": set(), "intensities": {"high-volatility"}},
    "migration": {"categories": {"learning", "friends"}, "intensities": {"active", "constructive"}},
    "public_controversy": {"categories": {"expression", "authority"}, "intensities": {"high-volatility", "active"}},
    "public_fame": {"categories": {"expression"}, "intensities": {"constructive", "active", "high-volatility"}},
    "relationship": {"categories": {"friends", "wealth"}, "intensities": {"active", "high-volatility"}},
    "sports_peak": {"categories": {"expression", "authority"}, "intensities": {"constructive", "active"}},
    "study_exam": {"categories": {"learning", "authority"}, "intensities": {"constructive", "active"}},
    "transition": {"categories": {"learning", "authority", "friends"}, "intensities": {"active", "high-volatility"}},
    "war_pressure": {"categories": {"authority"}, "intensities": {"high-volatility", "active"}},
}

EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR: dict[str, dict[str, dict[int, str]]] = {
    "bruce_lee": {
        "career_project": {
            1959: "screen_debut_or_entry",
            1964: "martial_arts_school_launch",
            1971: "breakthrough_film_release",
            1972: "major_film_release",
            1973: "posthumous_landmark_release",
        },
        "public_fame": {
            1966: "television_public_breakthrough",
            1971: "film_public_breakthrough",
            1972: "international_film_fame",
            1973: "posthumous_global_fame",
        },
        "health_risk": {1973: "sudden_death_health_crisis"},
    },
    "chiang_kai_shek": {
        "career_power": {
            1925: "command_succession",
            1926: "military_campaign_command",
            1928: "national_leadership_consolidation",
            1943: "international_power_recognition",
        },
        "war_pressure": {
            1937: "war_outbreak",
            1941: "wartime_alliance_pressure",
            1949: "civil_war_loss",
        },
        "migration": {1949: "regime_relocation"},
        "family_relation": {1927: "marriage_alliance", 1975: "death_family_transition"},
    },
    "marilyn_monroe": {
        "public_fame": {
            1953: "film_star_public_breakthrough",
            1954: "public_image_fame_consolidation",
            1955: "major_film_public_recognition",
            1959: "major_award_film_recognition",
        },
        "relationship": {
            1942: "early_marriage",
            1954: "celebrity_marriage",
            1956: "celebrity_marriage",
            1961: "marriage_breakdown_or_divorce",
        },
        "health_risk": {
            1961: "mental_health_or_hospitalization_crisis",
            1962: "acute_drug_related_death",
        },
        "career_project": {
            1953: "film_star_breakthrough_project",
            1959: "major_award_film_project",
        },
    },
    "albert_einstein": {
        "study_exam": {1896: "admission_exam", 1900: "graduation", 1905: "doctoral_publication"},
        "career_project": {1905: "landmark_publication", 1915: "major_theory_completion", 1921: "prize_recognition"},
        "migration": {1895: "education_relocation", 1933: "exile_relocation"},
        "public_fame": {1919: "public_recognition", 1921: "prize_recognition"},
    },
    "arthur_ashe": {
        "career_project": {
            1963: "sports_team_selection",
            1968: "grand_slam_breakthrough",
            1975: "grand_slam_title",
        },
        "public_fame": {1968: "historic_sports_title_recognition", 1975: "grand_slam_public_recognition"},
        "sports_peak": {
            1968: "grand_slam_breakthrough_title",
            1970: "major_international_team_title",
            1975: "grand_slam_title",
        },
        "health_risk": {
            1979: "cardiac_surgery_or_transfusion_risk",
            1983: "chronic_infectious_disease_diagnosis",
            1992: "terminal_illness_public_disclosure",
        },
    },
    "mark_spitz": {
        "career_project": {
            1965: "national_competition_breakthrough",
            1968: "olympic_medal_breakthrough",
            1972: "olympic_record_peak",
        },
        "public_fame": {1972: "olympic_record_public_fame"},
        "sports_peak": {
            1968: "olympic_medal_breakthrough",
            1972: "olympic_record_gold_peak",
        },
    },
    "roger_federer": {
        "public_fame": {
            2003: "grand_slam_breakthrough_fame",
            2004: "world_number_one_recognition",
            2009: "record_title_public_recognition",
        },
        "sports_peak": {
            2003: "grand_slam_breakthrough_title",
            2004: "world_number_one_peak",
            2006: "dominant_multi_slam_season",
            2007: "dominant_multi_slam_season",
            2009: "record_grand_slam_title",
            2012: "late_career_grand_slam_title",
            2017: "comeback_grand_slam_title",
        },
        "health_risk": {
            2016: "sports_injury_surgery",
            2020: "sports_injury_surgery",
            2021: "sports_injury_recurrence",
        },
    },
    "lucille_ball": {
        "career_project": {
            1933: "screen_contract_or_entry",
            1951: "landmark_tv_series_launch",
            1960: "production_business_launch",
        },
        "public_fame": {
            1951: "television_series_public_breakthrough",
            1952: "television_public_fame_consolidation",
            1953: "major_television_award_recognition",
        },
        "relationship": {1940: "marriage", 1960: "divorce"},
    },
    "sean_penn": {
        "career_project": {
            1982: "film_breakthrough_role",
            1995: "major_award_nominated_role",
            2003: "major_award_winning_role",
            2008: "major_award_winning_role",
        },
        "public_fame": {
            1982: "film_breakthrough_public_attention",
            2003: "major_award_public_recognition",
            2008: "major_award_public_recognition",
        },
        "relationship": {
            1985: "celebrity_marriage",
            1996: "celebrity_marriage",
            2010: "divorce_or_relationship_end",
        },
        "public_controversy": {
            1987: "media_legal_controversy",
            2005: "political_public_controversy",
        },
    },
    "aretha_franklin": {
        "career_project": {
            1960: "recording_contract_or_debut",
            1967: "breakthrough_single_release",
            1980: "label_or_career_relaunch",
        },
        "public_fame": {
            1967: "breakthrough_single_public_fame",
            1968: "major_award_music_recognition",
            1987: "hall_of_fame_recognition",
        },
        "relationship": {
            1961: "marriage",
            1969: "divorce_or_relationship_end",
            1978: "divorce_or_relationship_end",
        },
        "health_risk": {
            2010: "serious_cancer_diagnosis_or_treatment",
            2018: "terminal_cancer_death",
        },
    },
    "michael_jackson": {
        "career_project": {
            1979: "solo_album_breakthrough",
            1982: "landmark_album_release",
            1987: "major_album_release",
        },
        "public_fame": {
            1969: "group_chart_breakthrough_fame",
            1979: "solo_public_breakthrough",
            1982: "landmark_album_global_fame",
            1983: "broadcast_performance_cultural_fame",
        },
        "public_controversy": {
            1993: "criminal_allegation_public_controversy",
            2005: "trial_public_controversy",
        },
        "health_risk": {2009: "acute_drug_related_death"},
    },
    "madonna": {
        "career_project": {
            1983: "debut_album_release",
            1984: "breakthrough_album_release",
            1998: "major_album_reinvention",
        },
        "public_fame": {
            1983: "debut_public_breakthrough",
            1984: "album_global_breakthrough_fame",
            1989: "controversial_video_public_fame",
            1990: "tour_and_media_peak_fame",
        },
        "relationship": {
            1985: "celebrity_marriage",
            2000: "celebrity_marriage",
            2008: "divorce_or_relationship_end",
        },
        "public_controversy": {
            1989: "religious_media_controversy",
            1992: "sexual_expression_public_controversy",
        },
    },
}

EVENT_SUBTYPE_BY_TOPIC: dict[str, str] = {
    "business_power": "business_authority_event",
    "career_power": "career_authority_event",
    "career_project": "project_or_work_event",
    "family_relation": "family_relation_event",
    "health_risk": "health_risk_event",
    "migration": "residence_or_status_movement",
    "public_controversy": "controversy_event",
    "public_fame": "external_recognition_event",
    "relationship": "relationship_event",
    "sports_peak": "competition_peak_event",
    "study_exam": "credential_or_study_event",
    "transition": "career_or_life_transition",
    "war_pressure": "war_or_institutional_pressure",
}

BRANCH_CLASHES: dict[str, str] = {
    "Zi": "Wu",
    "Chou": "Wei",
    "Yin": "Shen",
    "Mao": "You",
    "Chen": "Xu",
    "Si": "Hai",
    "Wu": "Zi",
    "Wei": "Chou",
    "Shen": "Yin",
    "You": "Mao",
    "Xu": "Chen",
    "Hai": "Si",
}


def famous_case_records() -> tuple[dict[str, Any], ...]:
    """Return sourced famous-person validation fixtures."""
    return FAMOUS_CASES


def famous_case_receipt() -> dict[str, Any]:
    """Return a stable receipt for the famous-case fixture set."""
    domain_coverage = _fixture_domain_coverage(FAMOUS_CASES)
    birth_source_quality = _fixture_birth_source_quality(FAMOUS_CASES)
    material = {
        "schema_version": "mingli-famous-case-validation-v2",
        "cases": FAMOUS_CASES,
        "domain_coverage": domain_coverage,
        "birth_source_quality": birth_source_quality,
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
        "domain_coverage": domain_coverage,
        "birth_source_quality": birth_source_quality,
        "material": material,
    }


def _fixture_domain_coverage(cases: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """Summarize fixture coverage by public-life domain."""
    rows_by_domain: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        rows_by_domain.setdefault(str(case["domain"]), []).append(case)

    coverage = []
    for domain, rows in sorted(rows_by_domain.items()):
        topic_counts: dict[str, int] = {}
        event_count = 0
        for row in rows:
            for topic, years in row.get("event_tags", {}).items():
                topic_counts[str(topic)] = topic_counts.get(str(topic), 0) + len(years)
                event_count += len(years)
        coverage.append(
            {
                "domain": domain,
                "case_count": len(rows),
                "event_count": event_count,
                "case_ids": [str(row["id"]) for row in rows],
                "ratings": sorted({str(row["source"]["rating"]) for row in rows}),
                "sources": sorted({str(row["source"]["name"]) for row in rows}),
                "event_topics": sorted(topic_counts),
                "event_topic_counts": dict(sorted(topic_counts.items())),
                "boundary": "Domain coverage proves fixture breadth only; it does not prove prediction validity.",
            }
        )
    return coverage


def _fixture_birth_source_quality(cases: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Summarize whether fixture birth data is suitable for hour-sensitive calibration."""
    high_confidence_ratings = {"甲甲", "甲"}
    rating_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    high_confidence_case_ids: list[str] = []
    caution_case_ids: list[str] = []
    invalid_birth_time_case_ids: list[str] = []
    missing_birth_source_case_ids: list[str] = []
    for case in cases:
        case_id = str(case.get("id", ""))
        birth = case.get("birth", {}) if isinstance(case.get("birth"), dict) else {}
        source = case.get("source", {}) if isinstance(case.get("source"), dict) else {}
        rating = str(source.get("rating", ""))
        source_name = str(source.get("name", ""))
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
        source_counts[source_name] = source_counts.get(source_name, 0) + 1
        if not source_name or not rating:
            missing_birth_source_case_ids.append(case_id)
        if not _birth_time_format_valid(str(birth.get("birth_time", ""))):
            invalid_birth_time_case_ids.append(case_id)
        if rating in high_confidence_ratings:
            high_confidence_case_ids.append(case_id)
        else:
            caution_case_ids.append(case_id)
    hour_pillar_eligible_case_ids = [
        case_id
        for case_id in high_confidence_case_ids
        if case_id not in invalid_birth_time_case_ids and case_id not in missing_birth_source_case_ids
    ]
    return {
        "schema_version": "famous-case-birth-source-quality-v1",
        "case_count": len(cases),
        "source_counts": dict(sorted(source_counts.items())),
        "rating_counts": dict(sorted(rating_counts.items())),
        "high_confidence_ratings": sorted(high_confidence_ratings),
        "high_confidence_case_count": len(high_confidence_case_ids),
        "high_confidence_case_ids": sorted(high_confidence_case_ids),
        "caution_case_count": len(caution_case_ids),
        "caution_case_ids": sorted(caution_case_ids),
        "birth_time_format_valid_count": len(cases) - len(invalid_birth_time_case_ids),
        "birth_time_format_invalid_case_ids": sorted(invalid_birth_time_case_ids),
        "missing_birth_source_case_ids": sorted(missing_birth_source_case_ids),
        "hour_pillar_scoring_eligible_case_count": len(hour_pillar_eligible_case_ids),
        "hour_pillar_scoring_eligible_case_ids": sorted(hour_pillar_eligible_case_ids),
        "boundary": (
            "High source quality permits hour-sensitive symbolic calibration only. It does not prove predictive "
            "validity or replace external review of event labels."
        ),
    }


def _birth_time_format_valid(value: str) -> bool:
    return re.fullmatch(r"\d{2}:\d{2}", value) is not None


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


def famous_case_school_calibration_receipt() -> dict[str, Any]:
    """Run all famous cases through the BaZi school debate topic-coverage check."""
    fixture_receipt = famous_case_receipt()
    case_scores = [_score_case(case) for case in FAMOUS_CASES]
    school_summary = _school_summary(case_scores)
    domain_summary = _domain_summary(case_scores)
    material = {
        "schema_version": "mingli-famous-case-school-calibration-v1",
        "fixture_sha256": fixture_receipt["sha256"],
        "case_count": len(case_scores),
        "case_scores": case_scores,
        "school_summary": school_summary,
        "domain_summary": domain_summary,
        "mean_topic_recall": _mean([case["mean_topic_recall"] for case in case_scores]),
        "low_coverage_cases": [
            {
                "case_id": case["case_id"],
                "case_name": case["case_name"],
                "case_domain": case["case_domain"],
                "mean_topic_recall": case["mean_topic_recall"],
            }
            for case in case_scores
            if case["mean_topic_recall"] < 0.35
        ],
        "boundary": (
            "This is school-topic coverage against sourced celebrity event tags. "
            "It is not event-year accuracy and not statistical proof of prediction."
        ),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **material,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def famous_case_annual_event_calibration_receipt() -> dict[str, Any]:
    """Check whether annual rows expose weak signals around sourced event years."""
    fixture_receipt = famous_case_receipt()
    case_scores = [_score_case_annual_events(case) for case in FAMOUS_CASES]
    birth_source_quality_summary = _annual_birth_source_quality_summary(case_scores)
    topic_summary = _annual_topic_summary(case_scores)
    domain_topic_summary = _annual_domain_topic_summary(case_scores)
    domain_topic_variant_sweep = _domain_topic_variant_sweep(case_scores)
    event_subtype_summary = _annual_event_subtype_summary(case_scores)
    rule_variant_sweep = _annual_rule_variant_sweep(case_scores)
    rule_refinement_queue = _annual_rule_refinement_queue(topic_summary)
    material = {
        "schema_version": "mingli-famous-case-annual-event-calibration-v1",
        "fixture_sha256": fixture_receipt["sha256"],
        "case_count": len(case_scores),
        "event_count": sum(int(case["event_count"]) for case in case_scores),
        "negative_year_count": sum(int(case["negative_year_count"]) for case in case_scores),
        "exact_hit_count": sum(int(case["exact_hit_count"]) for case in case_scores),
        "window_hit_count": sum(int(case["window_hit_count"]) for case in case_scores),
        "false_positive_count": sum(int(case["false_positive_count"]) for case in case_scores),
        "strict_exact_hit_count": sum(int(case["strict_exact_hit_count"]) for case in case_scores),
        "strict_false_positive_count": sum(int(case["strict_false_positive_count"]) for case in case_scores),
        "exact_hit_rate": _rate(sum(int(case["exact_hit_count"]) for case in case_scores), sum(int(case["event_count"]) for case in case_scores)),
        "window_hit_rate": _rate(sum(int(case["window_hit_count"]) for case in case_scores), sum(int(case["event_count"]) for case in case_scores)),
        "exact_precision": _rate(
            sum(int(case["exact_hit_count"]) for case in case_scores),
            sum(int(case["exact_hit_count"]) + int(case["false_positive_count"]) for case in case_scores),
        ),
        "strict_exact_hit_rate": _rate(
            sum(int(case["strict_exact_hit_count"]) for case in case_scores),
            sum(int(case["event_count"]) for case in case_scores),
        ),
        "strict_exact_precision": _rate(
            sum(int(case["strict_exact_hit_count"]) for case in case_scores),
            sum(int(case["strict_exact_hit_count"]) + int(case["strict_false_positive_count"]) for case in case_scores),
        ),
        "strict_false_positive_rate": _rate(
            sum(int(case["strict_false_positive_count"]) for case in case_scores),
            sum(int(case["negative_year_count"]) for case in case_scores),
        ),
        "false_positive_rate": _rate(
            sum(int(case["false_positive_count"]) for case in case_scores),
            sum(int(case["negative_year_count"]) for case in case_scores),
        ),
        "case_scores": case_scores,
        "birth_source_quality_summary": birth_source_quality_summary,
        "domain_summary": _annual_domain_summary(case_scores),
        "domain_topic_summary": domain_topic_summary,
        "domain_topic_refinement_queue": _domain_topic_refinement_queue(domain_topic_summary),
        "domain_topic_variant_sweep": domain_topic_variant_sweep,
        "topic_summary": topic_summary,
        "industry_event_evidence_summary": _industry_event_evidence_summary(case_scores),
        "industry_event_source_coverage": _industry_event_source_coverage(case_scores),
        "event_subtype_summary": event_subtype_summary,
        "rule_variant_sweep": rule_variant_sweep,
        "rule_refinement_queue": rule_refinement_queue,
        "evolution_task_plan": _annual_evolution_task_plan(
            topic_summary,
            event_subtype_summary,
            rule_variant_sweep,
            rule_refinement_queue,
        ),
        "low_coverage_cases": [
            {
                "case_id": case["case_id"],
                "case_name": case["case_name"],
                "case_domain": case["case_domain"],
                "window_hit_rate": case["window_hit_rate"],
            }
            for case in case_scores
            if case["window_hit_rate"] < 0.35
        ],
        "boundary": (
            "This checks whether symbolic annual rows expose expected topic signals in the event year "
            "or adjacent years, and whether the same signals over-fire in non-event years. "
            "It is weak calibration, not causal proof or prediction accuracy."
        ),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **material,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _score_case(case: dict[str, Any]) -> dict[str, Any]:
    birth = _case_birth(case)
    chart = build_bazi_chart(birth)
    debate = chart.get("deep_analysis", {}).get("school_debate", {})
    scored = score_school_topics(debate, case)
    rows = scored["rows"]
    return {
        "case_id": case["id"],
        "case_name": case["name"],
        "case_domain": case["domain"],
        "source_rating": case["source"]["rating"],
        "provider_quality": chart.get("context", {}).get("provider_quality"),
        "school_debate_sha256": debate.get("sha256"),
        "event_topics": sorted(case.get("event_tags", {}).keys()),
        "mean_topic_recall": _mean([float(row.get("topic_recall", 0.0)) for row in rows]),
        "best_school": _best_school(rows),
        "rows": rows,
    }


def _score_case_annual_events(case: dict[str, Any]) -> dict[str, Any]:
    birth = _case_birth(case)
    chart = build_bazi_chart(birth)
    birth_source_quality = _case_birth_source_quality(case)
    years = sorted({int(year) for values in case.get("event_tags", {}).values() for year in values})
    if not years:
        annual = {"rows": []}
    else:
        annual = build_annual_luck(birth, chart, start_year=min(years), end_year=max(years))
    rows_by_year = {int(row["year"]): row for row in annual.get("rows", [])}
    events = []
    for topic, topic_years in sorted(case.get("event_tags", {}).items()):
        for year in topic_years:
            events.append(_score_event_year(case, topic, int(year), rows_by_year, chart.get("pillars", {})))
    negative_samples = []
    all_years = set(rows_by_year)
    for topic, topic_years in sorted(case.get("event_tags", {}).items()):
        event_years = {int(year) for year in topic_years}
        for year in sorted(all_years - event_years):
            sample = _score_negative_year(topic, year, rows_by_year, chart.get("pillars", {}))
            if sample:
                negative_samples.append(sample)
    exact_hit_count = sum(1 for event in events if event["exact_match"])
    window_hit_count = sum(1 for event in events if event["window_match"])
    false_positive_count = sum(1 for sample in negative_samples if sample["false_positive"])
    strict_exact_hit_count = sum(1 for event in events if event["strict_exact_match"])
    strict_false_positive_count = sum(1 for sample in negative_samples if sample["strict_false_positive"])
    return {
        "case_id": case["id"],
        "case_name": case["name"],
        "case_domain": case["domain"],
        "source_rating": case["source"]["rating"],
        "birth_source_quality": birth_source_quality,
        "hour_pillar_scoring_eligible": birth_source_quality["hour_pillar_scoring_eligible"],
        "annual_range": annual.get("range", {}),
        "annual_rows_sha256": _stable_hash(annual.get("rows", [])),
        "event_count": len(events),
        "negative_year_count": len(negative_samples),
        "exact_hit_count": exact_hit_count,
        "window_hit_count": window_hit_count,
        "false_positive_count": false_positive_count,
        "strict_exact_hit_count": strict_exact_hit_count,
        "strict_false_positive_count": strict_false_positive_count,
        "exact_hit_rate": _rate(exact_hit_count, len(events)),
        "window_hit_rate": _rate(window_hit_count, len(events)),
        "exact_precision": _rate(exact_hit_count, exact_hit_count + false_positive_count),
        "false_positive_rate": _rate(false_positive_count, len(negative_samples)),
        "strict_exact_hit_rate": _rate(strict_exact_hit_count, len(events)),
        "strict_exact_precision": _rate(strict_exact_hit_count, strict_exact_hit_count + strict_false_positive_count),
        "strict_false_positive_rate": _rate(strict_false_positive_count, len(negative_samples)),
        "events": events,
        "negative_samples": negative_samples,
    }


def _case_birth_source_quality(case: dict[str, Any]) -> dict[str, Any]:
    birth = case.get("birth", {}) if isinstance(case.get("birth"), dict) else {}
    source = case.get("source", {}) if isinstance(case.get("source"), dict) else {}
    rating = str(source.get("rating", ""))
    source_name = str(source.get("name", ""))
    birth_time_valid = _birth_time_format_valid(str(birth.get("birth_time", "")))
    high_confidence = rating in {"甲甲", "甲"}
    source_present = bool(source_name and rating)
    return {
        "schema_version": "famous-case-birth-source-quality-case-v1",
        "source_name": source_name,
        "source_rating": rating,
        "birth_time_format_valid": birth_time_valid,
        "high_confidence_birth_source": high_confidence,
        "hour_pillar_scoring_eligible": high_confidence and source_present and birth_time_valid,
        "caution": not high_confidence or not source_present or not birth_time_valid,
        "boundary": (
            "This case-level quality flag controls calibration hygiene. It does not certify event labels "
            "or predictive validity."
        ),
    }


def _annual_birth_source_quality_summary(case_scores: list[dict[str, Any]]) -> dict[str, Any]:
    eligible_cases = [
        str(case.get("case_id"))
        for case in case_scores
        if case.get("hour_pillar_scoring_eligible") is True
    ]
    caution_cases = [
        str(case.get("case_id"))
        for case in case_scores
        if case.get("hour_pillar_scoring_eligible") is not True
    ]
    eligible_event_count = sum(
        int(case.get("event_count", 0))
        for case in case_scores
        if case.get("hour_pillar_scoring_eligible") is True
    )
    caution_event_count = sum(
        int(case.get("event_count", 0))
        for case in case_scores
        if case.get("hour_pillar_scoring_eligible") is not True
    )
    return {
        "schema_version": "famous-case-annual-birth-source-quality-summary-v1",
        "case_count": len(case_scores),
        "hour_pillar_scoring_eligible_case_count": len(eligible_cases),
        "hour_pillar_scoring_eligible_case_ids": sorted(eligible_cases),
        "caution_case_count": len(caution_cases),
        "caution_case_ids": sorted(caution_cases),
        "eligible_event_count": eligible_event_count,
        "caution_event_count": caution_event_count,
        "eligible_event_rate": _rate(eligible_event_count, eligible_event_count + caution_event_count),
        "boundary": (
            "Hour-pillar-sensitive calibration should use eligible cases. Caution cases can remain in broad "
            "annual diagnostics only with source-quality caveats."
        ),
    }


def _score_event_year(
    case: dict[str, Any],
    topic: str,
    year: int,
    rows_by_year: dict[int, dict[str, Any]],
    natal_pillars: object,
) -> dict[str, Any]:
    expected = EVENT_TOPIC_ANNUAL_SIGNALS.get(topic, {"categories": set(), "intensities": set()})
    row = rows_by_year.get(year, {})
    neighbor_rows = [rows_by_year[item] for item in (year - 1, year, year + 1) if item in rows_by_year]
    evidence = _annual_event_evidence(row, natal_pillars)
    exact_match = _row_matches_event(row, expected)
    window_match = any(_row_matches_event(item, expected) for item in neighbor_rows)
    strict_exact_match = _row_strictly_matches_event(topic, row, expected, evidence)
    event_subtype = _event_subtype(case, topic, year)
    return {
        "event_topic": topic,
        "event_subtype": event_subtype,
        "industry_event_evidence": _industry_event_evidence(str(case.get("domain", "")), topic, event_subtype),
        "event_year": year,
        "expected_categories": sorted(expected.get("categories", set())),
        "expected_intensities": sorted(expected.get("intensities", set())),
        "annual_category": row.get("category", ""),
        "annual_intensity": row.get("intensity", ""),
        "annual_useful_state": row.get("bazi_evidence", {}).get("useful_state", "") if isinstance(row.get("bazi_evidence"), dict) else "",
        "annual_pillar": row.get("ganzhi", ""),
        "event_evidence": evidence,
        "exact_match": exact_match,
        "window_match": window_match,
        "strict_exact_match": strict_exact_match,
        "boundary": "A match means expected symbolic topic signal is present; it is not a verified prediction.",
    }


def _score_negative_year(
    topic: str,
    year: int,
    rows_by_year: dict[int, dict[str, Any]],
    natal_pillars: object,
) -> dict[str, Any]:
    expected = EVENT_TOPIC_ANNUAL_SIGNALS.get(topic)
    if not expected:
        return {}
    row = rows_by_year.get(year, {})
    evidence = _annual_event_evidence(row, natal_pillars)
    false_positive = _row_matches_event(row, expected)
    strict_false_positive = _row_strictly_matches_event(topic, row, expected, evidence)
    return {
        "event_topic": topic,
        "event_subtype": None,
        "negative_year": year,
        "annual_category": row.get("category", ""),
        "annual_intensity": row.get("intensity", ""),
        "annual_useful_state": row.get("bazi_evidence", {}).get("useful_state", "") if isinstance(row.get("bazi_evidence"), dict) else "",
        "annual_pillar": row.get("ganzhi", ""),
        "event_evidence": evidence,
        "false_positive": false_positive,
        "strict_false_positive": strict_false_positive,
        "boundary": "A false positive means the symbolic signal appears in a year without this sourced event tag.",
    }


def _event_subtype(case: dict[str, Any], topic: str, year: int) -> str:
    case_subtypes = EVENT_SUBTYPE_BY_CASE_TOPIC_YEAR.get(str(case.get("id")), {})
    topic_subtypes = case_subtypes.get(topic, {})
    return topic_subtypes.get(year, EVENT_SUBTYPE_BY_TOPIC.get(topic, "unspecified_event"))


def _industry_event_evidence(domain: str, topic: str, event_subtype: str) -> dict[str, Any]:
    subtype = event_subtype.lower()
    film_domain = domain in {"影视", "影视武术"}
    music_domain = domain == "歌手"
    sports_domain = domain == "体育"
    evidence = {
        "domain": domain,
        "event_topic": topic,
        "event_subtype": event_subtype,
        "industry": (
            "film_or_television"
            if film_domain
            else "music"
            if music_domain
            else "sports"
            if sports_domain
            else "general"
        ),
        "has_release_marker": any(
            token in subtype
            for token in (
                "release",
                "album",
                "single",
                "film",
                "television",
                "series",
                "screen",
                "video",
                "tour",
                "publication",
            )
        ),
        "has_award_or_recognition_marker": any(
            token in subtype
            for token in (
                "award",
                "recognition",
                "nominated",
                "winning",
                "hall_of_fame",
                "number_one",
                "record",
                "title",
                "prize",
            )
        ),
        "has_commercial_or_chart_marker": any(
            token in subtype
            for token in ("chart", "global", "box_office", "ratings", "commercial", "breakthrough_album")
        ),
        "has_media_or_publicity_marker": any(
            token in subtype
            for token in ("public", "fame", "media", "broadcast", "attention", "image", "cultural")
        ),
        "has_competition_marker": any(
            token in subtype
            for token in (
                "grand_slam",
                "slam",
                "olympic",
                "medal",
                "championship",
                "competition",
                "ranking",
                "title",
                "season",
                "peak",
                "comeback",
            )
        ),
        "has_project_marker": topic == "career_project",
        "has_industry_project_marker": topic == "career_project"
        and any(
            token in subtype
            for token in (
                "contract",
                "entry",
                "role",
                "production",
                "launch",
                "debut",
                "relaunch",
                "selection",
                "founding",
            )
        ),
        "has_fame_marker": topic == "public_fame",
        "boundary": "Industry evidence is extracted from sourced fixture subtypes for calibration only.",
    }
    evidence["has_domain_specific_evidence"] = any(
        bool(evidence[key])
        for key in (
            "has_release_marker",
            "has_award_or_recognition_marker",
            "has_commercial_or_chart_marker",
            "has_media_or_publicity_marker",
            "has_competition_marker",
            "has_industry_project_marker",
        )
    )
    if film_domain:
        evidence["has_film_fame_evidence"] = topic == "public_fame" and (
            evidence["has_release_marker"]
            or evidence["has_award_or_recognition_marker"]
            or evidence["has_media_or_publicity_marker"]
        )
        evidence["has_film_project_evidence"] = topic == "career_project" and (
            evidence["has_release_marker"]
            or evidence["has_award_or_recognition_marker"]
            or evidence["has_industry_project_marker"]
        )
    if music_domain:
        evidence["has_music_fame_evidence"] = topic == "public_fame" and (
            evidence["has_commercial_or_chart_marker"]
            or evidence["has_award_or_recognition_marker"]
            or evidence["has_media_or_publicity_marker"]
        )
        evidence["has_music_project_evidence"] = topic == "career_project" and evidence["has_release_marker"]
    if sports_domain:
        evidence["has_sports_peak_evidence"] = topic == "sports_peak" and (
            evidence["has_competition_marker"] or evidence["has_award_or_recognition_marker"]
        )
    return evidence


def _row_matches_event(row: dict[str, Any], expected: dict[str, set[str]]) -> bool:
    if not row:
        return False
    category = str(row.get("category", ""))
    intensity = str(row.get("intensity", ""))
    useful_state = ""
    if isinstance(row.get("bazi_evidence"), dict):
        useful_state = str(row["bazi_evidence"].get("useful_state", ""))
    category_match = category in expected.get("categories", set())
    intensity_match = intensity in expected.get("intensities", set())
    useful_match = useful_state in {"useful_element_activated", "dominant_element_reinforced"}
    return category_match or intensity_match or useful_match


def _annual_event_evidence(row: dict[str, Any], natal_pillars: object) -> dict[str, Any]:
    bazi_evidence = row.get("bazi_evidence", {}) if isinstance(row.get("bazi_evidence"), dict) else {}
    ten_gods_raw = bazi_evidence.get("annual_ten_gods", {}) if isinstance(bazi_evidence.get("annual_ten_gods"), dict) else {}
    ten_gods = sorted({str(value) for value in ten_gods_raw.values() if value})
    active_major_luck = bazi_evidence.get("active_major_luck", {})
    natal_matches = bazi_evidence.get("natal_pillar_matches", [])
    if not isinstance(active_major_luck, dict):
        active_major_luck = {}
    if not isinstance(natal_matches, list):
        natal_matches = []
    annual_branch = _branch_from_ganzhi(str(row.get("ganzhi") or bazi_evidence.get("annual_pillar", "")))
    branch_clashes = _branch_clash_evidence(annual_branch, natal_pillars)
    event_markers = row.get("event_markers", {}) if isinstance(row.get("event_markers"), dict) else {}
    career_signal_strength = sum(
        1
        for key in ("has_expression", "has_authority", "has_wealth")
        if {
            "has_expression": "expression" in ten_gods,
            "has_authority": "authority" in ten_gods,
            "has_wealth": "wealth" in ten_gods,
        }[key]
    )
    career_text = " ".join(
        str(row.get(key, ""))
        for key in ("career", "official_career", "leadership", "theme", "phase")
    ).lower()
    career_launch_signal = bool(event_markers.get("career_launch")) or _text_has_any(
        career_text,
        ("output", "visibility", "sales", "teaching", "public delivery", "creative outputs", "career entry"),
    )
    role_power_signal = bool(event_markers.get("role_power")) or _text_has_any(
        career_text,
        ("rules", "title", "leadership", "institutional pressure", "managers", "regulators", "role clarity"),
    )
    role_transition_signal = bool(event_markers.get("role_transition"))
    return {
        "ten_gods": ten_gods,
        "has_expression": "expression" in ten_gods,
        "has_authority": "authority" in ten_gods,
        "has_wealth": "wealth" in ten_gods,
        "has_resource": "resource" in ten_gods or "learning" in ten_gods,
        "has_peer": "peer" in ten_gods,
        "career_signal_strength": career_signal_strength,
        "career_launch_signal": career_launch_signal,
        "role_power_signal": role_power_signal,
        "role_transition_signal": role_transition_signal,
        "event_markers": dict(sorted(event_markers.items())),
        "major_luck_active": bool(active_major_luck),
        "natal_activation": bool(natal_matches),
        "natal_activation_pillars": sorted(
            str(item.get("pillar", "")) for item in natal_matches if isinstance(item, dict) and item.get("pillar")
        ),
        "annual_branch": annual_branch,
        "branch_clashes": branch_clashes,
        "movement_signal": bool(branch_clashes),
        "useful_state": str(bazi_evidence.get("useful_state", "")),
    }


def _branch_from_ganzhi(label: str) -> str:
    stem = next((candidate for candidate in STEMS if label.startswith(candidate)), "")
    branch = label[len(stem) :] if stem else ""
    return branch if branch in BRANCHES else ""


def _text_has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _branch_clash_evidence(annual_branch: str, natal_pillars: object) -> list[dict[str, str]]:
    if not annual_branch or not isinstance(natal_pillars, dict):
        return []
    clash_branch = BRANCH_CLASHES.get(annual_branch)
    rows = []
    for pillar, label in natal_pillars.items():
        natal_branch = _branch_from_ganzhi(str(label))
        if natal_branch and natal_branch == clash_branch:
            rows.append(
                {
                    "pillar": str(pillar),
                    "annual_branch": annual_branch,
                    "natal_branch": natal_branch,
                    "relation": "clash",
                }
            )
    return rows


def _row_strictly_matches_event(
    topic: str,
    row: dict[str, Any],
    expected: dict[str, set[str]],
    evidence: dict[str, Any],
) -> bool:
    if not row:
        return False
    category = str(row.get("category", ""))
    intensity = str(row.get("intensity", ""))
    useful_state = str(evidence.get("useful_state", ""))
    category_match = category in expected.get("categories", set())
    constructive = intensity in {"constructive", "active"}
    volatile = intensity == "high-volatility"
    useful_or_pressure = useful_state in {"useful_element_activated", "dominant_element_reinforced"}
    major_or_natal = bool(evidence.get("major_luck_active")) or bool(evidence.get("natal_activation"))
    movement_signal = bool(evidence.get("movement_signal"))
    event_markers = evidence.get("event_markers", {}) if isinstance(evidence.get("event_markers"), dict) else {}
    branch_clashes = evidence.get("branch_clashes", []) if isinstance(evidence.get("branch_clashes"), list) else []
    core_clash_count = _core_branch_clash_count(branch_clashes)
    if topic == "health_risk":
        return volatile and useful_state == "dominant_element_reinforced"
    if topic == "public_fame":
        return bool(evidence.get("has_expression")) and category == "expression" and (useful_or_pressure or major_or_natal)
    if topic == "public_controversy":
        return category in {"expression", "authority"} and volatile and (
            bool(evidence.get("has_expression")) or bool(evidence.get("has_authority"))
        )
    if topic == "relationship":
        return category in {"friends", "wealth"} and (bool(evidence.get("has_peer")) or bool(evidence.get("has_wealth"))) and (
            useful_or_pressure or bool(evidence.get("natal_activation"))
        )
    if topic == "sports_peak":
        return category in {"expression", "authority"} and constructive and (
            bool(evidence.get("has_expression")) or bool(evidence.get("has_authority"))
        )
    if topic == "study_exam":
        return category in {"learning", "authority"} and (
            bool(evidence.get("has_resource")) or bool(evidence.get("has_authority"))
        ) and (constructive or useful_or_pressure)
    if topic == "career_power":
        return (
            category == "authority"
            and bool(evidence.get("has_authority"))
            and bool(evidence.get("role_power_signal"))
            and (useful_or_pressure or major_or_natal)
        )
    if topic == "business_power":
        return category in {"wealth", "authority"} and (
            bool(evidence.get("has_authority")) or bool(evidence.get("has_wealth"))
        ) and major_or_natal
    if topic == "career_project":
        return (
            category_match
            and bool(event_markers.get("career_launch"))
            and (useful_or_pressure or bool(evidence.get("natal_activation")))
        )
    if topic in {"migration", "transition"}:
        return (
            category in {"learning", "friends", "wealth", "expression"}
            and movement_signal
            and core_clash_count >= 2
            and major_or_natal
        )
    if topic in {"war_pressure", "family_relation"}:
        return category_match and volatile and (major_or_natal or bool(evidence.get("has_authority")))
    return category_match and (constructive or volatile or useful_or_pressure)


def _core_branch_clash_count(branch_clashes: list[object]) -> int:
    return sum(
        1
        for item in branch_clashes
        if isinstance(item, dict) and item.get("pillar") in {"year", "month", "day"}
    )


def _case_birth(case: dict[str, Any]) -> dict[str, Any]:
    birth = case["birth"]
    year, month, day = str(birth["birth_date"]).split("-")
    hour, minute = str(birth["birth_time"]).split(":")
    return {
        "name": case["name"],
        "gender": birth["gender"],
        "year": int(year),
        "month": int(month),
        "day": int(day),
        "hour": int(hour),
        "minute": int(minute),
        "place": birth["birthplace"],
    }


def _best_school(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"school": "", "topic_recall": 0.0, "event_topic_overlap": []}
    best = max(rows, key=lambda row: float(row.get("topic_recall", 0.0)))
    return {
        "school": best.get("school", ""),
        "topic_recall": best.get("topic_recall", 0.0),
        "event_topic_overlap": best.get("event_topic_overlap", []),
    }


def _school_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_school: dict[str, list[dict[str, Any]]] = {}
    for case in case_scores:
        for row in case["rows"]:
            rows_by_school.setdefault(str(row["school"]), []).append(row)
    return [
        {
            "school": school,
            "case_count": len(rows),
            "mean_topic_recall": _mean([float(row.get("topic_recall", 0.0)) for row in rows]),
            "covered_case_count": sum(1 for row in rows if row.get("event_topic_overlap")),
            "boundary": "School-level summary measures event-topic coverage only.",
        }
        for school, rows in sorted(rows_by_school.items())
    ]


def _domain_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_domain: dict[str, list[dict[str, Any]]] = {}
    for case in case_scores:
        rows_by_domain.setdefault(str(case["case_domain"]), []).append(case)
    return [
        {
            "domain": domain,
            "case_count": len(rows),
            "mean_topic_recall": _mean([float(row.get("mean_topic_recall", 0.0)) for row in rows]),
            "case_ids": [str(row["case_id"]) for row in rows],
        }
        for domain, rows in sorted(rows_by_domain.items())
    ]


def _annual_domain_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_domain: dict[str, list[dict[str, Any]]] = {}
    for case in case_scores:
        rows_by_domain.setdefault(str(case["case_domain"]), []).append(case)
    return [
        {
            "domain": domain,
            "case_count": len(rows),
            "event_count": sum(int(row["event_count"]) for row in rows),
            "negative_year_count": sum(int(row["negative_year_count"]) for row in rows),
            "exact_hit_rate": _rate(
                sum(int(row["exact_hit_count"]) for row in rows),
                sum(int(row["event_count"]) for row in rows),
            ),
            "window_hit_rate": _rate(
                sum(int(row["window_hit_count"]) for row in rows),
                sum(int(row["event_count"]) for row in rows),
            ),
            "exact_precision": _rate(
                sum(int(row["exact_hit_count"]) for row in rows),
                sum(int(row["exact_hit_count"]) + int(row["false_positive_count"]) for row in rows),
            ),
            "false_positive_rate": _rate(
                sum(int(row["false_positive_count"]) for row in rows),
                sum(int(row["negative_year_count"]) for row in rows),
            ),
            "strict_exact_hit_rate": _rate(
                sum(int(row["strict_exact_hit_count"]) for row in rows),
                sum(int(row["event_count"]) for row in rows),
            ),
            "strict_exact_precision": _rate(
                sum(int(row["strict_exact_hit_count"]) for row in rows),
                sum(int(row["strict_exact_hit_count"]) + int(row["strict_false_positive_count"]) for row in rows),
            ),
            "strict_false_positive_rate": _rate(
                sum(int(row["strict_false_positive_count"]) for row in rows),
                sum(int(row["negative_year_count"]) for row in rows),
            ),
            "case_ids": [str(row["case_id"]) for row in rows],
        }
        for domain, rows in sorted(rows_by_domain.items())
    ]


def _annual_topic_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_rows_by_topic: dict[str, list[dict[str, Any]]] = {}
    negative_rows_by_topic: dict[str, list[dict[str, Any]]] = {}
    for case in case_scores:
        for event in case.get("events", []):
            event_rows_by_topic.setdefault(str(event["event_topic"]), []).append(event)
        for sample in case.get("negative_samples", []):
            negative_rows_by_topic.setdefault(str(sample["event_topic"]), []).append(sample)
    topics = sorted(set(event_rows_by_topic) | set(negative_rows_by_topic))
    rows = []
    for topic in topics:
        event_rows = event_rows_by_topic.get(topic, [])
        negative_rows = negative_rows_by_topic.get(topic, [])
        eligible_event_count = sum(
            1
            for case in case_scores
            if case.get("hour_pillar_scoring_eligible") is True
            for item in case.get("events", [])
            if item.get("event_topic") == topic
        )
        caution_event_count = sum(
            1
            for case in case_scores
            if case.get("hour_pillar_scoring_eligible") is not True
            for item in case.get("events", [])
            if item.get("event_topic") == topic
        )
        exact_hit_count = sum(1 for item in event_rows if item.get("exact_match"))
        window_hit_count = sum(1 for item in event_rows if item.get("window_match"))
        false_positive_count = sum(1 for item in negative_rows if item.get("false_positive"))
        strict_hit_count = sum(1 for item in event_rows if item.get("strict_exact_match"))
        strict_false_positive_count = sum(1 for item in negative_rows if item.get("strict_false_positive"))
        rows.append(
            {
                "event_topic": topic,
                "event_count": len(event_rows),
                "eligible_event_count": eligible_event_count,
                "caution_event_count": caution_event_count,
                "eligible_event_rate": _rate(eligible_event_count, len(event_rows)),
                "negative_year_count": len(negative_rows),
                "exact_hit_rate": _rate(exact_hit_count, len(event_rows)),
                "window_hit_rate": _rate(window_hit_count, len(event_rows)),
                "false_positive_rate": _rate(false_positive_count, len(negative_rows)),
                "exact_precision": _rate(exact_hit_count, exact_hit_count + false_positive_count),
                "strict_exact_hit_rate": _rate(strict_hit_count, len(event_rows)),
                "strict_false_positive_rate": _rate(strict_false_positive_count, len(negative_rows)),
                "strict_exact_precision": _rate(strict_hit_count, strict_hit_count + strict_false_positive_count),
                "precision_gap": round(
                    _rate(strict_hit_count, strict_hit_count + strict_false_positive_count)
                    - _rate(exact_hit_count, exact_hit_count + false_positive_count),
                    3,
                ),
                "case_ids": sorted(
                    {
                        str(case["case_id"])
                        for case in case_scores
                        if any(item.get("event_topic") == topic for item in case.get("events", []))
                    }
                ),
            }
        )
    return rows


def _annual_domain_topic_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    negative_rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    case_ids_by_key: dict[tuple[str, str], set[str]] = {}

    for case in case_scores:
        domain = str(case["case_domain"])
        case_id = str(case["case_id"])
        for event in case.get("events", []):
            key = (domain, str(event["event_topic"]))
            event_rows_by_key.setdefault(key, []).append(event)
            case_ids_by_key.setdefault(key, set()).add(case_id)
        for sample in case.get("negative_samples", []):
            key = (domain, str(sample["event_topic"]))
            negative_rows_by_key.setdefault(key, []).append(sample)
            case_ids_by_key.setdefault(key, set()).add(case_id)

    rows = []
    for domain, topic in sorted(set(event_rows_by_key) | set(negative_rows_by_key)):
        key = (domain, topic)
        event_rows = event_rows_by_key.get(key, [])
        negative_rows = negative_rows_by_key.get(key, [])
        eligible_event_count = sum(
            1
            for case in case_scores
            if case.get("case_domain") == domain and case.get("hour_pillar_scoring_eligible") is True
            for item in case.get("events", [])
            if item.get("event_topic") == topic
        )
        caution_event_count = sum(
            1
            for case in case_scores
            if case.get("case_domain") == domain and case.get("hour_pillar_scoring_eligible") is not True
            for item in case.get("events", [])
            if item.get("event_topic") == topic
        )
        exact_hit_count = sum(1 for item in event_rows if item.get("exact_match"))
        window_hit_count = sum(1 for item in event_rows if item.get("window_match"))
        false_positive_count = sum(1 for item in negative_rows if item.get("false_positive"))
        strict_hit_count = sum(1 for item in event_rows if item.get("strict_exact_match"))
        strict_false_positive_count = sum(1 for item in negative_rows if item.get("strict_false_positive"))
        rows.append(
            {
                "domain": domain,
                "event_topic": topic,
                "case_count": len(case_ids_by_key.get(key, set())),
                "event_count": len(event_rows),
                "eligible_event_count": eligible_event_count,
                "caution_event_count": caution_event_count,
                "eligible_event_rate": _rate(eligible_event_count, len(event_rows)),
                "negative_year_count": len(negative_rows),
                "exact_hit_rate": _rate(exact_hit_count, len(event_rows)),
                "window_hit_rate": _rate(window_hit_count, len(event_rows)),
                "exact_precision": _rate(exact_hit_count, exact_hit_count + false_positive_count),
                "false_positive_rate": _rate(false_positive_count, len(negative_rows)),
                "strict_exact_hit_rate": _rate(strict_hit_count, len(event_rows)),
                "strict_exact_precision": _rate(strict_hit_count, strict_hit_count + strict_false_positive_count),
                "strict_false_positive_rate": _rate(strict_false_positive_count, len(negative_rows)),
                "case_ids": sorted(case_ids_by_key.get(key, set())),
                "boundary": "Domain-topic metrics are diagnostic slices; small slices are not statistical proof.",
            }
        )
    return rows


def _domain_topic_refinement_queue(domain_topic_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in domain_topic_summary:
        event_count = int(item.get("event_count", 0))
        if event_count < 3:
            continue
        strict_hit_rate = float(item.get("strict_exact_hit_rate", 0.0))
        strict_precision = float(item.get("strict_exact_precision", 0.0))
        strict_false_positive_rate = float(item.get("strict_false_positive_rate", 0.0))
        if strict_hit_rate < 0.1:
            task_type = "add_domain_specific_evidence"
        elif strict_false_positive_rate >= 0.1:
            task_type = "reduce_domain_false_positive"
        elif strict_precision < 0.2:
            task_type = "refine_domain_precision"
        else:
            continue
        domain = str(item.get("domain", ""))
        topic = str(item.get("event_topic", ""))
        rows.append(
            {
                "task_id": f"domain-topic-{domain}-{topic}-{task_type}",
                "domain": domain,
                "event_topic": topic,
                "task_type": task_type,
                "case_count": int(item.get("case_count", 0)),
                "event_count": event_count,
                "eligible_event_count": int(item.get("eligible_event_count", 0)),
                "caution_event_count": int(item.get("caution_event_count", 0)),
                "eligible_event_rate": float(item.get("eligible_event_rate", 0.0)),
                "negative_year_count": int(item.get("negative_year_count", 0)),
                "strict_exact_hit_rate": strict_hit_rate,
                "strict_exact_precision": strict_precision,
                "strict_false_positive_rate": strict_false_positive_rate,
                "case_ids": item.get("case_ids", []),
                "next_evidence_to_add": _domain_topic_evidence(domain, topic, task_type),
                "acceptance_criteria": _domain_topic_acceptance_criteria(task_type),
                "source": "famous_case_annual_event_calibration.domain_topic_summary",
                "boundary": (
                    "This queue prioritizes domain-specific evidence design. It does not change strict rules "
                    "or claim predictive validity."
                ),
            }
        )
    task_rank = {
        "add_domain_specific_evidence": 0,
        "reduce_domain_false_positive": 1,
        "refine_domain_precision": 2,
    }
    return sorted(
        rows,
        key=lambda row: (
            task_rank.get(str(row["task_type"]), 9),
            -int(row["event_count"]),
            -float(row["strict_false_positive_rate"]),
            str(row["domain"]),
            str(row["event_topic"]),
        ),
    )


def _domain_topic_evidence(domain: str, topic: str, task_type: str) -> list[str]:
    specific: dict[tuple[str, str], list[str]] = {
        ("影视", "public_fame"): [
            "film-or-television release marker separated from generic expression",
            "award, nomination, ratings, box-office, or press-recognition marker",
            "public-image consolidation marker distinct from relationship or controversy publicity",
        ],
        ("影视", "career_project"): [
            "credited screen-role or production-launch marker",
            "project release marker separated from ordinary busy/output year",
            "award-season or industry-recognition marker for project impact",
        ],
        ("歌手", "public_fame"): [
            "chart-success or landmark-album public-recognition marker",
            "broadcast-performance or tour/media peak marker",
            "separate controversy-driven attention from music-achievement fame",
        ],
        ("歌手", "career_project"): [
            "single, album, tour, or label-contract project marker",
            "release-channel marker distinct from general expression",
            "commercial-success marker separated from public controversy",
        ],
        ("体育", "sports_peak"): [
            "championship-title marker separated from generic authority/expression years",
            "ranking, record, or medal marker tied to competitive season",
            "comeback-title marker separated from injury recovery signal",
        ],
    }
    fallback = [
        f"{domain} domain-specific event subtype evidence for {topic}",
        "negative-year contrast examples from the same domain-topic slice",
        "variant-sweep candidate before changing strict annual rules",
    ]
    if task_type == "reduce_domain_false_positive":
        return specific.get((domain, topic), fallback) + [
            "explicit exclusion rule for same-domain negative years that only share broad visibility"
        ]
    return specific.get((domain, topic), fallback)


def _domain_topic_acceptance_criteria(task_type: str) -> list[str]:
    if task_type == "add_domain_specific_evidence":
        return [
            "new domain-specific evidence field appears in event_evidence or event markers",
            "domain_topic_summary strict_exact_hit_rate improves or rejected candidate is recorded",
            "strict_false_positive_rate does not increase for the same domain-topic slice",
        ]
    if task_type == "reduce_domain_false_positive":
        return [
            "domain-topic strict_false_positive_rate decreases versus current slice",
            "strict_exact_precision does not decrease for the same domain-topic slice",
            "negative-year examples remain attached to the diagnostic receipt",
        ]
    return [
        "domain-topic strict_exact_precision improves versus current slice",
        "overall topic precision does not regress",
        "rule_variant_sweep or equivalent candidate metrics are recorded",
    ]


def _domain_topic_variant_sweep(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variants: dict[tuple[str, str], dict[str, Any]] = {
        ("影视", "public_fame"): {
            "rules": {
                "current_strict": _variant_current_strict,
                "expression_visibility_with_support": _variant_public_fame_visibility_support,
                "expression_visibility_or_major_luck": _variant_public_fame_visibility_major_luck,
                "fixture_industry_fame_marker": _variant_industry_fame_marker,
            },
            "boundary": "Film fame candidates are diagnostics until release, award, ratings, box-office, or press evidence exists.",
        },
        ("影视", "career_project"): {
            "rules": {
                "current_strict": _variant_current_strict,
                "project_launch_or_visibility_with_support": _variant_project_launch_or_visibility_support,
                "broad_project_channel_with_major_luck": _variant_project_channel_major_luck,
                "fixture_industry_project_marker": _variant_industry_project_marker,
            },
            "boundary": "Film project candidates are diagnostics until screen-role, production-launch, or release evidence exists.",
        },
        ("歌手", "public_fame"): {
            "rules": {
                "current_strict": _variant_current_strict,
                "expression_visibility_with_support": _variant_public_fame_visibility_support,
                "expression_visibility_or_major_luck": _variant_public_fame_visibility_major_luck,
                "fixture_industry_fame_marker": _variant_industry_fame_marker,
            },
            "boundary": "Music fame candidates are diagnostics until chart, album, broadcast, tour, or media-peak evidence exists.",
        },
        ("歌手", "career_project"): {
            "rules": {
                "current_strict": _variant_current_strict,
                "project_launch_or_visibility_with_support": _variant_project_launch_or_visibility_support,
                "broad_project_channel_with_major_luck": _variant_project_channel_major_luck,
                "fixture_industry_project_marker": _variant_industry_project_marker,
            },
            "boundary": "Music project candidates are diagnostics until single, album, tour, or label-contract evidence exists.",
        },
        ("体育", "sports_peak"): {
            "rules": {
                "current_strict": _variant_current_strict,
                "constructive_performance_current": _variant_sports_peak_constructive_current,
                "performance_with_major_or_natal": _variant_sports_peak_major_or_natal,
                "fixture_industry_peak_marker": _variant_industry_sports_peak_marker,
            },
            "boundary": "Sports peak candidates are diagnostics until title, ranking, record, medal, or comeback evidence exists.",
        },
    }
    rows = []
    for (domain, topic), config in variants.items():
        event_rows = _domain_topic_items(case_scores, domain, topic, "events")
        negative_rows = _domain_topic_items(case_scores, domain, topic, "negative_samples")
        for name, predicate in config["rules"].items():
            exact_hits = sum(1 for item in event_rows if predicate(item))
            false_positives = sum(1 for item in negative_rows if predicate(item))
            rows.append(
                {
                    "domain": domain,
                    "event_topic": topic,
                    "variant": name,
                    "selected": False,
                    "event_count": len(event_rows),
                    "negative_year_count": len(negative_rows),
                    "strict_exact_hit_count": exact_hits,
                    "strict_false_positive_count": false_positives,
                    "strict_exact_hit_rate": _rate(exact_hits, len(event_rows)),
                    "strict_exact_precision": _rate(exact_hits, exact_hits + false_positives),
                    "strict_false_positive_rate": _rate(false_positives, len(negative_rows)),
                    "case_ids": sorted(
                        {
                            str(case["case_id"])
                            for case in case_scores
                            if str(case["case_domain"]) == domain
                            and any(item.get("event_topic") == topic for item in case.get("events", []))
                        }
                    ),
                    "selection_basis": (
                        "No domain-topic variant is selected here. Fixture-industry variants use sourced known-event "
                        "labels as an upper-bound diagnostic and cannot be promoted to prediction rules without a "
                        "separate reviewed event-source provider and false-positive checks."
                    ),
                    "boundary": config["boundary"],
                }
            )
    return rows


def _annual_event_subtype_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_topic: dict[str, list[dict[str, Any]]] = {}
    for case in case_scores:
        for event in case.get("events", []):
            rows_by_topic.setdefault(str(event["event_topic"]), []).append(event)
    rows = []
    for topic, events in sorted(rows_by_topic.items()):
        subtype_counts = _counts(event.get("event_subtype") for event in events)
        default_subtype = EVENT_SUBTYPE_BY_TOPIC.get(topic, "unspecified_event")
        explicit_count = sum(1 for event in events if event.get("event_subtype") != default_subtype)
        rows.append(
            {
                "event_topic": topic,
                "event_count": len(events),
                "subtype_counts": subtype_counts,
                "explicit_subtype_count": explicit_count,
                "default_subtype_count": len(events) - explicit_count,
                "subtype_coverage_rate": _rate(explicit_count, len(events)),
                "boundary": "Subtypes label sourced fixture events for diagnostics; they are not available for negative years or future predictions.",
            }
        )
    return rows


def _industry_event_evidence_summary(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for case in case_scores:
        for event in case.get("events", []):
            evidence = event.get("industry_event_evidence", {})
            if not isinstance(evidence, dict):
                continue
            key = (str(evidence.get("industry", "")), str(event.get("event_topic", "")))
            rows_by_key.setdefault(key, []).append(evidence)

    rows = []
    for (industry, topic), items in sorted(rows_by_key.items()):
        rows.append(
            {
                "industry": industry,
                "event_topic": topic,
                "event_count": len(items),
                "domain_specific_evidence_count": sum(1 for item in items if item.get("has_domain_specific_evidence")),
                "release_marker_count": sum(1 for item in items if item.get("has_release_marker")),
                "award_or_recognition_marker_count": sum(
                    1 for item in items if item.get("has_award_or_recognition_marker")
                ),
                "commercial_or_chart_marker_count": sum(
                    1 for item in items if item.get("has_commercial_or_chart_marker")
                ),
                "media_or_publicity_marker_count": sum(
                    1 for item in items if item.get("has_media_or_publicity_marker")
                ),
                "competition_marker_count": sum(1 for item in items if item.get("has_competition_marker")),
                "industry_project_marker_count": sum(
                    1 for item in items if item.get("has_industry_project_marker")
                ),
                "domain_specific_evidence_rate": _rate(
                    sum(1 for item in items if item.get("has_domain_specific_evidence")),
                    len(items),
                ),
                "boundary": "Industry evidence is fixture-label calibration evidence, not a future prediction feature.",
            }
        )
    return rows


def _industry_event_source_coverage(case_scores: list[dict[str, Any]]) -> dict[str, Any]:
    negative_year_count = sum(len(case.get("negative_samples", [])) for case in case_scores)
    event_count = sum(len(case.get("events", [])) for case in case_scores)
    domain_topic_negative_counts: dict[tuple[str, str], int] = {}
    for case in case_scores:
        domain = str(case.get("case_domain", ""))
        for sample in case.get("negative_samples", []):
            key = (domain, str(sample.get("event_topic", "")))
            domain_topic_negative_counts[key] = domain_topic_negative_counts.get(key, 0) + 1

    required_slices = []
    for (domain, topic), count in sorted(domain_topic_negative_counts.items()):
        if domain in {"影视", "影视武术", "歌手", "体育"} and topic in {
            "career_project",
            "public_fame",
            "sports_peak",
        }:
            required_slices.append(
                {
                    "domain": domain,
                    "event_topic": topic,
                    "negative_year_count": count,
                    "industry_negative_label_count": 0,
                    "industry_negative_label_coverage_rate": 0.0,
                    "needed_to_close": (
                        "Attach reviewed external industry-event records for non-event years, including releases, "
                        "awards, nominations, chart/ranking results, sports titles, and explicit absence where available."
                    ),
                }
            )

    return {
        "status": "needs_external_event_source",
        "positive_event_count": event_count,
        "positive_event_industry_evidence_source": "fixture_event_subtypes",
        "negative_year_count": negative_year_count,
        "industry_negative_label_count": 0,
        "industry_negative_label_coverage_rate": 0.0,
        "required_external_source_families": [
            "film_or_television_release_award_box_office_source",
            "music_release_chart_award_broadcast_source",
            "sports_result_ranking_title_record_source",
        ],
        "provider_contract_required_fields": [
            "case_id",
            "domain",
            "year",
            "event_topic",
            "industry",
            "event_present",
            "event_type",
            "source",
            "source_url",
            "license_or_review",
            "collected_before_rule_change",
        ],
        "required_domain_topic_slices": required_slices,
        "blocking_rule_promotion": True,
        "boundary": (
            "Fixture industry labels cover sourced event years only. Negative-year industry labels require a "
            "separate reviewed event-source provider before fixture-industry candidates can be promoted."
        ),
    }


def _annual_rule_refinement_queue(topic_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for row in topic_summary:
        event_count = int(row.get("event_count", 0))
        strict_precision = float(row.get("strict_exact_precision", 0.0))
        strict_false_positive_rate = float(row.get("strict_false_positive_rate", 0.0))
        if event_count < 3:
            priority = "watch"
        elif strict_precision < 0.1 and strict_false_positive_rate >= 0.1:
            priority = "high"
        elif strict_precision < 0.2 or strict_false_positive_rate >= 0.2:
            priority = "medium"
        else:
            priority = "low"
        candidates.append(
            {
                "event_topic": row["event_topic"],
                "priority": priority,
                "event_count": event_count,
                "eligible_event_count": int(row.get("eligible_event_count", 0)),
                "caution_event_count": int(row.get("caution_event_count", 0)),
                "eligible_event_rate": float(row.get("eligible_event_rate", 0.0)),
                "strict_exact_precision": strict_precision,
                "strict_false_positive_rate": strict_false_positive_rate,
                "recommended_evidence": _recommended_event_evidence(str(row["event_topic"])),
                "reason": _refinement_reason(row, priority),
            }
        )
    priority_rank = {"high": 0, "medium": 1, "low": 2, "watch": 3}
    return sorted(
        candidates,
        key=lambda item: (
            priority_rank.get(str(item["priority"]), 9),
            -float(item["strict_false_positive_rate"]),
            float(item["strict_exact_precision"]),
            str(item["event_topic"]),
        ),
    )


def _annual_rule_variant_sweep(case_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variants: dict[str, dict[str, Any]] = {
        "career_project": {
            "selected": "structured_launch_with_useful_or_natal",
            "rules": {
                "legacy_broad_launch": _variant_career_project_legacy,
                "structured_launch_with_useful_or_natal": _variant_career_project_structured_launch,
                "expression_public_useful": _variant_career_project_expression_public,
            },
        },
        "migration": {
            "selected": "core_double_clash",
            "rules": {
                "legacy_any_clash": _variant_migration_legacy,
                "core_double_clash": _variant_migration_core_double_clash,
                "core_learning_clash": _variant_migration_core_learning_clash,
            },
        },
        "career_power": {
            "selected": "current_role_power",
            "rules": {
                "current_role_power": _variant_career_power_current,
                "role_transition_marker": _variant_career_power_role_transition,
                "authority_peer_resource": _variant_career_power_authority_peer_resource,
                "broad_authority_transition": _variant_career_power_broad_authority,
            },
        },
        "study_exam": {
            "selected": "current_formal_study",
            "rules": {
                "current_formal_study": _variant_study_exam_current,
                "formal_marker_or_natal": _variant_study_exam_marker_or_natal,
                "broad_resource_authority": _variant_study_exam_broad_resource_authority,
            },
        },
    }
    rows = []
    for topic, config in variants.items():
        event_rows = _topic_items(case_scores, topic, "events")
        negative_rows = _topic_items(case_scores, topic, "negative_samples")
        for name, predicate in config["rules"].items():
            exact_hits = sum(1 for item in event_rows if predicate(item))
            false_positives = sum(1 for item in negative_rows if predicate(item))
            rows.append(
                {
                    "event_topic": topic,
                    "variant": name,
                    "selected": name == config["selected"],
                    "event_count": len(event_rows),
                    "negative_year_count": len(negative_rows),
                    "strict_exact_hit_count": exact_hits,
                    "strict_false_positive_count": false_positives,
                    "strict_exact_hit_rate": _rate(exact_hits, len(event_rows)),
                    "strict_exact_precision": _rate(exact_hits, exact_hits + false_positives),
                    "strict_false_positive_rate": _rate(false_positives, len(negative_rows)),
                    "selection_basis": (
                        "Selected variants prioritize precision and lower false positives for strict exact-year claims; "
                        "loose matching remains available for recall diagnostics."
                    ),
                }
            )
    return rows


def _annual_evolution_task_plan(
    topic_summary: list[dict[str, Any]],
    event_subtype_summary: list[dict[str, Any]],
    rule_variant_sweep: list[dict[str, Any]],
    rule_refinement_queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary_by_topic = {str(row["event_topic"]): row for row in topic_summary}
    subtype_by_topic = {str(row["event_topic"]): row for row in event_subtype_summary}
    variants_by_topic: dict[str, list[dict[str, Any]]] = {}
    for row in rule_variant_sweep:
        variants_by_topic.setdefault(str(row["event_topic"]), []).append(row)
    tasks = []
    for queue_item in rule_refinement_queue:
        topic = str(queue_item["event_topic"])
        summary = summary_by_topic.get(topic, {})
        subtype_summary = subtype_by_topic.get(topic, {})
        variants = variants_by_topic.get(topic, [])
        selected = next((row for row in variants if row.get("selected")), None)
        rejected = [row for row in variants if not row.get("selected")]
        strict_precision = float(summary.get("strict_exact_precision", 0.0))
        strict_hit_rate = float(summary.get("strict_exact_hit_rate", 0.0))
        strict_false_positive_rate = float(summary.get("strict_false_positive_rate", 0.0))
        subtype_coverage_rate = float(subtype_summary.get("subtype_coverage_rate", 0.0))
        if subtype_coverage_rate < 0.5 and int(summary.get("event_count", 0)) >= 3:
            task_type = "expand_subtypes"
        elif str(queue_item.get("priority")) == "watch":
            task_type = "monitor"
        elif strict_false_positive_rate >= 0.1:
            task_type = "reduce_false_positive"
        elif strict_hit_rate < 0.1:
            task_type = "add_specific_evidence"
        else:
            task_type = "refine_precision"
        tasks.append(
            {
                "task_id": f"annual-{topic}-{task_type}",
                "event_topic": topic,
                "priority": queue_item.get("priority"),
                "task_type": task_type,
                "event_count": int(summary.get("event_count", 0)),
                "strict_exact_hit_rate": strict_hit_rate,
                "strict_exact_precision": strict_precision,
                "strict_false_positive_rate": strict_false_positive_rate,
                "subtype_coverage_rate": subtype_coverage_rate,
                "default_subtype_count": int(subtype_summary.get("default_subtype_count", 0)),
                "selected_variant": selected.get("variant") if isinstance(selected, dict) else None,
                "selected_variant_metrics": _variant_metric_summary(selected),
                "rejected_variant_metrics": [_variant_metric_summary(row) for row in rejected],
                "next_evidence_to_add": _next_evolution_evidence(topic, task_type, subtype_summary),
                "acceptance_criteria": _evolution_acceptance_criteria(task_type),
                "source": "famous_case_annual_event_calibration",
                "boundary": (
                    "This task plan directs future symbolic-rule work. It is not an instruction to optimize "
                    "predictive-truth claims without a larger reviewed dataset."
                ),
            }
        )
    priority_rank = {"high": 0, "medium": 1, "low": 2, "watch": 3}
    task_rank = {"reduce_false_positive": 0, "add_specific_evidence": 1, "refine_precision": 2, "monitor": 3}
    task_rank["expand_subtypes"] = 0
    return sorted(
        tasks,
        key=lambda item: (
            priority_rank.get(str(item["priority"]), 9),
            task_rank.get(str(item["task_type"]), 9),
            -float(item["strict_false_positive_rate"]),
            float(item["strict_exact_hit_rate"]),
            str(item["event_topic"]),
        ),
    )


def _variant_metric_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    return {
        "variant": row.get("variant"),
        "strict_exact_hit_rate": row.get("strict_exact_hit_rate"),
        "strict_exact_precision": row.get("strict_exact_precision"),
        "strict_false_positive_rate": row.get("strict_false_positive_rate"),
    }


def _next_evolution_evidence(topic: str, task_type: str, subtype_summary: dict[str, Any] | None = None) -> list[str]:
    if task_type == "expand_subtypes":
        default_count = 0
        if isinstance(subtype_summary, dict):
            default_count = int(subtype_summary.get("default_subtype_count", 0))
        return [
            f"replace default subtype labels for {default_count} sourced event years",
            "add domain-specific subtype labels before rule tuning",
            "keep subtype labels out of negative samples and strict predicates",
        ]
    evidence_by_topic = {
        "career_power": [
            "title-or-command-transition marker separated from ordinary authority pressure",
            "case-source event subtype: appointment, command seizure, institutional promotion, or loss of office",
            "role-axis branch interaction beyond broad authority ten-god",
        ],
        "study_exam": [
            "formal exam/certificate marker separated from general learning years",
            "school-age or credential-stage context",
            "resource-authority chain with event subtype: admission, graduation, certificate, or publication",
        ],
        "public_fame": [
            "public-release or award marker separated from generic output visibility",
            "domain subtype: film release, championship, publication, chart success, or prize",
            "visibility marker that requires output plus external recognition",
        ],
        "relationship": [
            "relationship subtype marker: marriage, divorce, public partner, or family disruption",
            "day-branch or spouse-axis activation",
            "peer/wealth signal filtered by public relationship evidence",
        ],
        "career_project": [
            "project subtype marker: debut, publication, company founding, major role, or landmark work",
            "launch marker that requires external artifact rather than generic output",
            "domain-specific output channel for sports, film, music, science, and politics",
        ],
    }
    fallback = [
        "event subtype labels extracted before rule tuning",
        "branch-interaction feature specific to the event domain",
        "negative-year contrast examples for the same case and topic",
    ]
    if task_type == "monitor":
        return ["collect more sourced cases before changing strict rules"]
    return evidence_by_topic.get(topic, fallback)


def _evolution_acceptance_criteria(task_type: str) -> list[str]:
    if task_type == "expand_subtypes":
        return [
            "subtype_coverage_rate improves for the event topic",
            "event_subtype_summary records explicit and default subtype counts",
            "strict prediction metrics remain unchanged unless rules are separately modified",
        ]
    if task_type == "reduce_false_positive":
        return [
            "strict_false_positive_rate decreases versus selected baseline",
            "strict_exact_precision does not decrease",
            "rule_variant_sweep records baseline and candidate metrics",
        ]
    if task_type == "add_specific_evidence":
        return [
            "new evidence field is present in event_evidence",
            "strict_false_positive_rate does not increase versus selected baseline",
            "strict_exact_hit_rate improves or rejected candidate is recorded with metrics",
        ]
    if task_type == "refine_precision":
        return [
            "strict_exact_precision improves versus selected baseline",
            "strict_false_positive_rate does not increase materially",
            "topic_summary and rule_variant_sweep remain deterministic",
        ]
    return [
        "case_count or event_count increases",
        "source provenance is recorded before changing rules",
        "existing selected variant remains stable until new evidence is available",
    ]


def _topic_items(case_scores: list[dict[str, Any]], topic: str, key: str) -> list[dict[str, Any]]:
    return [
        item
        for case in case_scores
        for item in case.get(key, [])
        if item.get("event_topic") == topic
    ]


def _domain_topic_items(case_scores: list[dict[str, Any]], domain: str, topic: str, key: str) -> list[dict[str, Any]]:
    return [
        item
        for case in case_scores
        if str(case.get("case_domain")) == domain
        for item in case.get(key, [])
        if item.get("event_topic") == topic
    ]


def _variant_evidence(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("event_evidence", {})
    return evidence if isinstance(evidence, dict) else {}


def _variant_industry_evidence(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("industry_event_evidence", {})
    return evidence if isinstance(evidence, dict) else {}


def _variant_category(item: dict[str, Any]) -> str:
    return str(item.get("annual_category", ""))


def _variant_intensity(item: dict[str, Any]) -> str:
    return str(item.get("annual_intensity", ""))


def _variant_useful_or_pressure(evidence: dict[str, Any]) -> bool:
    return str(evidence.get("useful_state", "")) in {"useful_element_activated", "dominant_element_reinforced"}


def _variant_major_or_natal(evidence: dict[str, Any]) -> bool:
    return bool(evidence.get("major_luck_active")) or bool(evidence.get("natal_activation"))


def _variant_markers(evidence: dict[str, Any]) -> dict[str, Any]:
    markers = evidence.get("event_markers", {})
    return markers if isinstance(markers, dict) else {}


def _variant_current_strict(item: dict[str, Any]) -> bool:
    return bool(item.get("strict_exact_match") or item.get("strict_false_positive"))


def _variant_industry_fame_marker(item: dict[str, Any]) -> bool:
    evidence = _variant_industry_evidence(item)
    return bool(
        evidence.get("has_film_fame_evidence")
        or evidence.get("has_music_fame_evidence")
        or (
            evidence.get("event_topic") == "public_fame"
            and evidence.get("has_domain_specific_evidence")
        )
    )


def _variant_industry_project_marker(item: dict[str, Any]) -> bool:
    evidence = _variant_industry_evidence(item)
    return bool(
        evidence.get("has_film_project_evidence")
        or evidence.get("has_music_project_evidence")
        or (
            evidence.get("event_topic") == "career_project"
            and evidence.get("has_industry_project_marker")
        )
    )


def _variant_industry_sports_peak_marker(item: dict[str, Any]) -> bool:
    evidence = _variant_industry_evidence(item)
    return bool(evidence.get("has_sports_peak_evidence"))


def _variant_public_fame_visibility_support(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) == "expression"
        and bool(evidence.get("has_expression"))
        and bool(_variant_markers(evidence).get("public_visibility"))
        and (_variant_useful_or_pressure(evidence) or bool(evidence.get("natal_activation")))
    )


def _variant_public_fame_visibility_major_luck(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) == "expression"
        and bool(evidence.get("has_expression"))
        and bool(_variant_markers(evidence).get("public_visibility"))
        and (_variant_useful_or_pressure(evidence) or _variant_major_or_natal(evidence))
    )


def _variant_project_launch_or_visibility_support(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    markers = _variant_markers(evidence)
    return (
        _variant_category(item) in {"expression", "authority", "wealth"}
        and (bool(markers.get("career_launch")) or bool(markers.get("public_visibility")))
        and (_variant_useful_or_pressure(evidence) or bool(evidence.get("natal_activation")))
    )


def _variant_project_channel_major_luck(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    markers = _variant_markers(evidence)
    return (
        _variant_category(item) in {"expression", "authority", "wealth"}
        and int(evidence.get("career_signal_strength", 0)) >= 1
        and (bool(markers.get("career_launch")) or bool(markers.get("public_visibility")))
        and _variant_major_or_natal(evidence)
    )


def _variant_sports_peak_constructive_current(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"expression", "authority"}
        and _variant_intensity(item) in {"constructive", "active"}
        and (bool(evidence.get("has_expression")) or bool(evidence.get("has_authority")))
    )


def _variant_sports_peak_major_or_natal(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"expression", "authority"}
        and (bool(evidence.get("has_expression")) or bool(evidence.get("has_authority")))
        and _variant_major_or_natal(evidence)
    )


def _variant_core_clash_count(evidence: dict[str, Any]) -> int:
    branch_clashes = evidence.get("branch_clashes", [])
    return _core_branch_clash_count(branch_clashes if isinstance(branch_clashes, list) else [])


def _variant_career_project_legacy(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"expression", "authority", "wealth"}
        and int(evidence.get("career_signal_strength", 0)) >= 1
        and bool(evidence.get("career_launch_signal"))
        and (_variant_useful_or_pressure(evidence) or _variant_major_or_natal(evidence))
    )


def _variant_career_project_structured_launch(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"expression", "authority", "wealth"}
        and bool(_variant_markers(evidence).get("career_launch"))
        and (_variant_useful_or_pressure(evidence) or bool(evidence.get("natal_activation")))
    )


def _variant_career_project_expression_public(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) == "expression"
        and bool(_variant_markers(evidence).get("public_visibility"))
        and (_variant_useful_or_pressure(evidence) or bool(evidence.get("natal_activation")))
    )


def _variant_migration_legacy(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"learning", "friends"}
        and bool(evidence.get("movement_signal"))
        and (
            _variant_intensity(item) == "high-volatility"
            or _variant_useful_or_pressure(evidence)
            or _variant_major_or_natal(evidence)
        )
    )


def _variant_migration_core_double_clash(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"learning", "friends", "wealth", "expression"}
        and bool(evidence.get("movement_signal"))
        and _variant_core_clash_count(evidence) >= 2
        and _variant_major_or_natal(evidence)
    )


def _variant_migration_core_learning_clash(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) == "learning"
        and bool(evidence.get("movement_signal"))
        and _variant_core_clash_count(evidence) >= 1
        and _variant_major_or_natal(evidence)
    )


def _variant_career_power_current(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) == "authority"
        and bool(evidence.get("has_authority"))
        and bool(evidence.get("role_power_signal"))
        and (_variant_useful_or_pressure(evidence) or _variant_major_or_natal(evidence))
    )


def _variant_career_power_authority_peer_resource(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    ten_gods = set(evidence.get("ten_gods", []))
    return (
        bool(evidence.get("has_authority"))
        and bool({"peer", "resource"} & ten_gods)
        and _variant_major_or_natal(evidence)
    )


def _variant_career_power_role_transition(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        bool(evidence.get("role_transition_signal"))
        and _variant_major_or_natal(evidence)
    )


def _variant_career_power_broad_authority(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        bool(evidence.get("has_authority"))
        and _variant_category(item) in {"friends", "wealth", "learning", "authority"}
        and _variant_major_or_natal(evidence)
    )


def _variant_study_exam_current(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"learning", "authority"}
        and (bool(evidence.get("has_resource")) or bool(evidence.get("has_authority")))
        and (_variant_intensity(item) in {"constructive", "active"} or _variant_useful_or_pressure(evidence))
    )


def _variant_study_exam_marker_or_natal(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        (bool(_variant_markers(evidence).get("study_exam")) or bool(evidence.get("natal_activation")))
        and (
            bool(evidence.get("has_resource"))
            or bool(evidence.get("has_authority"))
            or bool(evidence.get("has_wealth"))
        )
    )


def _variant_study_exam_broad_resource_authority(item: dict[str, Any]) -> bool:
    evidence = _variant_evidence(item)
    return (
        _variant_category(item) in {"learning", "authority", "friends"}
        and (bool(evidence.get("has_resource")) or bool(evidence.get("has_authority")))
        and _variant_major_or_natal(evidence)
    )


def _recommended_event_evidence(topic: str) -> list[str]:
    recommendations = {
        "public_fame": [
            "require expression ten-god in annual stem or branch",
            "require useful-element activation or major-luck support",
            "check output-to-public-image chain before accepting fame signal",
        ],
        "career_project": [
            "require career-domain ten-god: expression, authority, or wealth",
            "require active major-luck continuation or natal pillar activation",
            "separate project launch from generic busy/output years",
        ],
        "relationship": [
            "require spouse/relationship palace or day-branch activation",
            "require relationship-domain ten-god plus branch interaction",
            "separate public relationship events from generic peer/wealth signals",
        ],
        "sports_peak": [
            "require performance/output signal plus constructive intensity",
            "require low volatility unless the event is an injury comeback",
            "separate championship peak from generic fame visibility",
        ],
        "health_risk": [
            "require volatility plus dominant-element pressure",
            "add body-system or seasonal-climate evidence before severe health wording",
            "separate illness/death labels from general fatigue pressure",
        ],
        "study_exam": [
            "require learning/resource or authority ten-god",
            "require constructive intensity or useful-element support",
            "separate formal exam/certificate from generic planning years",
        ],
        "migration": [
            "require branch clash/movement signal or residence-axis activation",
            "require learning/resource or peer-network transition context",
        ],
        "transition": [
            "require major-luck boundary, role change, or branch clash",
            "separate retirement/exit from generic active change years",
        ],
        "public_controversy": [
            "require authority-expression conflict plus volatility",
            "separate controversy from ordinary visibility or pressure",
        ],
    }
    return recommendations.get(
        topic,
        [
            "add event-specific ten-god evidence",
            "add branch interaction evidence",
            "require major-luck or natal-pillar activation before exact-year claims",
        ],
    )


def _refinement_reason(row: dict[str, Any], priority: str) -> str:
    return (
        f"{row['event_topic']} priority={priority}; "
        f"events={row['event_count']}, "
        f"eligible_event_rate={row.get('eligible_event_rate', 0.0)}, "
        f"strict_precision={row['strict_exact_precision']}, "
        f"strict_false_positive_rate={row['strict_false_positive_rate']}."
    )


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 3)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
