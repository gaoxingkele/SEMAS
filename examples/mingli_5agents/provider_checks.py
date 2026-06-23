"""Provider readiness checks for optional professional backends."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from examples.mingli_5agents.method_surface import REQUIRED_METHODS, method_surface_receipt
from examples.mingli_5agents.provider_contracts import raw_json_cli_contract
from examples.mingli_5agents.provider_request_receipt import (
    attach_provider_request_identity,
    provider_request_receipt,
)
from examples.mingli_5agents.provider_protocols import provider_protocol_document
from examples.mingli_5agents.reference_charts import run_reference_chart_checks
from examples.mingli_5agents.tools.calendar_core import describe_calendar_providers
from examples.mingli_5agents.tools.professional_chart_provider import describe_domain_chart_providers


PRODUCTION_PROVIDER_GROUPS = [
    ("bazi_professional_calendar", ["bazi_lunar_python", "bazi_sxtwl"]),
    ("ziwei_professional_engine", ["ziwei_json_cli"]),
    ("qimen_professional_engine", ["qimen_kinqimen", "qimen_json_cli"]),
    ("astrology_ephemeris_engine", ["astrology_swiss_ephemeris", "astrology_json_cli"]),
    ("xuanze_almanac_engine", ["xuanze_json_cli"]),
]

JSON_CLI_ENV_VARS = {
    "ziwei_json_cli": "SEMAS_ZIWEI_CLI",
    "qimen_json_cli": "SEMAS_QIMEN_CLI",
    "astrology_json_cli": "SEMAS_ASTROLOGY_CLI",
    "xuanze_json_cli": "SEMAS_XUANZE_CLI",
}

JSON_CLI_PROVENANCE_ENV_VARS = {
    "ziwei_json_cli": "SEMAS_ZIWEI_PROVIDER_PROVENANCE",
    "qimen_json_cli": "SEMAS_QIMEN_PROVIDER_PROVENANCE",
    "astrology_json_cli": "SEMAS_ASTROLOGY_PROVIDER_PROVENANCE",
    "xuanze_json_cli": "SEMAS_XUANZE_PROVIDER_PROVENANCE",
}

JSON_CLI_CHECK_BY_DOMAIN = {
    "ziwei": "ziwei_json_cli",
    "qimen": "qimen_json_cli",
    "astrology": "astrology_json_cli",
    "xuanze": "xuanze_json_cli",
}
JSON_CLI_DOMAIN_BY_CHECK = {check: domain for domain, check in JSON_CLI_CHECK_BY_DOMAIN.items()}
REQUIRED_PROVIDER_PROVENANCE_FIELDS = ["provider", "version", "source", "license_or_review"]

PROVIDER_CONTRACT_NAMES = {
    "bazi_lunar_python": "professional_bazi_contract",
    "bazi_sxtwl": "professional_bazi_contract",
    "ziwei_json_cli": "raw_json_cli_contract:ziwei",
    "qimen_kinqimen": "raw_json_cli_contract:qimen",
    "qimen_json_cli": "raw_json_cli_contract:qimen",
    "astrology_swiss_ephemeris": "raw_json_cli_contract:astrology",
    "astrology_json_cli": "raw_json_cli_contract:astrology",
    "xuanze_json_cli": "raw_json_cli_contract:xuanze",
}

BUNDLED_JSON_CLI_EXAMPLES = {
    "ziwei": Path(__file__).resolve().parent / "providers" / "ziwei_json_cli_example.py",
    "qimen": Path(__file__).resolve().parent / "providers" / "qimen_json_cli_example.py",
    "astrology": Path(__file__).resolve().parent / "providers" / "astrology_json_cli_example.py",
    "xuanze": Path(__file__).resolve().parent / "providers" / "xuanze_json_cli_example.py",
}


def provider_health_checks(
    repo_path: Path | None = None,
    *,
    live: bool = False,
    profile: str = "development",
) -> dict[str, Any]:
    """Return non-destructive readiness checks for professional providers."""
    if profile not in {"development", "production"}:
        raise ValueError("provider profile must be 'development' or 'production'")
    calendar = describe_calendar_providers()
    domains = describe_domain_chart_providers()
    checks = {
        "bazi_lunar_python": _dependency_check(
            domain="bazi",
            provider="lunar_python",
            module="lunar_python",
            status="available" if calendar.get("professional_backend") == "lunar_python" else "missing",
            requirement="Professional BaZi pillars and deep analysis.",
            install_hint='pip install -e ".[mingli]"',
        ),
        "bazi_sxtwl": _dependency_check(
            domain="bazi",
            provider="sxtwl",
            module="sxtwl",
            status="available" if _module_available("sxtwl") else "missing",
            requirement="Fallback astronomical/lunar-calendar primitives.",
            install_hint='pip install -e ".[mingli]"',
            blocking_detail=_native_build_hint("sxtwl"),
        ),
        "ziwei_json_cli": _ziwei_cli_check(domains, live=live),
        "qimen_kinqimen": _dependency_check(
            domain="qimen",
            provider="kinqimen",
            module="kinqimen",
            status=_installed_status(domains, "qimen", "kinqimen"),
            requirement="Professional Qi Men plate provider.",
            install_hint='pip install -e ".[qimen]"',
            blocking_detail=_native_build_hint("kinqimen"),
        ),
        "qimen_json_cli": _json_cli_check(
            domains=domains,
            domain="qimen",
            provider="qimen_json_cli",
            env_var="SEMAS_QIMEN_CLI",
            requirement="External professional Qi Men engine through JSON stdin/stdout.",
            live=live,
        ),
        "astrology_swiss_ephemeris": _dependency_check(
            domain="astrology",
            provider="pyswisseph",
            module="swisseph",
            status=_installed_status(domains, "astrology", "swiss_ephemeris"),
            requirement="Ephemeris-backed Western astrology provider.",
            install_hint='pip install -e ".[astrology]"',
            blocking_detail=_native_build_hint("pyswisseph"),
        ),
        "astrology_json_cli": _json_cli_check(
            domains=domains,
            domain="astrology",
            provider="astrology_json_cli",
            env_var="SEMAS_ASTROLOGY_CLI",
            requirement="External professional Western astrology engine through JSON stdin/stdout.",
            live=live,
        ),
        "xuanze_json_cli": _json_cli_check(
            domains=domains,
            domain="xuanze",
            provider="xuanze_json_cli",
            env_var="SEMAS_XUANZE_CLI",
            requirement="External professional tongshu/xuanze engine through JSON stdin/stdout.",
            live=live,
        ),
    }
    reference = run_reference_chart_checks()
    ready_count = sum(1 for item in checks.values() if item["ready"])
    profile_report = _profile_readiness(checks, reference, profile=profile, live=live)
    integration_plan = _integration_plan(checks, reference, live=live, repo_path=repo_path)
    production_guidance = _production_provider_guidance(integration_plan, repo_path)
    return {
        "repo": str(repo_path) if repo_path is not None else None,
        "status": profile_report["status"],
        "profile": profile,
        "profile_readiness": profile_report,
        "integration_plan": integration_plan,
        "production_guidance": production_guidance,
        "live": live,
        "ready_count": ready_count,
        "total": len(checks),
        "calendar_providers": calendar,
        "domain_chart_providers": domains,
        "checks": checks,
        "reference_chart_checks": reference,
        "notes": [
            "Checks are non-destructive and do not execute SEMAS_ZIWEI_CLI, SEMAS_QIMEN_CLI, SEMAS_ASTROLOGY_CLI, or SEMAS_XUANZE_CLI by default.",
            "A missing optional backend does not break symbolic fallback execution.",
        ],
    }


def _production_provider_guidance(integration_plan: dict[str, Any], repo_path: Path | None) -> dict[str, Any]:
    """Aggregate provider integration steps for operators and deployment automation."""
    targets = [item for item in integration_plan.get("targets", []) if isinstance(item, dict)]
    blocked_targets = [item for item in targets if item.get("status") != "ready"]
    env_vars = sorted({env for item in blocked_targets for env in item.get("env_vars", []) if str(env).strip()})
    provenance_env_vars = sorted(
        {
            JSON_CLI_PROVENANCE_ENV_VARS.get(check_name, "")
            for item in blocked_targets
            for check_name in item.get("candidate_checks", [])
            if check_name in JSON_CLI_PROVENANCE_ENV_VARS
        }
        - {""}
    )
    certification_commands = _dedupe(
        [command for item in blocked_targets for command in item.get("certification_commands", [])]
    )
    drift_commands = _dedupe([command for item in blocked_targets for command in item.get("drift_commands", [])])
    deployment_checklist = _dedupe(
        [step for item in blocked_targets for step in item.get("deployment_checklist", [])]
    )
    next_actions = _dedupe([step for item in blocked_targets for step in item.get("next_actions", [])])
    repo = _repo_arg(repo_path)
    return {
        "production_ready": integration_plan.get("production_ready") is True,
        "blocked_targets": [str(item.get("name")) for item in blocked_targets],
        "required_env_vars": env_vars,
        "required_provenance_env_vars": provenance_env_vars,
        "certification_commands": certification_commands,
        "drift_commands": drift_commands,
        "deployment_checklist": deployment_checklist,
        "next_actions": next_actions,
        "provider_onboarding_command": f"python -m examples.mingli_5agents.cli --repo {repo} provider-onboarding",
        "provider_ledger_command": f"python -m examples.mingli_5agents.cli --repo {repo} provider-ledger",
        "production_readiness_command": f"python -m examples.mingli_5agents.cli --repo {repo} production-readiness --live",
        "smoke_command": integration_plan.get("smoke_command", ""),
        "policy": (
            "Production provider readiness requires reviewed live providers, provenance, certification receipts, "
            "provider ledger coverage, and drift checks. Bundled protocol examples are smoke fixtures only."
        ),
    }


def bundled_provider_example_smoke(repo_path: Path | None = None) -> dict[str, Any]:
    """Run bundled JSON-CLI protocol examples and return a non-production receipt."""
    commands = {
        JSON_CLI_ENV_VARS[JSON_CLI_CHECK_BY_DOMAIN[domain]]: f"{sys.executable} {script}"
        for domain, script in BUNDLED_JSON_CLI_EXAMPLES.items()
    }
    checks = _with_temporary_env(
        commands,
        lambda: provider_health_checks(repo_path, live=True, profile="production"),
    )
    domains = {}
    for domain in sorted(BUNDLED_JSON_CLI_EXAMPLES):
        check_name = JSON_CLI_CHECK_BY_DOMAIN[domain]
        check = checks.get("checks", {}).get(check_name, {})
        live_check = check.get("live_check", {}) if isinstance(check.get("live_check"), dict) else {}
        request_receipt = (
            live_check.get("provider_request_receipt", {}) if isinstance(live_check, dict) else {}
        )
        domains[domain] = {
            "check": check_name,
            "script": str(BUNDLED_JSON_CLI_EXAMPLES[domain]),
            "ready": check.get("ready") is True,
            "live_passed": live_check.get("passed") is True,
            "contract_valid": live_check.get("contract_valid") is True,
            "protocol_identity_matches": live_check.get("protocol_identity_matches") is True,
            "provider_request_receipt_valid": live_check.get("provider_request_receipt_valid") is True,
            "provider_request_receipt_sha256": request_receipt.get("sha256"),
            "protocol_version": check.get("protocol_version"),
            "protocol_hash": check.get("protocol_hash"),
            "command_is_bundled_example": check.get("command_is_bundled_example") is True,
            "production_credential_passed": check.get("production_credential_passed") is True,
            "production_blocker": check.get("production_blocker", ""),
        }
    material = {
        "schema_version": 1,
        "repo": str(repo_path) if repo_path is not None else None,
        "status": "passed" if all(item["live_passed"] for item in domains.values()) else "failed",
        "production_certification_allowed": False,
        "policy": "Bundled provider examples validate protocol wiring only and cannot certify production providers.",
        "domain_count": len(domains),
        "passed_domain_count": sum(1 for item in domains.values() if item["live_passed"]),
        "domains": domains,
        "profile_readiness_status": checks.get("profile_readiness", {}).get("status"),
        "integration_plan_status": checks.get("integration_plan", {}).get("status"),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    receipt = {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }
    return {
        "repo": str(repo_path) if repo_path is not None else None,
        "status": material["status"],
        "production_certification_allowed": False,
        "policy": material["policy"],
        "domains": domains,
        "profile_readiness": checks.get("profile_readiness", {}),
        "integration_plan": checks.get("integration_plan", {}),
        "example_provider_receipt": receipt,
    }


def certify_json_cli_provider(
    domain: str,
    repo_path: Path | None = None,
    *,
    live: bool = True,
    command: str | None = None,
    provenance: str | None = None,
    expected_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Return a focused certification report for one JSON-CLI provider domain."""
    if domain not in JSON_CLI_CHECK_BY_DOMAIN:
        raise ValueError("provider certification domain must be ziwei, qimen, astrology, or xuanze")
    check_name = JSON_CLI_CHECK_BY_DOMAIN[domain]
    env_var = JSON_CLI_ENV_VARS[check_name]
    provenance_env_var = JSON_CLI_PROVENANCE_ENV_VARS[check_name]
    override_env = {}
    if command is not None:
        override_env[env_var] = command
    if provenance is not None:
        override_env[provenance_env_var] = provenance
    checks = _with_temporary_env(
        override_env,
        lambda: provider_health_checks(repo_path, live=live, profile="production"),
    )
    check = checks["checks"][check_name]
    reference_contract_coverage = _reference_contract_coverage(domain, checks.get("reference_chart_checks", {}))
    live_check = check.get("live_check")
    command_fingerprint = check.get("provider_command_fingerprint", {})
    contract_name = PROVIDER_CONTRACT_NAMES[check_name]
    protocol = provider_protocol_document()["domains"].get(domain, {})
    target = next(
        (
            item
            for item in checks.get("integration_plan", {}).get("targets", [])
            if check_name in item.get("candidate_checks", [])
        ),
        {},
    )
    passed = bool(
        check.get("ready")
        and check.get("production_credential_passed")
        and (not live or _live_check_passed(live_check))
    )
    blockers = []
    if not check.get("command_configured"):
        blockers.append(f"{check.get('install_hint')}")
    if check.get("command_is_bundled_example"):
        blockers.append("Bundled protocol examples cannot certify production providers.")
    if not check.get("provider_provenance_audit", {}).get("valid"):
        blockers.append(f"Set structured provenance in {check.get('provenance_env_var')}.")
    if live and not _live_check_passed(live_check):
        blockers.append("Live JSON-CLI smoke test did not pass.")
    if check.get("production_blocker"):
        blockers.append(str(check["production_blocker"]))
    response = {
        "repo": str(repo_path) if repo_path is not None else None,
        "domain": domain,
        "provider_check": check_name,
        "status": "certified" if passed else "blocked",
        "certified": passed,
        "live_requested": live,
        "env_var": env_var,
        "provenance_env_var": provenance_env_var,
        "command_override_used": command is not None,
        "provenance_override_used": provenance is not None,
        "contract": contract_name,
        "protocol_version": protocol.get("protocol_version"),
        "protocol_hash": protocol.get("protocol_hash"),
        "command_configured": bool(check.get("command_configured")),
        "registered": bool(check.get("registered")),
        "live_check": live_check,
        "provider_provenance_audit": check.get("provider_provenance_audit"),
        "provider_command_fingerprint": command_fingerprint,
        "production_credential_passed": bool(check.get("production_credential_passed")),
        "command_is_bundled_example": bool(check.get("command_is_bundled_example")),
        "integration_target": target.get("name"),
        "integration_target_status": target.get("status"),
        "reference_contract_coverage": reference_contract_coverage,
        "blockers": _dedupe([item for item in blockers if item]),
        "next_actions": target.get("next_actions", []),
    }
    response["certification_receipt"] = _provider_certification_receipt(response)
    receipt_sha256 = response["certification_receipt"]["sha256"]
    receipt_matches_expected = (
        None if expected_receipt_sha256 is None else receipt_sha256 == expected_receipt_sha256
    )
    response["expected_receipt_sha256"] = expected_receipt_sha256
    response["receipt_matches_expected"] = receipt_matches_expected
    response["receipt_mismatch_reason"] = (
        "certification receipt sha256 does not match expected value"
        if receipt_matches_expected is False
        else ""
    )
    return response


