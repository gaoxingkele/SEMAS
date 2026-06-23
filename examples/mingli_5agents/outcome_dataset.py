"""Ethical outcome-dataset manifest checks for future empirical validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_FIELDS = {
    "dataset_id",
    "version",
    "purpose",
    "consent",
    "privacy",
    "external_review",
    "data_split",
    "label_collection",
    "labels",
    "baselines",
    "statistical_plan",
    "records",
}

REQUIRED_RECORD_FIELDS = {
    "case_id",
    "birth",
    "labels",
}

ALLOWED_LABEL_TYPES = {
    "life_event_outcome",
    "report_quality",
    "schema_quality",
}


def audit_outcome_dataset_manifest(path: Path) -> dict[str, Any]:
    """Validate a candidate outcome dataset manifest without enabling optimization."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    failures = _manifest_failures(payload)
    records = payload.get("records", []) if isinstance(payload, dict) else []
    labels = payload.get("labels", []) if isinstance(payload, dict) else []
    label_types = sorted(
        {
            str(label.get("type"))
            for record in records
            if isinstance(record, dict)
            for label in _labels(record)
        }
    )
    predictive_records = sum(
        1
        for record in records
        if isinstance(record, dict)
        for label in _labels(record)
        if label.get("type") == "life_event_outcome"
    )
    return {
        "status": "ready_for_review" if not failures else "invalid",
        "path": str(path),
        "valid": not failures,
        "failures": failures,
        "dataset_id": payload.get("dataset_id") if isinstance(payload, dict) else None,
        "version": payload.get("version") if isinstance(payload, dict) else None,
        "record_count": len(records) if isinstance(records, list) else 0,
        "record_fingerprints": _record_fingerprints(records),
        "data_split_record_coverage": _data_split_record_coverage(payload),
        "label_types": label_types,
        "label_inventory": _label_inventory(payload),
        "label_provenance": _label_provenance_summary(payload),
        "quality_task_projection": _quality_task_projection(payload),
        "predictive_truth_records": predictive_records,
        "predictive_optimization_enabled": False,
        "optimization_policy": _optimization_policy(payload),
        "external_review": _external_review_summary(payload),
        "data_split": _data_split_summary(payload),
        "label_collection": _label_collection_summary(payload),
        "statistical_plan": _statistical_plan_summary(payload),
        "governance_gates": _governance_gates(payload, failures),
        "policy": "Outcome manifests are audit inputs only until consent, privacy, baselines, and statistical plans are externally reviewed.",
        "content_hash": _content_hash(payload),
    }


