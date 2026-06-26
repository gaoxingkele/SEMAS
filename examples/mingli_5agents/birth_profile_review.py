"""Review-manifest audit for celebrity birth-profile collection tasks."""

from __future__ import annotations

import hashlib
import json
from pprint import pformat
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_BIRTH_PROFILE_REVIEW_MANIFEST = BASE_DIR / "providers" / "birth_profile_review_manifest_example.json"

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "status",
    "purpose",
    "boundary",
    "review",
    "required_profile_fields",
    "source_policy",
    "review_requests",
}
REQUIRED_REVIEW_REQUEST_FIELDS = {
    "case_id",
    "public_name",
    "domain",
    "identity_source_url",
    "missing_profile_fields",
    "suggested_search_queries",
    "blocked_symbolic_event_topics",
    "blocked_label_count",
    "review_status",
    "collected_before_rule_change",
}
REQUIRED_PROFILE_FIELDS = {
    "case_id",
    "public_name",
    "domain",
    "birth_date",
    "birth_time",
    "gender",
    "birthplace",
    "source_name",
    "source_url",
    "source_rating",
    "source_note",
    "identity_source_url",
    "review_status",
    "collected_before_rule_change",
}
ALLOWED_DOMAINS = {"film", "music", "sports"}
ALLOWED_REVIEW_STATUSES = {"not_started", "in_review", "externally_reviewed", "rejected"}
EXAMPLE_MANIFEST_STATUS = "example_only_requires_external_review"
REVIEWED_MANIFEST_STATUS = "reviewed_ready_for_import"
SUBSTANTIVE_BIRTH_EVIDENCE_FIELDS = {"birth_date", "birth_time", "gender", "birthplace"}
SOURCE_FAMILY_CATALOG = [
    {
        "source_family_id": "rated_birth_time_source",
        "name": "Astro-Databank or equivalent rated birth-data source",
        "url": "https://www.astro.com/astro-databank/Main_Page",
        "domain_fit": ["film", "music", "sports"],
        "usable_for_fields": ["birth_date", "birth_time", "birthplace", "source_rating"],
        "minimum_use": "birth_time_evidence",
        "trust_tier": "primary_for_birth_time_when_rated",
        "disallowed_use": "Do not use an unrated, quoted, or copied page as birth-time evidence without reviewer notes.",
    },
    {
        "source_family_id": "wikidata_identity_anchor",
        "name": "Wikidata Query Service",
        "url": "https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/Wikidata_Query_Help",
        "domain_fit": ["film", "music", "sports"],
        "usable_for_fields": ["birth_date", "birthplace", "gender", "identity_source_url"],
        "minimum_use": "identity_anchor_only",
        "trust_tier": "secondary_identity_anchor",
        "disallowed_use": "Do not use Wikidata alone as birth-time evidence.",
    },
    {
        "source_family_id": "film_identity_and_work_anchor",
        "name": "IMDb Non-Commercial Datasets",
        "url": "https://developer.imdb.com/non-commercial-datasets/",
        "domain_fit": ["film"],
        "usable_for_fields": ["birth_date", "public_name", "identity_source_url"],
        "minimum_use": "film_identity_and_work_anchor",
        "trust_tier": "secondary_domain_anchor",
        "disallowed_use": "Do not use IMDb dataset fields as birth-time evidence.",
    },
    {
        "source_family_id": "music_identity_and_work_anchor",
        "name": "MusicBrainz Database",
        "url": "https://musicbrainz.org/doc/MusicBrainz_Database",
        "domain_fit": ["music"],
        "usable_for_fields": ["birth_date", "public_name", "identity_source_url"],
        "minimum_use": "music_identity_and_work_anchor",
        "trust_tier": "secondary_domain_anchor",
        "disallowed_use": "Do not use MusicBrainz artist metadata as birth-time evidence.",
    },
    {
        "source_family_id": "sports_identity_and_result_anchor",
        "name": "Olympedia",
        "url": "https://www.olympedia.org/",
        "domain_fit": ["sports"],
        "usable_for_fields": ["birth_date", "birthplace", "public_name", "identity_source_url"],
        "minimum_use": "sports_identity_and_result_anchor",
        "trust_tier": "secondary_domain_anchor",
        "disallowed_use": "Do not use Olympedia athlete metadata as birth-time evidence.",
    },
]


def default_birth_profile_review_manifest_path() -> Path:
    return DEFAULT_BIRTH_PROFILE_REVIEW_MANIFEST


def birth_profile_source_family_catalog() -> dict[str, Any]:
    """Return the allowed source-family catalog for celebrity birth-profile review."""
    material = {
        "schema_version": "birth-profile-source-family-catalog-v1",
        "source_family_count": len(SOURCE_FAMILY_CATALOG),
        "source_families": SOURCE_FAMILY_CATALOG,
        "birth_time_policy": (
            "Only a rated or explicitly reviewed birth-data source may satisfy birth_time. "
            "Domain databases and public entity pages are identity/event anchors, not birth-time proof."
        ),
        "boundary": "This catalog guides source review. It does not certify any individual birth profile.",
    }
    receipt = _receipt("birth-profile-source-family-catalog-receipt-v1", material)
    return {
        **material,
        "source_family_catalog_receipt": receipt,
        "source_family_catalog_sha256": _stable_sha256(material),
    }


def audit_birth_profile_review_manifest(path: Path | None = None) -> dict[str, Any]:
    """Audit a birth-profile review worklist without promoting it to sourced fixture data."""
    selected_path = path or default_birth_profile_review_manifest_path()
    try:
        raw = selected_path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _invalid_audit(selected_path, [str(exc)])
    failures = _manifest_failures(payload)
    requests = payload.get("review_requests", []) if isinstance(payload, dict) else []
    request_rows = [request for request in requests if isinstance(request, dict)]
    domain_summary = _domain_summary(request_rows)
    ready_for_import = _ready_for_import(payload, request_rows, failures) if isinstance(payload, dict) else False
    production_evidence = ready_for_import
    material = {
        "schema_version": "birth-profile-review-manifest-audit-v1",
        "manifest_path": str(selected_path),
        "manifest_content_hash": hashlib.sha256(raw).hexdigest(),
        "manifest_schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
        "manifest_status": payload.get("status") if isinstance(payload, dict) else None,
        "externally_reviewed": payload.get("review", {}).get("externally_reviewed") is True
        if isinstance(payload, dict) and isinstance(payload.get("review"), dict)
        else False,
        "request_count": len(request_rows),
        "case_count": len({str(item.get("case_id")) for item in request_rows if item.get("case_id")}),
        "domains": sorted({str(item.get("domain")) for item in request_rows if item.get("domain")}),
        "domain_summary": domain_summary,
        "source_policy": payload.get("source_policy", {}) if isinstance(payload, dict) else {},
        "blocked_label_count": sum(
            int(item.get("blocked_label_count", 0))
            for item in request_rows
            if isinstance(item.get("blocked_label_count"), int)
        ),
        "ready_for_import": ready_for_import,
        "failures": failures,
    }
    return {
        "schema_version": material["schema_version"],
        "status": _audit_status(failures, ready_for_import),
        "valid": not failures,
        "production_evidence": production_evidence,
        "offline_only": True,
        "review_requests": request_rows,
        "birth_profile_review_manifest_receipt": _receipt("birth-profile-review-manifest-receipt-v1", material),
        **material,
        "boundary": (
            "This audit validates a birth-profile collection worklist only. It does not certify any birth data "
            "or allow symbolic scoring for blocked celebrity labels."
        ),
    }


def birth_profile_review_manifest_receipt(audit: dict[str, Any]) -> dict[str, Any]:
    material = {
        "schema_version": "birth-profile-review-manifest-summary-v1",
        "manifest_path": audit.get("manifest_path"),
        "manifest_content_hash": audit.get("manifest_content_hash"),
        "status": audit.get("status"),
        "valid": audit.get("valid") is True,
        "production_evidence": audit.get("production_evidence") is True,
        "externally_reviewed": audit.get("externally_reviewed") is True,
        "request_count": audit.get("request_count", 0),
        "case_count": audit.get("case_count", 0),
        "domains": audit.get("domains", []),
        "blocked_label_count": audit.get("blocked_label_count", 0),
        "ready_for_import": audit.get("ready_for_import") is True,
        "domain_summary": audit.get("domain_summary", []),
        "failures": audit.get("failures", []),
    }
    return _receipt("birth-profile-review-manifest-summary-receipt-v1", material)


