"""Audit candidate celebrity cases for public industry-event validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from examples.mingli_5agents.famous_case_validation import famous_case_records
from examples.mingli_5agents.industry_event_manifest import (
    REQUIRED_RECORD_FIELDS,
    audit_industry_event_manifest_payload,
    build_industry_event_validation_label_table_payload,
    industry_event_manifest_receipt,
)
from examples.mingli_5agents.industry_event_query_plan import (
    REQUIRED_TEMPLATE_FIELDS as REQUIRED_QUERY_TEMPLATE_FIELDS,
    build_industry_event_fetch_cache_plan,
    build_industry_event_manifest_draft_from_wikidata_response,
    default_industry_event_query_plan_path,
)


REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "status",
    "purpose",
    "boundary",
    "review",
    "selection_policy",
    "required_candidate_fields",
    "candidates",
}

REQUIRED_SELECTION_POLICY_FIELDS = {
    "candidate_domains",
    "min_candidates_per_domain",
    "requires_qid_source_url",
    "requires_identity_review_before_production",
    "requires_negative_year_collection",
    "collected_before_rule_change",
}

REQUIRED_CANDIDATE_FIELDS = {
    "case_id",
    "public_name",
    "domain",
    "industry",
    "person_qid",
    "public_source_url",
    "source_name",
    "source_lookup_method",
    "identity_review_status",
    "split_role",
    "event_query_domain",
    "collection_window",
    "selection_reason",
    "collected_before_rule_change",
}

ALLOWED_DOMAINS = {"film", "music", "sports"}
ALLOWED_SPLIT_ROLES = {"train", "holdout"}


def default_industry_event_candidate_cases_path() -> Path:
    return Path(__file__).resolve().parent / "providers" / "industry_event_candidate_cases_example.json"


def audit_industry_event_candidate_cases(path: Path) -> dict[str, Any]:
    """Validate candidate celebrity cases before event collection planning."""
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    failures = _candidate_manifest_failures(payload)
    candidates = (
        payload.get("candidates", [])
        if isinstance(payload, dict) and isinstance(payload.get("candidates"), list)
        else []
    )
    reviewed = bool(payload.get("review", {}).get("externally_reviewed")) if isinstance(payload, dict) else False
    domain_counts = _domain_counts(candidates)
    qids = sorted(
        {
            str(candidate.get("person_qid"))
            for candidate in candidates
            if isinstance(candidate, dict) and candidate.get("person_qid")
        }
    )
    production_ready = (
        reviewed
        and isinstance(payload, dict)
        and payload.get("status") == "reviewed_candidate_pool"
        and not failures
    )
    return {
        "status": "ready_for_review" if not failures else "invalid",
        "path": str(path),
        "valid": not failures,
        "failures": failures,
        "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
        "candidate_pool_status": payload.get("status") if isinstance(payload, dict) else None,
        "production_ready": production_ready,
        "externally_reviewed": reviewed,
        "candidate_count": len(candidates),
        "domain_counts": domain_counts,
        "domains": sorted(domain_counts),
        "split_roles": sorted(
            {
                str(candidate.get("split_role"))
                for candidate in candidates
                if isinstance(candidate, dict) and candidate.get("split_role")
            }
        ),
        "person_qids": qids,
        "required_candidate_fields": sorted(REQUIRED_CANDIDATE_FIELDS),
        "content_hash": hashlib.sha256(raw).hexdigest(),
        "policy": (
            "Candidate pools identify public people for future event collection only. They do not certify "
            "birth data, event labels, or production validation readiness."
        ),
    }


def industry_event_candidate_cases_receipt(audit: dict[str, Any]) -> dict[str, Any]:
    material = {
        "schema_version": "industry-event-candidate-cases-audit-receipt-v1",
        "path": audit.get("path"),
        "valid": audit.get("valid"),
        "status": audit.get("status"),
        "candidate_schema_version": audit.get("schema_version"),
        "candidate_pool_status": audit.get("candidate_pool_status"),
        "content_hash": audit.get("content_hash"),
        "production_ready": audit.get("production_ready"),
        "externally_reviewed": audit.get("externally_reviewed"),
        "candidate_count": audit.get("candidate_count"),
        "domain_counts": audit.get("domain_counts", {}),
        "domains": audit.get("domains", []),
        "split_roles": audit.get("split_roles", []),
        "person_qids": audit.get("person_qids", []),
        "failures": audit.get("failures", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def build_candidate_pool_fetch_cache_plan(
    candidate_path: Path,
    *,
    query_plan_path: Path | None = None,
    cache_dir: Path,
    domain: str | None = None,
    split_role: str | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """Build fetch/cache plans for every selected candidate in a candidate pool."""
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate_audit = audit_industry_event_candidate_cases(candidate_path)
    candidate_receipt = industry_event_candidate_cases_receipt(candidate_audit)
    selected_query_plan = query_plan_path or default_industry_event_query_plan_path()
    candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
    selected_candidates = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and (domain is None or candidate.get("domain") == domain)
        and (split_role is None or candidate.get("split_role") == split_role)
    ]
    failures = list(candidate_audit.get("failures", []))
    if domain is not None and domain not in ALLOWED_DOMAINS:
        failures.append(f"domain must be one of film, music, or sports: {domain}")
    if split_role is not None and split_role not in ALLOWED_SPLIT_ROLES:
        failures.append(f"split_role must be train or holdout: {split_role}")
    if not selected_candidates:
        failures.append("candidate filter selected no candidates")
    plans = [
        _fetch_cache_plan_for_candidate(
            candidate,
            query_plan_path=selected_query_plan,
            cache_dir=cache_dir,
            live=live,
        )
        for candidate in selected_candidates
    ]
    failures.extend(
        failure
        for plan in plans
        for failure in plan.get("failures", [])
        if isinstance(plan, dict)
    )
    material = {
        "schema_version": "industry-event-candidate-pool-fetch-cache-plan-v1",
        "candidate_path": str(candidate_path),
        "candidate_receipt_sha256": candidate_receipt.get("sha256"),
        "query_plan_path": str(selected_query_plan),
        "cache_dir": str(cache_dir),
        "live": live,
        "filters": {
            "domain": domain,
            "split_role": split_role,
        },
        "candidate_count": len(selected_candidates),
        "plan_count": len(plans),
        "total_request_count": sum(int(plan.get("request_count", 0)) for plan in plans if isinstance(plan, dict)),
        "total_planned_cache_count": sum(
            int(plan.get("planned_cache_count", 0)) for plan in plans if isinstance(plan, dict)
        ),
        "total_cache_write_count": sum(int(plan.get("cache_write_count", 0)) for plan in plans if isinstance(plan, dict)),
        "case_ids": [str(candidate.get("case_id")) for candidate in selected_candidates],
        "domains": sorted({str(candidate.get("domain")) for candidate in selected_candidates if candidate.get("domain")}),
        "plans": plans,
        "failures": failures,
    }
    return {
        "status": _candidate_pool_fetch_status(live=live, failures=failures),
        "valid": not failures,
        "offline_only": not live,
        "candidate_audit": candidate_audit,
        "candidate_receipt": candidate_receipt,
        "execution_gate": {
            "passed": live and not failures,
            "live_requested": live,
            "reason": (
                "Live fetch was executed for selected candidate plans."
                if live and not failures
                else "Dry run only; no live source was contacted."
                if not live
                else "Live batch fetch blocked or failed; inspect failures."
            ),
        },
        "candidate_pool_fetch_cache_receipt": _receipt(
            "industry-event-candidate-pool-fetch-cache-receipt-v1",
            material,
        ),
        **material,
    }


def build_candidate_pool_manifest_drafts_from_cache(
    candidate_path: Path,
    *,
    query_plan_path: Path | None = None,
    cache_dir: Path,
    domain: str | None = None,
    split_role: str | None = None,
) -> dict[str, Any]:
    """Import available cached responses for selected candidates into draft manifests."""
    selected_query_plan = query_plan_path or default_industry_event_query_plan_path()
    batch_plan = build_candidate_pool_fetch_cache_plan(
        candidate_path,
        query_plan_path=selected_query_plan,
        cache_dir=cache_dir,
        domain=domain,
        split_role=split_role,
        live=False,
    )
    drafts: list[dict[str, Any]] = []
    draft_manifests: list[dict[str, Any]] = []
    failures = list(batch_plan.get("failures", []))
    missing_response_paths: list[str] = []
    for plan in batch_plan.get("plans", []):
        if not isinstance(plan, dict):
            continue
        cache_entries = [entry for entry in plan.get("cache_entries", []) if isinstance(entry, dict)]
        case = plan.get("case", {}) if isinstance(plan.get("case"), dict) else {}
        if len(cache_entries) != 1:
            failures.append(f"candidate {case.get('case_id')} requires exactly one cached response path")
            continue
        response_path = Path(str(cache_entries[0].get("cache_path", "")))
        if not response_path.exists():
            missing_response_paths.append(str(response_path))
            failures.append(f"missing cached response for {case.get('case_id')}: {response_path}")
            continue
        draft = build_industry_event_manifest_draft_from_wikidata_response(
            selected_query_plan,
            response_path,
            case_id=str(case.get("case_id", "")),
            public_name=str(case.get("public_name", "")),
            person_qid=str(case.get("person_qid", "")),
            start_year=int(case.get("start_year", 0)),
            end_year=int(case.get("end_year", 0)),
            split_role=str(case.get("split_role", "holdout")),
            domain=str(case.get("domain", "")),
        )
        if isinstance(draft.get("draft_manifest"), dict):
            draft_manifests.append(draft["draft_manifest"])
        drafts.append(_draft_summary(draft))
        failures.extend(str(failure) for failure in draft.get("draft_receipt", {}).get("material", {}).get("failures", []))
    combined_manifest = _combined_draft_manifest_payload(
        manifests=draft_manifests,
        candidate_path=candidate_path,
        query_plan_path=selected_query_plan,
        batch_plan=batch_plan,
    )
    combined_audit = audit_industry_event_manifest_payload(combined_manifest, path=str(candidate_path))
    combined_receipt = industry_event_manifest_receipt(combined_audit)
    combined_label_table = build_industry_event_validation_label_table_payload(
        combined_manifest,
        path=f"{candidate_path}#combined_draft_manifest",
    )
    failures.extend(str(failure) for failure in combined_audit.get("failures", []))
    material = {
        "schema_version": "industry-event-candidate-pool-draft-import-v1",
        "candidate_path": str(candidate_path),
        "query_plan_path": str(selected_query_plan),
        "cache_dir": str(cache_dir),
        "candidate_pool_fetch_cache_receipt_sha256": batch_plan.get("candidate_pool_fetch_cache_receipt", {}).get(
            "sha256"
        ),
        "candidate_receipt_sha256": batch_plan.get("candidate_receipt", {}).get("sha256"),
        "filters": {
            "domain": domain,
            "split_role": split_role,
        },
        "candidate_count": batch_plan.get("candidate_count"),
        "draft_count": len(drafts),
        "missing_response_count": len(missing_response_paths),
        "missing_response_paths": missing_response_paths,
        "positive_record_count": sum(int(draft.get("positive_record_count", 0)) for draft in drafts),
        "negative_record_count": sum(int(draft.get("negative_record_count", 0)) for draft in drafts),
        "record_count": sum(int(draft.get("record_count", 0)) for draft in drafts),
        "combined_manifest_audit_receipt_sha256": combined_receipt.get("sha256"),
        "combined_manifest_valid": combined_audit.get("valid"),
        "combined_manifest_record_count": combined_audit.get("record_count"),
        "combined_manifest_positive_event_count": combined_audit.get("positive_event_count"),
        "combined_manifest_negative_event_count": combined_audit.get("negative_event_count"),
        "validation_label_table_receipt_sha256": combined_label_table.get("validation_label_table_receipt", {}).get(
            "sha256"
        ),
        "validation_label_count": combined_label_table.get("record_count"),
        "validation_positive_label_count": combined_label_table.get("positive_label_count"),
        "validation_negative_label_count": combined_label_table.get("negative_label_count"),
        "case_ids": batch_plan.get("case_ids", []),
        "domains": batch_plan.get("domains", []),
        "drafts": drafts,
        "failures": failures,
    }
    return {
        "status": "ready_for_review" if not failures else "invalid",
        "valid": not failures,
        "offline_only": True,
        "batch_plan": batch_plan,
        "combined_draft_manifest": combined_manifest,
        "combined_draft_manifest_audit": combined_audit,
        "combined_draft_manifest_audit_receipt": combined_receipt,
        "validation_label_table": combined_label_table,
        "candidate_pool_draft_import_receipt": _receipt(
            "industry-event-candidate-pool-draft-import-receipt-v1",
            material,
        ),
        **material,
    }


def build_industry_event_evidence_workplan_from_symbolic_score(
    symbolic_score: dict[str, Any],
    *,
    candidate_path: Path,
    query_plan_path: Path | None = None,
    cache_dir: Path,
) -> dict[str, Any]:
    """Turn symbolic score refinement tasks into candidate-pool collection work."""
    candidate_payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate_audit = audit_industry_event_candidate_cases(candidate_path)
    candidate_receipt = industry_event_candidate_cases_receipt(candidate_audit)
    selected_query_plan = query_plan_path or default_industry_event_query_plan_path()
    candidates = (
        candidate_payload.get("candidates", [])
        if isinstance(candidate_payload, dict) and isinstance(candidate_payload.get("candidates"), list)
        else []
    )
    tasks = [
        task
        for task in symbolic_score.get("evolution_task_plan", [])
        if isinstance(task, dict) and task.get("task_type") == "expand_ready_labels"
    ]
    local_birth_profile_suggestions = _local_birth_profile_suggestions_by_domain()
    deferred_tasks = [
        _deferred_evidence_task(
            task,
            local_birth_profile_suggestions=local_birth_profile_suggestions,
        )
        for task in symbolic_score.get("evolution_task_plan", [])
        if isinstance(task, dict) and task.get("task_type") != "expand_ready_labels"
    ]
    work_items = [
        _evidence_work_item(
            task,
            candidates=candidates,
            candidate_path=candidate_path,
            query_plan_path=selected_query_plan,
            cache_dir=cache_dir,
            candidate_receipt_sha256=str(candidate_receipt.get("sha256", "")),
        )
        for task in tasks
    ]
    failures = list(candidate_audit.get("failures", []))
    failures.extend(
        failure
        for item in work_items
        for failure in item.get("failures", [])
        if isinstance(item, dict)
    )
    cache_materialization_summary = _workplan_cache_materialization_summary(work_items)
    draft_import_readiness_gate = _draft_import_readiness_gate(
        cache_materialization_summary,
        scope="workplan",
    )
    readiness_summary = _workplan_readiness_summary(
        work_items=work_items,
        deferred_tasks=deferred_tasks,
        draft_import_readiness_gate=draft_import_readiness_gate,
        failures=failures,
    )
    material = {
        "schema_version": "industry-event-evidence-workplan-v1",
        "candidate_path": str(candidate_path),
        "candidate_receipt_sha256": candidate_receipt.get("sha256"),
        "query_plan_path": str(selected_query_plan),
        "cache_dir": str(cache_dir),
        "symbolic_annual_score_receipt_sha256": symbolic_score.get("symbolic_annual_score_receipt", {}).get("sha256"),
        "source_task_count": len(tasks),
        "deferred_task_count": len(deferred_tasks),
        "work_item_count": len(work_items),
        "candidate_count": sum(int(item.get("candidate_count", 0)) for item in work_items if isinstance(item, dict)),
        "planned_command_count": sum(len(item.get("commands", [])) for item in work_items if isinstance(item, dict)),
        "planned_request_count": sum(
            int(item.get("fetch_cache_plan_summary", {}).get("total_request_count", 0))
            for item in work_items
            if isinstance(item, dict)
        ),
        "planned_cache_count": sum(
            int(item.get("fetch_cache_plan_summary", {}).get("total_planned_cache_count", 0))
            for item in work_items
            if isinstance(item, dict)
        ),
        "existing_cache_count": cache_materialization_summary["existing_cache_count"],
        "missing_cache_count": cache_materialization_summary["missing_cache_count"],
        "cache_materialization_summary": cache_materialization_summary,
        "draft_import_ready": draft_import_readiness_gate["passed"],
        "draft_import_readiness_gate": draft_import_readiness_gate,
        "readiness_summary": readiness_summary,
        "next_action": draft_import_readiness_gate["next_action"],
        "domains": sorted({str(item.get("domain")) for item in work_items if item.get("domain")}),
        "deferred_tasks": deferred_tasks,
        "work_items": work_items,
        "failures": failures,
    }
    return {
        "schema_version": material["schema_version"],
        "status": "ready_for_review" if not failures else "invalid",
        "valid": not failures,
        "offline_only": True,
        "candidate_audit": candidate_audit,
        "candidate_receipt": candidate_receipt,
        "evidence_workplan_receipt": _receipt("industry-event-evidence-workplan-receipt-v1", material),
        **material,
        "boundary": (
            "This workplan converts score-derived evidence tasks into reviewable candidate-pool operations. "
            "It does not fetch live data or certify production evidence."
        ),
    }


def _evidence_work_item(
    task: dict[str, Any],
    *,
    candidates: list[Any],
    candidate_path: Path,
    query_plan_path: Path,
    cache_dir: Path,
    candidate_receipt_sha256: str,
) -> dict[str, Any]:
    domain = str(task.get("domain", ""))
    topic = str(task.get("symbolic_event_topic", ""))
    selected = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and str(candidate.get("domain")) == domain
    ]
    failures = []
    if not domain:
        failures.append(f"task {task.get('task_id')} missing domain")
    if not topic:
        failures.append(f"task {task.get('task_id')} missing symbolic_event_topic")
    if not selected:
        failures.append(f"no candidate-pool cases found for domain {domain}")
    current_metrics = task.get("current_metrics", {}) if isinstance(task.get("current_metrics"), dict) else {}
    required_positive = max(0, 3 - int(current_metrics.get("positive_label_count", 0)))
    required_negative = max(0, 3 - int(current_metrics.get("negative_label_count", 0)))
    command_base = "python -m examples.mingli_5agents.cli --repo .semas_mingli_repo"
    fetch_command = (
        f"{command_base} industry-event-candidate-fetch-cache --candidates {candidate_path} "
        f"--query-plan {query_plan_path} --cache-dir {cache_dir} --domain {domain}"
    )
    draft_command = (
        f"{command_base} industry-event-candidate-draft-import --candidates {candidate_path} "
        f"--query-plan {query_plan_path} --cache-dir {cache_dir} --domain {domain}"
    )
    fetch_plan = build_candidate_pool_fetch_cache_plan(
        candidate_path,
        query_plan_path=query_plan_path,
        cache_dir=cache_dir,
        domain=domain,
        live=False,
    )
    if fetch_plan.get("candidate_receipt", {}).get("sha256") != candidate_receipt_sha256:
        failures.append("embedded fetch/cache plan candidate receipt does not match workplan candidate receipt")
    failures.extend(str(failure) for failure in fetch_plan.get("failures", []))
    fetch_plan_summary = _fetch_cache_plan_summary(fetch_plan)
    cache_materialization_summary = _cache_materialization_summary(
        fetch_plan_summary.get("planned_cache_paths", [])
    )
    draft_import_readiness_gate = _draft_import_readiness_gate(
        cache_materialization_summary,
        scope=f"work_item:{domain}/{topic}",
    )
    return {
        "task_id": task.get("task_id"),
        "domain": domain,
        "symbolic_event_topic": topic,
        "priority": task.get("priority"),
        "task_type": task.get("task_type"),
        "current_metrics": current_metrics,
        "target_ready_positive_labels": 3,
        "target_ready_negative_labels": 3,
        "additional_positive_labels_needed": required_positive,
        "additional_negative_labels_needed": required_negative,
        "candidate_count": len(selected),
        "candidate_case_ids": [str(candidate.get("case_id")) for candidate in selected],
        "candidate_public_names": [str(candidate.get("public_name")) for candidate in selected],
        "fetch_cache_plan_summary": fetch_plan_summary,
        "cache_materialization_summary": cache_materialization_summary,
        "draft_import_ready": draft_import_readiness_gate["passed"],
        "draft_import_readiness_gate": draft_import_readiness_gate,
        "next_action": draft_import_readiness_gate["next_action"],
        "commands": [
            {
                "step": "dry_run_fetch_cache_plan",
                "command": fetch_command,
                "purpose": "Review planned source requests and cache paths before any live collection.",
            },
            {
                "step": "draft_import_after_cache_exists",
                "command": draft_command,
                "purpose": "Convert cached responses into draft positive and negative labels after review.",
            },
        ],
        "acceptance_criteria": task.get("acceptance_criteria", []),
        "recommended_evidence": task.get("next_evidence_to_add", []),
        "failures": failures,
    }


def _deferred_evidence_task(
    task: dict[str, Any],
    *,
    local_birth_profile_suggestions: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    domain = str(task.get("domain", ""))
    topic = str(task.get("symbolic_event_topic", ""))
    suggestions = [
        suggestion
        for suggestion in local_birth_profile_suggestions.get(domain, [])
        if _suggestion_supports_topic(suggestion, topic)
    ][:3]
    local_completion_work_order = _local_completion_work_order(task, suggestions)
    return {
        "task_id": task.get("task_id"),
        "domain": domain,
        "symbolic_event_topic": topic,
        "priority": task.get("priority"),
        "task_type": task.get("task_type"),
        "blocked_case_ids": task.get("blocked_case_ids", []),
        "blocked_public_names": task.get("blocked_public_names", []),
        "blocking_reasons": task.get("blocking_reasons", []),
        "local_birth_profile_suggestions": suggestions,
        "local_birth_profile_suggestion_count": len(suggestions),
        "local_completion_work_order": local_completion_work_order,
        "gate_summary": _deferred_task_gate_summary(local_completion_work_order),
        "next_evidence_to_add": task.get("next_evidence_to_add", []),
        "acceptance_criteria": task.get("acceptance_criteria", []),
        "next_action": _deferred_task_next_action(str(task.get("task_type", ""))),
        "reason": (
            "This task is carried in the workplan but does not produce source-cache requests until its "
            "upstream readiness requirement is satisfied."
        ),
    }


def _deferred_task_gate_summary(local_completion_work_order: dict[str, Any]) -> dict[str, Any]:
    gates = _collect_named_gate_states(local_completion_work_order)
    integrity_checks = _collect_integrity_check_states(local_completion_work_order)
    blocked_gates = [gate for gate in gates if gate.get("passed") is not True]
    failed_integrity = [check for check in integrity_checks if check.get("passed") is not True]
    material = {
        "schema_version": "deferred-task-gate-summary-v1",
        "status": "blocked" if blocked_gates or failed_integrity else "ready",
        "gate_count": len(gates),
        "blocked_gate_count": len(blocked_gates),
        "integrity_check_count": len(integrity_checks),
        "failed_integrity_check_count": len(failed_integrity),
        "blocked_gates": blocked_gates,
        "failed_integrity_checks": failed_integrity,
        "next_action": _deferred_gate_summary_next_action(blocked_gates, failed_integrity),
    }
    gate_summary_receipt = _receipt("deferred-task-gate-summary-receipt-v1", material)
    gate_summary_sha256 = _stable_sha256(material)
    return {
        **material,
        "gate_summary_receipt": gate_summary_receipt,
        "gate_summary_sha256": gate_summary_sha256,
        "integrity_check": _deferred_gate_summary_integrity_check(
            material,
            gate_summary_receipt,
            gate_summary_sha256,
        ),
    }


def _deferred_gate_summary_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    gate_summary_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_summary_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    summary_hash_matches = gate_summary_sha256 == recomputed_summary_sha256
    return {
        "status": "passed" if receipt_matches and summary_hash_matches else "failed",
        "gate_summary_receipt_matches_material": receipt_matches,
        "gate_summary_sha256_matches_material": summary_hash_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_gate_summary_sha256": gate_summary_sha256,
        "recomputed_gate_summary_sha256": recomputed_summary_sha256,
    }


def _collect_named_gate_states(value: Any, path: str = "$") -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key in ("acceptance_gate", "execution_gate"):
            gate = value.get(key)
            if isinstance(gate, dict):
                gates.append(
                    {
                        "path": f"{path}.{key}",
                        "id": gate.get("id", key),
                        "passed": gate.get("passed"),
                        "reason": gate.get("reason", ""),
                    }
                )
        for key, child in value.items():
            if key in {"acceptance_gate", "execution_gate"}:
                continue
            gates.extend(_collect_named_gate_states(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            gates.extend(_collect_named_gate_states(child, f"{path}[{index}]"))
    return gates


def _collect_integrity_check_states(value: Any, path: str = "$") -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if isinstance(value, dict):
        check = value.get("integrity_check")
        if isinstance(check, dict):
            checks.append(
                {
                    "path": f"{path}.integrity_check",
                    "status": check.get("status"),
                    "passed": check.get("status") == "passed",
                }
            )
        for key, child in value.items():
            if key == "integrity_check":
                continue
            checks.extend(_collect_integrity_check_states(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            checks.extend(_collect_integrity_check_states(child, f"{path}[{index}]"))
    return checks


def _deferred_gate_summary_next_action(
    blocked_gates: list[dict[str, Any]],
    failed_integrity: list[dict[str, Any]],
) -> str:
    if failed_integrity:
        return "repair failed integrity checks before reviewing or executing deferred evidence work"
    if blocked_gates:
        return "resolve blocked review gates before promoting music draft labels or query templates"
    return "all deferred gates are clear; proceed to reviewed evidence import workflow"


def _deferred_task_next_action(task_type: str) -> str:
    if task_type == "add_reviewed_birth_profiles":
        return "add or import reviewed birth profiles before industry-event source collection can be scored"
    return "resolve the non-collection evidence task before treating this slice as source-cache ready"


def _local_completion_work_order(task: dict[str, Any], suggestions: list[dict[str, Any]]) -> dict[str, Any]:
    task_type = str(task.get("task_type", ""))
    domain = str(task.get("domain", ""))
    topic = str(task.get("symbolic_event_topic", ""))
    if task_type != "add_reviewed_birth_profiles":
        return {
            "status": "not_applicable",
            "reason": "local completion work orders are only generated for birth-profile readiness tasks",
        }
    if not suggestions:
        return {
            "status": "blocked_no_local_suggestions",
            "reason": "no local reviewed birth-profile suggestions support this domain-topic slice",
            "required_next_step": "add a reviewed birth profile for the blocked case or add a new local fixture",
        }
    return {
        "status": "ready_for_human_review",
        "domain": domain,
        "symbolic_event_topic": topic,
        "strategy_options": [
            {
                "id": "preserve_blocked_case",
                "description": "add reviewed birth data for the currently blocked case without changing event labels",
                "blocked_case_ids": task.get("blocked_case_ids", []),
                "required_artifacts": [
                    "birth date",
                    "birth time",
                    "gender",
                    "birthplace",
                    "birth source URL",
                    "source rating or review note",
                ],
            },
            {
                "id": "use_local_singer_fixtures",
                "description": "create reviewed music event labels for local singer birth fixtures",
                "suggested_case_ids": [str(item.get("case_id")) for item in suggestions],
                "draft_label_plan": _local_music_label_draft_plan(suggestions, topic),
                "required_artifacts": [
                    "positive industry-event year for each selected singer",
                    "negative source-window year for each selected singer",
                    "source family and source URL for every event label",
                    "candidate-pool or manifest receipt after labels are added",
                ],
            },
        ],
        "acceptance_gate": {
            "id": "deferred_music_birth_profile_completion_reviewed",
            "passed": False,
            "reason": "the work order is advisory until a reviewed birth profile or reviewed event labels are added",
        },
    }


def _local_birth_profile_suggestions_by_domain() -> dict[str, list[dict[str, Any]]]:
    suggestions: dict[str, list[dict[str, Any]]] = {domain: [] for domain in ALLOWED_DOMAINS}
    for case in famous_case_records():
        domain = _industry_domain_from_famous_case(case)
        if domain not in ALLOWED_DOMAINS:
            continue
        source = case.get("source", {}) if isinstance(case.get("source"), dict) else {}
        birth = case.get("birth", {}) if isinstance(case.get("birth"), dict) else {}
        event_tags = case.get("event_tags", {}) if isinstance(case.get("event_tags"), dict) else {}
        suggestions[domain].append(
            {
                "case_id": case.get("id"),
                "public_name": case.get("name"),
                "domain": domain,
                "source_name": source.get("name"),
                "source_url": source.get("url"),
                "source_rating": source.get("rating"),
                "birth_date_present": bool(birth.get("birth_date")),
                "birth_time_present": bool(birth.get("birth_time")),
                "birthplace_present": bool(birth.get("birthplace")),
                "event_years_by_symbolic_event_topic": _symbolic_topic_years_from_event_tags(event_tags),
                "supported_symbolic_event_topics": _supported_symbolic_topics_from_event_tags(event_tags),
            }
        )
    return {
        domain: sorted(rows, key=lambda item: str(item.get("case_id")))
        for domain, rows in suggestions.items()
        if rows
    }


def _industry_domain_from_famous_case(case: dict[str, Any]) -> str:
    case_id = str(case.get("id", ""))
    if case_id in {"aretha_franklin", "michael_jackson", "madonna"}:
        return "music"
    if case_id in {"roger_federer", "arthur_ashe", "mark_spitz"}:
        return "sports"
    if case_id in {"marilyn_monroe", "lucille_ball", "sean_penn", "bruce_lee"}:
        return "film"
    return ""


def _supported_symbolic_topics_from_event_tags(event_tags: dict[str, Any]) -> list[str]:
    return sorted(_symbolic_topic_years_from_event_tags(event_tags))


def _symbolic_topic_years_from_event_tags(event_tags: dict[str, Any]) -> dict[str, list[int]]:
    by_topic: dict[str, list[int]] = {}
    for topic, years in event_tags.items():
        symbolic_topic = "career_project" if topic == "career_peak" else str(topic)
        if not isinstance(years, list):
            continue
        by_topic.setdefault(symbolic_topic, []).extend(int(year) for year in years if isinstance(year, int))
    return {topic: sorted(set(years)) for topic, years in sorted(by_topic.items())}


def _suggestion_supports_topic(suggestion: dict[str, Any], topic: str) -> bool:
    topics = suggestion.get("supported_symbolic_event_topics", [])
    return isinstance(topics, list) and topic in {str(item) for item in topics}


def _local_music_label_draft_plan(suggestions: list[dict[str, Any]], topic: str) -> dict[str, Any]:
    if topic != "career_project":
        return {
            "status": "not_applicable",
            "reason": "local music label draft plans currently cover career_project only",
        }
    draft_records = []
    for suggestion in suggestions:
        topic_years = suggestion.get("event_years_by_symbolic_event_topic", {})
        years = topic_years.get(topic, []) if isinstance(topic_years, dict) else []
        if not years:
            continue
        positive_year = min(int(year) for year in years)
        negative_year = _nearest_prior_negative_year(positive_year, set(int(year) for year in years))
        case_id = str(suggestion.get("case_id", ""))
        public_name = suggestion.get("public_name")
        source_url = suggestion.get("source_url")
        draft_records.extend(
            [
                _local_music_label_draft_record(
                    case_id=case_id,
                    public_name=public_name,
                    year=positive_year,
                    event_present=True,
                    source_url=source_url,
                    split_role="train",
                ),
                _local_music_label_draft_record(
                    case_id=case_id,
                    public_name=public_name,
                    year=negative_year,
                    event_present=False,
                    source_url=source_url,
                    split_role="holdout",
                ),
            ]
        )
    material = {
        "schema_version": "local-music-draft-label-plan-v1",
        "symbolic_event_topic": topic,
        "source": "local famous-case event_tags",
        "record_count": len(draft_records),
        "positive_record_count": sum(1 for record in draft_records if record.get("event_present") is True),
        "negative_record_count": sum(1 for record in draft_records if record.get("event_present") is False),
        "case_ids": sorted({str(record.get("case_id")) for record in draft_records if record.get("case_id")}),
        "draft_records": draft_records,
        "source_review_request_plan": _local_music_source_review_request_plan(draft_records),
        "acceptance_gate": {
            "id": "local_music_draft_labels_source_reviewed",
            "passed": False,
            "reason": "local famous-case event tags must be checked against industry-event source families before manifest import",
        },
    }
    draft_label_plan_receipt = _receipt("local-music-draft-label-plan-receipt-v1", material)
    draft_records_sha256 = _stable_sha256(draft_records)
    return {
        "status": "draft_requires_source_review" if draft_records else "blocked_no_local_event_years",
        **material,
        "draft_label_plan_receipt": draft_label_plan_receipt,
        "draft_records_sha256": draft_records_sha256,
        "integrity_check": _local_music_draft_plan_integrity_check(
            material,
            draft_label_plan_receipt,
            draft_records_sha256,
        ),
        "boundary": (
            "These records are a draft work order generated from local famous-case tags. "
            "They are not imported into the validation manifest until source review is complete."
        ),
    }


def _local_music_draft_plan_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    draft_records_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_records_sha256 = _stable_sha256(material.get("draft_records", []))
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    records_match = draft_records_sha256 == recomputed_records_sha256
    return {
        "status": "passed" if receipt_matches and records_match else "failed",
        "receipt_sha256_matches_material": receipt_matches,
        "draft_records_sha256_matches_records": records_match,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_draft_records_sha256": draft_records_sha256,
        "recomputed_draft_records_sha256": recomputed_records_sha256,
    }


def _local_music_source_review_request_plan(draft_records: list[dict[str, Any]]) -> dict[str, Any]:
    requests = [_local_music_source_review_request(record) for record in draft_records]
    return {
        "status": "requires_query_template_review" if requests else "blocked_no_draft_records",
        "request_count": len(requests),
        "source_families": ["music_release_chart_award_source"],
        "candidate_sources": ["MusicBrainz Database", "Wikidata Query Service"],
        "query_template_alignment": {
            "exact_event_topic_template_available": False,
            "nearest_existing_template_id": "wikidata_music_public_fame_events",
            "nearest_existing_template_event_topic": "public_fame",
            "draft_event_topic": "career_peak",
            "draft_symbolic_event_topic": "career_project",
            "required_action": "review or add a music career_project query template before importing these draft labels",
        },
        "query_template_draft": _local_music_career_project_query_template_draft(),
        "requests": requests,
        "acceptance_gate": {
            "id": "local_music_source_review_requests_template_aligned",
            "passed": False,
            "reason": "music career_project draft labels require source-window review and query-template alignment",
        },
    }


def _local_music_career_project_query_template_draft() -> dict[str, Any]:
    template = {
        "template_id": "wikidata_music_career_project_events_draft",
        "domain": "music",
        "event_topic": "career_peak",
        "symbolic_event_topic": "career_project",
        "positive_event_type": "music_release_or_public_visibility",
        "negative_year_rule": (
            "A negative year requires a reviewed source-window query showing no qualifying release, "
            "award, chart/publication, or comparable career-project marker for the artist-year."
        ),
        "placeholders": ["PERSON_QID", "START_YEAR", "END_YEAR"],
        "sparql": (
            "SELECT ?event ?eventLabel ?date ?source WHERE { VALUES ?person { wd:PERSON_QID } "
            "{ ?event wdt:P175 ?person . } UNION { ?event wdt:P86 ?person . } "
            "UNION { ?event wdt:P166 ?award . ?event wdt:P1346 ?person . } "
            "OPTIONAL { ?event wdt:P577 ?date . } OPTIONAL { ?event prov:wasDerivedFrom ?source . } "
            "FILTER(YEAR(?date) >= START_YEAR && YEAR(?date) <= END_YEAR) "
            "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en,zh\". } } LIMIT 500"
        ),
        "result_mapping": {
            "record_id": "template_id + case_id + year + event_qid",
            "case_id": "input.case_id",
            "public_name": "input.public_name",
            "domain": "music",
            "industry": "music",
            "year": "YEAR(date)",
            "event_topic": "career_peak",
            "event_present": True,
            "event_type": "positive_event_type",
            "source_family_id": "music_release_chart_award_source",
            "source_name": "Wikidata Query Service",
            "source_url": "event or statement reference URL",
            "license_or_review": "source.license_or_review",
            "collected_before_rule_change": "collection_policy.collected_before_rule_change",
            "split_role": "collector supplied train or holdout",
            "negative_year_reason": None,
        },
        "manifest_record_defaults": {
            "source_family_id": "music_release_chart_award_source",
            "source_name": "Wikidata Query Service",
            "source_url": "https://query.wikidata.org/",
            "license_or_review": "example_source_requires_review",
        },
    }
    template_sha256 = _stable_sha256(template)
    missing_required_fields = sorted(REQUIRED_QUERY_TEMPLATE_FIELDS - set(template))
    return {
        "status": "draft_requires_query_plan_review",
        "template": template,
        "template_sha256": template_sha256,
        "query_plan_patch_plan": _query_template_patch_plan(template, template_sha256),
        "required_template_fields_present": sorted(REQUIRED_QUERY_TEMPLATE_FIELDS & set(template)),
        "missing_required_template_fields": missing_required_fields,
        "integrity_check": _query_template_draft_integrity_check(
            template,
            template_sha256,
            missing_required_fields,
        ),
        "acceptance_gate": {
            "id": "local_music_career_project_query_template_reviewed",
            "passed": False,
            "reason": "draft query template must be reviewed and added to the query-plan manifest before collection",
        },
    }


def _query_template_patch_plan(template: dict[str, Any], template_sha256: str) -> dict[str, Any]:
    material = {
        "schema_version": "query-template-draft-patch-plan-v1",
        "status": "draft_patch_requires_review",
        "target_path": str(default_industry_event_query_plan_path()),
        "operation": "append_query_template",
        "insert_after_template_id": "wikidata_music_public_fame_events",
        "expected_existing_template_count": 3,
        "expected_template_count_after_patch": 4,
        "template_id": template.get("template_id"),
        "template_sha256": template_sha256,
        "review_required_fields": [
            "SPARQL semantics",
            "source licensing",
            "identity matching",
            "negative-year source-window rule",
            "statement reference handling",
        ],
        "post_patch_commands": [
            "python -m examples.mingli_5agents.cli --repo .semas_mingli_repo industry-event-queries --query-plan examples\\mingli_5agents\\providers\\industry_event_source_query_plan_example.json",
            "pytest examples\\mingli_5agents\\tests\\test_empirical_validation.py::test_industry_event_query_plan_audits_example_contract -q",
        ],
        "acceptance_gate": {
            "id": "local_music_query_template_patch_reviewed",
            "passed": False,
            "reason": "patch plan is advisory until the query-plan manifest is edited and reviewed",
        },
    }
    patch_plan_receipt = _receipt("query-template-draft-patch-plan-receipt-v1", material)
    patch_plan_sha256 = _stable_sha256(material)
    return {
        **material,
        "applicability_check": _query_template_patch_plan_applicability_check(material),
        "patch_preview": _query_template_patch_preview(material, template),
        "patch_plan_receipt": patch_plan_receipt,
        "patch_plan_sha256": patch_plan_sha256,
        "integrity_check": _query_template_patch_plan_integrity_check(
            material,
            patch_plan_receipt,
            patch_plan_sha256,
            template_sha256,
        ),
    }


def _query_template_patch_preview(material: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    target_path = Path(str(material.get("target_path", "")))
    failures = []
    if not target_path.exists():
        return {
            "status": "blocked",
            "failures": [f"target query-plan manifest does not exist: {target_path}"],
            "execution_gate": {
                "passed": False,
                "reason": "patch preview never authorizes mutation",
            },
        }
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive for malformed local files
        return {
            "status": "blocked",
            "failures": [f"target query-plan manifest cannot be read: {exc}"],
            "execution_gate": {
                "passed": False,
                "reason": "patch preview never authorizes mutation",
            },
        }
    templates = payload.get("query_templates", []) if isinstance(payload, dict) else []
    if not isinstance(templates, list):
        failures.append("target query-plan manifest query_templates must be a list")
        templates = []
    insert_after = str(material.get("insert_after_template_id", ""))
    template_id = str(material.get("template_id", ""))
    patched_templates = []
    inserted = False
    for existing in templates:
        patched_templates.append(existing)
        if isinstance(existing, dict) and existing.get("template_id") == insert_after:
            patched_templates.append(template)
            inserted = True
    if not inserted:
        failures.append(f"insert-after template not found: {insert_after}")
    if any(
        isinstance(existing, dict) and existing.get("template_id") == template_id
        for existing in templates
    ):
        failures.append(f"draft template already exists in target manifest: {template_id}")
    patched_payload = dict(payload) if isinstance(payload, dict) else {}
    patched_payload["query_templates"] = patched_templates
    patched_template_ids = [
        str(item.get("template_id"))
        for item in patched_templates
        if isinstance(item, dict) and item.get("template_id")
    ]
    status = "preview_ready" if not failures else "blocked"
    patched_query_plan_sha256 = _stable_sha256(patched_payload) if not failures else None
    preview_material = {
        "schema_version": "query-template-patch-preview-v1",
        "status": status,
        "target_path": str(target_path),
        "would_write_file": False,
        "inserted_template_id": template_id if inserted and not failures else None,
        "patched_template_count": len(patched_templates),
        "patched_template_ids": patched_template_ids,
        "patched_query_plan_sha256": patched_query_plan_sha256,
        "failures": failures,
    }
    patch_preview_sha256 = _stable_sha256(preview_material)
    patch_preview_receipt = _receipt("query-template-patch-preview-receipt-v1", preview_material)
    return {
        "status": status,
        "target_path": str(target_path),
        "would_write_file": False,
        "inserted_template_id": template_id if inserted and not failures else None,
        "patched_template_count": len(patched_templates),
        "patched_template_ids": patched_template_ids,
        "patched_query_plan_sha256": patched_query_plan_sha256,
        "patch_preview_sha256": patch_preview_sha256,
        "patch_preview_receipt": patch_preview_receipt,
        "integrity_check": _query_template_patch_preview_integrity_check(
            preview_material,
            patch_preview_receipt,
            patch_preview_sha256,
            patched_query_plan_sha256,
        ),
        "failures": failures,
        "execution_gate": {
            "passed": False,
            "reason": "patch preview is non-mutating and does not authorize writing the query-plan manifest",
        },
    }


def _query_template_patch_preview_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    patch_preview_sha256: str,
    patched_query_plan_sha256: str | None,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_preview_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    preview_hash_matches = patch_preview_sha256 == recomputed_preview_sha256
    patched_query_plan_hash_matches = material.get("patched_query_plan_sha256") == patched_query_plan_sha256
    return {
        "status": "passed" if receipt_matches and preview_hash_matches and patched_query_plan_hash_matches else "failed",
        "patch_preview_receipt_matches_material": receipt_matches,
        "patch_preview_sha256_matches_material": preview_hash_matches,
        "patched_query_plan_sha256_matches_preview": patched_query_plan_hash_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_patch_preview_sha256": patch_preview_sha256,
        "recomputed_patch_preview_sha256": recomputed_preview_sha256,
    }


def _query_template_patch_plan_applicability_check(material: dict[str, Any]) -> dict[str, Any]:
    target_path = Path(str(material.get("target_path", "")))
    failures = []
    template_ids: list[str] = []
    if not target_path.exists():
        failures.append(f"target query-plan manifest does not exist: {target_path}")
    else:
        try:
            payload = json.loads(target_path.read_text(encoding="utf-8"))
            templates = payload.get("query_templates", []) if isinstance(payload, dict) else []
            template_ids = [
                str(template.get("template_id"))
                for template in templates
                if isinstance(template, dict) and template.get("template_id")
            ]
        except Exception as exc:  # pragma: no cover - defensive for malformed local files
            failures.append(f"target query-plan manifest cannot be read: {exc}")
    expected_count = int(material.get("expected_existing_template_count", -1))
    insert_after = str(material.get("insert_after_template_id", ""))
    template_id = str(material.get("template_id", ""))
    current_count_matches = len(template_ids) == expected_count
    insert_point_present = insert_after in template_ids
    template_absent = template_id not in template_ids
    if template_ids and not current_count_matches:
        failures.append(f"expected {expected_count} templates but found {len(template_ids)}")
    if template_ids and not insert_point_present:
        failures.append(f"insert-after template not found: {insert_after}")
    if template_ids and not template_absent:
        failures.append(f"draft template already exists in target manifest: {template_id}")
    applicable = not failures and current_count_matches and insert_point_present and template_absent
    return {
        "status": "applicable" if applicable else "blocked",
        "target_path_exists": target_path.exists(),
        "current_template_count": len(template_ids),
        "expected_existing_template_count": expected_count,
        "current_template_count_matches_expected": current_count_matches,
        "insert_after_template_id": insert_after,
        "insert_point_present": insert_point_present,
        "template_id": template_id,
        "template_absent_from_target": template_absent,
        "target_template_ids": template_ids,
        "failures": failures,
        "execution_gate": {
            "passed": False,
            "reason": "applicability does not authorize mutation; query-plan review is still required",
        },
    }


def _query_template_patch_plan_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    patch_plan_sha256: str,
    template_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_patch_plan_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    patch_hash_matches = patch_plan_sha256 == recomputed_patch_plan_sha256
    template_hash_matches = material.get("template_sha256") == template_sha256
    return {
        "status": "passed" if receipt_matches and patch_hash_matches and template_hash_matches else "failed",
        "patch_plan_receipt_matches_material": receipt_matches,
        "patch_plan_sha256_matches_material": patch_hash_matches,
        "template_sha256_matches_template_draft": template_hash_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_patch_plan_sha256": patch_plan_sha256,
        "recomputed_patch_plan_sha256": recomputed_patch_plan_sha256,
    }


def _query_template_draft_integrity_check(
    template: dict[str, Any],
    template_sha256: str,
    missing_required_fields: list[str],
) -> dict[str, Any]:
    recomputed_template_sha256 = _stable_sha256(template)
    hash_matches = template_sha256 == recomputed_template_sha256
    required_fields_complete = not missing_required_fields
    return {
        "status": "passed" if hash_matches and required_fields_complete else "failed",
        "template_sha256_matches_template": hash_matches,
        "required_template_fields_complete": required_fields_complete,
        "expected_template_sha256": template_sha256,
        "recomputed_template_sha256": recomputed_template_sha256,
        "missing_required_template_fields": missing_required_fields,
    }


def _local_music_source_review_request(record: dict[str, Any]) -> dict[str, Any]:
    event_present = record.get("event_present") is True
    year = int(record.get("year", 0))
    case_id = str(record.get("case_id", ""))
    return {
        "request_id": f"review_{record.get('record_id')}",
        "record_id": record.get("record_id"),
        "case_id": case_id,
        "public_name": record.get("public_name"),
        "year": year,
        "event_present": event_present,
        "review_goal": (
            "verify a qualifying music release, award, chart, publication, or public career-project marker"
            if event_present
            else "verify no qualifying music career-project marker in the reviewed source window"
        ),
        "suggested_sources": [
            {
                "source_name": "MusicBrainz Database",
                "review_focus": "artist releases, recordings, and release dates around the target year",
            },
            {
                "source_name": "Wikidata Query Service",
                "review_focus": "release, award, publication, and referenced statement evidence around the target year",
            },
        ],
        "source_window": {
            "start_year": year,
            "end_year": year,
            "negative_window_rule": (
                ""
                if event_present
                else "confirm no qualifying release, award, chart/publication, or comparable career-project marker for the person-year"
            ),
        },
        "required_manifest_fields": sorted(REQUIRED_RECORD_FIELDS),
    }


def _nearest_prior_negative_year(positive_year: int, positive_years: set[int]) -> int:
    candidate = positive_year - 1
    while candidate in positive_years:
        candidate -= 1
    return candidate


def _local_music_label_draft_record(
    *,
    case_id: str,
    public_name: Any,
    year: int,
    event_present: bool,
    source_url: Any,
    split_role: str,
) -> dict[str, Any]:
    return {
        "record_id": f"local_music_draft_{case_id}_{'positive' if event_present else 'negative'}_{year}",
        "case_id": case_id,
        "public_name": public_name,
        "domain": "music",
        "industry": "music",
        "year": year,
        "event_topic": "career_peak",
        "symbolic_event_topic": "career_project",
        "event_present": event_present,
        "event_type": "music_release_or_public_visibility" if event_present else "no_qualifying_event",
        "source_family_id": "music_release_chart_award_source",
        "source_name": "local famous-case fixture pending source review",
        "source_url": source_url,
        "license_or_review": "local_fixture_requires_industry_event_source_review",
        "collected_before_rule_change": True,
        "split_role": split_role,
        "negative_year_reason": (
            None
            if event_present
            else "draft adjacent negative year; production use requires reviewed source-window evidence"
        ),
    }


def _fetch_cache_plan_summary(fetch_plan: dict[str, Any]) -> dict[str, Any]:
    cache_paths = [
        str(entry.get("cache_path"))
        for plan in fetch_plan.get("plans", [])
        if isinstance(plan, dict)
        for entry in plan.get("cache_entries", [])
        if isinstance(entry, dict) and entry.get("cache_path")
    ]
    return {
        "status": fetch_plan.get("status"),
        "valid": fetch_plan.get("valid"),
        "offline_only": fetch_plan.get("offline_only"),
        "candidate_pool_fetch_cache_receipt_sha256": fetch_plan.get("candidate_pool_fetch_cache_receipt", {}).get(
            "sha256"
        ),
        "candidate_count": fetch_plan.get("candidate_count"),
        "plan_count": fetch_plan.get("plan_count"),
        "total_request_count": fetch_plan.get("total_request_count"),
        "total_planned_cache_count": fetch_plan.get("total_planned_cache_count"),
        "total_cache_write_count": fetch_plan.get("total_cache_write_count"),
        "case_ids": fetch_plan.get("case_ids", []),
        "planned_cache_paths": cache_paths,
        "failures": fetch_plan.get("failures", []),
    }


def _cache_materialization_summary(cache_paths: object) -> dict[str, Any]:
    paths = [str(path) for path in cache_paths] if isinstance(cache_paths, list) else []
    existing = [path for path in paths if Path(path).exists()]
    missing = [path for path in paths if not Path(path).exists()]
    return {
        "planned_cache_count": len(paths),
        "existing_cache_count": len(existing),
        "missing_cache_count": len(missing),
        "all_cache_files_present": bool(paths) and not missing,
        "existing_cache_paths": existing,
        "missing_cache_paths": missing,
    }


def _workplan_cache_materialization_summary(work_items: list[dict[str, Any]]) -> dict[str, Any]:
    paths = [
        str(path)
        for item in work_items
        if isinstance(item, dict)
        for path in item.get("fetch_cache_plan_summary", {}).get("planned_cache_paths", [])
    ]
    summary = _cache_materialization_summary(paths)
    summary["work_item_count"] = len(work_items)
    return summary


def _draft_import_readiness_gate(
    cache_materialization_summary: dict[str, Any],
    *,
    scope: str,
) -> dict[str, Any]:
    planned = int(cache_materialization_summary.get("planned_cache_count", 0))
    existing = int(cache_materialization_summary.get("existing_cache_count", 0))
    missing = int(cache_materialization_summary.get("missing_cache_count", 0))
    missing_paths = [
        str(path)
        for path in cache_materialization_summary.get("missing_cache_paths", [])
        if path
    ]
    passed = bool(cache_materialization_summary.get("all_cache_files_present")) and planned > 0
    if passed:
        next_action = "run industry-event-candidate-draft-import with the reviewed candidate pool and cache directory"
        reason = "all planned source response cache files are present"
    else:
        next_action = "run industry-event-candidate-fetch-cache after reviewing the query plan and source policy"
        reason = "draft import is blocked until every planned source response cache file exists"
    return {
        "id": "industry_event_draft_import_cache_materialized",
        "scope": scope,
        "passed": passed,
        "planned_cache_count": planned,
        "existing_cache_count": existing,
        "missing_cache_count": missing,
        "blocking_missing_cache_paths": missing_paths,
        "next_action": next_action,
        "reason": reason,
    }


def _workplan_readiness_summary(
    *,
    work_items: list[dict[str, Any]],
    deferred_tasks: list[dict[str, Any]],
    draft_import_readiness_gate: dict[str, Any],
    failures: list[Any],
) -> dict[str, Any]:
    missing_cache_count = int(draft_import_readiness_gate.get("missing_cache_count", 0))
    deferred_blocked_gate_count = sum(
        int(task.get("gate_summary", {}).get("blocked_gate_count", 0))
        for task in deferred_tasks
        if isinstance(task, dict)
    )
    deferred_failed_integrity_check_count = sum(
        int(task.get("gate_summary", {}).get("failed_integrity_check_count", 0))
        for task in deferred_tasks
        if isinstance(task, dict)
    )
    blockers: list[dict[str, Any]] = []
    if draft_import_readiness_gate.get("passed") is not True:
        blockers.append(
            {
                "scope": "workplan",
                "type": "cache_materialization",
                "id": draft_import_readiness_gate.get("id"),
                "count": missing_cache_count,
                "reason": draft_import_readiness_gate.get("reason", ""),
                "next_action": draft_import_readiness_gate.get("next_action", ""),
            }
        )
    for task in deferred_tasks:
        if not isinstance(task, dict):
            continue
        gate_summary = task.get("gate_summary", {})
        if not isinstance(gate_summary, dict) or gate_summary.get("status") != "blocked":
            continue
        blockers.append(
            {
                "scope": f"deferred_task:{task.get('task_id')}",
                "type": "deferred_review_gates",
                "blocked_gate_count": int(gate_summary.get("blocked_gate_count", 0)),
                "failed_integrity_check_count": int(gate_summary.get("failed_integrity_check_count", 0)),
                "next_action": gate_summary.get("next_action", ""),
            }
        )
    if failures:
        blockers.append(
            {
                "scope": "workplan",
                "type": "validation_failures",
                "count": len(failures),
                "reason": "candidate or evidence workplan validation failures are present",
                "next_action": "fix validation failures before collecting source evidence",
            }
        )
    status = "blocked" if blockers else "ready_for_draft_import"
    material = {
        "schema_version": "industry-event-evidence-workplan-readiness-summary-v1",
        "status": status,
        "source_collection_ready": not failures and bool(work_items),
        "draft_import_ready": draft_import_readiness_gate.get("passed") is True,
        "work_item_count": len(work_items),
        "deferred_task_count": len(deferred_tasks),
        "missing_cache_count": missing_cache_count,
        "deferred_blocked_gate_count": deferred_blocked_gate_count,
        "deferred_failed_integrity_check_count": deferred_failed_integrity_check_count,
        "blocked_summary": blockers,
        "next_action": _workplan_readiness_next_action(
            failures=failures,
            missing_cache_count=missing_cache_count,
            deferred_blocked_gate_count=deferred_blocked_gate_count,
            deferred_failed_integrity_check_count=deferred_failed_integrity_check_count,
            draft_import_readiness_gate=draft_import_readiness_gate,
        ),
    }
    readiness_summary_receipt = _receipt("industry-event-evidence-workplan-readiness-summary-receipt-v1", material)
    readiness_summary_sha256 = _stable_sha256(material)
    return {
        **material,
        "readiness_summary_receipt": readiness_summary_receipt,
        "readiness_summary_sha256": readiness_summary_sha256,
        "integrity_check": _workplan_readiness_summary_integrity_check(
            material,
            readiness_summary_receipt,
            readiness_summary_sha256,
        ),
    }


def _workplan_readiness_next_action(
    *,
    failures: list[Any],
    missing_cache_count: int,
    deferred_blocked_gate_count: int,
    deferred_failed_integrity_check_count: int,
    draft_import_readiness_gate: dict[str, Any],
) -> str:
    if failures:
        return "fix validation failures before collecting source evidence"
    if missing_cache_count:
        return str(draft_import_readiness_gate.get("next_action", "materialize missing source response cache files"))
    if deferred_failed_integrity_check_count:
        return "repair deferred task integrity checks before promoting draft evidence"
    if deferred_blocked_gate_count:
        return "resolve blocked deferred review gates before promoting draft labels or query templates"
    return "run industry-event-candidate-draft-import with the reviewed candidate pool and cache directory"


def _workplan_readiness_summary_integrity_check(
    material: dict[str, Any],
    receipt: dict[str, Any],
    readiness_summary_sha256: str,
) -> dict[str, Any]:
    recomputed_receipt = _receipt(str(receipt.get("schema_version", "")), material)
    recomputed_summary_sha256 = _stable_sha256(material)
    receipt_matches = receipt.get("sha256") == recomputed_receipt.get("sha256")
    summary_hash_matches = readiness_summary_sha256 == recomputed_summary_sha256
    return {
        "status": "passed" if receipt_matches and summary_hash_matches else "failed",
        "readiness_summary_receipt_matches_material": receipt_matches,
        "readiness_summary_sha256_matches_material": summary_hash_matches,
        "expected_receipt_sha256": receipt.get("sha256"),
        "recomputed_receipt_sha256": recomputed_receipt.get("sha256"),
        "expected_readiness_summary_sha256": readiness_summary_sha256,
        "recomputed_readiness_summary_sha256": recomputed_summary_sha256,
    }


def _candidate_manifest_failures(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["candidate manifest must be a JSON object"]
    failures: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
    failures.extend(f"missing top-level field: {field}" for field in missing)
    failures.extend(_review_failures(payload.get("review"), payload.get("status")))
    failures.extend(_selection_policy_failures(payload.get("selection_policy")))
    failures.extend(_required_candidate_fields_failures(payload.get("required_candidate_fields")))
    failures.extend(_candidate_failures(payload.get("candidates"), payload.get("selection_policy")))
    return failures


def _review_failures(review: Any, status: Any) -> list[str]:
    if not isinstance(review, dict):
        return ["review must be an object"]
    failures = []
    reviewed = review.get("externally_reviewed")
    if not isinstance(reviewed, bool):
        failures.append("review.externally_reviewed must be boolean")
    if status == "reviewed_candidate_pool" and reviewed is not True:
        failures.append("reviewed_candidate_pool requires review.externally_reviewed true")
    if reviewed is True:
        if not review.get("reviewer"):
            failures.append("review.reviewer is required when externally reviewed")
        if not review.get("review_date"):
            failures.append("review.review_date is required when externally reviewed")
        if review.get("approval") not in {"approved_for_candidate_pool"}:
            failures.append("review.approval must be approved_for_candidate_pool")
    return failures


def _selection_policy_failures(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["selection_policy must be an object"]
    failures = []
    missing = sorted(REQUIRED_SELECTION_POLICY_FIELDS - set(policy))
    failures.extend(f"selection_policy missing field: {field}" for field in missing)
    domains = policy.get("candidate_domains")
    if not isinstance(domains, list) or set(domains) != ALLOWED_DOMAINS:
        failures.append("selection_policy.candidate_domains must be film, music, and sports")
    if not isinstance(policy.get("min_candidates_per_domain"), int) or policy.get("min_candidates_per_domain", 0) < 1:
        failures.append("selection_policy.min_candidates_per_domain must be a positive integer")
    for field in (
        "requires_qid_source_url",
        "requires_identity_review_before_production",
        "requires_negative_year_collection",
        "collected_before_rule_change",
    ):
        if policy.get(field) is not True:
            failures.append(f"selection_policy.{field} must be true")
    return failures


def _required_candidate_fields_failures(fields: Any) -> list[str]:
    if not isinstance(fields, list):
        return ["required_candidate_fields must be a list"]
    missing = sorted(REQUIRED_CANDIDATE_FIELDS - {str(field) for field in fields})
    return [f"required_candidate_fields missing: {field}" for field in missing]


def _candidate_failures(candidates: Any, policy: Any) -> list[str]:
    if not isinstance(candidates, list) or not candidates:
        return ["candidates must be a non-empty list"]
    failures = []
    case_ids = set()
    qids = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            failures.append("each candidate must be an object")
            continue
        case_id = str(candidate.get("case_id", ""))
        person_qid = str(candidate.get("person_qid", ""))
        if not case_id:
            failures.append("candidate missing case_id")
        if case_id in case_ids:
            failures.append(f"duplicate case_id: {case_id}")
        case_ids.add(case_id)
        if person_qid in qids:
            failures.append(f"duplicate person_qid: {person_qid}")
        qids.add(person_qid)
        missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate))
        failures.extend(f"candidate {case_id or '<missing>'} missing field: {field}" for field in missing)
        failures.extend(_single_candidate_failures(candidate, case_id or "<missing>"))
    failures.extend(_domain_coverage_failures(candidates, policy))
    return failures


def _single_candidate_failures(candidate: dict[str, Any], case_id: str) -> list[str]:
    failures = []
    domain = candidate.get("domain")
    if domain not in ALLOWED_DOMAINS:
        failures.append(f"candidate {case_id} domain must be film, music, or sports")
    if candidate.get("event_query_domain") != domain:
        failures.append(f"candidate {case_id} event_query_domain must match domain")
    if candidate.get("split_role") not in ALLOWED_SPLIT_ROLES:
        failures.append(f"candidate {case_id} split_role must be train or holdout")
    if not _valid_qid(str(candidate.get("person_qid", ""))):
        failures.append(f"candidate {case_id} person_qid must look like Q123")
    if not str(candidate.get("public_source_url", "")).startswith("https://www.wikidata.org/wiki/Q"):
        failures.append(f"candidate {case_id} public_source_url must be a Wikidata entity URL")
    if candidate.get("collected_before_rule_change") is not True:
        failures.append(f"candidate {case_id} collected_before_rule_change must be true")
    window = candidate.get("collection_window")
    if not isinstance(window, dict):
        failures.append(f"candidate {case_id} collection_window must be an object")
    else:
        start_year = window.get("start_year")
        end_year = window.get("end_year")
        if not isinstance(start_year, int) or not isinstance(end_year, int):
            failures.append(f"candidate {case_id} collection_window years must be integers")
        elif start_year > end_year:
            failures.append(f"candidate {case_id} collection_window.start_year must be <= end_year")
    for field in ("public_name", "industry", "source_name", "source_lookup_method", "identity_review_status", "selection_reason"):
        if not candidate.get(field):
            failures.append(f"candidate {case_id} {field} is required")
    return failures


def _domain_coverage_failures(candidates: list[Any], policy: Any) -> list[str]:
    min_count = policy.get("min_candidates_per_domain", 1) if isinstance(policy, dict) else 1
    counts = _domain_counts(candidates)
    failures = []
    for domain in sorted(ALLOWED_DOMAINS):
        if counts.get(domain, 0) < min_count:
            failures.append(f"domain {domain} has fewer than {min_count} candidates")
    return failures


def _domain_counts(candidates: list[Any]) -> dict[str, int]:
    counts = {domain: 0 for domain in ALLOWED_DOMAINS}
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("domain") in ALLOWED_DOMAINS:
            counts[str(candidate["domain"])] += 1
    return {domain: count for domain, count in sorted(counts.items()) if count}


def _valid_qid(value: str) -> bool:
    return len(value) > 1 and value.startswith("Q") and value[1:].isdigit()


def _fetch_cache_plan_for_candidate(
    candidate: dict[str, Any],
    *,
    query_plan_path: Path,
    cache_dir: Path,
    live: bool,
) -> dict[str, Any]:
    window = candidate.get("collection_window", {}) if isinstance(candidate.get("collection_window"), dict) else {}
    return build_industry_event_fetch_cache_plan(
        query_plan_path,
        cache_dir=cache_dir,
        case_id=str(candidate.get("case_id", "")),
        public_name=str(candidate.get("public_name", "")),
        person_qid=str(candidate.get("person_qid", "")),
        start_year=int(window.get("start_year", 0)),
        end_year=int(window.get("end_year", 0)),
        split_role=str(candidate.get("split_role", "holdout")),
        domain=str(candidate.get("event_query_domain") or candidate.get("domain") or ""),
        live=live,
    )


def _candidate_pool_fetch_status(*, live: bool, failures: list[str]) -> str:
    if failures:
        return "blocked" if live else "invalid"
    return "fetched" if live else "dry_run"


def _combined_draft_manifest_payload(
    *,
    manifests: list[dict[str, Any]],
    candidate_path: Path,
    query_plan_path: Path,
    batch_plan: dict[str, Any],
) -> dict[str, Any]:
    source_families: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for manifest in manifests:
        for family in manifest.get("source_families", []):
            if isinstance(family, dict) and family.get("id"):
                source_families[str(family["id"])] = family
        for record in manifest.get("records", []):
            if isinstance(record, dict):
                records.append(record)
    return {
        "schema_version": "industry-event-source-manifest-v1",
        "status": "draft_candidate_pool_from_cached_responses_not_production_evidence",
        "purpose": "Combined draft manifest generated from cached public industry-event source responses.",
        "boundary": (
            "This candidate-pool draft is not production evidence. It requires source review, identity review, "
            "negative-year review, and approval before calibration use."
        ),
        "review": {
            "externally_reviewed": False,
            "reviewer": "review required",
            "review_date": None,
            "approval": "not_approved_for_production",
        },
        "required_record_fields": [
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
        ],
        "source_families": list(source_families.values()),
        "split_policy": {
            "frozen_before_rule_change": True,
            "allowed_split_roles": ["train", "holdout"],
            "negative_year_rule": "Each candidate-year without a qualifying cached response event is recorded as an explicit negative year.",
        },
        "records": records,
        "draft_provenance": {
            "candidate_path": str(candidate_path),
            "query_plan_path": str(query_plan_path),
            "candidate_pool_fetch_cache_receipt_sha256": batch_plan.get("candidate_pool_fetch_cache_receipt", {}).get(
                "sha256"
            ),
            "candidate_receipt_sha256": batch_plan.get("candidate_receipt", {}).get("sha256"),
            "offline_only": True,
        },
    }


def _draft_summary(draft: dict[str, Any]) -> dict[str, Any]:
    receipt_material = draft.get("draft_receipt", {}).get("material", {})
    if not isinstance(receipt_material, dict):
        receipt_material = {}
    return {
        "status": draft.get("status"),
        "valid": draft.get("valid"),
        "response_path": draft.get("response_path"),
        "response_sha256": draft.get("response_sha256"),
        "draft_receipt_sha256": draft.get("draft_receipt", {}).get("sha256")
        if isinstance(draft.get("draft_receipt"), dict)
        else None,
        "manifest_audit_receipt_sha256": receipt_material.get("manifest_audit_receipt_sha256"),
        "case_id": receipt_material.get("case_id"),
        "public_name": receipt_material.get("public_name"),
        "person_qid": receipt_material.get("person_qid"),
        "domain": receipt_material.get("domain"),
        "start_year": receipt_material.get("start_year"),
        "end_year": receipt_material.get("end_year"),
        "split_role": receipt_material.get("split_role"),
        "positive_record_count": receipt_material.get("positive_record_count", 0),
        "negative_record_count": receipt_material.get("negative_record_count", 0),
        "record_count": receipt_material.get("record_count", 0),
        "manifest_valid": receipt_material.get("manifest_valid"),
        "failures": receipt_material.get("failures", []),
    }


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
