"""Evaluator metric for professional/external provider contract regressions."""

from __future__ import annotations

from typing import Any

from examples.mingli_5agents.reference_charts import run_reference_chart_checks


REQUIRED_PROVIDER_DOMAINS = {"bazi", "ziwei", "qimen", "astrology", "xuanze"}


def provider_contract_score(result: dict[str, Any], expected: dict[str, Any] | None = None) -> float:
    """Return provider-contract score for fixtures and the actual report.

    Fixed reference charts catch provider adapter regressions. The actual report
    governance check catches evolved candidates that keep the adapters working
    but drop provider-readiness boundaries from the user-facing synthesis.
    """
    checks = run_reference_chart_checks()
    total = int(checks.get("total", 0))
    if total <= 0:
        return 0.0
    reference_score = float(checks.get("passed_count", 0)) / total
    report_checks = provider_report_governance_checks(result)
    if report_checks["skipped"]:
        return reference_score
    return min(reference_score, report_checks["score"])


def provider_report_governance_checks(result: dict[str, Any]) -> dict[str, Any]:
    """Validate provider readiness metadata on an actual analysis result."""
    final_report = result.get("final_report")
    if not isinstance(final_report, dict):
        return {
            "skipped": True,
            "score": 1.0,
            "passed": True,
            "failures": [],
            "checked_domains": [],
        }

    provider_summary = final_report.get("provider_summary")
    failures: list[str] = []
    if not isinstance(provider_summary, dict):
        return {
            "skipped": False,
            "score": 0.0,
            "passed": False,
            "failures": ["final_report.provider_summary missing"],
            "checked_domains": [],
        }

    domains = provider_summary.get("domains")
    if not isinstance(domains, dict):
        failures.append("provider_summary.domains missing")
        domains = {}
    domain_keys = set(domains)
    missing_domains = sorted(REQUIRED_PROVIDER_DOMAINS - domain_keys)
    extra_domains = sorted(domain_keys - REQUIRED_PROVIDER_DOMAINS)
    if missing_domains:
        failures.append(f"provider_summary.domains missing {missing_domains}")
    if extra_domains:
        failures.append(f"provider_summary.domains has unexpected {extra_domains}")

    blockers = provider_summary.get("production_blockers")
    if not isinstance(blockers, list):
        failures.append("provider_summary.production_blockers must be a list")
        blockers = []
    blocker_set = {str(item) for item in blockers}

    production_ready_domains: set[str] = set()
    fallback_domains: set[str] = set()
    for domain in sorted(REQUIRED_PROVIDER_DOMAINS & domain_keys):
        row = domains.get(domain)
        if not isinstance(row, dict):
            failures.append(f"{domain} provider row must be an object")
            continue
        failures.extend(_provider_row_failures(domain, row))
        if row.get("production_ready") is True:
            production_ready_domains.add(domain)
        else:
            fallback_domains.add(domain)

    if blocker_set != fallback_domains:
        failures.append(
            f"provider_summary.production_blockers must match fallback domains: "
            f"expected {sorted(fallback_domains)}, got {sorted(blocker_set)}"
        )

    production_ready = provider_summary.get("production_ready")
    expected_ready = not fallback_domains and not missing_domains
    if production_ready is not expected_ready:
        failures.append(f"provider_summary.production_ready expected {expected_ready}, got {production_ready!r}")

    status = provider_summary.get("status")
    expected_status = "production_ready" if expected_ready else "ready_with_provider_gaps"
    if status != expected_status:
        failures.append(f"provider_summary.status expected {expected_status!r}, got {status!r}")

    boundary = provider_summary.get("boundary")
    if fallback_domains and not _nonempty_string(boundary):
        failures.append("provider_summary.boundary required when provider gaps exist")

    total_checks = 7 + len(REQUIRED_PROVIDER_DOMAINS) * 10
    passed_checks = max(0, total_checks - len(failures))
    score = passed_checks / total_checks
    return {
        "skipped": False,
        "score": score,
        "passed": not failures,
        "failures": failures,
        "checked_domains": sorted(REQUIRED_PROVIDER_DOMAINS & domain_keys),
    }


def _provider_row_failures(domain: str, row: dict[str, Any]) -> list[str]:
    failures = []
    if row.get("domain") != domain:
        failures.append(f"{domain}.domain expected {domain!r}, got {row.get('domain')!r}")
    if not _nonempty_string(row.get("provider")):
        failures.append(f"{domain}.provider required")
    if not _nonempty_string(row.get("provider_quality")):
        failures.append(f"{domain}.provider_quality required")
    if row.get("status") not in {"professional", "fallback"}:
        failures.append(f"{domain}.status must be professional or fallback")
    if not isinstance(row.get("contract_valid"), bool):
        failures.append(f"{domain}.contract_valid must be bool")
    if not isinstance(row.get("provider_provenance_valid"), bool):
        failures.append(f"{domain}.provider_provenance_valid must be bool")
    if not isinstance(row.get("external_payload_receipt_valid"), bool):
        failures.append(f"{domain}.external_payload_receipt_valid must be bool")
    if not isinstance(row.get("production_ready"), bool):
        failures.append(f"{domain}.production_ready must be bool")

    production_ready = row.get("production_ready")
    quality = str(row.get("provider_quality", ""))
    if quality.startswith("external_"):
        if row.get("external_payload_receipt_valid") is not True:
            failures.append(f"{domain}.external_payload_receipt_valid required for external providers")
        receipt_sha = row.get("external_payload_receipt_sha256")
        if not (isinstance(receipt_sha, str) and len(receipt_sha) == 64):
            failures.append(f"{domain}.external_payload_receipt_sha256 required for external providers")
    expected_status = "professional" if production_ready is True else "fallback"
    if row.get("status") in {"professional", "fallback"} and row.get("status") != expected_status:
        failures.append(f"{domain}.status must match production_ready")
    if production_ready is False and not _nonempty_string(row.get("replacement_boundary")):
        failures.append(f"{domain}.replacement_boundary required for fallback providers")
    if production_ready is True and row.get("replacement_boundary") not in {"", None}:
        failures.append(f"{domain}.replacement_boundary must be empty for production providers")
    return failures


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