def build_birth_profile_import_preview(path: Path | None = None) -> dict[str, Any]:
    """Build a non-mutating preview for reviewed birth-profile import."""
    audit = audit_birth_profile_review_manifest(path)
    review_receipt = birth_profile_review_manifest_receipt(audit)
    requests = audit.get("review_requests", []) if isinstance(audit.get("review_requests"), list) else []
    import_ready_requests = [request for request in requests if _request_import_ready(request)]
    blocking_reasons = _import_preview_blocking_reasons(audit, requests)
    import_allowed = not blocking_reasons and bool(import_ready_requests)
    candidate_profiles = [_candidate_profile(request) for request in import_ready_requests]
    material = {
        "schema_version": "birth-profile-import-preview-v1",
        "manifest_path": audit.get("manifest_path"),
        "review_manifest_receipt_sha256": review_receipt.get("sha256"),
        "target_fixture": "examples.mingli_5agents.famous_case_validation.FAMOUS_CASES",
        "would_write_file": False,
        "import_allowed": import_allowed,
        "request_count": audit.get("request_count", 0),
        "import_ready_request_count": len(import_ready_requests),
        "blocked_request_count": max(0, int(audit.get("request_count", 0)) - len(import_ready_requests)),
        "case_ids": sorted(str(request.get("case_id")) for request in requests if isinstance(request, dict)),
        "candidate_profiles": candidate_profiles,
        "domain_summary": audit.get("domain_summary", []),
        "blocking_reasons": blocking_reasons,
        "import_gate": {
            "id": "birth_profile_import_reviewed_profiles_present",
            "passed": import_allowed,
            "reason": _import_gate_reason(import_allowed),
            "blocking_reasons": blocking_reasons,
        },
        "next_action": _import_preview_next_action(import_allowed),
    }
    preview_receipt = _receipt("birth-profile-import-preview-receipt-v1", material)
    preview_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_non_mutating_import_plan" if import_allowed else "blocked_not_ready_for_import",
        "valid": audit.get("valid") is True,
        "offline_only": True,
        "audit": audit,
        "review_manifest_receipt": review_receipt,
        "import_preview_receipt": preview_receipt,
        "import_preview_sha256": preview_sha256,
        "integrity_check": _import_preview_integrity_check(material, preview_receipt, preview_sha256),
        **material,
        "boundary": (
            "This preview is non-mutating. It never authorizes writing famous-case fixtures and does not certify "
            "birth-profile evidence."
        ),
    }


def build_birth_profile_fixture_patch_preview(path: Path | None = None) -> dict[str, Any]:
    """Build a non-mutating patch preview for adding reviewed birth profiles to fixtures."""
    import_preview = build_birth_profile_import_preview(path)
    candidates = import_preview.get("candidate_profiles", [])
    candidate_profiles = [item for item in candidates if isinstance(item, dict)]
    target_path = BASE_DIR / "famous_case_validation.py"
    target_hash = _file_sha256(target_path)
    patch_ready = import_preview.get("import_allowed") is True and bool(candidate_profiles)
    blocking_reasons = [] if patch_ready else _fixture_patch_blocking_reasons(import_preview)
    patch_text = _fixture_patch_text(candidate_profiles) if patch_ready else ""
    patch_sha256 = _stable_sha256({"patch_text": patch_text})
    material = {
        "schema_version": "birth-profile-fixture-patch-preview-v1",
        "manifest_path": import_preview.get("manifest_path"),
        "import_preview_receipt_sha256": import_preview.get("import_preview_receipt", {}).get("sha256")
        if isinstance(import_preview.get("import_preview_receipt"), dict)
        else None,
        "target_file": str(target_path),
        "target_file_sha256": target_hash,
        "would_write_file": False,
        "patch_ready_for_review": patch_ready,
        "candidate_count": len(candidate_profiles),
        "candidate_case_ids": [str(item.get("case_id")) for item in candidate_profiles if item.get("case_id")],
        "candidate_profiles": candidate_profiles,
        "patch_format": "manual_python_fixture_append_v1",
        "patch_text": patch_text,
        "patch_text_sha256": patch_sha256,
        "blocking_reasons": blocking_reasons,
        "patch_gate": {
            "id": "birth_profile_fixture_patch_preview_ready",
            "passed": patch_ready,
            "reason": _fixture_patch_gate_reason(patch_ready),
            "blocking_reasons": blocking_reasons,
        },
        "next_action": _fixture_patch_next_action(patch_ready),
    }
    receipt = _receipt("birth-profile-fixture-patch-preview-receipt-v1", material)
    preview_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_patch_review" if patch_ready else "blocked_not_ready_for_patch_preview",
        "valid": import_preview.get("valid") is True,
        "offline_only": True,
        "import_preview": import_preview,
        "fixture_patch_preview_receipt": receipt,
        "fixture_patch_preview_sha256": preview_sha256,
        "integrity_check": _fixture_patch_integrity_check(material, receipt, preview_sha256),
        **material,
        "boundary": (
            "This preview never writes famous-case fixtures. It only renders the reviewed candidate profiles "
            "as a patch-review payload."
        ),
    }


def build_birth_profile_source_review_workplan(path: Path | None = None) -> dict[str, Any]:
    """Build a non-mutating human source-review workplan from birth-profile review requests."""
    audit = audit_birth_profile_review_manifest(path)
    review_receipt = birth_profile_review_manifest_receipt(audit)
    requests = audit.get("review_requests", []) if isinstance(audit.get("review_requests"), list) else []
    request_rows = [item for item in requests if isinstance(item, dict)]
    work_items = [_source_review_work_item(item, audit) for item in request_rows]
    material = {
        "schema_version": "birth-profile-source-review-workplan-v1",
        "manifest_path": audit.get("manifest_path"),
        "review_manifest_receipt_sha256": review_receipt.get("sha256"),
        "manifest_valid": audit.get("valid") is True,
        "would_fetch_live_sources": False,
        "would_write_review_manifest": False,
        "request_count": audit.get("request_count", 0),
        "work_item_count": len(work_items),
        "domain_summary": audit.get("domain_summary", []),
        "review_progress_summary": _source_review_progress_summary(work_items),
        "field_gap_summary": _source_review_field_gap_summary(work_items),
        "work_items": work_items,
        "source_review_gate": {
            "id": "birth_profile_source_review_required",
            "passed": False,
            "reason": (
                "Birth-profile source review requires a human or approved external source steward to fill and "
                "approve every requested birth field before import."
            ),
            "blocking_reasons": _source_review_blocking_reasons(audit, work_items),
        },
        "next_action": "Review each work item, fill reviewed_profile_draft fields from acceptable sources, then create a reviewed_ready_for_import manifest.",
    }
    receipt = _receipt("birth-profile-source-review-workplan-receipt-v1", material)
    workplan_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_human_source_review" if audit.get("valid") is True else "invalid",
        "valid": audit.get("valid") is True,
        "offline_only": True,
        "audit": audit,
        "review_manifest_receipt": review_receipt,
        "source_review_workplan_receipt": receipt,
        "source_review_workplan_sha256": workplan_sha256,
        "integrity_check": _source_review_workplan_integrity_check(material, receipt, workplan_sha256),
        **material,
        "boundary": (
            "This workplan organizes source review tasks only. It does not fetch live sources, certify birth data, "
            "write review manifests, or unlock symbolic scoring."
        ),
    }


