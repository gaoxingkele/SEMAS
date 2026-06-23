"""Tests for the optional Zi Wei JSON-CLI provider."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.ziwei_cli_provider import ZiweiJsonCliProvider
from examples.mingli_5agents.tools.ziwei_deep_analysis import build_ziwei_deep_analysis
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart


def test_ziwei_json_cli_provider_maps_professional_payload(tmp_path: Path):
    script = tmp_path / "fake_ziwei_provider.py"
    script.write_text(
        """
import json
import sys

payload = json.loads(sys.stdin.read())
palaces = [
    {
        "index": idx,
        "name": name,
        "theme": f"provider theme {name}",
        "primary_stars": ["Ziwei", "Wuqu"] if name == "Career" else ["Tianji"],
        "auxiliary_stars": [],
        "markers": ["ming"] if name == "Career" else [],
        "strength": "provider",
    }
    for idx, name in enumerate(payload["fallback"].get("palace_order") or [
        "Ming", "Siblings", "Spouse", "Children", "Wealth", "Health",
        "Travel", "Friends", "Career", "Property", "Fortune", "Parents",
    ])
]
print(json.dumps({
    "protocol": payload.get("protocol"),
    "ming_palace": "Career",
    "body_palace": "Wealth",
    "major_stars": ["Ziwei", "Wuqu"],
    "transformations": {"lu": "Wuqu", "quan": "Ziwei", "ke": "Tianji", "ji": "Taiyin"},
    "calculation_basis": {
        "provider": "fake ziwei provider",
        "rule_set": "fake_ziwei_rules",
        "rule_set_version": "fixture-1.0",
        "rule_source": "test fixture",
        "rule_source_sha256": "0" * 64,
        "license_or_review": "test fixture",
        "calculation_scope": "twelve palaces, major stars, sihua, major limits, annual activation",
    },
    "palaces": palaces,
    "major_limits": [{"start_year": 1990, "end_year": 1999, "palace": "Career"}],
    "annual_activation": [{"year": 2026, "palace": "Career"}],
}))
""".strip(),
        encoding="utf-8",
    )
    birth = normalize_birth_input(
        {
            "name": "Ziwei CLI Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    fallback = build_ziwei_chart(birth)
    chart = ZiweiJsonCliProvider(command=[sys.executable, str(script)]).build_chart(birth, fallback)
    deep = build_ziwei_deep_analysis(chart, birth)

    assert chart["provider_quality"] == "ziwei_json_cli"
    assert chart["ming_palace"] == "Career"
    assert chart["body_palace"] == "Wealth"
    assert chart["raw_provider_output"]["major_stars"] == ["Ziwei", "Wuqu"]
    assert chart["raw_provider_output"]["calculation_basis"]["rule_set"] == "fake_ziwei_rules"
    assert chart["context"]["domain_provider_source"] == "json_cli"
    assert chart["provider_request_receipt"]["domain"] == "ziwei"
    assert chart["provider_request_receipt"]["protocol_echo_matches"] is True
    assert len(chart["provider_request_receipt"]["birth_profile_sha256"]) == 64
    assert len(chart["provider_request_receipt"]["stdin_sha256"]) == 64
    assert chart["context"]["provider_request_receipt"]["sha256"] == chart["provider_request_receipt"]["sha256"]
    assert deep["provider_quality"] == "ziwei_json_cli"
    assert deep["palaces"][8]["name"] == "Career"
    assert deep["palaces"][8]["primary_stars"] == ["Ziwei", "Wuqu"]
    assert deep["major_limits"][0]["palace"] == "Career"
    assert deep["annual_activation"][0]["year"] == 2026
