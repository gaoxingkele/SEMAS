"""Audit public industry-event manifests for famous-case calibration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from examples.mingli_5agents.tools.annual_luck import build_annual_luck
from examples.mingli_5agents.tools.bazi_pai_pan import build_bazi_chart


REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "status",
    "purpose",
    "boundary",
    "review",
    "required_record_fields",
    "source_families",
    "split_policy",
    "records",
}

REQUIRED_RECORD_FIELDS = {
    "record_id",
    "case_id",
    "public_name",
    "domain",
    "industry",
    "year",
    "event_topic",
    "event_present",
    "event_type",
    "source_family_id",
    "source_name",
    "source_url",
    "license_or_review",
    "collected_before_rule_change",
    "split_role",
    "negative_year_reason",
}

ALLOWED_SPLIT_ROLES = {"train", "holdout"}
REQUIRED_CROSS_DOMAIN_VALIDATION_DOMAINS = {"film", "music", "sports"}
INDUSTRY_EVENT_TOPIC_SIGNAL_MAP = {
    "business_power": {"categories": {"wealth", "authority"}, "intensities": {"constructive", "active"}},
    "career_project": {"categories": {"expression", "authority", "wealth"}, "intensities": {"constructive", "active"}},
    "public_fame": {"categories": {"expression"}, "intensities": {"constructive", "active", "high-volatility"}},
    "sports_peak": {"categories": {"expression", "authority"}, "intensities": {"constructive", "active"}},
}


def default_industry_event_manifest_path() -> Path:
    return Path(__file__).resolve().parent / "providers" / "industry_event_source_manifest_example.json"


def audit_industry_event_manifest(path: Path) -> dict[str, Any]:
    """Validate a public famous-person industry-event manifest."""
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return audit_industry_event_manifest_payload(payload, path=str(path), raw=raw)


def audit_industry_event_manifest_payload(
    payload: dict[str, Any],
    *,
    path: str = "<memory>",
    raw: bytes | None = None,
) -> dict[str, Any]:
    """Validate an in-memory public famous-person industry-event manifest."""
    if raw is None:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    failures = _manifest_failures(payload)
    records = payload.get("records", []) if isinstance(payload, dict) and isinstance(payload.get("records"), list) else []
    source_families = (
        payload.get("source_families", [])
        if isinstance(payload, dict) and isinstance(payload.get("source_families"), list)
        else []
    )
    positive_count = sum(1 for record in records if isinstance(record, dict) and record.get("event_present") is True)
    negative_count = sum(1 for record in records if isinstance(record, dict) and record.get("event_present") is False)
    source_family_ids = {
        str(item.get("id"))
        for item in source_families
        if isinstance(item, dict) and item.get("id")
    }
    candidate_source_names = sorted(
        {
            str(candidate.get("name"))
            for family in source_families
            if isinstance(family, dict)
            for candidate in family.get("candidate_sources", [])
            if isinstance(candidate, dict) and candidate.get("name")
        }
    )
    reviewed = bool(payload.get("review", {}).get("externally_reviewed")) if isinstance(payload, dict) else False
    production_evidence = (
        reviewed
        and isinstance(payload, dict)
        and payload.get("status") == "reviewed_production_evidence"
        and not failures
    )
    return {
        "status": "ready_for_review" if not failures else "invalid",
        "path": path,
        "valid": not failures,
        "failures": failures,
        "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
        "manifest_status": payload.get("status") if isinstance(payload, dict) else None,
        "production_evidence": production_evidence,
        "externally_reviewed": reviewed,
        "record_count": len(records),
        "positive_event_count": positive_count,
        "negative_event_count": negative_count,
        "has_positive_and_negative_examples": positive_count > 0 and negative_count > 0,
        "domains": sorted(
            {str(record.get("domain")) for record in records if isinstance(record, dict) and record.get("domain")}
        ),
        "industries": sorted(
            {str(record.get("industry")) for record in records if isinstance(record, dict) and record.get("industry")}
        ),
        "event_topics": sorted(
            {str(record.get("event_topic")) for record in records if isinstance(record, dict) and record.get("event_topic")}
        ),
        "split_roles": sorted(
            {str(record.get("split_role")) for record in records if isinstance(record, dict) and record.get("split_role")}
        ),
        "source_family_count": len(source_family_ids),
        "source_families": sorted(source_family_ids),
        "candidate_source_count": len(candidate_source_names),
        "candidate_source_names": candidate_source_names,
        "required_record_fields": sorted(REQUIRED_RECORD_FIELDS),
        "content_hash": hashlib.sha256(raw).hexdigest(),
        "policy": (
            "Industry-event manifests support public famous-case calibration only. "
            "They are not production evidence until externally reviewed and explicitly marked reviewed_production_evidence."
        ),
    }


def industry_event_manifest_receipt(audit: dict[str, Any]) -> dict[str, Any]:
    material = {
        "schema_version": "industry-event-manifest-audit-receipt-v1",
        "path": audit.get("path"),
        "valid": audit.get("valid"),
        "status": audit.get("status"),
        "manifest_schema_version": audit.get("schema_version"),
        "manifest_status": audit.get("manifest_status"),
        "content_hash": audit.get("content_hash"),
        "production_evidence": audit.get("production_evidence"),
        "externally_reviewed": audit.get("externally_reviewed"),
        "record_count": audit.get("record_count"),
        "positive_event_count": audit.get("positive_event_count"),
        "negative_event_count": audit.get("negative_event_count"),
        "domains": audit.get("domains", []),
        "industries": audit.get("industries", []),
        "event_topics": audit.get("event_topics", []),
        "source_families": audit.get("source_families", []),
        "candidate_source_names": audit.get("candidate_source_names", []),
        "failures": audit.get("failures", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def build_industry_event_validation_label_table(path: Path) -> dict[str, Any]:
    """Convert an audited industry-event manifest into annual validation labels."""
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return build_industry_event_validation_label_table_payload(payload, path=str(path), raw=raw)


def build_industry_event_symbolic_scoring_readiness(
    path: Path,
    *,
    birth_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Check which validation labels can enter symbolic annual scoring."""
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return build_industry_event_symbolic_scoring_readiness_payload(
        payload,
        path=str(path),
        raw=raw,
        birth_cases=birth_cases,
    )