def build_birth_profile_source_lookup_plan(
    path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build a dry-run lookup plan for human review of celebrity birth-profile sources."""
    workplan = build_birth_profile_source_review_workplan(path)
    selected_cache_dir = cache_dir or (BASE_DIR.parents[1] / ".semas_mingli_repo" / "birth_profile_source_cache")
    work_items = workplan.get("work_items", []) if isinstance(workplan.get("work_items"), list) else []
    selected_items = [
        item
        for item in work_items
        if isinstance(item, dict) and (domain is None or item.get("domain") == domain)
    ]
    failures = []
    if domain is not None and domain not in ALLOWED_DOMAINS:
        failures.append(f"domain must be one of film, music, or sports: {domain}")
    if not selected_items:
        failures.append("birth-profile source lookup filter selected no work items")
    lookup_items = [
        _source_lookup_item(item, selected_cache_dir=selected_cache_dir, rank=rank)
        for rank, item in enumerate(selected_items, start=1)
    ]
    material = {
        "schema_version": "birth-profile-source-lookup-plan-v1",
        "manifest_path": workplan.get("manifest_path"),
        "source_review_workplan_receipt_sha256": workplan.get("source_review_workplan_receipt", {}).get("sha256")
        if isinstance(workplan.get("source_review_workplan_receipt"), dict)
        else None,
        "source_family_catalog": birth_profile_source_family_catalog(),
        "cache_dir": str(selected_cache_dir),
        "filters": {"domain": domain},
        "would_fetch_live_sources": False,
        "would_write_cache": False,
        "would_write_review_manifest": False,
        "selected_work_item_count": len(selected_items),
        "lookup_item_count": len(lookup_items),
        "query_count": sum(int(item.get("query_count", 0)) for item in lookup_items),
        "domain_summary": _source_lookup_domain_summary(lookup_items),
        "lookup_items": lookup_items,
        "failures": failures,
        "lookup_gate": {
            "id": "birth_profile_source_lookup_requires_human_execution",
            "passed": False,
            "reason": "This plan only prepares source lookup tasks; a human reviewer must execute and assess sources.",
            "blocking_reasons": _source_lookup_blocking_reasons(workplan, lookup_items, failures),
        },
        "next_action": (
            "Run each suggested query outside this dry-run plan, record acceptable source evidence, then update "
            "the reviewed birth-profile manifest through a separate reviewed step."
        ),
    }
    receipt = _receipt("birth-profile-source-lookup-plan-receipt-v1", material)
    plan_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_manual_lookup" if workplan.get("valid") is True and not failures else "blocked",
        "valid": workplan.get("valid") is True and not failures,
        "offline_only": True,
        "source_review_workplan": workplan,
        "source_lookup_plan_receipt": receipt,
        "source_lookup_plan_sha256": plan_sha256,
        "integrity_check": _source_lookup_plan_integrity_check(material, receipt, plan_sha256),
        **material,
        "boundary": (
            "This lookup plan is dry-run only. It does not fetch webpages, write cache files, certify birth data, "
            "write review manifests, or unlock symbolic scoring."
        ),
    }


def build_birth_profile_source_cache_audit(
    path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Audit manually collected source lookup cache files without importing birth profiles."""
    lookup_plan = build_birth_profile_source_lookup_plan(path, cache_dir=cache_dir, domain=domain)
    lookup_items = lookup_plan.get("lookup_items", []) if isinstance(lookup_plan.get("lookup_items"), list) else []
    planned_queries = [
        query
        for item in lookup_items
        if isinstance(item, dict)
        for query in item.get("planned_queries", [])
        if isinstance(query, dict)
    ]
    cache_items = [_source_cache_audit_item(query) for query in planned_queries]
    failures = [
        failure
        for item in cache_items
        for failure in item.get("failures", [])
        if isinstance(item, dict)
    ]
    material = {
        "schema_version": "birth-profile-source-cache-audit-v1",
        "manifest_path": lookup_plan.get("manifest_path"),
        "source_lookup_plan_receipt_sha256": lookup_plan.get("source_lookup_plan_receipt", {}).get("sha256")
        if isinstance(lookup_plan.get("source_lookup_plan_receipt"), dict)
        else None,
        "cache_dir": lookup_plan.get("cache_dir"),
        "filters": lookup_plan.get("filters", {}),
        "would_fetch_live_sources": False,
        "would_write_cache": False,
        "would_write_review_manifest": False,
        "would_import_profiles": False,
        "expected_cache_count": len(planned_queries),
        "present_cache_count": sum(1 for item in cache_items if item.get("cache_status") == "present"),
        "missing_cache_count": sum(1 for item in cache_items if item.get("cache_status") == "missing"),
        "reviewed_cache_count": sum(1 for item in cache_items if item.get("review_status") == "source_reviewed"),
        "accepted_cache_count": sum(1 for item in cache_items if item.get("source_evidence_acceptable") is True),
        "cache_items": cache_items,
        "failures": failures,
        "cache_audit_gate": {
            "id": "birth_profile_source_cache_requires_reviewed_manifest_draft",
            "passed": False,
            "reason": (
                "Cache audit can inspect manually collected source evidence, but it cannot certify birth profiles "
                "or write a reviewed manifest."
            ),
            "blocking_reasons": _source_cache_audit_blocking_reasons(cache_items, failures),
        },
        "next_action": (
            "Fill missing cache files with reviewed source evidence, resolve cache audit failures, then create a "
            "separate reviewed manifest draft for human approval."
        ),
    }
    receipt = _receipt("birth-profile-source-cache-audit-receipt-v1", material)
    audit_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": _source_cache_audit_status(material),
        "valid": not failures,
        "offline_only": True,
        "source_lookup_plan": lookup_plan,
        "source_cache_audit_receipt": receipt,
        "source_cache_audit_sha256": audit_sha256,
        "integrity_check": _source_cache_audit_integrity_check(material, receipt, audit_sha256),
        **material,
        "boundary": (
            "This audit reads manually prepared cache files only. It does not fetch webpages, write cache files, "
            "certify birth data, write reviewed manifests, import profiles, or unlock symbolic scoring."
        ),
    }


def build_birth_profile_source_cache_template_preview(
    path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build non-mutating JSON templates for manual birth-profile source cache files."""
    lookup_plan = build_birth_profile_source_lookup_plan(path, cache_dir=cache_dir, domain=domain)
    lookup_items = lookup_plan.get("lookup_items", []) if isinstance(lookup_plan.get("lookup_items"), list) else []
    planned_queries = [
        query
        for item in lookup_items
        if isinstance(item, dict)
        for query in item.get("planned_queries", [])
        if isinstance(query, dict)
    ]
    templates = [_source_cache_template_item(query) for query in planned_queries]
    material = {
        "schema_version": "birth-profile-source-cache-template-preview-v1",
        "manifest_path": lookup_plan.get("manifest_path"),
        "source_lookup_plan_receipt_sha256": lookup_plan.get("source_lookup_plan_receipt", {}).get("sha256")
        if isinstance(lookup_plan.get("source_lookup_plan_receipt"), dict)
        else None,
        "cache_dir": lookup_plan.get("cache_dir"),
        "filters": lookup_plan.get("filters", {}),
        "would_write_cache": False,
        "would_fetch_live_sources": False,
        "would_import_profiles": False,
        "template_count": len(templates),
        "templates": templates,
        "template_preview_gate": {
            "id": "birth_profile_source_cache_template_requires_manual_fill",
            "passed": False,
            "reason": "Cache templates require a human reviewer to execute lookup, fill evidence, and choose review_status.",
            "blocking_reasons": _source_cache_template_blocking_reasons(lookup_plan, templates),
        },
        "next_action": (
            "For each template, manually inspect sources, fill the planned cache JSON, then run "
            "birth-profile-source-cache-audit."
        ),
    }
    receipt = _receipt("birth-profile-source-cache-template-preview-receipt-v1", material)
    preview_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_manual_cache_fill" if lookup_plan.get("valid") is True and templates else "blocked",
        "valid": lookup_plan.get("valid") is True and bool(templates),
        "offline_only": True,
        "source_lookup_plan": lookup_plan,
        "source_cache_template_preview_receipt": receipt,
        "source_cache_template_preview_sha256": preview_sha256,
        "integrity_check": _source_cache_template_preview_integrity_check(material, receipt, preview_sha256),
        **material,
        "boundary": (
            "This template preview is non-mutating. It does not fetch sources, write cache files, certify "
            "birth data, or unlock symbolic scoring."
        ),
    }


def build_birth_profile_reviewed_manifest_draft_preview(
    path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build a non-mutating reviewed-manifest draft from accepted source cache evidence."""
    cache_audit = build_birth_profile_source_cache_audit(path, cache_dir=cache_dir, domain=domain)
    source_workplan = cache_audit.get("source_lookup_plan", {}).get("source_review_workplan", {})
    work_items = source_workplan.get("work_items", []) if isinstance(source_workplan, dict) else []
    selected_case_ids = {
        str(item.get("case_id"))
        for item in cache_audit.get("cache_items", [])
        if isinstance(item, dict) and item.get("case_id")
    }
    if selected_case_ids:
        work_items = [
            item
            for item in work_items
            if isinstance(item, dict) and str(item.get("case_id")) in selected_case_ids
        ]
    review_requests = _reviewed_manifest_draft_requests(work_items, cache_audit)
    draft_ready = bool(review_requests) and all(not item.get("missing_profile_fields") for item in review_requests)
    blocking_reasons = [] if draft_ready else _reviewed_manifest_draft_blocking_reasons(work_items, cache_audit)
    draft_manifest = _reviewed_manifest_draft_payload(source_workplan, review_requests, draft_ready)
    draft_text = json.dumps(draft_manifest, ensure_ascii=False, indent=2, sort_keys=False)
    material = {
        "schema_version": "birth-profile-reviewed-manifest-draft-preview-v1",
        "manifest_path": cache_audit.get("manifest_path"),
        "source_cache_audit_receipt_sha256": cache_audit.get("source_cache_audit_receipt", {}).get("sha256")
        if isinstance(cache_audit.get("source_cache_audit_receipt"), dict)
        else None,
        "would_write_review_manifest": False,
        "would_import_profiles": False,
        "draft_ready_for_human_approval": draft_ready,
        "review_request_count": len(review_requests),
        "complete_review_request_count": sum(1 for item in review_requests if not item.get("missing_profile_fields")),
        "incomplete_review_request_count": sum(1 for item in review_requests if item.get("missing_profile_fields")),
        "draft_manifest": draft_manifest,
        "draft_manifest_sha256": _stable_sha256(draft_manifest),
        "draft_text": draft_text,
        "draft_text_sha256": _stable_sha256({"draft_text": draft_text}),
        "blocking_reasons": blocking_reasons,
        "draft_gate": {
            "id": "birth_profile_reviewed_manifest_draft_requires_human_approval",
            "passed": False,
            "reason": "Reviewed manifest drafts require explicit human approval before import preview.",
            "blocking_reasons": blocking_reasons,
        },
        "next_action": (
            "Review the draft manifest, verify every source note and rating, then write a separate approved "
            "reviewed manifest only after human approval."
        ),
    }
    receipt = _receipt("birth-profile-reviewed-manifest-draft-preview-receipt-v1", material)
    preview_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_human_approval" if draft_ready else "blocked_waiting_for_complete_source_cache",
        "valid": cache_audit.get("valid") is True,
        "offline_only": True,
        "source_cache_audit": cache_audit,
        "reviewed_manifest_draft_preview_receipt": receipt,
        "reviewed_manifest_draft_preview_sha256": preview_sha256,
        "integrity_check": _reviewed_manifest_draft_preview_integrity_check(material, receipt, preview_sha256),
        **material,
        "boundary": (
            "This preview does not write reviewed manifests, import profiles, certify birth data, or unlock "
            "symbolic scoring."
        ),
    }


