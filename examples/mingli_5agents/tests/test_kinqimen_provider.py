"""Tests for the optional kinqimen Qi Men provider adapter."""

from __future__ import annotations

from examples.mingli_5agents.tools.kinqimen_provider import KinqimenProvider
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.qimen_deep_analysis import build_qimen_deep_analysis
from examples.mingli_5agents.tools.qimen_ju import build_qimen_chart


def test_kinqimen_provider_preserves_raw_plate_and_maps_key_fields():
    birth = normalize_birth_input(
        {
            "name": "Kinqimen Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    fallback = build_qimen_chart(birth)
    chart = KinqimenProvider(qimen_class=FakeQimen).build_chart(birth, fallback)
    deep = build_qimen_deep_analysis(chart, birth)

    assert chart["provider"] == "kinqimen"
    assert chart["provider_quality"] == "kinqimen"
    assert chart["duty_door"] == "Open"
    assert chart["duty_star"] == "Tianxin"
    assert chart["spirit"] == "Nine Heaven"
    assert chart["raw_provider_output"]["pattern"] == "verified kinqimen fixture"
    assert chart["context"]["domain_provider_source"] == "kinqimen"
    assert deep["provider_quality"] == "kinqimen"
    assert len(deep["palaces"]) == 9


class FakeQimen:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int):
        self.values = (year, month, day, hour, minute)

    def pan(self, option: int):
        return {
            "pattern": "verified kinqimen fixture",
            "door": {"Kan": "Open", "Kun": "Rest"},
            "star": {"Kan": "Tianxin", "Kun": "Tianfu"},
            "spirit": {"Kan": "Nine Heaven", "Kun": "Six Harmony"},
            "zhifu": {"star": "Tianxin", "palace": "Kan", "option": option},
        }
