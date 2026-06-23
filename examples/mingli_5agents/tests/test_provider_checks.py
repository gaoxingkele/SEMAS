"""Tests for optional provider readiness checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from examples.mingli_5agents.api_core import provider_checks
from examples.mingli_5agents.method_surface import method_surface_receipt
from examples.mingli_5agents.provider_checks import certify_json_cli_provider, provider_health_checks
from examples.mingli_5agents.provider_protocols import provider_protocol_document


def test_provider_health_checks_report_optional_backends():
    result = provider_health_checks()

    assert result["status"] in {"ready_with_optional_gaps", "contract_failure"}
    assert result["profile"] == "development"
    assert result["profile_readiness"]["profile"] == "development"
    assert result["total"] == 8
    assert result["reference_chart_checks"]["passed"] is True
    assert set(result["checks"]) == {
        "bazi_lunar_python",
        "bazi_sxtwl",
        "ziwei_json_cli",
        "qimen_kinqimen",
        "qimen_json_cli",
        "astrology_swiss_ephemeris",
        "astrology_json_cli",
        "xuanze_json_cli",
    }
    assert result["checks"]["ziwei_json_cli"]["status"] in {"configured", "not_configured"}
    assert result["checks"]["qimen_kinqimen"]["status"] in {"available", "missing"}
    assert result["checks"]["qimen_json_cli"]["status"] in {"configured", "not_configured"}
    assert result["checks"]["astrology_json_cli"]["status"] in {"configured", "not_configured"}
    assert result["checks"]["xuanze_json_cli"]["status"] in {"configured", "not_configured"}
    assert "install_hint" in result["checks"]["qimen_kinqimen"]
    assert "blocking_detail" in result["checks"]["qimen_kinqimen"]
    assert result["checks"]["ziwei_json_cli"]["install_hint"].startswith("Set SEMAS_ZIWEI_CLI")
    assert result["checks"]["ziwei_json_cli"]["install_diagnostics"]["kind"] == "json_cli_provider"
    assert result["checks"]["ziwei_json_cli"]["install_diagnostics"]["requires_external_command"] is True
    assert "SEMAS_ZIWEI_CLI" in result["checks"]["ziwei_json_cli"]["install_diagnostics"]["install_command"]
    ziwei_protocol = provider_protocol_document()["domains"]["ziwei"]
    assert result["checks"]["ziwei_json_cli"]["protocol_version"] == ziwei_protocol["protocol_version"]
    assert result["checks"]["ziwei_json_cli"]["protocol_hash"] == ziwei_protocol["protocol_hash"]
    assert result["checks"]["astrology_json_cli"]["install_hint"].startswith("Set SEMAS_ASTROLOGY_CLI")
    assert result["checks"]["xuanze_json_cli"]["install_hint"].startswith("Set SEMAS_XUANZE_CLI")
    assert result["checks"]["astrology_swiss_ephemeris"]["install_diagnostics"]["kind"] == "python_dependency"
    assert result["checks"]["astrology_swiss_ephemeris"]["install_diagnostics"]["module"] == "swisseph"
    assert "python_version" in result["checks"]["astrology_swiss_ephemeris"]["install_diagnostics"]
    assert result["checks"]["qimen_kinqimen"]["install_diagnostics"]["provider"] == "kinqimen"
    assert result["integration_plan"]["total_targets"] == 5
    assert result["integration_plan"]["status"] == "production_blocked"
    assert result["integration_plan"]["production_ready"] is False
    assert result["integration_plan"]["reference_contracts_passed"] is True
    assert result["integration_plan"]["smoke_command"].endswith("providers --profile production --live")
    target_names = {target["name"] for target in result["integration_plan"]["targets"]}
    assert target_names == {
        "bazi_professional_calendar",
        "ziwei_professional_engine",
        "qimen_professional_engine",
        "astrology_ephemeris_engine",
        "xuanze_almanac_engine",
    }
    ziwei_target = next(
        target for target in result["integration_plan"]["targets"] if target["name"] == "ziwei_professional_engine"
    )
    assert ziwei_target["contracts"] == ["raw_json_cli_contract:ziwei"]
    assert ziwei_target["provider_domain"] == "ziwei"
    assert ziwei_target["env_vars"] == ["SEMAS_ZIWEI_CLI"]
    assert ziwei_target["protocols"]["ziwei_json_cli"]["protocol_hash"] == ziwei_protocol["protocol_hash"]
    assert ziwei_target["protocols"]["ziwei_json_cli"]["protocol_version"] == ziwei_protocol["protocol_version"]
    assert ziwei_target["production_credential_required"] is True
    assert ziwei_target["production_credential_passed"] is False
    assert ziwei_target["required_provenance_fields"] == ["provider", "version", "source", "license_or_review"]
    assert ziwei_target["bundled_example_policy"].startswith("Bundled *_json_cli_example.py")
    assert ziwei_target["certification_commands"] == [
        'python -m examples.mingli_5agents.cli --repo .semas_mingli_repo certify-provider ziwei --command "<provider-command>" --provenance "provider=<provider-name>; version=<provider-version>; source=<review-source>; license_or_review=<license-or-review>" --record'
    ]
    assert ziwei_target["drift_commands"] == [
        "python -m examples.mingli_5agents.cli --repo .semas_mingli_repo provider-drift --domain ziwei"
    ]
    assert any("certify-provider ziwei --record" in item for item in ziwei_target["deployment_checklist"])
    assert any("provider-drift --domain ziwei" in item for item in ziwei_target["deployment_checklist"])
    assert any("SEMAS_ZIWEI_CLI" in action for action in ziwei_target["next_actions"])
    assert any("SEMAS_ZIWEI_PROVIDER_PROVENANCE" in action for action in ziwei_target["next_actions"])
    guidance = result["production_guidance"]
    assert guidance["production_ready"] is False
    assert "ziwei_professional_engine" in guidance["blocked_targets"]
    assert "SEMAS_ZIWEI_CLI" in guidance["required_env_vars"]
    assert "SEMAS_ZIWEI_PROVIDER_PROVENANCE" in guidance["required_provenance_env_vars"]
    assert any("certify-provider ziwei" in command for command in guidance["certification_commands"])
    assert any("provider-drift --domain ziwei" in command for command in guidance["drift_commands"])
    assert any("certify-provider ziwei --record" in item for item in guidance["deployment_checklist"])
    assert any("SEMAS_ZIWEI_CLI" in action for action in guidance["next_actions"])
    assert "provider-onboarding" in guidance["provider_onboarding_command"]
    assert "provider-ledger" in guidance["provider_ledger_command"]
    assert "production-readiness --live" in guidance["production_readiness_command"]
    assert "providers --profile production --live" in guidance["smoke_command"]
    assert "Bundled protocol examples" in guidance["policy"]


def test_provider_checks_service_bootstraps_repo(tmp_path: Path):
    result = provider_checks(tmp_path / "repo")

    assert result["repo"] == str(tmp_path / "repo")
    assert result["reference_chart_checks"]["passed"] is True


def test_provider_health_checks_production_profile_reports_blockers():
    result = provider_health_checks(profile="production")

    assert result["profile"] == "production"
    assert result["status"] == "production_blocked"
    assert result["profile_readiness"]["ready"] is False
    assert result["profile_readiness"]["live_required"] is True
    assert any("requires --live" in blocker for blocker in result["profile_readiness"]["blockers"])
    assert result["integration_plan"]["status"] == "production_blocked"
    assert result["integration_plan"]["production_ready"] is False
    assert result["production_guidance"]["production_ready"] is False
    assert "production-readiness --live" in result["production_guidance"]["production_readiness_command"]
    assert "ziwei_professional_engine" in result["integration_plan"]["blocked_targets"]
    assert {group["name"] for group in result["profile_readiness"]["required_groups"]} == {
        "bazi_professional_calendar",
        "ziwei_professional_engine",
        "qimen_professional_engine",
        "astrology_ephemeris_engine",
        "xuanze_almanac_engine",
    }


def test_provider_health_checks_live_smoke_rejects_partial_qimen_cli(tmp_path: Path, monkeypatch):
    script = tmp_path / "fake_qimen_provider.py"
    script.write_text(
        "import json, sys\n"
        "json.loads(sys.stdin.read())\n"
        "print(json.dumps({'duty_door': 'Open', 'duty_star': 'Tianxin'}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SEMAS_QIMEN_CLI", f"{sys.executable} {script}")

    result = provider_health_checks(live=True)
    live_check = result["checks"]["qimen_json_cli"]["live_check"]

    assert result["live"] is True
    assert live_check["executed"] is True
    assert live_check["protocol_hash"] == provider_protocol_document()["domains"]["qimen"]["protocol_hash"]
    assert live_check["passed"] is False
    assert live_check["contract_valid"] is False
    assert "palaces" in live_check["missing_required_keys"]
    assert "useful_gods" in live_check["missing_required_keys"]


def test_provider_health_checks_live_smoke_rejects_partial_astrology_cli(tmp_path: Path, monkeypatch):
    script = tmp_path / "fake_astrology_provider.py"
    script.write_text(
        "import json, sys\n"
        "json.loads(sys.stdin.read())\n"
        "print(json.dumps({'planets': [{'name': 'Sun'}], 'houses': [{'number': 1}]}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SEMAS_ASTROLOGY_CLI", f"{sys.executable} {script}")

    result = provider_health_checks(live=True)
    live_check = result["checks"]["astrology_json_cli"]["live_check"]

    assert result["live"] is True
    assert live_check["executed"] is True
    assert live_check["protocol_hash"] == provider_protocol_document()["domains"]["astrology"]["protocol_hash"]
    assert live_check["passed"] is False
    assert live_check["contract_valid"] is False
    assert "annual_transits" in live_check["missing_required_keys"]
    assert "planets[>=10]" in live_check["missing_required_keys"]
    assert "houses[12]" in live_check["missing_required_keys"]


def test_provider_health_checks_live_smoke_rejects_partial_xuanze_cli(tmp_path: Path, monkeypatch):
    script = tmp_path / "fake_xuanze_provider.py"
    script.write_text(
        "import json, sys\n"
        "json.loads(sys.stdin.read())\n"
        "print(json.dumps({'rows': [{'date': '2026-06-21'}]}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SEMAS_XUANZE_CLI", f"{sys.executable} {script}")

    result = provider_health_checks(live=True)
    live_check = result["checks"]["xuanze_json_cli"]["live_check"]

    assert result["live"] is True
    assert live_check["executed"] is True
    assert live_check["protocol_hash"] == provider_protocol_document()["domains"]["xuanze"]["protocol_hash"]
    assert live_check["passed"] is False
    assert live_check["contract_valid"] is False
    assert "summary.favorable_dates" in live_check["missing_required_keys"]
    assert "rows[0].required_fields" in live_check["missing_required_keys"]


def test_provider_health_checks_marks_non_example_cli_with_provenance_as_credentialed(tmp_path: Path, monkeypatch):
    script = tmp_path / "reviewed_ziwei_provider.py"
    source = Path(__file__).resolve().parents[1] / "providers" / "ziwei_json_cli_example.py"
    script.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("SEMAS_ZIWEI_CLI", f"{sys.executable} {script}")
    monkeypatch.setenv(
        "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
        "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
    )

    result = provider_health_checks(live=True, profile="production")
    check = result["checks"]["ziwei_json_cli"]

    assert check["live_check"]["passed"] is True
    assert check["live_check"]["protocol_hash"] == provider_protocol_document()["domains"]["ziwei"]["protocol_hash"]
    assert check["live_check"]["protocol_identity_matches"] is True
    assert check["live_check"]["provider_request_receipt_valid"] is True
    assert check["live_check"]["provider_request_receipt"]["protocol_echo_matches"] is True
    assert len(check["live_check"]["provider_request_receipt"]["birth_profile_sha256"]) == 64
    assert len(check["live_check"]["provider_request_receipt"]["stdin_sha256"]) == 64
    assert (
        check["live_check"]["protocol_identity"]["returned_hash"]
        == provider_protocol_document()["domains"]["ziwei"]["protocol_hash"]
    )
    assert check["command_is_bundled_example"] is False
    assert check["provider_command_fingerprint"]["configured"] is True
    assert len(check["provider_command_fingerprint"]["command_sha256"]) == 64
    assert check["provider_command_fingerprint"]["artifact_path"].endswith("reviewed_ziwei_provider.py")
    assert check["provider_command_fingerprint"]["artifact_exists"] is True
    assert len(check["provider_command_fingerprint"]["artifact_sha256"]) == 64
    assert check["provider_command_fingerprint"]["artifact_kind"] == "python_script"
    assert check["production_credential_passed"] is True
    assert check["provider_provenance_audit"]["valid"] is True
    assert check["provider_provenance_audit"]["fields"]["version"] == "1.0"


def test_certify_json_cli_provider_accepts_reviewed_live_provider(tmp_path: Path, monkeypatch):
    script = tmp_path / "reviewed_ziwei_provider.py"
    source = Path(__file__).resolve().parents[1] / "providers" / "ziwei_json_cli_example.py"
    script.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("SEMAS_ZIWEI_CLI", f"{sys.executable} {script}")
    monkeypatch.setenv(
        "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
        "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
    )

    result = certify_json_cli_provider("ziwei", tmp_path / "repo", live=True)

    assert result["domain"] == "ziwei"
    assert result["status"] == "certified"
    assert result["certified"] is True
    assert result["live_check"]["passed"] is True
    assert result["provider_provenance_audit"]["valid"] is True
    assert result["production_credential_passed"] is True
    assert result["blockers"] == []
    ziwei_protocol = provider_protocol_document()["domains"]["ziwei"]
    assert result["protocol_version"] == ziwei_protocol["protocol_version"]
    assert result["protocol_hash"] == ziwei_protocol["protocol_hash"]
    assert len(result["certification_receipt"]["sha256"]) == 64
    assert result["certification_receipt"]["material"]["certified"] is True
    assert result["certification_receipt"]["material"]["protocol_version"] == ziwei_protocol["protocol_version"]
    assert result["certification_receipt"]["material"]["protocol_hash"] == ziwei_protocol["protocol_hash"]
    assert result["certification_receipt"]["material"]["protocol_identity_matches"] is True
    assert result["certification_receipt"]["material"]["protocol_identity"]["returned_hash"] == ziwei_protocol["protocol_hash"]
    coverage = result["certification_receipt"]["material"]["reference_contract_coverage"]
    assert coverage["method_surface_sha256"] == method_surface_receipt()["sha256"]
    assert coverage["required_method_surface"] == ziwei_protocol["required_method_surface"]
    assert result["certification_receipt"]["material"]["provider_request_receipt_valid"] is True
    assert result["certification_receipt"]["material"]["provider_request_receipt"]["protocol_echo_matches"] is True
    assert len(result["certification_receipt"]["material"]["provider_request_receipt"]["stdout_sha256"]) == 64
    raw_contract_receipt = result["certification_receipt"]["material"]["raw_contract_receipt"]
    assert len(raw_contract_receipt["sha256"]) == 64
    assert raw_contract_receipt["material"]["domain"] == "ziwei"
    assert raw_contract_receipt["material"]["contract_valid"] is True
    assert raw_contract_receipt["material"]["missing_required_keys"] == []
    assert raw_contract_receipt["material"]["provider_request_receipt_sha256"] == result[
        "certification_receipt"
    ]["material"]["provider_request_receipt"]["sha256"]
    assert raw_contract_receipt["material"]["stdout_sha256"] == result["certification_receipt"]["material"][
        "provider_request_receipt"
    ]["stdout_sha256"]
    assert result["provider_command_fingerprint"]["configured"] is True
    assert len(result["provider_command_fingerprint"]["command_sha256"]) == 64
    assert result["provider_command_fingerprint"]["artifact_path"].endswith("reviewed_ziwei_provider.py")
    assert len(result["provider_command_fingerprint"]["artifact_sha256"]) == 64
    assert (
        result["certification_receipt"]["material"]["provider_command_fingerprint"]
        == result["provider_command_fingerprint"]
    )


def test_provider_health_checks_blocks_valid_contract_with_stale_protocol_identity(tmp_path: Path, monkeypatch):
    script = tmp_path / "stale_protocol_ziwei_provider.py"
    script.write_text(
        "import json, sys\n"
        "json.loads(sys.stdin.read())\n"
        "palaces = [\n"
        "    {'index': i, 'name': name, 'theme': name, 'primary_stars': ['Ziwei'], 'auxiliary_stars': [], 'markers': []}\n"
        "    for i, name in enumerate(['Ming','Siblings','Spouse','Children','Wealth','Health','Travel','Friends','Career','Property','Fortune','Parents'])\n"
        "]\n"
        "print(json.dumps({\n"
        "    'protocol': {'version': 'json-cli-v1', 'hash': '0' * 64},\n"
        "    'ming_palace': 'Career',\n"
        "    'body_palace': 'Wealth',\n"
        "    'major_stars': ['Ziwei', 'Wuqu'],\n"
        "    'transformations': {'lu': 'Wuqu', 'quan': 'Ziwei', 'ke': 'Tianji', 'ji': 'Taiyin'},\n"
        "    'palaces': palaces,\n"
        "    'major_limits': [{'start_year': 1990, 'end_year': 1999, 'palace': 'Career'}],\n"
        "    'annual_activation': [{'year': 2026, 'palace': 'Career'}],\n"
        "}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SEMAS_ZIWEI_CLI", f"{sys.executable} {script}")
    monkeypatch.setenv(
        "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
        "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
    )

    result = provider_health_checks(live=True, profile="production")
    check = result["checks"]["ziwei_json_cli"]
    live_check = check["live_check"]

    assert live_check["contract_valid"] is True
    assert live_check["protocol_identity_matches"] is False
    assert live_check["provider_request_receipt_valid"] is False
    assert live_check["provider_request_receipt"]["protocol_echo_matches"] is False
    assert live_check["protocol_identity"]["hash_matches"] is False
    assert "protocol.hash mismatch or missing" in live_check["protocol_failures"]
    assert live_check["passed"] is False
    assert check["production_credential_passed"] is False
    assert "live smoke did not pass" in check["production_blocker"]


def test_certify_json_cli_provider_receipt_records_protocol_identity_failure(tmp_path: Path, monkeypatch):
    script = tmp_path / "missing_protocol_ziwei_provider.py"
    source = Path(__file__).resolve().parents[1] / "providers" / "ziwei_json_cli_example.py"
    script.write_text(
        source.read_text(encoding="utf-8").replace(
            '"protocol": {"version": protocol.get("version"), "hash": protocol.get("hash")},\n        ',
            "",
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SEMAS_ZIWEI_CLI", f"{sys.executable} {script}")
    monkeypatch.setenv(
        "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
        "provider=reviewed-ziwei-provider; version=1.0; source=internal review; license_or_review=licensed fixture",
    )

    result = certify_json_cli_provider("ziwei", tmp_path / "repo", live=True)

    assert result["status"] == "blocked"
    assert result["certified"] is False
    assert result["live_check"]["contract_valid"] is True
    assert result["live_check"]["protocol_identity_matches"] is False
    assert result["certification_receipt"]["material"]["contract_valid"] is True
    assert result["certification_receipt"]["material"]["raw_contract_receipt"]["material"]["contract_valid"] is True
    assert result["certification_receipt"]["material"]["protocol_identity_matches"] is False
    assert "protocol.hash mismatch or missing" in result["certification_receipt"]["material"]["protocol_failures"]


def test_certify_json_cli_provider_accepts_command_override_without_env_leak(tmp_path: Path, monkeypatch):
    script = tmp_path / "reviewed_ziwei_provider.py"
    source = Path(__file__).resolve().parents[1] / "providers" / "ziwei_json_cli_example.py"
    script.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.delenv("SEMAS_ZIWEI_CLI", raising=False)
    monkeypatch.delenv("SEMAS_ZIWEI_PROVIDER_PROVENANCE", raising=False)

    result = certify_json_cli_provider(
        "ziwei",
        tmp_path / "repo",
        live=True,
        command=f"{sys.executable} {script}",
        provenance=(
            "provider=reviewed-ziwei-provider; version=1.0; "
            "source=internal review; license_or_review=licensed fixture"
        ),
    )

    assert result["status"] == "certified"
    assert result["command_override_used"] is True
    assert result["provenance_override_used"] is True
    assert result["live_check"]["passed"] is True
    first_receipt = result["certification_receipt"]["sha256"]
    assert result["expected_receipt_sha256"] is None
    assert result["receipt_matches_expected"] is None
    assert result["receipt_mismatch_reason"] == ""
    repeated = certify_json_cli_provider(
        "ziwei",
        tmp_path / "repo",
        live=True,
        command=f"{sys.executable} {script}",
        provenance=(
            "provider=reviewed-ziwei-provider; version=1.0; "
            "source=internal review; license_or_review=licensed fixture"
        ),
    )
    assert repeated["certification_receipt"]["sha256"] == first_receipt
    matched = certify_json_cli_provider(
        "ziwei",
        tmp_path / "repo",
        live=True,
        command=f"{sys.executable} {script}",
        provenance=(
            "provider=reviewed-ziwei-provider; version=1.0; "
            "source=internal review; license_or_review=licensed fixture"
        ),
        expected_receipt_sha256=first_receipt,
    )
    assert matched["certification_receipt"]["sha256"] == first_receipt
    assert matched["expected_receipt_sha256"] == first_receipt
    assert matched["receipt_matches_expected"] is True
    assert matched["receipt_mismatch_reason"] == ""
    mismatched = certify_json_cli_provider(
        "ziwei",
        tmp_path / "repo",
        live=True,
        command=f"{sys.executable} {script}",
        provenance=(
            "provider=reviewed-ziwei-provider; version=1.0; "
            "source=internal review; license_or_review=licensed fixture"
        ),
        expected_receipt_sha256="0" * 64,
    )
    assert mismatched["receipt_matches_expected"] is False
    assert "does not match" in mismatched["receipt_mismatch_reason"]
    assert "SEMAS_ZIWEI_CLI" not in os.environ
    assert "SEMAS_ZIWEI_PROVIDER_PROVENANCE" not in os.environ


def test_certify_json_cli_provider_blocks_unconfigured_provider(monkeypatch):
    monkeypatch.delenv("SEMAS_QIMEN_CLI", raising=False)
    monkeypatch.delenv("SEMAS_QIMEN_PROVIDER_PROVENANCE", raising=False)

    result = certify_json_cli_provider("qimen", live=True)

    assert result["domain"] == "qimen"
    assert result["status"] == "blocked"
    assert result["certified"] is False
    assert result["env_var"] == "SEMAS_QIMEN_CLI"
    assert result["production_credential_passed"] is False
    assert len(result["certification_receipt"]["sha256"]) == 64
    assert result["certification_receipt"]["material"]["certified"] is False
    assert any("SEMAS_QIMEN_CLI" in item for item in result["blockers"])


def test_provider_health_checks_rejects_unstructured_provenance(tmp_path: Path, monkeypatch):
    script = tmp_path / "reviewed_ziwei_provider.py"
    source = Path(__file__).resolve().parents[1] / "providers" / "ziwei_json_cli_example.py"
    script.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("SEMAS_ZIWEI_CLI", f"{sys.executable} {script}")
    monkeypatch.setenv("SEMAS_ZIWEI_PROVIDER_PROVENANCE", "reviewed provider 1.0 licensed fixture")

    result = provider_health_checks(live=True, profile="production")
    check = result["checks"]["ziwei_json_cli"]

    assert check["live_check"]["passed"] is True
    assert check["provider_provenance_audit"]["valid"] is False
    assert check["provider_provenance_audit"]["missing"] == [
        "provider",
        "version",
        "source",
        "license_or_review",
    ]
    assert check["production_credential_passed"] is False
    assert "license_or_review" in check["production_blocker"]