def build_birth_profile_reviewed_manifest_file_preview(
    path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
    target_path: Path | None = None,
) -> dict[str, Any]:
    """Build a non-mutating file-write preview for an approved reviewed manifest draft."""
    draft_preview = build_birth_profile_reviewed_manifest_draft_preview(path, cache_dir=cache_dir, domain=domain)
    selected_target = target_path or (BASE_DIR / "providers" / "birth_profile_review_manifest_reviewed.json")
    write_ready = draft_preview.get("draft_ready_for_human_approval") is True
    blocking_reasons = [] if write_ready else _reviewed_manifest_file_preview_blocking_reasons(draft_preview)
    material = {
        "schema_version": "birth-profile-reviewed-manifest-file-preview-v1",
        "manifest_path": draft_preview.get("manifest_path"),
        "reviewed_manifest_draft_preview_receipt_sha256": draft_preview.get(
            "reviewed_manifest_draft_preview_receipt", {}
        ).get("sha256")
        if isinstance(draft_preview.get("reviewed_manifest_draft_preview_receipt"), dict)
        else None,
        "target_file": str(selected_target),
        "target_file_exists": selected_target.exists(),
        "target_file_sha256": _file_sha256(selected_target),
        "would_write_file": False,
        "would_import_profiles": False,
        "write_ready_for_human_approval": write_ready,
        "draft_manifest_sha256": draft_preview.get("draft_manifest_sha256"),
        "draft_text": draft_preview.get("draft_text", ""),
        "draft_text_sha256": draft_preview.get("draft_text_sha256"),
        "blocking_reasons": blocking_reasons,
        "file_preview_gate": {
            "id": "birth_profile_reviewed_manifest_file_write_requires_human_approval",
            "passed": False,
            "reason": "Reviewed manifest file writes require explicit human approval and a separate reviewed step.",
            "blocking_reasons": blocking_reasons,
        },
        "next_action": (
            "After human approval, write draft_text to target_file in a separate explicit operation, then run "
            "birth-profile-import-preview against that reviewed manifest."
        ),
    }
    receipt = _receipt("birth-profile-reviewed-manifest-file-preview-receipt-v1", material)
    preview_sha256 = _stable_sha256(material)
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_file_write_review" if write_ready else "blocked_waiting_for_approved_draft",
        "valid": draft_preview.get("valid") is True,
        "offline_only": True,
        "reviewed_manifest_draft_preview": draft_preview,
        "reviewed_manifest_file_preview_receipt": receipt,
        "reviewed_manifest_file_preview_sha256": preview_sha256,
        "integrity_check": _reviewed_manifest_file_preview_integrity_check(material, receipt, preview_sha256),
        **material,
        "boundary": (
            "This preview does not write reviewed manifests, import profiles, certify birth data, or unlock "
            "symbolic scoring."
        ),
    }


def _import_preview_blocking_reasons(audit: dict[str, Any], requests: list[Any]) -> list[str]:
    reasons = []
    if audit.get("valid") is not True:
        reasons.append("birth profile review manifest is invalid")
    if audit.get("ready_for_import") is not True:
        reasons.append("birth profile review manifest is not marked ready_for_import")
    if audit.get("production_evidence") is not True:
        reasons.append("birth profile review manifest is not production evidence")
    if audit.get("externally_reviewed") is not True:
        reasons.append("birth profile review manifest has not been externally reviewed")
    missing_data_count = sum(
        1
        for request in requests
        if isinstance(request, dict) and bool(request.get("missing_profile_fields"))
    )
    if missing_data_count:
        reasons.append(f"{missing_data_count} review requests still list missing_profile_fields")
    unreviewed_count = sum(
        1
        for request in requests
        if isinstance(request, dict) and request.get("review_status") != "externally_reviewed"
    )
    if unreviewed_count:
        reasons.append(f"{unreviewed_count} review requests are not externally_reviewed")
    return reasons


def _request_import_ready(request: Any) -> bool:
    if not isinstance(request, dict):
        return False
    return (
        request.get("review_status") == "externally_reviewed"
        and not request.get("missing_profile_fields")
        and all(_present(request.get(field)) for field in REQUIRED_PROFILE_FIELDS)
    )


def _candidate_profile(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": request.get("case_id"),
        "public_name": request.get("public_name"),
        "domain": request.get("domain"),
        "birth": {
            "birth_date": request.get("birth_date"),
            "birth_time": request.get("birth_time"),
            "gender": request.get("gender"),
            "birthplace": request.get("birthplace"),
        },
        "source": {
            "name": request.get("source_name"),
            "url": request.get("source_url"),
            "rating": request.get("source_rating"),
            "note": request.get("source_note"),
        },
        "identity_source_url": request.get("identity_source_url"),
        "review_status": request.get("review_status"),
        "collected_before_rule_change": request.get("collected_before_rule_change"),
    }


def _import_gate_reason(import_allowed: bool) -> str:
    if import_allowed:
        return (
            "All selected birth-profile requests have externally reviewed source evidence and complete birth fields; "
            "the preview is still non-mutating and only describes the fixture import plan."
        )
    return (
        "Reviewed birth-profile requests are not importable until every selected request has externally reviewed "
        "source evidence and complete birth fields."
    )


def _import_preview_next_action(import_allowed: bool) -> str:
    if import_allowed:
        return "Review the non-mutating candidate_profiles payload, then generate an explicit fixture patch in a separate step."
    return (
        "Add externally reviewed birth_date, birth_time, gender, birthplace, source name, source URL, "
        "source rating, and source note before generating a fixture patch."
    )


def _fixture_patch_blocking_reasons(import_preview: dict[str, Any]) -> list[str]:
    reasons = list(import_preview.get("blocking_reasons", [])) if isinstance(import_preview.get("blocking_reasons"), list) else []
    if import_preview.get("import_allowed") is not True:
        reasons.append("birth profile import preview is not import_allowed")
    if not import_preview.get("candidate_profiles"):
        reasons.append("birth profile import preview has no candidate_profiles")
    return reasons


def _fixture_patch_text(candidate_profiles: list[dict[str, Any]]) -> str:
    entries = []
    for profile in candidate_profiles:
        entries.append(
            {
                "id": profile.get("case_id"),
                "name": profile.get("public_name"),
                "domain": profile.get("domain"),
                "birth": profile.get("birth", {}),
                "source": profile.get("source", {}),
                "event_tags": {},
                "validation_use": (
                    "Reviewed celebrity birth profile imported from birth-profile review manifest; "
                    "event tags must be added through reviewed industry-event manifests."
                ),
            }
        )
    rendered_entries = pformat(entries, width=100, sort_dicts=False)
    return (
        "# Non-mutating preview only. Review before appending these entries to FAMOUS_CASES.\n"
        f"{rendered_entries}\n"
    )


def _fixture_patch_gate_reason(patch_ready: bool) -> str:
    if patch_ready:
        return "Reviewed candidate profiles can be rendered as a fixture patch preview; no file writes are performed."
    return "Fixture patch preview requires an import-allowed birth-profile preview with candidate profiles."


