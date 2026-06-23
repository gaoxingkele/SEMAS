"""Tests for the optional xuanze JSON-CLI provider."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from examples.mingli_5agents.tools.auspicious_calendar import build_auspicious_calendar
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.xuanze_cli_provider import XuanzeJsonCliProvider


def test_xuanze_json_cli_provider_maps_tongshu_payload(tmp_path: Path):
    script = tmp_path / "fake_xuanze_provider.py"
    script.write_text(
        """
import json
import sys

payload = json.loads(sys.stdin.read())
rows = []
for row in payload["fallback"]["rows"]:
    rows.append({
        **row,
        "twelve_officer": "Open",
        "twenty_eight_mansion": "Well",
        "huangdao": True,
        "rating": "favorable",
        "suitable": ["verified meeting"],
        "avoid": ["verified avoid"],
        "risk_notes": ["verified caution"],
    })
print(json.dumps({
    "protocol": payload.get("protocol"),
    "basis": {
        "provider": "verified_tongshu",
        "provider_quality": "verified_fixture",
        "rule_set": "verified_tongshu_rules",
        "rule_table_source": "reviewed test table",
        "rule_table_version": "fixture-1.0",
        "rule_table_sha256": "1" * 64,
        "license_or_review": "unit test review",
        "calculation_scope": "twelve officers, twenty-eight mansions, huangdao rating, recommended hours"
    },
    "rows": rows,
    "summary": {"favorable_dates": [row["date"] for row in rows], "cautious_dates": [], "best_date": rows[0]["date"]},
}))
""".strip(),
        encoding="utf-8",
    )
    birth = normalize_birth_input(
        {
            "name": "Xuanze CLI Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    fallback = build_auspicious_calendar(birth, start_date="2026-06-21", end_date="2026-06-23")
    calendar = XuanzeJsonCliProvider(command=[sys.executable, str(script)]).build_calendar(birth, fallback)

    assert calendar["provider_quality"] == "xuanze_json_cli"
    assert calendar["basis"]["provider"] == "xuanze_json_cli"
    assert calendar["basis"]["provider_quality"] == "xuanze_json_cli"
    assert calendar["rows"][0]["twelve_officer"] == "Open"
    assert calendar["rows"][0]["rating"] == "favorable"
    assert calendar["summary"]["best_date"] == "2026-06-21"
    assert calendar["raw_provider_output"]["basis"]["provider"] == "verified_tongshu"
    assert calendar["raw_provider_output"]["basis"]["license_or_review"] == "unit test review"
    assert calendar["provider_request_receipt"]["domain"] == "xuanze"
    assert calendar["provider_request_receipt"]["protocol_echo_matches"] is True
    assert len(calendar["provider_request_receipt"]["birth_profile_sha256"]) == 64
    assert len(calendar["provider_request_receipt"]["sha256"]) == 64
    assert calendar["basis"]["provider_request_receipt"]["sha256"] == calendar["provider_request_receipt"]["sha256"]
    assert calendar["provider_quality_analysis"]["provider_quality"] == "xuanze_json_cli"
    assert {item["method"] for item in calendar["method_matrix"]} == {
        "twelve_officer",
        "twenty_eight_mansion",
        "huangdao_rating",
        "recommended_hours",
        "risk_boundary",
        "provider_quality",
    }


def test_external_xuanze_payload_overlays_calendar_contract():
    birth = normalize_birth_input(
        {
            "name": "External Xuanze Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "professional_charts": {
                "xuanze": {
                    "source": "fixture_verified_tongshu",
                    "version": "fixture-1.0",
                    "license_or_review": "reviewed test fixture",
                    "basis": {"rule_set": "fixture_tongshu_rules"},
                    "rows": [
                        {
                            "date": "2026-06-21",
                            "weekday": "Sunday",
                            "ganzhi": "JiaZi",
                            "solar_term": "Summer Solstice",
                            "twelve_officer": "Open",
                            "twenty_eight_mansion": "Well",
                            "huangdao": True,
                            "rating": "favorable",
                            "suitable": ["verified opening"],
                            "avoid": ["verified avoid"],
                            "recommended_hours": [{"start": "09:00", "end": "10:59", "branch": "Si", "element": "Fire"}],
                            "risk_notes": ["verified caution"],
                        }
                    ],
                    "summary": {
                        "favorable_dates": ["2026-06-21"],
                        "cautious_dates": [],
                        "best_date": "2026-06-21",
                    },
                }
            },
        }
    )

    calendar = build_auspicious_calendar(birth, start_date="2026-06-21", end_date="2026-06-21")

    assert calendar["provider"] == "external_structured"
    assert calendar["provider_quality"] == "external_xuanze"
    assert calendar["basis"]["provider"] == "external_structured"
    assert calendar["basis"]["provider_quality"] == "external_xuanze"
    assert calendar["basis"]["provider_source"] == "fixture_verified_tongshu"
    assert calendar["basis"]["provider_provenance"]["valid"] is True
    assert calendar["rows"][0]["suitable"] == ["verified opening"]
    assert calendar["summary"]["best_date"] == "2026-06-21"
    assert calendar["provider_quality_analysis"]["provider_quality"] == "external_xuanze"
    assert calendar["method_matrix"]