def build_industry_event_symbolic_annual_score(
    path: Path,
    *,
    birth_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Score ready industry-event labels against symbolic annual rows."""
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return build_industry_event_symbolic_annual_score_payload(
        payload,
        path=str(path),
        raw=raw,
        birth_cases=birth_cases,
    )


def build_industry_event_symbolic_annual_score_payload(
    payload: dict[str, Any],
    *,
    path: str = "<memory>",
    raw: bytes | None = None,
    birth_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Run symbolic annual diagnostics for labels that have matching birth profiles."""
    readiness = build_industry_event_symbolic_scoring_readiness_payload(
        payload,
        path=path,
        raw=raw,
        birth_cases=birth_cases,
    )
    birth_case_index = _birth_case_index(birth_cases)
    ready_labels = [
        row
        for row in readiness.get("label_readiness", [])
        if isinstance(row, dict) and row.get("scoring_ready") is True
    ]
    scored_labels = _score_ready_industry_event_labels(ready_labels, birth_case_index)
    positive_rows = [row for row in scored_labels if row.get("event_present") is True]
    negative_rows = [row for row in scored_labels if row.get("event_present") is False]
    exact_hit_count = sum(1 for row in positive_rows if row.get("exact_match") is True)
    strict_exact_hit_count = sum(1 for row in positive_rows if row.get("strict_exact_match") is True)
    false_positive_count = sum(1 for row in negative_rows if row.get("false_positive") is True)
    strict_false_positive_count = sum(1 for row in negative_rows if row.get("strict_false_positive") is True)
    domain_topic_summary = _symbolic_annual_score_domain_topic_summary(scored_labels)
    evidence_refinement_queue = _industry_symbolic_evidence_refinement_queue(domain_topic_summary)
    blocked_readiness_summary = _symbolic_blocked_readiness_domain_topic_summary(
        readiness.get("label_readiness", [])
    )
    blocked_readiness_queue = _industry_symbolic_blocked_readiness_queue(blocked_readiness_summary)
    evolution_task_plan = _industry_symbolic_evolution_task_plan(evidence_refinement_queue + blocked_readiness_queue)
    material = {
        "schema_version": "industry-event-symbolic-annual-score-v1",
        "manifest_path": path,
        "readiness_receipt_sha256": readiness.get("symbolic_scoring_readiness_receipt", {}).get("sha256"),
        "label_count": readiness.get("label_count"),
        "scored_label_count": len(scored_labels),
        "blocked_label_count": readiness.get("blocked_label_count"),
        "positive_scored_label_count": len(positive_rows),
        "negative_scored_label_count": len(negative_rows),
        "exact_hit_count": exact_hit_count,
        "strict_exact_hit_count": strict_exact_hit_count,
        "false_positive_count": false_positive_count,
        "strict_false_positive_count": strict_false_positive_count,
        "exact_hit_rate": _rate(exact_hit_count, len(positive_rows)),
        "strict_exact_hit_rate": _rate(strict_exact_hit_count, len(positive_rows)),
        "exact_precision": _rate(exact_hit_count, exact_hit_count + false_positive_count),
        "strict_exact_precision": _rate(strict_exact_hit_count, strict_exact_hit_count + strict_false_positive_count),
        "false_positive_rate": _rate(false_positive_count, len(negative_rows)),
        "strict_false_positive_rate": _rate(strict_false_positive_count, len(negative_rows)),
        "case_summary": _symbolic_annual_score_case_summary(scored_labels),
        "domain_topic_summary": domain_topic_summary,
        "blocked_readiness_domain_topic_summary": blocked_readiness_summary,
        "evidence_refinement_queue": evidence_refinement_queue,
        "blocked_readiness_refinement_queue": blocked_readiness_queue,
        "evolution_task_plan": evolution_task_plan,
        "scored_labels_sha256": _stable_sha256(scored_labels),
    }
    return {
        "schema_version": material["schema_version"],
        "status": "scored_ready_labels" if scored_labels else "blocked_no_ready_labels",
        "valid": readiness.get("valid") is True,
        "offline_only": True,
        "symbolic_scoring_readiness": readiness,
        "scored_labels": scored_labels,
        "symbolic_annual_score_receipt": _receipt("industry-event-symbolic-annual-score-receipt-v1", material),
        **material,
        "boundary": (
            "This is a symbolic annual-signal diagnostic over labels that already have birth profiles. "
            "It is not statistical proof of predictive validity."
        ),
    }


def build_industry_event_symbolic_scoring_readiness_payload(
    payload: dict[str, Any],
    *,
    path: str = "<memory>",
    raw: bytes | None = None,
    birth_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Check label-table readiness without pretending missing birth data can be scored."""
    label_table = build_industry_event_validation_label_table_payload(payload, path=path, raw=raw)
    birth_case_index = _birth_case_index(birth_cases)
    label_rows = [
        _symbolic_scoring_label_readiness(label, birth_case_index, label_table)
        for label in label_table.get("labels", [])
        if isinstance(label, dict)
    ]
    ready_labels = [row for row in label_rows if row.get("scoring_ready") is True]
    blocked_labels = [row for row in label_rows if row.get("scoring_ready") is not True]
    case_summary = _symbolic_scoring_case_summary(label_rows)
    domain_topic_summary = _symbolic_scoring_domain_topic_summary(label_rows)
    material = {
        "schema_version": "industry-event-symbolic-scoring-readiness-v1",
        "manifest_path": path,
        "validation_label_table_receipt_sha256": label_table.get("validation_label_table_receipt", {}).get("sha256"),
        "manifest_valid": label_table.get("manifest_valid"),
        "manifest_status": label_table.get("manifest_status"),
        "production_evidence": label_table.get("production_evidence"),
        "label_count": len(label_rows),
        "ready_label_count": len(ready_labels),
        "blocked_label_count": len(blocked_labels),
        "positive_ready_label_count": sum(1 for row in ready_labels if row.get("event_present") is True),
        "negative_ready_label_count": sum(1 for row in ready_labels if row.get("event_present") is False),
        "case_count": len({str(row.get("case_id")) for row in label_rows if row.get("case_id")}),
        "ready_case_count": len({str(row.get("case_id")) for row in ready_labels if row.get("case_id")}),
        "blocked_case_count": len({str(row.get("case_id")) for row in blocked_labels if row.get("case_id")}),
        "birth_case_count": len(birth_case_index),
        "case_summary": case_summary,
        "domain_topic_summary": domain_topic_summary,
        "gates": _symbolic_scoring_readiness_gates(label_table, label_rows, ready_labels, blocked_labels),
        "labels_sha256": _stable_sha256(label_rows),
    }
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_symbolic_scoring" if material["ready_label_count"] > 0 else "blocked_missing_birth_profiles",
        "valid": label_table.get("valid") is True,
        "offline_only": True,
        "validation_label_table": label_table,
        "label_readiness": label_rows,
        "symbolic_scoring_readiness_receipt": _receipt(
            "industry-event-symbolic-scoring-readiness-receipt-v1",
            material,
        ),
        **material,
        "boundary": (
            "This readiness table only decides which factual labels have birth data for later symbolic scoring. "
            "It does not compute or certify predictive accuracy."
        ),
    }


def build_industry_event_validation_label_table_payload(
    payload: dict[str, Any],
    *,
    path: str = "<memory>",
    raw: bytes | None = None,
) -> dict[str, Any]:
    """Convert an in-memory industry-event manifest into annual validation labels."""
    if raw is None:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    audit = audit_industry_event_manifest_payload(payload, path=path, raw=raw)
    records = payload.get("records", []) if isinstance(payload, dict) and isinstance(payload.get("records"), list) else []
    labels = [_label_from_record(record) for record in records if isinstance(record, dict)]
    domain_topic_summary = _label_domain_topic_summary(labels)
    domain_coverage_summary = _label_domain_coverage_summary(labels)
    cross_domain_coverage_gate = _cross_domain_coverage_gate(domain_coverage_summary)
    material = {
        "schema_version": "industry-event-validation-label-table-v1",
        "manifest_path": path,
        "manifest_content_hash": audit.get("content_hash"),
        "manifest_audit_receipt_sha256": industry_event_manifest_receipt(audit).get("sha256"),
        "manifest_valid": audit.get("valid"),
        "manifest_status": audit.get("manifest_status"),
        "production_evidence": audit.get("production_evidence"),
        "record_count": len(labels),
        "positive_label_count": sum(1 for label in labels if label.get("event_present") is True),
        "negative_label_count": sum(1 for label in labels if label.get("event_present") is False),
        "case_count": len({str(label.get("case_id")) for label in labels if label.get("case_id")}),
        "domains": sorted({str(label.get("domain")) for label in labels if label.get("domain")}),
        "event_topics": sorted({str(label.get("event_topic")) for label in labels if label.get("event_topic")}),
        "split_roles": sorted({str(label.get("split_role")) for label in labels if label.get("split_role")}),
        "domain_coverage_summary": domain_coverage_summary,
        "cross_domain_coverage_gate": cross_domain_coverage_gate,
        "domain_topic_summary": domain_topic_summary,
        "labels_sha256": _stable_sha256(labels),
        "failures": list(audit.get("failures", [])),
    }
    return {
        "status": "ready_for_review" if audit.get("valid") else "invalid",
        "valid": audit.get("valid") is True,
        "offline_only": True,
        "manifest_audit": audit,
        "labels": labels,
        "validation_label_table_receipt": _receipt("industry-event-validation-label-table-receipt-v1", material),
        **material,
        "boundary": (
            "This label table is a factual event-label adapter. It does not score symbolic timing rules "
            "and does not certify production evidence without manifest review."
        ),
    }


def _manifest_failures(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["manifest must be a JSON object"]
    failures: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
    failures.extend(f"missing top-level field: {field}" for field in missing)
    failures.extend(_review_failures(payload.get("review"), payload.get("status")))
    failures.extend(_source_family_failures(payload.get("source_families")))
    failures.extend(_split_policy_failures(payload.get("split_policy")))
    failures.extend(_required_record_fields_failures(payload.get("required_record_fields")))
    failures.extend(_record_failures(payload.get("records"), payload.get("source_families")))
    return failures


def _label_from_record(record: dict[str, Any]) -> dict[str, Any]:
    event_present = record.get("event_present")
    return {
        "label_id": _stable_sha256(
            {
                "record_id": record.get("record_id"),
                "case_id": record.get("case_id"),
                "year": record.get("year"),
                "event_topic": record.get("event_topic"),
                "event_present": event_present,
            }
        )[:16],
        "record_id": record.get("record_id"),
        "case_id": record.get("case_id"),
        "public_name": record.get("public_name"),
        "domain": record.get("domain"),
        "industry": record.get("industry"),
        "year": record.get("year"),
        "event_topic": record.get("event_topic"),
        "event_present": event_present,
        "label_kind": "positive_year" if event_present is True else "negative_year",
        "event_type": record.get("event_type"),
        "split_role": record.get("split_role"),
        "source_family_id": record.get("source_family_id"),
        "source_name": record.get("source_name"),
        "source_url": record.get("source_url"),
        "license_or_review": record.get("license_or_review"),
        "negative_year_reason": record.get("negative_year_reason"),
        "collected_before_rule_change": record.get("collected_before_rule_change"),
    }


def _label_domain_topic_summary(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for label in labels:
        key = (str(label.get("domain")), str(label.get("event_topic")))
        grouped.setdefault(key, []).append(label)
    rows = []
    for (domain, event_topic), group in sorted(grouped.items()):
        rows.append(
            {
                "domain": domain,
                "event_topic": event_topic,
                "label_count": len(group),
                "positive_label_count": sum(1 for item in group if item.get("event_present") is True),
                "negative_label_count": sum(1 for item in group if item.get("event_present") is False),
                "case_count": len({str(item.get("case_id")) for item in group if item.get("case_id")}),
                "year_min": min(int(item.get("year")) for item in group if isinstance(item.get("year"), int)),
                "year_max": max(int(item.get("year")) for item in group if isinstance(item.get("year"), int)),
            }
        )
    return rows


def _label_domain_coverage_summary(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for label in labels:
        domain = str(label.get("domain"))
        grouped.setdefault(domain, []).append(label)
    rows = []
    for domain, group in sorted(grouped.items()):
        positive_count = sum(1 for item in group if item.get("event_present") is True)
        negative_count = sum(1 for item in group if item.get("event_present") is False)
        rows.append(
            {
                "domain": domain,
                "label_count": len(group),
                "positive_label_count": positive_count,
                "negative_label_count": negative_count,
                "case_count": len({str(item.get("case_id")) for item in group if item.get("case_id")}),
                "event_topics": sorted(
                    {str(item.get("event_topic")) for item in group if item.get("event_topic")}
                ),
                "has_positive_and_negative_labels": positive_count > 0 and negative_count > 0,
                "year_min": min(int(item.get("year")) for item in group if isinstance(item.get("year"), int)),
                "year_max": max(int(item.get("year")) for item in group if isinstance(item.get("year"), int)),
            }
        )
    return rows


def _cross_domain_coverage_gate(domain_coverage_summary: list[dict[str, Any]]) -> dict[str, Any]:
    by_domain = {
        str(item.get("domain")): item
        for item in domain_coverage_summary
        if isinstance(item, dict) and item.get("domain")
    }
    missing_domains = sorted(REQUIRED_CROSS_DOMAIN_VALIDATION_DOMAINS - set(by_domain))
    domains_without_positive_negative = sorted(
        domain
        for domain in REQUIRED_CROSS_DOMAIN_VALIDATION_DOMAINS
        if domain in by_domain and by_domain[domain].get("has_positive_and_negative_labels") is not True
    )
    passed = not missing_domains and not domains_without_positive_negative
    return {
        "id": "industry_event_cross_domain_positive_negative_coverage",
        "passed": passed,
        "required_domains": sorted(REQUIRED_CROSS_DOMAIN_VALIDATION_DOMAINS),
        "present_domains": sorted(by_domain),
        "missing_domains": missing_domains,
        "domains_without_positive_negative_labels": domains_without_positive_negative,
        "policy": (
            "Cross-domain celebrity validation requires film, music, and sports labels, with at least "
            "one positive and one negative year in each domain."
        ),
    }


def _birth_case_index(birth_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("id")): case
        for case in birth_cases
        if isinstance(case, dict) and case.get("id") and isinstance(case.get("birth"), dict)
    }


def _symbolic_scoring_label_readiness(
    label: dict[str, Any],
    birth_case_index: dict[str, dict[str, Any]],
    label_table: dict[str, Any],
) -> dict[str, Any]:
    case_id = str(label.get("case_id", ""))
    birth_case = birth_case_index.get(case_id)
    blocking_reasons = []
    if label_table.get("valid") is not True:
        blocking_reasons.append("validation label table is invalid")
    if birth_case is None:
        blocking_reasons.append("missing reviewed birth profile for case_id")
    if not isinstance(label.get("year"), int):
        blocking_reasons.append("label year is not an integer")
    if not label.get("event_topic"):
        blocking_reasons.append("label event_topic is missing")
    if label.get("event_present") not in {True, False}:
        blocking_reasons.append("label event_present is not boolean")
    return {
        "label_id": label.get("label_id"),
        "record_id": label.get("record_id"),
        "case_id": case_id,
        "public_name": label.get("public_name"),
        "domain": label.get("domain"),
        "industry": label.get("industry"),
        "year": label.get("year"),
        "event_topic": label.get("event_topic"),
        "event_present": label.get("event_present"),
        "label_kind": label.get("label_kind"),
        "split_role": label.get("split_role"),
        "scoring_ready": not blocking_reasons,
        "birth_profile_available": birth_case is not None,
        "birth_source_name": birth_case.get("source", {}).get("name") if isinstance(birth_case, dict) else None,
        "birth_source_rating": birth_case.get("source", {}).get("rating") if isinstance(birth_case, dict) else None,
        "blocking_reasons": blocking_reasons,
    }


def _symbolic_scoring_case_summary(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in label_rows:
        grouped.setdefault(str(row.get("case_id")), []).append(row)
    summary = []
    for case_id, rows in sorted(grouped.items()):
        ready = [row for row in rows if row.get("scoring_ready") is True]
        blocked = [row for row in rows if row.get("scoring_ready") is not True]
        blocking_reasons = sorted(
            {
                str(reason)
                for row in blocked
                for reason in row.get("blocking_reasons", [])
                if reason
            }
        )
        summary.append(
            {
                "case_id": case_id,
                "public_name": rows[0].get("public_name") if rows else "",
                "domain": rows[0].get("domain") if rows else "",
                "label_count": len(rows),
                "ready_label_count": len(ready),
                "blocked_label_count": len(blocked),
                "positive_ready_label_count": sum(1 for row in ready if row.get("event_present") is True),
                "negative_ready_label_count": sum(1 for row in ready if row.get("event_present") is False),
                "birth_profile_available": any(row.get("birth_profile_available") is True for row in rows),
                "scoring_ready": len(ready) == len(rows) and bool(rows),
                "blocking_reasons": blocking_reasons,
            }
        )
    return summary


def _symbolic_scoring_domain_topic_summary(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in label_rows:
        key = (str(row.get("domain")), str(row.get("event_topic")))
        grouped.setdefault(key, []).append(row)
    summary = []
    for (domain, event_topic), rows in sorted(grouped.items()):
        ready = [row for row in rows if row.get("scoring_ready") is True]
        summary.append(
            {
                "domain": domain,
                "event_topic": event_topic,
                "label_count": len(rows),
                "ready_label_count": len(ready),
                "blocked_label_count": len(rows) - len(ready),
                "positive_ready_label_count": sum(1 for row in ready if row.get("event_present") is True),
                "negative_ready_label_count": sum(1 for row in ready if row.get("event_present") is False),
                "case_count": len({str(row.get("case_id")) for row in rows if row.get("case_id")}),
                "ready_case_count": len({str(row.get("case_id")) for row in ready if row.get("case_id")}),
                "can_score_false_positive_rate": any(row.get("event_present") is False for row in ready),
            }
        )
    return summary


def _symbolic_scoring_readiness_gates(
    label_table: dict[str, Any],
    label_rows: list[dict[str, Any]],
    ready_labels: list[dict[str, Any]],
    blocked_labels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    positive_ready = sum(1 for row in ready_labels if row.get("event_present") is True)
    negative_ready = sum(1 for row in ready_labels if row.get("event_present") is False)
    blocking_reasons = sorted(
        {
            str(reason)
            for row in blocked_labels
            for reason in row.get("blocking_reasons", [])
            if reason
        }
    )
    return [
        {
            "id": "validation_label_table_valid",
            "passed": label_table.get("valid") is True,
            "reason": "Validation label table is valid." if label_table.get("valid") is True else "Validation label table is invalid.",
        },
        {
            "id": "symbolic_scoring_birth_profile_coverage",
            "passed": bool(label_rows) and not blocked_labels,
            "reason": (
                "Every label has a matching reviewed birth profile."
                if bool(label_rows) and not blocked_labels
                else "Some labels cannot be scored because birth profiles or required label fields are missing."
            ),
            "blocking_reasons": blocking_reasons,
        },
        {
            "id": "symbolic_scoring_positive_negative_ready_labels",
            "passed": positive_ready > 0 and negative_ready > 0,
            "reason": (
                "Ready labels include both positive and negative years."
                if positive_ready > 0 and negative_ready > 0
                else "Symbolic scoring needs at least one ready positive label and one ready negative label."
            ),
            "positive_ready_label_count": positive_ready,
            "negative_ready_label_count": negative_ready,
        },
        label_table.get("cross_domain_coverage_gate", {}),
    ]


def _score_ready_industry_event_labels(
    ready_labels: list[dict[str, Any]],
    birth_case_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for label in ready_labels:
        grouped.setdefault(str(label.get("case_id")), []).append(label)
    scored: list[dict[str, Any]] = []
    for case_id, labels in sorted(grouped.items()):
        birth_case = birth_case_index.get(case_id)
        if not birth_case:
            continue
        years = sorted(int(label["year"]) for label in labels if isinstance(label.get("year"), int))
        if not years:
            continue
        birth = _birth_profile_from_case(birth_case)
        chart = build_bazi_chart(birth)
        annual = build_annual_luck(birth, chart, start_year=min(years), end_year=max(years))
        rows_by_year = {int(row["year"]): row for row in annual.get("rows", [])}
        for label in sorted(labels, key=lambda item: (str(item.get("event_topic")), int(item.get("year", 0)))):
            scored.append(_score_industry_event_label(label, rows_by_year, chart))
    return scored


def _score_industry_event_label(
    label: dict[str, Any],
    rows_by_year: dict[int, dict[str, Any]],
    chart: dict[str, Any],
) -> dict[str, Any]:
    topic_mapping = _symbolic_topic_mapping(label)
    symbolic_topic = topic_mapping["symbolic_event_topic"]
    expected = INDUSTRY_EVENT_TOPIC_SIGNAL_MAP.get(symbolic_topic, {"categories": set(), "intensities": set()})
    year = int(label.get("year"))
    row = rows_by_year.get(year, {})
    evidence = _industry_annual_evidence(row, chart.get("pillars", {}))
    exact_match = _industry_row_matches_event(row, expected)
    strict_match = _industry_row_strictly_matches_event(symbolic_topic, row, expected, evidence)
    event_present = label.get("event_present") is True
    return {
        "label_id": label.get("label_id"),
        "record_id": label.get("record_id"),
        "case_id": label.get("case_id"),
        "public_name": label.get("public_name"),
        "domain": label.get("domain"),
        "industry": label.get("industry"),
        "year": year,
        "event_topic": label.get("event_topic"),
        "symbolic_event_topic": symbolic_topic,
        "topic_mapping_reason": topic_mapping["reason"],
        "event_present": label.get("event_present"),
        "label_kind": label.get("label_kind"),
        "split_role": label.get("split_role"),
        "annual_category": row.get("category", ""),
        "annual_intensity": row.get("intensity", ""),
        "annual_pillar": row.get("ganzhi", ""),
        "annual_useful_state": (
            row.get("bazi_evidence", {}).get("useful_state", "")
            if isinstance(row.get("bazi_evidence"), dict)
            else ""
        ),
        "expected_categories": sorted(expected.get("categories", set())),
        "expected_intensities": sorted(expected.get("intensities", set())),
        "event_evidence": evidence,
        "exact_match": exact_match if event_present else None,
        "strict_exact_match": strict_match if event_present else None,
        "false_positive": exact_match if not event_present else None,
        "strict_false_positive": strict_match if not event_present else None,
        "boundary": (
            "Positive labels count matches; negative labels count false positives. "
            "This is symbolic signal scoring, not proof of prediction."
        ),
    }


def _symbolic_topic_mapping(label: dict[str, Any]) -> dict[str, str]:
    topic = str(label.get("event_topic", ""))
    domain = str(label.get("domain", ""))
    if topic == "career_peak" and domain == "sports":
        return {
            "symbolic_event_topic": "sports_peak",
            "reason": "career_peak in sports is scored with sports_peak timing signals",
        }
    if topic == "career_peak":
        return {
            "symbolic_event_topic": "career_project",
            "reason": "career_peak outside sports is scored with career_project timing signals",
        }
    return {
        "symbolic_event_topic": topic,
        "reason": "event topic already has a direct symbolic scoring rule",
    }


def _industry_row_matches_event(row: dict[str, Any], expected: dict[str, set[str]]) -> bool:
    if not row:
        return False
    return str(row.get("category", "")) in expected.get("categories", set()) or str(row.get("intensity", "")) in expected.get(
        "intensities", set()
    )


def _industry_row_strictly_matches_event(
    topic: str,
    row: dict[str, Any],
    expected: dict[str, set[str]],
    evidence: dict[str, Any],
) -> bool:
    if not row:
        return False
    category = str(row.get("category", ""))
    intensity = str(row.get("intensity", ""))
    category_match = category in expected.get("categories", set())
    constructive = intensity in {"constructive", "active"}
    useful_state = str(evidence.get("useful_state", ""))
    useful_or_pressure = useful_state in {"useful_element_activated", "dominant_element_reinforced"}
    major_or_natal = bool(evidence.get("major_luck_active")) or bool(evidence.get("natal_activation"))
    event_markers = evidence.get("event_markers", {}) if isinstance(evidence.get("event_markers"), dict) else {}
    if topic == "public_fame":
        return bool(evidence.get("has_expression")) and category == "expression" and (useful_or_pressure or major_or_natal)
    if topic == "sports_peak":
        return category in {"expression", "authority"} and constructive and (
            bool(evidence.get("has_expression")) or bool(evidence.get("has_authority"))
        )
    if topic == "career_project":
        return category_match and bool(event_markers.get("career_launch")) and (
            useful_or_pressure or bool(evidence.get("natal_activation"))
        )
    if topic == "business_power":
        return category in {"wealth", "authority"} and (
            bool(evidence.get("has_authority")) or bool(evidence.get("has_wealth"))
        ) and major_or_natal
    return category_match and (constructive or useful_or_pressure)


def _industry_annual_evidence(row: dict[str, Any], natal_pillars: object) -> dict[str, Any]:
    bazi_evidence = row.get("bazi_evidence", {}) if isinstance(row.get("bazi_evidence"), dict) else {}
    event_markers = row.get("event_markers", {}) if isinstance(row.get("event_markers"), dict) else {}
    annual_ten_gods = bazi_evidence.get("annual_ten_gods", {}) if isinstance(bazi_evidence, dict) else {}
    ten_gods = {
        str(value)
        for value in annual_ten_gods.values()
        if isinstance(value, str) and value
    }
    active_major_luck = bazi_evidence.get("active_major_luck", {}) if isinstance(bazi_evidence, dict) else {}
    natal_matches = bazi_evidence.get("natal_pillar_matches", []) if isinstance(bazi_evidence, dict) else []
    return {
        "ten_gods": sorted(ten_gods),
        "has_expression": "expression" in ten_gods,
        "has_authority": "authority" in ten_gods,
        "has_wealth": "wealth" in ten_gods,
        "has_resource": "resource" in ten_gods or "learning" in ten_gods,
        "has_peer": "peer" in ten_gods,
        "event_markers": dict(sorted(event_markers.items())),
        "major_luck_active": bool(active_major_luck),
        "natal_activation": bool(natal_matches),
        "useful_state": str(bazi_evidence.get("useful_state", "")),
        "natal_pillars_sha256": _stable_sha256(natal_pillars)[:16],
    }


def _symbolic_annual_score_case_summary(scored_labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in scored_labels:
        grouped.setdefault(str(row.get("case_id")), []).append(row)
    summary = []
    for case_id, rows in sorted(grouped.items()):
        positives = [row for row in rows if row.get("event_present") is True]
        negatives = [row for row in rows if row.get("event_present") is False]
        exact_hits = sum(1 for row in positives if row.get("exact_match") is True)
        strict_hits = sum(1 for row in positives if row.get("strict_exact_match") is True)
        false_positives = sum(1 for row in negatives if row.get("false_positive") is True)
        strict_false_positives = sum(1 for row in negatives if row.get("strict_false_positive") is True)
        summary.append(
            {
                "case_id": case_id,
                "public_name": rows[0].get("public_name") if rows else "",
                "domain": rows[0].get("domain") if rows else "",
                "scored_label_count": len(rows),
                "positive_label_count": len(positives),
                "negative_label_count": len(negatives),
                "exact_hit_rate": _rate(exact_hits, len(positives)),
                "strict_exact_hit_rate": _rate(strict_hits, len(positives)),
                "false_positive_rate": _rate(false_positives, len(negatives)),
                "strict_false_positive_rate": _rate(strict_false_positives, len(negatives)),
            }
        )
    return summary


def _symbolic_annual_score_domain_topic_summary(scored_labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in scored_labels:
        grouped.setdefault((str(row.get("domain")), str(row.get("symbolic_event_topic"))), []).append(row)
    summary = []
    for (domain, topic), rows in sorted(grouped.items()):
        positives = [row for row in rows if row.get("event_present") is True]
        negatives = [row for row in rows if row.get("event_present") is False]
        exact_hits = sum(1 for row in positives if row.get("exact_match") is True)
        strict_hits = sum(1 for row in positives if row.get("strict_exact_match") is True)
        false_positives = sum(1 for row in negatives if row.get("false_positive") is True)
        strict_false_positives = sum(1 for row in negatives if row.get("strict_false_positive") is True)
        summary.append(
            {
                "domain": domain,
                "symbolic_event_topic": topic,
                "scored_label_count": len(rows),
                "case_count": len({str(row.get("case_id")) for row in rows if row.get("case_id")}),
                "positive_label_count": len(positives),
                "negative_label_count": len(negatives),
                "exact_hit_rate": _rate(exact_hits, len(positives)),
                "strict_exact_hit_rate": _rate(strict_hits, len(positives)),
                "exact_precision": _rate(exact_hits, exact_hits + false_positives),
                "strict_exact_precision": _rate(strict_hits, strict_hits + strict_false_positives),
                "false_positive_rate": _rate(false_positives, len(negatives)),
                "strict_false_positive_rate": _rate(strict_false_positives, len(negatives)),
            }
        )
    return summary


def _industry_symbolic_evidence_refinement_queue(domain_topic_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for row in domain_topic_summary:
        scored_count = int(row.get("scored_label_count", 0))
        positive_count = int(row.get("positive_label_count", 0))
        negative_count = int(row.get("negative_label_count", 0))
        strict_hit_rate = float(row.get("strict_exact_hit_rate", 0.0))
        strict_false_positive_rate = float(row.get("strict_false_positive_rate", 0.0))
        if positive_count < 3 or negative_count < 3:
            priority = "high"
            task_type = "expand_ready_labels"
        elif strict_false_positive_rate >= 0.2:
            priority = "high"
            task_type = "reduce_false_positive"
        elif strict_hit_rate < 0.2:
            priority = "medium"
            task_type = "add_specific_evidence"
        else:
            priority = "watch"
            task_type = "monitor"
        topic = str(row.get("symbolic_event_topic", ""))
        domain = str(row.get("domain", ""))
        queue.append(
            {
                "task_id": f"industry-symbolic-{domain}-{topic}-{task_type}",
                "domain": domain,
                "symbolic_event_topic": topic,
                "priority": priority,
                "task_type": task_type,
                "scored_label_count": scored_count,
                "positive_label_count": positive_count,
                "negative_label_count": negative_count,
                "strict_exact_hit_rate": strict_hit_rate,
                "strict_exact_precision": float(row.get("strict_exact_precision", 0.0)),
                "strict_false_positive_rate": strict_false_positive_rate,
                "recommended_evidence": _industry_recommended_evidence(domain, topic, task_type),
                "reason": _industry_refinement_reason(row, task_type),
                "source": "industry_event_symbolic_annual_score.domain_topic_summary",
            }
        )
    priority_rank = {"high": 0, "medium": 1, "watch": 2, "low": 3}
    task_rank = {
        "add_reviewed_birth_profiles": 0,
        "expand_ready_labels": 1,
        "reduce_false_positive": 2,
        "add_specific_evidence": 3,
        "monitor": 4,
    }
    return sorted(
        queue,
        key=lambda item: (
            priority_rank.get(str(item.get("priority")), 9),
            task_rank.get(str(item.get("task_type")), 9),
            str(item.get("domain")),
            str(item.get("symbolic_event_topic")),
        ),
    )


def _symbolic_blocked_readiness_domain_topic_summary(label_rows: object) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not isinstance(label_rows, list):
        return []
    for row in label_rows:
        if not isinstance(row, dict) or row.get("scoring_ready") is True:
            continue
        topic = _symbolic_topic_mapping(row)["symbolic_event_topic"]
        grouped.setdefault((str(row.get("domain")), topic), []).append(row)
    summary = []
    for (domain, topic), rows in sorted(grouped.items()):
        blocking_reasons = sorted(
            {
                str(reason)
                for row in rows
                for reason in row.get("blocking_reasons", [])
                if reason
            }
        )
        summary.append(
            {
                "domain": domain,
                "symbolic_event_topic": topic,
                "blocked_label_count": len(rows),
                "blocked_case_count": len({str(row.get("case_id")) for row in rows if row.get("case_id")}),
                "positive_blocked_label_count": sum(1 for row in rows if row.get("event_present") is True),
                "negative_blocked_label_count": sum(1 for row in rows if row.get("event_present") is False),
                "case_ids": sorted({str(row.get("case_id")) for row in rows if row.get("case_id")}),
                "public_names": sorted({str(row.get("public_name")) for row in rows if row.get("public_name")}),
                "blocking_reasons": blocking_reasons,
            }
        )
    return summary


def _industry_symbolic_blocked_readiness_queue(
    blocked_readiness_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue = []
    for row in blocked_readiness_summary:
        domain = str(row.get("domain", ""))
        topic = str(row.get("symbolic_event_topic", ""))
        task_type = "add_reviewed_birth_profiles"
        queue.append(
            {
                "task_id": f"industry-symbolic-{domain}-{topic}-{task_type}",
                "domain": domain,
                "symbolic_event_topic": topic,
                "priority": "high",
                "task_type": task_type,
                "scored_label_count": 0,
                "positive_label_count": 0,
                "negative_label_count": 0,
                "strict_exact_hit_rate": 0.0,
                "strict_exact_precision": 0.0,
                "strict_false_positive_rate": 0.0,
                "blocked_label_count": row.get("blocked_label_count", 0),
                "blocked_case_count": row.get("blocked_case_count", 0),
                "blocked_case_ids": row.get("case_ids", []),
                "blocked_public_names": row.get("public_names", []),
                "blocking_reasons": row.get("blocking_reasons", []),
                "recommended_evidence": [
                    f"reviewed birth profile for blocked {domain}/{topic} cases",
                    "birth source name, source URL, rating, date, time, gender, and birthplace",
                    "matching case_id between birth fixture and industry-event labels",
                ],
                "reason": (
                    "This domain-topic slice has event labels but cannot enter symbolic scoring until "
                    "birth profiles are reviewed."
                ),
                "source": "industry_event_symbolic_scoring_readiness.blocked_labels",
            }
        )
    return sorted(queue, key=lambda item: (str(item.get("domain")), str(item.get("symbolic_event_topic"))))


def _industry_symbolic_evolution_task_plan(refinement_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": item.get("task_id"),
            "domain": item.get("domain"),
            "symbolic_event_topic": item.get("symbolic_event_topic"),
            "priority": item.get("priority"),
            "task_type": item.get("task_type"),
            "next_evidence_to_add": item.get("recommended_evidence", []),
            "acceptance_criteria": _industry_task_acceptance_criteria(str(item.get("task_type", ""))),
            "current_metrics": {
                "scored_label_count": item.get("scored_label_count"),
                "positive_label_count": item.get("positive_label_count"),
                "negative_label_count": item.get("negative_label_count"),
                "strict_exact_hit_rate": item.get("strict_exact_hit_rate"),
                "strict_exact_precision": item.get("strict_exact_precision"),
                "strict_false_positive_rate": item.get("strict_false_positive_rate"),
                "blocked_label_count": item.get("blocked_label_count", 0),
                "blocked_case_count": item.get("blocked_case_count", 0),
            },
            "blocked_case_ids": item.get("blocked_case_ids", []),
            "blocked_public_names": item.get("blocked_public_names", []),
            "blocking_reasons": item.get("blocking_reasons", []),
            "boundary": (
                "This task plan guides evidence and rule work for industry-event diagnostics. "
                "It is not permission to claim predictive validity."
            ),
        }
        for item in refinement_queue
    ]


def _industry_recommended_evidence(domain: str, topic: str, task_type: str) -> list[str]:
    base = {
        "public_fame": [
            "structured public visibility marker from award, box-office, ranking, media, or release evidence",
            "annual row marker linking expression output to public recognition",
            "negative-year evidence showing no comparable visibility event in the source window",
        ],
        "sports_peak": [
            "structured competition result marker with title, ranking, medal, or record field",
            "sports achievement subtype distinguishing breakthrough, peak, comeback, and retirement",
            "negative-year evidence for seasons without title, ranking, or record breakthrough",
        ],
        "career_project": [
            "structured project launch marker with release, debut, contract, or representative work field",
            "role of the project in public career stage: entry, breakthrough, consolidation, relaunch",
            "negative-year evidence for years without comparable project launch",
        ],
        "business_power": [
            "structured ownership, leadership, production, or company-control marker",
            "authority transition marker distinguishing role title from public fame",
            "negative-year evidence for years without role-power change",
        ],
    }
    evidence = list(base.get(topic, ["domain-specific event marker", "positive and negative source-window evidence"]))
    if task_type == "expand_ready_labels":
        evidence.insert(0, f"more reviewed birth profiles and positive/negative labels for {domain}/{topic}")
    if task_type == "reduce_false_positive":
        evidence.append("stricter negative-year contrast before changing symbolic predicates")
    return evidence


def _industry_refinement_reason(row: dict[str, Any], task_type: str) -> str:
    if task_type == "expand_ready_labels":
        return (
            "Ready positive or negative labels are below the minimum needed for stable hit/false-positive diagnostics."
        )
    if task_type == "reduce_false_positive":
        return "Strict false-positive rate is high enough that rule tightening should precede recall improvements."
    if task_type == "add_specific_evidence":
        return "Strict hit rate is low, so the next step is stronger event-specific evidence rather than looser rules."
    return "Current slice should be monitored until more labels or stronger evidence change the diagnostic."


def _industry_task_acceptance_criteria(task_type: str) -> list[str]:
    if task_type == "add_reviewed_birth_profiles":
        return [
            "every blocked label in the domain-topic slice has a matching reviewed birth profile",
            "birth profile source name, URL, rating, date, time, gender, and birthplace are recorded",
            "readiness receipt shows the slice moving from blocked to scoreable before symbolic scoring",
        ]
    if task_type == "expand_ready_labels":
        return [
            "at least three ready positive labels and three ready negative labels for the domain-topic slice",
            "all added labels have reviewed source windows and matching birth profiles",
            "score receipt changes are recorded before any symbolic rule change",
        ]
    if task_type == "reduce_false_positive":
        return [
            "strict false-positive rate decreases versus current slice",
            "strict exact precision does not decrease",
            "rejected rule variants are retained with metrics",
        ]
    if task_type == "add_specific_evidence":
        return [
            "new structured evidence marker is observable in annual rows or event labels",
            "strict hit rate improves or the rejected candidate is recorded",
            "strict false-positive rate does not increase materially",
        ]
    return ["monitor metrics after additional reviewed labels are added"]


def _birth_profile_from_case(case: dict[str, Any]) -> dict[str, Any]:
    birth = case["birth"]
    year, month, day = str(birth["birth_date"]).split("-")
    hour, minute = str(birth["birth_time"]).split(":")
    return {
        "name": case.get("name", case.get("id", "")),
        "gender": birth["gender"],
        "year": int(year),
        "month": int(month),
        "day": int(day),
        "hour": int(hour),
        "minute": int(minute),
        "place": birth["birthplace"],
    }


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def _receipt(schema_version: str, material: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": schema_version,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _stable_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _review_failures(review: Any, status: Any) -> list[str]:
    if not isinstance(review, dict):
        return ["review must be an object"]
    failures = []
    reviewed = review.get("externally_reviewed")
    if not isinstance(reviewed, bool):
        failures.append("review.externally_reviewed must be boolean")
    if reviewed is True:
        if not review.get("reviewer"):
            failures.append("review.reviewer is required when externally reviewed")
        if not review.get("review_date"):
            failures.append("review.review_date is required when externally reviewed")
        if review.get("approval") not in {"approved_for_audit_only", "approved_for_production_evidence"}:
            failures.append("review.approval must be approved_for_audit_only or approved_for_production_evidence")
        if status == "reviewed_production_evidence" and review.get("approval") != "approved_for_production_evidence":
            failures.append("reviewed production evidence requires production evidence approval")
    else:
        if status == "reviewed_production_evidence":
            failures.append("reviewed_production_evidence status requires review.externally_reviewed true")
    return failures


def _source_family_failures(source_families: Any) -> list[str]:
    if not isinstance(source_families, list) or not source_families:
        return ["source_families must be a non-empty list"]
    failures = []
    ids = set()
    for family in source_families:
        if not isinstance(family, dict):
            failures.append("each source family must be an object")
            continue
        family_id = str(family.get("id", ""))
        if not family_id:
            failures.append("source family missing id")
        if family_id in ids:
            failures.append(f"duplicate source family id: {family_id}")
        ids.add(family_id)
        candidates = family.get("candidate_sources")
        if not isinstance(candidates, list) or not candidates:
            failures.append(f"source family {family_id} must include candidate_sources")
        else:
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    failures.append(f"source family {family_id} candidate must be an object")
                    continue
                if not candidate.get("name"):
                    failures.append(f"source family {family_id} candidate missing name")
                if not str(candidate.get("url", "")).startswith("https://"):
                    failures.append(f"source family {family_id} candidate url must be https")
    return failures


def _split_policy_failures(split_policy: Any) -> list[str]:
    if not isinstance(split_policy, dict):
        return ["split_policy must be an object"]
    failures = []
    if split_policy.get("frozen_before_rule_change") is not True:
        failures.append("split_policy.frozen_before_rule_change must be true")
    roles = split_policy.get("allowed_split_roles")
    if not isinstance(roles, list) or set(roles) != ALLOWED_SPLIT_ROLES:
        failures.append("split_policy.allowed_split_roles must be train and holdout")
    if not split_policy.get("negative_year_rule"):
        failures.append("split_policy.negative_year_rule is required")
    return failures


def _required_record_fields_failures(fields: Any) -> list[str]:
    if not isinstance(fields, list):
        return ["required_record_fields must be a list"]
    missing = sorted(REQUIRED_RECORD_FIELDS - {str(field) for field in fields})
    return [f"required_record_fields missing: {field}" for field in missing]


def _record_failures(records: Any, source_families: Any) -> list[str]:
    if not isinstance(records, list) or not records:
        return ["records must be a non-empty list"]
    family_ids = {
        str(item.get("id"))
        for item in source_families
        if isinstance(source_families, list) and isinstance(item, dict) and item.get("id")
    }
    failures = []
    record_ids = set()
    positive_count = 0
    negative_count = 0
    for record in records:
        if not isinstance(record, dict):
            failures.append("each record must be an object")
            continue
        record_id = str(record.get("record_id", ""))
        if not record_id:
            failures.append("record missing record_id")
        if record_id in record_ids:
            failures.append(f"duplicate record_id: {record_id}")
        record_ids.add(record_id)
        missing = sorted(REQUIRED_RECORD_FIELDS - set(record))
        failures.extend(f"record {record_id or '<missing>'} missing field: {field}" for field in missing)
        failures.extend(_single_record_failures(record, family_ids, record_id or "<missing>"))
        if record.get("event_present") is True:
            positive_count += 1
        if record.get("event_present") is False:
            negative_count += 1
    if positive_count == 0:
        failures.append("records must include at least one positive event year")
    if negative_count == 0:
        failures.append("records must include at least one explicit negative year")
    return failures


def _single_record_failures(record: dict[str, Any], family_ids: set[str], record_id: str) -> list[str]:
    failures = []
    if not isinstance(record.get("year"), int):
        failures.append(f"record {record_id} year must be integer")
    if not isinstance(record.get("event_present"), bool):
        failures.append(f"record {record_id} event_present must be boolean")
    if record.get("split_role") not in ALLOWED_SPLIT_ROLES:
        failures.append(f"record {record_id} split_role must be train or holdout")
    if record.get("collected_before_rule_change") is not True:
        failures.append(f"record {record_id} collected_before_rule_change must be true")
    if record.get("source_family_id") not in family_ids:
        failures.append(f"record {record_id} source_family_id is not declared")
    if not str(record.get("source_url", "")).startswith("https://"):
        failures.append(f"record {record_id} source_url must be https")
    if record.get("event_present") is False and not record.get("negative_year_reason"):
        failures.append(f"record {record_id} negative_year_reason is required for negative years")
    if record.get("event_present") is True and record.get("negative_year_reason") not in {None, ""}:
        failures.append(f"record {record_id} positive years must not include negative_year_reason")
    for field in ("case_id", "public_name", "domain", "industry", "event_topic", "event_type", "source_name"):
        if not record.get(field):
            failures.append(f"record {record_id} {field} is required")
    return failures