def _fixture_patch_next_action(patch_ready: bool) -> str:
    if patch_ready:
        return "Review patch_text and target_file_sha256, then apply an explicit fixture patch in a separate reviewed step."
    return "Complete the reviewed birth-profile import preview before requesting a fixture patch preview."


def _fixture_patch_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    preview_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    preview_matches = preview_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and preview_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "preview_sha256_matches_material": preview_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_preview_sha256": preview_sha256,
        "recomputed_preview_sha256": recomputed_sha256,
    }


def _source_review_work_item(request: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    case_id = str(request.get("case_id", ""))
    source_policy = audit.get("source_policy", {}) if isinstance(audit.get("source_policy"), dict) else {}
    missing_fields = [str(field) for field in request.get("missing_profile_fields", []) if field]
    return {
        "task_id": f"birth-profile-source-review-{case_id}",
        "case_id": case_id,
        "public_name": request.get("public_name"),
        "domain": request.get("domain"),
        "identity_source_url": request.get("identity_source_url"),
        "review_status": request.get("review_status"),
        "blocked_symbolic_event_topics": request.get("blocked_symbolic_event_topics", []),
        "blocked_label_count": request.get("blocked_label_count", 0),
        "missing_profile_fields": missing_fields,
        "suggested_search_queries": request.get("suggested_search_queries", []),
        "allowed_source_families": source_policy.get("allowed_source_families", []),
        "disallowed_use": source_policy.get("disallowed_use", ""),
        "required_evidence": [
            "identity source must match the public person",
            "birth time must come from a rated or explicitly reviewed source",
            "birthplace must be sourced, not inferred from nationality",
            "source rating and source note must explain reliability",
        ],
        "reviewed_profile_draft": {
            "case_id": case_id,
            "public_name": request.get("public_name"),
            "domain": request.get("domain"),
            "birth_date": None,
            "birth_time": None,
            "gender": None,
            "birthplace": None,
            "source_name": None,
            "source_url": None,
            "source_rating": None,
            "source_note": None,
            "identity_source_url": request.get("identity_source_url"),
            "review_status": "in_review",
            "collected_before_rule_change": request.get("collected_before_rule_change"),
        },
        "acceptance_criteria": [
            "missing_profile_fields is empty",
            "review_status is externally_reviewed",
            "review.externally_reviewed is true",
            "review.approval is approved_for_birth_profile_import",
            "build_birth_profile_import_preview reports import_allowed true",
            "build_birth_profile_fixture_patch_preview reports patch_ready_for_review true while would_write_file remains false",
        ],
        "boundary": "This item is a source-review task, not certified birth evidence.",
    }


def _source_review_progress_summary(work_items: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = {status: 0 for status in sorted(ALLOWED_REVIEW_STATUSES)}
    domain_work_item_counts: dict[str, int] = {}
    domain_blocked_label_counts: dict[str, int] = {}
    total_blocked_label_count = 0
    ready_for_import_count = 0
    for item in work_items:
        status = str(item.get("review_status", ""))
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
        domain = str(item.get("domain", "unknown") or "unknown")
        domain_work_item_counts[domain] = domain_work_item_counts.get(domain, 0) + 1
        blocked_count = item.get("blocked_label_count", 0)
        blocked_count = blocked_count if isinstance(blocked_count, int) else 0
        total_blocked_label_count += blocked_count
        domain_blocked_label_counts[domain] = domain_blocked_label_counts.get(domain, 0) + blocked_count
        if item.get("review_status") == "externally_reviewed" and not item.get("missing_profile_fields"):
            ready_for_import_count += 1
    return {
        "work_item_count": len(work_items),
        "review_status_counts": status_counts,
        "domain_work_item_counts": dict(sorted(domain_work_item_counts.items())),
        "domain_blocked_label_counts": dict(sorted(domain_blocked_label_counts.items())),
        "total_blocked_label_count": total_blocked_label_count,
        "ready_for_import_count": ready_for_import_count,
        "not_started_count": status_counts.get("not_started", 0),
        "in_review_count": status_counts.get("in_review", 0),
        "externally_reviewed_count": status_counts.get("externally_reviewed", 0),
        "rejected_count": status_counts.get("rejected", 0),
    }


def _source_review_field_gap_summary(work_items: list[dict[str, Any]]) -> dict[str, Any]:
    missing_field_counts: dict[str, int] = {}
    for item in work_items:
        missing_fields = item.get("missing_profile_fields", [])
        if not isinstance(missing_fields, list):
            continue
        for field in missing_fields:
            field_name = str(field)
            missing_field_counts[field_name] = missing_field_counts.get(field_name, 0) + 1
    highest_gap_fields = [
        {"field": field, "count": count}
        for field, count in sorted(missing_field_counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]
    return {
        "missing_field_counts": dict(sorted(missing_field_counts.items())),
        "highest_gap_fields": highest_gap_fields,
        "complete_profile_count": sum(1 for item in work_items if not item.get("missing_profile_fields")),
        "incomplete_profile_count": sum(1 for item in work_items if bool(item.get("missing_profile_fields"))),
    }


def _source_lookup_item(item: dict[str, Any], *, selected_cache_dir: Path, rank: int) -> dict[str, Any]:
    case_id = str(item.get("case_id", ""))
    domain = str(item.get("domain", ""))
    missing_fields = [str(field) for field in item.get("missing_profile_fields", []) if field]
    queries = [str(query) for query in item.get("suggested_search_queries", []) if query]
    planned_queries = [
        {
            "query_id": f"birth-profile-source-lookup-{case_id}-{index}",
            "query": query,
            "priority": index,
            "target_fields": _source_lookup_target_fields(query, missing_fields),
            "recommended_source_families": _recommended_source_families(query, domain),
            "source_use_policy": _source_use_policy(query, domain),
            "planned_cache_path": str(selected_cache_dir / f"{case_id}_{index}.json"),
            "would_fetch_live_source": False,
            "would_write_cache": False,
            "review_note_required": True,
        }
        for index, query in enumerate(queries, start=1)
    ]
    return {
        "task_id": f"birth-profile-source-lookup-{case_id}",
        "source_review_task_id": item.get("task_id"),
        "rank": rank,
        "case_id": case_id,
        "public_name": item.get("public_name"),
        "domain": domain,
        "identity_source_url": item.get("identity_source_url"),
        "missing_profile_fields": missing_fields,
        "blocked_label_count": item.get("blocked_label_count", 0),
        "query_count": len(planned_queries),
        "planned_queries": planned_queries,
        "acceptance_criteria": [
            "identity source and collected source must refer to the same public person",
            "birth time must be explicit or rated; do not infer it from date-only sources",
            "birthplace must be stated by a source and must not be inferred from nationality",
            "source_name, source_url, source_rating, and source_note must be filled before import preview",
        ],
        "boundary": "This lookup item is a dry-run search plan, not reviewed birth evidence.",
    }


def _source_lookup_target_fields(query: str, missing_fields: list[str]) -> list[str]:
    query_lower = query.lower()
    if "birth time" in query_lower or "rated source" in query_lower:
        return [field for field in missing_fields if field in {"birth_date", "birth_time", "source_name", "source_url", "source_rating"}]
    if "birthplace" in query_lower or "biography" in query_lower:
        return [field for field in missing_fields if field in {"birth_date", "birthplace", "gender", "source_name", "source_url", "source_rating"}]
    return missing_fields


def _recommended_source_families(query: str, domain: str) -> list[dict[str, Any]]:
    query_lower = query.lower()
    family_ids = ["rated_birth_time_source"] if "birth time" in query_lower or "rated source" in query_lower else []
    family_ids.append("wikidata_identity_anchor")
    family_ids.extend(_domain_anchor_family_ids(domain))
    families = []
    seen: set[str] = set()
    for family_id in family_ids:
        if family_id in seen:
            continue
        seen.add(family_id)
        family = next(
            (item for item in SOURCE_FAMILY_CATALOG if item.get("source_family_id") == family_id),
            None,
        )
        if family:
            families.append(family)
    return families


def _source_use_policy(query: str, domain: str) -> dict[str, Any]:
    query_lower = query.lower()
    requires_birth_time_source = "birth time" in query_lower or "rated source" in query_lower
    return {
        "domain": domain,
        "requires_rated_birth_time_source": requires_birth_time_source,
        "identity_anchor_required": True,
        "domain_anchor_allowed": domain in ALLOWED_DOMAINS,
        "birth_time_may_be_satisfied_by": ["rated_birth_time_source"] if requires_birth_time_source else [],
        "identity_may_be_satisfied_by": ["wikidata_identity_anchor", *_domain_anchor_family_ids(domain)],
        "disallowed_shortcut": (
            "Do not promote identity-only or domain-only metadata into birth_time. "
            "A reviewer must cite a rated or explicit birth-time source."
        ),
    }


def _domain_anchor_family_ids(domain: str) -> list[str]:
    if domain == "film":
        return ["film_identity_and_work_anchor"]
    if domain == "music":
        return ["music_identity_and_work_anchor"]
    if domain == "sports":
        return ["sports_identity_and_result_anchor"]
    return []


def _source_lookup_domain_summary(lookup_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_domain: dict[str, dict[str, Any]] = {}
    for item in lookup_items:
        domain = str(item.get("domain", "unknown") or "unknown")
        summary = by_domain.setdefault(
            domain,
            {
                "domain": domain,
                "lookup_item_count": 0,
                "query_count": 0,
                "blocked_label_count": 0,
                "case_ids": [],
            },
        )
        summary["lookup_item_count"] += 1
        summary["query_count"] += int(item.get("query_count", 0))
        blocked_count = item.get("blocked_label_count", 0)
        summary["blocked_label_count"] += blocked_count if isinstance(blocked_count, int) else 0
        if item.get("case_id"):
            summary["case_ids"].append(str(item.get("case_id")))
    return [by_domain[key] for key in sorted(by_domain)]


def _source_lookup_blocking_reasons(
    workplan: dict[str, Any],
    lookup_items: list[dict[str, Any]],
    failures: list[str],
) -> list[str]:
    reasons = list(failures)
    if workplan.get("valid") is not True:
        reasons.append("birth profile source review workplan is invalid")
    if lookup_items:
        reasons.append(f"{len(lookup_items)} birth-profile source lookup items require manual execution")
    return reasons


def _source_cache_audit_item(query: dict[str, Any]) -> dict[str, Any]:
    cache_path = Path(str(query.get("planned_cache_path", "")))
    base = {
        "query_id": query.get("query_id"),
        "case_id": _case_id_from_lookup_query_id(str(query.get("query_id", ""))),
        "query": query.get("query"),
        "target_fields": query.get("target_fields", []),
        "cache_path": str(cache_path),
    }
    if not cache_path.exists():
        return {
            **base,
            "cache_status": "missing",
            "review_status": "missing",
            "source_evidence_acceptable": False,
            "payload": None,
            "failures": [],
            "boundary": "Missing cache is a pending review task, not a validation failure.",
        }
    failures = []
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            **base,
            "cache_status": "invalid",
            "review_status": "invalid",
            "source_evidence_acceptable": False,
            "payload": None,
            "failures": [f"{cache_path}: {exc}"],
            "boundary": "Invalid cache cannot be used as reviewed birth evidence.",
        }
    if not isinstance(payload, dict):
        payload = {"raw_payload": payload}
        failures.append(f"{cache_path}: payload must be a JSON object")
    failures.extend(_source_cache_payload_failures(payload, query, cache_path))
    review_status = str(payload.get("review_status", "missing"))
    source_evidence_acceptable = not failures and review_status == "source_reviewed"
    return {
        **base,
        "cache_status": "present",
        "review_status": review_status,
        "source_evidence_acceptable": source_evidence_acceptable,
        "source_family_id": payload.get("source_family_id"),
        "source_name": payload.get("source_name"),
        "source_url": payload.get("source_url"),
        "source_rating": payload.get("source_rating"),
        "extracted_fields": {
            "birth_date": payload.get("birth_date"),
            "birth_time": payload.get("birth_time"),
            "gender": payload.get("gender"),
            "birthplace": payload.get("birthplace"),
        },
        "payload_sha256": _stable_sha256(payload),
        "payload": payload,
        "failures": failures,
        "boundary": "Present cache is source-review evidence only; it is not certified birth data.",
    }


def _source_cache_template_item(query: dict[str, Any]) -> dict[str, Any]:
    target_fields = [str(field) for field in query.get("target_fields", []) if field]
    template_payload = {
        "query_id": query.get("query_id"),
        "case_id": _case_id_from_lookup_query_id(str(query.get("query_id", ""))),
        "query": query.get("query"),
        "source_family_id": "",
        "source_name": "",
        "source_url": "",
        "source_rating": "",
        "reviewer_note": "",
        "review_status": "needs_more_evidence",
        "birth_date": "",
        "birth_time": "",
        "gender": "",
        "birthplace": "",
    }
    template_text = json.dumps(template_payload, ensure_ascii=False, indent=2, sort_keys=True)
    return {
        "query_id": query.get("query_id"),
        "case_id": template_payload["case_id"],
        "query": query.get("query"),
        "target_fields": target_fields,
        "planned_cache_path": query.get("planned_cache_path"),
        "recommended_source_families": query.get("recommended_source_families", []),
        "source_use_policy": query.get("source_use_policy", {}),
        "allowed_source_family_ids": _recommended_source_family_ids(query),
        "would_write_cache": False,
        "template_payload": template_payload,
        "template_text": template_text,
        "template_text_sha256": _stable_sha256({"template_text": template_text}),
        "required_fields": [
            "query_id",
            "case_id",
            "source_family_id",
            "source_name",
            "source_url",
            "source_rating",
            "reviewer_note",
            "review_status",
        ],
        "review_status_options": ["source_reviewed", "rejected", "needs_more_evidence"],
        "acceptance_note": (
            "Use review_status=source_reviewed only when at least one substantive birth field "
            "(birth_date, birth_time, gender, or birthplace) is filled from the cited source."
        ),
    }


def _source_cache_template_blocking_reasons(
    lookup_plan: dict[str, Any],
    templates: list[dict[str, Any]],
) -> list[str]:
    reasons = []
    if lookup_plan.get("valid") is not True:
        reasons.append("birth profile source lookup plan is invalid")
    if templates:
        reasons.append(f"{len(templates)} cache templates require manual source review and file creation")
    else:
        reasons.append("no cache templates were generated")
    return reasons


def _case_id_from_lookup_query_id(query_id: str) -> str:
    prefix = "birth-profile-source-lookup-"
    if not query_id.startswith(prefix):
        return ""
    body = query_id[len(prefix) :]
    return body.rsplit("-", 1)[0]


def _source_cache_payload_failures(payload: dict[str, Any], query: dict[str, Any], cache_path: Path) -> list[str]:
    failures = []
    expected_query_id = query.get("query_id")
    expected_case_id = _case_id_from_lookup_query_id(str(expected_query_id))
    if payload.get("query_id") != expected_query_id:
        failures.append(f"{cache_path}: query_id does not match planned query")
    if payload.get("case_id") != expected_case_id:
        failures.append(f"{cache_path}: case_id does not match planned query")
    for field in ["source_family_id", "source_name", "source_url", "source_rating", "reviewer_note", "review_status"]:
        if not _present(payload.get(field)):
            failures.append(f"{cache_path}: {field} is required")
    source_family_id = str(payload.get("source_family_id", ""))
    allowed_family_ids = _recommended_source_family_ids(query)
    if source_family_id and source_family_id not in allowed_family_ids:
        failures.append(f"{cache_path}: source_family_id is not allowed for planned query")
    if _present(payload.get("birth_time")) and source_family_id != "rated_birth_time_source":
        failures.append(f"{cache_path}: birth_time evidence requires source_family_id=rated_birth_time_source")
    failures.extend(_source_cache_family_target_failures(payload, query, source_family_id, cache_path))
    if payload.get("review_status") not in {"source_reviewed", "rejected", "needs_more_evidence"}:
        failures.append(f"{cache_path}: review_status must be source_reviewed, rejected, or needs_more_evidence")
    if payload.get("review_status") == "source_reviewed" and not _source_cache_has_target_evidence(payload, query):
        failures.append(f"{cache_path}: reviewed payload does not fill any substantive birth field")
    return failures


def _recommended_source_family_ids(query: dict[str, Any]) -> list[str]:
    families = query.get("recommended_source_families", [])
    if not isinstance(families, list):
        return []
    return [
        str(family.get("source_family_id"))
        for family in families
        if isinstance(family, dict) and family.get("source_family_id")
    ]


def _source_cache_family_target_failures(
    payload: dict[str, Any],
    query: dict[str, Any],
    source_family_id: str,
    cache_path: Path,
) -> list[str]:
    if not source_family_id:
        return []
    family = next(
        (item for item in SOURCE_FAMILY_CATALOG if item.get("source_family_id") == source_family_id),
        None,
    )
    if not isinstance(family, dict):
        return [f"{cache_path}: source_family_id is not declared in source family catalog"]
    usable_fields = {str(field) for field in family.get("usable_for_fields", [])}
    metadata_fields = {"source_name", "source_url", "source_rating"}
    target_fields = query.get("target_fields", [])
    if not isinstance(target_fields, list):
        return []
    failures = []
    for field in target_fields:
        field_name = str(field)
        if field_name in metadata_fields or not _present(payload.get(field_name)):
            continue
        if field_name not in usable_fields:
            failures.append(f"{cache_path}: source_family_id={source_family_id} cannot satisfy {field_name}")
    return failures


def _source_cache_has_target_evidence(payload: dict[str, Any], query: dict[str, Any]) -> bool:
    target_fields = query.get("target_fields", [])
    if not isinstance(target_fields, list):
        return False
    substantive_targets = [
        str(field)
        for field in target_fields
        if str(field) in SUBSTANTIVE_BIRTH_EVIDENCE_FIELDS
    ]
    return any(_present(payload.get(field)) for field in substantive_targets)


def _source_cache_audit_blocking_reasons(cache_items: list[dict[str, Any]], failures: list[str]) -> list[str]:
    reasons = list(failures)
    missing_count = sum(1 for item in cache_items if item.get("cache_status") == "missing")
    present_count = sum(1 for item in cache_items if item.get("cache_status") == "present")
    accepted_count = sum(1 for item in cache_items if item.get("source_evidence_acceptable") is True)
    if missing_count:
        reasons.append(f"{missing_count} planned source cache files are missing")
    if present_count and accepted_count < present_count:
        reasons.append(f"{present_count - accepted_count} present cache files are not acceptable source evidence")
    if accepted_count:
        reasons.append("accepted cache evidence still requires a separate reviewed manifest draft")
    return reasons


def _source_cache_audit_status(material: dict[str, Any]) -> str:
    if material.get("failures"):
        return "cache_audit_failed"
    if int(material.get("missing_cache_count", 0)) > 0:
        return "waiting_for_manual_cache"
    if int(material.get("accepted_cache_count", 0)) == int(material.get("expected_cache_count", -1)):
        return "cache_ready_for_reviewed_manifest_draft"
    return "cache_present_requires_review"


def _reviewed_manifest_draft_requests(
    work_items: list[dict[str, Any]],
    cache_audit: dict[str, Any],
) -> list[dict[str, Any]]:
    accepted_by_case: dict[str, list[dict[str, Any]]] = {}
    for item in cache_audit.get("cache_items", []):
        if isinstance(item, dict) and item.get("source_evidence_acceptable") is True:
            accepted_by_case.setdefault(str(item.get("case_id")), []).append(item)
    requests = []
    for work_item in work_items:
        if not isinstance(work_item, dict):
            continue
        case_id = str(work_item.get("case_id", ""))
        accepted_items = accepted_by_case.get(case_id, [])
        field_values = _reviewed_manifest_field_values(accepted_items)
        missing_fields = [
            field
            for field in [
                "birth_date",
                "birth_time",
                "gender",
                "birthplace",
                "source_name",
                "source_url",
                "source_rating",
                "source_note",
            ]
            if not _present(field_values.get(field))
        ]
        requests.append(
            {
                "case_id": case_id,
                "public_name": work_item.get("public_name"),
                "domain": work_item.get("domain"),
                "identity_source_url": work_item.get("identity_source_url"),
                "missing_profile_fields": missing_fields,
                "suggested_search_queries": work_item.get("suggested_search_queries", []),
                "blocked_symbolic_event_topics": work_item.get("blocked_symbolic_event_topics", []),
                "blocked_label_count": work_item.get("blocked_label_count", 0),
                "review_status": "externally_reviewed" if not missing_fields else "in_review",
                "collected_before_rule_change": True,
                **field_values,
                "source_cache_item_count": len(accepted_items),
                "source_cache_payload_sha256s": [
                    str(item.get("payload_sha256")) for item in accepted_items if item.get("payload_sha256")
                ],
            }
        )
    return requests


def _reviewed_manifest_field_values(accepted_items: list[dict[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {
        "birth_date": None,
        "birth_time": None,
        "gender": None,
        "birthplace": None,
        "source_name": None,
        "source_url": None,
        "source_rating": None,
        "source_note": None,
    }
    source_notes = []
    source_names = []
    source_urls = []
    source_ratings = []
    for item in accepted_items:
        extracted = item.get("extracted_fields", {}) if isinstance(item.get("extracted_fields"), dict) else {}
        for field in ["birth_date", "birth_time", "gender", "birthplace"]:
            if not _present(values.get(field)) and _present(extracted.get(field)):
                values[field] = extracted.get(field)
        payload = item.get("payload", {}) if isinstance(item.get("payload"), dict) else {}
        if _present(item.get("source_name")):
            source_names.append(str(item.get("source_name")))
        if _present(item.get("source_url")):
            source_urls.append(str(item.get("source_url")))
        if _present(item.get("source_rating")):
            source_ratings.append(str(item.get("source_rating")))
        if _present(payload.get("reviewer_note")):
            source_notes.append(str(payload.get("reviewer_note")))
    values["source_name"] = "; ".join(dict.fromkeys(source_names)) or None
    values["source_url"] = "; ".join(dict.fromkeys(source_urls)) or None
    values["source_rating"] = "; ".join(dict.fromkeys(source_ratings)) or None
    values["source_note"] = " | ".join(dict.fromkeys(source_notes)) or None
    return values


def _reviewed_manifest_draft_payload(
    source_workplan: dict[str, Any],
    review_requests: list[dict[str, Any]],
    draft_ready: bool,
) -> dict[str, Any]:
    return {
        "schema_version": "birth-profile-review-manifest-v1",
        "status": REVIEWED_MANIFEST_STATUS if draft_ready else EXAMPLE_MANIFEST_STATUS,
        "purpose": "Draft reviewed celebrity birth-profile manifest generated from accepted source cache evidence.",
        "boundary": "Draft preview only; requires human approval before it can be used for import preview.",
        "review": {
            "externally_reviewed": draft_ready,
            "reviewer": "human approval required",
            "review_date": None,
            "approval": "approved_for_birth_profile_import" if draft_ready else "not_approved_for_birth_profile_import",
        },
        "required_profile_fields": sorted(REQUIRED_PROFILE_FIELDS),
        "source_policy": source_workplan.get("audit", {}).get("source_policy", {})
        if isinstance(source_workplan.get("audit"), dict)
        else {},
        "review_requests": review_requests,
    }


def _reviewed_manifest_draft_blocking_reasons(
    work_items: list[dict[str, Any]],
    cache_audit: dict[str, Any],
) -> list[str]:
    reasons = []
    reasons.extend(cache_audit.get("failures", []) if isinstance(cache_audit.get("failures"), list) else [])
    if not work_items:
        reasons.append("source review workplan has no work items")
    if int(cache_audit.get("missing_cache_count", 0)) > 0:
        reasons.append(f"{cache_audit.get('missing_cache_count')} planned source cache files are missing")
    if int(cache_audit.get("accepted_cache_count", 0)) <= 0:
        reasons.append("no accepted source cache evidence is available")
    requests = _reviewed_manifest_draft_requests(work_items, cache_audit)
    incomplete = [item["case_id"] for item in requests if item.get("missing_profile_fields")]
    if incomplete:
        reasons.append("incomplete reviewed profile drafts: " + ",".join(incomplete))
    return reasons


def _reviewed_manifest_file_preview_blocking_reasons(draft_preview: dict[str, Any]) -> list[str]:
    reasons = list(draft_preview.get("blocking_reasons", [])) if isinstance(draft_preview.get("blocking_reasons"), list) else []
    if draft_preview.get("draft_ready_for_human_approval") is not True:
        reasons.append("reviewed manifest draft preview is not ready for human approval")
    if draft_preview.get("would_write_review_manifest") is not False:
        reasons.append("reviewed manifest draft preview would write a manifest")
    if draft_preview.get("would_import_profiles") is not False:
        reasons.append("reviewed manifest draft preview would import profiles")
    integrity = draft_preview.get("integrity_check", {}) if isinstance(draft_preview.get("integrity_check"), dict) else {}
    if integrity.get("status") != "passed":
        reasons.append("reviewed manifest draft preview integrity check did not pass")
    return reasons


def _source_review_blocking_reasons(audit: dict[str, Any], work_items: list[dict[str, Any]]) -> list[str]:
    reasons = []
    if audit.get("valid") is not True:
        reasons.append("birth profile review manifest is invalid")
    if work_items:
        reasons.append(f"{len(work_items)} birth-profile source review work items require external review")
    if audit.get("ready_for_import") is not True:
        reasons.append("birth profile review manifest is not ready_for_import")
    return reasons


def _source_review_workplan_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    workplan_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    workplan_matches = workplan_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and workplan_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "workplan_sha256_matches_material": workplan_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_workplan_sha256": workplan_sha256,
        "recomputed_workplan_sha256": recomputed_sha256,
    }


def _source_lookup_plan_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    plan_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    plan_matches = plan_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and plan_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "plan_sha256_matches_material": plan_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_plan_sha256": plan_sha256,
        "recomputed_plan_sha256": recomputed_sha256,
    }


def _source_cache_audit_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    audit_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    audit_matches = audit_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and audit_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "audit_sha256_matches_material": audit_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_audit_sha256": audit_sha256,
        "recomputed_audit_sha256": recomputed_sha256,
    }


def _source_cache_template_preview_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    preview_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    preview_matches = preview_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and preview_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "preview_sha256_matches_material": preview_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_preview_sha256": preview_sha256,
        "recomputed_preview_sha256": recomputed_sha256,
    }


def _reviewed_manifest_draft_preview_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    preview_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    preview_matches = preview_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and preview_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "preview_sha256_matches_material": preview_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_preview_sha256": preview_sha256,
        "recomputed_preview_sha256": recomputed_sha256,
    }


def _reviewed_manifest_file_preview_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    preview_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    preview_matches = preview_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and preview_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "preview_sha256_matches_material": preview_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_preview_sha256": preview_sha256,
        "recomputed_preview_sha256": recomputed_sha256,
    }


