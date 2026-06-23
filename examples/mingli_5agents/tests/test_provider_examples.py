"""Tests for bundled JSON-CLI provider examples."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from examples.mingli_5agents.provider_checks import bundled_provider_example_smoke, provider_health_checks
from examples.mingli_5agents.api_core import (
    provider_certification,
    provider_certification_drift,
    provider_certification_ledger,
    provider_onboarding,
)
from examples.mingli_5agents.tools.astrology_chart import build_astrology_chart
from examples.mingli_5agents.tools.astrology_cli_provider import AstrologyJsonCliProvider
from examples.mingli_5agents.tools.auspicious_calendar import build_auspicious_calendar
from examples.mingli_5agents.tools.lunar_date import normalize_birth_input
from examples.mingli_5agents.tools.qimen_cli_provider import QimenJsonCliProvider
from examples.mingli_5agents.tools.qimen_ju import build_qimen_chart
from examples.mingli_5agents.tools.ziwei_cli_provider import ZiweiJsonCliProvider
from examples.mingli_5agents.tools.ziwei_pai_pan import build_ziwei_chart
from examples.mingli_5agents.tools.xuanze_cli_provider import XuanzeJsonCliProvider


ROOT = Path(__file__).resolve().parents[1]


def test_bundled_json_cli_examples_pass_live_smoke(monkeypatch):
    monkeypatch.setenv(
        "SEMAS_ZIWEI_CLI",
        f"{sys.executable} {ROOT / 'providers' / 'ziwei_json_cli_example.py'}",
    )
    monkeypatch.setenv(
        "SEMAS_QIMEN_CLI",
        f"{sys.executable} {ROOT / 'providers' / 'qimen_json_cli_example.py'}",
    )
    monkeypatch.setenv(
        "SEMAS_ASTROLOGY_CLI",
        f"{sys.executable} {ROOT / 'providers' / 'astrology_json_cli_example.py'}",
    )
    monkeypatch.setenv(
        "SEMAS_XUANZE_CLI",
        f"{sys.executable} {ROOT / 'providers' / 'xuanze_json_cli_example.py'}",
    )

    result = provider_health_checks(live=True, profile="production")

    assert result["profile_readiness"]["status"] == "production_blocked"
    assert result["profile_readiness"]["ready"] is False
    assert result["integration_plan"]["status"] == "production_blocked"
    assert result["integration_plan"]["production_ready"] is False
    assert result["integration_plan"]["ready_targets"] < result["integration_plan"]["total_targets"]
    assert {
        "ziwei_professional_engine",
        "qimen_professional_engine",
        "astrology_ephemeris_engine",
        "xuanze_almanac_engine",
    }.issubset(set(result["integration_plan"]["blocked_targets"]))
    assert result["checks"]["ziwei_json_cli"]["live_check"]["passed"] is True
    assert result["checks"]["qimen_json_cli"]["live_check"]["passed"] is True
    assert result["checks"]["astrology_json_cli"]["live_check"]["passed"] is True
    assert result["checks"]["xuanze_json_cli"]["live_check"]["passed"] is True
    assert result["checks"]["ziwei_json_cli"]["command_is_bundled_example"] is True
    assert result["checks"]["ziwei_json_cli"]["production_credential_passed"] is False
    assert "protocol examples" in result["checks"]["ziwei_json_cli"]["production_blocker"]


def test_bundled_provider_example_smoke_emits_non_production_receipt(tmp_path):
    result = bundled_provider_example_smoke(tmp_path / "repo")
    repeat = bundled_provider_example_smoke(tmp_path / "repo")

    assert result["status"] == "passed"
    assert result["production_certification_allowed"] is False
    assert "cannot certify production providers" in result["policy"]
    assert set(result["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert all(item["live_passed"] is True for item in result["domains"].values())
    assert all(item["contract_valid"] is True for item in result["domains"].values())
    assert all(item["protocol_identity_matches"] is True for item in result["domains"].values())
    assert all(item["provider_request_receipt_valid"] is True for item in result["domains"].values())
    assert all(item["command_is_bundled_example"] is True for item in result["domains"].values())
    assert all(item["production_credential_passed"] is False for item in result["domains"].values())
    assert len(result["example_provider_receipt"]["sha256"]) == 64
    assert repeat["example_provider_receipt"]["sha256"] == result["example_provider_receipt"]["sha256"]
    assert result["example_provider_receipt"]["material"]["passed_domain_count"] == 4


def test_provider_onboarding_combines_protocol_examples_and_ledger_gaps(tmp_path):
    result = provider_onboarding(tmp_path / "repo")

    assert result["status"] == "actions_required"
    assert set(result["domains"]) == {"ziwei", "qimen", "astrology", "xuanze"}
    assert result["provider_onboarding_receipt"]["material"]["domain_count"] == 4
    assert result["provider_onboarding_receipt"]["material"]["ready_domain_count"] == 0
    assert result["provider_onboarding_receipt"]["material"]["example_provider_receipt_sha256"] == result[
        "example_provider_receipt"
    ]["sha256"]
    assert len(result["provider_onboarding_receipt"]["sha256"]) == 64
    assert all("certified_provider_ledger_record" in item["missing_evidence"] for item in result["domains"].values())
    assert all(item["bundled_example_smoke"]["live_passed"] is True for item in result["domains"].values())
    assert all(
        item["bundled_example_smoke"]["production_certification_allowed"] is False
        for item in result["domains"].values()
    )


def test_provider_ledger_exposes_configuration_guidance(tmp_path):
    result = provider_certification_ledger(tmp_path / "repo")
    guidance = result["configuration_guidance"]

    assert result["ledger"]["exists"] is False
    assert guidance["configured"] is False
    assert guidance["ledger_path"].endswith("provider_certification_ledger.json")
    assert guidance["required_domains"] == ["astrology", "qimen", "xuanze", "ziwei"]
    assert guidance["missing_domains"] == ["astrology", "qimen", "xuanze", "ziwei"]
    assert guidance["domain_env_vars"]["ziwei"] == "SEMAS_ZIWEI_CLI"
    assert guidance["domain_provenance_env_vars"]["qimen"] == "SEMAS_QIMEN_PROVIDER_PROVENANCE"
    assert len(guidance["certification_commands"]) == 4
    assert all("certify-provider" in command and "--record" in command for command in guidance["certification_commands"])
    assert len(guidance["drift_commands"]) == 4
    assert all("provider-drift --domain" in command for command in guidance["drift_commands"])
    assert "provider-onboarding" in guidance["provider_onboarding_command"]
    assert "provider-ledger" in guidance["provider_ledger_command"]
    assert "production-readiness --live" in guidance["production_readiness_command"]
    assert guidance["http_query"] == "GET /provider-ledger"
    assert "must not be recorded as production certifications" in guidance["policy"]


def test_provider_drift_exposes_resolution_guidance(tmp_path):
    result = provider_certification_drift(tmp_path / "repo", domain="ziwei")
    guidance = result["resolution_guidance"]

    assert result["drift"]["passed"] is False
    assert guidance["passed"] is False
    assert guidance["status"] == "drift_detected"
    assert guidance["checked_domains"] == ["ziwei"]
    assert len(guidance["recertification_commands"]) == 1
    assert "certify-provider ziwei" in guidance["recertification_commands"][0]
    assert "--record" in guidance["recertification_commands"][0]
    assert guidance["drift_commands"] == [
        f"python -m examples.mingli_5agents.cli --repo {tmp_path / 'repo'} provider-drift --domain ziwei"
    ]
    assert "provider-ledger" in guidance["provider_ledger_command"]
    assert "provider-onboarding" in guidance["provider_onboarding_command"]
    assert "production-readiness --live" in guidance["production_readiness_command"]
    assert guidance["http_query"] == "GET /provider-drift?domain=ziwei"
    assert guidance["blocking_failures"] == ["ziwei has no recorded certification receipt"]
    assert "Do not use bundled protocol examples" in guidance["policy"]


def test_provider_certification_exposes_resolution_guidance_for_blocked_record(tmp_path):
    command = f"{sys.executable} {ROOT / 'providers' / 'ziwei_json_cli_example.py'}"
    result = provider_certification(
        tmp_path / "repo",
        "ziwei",
        command=command,
        provenance="provider=example; version=0; source=test; license_or_review=fixture",
        record=True,
    )
    guidance = result["resolution_guidance"]

    assert result["certified"] is False
    assert result["ledger_record_requested"] is True
    assert result["ledger_recorded"] is False
    assert result["ledger_record_blocker"] == "only certified provider results can be recorded"
    assert guidance["certified"] is False
    assert guidance["ledger_record_requested"] is True
    assert guidance["ledger_recorded"] is False
    assert guidance["ledger_record_blocker"] == result["ledger_record_blocker"]
    assert guidance["domain"] == "ziwei"
    assert guidance["env_var"] == "SEMAS_ZIWEI_CLI"
    assert guidance["provenance_env_var"] == "SEMAS_ZIWEI_PROVIDER_PROVENANCE"
    assert guidance["command_is_bundled_example"] is True
    assert any("Bundled protocol examples" in item for item in guidance["blockers"])
    assert any("Replace bundled protocol examples" in item for item in guidance["next_actions"])
    assert "certify-provider ziwei" in guidance["recertification_command"]
    assert "--record" in guidance["recertification_command"]
    assert "provider-drift --domain ziwei" in guidance["drift_command"]
    assert "provider-ledger" in guidance["provider_ledger_command"]
    assert "provider-onboarding" in guidance["provider_onboarding_command"]
    assert "production-readiness --live" in guidance["production_readiness_command"]
    assert "Only certified" in guidance["record_policy"]


def test_bundled_json_cli_examples_map_into_charts():
    birth = normalize_birth_input(
        {
            "name": "Example Provider Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
        }
    )
    ziwei = ZiweiJsonCliProvider(
        command=[sys.executable, os.fspath(ROOT / "providers" / "ziwei_json_cli_example.py")]
    ).build_chart(birth, build_ziwei_chart(birth))
    qimen = QimenJsonCliProvider(
        command=[sys.executable, os.fspath(ROOT / "providers" / "qimen_json_cli_example.py")]
    ).build_chart(birth, build_qimen_chart(birth))
    astrology = AstrologyJsonCliProvider(
        command=[sys.executable, os.fspath(ROOT / "providers" / "astrology_json_cli_example.py")]
    ).build_chart(birth, build_astrology_chart(birth))
    xuanze = XuanzeJsonCliProvider(
        command=[sys.executable, os.fspath(ROOT / "providers" / "xuanze_json_cli_example.py")]
    ).build_calendar(birth, build_auspicious_calendar(birth, start_date="2026-06-21", end_date="2026-06-23"))

    assert ziwei["provider_quality"] == "ziwei_json_cli"
    assert ziwei["provider_palaces"][8]["name"] == "Career"
    assert qimen["provider_quality"] == "qimen_json_cli"
    assert qimen["provider_palaces"][0]["name"] == "Kan"
    assert astrology["provider_quality"] == "astrology_json_cli"
    assert astrology["ephemeris_planets"][0]["name"] == "Sun"
    assert xuanze["provider_quality"] == "xuanze_json_cli"
    assert xuanze["rows"][0]["rating"] == "favorable"
