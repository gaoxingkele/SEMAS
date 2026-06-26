"""Audit query plans for collecting public industry-event evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from examples.mingli_5agents.industry_event_manifest import (
    REQUIRED_RECORD_FIELDS,
    audit_industry_event_manifest_payload,
    industry_event_manifest_receipt,
)


REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "status",
    "purpose",
    "boundary",
    "review",
    "source",
    "collection_policy",
    "required_template_fields",
    "query_templates",
}

REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "name",
    "endpoint_url",
    "documentation_url",
    "license_or_review",
    "access_mode",
    "live_collection_allowed",
}

REQUIRED_COLLECTION_POLICY_FIELDS = {
    "requires_identity_review",
    "requires_statement_references",
    "requires_negative_year_source_window",
    "collected_before_rule_change",
    "max_rows_per_query",
    "rate_limit_note",
}

REQUIRED_TEMPLATE_FIELDS = {
    "template_id",
    "domain",
    "event_topic",
    "positive_event_type",
    "negative_year_rule",
    "placeholders",
    "sparql",
    "result_mapping",
    "manifest_record_defaults",
}

REQUIRED_PLACEHOLDERS = {"PERSON_QID", "START_YEAR", "END_YEAR"}
ALLOWED_SPLIT_ROLES = {"train", "holdout"}


def default_industry_event_query_plan_path() -> Path:
    return Path(__file__).resolve().parent / "providers" / "industry_event_source_query_plan_example.json"


def audit_industry_event_query_plan(path: Path) -> dict[str, Any]:
    """Validate an industry-event query plan before live collection."""
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    failures = _query_plan_failures(payload)
    templates = (
        payload.get("query_templates", [])
        if isinstance(payload, dict) and isinstance(payload.get("query_templates"), list)
        else []
    )
    source = payload.get("source", {}) if isinstance(payload, dict) and isinstance(payload.get("source"), dict) else {}
    policy = (
        payload.get("collection_policy", {})
        if isinstance(payload, dict) and isinstance(payload.get("collection_policy"), dict)
        else {}
    )
    domains = sorted(
        {str(template.get("domain")) for template in templates if isinstance(template, dict) and template.get("domain")}
    )
    event_topics = sorted(
        {
            str(template.get("event_topic"))
            for template in templates
            if isinstance(template, dict) and template.get("event_topic")
        }
    )
    reviewed = bool(payload.get("review", {}).get("externally_reviewed")) if isinstance(payload, dict) else False
    live_collection_allowed = bool(source.get("live_collection_allowed"))
    collection_ready = (
        reviewed
        and live_collection_allowed
        and isinstance(payload, dict)
        and payload.get("status") == "reviewed_live_collection_plan"
        and not failures
    )
    return {
        "status": "ready_for_review" if not failures else "invalid",
        "path": str(path),
        "valid": not failures,
        "failures": failures,
        "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
        "plan_status": payload.get("status") if isinstance(payload, dict) else None,
        "collection_ready": collection_ready,
        "externally_reviewed": reviewed,
        "live_collection_allowed": live_collection_allowed,
        "source_id": source.get("source_id"),
        "source_name": source.get("name"),
        "endpoint_url": source.get("endpoint_url"),
        "documentation_url": source.get("documentation_url"),
        "template_count": len(templates),
        "domains": domains,
        "event_topics": event_topics,
        "required_manifest_fields_mapped": _required_manifest_fields_mapped(templates),
        "requires_identity_review": policy.get("requires_identity_review") is True,
        "requires_statement_references": policy.get("requires_statement_references") is True,
        "requires_negative_year_source_window": policy.get("requires_negative_year_source_window") is True,
        "content_hash": hashlib.sha256(raw).hexdigest(),
        "policy": (
            "Query plans define collection requests only. They must be externally reviewed and explicitly "
            "marked reviewed_live_collection_plan before live collection is considered ready."
        ),
    }


def industry_event_query_plan_receipt(audit: dict[str, Any]) -> dict[str, Any]:
    material = {
        "schema_version": "industry-event-query-plan-audit-receipt-v1",
        "path": audit.get("path"),
        "valid": audit.get("valid"),
        "status": audit.get("status"),
        "plan_schema_version": audit.get("schema_version"),
        "plan_status": audit.get("plan_status"),
        "content_hash": audit.get("content_hash"),
        "collection_ready": audit.get("collection_ready"),
        "externally_reviewed": audit.get("externally_reviewed"),
        "live_collection_allowed": audit.get("live_collection_allowed"),
        "source_id": audit.get("source_id"),
        "endpoint_url": audit.get("endpoint_url"),
        "template_count": audit.get("template_count"),
        "domains": audit.get("domains", []),
        "event_topics": audit.get("event_topics", []),
        "required_manifest_fields_mapped": audit.get("required_manifest_fields_mapped"),
        "failures": audit.get("failures", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def build_industry_event_collection_request_bundle(
    query_plan_path: Path,
    *,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str,
    domain: str | None = None,
) -> dict[str, Any]:
    """Expand a reviewed query plan into offline collection requests without executing them."""
    payload = json.loads(query_plan_path.read_text(encoding="utf-8"))
    audit = audit_industry_event_query_plan(query_plan_path)
    input_failures = _collection_request_input_failures(
        case_id=case_id,
        public_name=public_name,
        person_qid=person_qid,
        start_year=start_year,
        end_year=end_year,
        split_role=split_role,
    )
    templates = payload.get("query_templates", []) if isinstance(payload, dict) else []
    if domain:
        templates = [template for template in templates if isinstance(template, dict) and template.get("domain") == domain]
        if not templates:
            input_failures.append(f"domain has no query templates: {domain}")
    source = payload.get("source", {}) if isinstance(payload, dict) and isinstance(payload.get("source"), dict) else {}
    requests = [
        _collection_request_from_template(
            template,
            source=source,
            case_id=case_id,
            public_name=public_name,
            person_qid=person_qid,
            start_year=start_year,
            end_year=end_year,
            split_role=split_role,
        )
        for template in templates
        if isinstance(template, dict)
    ]
    request_failures = [
        failure
        for request in requests
        for failure in request.get("failures", [])
    ]
    failures = list(audit.get("failures", [])) + input_failures + request_failures
    material = {
        "schema_version": "industry-event-collection-request-bundle-v1",
        "query_plan_path": str(query_plan_path),
        "query_plan_receipt_sha256": industry_event_query_plan_receipt(audit).get("sha256"),
        "query_plan_content_hash": audit.get("content_hash"),
        "source_id": audit.get("source_id"),
        "endpoint_url": audit.get("endpoint_url"),
        "collection_ready": audit.get("collection_ready"),
        "live_execution_allowed": False,
        "case": {
            "case_id": case_id,
            "public_name": public_name,
            "person_qid": person_qid,
            "start_year": start_year,
            "end_year": end_year,
            "split_role": split_role,
            "domain": domain,
        },
        "request_count": len(requests),
        "template_ids": [request.get("template_id") for request in requests],
        "domains": sorted({str(request.get("domain")) for request in requests if request.get("domain")}),
        "requests": requests,
        "failures": failures,
        "policy": (
            "This bundle expands query templates for offline review only. It must not execute live collection "
            "until the query plan is externally reviewed and marked collection_ready."
        ),
    }
    return {
        "status": "ready_for_review" if not failures else "invalid",
        "valid": not failures,
        "execution_gate": {
            "passed": False,
            "reason": "Offline request bundles are not live collection authorization.",
            "collection_ready": audit.get("collection_ready"),
            "live_execution_allowed": False,
        },
        "bundle_receipt": industry_event_collection_request_bundle_receipt(material),
        **material,
    }


def industry_event_collection_request_bundle_receipt(material: dict[str, Any]) -> dict[str, Any]:
    receipt_material = {
        "schema_version": "industry-event-collection-request-bundle-receipt-v1",
        "query_plan_content_hash": material.get("query_plan_content_hash"),
        "query_plan_receipt_sha256": material.get("query_plan_receipt_sha256"),
        "source_id": material.get("source_id"),
        "endpoint_url": material.get("endpoint_url"),
        "collection_ready": material.get("collection_ready"),
        "live_execution_allowed": material.get("live_execution_allowed"),
        "case": material.get("case"),
        "request_count": material.get("request_count"),
        "template_ids": material.get("template_ids", []),
        "domains": material.get("domains", []),
        "request_sha256s": [
            request.get("request_sha256")
            for request in material.get("requests", [])
            if isinstance(request, dict)
        ],
        "failures": material.get("failures", []),
    }
    encoded = json.dumps(receipt_material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": receipt_material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": receipt_material,
    }


def build_industry_event_fetch_cache_plan(
    query_plan_path: Path,
    *,
    cache_dir: Path,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str,
    domain: str | None = None,
    live: bool = False,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    """Plan or execute reviewed industry-event source fetches into a local cache."""
    request_bundle = build_industry_event_collection_request_bundle(
        query_plan_path,
        case_id=case_id,
        public_name=public_name,
        person_qid=person_qid,
        start_year=start_year,
        end_year=end_year,
        split_role=split_role,
        domain=domain,
    )
    requests = [request for request in request_bundle.get("requests", []) if isinstance(request, dict)]
    cache_entries = [_cache_entry_for_request(cache_dir, request) for request in requests]
    failures = list(request_bundle.get("failures", []))
    fetched_entries: list[dict[str, Any]] = []
    if live and not request_bundle.get("collection_ready"):
        failures.append("live collection requires reviewed collection_ready query plan")
    elif live:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        for request, entry in zip(requests, cache_entries):
            fetch_result = _fetch_request_to_cache(request, entry, timeout_seconds=timeout_seconds)
            if fetch_result.get("failure"):
                failures.append(str(fetch_result["failure"]))
            else:
                fetched_entries.append(fetch_result)
    material = {
        "schema_version": "industry-event-fetch-cache-plan-v1",
        "query_plan_path": str(query_plan_path),
        "cache_dir": str(cache_dir),
        "live": live,
        "collection_ready": request_bundle.get("collection_ready"),
        "request_bundle_receipt_sha256": request_bundle.get("bundle_receipt", {}).get("sha256"),
        "case": request_bundle.get("case"),
        "request_count": len(requests),
        "planned_cache_count": len(cache_entries),
        "cache_write_count": len(fetched_entries),
        "cache_entries": cache_entries,
        "fetched_entries": fetched_entries,
        "failures": failures,
    }
    return {
        "status": _fetch_cache_status(live=live, failures=failures, fetched_count=len(fetched_entries)),
        "valid": not failures,
        "offline_only": not live,
        "request_bundle": request_bundle,
        "execution_gate": {
            "passed": live and not failures and request_bundle.get("collection_ready") is True,
            "live_requested": live,
            "collection_ready": request_bundle.get("collection_ready"),
            "reason": (
                "Live fetch was executed into cache."
                if live and not failures
                else "Dry run only; no live source was contacted."
                if not live
                else "Live fetch blocked or failed; inspect failures."
            ),
        },
        "fetch_cache_receipt": _receipt("industry-event-fetch-cache-receipt-v1", material),
        **material,
    }


def build_industry_event_manifest_draft_from_wikidata_response(
    query_plan_path: Path,
    response_path: Path,
    *,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str,
    domain: str,
) -> dict[str, Any]:
    """Convert a cached Wikidata-like JSON response into a draft industry-event manifest."""
    request_bundle = build_industry_event_collection_request_bundle(
        query_plan_path,
        case_id=case_id,
        public_name=public_name,
        person_qid=person_qid,
        start_year=start_year,
        end_year=end_year,
        split_role=split_role,
        domain=domain,
    )
    if request_bundle.get("request_count") != 1:
        return _draft_failure_response(
            request_bundle=request_bundle,
            response_path=response_path,
            failures=["draft manifest import requires exactly one domain template"],
        )
    response_payload = json.loads(response_path.read_text(encoding="utf-8"))
    response_hash = _stable_sha256(response_payload)
    request = request_bundle["requests"][0]
    positive_records = _positive_records_from_wikidata_response(
        response_payload,
        request=request,
        case_id=case_id,
        public_name=public_name,
        split_role=split_role,
    )
    positive_years = {record["year"] for record in positive_records}
    negative_records = [
        _negative_record_for_year(
            year,
            request=request,
            case_id=case_id,
            public_name=public_name,
            split_role=split_role,
            response_hash=response_hash,
        )
        for year in range(start_year, end_year + 1)
        if year not in positive_years
    ]
    manifest = _draft_manifest_payload(
        records=positive_records + negative_records,
        request=request,
        response_hash=response_hash,
    )
    audit = audit_industry_event_manifest_payload(manifest, path=str(response_path))
    receipt = industry_event_manifest_receipt(audit)
    draft_material = {
        "schema_version": "industry-event-manifest-draft-receipt-v1",
        "query_plan_path": str(query_plan_path),
        "response_path": str(response_path),
        "response_sha256": response_hash,
        "request_bundle_receipt_sha256": request_bundle.get("bundle_receipt", {}).get("sha256"),
        "manifest_audit_receipt_sha256": receipt.get("sha256"),
        "case_id": case_id,
        "public_name": public_name,
        "person_qid": person_qid,
        "domain": domain,
        "start_year": start_year,
        "end_year": end_year,
        "split_role": split_role,
        "positive_record_count": len(positive_records),
        "negative_record_count": len(negative_records),
        "record_count": len(positive_records) + len(negative_records),
        "manifest_valid": audit.get("valid"),
        "failures": list(request_bundle.get("failures", [])) + list(audit.get("failures", [])),
    }
    return {
        "status": "ready_for_review" if audit.get("valid") and not request_bundle.get("failures") else "invalid",
        "valid": audit.get("valid") is True and not request_bundle.get("failures"),
        "offline_only": True,
        "request_bundle": request_bundle,
        "response_path": str(response_path),
        "response_sha256": response_hash,
        "draft_manifest": manifest,
        "draft_manifest_audit": audit,
        "draft_manifest_audit_receipt": receipt,
        "draft_receipt": _receipt("industry-event-manifest-draft-receipt-v1", draft_material),
        "policy": (
            "Draft manifests produced from cached responses are audit inputs only. They require external review "
            "before production evidence or calibration promotion."
        ),
    }


def _draft_failure_response(
    *,
    request_bundle: dict[str, Any],
    response_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    material = {
        "schema_version": "industry-event-manifest-draft-receipt-v1",
        "response_path": str(response_path),
        "request_bundle_receipt_sha256": request_bundle.get("bundle_receipt", {}).get("sha256"),
        "failures": failures,
    }
    return {
        "status": "invalid",
        "valid": False,
        "offline_only": True,
        "request_bundle": request_bundle,
        "response_path": str(response_path),
        "failures": failures,
        "draft_receipt": _receipt("industry-event-manifest-draft-receipt-v1", material),
    }


def _positive_records_from_wikidata_response(
    response_payload: dict[str, Any],
    *,
    request: dict[str, Any],
    case_id: str,
    public_name: str,
    split_role: str,
) -> list[dict[str, Any]]:
    records = []
    bindings = (
        response_payload.get("results", {}).get("bindings", [])
        if isinstance(response_payload.get("results"), dict)
        else []
    )
    preview = request.get("manifest_record_preview", {})
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            continue
        year = _year_from_binding(binding)
        if year is None:
            continue
        event_url = _binding_value(binding, "event") or preview.get("source_url")
        event_label = _binding_value(binding, "eventLabel") or "wikidata_event"
        record_id = _safe_record_id(f"{request.get('template_id')}_{case_id}_{year}_{index}_{event_label}")
        records.append(
            {
                "record_id": record_id,
                "case_id": case_id,
                "public_name": public_name,
                "domain": preview.get("domain"),
                "industry": preview.get("industry"),
                "year": year,
                "event_topic": preview.get("event_topic"),
                "event_present": True,
                "event_type": preview.get("event_type"),
                "source_family_id": preview.get("source_family_id"),
                "source_name": preview.get("source_name"),
                "source_url": event_url,
                "license_or_review": preview.get("license_or_review"),
                "collected_before_rule_change": True,
                "split_role": split_role,
                "negative_year_reason": None,
            }
        )
    return records


def _negative_record_for_year(
    year: int,
    *,
    request: dict[str, Any],
    case_id: str,
    public_name: str,
    split_role: str,
    response_hash: str,
) -> dict[str, Any]:
    preview = request.get("manifest_record_preview", {})
    return {
        "record_id": _safe_record_id(f"{request.get('template_id')}_{case_id}_{year}_negative"),
        "case_id": case_id,
        "public_name": public_name,
        "domain": preview.get("domain"),
        "industry": preview.get("industry"),
        "year": year,
        "event_topic": preview.get("event_topic"),
        "event_present": False,
        "event_type": "no_qualifying_event",
        "source_family_id": preview.get("source_family_id"),
        "source_name": preview.get("source_name"),
        "source_url": preview.get("source_url"),
        "license_or_review": preview.get("license_or_review"),
        "collected_before_rule_change": True,
        "split_role": split_role,
        "negative_year_reason": (
            f"offline response hash {response_hash} had no qualifying event for this "
            f"case-topic-year under template {request.get('template_id')}"
        ),
    }


def _draft_manifest_payload(
    *,
    records: list[dict[str, Any]],
    request: dict[str, Any],
    response_hash: str,
) -> dict[str, Any]:
    preview = request.get("manifest_record_preview", {})
    family_id = preview.get("source_family_id")
    source_name = preview.get("source_name")
    source_url = preview.get("source_url")
    return {
        "schema_version": "industry-event-source-manifest-v1",
        "status": "draft_from_cached_response_not_production_evidence",
        "purpose": "Draft manifest generated from a cached public industry-event source response.",
        "boundary": "This draft is not production evidence. It requires source review, identity review, and negative-year review.",
        "review": {
            "externally_reviewed": False,
            "reviewer": "review required",
            "review_date": None,
            "approval": "not_approved_for_production",
        },
        "required_record_fields": sorted(REQUIRED_RECORD_FIELDS),
        "source_families": [
            {
                "id": family_id,
                "coverage": preview.get("industry"),
                "candidate_sources": [
                    {
                        "name": source_name,
                        "url": source_url,
                        "intended_fields": ["event", "eventLabel", "date", "source"],
                    }
                ],
            }
        ],
        "split_policy": {
            "frozen_before_rule_change": True,
            "allowed_split_roles": ["train", "holdout"],
            "negative_year_rule": request.get("negative_year_rule"),
        },
        "records": records,
        "draft_provenance": {
            "response_sha256": response_hash,
            "request_sha256": request.get("request_sha256"),
            "template_id": request.get("template_id"),
            "offline_only": True,
        },
    }


def _year_from_binding(binding: dict[str, Any]) -> int | None:
    raw = _binding_value(binding, "date")
    if not raw or len(raw) < 4:
        return None
    try:
        return int(str(raw)[:4])
    except ValueError:
        return None


def _binding_value(binding: dict[str, Any], key: str) -> str | None:
    value = binding.get(key)
    if not isinstance(value, dict):
        return None
    raw = value.get("value")
    return str(raw) if raw is not None else None


def _safe_record_id(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in value]
    return "_".join("".join(chars).split("_")).strip("_") or "record"


def _cache_entry_for_request(cache_dir: Path, request: dict[str, Any]) -> dict[str, Any]:
    case_id = _safe_record_id(str(request.get("manifest_record_preview", {}).get("case_id") or "case"))
    template_id = _safe_record_id(str(request.get("template_id") or "template"))
    start_year = request.get("start_year")
    end_year = request.get("end_year")
    request_sha = str(request.get("request_sha256") or _stable_sha256(request))
    filename = f"{case_id}_{template_id}_{start_year}_{end_year}_{request_sha[:12]}.json"
    path = Path(cache_dir) / filename
    return {
        "template_id": request.get("template_id"),
        "domain": request.get("domain"),
        "event_topic": request.get("event_topic"),
        "request_sha256": request_sha,
        "cache_path": str(path),
    }


def _fetch_request_to_cache(
    request: dict[str, Any],
    entry: dict[str, Any],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    query_url = str(request.get("query_url", ""))
    try:
        http_request = Request(
            query_url,
            headers={
                "accept": "application/sparql-results+json",
                "user-agent": "semas-mingli-industry-event-audit/1.0",
            },
        )
        with urlopen(http_request, timeout=timeout_seconds) as response:
            body = response.read()
        cache_path = Path(str(entry.get("cache_path")))
        cache_path.write_bytes(body)
        return {
            **entry,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "byte_count": len(body),
        }
    except (OSError, URLError, TimeoutError, ValueError) as exc:
        return {
            **entry,
            "failure": f"fetch failed for {request.get('template_id')}: {exc}",
        }


def _fetch_cache_status(*, live: bool, failures: list[str], fetched_count: int) -> str:
    if failures:
        return "blocked" if live else "invalid"
    if live:
        return "fetched" if fetched_count else "no_requests"
    return "dry_run"


def _receipt(schema_version: str, material: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": schema_version,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _collection_request_input_failures(
    *,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str,
) -> list[str]:
    failures = []
    if not case_id:
        failures.append("case_id is required")
    if not public_name:
        failures.append("public_name is required")
    if not _valid_qid(person_qid):
        failures.append("person_qid must look like Q123")
    if not isinstance(start_year, int) or not isinstance(end_year, int):
        failures.append("start_year and end_year must be integers")
    elif start_year > end_year:
        failures.append("start_year must be <= end_year")
    if split_role not in ALLOWED_SPLIT_ROLES:
        failures.append("split_role must be train or holdout")
    return failures


def _collection_request_from_template(
    template: dict[str, Any],
    *,
    source: dict[str, Any],
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str,
) -> dict[str, Any]:
    template_id = str(template.get("template_id", ""))
    sparql = str(template.get("sparql", ""))
    expanded_sparql = (
        sparql.replace("PERSON_QID", person_qid)
        .replace("START_YEAR", str(start_year))
        .replace("END_YEAR", str(end_year))
    )
    endpoint_url = str(source.get("endpoint_url", ""))
    query_url = f"{endpoint_url}?{urlencode({'query': expanded_sparql, 'format': 'json'})}" if endpoint_url else ""
    defaults = template.get("manifest_record_defaults", {}) if isinstance(template.get("manifest_record_defaults"), dict) else {}
    preview = {
        "case_id": case_id,
        "public_name": public_name,
        "domain": template.get("domain"),
        "industry": template.get("result_mapping", {}).get("industry")
        if isinstance(template.get("result_mapping"), dict)
        else None,
        "event_topic": template.get("event_topic"),
        "event_present": True,
        "event_type": template.get("positive_event_type"),
        "source_family_id": defaults.get("source_family_id"),
        "source_name": defaults.get("source_name"),
        "source_url": defaults.get("source_url"),
        "license_or_review": defaults.get("license_or_review"),
        "collected_before_rule_change": True,
        "split_role": split_role,
        "negative_year_reason": None,
    }
    material = {
        "template_id": template_id,
        "domain": template.get("domain"),
        "event_topic": template.get("event_topic"),
        "person_qid": person_qid,
        "start_year": start_year,
        "end_year": end_year,
        "endpoint_url": endpoint_url,
        "expanded_sparql": expanded_sparql,
        "query_url": query_url,
        "manifest_record_preview": preview,
        "negative_year_rule": template.get("negative_year_rule"),
        "failures": _expanded_request_failures(template_id, expanded_sparql, query_url),
    }
    return {
        **material,
        "request_sha256": _stable_sha256(material),
    }


def _expanded_request_failures(template_id: str, expanded_sparql: str, query_url: str) -> list[str]:
    failures = []
    for placeholder in REQUIRED_PLACEHOLDERS:
        if placeholder in expanded_sparql:
            failures.append(f"request {template_id} still contains placeholder {placeholder}")
    if not query_url.startswith("https://"):
        failures.append(f"request {template_id} query_url must be https")
    return failures


def _valid_qid(value: str) -> bool:
    return isinstance(value, str) and len(value) > 1 and value.startswith("Q") and value[1:].isdigit()


def _stable_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _query_plan_failures(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["query plan must be a JSON object"]
    failures: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
    failures.extend(f"missing top-level field: {field}" for field in missing)
    failures.extend(_review_failures(payload.get("review"), payload.get("status"), payload.get("source")))
    failures.extend(_source_failures(payload.get("source")))
    failures.extend(_collection_policy_failures(payload.get("collection_policy")))
    failures.extend(_required_template_fields_failures(payload.get("required_template_fields")))
    failures.extend(_template_failures(payload.get("query_templates")))
    return failures


def _review_failures(review: Any, status: Any, source: Any) -> list[str]:
    if not isinstance(review, dict):
        return ["review must be an object"]
    failures = []
    reviewed = review.get("externally_reviewed")
    if not isinstance(reviewed, bool):
        failures.append("review.externally_reviewed must be boolean")
    live_allowed = source.get("live_collection_allowed") if isinstance(source, dict) else None
    if status == "reviewed_live_collection_plan":
        if reviewed is not True:
            failures.append("reviewed_live_collection_plan requires review.externally_reviewed true")
        if live_allowed is not True:
            failures.append("reviewed_live_collection_plan requires source.live_collection_allowed true")
    if reviewed is True:
        if not review.get("reviewer"):
            failures.append("review.reviewer is required when externally reviewed")
        if not review.get("review_date"):
            failures.append("review.review_date is required when externally reviewed")
        if review.get("approval") not in {"approved_for_query_design", "approved_for_live_collection"}:
            failures.append("review.approval must be approved_for_query_design or approved_for_live_collection")
    return failures


def _source_failures(source: Any) -> list[str]:
    if not isinstance(source, dict):
        return ["source must be an object"]
    failures = []
    missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
    failures.extend(f"source missing field: {field}" for field in missing)
    for field in ("endpoint_url", "documentation_url"):
        if source.get(field) and not str(source.get(field)).startswith("https://"):
            failures.append(f"source.{field} must be https")
    if not isinstance(source.get("live_collection_allowed"), bool):
        failures.append("source.live_collection_allowed must be boolean")
    return failures


def _collection_policy_failures(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["collection_policy must be an object"]
    failures = []
    missing = sorted(REQUIRED_COLLECTION_POLICY_FIELDS - set(policy))
    failures.extend(f"collection_policy missing field: {field}" for field in missing)
    for field in (
        "requires_identity_review",
        "requires_statement_references",
        "requires_negative_year_source_window",
        "collected_before_rule_change",
    ):
        if policy.get(field) is not True:
            failures.append(f"collection_policy.{field} must be true")
    if not isinstance(policy.get("max_rows_per_query"), int) or policy.get("max_rows_per_query", 0) <= 0:
        failures.append("collection_policy.max_rows_per_query must be a positive integer")
    return failures


def _required_template_fields_failures(fields: Any) -> list[str]:
    if not isinstance(fields, list):
        return ["required_template_fields must be a list"]
    missing = sorted(REQUIRED_TEMPLATE_FIELDS - {str(field) for field in fields})
    return [f"required_template_fields missing: {field}" for field in missing]


def _template_failures(templates: Any) -> list[str]:
    if not isinstance(templates, list) or not templates:
        return ["query_templates must be a non-empty list"]
    failures = []
    template_ids = set()
    for template in templates:
        if not isinstance(template, dict):
            failures.append("each query template must be an object")
            continue
        template_id = str(template.get("template_id", ""))
        if not template_id:
            failures.append("query template missing template_id")
        if template_id in template_ids:
            failures.append(f"duplicate template_id: {template_id}")
        template_ids.add(template_id)
        missing = sorted(REQUIRED_TEMPLATE_FIELDS - set(template))
        failures.extend(f"template {template_id or '<missing>'} missing field: {field}" for field in missing)
        failures.extend(_single_template_failures(template, template_id or "<missing>"))
    if len({template.get("domain") for template in templates if isinstance(template, dict)}) < 3:
        failures.append("query_templates must cover at least three domains")
    return failures


def _single_template_failures(template: dict[str, Any], template_id: str) -> list[str]:
    failures = []
    placeholders = {str(item) for item in template.get("placeholders", []) if isinstance(template.get("placeholders"), list)}
    if placeholders != REQUIRED_PLACEHOLDERS:
        failures.append(f"template {template_id} placeholders must be PERSON_QID, START_YEAR, and END_YEAR")
    sparql = str(template.get("sparql", ""))
    for placeholder in REQUIRED_PLACEHOLDERS:
        if placeholder not in sparql:
            failures.append(f"template {template_id} sparql missing placeholder {placeholder}")
    if "SELECT" not in sparql.upper() or "LIMIT" not in sparql.upper():
        failures.append(f"template {template_id} sparql must include SELECT and LIMIT")
    mapping = template.get("result_mapping")
    if not isinstance(mapping, dict):
        failures.append(f"template {template_id} result_mapping must be an object")
    else:
        missing_mapping = sorted(REQUIRED_RECORD_FIELDS - set(mapping))
        failures.extend(f"template {template_id} result_mapping missing manifest field: {field}" for field in missing_mapping)
    defaults = template.get("manifest_record_defaults")
    if not isinstance(defaults, dict):
        failures.append(f"template {template_id} manifest_record_defaults must be an object")
    else:
        for field in ("source_family_id", "source_name", "source_url", "license_or_review"):
            if not defaults.get(field):
                failures.append(f"template {template_id} manifest_record_defaults.{field} is required")
        if defaults.get("source_url") and not str(defaults.get("source_url")).startswith("https://"):
            failures.append(f"template {template_id} manifest_record_defaults.source_url must be https")
    if not template.get("negative_year_rule"):
        failures.append(f"template {template_id} negative_year_rule is required")
    return failures


def _required_manifest_fields_mapped(templates: list[Any]) -> bool:
    if not templates:
        return False
    for template in templates:
        mapping = template.get("result_mapping") if isinstance(template, dict) else None
        if not isinstance(mapping, dict) or not REQUIRED_RECORD_FIELDS.issubset(set(mapping)):
            return False
    return True