def _import_preview_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    preview_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    preview_matches = preview_sha256 == recomputed_sha256
    return {
        "status": "passed" if receipt_matches and preview_matches else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "preview_sha256_matches_material": preview_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_preview_sha256": preview_sha256,
        "recomputed_preview_sha256": recomputed_sha256,
    }


def _invalid_audit(path: Path, failures: list[str]) -> dict[str, Any]:
    material = {
        "schema_version": "birth-profile-review-manifest-audit-v1",
        "manifest_path": str(path),
        "manifest_content_hash": None,
        "manifest_schema_version": None,
        "manifest_status": None,
        "externally_reviewed": False,
        "request_count": 0,
        "case_count": 0,
        "domains": [],
        "domain_summary": [],
        "source_policy": {},
        "blocked_label_count": 0,
        "ready_for_import": False,
        "failures": failures,
    }
    return {
        "schema_version": material["schema_version"],
        "status": "invalid",
        "valid": False,
        "production_evidence": False,
        "offline_only": True,
        "review_requests": [],
        "birth_profile_review_manifest_receipt": _receipt("birth-profile-review-manifest-receipt-v1", material),
        **material,
        "boundary": "The birth-profile review manifest could not be parsed or audited.",
    }


def _manifest_failures(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["manifest must be a JSON object"]
    failures: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
    failures.extend(f"missing top-level field: {field}" for field in missing)
    if payload.get("schema_version") != "birth-profile-review-manifest-v1":
        failures.append("schema_version must be birth-profile-review-manifest-v1")
    manifest_status = payload.get("status")
    if manifest_status not in {EXAMPLE_MANIFEST_STATUS, REVIEWED_MANIFEST_STATUS}:
        failures.append(f"status must be {EXAMPLE_MANIFEST_STATUS} or {REVIEWED_MANIFEST_STATUS}")
    review = payload.get("review", {})
    if not isinstance(review, dict):
        failures.append("review must be an object")
    elif manifest_status == EXAMPLE_MANIFEST_STATUS and review.get("externally_reviewed") is not False:
        failures.append("review.externally_reviewed must be false for the bundled example")
    elif manifest_status == REVIEWED_MANIFEST_STATUS:
        if review.get("externally_reviewed") is not True:
            failures.append("review.externally_reviewed must be true for reviewed import manifests")
        if review.get("approval") != "approved_for_birth_profile_import":
            failures.append("review.approval must be approved_for_birth_profile_import")
    profile_fields = payload.get("required_profile_fields", [])
    if not isinstance(profile_fields, list):
        failures.append("required_profile_fields must be a list")
    else:
        missing_fields = sorted(REQUIRED_PROFILE_FIELDS - {str(field) for field in profile_fields})
        failures.extend(f"required_profile_fields missing: {field}" for field in missing_fields)
    source_policy = payload.get("source_policy", {})
    if not isinstance(source_policy, dict):
        failures.append("source_policy must be an object")
    else:
        for field in ("requires_identity_match", "requires_birth_time_source", "requires_source_rating"):
            if source_policy.get(field) is not True:
                failures.append(f"source_policy.{field} must be true")
    failures.extend(_request_failures(payload.get("review_requests")))
    return failures


def _request_failures(requests: Any) -> list[str]:
    if not isinstance(requests, list) or not requests:
        return ["review_requests must be a non-empty list"]
    failures = []
    case_ids: set[str] = set()
    for request in requests:
        if not isinstance(request, dict):
            failures.append("each review request must be an object")
            continue
        case_id = str(request.get("case_id", ""))
        if not case_id:
            failures.append("review request missing case_id")
        if case_id in case_ids:
            failures.append(f"duplicate review request case_id: {case_id}")
        case_ids.add(case_id)
        missing = sorted(REQUIRED_REVIEW_REQUEST_FIELDS - set(request))
        failures.extend(f"review request {case_id or '<missing>'} missing field: {field}" for field in missing)
        failures.extend(_single_request_failures(request, case_id or "<missing>"))
    return failures


def _single_request_failures(request: dict[str, Any], case_id: str) -> list[str]:
    failures = []
    if request.get("domain") not in ALLOWED_DOMAINS:
        failures.append(f"review request {case_id} domain must be film, music, or sports")
    if not str(request.get("identity_source_url", "")).startswith("https://www.wikidata.org/wiki/"):
        failures.append(f"review request {case_id} identity_source_url must be a Wikidata https URL")
    review_status = request.get("review_status")
    missing_profile_fields = request.get("missing_profile_fields")
    if not isinstance(missing_profile_fields, list):
        failures.append(f"review request {case_id} missing_profile_fields must be a list")
    elif review_status == "externally_reviewed" and missing_profile_fields:
        failures.append(f"review request {case_id} missing_profile_fields must be empty after external review")
    elif review_status != "externally_reviewed" and not missing_profile_fields:
        failures.append(f"review request {case_id} missing_profile_fields must be non-empty until external review")
    if not isinstance(request.get("suggested_search_queries"), list) or not request.get("suggested_search_queries"):
        failures.append(f"review request {case_id} suggested_search_queries must be a non-empty list")
    if not isinstance(request.get("blocked_symbolic_event_topics"), list) or not request.get(
        "blocked_symbolic_event_topics"
    ):
        failures.append(f"review request {case_id} blocked_symbolic_event_topics must be a non-empty list")
    if not isinstance(request.get("blocked_label_count"), int) or request.get("blocked_label_count", 0) <= 0:
        failures.append(f"review request {case_id} blocked_label_count must be a positive integer")
    if review_status not in ALLOWED_REVIEW_STATUSES:
        failures.append(f"review request {case_id} review_status is not allowed")
    if review_status == "externally_reviewed":
        for field in REQUIRED_PROFILE_FIELDS:
            if not _present(request.get(field)):
                failures.append(f"review request {case_id} reviewed profile missing field: {field}")
    if request.get("collected_before_rule_change") is not True:
        failures.append(f"review request {case_id} collected_before_rule_change must be true")
    return failures


def _ready_for_import(payload: dict[str, Any], requests: list[dict[str, Any]], failures: list[str]) -> bool:
    if failures:
        return False
    review = payload.get("review", {})
    return (
        payload.get("status") == REVIEWED_MANIFEST_STATUS
        and isinstance(review, dict)
        and review.get("externally_reviewed") is True
        and review.get("approval") == "approved_for_birth_profile_import"
        and bool(requests)
        and all(_request_import_ready(request) for request in requests)
    )


def _audit_status(failures: list[str], ready_for_import: bool) -> str:
    if failures:
        return "invalid"
    if ready_for_import:
        return "ready_for_import"
    return "ready_for_review"


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _domain_summary(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for request in requests:
        grouped.setdefault(str(request.get("domain")), []).append(request)
    return [
        {
            "domain": domain,
            "request_count": len(rows),
            "case_ids": sorted({str(row.get("case_id")) for row in rows if row.get("case_id")}),
            "blocked_label_count": sum(
                int(row.get("blocked_label_count", 0))
                for row in rows
                if isinstance(row.get("blocked_label_count"), int)
            ),
            "blocked_symbolic_event_topics": sorted(
                {
                    str(topic)
                    for row in rows
                    for topic in row.get("blocked_symbolic_event_topics", [])
                    if topic
                }
            ),
        }
        for domain, rows in sorted(grouped.items())
    ]


def _receipt(schema_version: str, material: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": schema_version,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _stable_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