def _manifest_failures(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["manifest must be a JSON object"]
    failures: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
    failures.extend(f"missing top-level field: {field}" for field in missing)
    failures.extend(_consent_failures(payload.get("consent")))
    failures.extend(_privacy_failures(payload.get("privacy")))
    failures.extend(_external_review_failures(payload.get("external_review")))
    failures.extend(_label_collection_failures(payload.get("label_collection")))
    failures.extend(_label_definition_failures(payload.get("labels")))
    failures.extend(_baseline_failures(payload.get("baselines")))
    failures.extend(_statistical_plan_failures(payload.get("statistical_plan")))
    failures.extend(_record_failures(payload.get("records")))
    failures.extend(_label_provenance_failures(payload.get("records")))
    failures.extend(_data_split_failures(payload.get("data_split"), payload.get("records")))
    failures.extend(_record_label_reference_failures(payload.get("records"), payload.get("labels")))
    return failures


def _consent_failures(consent: Any) -> list[str]:
    if not isinstance(consent, dict):
        return ["consent must be an object"]
    failures = []
    if consent.get("documented") is not True:
        failures.append("consent.documented must be true")
    if consent.get("scope") not in {"research", "benchmarking", "quality_validation"}:
        failures.append("consent.scope must be research, benchmarking, or quality_validation")
    if not consent.get("withdrawal_process"):
        failures.append("consent.withdrawal_process is required")
    return failures


def _privacy_failures(privacy: Any) -> list[str]:
    if not isinstance(privacy, dict):
        return ["privacy must be an object"]
    failures = []
    if privacy.get("deidentified") is not True:
        failures.append("privacy.deidentified must be true")
    if privacy.get("direct_identifiers_removed") is not True:
        failures.append("privacy.direct_identifiers_removed must be true")
    if privacy.get("retention_policy") not in {"delete_after_study", "bounded_archive", "user_controlled"}:
        failures.append("privacy.retention_policy must be explicit")
    return failures


def _external_review_failures(review: Any) -> list[str]:
    if not isinstance(review, dict):
        return ["external_review must be an object"]
    failures = []
    if review.get("reviewed") is not True:
        failures.append("external_review.reviewed must be true")
    if not review.get("reviewer"):
        failures.append("external_review.reviewer is required")
    if not review.get("review_date"):
        failures.append("external_review.review_date is required")
    if review.get("approval") not in {"approved_for_quality_validation", "approved_for_audit_only"}:
        failures.append("external_review.approval must be approved_for_quality_validation or approved_for_audit_only")
    if not review.get("protocol_id"):
        failures.append("external_review.protocol_id is required")
    return failures


def _label_collection_failures(collection: Any) -> list[str]:
    if not isinstance(collection, dict):
        return ["label_collection must be an object"]
    failures = []
    if collection.get("source") not in {"self_report", "reviewer_scored", "mixed"}:
        failures.append("label_collection.source must be self_report, reviewer_scored, or mixed")
    if collection.get("collected_before_analysis") is not True:
        failures.append("label_collection.collected_before_analysis must be true")
    if not collection.get("collection_window"):
        failures.append("label_collection.collection_window is required")
    if not collection.get("adjudication"):
        failures.append("label_collection.adjudication is required")
    return failures


def _label_definition_failures(labels: Any) -> list[str]:
    if not isinstance(labels, list) or not labels:
        return ["labels must be a non-empty list"]
    failures = []
    ids = set()
    for label in labels:
        if not isinstance(label, dict):
            failures.append("each label definition must be an object")
            continue
        label_id = label.get("id")
        if not label_id:
            failures.append("label definition missing id")
        ids.add(str(label_id))
        if label.get("type") not in ALLOWED_LABEL_TYPES:
            failures.append(f"label {label_id} has unsupported type")
        if not label.get("definition"):
            failures.append(f"label {label_id} missing definition")
        if not label.get("measurement_window"):
            failures.append(f"label {label_id} missing measurement_window")
    if len(ids) != len(labels):
        failures.append("label ids must be unique")
    return failures


def _baseline_failures(baselines: Any) -> list[str]:
    if not isinstance(baselines, list) or not baselines:
        return ["baselines must be a non-empty list"]
    failures = []
    for baseline in baselines:
        if not isinstance(baseline, dict):
            failures.append("each baseline must be an object")
            continue
        if not baseline.get("name"):
            failures.append("baseline missing name")
        if not baseline.get("method"):
            failures.append("baseline missing method")
    return failures


def _statistical_plan_failures(plan: Any) -> list[str]:
    if not isinstance(plan, dict):
        return ["statistical_plan must be an object"]
    failures = []
    for key in ("hypotheses", "metrics", "minimum_sample_size", "holdout_strategy"):
        if not plan.get(key):
            failures.append(f"statistical_plan.{key} is required")
    sample_size = plan.get("minimum_sample_size")
    if not isinstance(sample_size, int) or sample_size < 30:
        failures.append("statistical_plan.minimum_sample_size must be an integer >= 30")
    if plan.get("pre_registered") is not True:
        failures.append("statistical_plan.pre_registered must be true")
    if not plan.get("registration_id"):
        failures.append("statistical_plan.registration_id is required")
    if not plan.get("registered_at"):
        failures.append("statistical_plan.registered_at is required")
    if not plan.get("analysis_freeze_date"):
        failures.append("statistical_plan.analysis_freeze_date is required")
    if not any(str(plan.get(field, "")).strip() for field in ("plan_sha256", "plan_receipt_sha256")):
        failures.append("statistical_plan.plan_sha256 or statistical_plan.plan_receipt_sha256 is required")
    return failures


def _record_failures(records: Any) -> list[str]:
    if not isinstance(records, list) or not records:
        return ["records must be a non-empty list"]
    failures = []
    case_ids = set()
    for record in records:
        if not isinstance(record, dict):
            failures.append("each record must be an object")
            continue
        missing = sorted(REQUIRED_RECORD_FIELDS - set(record))
        failures.extend(f"record missing field: {field}" for field in missing)
        case_id = str(record.get("case_id", ""))
        if case_id in case_ids:
            failures.append(f"duplicate case_id: {case_id}")
        case_ids.add(case_id)
        failures.extend(_birth_failures(record.get("birth"), case_id))
        if not _labels(record):
            failures.append(f"record {case_id} must include labels")
    return failures


def _data_split_failures(split: Any, records: Any) -> list[str]:
    if not isinstance(split, dict):
        return ["data_split must be an object"]
    failures = []
    if split.get("strategy") not in {"pre_registered_holdout", "audit_only", "temporal_holdout"}:
        failures.append("data_split.strategy must be pre_registered_holdout, audit_only, or temporal_holdout")
    if split.get("frozen") is not True:
        failures.append("data_split.frozen must be true")
    if not split.get("split_date"):
        failures.append("data_split.split_date is required")
    if not split.get("leakage_controls"):
        failures.append("data_split.leakage_controls is required")
    holdout_case_ids = split.get("holdout_case_ids")
    if not isinstance(holdout_case_ids, list) or not holdout_case_ids:
        failures.append("data_split.holdout_case_ids must be a non-empty list")
    train_case_ids = split.get("train_case_ids", [])
    if train_case_ids is not None and not isinstance(train_case_ids, list):
        failures.append("data_split.train_case_ids must be a list when present")
    if isinstance(records, list):
        record_ids = {str(record.get("case_id")) for record in records if isinstance(record, dict) and record.get("case_id")}
        train_ids = {str(item) for item in train_case_ids} if isinstance(train_case_ids, list) else set()
        holdout_ids = {str(item) for item in holdout_case_ids} if isinstance(holdout_case_ids, list) else set()
        unknown = sorted((train_ids | holdout_ids) - record_ids)
        if unknown:
            failures.append(f"data_split references unknown case_ids: {', '.join(unknown)}")
        overlap = sorted(train_ids & holdout_ids)
        if overlap:
            failures.append(f"data_split train and holdout case_ids overlap: {', '.join(overlap)}")
        unassigned = sorted(record_ids - (train_ids | holdout_ids))
        if unassigned:
            failures.append(f"data_split does not assign all record case_ids: {', '.join(unassigned)}")
    return failures


def _birth_failures(birth: Any, case_id: str) -> list[str]:
    if not isinstance(birth, dict):
        return [f"record {case_id} birth must be an object"]
    failures = []
    for key in ("birth_date", "birth_time", "gender"):
        if not birth.get(key):
            failures.append(f"record {case_id} birth.{key} is required")
    if birth.get("name"):
        failures.append(f"record {case_id} birth.name must be omitted for deidentification")
    return failures


def _labels(record: dict[str, Any]) -> list[dict[str, Any]]:
    labels = record.get("labels", [])
    return labels if isinstance(labels, list) else []


def _record_label_reference_failures(records: Any, label_definitions: Any) -> list[str]:
    if not isinstance(records, list) or not isinstance(label_definitions, list):
        return []
    definitions = {
        str(label.get("id")): str(label.get("type"))
        for label in label_definitions
        if isinstance(label, dict) and label.get("id")
    }
    failures = []
    for record in records:
        if not isinstance(record, dict):
            continue
        case_id = str(record.get("case_id", ""))
        for label in _labels(record):
            label_id = str(label.get("id", ""))
            label_type = str(label.get("type", ""))
            if label_id not in definitions:
                failures.append(f"record {case_id} label {label_id} has no label definition")
            elif definitions[label_id] != label_type:
                failures.append(
                    f"record {case_id} label {label_id} type {label_type} does not match definition {definitions[label_id]}"
                )
    return failures


def _label_provenance_failures(records: Any) -> list[str]:
    if not isinstance(records, list):
        return []
    failures = []
    for record in records:
        if not isinstance(record, dict):
            continue
        case_id = str(record.get("case_id", ""))
        for label in _labels(record):
            label_id = str(label.get("id", ""))
            provenance = label.get("provenance")
            if not isinstance(provenance, dict):
                failures.append(f"record {case_id} label {label_id} provenance must be an object")
                continue
            for field in ("source", "collected_at", "reviewer_or_method"):
                if not provenance.get(field):
                    failures.append(f"record {case_id} label {label_id} provenance.{field} is required")
            if provenance.get("collected_before_analysis") is not True:
                failures.append(f"record {case_id} label {label_id} provenance.collected_before_analysis must be true")
            if label.get("type") == "life_event_outcome" and provenance.get("audit_only_acknowledged") is not True:
                failures.append(
                    f"record {case_id} label {label_id} provenance.audit_only_acknowledged must be true for life_event_outcome"
                )
    return failures


def _label_inventory(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "definitions": {},
            "record_labels": {},
            "defined_label_ids": [],
            "observed_label_ids": [],
            "undefined_label_ids": [],
        }
    definitions = payload.get("labels", [])
    records = payload.get("records", [])
    definition_counts: dict[str, int] = {}
    for label in definitions if isinstance(definitions, list) else []:
        if isinstance(label, dict):
            label_type = str(label.get("type", "unknown"))
            definition_counts[label_type] = definition_counts.get(label_type, 0) + 1
    record_counts: dict[str, int] = {}
    definition_ids = {str(label.get("id")) for label in definitions if isinstance(label, dict) and label.get("id")}
    observed_ids = set()
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        for label in _labels(record):
            label_type = str(label.get("type", "unknown"))
            record_counts[label_type] = record_counts.get(label_type, 0) + 1
            if label.get("id"):
                observed_ids.add(str(label.get("id")))
    return {
        "definitions": definition_counts,
        "record_labels": record_counts,
        "defined_label_ids": sorted(definition_ids),
        "observed_label_ids": sorted(observed_ids),
        "undefined_label_ids": sorted(observed_ids - definition_ids),
    }


def _label_provenance_summary(payload: Any) -> dict[str, Any]:
    records = payload.get("records", []) if isinstance(payload, dict) else []
    total = 0
    complete = 0
    missing = []
    sources: dict[str, int] = {}
    reviewer_or_methods: dict[str, int] = {}
    audit_only_acknowledged = 0
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        case_id = str(record.get("case_id", ""))
        for label in _labels(record):
            total += 1
            label_id = str(label.get("id", ""))
            provenance = label.get("provenance")
            if isinstance(provenance, dict):
                source = str(provenance.get("source") or "")
                reviewer = str(provenance.get("reviewer_or_method") or "")
                if source:
                    sources[source] = sources.get(source, 0) + 1
                if reviewer:
                    reviewer_or_methods[reviewer] = reviewer_or_methods.get(reviewer, 0) + 1
                if provenance.get("audit_only_acknowledged") is True:
                    audit_only_acknowledged += 1
                required_ok = (
                    bool(provenance.get("source"))
                    and bool(provenance.get("collected_at"))
                    and bool(provenance.get("reviewer_or_method"))
                    and provenance.get("collected_before_analysis") is True
                    and (
                        label.get("type") != "life_event_outcome"
                        or provenance.get("audit_only_acknowledged") is True
                    )
                )
                if required_ok:
                    complete += 1
                    continue
            missing.append({"case_id": case_id, "label_id": label_id})
    return {
        "label_count": total,
        "complete_count": complete,
        "provenance_complete": total > 0 and total == complete,
        "missing": missing,
        "sources": sources,
        "reviewer_or_methods": reviewer_or_methods,
        "audit_only_acknowledged_count": audit_only_acknowledged,
    }


def _record_fingerprints(records: Any) -> list[dict[str, str]]:
    if not isinstance(records, list):
        return []
    fingerprints = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        encoded = json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
        fingerprints.append(
            {
                "case_id": str(record.get("case_id", f"record_{index}")),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
    return fingerprints


def _data_split_record_coverage(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "record_count": 0,
            "assigned_count": 0,
            "train_count": 0,
            "holdout_count": 0,
            "unassigned_case_ids": [],
            "unknown_case_ids": [],
            "overlap_case_ids": [],
            "coverage_complete": False,
            "split_fingerprint": None,
        }
    records = payload.get("records", [])
    split = payload.get("data_split", {})
    record_ids = sorted(
        str(record.get("case_id"))
        for record in records
        if isinstance(records, list) and isinstance(record, dict) and record.get("case_id")
    )
    train_ids = (
        sorted(str(item) for item in split.get("train_case_ids", []))
        if isinstance(split, dict) and isinstance(split.get("train_case_ids", []), list)
        else []
    )
    holdout_ids = (
        sorted(str(item) for item in split.get("holdout_case_ids", []))
        if isinstance(split, dict) and isinstance(split.get("holdout_case_ids", []), list)
        else []
    )
    record_id_set = set(record_ids)
    train_set = set(train_ids)
    holdout_set = set(holdout_ids)
    assigned = train_set | holdout_set
    unknown = sorted(assigned - record_id_set)
    overlap = sorted(train_set & holdout_set)
    unassigned = sorted(record_id_set - assigned)
    material = {
        "dataset_id": payload.get("dataset_id"),
        "version": payload.get("version"),
        "record_case_ids": record_ids,
        "train_case_ids": train_ids,
        "holdout_case_ids": holdout_ids,
    }
    return {
        "record_count": len(record_ids),
        "assigned_count": len(record_id_set & assigned),
        "train_count": len(train_ids),
        "holdout_count": len(holdout_ids),
        "unassigned_case_ids": unassigned,
        "unknown_case_ids": unknown,
        "overlap_case_ids": overlap,
        "coverage_complete": bool(record_ids) and not unassigned and not unknown and not overlap,
        "split_fingerprint": hashlib.sha256(
            json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest(),
    }


def _quality_task_projection(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "included_label_types": ["report_quality", "schema_quality"],
            "excluded_label_types": ["life_event_outcome"],
            "projected_task_count": 0,
            "audit_only_label_count": 0,
            "projected_task_fingerprints": [],
        }
    projected = []
    audit_only_count = 0
    records = payload.get("records", [])
    split_roles = _split_roles(payload)
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        case_id = str(record.get("case_id", ""))
        for label in _labels(record):
            label_type = label.get("type")
            if label_type in {"report_quality", "schema_quality"}:
                projected.append(
                    {
                        "case_id": case_id,
                        "label_id": str(label.get("id", label_type)),
                        "split_role": split_roles.get(case_id, "unassigned"),
                        "sha256": _projected_task_fingerprint(record, label, payload),
                    }
                )
            elif label_type == "life_event_outcome":
                audit_only_count += 1
    return {
        "included_label_types": ["report_quality", "schema_quality"],
        "excluded_label_types": ["life_event_outcome"],
        "projected_task_count": len(projected),
        "audit_only_label_count": audit_only_count,
        "projected_task_fingerprints": projected,
    }


def _split_roles(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    split = payload.get("data_split")
    if not isinstance(split, dict):
        return {}
    roles: dict[str, str] = {}
    train_ids = split.get("train_case_ids", [])
    holdout_ids = split.get("holdout_case_ids", [])
    if isinstance(train_ids, list):
        roles.update({str(case_id): "train" for case_id in train_ids})
    if isinstance(holdout_ids, list):
        roles.update({str(case_id): "holdout" for case_id in holdout_ids})
    return roles


def _projected_task_fingerprint(record: dict[str, Any], label: dict[str, Any], payload: dict[str, Any]) -> str:
    projection = {
        "dataset_id": payload.get("dataset_id"),
        "version": payload.get("version"),
        "case_id": record.get("case_id"),
        "birth": record.get("birth"),
        "input_overrides": record.get("input_overrides", {}),
        "label": label,
    }
    encoded = json.dumps(projection, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _optimization_policy(payload: Any) -> dict[str, Any]:
    inventory = _label_inventory(payload)
    record_counts = inventory.get("record_labels", {})
    predictive_count = int(record_counts.get("life_event_outcome", 0)) if isinstance(record_counts, dict) else 0
    return {
        "quality_task_label_types": ["report_quality", "schema_quality"],
        "audit_only_label_types": ["life_event_outcome"],
        "predictive_truth_optimization_enabled": False,
        "predictive_truth_records": predictive_count,
        "blocked_reason": (
            "life_event_outcome labels are audit-only until external review, preregistration, baselines, and holdout rules approve predictive optimization"
            if predictive_count
            else "no predictive truth labels configured"
        ),
    }


def _external_review_summary(payload: Any) -> dict[str, Any]:
    review = payload.get("external_review") if isinstance(payload, dict) else None
    if not isinstance(review, dict):
        return {"reviewed": False, "approval": None, "reviewer": None, "review_date": None, "protocol_id": None}
    return {
        "reviewed": review.get("reviewed") is True,
        "approval": review.get("approval"),
        "reviewer": review.get("reviewer"),
        "review_date": review.get("review_date"),
        "protocol_id": review.get("protocol_id"),
    }


def _data_split_summary(payload: Any) -> dict[str, Any]:
    split = payload.get("data_split") if isinstance(payload, dict) else None
    if not isinstance(split, dict):
        return {
            "strategy": None,
            "frozen": False,
            "split_date": None,
            "train_count": 0,
            "holdout_count": 0,
            "leakage_controls_present": False,
        }
    train_case_ids = split.get("train_case_ids", [])
    holdout_case_ids = split.get("holdout_case_ids", [])
    return {
        "strategy": split.get("strategy"),
        "frozen": split.get("frozen") is True,
        "split_date": split.get("split_date"),
        "train_count": len(train_case_ids) if isinstance(train_case_ids, list) else 0,
        "holdout_count": len(holdout_case_ids) if isinstance(holdout_case_ids, list) else 0,
        "leakage_controls_present": bool(split.get("leakage_controls")),
    }


def _label_collection_summary(payload: Any) -> dict[str, Any]:
    collection = payload.get("label_collection") if isinstance(payload, dict) else None
    if not isinstance(collection, dict):
        return {
            "source": None,
            "collected_before_analysis": False,
            "collection_window": None,
            "adjudication": None,
        }
    return {
        "source": collection.get("source"),
        "collected_before_analysis": collection.get("collected_before_analysis") is True,
        "collection_window": collection.get("collection_window"),
        "adjudication": collection.get("adjudication"),
    }


def _statistical_plan_summary(payload: Any) -> dict[str, Any]:
    plan = payload.get("statistical_plan") if isinstance(payload, dict) else None
    if not isinstance(plan, dict):
        return {
            "pre_registered": False,
            "registration_id": None,
            "registered_at": None,
            "analysis_freeze_date": None,
            "minimum_sample_size": None,
            "holdout_strategy": None,
            "plan_sha256": None,
            "plan_receipt_sha256": None,
            "preregistration_complete": False,
        }
    has_plan_hash = bool(str(plan.get("plan_sha256") or "").strip())
    has_receipt_hash = bool(str(plan.get("plan_receipt_sha256") or "").strip())
    return {
        "pre_registered": plan.get("pre_registered") is True,
        "registration_id": plan.get("registration_id"),
        "registered_at": plan.get("registered_at"),
        "analysis_freeze_date": plan.get("analysis_freeze_date"),
        "minimum_sample_size": plan.get("minimum_sample_size"),
        "holdout_strategy": plan.get("holdout_strategy"),
        "plan_sha256": plan.get("plan_sha256"),
        "plan_receipt_sha256": plan.get("plan_receipt_sha256"),
        "preregistration_complete": (
            plan.get("pre_registered") is True
            and bool(plan.get("registration_id"))
            and bool(plan.get("registered_at"))
            and bool(plan.get("analysis_freeze_date"))
            and (has_plan_hash or has_receipt_hash)
        ),
    }


def _governance_gates(payload: Any, failures: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "passed": False,
            "gates": {"json_object": False},
            "blocking_failures": failures,
        }
    consent = payload.get("consent")
    privacy = payload.get("privacy")
    review = payload.get("external_review")
    split = payload.get("data_split")
    collection = payload.get("label_collection")
    plan = payload.get("statistical_plan")
    records = payload.get("records")
    inventory = _label_inventory(payload)
    split_coverage = _data_split_record_coverage(payload)
    label_provenance = _label_provenance_summary(payload)
    statistical_plan = _statistical_plan_summary(payload)
    gates = {
        "consent_documented": isinstance(consent, dict) and consent.get("documented") is True,
        "withdrawal_process_present": isinstance(consent, dict) and bool(consent.get("withdrawal_process")),
        "deidentified": isinstance(privacy, dict) and privacy.get("deidentified") is True,
        "direct_identifiers_removed": isinstance(privacy, dict) and privacy.get("direct_identifiers_removed") is True,
        "external_review_approved": isinstance(review, dict)
        and review.get("reviewed") is True
        and review.get("approval") in {"approved_for_quality_validation", "approved_for_audit_only"},
        "label_collection_pre_analysis": isinstance(collection, dict)
        and collection.get("collected_before_analysis") is True,
        "data_split_frozen": isinstance(split, dict) and split.get("frozen") is True,
        "holdout_case_ids_present": isinstance(split, dict)
        and isinstance(split.get("holdout_case_ids"), list)
        and bool(split.get("holdout_case_ids")),
        "data_split_records_covered": split_coverage.get("coverage_complete") is True,
        "baselines_present": isinstance(payload.get("baselines"), list) and bool(payload.get("baselines")),
        "statistical_plan_present": isinstance(plan, dict) and bool(plan.get("hypotheses")) and bool(plan.get("metrics")),
        "minimum_sample_size_declared": isinstance(plan, dict) and isinstance(plan.get("minimum_sample_size"), int) and plan.get("minimum_sample_size") >= 30,
        "statistical_plan_preregistered": statistical_plan.get("preregistration_complete") is True,
        "records_present": isinstance(records, list) and bool(records),
        "record_labels_defined": not inventory.get("undefined_label_ids"),
        "record_label_provenance_complete": label_provenance.get("provenance_complete") is True,
        "predictive_optimization_disabled": True,
    }
    return {
        "passed": not failures and all(gates.values()),
        "gates": gates,
        "blocking_failures": failures,
    }


def _content_hash(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