def _with_temporary_env(overrides: dict[str, str], callback: Any) -> Any:
    if not overrides:
        return callback()
    previous = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        return callback()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _provider_certification_receipt(response: dict[str, Any]) -> dict[str, Any]:
    live_check = response.get("live_check")
    provenance = response.get("provider_provenance_audit")
    material = {
        "schema_version": 1,
        "domain": response.get("domain"),
        "provider_check": response.get("provider_check"),
        "status": response.get("status"),
        "certified": response.get("certified"),
        "live_requested": response.get("live_requested"),
        "contract": response.get("contract"),
        "protocol_version": response.get("protocol_version"),
        "protocol_hash": response.get("protocol_hash"),
        "contract_valid": live_check.get("contract_valid") if isinstance(live_check, dict) else None,
        "raw_contract_receipt": live_check.get("raw_contract_receipt", {}) if isinstance(live_check, dict) else {},
        "protocol_identity_matches": (
            live_check.get("protocol_identity_matches") if isinstance(live_check, dict) else None
        ),
        "protocol_identity": live_check.get("protocol_identity", {}) if isinstance(live_check, dict) else {},
        "protocol_failures": live_check.get("protocol_failures", []) if isinstance(live_check, dict) else [],
        "provider_request_receipt": live_check.get("provider_request_receipt", {}) if isinstance(live_check, dict) else {},
        "provider_request_receipt_valid": (
            live_check.get("provider_request_receipt_valid") if isinstance(live_check, dict) else None
        ),
        "provider_command_fingerprint": response.get("provider_command_fingerprint", {}),
        "live_passed": live_check.get("passed") if isinstance(live_check, dict) else None,
        "returned_keys": live_check.get("returned_keys", []) if isinstance(live_check, dict) else [],
        "missing_required_keys": live_check.get("missing_required_keys", []) if isinstance(live_check, dict) else [],
        "provenance_valid": provenance.get("valid") if isinstance(provenance, dict) else None,
        "provenance_fields": provenance.get("fields", {}) if isinstance(provenance, dict) else {},
        "reference_contract_coverage": response.get("reference_contract_coverage", {}),
        "production_credential_passed": response.get("production_credential_passed"),
        "command_is_bundled_example": response.get("command_is_bundled_example"),
        "blockers": response.get("blockers", []),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _reference_contract_coverage(domain: str, reference: dict[str, Any]) -> dict[str, Any]:
    method_surface = method_surface_receipt()
    required_surface = sorted(str(item) for item in REQUIRED_METHODS[domain])
    method_domain = (
        reference.get("method_coverage", {}).get("domains", {}).get(domain, {})
        if isinstance(reference, dict)
        else {}
    )
    cases = reference.get("cases", []) if isinstance(reference, dict) else []
    covered_cases = []
    provenance_cases = []
    for case in cases if isinstance(cases, list) else []:
        if not isinstance(case, dict):
            continue
        checked_domains = case.get("checked_domains", [])
        if isinstance(checked_domains, list) and domain in checked_domains:
            covered_cases.append(str(case.get("name")))
        provenance = case.get("provenance_coverage", {})
        if isinstance(provenance, dict) and provenance.get(domain) is True:
            provenance_cases.append(str(case.get("name")))
    missing_methods = method_domain.get("missing", []) if isinstance(method_domain, dict) else []
    observed_methods = method_domain.get("observed", []) if isinstance(method_domain, dict) else []
    required_methods = method_domain.get("required", []) if isinstance(method_domain, dict) else []
    passed = (
        reference.get("passed") is True
        and isinstance(method_domain, dict)
        and method_domain.get("passed") is True
        and bool(covered_cases)
        and bool(provenance_cases)
    )
    material = {
        "domain": domain,
        "passed": passed,
        "covered_cases": sorted(covered_cases),
        "provenance_cases": sorted(provenance_cases),
        "method_surface_schema_version": method_surface.get("schema_version"),
        "method_surface_sha256": method_surface.get("sha256"),
        "required_method_surface": required_surface,
        "required_methods": sorted(str(item) for item in required_methods),
        "observed_methods": sorted(str(item) for item in observed_methods),
        "missing_methods": sorted(str(item) for item in missing_methods),
    }
    material["coverage_sha256"] = hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return material


def _profile_readiness(
    checks: dict[str, dict[str, Any]],
    reference: dict[str, Any],
    *,
    profile: str,
    live: bool,
) -> dict[str, Any]:
    if not reference.get("passed"):
        return {
            "profile": profile,
            "status": "contract_failure",
            "ready": False,
            "required_groups": [],
            "blockers": ["reference chart contracts failed"],
            "live_required": False,
        }
    if profile == "development":
        return {
            "profile": profile,
            "status": "ready_with_optional_gaps",
            "ready": True,
            "required_groups": [{"name": "reference_contracts", "ready": True, "accepted_checks": []}],
            "blockers": [],
            "live_required": False,
        }

    required_groups = []
    blockers = []
    json_cli_checks = set(JSON_CLI_ENV_VARS)
    for name, check_names in PRODUCTION_PROVIDER_GROUPS:
        accepted = [check_name for check_name in check_names if checks.get(check_name, {}).get("ready")]
        production_accepted = [
            check_name
            for check_name in accepted
            if _production_credential_passed(checks.get(check_name, {}), check_name)
        ]
        group_ready = bool(production_accepted)
        required_groups.append({"name": name, "ready": group_ready, "accepted_checks": accepted, "checks": check_names})
        if not group_ready:
            blockers.append(f"{name} has no ready provider: {', '.join(check_names)}")
        if live:
            for check_name in accepted:
                if check_name in json_cli_checks:
                    live_check = checks.get(check_name, {}).get("live_check")
                    if not (isinstance(live_check, dict) and live_check.get("passed") is True):
                        blockers.append(f"{check_name} live smoke did not pass")
                    if not _production_credential_passed(checks.get(check_name, {}), check_name):
                        blockers.append(f"{check_name} lacks production provider provenance")
    if not live:
        blockers.append("production profile requires --live to verify configured JSON-CLI providers")
    ready = not blockers
    return {
        "profile": profile,
        "status": "production_ready" if ready else "production_blocked",
        "ready": ready,
        "required_groups": required_groups,
        "blockers": blockers,
        "live_required": True,
    }


def _integration_plan(
    checks: dict[str, dict[str, Any]],
    reference: dict[str, Any],
    *,
    live: bool,
    repo_path: Path | None = None,
) -> dict[str, Any]:
    targets = []
    for name, check_names in PRODUCTION_PROVIDER_GROUPS:
        provider_domain = _target_provider_domain(checks, check_names)
        json_cli_check_names = [check_name for check_name in check_names if check_name in JSON_CLI_ENV_VARS]
        accepted = [check_name for check_name in check_names if checks.get(check_name, {}).get("ready")]
        production_accepted = [
            check_name
            for check_name in accepted
            if _production_credential_passed(checks.get(check_name, {}), check_name)
        ]
        blocked = [
            check_name
            for check_name in check_names
            if not checks.get(check_name, {}).get("ready")
            or (
                check_name in JSON_CLI_ENV_VARS
                and checks.get(check_name, {}).get("ready")
                and not _production_credential_passed(checks.get(check_name, {}), check_name)
            )
        ]
        target_status = "ready" if production_accepted else "blocked"
        target = {
            "name": name,
            "provider_domain": provider_domain,
            "status": target_status,
            "accepted_checks": accepted,
            "production_accepted_checks": production_accepted,
            "candidate_checks": check_names,
            "blocked_checks": blocked,
            "contracts": sorted({PROVIDER_CONTRACT_NAMES[check_name] for check_name in check_names}),
            "env_vars": [
                JSON_CLI_ENV_VARS[check_name]
                for check_name in check_names
                if check_name in JSON_CLI_ENV_VARS
            ],
            "protocols": {
                check_name: {
                    "protocol_version": checks.get(check_name, {}).get("protocol_version"),
                    "protocol_hash": checks.get(check_name, {}).get("protocol_hash"),
                    "contract": PROVIDER_CONTRACT_NAMES[check_name],
                }
                for check_name in check_names
                if check_name in JSON_CLI_ENV_VARS
            },
            "live_smoke_required": any(check_name in JSON_CLI_ENV_VARS for check_name in check_names),
            "live_smoke_passed": _live_smoke_passed(checks, check_names),
            "production_credential_required": any(check_name in JSON_CLI_ENV_VARS for check_name in check_names),
            "production_credential_passed": any(
                _production_credential_passed(checks.get(check_name, {}), check_name)
                for check_name in check_names
            ),
            "required_provenance_fields": (
                list(REQUIRED_PROVIDER_PROVENANCE_FIELDS) if json_cli_check_names else []
            ),
            "certification_commands": _target_certification_commands(json_cli_check_names, repo_path),
            "drift_commands": _target_drift_commands(json_cli_check_names, repo_path),
            "deployment_checklist": _target_deployment_checklist(checks, check_names, repo_path),
            "bundled_example_policy": (
                "Bundled *_json_cli_example.py scripts are protocol fixtures for smoke tests and cannot certify production providers."
                if json_cli_check_names
                else ""
            ),
            "next_actions": _target_next_actions(checks, check_names),
        }
        targets.append(target)

    ready_targets = sum(1 for item in targets if item["status"] == "ready")
    production_ready = (
        bool(reference.get("passed"))
        and ready_targets == len(targets)
        and live
        and all(
            (not item["live_smoke_required"]) or item["live_smoke_passed"]
            for item in targets
        )
    )
    return {
        "status": "production_ready" if production_ready else "production_blocked",
        "production_ready": production_ready,
        "reference_contracts_passed": bool(reference.get("passed")),
        "live_requested": live,
        "live_required_for_production": True,
        "ready_targets": ready_targets,
        "total_targets": len(targets),
        "blocked_targets": [item["name"] for item in targets if item["status"] != "ready"],
        "targets": targets,
        "smoke_command": "python -m examples.mingli_5agents.cli providers --profile production --live",
    }


def _target_provider_domain(checks: dict[str, dict[str, Any]], check_names: list[str]) -> str:
    for check_name in check_names:
        domain = checks.get(check_name, {}).get("domain")
        if domain:
            return str(domain)
    return ""


def _repo_arg(repo_path: Path | None) -> str:
    return str(repo_path) if repo_path is not None else ".semas_mingli_repo"


def _target_certification_commands(check_names: list[str], repo_path: Path | None) -> list[str]:
    repo = _repo_arg(repo_path)
    commands = []
    for check_name in check_names:
        domain = JSON_CLI_DOMAIN_BY_CHECK.get(check_name)
        if not domain:
            continue
        commands.append(
            "python -m examples.mingli_5agents.cli "
            f"--repo {repo} certify-provider {domain} "
            '--command "<provider-command>" '
            '--provenance "provider=<provider-name>; version=<provider-version>; '
            'source=<review-source>; license_or_review=<license-or-review>" '
            "--record"
        )
    return commands


def _target_drift_commands(check_names: list[str], repo_path: Path | None) -> list[str]:
    repo = _repo_arg(repo_path)
    commands = []
    for check_name in check_names:
        domain = JSON_CLI_DOMAIN_BY_CHECK.get(check_name)
        if domain:
            commands.append(f"python -m examples.mingli_5agents.cli --repo {repo} provider-drift --domain {domain}")
    return commands


def _target_deployment_checklist(
    checks: dict[str, dict[str, Any]],
    check_names: list[str],
    repo_path: Path | None,
) -> list[str]:
    checklist = []
    repo = _repo_arg(repo_path)
    for check_name in check_names:
        check = checks.get(check_name, {})
        env_var = JSON_CLI_ENV_VARS.get(check_name)
        provenance_env_var = JSON_CLI_PROVENANCE_ENV_VARS.get(check_name)
        domain = JSON_CLI_DOMAIN_BY_CHECK.get(check_name)
        if env_var and provenance_env_var and domain:
            checklist.extend(
                [
                    f"Set {env_var} to the reviewed JSON-CLI provider command.",
                    f"Set {provenance_env_var} with provider, version, source, and license_or_review.",
                    "Run python -m examples.mingli_5agents.cli --repo "
                    f"{repo} providers --profile production --live.",
                    "Run python -m examples.mingli_5agents.cli --repo "
                    f"{repo} certify-provider {domain} --record.",
                    "Run python -m examples.mingli_5agents.cli --repo "
                    f"{repo} provider-ledger and confirm integrity_status=pass.",
                    "Run python -m examples.mingli_5agents.cli --repo "
                    f"{repo} provider-drift --domain {domain} and confirm status=passed.",
                ]
            )
        elif check.get("install_hint"):
            checklist.append(str(check["install_hint"]))
        if check.get("command_is_bundled_example"):
            checklist.append("Replace bundled protocol examples before recording certification receipts.")
    return _dedupe(checklist)


def _live_smoke_passed(checks: dict[str, dict[str, Any]], check_names: list[str]) -> bool:
    json_cli_checks = [check_name for check_name in check_names if check_name in JSON_CLI_ENV_VARS]
    if not json_cli_checks:
        return True
    passed = []
    for check_name in json_cli_checks:
        live_check = checks.get(check_name, {}).get("live_check")
        passed.append(isinstance(live_check, dict) and live_check.get("passed") is True)
    return any(passed)


def _target_next_actions(checks: dict[str, dict[str, Any]], check_names: list[str]) -> list[str]:
    actions = []
    for check_name in check_names:
        check = checks.get(check_name, {})
        if check.get("ready") and _production_credential_passed(check, check_name):
            continue
        install_hint = check.get("install_hint")
        if install_hint:
            actions.append(str(install_hint))
        blocking_detail = check.get("blocking_detail")
        if blocking_detail:
            actions.append(str(blocking_detail))
        env_var = JSON_CLI_ENV_VARS.get(check_name)
        if env_var:
            actions.append(f"Run providers --live after configuring {env_var}.")
        provenance_env_var = JSON_CLI_PROVENANCE_ENV_VARS.get(check_name)
        if provenance_env_var and not check.get("production_credential_passed"):
            actions.append(
                f"Set {provenance_env_var} to a reviewed provider name/version/license before claiming production readiness."
            )
        if check.get("command_is_bundled_example"):
            actions.append("Replace bundled protocol examples with an independently reviewed provider command.")
    return _dedupe(actions)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _dependency_check(
    *,
    domain: str,
    provider: str,
    module: str,
    status: str,
    requirement: str,
    install_hint: str,
    blocking_detail: str | None = None,
) -> dict[str, Any]:
    available = _module_available(module)
    final_status = status if available or status != "available" else "missing"
    install_diagnostics = _dependency_install_diagnostics(
        provider=provider,
        module=module,
        install_hint=install_hint,
        available=available,
        blocking_detail=blocking_detail,
    )
    return {
        "domain": domain,
        "provider": provider,
        "module": module,
        "status": final_status,
        "ready": final_status == "available" and available,
        "module_available": available,
        "requirement": requirement,
        "install_hint": install_hint,
        "blocking_detail": None if available else blocking_detail,
        "install_diagnostics": install_diagnostics,
    }


def _ziwei_cli_check(domains: dict[str, Any], *, live: bool = False) -> dict[str, Any]:
    return _json_cli_check(
        domains=domains,
        domain="ziwei",
        provider="ziwei_json_cli",
        env_var="SEMAS_ZIWEI_CLI",
        requirement="External professional Zi Wei engine through JSON stdin/stdout.",
        live=live,
    )


def _json_cli_check(
    *,
    domains: dict[str, Any],
    domain: str,
    provider: str,
    env_var: str,
    requirement: str,
    live: bool = False,
) -> dict[str, Any]:
    command = os.environ.get(env_var)
    installed = _json_cli_registered(domains, domain, provider)
    protocol = provider_protocol_document()["domains"].get(domain, {})
    live_check = _run_json_cli_smoke(command, domain) if live and command else None
    provenance_env_var = _provenance_env_var(provider)
    provenance = os.environ.get(provenance_env_var) if provenance_env_var else None
    provenance_audit = _provider_provenance_audit(provenance)
    command_is_bundled_example = _command_is_bundled_example(command)
    command_fingerprint = _provider_command_fingerprint(command)
    production_credential_passed = bool(
        command
        and provenance_audit["valid"]
        and not command_is_bundled_example
        and (not live or _live_check_passed(live_check))
    )
    return {
        "domain": domain,
        "provider": provider,
        "module": None,
        "status": "configured" if command else "not_configured",
        "ready": bool(command and installed),
        "module_available": None,
        "command_configured": bool(command),
        "registered": installed,
        "requirement": requirement,
        "protocol_version": protocol.get("protocol_version"),
        "protocol_hash": protocol.get("protocol_hash"),
        "install_hint": f"Set {env_var} to a JSON-speaking {domain} provider command.",
        "blocking_detail": None if command else f"{env_var} is not configured in the current environment.",
        "install_diagnostics": _json_cli_install_diagnostics(env_var, provenance_env_var, domain),
        "live_check": live_check,
        "provider_command_fingerprint": command_fingerprint,
        "command_is_bundled_example": command_is_bundled_example,
        "production_credential_required": True,
        "production_credential_passed": production_credential_passed,
        "provenance_env_var": provenance_env_var,
        "provider_provenance": provenance,
        "provider_provenance_audit": provenance_audit,
        "production_blocker": _json_cli_production_blocker(
            command=command,
            provenance=provenance,
            provenance_audit=provenance_audit,
            provenance_env_var=provenance_env_var,
            command_is_bundled_example=command_is_bundled_example,
            live=live,
            live_check=live_check,
        ),
    }


def _installed_status(domains: dict[str, Any], domain: str, provider: str) -> str:
    installed = domains.get(domain, {}).get("installed_professional_backend")
    if installed == provider:
        return "available"
    return "missing"


def _json_cli_registered(domains: dict[str, Any], domain: str, provider: str) -> bool:
    env_vars = {
        "ziwei": "SEMAS_ZIWEI_CLI",
        "qimen": "SEMAS_QIMEN_CLI",
        "astrology": "SEMAS_ASTROLOGY_CLI",
        "xuanze": "SEMAS_XUANZE_CLI",
    }
    if provider == f"{domain}_json_cli" and env_vars.get(domain):
        return bool(os.environ.get(env_vars[domain]))
    return domains.get(domain, {}).get("installed_professional_backend") == provider


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _dependency_install_diagnostics(
    *,
    provider: str,
    module: str,
    install_hint: str,
    available: bool,
    blocking_detail: str | None,
) -> dict[str, Any]:
    native_risk = _native_build_risk(provider)
    return {
        "kind": "python_dependency",
        "provider": provider,
        "module": module,
        "available": available,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "install_command": install_hint,
        "native_build_risk": native_risk,
        "requires_external_command": False,
        "blocking_detail": None if available else blocking_detail,
        "remediation": _dependency_remediation(provider, native_risk),
    }


def _json_cli_install_diagnostics(env_var: str, provenance_env_var: str | None, domain: str) -> dict[str, Any]:
    return {
        "kind": "json_cli_provider",
        "provider": f"{domain}_json_cli",
        "module": None,
        "available": bool(os.environ.get(env_var)),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "install_command": f"Set {env_var} to a reviewed JSON-CLI provider command.",
        "native_build_risk": False,
        "requires_external_command": True,
        "blocking_detail": None if os.environ.get(env_var) else f"{env_var} is not configured.",
        "remediation": (
            f"Run or deploy the professional {domain} engine outside this process, set {env_var}, "
            f"set {provenance_env_var}, then run providers --profile production --live."
        ),
    }


def _native_build_risk(provider: str) -> bool:
    return provider in {"sxtwl", "kinqimen", "pyswisseph"} and sys.version_info >= (3, 14)


def _dependency_remediation(provider: str, native_risk: bool) -> str:
    if native_risk and os.name == "nt":
        return (
            "Use a Python version with prebuilt wheels for this dependency, install Microsoft C++ Build Tools, "
            "or connect the provider through the JSON-CLI boundary instead."
        )
    if native_risk:
        return "Use a Python version with prebuilt wheels, install native build tooling, or use JSON-CLI provider integration."
    return "Install the optional dependency or configure an external JSON-CLI provider for this domain."


def _run_json_cli_smoke(command: str, domain: str) -> dict[str, Any]:
    protocol = provider_protocol_document()["domains"].get(domain, {})
    protocol_meta = {
        "protocol_version": protocol.get("protocol_version"),
        "protocol_hash": protocol.get("protocol_hash"),
        "protocol_contract_hash": protocol.get("protocol_hash"),
    }
    payload = {
        "birth": {
            "name": "Provider Smoke Case",
            "birth_date": "1990-04-12",
            "birth_time": "09:20",
            "gender": "unspecified",
            "birthplace": "Hangzhou",
            "year": 1990,
            "month": 4,
            "day": 12,
            "hour": 9,
            "minute": 20,
        },
        "fallback": {},
    }
    if domain == "xuanze":
        payload["fallback"] = {
            "range": {"start_date": "2026-06-21", "end_date": "2026-06-21", "count": 1},
            "basis": {
                "provider": "offline_rule_scaffold",
                "provider_quality": "offline_rule_scaffold",
            },
            "rows": [
                {
                    "date": "2026-06-21",
                    "weekday": "Sunday",
                    "ganzhi": "BingChen",
                    "solar_term": "Summer Solstice",
                    "twelve_officer": "Establish",
                    "twenty_eight_mansion": "Well",
                    "huangdao": True,
                    "rating": "mixed",
                    "recommended_hours": [
                        {"start": "09:00", "end": "10:59", "branch": "Si", "element": "Fire"}
                    ],
                    "suitable": ["smoke test"],
                    "avoid": ["high-stakes decisions"],
                    "risk_notes": ["provider smoke fixture"],
                }
            ],
            "summary": {
                "favorable_dates": [],
                "cautious_dates": [],
                "best_date": None,
            },
        }
    payload = attach_provider_request_identity(domain, payload["birth"], payload)
    protocol_identity = payload["protocol"]
    try:
        completed = subprocess.run(
            _split_command(command),
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if completed.returncode != 0:
            return {
                **protocol_meta,
                "executed": True,
                "passed": False,
                "error": completed.stderr.strip() or f"exit code {completed.returncode}",
            }
        result = json.loads(completed.stdout)
        if not isinstance(result, dict):
            return {
                **protocol_meta,
                "executed": True,
                "passed": False,
                "error": "provider did not return a JSON object",
            }
        contract = raw_json_cli_contract(domain, result)
        identity = _json_cli_protocol_identity(protocol_identity, result)
        request_receipt = provider_request_receipt(
            domain=domain,
            payload=payload,
            raw_stdout=completed.stdout,
            parsed_stdout=result,
        )
        raw_contract_receipt = _raw_provider_contract_receipt(
            domain=domain,
            contract=contract,
            returned_keys=sorted(str(key) for key in result),
            request_receipt=request_receipt,
        )
        return {
            **protocol_meta,
            "executed": True,
            "passed": contract["valid"] and identity["matches"] and request_receipt["protocol_echo_matches"],
            "returned_keys": sorted(str(key) for key in result),
            "missing_required_keys": contract["missing"],
            "contract_valid": contract["valid"],
            "contract_name": contract["name"],
            "raw_contract_receipt": raw_contract_receipt,
            "protocol_identity": identity,
            "protocol_identity_matches": identity["matches"],
            "protocol_failures": identity["failures"],
            "provider_request_receipt": request_receipt,
            "provider_request_receipt_valid": (
                request_receipt["protocol_echo_matches"]
                and isinstance(request_receipt.get("birth_profile_sha256"), str)
                and len(request_receipt["birth_profile_sha256"]) == 64
            ),
        }
    except Exception as exc:
        return {**protocol_meta, "executed": True, "passed": False, "error": str(exc)}


def _raw_provider_contract_receipt(
    *,
    domain: str,
    contract: dict[str, Any],
    returned_keys: list[str],
    request_receipt: dict[str, Any],
) -> dict[str, Any]:
    material = {
        "schema_version": 1,
        "domain": domain,
        "contract_name": contract.get("name"),
        "contract_valid": contract.get("valid") is True,
        "missing_required_keys": [str(item) for item in contract.get("missing", [])],
        "returned_keys": [str(item) for item in returned_keys],
        "provider_request_receipt_sha256": request_receipt.get("sha256"),
        "stdout_sha256": request_receipt.get("stdout_sha256"),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _json_cli_protocol_identity(expected: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    returned_protocol = result.get("protocol") if isinstance(result.get("protocol"), dict) else {}
    returned_version = returned_protocol.get("version") or result.get("protocol_version")
    returned_hash = returned_protocol.get("hash") or result.get("protocol_hash")
    version_matches = returned_version == expected.get("version")
    hash_matches = returned_hash == expected.get("hash")
    failures = []
    if not version_matches:
        failures.append("protocol.version mismatch or missing")
    if not hash_matches:
        failures.append("protocol.hash mismatch or missing")
    return {
        "expected_version": expected.get("version"),
        "expected_hash": expected.get("hash"),
        "returned_version": returned_version,
        "returned_hash": returned_hash,
        "version_matches": version_matches,
        "hash_matches": hash_matches,
        "matches": version_matches and hash_matches,
        "failures": failures,
    }


def _split_command(command: str) -> list[str]:
    try:
        import shlex

        return shlex.split(command, posix=os.name != "nt")
    except Exception:
        return [command]


def _provenance_env_var(provider: str) -> str | None:
    return JSON_CLI_PROVENANCE_ENV_VARS.get(provider)


def _production_credential_passed(check: dict[str, Any], check_name: str) -> bool:
    if check_name not in JSON_CLI_ENV_VARS:
        return check.get("ready") is True
    return check.get("ready") is True and check.get("production_credential_passed") is True


def _live_check_passed(live_check: Any) -> bool:
    return isinstance(live_check, dict) and live_check.get("passed") is True


def _provider_command_fingerprint(command: str | None) -> dict[str, Any]:
    if not command:
        return {
            "configured": False,
            "command_sha256": None,
            "artifact_path": None,
            "artifact_exists": False,
            "artifact_sha256": None,
            "artifact_kind": None,
        }
    parts = _split_command(command)
    artifact = _provider_command_artifact(parts)
    artifact_sha256 = _file_sha256(artifact) if artifact and artifact.exists() and artifact.is_file() else None
    return {
        "configured": True,
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "artifact_path": str(artifact) if artifact else None,
        "artifact_exists": bool(artifact and artifact.exists()),
        "artifact_sha256": artifact_sha256,
        "artifact_kind": _provider_command_artifact_kind(artifact),
    }


def _provider_command_artifact(parts: list[str]) -> Path | None:
    candidates = []
    for part in parts:
        try:
            path = Path(part)
        except (OSError, ValueError):
            continue
        if path.suffix.lower() == ".py":
            candidates.insert(0, path)
        elif path.exists() and path.is_file():
            candidates.append(path)
    if not candidates:
        return None
    try:
        return candidates[0].resolve()
    except OSError:
        return candidates[0]


def _provider_command_artifact_kind(path: Path | None) -> str | None:
    if path is None:
        return None
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python_script"
    if os.access(path, os.X_OK):
        return "executable"
    return "file"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command_is_bundled_example(command: str | None) -> bool:
    if not command:
        return False
    parts = _split_command(command)
    example_paths = [part for part in parts if part.endswith("_json_cli_example.py")]
    if not example_paths:
        return False
    provider_dir = Path(__file__).resolve().parent / "providers"
    for item in example_paths:
        try:
            path = Path(item).resolve()
        except OSError:
            continue
        if provider_dir in path.parents:
            return True
    return False


def _json_cli_production_blocker(
    *,
    command: str | None,
    provenance: str | None,
    provenance_audit: dict[str, Any],
    provenance_env_var: str | None,
    command_is_bundled_example: bool,
    live: bool,
    live_check: Any,
) -> str | None:
    if not command:
        return "provider command is not configured"
    if command_is_bundled_example:
        return "bundled protocol examples are smoke-test fixtures, not production providers"
    if not provenance:
        return f"{provenance_env_var} is required for production provider provenance"
    if not provenance_audit.get("valid"):
        missing = ", ".join(provenance_audit.get("missing", []))
        return f"{provenance_env_var} must include provider, version, source, and license_or_review; missing: {missing}"
    if live and not _live_check_passed(live_check):
        return "live smoke did not pass"
    return None


def _provider_provenance_audit(provenance: str | None) -> dict[str, Any]:
    required = ["provider", "version", "source", "license_or_review"]
    fields = _parse_provider_provenance(provenance)
    missing = [key for key in required if not fields.get(key)]
    return {
        "valid": not missing,
        "required": required,
        "missing": missing,
        "fields": fields,
        "format": "json_or_semicolon_key_value",
    }


def _parse_provider_provenance(provenance: str | None) -> dict[str, str]:
    if not provenance:
        return {}
    text = provenance.strip()
    if not text:
        return {}
    if text.startswith("{"):
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(key): str(value).strip() for key, value in raw.items() if str(value).strip()}
    fields: dict[str, str] = {}
    for part in text.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            fields[key] = value
    return fields


def _native_build_hint(provider: str) -> str | None:
    if _native_build_risk(provider):
        return (
            f"{provider} or its dependencies may require prebuilt wheels or Microsoft C++ Build Tools "
            f"on Python {sys.version_info.major}.{sys.version_info.minor} for Windows."
        )
    return None
