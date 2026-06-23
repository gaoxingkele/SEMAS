"""Tests for the optional Qi Men JSON-CLI provider."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.qimen_cli_provider import QimenJsonCliProvider
from examples.mingli_5agents.tools.qimen_deep_analysis import build_qimen_deep_analysis
from examples.mingli_5agents.tools.qimen_ju import build_qimen_chart


def test_qimen_json_cli_provider_maps_professional_payload(tmp_path: Path):
    script = tmp_path / "fake_qimen_provider.py"
    script.write_text(
        """
import json
import sys

payload = json.loads(sys.stdin.read())
names = ["Kan", "Kun", "Zhen", "Xun", "Center", "Qian", "Dui", "Gen", "Li"]
palaces = [
    {
        "number": idx + 1,
        "name": name,
        "direction": "provider",
        "element": "provider",
        "door": "Open" if idx == 0 else "Rest",
        "star": "Tianxin" if idx == 0 else "Tianfu",
        "spirit": "Nine Heaven" if idx == 0 else "Six Harmony",
        "heaven_stem": "Jia",
        "earth_stem": "Yi",
        "theme": f"provider theme {name}",
        "judgment": "verified",
    }
    for idx, name in enumerate(names)
]
print(json.dumps({
    "protocol": payload.get("protocol"),
    "duty_door": "Open",
    "duty_star": "Tianxin",
    "spirit": "Nine Heaven",
    "pattern": "verified qimen cli fixture",
    "calculation_basis": {
        "provider": "fake qimen provider",
        "rule_set": "fake_qimen_rules",
        "rule_set_version": "fixture-1.0",
        "rule_source": "test fixture",
        "rule_source_sha256": "0" * 64,
        "license_or_review": "test fixture",
        "calculation_scope": "nine palaces, duty door, duty star, spirits, useful gods, annual timing",
    },
    "palaces": palaces,
    "useful_gods": {
        "career": {"palace": "Kan", "door": "Open", "star": "Tianxin", "spirit": "Nine Heaven", "judgment": "verified"},
        "wealth": {"palace": "Kun", "door": "Rest", "star": "Tianfu", "spirit": "Six Harmony", "judgment": "verified"},
        "relationship": {"palace": "Kun", "door": "Rest", "star": "Tianfu", "spirit": "Six Harmony", "judgment": "verified"},
        "study": {"palace": "Kan", "door": "Open", "star": "Tianxin", "spirit": "Nine Heaven", "judgment": "verified"},
        "health": {"palace": "Kun", "door": "Rest", "star": "Tianfu", "spirit": "Six Harmony", "judgment": "verified"}
    },
    "annual_timing": [{"year": 2026, "palace": "Kan", "door": "Open", "judgment": "verified"}]
}))
""".strip(),
        encoding="utf-8",
    )
    birth = normalize_birth_input(
        {
            "name": "Qimen CLI Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    fallback = build_qimen_chart(birth)
    chart = QimenJsonCliProvider(command=[sys.executable, str(script)]).build_chart(birth, fallback)
    deep = build_qimen_deep_analysis(chart, birth)

    assert chart["provider_quality"] == "qimen_json_cli"
    assert chart["duty_door"] == "Open"
    assert chart["duty_star"] == "Tianxin"
    assert chart["spirit"] == "Nine Heaven"
    assert chart["raw_provider_output"]["pattern"] == "verified qimen cli fixture"
    assert chart["raw_provider_output"]["calculation_basis"]["rule_set"] == "fake_qimen_rules"
    assert chart["context"]["domain_provider_source"] == "json_cli"
    assert chart["provider_request_receipt"]["domain"] == "qimen"
    assert chart["provider_request_receipt"]["protocol_echo_matches"] is True
    assert len(chart["provider_request_receipt"]["birth_profile_sha256"]) == 64
    assert len(chart["provider_request_receipt"]["stdout_sha256"]) == 64
    assert chart["context"]["provider_request_receipt"]["sha256"] == chart["provider_request_receipt"]["sha256"]
    assert deep["provider_quality"] == "qimen_json_cli"
    assert deep["palaces"][0]["name"] == "Kan"
    assert deep["palaces"][0]["judgment"] == "verified"
    assert deep["useful_gods"]["career"]["palace"] == "Kan"
    assert deep["annual_timing"][0]["year"] == 2026
