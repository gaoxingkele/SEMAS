"""Reusable service functions for the mingli five-agent framework."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semas.genome.repository import GenomeRepository
from semas.utils.llm_client import llm_backend_status

from examples.mingli_5agents.benchmark import benchmark_cases, compare_versions, run_benchmark
from examples.mingli_5agents.birth_profile_review import (
    audit_birth_profile_review_manifest,
    build_birth_profile_fixture_patch_preview,
    birth_profile_review_manifest_receipt,
    build_birth_profile_import_preview,
    build_birth_profile_source_cache_audit,
    build_birth_profile_source_cache_template_preview,
    build_birth_profile_source_lookup_plan,
    build_birth_profile_source_review_workplan,
    build_birth_profile_reviewed_manifest_draft_preview,
    build_birth_profile_reviewed_manifest_file_preview,
    default_birth_profile_review_manifest_path,
)
from examples.mingli_5agents.capability_audit import (
    capability_audit as build_capability_audit,
    known_gap_verification_command_coverage,
)
from examples.mingli_5agents.classical_corpus_refresh import refresh_corpus_manifests, source_list_audit
from examples.mingli_5agents.empirical_validation import (
    empirical_validation_tasks,
    outcome_dataset_audit,
    outcome_dataset_evolution_gate,
)
from examples.mingli_5agents.evolution import METRIC_FLOORS, MingliEvolutionArchive, MingliPopulationEvolver, genome_fingerprint
from examples.mingli_5agents.industry_event_manifest import (
    audit_industry_event_manifest,
    build_industry_event_symbolic_annual_score,
    build_industry_event_symbolic_scoring_readiness,
    build_industry_event_validation_label_table,
    default_industry_event_manifest_path,
    industry_event_manifest_receipt,
)
from examples.mingli_5agents.industry_event_candidates import (
    audit_industry_event_candidate_cases,
    build_candidate_pool_fetch_cache_plan,
    build_candidate_pool_manifest_drafts_from_cache,
    build_industry_event_evidence_workplan_from_symbolic_score,
    default_industry_event_candidate_cases_path,
    industry_event_candidate_cases_receipt,
)
from examples.mingli_5agents.industry_event_query_plan import (
    audit_industry_event_query_plan,
    build_industry_event_collection_request_bundle,
    build_industry_event_fetch_cache_plan,
    build_industry_event_manifest_draft_from_wikidata_response,
    default_industry_event_query_plan_path,
    industry_event_query_plan_receipt,
)
from examples.mingli_5agents.famous_case_validation import famous_case_records
from examples.mingli_5agents.memory import MingliFeedbackMemory
from examples.mingli_5agents.method_surface import method_surface_receipt
from examples.mingli_5agents.provider_checks import (
    JSON_CLI_CHECK_BY_DOMAIN,
    bundled_provider_example_smoke,
    certify_json_cli_provider,
    provider_health_checks,
)
from examples.mingli_5agents.provider_protocols import provider_protocol_document, provider_protocol_receipt
from examples.mingli_5agents.production_gates import PRODUCTION_READINESS_GATE_IDS
from examples.mingli_5agents.run_demo import MingliFiveAgentSystem, bootstrap_repo, build_mingli_evaluator
from examples.mingli_5agents.tools.calendar_core import describe_calendar_providers
from examples.mingli_5agents.tools.professional_chart_provider import describe_domain_chart_providers


_BENCHMARK_ANALYZE_RESPONSE_SCHEMA_CACHE: dict[tuple[str, int], dict[str, Any]] = {}


def ensure_repo(repo_path: Path) -> GenomeRepository:
    """Open an existing repo or bootstrap it if no coordinator genome exists."""
    repo = GenomeRepository(repo_path)
    try:
        repo.load_agent("mingli_orchestrator")
    except FileNotFoundError:
        repo = bootstrap_repo(repo_path)
    return repo


def init_repo(repo_path: Path) -> dict[str, Any]:
    """Initialize or reset a mingli genome repository."""
    repo = bootstrap_repo(repo_path)
    latest = repo.load_agent("mingli_orchestrator")
    return {
        "repo": str(repo_path),
        "status": "initialized",
        "coordinator_version": latest.version,
        "agents": [
            "mingli_orchestrator",
            "bazi_analyst",
            "ziwei_analyst",
            "qimen_analyst",
            "astrology_analyst",
        ],
    }


def analyze_case(
    repo_path: Path,
    task_input: dict[str, Any],
    expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one analysis and return runtime output plus evaluator metrics."""
    repo = ensure_repo(repo_path)
    agent = repo.load_agent("mingli_orchestrator")
    result = MingliFiveAgentSystem(repo)(agent, task_input)
    evaluation = build_mingli_evaluator().evaluate({**task_input, **result}, expected)
    response = {
        "repo": str(repo_path),
        "agent_version": agent.version,
        "passed": evaluation.passed,
        "score": evaluation.score,
        "metrics": evaluation.metrics,
        "result": result,
        "schema_validation": {
            "schema_name": "AnalyzeResponse",
            "valid": False,
            "error_count": 0,
            "errors": [],
        },
    }
    json_response = json.loads(json.dumps(response, ensure_ascii=False))
    errors = schema_validation_errors(json_response, schema_name="AnalyzeResponse")
    response["schema_validation"] = {
        "schema_name": "AnalyzeResponse",
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
    }
    return response


def evolve_case(
    repo_path: Path,
    task_input: dict[str, Any],
    feedback: dict[str, Any],
    *,
    validate_on_input: bool = False,
) -> dict[str, Any]:
    """Store feedback, run population evolution, and return selected genome status."""
    repo = ensure_repo(repo_path)
    train_tasks = [{"input": task_input, "expected": feedback}]
    validation_gate = outcome_dataset_evolution_gate()
    trigger_receipt = _evolution_trigger_receipt(
        repo_path=repo_path,
        task_input=task_input,
        feedback=feedback,
        train_tasks=train_tasks,
        validation_tasks=[],
        validation_gate=validation_gate,
        validate_on_input=validate_on_input,
    )
    if not validation_gate["passed"]:
        latest = repo.load_agent("mingli_orchestrator")
        selection_decision = {
            "accepted": False,
            "selected": latest.meta.get("candidate_name"),
            "baseline_average_score": None,
            "selected_average_score": None,
            "selected_adjusted_score": None,
            "validation_average_score": None,
            "validation_task_count": 0,
            "gates": {
                "outcome_dataset_gate": False,
                "regression_gate": False,
                "metric_floors": False,
                "train_score_improved": False,
                "validation_metric_floors": False,
                "validation_score_not_regressed": False,
            },
            "rejection_reasons": validation_gate.get("blocking_failures", []) or [validation_gate["reason"]],
        }
        return {
            "repo": str(repo_path),
            "accepted": False,
            "blocked": True,
            "block_reason": validation_gate["reason"],
            "validation_gate": validation_gate,
            "trigger_receipt": trigger_receipt,
            "selection_decision": selection_decision,
            "before_version": latest.version,
            "after_version": latest.version,
            "selected": latest.meta.get("candidate_name"),
            "workflow": latest.meta.get("workflow"),
            "validation_case_count": 0,
            "memory_profile": MingliFeedbackMemory(repo_path / "memory" / "feedback_memory.json").profile(),
            "archive_events": len(MingliEvolutionArchive(repo_path / "archives" / "mingli_evolution.json").load()),
        }
    validation_tasks = empirical_validation_tasks()
    if validate_on_input:
        validation_tasks = [{"input": task_input, "expected": feedback}, *validation_tasks]
    trigger_receipt = _evolution_trigger_receipt(
        repo_path=repo_path,
        task_input=task_input,
        feedback=feedback,
        train_tasks=train_tasks,
        validation_tasks=validation_tasks,
        validation_gate=validation_gate,
        validate_on_input=validate_on_input,
    )
    memory = MingliFeedbackMemory(repo_path / "memory" / "feedback_memory.json")
    memory.remember_feedback(feedback, notes="api feedback")
    archive = MingliEvolutionArchive(repo_path / "archives" / "mingli_evolution.json")
    evolver = MingliPopulationEvolver(
        repo=repo,
        evaluator=build_mingli_evaluator(),
        executor=MingliFiveAgentSystem(repo),
        archive=archive,
        memory=memory,
    )
    before = repo.load_agent("mingli_orchestrator")
    evolved = evolver.evolve(
        train_tasks=train_tasks,
        validation_tasks=validation_tasks,
        trigger_receipt=trigger_receipt,
    )
    after = repo.load_agent("mingli_orchestrator")
    archive_events = archive.load()
    latest_event = archive_events[-1] if archive_events else {}
    selection_decision = latest_event.get("selection_decision") if isinstance(latest_event, dict) else None
    return {
        "repo": str(repo_path),
        "accepted": evolved is not None,
        "blocked": False,
        "validation_gate": validation_gate,
        "trigger_receipt": trigger_receipt,
        "selection_decision": selection_decision,
        "before_version": before.version,
        "after_version": after.version,
        "selected": after.meta.get("candidate_name"),
        "workflow": after.meta.get("workflow"),
        "validation_case_count": len(validation_tasks),
        "memory_profile": memory.profile(),
        "archive_events": len(archive_events),
    }


def _evolution_trigger_receipt(
    *,
    repo_path: Path,
    task_input: dict[str, Any],
    feedback: dict[str, Any],
    train_tasks: list[dict[str, Any]],
    validation_tasks: list[dict[str, Any]],
    validation_gate: dict[str, Any],
    validate_on_input: bool,
) -> dict[str, Any]:
    """Bind the reason and materials that triggered a SEMAS evolution run."""
    feedback_present = bool(feedback)
    feedback_corrections = feedback.get("feedback", {}).get("corrections", []) if isinstance(feedback, dict) else []
    if not isinstance(feedback_corrections, list):
        feedback_corrections = []
    trigger_reasons = []
    if feedback_present:
        trigger_reasons.append("explicit_feedback")
    if validate_on_input:
        trigger_reasons.append("operator_requested_input_validation")
    if not validation_gate.get("passed"):
        trigger_reasons.append("outcome_dataset_gate_blocked")
    if not trigger_reasons:
        trigger_reasons.append("operator_command")
    material = {
        "schema_version": "evolution-trigger-receipt-v1",
        "repo": str(repo_path),
        "trigger_reasons": trigger_reasons,
        "feedback_present": feedback_present,
        "feedback_correction_count": len(feedback_corrections),
        "feedback_sha256": _json_sha256(feedback),
        "task_input_sha256": _json_sha256(task_input),
        "train_task_count": len(train_tasks),
        "train_task_sha256": _json_sha256(train_tasks),
        "validation_task_count": len(validation_tasks),
        "validation_task_sha256": _json_sha256(validation_tasks),
        "validate_on_input": validate_on_input,
        "outcome_dataset_gate_passed": validation_gate.get("passed") is True,
        "outcome_dataset_gate_reason": validation_gate.get("reason", ""),
        "outcome_dataset_gate_blocking_failures": validation_gate.get("blocking_failures", []),
        "policy": (
            "SEMAS evolution may react to explicit feedback and quality gates, but predictive truth optimization "
            "remains blocked unless reviewed outcome-dataset governance passes."
        ),
    }
    encoded = json.dumps(material, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": material["schema_version"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _json_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def rollback_coordinator(repo_path: Path, to_version: int, reason: str | None = None) -> dict[str, Any]:
    """Roll back the coordinator to a prior version while preserving audit lineage."""
    repo = ensure_repo(repo_path)
    before = repo.load_agent("mingli_orchestrator")
    if to_version >= before.version:
        raise ValueError("rollback target must be an existing prior coordinator version")
    rollback_reason = (reason or "operator_requested_rollback").strip() or "operator_requested_rollback"
    target = repo.load_agent("mingli_orchestrator", version=to_version)
    target_meta = {
        key: value
        for key, value in target.meta.items()
        if key not in {"evolution_lineage", "rollback_lineage"}
    }
    rolled = target.evolve_from(
        version=before.version + 1,
        parent_version=before.version,
        meta={
            **target_meta,
            "rolled_back_from": before.version,
            "rollback_target_version": to_version,
            "rollback_reason": rollback_reason,
        },
    )
    archive = MingliEvolutionArchive(repo_path / "archives" / "mingli_evolution.json")
    archived_event = archive.append(
        {
            "event": "rollback",
            "from_version": before.version,
            "target_version": to_version,
            "accepted_genome_version": rolled.version,
            "target_genome_fingerprint": genome_fingerprint(target),
            "rollback_reason": rollback_reason,
        }
    )
    lineage = {
        "event": "rollback",
        "archive_hash": archived_event.get("archive_hash"),
        "previous_archive_hash": archived_event.get("previous_archive_hash"),
        "archive_timestamp": archived_event.get("timestamp"),
        "genome_fingerprint": genome_fingerprint(rolled),
        "baseline_genome_version": before.version,
        "accepted_genome_version": rolled.version,
        "selected_strategy": None,
        "selection_decision": None,
        "trigger_receipt": None,
        "reproducibility_manifest": None,
        "rollback_target_version": to_version,
        "rollback_reason": rollback_reason,
    }
    rolled = rolled.model_copy(update={"meta": {**rolled.meta, "evolution_lineage": lineage}})
    repo.save_agent(rolled)
    return {
        "repo": str(repo_path),
        "status": "rolled_back",
        "before_version": before.version,
        "target_version": to_version,
        "after_version": rolled.version,
        "rollback_reason": rollback_reason,
        "archive_hash": archived_event.get("archive_hash"),
        "genome_lineage": lineage,
        "archive_integrity": archive.integrity_report(),
    }


def status(repo_path: Path) -> dict[str, Any]:
    """Return latest genome, provider, archive, and memory status."""
    repo = ensure_repo(repo_path)
    agent = repo.load_agent("mingli_orchestrator")
    archive = MingliEvolutionArchive(repo_path / "archives" / "mingli_evolution.json")
    memory = MingliFeedbackMemory(repo_path / "memory" / "feedback_memory.json")
    archive_events = archive.load()
    return {
        "repo": str(repo_path),
        "coordinator_version": agent.version,
        "candidate_name": agent.meta.get("candidate_name"),
        "genome_lineage": agent.meta.get("evolution_lineage"),
        "lineage_integrity": _lineage_integrity_status(agent, agent.meta.get("evolution_lineage"), archive_events),
        "workflow": agent.meta.get("workflow"),
        "calendar_providers": describe_calendar_providers(),
        "domain_chart_providers": describe_domain_chart_providers(),
        "llm_backend": llm_backend_status(),
        "archive_events": len(archive_events),
        "archive_integrity": archive.integrity_report(),
        "latest_evolution": _latest_evolution_status(archive_events),
        "memory_profile": memory.profile(),
    }


def version_history(repo_path: Path) -> dict[str, Any]:
    """Return coordinator genome versions with lineage and archive provenance."""
    repo = ensure_repo(repo_path)
    versions = repo.list_versions("agents", "mingli_orchestrator")
    latest_version = repo.latest_version("agents", "mingli_orchestrator")
    archive = MingliEvolutionArchive(repo_path / "archives" / "mingli_evolution.json")
    archive_events = archive.load()
    event_by_hash = {
        event.get("archive_hash"): (index, event)
        for index, event in enumerate(archive_events)
        if isinstance(event, dict) and event.get("archive_hash")
    }
    rows = []
    for version in versions:
        agent = repo.load_agent("mingli_orchestrator", version=version)
        lineage = agent.meta.get("evolution_lineage")
        archive_hash = lineage.get("archive_hash") if isinstance(lineage, dict) else None
        archive_match = event_by_hash.get(archive_hash)
        archive_index = archive_match[0] if archive_match else None
        archive_event = archive_match[1] if archive_match else None
        fingerprint = genome_fingerprint(agent)
        rows.append(
            {
                "version": agent.version,
                "parent_version": agent.parent_version,
                "is_latest": agent.version == latest_version,
                "candidate_name": agent.meta.get("candidate_name"),
                "evolution_strategies": agent.meta.get("mingli_evolution", []),
                "workflow": agent.meta.get("workflow"),
                "genome_fingerprint": fingerprint,
                "lineage_present": isinstance(lineage, dict),
                "lineage_event": lineage.get("event") if isinstance(lineage, dict) else None,
                "lineage_archive_hash": archive_hash,
                "lineage_fingerprint_matches": (
                    lineage.get("genome_fingerprint") == fingerprint if isinstance(lineage, dict) else version == 1
                ),
                "baseline_genome_version": lineage.get("baseline_genome_version") if isinstance(lineage, dict) else None,
                "accepted_genome_version": lineage.get("accepted_genome_version") if isinstance(lineage, dict) else None,
                "selected_strategy": lineage.get("selected_strategy") if isinstance(lineage, dict) else None,
                "trigger_receipt_sha256": lineage.get("trigger_receipt", {}).get("sha256")
                if isinstance(lineage, dict) and isinstance(lineage.get("trigger_receipt"), dict)
                else None,
                "rollback_target_version": lineage.get("rollback_target_version") if isinstance(lineage, dict) else None,
                "rollback_reason": lineage.get("rollback_reason") if isinstance(lineage, dict) else None,
                "archive_event_found": archive_event is not None,
                "archive_event_index": archive_index,
                "archive_event_timestamp": archive_event.get("timestamp") if isinstance(archive_event, dict) else None,
                "archive_event_selected": archive_event.get("selected") if isinstance(archive_event, dict) else None,
                "archive_event_accepted": archive_event.get("accepted") if isinstance(archive_event, dict) else None,
            }
        )
    archive_integrity = archive.integrity_report()
    return {
        "repo": str(repo_path),
        "agent_name": "mingli_orchestrator",
        "latest_version": latest_version,
        "version_count": len(rows),
        "versions": rows,
        "archive_events": len(archive_events),
        "archive_integrity": archive_integrity,
        "history_integrity": _version_history_integrity(rows, latest_version, archive_integrity),
    }


def _version_history_integrity(
    rows: list[dict[str, Any]],
    latest_version: int,
    archive_integrity: dict[str, Any],
) -> dict[str, Any]:
    lineage_missing_versions = [
        row["version"]
        for row in rows
        if row.get("version") != 1 and not row.get("lineage_present")
    ]
    fingerprint_mismatch_versions = [
        row["version"]
        for row in rows
        if not row.get("lineage_fingerprint_matches")
    ]
    archive_missing_versions = [
        row["version"]
        for row in rows
        if row.get("lineage_present") and not row.get("archive_event_found")
    ]
    latest_flags = [row["version"] for row in rows if row.get("is_latest")]
    version_sequence = [row.get("version") for row in rows]
    expected_sequence = list(range(1, latest_version + 1))
    failures = []
    if version_sequence != expected_sequence:
        failures.append("coordinator versions are not contiguous from v1 to latest")
    if latest_flags != [latest_version]:
        failures.append("exactly one row must be marked as latest")
    if lineage_missing_versions:
        failures.append("non-initial versions are missing lineage")
    if fingerprint_mismatch_versions:
        failures.append("one or more version fingerprints do not match lineage")
    if archive_missing_versions:
        failures.append("one or more lineage archive hashes are not present in archive events")
    if archive_integrity.get("status") != "pass":
        failures.append("archive hash-chain integrity is not pass")
    return {
        "status": "pass" if not failures else "fail",
        "checked": True,
        "checked_versions": len(rows),
        "latest_version": latest_version,
        "lineage_missing_versions": lineage_missing_versions,
        "fingerprint_mismatch_versions": fingerprint_mismatch_versions,
        "archive_missing_versions": archive_missing_versions,
        "latest_marker_versions": latest_flags,
        "version_sequence_contiguous": version_sequence == expected_sequence,
        "archive_integrity_status": archive_integrity.get("status"),
        "failures": failures,
    }


def _latest_evolution_status(archive_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not archive_events:
        return None
    event = archive_events[-1]
    if not isinstance(event, dict):
        return None
    return {
        "event": event.get("event"),
        "timestamp": event.get("timestamp"),
        "accepted": event.get("accepted"),
        "selected": event.get("selected"),
        "pareto_front": event.get("pareto_front", []),
        "archive_hash": event.get("archive_hash"),
        "previous_archive_hash": event.get("previous_archive_hash"),
        "selection_decision": event.get("selection_decision"),
        "trigger_receipt": event.get("trigger_receipt"),
        "reproducibility_manifest": event.get("reproducibility_manifest"),
    }


def _lineage_integrity_status(
    agent: Any,
    genome_lineage: Any,
    archive_events: list[dict[str, Any]],
) -> dict[str, Any]:
    coordinator_version = int(getattr(agent, "version", 0))
    if not genome_lineage:
        return {
            "status": "not_applicable" if coordinator_version == 1 and not archive_events else "missing",
            "checked": False,
            "failures": [] if coordinator_version == 1 and not archive_events else ["current genome has no evolution_lineage"],
            "archive_hash_matches_latest": False,
            "genome_fingerprint_matches": coordinator_version == 1,
            "genome_version_matches": coordinator_version == 1,
            "selection_decision_matches": False,
            "trigger_receipt_matches": False,
            "reproducibility_manifest_matches": False,
        }
    if not isinstance(genome_lineage, dict):
        return {
            "status": "fail",
            "checked": True,
            "failures": ["genome_lineage is not an object"],
            "archive_hash_matches_latest": False,
            "genome_fingerprint_matches": False,
            "genome_version_matches": False,
            "selection_decision_matches": False,
            "trigger_receipt_matches": False,
            "reproducibility_manifest_matches": False,
        }
    latest_event = archive_events[-1] if archive_events and isinstance(archive_events[-1], dict) else {}
    archive_hash_matches = bool(latest_event) and genome_lineage.get("archive_hash") == latest_event.get("archive_hash")
    fingerprint_matches = genome_lineage.get("genome_fingerprint") == genome_fingerprint(agent)
    version_matches = genome_lineage.get("accepted_genome_version") == coordinator_version
    selection_matches = genome_lineage.get("selection_decision") == latest_event.get("selection_decision")
    trigger_matches = genome_lineage.get("trigger_receipt") == latest_event.get("trigger_receipt")
    manifest_matches = genome_lineage.get("reproducibility_manifest") == latest_event.get("reproducibility_manifest")
    failures = []
    if not latest_event:
        failures.append("archive has no latest evolution event")
    if not archive_hash_matches:
        failures.append("genome_lineage.archive_hash does not match latest archive event")
    if not fingerprint_matches:
        failures.append("genome_lineage.genome_fingerprint does not match current genome content")
    if not version_matches:
        failures.append("genome_lineage.accepted_genome_version does not match coordinator_version")
    if not selection_matches:
        failures.append("genome_lineage.selection_decision does not match latest archive event")
    if not trigger_matches:
        failures.append("genome_lineage.trigger_receipt does not match latest archive event")
    if not manifest_matches:
        failures.append("genome_lineage.reproducibility_manifest does not match latest archive event")
    return {
        "status": "pass" if not failures else "fail",
        "checked": True,
        "failures": failures,
        "archive_hash_matches_latest": archive_hash_matches,
        "genome_fingerprint_matches": fingerprint_matches,
        "genome_version_matches": version_matches,
        "selection_decision_matches": selection_matches,
        "trigger_receipt_matches": trigger_matches,
        "reproducibility_manifest_matches": manifest_matches,
    }


def capability_audit(
    repo_path: Path,
    *,
    expected_audit_receipt_sha256: str | None = None,
    classical_source_list_path: Path | None = None,
) -> dict[str, Any]:
    """Return implementation coverage and known professional-grade gaps."""
    ensure_repo(repo_path)
    response = build_capability_audit(repo_path, classical_source_list_path=classical_source_list_path)
    receipt_sha256 = response["audit_receipt"]["sha256"]
    matches_expected = None if expected_audit_receipt_sha256 is None else receipt_sha256 == expected_audit_receipt_sha256
    response["expected_audit_receipt_sha256"] = expected_audit_receipt_sha256
    response["audit_receipt_matches_expected"] = matches_expected
    response["audit_receipt_mismatch_reason"] = (
        "audit receipt sha256 does not match expected value" if matches_expected is False else ""
    )
    return response


def known_gap_handoff(
    repo_path: Path,
    *,
    expected_audit_receipt_sha256: str | None = None,
    classical_source_list_path: Path | None = None,
) -> dict[str, Any]:
    """Export the portable handoff bundle for open known gaps."""
    audit = capability_audit(
        repo_path,
        expected_audit_receipt_sha256=expected_audit_receipt_sha256,
        classical_source_list_path=classical_source_list_path,
    )
    bundle = audit.get("known_gap_handoff_bundle", {})
    audit_receipt_sha256 = (
        audit.get("audit_receipt", {}).get("sha256") if isinstance(audit.get("audit_receipt"), dict) else None
    )
    response = {
        "schema_version": "known-gap-handoff-export-v1",
        "repo": str(repo_path),
        "status": bundle.get("status", "incomplete") if isinstance(bundle, dict) else "incomplete",
        "known_gap_ids": [str(item.get("id")) for item in audit.get("known_gaps", []) if isinstance(item, dict)],
        "known_gap_handoff_bundle": bundle if isinstance(bundle, dict) else {},
        "audit_receipt_sha256": audit_receipt_sha256,
        "expected_audit_receipt_sha256": expected_audit_receipt_sha256,
        "audit_receipt_matches_expected": audit.get("audit_receipt_matches_expected"),
        "audit_receipt_mismatch_reason": audit.get("audit_receipt_mismatch_reason", ""),
    }
    receipt_material = {
        "schema_version": "known-gap-handoff-export-receipt-v1",
        "repo": response["repo"],
        "status": response["status"],
        "known_gap_ids": response["known_gap_ids"],
        "bundle_sha256": response["known_gap_handoff_bundle"].get("bundle_sha256")
        if isinstance(response["known_gap_handoff_bundle"], dict)
        else None,
        "audit_receipt_sha256": response["audit_receipt_sha256"],
        "expected_audit_receipt_sha256": response["expected_audit_receipt_sha256"],
        "audit_receipt_matches_expected": response["audit_receipt_matches_expected"],
    }
    response["handoff_export_receipt"] = {
        "schema_version": receipt_material["schema_version"],
        "sha256": hashlib.sha256(json.dumps(receipt_material, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest(),
        "material": receipt_material,
    }
    return response


def verify_known_gap_handoff_export(
    export_payload: dict[str, Any],
    *,
    expected_handoff_export_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify a known-gap handoff export JSON object and its receipt."""
    failures: list[str] = []
    if not isinstance(export_payload, dict):
        export_payload = {}
        failures.append("export payload must be a JSON object")
    bundle = export_payload.get("known_gap_handoff_bundle", {})
    receipt = export_payload.get("handoff_export_receipt", {})
    receipt_material = receipt.get("material", {}) if isinstance(receipt, dict) else {}
    bundle_material = {
        "bundle_version": bundle.get("bundle_version") if isinstance(bundle, dict) else None,
        "open_gap_ids": bundle.get("open_gap_ids", []) if isinstance(bundle, dict) else [],
        "missing_handoff_gap_ids": bundle.get("missing_handoff_gap_ids", []) if isinstance(bundle, dict) else [],
        "items": bundle.get("items", []) if isinstance(bundle, dict) else [],
    }
    expected_bundle_sha256 = hashlib.sha256(
        json.dumps(bundle_material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    observed_bundle_sha256 = bundle.get("bundle_sha256") if isinstance(bundle, dict) else None
    bundle_hash_valid = observed_bundle_sha256 == expected_bundle_sha256
    if not bundle_hash_valid:
        failures.append("known_gap_handoff_bundle.bundle_sha256 does not match bundle content")
    expected_receipt_material = {
        "schema_version": "known-gap-handoff-export-receipt-v1",
        "repo": export_payload.get("repo"),
        "status": export_payload.get("status"),
        "known_gap_ids": export_payload.get("known_gap_ids", []),
        "bundle_sha256": observed_bundle_sha256,
        "audit_receipt_sha256": export_payload.get("audit_receipt_sha256"),
        "expected_audit_receipt_sha256": export_payload.get("expected_audit_receipt_sha256"),
        "audit_receipt_matches_expected": export_payload.get("audit_receipt_matches_expected"),
    }
    receipt_material_valid = receipt_material == expected_receipt_material
    if not receipt_material_valid:
        failures.append("handoff_export_receipt.material does not match export payload")
    expected_receipt_sha256 = hashlib.sha256(
        json.dumps(expected_receipt_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    observed_receipt_sha256 = receipt.get("sha256") if isinstance(receipt, dict) else None
    receipt_hash_valid = observed_receipt_sha256 == expected_receipt_sha256
    if not receipt_hash_valid:
        failures.append("handoff_export_receipt.sha256 does not match receipt material")
    receipt_schema_valid = (
        isinstance(receipt, dict)
        and receipt.get("schema_version") == "known-gap-handoff-export-receipt-v1"
        and receipt_material.get("schema_version") == "known-gap-handoff-export-receipt-v1"
    )
    if not receipt_schema_valid:
        failures.append("handoff_export_receipt schema_version is invalid")
    known_gap_ids = export_payload.get("known_gap_ids", [])
    open_gap_ids = bundle.get("open_gap_ids", []) if isinstance(bundle, dict) else []
    known_gap_ids_match_bundle = known_gap_ids == open_gap_ids
    if not known_gap_ids_match_bundle:
        failures.append("known_gap_ids do not match bundle open_gap_ids")
    expected_receipt_matches = (
        None
        if expected_handoff_export_receipt_sha256 is None
        else observed_receipt_sha256 == expected_handoff_export_receipt_sha256
    )
    if expected_receipt_matches is False:
        failures.append("handoff export receipt sha256 does not match expected value")
    return {
        "schema_version": "known-gap-handoff-export-verification-v1",
        "valid": not failures,
        "failures": failures,
        "handoff_export_receipt_sha256": observed_receipt_sha256,
        "expected_handoff_export_receipt_sha256": expected_handoff_export_receipt_sha256,
        "handoff_export_receipt_matches_expected": expected_receipt_matches,
        "expected_handoff_export_receipt_sha256_material": expected_receipt_sha256,
        "bundle_sha256": observed_bundle_sha256,
        "expected_bundle_sha256": expected_bundle_sha256,
        "bundle_hash_valid": bundle_hash_valid,
        "receipt_material_valid": receipt_material_valid,
        "receipt_hash_valid": receipt_hash_valid,
        "receipt_schema_valid": receipt_schema_valid,
        "known_gap_ids_match_bundle": known_gap_ids_match_bundle,
    }


def known_gap_handoff_implementation_checklist(
    export_payload: dict[str, Any],
    *,
    expected_handoff_export_receipt_sha256: str | None = None,
    expected_checklist_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Build an implementation checklist from a verified known-gap handoff export."""
    verification = verify_known_gap_handoff_export(
        export_payload,
        expected_handoff_export_receipt_sha256=expected_handoff_export_receipt_sha256,
    )
    bundle = export_payload.get("known_gap_handoff_bundle", {}) if isinstance(export_payload, dict) else {}
    bundle_items = bundle.get("items", []) if isinstance(bundle, dict) else []
    if not isinstance(bundle_items, list):
        bundle_items = []
    items = []
    for item in bundle_items:
        if not isinstance(item, dict):
            continue
        gap_id = str(item.get("gap_id", ""))
        env_vars = [str(value) for value in item.get("required_env_vars", [])]
        provenance_vars = [str(value) for value in item.get("required_provenance_env_vars", [])]
        candidate_projects = [
            {
                "name": str(candidate.get("name", "")),
                "url": str(candidate.get("url", "")),
                "fit": str(candidate.get("fit", "")),
                "audit_note": str(candidate.get("audit_note", "")),
            }
            for candidate in item.get("external_candidate_projects", [])
            if isinstance(candidate, dict)
        ]
        verification_commands = [str(command) for command in item.get("verification_commands", [])]
        production_gate_ids = [str(gate) for gate in item.get("production_gate_ids", [])]
        checklist = [
            f"Confirm owner domain {item.get('owner_domain')} and blocking scope {item.get('blocking_scope')}.",
            "Configure required provider/source/dataset environment variables."
            if env_vars or provenance_vars
            else "Confirm this gap does not require provider environment variables.",
            "Review candidate projects and licensing before adapter implementation."
            if candidate_projects
            else "Select or document the external source/provider/dataset used to close this gap.",
            "Run every verification command after implementation.",
            "Confirm all listed production gates pass before closing the gap.",
        ]
        items.append(
            {
                "gap_id": gap_id,
                "owner_domain": str(item.get("owner_domain", "")),
                "blocking_scope": str(item.get("blocking_scope", "")),
                "handoff_ready": item.get("handoff_ready") is True,
                "ready_to_implement": verification.get("valid") is True and item.get("handoff_ready") is True,
                "required_env_vars": env_vars,
                "required_provenance_env_vars": provenance_vars,
                "external_candidate_projects": candidate_projects,
                "verification_commands": verification_commands,
                "production_gate_ids": production_gate_ids,
                "blocked_capabilities": [str(value) for value in item.get("blocked_capabilities", [])],
                "closure_condition": str(item.get("closure_condition", "")),
                "checklist": checklist,
            }
        )
    receipt_material = {
        "schema_version": "known-gap-handoff-checklist-receipt-v1",
        "handoff_export_receipt_sha256": verification.get("handoff_export_receipt_sha256"),
        "verification_valid": verification.get("valid"),
        "gap_ids": [item["gap_id"] for item in items],
        "item_count": len(items),
        "ready_item_count": sum(1 for item in items if item["ready_to_implement"]),
    }
    checklist_receipt_sha256 = hashlib.sha256(
        json.dumps(receipt_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    checklist_receipt_matches_expected = (
        None
        if expected_checklist_receipt_sha256 is None
        else checklist_receipt_sha256 == expected_checklist_receipt_sha256
    )
    return {
        "schema_version": "known-gap-handoff-checklist-v1",
        "status": "ready" if verification.get("valid") is True and all(item["ready_to_implement"] for item in items) else "blocked",
        "verification": verification,
        "item_count": len(items),
        "ready_item_count": sum(1 for item in items if item["ready_to_implement"]),
        "items": items,
        "expected_checklist_receipt_sha256": expected_checklist_receipt_sha256,
        "checklist_receipt_matches_expected": checklist_receipt_matches_expected,
        "checklist_receipt_mismatch_reason": ""
        if checklist_receipt_matches_expected is not False
        else "checklist_receipt.sha256 does not match expected_checklist_receipt_sha256",
        "checklist_receipt": {
            "schema_version": receipt_material["schema_version"],
            "sha256": checklist_receipt_sha256,
            "material": receipt_material,
        },
    }


def provider_checks(repo_path: Path, *, live: bool = False, profile: str = "development") -> dict[str, Any]:
    """Return optional professional provider readiness checks."""
    ensure_repo(repo_path)
    return provider_health_checks(repo_path, live=live, profile=profile)


def provider_examples(repo_path: Path) -> dict[str, Any]:
    """Run bundled JSON-CLI provider examples as protocol fixtures."""
    ensure_repo(repo_path)
    return bundled_provider_example_smoke(repo_path)


def provider_onboarding(repo_path: Path) -> dict[str, Any]:
    """Return a machine-readable onboarding plan for real professional providers."""
    ensure_repo(repo_path)
    protocols = provider_protocol_document().get("domains", {})
    checks = provider_health_checks(repo_path, live=False, profile="production")
    ledger = _provider_certification_ledger_status(repo_path)
    examples = bundled_provider_example_smoke(repo_path)
    targets = {
        target.get("provider_domain"): target
        for target in checks.get("integration_plan", {}).get("targets", [])
        if isinstance(target, dict) and target.get("provider_domain")
    }
    domains = {}
    for domain in sorted(JSON_CLI_CHECK_BY_DOMAIN):
        protocol = protocols.get(domain, {})
        target = targets.get(domain, {})
        ledger_domain = ledger.get("domains", {}).get(domain, {}) if isinstance(ledger.get("domains"), dict) else {}
        example_domain = examples.get("domains", {}).get(domain, {}) if isinstance(examples.get("domains"), dict) else {}
        missing = []
        if target.get("production_credential_passed") is not True:
            missing.append("production_provider_provenance")
        if target.get("live_smoke_passed") is not True:
            missing.append("live_json_cli_smoke")
        if ledger_domain.get("certified") is not True:
            missing.append("certified_provider_ledger_record")
        if ledger_domain.get("protocol_matches_current") is not True:
            missing.append("current_protocol_receipt")
        if ledger_domain.get("request_receipt_valid") is not True:
            missing.append("provider_request_receipt")
        if ledger_domain.get("reference_contract_covered") is not True:
            missing.append("reference_contract_coverage")
        if ledger_domain.get("provider_command_fingerprint_present") is not True:
            missing.append("provider_command_fingerprint")
        domains[domain] = {
            "domain": domain,
            "status": "ready" if not missing else "blocked",
            "missing_evidence": missing,
            "env_var": protocol.get("env_var"),
            "provenance_env_var": protocol.get("provenance_env_var"),
            "protocol_version": protocol.get("protocol_version"),
            "protocol_hash": protocol.get("protocol_hash"),
            "required_provenance_fields": protocol.get("required_provenance_fields", []),
            "certification_command": str(protocol.get("certification_command_template", "")).replace(
                "<repo>", str(repo_path)
            ),
            "drift_command": str(protocol.get("drift_command_template", "")).replace("<repo>", str(repo_path)),
            "deployment_checklist": target.get("deployment_checklist", []),
            "next_actions": target.get("next_actions", []),
            "ledger_status": ledger_domain,
            "bundled_example_smoke": {
                "live_passed": example_domain.get("live_passed"),
                "contract_valid": example_domain.get("contract_valid"),
                "protocol_identity_matches": example_domain.get("protocol_identity_matches"),
                "provider_request_receipt_valid": example_domain.get("provider_request_receipt_valid"),
                "receipt_sha256": example_domain.get("provider_request_receipt_sha256"),
                "production_certification_allowed": False,
            },
        }
    missing_evidence_by_domain = {
        domain: list(item.get("missing_evidence", []))
        for domain, item in domains.items()
    }
    missing_evidence_counts: dict[str, int] = {}
    for missing_items in missing_evidence_by_domain.values():
        for evidence_id in missing_items:
            missing_evidence_counts[evidence_id] = missing_evidence_counts.get(evidence_id, 0) + 1
    material = {
        "schema_version": 1,
        "repo": str(repo_path),
        "status": "ready" if all(item["status"] == "ready" for item in domains.values()) else "actions_required",
        "domain_count": len(domains),
        "ready_domain_count": sum(1 for item in domains.values() if item["status"] == "ready"),
        "missing_evidence_by_domain": missing_evidence_by_domain,
        "missing_evidence_counts": dict(sorted(missing_evidence_counts.items())),
        "provider_ledger_exists": ledger.get("exists"),
        "provider_ledger_latest_record_hash": ledger.get("latest_record_hash"),
        "example_provider_receipt_sha256": examples.get("example_provider_receipt", {}).get("sha256"),
        "domains": domains,
        "policy": "Real production providers must be certified and recorded; bundled examples only verify protocol wiring.",
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    receipt = {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }
    return {
        "repo": str(repo_path),
        "status": material["status"],
        "domains": domains,
        "provider_ledger": ledger,
        "example_provider_receipt": examples.get("example_provider_receipt", {}),
        "provider_onboarding_receipt": receipt,
    }


def provider_certification(
    repo_path: Path,
    domain: str,
    *,
    live: bool = True,
    command: str | None = None,
    provenance: str | None = None,
    expected_receipt_sha256: str | None = None,
    record: bool = False,
) -> dict[str, Any]:
    """Return a focused JSON-CLI provider certification report."""
    ensure_repo(repo_path)
    result = certify_json_cli_provider(
        domain,
        repo_path,
        live=live,
        command=command,
        provenance=provenance,
        expected_receipt_sha256=expected_receipt_sha256,
    )
    result["ledger_record_requested"] = bool(record)
    result["ledger_recorded"] = False
    result["ledger_record_path"] = str(_provider_certification_ledger_path(repo_path))
    result["ledger_record_index"] = None
    result["ledger_record_hash"] = None
    result["ledger_record_blocker"] = ""
    if record:
        if result.get("certified") is not True:
            result["ledger_record_blocker"] = "only certified provider results can be recorded"
        else:
            ledger_result = _append_provider_certification_record(repo_path, result)
            result.update(ledger_result)
    result["resolution_guidance"] = _provider_certification_resolution_guidance(repo_path, result)
    return result


def _provider_certification_resolution_guidance(repo_path: Path, certification: dict[str, Any]) -> dict[str, Any]:
    """Return stable remediation guidance for a provider certification attempt."""
    domain = str(certification.get("domain") or "")
    recertification_command = _provider_certification_command(repo_path, domain) if domain in JSON_CLI_CHECK_BY_DOMAIN else ""
    drift_command = (
        f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-drift --domain {domain}"
        if domain in JSON_CLI_CHECK_BY_DOMAIN
        else f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-drift"
    )
    return {
        "certified": certification.get("certified") is True,
        "ledger_record_requested": certification.get("ledger_record_requested") is True,
        "ledger_recorded": certification.get("ledger_recorded") is True,
        "ledger_record_blocker": str(certification.get("ledger_record_blocker") or ""),
        "domain": domain,
        "env_var": certification.get("env_var"),
        "provenance_env_var": certification.get("provenance_env_var"),
        "command_is_bundled_example": certification.get("command_is_bundled_example") is True,
        "blockers": list(certification.get("blockers", [])),
        "next_actions": list(certification.get("next_actions", [])),
        "recertification_command": recertification_command,
        "drift_command": drift_command,
        "provider_ledger_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger",
        "provider_onboarding_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-onboarding",
        "production_readiness_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --live",
        "record_policy": (
            "Only certified, reviewed, live, non-bundled provider results may be recorded in the provider ledger."
        ),
    }


def _provider_certification_ledger_path(repo_path: Path) -> Path:
    return repo_path / "providers" / "provider_certification_ledger.json"


def _append_provider_certification_record(repo_path: Path, certification: dict[str, Any]) -> dict[str, Any]:
    ledger_path = _provider_certification_ledger_path(repo_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if not isinstance(ledger, dict):
            raise ValueError("provider certification ledger must be a JSON object")
    else:
        ledger = {"schema_version": 1, "records": []}
    records = ledger.setdefault("records", [])
    if not isinstance(records, list):
        raise ValueError("provider certification ledger records must be a list")
    previous_hash = records[-1].get("record_hash") if records and isinstance(records[-1], dict) else None
    receipt = certification.get("certification_receipt", {})
    provenance = certification.get("provider_provenance_audit") or {}
    record = {
        "schema_version": 1,
        "index": len(records),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "domain": certification.get("domain"),
        "provider_check": certification.get("provider_check"),
        "status": certification.get("status"),
        "certified": certification.get("certified"),
        "live_requested": certification.get("live_requested"),
        "receipt_sha256": receipt.get("sha256"),
        "certification_receipt": receipt,
        "contract": certification.get("contract"),
        "protocol_version": certification.get("protocol_version"),
        "protocol_hash": certification.get("protocol_hash"),
        "reference_contract_coverage": certification.get("reference_contract_coverage", {}),
        "provider_command_fingerprint": certification.get("provider_command_fingerprint", {}),
        "provenance_fields": provenance.get("fields", {}) if isinstance(provenance, dict) else {},
        "command_override_used": certification.get("command_override_used"),
        "provenance_override_used": certification.get("provenance_override_used"),
        "previous_record_hash": previous_hash,
    }
    record_material = {key: value for key, value in record.items() if key != "record_hash"}
    encoded = json.dumps(record_material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    record["record_hash"] = hashlib.sha256(encoded).hexdigest()
    records.append(record)
    ledger["latest_record_hash"] = record["record_hash"]
    ledger["latest_record_index"] = record["index"]
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ledger_recorded": True,
        "ledger_record_path": str(ledger_path),
        "ledger_record_index": record["index"],
        "ledger_record_hash": record["record_hash"],
        "ledger_record_blocker": "",
    }


def provider_certification_ledger(repo_path: Path) -> dict[str, Any]:
    """Return provider certification ledger status and domain coverage."""
    ensure_repo(repo_path)
    ledger = _provider_certification_ledger_status(repo_path)
    return {
        "repo": str(repo_path),
        "ledger": ledger,
        "configuration_guidance": _provider_ledger_configuration_guidance(repo_path, ledger),
    }


def _provider_ledger_configuration_guidance(repo_path: Path, ledger: dict[str, Any]) -> dict[str, Any]:
    """Return stable operator guidance for certifying real production providers."""
    domains = sorted(JSON_CLI_CHECK_BY_DOMAIN)
    commands = [_provider_certification_command(repo_path, domain) for domain in domains]
    drift_commands = [f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-drift --domain {domain}" for domain in domains]
    return {
        "configured": ledger.get("coverage_status") == "complete"
        and ledger.get("integrity_status") == "pass"
        and ledger.get("protocol_status") == "current"
        and ledger.get("request_receipt_status") == "current"
        and ledger.get("reference_contract_status") == "current"
        and ledger.get("command_fingerprint_status") == "current",
        "ledger_path": ledger.get("path"),
        "required_domains": domains,
        "missing_domains": list(ledger.get("missing_domains", [])),
        "domain_env_vars": {domain: f"SEMAS_{domain.upper()}_CLI" for domain in domains},
        "domain_provenance_env_vars": {domain: f"SEMAS_{domain.upper()}_PROVIDER_PROVENANCE" for domain in domains},
        "certification_commands": commands,
        "drift_commands": drift_commands,
        "provider_onboarding_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-onboarding",
        "provider_ledger_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger",
        "production_readiness_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --live",
        "http_query": "GET /provider-ledger",
        "policy": (
            "Record only reviewed, live, non-bundled JSON-CLI providers. "
            "Bundled provider examples verify protocol wiring but must not be recorded as production certifications."
        ),
    }


def provider_certification_drift(repo_path: Path, *, live: bool = True, domain: str | None = None) -> dict[str, Any]:
    """Compare current provider certifications with the recorded ledger receipts."""
    ensure_repo(repo_path)
    ledger = _provider_certification_ledger_status(repo_path)
    drift = _provider_certification_drift_status(repo_path, ledger, live=live, domain=domain)
    return {
        "repo": str(repo_path),
        "domain": domain,
        "ledger": ledger,
        "drift": drift,
        "resolution_guidance": _provider_drift_resolution_guidance(repo_path, drift, domain=domain),
    }


def _provider_drift_resolution_guidance(
    repo_path: Path,
    drift: dict[str, Any],
    *,
    domain: str | None = None,
) -> dict[str, Any]:
    """Return stable remediation guidance for provider certification drift."""
    checked_domains = list(drift.get("checked_domains", []))
    if not checked_domains:
        checked_domains = [domain] if domain else sorted(JSON_CLI_CHECK_BY_DOMAIN)
    checked_domains = [str(item) for item in checked_domains if str(item) in JSON_CLI_CHECK_BY_DOMAIN]
    recertification_commands = [_provider_certification_command(repo_path, item) for item in checked_domains]
    drift_commands = [
        f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-drift --domain {item}"
        for item in checked_domains
    ]
    return {
        "passed": drift.get("passed") is True,
        "status": drift.get("status"),
        "checked_domains": checked_domains,
        "recertification_commands": recertification_commands,
        "drift_commands": drift_commands,
        "provider_ledger_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger",
        "provider_onboarding_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-onboarding",
        "production_readiness_command": f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --live",
        "http_query": (
            f"GET /provider-drift?domain={domain}"
            if domain
            else "GET /provider-drift"
        ),
        "blocking_failures": list(drift.get("failures", [])),
        "policy": (
            "Resolve drift by re-certifying reviewed live providers and recording certified receipts. "
            "Do not use bundled protocol examples as production provider certifications."
        ),
    }


def provider_protocols(repo_path: Path, domain: str | None = None) -> dict[str, Any]:
    """Return external JSON-CLI provider protocol contracts."""
    ensure_repo(repo_path)
    document = provider_protocol_document()
    if domain is not None:
        domains = document.get("domains", {})
        if domain not in domains:
            raise ValueError("provider protocol domain must be ziwei, qimen, astrology, or xuanze")
        document = {**document, "domains": {domain: domains[domain]}}
    receipt = provider_protocol_receipt(document, repo=str(repo_path), domain=domain)
    return {
        "repo": str(repo_path),
        "domain": domain,
        "provider_protocols": document,
        "provider_protocols_receipt": receipt,
    }


def outcome_dataset_manifest_status(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Audit an outcome dataset manifest and expose its evolution-gate status."""
    ensure_repo(repo_path)
    audit = outcome_dataset_audit(manifest_path)
    receipt = _outcome_dataset_receipt(audit)
    failures = list(audit.get("failures", []))
    configured = manifest_path is not None
    gate = {
        "passed": audit.get("valid") is True if configured else True,
        "status": audit.get("status"),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "reason": (
            "Provided outcome manifest passed governance audit; only non-predictive quality labels may drive validation."
            if audit.get("valid") is True
            else (
                "No outcome manifest provided; built-in non-predictive validation remains active."
                if not configured
                else "Provided outcome manifest failed governance audit and cannot be used for SEMAS evolution gates."
            )
        ),
        "blocking_failures": failures,
        "predictive_optimization_enabled": audit.get("predictive_optimization_enabled", False),
    }
    return {
        "repo": str(repo_path),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "audit": audit,
        "outcome_dataset_receipt": receipt,
        "evolution_gate": gate,
        "configuration_guidance": _outcome_dataset_configuration_guidance(repo_path, manifest_path),
    }


def industry_event_manifest_status(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Audit a public famous-case industry-event manifest."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_industry_event_manifest_path()
    audit = audit_industry_event_manifest(selected_path)
    receipt = industry_event_manifest_receipt(audit)
    configured = manifest_path is not None
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": configured,
        "audit": audit,
        "industry_event_manifest_receipt": receipt,
        "production_gate": {
            "id": "industry_event_source_provider_reviewed_manifest",
            "passed": audit.get("production_evidence") is True,
            "reason": (
                "Industry-event manifest is externally reviewed and marked as production evidence."
                if audit.get("production_evidence") is True
                else "Industry-event manifest is only a contract/audit input until external review approves production evidence."
            ),
            "blocking_failures": list(audit.get("failures", [])),
            "externally_reviewed": audit.get("externally_reviewed"),
            "production_evidence": audit.get("production_evidence"),
        },
        "configuration_guidance": _industry_event_manifest_configuration_guidance(repo_path, manifest_path),
    }


def industry_event_validation_labels(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Convert an industry-event manifest into annual validation labels."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_industry_event_manifest_path()
    label_table = build_industry_event_validation_label_table(selected_path)
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": manifest_path is not None,
        "validation_label_table": label_table,
        "configuration_guidance": {
            "example_manifest_path": str(default_industry_event_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-labels --manifest {selected_path}"
            ),
            "policy": (
                "Validation labels adapt factual event manifests for future timing-rule scoring. "
                "They do not score symbolic rules by themselves."
            ),
        },
    }


def industry_event_symbolic_scoring_readiness(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Check which industry-event labels can enter symbolic annual scoring."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_industry_event_manifest_path()
    readiness = build_industry_event_symbolic_scoring_readiness(
        selected_path,
        birth_cases=famous_case_records(),
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": manifest_path is not None,
        "symbolic_scoring_readiness": readiness,
        "configuration_guidance": {
            "example_manifest_path": str(default_industry_event_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-scoring-readiness --manifest {selected_path}"
            ),
            "policy": (
                "This checks whether validation labels have matching birth profiles before symbolic scoring. "
                "It does not compute prediction accuracy."
            ),
        },
    }


def industry_event_symbolic_annual_score(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Score ready industry-event labels against symbolic annual rows."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_industry_event_manifest_path()
    score = build_industry_event_symbolic_annual_score(
        selected_path,
        birth_cases=famous_case_records(),
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": manifest_path is not None,
        "symbolic_annual_score": score,
        "configuration_guidance": {
            "example_manifest_path": str(default_industry_event_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-symbolic-score --manifest {selected_path}"
            ),
            "policy": (
                "This scores only labels that have matching birth profiles and remains a diagnostic, "
                "not a predictive-validity claim."
            ),
        },
    }


def industry_event_evidence_workplan(
    repo_path: Path,
    manifest_path: Path | None = None,
    candidate_path: Path | None = None,
    query_plan_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    """Convert score-derived evidence tasks into candidate collection work."""
    ensure_repo(repo_path)
    selected_manifest = manifest_path or default_industry_event_manifest_path()
    selected_candidates = candidate_path or default_industry_event_candidate_cases_path()
    selected_query_plan = query_plan_path or default_industry_event_query_plan_path()
    selected_cache_dir = cache_dir or repo_path / "industry_event_cache"
    score = build_industry_event_symbolic_annual_score(
        selected_manifest,
        birth_cases=famous_case_records(),
    )
    workplan = build_industry_event_evidence_workplan_from_symbolic_score(
        score,
        candidate_path=selected_candidates,
        query_plan_path=selected_query_plan,
        cache_dir=selected_cache_dir,
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_manifest),
        "candidate_path": str(selected_candidates),
        "query_plan_path": str(selected_query_plan),
        "cache_dir": str(selected_cache_dir),
        "configured": manifest_path is not None or candidate_path is not None or query_plan_path is not None or cache_dir is not None,
        "symbolic_annual_score": score,
        "evidence_workplan": workplan,
        "configuration_guidance": {
            "example_manifest_path": str(default_industry_event_manifest_path()),
            "example_candidate_path": str(default_industry_event_candidate_cases_path()),
            "example_query_plan_path": str(default_industry_event_query_plan_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-evidence-workplan --manifest {selected_manifest} "
                f"--candidates {selected_candidates} --query-plan {selected_query_plan} --cache-dir {selected_cache_dir}"
            ),
            "policy": (
                "This converts score-derived tasks into reviewable dry-run collection commands. "
                "It does not fetch live sources."
            ),
        },
    }


def birth_profile_review_status(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Audit a reviewed-birth-profile collection worklist."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    audit = audit_birth_profile_review_manifest(selected_path)
    receipt = birth_profile_review_manifest_receipt(audit)
    configured = manifest_path is not None
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": configured,
        "audit": audit,
        "birth_profile_review_manifest_receipt": receipt,
        "production_gate": {
            "id": "birth_profile_review_manifest_ready_for_import",
            "passed": audit.get("ready_for_import") is True and audit.get("production_evidence") is True,
            "reason": (
                "Birth-profile review manifest is approved for import."
                if audit.get("ready_for_import") is True and audit.get("production_evidence") is True
                else "Birth-profile review manifest is a collection worklist until external review approves import."
            ),
            "blocking_failures": list(audit.get("failures", [])),
            "externally_reviewed": audit.get("externally_reviewed"),
            "production_evidence": audit.get("production_evidence"),
            "ready_for_import": audit.get("ready_for_import"),
        },
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-review --manifest {selected_path}"
            ),
            "http_query": f"GET /birth-profile-review?manifest={selected_path}",
            "policy": (
                "This audits a birth-profile collection worklist. It does not certify birth data or import "
                "profiles into famous-case fixtures."
            ),
        },
    }


def birth_profile_source_review_workplan(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Build a non-mutating source-review workplan for celebrity birth-profile requests."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    workplan = build_birth_profile_source_review_workplan(selected_path)
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": manifest_path is not None,
        "source_review_workplan": workplan,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-source-review-workplan --manifest {selected_path}"
            ),
            "http_query": f"GET /birth-profile-source-review-workplan?manifest={selected_path}",
            "policy": (
                "This creates a human source-review workplan only. It does not fetch live sources, certify "
                "birth data, write reviewed manifests, or unlock symbolic scoring."
            ),
        },
    }


def birth_profile_source_lookup_plan(
    repo_path: Path,
    manifest_path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build a dry-run source lookup plan for celebrity birth-profile review tasks."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    selected_cache_dir = cache_dir or repo_path / "birth_profile_source_cache"
    plan = build_birth_profile_source_lookup_plan(
        selected_path,
        cache_dir=selected_cache_dir,
        domain=domain,
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "cache_dir": str(selected_cache_dir),
        "configured": manifest_path is not None or cache_dir is not None or domain is not None,
        "source_lookup_plan": plan,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-source-lookup-plan --manifest {selected_path} --cache-dir {selected_cache_dir}"
            ),
            "http_query": f"GET /birth-profile-source-lookup-plan?manifest={selected_path}&cache_dir={selected_cache_dir}",
            "policy": (
                "This creates a dry-run lookup plan only. It does not fetch live sources, write caches, certify "
                "birth data, write reviewed manifests, or unlock symbolic scoring."
            ),
        },
    }


def birth_profile_source_cache_audit(
    repo_path: Path,
    manifest_path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Audit manually prepared source lookup cache files without importing birth profiles."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    selected_cache_dir = cache_dir or repo_path / "birth_profile_source_cache"
    audit = build_birth_profile_source_cache_audit(
        selected_path,
        cache_dir=selected_cache_dir,
        domain=domain,
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "cache_dir": str(selected_cache_dir),
        "configured": manifest_path is not None or cache_dir is not None or domain is not None,
        "source_cache_audit": audit,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-source-cache-audit --manifest {selected_path} --cache-dir {selected_cache_dir}"
            ),
            "http_query": f"GET /birth-profile-source-cache-audit?manifest={selected_path}&cache_dir={selected_cache_dir}",
            "policy": (
                "This audits manually prepared cache files only. It does not fetch live sources, write caches, "
                "certify birth data, write reviewed manifests, import profiles, or unlock symbolic scoring."
            ),
        },
    }


def birth_profile_source_cache_template_preview(
    repo_path: Path,
    manifest_path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build non-mutating source-cache JSON templates for celebrity birth-profile review tasks."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    selected_cache_dir = cache_dir or repo_path / "birth_profile_source_cache"
    preview = build_birth_profile_source_cache_template_preview(
        selected_path,
        cache_dir=selected_cache_dir,
        domain=domain,
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "cache_dir": str(selected_cache_dir),
        "configured": manifest_path is not None or cache_dir is not None or domain is not None,
        "source_cache_template_preview": preview,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-source-cache-template-preview --manifest {selected_path} --cache-dir {selected_cache_dir}"
            ),
            "http_query": (
                f"GET /birth-profile-source-cache-template-preview?manifest={selected_path}"
                f"&cache_dir={selected_cache_dir}"
            ),
            "policy": (
                "This renders cache JSON templates only. It does not fetch live sources, write caches, certify "
                "birth data, write reviewed manifests, import profiles, or unlock symbolic scoring."
            ),
        },
    }


def birth_profile_reviewed_manifest_draft_preview(
    repo_path: Path,
    manifest_path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build a non-mutating reviewed-manifest draft preview from accepted source cache evidence."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    selected_cache_dir = cache_dir or repo_path / "birth_profile_source_cache"
    preview = build_birth_profile_reviewed_manifest_draft_preview(
        selected_path,
        cache_dir=selected_cache_dir,
        domain=domain,
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "cache_dir": str(selected_cache_dir),
        "configured": manifest_path is not None or cache_dir is not None or domain is not None,
        "reviewed_manifest_draft_preview": preview,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-reviewed-manifest-draft-preview --manifest {selected_path} --cache-dir {selected_cache_dir}"
            ),
            "http_query": (
                f"GET /birth-profile-reviewed-manifest-draft-preview?manifest={selected_path}"
                f"&cache_dir={selected_cache_dir}"
            ),
            "policy": (
                "This builds a non-mutating reviewed-manifest draft preview only. It does not write manifests, "
                "import profiles, certify birth data, or unlock symbolic scoring."
            ),
        },
    }


def birth_profile_reviewed_manifest_file_preview(
    repo_path: Path,
    manifest_path: Path | None = None,
    *,
    cache_dir: Path | None = None,
    domain: str | None = None,
    target_path: Path | None = None,
) -> dict[str, Any]:
    """Build a non-mutating file-write preview for an approved reviewed-manifest draft."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    selected_cache_dir = cache_dir or repo_path / "birth_profile_source_cache"
    selected_target = target_path or repo_path / "birth_profile_review_manifest_reviewed.json"
    preview = build_birth_profile_reviewed_manifest_file_preview(
        selected_path,
        cache_dir=selected_cache_dir,
        domain=domain,
        target_path=selected_target,
    )
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "cache_dir": str(selected_cache_dir),
        "target_path": str(selected_target),
        "configured": (
            manifest_path is not None or cache_dir is not None or domain is not None or target_path is not None
        ),
        "reviewed_manifest_file_preview": preview,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-reviewed-manifest-file-preview --manifest {selected_path} "
                f"--cache-dir {selected_cache_dir} --target {selected_target}"
            ),
            "http_query": (
                f"GET /birth-profile-reviewed-manifest-file-preview?manifest={selected_path}"
                f"&cache_dir={selected_cache_dir}&target={selected_target}"
            ),
            "policy": (
                "This builds a non-mutating file-write preview only. It does not write manifests, import profiles, "
                "certify birth data, or unlock symbolic scoring."
            ),
        },
    }


def birth_profile_import_preview(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Build a non-mutating preview for reviewed birth-profile fixture import."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    preview = build_birth_profile_import_preview(selected_path)
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": manifest_path is not None,
        "import_preview": preview,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-import-preview --manifest {selected_path}"
            ),
            "http_query": f"GET /birth-profile-import-preview?manifest={selected_path}",
            "policy": (
                "This builds a non-mutating import preview. It does not write famous-case fixtures and remains "
                "blocked until reviewed birth-profile evidence is complete."
            ),
        },
    }


def birth_profile_fixture_patch_preview(repo_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Build a non-mutating fixture patch preview for reviewed birth-profile imports."""
    ensure_repo(repo_path)
    selected_path = manifest_path or default_birth_profile_review_manifest_path()
    preview = build_birth_profile_fixture_patch_preview(selected_path)
    return {
        "repo": str(repo_path),
        "manifest_path": str(selected_path),
        "configured": manifest_path is not None,
        "fixture_patch_preview": preview,
        "configuration_guidance": {
            "example_manifest_path": str(default_birth_profile_review_manifest_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"birth-profile-fixture-patch-preview --manifest {selected_path}"
            ),
            "http_query": f"GET /birth-profile-fixture-patch-preview?manifest={selected_path}",
            "policy": (
                "This renders a non-mutating patch-review payload. It does not write famous-case fixtures; "
                "actual fixture edits require a separate reviewed patch."
            ),
        },
    }


def industry_event_query_plan_status(repo_path: Path, query_plan_path: Path | None = None) -> dict[str, Any]:
    """Audit a public industry-event source query plan."""
    ensure_repo(repo_path)
    selected_path = query_plan_path or default_industry_event_query_plan_path()
    audit = audit_industry_event_query_plan(selected_path)
    receipt = industry_event_query_plan_receipt(audit)
    configured = query_plan_path is not None
    return {
        "repo": str(repo_path),
        "query_plan_path": str(selected_path),
        "configured": configured,
        "audit": audit,
        "industry_event_query_plan_receipt": receipt,
        "collection_gate": {
            "id": "industry_event_source_query_plan_reviewed",
            "passed": audit.get("collection_ready") is True,
            "reason": (
                "Industry-event query plan is externally reviewed and marked ready for live collection."
                if audit.get("collection_ready") is True
                else "Industry-event query plan is only a contract/audit input until external review approves live collection."
            ),
            "blocking_failures": list(audit.get("failures", [])),
            "externally_reviewed": audit.get("externally_reviewed"),
            "live_collection_allowed": audit.get("live_collection_allowed"),
            "collection_ready": audit.get("collection_ready"),
        },
        "configuration_guidance": _industry_event_query_plan_configuration_guidance(repo_path, query_plan_path),
    }


def industry_event_candidate_cases_status(repo_path: Path, candidate_path: Path | None = None) -> dict[str, Any]:
    """Audit a candidate celebrity pool for future industry-event validation."""
    ensure_repo(repo_path)
    selected_path = candidate_path or default_industry_event_candidate_cases_path()
    audit = audit_industry_event_candidate_cases(selected_path)
    receipt = industry_event_candidate_cases_receipt(audit)
    configured = candidate_path is not None
    return {
        "repo": str(repo_path),
        "candidate_path": str(selected_path),
        "configured": configured,
        "audit": audit,
        "industry_event_candidate_cases_receipt": receipt,
        "candidate_pool_gate": {
            "id": "industry_event_candidate_pool_reviewed",
            "passed": audit.get("production_ready") is True,
            "reason": (
                "Candidate pool is externally reviewed for production validation planning."
                if audit.get("production_ready") is True
                else "Candidate pool is an example planning input until external review approves identity and sampling."
            ),
            "blocking_failures": list(audit.get("failures", [])),
            "externally_reviewed": audit.get("externally_reviewed"),
            "production_ready": audit.get("production_ready"),
        },
        "configuration_guidance": {
            "example_candidate_path": str(default_industry_event_candidate_cases_path()),
            "example_is_demonstration_only": True,
            "cli_audit_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-candidates --candidates {selected_path}"
            ),
            "http_query": f"GET /industry-event-candidates?candidates={selected_path}",
            "policy": (
                "Use candidate pools to select public people before event collection. Production validation still "
                "requires reviewed identity, reviewed event manifests, and negative-year coverage."
            ),
        },
    }


def industry_event_candidate_pool_fetch_cache(
    repo_path: Path,
    *,
    candidate_path: Path | None = None,
    query_plan_path: Path | None = None,
    cache_dir: Path | None = None,
    domain: str | None = None,
    split_role: str | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """Plan or execute fetch/cache steps for a celebrity candidate pool."""
    ensure_repo(repo_path)
    selected_candidate_path = candidate_path or default_industry_event_candidate_cases_path()
    selected_query_plan = query_plan_path or default_industry_event_query_plan_path()
    selected_cache_dir = cache_dir or repo_path / "industry_event_cache"
    batch_plan = build_candidate_pool_fetch_cache_plan(
        selected_candidate_path,
        query_plan_path=selected_query_plan,
        cache_dir=selected_cache_dir,
        domain=domain,
        split_role=split_role,
        live=live,
    )
    return {
        "repo": str(repo_path),
        "candidate_path": str(selected_candidate_path),
        "query_plan_path": str(selected_query_plan),
        "cache_dir": str(selected_cache_dir),
        "configured": candidate_path is not None,
        "live_requested": live,
        "candidate_pool_fetch_cache_plan": batch_plan,
        "configuration_guidance": {
            "example_candidate_path": str(default_industry_event_candidate_cases_path()),
            "example_query_plan_path": str(default_industry_event_query_plan_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-candidate-fetch-cache --candidates {selected_candidate_path} "
                f"--query-plan {selected_query_plan} --cache-dir {selected_cache_dir}"
            ),
            "policy": (
                "Without --live this batch command creates deterministic cache plans only. Live collection still "
                "requires reviewed candidate identity, reviewed query plans, and event-manifest review."
            ),
        },
    }


def industry_event_candidate_pool_draft_import(
    repo_path: Path,
    *,
    candidate_path: Path | None = None,
    query_plan_path: Path | None = None,
    cache_dir: Path | None = None,
    domain: str | None = None,
    split_role: str | None = None,
) -> dict[str, Any]:
    """Import cached candidate-pool source responses into draft manifests."""
    ensure_repo(repo_path)
    selected_candidate_path = candidate_path or default_industry_event_candidate_cases_path()
    selected_query_plan = query_plan_path or default_industry_event_query_plan_path()
    selected_cache_dir = cache_dir or repo_path / "industry_event_cache"
    draft_import = build_candidate_pool_manifest_drafts_from_cache(
        selected_candidate_path,
        query_plan_path=selected_query_plan,
        cache_dir=selected_cache_dir,
        domain=domain,
        split_role=split_role,
    )
    return {
        "repo": str(repo_path),
        "candidate_path": str(selected_candidate_path),
        "query_plan_path": str(selected_query_plan),
        "cache_dir": str(selected_cache_dir),
        "configured": candidate_path is not None,
        "candidate_pool_draft_import": draft_import,
        "configuration_guidance": {
            "example_candidate_path": str(default_industry_event_candidate_cases_path()),
            "example_query_plan_path": str(default_industry_event_query_plan_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} "
                f"industry-event-candidate-draft-import --candidates {selected_candidate_path} "
                f"--query-plan {selected_query_plan} --cache-dir {selected_cache_dir}"
            ),
            "policy": (
                "This imports existing cached source responses only. It does not fetch live data and generated "
                "draft manifests still require source review before calibration use."
            ),
        },
    }


def industry_event_collection_requests(
    repo_path: Path,
    *,
    query_plan_path: Path | None = None,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str = "holdout",
    domain: str | None = None,
) -> dict[str, Any]:
    """Build an offline collection request bundle from an industry-event query plan."""
    ensure_repo(repo_path)
    selected_path = query_plan_path or default_industry_event_query_plan_path()
    bundle = build_industry_event_collection_request_bundle(
        selected_path,
        case_id=case_id,
        public_name=public_name,
        person_qid=person_qid,
        start_year=start_year,
        end_year=end_year,
        split_role=split_role,
        domain=domain,
    )
    return {
        "repo": str(repo_path),
        "query_plan_path": str(selected_path),
        "configured": query_plan_path is not None,
        "offline_only": True,
        "request_bundle": bundle,
        "configuration_guidance": {
            "example_query_plan_path": str(default_industry_event_query_plan_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} industry-event-requests "
                f"--query-plan {selected_path} --case-id {case_id} --public-name \"{public_name}\" "
                f"--person-qid {person_qid} --start-year {start_year} --end-year {end_year} "
                f"--split-role {split_role}"
            ),
            "policy": "Review the offline request bundle before any live collection. Live execution remains disabled here.",
        },
    }


def industry_event_fetch_cache(
    repo_path: Path,
    *,
    cache_dir: Path | None = None,
    query_plan_path: Path | None = None,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str = "holdout",
    domain: str | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """Plan or execute reviewed industry-event source fetches into cache."""
    ensure_repo(repo_path)
    selected_path = query_plan_path or default_industry_event_query_plan_path()
    selected_cache_dir = cache_dir or repo_path / "industry_event_cache"
    fetch_plan = build_industry_event_fetch_cache_plan(
        selected_path,
        cache_dir=selected_cache_dir,
        case_id=case_id,
        public_name=public_name,
        person_qid=person_qid,
        start_year=start_year,
        end_year=end_year,
        split_role=split_role,
        domain=domain,
        live=live,
    )
    return {
        "repo": str(repo_path),
        "query_plan_path": str(selected_path),
        "cache_dir": str(selected_cache_dir),
        "configured": query_plan_path is not None,
        "live_requested": live,
        "fetch_cache_plan": fetch_plan,
        "configuration_guidance": {
            "example_query_plan_path": str(default_industry_event_query_plan_path()),
            "example_is_demonstration_only": True,
            "cli_command": (
                f"python -m examples.mingli_5agents.cli --repo {repo_path} industry-event-fetch-cache "
                f"--query-plan {selected_path} --cache-dir {selected_cache_dir} --case-id {case_id} "
                f"--public-name \"{public_name}\" --person-qid {person_qid} --start-year {start_year} "
                f"--end-year {end_year} --split-role {split_role}"
            ),
            "policy": (
                "Without --live this only creates a deterministic cache plan. With --live it still requires "
                "a reviewed collection_ready query plan before contacting any public source."
            ),
        },
    }


def industry_event_manifest_draft_from_response(
    repo_path: Path,
    *,
    response_path: Path,
    query_plan_path: Path | None = None,
    case_id: str,
    public_name: str,
    person_qid: str,
    start_year: int,
    end_year: int,
    split_role: str = "holdout",
    domain: str,
) -> dict[str, Any]:
    """Build a draft industry-event manifest from a cached source response."""
    ensure_repo(repo_path)
    selected_path = query_plan_path or default_industry_event_query_plan_path()
    draft = build_industry_event_manifest_draft_from_wikidata_response(
        selected_path,
        response_path,
        case_id=case_id,
        public_name=public_name,
        person_qid=person_qid,
        start_year=start_year,
        end_year=end_year,
        split_role=split_role,
        domain=domain,
    )
    return {
        "repo": str(repo_path),
        "query_plan_path": str(selected_path),
        "response_path": str(response_path),
        "offline_only": True,
        "draft": draft,
        "configuration_guidance": {
            "example_query_plan_path": str(default_industry_event_query_plan_path()),
            "example_is_demonstration_only": True,
            "policy": (
                "Draft manifests generated from cached responses must pass industry-events audit and external "
                "review before use as production evidence."
            ),
        },
    }


def _industry_event_query_plan_configuration_guidance(repo_path: Path, query_plan_path: Path | None) -> dict[str, Any]:
    example_query_plan = default_industry_event_query_plan_path()
    query_plan_arg = str(query_plan_path) if query_plan_path else str(example_query_plan)
    return {
        "configured": query_plan_path is not None,
        "env_var": "SEMAS_INDUSTRY_EVENT_QUERY_PLAN",
        "current_query_plan_path": str(query_plan_path) if query_plan_path else None,
        "example_query_plan_path": str(example_query_plan),
        "example_is_demonstration_only": True,
        "cli_audit_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"industry-event-queries --query-plan {query_plan_arg}"
        ),
        "http_query": f"GET /industry-event-queries?query_plan={query_plan_arg}",
        "policy": (
            "Provide an externally reviewed query plan before collecting public industry events from live sources. "
            "The query plan still does not certify the resulting manifest; collected records must pass the "
            "industry-events manifest audit."
        ),
    }


def _industry_event_manifest_configuration_guidance(repo_path: Path, manifest_path: Path | None) -> dict[str, Any]:
    example_manifest = default_industry_event_manifest_path()
    manifest_arg = str(manifest_path) if manifest_path else str(example_manifest)
    return {
        "configured": manifest_path is not None,
        "env_var": "SEMAS_INDUSTRY_EVENT_MANIFEST",
        "current_manifest_path": str(manifest_path) if manifest_path else None,
        "example_manifest_path": str(example_manifest),
        "example_is_demonstration_only": True,
        "cli_audit_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"industry-events --manifest {manifest_arg}"
        ),
        "http_query": f"GET /industry-events?manifest={manifest_arg}",
        "policy": (
            "Provide a reviewed public industry-event manifest covering positive and negative years before using "
            "film, music, or sports event data for false-positive-sensitive calibration."
        ),
    }


def _outcome_dataset_configuration_guidance(repo_path: Path, manifest_path: Path | None) -> dict[str, Any]:
    """Return stable operator guidance for configuring a real outcome manifest."""
    example_manifest = Path(__file__).resolve().parent / "providers" / "outcome_dataset_manifest_example.json"
    manifest_arg = str(manifest_path) if manifest_path else "<manifest.json>"
    return {
        "configured": manifest_path is not None,
        "env_var": "SEMAS_OUTCOME_DATASET_MANIFEST",
        "current_manifest_path": str(manifest_path) if manifest_path else None,
        "example_manifest_path": str(example_manifest),
        "example_is_demonstration_only": True,
        "cli_audit_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"outcome-dataset --manifest {manifest_arg}"
        ),
        "production_readiness_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"production-readiness --manifest {manifest_arg} --live"
        ),
        "http_query": f"GET /outcome-dataset?manifest={manifest_arg}",
        "policy": (
            "Provide an externally reviewed, deidentified, frozen-split manifest. "
            "The bundled example is only a contract demonstration and must not be treated as production evidence."
        ),
    }


def classical_sources_status(repo_path: Path, *, source_list_path: Path | None = None) -> dict[str, Any]:
    """Audit external classical-source refresh configuration."""
    ensure_repo(repo_path)
    audit = source_list_audit(source_list_path)
    passed = audit.get("status") == "ready"
    return {
        "repo": str(repo_path),
        "configured": passed,
        "source_list_path": str(source_list_path) if source_list_path else audit.get("source_list", ""),
        "audit": audit,
        "configuration_guidance": _classical_sources_configuration_guidance(repo_path, source_list_path),
        "production_gate": {
            "id": "classical_source_refresh_ready",
            "passed": passed,
            "reason": "External classical-source refresh list is configured, allowlisted, and hash-pinned.",
            "failure_reason": ""
            if passed
            else "Configure SEMAS_CLASSIC_SOURCE_LIST with allowlisted, SHA-256-pinned classical-source manifests.",
            "details": audit.get("failures", []),
        },
    }


def _classical_sources_configuration_guidance(repo_path: Path, source_list_path: Path | None) -> dict[str, Any]:
    """Return stable operator guidance for configuring classical-source refresh."""
    example_source_list = Path(__file__).resolve().parent / "providers" / "classical_source_list_example.json"
    source_list_arg = str(source_list_path) if source_list_path else "<source-list.json>"
    cache_arg = str(repo_path / "classical_sources" / "cache")
    output_arg = str(repo_path / "classical_sources" / "corpus")
    return {
        "configured": source_list_path is not None,
        "env_var": "SEMAS_CLASSIC_SOURCE_LIST",
        "current_source_list_path": str(source_list_path) if source_list_path else None,
        "example_source_list_path": str(example_source_list),
        "example_is_demonstration_only": True,
        "cli_audit_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"classical-sources --source-list {source_list_arg}"
        ),
        "cli_refresh_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"classical-refresh --source-list {source_list_arg} --cache-dir {cache_arg} --output-dir {output_arg}"
        ),
        "production_readiness_command": (
            f"python -m examples.mingli_5agents.cli --repo {repo_path} "
            f"production-readiness --classical-source-list {source_list_arg} --live"
        ),
        "http_query": f"GET /classical-sources?source_list={source_list_arg}",
        "policy": (
            "Provide an allowlisted, SHA-256-pinned source list and refresh it into a reviewed local corpus. "
            "The bundled example is only a contract demonstration and must not be treated as a production corpus."
        ),
    }


def classical_sources_refresh(
    repo_path: Path,
    *,
    source_list_path: Path | None = None,
    cache_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Refresh allowlisted classical-source manifests into a local JSONL corpus."""
    ensure_repo(repo_path)
    audit = source_list_audit(source_list_path)
    source_list = Path(str(audit.get("source_list") or "")) if audit.get("source_list") else None
    default_cache = repo_path / "classical_sources" / "cache"
    default_output = repo_path / "classical_sources" / "corpus"
    target_cache = cache_dir or default_cache
    target_output = output_dir or default_output
    if audit.get("status") != "ready" or source_list is None:
        return {
            "repo": str(repo_path),
            "status": "blocked",
            "refreshed": False,
            "source_list_path": str(source_list_path) if source_list_path else audit.get("source_list", ""),
            "cache_dir": str(target_cache),
            "output_dir": str(target_output),
            "audit": audit,
            "refresh": None,
            "refresh_receipt": None,
            "failures": audit.get("failures", []),
            "source_list_receipt": audit.get("source_list_receipt", {}),
        }
    try:
        refresh = refresh_corpus_manifests(source_list, target_cache, target_output)
    except Exception as exc:  # noqa: BLE001 - user-facing refresh should return JSON diagnostics.
        return {
            "repo": str(repo_path),
            "status": "failed",
            "refreshed": False,
            "source_list_path": str(source_list),
            "cache_dir": str(target_cache),
            "output_dir": str(target_output),
            "audit": audit,
            "refresh": None,
            "refresh_receipt": None,
            "failures": [str(exc)],
            "source_list_receipt": audit.get("source_list_receipt", {}),
        }
    return {
        "repo": str(repo_path),
        "status": "refreshed",
        "refreshed": True,
        "source_list_path": str(source_list),
        "cache_dir": str(target_cache),
        "output_dir": str(target_output),
        "audit": audit,
        "refresh": refresh,
        "refresh_receipt": refresh.get("refresh_receipt", {}),
        "failures": [],
        "source_list_receipt": audit.get("source_list_receipt", {}),
    }


def _classical_refresh_receipt_path(repo_path: Path) -> Path:
    return repo_path / "classical_sources" / "corpus" / "refresh_receipt.json"


def _read_classical_refresh_receipt(repo_path: Path) -> dict[str, Any] | None:
    path = _classical_refresh_receipt_path(repo_path)
    if not path.exists():
        return None
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(receipt, dict):
        return None
    if not isinstance(receipt.get("sha256"), str) or len(receipt.get("sha256", "")) != 64:
        return None
    return receipt


def _classical_latest_refresh_receipt_current(source_audit: Any, refresh_receipt: Any) -> bool:
    if not isinstance(source_audit, dict) or source_audit.get("status") != "ready":
        return False
    if not isinstance(refresh_receipt, dict) or not isinstance(refresh_receipt.get("material"), dict):
        return False
    source_receipt = source_audit.get("source_list_receipt", {})
    expected_source_sha = source_receipt.get("sha256") if isinstance(source_receipt, dict) else None
    material = refresh_receipt.get("material", {})
    return (
        isinstance(refresh_receipt.get("sha256"), str)
        and len(refresh_receipt.get("sha256", "")) == 64
        and isinstance(expected_source_sha, str)
        and len(expected_source_sha) == 64
        and material.get("source_list_receipt_sha256") == expected_source_sha
        and isinstance(material.get("record_count"), int)
        and material.get("record_count") > 0
    )


def _classical_latest_refresh_receipt_failures(source_audit: Any, refresh_receipt: Any) -> list[str]:
    failures = []
    if not isinstance(source_audit, dict) or source_audit.get("status") != "ready":
        failures.append("classical source list is not ready")
    source_receipt = source_audit.get("source_list_receipt", {}) if isinstance(source_audit, dict) else {}
    expected_source_sha = source_receipt.get("sha256") if isinstance(source_receipt, dict) else None
    if not isinstance(expected_source_sha, str) or len(expected_source_sha) != 64:
        failures.append("current source_list_receipt sha256 is missing")
    if not isinstance(refresh_receipt, dict):
        failures.append("latest classical refresh receipt is missing")
        return failures
    if not isinstance(refresh_receipt.get("sha256"), str) or len(refresh_receipt.get("sha256", "")) != 64:
        failures.append("latest classical refresh receipt sha256 is missing")
    material = refresh_receipt.get("material", {})
    if not isinstance(material, dict):
        failures.append("latest classical refresh receipt material is missing")
        return failures
    if isinstance(expected_source_sha, str) and material.get("source_list_receipt_sha256") != expected_source_sha:
        failures.append("latest classical refresh receipt does not match current source_list_receipt")
    if not isinstance(material.get("record_count"), int) or material.get("record_count") <= 0:
        failures.append("latest classical refresh receipt has no ingested records")
    return failures


def production_readiness(
    repo_path: Path,
    *,
    manifest_path: Path | None = None,
    classical_source_list_path: Path | None = None,
    live: bool = False,
    expected_readiness_receipt_sha256: str | None = None,
    expected_audit_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Aggregate hard production-readiness gates for the mingli framework."""
    ensure_repo(repo_path)
    providers = provider_checks(repo_path, live=live, profile="production")
    outcome = outcome_dataset_manifest_status(repo_path, manifest_path=manifest_path)
    history = version_history(repo_path)
    audit = capability_audit(
        repo_path,
        expected_audit_receipt_sha256=expected_audit_receipt_sha256,
        classical_source_list_path=classical_source_list_path,
    )
    audit_receipt = audit.get("audit_receipt", {})
    audit_receipt_matches_expected = audit.get("audit_receipt_matches_expected")
    evidence_materialization = audit.get("evidence_materialization", {})
    blocked_capability_coverage = audit.get("blocked_capability_coverage", {})
    known_gap_handoff_bundle = audit.get("known_gap_handoff_bundle", {})
    classical_source_refresh = audit.get("classical_source_refresh", {})
    classical_refresh_receipt = _read_classical_refresh_receipt(repo_path)
    known_gap_ids = [str(item.get("id")) for item in audit.get("known_gaps", []) if isinstance(item, dict)]
    known_gap_resolution_plan = audit.get("known_gap_resolution_plan", [])
    birth_profile_source_review_workplan_summary = _birth_profile_source_review_workplan_summary_from_audit(audit)
    birth_profile_source_lookup_plan_summary = _birth_profile_source_lookup_plan_summary_from_audit(audit)
    birth_profile_source_cache_template_preview_summary = (
        _birth_profile_source_cache_template_preview_summary_from_audit(audit)
    )
    birth_profile_source_family_cache_enforcement_summary = (
        _birth_profile_source_family_cache_enforcement_summary_from_audit(audit)
    )
    birth_profile_substantive_evidence_cache_enforcement_summary = (
        _birth_profile_substantive_evidence_cache_enforcement_summary_from_audit(audit)
    )
    birth_profile_source_cache_audit_summary = _birth_profile_source_cache_audit_summary_from_audit(audit)
    birth_profile_reviewed_manifest_draft_preview_summary = (
        _birth_profile_reviewed_manifest_draft_preview_summary_from_audit(audit)
    )
    birth_profile_import_preview_summary = _birth_profile_import_preview_summary_from_audit(audit)
    birth_profile_fixture_patch_preview_summary = _birth_profile_fixture_patch_preview_summary_from_audit(audit)
    known_gap_resolution_plan_coverage = _known_gap_resolution_plan_coverage_from_response(
        {
            "known_gap_ids": known_gap_ids,
            "known_gap_resolution_plan": known_gap_resolution_plan,
            "capability_audit_receipt": audit_receipt,
        }
    )
    current_repo = ensure_repo(repo_path)
    current_benchmark = run_benchmark(current_repo).__dict__
    benchmark_floor_failures = _benchmark_metric_floor_failures(current_benchmark)
    benchmark_geocoding_failures = _benchmark_birthplace_geocoding_failures(current_benchmark)
    benchmark_deliberation_failures = _benchmark_deliberation_receipt_failures(current_benchmark)
    benchmark_annual_timeline_failures = _benchmark_annual_timeline_receipt_failures(current_benchmark)
    benchmark_monthly_luck_failures = _benchmark_monthly_luck_receipt_failures(current_benchmark)
    benchmark_auspicious_calendar_failures = _benchmark_auspicious_calendar_receipt_failures(current_benchmark)
    benchmark_external_birth_match_failures = _benchmark_external_payload_birth_match_failures(current_benchmark)
    benchmark_topic_confidence_failures = _benchmark_topic_confidence_failures(current_benchmark)
    benchmark_chinese_render_quality_failures = _benchmark_chinese_render_quality_failures(current_benchmark)
    benchmark_analyze_response_schema = _benchmark_analyze_response_schema_audit(
        repo_path,
        version=int(current_benchmark.get("genome_version", 0) or 0),
    )
    benchmark_analyze_response_schema_failures = _benchmark_analyze_response_schema_failures(
        benchmark_analyze_response_schema
    )
    provider_ledger = _provider_certification_ledger_status(repo_path)
    provider_drift = _provider_certification_drift_status(repo_path, provider_ledger, live=live)
    release_ledger = _release_manifest_ledger_status(repo_path)
    gates = [
        _readiness_gate(
            "provider_profile_ready",
            providers.get("profile_readiness", {}).get("ready") is True,
            "Production provider profile is ready.",
            "Configure professional providers, provenance, and run live smoke checks.",
            providers.get("profile_readiness", {}).get("blockers", []),
        ),
        _readiness_gate(
            "provider_integration_ready",
            providers.get("integration_plan", {}).get("production_ready") is True,
            "All professional integration targets are ready.",
            "Complete blocked provider integration targets.",
            providers.get("integration_plan", {}).get("blocked_targets", []),
        ),
        _readiness_gate(
            "outcome_dataset_configured",
            manifest_path is not None,
            "Outcome dataset manifest is configured.",
            "Provide an externally reviewed outcome dataset manifest path.",
            [] if manifest_path else ["manifest path is required for production readiness"],
        ),
        _readiness_gate(
            "outcome_dataset_gate_passed",
            outcome.get("evolution_gate", {}).get("passed") is True and manifest_path is not None,
            "Outcome dataset governance gate passed.",
            "Fix outcome manifest consent, privacy, labels, baselines, statistical plan, or records.",
            outcome.get("evolution_gate", {}).get("blocking_failures", []),
        ),
        _readiness_gate(
            "predictive_optimization_disabled",
            outcome.get("evolution_gate", {}).get("predictive_optimization_enabled") is False,
            "Predictive optimization is disabled.",
            "Disable predictive optimization until external review approves it.",
            [],
        ),
        _readiness_gate(
            "outcome_dataset_data_split_records_covered",
            outcome.get("audit", {}).get("data_split_record_coverage", {}).get("coverage_complete") is True
            and manifest_path is not None,
            "Outcome dataset train/holdout split covers every manifest record.",
            "Assign every records[].case_id to train_case_ids or holdout_case_ids and remove unknown or overlapping IDs.",
            _outcome_dataset_split_coverage_failures(outcome),
        ),
        _readiness_gate(
            "outcome_dataset_statistical_plan_preregistered",
            outcome.get("audit", {}).get("statistical_plan", {}).get("preregistration_complete") is True
            and manifest_path is not None,
            "Outcome dataset statistical plan is pre-registered and hash- or receipt-pinned.",
            "Pre-register and freeze the statistical plan before using the outcome dataset for production validation.",
            []
            if outcome.get("audit", {}).get("statistical_plan", {}).get("preregistration_complete") is True
            else ["statistical_plan.preregistration_complete is false"],
        ),
        _readiness_gate(
            "provider_certification_ledger_available",
            provider_ledger.get("record_count", 0) > 0,
            "Provider certification ledger has at least one recorded receipt.",
            "Record certified professional provider receipts before production.",
            provider_ledger.get("failures", []),
        ),
        _readiness_gate(
            "provider_certification_ledger_integrity",
            provider_ledger.get("integrity_status") == "pass",
            "Provider certification ledger hash-chain integrity passed.",
            "Repair provider certification ledger hash-chain failures before production.",
            provider_ledger.get("failures", []),
        ),
        _readiness_gate(
            "provider_certification_ledger_covers_domains",
            provider_ledger.get("coverage_status") == "complete",
            "Provider certification ledger covers all professional JSON-CLI domains.",
            "Record certified receipts for every professional JSON-CLI provider domain.",
            provider_ledger.get("missing_domains", []),
        ),
        _readiness_gate(
            "provider_certification_protocols_current",
            provider_ledger.get("protocol_status") == "current" and provider_ledger.get("record_count", 0) > 0,
            "Recorded provider certifications match the current JSON-CLI protocol hashes.",
            "Re-certify providers after protocol changes and record fresh receipts.",
            provider_ledger.get("protocol_failures", []),
        ),
        _readiness_gate(
            "provider_certification_request_receipts_current",
            provider_ledger.get("request_receipt_status") == "current" and provider_ledger.get("record_count", 0) > 0,
            "Recorded provider certifications include valid request-level stdin/stdout receipts.",
            "Re-certify providers with request receipt binding before production.",
            provider_ledger.get("request_receipt_failures", []),
        ),
        _readiness_gate(
            "provider_certification_reference_contracts_current",
            provider_ledger.get("reference_contract_status") == "current" and provider_ledger.get("record_count", 0) > 0,
            "Recorded provider certifications include reference contract coverage evidence.",
            "Re-certify providers so receipts bind reference chart and method coverage.",
            provider_ledger.get("reference_contract_failures", []),
        ),
        _readiness_gate(
            "provider_certification_command_fingerprints_current",
            provider_ledger.get("command_fingerprint_status") == "current" and provider_ledger.get("record_count", 0) > 0,
            "Recorded provider certifications bind external command and artifact fingerprints.",
            "Re-certify providers so receipts bind the JSON-CLI command and provider artifact fingerprint.",
            provider_ledger.get("command_fingerprint_failures", []),
        ),
        _readiness_gate(
            "provider_certification_receipts_current",
            provider_drift.get("passed") is True,
            "Current provider certifications match recorded ledger receipts.",
            "Re-run live provider certification and resolve receipt drift before production.",
            provider_drift.get("failures", []),
        ),
        _readiness_gate(
            "release_manifest_ledger_integrity",
            release_ledger.get("exists") is not True or release_ledger.get("integrity_status") == "pass",
            "Release manifest ledger is absent or has valid hash-chain integrity.",
            "Repair release manifest ledger hash-chain failures before production.",
            release_ledger.get("failures", []) if release_ledger.get("exists") is True else [],
        ),
        _readiness_gate(
            "history_integrity_passed",
            history.get("history_integrity", {}).get("status") == "pass",
            "Version history integrity passed.",
            "Repair lineage, fingerprints, archive references, or version sequence.",
            history.get("history_integrity", {}).get("failures", []),
        ),
        _readiness_gate(
            "archive_integrity_passed",
            history.get("archive_integrity", {}).get("status") == "pass",
            "Archive hash-chain integrity passed.",
            "Repair archive hash-chain failures before production.",
            history.get("archive_integrity", {}).get("failures", []),
        ),
        _readiness_gate(
            "capability_audit_available",
            audit.get("status") in {"operational_with_known_gaps", "production_ready"},
            "Capability audit is available.",
            "Capability audit must run before production.",
            [],
        ),
        _readiness_gate(
            "capability_audit_receipt_current",
            audit_receipt_matches_expected is not False,
            "Capability audit receipt matches the expected value, or no expected audit receipt was provided.",
            "Review capability audit drift and update the expected audit receipt only after accepting the change.",
            [audit.get("audit_receipt_mismatch_reason", "")]
            if audit_receipt_matches_expected is False
            else [],
        ),
        _readiness_gate(
            "implemented_evidence_materialized",
            evidence_materialization.get("failed_count") == 0,
            "Implemented requirement evidence materialization has no failed checks.",
            "Repair implemented requirement evidence paths or Python symbols before production.",
            _evidence_materialization_failures(evidence_materialization),
        ),
        _readiness_gate(
            "blocked_capability_coverage_complete",
            blocked_capability_coverage.get("coverage_complete") is True,
            "Every false capability is mapped to a known gap or explicit optional-configuration policy.",
            "Repair blocked capability coverage so no false capability remains unaccounted.",
            blocked_capability_coverage.get("unaccounted_capabilities", [])
            if isinstance(blocked_capability_coverage, dict)
            else ["blocked_capability_coverage is missing"],
        ),
        _readiness_gate(
            "known_gap_handoff_bundle_ready",
            isinstance(known_gap_handoff_bundle, dict)
            and known_gap_handoff_bundle.get("status") == "ready"
            and known_gap_handoff_bundle.get("gap_count") == len(known_gap_ids)
            and known_gap_handoff_bundle.get("missing_handoff_gap_ids") == []
            and isinstance(known_gap_handoff_bundle.get("bundle_sha256"), str)
            and len(known_gap_handoff_bundle.get("bundle_sha256", "")) == 64,
            "Every open known gap has a portable handoff bundle with closure commands, gates, provenance, and ownership.",
            "Repair known-gap handoff coverage before production so external provider/source/dataset closure is portable.",
            (
                known_gap_handoff_bundle.get("missing_handoff_gap_ids", [])
                if isinstance(known_gap_handoff_bundle, dict)
                else ["known_gap_handoff_bundle is missing"]
            ),
        ),
        _readiness_gate(
            "ziwei_qimen_calculation_basis_audit_contract",
            audit.get("capabilities", {}).get("ziwei_qimen_calculation_basis_audit_contract") is True,
            "Ziwei and Qimen provider protocols require auditable calculation-basis metadata.",
            "Restore raw provider contracts and stdout schemas for Ziwei/Qimen calculation-basis metadata before production.",
            []
            if audit.get("capabilities", {}).get("ziwei_qimen_calculation_basis_audit_contract") is True
            else ["ziwei_qimen_calculation_basis_audit_contract is not implemented"],
        ),
        _readiness_gate(
            "astrology_ephemeris_audit_contract",
            audit.get("capabilities", {}).get("astrology_ephemeris_audit_contract") is True,
            "Astrology provider protocols require auditable ephemeris metadata.",
            "Restore raw astrology provider contracts and stdout schemas for ephemeris provenance before production.",
            []
            if audit.get("capabilities", {}).get("astrology_ephemeris_audit_contract") is True
            else ["astrology_ephemeris_audit_contract is not implemented"],
        ),
        _readiness_gate(
            "xuanze_rule_table_audit_contract",
            audit.get("capabilities", {}).get("xuanze_rule_table_audit_contract") is True,
            "Xuanze provider protocols require auditable rule-table metadata.",
            "Restore raw xuanze provider contracts and stdout schemas for rule-table provenance before production.",
            []
            if audit.get("capabilities", {}).get("xuanze_rule_table_audit_contract") is True
            else ["xuanze_rule_table_audit_contract is not implemented"],
        ),
        _readiness_gate(
            "known_gap_resolution_plan_covered",
            known_gap_resolution_plan_coverage.get("coverage_complete") is True,
            "Every known gap has a remediation plan with verification commands and production gate IDs.",
            "Repair the capability audit known-gap resolution plan before production.",
            (
                [
                    "missing_gap_ids="
                    + ",".join(known_gap_resolution_plan_coverage.get("missing_gap_ids", [])),
                    "invalid_plan_gap_ids="
                    + ",".join(known_gap_resolution_plan_coverage.get("invalid_plan_gap_ids", [])),
                    "invalid_gate_ids_by_gap="
                    + json.dumps(
                        known_gap_resolution_plan_coverage.get("invalid_gate_ids_by_gap", {}),
                        sort_keys=True,
                        ensure_ascii=True,
                    ),
                ]
                if known_gap_resolution_plan_coverage.get("coverage_complete") is not True
                else []
            ),
        ),
        _readiness_gate(
            "classical_source_refresh_ready",
            classical_source_refresh.get("status") == "ready",
            "External classical-source refresh list is configured, allowlisted, and hash-pinned.",
            "Configure SEMAS_CLASSIC_SOURCE_LIST with allowlisted, SHA-256-pinned classical-source manifests.",
            classical_source_refresh.get("failures", []),
        ),
        _readiness_gate(
            "classical_source_latest_refresh_receipt_present",
            _classical_latest_refresh_receipt_current(classical_source_refresh, classical_refresh_receipt),
            "Latest classical-source refresh receipt is present and bound to the current source-list receipt.",
            "Run classical-refresh after configuring the source list so production readiness binds the local corpus receipt.",
            _classical_latest_refresh_receipt_failures(classical_source_refresh, classical_refresh_receipt),
        ),
        _readiness_gate(
            "current_benchmark_passed",
            current_benchmark.get("passed_rate") == 1.0
            and current_benchmark.get("reference_charts", {}).get("passed") is True
            and current_benchmark.get("empirical_validation", {}).get("status") == "ready_non_predictive"
            and not benchmark_floor_failures,
            "Current coordinator benchmark passed all built-in cases, reference charts, and metric floors.",
            "Run benchmark and repair current coordinator regressions before production.",
            benchmark_floor_failures
            or [
                f"passed_rate={current_benchmark.get('passed_rate')}",
                f"reference_charts_passed={current_benchmark.get('reference_charts', {}).get('passed')}",
                f"empirical_validation_status={current_benchmark.get('empirical_validation', {}).get('status')}",
            ],
        ),
        _readiness_gate(
            "benchmark_birthplaces_geocoded",
            not benchmark_geocoding_failures,
            "Benchmark birthplaces resolve to auditable timezone and coordinates.",
            "Add offline geocoding entries or explicit coordinates/timezone for benchmark birthplaces.",
            benchmark_geocoding_failures,
        ),
        _readiness_gate(
            "benchmark_deliberation_receipts_bound",
            not benchmark_deliberation_failures,
            "Benchmark cases carry deliberation receipts binding discussion, votes, source review, and conflicts.",
            "Restore deliberation receipt generation and request-provenance binding for benchmark reports.",
            benchmark_deliberation_failures,
        ),
        _readiness_gate(
            "benchmark_annual_timeline_receipts_bound",
            not benchmark_annual_timeline_failures,
            "Benchmark cases carry annual timeline receipts bound to request provenance.",
            "Restore annual timeline receipt generation and request-provenance binding for benchmark reports.",
            benchmark_annual_timeline_failures,
        ),
        _readiness_gate(
            "benchmark_monthly_luck_receipts_bound",
            not benchmark_monthly_luck_failures,
            "Benchmark cases carry monthly luck receipts bound to request provenance.",
            "Restore monthly luck receipt generation and request-provenance binding for benchmark reports.",
            benchmark_monthly_luck_failures,
        ),
        _readiness_gate(
            "benchmark_auspicious_calendar_receipts_bound",
            not benchmark_auspicious_calendar_failures,
            "Benchmark cases carry auspicious-calendar receipts bound to request provenance.",
            "Restore auspicious-calendar receipt generation and request-provenance binding for benchmark reports.",
            benchmark_auspicious_calendar_failures,
        ),
        _readiness_gate(
            "benchmark_external_payload_birth_matches",
            not benchmark_external_birth_match_failures,
            "Benchmark external professional payloads do not declare mismatched birth data.",
            "Reject or regenerate external professional payloads whose declared birth profile does not match the request.",
            benchmark_external_birth_match_failures,
        ),
        _readiness_gate(
            "benchmark_topic_confidence_boundaries",
            not benchmark_topic_confidence_failures,
            "Benchmark topic synthesis carries confidence summaries and non-predictive boundaries.",
            "Restore topic synthesis confidence summaries before production.",
            benchmark_topic_confidence_failures,
        ),
        _readiness_gate(
            "benchmark_chinese_render_quality_diagnostics",
            not benchmark_chinese_render_quality_failures,
            "Benchmark Chinese reports expose clean prose, zero repetition, and full row-evidence anchors.",
            "Restore Chinese report rendering so benchmark diagnostics show no English/code leakage, no duplicated annual/monthly bullets, and full evidence-anchor coverage.",
            benchmark_chinese_render_quality_failures,
        ),
        _readiness_gate(
            "benchmark_analyze_response_schema_valid",
            not benchmark_analyze_response_schema_failures,
            "Every built-in benchmark AnalyzeResponse validates against the public schema contract.",
            "Repair analyze_case runtime output or schema_document so benchmark responses pass AnalyzeResponse validation.",
            benchmark_analyze_response_schema_failures,
        ),
        _readiness_gate(
            "birth_profile_source_review_workplan_available",
            _birth_profile_source_review_workplan_available(birth_profile_source_review_workplan_summary),
            "Celebrity birth-profile source-review workplan is present, non-mutating, and ready for human review.",
            "Restore the non-mutating birth-profile source-review workplan before production.",
            _birth_profile_source_review_workplan_failures(birth_profile_source_review_workplan_summary),
        ),
        _readiness_gate(
            "birth_profile_source_lookup_plan_dry_run",
            _birth_profile_source_lookup_plan_dry_run(birth_profile_source_lookup_plan_summary),
            "Celebrity birth-profile source lookup plan is present and remains dry-run.",
            "Restore the non-mutating birth-profile source lookup plan before production.",
            _birth_profile_source_lookup_plan_failures(birth_profile_source_lookup_plan_summary),
        ),
        _readiness_gate(
            "birth_profile_source_family_catalog_bound",
            _birth_profile_source_family_catalog_bound(birth_profile_source_lookup_plan_summary),
            "Celebrity birth-profile lookup plan binds source families and birth-time evidence policy.",
            "Restore source-family catalog binding so identity anchors cannot be promoted to birth-time evidence.",
            _birth_profile_source_family_catalog_failures(birth_profile_source_lookup_plan_summary),
        ),
        _readiness_gate(
            "birth_profile_source_cache_template_preview_non_mutating",
            _birth_profile_source_cache_template_preview_non_mutating(
                birth_profile_source_cache_template_preview_summary
            ),
            "Celebrity birth-profile source cache template preview is present and non-mutating.",
            "Restore the non-mutating source-cache template preview before production.",
            _birth_profile_source_cache_template_preview_failures(
                birth_profile_source_cache_template_preview_summary
            ),
        ),
        _readiness_gate(
            "birth_profile_source_family_cache_enforcement_probe",
            _birth_profile_source_family_cache_enforcement_probe_passed(
                birth_profile_source_family_cache_enforcement_summary
            ),
            "Celebrity birth-profile cache audit rejects identity-anchor payloads that claim birth_time evidence.",
            "Restore source-family enforcement so identity/domain anchors cannot satisfy birth_time in cache audit.",
            _birth_profile_source_family_cache_enforcement_probe_failures(
                birth_profile_source_family_cache_enforcement_summary
            ),
        ),
        _readiness_gate(
            "birth_profile_substantive_evidence_cache_enforcement_probe",
            _birth_profile_substantive_evidence_cache_enforcement_probe_passed(
                birth_profile_substantive_evidence_cache_enforcement_summary
            ),
            "Celebrity birth-profile cache audit rejects reviewed metadata-only payloads.",
            "Restore substantive-evidence enforcement so source metadata cannot satisfy birth-profile facts.",
            _birth_profile_substantive_evidence_cache_enforcement_probe_failures(
                birth_profile_substantive_evidence_cache_enforcement_summary
            ),
        ),
        _readiness_gate(
            "birth_profile_source_cache_audit_read_only",
            _birth_profile_source_cache_audit_read_only(birth_profile_source_cache_audit_summary),
            "Celebrity birth-profile source cache audit is present, read-only, and non-importing.",
            "Restore the read-only birth-profile source cache audit before production.",
            _birth_profile_source_cache_audit_failures(birth_profile_source_cache_audit_summary),
        ),
        _readiness_gate(
            "birth_profile_reviewed_manifest_draft_preview_non_mutating",
            _birth_profile_reviewed_manifest_draft_preview_non_mutating(
                birth_profile_reviewed_manifest_draft_preview_summary
            ),
            "Celebrity birth-profile reviewed-manifest draft preview is present and non-mutating.",
            "Restore the non-mutating reviewed-manifest draft preview before production.",
            _birth_profile_reviewed_manifest_draft_preview_failures(
                birth_profile_reviewed_manifest_draft_preview_summary
            ),
        ),
        _readiness_gate(
            "birth_profile_import_preview_blocked",
            _birth_profile_import_preview_blocked(birth_profile_import_preview_summary),
            "Celebrity birth-profile import preview is present, non-mutating, and blocked until review completes.",
            "Restore the blocked non-mutating birth-profile import preview before production.",
            _birth_profile_import_preview_blocker_failures(birth_profile_import_preview_summary),
        ),
        _readiness_gate(
            "birth_profile_fixture_patch_preview_blocked",
            _birth_profile_fixture_patch_preview_blocked(birth_profile_fixture_patch_preview_summary),
            "Celebrity birth-profile fixture patch preview is present, non-mutating, and blocked until review completes.",
            "Restore the blocked non-mutating birth-profile fixture patch preview before production.",
            _birth_profile_fixture_patch_preview_blocker_failures(birth_profile_fixture_patch_preview_summary),
        ),
    ]
    production_gate_registry_audit = _production_gate_registry_audit(
        [*gates, {"id": "production_gate_registry_current"}]
    )
    gates.append(
        _readiness_gate(
            "production_gate_registry_current",
            production_gate_registry_audit.get("registry_current") is True,
            "Shared production gate registry covers every runtime readiness gate.",
            "Add missing readiness gate IDs to PRODUCTION_READINESS_GATE_IDS before production.",
            production_gate_registry_audit.get("missing_from_registry", []),
        )
    )
    blockers = [
        {
            "gate": gate["id"],
            "reason": gate["failure_reason"],
            "details": gate["details"],
        }
        for gate in gates
        if not gate["passed"]
    ]
    ready = not blockers
    resolution_plan = _production_resolution_plan(
        repo_path=repo_path,
        manifest_path=manifest_path,
        live=live,
        providers=providers,
        outcome=outcome,
        provider_ledger=provider_ledger,
        provider_drift=provider_drift,
        release_ledger=release_ledger,
        evidence_materialization=evidence_materialization,
        classical_source_refresh=classical_source_refresh,
        current_benchmark=current_benchmark,
        benchmark_analyze_response_schema=benchmark_analyze_response_schema,
        blockers=blockers,
    )
    response = {
        "repo": str(repo_path),
        "status": "production_ready" if ready else "production_blocked",
        "production_ready": ready,
        "live_requested": live,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "classical_source_list_path": str(classical_source_list_path) if classical_source_list_path else None,
        "gates": gates,
        "blockers": blockers,
        "resolution_plan": resolution_plan,
        "provider_readiness": providers.get("profile_readiness", {}),
        "provider_integration_plan": providers.get("integration_plan", {}),
        "provider_certification_ledger": provider_ledger,
        "provider_certification_drift": provider_drift,
        "release_manifest_ledger": release_ledger,
        "outcome_dataset": outcome,
        "outcome_dataset_receipt": outcome.get("outcome_dataset_receipt", {}),
        "history_integrity": history.get("history_integrity", {}),
        "archive_integrity": history.get("archive_integrity", {}),
        "state_of_art": audit.get("state_of_art", {}),
        "capability_audit_receipt": audit_receipt,
        "expected_audit_receipt_sha256": expected_audit_receipt_sha256,
        "audit_receipt_matches_expected": audit_receipt_matches_expected,
        "audit_receipt_mismatch_reason": audit.get("audit_receipt_mismatch_reason", ""),
        "evidence_materialization": evidence_materialization,
        "known_gap_handoff_bundle": known_gap_handoff_bundle,
        "classical_source_refresh": classical_source_refresh,
        "classical_refresh_receipt": classical_refresh_receipt,
        "current_benchmark": current_benchmark,
        "benchmark_analyze_response_schema": benchmark_analyze_response_schema,
        "known_gap_ids": known_gap_ids,
        "known_gap_resolution_plan": known_gap_resolution_plan,
        "production_gate_registry_audit": production_gate_registry_audit,
    }
    response["readiness_receipt"] = _production_readiness_receipt(response)
    receipt_sha256 = response["readiness_receipt"]["sha256"]
    response["expected_readiness_receipt_sha256"] = expected_readiness_receipt_sha256
    response["readiness_receipt_matches_expected"] = (
        None if expected_readiness_receipt_sha256 is None else receipt_sha256 == expected_readiness_receipt_sha256
    )
    response["readiness_receipt_mismatch_reason"] = (
        "production readiness receipt sha256 does not match expected value"
        if response["readiness_receipt_matches_expected"] is False
        else ""
    )
    return response


def _production_gate_registry_audit(gates: list[dict[str, Any]]) -> dict[str, Any]:
    actual_gate_ids = sorted(
        {str(gate.get("id")) for gate in gates if isinstance(gate, dict) and gate.get("id")}
    )
    registry_gate_ids = sorted(PRODUCTION_READINESS_GATE_IDS)
    missing_from_registry = sorted(set(actual_gate_ids) - set(registry_gate_ids))
    registry_only_gate_ids = sorted(set(registry_gate_ids) - set(actual_gate_ids))
    material = {
        "actual_gate_ids": actual_gate_ids,
        "registry_gate_ids": registry_gate_ids,
        "missing_from_registry": missing_from_registry,
        "registry_only_gate_ids": registry_only_gate_ids,
    }
    return {
        "actual_gate_count": len(actual_gate_ids),
        "registry_gate_count": len(registry_gate_ids),
        "actual_gate_ids": actual_gate_ids,
        "registry_gate_ids": registry_gate_ids,
        "missing_from_registry": missing_from_registry,
        "registry_only_gate_ids": registry_only_gate_ids,
        "registry_current": not missing_from_registry,
        "registry_audit_sha256": hashlib.sha256(
            json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest(),
    }


def _production_resolution_plan(
    *,
    repo_path: Path,
    manifest_path: Path | None,
    live: bool,
    providers: dict[str, Any],
    outcome: dict[str, Any],
    provider_ledger: dict[str, Any],
    provider_drift: dict[str, Any],
    release_ledger: dict[str, Any],
    evidence_materialization: dict[str, Any],
    classical_source_refresh: dict[str, Any],
    current_benchmark: dict[str, Any],
    benchmark_analyze_response_schema: dict[str, Any],
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return machine-readable remediation steps for failed production gates."""
    steps: list[dict[str, Any]] = []
    blocker_gates = {str(item.get("gate")) for item in blockers}
    if "outcome_dataset_configured" in blocker_gates:
        steps.append(
            _resolution_step(
                "configure_outcome_dataset_manifest",
                "outcome_dataset",
                "Provide a reviewed outcome manifest before production readiness.",
                ["python -m examples.mingli_5agents.cli --repo " f"{repo_path} production-readiness --manifest <manifest.json>"],
                ["manifest path is required for production readiness"],
                10,
            )
        )
    elif "outcome_dataset_gate_passed" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_outcome_dataset_manifest",
                "outcome_dataset",
                "Fix outcome manifest governance failures.",
                ["python -m examples.mingli_5agents.cli --repo " f"{repo_path} outcome-dataset --manifest {manifest_path}"],
                outcome.get("evolution_gate", {}).get("blocking_failures", []),
                20,
            )
        )
    if "outcome_dataset_data_split_records_covered" in blocker_gates and manifest_path is not None:
        steps.append(
            _resolution_step(
                "repair_outcome_dataset_split_coverage",
                "outcome_dataset",
                "Assign every outcome manifest record to the frozen train/holdout split.",
                ["python -m examples.mingli_5agents.cli --repo " f"{repo_path} outcome-dataset --manifest {manifest_path}"],
                _outcome_dataset_split_coverage_failures(outcome),
                15,
            )
        )
    if "outcome_dataset_statistical_plan_preregistered" in blocker_gates and manifest_path is not None:
        steps.append(
            _resolution_step(
                "preregister_outcome_statistical_plan",
                "outcome_dataset",
                "Pre-register, freeze, and hash-pin the outcome dataset statistical plan.",
                ["python -m examples.mingli_5agents.cli --repo " f"{repo_path} outcome-dataset --manifest {manifest_path}"],
                ["statistical_plan requires pre_registered, registration_id, registered_at, analysis_freeze_date, and plan_sha256 or plan_receipt_sha256"],
                16,
            )
        )
    steps.extend(_provider_resolution_steps(repo_path, providers, blocker_gates))
    if "provider_certification_ledger_covers_domains" in blocker_gates:
        missing_domains = [str(item) for item in provider_ledger.get("missing_domains", [])]
        for domain in missing_domains:
            steps.append(
                _resolution_step(
                    f"record_{domain}_provider_receipt",
                    "provider_ledger",
                    f"Record a certified provider receipt for {domain}.",
                    [
                        _provider_certification_command(repo_path, domain),
                        f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger",
                    ],
                    [f"{domain} has no recorded provider certification receipt"],
                    40,
                )
            )
    if "provider_certification_ledger_integrity" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_provider_certification_ledger_integrity",
                "provider_ledger",
                "Repair provider certification ledger hash-chain or receipt consistency failures.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger"],
                provider_ledger.get("failures", []),
                50,
            )
        )
    if "provider_certification_protocols_current" in blocker_gates:
        steps.append(
            _resolution_step(
                "recertify_stale_provider_protocols",
                "provider_ledger",
                "Re-certify providers whose recorded receipt protocol hash is stale.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger"],
                provider_ledger.get("protocol_failures", []),
                60,
            )
        )
    if "provider_certification_request_receipts_current" in blocker_gates:
        steps.append(
            _resolution_step(
                "recertify_provider_request_receipts",
                "provider_ledger",
                "Re-certify providers whose ledger records lack valid request-level stdin/stdout receipts.",
                _provider_recertification_commands(repo_path, provider_ledger.get("request_receipt_failures", [])),
                provider_ledger.get("request_receipt_failures", []),
                65,
            )
        )
    if "provider_certification_reference_contracts_current" in blocker_gates:
        steps.append(
            _resolution_step(
                "recertify_provider_reference_contract_coverage",
                "provider_ledger",
                "Re-certify providers whose ledger records lack reference chart and method coverage evidence.",
                _provider_recertification_commands(repo_path, provider_ledger.get("reference_contract_failures", [])),
                provider_ledger.get("reference_contract_failures", []),
                66,
            )
        )
    if "provider_certification_command_fingerprints_current" in blocker_gates:
        steps.append(
            _resolution_step(
                "recertify_provider_command_fingerprints",
                "provider_ledger",
                "Re-certify providers whose ledger records lack external command and artifact fingerprints.",
                _provider_recertification_commands(repo_path, provider_ledger.get("command_fingerprint_failures", [])),
                provider_ledger.get("command_fingerprint_failures", []),
                67,
            )
        )
    if "provider_certification_receipts_current" in blocker_gates:
        commands = [f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --live"]
        if manifest_path:
            commands = [
                "python -m examples.mingli_5agents.cli --repo "
                f"{repo_path} production-readiness --manifest {manifest_path} --live"
            ]
        steps.append(
            _resolution_step(
                "check_provider_receipt_drift",
                "provider_drift",
                "Run live certification drift checks and resolve mismatched receipts.",
                commands,
                provider_drift.get("failures", []),
                70,
            )
        )
    if "release_manifest_ledger_integrity" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_release_manifest_ledger_integrity",
                "release_ledger",
                "Repair release manifest ledger hash-chain or receipt consistency failures.",
                [
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} release-ledger",
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} release-drift",
                ],
                release_ledger.get("failures", []),
                75,
            )
        )
    if "implemented_evidence_materialized" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_implemented_evidence_materialization",
                "capability_audit",
                "Repair missing implementation evidence paths or Python symbols before production.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} audit"],
                _evidence_materialization_failures(evidence_materialization),
                80,
            )
        )
    if "classical_source_refresh_ready" in blocker_gates:
        steps.append(
            _resolution_step(
                "configure_classical_source_refresh",
                "classical_sources",
                "Configure reviewed external classical-source manifests before production.",
                [
                    "set SEMAS_CLASSIC_SOURCE_LIST=path-to-source-list.json",
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} audit",
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --manifest <manifest.json>",
                ],
                classical_source_refresh.get("failures", []),
                82,
            )
        )
    if "classical_source_latest_refresh_receipt_present" in blocker_gates:
        steps.append(
            _resolution_step(
                "run_classical_source_refresh",
                "classical_sources",
                "Refresh reviewed classical-source manifests into the local corpus and record refresh_receipt.json.",
                [
                    "python -m examples.mingli_5agents.cli --repo "
                    f"{repo_path} classical-refresh --source-list <source-list.json>"
                ],
                _classical_latest_refresh_receipt_failures(classical_source_refresh, _read_classical_refresh_receipt(repo_path)),
                82,
            )
        )
    if "known_gap_resolution_plan_covered" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_known_gap_resolution_plan",
                "capability_audit",
                "Ensure every known gap has closure criteria, verification commands, and production gate IDs.",
                [
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} audit",
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --manifest <manifest.json>",
                ],
                [str(item.get("details", "")) for item in blockers if item.get("gate") == "known_gap_resolution_plan_covered"],
                83,
            )
        )
    if "blocked_capability_coverage_complete" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_blocked_capability_coverage",
                "capability_audit",
                "Map every false capability to a known gap or explicit optional-configuration policy.",
                [
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} audit",
                    f"python -m examples.mingli_5agents.cli --repo {repo_path} production-readiness --manifest <manifest.json>",
                ],
                [
                    str(item.get("details", ""))
                    for item in blockers
                    if item.get("gate") == "blocked_capability_coverage_complete"
                ],
                84,
            )
        )
    if "capability_audit_receipt_current" in blocker_gates:
        commands = [
            f"python -m examples.mingli_5agents.cli --repo {repo_path} audit",
            "python -m examples.mingli_5agents.cli --repo "
            f"{repo_path} production-readiness --expected-audit-receipt-sha256 <accepted_audit_receipt_sha256>",
        ]
        if manifest_path:
            commands[1] = (
                "python -m examples.mingli_5agents.cli --repo "
                f"{repo_path} production-readiness --manifest {manifest_path} "
                "--expected-audit-receipt-sha256 <accepted_audit_receipt_sha256>"
            )
        steps.append(
            _resolution_step(
                "review_capability_audit_receipt_drift",
                "capability_audit",
                "Review capability audit drift before accepting a new expected audit receipt.",
                commands,
                ["audit receipt sha256 does not match expected value"],
                85,
            )
        )
    if "current_benchmark_passed" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_current_benchmark_regressions",
                "benchmark",
                "Run the built-in benchmark and repair coordinator metric or reference-chart regressions.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_metric_floor_failures(current_benchmark)
                or [
                    f"passed_rate={current_benchmark.get('passed_rate')}",
                    f"reference_charts_passed={current_benchmark.get('reference_charts', {}).get('passed')}",
                    f"empirical_validation_status={current_benchmark.get('empirical_validation', {}).get('status')}",
                ],
                90,
            )
        )
    if "benchmark_birthplaces_geocoded" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_benchmark_birthplace_geocoding",
                "birth_profile",
                "Add deterministic birthplace geocoding for benchmark cases.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_birthplace_geocoding_failures(current_benchmark),
                95,
            )
        )
    if "benchmark_deliberation_receipts_bound" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_benchmark_deliberation_receipts",
                "workflow",
                "Restore deliberation receipts for every benchmark case before release.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_deliberation_receipt_failures(current_benchmark),
                96,
            )
        )
    if "benchmark_annual_timeline_receipts_bound" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_benchmark_annual_timeline_receipts",
                "annual_timeline",
                "Restore annual timeline receipts and request-provenance binding for every benchmark case.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_annual_timeline_receipt_failures(current_benchmark),
                97,
            )
        )
    if "benchmark_monthly_luck_receipts_bound" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_benchmark_monthly_luck_receipts",
                "monthly_luck",
                "Restore monthly luck receipts and request-provenance binding for every benchmark case.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_monthly_luck_receipt_failures(current_benchmark),
                98,
            )
        )
    if "benchmark_auspicious_calendar_receipts_bound" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_benchmark_auspicious_calendar_receipts",
                "auspicious_calendar",
                "Restore auspicious-calendar receipts and request-provenance binding for every benchmark case.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_auspicious_calendar_receipt_failures(current_benchmark),
                99,
            )
        )
    if "benchmark_external_payload_birth_matches" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_external_payload_birth_mismatches",
                "provider_payloads",
                "Regenerate or reject external professional payloads whose declared birth data differs from the request.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_external_payload_birth_match_failures(current_benchmark),
                100,
            )
        )
    if "benchmark_topic_confidence_boundaries" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_topic_confidence_boundaries",
                "topic_synthesis",
                "Restore topic-synthesis confidence summaries, downgrade reasons, and non-predictive boundaries.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_topic_confidence_failures(current_benchmark),
                100,
            )
        )
    if "benchmark_analyze_response_schema_valid" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_benchmark_analyze_response_schema",
                "schema_contract",
                "Repair analyze_case runtime output or the public schema so every benchmark AnalyzeResponse validates.",
                [f"python -m examples.mingli_5agents.cli --repo {repo_path} benchmark"],
                _benchmark_analyze_response_schema_failures(benchmark_analyze_response_schema),
                100,
            )
        )
    if "production_gate_registry_current" in blocker_gates:
        steps.append(
            _resolution_step(
                "repair_production_gate_registry",
                "governance",
                "Register every runtime production-readiness gate ID in the shared governance registry.",
                [
                    (
                        "python -c \"from examples.mingli_5agents.api_core import production_readiness; "
                        "print(production_readiness().get('production_gate_registry_audit', {}))\""
                    )
                ],
                ["Update examples/mingli_5agents/production_gates.py PRODUCTION_READINESS_GATE_IDS."],
                101,
            )
        )
    return {
        "status": "clear" if not steps else "actions_required",
        "step_count": len(steps),
        "steps": sorted(steps, key=lambda item: (item["priority"], item["id"])),
    }


def _evidence_materialization_failures(evidence_materialization: dict[str, Any]) -> list[str]:
    failures = []
    for requirement in evidence_materialization.get("requirements", []):
        if not isinstance(requirement, dict):
            continue
        requirement_id = str(requirement.get("id", "unknown"))
        for evidence in requirement.get("evidence", []):
            if isinstance(evidence, dict) and evidence.get("status") == "failed":
                failures.append(f"{requirement_id}: {evidence.get('evidence')} - {evidence.get('reason')}")
    return failures


def _benchmark_metric_floor_failures(benchmark_result: dict[str, Any]) -> list[str]:
    mean_metrics = benchmark_result.get("mean_metrics", {})
    if not isinstance(mean_metrics, dict):
        return ["benchmark mean_metrics missing"]
    failures = []
    for metric_name, floor in METRIC_FLOORS.items():
        value = float(mean_metrics.get(metric_name, 0.0) or 0.0)
        if value < floor:
            failures.append(f"{metric_name} below production floor {floor}: {value:.3f}")
    return failures


def _benchmark_birthplace_geocoding_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    for case in benchmark_result.get("cases", []):
        if not isinstance(case, dict):
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            continue
        if features.get("birthplace_geocoded") is not True:
            failures.append(
                f"{case.get('name')} birthplace geocoding unresolved: "
                f"{features.get('birthplace_geocoding_quality')}"
            )
    return failures


def _benchmark_deliberation_receipt_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    cases = benchmark_result.get("cases", [])
    if not isinstance(cases, list):
        return ["benchmark cases missing"]
    for case in cases:
        if not isinstance(case, dict):
            failures.append("benchmark case is not an object")
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            failures.append(f"{case.get('name')} report_features missing")
            continue
        receipt_sha = features.get("deliberation_receipt_sha256")
        claim_count = features.get("deliberation_claim_count")
        if features.get("deliberation_receipt_present") is not True:
            failures.append(f"{case.get('name')} deliberation receipt missing")
        elif not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
            failures.append(f"{case.get('name')} deliberation receipt sha256 invalid")
        elif not isinstance(claim_count, int) or claim_count <= 0:
            failures.append(f"{case.get('name')} deliberation claim count invalid: {claim_count}")
    return failures


def _benchmark_annual_timeline_receipt_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    cases = benchmark_result.get("cases", [])
    if not isinstance(cases, list):
        return ["benchmark cases missing"]
    for case in cases:
        if not isinstance(case, dict):
            failures.append("benchmark case is not an object")
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            failures.append(f"{case.get('name')} report_features missing")
            continue
        receipt_sha = features.get("annual_timeline_receipt_sha256")
        row_count = features.get("annual_timeline_row_count")
        if features.get("annual_timeline_receipt_present") is not True:
            failures.append(f"{case.get('name')} annual timeline receipt missing")
        elif not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
            failures.append(f"{case.get('name')} annual timeline receipt sha256 invalid")
        elif not isinstance(row_count, int) or row_count <= 0:
            failures.append(f"{case.get('name')} annual timeline row count invalid: {row_count}")
        elif features.get("annual_timeline_receipt_bound_to_provenance") is not True:
            failures.append(f"{case.get('name')} annual timeline receipt is not bound to request provenance")
    return failures


def _benchmark_monthly_luck_receipt_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    cases = benchmark_result.get("cases", [])
    if not isinstance(cases, list):
        return ["benchmark cases missing"]
    for case in cases:
        if not isinstance(case, dict):
            failures.append("benchmark case is not an object")
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            failures.append(f"{case.get('name')} report_features missing")
            continue
        receipt_sha = features.get("monthly_luck_receipt_sha256")
        row_count = features.get("monthly_luck_row_count")
        if features.get("monthly_luck_receipt_present") is not True:
            failures.append(f"{case.get('name')} monthly luck receipt missing")
        elif not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
            failures.append(f"{case.get('name')} monthly luck receipt sha256 invalid")
        elif not isinstance(row_count, int) or row_count <= 0:
            failures.append(f"{case.get('name')} monthly luck row count invalid: {row_count}")
        elif features.get("monthly_luck_receipt_bound_to_provenance") is not True:
            failures.append(f"{case.get('name')} monthly luck receipt is not bound to request provenance")
    return failures


def _benchmark_auspicious_calendar_receipt_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    cases = benchmark_result.get("cases", [])
    if not isinstance(cases, list):
        return ["benchmark cases missing"]
    for case in cases:
        if not isinstance(case, dict):
            failures.append("benchmark case is not an object")
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            failures.append(f"{case.get('name')} report_features missing")
            continue
        receipt_sha = features.get("auspicious_calendar_receipt_sha256")
        row_count = features.get("auspicious_calendar_row_count")
        if features.get("auspicious_calendar_receipt_present") is not True:
            failures.append(f"{case.get('name')} auspicious-calendar receipt missing")
        elif not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
            failures.append(f"{case.get('name')} auspicious-calendar receipt sha256 invalid")
        elif not isinstance(row_count, int) or row_count <= 0:
            failures.append(f"{case.get('name')} auspicious-calendar row count invalid: {row_count}")
        elif features.get("auspicious_calendar_receipt_bound_to_provenance") is not True:
            failures.append(f"{case.get('name')} auspicious-calendar receipt is not bound to request provenance")
    return failures


def _benchmark_external_payload_birth_match_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    for case in benchmark_result.get("cases", []):
        if not isinstance(case, dict):
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            continue
        mismatch_domains = features.get("external_payload_birth_mismatch_domains", [])
        if not isinstance(mismatch_domains, list) or not mismatch_domains:
            continue
        failures.append(
            f"{case.get('name')} external payload birth mismatch domains="
            + ",".join(str(domain) for domain in mismatch_domains)
        )
    return failures


def _benchmark_topic_confidence_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    for case in benchmark_result.get("cases", []):
        if not isinstance(case, dict):
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            failures.append(f"{case.get('name')} report_features missing")
            continue
        summary = features.get("topic_confidence_summary")
        if not isinstance(summary, dict):
            failures.append(f"{case.get('name')} topic confidence summary missing")
            continue
        if features.get("topic_confidence_boundaries_ok") is not True:
            failures.append(f"{case.get('name')} topic confidence boundaries missing or invalid")
        missing_topics = features.get("topic_confidence_missing_topics", [])
        if isinstance(missing_topics, list) and missing_topics:
            failures.append(
                f"{case.get('name')} topic confidence missing topics="
                + ",".join(str(item) for item in missing_topics)
            )
        levels = features.get("topic_confidence_levels", {})
        if not isinstance(levels, dict) or len(levels) < 8:
            failures.append(f"{case.get('name')} topic confidence levels incomplete")
    return failures


def _benchmark_chinese_render_quality_failures(benchmark_result: dict[str, Any]) -> list[str]:
    failures = []
    cases = benchmark_result.get("cases", [])
    if not isinstance(cases, list):
        return ["benchmark cases missing"]
    for case in cases:
        if not isinstance(case, dict):
            failures.append("benchmark case is not an object")
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            failures.append(f"{case.get('name')} report_features missing")
            continue
        if features.get("has_chinese_render") is not True:
            continue
        duplicate_ratio = float(features.get("chinese_render_duplicate_bullet_ratio", 1.0) or 0.0)
        anchor_ratio = float(features.get("chinese_render_topic_evidence_anchor_ratio", 0.0) or 0.0)
        judgment_ratio = float(features.get("chinese_render_topic_judgment_structure_ratio", 0.0) or 0.0)
        ascii_count = int(features.get("chinese_render_ascii_letter_count", 0) or 0)
        if duplicate_ratio > 0.02:
            failures.append(f"{case.get('name')} Chinese annual/monthly duplicate ratio={duplicate_ratio:.3f}")
        if anchor_ratio < 1.0:
            failures.append(f"{case.get('name')} Chinese annual/monthly evidence-anchor ratio={anchor_ratio:.3f}")
        if judgment_ratio < 1.0:
            failures.append(f"{case.get('name')} Chinese annual/monthly judgment-structure ratio={judgment_ratio:.3f}")
        if ascii_count != 0:
            failures.append(f"{case.get('name')} Chinese render ASCII letter count={ascii_count}")
        if features.get("chinese_render_ascii_question_present") is True:
            failures.append(f"{case.get('name')} Chinese render contains ASCII question mark")
        if features.get("chinese_render_code_marker_present") is True:
            failures.append(f"{case.get('name')} Chinese render contains code or provider command marker")
    return failures


def _benchmark_analyze_response_schema_audit(repo_path: Path, *, version: int | None = None) -> dict[str, Any]:
    """Validate full analyze_case responses for built-in benchmark cases."""
    cache_key: tuple[str, int] | None = None
    if version is not None:
        cache_key = (str(Path(repo_path).resolve()), int(version))
        cached = _BENCHMARK_ANALYZE_RESPONSE_SCHEMA_CACHE.get(cache_key)
        if isinstance(cached, dict):
            return json.loads(json.dumps(cached, ensure_ascii=False))
    case_results = []
    for case in benchmark_cases():
        response = analyze_case(repo_path, case["input"], case.get("expected"))
        json_response = json.loads(json.dumps(response, ensure_ascii=False))
        errors = schema_validation_errors(json_response, schema_name="AnalyzeResponse")
        schema_validation = json_response.get("schema_validation", {})
        declared_valid = isinstance(schema_validation, dict) and schema_validation.get("valid") is True
        valid = not errors and declared_valid
        case_results.append(
            {
                "case": str(case.get("name")),
                "schema_name": "AnalyzeResponse",
                "valid": valid,
                "declared_valid": declared_valid,
                "error_count": len(errors),
                "errors_sample": errors[:10],
            }
        )
    invalid_cases = [item for item in case_results if item.get("valid") is not True]
    audit = {
        "schema_name": "AnalyzeResponse",
        "case_count": len(case_results),
        "valid_count": len(case_results) - len(invalid_cases),
        "coverage_complete": not invalid_cases and bool(case_results),
        "invalid_cases": invalid_cases,
        "cases": case_results,
    }
    if cache_key is not None:
        _BENCHMARK_ANALYZE_RESPONSE_SCHEMA_CACHE[cache_key] = json.loads(json.dumps(audit, ensure_ascii=False))
    return audit


def _benchmark_analyze_response_schema_failures(schema_audit: dict[str, Any]) -> list[str]:
    if not isinstance(schema_audit, dict):
        return ["benchmark AnalyzeResponse schema audit missing"]
    failures = []
    if schema_audit.get("coverage_complete") is not True:
        failures.append(
            f"AnalyzeResponse schema coverage incomplete: "
            f"{schema_audit.get('valid_count')}/{schema_audit.get('case_count')} valid"
        )
    invalid_cases = schema_audit.get("invalid_cases", [])
    if not isinstance(invalid_cases, list):
        return failures + ["AnalyzeResponse schema invalid_cases is not a list"]
    for item in invalid_cases:
        if not isinstance(item, dict):
            failures.append("AnalyzeResponse schema invalid case is not an object")
            continue
        sample = item.get("errors_sample", [])
        first_error = sample[0] if isinstance(sample, list) and sample else "unknown schema error"
        failures.append(f"{item.get('case')} AnalyzeResponse schema invalid: {first_error}")
    return failures


def _birth_profile_import_preview_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = readiness.get("birth_profile_import_preview_summary", {}) if isinstance(readiness, dict) else {}
    return summary if isinstance(summary, dict) else {}


def _birth_profile_source_review_workplan_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = (
        readiness.get("birth_profile_source_review_workplan_summary", {}) if isinstance(readiness, dict) else {}
    )
    return summary if isinstance(summary, dict) else {}


def _birth_profile_source_lookup_plan_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = readiness.get("birth_profile_source_lookup_plan_summary", {}) if isinstance(readiness, dict) else {}
    return summary if isinstance(summary, dict) else {}


def _birth_profile_source_cache_template_preview_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = (
        readiness.get("birth_profile_source_cache_template_preview_summary", {})
        if isinstance(readiness, dict)
        else {}
    )
    return summary if isinstance(summary, dict) else {}


def _birth_profile_source_family_cache_enforcement_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = (
        readiness.get("birth_profile_source_family_cache_enforcement_summary", {})
        if isinstance(readiness, dict)
        else {}
    )
    return summary if isinstance(summary, dict) else {}


def _birth_profile_substantive_evidence_cache_enforcement_summary_from_audit(
    audit: dict[str, Any],
) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = (
        readiness.get("birth_profile_substantive_evidence_cache_enforcement_summary", {})
        if isinstance(readiness, dict)
        else {}
    )
    return summary if isinstance(summary, dict) else {}


def _birth_profile_source_cache_audit_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = readiness.get("birth_profile_source_cache_audit_summary", {}) if isinstance(readiness, dict) else {}
    return summary if isinstance(summary, dict) else {}


def _birth_profile_reviewed_manifest_draft_preview_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = (
        readiness.get("birth_profile_reviewed_manifest_draft_preview_summary", {})
        if isinstance(readiness, dict)
        else {}
    )
    return summary if isinstance(summary, dict) else {}


def _birth_profile_fixture_patch_preview_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    fixture = audit.get("industry_event_cross_domain_fixture_import", {})
    material = fixture.get("material", {}) if isinstance(fixture, dict) else {}
    readiness = material.get("symbolic_scoring_readiness_summary", {}) if isinstance(material, dict) else {}
    summary = (
        readiness.get("birth_profile_fixture_patch_preview_summary", {}) if isinstance(readiness, dict) else {}
    )
    return summary if isinstance(summary, dict) else {}


def _birth_profile_import_preview_blocked(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "blocked_not_ready_for_import"
        and summary.get("valid") is True
        and summary.get("would_write_file") is False
        and summary.get("import_allowed") is False
        and summary.get("import_gate_passed") is False
        and summary.get("integrity_check_status") == "passed"
        and int(summary.get("blocked_request_count", 0)) > 0
        and int(summary.get("import_ready_request_count", -1)) == 0
    )


def _birth_profile_import_preview_blocker_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile import preview summary is missing from capability audit"]
    if summary.get("status") != "blocked_not_ready_for_import":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("preview summary is not valid")
    if summary.get("would_write_file") is not False:
        failures.append("preview would write a file")
    if summary.get("import_allowed") is not False:
        failures.append("preview allows import")
    if summary.get("import_gate_passed") is not False:
        failures.append("preview import gate is not blocked")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    if int(summary.get("blocked_request_count", 0)) <= 0:
        failures.append("blocked_request_count is not positive")
    if int(summary.get("import_ready_request_count", -1)) != 0:
        failures.append(f"import_ready_request_count={summary.get('import_ready_request_count')}")
    return failures


def _birth_profile_source_review_workplan_available(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "ready_for_human_source_review"
        and summary.get("valid") is True
        and summary.get("would_fetch_live_sources") is False
        and summary.get("would_write_review_manifest") is False
        and int(summary.get("request_count", 0)) > 0
        and int(summary.get("work_item_count", 0)) > 0
        and summary.get("source_review_gate_passed") is False
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_source_review_workplan_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile source-review workplan summary is missing from capability audit"]
    if summary.get("status") != "ready_for_human_source_review":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("source-review workplan summary is not valid")
    if summary.get("would_fetch_live_sources") is not False:
        failures.append("source-review workplan would fetch live sources")
    if summary.get("would_write_review_manifest") is not False:
        failures.append("source-review workplan would write a reviewed manifest")
    if int(summary.get("request_count", 0)) <= 0:
        failures.append("request_count is not positive")
    if int(summary.get("work_item_count", 0)) <= 0:
        failures.append("work_item_count is not positive")
    if summary.get("source_review_gate_passed") is not False:
        failures.append("source-review workplan gate unexpectedly passed")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _birth_profile_source_lookup_plan_dry_run(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "ready_for_manual_lookup"
        and summary.get("valid") is True
        and summary.get("would_fetch_live_sources") is False
        and summary.get("would_write_cache") is False
        and summary.get("would_write_review_manifest") is False
        and int(summary.get("lookup_item_count", 0)) > 0
        and int(summary.get("query_count", 0)) > 0
        and summary.get("lookup_gate_passed") is False
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_source_lookup_plan_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile source lookup plan summary is missing from capability audit"]
    if summary.get("status") != "ready_for_manual_lookup":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("source lookup plan summary is not valid")
    if summary.get("would_fetch_live_sources") is not False:
        failures.append("source lookup plan would fetch live sources")
    if summary.get("would_write_cache") is not False:
        failures.append("source lookup plan would write cache files")
    if summary.get("would_write_review_manifest") is not False:
        failures.append("source lookup plan would write a reviewed manifest")
    if int(summary.get("lookup_item_count", 0)) <= 0:
        failures.append("lookup_item_count is not positive")
    if int(summary.get("query_count", 0)) <= 0:
        failures.append("query_count is not positive")
    if summary.get("lookup_gate_passed") is not False:
        failures.append("source lookup gate unexpectedly passed")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _birth_profile_source_family_catalog_bound(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "ready_for_manual_lookup"
        and summary.get("valid") is True
        and int(summary.get("source_family_count", 0)) >= 5
        and summary.get("source_family_catalog_bound") is True
        and summary.get("birth_time_source_policy_bound") is True
        and summary.get("identity_anchor_birth_time_disallowed") is True
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_source_family_catalog_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile source lookup plan summary is missing from capability audit"]
    if summary.get("status") != "ready_for_manual_lookup":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("source lookup plan summary is not valid")
    if int(summary.get("source_family_count", 0)) < 5:
        failures.append(f"source_family_count={summary.get('source_family_count')}")
    if summary.get("source_family_catalog_bound") is not True:
        failures.append("source family catalog is not bound to the lookup plan")
    if summary.get("birth_time_source_policy_bound") is not True:
        failures.append("birth-time queries are not bound to rated birth-time source policy")
    if summary.get("identity_anchor_birth_time_disallowed") is not True:
        failures.append("identity/domain anchors are not explicitly barred from satisfying birth_time")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _birth_profile_source_cache_template_preview_non_mutating(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "ready_for_manual_cache_fill"
        and summary.get("valid") is True
        and summary.get("would_fetch_live_sources") is False
        and summary.get("would_write_cache") is False
        and summary.get("would_import_profiles") is False
        and int(summary.get("template_count", 0)) > 0
        and summary.get("template_preview_gate_passed") is False
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_source_cache_template_preview_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile source cache template preview summary is missing from capability audit"]
    if summary.get("status") != "ready_for_manual_cache_fill":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("source cache template preview summary is not valid")
    if summary.get("would_fetch_live_sources") is not False:
        failures.append("source cache template preview would fetch live sources")
    if summary.get("would_write_cache") is not False:
        failures.append("source cache template preview would write cache files")
    if summary.get("would_import_profiles") is not False:
        failures.append("source cache template preview would import profiles")
    if int(summary.get("template_count", 0)) <= 0:
        failures.append("template_count is not positive")
    if summary.get("template_preview_gate_passed") is not False:
        failures.append("source cache template preview gate unexpectedly passed")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _birth_profile_source_family_cache_enforcement_probe_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "passed"
        and summary.get("valid") is True
        and summary.get("probe_executed") is True
        and summary.get("identity_anchor_birth_time_rejected") is True
        and summary.get("accepted_cache_count_after_probe") == 0
        and summary.get("probe_source_family_id") == "wikidata_identity_anchor"
        and summary.get("failure_contains_birth_time_policy") is True
    )


def _birth_profile_source_family_cache_enforcement_probe_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile source-family cache enforcement probe summary is missing from capability audit"]
    if summary.get("status") != "passed":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("source-family cache enforcement probe is not valid")
    if summary.get("probe_executed") is not True:
        failures.append("source-family cache enforcement probe did not execute")
    if summary.get("identity_anchor_birth_time_rejected") is not True:
        failures.append("identity-anchor birth_time payload was not rejected")
    if summary.get("accepted_cache_count_after_probe") != 0:
        failures.append(f"accepted_cache_count_after_probe={summary.get('accepted_cache_count_after_probe')}")
    if summary.get("probe_source_family_id") != "wikidata_identity_anchor":
        failures.append(f"probe_source_family_id={summary.get('probe_source_family_id')}")
    if summary.get("failure_contains_birth_time_policy") is not True:
        failures.append("birth_time source-family policy failure was not observed")
    failures.extend(str(item) for item in summary.get("failures", []) if item)
    return failures


def _birth_profile_substantive_evidence_cache_enforcement_probe_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "passed"
        and summary.get("valid") is True
        and summary.get("probe_executed") is True
        and summary.get("metadata_only_reviewed_cache_rejected") is True
        and summary.get("accepted_cache_count_after_probe") == 0
        and summary.get("probe_source_family_id") == "rated_birth_time_source"
        and summary.get("failure_contains_substantive_birth_policy") is True
    )


def _birth_profile_substantive_evidence_cache_enforcement_probe_failures(
    summary: dict[str, Any],
) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile substantive-evidence cache enforcement probe summary is missing from capability audit"]
    if summary.get("status") != "passed":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("substantive-evidence cache enforcement probe is not valid")
    if summary.get("probe_executed") is not True:
        failures.append("substantive-evidence cache enforcement probe did not execute")
    if summary.get("metadata_only_reviewed_cache_rejected") is not True:
        failures.append("reviewed metadata-only cache payload was not rejected")
    if summary.get("accepted_cache_count_after_probe") != 0:
        failures.append(f"accepted_cache_count_after_probe={summary.get('accepted_cache_count_after_probe')}")
    if summary.get("probe_source_family_id") != "rated_birth_time_source":
        failures.append(f"probe_source_family_id={summary.get('probe_source_family_id')}")
    if summary.get("failure_contains_substantive_birth_policy") is not True:
        failures.append("substantive birth evidence policy failure was not observed")
    failures.extend(str(item) for item in summary.get("failures", []) if item)
    return failures


def _birth_profile_source_cache_audit_read_only(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") in {"waiting_for_manual_cache", "cache_present_requires_review", "cache_ready_for_reviewed_manifest_draft"}
        and summary.get("valid") is True
        and summary.get("would_fetch_live_sources") is False
        and summary.get("would_write_cache") is False
        and summary.get("would_write_review_manifest") is False
        and summary.get("would_import_profiles") is False
        and int(summary.get("expected_cache_count", 0)) > 0
        and summary.get("cache_audit_gate_passed") is False
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_source_cache_audit_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile source cache audit summary is missing from capability audit"]
    if summary.get("status") not in {
        "waiting_for_manual_cache",
        "cache_present_requires_review",
        "cache_ready_for_reviewed_manifest_draft",
    }:
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("source cache audit summary is not valid")
    if summary.get("would_fetch_live_sources") is not False:
        failures.append("source cache audit would fetch live sources")
    if summary.get("would_write_cache") is not False:
        failures.append("source cache audit would write cache files")
    if summary.get("would_write_review_manifest") is not False:
        failures.append("source cache audit would write a reviewed manifest")
    if summary.get("would_import_profiles") is not False:
        failures.append("source cache audit would import profiles")
    if int(summary.get("expected_cache_count", 0)) <= 0:
        failures.append("expected_cache_count is not positive")
    if summary.get("cache_audit_gate_passed") is not False:
        failures.append("source cache audit gate unexpectedly passed")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _birth_profile_reviewed_manifest_draft_preview_non_mutating(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") in {"blocked_waiting_for_complete_source_cache", "ready_for_human_approval"}
        and summary.get("valid") is True
        and summary.get("would_write_review_manifest") is False
        and summary.get("would_import_profiles") is False
        and int(summary.get("review_request_count", 0)) > 0
        and summary.get("draft_gate_passed") is False
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_reviewed_manifest_draft_preview_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile reviewed manifest draft preview summary is missing from capability audit"]
    if summary.get("status") not in {"blocked_waiting_for_complete_source_cache", "ready_for_human_approval"}:
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("reviewed manifest draft preview summary is not valid")
    if summary.get("would_write_review_manifest") is not False:
        failures.append("reviewed manifest draft preview would write a reviewed manifest")
    if summary.get("would_import_profiles") is not False:
        failures.append("reviewed manifest draft preview would import profiles")
    if int(summary.get("review_request_count", 0)) <= 0:
        failures.append("review_request_count is not positive")
    if summary.get("draft_gate_passed") is not False:
        failures.append("reviewed manifest draft gate unexpectedly passed")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _birth_profile_fixture_patch_preview_blocked(summary: dict[str, Any]) -> bool:
    return (
        summary.get("status") == "blocked_not_ready_for_patch_preview"
        and summary.get("valid") is True
        and summary.get("would_write_file") is False
        and summary.get("patch_ready_for_review") is False
        and int(summary.get("candidate_count", -1)) == 0
        and summary.get("patch_gate_passed") is False
        and isinstance(summary.get("target_file_sha256"), str)
        and len(str(summary.get("target_file_sha256"))) == 64
        and isinstance(summary.get("patch_text_sha256"), str)
        and len(str(summary.get("patch_text_sha256"))) == 64
        and summary.get("integrity_check_status") == "passed"
    )


def _birth_profile_fixture_patch_preview_blocker_failures(summary: dict[str, Any]) -> list[str]:
    failures = []
    if not summary:
        return ["birth profile fixture patch preview summary is missing from capability audit"]
    if summary.get("status") != "blocked_not_ready_for_patch_preview":
        failures.append(f"status={summary.get('status')}")
    if summary.get("valid") is not True:
        failures.append("fixture patch preview summary is not valid")
    if summary.get("would_write_file") is not False:
        failures.append("fixture patch preview would write a file")
    if summary.get("patch_ready_for_review") is not False:
        failures.append("fixture patch preview is ready for review before birth-profile review completion")
    if int(summary.get("candidate_count", -1)) != 0:
        failures.append(f"candidate_count={summary.get('candidate_count')}")
    if summary.get("patch_gate_passed") is not False:
        failures.append("fixture patch preview gate is not blocked")
    if not isinstance(summary.get("target_file_sha256"), str) or len(str(summary.get("target_file_sha256"))) != 64:
        failures.append("target_file_sha256 is missing or invalid")
    if not isinstance(summary.get("patch_text_sha256"), str) or len(str(summary.get("patch_text_sha256"))) != 64:
        failures.append("patch_text_sha256 is missing or invalid")
    if summary.get("integrity_check_status") != "passed":
        failures.append(f"integrity_check_status={summary.get('integrity_check_status')}")
    return failures


def _production_readiness_receipt(response: dict[str, Any]) -> dict[str, Any]:
    """Return a stable receipt for comparing production-readiness results."""
    benchmark = response.get("current_benchmark", {})
    benchmark_schema = response.get("benchmark_analyze_response_schema", {})
    evidence = response.get("evidence_materialization", {})
    provider_ledger = response.get("provider_certification_ledger", {})
    provider_drift = response.get("provider_certification_drift", {})
    audit_receipt = response.get("capability_audit_receipt", {})
    outcome_response = response.get("outcome_dataset", {})
    outcome_audit = outcome_response.get("audit", {}) if isinstance(outcome_response, dict) else {}
    outcome_receipt = (
        outcome_response.get("outcome_dataset_receipt", {}) if isinstance(outcome_response, dict) else {}
    )
    classical_source_refresh = response.get("classical_source_refresh", {})
    classical_refresh_receipt = response.get("classical_refresh_receipt")
    known_gap_handoff_bundle = response.get("known_gap_handoff_bundle", {})
    material = {
        "schema_version": 1,
        "status": response.get("status"),
        "production_ready": response.get("production_ready"),
        "live_requested": response.get("live_requested"),
        "manifest_path": response.get("manifest_path"),
        "classical_source_list_path": response.get("classical_source_list_path"),
        "gates": [
            {
                "id": gate.get("id"),
                "passed": gate.get("passed"),
                "reason": gate.get("reason"),
                "failure_reason": gate.get("failure_reason"),
                "details": gate.get("details", []),
            }
            for gate in response.get("gates", [])
            if isinstance(gate, dict)
        ],
        "blocker_gates": [blocker.get("gate") for blocker in response.get("blockers", []) if isinstance(blocker, dict)],
        "current_benchmark": {
            "genome_version": benchmark.get("genome_version"),
            "candidate_name": benchmark.get("candidate_name"),
            "passed_rate": benchmark.get("passed_rate"),
            "average_score": benchmark.get("average_score"),
            "mean_metrics": benchmark.get("mean_metrics", {}),
            "birth_profile_audit": _benchmark_birth_profile_audit(benchmark),
            "request_provenance_audit": _benchmark_request_provenance_audit(benchmark),
            "provider_action_plan_audit": _benchmark_provider_action_plan_audit(benchmark),
            "topic_confidence_audit": _benchmark_topic_confidence_audit(benchmark),
            "analyze_response_schema_audit": _benchmark_analyze_response_schema_receipt_summary(benchmark_schema),
            "reference_charts_passed": benchmark.get("reference_charts", {}).get("passed")
            if isinstance(benchmark.get("reference_charts"), dict)
            else None,
            "empirical_validation_status": benchmark.get("empirical_validation", {}).get("status")
            if isinstance(benchmark.get("empirical_validation"), dict)
            else None,
            "reproducibility_manifest": benchmark.get("reproducibility_manifest", {}),
        },
        "evidence_materialization": {
            "status": evidence.get("status"),
            "total_evidence": evidence.get("total_evidence"),
            "passed_count": evidence.get("passed_count"),
            "failed_count": evidence.get("failed_count"),
            "unchecked_count": evidence.get("unchecked_count"),
        },
        "capability_audit_receipt": {
            "schema_version": audit_receipt.get("schema_version") if isinstance(audit_receipt, dict) else None,
            "sha256": audit_receipt.get("sha256") if isinstance(audit_receipt, dict) else None,
            "matches_expected": response.get("audit_receipt_matches_expected"),
        },
        "classical_source_refresh": {
            "status": classical_source_refresh.get("status") if isinstance(classical_source_refresh, dict) else None,
            "valid": classical_source_refresh.get("valid") if isinstance(classical_source_refresh, dict) else None,
            "source_count": classical_source_refresh.get("source_count") if isinstance(classical_source_refresh, dict) else None,
            "locked_source_count": classical_source_refresh.get("locked_source_count")
            if isinstance(classical_source_refresh, dict)
            else None,
            "content_hash": classical_source_refresh.get("content_hash") if isinstance(classical_source_refresh, dict) else None,
            "source_list_receipt_sha256": classical_source_refresh.get("source_list_receipt", {}).get("sha256")
            if isinstance(classical_source_refresh, dict)
            and isinstance(classical_source_refresh.get("source_list_receipt"), dict)
            else None,
            "source_list_receipt_material_sha256": _receipt_material_sha256(
                classical_source_refresh.get("source_list_receipt", {})
            )
            if isinstance(classical_source_refresh, dict)
            else None,
            "latest_refresh_receipt_sha256": classical_refresh_receipt.get("sha256")
            if isinstance(classical_refresh_receipt, dict)
            else None,
            "latest_refresh_record_count": classical_refresh_receipt.get("material", {}).get("record_count")
            if isinstance(classical_refresh_receipt, dict)
            and isinstance(classical_refresh_receipt.get("material"), dict)
            else None,
            "failures": classical_source_refresh.get("failures", []) if isinstance(classical_source_refresh, dict) else [],
        },
        "provider_certification_ledger": {
            "integrity_status": provider_ledger.get("integrity_status"),
            "coverage_status": provider_ledger.get("coverage_status"),
            "protocol_status": provider_ledger.get("protocol_status"),
            "request_receipt_status": provider_ledger.get("request_receipt_status"),
            "reference_contract_status": provider_ledger.get("reference_contract_status"),
            "command_fingerprint_status": provider_ledger.get("command_fingerprint_status"),
            "record_count": provider_ledger.get("record_count"),
            "latest_record_hash": provider_ledger.get("latest_record_hash"),
            "latest_record_index": provider_ledger.get("latest_record_index"),
            "missing_domains": provider_ledger.get("missing_domains", []),
            "request_receipt_failures": provider_ledger.get("request_receipt_failures", []),
            "reference_contract_failures": provider_ledger.get("reference_contract_failures", []),
            "command_fingerprint_failures": provider_ledger.get("command_fingerprint_failures", []),
        },
        "provider_certification_drift": {
            "status": provider_drift.get("status"),
            "passed": provider_drift.get("passed"),
            "checked_domains": provider_drift.get("checked_domains", []),
            "failures": provider_drift.get("failures", []),
        },
        "outcome_dataset_receipt_sha256": outcome_receipt.get("sha256")
        if isinstance(outcome_receipt, dict)
        else None,
        "outcome_dataset": _outcome_dataset_receipt_material(outcome_audit),
        "history_integrity_status": response.get("history_integrity", {}).get("status")
        if isinstance(response.get("history_integrity"), dict)
        else None,
        "archive_integrity_status": response.get("archive_integrity", {}).get("status")
        if isinstance(response.get("archive_integrity"), dict)
        else None,
        "known_gap_ids": response.get("known_gap_ids", []),
        "known_gap_handoff_bundle": known_gap_handoff_bundle if isinstance(known_gap_handoff_bundle, dict) else {},
        "known_gap_resolution_plan_coverage": _known_gap_resolution_plan_coverage_from_response(response),
        "production_resolution_plan_summary": _production_resolution_plan_summary(response.get("resolution_plan", {})),
        "production_gate_registry_audit": response.get("production_gate_registry_audit", {}),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _benchmark_birth_profile_audit(benchmark: Any) -> dict[str, Any]:
    cases = benchmark.get("cases", []) if isinstance(benchmark, dict) else []
    fingerprints = []
    covered = 0
    geocoded = 0
    unresolved = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            continue
        if features.get("birth_profile_present") is True:
            covered += 1
        if features.get("birthplace_geocoded") is True:
            geocoded += 1
        else:
            unresolved.append({"case": case.get("name"), "quality": features.get("birthplace_geocoding_quality")})
        fingerprint = features.get("birth_profile_fingerprint")
        if isinstance(fingerprint, str) and fingerprint:
            fingerprints.append({"case": case.get("name"), "sha256": fingerprint})
    return {
        "case_count": len([case for case in cases if isinstance(case, dict)]),
        "covered_count": covered,
        "geocoded_count": geocoded,
        "unresolved_geocoding": unresolved,
        "fingerprints": fingerprints,
    }


def _benchmark_topic_confidence_audit(benchmark: Any) -> dict[str, Any]:
    cases = benchmark.get("cases", []) if isinstance(benchmark, dict) else []
    covered = 0
    boundary_failures = []
    missing_topics: dict[str, list[str]] = {}
    downgrade_reasons: set[str] = set()
    level_counts: dict[str, int] = {}
    normalized_cases = [case for case in cases if isinstance(case, dict)]
    for case in normalized_cases:
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            continue
        summary = features.get("topic_confidence_summary")
        if isinstance(summary, dict):
            covered += 1
            reasons = summary.get("downgrade_reasons", [])
            if isinstance(reasons, list):
                downgrade_reasons.update(str(reason) for reason in reasons)
        if features.get("topic_confidence_boundaries_ok") is not True:
            boundary_failures.append(str(case.get("name")))
        case_missing = features.get("topic_confidence_missing_topics", [])
        if isinstance(case_missing, list) and case_missing:
            missing_topics[str(case.get("name"))] = [str(item) for item in case_missing]
        levels = features.get("topic_confidence_levels", {})
        if isinstance(levels, dict):
            for level in levels.values():
                key = str(level)
                level_counts[key] = level_counts.get(key, 0) + 1
    return {
        "case_count": len(normalized_cases),
        "covered_count": covered,
        "coverage_complete": bool(normalized_cases)
        and covered == len(normalized_cases)
        and not boundary_failures
        and not missing_topics,
        "boundary_failures": boundary_failures,
        "missing_topics": missing_topics,
        "downgrade_reasons": sorted(downgrade_reasons),
        "level_counts": level_counts,
    }


def _benchmark_analyze_response_schema_receipt_summary(schema_audit: Any) -> dict[str, Any]:
    if not isinstance(schema_audit, dict):
        return {
            "schema_name": "AnalyzeResponse",
            "case_count": 0,
            "valid_count": 0,
            "coverage_complete": False,
            "invalid_cases": [],
        }
    invalid_cases = []
    for item in schema_audit.get("invalid_cases", []):
        if not isinstance(item, dict):
            continue
        errors_sample = item.get("errors_sample", [])
        first_error = errors_sample[0] if isinstance(errors_sample, list) and errors_sample else ""
        invalid_cases.append(
            {
                "case": str(item.get("case")),
                "error_count": int(item.get("error_count", 0) or 0),
                "first_error": str(first_error),
            }
        )
    return {
        "schema_name": str(schema_audit.get("schema_name") or "AnalyzeResponse"),
        "case_count": int(schema_audit.get("case_count", 0) or 0),
        "valid_count": int(schema_audit.get("valid_count", 0) or 0),
        "coverage_complete": schema_audit.get("coverage_complete") is True,
        "invalid_cases": invalid_cases,
    }


def _known_gap_resolution_plan_coverage_from_response(response: dict[str, Any]) -> dict[str, Any]:
    known_gap_ids = [str(item) for item in response.get("known_gap_ids", [])]
    plan_items = response.get("known_gap_resolution_plan", [])
    if not isinstance(plan_items, list):
        plan_items = []
    normalized = [item for item in plan_items if isinstance(item, dict)]
    command_coverage = known_gap_verification_command_coverage(normalized)
    plan_by_gap = {_known_gap_plan_item_id(item): item for item in normalized if _known_gap_plan_item_id(item)}
    missing_gap_ids = [gap_id for gap_id in known_gap_ids if gap_id not in plan_by_gap]
    invalid_plan_gap_ids = []
    invalid_gate_ids_by_gap: dict[str, list[str]] = {}
    command_counts = {}
    gate_counts = {}
    for gap_id in known_gap_ids:
        item = plan_by_gap.get(gap_id)
        if not isinstance(item, dict):
            continue
        commands = item.get("verification_commands", [])
        gates = item.get("production_gate_ids", [])
        command_count = len(commands) if isinstance(commands, list) else 0
        gate_count = len(gates) if isinstance(gates, list) else 0
        command_counts[gap_id] = command_count
        gate_counts[gap_id] = gate_count
        invalid_gate_ids = (
            sorted({str(gate) for gate in gates if str(gate) not in PRODUCTION_READINESS_GATE_IDS})
            if isinstance(gates, list)
            else []
        )
        if invalid_gate_ids:
            invalid_gate_ids_by_gap[gap_id] = invalid_gate_ids
        if (
            item.get("status") != "open"
            or command_count <= 0
            or gate_count <= 0
            or invalid_gate_ids
            or gap_id in command_coverage.get("invalid_verification_commands_by_gap", {})
            or gap_id in command_coverage.get("invalid_verification_options_by_gap", {})
        ):
            invalid_plan_gap_ids.append(gap_id)
    covered_count = len(known_gap_ids) - len(missing_gap_ids) - len(invalid_plan_gap_ids)
    material = {
        "known_gap_ids": known_gap_ids,
        "planned_gap_ids": sorted(plan_by_gap),
        "command_counts": command_counts,
        "gate_counts": gate_counts,
        "invalid_gate_ids_by_gap": invalid_gate_ids_by_gap,
        "invalid_verification_commands_by_gap": command_coverage.get("invalid_verification_commands_by_gap", {}),
        "invalid_verification_options_by_gap": command_coverage.get("invalid_verification_options_by_gap", {}),
        "command_subcommands_by_gap": command_coverage.get("command_subcommands_by_gap", {}),
        "command_options_by_gap": command_coverage.get("command_options_by_gap", {}),
    }
    audit_receipt = response.get("capability_audit_receipt", {})
    audit_material = audit_receipt.get("material", {}) if isinstance(audit_receipt, dict) else {}
    return {
        "known_gap_count": len(known_gap_ids),
        "plan_item_count": len(normalized),
        "covered_count": max(0, covered_count),
        "coverage_complete": (
            not missing_gap_ids
            and not invalid_plan_gap_ids
            and command_coverage.get("command_validation_complete") is True
            and len(known_gap_ids) > 0
        ),
        "planned_gap_ids": sorted(plan_by_gap),
        "missing_gap_ids": missing_gap_ids,
        "invalid_plan_gap_ids": invalid_plan_gap_ids,
        "invalid_gate_ids_by_gap": invalid_gate_ids_by_gap,
        "invalid_verification_commands_by_gap": command_coverage.get("invalid_verification_commands_by_gap", {}),
        "invalid_verification_options_by_gap": command_coverage.get("invalid_verification_options_by_gap", {}),
        "valid_production_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
        "valid_cli_subcommands": command_coverage.get("valid_subcommands", []),
        "valid_cli_options_by_subcommand": command_coverage.get("valid_options_by_subcommand", {}),
        "command_validation_complete": command_coverage.get("command_validation_complete") is True,
        "command_subcommands_by_gap": command_coverage.get("command_subcommands_by_gap", {}),
        "command_options_by_gap": command_coverage.get("command_options_by_gap", {}),
        "command_coverage_sha256": command_coverage.get("command_coverage_sha256"),
        "command_counts": command_counts,
        "gate_counts": gate_counts,
        "plan_coverage_sha256": hashlib.sha256(
            json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest(),
        "audit_plan_hash": audit_material.get("known_gap_resolution_plan_hash")
        if isinstance(audit_material, dict)
        else None,
    }


def _known_gap_plan_item_id(item: dict[str, Any]) -> str:
    return str(item.get("gap_id") or item.get("id") or "")


def _production_resolution_plan_summary(resolution_plan: Any) -> dict[str, Any]:
    if not isinstance(resolution_plan, dict):
        resolution_plan = {}
    steps = resolution_plan.get("steps", [])
    if not isinstance(steps, list):
        steps = []
    normalized_steps = [step for step in steps if isinstance(step, dict)]
    categories = sorted({str(step.get("category")) for step in normalized_steps if step.get("category")})
    category_counts: dict[str, int] = {}
    step_ids = [str(step.get("id")) for step in normalized_steps if step.get("id")]
    command_count = 0
    diagnostic_count = 0
    checklist_count = 0
    for step in normalized_steps:
        category = step.get("category")
        if category:
            category_text = str(category)
            category_counts[category_text] = category_counts.get(category_text, 0) + 1
        commands = step.get("commands", [])
        diagnostics = step.get("diagnostics", [])
        checklist = step.get("checklist", [])
        command_count += len(commands) if isinstance(commands, list) else 0
        diagnostic_count += len(diagnostics) if isinstance(diagnostics, list) else 0
        checklist_count += len(checklist) if isinstance(checklist, list) else 0
    return {
        "status": resolution_plan.get("status"),
        "step_count": len(normalized_steps),
        "step_ids": step_ids,
        "categories": categories,
        "category_counts": dict(sorted(category_counts.items())),
        "command_count": command_count,
        "diagnostic_count": diagnostic_count,
        "checklist_count": checklist_count,
        "resolution_plan_sha256": hashlib.sha256(
            json.dumps(resolution_plan, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest(),
    }


def _benchmark_provider_action_plan_audit(benchmark: Any) -> dict[str, Any]:
    cases = benchmark.get("cases", []) if isinstance(benchmark, dict) else []
    valid_cases = [case for case in cases if isinstance(case, dict)]
    covered = 0
    unresolved = []
    action_plan_counts = []
    for case in valid_cases:
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            unresolved.append({"case": case.get("name"), "reason": "report_features missing"})
            continue
        if features.get("provider_action_plan_covers_blockers") is True:
            covered += 1
        else:
            unresolved.append(
                {
                    "case": case.get("name"),
                    "provider_blocker_count": features.get("provider_blocker_count"),
                    "provider_action_plan_count": features.get("provider_action_plan_count"),
                    "provider_action_plan_domains": features.get("provider_action_plan_domains", []),
                }
            )
        action_plan_counts.append(
            {
                "case": case.get("name"),
                "provider_blocker_count": features.get("provider_blocker_count"),
                "provider_action_plan_count": features.get("provider_action_plan_count"),
            }
        )
    return {
        "case_count": len(valid_cases),
        "covered_count": covered,
        "coverage_complete": covered == len(valid_cases) if valid_cases else False,
        "unresolved": unresolved,
        "action_plan_counts": action_plan_counts,
    }


def _benchmark_request_provenance_audit(benchmark: Any) -> dict[str, Any]:
    cases = benchmark.get("cases", []) if isinstance(benchmark, dict) else []
    chains = []
    deliberation_receipts = []
    annual_timeline_receipts = []
    annual_timeline_unbound_cases = []
    monthly_luck_receipts = []
    monthly_luck_unbound_cases = []
    auspicious_calendar_receipts = []
    auspicious_calendar_unbound_cases = []
    external_payload_receipt_cases = []
    external_payload_receipt_domains: set[str] = set()
    external_payload_birth_match_cases = []
    external_payload_birth_mismatch_domains: set[str] = set()
    covered = 0
    deliberation_covered = 0
    annual_timeline_covered = 0
    annual_timeline_bound = 0
    monthly_luck_covered = 0
    monthly_luck_bound = 0
    auspicious_calendar_covered = 0
    auspicious_calendar_bound = 0
    for case in cases:
        if not isinstance(case, dict):
            continue
        features = case.get("report_features", {})
        if not isinstance(features, dict):
            continue
        if features.get("request_provenance_present") is True:
            covered += 1
        chain = features.get("request_provenance_chain_sha256")
        if isinstance(chain, str) and chain:
            chains.append({"case": case.get("name"), "sha256": chain})
        if features.get("deliberation_receipt_present") is True:
            deliberation_covered += 1
        deliberation_sha = features.get("deliberation_receipt_sha256")
        if isinstance(deliberation_sha, str) and deliberation_sha:
            deliberation_receipts.append(
                {
                    "case": case.get("name"),
                    "sha256": deliberation_sha,
                    "claim_count": features.get("deliberation_claim_count"),
                }
            )
        if features.get("annual_timeline_receipt_present") is True:
            annual_timeline_covered += 1
        annual_timeline_sha = features.get("annual_timeline_receipt_sha256")
        if isinstance(annual_timeline_sha, str) and annual_timeline_sha:
            annual_timeline_receipts.append(
                {
                    "case": case.get("name"),
                    "sha256": annual_timeline_sha,
                    "row_count": features.get("annual_timeline_row_count"),
                    "bound_to_provenance": features.get("annual_timeline_receipt_bound_to_provenance") is True,
                }
            )
        if features.get("annual_timeline_receipt_bound_to_provenance") is True:
            annual_timeline_bound += 1
        else:
            annual_timeline_unbound_cases.append(str(case.get("name")))
        if features.get("monthly_luck_receipt_present") is True:
            monthly_luck_covered += 1
        monthly_luck_sha = features.get("monthly_luck_receipt_sha256")
        if isinstance(monthly_luck_sha, str) and monthly_luck_sha:
            monthly_luck_receipts.append(
                {
                    "case": case.get("name"),
                    "sha256": monthly_luck_sha,
                    "row_count": features.get("monthly_luck_row_count"),
                    "bound_to_provenance": features.get("monthly_luck_receipt_bound_to_provenance") is True,
                }
            )
        if features.get("monthly_luck_receipt_bound_to_provenance") is True:
            monthly_luck_bound += 1
        else:
            monthly_luck_unbound_cases.append(str(case.get("name")))
        if features.get("auspicious_calendar_receipt_present") is True:
            auspicious_calendar_covered += 1
        auspicious_calendar_sha = features.get("auspicious_calendar_receipt_sha256")
        if isinstance(auspicious_calendar_sha, str) and auspicious_calendar_sha:
            auspicious_calendar_receipts.append(
                {
                    "case": case.get("name"),
                    "sha256": auspicious_calendar_sha,
                    "row_count": features.get("auspicious_calendar_row_count"),
                    "bound_to_provenance": features.get("auspicious_calendar_receipt_bound_to_provenance") is True,
                }
            )
        if features.get("auspicious_calendar_receipt_bound_to_provenance") is True:
            auspicious_calendar_bound += 1
        else:
            auspicious_calendar_unbound_cases.append(str(case.get("name")))
        receipt_domains = features.get("external_payload_receipt_domains")
        if isinstance(receipt_domains, list) and receipt_domains:
            normalized_domains = sorted(str(domain) for domain in receipt_domains)
            external_payload_receipt_domains.update(normalized_domains)
            external_payload_receipt_cases.append(
                {
                    "case": case.get("name"),
                    "domains": normalized_domains,
                    "complete": features.get("external_payload_receipts_complete") is True,
                }
            )
        match_statuses = features.get("external_payload_birth_match_statuses")
        if isinstance(match_statuses, list) and match_statuses:
            normalized_statuses = [
                {
                    "domain": str(item.get("domain")),
                    "status": str(item.get("status")),
                    "mismatch_fields": [
                        str(field)
                        for field in item.get("mismatch_fields", [])
                    ]
                    if isinstance(item, dict) and isinstance(item.get("mismatch_fields"), list)
                    else [],
                    "declared_birth_profile_sha256": item.get("declared_birth_profile_sha256")
                    if isinstance(item, dict)
                    else None,
                }
                for item in match_statuses
                if isinstance(item, dict) and item.get("domain")
            ]
            mismatch_domains = [
                item["domain"]
                for item in normalized_statuses
                if item.get("status") == "mismatch"
            ]
            external_payload_birth_mismatch_domains.update(mismatch_domains)
            external_payload_birth_match_cases.append(
                {
                    "case": case.get("name"),
                    "statuses": normalized_statuses,
                    "mismatch_domains": mismatch_domains,
                    "matches_ok": features.get("external_payload_birth_matches_ok") is True,
                }
            )
    return {
        "case_count": len([case for case in cases if isinstance(case, dict)]),
        "covered_count": covered,
        "chains": chains,
        "deliberation_receipt_covered_count": deliberation_covered,
        "deliberation_receipts": deliberation_receipts,
        "annual_timeline_receipt_covered_count": annual_timeline_covered,
        "annual_timeline_receipt_bound_count": annual_timeline_bound,
        "annual_timeline_receipts": annual_timeline_receipts,
        "annual_timeline_unbound_cases": annual_timeline_unbound_cases,
        "monthly_luck_receipt_covered_count": monthly_luck_covered,
        "monthly_luck_receipt_bound_count": monthly_luck_bound,
        "monthly_luck_receipts": monthly_luck_receipts,
        "monthly_luck_unbound_cases": monthly_luck_unbound_cases,
        "auspicious_calendar_receipt_covered_count": auspicious_calendar_covered,
        "auspicious_calendar_receipt_bound_count": auspicious_calendar_bound,
        "auspicious_calendar_receipts": auspicious_calendar_receipts,
        "auspicious_calendar_unbound_cases": auspicious_calendar_unbound_cases,
        "external_payload_receipt_case_count": len(external_payload_receipt_cases),
        "external_payload_receipt_domains": sorted(external_payload_receipt_domains),
        "external_payload_receipt_cases": external_payload_receipt_cases,
        "external_payload_birth_match_case_count": len(external_payload_birth_match_cases),
        "external_payload_birth_match_cases": external_payload_birth_match_cases,
        "external_payload_birth_mismatch_domains": sorted(external_payload_birth_mismatch_domains),
        "external_payload_birth_matches_ok": not external_payload_birth_mismatch_domains,
    }


def _outcome_dataset_receipt_material(outcome_dataset: Any) -> dict[str, Any]:
    if not isinstance(outcome_dataset, dict):
        outcome_dataset = {}
    governance_gates = outcome_dataset.get("governance_gates", {})
    gate_values = governance_gates.get("gates", {}) if isinstance(governance_gates, dict) else {}
    return {
        "schema_version": 1,
        "status": outcome_dataset.get("status"),
        "valid": outcome_dataset.get("valid"),
        "content_hash": outcome_dataset.get("content_hash"),
        "record_count": outcome_dataset.get("record_count"),
        "data_split_record_coverage": outcome_dataset.get("data_split_record_coverage", {}),
        "predictive_optimization_enabled": outcome_dataset.get("predictive_optimization_enabled"),
        "external_review": outcome_dataset.get("external_review", {}),
        "data_split": outcome_dataset.get("data_split", {}),
        "label_collection": outcome_dataset.get("label_collection", {}),
        "statistical_plan": outcome_dataset.get("statistical_plan", {}),
        "label_provenance": outcome_dataset.get("label_provenance", {}),
        "governance_gate_ids": sorted(gate_values) if isinstance(gate_values, dict) else [],
    }


def _outcome_dataset_receipt(outcome_dataset: Any) -> dict[str, Any]:
    """Return a stable receipt for outcome dataset governance evidence."""
    material = _outcome_dataset_receipt_material(outcome_dataset)
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _outcome_dataset_split_coverage_failures(outcome: Any) -> list[str]:
    audit = outcome.get("audit", {}) if isinstance(outcome, dict) else {}
    coverage = audit.get("data_split_record_coverage", {}) if isinstance(audit, dict) else {}
    if not isinstance(coverage, dict):
        return ["outcome data_split_record_coverage is missing"]
    failures: list[str] = []
    for field, label in (
        ("unassigned_case_ids", "unassigned"),
        ("unknown_case_ids", "unknown"),
        ("overlap_case_ids", "overlapping"),
    ):
        values = coverage.get(field, [])
        if isinstance(values, list) and values:
            failures.append(f"{label} case_ids: {', '.join(str(item) for item in values)}")
    if coverage.get("record_count", 0) == 0:
        failures.append("no outcome records are available for split coverage")
    if not failures and coverage.get("coverage_complete") is not True:
        failures.append("data_split_record_coverage.coverage_complete is false")
    return failures


def _provider_resolution_steps(
    repo_path: Path,
    providers: dict[str, Any],
    blocker_gates: set[str],
) -> list[dict[str, Any]]:
    if not {"provider_profile_ready", "provider_integration_ready"} & blocker_gates:
        return []
    steps = []
    for target in providers.get("integration_plan", {}).get("targets", []):
        if not isinstance(target, dict) or target.get("status") == "ready":
            continue
        commands = list(target.get("certification_commands", []))
        commands.extend(str(item) for item in target.get("drift_commands", []))
        if not commands:
            commands = [f"python -m examples.mingli_5agents.cli --repo {repo_path} providers --profile production --live"]
        diagnostics = []
        for check_name in target.get("blocked_checks", []):
            check = providers.get("checks", {}).get(check_name, {})
            detail = check.get("production_blocker") or check.get("blocking_detail")
            if detail:
                diagnostics.append(str(detail))
            install_diagnostics = check.get("install_diagnostics")
            if isinstance(install_diagnostics, dict) and install_diagnostics.get("remediation"):
                diagnostics.append(str(install_diagnostics["remediation"]))
        steps.append(
            _resolution_step(
                f"complete_{target.get('name')}",
                "provider_integration",
                f"Complete provider integration target {target.get('name')}.",
                commands,
                diagnostics or target.get("next_actions", []),
                30,
                checklist=target.get("deployment_checklist", []),
            )
        )
    return steps


def _provider_certification_command(repo_path: Path, domain: str) -> str:
    return (
        "python -m examples.mingli_5agents.cli --repo "
        f"{repo_path} certify-provider {domain} --command \"<provider-command>\" "
        "--provenance \"provider=<provider-name>; version=<provider-version>; "
        "source=<review-source>; license_or_review=<license-or-review>\" --record"
    )


def _provider_recertification_commands(repo_path: Path, failures: Any) -> list[str]:
    domains = _provider_domains_from_failures(failures)
    if not domains:
        domains = ["ziwei", "qimen", "astrology", "xuanze"]
    commands = [_provider_certification_command(repo_path, domain) for domain in domains]
    commands.append(f"python -m examples.mingli_5agents.cli --repo {repo_path} provider-ledger")
    return commands


def _provider_domains_from_failures(failures: Any) -> list[str]:
    if not isinstance(failures, list):
        return []
    domains = []
    for item in failures:
        text = str(item)
        first = text.split(" ", 1)[0].strip().lower()
        if first in {"ziwei", "qimen", "astrology", "xuanze"} and first not in domains:
            domains.append(first)
    return sorted(domains)


def _resolution_step(
    step_id: str,
    category: str,
    summary: str,
    commands: list[str],
    diagnostics: list[Any],
    priority: int,
    *,
    checklist: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "category": category,
        "priority": priority,
        "summary": summary,
        "commands": [str(item) for item in commands if str(item).strip()],
        "diagnostics": _string_list(diagnostics),
        "checklist": _string_list(checklist or []),
    }


def _string_list(values: list[Any]) -> list[str]:
    return [str(item) for item in values if str(item).strip()]


def _provider_certification_ledger_status(repo_path: Path) -> dict[str, Any]:
    ledger_path = _provider_certification_ledger_path(repo_path)
    empty_domains = _provider_ledger_domain_status([])
    empty_request_receipt_failures = [
        f"{domain} latest certification is missing provider request receipt"
        for domain in sorted(empty_domains)
    ]
    if not ledger_path.exists():
        return {
            "path": str(ledger_path),
            "exists": False,
            "integrity_status": "fail",
            "protocol_status": "unknown",
            "request_receipt_status": "missing",
            "reference_contract_status": "missing",
            "command_fingerprint_status": "missing",
            "coverage_status": "incomplete",
            "record_count": 0,
            "latest_record_hash": None,
            "latest_record_index": None,
            "domains": empty_domains,
            "covered_domains": [],
            "missing_domains": sorted(empty_domains),
            "protocol_failures": ["provider certification ledger is missing"],
            "request_receipt_failures": empty_request_receipt_failures,
            "reference_contract_failures": [
                f"{domain} latest certification is missing reference contract coverage"
                for domain in sorted(empty_domains)
            ],
            "command_fingerprint_failures": [
                f"{domain} latest certification is missing provider command fingerprint"
                for domain in sorted(empty_domains)
            ],
            "failures": ["provider certification ledger is missing"],
        }
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "path": str(ledger_path),
            "exists": True,
            "integrity_status": "fail",
            "protocol_status": "unknown",
            "request_receipt_status": "missing",
            "reference_contract_status": "missing",
            "command_fingerprint_status": "missing",
            "coverage_status": "incomplete",
            "record_count": 0,
            "latest_record_hash": None,
            "latest_record_index": None,
            "domains": empty_domains,
            "covered_domains": [],
            "missing_domains": sorted(empty_domains),
            "protocol_failures": [f"provider certification ledger JSON is invalid: {exc}"],
            "request_receipt_failures": empty_request_receipt_failures,
            "reference_contract_failures": [
                f"{domain} latest certification is missing reference contract coverage"
                for domain in sorted(empty_domains)
            ],
            "command_fingerprint_failures": [
                f"{domain} latest certification is missing provider command fingerprint"
                for domain in sorted(empty_domains)
            ],
            "failures": [f"provider certification ledger JSON is invalid: {exc}"],
        }
    records = ledger.get("records") if isinstance(ledger, dict) else None
    if not isinstance(records, list):
        return {
            "path": str(ledger_path),
            "exists": True,
            "integrity_status": "fail",
            "protocol_status": "unknown",
            "request_receipt_status": "missing",
            "reference_contract_status": "missing",
            "command_fingerprint_status": "missing",
            "coverage_status": "incomplete",
            "record_count": 0,
            "latest_record_hash": None,
            "latest_record_index": None,
            "domains": empty_domains,
            "covered_domains": [],
            "missing_domains": sorted(empty_domains),
            "protocol_failures": ["provider certification ledger records must be a list"],
            "request_receipt_failures": empty_request_receipt_failures,
            "reference_contract_failures": [
                f"{domain} latest certification is missing reference contract coverage"
                for domain in sorted(empty_domains)
            ],
            "command_fingerprint_failures": [
                f"{domain} latest certification is missing provider command fingerprint"
                for domain in sorted(empty_domains)
            ],
            "failures": ["provider certification ledger records must be a list"],
        }
    failures = []
    previous_hash = None
    latest_record_index = None
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            failures.append(f"record {index} is not an object")
            continue
        if record.get("index") != index:
            failures.append(f"record {index} has incorrect index")
        if record.get("previous_record_hash") != previous_hash:
            failures.append(f"record {index} previous_record_hash mismatch")
        failures.extend(_provider_ledger_record_consistency_failures(index, record))
        material = {key: value for key, value in record.items() if key != "record_hash"}
        expected_hash = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
        if record.get("record_hash") != expected_hash:
            failures.append(f"record {index} hash mismatch")
        previous_hash = record.get("record_hash")
        latest_record_index = index
    if ledger.get("latest_record_hash") != previous_hash:
        failures.append("latest_record_hash does not match last record")
    if ledger.get("latest_record_index") != latest_record_index:
        failures.append("latest_record_index does not match last record")
    domains = _provider_ledger_domain_status(records)
    missing_domains = sorted([domain for domain, status in domains.items() if status["record_count"] == 0])
    protocol_failures = [
        f"{domain} latest certification protocol hash does not match current protocol"
        for domain, status in domains.items()
        if status["record_count"] > 0 and status.get("protocol_matches_current") is not True
    ]
    request_receipt_failures = _provider_request_receipt_failures(domains)
    reference_contract_failures = _provider_reference_contract_failures(domains)
    command_fingerprint_failures = _provider_command_fingerprint_failures(domains)
    return {
        "path": str(ledger_path),
        "exists": True,
        "integrity_status": "pass" if not failures else "fail",
        "protocol_status": "current" if not protocol_failures else "stale",
        "request_receipt_status": "current" if not request_receipt_failures else "missing",
        "reference_contract_status": "current" if not reference_contract_failures else "missing",
        "command_fingerprint_status": "current" if not command_fingerprint_failures else "missing",
        "coverage_status": "complete" if not missing_domains else "incomplete",
        "record_count": len(records),
        "latest_record_hash": previous_hash,
        "latest_record_index": latest_record_index,
        "domains": domains,
        "covered_domains": sorted([domain for domain, status in domains.items() if status["record_count"] > 0]),
        "missing_domains": missing_domains,
        "protocol_failures": protocol_failures,
        "request_receipt_failures": request_receipt_failures,
        "reference_contract_failures": reference_contract_failures,
        "command_fingerprint_failures": command_fingerprint_failures,
        "failures": failures,
    }


def _provider_ledger_domain_status(records: list[Any]) -> dict[str, Any]:
    protocols = provider_protocol_document()["domains"]
    current_method_surface = method_surface_receipt()
    domains = {
        domain: {
            "domain": domain,
            "record_count": 0,
            "latest_receipt_sha256": None,
            "latest_protocol_version": None,
            "latest_protocol_hash": None,
            "current_protocol_version": protocols.get(domain, {}).get("protocol_version"),
            "current_protocol_hash": protocols.get(domain, {}).get("protocol_hash"),
            "protocol_matches_current": False,
            "latest_provider_request_receipt_sha256": None,
            "latest_provider_command_sha256": None,
            "latest_provider_artifact_sha256": None,
            "provider_command_fingerprint_present": False,
            "request_receipt_present": False,
            "request_receipt_valid": False,
            "request_receipt_protocol_echo_matches": False,
            "request_receipt_birth_profile_sha256": None,
            "latest_reference_contract_coverage_sha256": None,
            "latest_reference_contract_method_surface_sha256": None,
            "current_method_surface_sha256": current_method_surface.get("sha256"),
            "reference_contract_method_surface_current": False,
            "reference_contract_covered": False,
            "reference_contract_method_count": 0,
            "reference_contract_case_count": 0,
            "latest_record_hash": None,
            "latest_record_index": None,
            "certified": False,
        }
        for domain in sorted(JSON_CLI_CHECK_BY_DOMAIN)
    }
    for record in records:
        if not isinstance(record, dict):
            continue
        domain = record.get("domain")
        if domain not in domains:
            continue
        status = domains[domain]
        status["record_count"] += 1
        status["latest_receipt_sha256"] = record.get("receipt_sha256")
        material = record.get("certification_receipt", {}).get("material", {})
        if not isinstance(material, dict):
            material = {}
        status["latest_protocol_version"] = record.get("protocol_version") or material.get("protocol_version")
        status["latest_protocol_hash"] = record.get("protocol_hash") or material.get("protocol_hash")
        status["protocol_matches_current"] = (
            bool(status["latest_protocol_hash"])
            and status["latest_protocol_hash"] == status["current_protocol_hash"]
            and status["latest_protocol_version"] == status["current_protocol_version"]
        )
        request_receipt = material.get("provider_request_receipt")
        if not isinstance(request_receipt, dict):
            request_receipt = {}
        status["latest_provider_request_receipt_sha256"] = request_receipt.get("sha256")
        command_fingerprint = material.get("provider_command_fingerprint")
        if not isinstance(command_fingerprint, dict):
            command_fingerprint = {}
        status["latest_provider_command_sha256"] = command_fingerprint.get("command_sha256")
        status["latest_provider_artifact_sha256"] = command_fingerprint.get("artifact_sha256")
        status["provider_command_fingerprint_present"] = _provider_command_fingerprint_valid(command_fingerprint)
        status["request_receipt_present"] = bool(request_receipt)
        status["request_receipt_protocol_echo_matches"] = request_receipt.get("protocol_echo_matches") is True
        status["request_receipt_birth_profile_sha256"] = request_receipt.get("birth_profile_sha256")
        status["request_receipt_valid"] = _provider_request_receipt_material_valid(domain, material, request_receipt)
        reference_coverage = material.get("reference_contract_coverage")
        if not isinstance(reference_coverage, dict):
            reference_coverage = {}
        observed_methods = reference_coverage.get("observed_methods", [])
        covered_cases = reference_coverage.get("covered_cases", [])
        status["latest_reference_contract_coverage_sha256"] = reference_coverage.get("coverage_sha256")
        status["latest_reference_contract_method_surface_sha256"] = reference_coverage.get("method_surface_sha256")
        status["reference_contract_method_surface_current"] = (
            bool(status["latest_reference_contract_method_surface_sha256"])
            and status["latest_reference_contract_method_surface_sha256"] == status["current_method_surface_sha256"]
        )
        status["reference_contract_covered"] = reference_coverage.get("passed") is True and _is_sha256(
            reference_coverage.get("coverage_sha256")
        ) and status["reference_contract_method_surface_current"] is True
        status["reference_contract_method_count"] = len(observed_methods) if isinstance(observed_methods, list) else 0
        status["reference_contract_case_count"] = len(covered_cases) if isinstance(covered_cases, list) else 0
        status["latest_record_hash"] = record.get("record_hash")
        status["latest_record_index"] = record.get("index")
        status["certified"] = bool(record.get("certified"))
    return domains


def _provider_request_receipt_material_valid(
    domain: str, material: dict[str, Any], request_receipt: dict[str, Any]
) -> bool:
    if material.get("provider_request_receipt_valid") is not True:
        return False
    if request_receipt.get("schema_version") != "provider-request-receipt-v1":
        return False
    if request_receipt.get("domain") != domain:
        return False
    if request_receipt.get("protocol_echo_matches") is not True:
        return False
    required_hash_fields = ["birth_profile_sha256", "stdin_sha256", "stdout_sha256", "sha256"]
    return all(_is_sha256(request_receipt.get(field)) for field in required_hash_fields)


def _provider_request_receipt_failures(domains: dict[str, Any]) -> list[str]:
    failures = []
    for domain, status in sorted(domains.items()):
        if not isinstance(status, dict) or status.get("record_count", 0) <= 0:
            continue
        if status.get("request_receipt_present") is not True:
            failures.append(f"{domain} latest certification is missing provider request receipt")
        elif status.get("request_receipt_valid") is not True:
            failures.append(f"{domain} latest provider request receipt is invalid")
    return failures


def _provider_reference_contract_failures(domains: dict[str, Any]) -> list[str]:
    failures = []
    for domain, status in sorted(domains.items()):
        if not isinstance(status, dict) or status.get("record_count", 0) <= 0:
            continue
        if status.get("reference_contract_covered") is not True:
            failures.append(f"{domain} latest certification is missing reference contract coverage")
    return failures


def _provider_command_fingerprint_failures(domains: dict[str, Any]) -> list[str]:
    failures = []
    for domain, status in sorted(domains.items()):
        if not isinstance(status, dict) or status.get("record_count", 0) <= 0:
            continue
        if status.get("provider_command_fingerprint_present") is not True:
            failures.append(f"{domain} latest certification is missing provider command fingerprint")
    return failures


def _provider_command_fingerprint_valid(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and _is_sha256(value.get("command_sha256"))
        and (
            value.get("artifact_sha256") is None
            or _is_sha256(value.get("artifact_sha256"))
        )
    )


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _provider_ledger_record_consistency_failures(index: int, record: dict[str, Any]) -> list[str]:
    failures = []
    receipt = record.get("certification_receipt")
    if not isinstance(receipt, dict):
        return [f"record {index} certification_receipt is missing or invalid"]
    material = receipt.get("material")
    if not isinstance(material, dict):
        failures.append(f"record {index} certification_receipt.material is missing or invalid")
        material = {}
    expected_receipt_sha256 = hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    if receipt.get("sha256") != expected_receipt_sha256:
        failures.append(f"record {index} certification_receipt sha256 mismatch")
    if record.get("receipt_sha256") != receipt.get("sha256"):
        failures.append(f"record {index} receipt_sha256 mismatch")
    if record.get("domain") != material.get("domain"):
        failures.append(f"record {index} domain does not match certification receipt")
    if record.get("provider_check") != material.get("provider_check"):
        failures.append(f"record {index} provider_check does not match certification receipt")
    if record.get("status") != material.get("status"):
        failures.append(f"record {index} status does not match certification receipt")
    if record.get("certified") is not True or material.get("certified") is not True:
        failures.append(f"record {index} is not a certified provider receipt")
    if record.get("live_requested") != material.get("live_requested"):
        failures.append(f"record {index} live_requested does not match certification receipt")
    if record.get("contract") != material.get("contract"):
        failures.append(f"record {index} contract does not match certification receipt")
    if record.get("protocol_version") != material.get("protocol_version"):
        failures.append(f"record {index} protocol_version does not match certification receipt")
    if record.get("protocol_hash") != material.get("protocol_hash"):
        failures.append(f"record {index} protocol_hash does not match certification receipt")
    if record.get("reference_contract_coverage") != material.get("reference_contract_coverage"):
        failures.append(f"record {index} reference_contract_coverage does not match certification receipt")
    if record.get("provider_command_fingerprint") != material.get("provider_command_fingerprint"):
        failures.append(f"record {index} provider_command_fingerprint does not match certification receipt")
    return failures


def _provider_certification_drift_status(
    repo_path: Path,
    provider_ledger: dict[str, Any],
    *,
    live: bool,
    domain: str | None = None,
) -> dict[str, Any]:
    if domain is not None and domain not in JSON_CLI_CHECK_BY_DOMAIN:
        raise ValueError("provider drift domain must be ziwei, qimen, astrology, or xuanze")
    checked_domains = [domain] if domain is not None else sorted(JSON_CLI_CHECK_BY_DOMAIN)
    domains = provider_ledger.get("domains") if isinstance(provider_ledger, dict) else {}
    if not live:
        return {
            "status": "not_checked",
            "passed": False,
            "live_requested": False,
            "checked_domains": checked_domains,
            "checks": [],
            "failures": ["run production-readiness with --live to compare current provider receipts"],
        }
    checks = []
    failures = []
    for check_domain in checked_domains:
        domain_status = domains.get(check_domain, {}) if isinstance(domains, dict) else {}
        expected_receipt = domain_status.get("latest_receipt_sha256") if isinstance(domain_status, dict) else None
        if not expected_receipt:
            checks.append(
                {
                    "domain": check_domain,
                    "status": "missing_ledger_receipt",
                    "expected_receipt_sha256": None,
                    "current_receipt_sha256": None,
                    "expected_provider_request_receipt_sha256": None,
                    "current_provider_request_receipt_sha256": None,
                    "expected_provider_command_sha256": None,
                    "current_provider_command_sha256": None,
                    "expected_provider_artifact_sha256": None,
                    "current_provider_artifact_sha256": None,
                    "provider_request_receipt_matches_expected": False,
                    "provider_request_receipt_valid": False,
                    "provider_command_fingerprint_matches_expected": False,
                    "matches_expected": False,
                    "certified": False,
                    "blockers": ["missing ledger receipt for domain"],
                }
            )
            failures.append(f"{check_domain} has no recorded certification receipt")
            continue
        try:
            certification = certify_json_cli_provider(
                check_domain,
                repo_path,
                live=True,
                expected_receipt_sha256=expected_receipt,
            )
        except Exception as exc:  # pragma: no cover - defensive boundary for provider subprocess failures.
            checks.append(
                {
                    "domain": check_domain,
                    "status": "certification_error",
                    "expected_receipt_sha256": expected_receipt,
                    "current_receipt_sha256": None,
                    "expected_provider_request_receipt_sha256": domain_status.get(
                        "latest_provider_request_receipt_sha256"
                    )
                    if isinstance(domain_status, dict)
                    else None,
                    "current_provider_request_receipt_sha256": None,
                    "expected_provider_command_sha256": domain_status.get("latest_provider_command_sha256")
                    if isinstance(domain_status, dict)
                    else None,
                    "current_provider_command_sha256": None,
                    "expected_provider_artifact_sha256": domain_status.get("latest_provider_artifact_sha256")
                    if isinstance(domain_status, dict)
                    else None,
                    "current_provider_artifact_sha256": None,
                    "provider_request_receipt_matches_expected": False,
                    "provider_request_receipt_valid": False,
                    "provider_command_fingerprint_matches_expected": False,
                    "matches_expected": False,
                    "certified": False,
                    "blockers": [str(exc)],
                }
            )
            failures.append(f"{check_domain} certification failed: {exc}")
            continue
        current_receipt = certification.get("certification_receipt", {}).get("sha256")
        current_material = certification.get("certification_receipt", {}).get("material", {})
        if not isinstance(current_material, dict):
            current_material = {}
        current_request_receipt = current_material.get("provider_request_receipt")
        if not isinstance(current_request_receipt, dict):
            current_request_receipt = {}
        expected_request_receipt = (
            domain_status.get("latest_provider_request_receipt_sha256") if isinstance(domain_status, dict) else None
        )
        current_request_receipt_sha256 = current_request_receipt.get("sha256")
        current_command_fingerprint = current_material.get("provider_command_fingerprint")
        if not isinstance(current_command_fingerprint, dict):
            current_command_fingerprint = {}
        expected_command_sha256 = (
            domain_status.get("latest_provider_command_sha256") if isinstance(domain_status, dict) else None
        )
        expected_artifact_sha256 = (
            domain_status.get("latest_provider_artifact_sha256") if isinstance(domain_status, dict) else None
        )
        current_command_sha256 = current_command_fingerprint.get("command_sha256")
        current_artifact_sha256 = current_command_fingerprint.get("artifact_sha256")
        command_fingerprint_matches = (
            bool(expected_command_sha256)
            and current_command_sha256 == expected_command_sha256
            and current_artifact_sha256 == expected_artifact_sha256
        )
        matches = certification.get("receipt_matches_expected") is True
        check = {
            "domain": check_domain,
            "status": "match" if matches else "drift",
            "expected_receipt_sha256": expected_receipt,
            "current_receipt_sha256": current_receipt,
            "expected_provider_request_receipt_sha256": expected_request_receipt,
            "current_provider_request_receipt_sha256": current_request_receipt_sha256,
            "expected_provider_command_sha256": expected_command_sha256,
            "current_provider_command_sha256": current_command_sha256,
            "expected_provider_artifact_sha256": expected_artifact_sha256,
            "current_provider_artifact_sha256": current_artifact_sha256,
            "provider_request_receipt_matches_expected": (
                bool(expected_request_receipt) and current_request_receipt_sha256 == expected_request_receipt
            ),
            "provider_request_receipt_valid": current_material.get("provider_request_receipt_valid") is True,
            "provider_command_fingerprint_matches_expected": command_fingerprint_matches,
            "matches_expected": matches,
            "certified": certification.get("certified") is True,
            "blockers": certification.get("blockers", []),
        }
        checks.append(check)
        if not matches:
            failures.append(f"{check_domain} current certification receipt does not match ledger")
        if not command_fingerprint_matches:
            failures.append(f"{check_domain} provider command fingerprint drift")
    return {
        "status": "passed" if not failures else "drift_detected",
        "passed": not failures,
        "live_requested": True,
        "checked_domains": checked_domains,
        "checks": checks,
        "failures": failures,
    }


def _readiness_gate(
    gate_id: str,
    passed: bool,
    pass_reason: str,
    failure_reason: str,
    details: Any,
) -> dict[str, Any]:
    return {
        "id": gate_id,
        "passed": bool(passed),
        "reason": pass_reason if passed else failure_reason,
        "failure_reason": "" if passed else failure_reason,
        "details": details if isinstance(details, list) else ([] if details in (None, "") else [details]),
    }


def benchmark(
    repo_path: Path,
    version: int | None = None,
    baseline_version: int | None = None,
    expected_benchmark_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Run benchmark or version comparison."""
    repo = ensure_repo(repo_path)
    if baseline_version is not None:
        result = compare_versions(repo, baseline_version=baseline_version, candidate_version=version)
        receipt_sha256 = result.get("candidate", {}).get("benchmark_receipt", {}).get("sha256")
    else:
        result = run_benchmark(repo, version=version).__dict__
        receipt_sha256 = result.get("benchmark_receipt", {}).get("sha256")
    matches_expected = (
        None
        if expected_benchmark_receipt_sha256 is None
        else receipt_sha256 == expected_benchmark_receipt_sha256
    )
    return {
        "repo": str(repo_path),
        "benchmark": result,
        "expected_benchmark_receipt_sha256": expected_benchmark_receipt_sha256,
        "benchmark_receipt_matches_expected": matches_expected,
        "benchmark_receipt_mismatch_reason": (
            "benchmark receipt sha256 does not match expected value" if matches_expected is False else ""
        ),
    }


def release_manifest(
    repo_path: Path,
    *,
    manifest_path: Path | None = None,
    classical_source_list_path: Path | None = None,
    live: bool = False,
    record: bool = False,
    expected_audit_receipt_sha256: str | None = None,
    expected_benchmark_receipt_sha256: str | None = None,
    expected_readiness_receipt_sha256: str | None = None,
    expected_release_manifest_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Return an aggregate release evidence manifest for CI/archive approval."""
    ensure_repo(repo_path)
    current_status = status(repo_path)
    history = version_history(repo_path)
    audit = capability_audit(
        repo_path,
        expected_audit_receipt_sha256=expected_audit_receipt_sha256,
        classical_source_list_path=classical_source_list_path,
    )
    protocols_receipt = provider_protocol_receipt(provider_protocol_document(), repo=str(repo_path), domain=None)
    provider_onboarding_response = audit.get("provider_onboarding", {})
    provider_onboarding_receipt = (
        provider_onboarding_response.get("provider_onboarding_receipt", {})
        if isinstance(provider_onboarding_response, dict)
        else {}
    )
    readiness = production_readiness(
        repo_path,
        manifest_path=manifest_path,
        classical_source_list_path=classical_source_list_path,
        live=live,
        expected_readiness_receipt_sha256=expected_readiness_receipt_sha256,
        expected_audit_receipt_sha256=expected_audit_receipt_sha256,
    )
    benchmark_receipt = _benchmark_receipt_from_readiness(readiness)
    benchmark_receipt_sha256 = benchmark_receipt.get("sha256") if isinstance(benchmark_receipt, dict) else None
    benchmark_receipt_matches_expected = (
        None
        if expected_benchmark_receipt_sha256 is None
        else benchmark_receipt_sha256 == expected_benchmark_receipt_sha256
    )
    audit_protocol_governance = audit.get("provider_protocol_governance", {})
    protocol_material = protocols_receipt.get("material", {}) if isinstance(protocols_receipt, dict) else {}
    provider_protocols_receipt_current = (
        isinstance(audit_protocol_governance, dict)
        and isinstance(protocol_material, dict)
        and protocols_receipt.get("sha256") == audit_protocol_governance.get("protocol_receipt_sha256")
        and protocol_material.get("protocol_document_sha256")
        == audit_protocol_governance.get("protocol_document_sha256")
    )
    audit_provider_onboarding = (
        audit.get("audit_receipt", {}).get("material", {}).get("provider_onboarding", {})
        if isinstance(audit.get("audit_receipt"), dict)
        and isinstance(audit.get("audit_receipt", {}).get("material"), dict)
        else {}
    )
    provider_onboarding_receipt_current = (
        isinstance(provider_onboarding_receipt, dict)
        and isinstance(audit_provider_onboarding, dict)
        and provider_onboarding_receipt.get("sha256") == audit_provider_onboarding.get("receipt_sha256")
    )
    latest_evolution = current_status.get("latest_evolution")
    evolution_trigger_receipt = (
        latest_evolution.get("trigger_receipt") if isinstance(latest_evolution, dict) else None
    )
    evolution_trigger_receipt_sha256 = (
        evolution_trigger_receipt.get("sha256") if isinstance(evolution_trigger_receipt, dict) else None
    )
    genome_lineage = current_status.get("genome_lineage")
    lineage_trigger_receipt = genome_lineage.get("trigger_receipt") if isinstance(genome_lineage, dict) else None
    if evolution_trigger_receipt is None:
        evolution_trigger_receipt_current = True
    else:
        evolution_trigger_receipt_current = (
            isinstance(evolution_trigger_receipt_sha256, str)
            and len(evolution_trigger_receipt_sha256) == 64
            and lineage_trigger_receipt == evolution_trigger_receipt
            and current_status.get("lineage_integrity", {}).get("trigger_receipt_matches") is True
        )
    release_gate_checks = {
        "history_integrity_passed": history.get("history_integrity", {}).get("status") == "pass",
        "archive_integrity_passed": history.get("archive_integrity", {}).get("status") == "pass",
        "lineage_integrity_passed": current_status.get("lineage_integrity", {}).get("status")
        in {"pass", "not_applicable"},
        "audit_receipt_current": audit.get("audit_receipt_matches_expected") is not False,
        "provider_onboarding_receipt_current": provider_onboarding_receipt_current,
        "provider_protocols_receipt_current": provider_protocols_receipt_current,
        "benchmark_receipt_current": benchmark_receipt_matches_expected is not False,
        "readiness_receipt_current": readiness.get("readiness_receipt_matches_expected") is not False,
        "outcome_dataset_split_coverage_bound": readiness.get("readiness_receipt", {})
        .get("material", {})
        .get("outcome_dataset", {})
        .get("data_split_record_coverage", {})
        .get("coverage_complete")
        is True,
        "provider_audit_contract_gates_bound": _release_provider_audit_contract_gates_bound(readiness),
        "outcome_statistical_plan_preregistration_bound": (
            _release_outcome_statistical_plan_preregistration_bound(readiness)
        ),
        "classical_latest_refresh_receipt_bound": _release_classical_latest_refresh_receipt_bound(readiness),
        "blocked_capability_coverage_bound": _readiness_gate_decision_bound(
            readiness, "blocked_capability_coverage_complete"
        ),
        "known_gap_handoff_bundle_bound": _readiness_gate_decision_bound(readiness, "known_gap_handoff_bundle_ready"),
        "known_gap_command_coverage_bound": _release_known_gap_command_coverage_bound(readiness),
    }
    release_blockers = _release_approval_blockers(release_gate_checks, readiness)
    response = {
        "repo": str(repo_path),
        "status": "release_blocked" if not all(release_gate_checks.values()) else "release_manifest_ready",
        "release_gate_checks": release_gate_checks,
        "release_approval_ready": not release_blockers,
        "release_approval_status": "release_ready" if not release_blockers else "release_blocked",
        "release_blockers": release_blockers,
        "live_requested": live,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "classical_source_list_path": str(classical_source_list_path) if classical_source_list_path else None,
        "coordinator_version": current_status.get("coordinator_version"),
        "candidate_name": current_status.get("candidate_name"),
        "history_integrity": history.get("history_integrity", {}),
        "archive_integrity": history.get("archive_integrity", {}),
        "lineage_integrity": current_status.get("lineage_integrity", {}),
        "audit_receipt": audit.get("audit_receipt", {}),
        "github_comparison_receipt": audit.get("github_comparison_receipt", {}),
        "github_comparison_receipt_sha256": audit.get("github_comparison_receipt", {}).get("sha256")
        if isinstance(audit.get("github_comparison_receipt"), dict)
        else None,
        "plan_compliance_receipt": audit.get("plan_compliance_receipt", {}),
        "plan_compliance_receipt_sha256": audit.get("plan_compliance_receipt", {}).get("sha256")
        if isinstance(audit.get("plan_compliance_receipt"), dict)
        else None,
        "provider_onboarding_receipt": provider_onboarding_receipt,
        "provider_protocols_receipt": protocols_receipt,
        "expected_audit_receipt_sha256": expected_audit_receipt_sha256,
        "audit_receipt_matches_expected": audit.get("audit_receipt_matches_expected"),
        "benchmark_receipt": benchmark_receipt,
        "expected_benchmark_receipt_sha256": expected_benchmark_receipt_sha256,
        "benchmark_receipt_matches_expected": benchmark_receipt_matches_expected,
        "readiness_receipt": readiness.get("readiness_receipt", {}),
        "expected_readiness_receipt_sha256": expected_readiness_receipt_sha256,
        "readiness_receipt_matches_expected": readiness.get("readiness_receipt_matches_expected"),
        "production_readiness_status": readiness.get("status"),
        "production_ready": readiness.get("production_ready"),
        "known_gap_ids": readiness.get("known_gap_ids", []),
        "provider_ledger": readiness.get("provider_certification_ledger", {}),
        "outcome_dataset": readiness.get("outcome_dataset", {}).get("audit", {}),
        "outcome_dataset_receipt": readiness.get("outcome_dataset", {}).get("outcome_dataset_receipt", {}),
        "evolution_trigger_receipt_sha256": evolution_trigger_receipt_sha256,
        "evolution_trigger_receipt": evolution_trigger_receipt,
        "evolution_trigger_receipt_current": evolution_trigger_receipt_current,
    }
    response["release_manifest_receipt"] = _release_manifest_receipt(response)
    receipt_sha256 = response["release_manifest_receipt"]["sha256"]
    response["expected_release_manifest_receipt_sha256"] = expected_release_manifest_receipt_sha256
    response["release_manifest_receipt_matches_expected"] = (
        None
        if expected_release_manifest_receipt_sha256 is None
        else receipt_sha256 == expected_release_manifest_receipt_sha256
    )
    response["release_manifest_receipt_mismatch_reason"] = (
        "release manifest receipt sha256 does not match expected value"
        if response["release_manifest_receipt_matches_expected"] is False
        else ""
    )
    response["ledger_record_requested"] = bool(record)
    response["ledger_recorded"] = False
    response["ledger_record_path"] = str(_release_manifest_ledger_path(repo_path))
    response["ledger_record_index"] = None
    response["ledger_record_hash"] = None
    response["ledger_record_blocker"] = ""
    if record:
        if response.get("status") != "release_manifest_ready":
            response["ledger_record_blocker"] = "only ready release manifests can be recorded"
        elif response.get("release_manifest_receipt_matches_expected") is False:
            response["ledger_record_blocker"] = "release manifest receipt must match expected value before recording"
        else:
            response.update(_append_release_manifest_record(repo_path, response))
    return response


def _release_approval_blockers(release_gate_checks: dict[str, bool], readiness: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = [
        {"gate": gate, "reason": "release evidence gate did not pass", "details": []}
        for gate, passed in sorted(release_gate_checks.items())
        if passed is not True
    ]
    if readiness.get("production_ready") is not True:
        blockers.append(
            {
                "gate": "production_ready",
                "reason": "Production readiness must pass before release approval.",
                "details": [
                    str(item.get("gate"))
                    for item in readiness.get("blockers", [])
                    if isinstance(item, dict) and item.get("gate")
                ],
            }
        )
    return blockers


def release_manifest_ledger(repo_path: Path) -> dict[str, Any]:
    """Return release manifest ledger hash-chain status."""
    ensure_repo(repo_path)
    return {"repo": str(repo_path), "ledger": _release_manifest_ledger_status(repo_path)}


def release_manifest_drift(
    repo_path: Path,
    *,
    manifest_path: Path | None = None,
    classical_source_list_path: Path | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """Compare the current release manifest receipt with the latest recorded release ledger receipt."""
    ensure_repo(repo_path)
    ledger = _release_manifest_ledger_status(repo_path)
    expected_receipt = ledger.get("latest_release_manifest_receipt_sha256")
    if ledger.get("integrity_status") != "pass":
        drift = {
            "status": "not_checked",
            "passed": False,
            "live_requested": live,
            "expected_release_manifest_receipt_sha256": expected_receipt,
            "current_release_manifest_receipt_sha256": None,
            "matches_expected": False,
            "failures": ["release manifest ledger integrity must pass before drift can be checked"],
        }
    elif not expected_receipt:
        drift = {
            "status": "not_checked",
            "passed": False,
            "live_requested": live,
            "expected_release_manifest_receipt_sha256": None,
            "current_release_manifest_receipt_sha256": None,
            "matches_expected": False,
            "failures": ["release manifest ledger has no recorded release receipt"],
        }
    else:
        current = release_manifest(
            repo_path,
            manifest_path=manifest_path,
            classical_source_list_path=classical_source_list_path,
            live=live,
            expected_release_manifest_receipt_sha256=expected_receipt,
        )
        current_receipt = current.get("release_manifest_receipt", {}).get("sha256")
        matches = current.get("release_manifest_receipt_matches_expected") is True
        drift = {
            "status": "passed" if matches else "drift_detected",
            "passed": matches,
            "live_requested": live,
            "expected_release_manifest_receipt_sha256": expected_receipt,
            "current_release_manifest_receipt_sha256": current_receipt,
            "matches_expected": matches,
            "failures": [] if matches else ["current release manifest receipt does not match latest ledger record"],
        }
    return {
        "repo": str(repo_path),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "classical_source_list_path": str(classical_source_list_path) if classical_source_list_path else None,
        "ledger": ledger,
        "drift": drift,
    }


def _benchmark_response_receipt(benchmark_response: dict[str, Any]) -> dict[str, Any]:
    benchmark_payload = benchmark_response.get("benchmark", {})
    if isinstance(benchmark_payload, dict) and isinstance(benchmark_payload.get("benchmark_receipt"), dict):
        return benchmark_payload["benchmark_receipt"]
    if isinstance(benchmark_payload, dict) and isinstance(benchmark_payload.get("candidate"), dict):
        receipt = benchmark_payload["candidate"].get("benchmark_receipt")
        if isinstance(receipt, dict):
            return receipt
    return {}


def _benchmark_receipt_from_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    current_benchmark = readiness.get("current_benchmark", {})
    if isinstance(current_benchmark, dict) and isinstance(current_benchmark.get("benchmark_receipt"), dict):
        return current_benchmark["benchmark_receipt"]
    return {}


def _readiness_gate_by_id(readiness: Any, gate_id: str) -> dict[str, Any] | None:
    gates = readiness.get("gates", []) if isinstance(readiness, dict) else []
    if not isinstance(gates, list):
        return None
    for gate in gates:
        if isinstance(gate, dict) and gate.get("id") == gate_id:
            return gate
    return None


def _readiness_blocker_gate_ids(readiness: Any) -> set[str]:
    blockers = readiness.get("blockers", []) if isinstance(readiness, dict) else []
    if not isinstance(blockers, list):
        return set()
    return {
        str(blocker.get("gate"))
        for blocker in blockers
        if isinstance(blocker, dict) and isinstance(blocker.get("gate"), str)
    }


def _readiness_gate_decision_bound(readiness: Any, gate_id: str) -> bool:
    gate = _readiness_gate_by_id(readiness, gate_id)
    if not isinstance(gate, dict):
        return False
    if gate.get("passed") is True:
        return True
    return gate_id in _readiness_blocker_gate_ids(readiness)


def _release_provider_audit_contract_gates_bound(readiness: Any) -> bool:
    required_gates = (
        "ziwei_qimen_calculation_basis_audit_contract",
        "astrology_ephemeris_audit_contract",
        "xuanze_rule_table_audit_contract",
    )
    return all(_readiness_gate_decision_bound(readiness, gate_id) for gate_id in required_gates)


def _release_outcome_statistical_plan_preregistration_bound(readiness: Any) -> bool:
    gate_id = "outcome_dataset_statistical_plan_preregistered"
    gate = _readiness_gate_by_id(readiness, gate_id)
    if not isinstance(gate, dict):
        return False
    if gate.get("passed") is not True:
        return gate_id in _readiness_blocker_gate_ids(readiness)
    material = readiness.get("readiness_receipt", {}).get("material", {}) if isinstance(readiness, dict) else {}
    statistical_plan = (
        material.get("outcome_dataset", {}).get("statistical_plan", {}) if isinstance(material, dict) else {}
    )
    return isinstance(statistical_plan, dict) and statistical_plan.get("preregistration_complete") is True


def _release_classical_latest_refresh_receipt_bound(readiness: Any) -> bool:
    gate_id = "classical_source_latest_refresh_receipt_present"
    gate = _readiness_gate_by_id(readiness, gate_id)
    if not isinstance(gate, dict):
        return False
    if gate.get("passed") is not True:
        return gate_id in _readiness_blocker_gate_ids(readiness)
    return _classical_source_receipt_coverage(
        readiness.get("readiness_receipt", {}) if isinstance(readiness, dict) else {}
    ).get("refresh_receipt_present") is True


def _release_known_gap_command_coverage_bound(readiness: Any) -> bool:
    if not _readiness_gate_decision_bound(readiness, "known_gap_resolution_plan_covered"):
        return False
    material = readiness.get("readiness_receipt", {}).get("material", {}) if isinstance(readiness, dict) else {}
    coverage = material.get("known_gap_resolution_plan_coverage", {}) if isinstance(material, dict) else {}
    if not isinstance(coverage, dict):
        return False
    command_hash = coverage.get("command_coverage_sha256")
    return (
        coverage.get("coverage_complete") is True
        and coverage.get("command_validation_complete") is True
        and coverage.get("invalid_verification_commands_by_gap") == {}
        and coverage.get("invalid_verification_options_by_gap") == {}
        and isinstance(command_hash, str)
        and len(command_hash) == 64
    )


def _release_manifest_ledger_path(repo_path: Path) -> Path:
    return repo_path / "release" / "release_manifest_ledger.json"


def _append_release_manifest_record(repo_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    ledger_path = _release_manifest_ledger_path(repo_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if not isinstance(ledger, dict):
            raise ValueError("release manifest ledger must be a JSON object")
    else:
        ledger = {"schema_version": 1, "records": []}
    records = ledger.setdefault("records", [])
    if not isinstance(records, list):
        raise ValueError("release manifest ledger records must be a list")
    previous_hash = records[-1].get("record_hash") if records and isinstance(records[-1], dict) else None
    receipt = manifest.get("release_manifest_receipt", {})
    record = {
        "schema_version": 1,
        "index": len(records),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": manifest.get("status"),
        "release_manifest_receipt_sha256": receipt.get("sha256") if isinstance(receipt, dict) else None,
        "release_manifest_receipt": receipt,
        "coordinator_version": manifest.get("coordinator_version"),
        "candidate_name": manifest.get("candidate_name"),
        "production_readiness_status": manifest.get("production_readiness_status"),
        "production_ready": manifest.get("production_ready"),
        "release_approval_ready": manifest.get("release_approval_ready"),
        "release_approval_status": manifest.get("release_approval_status"),
        "release_blockers": manifest.get("release_blockers", []),
        "release_gate_checks": manifest.get("release_gate_checks", {}),
        "classical_source_list_path": manifest.get("classical_source_list_path"),
        "audit_receipt_sha256": manifest.get("audit_receipt", {}).get("sha256")
        if isinstance(manifest.get("audit_receipt"), dict)
        else None,
        "provider_protocols_receipt_sha256": manifest.get("provider_protocols_receipt", {}).get("sha256")
        if isinstance(manifest.get("provider_protocols_receipt"), dict)
        else None,
        "provider_protocols_receipt": manifest.get("provider_protocols_receipt", {}),
        "provider_onboarding_receipt_sha256": manifest.get("provider_onboarding_receipt", {}).get("sha256")
        if isinstance(manifest.get("provider_onboarding_receipt"), dict)
        else None,
        "provider_onboarding_receipt": manifest.get("provider_onboarding_receipt", {}),
        "github_comparison_receipt_sha256": manifest.get("github_comparison_receipt_sha256"),
        "github_comparison_receipt": manifest.get("github_comparison_receipt", {}),
        "plan_compliance_receipt_sha256": manifest.get("plan_compliance_receipt_sha256"),
        "plan_compliance_receipt": manifest.get("plan_compliance_receipt", {}),
        "benchmark_receipt_sha256": manifest.get("benchmark_receipt", {}).get("sha256")
        if isinstance(manifest.get("benchmark_receipt"), dict)
        else None,
        "readiness_receipt_sha256": manifest.get("readiness_receipt", {}).get("sha256")
        if isinstance(manifest.get("readiness_receipt"), dict)
        else None,
        "readiness_deliberation_receipt_coverage": _readiness_deliberation_receipt_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "annual_timeline_receipt_coverage": _annual_timeline_receipt_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "monthly_luck_receipt_coverage": _monthly_luck_receipt_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "auspicious_calendar_receipt_coverage": _auspicious_calendar_receipt_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "external_payload_birth_match_coverage": _external_payload_birth_match_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "provider_action_plan_coverage": _provider_action_plan_coverage(manifest.get("readiness_receipt", {})),
        "classical_source_receipt_coverage": _classical_source_receipt_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "known_gap_resolution_plan_coverage": _known_gap_resolution_plan_coverage(
            manifest.get("readiness_receipt", {})
        ),
        "known_gap_handoff_bundle": _known_gap_handoff_bundle_from_receipt(manifest.get("readiness_receipt", {})),
        "production_gate_registry_audit": _production_gate_registry_audit_from_receipt(
            manifest.get("readiness_receipt", {})
        ),
        "production_resolution_plan_summary": _production_resolution_plan_summary_from_receipt(
            manifest.get("readiness_receipt", {})
        ),
        "known_gap_ids": manifest.get("known_gap_ids", []),
        "outcome_dataset_receipt_sha256": manifest.get("outcome_dataset_receipt", {}).get("sha256")
        if isinstance(manifest.get("outcome_dataset_receipt"), dict)
        else None,
        "outcome_dataset": _outcome_dataset_receipt_material(manifest.get("outcome_dataset", {})),
        "evolution_trigger_receipt_sha256": manifest.get("evolution_trigger_receipt_sha256"),
        "evolution_trigger_receipt": manifest.get("evolution_trigger_receipt"),
        "evolution_trigger_receipt_current": manifest.get("evolution_trigger_receipt_current"),
        "previous_record_hash": previous_hash,
    }
    material = {key: value for key, value in record.items() if key != "record_hash"}
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    record["record_hash"] = hashlib.sha256(encoded).hexdigest()
    records.append(record)
    ledger["latest_record_hash"] = record["record_hash"]
    ledger["latest_record_index"] = record["index"]
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ledger_recorded": True,
        "ledger_record_path": str(ledger_path),
        "ledger_record_index": record["index"],
        "ledger_record_hash": record["record_hash"],
        "ledger_record_blocker": "",
    }


def _release_manifest_ledger_status(repo_path: Path) -> dict[str, Any]:
    ledger_path = _release_manifest_ledger_path(repo_path)
    if not ledger_path.exists():
        return {
            "path": str(ledger_path),
            "exists": False,
            "integrity_status": "fail",
            "record_count": 0,
            "latest_record_index": None,
            "latest_record_hash": None,
            "latest_release_manifest_receipt_sha256": None,
            "failures": ["release manifest ledger does not exist"],
        }
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "path": str(ledger_path),
            "exists": True,
            "integrity_status": "fail",
            "record_count": 0,
            "latest_record_index": None,
            "latest_record_hash": None,
            "latest_release_manifest_receipt_sha256": None,
            "failures": [f"release manifest ledger is not valid JSON: {exc}"],
        }
    records = ledger.get("records") if isinstance(ledger, dict) else None
    if not isinstance(records, list):
        return {
            "path": str(ledger_path),
            "exists": True,
            "integrity_status": "fail",
            "record_count": 0,
            "latest_record_index": None,
            "latest_record_hash": None,
            "latest_release_manifest_receipt_sha256": None,
            "failures": ["release manifest ledger records must be a list"],
        }
    failures = []
    previous_hash = None
    latest_record_index = None
    latest_receipt_sha256 = None
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            failures.append(f"record {index} is not an object")
            continue
        if record.get("index") != index:
            failures.append(f"record {index} has incorrect index")
        if record.get("previous_record_hash") != previous_hash:
            failures.append(f"record {index} previous_record_hash mismatch")
        failures.extend(_release_manifest_ledger_record_failures(index, record))
        material = {key: value for key, value in record.items() if key != "record_hash"}
        expected_hash = hashlib.sha256(
            json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        if record.get("record_hash") != expected_hash:
            failures.append(f"record {index} hash mismatch")
        previous_hash = record.get("record_hash")
        latest_record_index = index
        latest_receipt_sha256 = record.get("release_manifest_receipt_sha256")
    if isinstance(ledger, dict) and ledger.get("latest_record_hash") != previous_hash:
        failures.append("latest_record_hash does not match last record")
    if isinstance(ledger, dict) and ledger.get("latest_record_index") != latest_record_index:
        failures.append("latest_record_index does not match last record")
    return {
        "path": str(ledger_path),
        "exists": True,
        "integrity_status": "pass" if not failures else "fail",
        "record_count": len(records),
        "latest_record_index": latest_record_index,
        "latest_record_hash": previous_hash,
        "latest_release_manifest_receipt_sha256": latest_receipt_sha256,
        "failures": failures,
    }


def _release_manifest_ledger_record_failures(index: int, record: dict[str, Any]) -> list[str]:
    failures = []
    receipt = record.get("release_manifest_receipt")
    if not isinstance(receipt, dict):
        return [f"record {index} release_manifest_receipt is missing or invalid"]
    material = receipt.get("material")
    if not isinstance(material, dict):
        failures.append(f"record {index} release_manifest_receipt.material is missing or invalid")
        material = {}
    expected_receipt_sha256 = hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    if receipt.get("sha256") != expected_receipt_sha256:
        failures.append(f"record {index} release_manifest_receipt sha256 mismatch")
    if record.get("release_manifest_receipt_sha256") != receipt.get("sha256"):
        failures.append(f"record {index} release_manifest_receipt_sha256 mismatch")
    if record.get("status") != material.get("status"):
        failures.append(f"record {index} status does not match release manifest receipt")
    if record.get("candidate_name") != material.get("candidate_name"):
        failures.append(f"record {index} candidate_name does not match release manifest receipt")
    if record.get("coordinator_version") != material.get("coordinator_version"):
        failures.append(f"record {index} coordinator_version does not match release manifest receipt")
    if record.get("production_readiness_status") != material.get("production_readiness_status"):
        failures.append(f"record {index} production_readiness_status does not match release manifest receipt")
    if record.get("production_ready") != material.get("production_ready"):
        failures.append(f"record {index} production_ready does not match release manifest receipt")
    if record.get("release_approval_ready") != material.get("release_approval_ready"):
        failures.append(f"record {index} release_approval_ready does not match release manifest receipt")
    if record.get("release_approval_status") != material.get("release_approval_status"):
        failures.append(f"record {index} release_approval_status does not match release manifest receipt")
    if record.get("release_blockers") != material.get("release_blockers"):
        failures.append(f"record {index} release_blockers does not match release manifest receipt")
    if record.get("release_gate_checks") != material.get("release_gate_checks"):
        failures.append(f"record {index} release_gate_checks does not match release manifest receipt")
    if record.get("classical_source_list_path") != material.get("classical_source_list_path"):
        failures.append(f"record {index} classical_source_list_path does not match release manifest receipt")
    if record.get("audit_receipt_sha256") != material.get("audit_receipt_sha256"):
        failures.append(f"record {index} audit_receipt_sha256 does not match release manifest receipt")
    if record.get("provider_protocols_receipt_sha256") != material.get("provider_protocols_receipt_sha256"):
        failures.append(f"record {index} provider_protocols_receipt_sha256 does not match release manifest receipt")
    if record.get("provider_protocols_receipt") != material.get("provider_protocols_receipt"):
        failures.append(f"record {index} provider_protocols_receipt does not match release manifest receipt")
    if record.get("provider_onboarding_receipt_sha256") != material.get("provider_onboarding_receipt_sha256"):
        failures.append(f"record {index} provider_onboarding_receipt_sha256 does not match release manifest receipt")
    if record.get("provider_onboarding_receipt") != material.get("provider_onboarding_receipt"):
        failures.append(f"record {index} provider_onboarding_receipt does not match release manifest receipt")
    if record.get("github_comparison_receipt_sha256") != material.get("github_comparison_receipt_sha256"):
        failures.append(f"record {index} github_comparison_receipt_sha256 does not match release manifest receipt")
    if record.get("github_comparison_receipt") != material.get("github_comparison_receipt"):
        failures.append(f"record {index} github_comparison_receipt does not match release manifest receipt")
    if record.get("plan_compliance_receipt_sha256") != material.get("plan_compliance_receipt_sha256"):
        failures.append(f"record {index} plan_compliance_receipt_sha256 does not match release manifest receipt")
    if record.get("plan_compliance_receipt") != material.get("plan_compliance_receipt"):
        failures.append(f"record {index} plan_compliance_receipt does not match release manifest receipt")
    if record.get("benchmark_receipt_sha256") != material.get("benchmark_receipt_sha256"):
        failures.append(f"record {index} benchmark_receipt_sha256 does not match release manifest receipt")
    if record.get("readiness_receipt_sha256") != material.get("readiness_receipt_sha256"):
        failures.append(f"record {index} readiness_receipt_sha256 does not match release manifest receipt")
    if record.get("readiness_deliberation_receipt_coverage") != material.get(
        "readiness_deliberation_receipt_coverage"
    ):
        failures.append(
            f"record {index} readiness_deliberation_receipt_coverage does not match release manifest receipt"
        )
    if record.get("annual_timeline_receipt_coverage") != material.get("annual_timeline_receipt_coverage"):
        failures.append(f"record {index} annual_timeline_receipt_coverage does not match release manifest receipt")
    if record.get("monthly_luck_receipt_coverage") != material.get("monthly_luck_receipt_coverage"):
        failures.append(f"record {index} monthly_luck_receipt_coverage does not match release manifest receipt")
    if record.get("auspicious_calendar_receipt_coverage") != material.get(
        "auspicious_calendar_receipt_coverage"
    ):
        failures.append(
            f"record {index} auspicious_calendar_receipt_coverage does not match release manifest receipt"
        )
    if record.get("external_payload_birth_match_coverage") != material.get("external_payload_birth_match_coverage"):
        failures.append(
            f"record {index} external_payload_birth_match_coverage does not match release manifest receipt"
        )
    if record.get("provider_action_plan_coverage") != material.get("provider_action_plan_coverage"):
        failures.append(f"record {index} provider_action_plan_coverage does not match release manifest receipt")
    if record.get("classical_source_receipt_coverage") != material.get("classical_source_receipt_coverage"):
        failures.append(f"record {index} classical_source_receipt_coverage does not match release manifest receipt")
    if record.get("known_gap_resolution_plan_coverage") != material.get("known_gap_resolution_plan_coverage"):
        failures.append(f"record {index} known_gap_resolution_plan_coverage does not match release manifest receipt")
    if record.get("known_gap_handoff_bundle") != material.get("known_gap_handoff_bundle"):
        failures.append(f"record {index} known_gap_handoff_bundle does not match release manifest receipt")
    if record.get("production_gate_registry_audit") != material.get("production_gate_registry_audit"):
        failures.append(f"record {index} production_gate_registry_audit does not match release manifest receipt")
    if record.get("production_resolution_plan_summary") != material.get("production_resolution_plan_summary"):
        failures.append(f"record {index} production_resolution_plan_summary does not match release manifest receipt")
    if record.get("known_gap_ids") != material.get("known_gap_ids"):
        failures.append(f"record {index} known_gap_ids does not match release manifest receipt")
    if record.get("outcome_dataset_receipt_sha256") != material.get("outcome_dataset_receipt_sha256"):
        failures.append(f"record {index} outcome_dataset_receipt_sha256 does not match release manifest receipt")
    if record.get("outcome_dataset") != material.get("outcome_dataset"):
        failures.append(f"record {index} outcome_dataset does not match release manifest receipt")
    if record.get("evolution_trigger_receipt_sha256") != material.get("evolution_trigger_receipt_sha256"):
        failures.append(
            f"record {index} evolution_trigger_receipt_sha256 does not match release manifest receipt"
        )
    if record.get("evolution_trigger_receipt") != material.get("evolution_trigger_receipt"):
        failures.append(f"record {index} evolution_trigger_receipt does not match release manifest receipt")
    if record.get("evolution_trigger_receipt_current") != material.get("evolution_trigger_receipt_current"):
        failures.append(
            f"record {index} evolution_trigger_receipt_current does not match release manifest receipt"
        )
    return failures


def _release_manifest_receipt(response: dict[str, Any]) -> dict[str, Any]:
    audit_receipt = response.get("audit_receipt", {})
    audit_material = audit_receipt.get("material", {}) if isinstance(audit_receipt, dict) else {}
    benchmark_receipt = response.get("benchmark_receipt", {})
    readiness_receipt = response.get("readiness_receipt", {})
    outcome_dataset = response.get("outcome_dataset", {})
    outcome_dataset_receipt = response.get("outcome_dataset_receipt", {})
    provider_ledger = response.get("provider_ledger", {})
    material = {
        "schema_version": 1,
        "status": response.get("status"),
        "release_gate_checks": response.get("release_gate_checks", {}),
        "coordinator_version": response.get("coordinator_version"),
        "candidate_name": response.get("candidate_name"),
        "live_requested": response.get("live_requested"),
        "classical_source_list_path": response.get("classical_source_list_path"),
        "history_integrity_status": response.get("history_integrity", {}).get("status")
        if isinstance(response.get("history_integrity"), dict)
        else None,
        "archive_integrity_status": response.get("archive_integrity", {}).get("status")
        if isinstance(response.get("archive_integrity"), dict)
        else None,
        "lineage_integrity_status": response.get("lineage_integrity", {}).get("status")
        if isinstance(response.get("lineage_integrity"), dict)
        else None,
        "audit_receipt_sha256": audit_receipt.get("sha256") if isinstance(audit_receipt, dict) else None,
        "audit_receipt_matches_expected": response.get("audit_receipt_matches_expected"),
        "provider_protocols_receipt_sha256": response.get("provider_protocols_receipt", {}).get("sha256")
        if isinstance(response.get("provider_protocols_receipt"), dict)
        else None,
        "provider_protocols_receipt": response.get("provider_protocols_receipt", {}),
        "provider_onboarding_receipt_sha256": response.get("provider_onboarding_receipt", {}).get("sha256")
        if isinstance(response.get("provider_onboarding_receipt"), dict)
        else None,
        "provider_onboarding_receipt": response.get("provider_onboarding_receipt", {}),
        "github_comparison_receipt_sha256": response.get("github_comparison_receipt_sha256"),
        "github_comparison_receipt": response.get("github_comparison_receipt", {}),
        "plan_compliance_receipt_sha256": response.get("plan_compliance_receipt_sha256"),
        "plan_compliance_receipt": response.get("plan_compliance_receipt", {}),
        "method_surface": audit_material.get("method_surface", {}) if isinstance(audit_material, dict) else {},
        "benchmark_receipt_sha256": benchmark_receipt.get("sha256") if isinstance(benchmark_receipt, dict) else None,
        "benchmark_receipt_matches_expected": response.get("benchmark_receipt_matches_expected"),
        "readiness_receipt_sha256": readiness_receipt.get("sha256") if isinstance(readiness_receipt, dict) else None,
        "readiness_receipt_matches_expected": response.get("readiness_receipt_matches_expected"),
        "readiness_deliberation_receipt_coverage": _readiness_deliberation_receipt_coverage(readiness_receipt),
        "annual_timeline_receipt_coverage": _annual_timeline_receipt_coverage(readiness_receipt),
        "monthly_luck_receipt_coverage": _monthly_luck_receipt_coverage(readiness_receipt),
        "auspicious_calendar_receipt_coverage": _auspicious_calendar_receipt_coverage(readiness_receipt),
        "external_payload_birth_match_coverage": _external_payload_birth_match_coverage(readiness_receipt),
        "provider_action_plan_coverage": _provider_action_plan_coverage(readiness_receipt),
        "classical_source_receipt_coverage": _classical_source_receipt_coverage(readiness_receipt),
        "known_gap_resolution_plan_coverage": _known_gap_resolution_plan_coverage(readiness_receipt),
        "known_gap_handoff_bundle": _known_gap_handoff_bundle_from_receipt(readiness_receipt),
        "production_gate_registry_audit": _production_gate_registry_audit_from_receipt(readiness_receipt),
        "production_resolution_plan_summary": _production_resolution_plan_summary_from_receipt(readiness_receipt),
        "production_readiness_status": response.get("production_readiness_status"),
        "production_ready": response.get("production_ready"),
        "release_approval_ready": response.get("release_approval_ready"),
        "release_approval_status": response.get("release_approval_status"),
        "release_blockers": response.get("release_blockers", []),
        "known_gap_ids": response.get("known_gap_ids", []),
        "outcome_dataset_receipt_sha256": outcome_dataset_receipt.get("sha256")
        if isinstance(outcome_dataset_receipt, dict)
        else None,
        "provider_ledger": {
            "integrity_status": provider_ledger.get("integrity_status") if isinstance(provider_ledger, dict) else None,
            "coverage_status": provider_ledger.get("coverage_status") if isinstance(provider_ledger, dict) else None,
            "protocol_status": provider_ledger.get("protocol_status") if isinstance(provider_ledger, dict) else None,
            "request_receipt_status": provider_ledger.get("request_receipt_status")
            if isinstance(provider_ledger, dict)
            else None,
            "reference_contract_status": provider_ledger.get("reference_contract_status")
            if isinstance(provider_ledger, dict)
            else None,
            "command_fingerprint_status": provider_ledger.get("command_fingerprint_status")
            if isinstance(provider_ledger, dict)
            else None,
            "record_count": provider_ledger.get("record_count") if isinstance(provider_ledger, dict) else None,
            "latest_record_hash": provider_ledger.get("latest_record_hash") if isinstance(provider_ledger, dict) else None,
            "latest_record_index": provider_ledger.get("latest_record_index") if isinstance(provider_ledger, dict) else None,
            "missing_domains": provider_ledger.get("missing_domains", []) if isinstance(provider_ledger, dict) else [],
            "request_receipt_failures": provider_ledger.get("request_receipt_failures", [])
            if isinstance(provider_ledger, dict)
            else [],
            "reference_contract_failures": provider_ledger.get("reference_contract_failures", [])
            if isinstance(provider_ledger, dict)
            else [],
            "command_fingerprint_failures": provider_ledger.get("command_fingerprint_failures", [])
            if isinstance(provider_ledger, dict)
            else [],
        },
        "outcome_dataset": {
            **_outcome_dataset_receipt_material(outcome_dataset),
        },
        "evolution_trigger_receipt_sha256": response.get("evolution_trigger_receipt_sha256"),
        "evolution_trigger_receipt": response.get("evolution_trigger_receipt"),
        "evolution_trigger_receipt_current": response.get("evolution_trigger_receipt_current"),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _readiness_deliberation_receipt_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "case_count": 0,
            "covered_count": 0,
            "coverage_complete": False,
            "receipt_count": 0,
            "claim_counts": [],
            "receipt_sha256s": [],
        }
    material = readiness_receipt.get("material", {})
    current_benchmark = material.get("current_benchmark", {}) if isinstance(material, dict) else {}
    audit = (
        current_benchmark.get("request_provenance_audit", {})
        if isinstance(current_benchmark, dict)
        else {}
    )
    if not isinstance(audit, dict):
        audit = {}
    receipts = audit.get("deliberation_receipts", [])
    if not isinstance(receipts, list):
        receipts = []
    receipt_sha256s = sorted(
        item.get("sha256")
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("sha256"), str) and len(item.get("sha256", "")) == 64
    )
    claim_counts = sorted(
        int(item.get("claim_count"))
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("claim_count"), int)
    )
    case_count = audit.get("case_count") if isinstance(audit.get("case_count"), int) else 0
    covered_count = (
        audit.get("deliberation_receipt_covered_count")
        if isinstance(audit.get("deliberation_receipt_covered_count"), int)
        else 0
    )
    return {
        "case_count": case_count,
        "covered_count": covered_count,
        "coverage_complete": case_count > 0 and covered_count == case_count and len(receipt_sha256s) == case_count,
        "receipt_count": len(receipt_sha256s),
        "claim_counts": claim_counts,
        "receipt_sha256s": receipt_sha256s,
    }


def _annual_timeline_receipt_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "case_count": 0,
            "covered_count": 0,
            "bound_count": 0,
            "coverage_complete": False,
            "binding_complete": False,
            "receipt_count": 0,
            "row_counts": [],
            "receipt_sha256s": [],
            "unbound_cases": [],
        }
    material = readiness_receipt.get("material", {})
    current_benchmark = material.get("current_benchmark", {}) if isinstance(material, dict) else {}
    audit = (
        current_benchmark.get("request_provenance_audit", {})
        if isinstance(current_benchmark, dict)
        else {}
    )
    if not isinstance(audit, dict):
        audit = {}
    receipts = audit.get("annual_timeline_receipts", [])
    if not isinstance(receipts, list):
        receipts = []
    receipt_sha256s = sorted(
        item.get("sha256")
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("sha256"), str) and len(item.get("sha256", "")) == 64
    )
    row_counts = sorted(
        int(item.get("row_count"))
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("row_count"), int)
    )
    case_count = audit.get("case_count") if isinstance(audit.get("case_count"), int) else 0
    covered_count = (
        audit.get("annual_timeline_receipt_covered_count")
        if isinstance(audit.get("annual_timeline_receipt_covered_count"), int)
        else 0
    )
    bound_count = (
        audit.get("annual_timeline_receipt_bound_count")
        if isinstance(audit.get("annual_timeline_receipt_bound_count"), int)
        else 0
    )
    unbound_cases = audit.get("annual_timeline_unbound_cases", [])
    if not isinstance(unbound_cases, list):
        unbound_cases = []
    return {
        "case_count": case_count,
        "covered_count": covered_count,
        "bound_count": bound_count,
        "coverage_complete": case_count > 0 and covered_count == case_count and len(receipt_sha256s) == case_count,
        "binding_complete": case_count > 0 and bound_count == case_count and not unbound_cases,
        "receipt_count": len(receipt_sha256s),
        "row_counts": row_counts,
        "receipt_sha256s": receipt_sha256s,
        "unbound_cases": [str(item) for item in unbound_cases],
    }


def _monthly_luck_receipt_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "case_count": 0,
            "covered_count": 0,
            "bound_count": 0,
            "coverage_complete": False,
            "binding_complete": False,
            "receipt_count": 0,
            "row_counts": [],
            "receipt_sha256s": [],
            "unbound_cases": [],
        }
    material = readiness_receipt.get("material", {})
    current_benchmark = material.get("current_benchmark", {}) if isinstance(material, dict) else {}
    audit = (
        current_benchmark.get("request_provenance_audit", {})
        if isinstance(current_benchmark, dict)
        else {}
    )
    if not isinstance(audit, dict):
        audit = {}
    receipts = audit.get("monthly_luck_receipts", [])
    if not isinstance(receipts, list):
        receipts = []
    receipt_sha256s = sorted(
        item.get("sha256")
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("sha256"), str) and len(item.get("sha256", "")) == 64
    )
    row_counts = sorted(
        int(item.get("row_count"))
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("row_count"), int)
    )
    case_count = audit.get("case_count") if isinstance(audit.get("case_count"), int) else 0
    covered_count = (
        audit.get("monthly_luck_receipt_covered_count")
        if isinstance(audit.get("monthly_luck_receipt_covered_count"), int)
        else 0
    )
    bound_count = (
        audit.get("monthly_luck_receipt_bound_count")
        if isinstance(audit.get("monthly_luck_receipt_bound_count"), int)
        else 0
    )
    unbound_cases = audit.get("monthly_luck_unbound_cases", [])
    if not isinstance(unbound_cases, list):
        unbound_cases = []
    return {
        "case_count": case_count,
        "covered_count": covered_count,
        "bound_count": bound_count,
        "coverage_complete": case_count > 0 and covered_count == case_count and len(receipt_sha256s) == case_count,
        "binding_complete": case_count > 0 and bound_count == case_count and not unbound_cases,
        "receipt_count": len(receipt_sha256s),
        "row_counts": row_counts,
        "receipt_sha256s": receipt_sha256s,
        "unbound_cases": [str(item) for item in unbound_cases],
    }


def _auspicious_calendar_receipt_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "case_count": 0,
            "covered_count": 0,
            "bound_count": 0,
            "coverage_complete": False,
            "binding_complete": False,
            "receipt_count": 0,
            "row_counts": [],
            "receipt_sha256s": [],
            "unbound_cases": [],
        }
    material = readiness_receipt.get("material", {})
    current_benchmark = material.get("current_benchmark", {}) if isinstance(material, dict) else {}
    audit = (
        current_benchmark.get("request_provenance_audit", {})
        if isinstance(current_benchmark, dict)
        else {}
    )
    if not isinstance(audit, dict):
        audit = {}
    receipts = audit.get("auspicious_calendar_receipts", [])
    if not isinstance(receipts, list):
        receipts = []
    receipt_sha256s = sorted(
        item.get("sha256")
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("sha256"), str) and len(item.get("sha256", "")) == 64
    )
    row_counts = sorted(
        int(item.get("row_count"))
        for item in receipts
        if isinstance(item, dict) and isinstance(item.get("row_count"), int)
    )
    case_count = audit.get("case_count") if isinstance(audit.get("case_count"), int) else 0
    covered_count = (
        audit.get("auspicious_calendar_receipt_covered_count")
        if isinstance(audit.get("auspicious_calendar_receipt_covered_count"), int)
        else 0
    )
    bound_count = (
        audit.get("auspicious_calendar_receipt_bound_count")
        if isinstance(audit.get("auspicious_calendar_receipt_bound_count"), int)
        else 0
    )
    unbound_cases = audit.get("auspicious_calendar_unbound_cases", [])
    if not isinstance(unbound_cases, list):
        unbound_cases = []
    return {
        "case_count": case_count,
        "covered_count": covered_count,
        "bound_count": bound_count,
        "coverage_complete": case_count > 0 and covered_count == case_count and len(receipt_sha256s) == case_count,
        "binding_complete": case_count > 0 and bound_count == case_count and not unbound_cases,
        "receipt_count": len(receipt_sha256s),
        "row_counts": row_counts,
        "receipt_sha256s": receipt_sha256s,
        "unbound_cases": [str(item) for item in unbound_cases],
    }


def _external_payload_birth_match_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "case_count": 0,
            "match_case_count": 0,
            "coverage_complete": False,
            "mismatch_domains": [],
            "match_cases": [],
        }
    material = readiness_receipt.get("material", {})
    current_benchmark = material.get("current_benchmark", {}) if isinstance(material, dict) else {}
    audit = (
        current_benchmark.get("request_provenance_audit", {})
        if isinstance(current_benchmark, dict)
        else {}
    )
    if not isinstance(audit, dict):
        audit = {}
    cases = audit.get("external_payload_birth_match_cases", [])
    if not isinstance(cases, list):
        cases = []
    match_cases = [
        {
            "case": item.get("case"),
            "matches_ok": item.get("matches_ok") is True,
            "mismatch_domains": item.get("mismatch_domains", []) if isinstance(item.get("mismatch_domains"), list) else [],
            "statuses": item.get("statuses", []) if isinstance(item.get("statuses"), list) else [],
        }
        for item in cases
        if isinstance(item, dict)
    ]
    mismatch_domains = audit.get("external_payload_birth_mismatch_domains", [])
    if not isinstance(mismatch_domains, list):
        mismatch_domains = []
    case_count = audit.get("case_count") if isinstance(audit.get("case_count"), int) else 0
    match_case_count = (
        audit.get("external_payload_birth_match_case_count")
        if isinstance(audit.get("external_payload_birth_match_case_count"), int)
        else len(match_cases)
    )
    return {
        "case_count": case_count,
        "match_case_count": match_case_count,
        "coverage_complete": match_case_count > 0 and not mismatch_domains and audit.get("external_payload_birth_matches_ok") is True,
        "mismatch_domains": sorted(str(item) for item in mismatch_domains),
        "match_cases": match_cases,
    }


def _provider_action_plan_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "case_count": 0,
            "covered_count": 0,
            "coverage_complete": False,
            "unresolved": [],
            "action_plan_counts": [],
        }
    material = readiness_receipt.get("material", {})
    current_benchmark = material.get("current_benchmark", {}) if isinstance(material, dict) else {}
    audit = (
        current_benchmark.get("provider_action_plan_audit", {})
        if isinstance(current_benchmark, dict)
        else {}
    )
    if not isinstance(audit, dict):
        audit = {}
    case_count = audit.get("case_count") if isinstance(audit.get("case_count"), int) else 0
    covered_count = audit.get("covered_count") if isinstance(audit.get("covered_count"), int) else 0
    unresolved = audit.get("unresolved") if isinstance(audit.get("unresolved"), list) else []
    action_plan_counts = audit.get("action_plan_counts") if isinstance(audit.get("action_plan_counts"), list) else []
    return {
        "case_count": case_count,
        "covered_count": covered_count,
        "coverage_complete": bool(audit.get("coverage_complete")) and case_count > 0 and covered_count == case_count,
        "unresolved": unresolved,
        "action_plan_counts": action_plan_counts,
    }


def _receipt_material_sha256(receipt: Any) -> str | None:
    if not isinstance(receipt, dict) or not isinstance(receipt.get("material"), dict):
        return None
    encoded = json.dumps(receipt["material"], sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _classical_source_receipt_coverage(readiness_receipt: Any) -> dict[str, Any]:
    if not isinstance(readiness_receipt, dict):
        return {
            "status": None,
            "valid": None,
            "receipt_present": False,
            "source_list_receipt_sha256": None,
            "source_list_receipt_material_sha256": None,
            "refresh_receipt_present": False,
            "latest_refresh_receipt_sha256": None,
            "latest_refresh_record_count": None,
            "source_count": None,
            "locked_source_count": None,
        }
    material = readiness_receipt.get("material", {})
    refresh = material.get("classical_source_refresh", {}) if isinstance(material, dict) else {}
    if not isinstance(refresh, dict):
        refresh = {}
    receipt_sha = refresh.get("source_list_receipt_sha256")
    receipt_material_sha = refresh.get("source_list_receipt_material_sha256")
    receipt_present = isinstance(receipt_sha, str) and len(receipt_sha) == 64
    receipt_material_present = isinstance(receipt_material_sha, str) and len(receipt_material_sha) == 64
    refresh_receipt_sha = refresh.get("latest_refresh_receipt_sha256")
    refresh_receipt_present = isinstance(refresh_receipt_sha, str) and len(refresh_receipt_sha) == 64
    return {
        "status": refresh.get("status"),
        "valid": refresh.get("valid"),
        "receipt_present": receipt_present,
        "source_list_receipt_sha256": receipt_sha if receipt_present else None,
        "source_list_receipt_material_sha256": receipt_material_sha if receipt_material_present else None,
        "refresh_receipt_present": refresh_receipt_present,
        "latest_refresh_receipt_sha256": refresh_receipt_sha if refresh_receipt_present else None,
        "latest_refresh_record_count": refresh.get("latest_refresh_record_count")
        if isinstance(refresh.get("latest_refresh_record_count"), int)
        else None,
        "source_count": refresh.get("source_count") if isinstance(refresh.get("source_count"), int) else None,
        "locked_source_count": refresh.get("locked_source_count")
        if isinstance(refresh.get("locked_source_count"), int)
        else None,
    }


def _known_gap_resolution_plan_coverage(readiness_receipt: Any) -> dict[str, Any]:
    fallback = {
        "known_gap_count": 0,
        "plan_item_count": 0,
        "covered_count": 0,
        "coverage_complete": False,
        "planned_gap_ids": [],
        "missing_gap_ids": [],
        "invalid_plan_gap_ids": [],
        "invalid_gate_ids_by_gap": {},
        "invalid_verification_commands_by_gap": {},
        "invalid_verification_options_by_gap": {},
        "valid_production_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
        "valid_cli_subcommands": [],
        "valid_cli_options_by_subcommand": {},
        "command_validation_complete": False,
        "command_subcommands_by_gap": {},
        "command_options_by_gap": {},
        "command_counts": {},
        "gate_counts": {},
        "command_coverage_sha256": None,
        "plan_coverage_sha256": None,
        "audit_plan_hash": None,
    }
    if not isinstance(readiness_receipt, dict):
        return fallback
    material = readiness_receipt.get("material", {})
    if not isinstance(material, dict):
        return fallback
    coverage = material.get("known_gap_resolution_plan_coverage")
    return coverage if isinstance(coverage, dict) else fallback


def _known_gap_handoff_bundle_from_receipt(readiness_receipt: Any) -> dict[str, Any]:
    fallback = {
        "bundle_version": "known-gap-handoff-v1",
        "status": "incomplete",
        "gap_count": 0,
        "open_gap_ids": [],
        "missing_handoff_gap_ids": [],
        "items": [],
        "bundle_sha256": "",
    }
    if not isinstance(readiness_receipt, dict):
        return fallback
    material = readiness_receipt.get("material", {})
    if not isinstance(material, dict):
        return fallback
    bundle = material.get("known_gap_handoff_bundle")
    return bundle if isinstance(bundle, dict) else fallback


def _production_gate_registry_audit_from_receipt(readiness_receipt: Any) -> dict[str, Any]:
    def fallback() -> dict[str, Any]:
        material = {
            "actual_gate_ids": [],
            "registry_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
            "missing_from_registry": [],
            "registry_only_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
        }
        return {
            "actual_gate_count": 0,
            "registry_gate_count": len(PRODUCTION_READINESS_GATE_IDS),
            "actual_gate_ids": [],
            "registry_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
            "missing_from_registry": [],
            "registry_only_gate_ids": sorted(PRODUCTION_READINESS_GATE_IDS),
            "registry_current": False,
            "registry_audit_sha256": hashlib.sha256(
                json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
            ).hexdigest(),
        }

    if not isinstance(readiness_receipt, dict):
        return fallback()
    material = readiness_receipt.get("material", {})
    if not isinstance(material, dict):
        return fallback()
    audit = material.get("production_gate_registry_audit")
    return audit if isinstance(audit, dict) else fallback()


def _production_resolution_plan_summary_from_receipt(readiness_receipt: Any) -> dict[str, Any]:
    fallback = {
        "status": None,
        "step_count": 0,
        "step_ids": [],
        "categories": [],
        "command_count": 0,
        "diagnostic_count": 0,
        "checklist_count": 0,
        "resolution_plan_sha256": None,
    }
    if not isinstance(readiness_receipt, dict):
        return fallback
    material = readiness_receipt.get("material", {})
    if not isinstance(material, dict):
        return fallback
    summary = material.get("production_resolution_plan_summary")
    return summary if isinstance(summary, dict) else fallback


def schema_document() -> dict[str, Any]:
    """Return a compact JSON schema document for service clients."""
    external_payload_schema = {
        "type": "object",
        "required": ["source", "version", "license_or_review"],
        "properties": {
            "source": {"type": "string"},
            "version": {"type": "string"},
            "license_or_review": {"type": "string"},
        },
        "additionalProperties": True,
    }
    birth_properties = {
        "name": {"type": "string"},
        "birth_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "birth_time": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
        "gender": {"type": "string"},
        "birthplace": {"type": "string"},
        "birth_place": {"type": "string"},
        "latitude": {"type": "number"},
        "longitude": {"type": "number"},
        "timezone_offset": {"type": ["number", "string"]},
        "utc_offset": {"type": ["number", "string"]},
        "house_system": {"type": "string"},
        "professional_charts": {
            "type": "object",
            "description": "Optional externally supplied professional Zi Wei/Qi Men/astrology chart payloads.",
            "properties": {
                "bazi": external_payload_schema,
                "ziwei": external_payload_schema,
                "qimen": external_payload_schema,
                "astrology": external_payload_schema,
                "xuanze": external_payload_schema,
            },
        },
    }
    return {
        "openapi_fragment": False,
        "schemas": {
            "AnalyzeRequest": {
                "type": "object",
                "required": ["birth"],
                "properties": {
                    "birth": {
                        "type": "object",
                        "required": ["name", "birth_date", "birth_time", "gender"],
                        "properties": birth_properties,
                        "anyOf": [
                            {"required": ["birthplace"]},
                            {"required": ["birth_place"]},
                        ],
                    },
                    "annual_start_year": {"type": "integer"},
                    "annual_end_year": {"type": "integer"},
                    "monthly_years": {"type": "array", "items": {"type": "integer"}},
                    "auspicious_start_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "auspicious_end_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "calendar_provider": {"type": "string", "enum": ["approximate", "auto", "professional"]},
                    "language": {"type": "string", "enum": ["en", "zh"]},
                    "llm_synthesis": {
                        "oneOf": [
                            {"type": "boolean"},
                            {
                                "type": "object",
                                "properties": {
                                    "enabled": {"type": "boolean"},
                                },
                            },
                        ],
                    },
                    "expected": {"type": "object"},
                },
            },
            "EvolveRequest": {
                "type": "object",
                "required": ["input", "feedback"],
                "properties": {
                    "input": {"$ref": "#/schemas/AnalyzeRequest"},
                    "feedback": {"type": "object"},
                    "validate_on_input": {"type": "boolean"},
                },
            },
            "EvolutionSelectionDecision": {
                "type": "object",
                "required": ["accepted", "selected", "validation_task_count", "gates", "rejection_reasons"],
                "properties": {
                    "accepted": {"type": "boolean"},
                    "selected": {"type": ["string", "null"]},
                    "baseline_average_score": {"type": ["number", "null"]},
                    "selected_average_score": {"type": ["number", "null"]},
                    "selected_adjusted_score": {"type": ["number", "null"]},
                    "validation_average_score": {"type": ["number", "null"]},
                    "validation_task_count": {"type": "integer"},
                    "gates": {"type": "object", "additionalProperties": {"type": "boolean"}},
                    "rejection_reasons": {"type": "array", "items": {"type": "string"}},
                },
            },
            "EvolutionTriggerReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "repo",
                    "trigger_reasons",
                    "feedback_present",
                    "feedback_correction_count",
                    "feedback_sha256",
                    "task_input_sha256",
                    "train_task_count",
                    "train_task_sha256",
                    "validation_task_count",
                    "validation_task_sha256",
                    "validate_on_input",
                    "outcome_dataset_gate_passed",
                    "outcome_dataset_gate_reason",
                    "outcome_dataset_gate_blocking_failures",
                    "policy",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "evolution-trigger-receipt-v1"},
                    "repo": {"type": "string"},
                    "trigger_reasons": {"type": "array", "items": {"type": "string"}},
                    "feedback_present": {"type": "boolean"},
                    "feedback_correction_count": {"type": "integer"},
                    "feedback_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "task_input_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "train_task_count": {"type": "integer"},
                    "train_task_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "validation_task_count": {"type": "integer"},
                    "validation_task_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "validate_on_input": {"type": "boolean"},
                    "outcome_dataset_gate_passed": {"type": "boolean"},
                    "outcome_dataset_gate_reason": {"type": "string"},
                    "outcome_dataset_gate_blocking_failures": {"type": "array", "items": {"type": "string"}},
                    "policy": {"type": "string"},
                },
            },
            "EvolutionTriggerReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "evolution-trigger-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/EvolutionTriggerReceiptMaterial"},
                },
            },
            "MemoryProfile": {
                "type": "object",
                "required": [
                    "correction_counts",
                    "unsafe_corrections",
                    "unsafe_feedback_count",
                    "strategy_priors",
                    "total_events",
                ],
                "properties": {
                    "correction_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "unsafe_corrections": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "unsafe_feedback_count": {"type": "integer"},
                    "strategy_priors": {"type": "object", "additionalProperties": {"type": "number"}},
                    "total_events": {"type": "integer"},
                },
            },
            "EvolveResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "accepted",
                    "blocked",
                    "validation_gate",
                    "trigger_receipt",
                    "selection_decision",
                    "before_version",
                    "after_version",
                    "validation_case_count",
                    "memory_profile",
                    "archive_events",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "accepted": {"type": "boolean"},
                    "blocked": {"type": "boolean"},
                    "block_reason": {"type": "string"},
                    "validation_gate": {"type": "object"},
                    "trigger_receipt": {"$ref": "#/schemas/EvolutionTriggerReceipt"},
                    "selection_decision": {"$ref": "#/schemas/EvolutionSelectionDecision"},
                    "before_version": {"type": "integer"},
                    "after_version": {"type": "integer"},
                    "selected": {"type": ["string", "null"]},
                    "workflow": {"type": ["object", "null"]},
                    "validation_case_count": {"type": "integer"},
                    "memory_profile": {"$ref": "#/schemas/MemoryProfile"},
                    "archive_events": {"type": "integer"},
                },
            },
            "LatestEvolutionStatus": {
                "type": "object",
                "required": [
                    "event",
                    "timestamp",
                    "accepted",
                    "selected",
                    "pareto_front",
                    "archive_hash",
                    "previous_archive_hash",
                    "selection_decision",
                    "trigger_receipt",
                    "reproducibility_manifest",
                ],
                "properties": {
                    "event": {"type": ["string", "null"]},
                    "timestamp": {"type": ["string", "null"]},
                    "accepted": {"type": ["boolean", "null"]},
                    "selected": {"type": ["string", "null"]},
                    "pareto_front": {"type": "array", "items": {"type": "string"}},
                    "archive_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "previous_archive_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "selection_decision": {
                        "anyOf": [
                            {"$ref": "#/schemas/EvolutionSelectionDecision"},
                            {"type": "null"},
                        ]
                    },
                    "trigger_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/EvolutionTriggerReceipt"},
                            {"type": "null"},
                        ]
                    },
                    "reproducibility_manifest": {
                        "anyOf": [
                            {"$ref": "#/schemas/ReproducibilityManifest"},
                            {"type": "null"},
                        ]
                    },
                },
            },
            "ArchiveIntegrityReport": {
                "type": "object",
                "required": [
                    "status",
                    "event_count",
                    "hashed_event_count",
                    "legacy_event_count",
                    "latest_hash",
                    "failures",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "fail"]},
                    "event_count": {"type": "integer"},
                    "hashed_event_count": {"type": "integer"},
                    "legacy_event_count": {"type": "integer"},
                    "latest_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "GenomeLineage": {
                "type": "object",
                "required": [
                    "event",
                    "archive_hash",
                    "previous_archive_hash",
                    "archive_timestamp",
                    "genome_fingerprint",
                    "baseline_genome_version",
                    "accepted_genome_version",
                    "selected_strategy",
                    "selection_decision",
                    "trigger_receipt",
                    "reproducibility_manifest",
                ],
                "properties": {
                    "event": {"type": "string", "enum": ["population_evolution", "rollback"]},
                    "archive_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "previous_archive_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "archive_timestamp": {"type": ["string", "null"]},
                    "genome_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "baseline_genome_version": {"type": "integer"},
                    "accepted_genome_version": {"type": "integer"},
                    "selected_strategy": {"type": ["string", "null"]},
                    "selection_decision": {
                        "anyOf": [
                            {"$ref": "#/schemas/EvolutionSelectionDecision"},
                            {"type": "null"},
                        ]
                    },
                    "trigger_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/EvolutionTriggerReceipt"},
                            {"type": "null"},
                        ]
                    },
                    "reproducibility_manifest": {
                        "anyOf": [
                            {"$ref": "#/schemas/ReproducibilityManifest"},
                            {"type": "null"},
                        ]
                    },
                    "rollback_target_version": {"type": "integer"},
                    "rollback_reason": {"type": "string"},
                },
            },
            "LineageIntegrityReport": {
                "type": "object",
                "required": [
                    "status",
                    "checked",
                    "failures",
                    "archive_hash_matches_latest",
                    "genome_fingerprint_matches",
                    "genome_version_matches",
                    "selection_decision_matches",
                    "trigger_receipt_matches",
                    "reproducibility_manifest_matches",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "fail", "missing", "not_applicable"]},
                    "checked": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                    "archive_hash_matches_latest": {"type": "boolean"},
                    "genome_fingerprint_matches": {"type": "boolean"},
                    "genome_version_matches": {"type": "boolean"},
                    "selection_decision_matches": {"type": "boolean"},
                    "trigger_receipt_matches": {"type": "boolean"},
                    "reproducibility_manifest_matches": {"type": "boolean"},
                },
            },
            "VersionHistoryRow": {
                "type": "object",
                "required": [
                    "version",
                    "parent_version",
                    "is_latest",
                    "candidate_name",
                    "evolution_strategies",
                    "workflow",
                    "genome_fingerprint",
                    "lineage_present",
                    "lineage_event",
                    "lineage_archive_hash",
                    "trigger_receipt_sha256",
                    "lineage_fingerprint_matches",
                    "archive_event_found",
                    "archive_event_index",
                    "archive_event_timestamp",
                ],
                "properties": {
                    "version": {"type": "integer"},
                    "parent_version": {"type": ["integer", "null"]},
                    "is_latest": {"type": "boolean"},
                    "candidate_name": {"type": ["string", "null"]},
                    "evolution_strategies": {"type": "array", "items": {"type": "string"}},
                    "workflow": {"type": ["object", "null"]},
                    "genome_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "lineage_present": {"type": "boolean"},
                    "lineage_event": {"type": ["string", "null"], "enum": ["population_evolution", "rollback", None]},
                    "lineage_archive_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "trigger_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "lineage_fingerprint_matches": {"type": "boolean"},
                    "baseline_genome_version": {"type": ["integer", "null"]},
                    "accepted_genome_version": {"type": ["integer", "null"]},
                    "selected_strategy": {"type": ["string", "null"]},
                    "rollback_target_version": {"type": ["integer", "null"]},
                    "rollback_reason": {"type": ["string", "null"]},
                    "archive_event_found": {"type": "boolean"},
                    "archive_event_index": {"type": ["integer", "null"]},
                    "archive_event_timestamp": {"type": ["string", "null"]},
                    "archive_event_selected": {"type": ["string", "null"]},
                    "archive_event_accepted": {"type": ["boolean", "null"]},
                },
            },
            "VersionHistoryResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "agent_name",
                    "latest_version",
                    "version_count",
                    "versions",
                    "archive_events",
                    "archive_integrity",
                    "history_integrity",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "agent_name": {"type": "string", "const": "mingli_orchestrator"},
                    "latest_version": {"type": "integer"},
                    "version_count": {"type": "integer"},
                    "versions": {"type": "array", "items": {"$ref": "#/schemas/VersionHistoryRow"}},
                    "archive_events": {"type": "integer"},
                    "archive_integrity": {"$ref": "#/schemas/ArchiveIntegrityReport"},
                    "history_integrity": {"$ref": "#/schemas/VersionHistoryIntegrity"},
                },
            },
            "VersionHistoryIntegrity": {
                "type": "object",
                "required": [
                    "status",
                    "checked",
                    "checked_versions",
                    "latest_version",
                    "lineage_missing_versions",
                    "fingerprint_mismatch_versions",
                    "archive_missing_versions",
                    "latest_marker_versions",
                    "version_sequence_contiguous",
                    "archive_integrity_status",
                    "failures",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "fail"]},
                    "checked": {"type": "boolean"},
                    "checked_versions": {"type": "integer"},
                    "latest_version": {"type": "integer"},
                    "lineage_missing_versions": {"type": "array", "items": {"type": "integer"}},
                    "fingerprint_mismatch_versions": {"type": "array", "items": {"type": "integer"}},
                    "archive_missing_versions": {"type": "array", "items": {"type": "integer"}},
                    "latest_marker_versions": {"type": "array", "items": {"type": "integer"}},
                    "version_sequence_contiguous": {"type": "boolean"},
                    "archive_integrity_status": {"type": "string"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "StatusResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "coordinator_version",
                    "candidate_name",
                    "genome_lineage",
                    "lineage_integrity",
                    "workflow",
                    "calendar_providers",
                    "domain_chart_providers",
                    "llm_backend",
                    "archive_events",
                    "archive_integrity",
                    "latest_evolution",
                    "memory_profile",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "coordinator_version": {"type": "integer"},
                    "candidate_name": {"type": ["string", "null"]},
                    "genome_lineage": {
                        "anyOf": [
                            {"$ref": "#/schemas/GenomeLineage"},
                            {"type": "null"},
                        ]
                    },
                    "lineage_integrity": {"$ref": "#/schemas/LineageIntegrityReport"},
                    "workflow": {"type": ["object", "null"]},
                    "calendar_providers": {"type": "object"},
                    "domain_chart_providers": {"type": "object"},
                    "llm_backend": {"type": "object"},
                    "archive_events": {"type": "integer"},
                    "archive_integrity": {"$ref": "#/schemas/ArchiveIntegrityReport"},
                    "latest_evolution": {
                        "anyOf": [
                            {"$ref": "#/schemas/LatestEvolutionStatus"},
                            {"type": "null"},
                        ]
                    },
                    "memory_profile": {"$ref": "#/schemas/MemoryProfile"},
                },
            },
            "RollbackResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "status",
                    "before_version",
                    "target_version",
                    "after_version",
                    "rollback_reason",
                    "archive_hash",
                    "genome_lineage",
                    "archive_integrity",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["rolled_back"]},
                    "before_version": {"type": "integer"},
                    "target_version": {"type": "integer"},
                    "after_version": {"type": "integer"},
                    "rollback_reason": {"type": "string"},
                    "archive_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "genome_lineage": {"$ref": "#/schemas/GenomeLineage"},
                    "archive_integrity": {"$ref": "#/schemas/ArchiveIntegrityReport"},
                },
            },
            "RollbackRequest": {
                "type": "object",
                "required": ["to_version"],
                "properties": {
                    "to_version": {"type": "integer", "minimum": 1},
                    "reason": {"type": "string"},
                },
            },
            "ProviderDomainStatus": {
                "type": "object",
                "required": [
                    "domain",
                    "provider",
                    "provider_quality",
                    "status",
                    "interpretation_mode",
                    "confidence_level",
                    "blocking_reasons",
                    "contract_valid",
                    "provider_provenance_valid",
                    "provider_provenance_missing",
                    "external_payload_receipt_valid",
                    "external_payload_receipt_sha256",
                    "external_payload_birth_match_status",
                    "external_payload_birth_mismatch_fields",
                    "external_payload_declared_birth_profile_sha256",
                    "production_ready",
                ],
                "properties": {
                    "domain": {"type": "string"},
                    "provider": {"type": "string"},
                    "provider_quality": {"type": "string"},
                    "status": {"type": "string", "enum": ["professional", "fallback"]},
                    "interpretation_mode": {
                        "type": "string",
                        "enum": ["professional_verified", "symbolic_fallback", "external_payload_blocked"],
                    },
                    "confidence_level": {
                        "type": "string",
                        "enum": ["production", "research_symbolic", "blocked"],
                    },
                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                    "contract_valid": {"type": "boolean"},
                    "provider_source": {"type": ["string", "null"]},
                    "provider_provenance_valid": {"type": "boolean"},
                    "provider_provenance_missing": {"type": "array", "items": {"type": "string"}},
                    "external_payload_receipt_valid": {"type": "boolean"},
                    "external_payload_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "external_payload_birth_match_status": {
                        "type": "string",
                        "enum": ["matched", "mismatch", "not_declared", "not_applicable", "missing_receipt", "unknown"],
                    },
                    "external_payload_birth_mismatch_fields": {"type": "array", "items": {"type": "string"}},
                    "external_payload_declared_birth_profile_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "production_ready": {"type": "boolean"},
                    "replacement_boundary": {"type": "string"},
                },
            },
            "ProviderActionPlanItem": {
                "type": "object",
                "required": [
                    "domain",
                    "status",
                    "current_provider",
                    "provider_quality",
                    "reason",
                    "env_var",
                    "provenance_env_var",
                    "certification_command_template",
                    "production_readiness_command_template",
                    "deployment_checklist",
                ],
                "properties": {
                    "domain": {"type": "string", "enum": ["bazi", "ziwei", "qimen", "astrology", "xuanze"]},
                    "status": {"type": "string", "enum": ["professional", "fallback"]},
                    "current_provider": {"type": "string"},
                    "provider_quality": {"type": "string"},
                    "reason": {"type": "string"},
                    "env_var": {"type": ["string", "null"]},
                    "provenance_env_var": {"type": ["string", "null"]},
                    "certification_command_template": {"type": ["string", "null"]},
                    "production_readiness_command_template": {"type": ["string", "null"]},
                    "deployment_checklist": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderReadinessMatrixItem": {
                "type": "object",
                "required": [
                    "domain",
                    "provider",
                    "provider_quality",
                    "production_ready",
                    "interpretation_mode",
                    "confidence_level",
                    "blocking_reasons",
                ],
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": ["bazi", "ziwei", "qimen", "astrology", "xuanze"],
                    },
                    "provider": {"type": ["string", "null"]},
                    "provider_quality": {"type": ["string", "null"]},
                    "production_ready": {"type": "boolean"},
                    "interpretation_mode": {
                        "type": ["string", "null"],
                        "enum": [
                            "professional_verified",
                            "symbolic_fallback",
                            "external_payload_blocked",
                            None,
                        ],
                    },
                    "confidence_level": {
                        "type": ["string", "null"],
                        "enum": ["production", "research_symbolic", "blocked", None],
                    },
                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderSummary": {
                "type": "object",
                "required": [
                    "status",
                    "production_ready",
                    "domains",
                    "readiness_matrix",
                    "professional_domain_count",
                    "fallback_domain_count",
                    "production_blockers",
                    "action_plan",
                    "boundary",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["production_ready", "ready_with_provider_gaps"]},
                    "production_ready": {"type": "boolean"},
                    "domains": {
                        "type": "object",
                        "required": ["bazi", "ziwei", "qimen", "astrology", "xuanze"],
                        "properties": {
                            "bazi": {"$ref": "#/schemas/ProviderDomainStatus"},
                            "ziwei": {"$ref": "#/schemas/ProviderDomainStatus"},
                            "qimen": {"$ref": "#/schemas/ProviderDomainStatus"},
                            "astrology": {"$ref": "#/schemas/ProviderDomainStatus"},
                            "xuanze": {"$ref": "#/schemas/ProviderDomainStatus"},
                        },
                    },
                    "readiness_matrix": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProviderReadinessMatrixItem"},
                    },
                    "professional_domain_count": {"type": "integer"},
                    "fallback_domain_count": {"type": "integer"},
                    "production_blockers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["bazi", "ziwei", "qimen", "astrology", "xuanze"]},
                    },
                    "action_plan": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProviderActionPlanItem"},
                    },
                    "boundary": {"type": "string"},
                },
            },
            "BirthProfile": {
                "type": "object",
                "required": [
                    "name",
                    "birth_date",
                    "birth_time",
                    "gender",
                    "birthplace",
                    "birthplace_normalized",
                    "birthplace_region",
                    "latitude",
                    "longitude",
                    "timezone_offset",
                    "geocoding_provider",
                    "geocoding_quality",
                    "year",
                    "month",
                    "day",
                    "hour",
                    "minute",
                    "calendar_provider",
                    "lunar_note",
                    "annual_start_year",
                    "annual_end_year",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "birth_date": {"type": "string"},
                    "birth_time": {"type": "string"},
                    "gender": {"type": "string"},
                    "birthplace": {"type": "string"},
                    "birthplace_normalized": {"type": "string"},
                    "birthplace_region": {"type": "string"},
                    "latitude": {"type": ["number", "null"]},
                    "longitude": {"type": ["number", "null"]},
                    "timezone_offset": {"type": ["number", "string", "null"]},
                    "geocoding_provider": {"type": "string"},
                    "geocoding_quality": {"type": "string"},
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "day": {"type": "integer"},
                    "hour": {"type": "integer"},
                    "minute": {"type": "integer"},
                    "calendar_provider": {"type": "string"},
                    "lunar_note": {"type": "string"},
                    "annual_start_year": {"type": ["integer", "null"]},
                    "annual_end_year": {"type": ["integer", "null"]},
                },
            },
            "RequestProvenance": {
                "type": "object",
                "required": [
                    "schema_version",
                    "raw_task_input_sha256",
                    "birth_profile_sha256",
                    "specialist_contexts",
                    "report_material_sha256",
                    "report_material",
                    "chain_sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "request-provenance-v1"},
                    "raw_task_input_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "birth_profile_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "specialist_contexts": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": ["context_sha256", "birth_profile_sha256"],
                            "properties": {
                                "provider": {"type": ["string", "null"]},
                                "provider_quality": {"type": ["string", "null"]},
                                "context_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                "birth_profile_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                "provider_request_receipt_sha256": {
                                    "type": ["string", "null"],
                                    "pattern": "^[0-9a-f]{64}$",
                                },
                                "external_payload_receipt_sha256": {
                                    "type": ["string", "null"],
                                    "pattern": "^[0-9a-f]{64}$",
                                },
                            },
                        },
                    },
                    "report_material_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "report_material": {"type": "object"},
                    "chain_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "BaziMethodMatrixItem": {
                "type": "object",
                "required": ["method", "status", "evidence_fields", "summary"],
                "properties": {
                    "method": {"type": "string"},
                    "status": {"type": "string"},
                    "evidence_fields": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                },
            },
            "BaziMajorLuckAnnualPreview": {
                "type": "object",
                "required": ["year", "age", "ganzhi"],
                "properties": {
                    "year": {"type": "integer"},
                    "age": {"type": "integer"},
                    "ganzhi": {"type": "string"},
                },
            },
            "BaziMajorLuckPeriod": {
                "type": "object",
                "required": [
                    "index",
                    "start_age",
                    "end_age",
                    "start_year",
                    "end_year",
                    "ganzhi",
                ],
                "properties": {
                    "index": {"type": "integer"},
                    "start_age": {"type": "integer"},
                    "end_age": {"type": "integer"},
                    "start_year": {"type": "integer"},
                    "end_year": {"type": "integer"},
                    "ganzhi": {"type": "string"},
                    "xun": {"type": "string"},
                    "xun_kong": {"type": "string"},
                    "annual_preview": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/BaziMajorLuckAnnualPreview"},
                    },
                },
            },
            "BaziStrengthAnalysis": {
                "type": "object",
                "required": [
                    "day_master",
                    "day_master_element",
                    "dominant_element",
                    "element_counts",
                    "element_spread",
                    "season",
                    "solar_term",
                    "strength",
                    "basis",
                ],
                "properties": {
                    "day_master": {"type": "string"},
                    "day_master_element": {"type": "string"},
                    "dominant_element": {"type": "string"},
                    "element_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "element_spread": {"type": "integer"},
                    "season": {"type": "string"},
                    "solar_term": {"type": "string"},
                    "strength": {"type": "string"},
                    "basis": {"type": "string"},
                },
            },
            "BaziPatternAnalysis": {
                "type": "object",
                "required": ["structure", "pattern", "month_ten_god", "risk"],
                "properties": {
                    "structure": {"type": "string"},
                    "pattern": {"type": "string"},
                    "month_ten_god": {"type": "string"},
                    "risk": {"type": "string"},
                },
            },
            "BaziUsefulGodAnalysis": {
                "type": "object",
                "required": [
                    "useful_element",
                    "supporting_element",
                    "avoid_overweight_element",
                    "rationale",
                ],
                "properties": {
                    "useful_element": {"type": "string"},
                    "supporting_element": {"type": "string"},
                    "avoid_overweight_element": {"type": "string"},
                    "rationale": {"type": "string"},
                },
            },
            "BaziLuckStart": {
                "type": "object",
                "required": ["years", "months", "days", "hours", "forward"],
                "properties": {
                    "years": {"type": "integer"},
                    "months": {"type": "integer"},
                    "days": {"type": "integer"},
                    "hours": {"type": "integer"},
                    "forward": {"type": "boolean"},
                },
            },
            "BaziProfile": {
                "type": "object",
                "required": [
                    "provider",
                    "provider_quality",
                    "pillars",
                    "structure",
                    "dominant_element",
                    "useful_element",
                    "day_master",
                    "luck_start",
                    "major_luck",
                    "method_matrix",
                    "strength_analysis",
                    "pattern_analysis",
                    "useful_god_analysis",
                    "tiaohou_analysis",
                    "image_symbol_analysis",
                    "new_school_simplified_analysis",
                    "data_validation_analysis",
                    "school_debate",
                ],
                "properties": {
                    "provider": {"type": ["string", "null"]},
                    "provider_quality": {"type": ["string", "null"]},
                    "pillars": {
                        "type": "object",
                        "required": ["year", "month", "day", "hour"],
                        "properties": {
                            "year": {"type": "string"},
                            "month": {"type": "string"},
                            "day": {"type": "string"},
                            "hour": {"type": "string"},
                        },
                    },
                    "structure": {"type": ["string", "null"]},
                    "dominant_element": {"type": ["string", "null"]},
                    "useful_element": {"type": ["string", "null"]},
                    "day_master": {"type": ["string", "null"]},
                    "ten_god_distribution": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "hidden_stem_profile": {"type": "object"},
                    "nayin_growth_profile": {"type": "object"},
                    "strength_analysis": {"$ref": "#/schemas/BaziStrengthAnalysis"},
                    "pattern_analysis": {"$ref": "#/schemas/BaziPatternAnalysis"},
                    "useful_god_analysis": {"$ref": "#/schemas/BaziUsefulGodAnalysis"},
                    "tiaohou_analysis": {"type": "object"},
                    "image_symbol_analysis": {"type": "object"},
                    "new_school_simplified_analysis": {"type": "object"},
                    "data_validation_analysis": {"type": "object"},
                    "school_debate": {"type": "object"},
                    "method_matrix": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/BaziMethodMatrixItem"},
                    },
                    "luck_start": {"$ref": "#/schemas/BaziLuckStart"},
                    "major_luck": {"type": "array", "items": {"$ref": "#/schemas/BaziMajorLuckPeriod"}},
                    "caution": {"type": ["string", "null"]},
                },
            },
            "ProviderIntegrationTarget": {
                "type": "object",
                "required": [
                    "name",
                    "provider_domain",
                    "status",
                    "accepted_checks",
                    "candidate_checks",
                    "blocked_checks",
                    "contracts",
                    "env_vars",
                    "protocols",
                    "live_smoke_required",
                    "live_smoke_passed",
                    "production_credential_required",
                    "production_credential_passed",
                    "required_provenance_fields",
                    "certification_commands",
                    "drift_commands",
                    "deployment_checklist",
                    "bundled_example_policy",
                    "next_actions",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "provider_domain": {"type": "string"},
                    "status": {"type": "string", "enum": ["ready", "blocked"]},
                    "accepted_checks": {"type": "array", "items": {"type": "string"}},
                    "candidate_checks": {"type": "array", "items": {"type": "string"}},
                    "blocked_checks": {"type": "array", "items": {"type": "string"}},
                    "contracts": {"type": "array", "items": {"type": "string"}},
                    "env_vars": {"type": "array", "items": {"type": "string"}},
                    "protocols": {"type": "object"},
                    "live_smoke_required": {"type": "boolean"},
                    "live_smoke_passed": {"type": "boolean"},
                    "production_credential_required": {"type": "boolean"},
                    "production_credential_passed": {"type": "boolean"},
                    "required_provenance_fields": {"type": "array", "items": {"type": "string"}},
                    "certification_commands": {"type": "array", "items": {"type": "string"}},
                    "drift_commands": {"type": "array", "items": {"type": "string"}},
                    "deployment_checklist": {"type": "array", "items": {"type": "string"}},
                    "bundled_example_policy": {"type": "string"},
                    "next_actions": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderIntegrationPlan": {
                "type": "object",
                "required": [
                    "status",
                    "production_ready",
                    "reference_contracts_passed",
                    "live_requested",
                    "live_required_for_production",
                    "ready_targets",
                    "total_targets",
                    "blocked_targets",
                    "targets",
                    "smoke_command",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["production_ready", "production_blocked"]},
                    "production_ready": {"type": "boolean"},
                    "reference_contracts_passed": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "live_required_for_production": {"type": "boolean"},
                    "ready_targets": {"type": "integer"},
                    "total_targets": {"type": "integer"},
                    "blocked_targets": {"type": "array", "items": {"type": "string"}},
                    "targets": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProviderIntegrationTarget"},
                    },
                    "smoke_command": {"type": "string"},
                },
            },
            "ProviderProductionGuidance": {
                "type": "object",
                "required": [
                    "production_ready",
                    "blocked_targets",
                    "required_env_vars",
                    "required_provenance_env_vars",
                    "certification_commands",
                    "drift_commands",
                    "deployment_checklist",
                    "next_actions",
                    "provider_onboarding_command",
                    "provider_ledger_command",
                    "production_readiness_command",
                    "smoke_command",
                    "policy",
                ],
                "properties": {
                    "production_ready": {"type": "boolean"},
                    "blocked_targets": {"type": "array", "items": {"type": "string"}},
                    "required_env_vars": {"type": "array", "items": {"type": "string"}},
                    "required_provenance_env_vars": {"type": "array", "items": {"type": "string"}},
                    "certification_commands": {"type": "array", "items": {"type": "string"}},
                    "drift_commands": {"type": "array", "items": {"type": "string"}},
                    "deployment_checklist": {"type": "array", "items": {"type": "string"}},
                    "next_actions": {"type": "array", "items": {"type": "string"}},
                    "provider_onboarding_command": {"type": "string"},
                    "provider_ledger_command": {"type": "string"},
                    "production_readiness_command": {"type": "string"},
                    "smoke_command": {"type": "string"},
                    "policy": {"type": "string"},
                },
            },
            "ProviderProfileRequiredGroup": {
                "type": "object",
                "required": ["name", "ready", "accepted_checks"],
                "properties": {
                    "name": {"type": "string"},
                    "ready": {"type": "boolean"},
                    "accepted_checks": {"type": "array", "items": {"type": "string"}},
                    "checks": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderProfileReadiness": {
                "type": "object",
                "required": ["profile", "status", "ready", "required_groups", "blockers", "live_required"],
                "properties": {
                    "profile": {"type": "string", "enum": ["development", "production"]},
                    "status": {"type": "string"},
                    "ready": {"type": "boolean"},
                    "required_groups": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProviderProfileRequiredGroup"},
                    },
                    "blockers": {"type": "array", "items": {"type": "string"}},
                    "live_required": {"type": "boolean"},
                },
            },
            "ProductionReadinessGate": {
                "type": "object",
                "required": ["id", "passed", "reason", "failure_reason", "details"],
                "properties": {
                    "id": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "reason": {"type": "string"},
                    "failure_reason": {"type": "string"},
                    "details": {"type": "array", "items": {}},
                },
            },
            "ProductionBlocker": {
                "type": "object",
                "required": ["gate", "reason", "details"],
                "properties": {
                    "gate": {"type": "string"},
                    "reason": {"type": "string"},
                    "details": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProductionGateRegistryAudit": {
                "type": "object",
                "required": [
                    "actual_gate_count",
                    "registry_gate_count",
                    "actual_gate_ids",
                    "registry_gate_ids",
                    "missing_from_registry",
                    "registry_only_gate_ids",
                    "registry_current",
                    "registry_audit_sha256",
                ],
                "properties": {
                    "actual_gate_count": {"type": "integer"},
                    "registry_gate_count": {"type": "integer"},
                    "actual_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "registry_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "missing_from_registry": {"type": "array", "items": {"type": "string"}},
                    "registry_only_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "registry_current": {"type": "boolean"},
                    "registry_audit_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProductionReadinessAnalyzeResponseSchemaCase": {
                "type": "object",
                "required": ["case", "schema_name", "valid", "declared_valid", "error_count", "errors_sample"],
                "properties": {
                    "case": {"type": "string"},
                    "schema_name": {"type": "string", "const": "AnalyzeResponse"},
                    "valid": {"type": "boolean"},
                    "declared_valid": {"type": "boolean"},
                    "error_count": {"type": "integer"},
                    "errors_sample": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProductionReadinessAnalyzeResponseSchemaIssue": {
                "type": "object",
                "required": ["case", "error_count", "first_error"],
                "properties": {
                    "case": {"type": "string"},
                    "error_count": {"type": "integer"},
                    "first_error": {"type": "string"},
                },
            },
            "ProductionReadinessAnalyzeResponseSchemaAudit": {
                "type": "object",
                "required": [
                    "schema_name",
                    "case_count",
                    "valid_count",
                    "coverage_complete",
                    "invalid_cases",
                    "cases",
                ],
                "properties": {
                    "schema_name": {"type": "string", "const": "AnalyzeResponse"},
                    "case_count": {"type": "integer"},
                    "valid_count": {"type": "integer"},
                    "coverage_complete": {"type": "boolean"},
                    "invalid_cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessAnalyzeResponseSchemaCase"},
                    },
                    "cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessAnalyzeResponseSchemaCase"},
                    },
                },
            },
            "ProductionReadinessAnalyzeResponseSchemaReceiptSummary": {
                "type": "object",
                "required": ["schema_name", "case_count", "valid_count", "coverage_complete", "invalid_cases"],
                "properties": {
                    "schema_name": {"type": "string", "const": "AnalyzeResponse"},
                    "case_count": {"type": "integer"},
                    "valid_count": {"type": "integer"},
                    "coverage_complete": {"type": "boolean"},
                    "invalid_cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessAnalyzeResponseSchemaIssue"},
                    },
                },
            },
            "ProductionReadinessResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "status",
                    "production_ready",
                    "live_requested",
                    "manifest_path",
                    "classical_source_list_path",
                    "gates",
                    "blockers",
                    "resolution_plan",
                    "provider_readiness",
                    "provider_integration_plan",
                    "provider_certification_ledger",
                    "provider_certification_drift",
                    "release_manifest_ledger",
                    "outcome_dataset",
                    "outcome_dataset_receipt",
                    "history_integrity",
                    "archive_integrity",
                    "state_of_art",
                    "capability_audit_receipt",
                    "expected_audit_receipt_sha256",
                    "audit_receipt_matches_expected",
                    "audit_receipt_mismatch_reason",
                    "evidence_materialization",
                    "classical_source_refresh",
                    "classical_refresh_receipt",
                    "current_benchmark",
                    "benchmark_analyze_response_schema",
                    "readiness_receipt",
                    "expected_readiness_receipt_sha256",
                    "readiness_receipt_matches_expected",
                    "readiness_receipt_mismatch_reason",
                    "known_gap_ids",
                    "known_gap_handoff_bundle",
                    "known_gap_resolution_plan",
                    "production_gate_registry_audit",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["production_ready", "production_blocked"]},
                    "production_ready": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "manifest_path": {"type": ["string", "null"]},
                    "classical_source_list_path": {"type": ["string", "null"]},
                    "gates": {"type": "array", "items": {"$ref": "#/schemas/ProductionReadinessGate"}},
                    "blockers": {"type": "array", "items": {"$ref": "#/schemas/ProductionBlocker"}},
                    "resolution_plan": {"$ref": "#/schemas/ProductionResolutionPlan"},
                    "provider_readiness": {"$ref": "#/schemas/ProviderProfileReadiness"},
                    "provider_integration_plan": {"$ref": "#/schemas/ProviderIntegrationPlan"},
                    "provider_certification_ledger": {"$ref": "#/schemas/ProviderCertificationLedgerStatus"},
                    "provider_certification_drift": {"$ref": "#/schemas/ProviderCertificationDriftStatus"},
                    "release_manifest_ledger": {"$ref": "#/schemas/ReleaseManifestLedgerStatus"},
                    "outcome_dataset": {"$ref": "#/schemas/OutcomeDatasetAuditResponse"},
                    "outcome_dataset_receipt": {"$ref": "#/schemas/OutcomeDatasetReceipt"},
                    "history_integrity": {"$ref": "#/schemas/VersionHistoryIntegrity"},
                    "archive_integrity": {"$ref": "#/schemas/ArchiveIntegrityReport"},
                    "state_of_art": {"$ref": "#/schemas/StateOfArtAssessment"},
                    "capability_audit_receipt": {"$ref": "#/schemas/CapabilityAuditReceipt"},
                    "expected_audit_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "audit_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "audit_receipt_mismatch_reason": {"type": "string"},
                    "evidence_materialization": {"$ref": "#/schemas/EvidenceMaterialization"},
                    "classical_source_refresh": {"$ref": "#/schemas/ClassicalSourceListAudit"},
                    "classical_refresh_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/ClassicalRefreshReceipt"},
                            {"type": "null"},
                        ]
                    },
                    "current_benchmark": {"$ref": "#/schemas/BenchmarkResult"},
                    "benchmark_analyze_response_schema": {
                        "$ref": "#/schemas/ProductionReadinessAnalyzeResponseSchemaAudit"
                    },
                    "readiness_receipt": {"$ref": "#/schemas/ProductionReadinessReceipt"},
                    "expected_readiness_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "readiness_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "readiness_receipt_mismatch_reason": {"type": "string"},
                    "known_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "known_gap_handoff_bundle": {"$ref": "#/schemas/KnownGapHandoffBundle"},
                    "known_gap_resolution_plan": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/KnownGapResolutionPlanItem"},
                    },
                    "production_gate_registry_audit": {"$ref": "#/schemas/ProductionGateRegistryAudit"},
                },
            },
            "ProductionResolutionStep": {
                "type": "object",
                "required": ["id", "category", "priority", "summary", "commands", "diagnostics", "checklist"],
                "properties": {
                    "id": {"type": "string"},
                    "category": {"type": "string"},
                    "priority": {"type": "integer"},
                    "summary": {"type": "string"},
                    "commands": {"type": "array", "items": {"type": "string"}},
                    "diagnostics": {"type": "array", "items": {"type": "string"}},
                    "checklist": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProductionResolutionPlan": {
                "type": "object",
                "required": ["status", "step_count", "steps"],
                "properties": {
                    "status": {"type": "string", "enum": ["clear", "actions_required"]},
                    "step_count": {"type": "integer"},
                    "steps": {"type": "array", "items": {"$ref": "#/schemas/ProductionResolutionStep"}},
                },
            },
            "ProviderCertificationDriftStatus": {
                "type": "object",
                "required": ["status", "passed", "live_requested", "checked_domains", "checks", "failures"],
                "properties": {
                    "status": {"type": "string", "enum": ["not_checked", "passed", "drift_detected"]},
                    "passed": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "checked_domains": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["astrology", "qimen", "xuanze", "ziwei"]},
                    },
                    "checks": {"type": "array", "items": {"$ref": "#/schemas/ProviderCertificationDriftCheck"}},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderCertificationDriftCheck": {
                "type": "object",
                "required": [
                    "domain",
                    "status",
                    "expected_receipt_sha256",
                    "current_receipt_sha256",
                    "expected_provider_request_receipt_sha256",
                    "current_provider_request_receipt_sha256",
                    "expected_provider_command_sha256",
                    "current_provider_command_sha256",
                    "expected_provider_artifact_sha256",
                    "current_provider_artifact_sha256",
                    "provider_request_receipt_matches_expected",
                    "provider_request_receipt_valid",
                    "provider_command_fingerprint_matches_expected",
                    "matches_expected",
                    "certified",
                    "blockers",
                ],
                "properties": {
                    "domain": {"type": "string", "enum": ["astrology", "qimen", "xuanze", "ziwei"]},
                    "status": {
                        "type": "string",
                        "enum": ["match", "drift", "missing_ledger_receipt", "certification_error"],
                    },
                    "expected_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "current_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "expected_provider_request_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "current_provider_request_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "expected_provider_command_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "current_provider_command_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "expected_provider_artifact_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "current_provider_artifact_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "provider_request_receipt_matches_expected": {"type": "boolean"},
                    "provider_request_receipt_valid": {"type": "boolean"},
                    "provider_command_fingerprint_matches_expected": {"type": "boolean"},
                    "matches_expected": {"type": "boolean"},
                    "certified": {"type": "boolean"},
                    "blockers": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderDriftResolutionGuidance": {
                "type": "object",
                "required": [
                    "passed",
                    "status",
                    "checked_domains",
                    "recertification_commands",
                    "drift_commands",
                    "provider_ledger_command",
                    "provider_onboarding_command",
                    "production_readiness_command",
                    "http_query",
                    "blocking_failures",
                    "policy",
                ],
                "properties": {
                    "passed": {"type": "boolean"},
                    "status": {"type": "string"},
                    "checked_domains": {"type": "array", "items": {"type": "string"}},
                    "recertification_commands": {"type": "array", "items": {"type": "string"}},
                    "drift_commands": {"type": "array", "items": {"type": "string"}},
                    "provider_ledger_command": {"type": "string"},
                    "provider_onboarding_command": {"type": "string"},
                    "production_readiness_command": {"type": "string"},
                    "http_query": {"type": "string"},
                    "blocking_failures": {"type": "array", "items": {"type": "string"}},
                    "policy": {"type": "string"},
                },
            },
            "ProviderCertificationDriftResponse": {
                "type": "object",
                "required": ["repo", "domain", "ledger", "drift", "resolution_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "domain": {"type": ["string", "null"], "enum": ["astrology", "qimen", "xuanze", "ziwei", None]},
                    "ledger": {"$ref": "#/schemas/ProviderCertificationLedgerStatus"},
                    "drift": {"$ref": "#/schemas/ProviderCertificationDriftStatus"},
                    "resolution_guidance": {"$ref": "#/schemas/ProviderDriftResolutionGuidance"},
                },
            },
            "ProviderProtocolsResponse": {
                "type": "object",
                "required": ["repo", "domain", "provider_protocols", "provider_protocols_receipt"],
                "properties": {
                    "repo": {"type": "string"},
                    "domain": {"type": ["string", "null"], "enum": ["astrology", "qimen", "xuanze", "ziwei", None]},
                    "provider_protocols": {"type": "object"},
                    "provider_protocols_receipt": {"$ref": "#/schemas/ProviderProtocolsReceipt"},
                },
            },
            "ProviderProtocolsReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "repo",
                    "domain",
                    "protocol_version",
                    "protocol_hash",
                    "domain_count",
                    "domain_protocol_hashes",
                    "sample_stdout_contracts_valid",
                    "protocol_document_sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "provider-protocols-receipt-v1"},
                    "repo": {"type": "string"},
                    "domain": {"type": ["string", "null"], "enum": ["astrology", "qimen", "xuanze", "ziwei", None]},
                    "protocol_version": {"type": "string"},
                    "protocol_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "domain_count": {"type": "integer"},
                    "domain_protocol_hashes": {
                        "type": "object",
                        "additionalProperties": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                    "sample_stdout_contracts_valid": {"type": "boolean"},
                    "protocol_document_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProviderProtocolsReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "provider-protocols-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ProviderProtocolsReceiptMaterial"},
                },
            },
            "ProviderCertificationLedgerStatus": {
                "type": "object",
                "required": [
                    "path",
                    "exists",
                    "integrity_status",
                    "protocol_status",
                    "request_receipt_status",
                    "reference_contract_status",
                    "command_fingerprint_status",
                    "coverage_status",
                    "record_count",
                    "latest_record_hash",
                    "latest_record_index",
                    "domains",
                    "covered_domains",
                    "missing_domains",
                    "protocol_failures",
                    "request_receipt_failures",
                    "reference_contract_failures",
                    "command_fingerprint_failures",
                    "failures",
                ],
                "properties": {
                    "path": {"type": "string"},
                    "exists": {"type": "boolean"},
                    "integrity_status": {"type": "string", "enum": ["pass", "fail"]},
                    "protocol_status": {"type": "string", "enum": ["current", "stale", "unknown"]},
                    "request_receipt_status": {"type": "string", "enum": ["current", "missing"]},
                    "reference_contract_status": {"type": "string", "enum": ["current", "missing"]},
                    "command_fingerprint_status": {"type": "string", "enum": ["current", "missing"]},
                    "coverage_status": {"type": "string", "enum": ["complete", "incomplete"]},
                    "record_count": {"type": "integer"},
                    "latest_record_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "latest_record_index": {"type": ["integer", "null"]},
                    "domains": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/ProviderCertificationLedgerDomainStatus"},
                    },
                    "covered_domains": {"type": "array", "items": {"type": "string"}},
                    "missing_domains": {"type": "array", "items": {"type": "string"}},
                    "protocol_failures": {"type": "array", "items": {"type": "string"}},
                    "request_receipt_failures": {"type": "array", "items": {"type": "string"}},
                    "reference_contract_failures": {"type": "array", "items": {"type": "string"}},
                    "command_fingerprint_failures": {"type": "array", "items": {"type": "string"}},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderCertificationLedgerDomainStatus": {
                "type": "object",
                "required": [
                    "domain",
                    "record_count",
                    "latest_receipt_sha256",
                    "latest_protocol_version",
                    "latest_protocol_hash",
                    "current_protocol_version",
                    "current_protocol_hash",
                    "protocol_matches_current",
                    "latest_provider_request_receipt_sha256",
                    "latest_provider_command_sha256",
                    "latest_provider_artifact_sha256",
                    "provider_command_fingerprint_present",
                    "request_receipt_present",
                    "request_receipt_valid",
                    "request_receipt_protocol_echo_matches",
                    "request_receipt_birth_profile_sha256",
                    "latest_reference_contract_coverage_sha256",
                    "latest_reference_contract_method_surface_sha256",
                    "current_method_surface_sha256",
                    "reference_contract_method_surface_current",
                    "reference_contract_covered",
                    "reference_contract_method_count",
                    "reference_contract_case_count",
                    "latest_record_hash",
                    "latest_record_index",
                    "certified",
                ],
                "properties": {
                    "domain": {"type": "string", "enum": ["astrology", "qimen", "xuanze", "ziwei"]},
                    "record_count": {"type": "integer"},
                    "latest_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "latest_protocol_version": {"type": ["string", "null"]},
                    "latest_protocol_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "current_protocol_version": {"type": ["string", "null"]},
                    "current_protocol_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "protocol_matches_current": {"type": "boolean"},
                    "latest_provider_request_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "latest_provider_command_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "latest_provider_artifact_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "provider_command_fingerprint_present": {"type": "boolean"},
                    "request_receipt_present": {"type": "boolean"},
                    "request_receipt_valid": {"type": "boolean"},
                    "request_receipt_protocol_echo_matches": {"type": "boolean"},
                    "request_receipt_birth_profile_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "latest_reference_contract_coverage_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "latest_reference_contract_method_surface_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "current_method_surface_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "reference_contract_method_surface_current": {"type": "boolean"},
                    "reference_contract_covered": {"type": "boolean"},
                    "reference_contract_method_count": {"type": "integer"},
                    "reference_contract_case_count": {"type": "integer"},
                    "latest_record_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "latest_record_index": {"type": ["integer", "null"]},
                    "certified": {"type": "boolean"},
                },
            },
            "ProviderLedgerConfigurationGuidance": {
                "type": "object",
                "required": [
                    "configured",
                    "ledger_path",
                    "required_domains",
                    "missing_domains",
                    "domain_env_vars",
                    "domain_provenance_env_vars",
                    "certification_commands",
                    "drift_commands",
                    "provider_onboarding_command",
                    "provider_ledger_command",
                    "production_readiness_command",
                    "http_query",
                    "policy",
                ],
                "properties": {
                    "configured": {"type": "boolean"},
                    "ledger_path": {"type": ["string", "null"]},
                    "required_domains": {"type": "array", "items": {"type": "string"}},
                    "missing_domains": {"type": "array", "items": {"type": "string"}},
                    "domain_env_vars": {"type": "object", "additionalProperties": {"type": "string"}},
                    "domain_provenance_env_vars": {"type": "object", "additionalProperties": {"type": "string"}},
                    "certification_commands": {"type": "array", "items": {"type": "string"}},
                    "drift_commands": {"type": "array", "items": {"type": "string"}},
                    "provider_onboarding_command": {"type": "string"},
                    "provider_ledger_command": {"type": "string"},
                    "production_readiness_command": {"type": "string"},
                    "http_query": {"type": "string"},
                    "policy": {"type": "string"},
                },
            },
            "ProviderCertificationLedgerResponse": {
                "type": "object",
                "required": ["repo", "ledger", "configuration_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "ledger": {"$ref": "#/schemas/ProviderCertificationLedgerStatus"},
                    "configuration_guidance": {"$ref": "#/schemas/ProviderLedgerConfigurationGuidance"},
                },
            },
            "ProviderProvenanceAudit": {
                "type": "object",
                "required": ["valid", "required", "missing", "fields", "format"],
                "properties": {
                    "valid": {"type": "boolean"},
                    "required": {"type": "array", "items": {"type": "string"}},
                    "missing": {"type": "array", "items": {"type": "string"}},
                    "fields": {"type": "object", "additionalProperties": {"type": "string"}},
                    "format": {"type": "string", "enum": ["json_or_semicolon_key_value"]},
                },
            },
            "ProviderCommandFingerprint": {
                "type": "object",
                "required": [
                    "configured",
                    "command_sha256",
                    "artifact_path",
                    "artifact_exists",
                    "artifact_sha256",
                    "artifact_kind",
                ],
                "properties": {
                    "configured": {"type": "boolean"},
                    "command_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "artifact_path": {"type": ["string", "null"]},
                    "artifact_exists": {"type": "boolean"},
                    "artifact_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "artifact_kind": {
                        "type": ["string", "null"],
                        "enum": ["python_script", "executable", "file", None],
                    },
                },
            },
            "ProviderProtocolIdentity": {
                "type": "object",
                "required": [
                    "expected_version",
                    "returned_version",
                    "version_matches",
                    "expected_hash",
                    "returned_hash",
                    "hash_matches",
                    "matches",
                    "failures",
                ],
                "properties": {
                    "expected_version": {"type": ["string", "null"]},
                    "returned_version": {"type": ["string", "null"]},
                    "version_matches": {"type": "boolean"},
                    "expected_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "returned_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "hash_matches": {"type": "boolean"},
                    "matches": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderRequestReceipt": {
                "type": "object",
                "required": [
                    "schema_version",
                    "domain",
                    "protocol",
                    "stdin_sha256",
                    "stdout_sha256",
                    "birth_profile_sha256",
                    "stdout_contract_type",
                    "protocol_echo_matches",
                    "sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "provider-request-receipt-v1"},
                    "domain": {"type": "string"},
                    "protocol": {"$ref": "#/schemas/ProviderRequestProtocolIdentity"},
                    "stdin_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "stdout_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "birth_profile_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "stdout_contract_type": {"type": "string"},
                    "protocol_echo_matches": {"type": "boolean"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProviderRequestProtocolIdentity": {
                "type": "object",
                "required": ["version", "hash"],
                "properties": {
                    "version": {"type": "string"},
                    "hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProviderRawContractReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "domain",
                    "contract_name",
                    "contract_valid",
                    "missing_required_keys",
                    "returned_keys",
                    "provider_request_receipt_sha256",
                    "stdout_sha256",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "domain": {"type": "string"},
                    "contract_name": {"type": ["string", "null"]},
                    "contract_valid": {"type": "boolean"},
                    "missing_required_keys": {"type": "array", "items": {"type": "string"}},
                    "returned_keys": {"type": "array", "items": {"type": "string"}},
                    "provider_request_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "stdout_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProviderRawContractReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ProviderRawContractReceiptMaterial"},
                },
            },
            "ProviderReferenceContractCoverage": {
                "type": "object",
                "required": [
                    "domain",
                    "passed",
                    "required_methods",
                    "observed_methods",
                    "missing_methods",
                    "covered_cases",
                    "provenance_cases",
                    "required_method_surface",
                    "method_surface_schema_version",
                    "method_surface_sha256",
                    "coverage_sha256",
                ],
                "properties": {
                    "domain": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "required_methods": {"type": "array", "items": {"type": "string"}},
                    "observed_methods": {"type": "array", "items": {"type": "string"}},
                    "missing_methods": {"type": "array", "items": {"type": "string"}},
                    "covered_cases": {"type": "array", "items": {"type": "string"}},
                    "provenance_cases": {"type": "array", "items": {"type": "string"}},
                    "required_method_surface": {"type": "array", "items": {"type": "string"}},
                    "method_surface_schema_version": {"type": "string"},
                    "method_surface_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "coverage_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProviderCertificationReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "domain",
                    "provider_check",
                    "status",
                    "certified",
                    "live_requested",
                    "contract",
                    "protocol_version",
                    "protocol_hash",
                    "contract_valid",
                    "raw_contract_receipt",
                    "protocol_identity_matches",
                    "protocol_identity",
                    "protocol_failures",
                    "provider_request_receipt",
                    "provider_request_receipt_valid",
                    "provider_command_fingerprint",
                    "live_passed",
                    "returned_keys",
                    "missing_required_keys",
                    "provenance_valid",
                    "provenance_fields",
                    "reference_contract_coverage",
                    "production_credential_passed",
                    "command_is_bundled_example",
                    "blockers",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "domain": {"type": "string"},
                    "provider_check": {"type": "string"},
                    "status": {"type": "string"},
                    "certified": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "contract": {"type": "string"},
                    "protocol_version": {"type": "string"},
                    "protocol_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "contract_valid": {"type": ["boolean", "null"]},
                    "raw_contract_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/ProviderRawContractReceipt"},
                            {"type": "object", "maxProperties": 0},
                        ]
                    },
                    "protocol_identity_matches": {"type": ["boolean", "null"]},
                    "protocol_identity": {
                        "anyOf": [
                            {"$ref": "#/schemas/ProviderProtocolIdentity"},
                            {"type": "object", "maxProperties": 0},
                        ]
                    },
                    "protocol_failures": {"type": "array", "items": {"type": "string"}},
                    "provider_request_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/ProviderRequestReceipt"},
                            {"type": "object", "maxProperties": 0},
                        ]
                    },
                    "provider_request_receipt_valid": {"type": ["boolean", "null"]},
                    "provider_command_fingerprint": {"$ref": "#/schemas/ProviderCommandFingerprint"},
                    "live_passed": {"type": ["boolean", "null"]},
                    "returned_keys": {"type": "array", "items": {"type": "string"}},
                    "missing_required_keys": {"type": "array", "items": {"type": "string"}},
                    "provenance_valid": {"type": ["boolean", "null"]},
                    "provenance_fields": {"type": "object", "additionalProperties": {"type": "string"}},
                    "reference_contract_coverage": {"$ref": "#/schemas/ProviderReferenceContractCoverage"},
                    "production_credential_passed": {"type": "boolean"},
                    "command_is_bundled_example": {"type": "boolean"},
                    "blockers": {"type": "array", "items": {"type": "string"}},
                },
            },
            "BenchmarkReceiptReferenceChartsSummary": {
                "type": "object",
                "required": ["passed", "passed_count", "total"],
                "properties": {
                    "passed": {"type": ["boolean", "null"]},
                    "passed_count": {"type": ["integer", "null"]},
                    "total": {"type": ["integer", "null"]},
                },
            },
            "BenchmarkReceiptEmpiricalValidationSummary": {
                "type": "object",
                "required": ["status", "case_count", "predictive_truth_cases"],
                "properties": {
                    "status": {"type": ["string", "null"]},
                    "case_count": {"type": ["integer", "null"]},
                    "predictive_truth_cases": {"type": ["integer", "null"]},
                },
            },
            "BenchmarkReceiptCaseSummary": {
                "type": "object",
                "required": ["name", "passed", "score", "metrics", "report_features"],
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "passed": {"type": ["boolean", "null"]},
                    "score": {"type": ["number", "null"]},
                    "metrics": {"type": "object", "additionalProperties": {"type": "number"}},
                    "report_features": {"type": "object", "additionalProperties": {}},
                },
            },
            "BenchmarkReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "genome_version",
                    "candidate_name",
                    "passed_rate",
                    "average_score",
                    "mean_metrics",
                    "reference_charts",
                    "empirical_validation",
                    "reproducibility_manifest",
                    "cases",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "genome_version": {"type": ["integer", "null"]},
                    "candidate_name": {"type": ["string", "null"]},
                    "passed_rate": {"type": ["number", "null"]},
                    "average_score": {"type": ["number", "null"]},
                    "mean_metrics": {"type": "object", "additionalProperties": {"type": "number"}},
                    "reference_charts": {"$ref": "#/schemas/BenchmarkReceiptReferenceChartsSummary"},
                    "empirical_validation": {"$ref": "#/schemas/BenchmarkReceiptEmpiricalValidationSummary"},
                    "reproducibility_manifest": {"$ref": "#/schemas/ReproducibilityManifest"},
                    "cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/BenchmarkReceiptCaseSummary"},
                    },
                },
            },
            "ProviderReadinessCheck": {
                "type": "object",
                "required": [
                    "domain",
                    "provider",
                    "status",
                    "ready",
                    "requirement",
                    "protocol_version",
                    "protocol_hash",
                    "install_hint",
                    "install_diagnostics",
                ],
                "properties": {
                    "domain": {"type": "string"},
                    "provider": {"type": "string"},
                    "module": {"type": ["string", "null"]},
                    "status": {"type": "string"},
                    "ready": {"type": "boolean"},
                    "module_available": {"type": ["boolean", "null"]},
                    "command_configured": {"type": "boolean"},
                    "registered": {"type": "boolean"},
                    "requirement": {"type": "string"},
                    "protocol_version": {"type": ["string", "null"]},
                    "protocol_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "install_hint": {"type": "string"},
                    "install_diagnostics": {"$ref": "#/schemas/ProviderInstallDiagnostics"},
                    "blocking_detail": {"type": ["string", "null"]},
                    "live_check": {"type": ["object", "null"]},
                    "provider_command_fingerprint": {"$ref": "#/schemas/ProviderCommandFingerprint"},
                    "command_is_bundled_example": {"type": "boolean"},
                    "production_credential_required": {"type": "boolean"},
                    "production_credential_passed": {"type": "boolean"},
                    "provenance_env_var": {"type": ["string", "null"]},
                    "provider_provenance": {"type": ["string", "null"]},
                    "provider_provenance_audit": {"$ref": "#/schemas/ProviderProvenanceAudit"},
                    "production_blocker": {"type": ["string", "null"]},
                },
            },
            "ProviderInstallDiagnostics": {
                "type": "object",
                "required": [
                    "kind",
                    "provider",
                    "module",
                    "available",
                    "python_version",
                    "platform",
                    "install_command",
                    "native_build_risk",
                    "requires_external_command",
                    "blocking_detail",
                    "remediation",
                ],
                "properties": {
                    "kind": {"type": "string", "enum": ["python_dependency", "json_cli_provider"]},
                    "provider": {"type": "string"},
                    "module": {"type": ["string", "null"]},
                    "available": {"type": "boolean"},
                    "python_version": {"type": "string"},
                    "platform": {"type": "string"},
                    "install_command": {"type": "string"},
                    "native_build_risk": {"type": "boolean"},
                    "requires_external_command": {"type": "boolean"},
                    "blocking_detail": {"type": ["string", "null"]},
                    "remediation": {"type": "string"},
                },
            },
            "ProviderCertificationResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "domain",
                    "provider_check",
                    "status",
                    "certified",
                    "live_requested",
                    "env_var",
                    "provenance_env_var",
                    "command_override_used",
                    "provenance_override_used",
                    "contract",
                    "protocol_version",
                    "protocol_hash",
                    "command_configured",
                    "registered",
                    "live_check",
                    "provider_command_fingerprint",
                    "provider_provenance_audit",
                    "production_credential_passed",
                    "command_is_bundled_example",
                    "integration_target",
                    "integration_target_status",
                    "reference_contract_coverage",
                    "blockers",
                    "next_actions",
                    "certification_receipt",
                    "expected_receipt_sha256",
                    "receipt_matches_expected",
                    "receipt_mismatch_reason",
                    "ledger_record_requested",
                    "ledger_recorded",
                    "ledger_record_path",
                    "ledger_record_index",
                    "ledger_record_hash",
                    "ledger_record_blocker",
                    "resolution_guidance",
                ],
                "properties": {
                    "repo": {"type": ["string", "null"]},
                    "domain": {"type": "string", "enum": ["ziwei", "qimen", "astrology", "xuanze"]},
                    "provider_check": {"type": "string"},
                    "status": {"type": "string", "enum": ["certified", "blocked"]},
                    "certified": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "env_var": {"type": "string"},
                    "provenance_env_var": {"type": "string"},
                    "command_override_used": {"type": "boolean"},
                    "provenance_override_used": {"type": "boolean"},
                    "contract": {"type": "string"},
                    "protocol_version": {"type": "string"},
                    "protocol_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "command_configured": {"type": "boolean"},
                    "registered": {"type": "boolean"},
                    "live_check": {"type": ["object", "null"]},
                    "provider_command_fingerprint": {"$ref": "#/schemas/ProviderCommandFingerprint"},
                    "provider_provenance_audit": {"$ref": "#/schemas/ProviderProvenanceAudit"},
                    "production_credential_passed": {"type": "boolean"},
                    "command_is_bundled_example": {"type": "boolean"},
                    "integration_target": {"type": ["string", "null"]},
                    "integration_target_status": {"type": ["string", "null"]},
                    "reference_contract_coverage": {"$ref": "#/schemas/ProviderReferenceContractCoverage"},
                    "blockers": {"type": "array", "items": {"type": "string"}},
                    "next_actions": {"type": "array", "items": {"type": "string"}},
                    "certification_receipt": {"$ref": "#/schemas/ProviderCertificationReceipt"},
                    "expected_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "receipt_matches_expected": {"type": ["boolean", "null"]},
                    "receipt_mismatch_reason": {"type": "string"},
                    "ledger_record_requested": {"type": "boolean"},
                    "ledger_recorded": {"type": "boolean"},
                    "ledger_record_path": {"type": "string"},
                    "ledger_record_index": {"type": ["integer", "null"]},
                    "ledger_record_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "ledger_record_blocker": {"type": "string"},
                    "resolution_guidance": {"$ref": "#/schemas/ProviderCertificationResolutionGuidance"},
                },
            },
            "ProviderCertificationResolutionGuidance": {
                "type": "object",
                "required": [
                    "certified",
                    "ledger_record_requested",
                    "ledger_recorded",
                    "ledger_record_blocker",
                    "domain",
                    "env_var",
                    "provenance_env_var",
                    "command_is_bundled_example",
                    "blockers",
                    "next_actions",
                    "recertification_command",
                    "drift_command",
                    "provider_ledger_command",
                    "provider_onboarding_command",
                    "production_readiness_command",
                    "record_policy",
                ],
                "properties": {
                    "certified": {"type": "boolean"},
                    "ledger_record_requested": {"type": "boolean"},
                    "ledger_recorded": {"type": "boolean"},
                    "ledger_record_blocker": {"type": "string"},
                    "domain": {"type": "string"},
                    "env_var": {"type": ["string", "null"]},
                    "provenance_env_var": {"type": ["string", "null"]},
                    "command_is_bundled_example": {"type": "boolean"},
                    "blockers": {"type": "array", "items": {"type": "string"}},
                    "next_actions": {"type": "array", "items": {"type": "string"}},
                    "recertification_command": {"type": "string"},
                    "drift_command": {"type": "string"},
                    "provider_ledger_command": {"type": "string"},
                    "provider_onboarding_command": {"type": "string"},
                    "production_readiness_command": {"type": "string"},
                    "record_policy": {"type": "string"},
                },
            },
            "ProviderCertificationReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {
                        "anyOf": [
                            {"$ref": "#/schemas/ProviderCertificationReceiptMaterial"},
                            {"$ref": "#/schemas/BenchmarkReceiptMaterial"},
                        ]
                    },
                },
            },
            "OutcomeDatasetReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "valid",
                    "content_hash",
                    "record_count",
                    "data_split_record_coverage",
                    "predictive_optimization_enabled",
                    "external_review",
                    "data_split",
                    "label_collection",
                    "statistical_plan",
                    "label_provenance",
                    "governance_gate_ids",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "status": {"type": ["string", "null"]},
                    "valid": {"type": ["boolean", "null"]},
                    "content_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "record_count": {"type": ["integer", "null"]},
                    "data_split_record_coverage": {"$ref": "#/schemas/OutcomeDataSplitRecordCoverage"},
                    "predictive_optimization_enabled": {"type": ["boolean", "null"]},
                    "external_review": {"$ref": "#/schemas/OutcomeExternalReview"},
                    "data_split": {"$ref": "#/schemas/OutcomeDataSplit"},
                    "label_collection": {"$ref": "#/schemas/OutcomeLabelCollection"},
                    "statistical_plan": {"$ref": "#/schemas/OutcomeStatisticalPlanSummary"},
                    "label_provenance": {"$ref": "#/schemas/OutcomeLabelProvenanceSummary"},
                    "governance_gate_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
            "OutcomeDatasetReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/OutcomeDatasetReceiptMaterial"},
                },
            },
            "ClassicalSourceListReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "source_list",
                    "exists",
                    "valid",
                    "source_count",
                    "locked_source_count",
                    "allowed_hosts",
                    "allow_file_urls",
                    "max_bytes",
                    "source_audits",
                    "content_hash",
                    "failures",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "status": {"type": "string"},
                    "source_list": {"type": "string"},
                    "exists": {"type": "boolean"},
                    "valid": {"type": "boolean"},
                    "source_count": {"type": "integer"},
                    "locked_source_count": {"type": "integer"},
                    "allowed_hosts": {"type": "array", "items": {"type": "string"}},
                    "allow_file_urls": {"type": "boolean"},
                    "max_bytes": {"type": "integer"},
                    "source_audits": {"type": "array", "items": {"$ref": "#/schemas/ClassicalSourceAuditEntry"}},
                    "content_hash": {"type": "string"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ClassicalSourceAuditEntry": {
                "type": "object",
                "required": [
                    "index",
                    "name",
                    "url",
                    "scheme",
                    "host",
                    "allowed",
                    "sha256_pinned",
                    "refreshable",
                    "failures",
                ],
                "properties": {
                    "index": {"type": "integer"},
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "scheme": {"type": "string"},
                    "host": {"type": "string"},
                    "allowed": {"type": "boolean"},
                    "sha256_pinned": {"type": "boolean"},
                    "refreshable": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ClassicalSourceListReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ClassicalSourceListReceiptMaterial"},
                },
            },
            "ClassicalSourceListAudit": {
                "type": "object",
                "required": [
                    "status",
                    "source_list",
                    "exists",
                    "valid",
                    "source_count",
                    "locked_source_count",
                    "allowed_hosts",
                    "allow_file_urls",
                    "max_bytes",
                    "source_audits",
                    "content_hash",
                    "failures",
                    "refresh_command",
                    "source_list_receipt",
                ],
                "properties": {
                    "status": {"type": "string"},
                    "source_list": {"type": "string"},
                    "exists": {"type": "boolean"},
                    "valid": {"type": "boolean"},
                    "source_count": {"type": "integer"},
                    "locked_source_count": {"type": "integer"},
                    "allowed_hosts": {"type": "array", "items": {"type": "string"}},
                    "allow_file_urls": {"type": "boolean"},
                    "max_bytes": {"type": "integer"},
                    "source_audits": {"type": "array", "items": {"$ref": "#/schemas/ClassicalSourceAuditEntry"}},
                    "content_hash": {"type": "string"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                    "refresh_command": {"type": "string"},
                    "source_list_receipt": {"$ref": "#/schemas/ClassicalSourceListReceipt"},
                },
            },
            "ClassicalSourcesConfigurationGuidance": {
                "type": "object",
                "required": [
                    "configured",
                    "env_var",
                    "current_source_list_path",
                    "example_source_list_path",
                    "example_is_demonstration_only",
                    "cli_audit_command",
                    "cli_refresh_command",
                    "production_readiness_command",
                    "http_query",
                    "policy",
                ],
                "properties": {
                    "configured": {"type": "boolean"},
                    "env_var": {"type": "string", "const": "SEMAS_CLASSIC_SOURCE_LIST"},
                    "current_source_list_path": {"type": ["string", "null"]},
                    "example_source_list_path": {"type": "string"},
                    "example_is_demonstration_only": {"type": "boolean"},
                    "cli_audit_command": {"type": "string"},
                    "cli_refresh_command": {"type": "string"},
                    "production_readiness_command": {"type": "string"},
                    "http_query": {"type": "string"},
                    "policy": {"type": "string"},
                },
            },
            "ClassicalSourcesResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "configured",
                    "source_list_path",
                    "audit",
                    "configuration_guidance",
                    "production_gate",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "source_list_path": {"type": "string"},
                    "audit": {"$ref": "#/schemas/ClassicalSourceListAudit"},
                    "configuration_guidance": {"$ref": "#/schemas/ClassicalSourcesConfigurationGuidance"},
                    "production_gate": {"$ref": "#/schemas/ProductionReadinessGate"},
                },
            },
            "ClassicalSourcesRefreshResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "status",
                    "refreshed",
                    "source_list_path",
                    "cache_dir",
                    "output_dir",
                    "audit",
                    "refresh",
                    "refresh_receipt",
                    "failures",
                    "source_list_receipt",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "status": {"type": "string"},
                    "refreshed": {"type": "boolean"},
                    "source_list_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "output_dir": {"type": "string"},
                    "audit": {"$ref": "#/schemas/ClassicalSourceListAudit"},
                    "refresh": {"type": ["object", "null"]},
                    "refresh_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/ClassicalRefreshReceipt"},
                            {"type": "null"},
                        ]
                    },
                    "failures": {"type": "array", "items": {"type": "string"}},
                    "source_list_receipt": {"$ref": "#/schemas/ClassicalSourceListReceipt"},
                },
            },
            "ClassicalRefreshReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ClassicalRefreshReceiptMaterial"},
                },
            },
            "ClassicalRefreshSourceReceipt": {
                "type": "object",
                "required": [
                    "name",
                    "url",
                    "cache_file",
                    "content_hash",
                    "ingest_status",
                    "ingest_output_file",
                    "ingest_record_count",
                    "ingest_content_hash",
                    "source_ids",
                    "citation_policies",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "cache_file": {"type": "string"},
                    "content_hash": {"type": "string"},
                    "ingest_status": {"type": "string"},
                    "ingest_output_file": {"type": "string"},
                    "ingest_record_count": {"type": "integer"},
                    "ingest_content_hash": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "citation_policies": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ClassicalRefreshReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "source_list",
                    "source_list_receipt_sha256",
                    "source_list_receipt_material_sha256",
                    "cache_dir",
                    "output_dir",
                    "source_count",
                    "record_count",
                    "allowed_hosts",
                    "allow_file_urls",
                    "sources",
                    "content_hash",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "status": {"type": "string"},
                    "source_list": {"type": "string"},
                    "source_list_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "source_list_receipt_material_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "cache_dir": {"type": "string"},
                    "output_dir": {"type": "string"},
                    "source_count": {"type": "integer"},
                    "record_count": {"type": "integer"},
                    "allowed_hosts": {"type": "array", "items": {"type": "string"}},
                    "allow_file_urls": {"type": "boolean"},
                    "sources": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ClassicalRefreshSourceReceipt"},
                    },
                    "content_hash": {"type": "string"},
                },
            },
            "ClassicalSourceRefreshReceiptSummary": {
                "type": "object",
                "required": [
                    "status",
                    "valid",
                    "source_count",
                    "locked_source_count",
                    "content_hash",
                    "source_list_receipt_sha256",
                    "source_list_receipt_material_sha256",
                    "latest_refresh_receipt_sha256",
                    "latest_refresh_record_count",
                    "failures",
                ],
                "properties": {
                    "status": {"type": ["string", "null"]},
                    "valid": {"type": ["boolean", "null"]},
                    "source_count": {"type": ["integer", "null"]},
                    "locked_source_count": {"type": ["integer", "null"]},
                    "content_hash": {"type": ["string", "null"]},
                    "source_list_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "source_list_receipt_material_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "latest_refresh_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "latest_refresh_record_count": {"type": ["integer", "null"]},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "KnownGapResolutionPlanCoverage": {
                "type": "object",
                "required": [
                    "known_gap_count",
                    "plan_item_count",
                    "covered_count",
                    "coverage_complete",
                    "planned_gap_ids",
                    "missing_gap_ids",
                    "invalid_plan_gap_ids",
                    "invalid_gate_ids_by_gap",
                    "invalid_verification_commands_by_gap",
                    "invalid_verification_options_by_gap",
                    "valid_production_gate_ids",
                    "valid_cli_subcommands",
                    "valid_cli_options_by_subcommand",
                    "command_validation_complete",
                    "command_subcommands_by_gap",
                    "command_options_by_gap",
                    "command_counts",
                    "gate_counts",
                    "command_coverage_sha256",
                    "plan_coverage_sha256",
                    "audit_plan_hash",
                ],
                "properties": {
                    "known_gap_count": {"type": "integer"},
                    "plan_item_count": {"type": "integer"},
                    "covered_count": {"type": "integer"},
                    "coverage_complete": {"type": "boolean"},
                    "planned_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "missing_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "invalid_plan_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "invalid_gate_ids_by_gap": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "invalid_verification_commands_by_gap": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "invalid_verification_options_by_gap": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "valid_production_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "valid_cli_subcommands": {"type": "array", "items": {"type": "string"}},
                    "valid_cli_options_by_subcommand": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "command_validation_complete": {"type": "boolean"},
                    "command_subcommands_by_gap": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "command_options_by_gap": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "command_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "gate_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "command_coverage_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "plan_coverage_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "audit_plan_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProductionResolutionPlanSummary": {
                "type": "object",
                "required": [
                    "status",
                    "step_count",
                    "step_ids",
                    "categories",
                    "category_counts",
                    "command_count",
                    "diagnostic_count",
                    "checklist_count",
                    "resolution_plan_sha256",
                ],
                "properties": {
                    "status": {"type": ["string", "null"]},
                    "step_count": {"type": "integer"},
                    "step_ids": {"type": "array", "items": {"type": "string"}},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "category_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "command_count": {"type": "integer"},
                    "diagnostic_count": {"type": "integer"},
                    "checklist_count": {"type": "integer"},
                    "resolution_plan_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProductionReadinessBenchmarkCaseSha256": {
                "type": "object",
                "required": ["case", "sha256"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ProductionReadinessBenchmarkGeocodingIssue": {
                "type": "object",
                "required": ["case", "quality"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "quality": {"type": ["string", "null"]},
                },
            },
            "ProductionReadinessBenchmarkBirthProfileAudit": {
                "type": "object",
                "required": [
                    "case_count",
                    "covered_count",
                    "geocoded_count",
                    "unresolved_geocoding",
                    "fingerprints",
                ],
                "properties": {
                    "case_count": {"type": "integer"},
                    "covered_count": {"type": "integer"},
                    "geocoded_count": {"type": "integer"},
                    "unresolved_geocoding": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkGeocodingIssue"},
                    },
                    "fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkCaseSha256"},
                    },
                },
            },
            "ProductionReadinessBenchmarkDeliberationReceiptAudit": {
                "type": "object",
                "required": ["case", "sha256", "claim_count"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "claim_count": {"type": ["integer", "null"]},
                },
            },
            "ProductionReadinessBenchmarkReceiptBindingAudit": {
                "type": "object",
                "required": ["case", "sha256", "row_count", "bound_to_provenance"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "row_count": {"type": ["integer", "null"]},
                    "bound_to_provenance": {"type": "boolean"},
                },
            },
            "ProductionReadinessBenchmarkExternalPayloadReceiptCase": {
                "type": "object",
                "required": ["case", "domains", "complete"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "complete": {"type": "boolean"},
                },
            },
            "ProductionReadinessBenchmarkExternalPayloadBirthMatchStatus": {
                "type": "object",
                "required": ["domain", "status", "mismatch_fields", "declared_birth_profile_sha256"],
                "properties": {
                    "domain": {"type": "string"},
                    "status": {"type": "string"},
                    "mismatch_fields": {"type": "array", "items": {"type": "string"}},
                    "declared_birth_profile_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
            },
            "ProductionReadinessBenchmarkExternalPayloadBirthMatchCase": {
                "type": "object",
                "required": ["case", "statuses", "mismatch_domains", "matches_ok"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "statuses": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkExternalPayloadBirthMatchStatus"},
                    },
                    "mismatch_domains": {"type": "array", "items": {"type": "string"}},
                    "matches_ok": {"type": "boolean"},
                },
            },
            "ProductionReadinessBenchmarkRequestProvenanceAudit": {
                "type": "object",
                "required": [
                    "case_count",
                    "covered_count",
                    "chains",
                    "deliberation_receipt_covered_count",
                    "deliberation_receipts",
                    "annual_timeline_receipt_covered_count",
                    "annual_timeline_receipt_bound_count",
                    "annual_timeline_receipts",
                    "annual_timeline_unbound_cases",
                    "monthly_luck_receipt_covered_count",
                    "monthly_luck_receipt_bound_count",
                    "monthly_luck_receipts",
                    "monthly_luck_unbound_cases",
                    "auspicious_calendar_receipt_covered_count",
                    "auspicious_calendar_receipt_bound_count",
                    "auspicious_calendar_receipts",
                    "auspicious_calendar_unbound_cases",
                    "external_payload_receipt_case_count",
                    "external_payload_receipt_domains",
                    "external_payload_receipt_cases",
                    "external_payload_birth_match_case_count",
                    "external_payload_birth_match_cases",
                    "external_payload_birth_mismatch_domains",
                    "external_payload_birth_matches_ok",
                ],
                "properties": {
                    "case_count": {"type": "integer"},
                    "covered_count": {"type": "integer"},
                    "chains": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkCaseSha256"},
                    },
                    "deliberation_receipt_covered_count": {"type": "integer"},
                    "deliberation_receipts": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkDeliberationReceiptAudit"},
                    },
                    "annual_timeline_receipt_covered_count": {"type": "integer"},
                    "annual_timeline_receipt_bound_count": {"type": "integer"},
                    "annual_timeline_receipts": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkReceiptBindingAudit"},
                    },
                    "annual_timeline_unbound_cases": {"type": "array", "items": {"type": "string"}},
                    "monthly_luck_receipt_covered_count": {"type": "integer"},
                    "monthly_luck_receipt_bound_count": {"type": "integer"},
                    "monthly_luck_receipts": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkReceiptBindingAudit"},
                    },
                    "monthly_luck_unbound_cases": {"type": "array", "items": {"type": "string"}},
                    "auspicious_calendar_receipt_covered_count": {"type": "integer"},
                    "auspicious_calendar_receipt_bound_count": {"type": "integer"},
                    "auspicious_calendar_receipts": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkReceiptBindingAudit"},
                    },
                    "auspicious_calendar_unbound_cases": {"type": "array", "items": {"type": "string"}},
                    "external_payload_receipt_case_count": {"type": "integer"},
                    "external_payload_receipt_domains": {"type": "array", "items": {"type": "string"}},
                    "external_payload_receipt_cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkExternalPayloadReceiptCase"},
                    },
                    "external_payload_birth_match_case_count": {"type": "integer"},
                    "external_payload_birth_match_cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkExternalPayloadBirthMatchCase"},
                    },
                    "external_payload_birth_mismatch_domains": {"type": "array", "items": {"type": "string"}},
                    "external_payload_birth_matches_ok": {"type": "boolean"},
                },
            },
            "ProductionReadinessBenchmarkProviderActionPlanCount": {
                "type": "object",
                "required": ["case", "provider_blocker_count", "provider_action_plan_count"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "provider_blocker_count": {"type": ["integer", "null"]},
                    "provider_action_plan_count": {"type": ["integer", "null"]},
                },
            },
            "ProductionReadinessBenchmarkProviderActionPlanIssue": {
                "type": "object",
                "required": ["case"],
                "properties": {
                    "case": {"type": ["string", "null"]},
                    "reason": {"type": "string"},
                    "provider_blocker_count": {"type": ["integer", "null"]},
                    "provider_action_plan_count": {"type": ["integer", "null"]},
                    "provider_action_plan_domains": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProductionReadinessBenchmarkProviderActionPlanAudit": {
                "type": "object",
                "required": ["case_count", "covered_count", "coverage_complete", "unresolved", "action_plan_counts"],
                "properties": {
                    "case_count": {"type": "integer"},
                    "covered_count": {"type": "integer"},
                    "coverage_complete": {"type": "boolean"},
                    "unresolved": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkProviderActionPlanIssue"},
                    },
                    "action_plan_counts": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionReadinessBenchmarkProviderActionPlanCount"},
                    },
                },
            },
            "ProductionReadinessBenchmarkTopicConfidenceAudit": {
                "type": "object",
                "required": [
                    "case_count",
                    "covered_count",
                    "coverage_complete",
                    "boundary_failures",
                    "missing_topics",
                    "downgrade_reasons",
                    "level_counts",
                ],
                "properties": {
                    "case_count": {"type": "integer"},
                    "covered_count": {"type": "integer"},
                    "coverage_complete": {"type": "boolean"},
                    "boundary_failures": {"type": "array", "items": {"type": "string"}},
                    "missing_topics": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "downgrade_reasons": {"type": "array", "items": {"type": "string"}},
                    "level_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                },
            },
            "ProductionReadinessBenchmarkSummary": {
                "type": "object",
                "required": [
                    "genome_version",
                    "candidate_name",
                    "passed_rate",
                    "average_score",
                    "mean_metrics",
                    "birth_profile_audit",
                    "request_provenance_audit",
                    "provider_action_plan_audit",
                    "topic_confidence_audit",
                    "analyze_response_schema_audit",
                    "reference_charts_passed",
                    "empirical_validation_status",
                    "reproducibility_manifest",
                ],
                "properties": {
                    "genome_version": {"type": ["integer", "null"]},
                    "candidate_name": {"type": ["string", "null"]},
                    "passed_rate": {"type": ["number", "null"]},
                    "average_score": {"type": ["number", "null"]},
                    "mean_metrics": {"type": "object", "additionalProperties": {"type": "number"}},
                    "birth_profile_audit": {"$ref": "#/schemas/ProductionReadinessBenchmarkBirthProfileAudit"},
                    "request_provenance_audit": {
                        "$ref": "#/schemas/ProductionReadinessBenchmarkRequestProvenanceAudit"
                    },
                    "provider_action_plan_audit": {
                        "$ref": "#/schemas/ProductionReadinessBenchmarkProviderActionPlanAudit"
                    },
                    "topic_confidence_audit": {"$ref": "#/schemas/ProductionReadinessBenchmarkTopicConfidenceAudit"},
                    "analyze_response_schema_audit": {
                        "$ref": "#/schemas/ProductionReadinessAnalyzeResponseSchemaReceiptSummary"
                    },
                    "reference_charts_passed": {"type": ["boolean", "null"]},
                    "empirical_validation_status": {"type": ["string", "null"]},
                    "reproducibility_manifest": {"$ref": "#/schemas/ReproducibilityManifest"},
                },
            },
            "ProductionReadinessCapabilityAuditReceiptSummary": {
                "type": "object",
                "required": ["schema_version", "sha256", "matches_expected"],
                "properties": {
                    "schema_version": {"type": ["string", "null"]},
                    "sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "matches_expected": {"type": ["boolean", "null"]},
                },
            },
            "ProductionReadinessProviderLedgerSummary": {
                "type": "object",
                "required": [
                    "integrity_status",
                    "coverage_status",
                    "protocol_status",
                    "request_receipt_status",
                    "reference_contract_status",
                    "command_fingerprint_status",
                    "record_count",
                    "latest_record_hash",
                    "latest_record_index",
                    "missing_domains",
                    "request_receipt_failures",
                    "reference_contract_failures",
                    "command_fingerprint_failures",
                ],
                "properties": {
                    "integrity_status": {"type": ["string", "null"]},
                    "coverage_status": {"type": ["string", "null"]},
                    "protocol_status": {"type": ["string", "null"]},
                    "request_receipt_status": {"type": ["string", "null"]},
                    "reference_contract_status": {"type": ["string", "null"]},
                    "command_fingerprint_status": {"type": ["string", "null"]},
                    "record_count": {"type": ["integer", "null"]},
                    "latest_record_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "latest_record_index": {"type": ["integer", "null"]},
                    "missing_domains": {"type": "array", "items": {"type": "string"}},
                    "request_receipt_failures": {"type": "array", "items": {"type": "string"}},
                    "reference_contract_failures": {"type": "array", "items": {"type": "string"}},
                    "command_fingerprint_failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProductionReadinessProviderDriftSummary": {
                "type": "object",
                "required": ["status", "passed", "checked_domains", "failures"],
                "properties": {
                    "status": {"type": ["string", "null"]},
                    "passed": {"type": ["boolean", "null"]},
                    "checked_domains": {"type": "array", "items": {"type": "string"}},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProductionReadinessEvidenceMaterializationSummary": {
                "type": "object",
                "required": ["status", "total_evidence", "passed_count", "failed_count", "unchecked_count"],
                "properties": {
                    "status": {"type": ["string", "null"], "enum": ["passed", "failed", "partially_checked", None]},
                    "total_evidence": {"type": ["integer", "null"]},
                    "passed_count": {"type": ["integer", "null"]},
                    "failed_count": {"type": ["integer", "null"]},
                    "unchecked_count": {"type": ["integer", "null"]},
                },
            },
            "ProductionReadinessReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "production_ready",
                    "classical_source_list_path",
                    "gates",
                    "current_benchmark",
                    "evidence_materialization",
                    "classical_source_refresh",
                    "capability_audit_receipt",
                    "provider_certification_ledger",
                    "provider_certification_drift",
                    "outcome_dataset_receipt_sha256",
                    "outcome_dataset",
                    "known_gap_ids",
                    "known_gap_handoff_bundle",
                    "known_gap_resolution_plan_coverage",
                    "production_resolution_plan_summary",
                    "production_gate_registry_audit",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "status": {"type": "string"},
                    "production_ready": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "manifest_path": {"type": ["string", "null"]},
                    "classical_source_list_path": {"type": ["string", "null"]},
                    "gates": {"type": "array", "items": {"$ref": "#/schemas/ProductionReadinessGate"}},
                    "blocker_gates": {"type": "array", "items": {"type": "string"}},
                    "current_benchmark": {"$ref": "#/schemas/ProductionReadinessBenchmarkSummary"},
                    "evidence_materialization": {
                        "$ref": "#/schemas/ProductionReadinessEvidenceMaterializationSummary"
                    },
                    "classical_source_refresh": {"$ref": "#/schemas/ClassicalSourceRefreshReceiptSummary"},
                    "capability_audit_receipt": {
                        "$ref": "#/schemas/ProductionReadinessCapabilityAuditReceiptSummary"
                    },
                    "provider_certification_ledger": {
                        "$ref": "#/schemas/ProductionReadinessProviderLedgerSummary"
                    },
                    "provider_certification_drift": {
                        "$ref": "#/schemas/ProductionReadinessProviderDriftSummary"
                    },
                    "outcome_dataset_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "outcome_dataset": {"$ref": "#/schemas/OutcomeDatasetReceiptMaterial"},
                    "history_integrity_status": {"type": ["string", "null"]},
                    "archive_integrity_status": {"type": ["string", "null"]},
                    "known_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "known_gap_handoff_bundle": {"$ref": "#/schemas/KnownGapHandoffBundle"},
                    "known_gap_resolution_plan_coverage": {"$ref": "#/schemas/KnownGapResolutionPlanCoverage"},
                    "production_resolution_plan_summary": {"$ref": "#/schemas/ProductionResolutionPlanSummary"},
                    "production_gate_registry_audit": {"$ref": "#/schemas/ProductionGateRegistryAudit"},
                },
            },
            "ProductionReadinessReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ProductionReadinessReceiptMaterial"},
                },
            },
            "ReleaseManifestReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "release_gate_checks",
                    "classical_source_list_path",
                    "audit_receipt_sha256",
                    "github_comparison_receipt_sha256",
                    "github_comparison_receipt",
                    "plan_compliance_receipt_sha256",
                    "plan_compliance_receipt",
                    "provider_protocols_receipt_sha256",
                    "provider_protocols_receipt",
                    "provider_onboarding_receipt_sha256",
                    "provider_onboarding_receipt",
                    "benchmark_receipt_sha256",
                    "readiness_receipt_sha256",
                    "method_surface",
                    "readiness_deliberation_receipt_coverage",
                    "annual_timeline_receipt_coverage",
                    "monthly_luck_receipt_coverage",
                    "auspicious_calendar_receipt_coverage",
                    "external_payload_birth_match_coverage",
                    "provider_action_plan_coverage",
                    "classical_source_receipt_coverage",
                    "known_gap_resolution_plan_coverage",
                    "known_gap_handoff_bundle",
                    "production_gate_registry_audit",
                    "production_resolution_plan_summary",
                    "production_readiness_status",
                    "production_ready",
                    "release_approval_ready",
                    "release_approval_status",
                    "release_blockers",
                    "known_gap_ids",
                    "provider_ledger",
                    "outcome_dataset_receipt_sha256",
                    "outcome_dataset",
                    "evolution_trigger_receipt_sha256",
                    "evolution_trigger_receipt",
                    "evolution_trigger_receipt_current",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "status": {"type": "string"},
                    "release_gate_checks": {"$ref": "#/schemas/ReleaseManifestGateChecks"},
                    "coordinator_version": {"type": ["integer", "null"]},
                    "candidate_name": {"type": ["string", "null"]},
                    "live_requested": {"type": "boolean"},
                    "classical_source_list_path": {"type": ["string", "null"]},
                    "history_integrity_status": {"type": ["string", "null"]},
                    "archive_integrity_status": {"type": ["string", "null"]},
                    "lineage_integrity_status": {"type": ["string", "null"]},
                    "audit_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "audit_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "github_comparison_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "github_comparison_receipt": {"$ref": "#/schemas/GitHubComparisonReceipt"},
                    "plan_compliance_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "plan_compliance_receipt": {"$ref": "#/schemas/PlanComplianceReceipt"},
                    "provider_protocols_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "provider_protocols_receipt": {"$ref": "#/schemas/ProviderProtocolsReceipt"},
                    "provider_onboarding_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "provider_onboarding_receipt": {"$ref": "#/schemas/ProviderOnboardingReceipt"},
                    "method_surface": {"$ref": "#/schemas/MethodSurfaceReceiptSummary"},
                    "benchmark_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "benchmark_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "readiness_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "readiness_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "readiness_deliberation_receipt_coverage": {
                        "type": "object",
                        "required": [
                            "case_count",
                            "covered_count",
                            "coverage_complete",
                            "receipt_count",
                            "claim_counts",
                            "receipt_sha256s",
                        ],
                        "properties": {
                            "case_count": {"type": "integer"},
                            "covered_count": {"type": "integer"},
                            "coverage_complete": {"type": "boolean"},
                            "receipt_count": {"type": "integer"},
                            "claim_counts": {"type": "array", "items": {"type": "integer"}},
                            "receipt_sha256s": {
                                "type": "array",
                                "items": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            },
                        },
                    },
                    "annual_timeline_receipt_coverage": {
                        "type": "object",
                        "required": [
                            "case_count",
                            "covered_count",
                            "bound_count",
                            "coverage_complete",
                            "binding_complete",
                            "receipt_count",
                            "row_counts",
                            "receipt_sha256s",
                            "unbound_cases",
                        ],
                        "properties": {
                            "case_count": {"type": "integer"},
                            "covered_count": {"type": "integer"},
                            "bound_count": {"type": "integer"},
                            "coverage_complete": {"type": "boolean"},
                            "binding_complete": {"type": "boolean"},
                            "receipt_count": {"type": "integer"},
                            "row_counts": {"type": "array", "items": {"type": "integer"}},
                            "receipt_sha256s": {
                                "type": "array",
                                "items": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            },
                            "unbound_cases": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "monthly_luck_receipt_coverage": {
                        "type": "object",
                        "required": [
                            "case_count",
                            "covered_count",
                            "bound_count",
                            "coverage_complete",
                            "binding_complete",
                            "receipt_count",
                            "row_counts",
                            "receipt_sha256s",
                            "unbound_cases",
                        ],
                        "properties": {
                            "case_count": {"type": "integer"},
                            "covered_count": {"type": "integer"},
                            "bound_count": {"type": "integer"},
                            "coverage_complete": {"type": "boolean"},
                            "binding_complete": {"type": "boolean"},
                            "receipt_count": {"type": "integer"},
                            "row_counts": {"type": "array", "items": {"type": "integer"}},
                            "receipt_sha256s": {
                                "type": "array",
                                "items": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            },
                            "unbound_cases": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "auspicious_calendar_receipt_coverage": {
                        "type": "object",
                        "required": [
                            "case_count",
                            "covered_count",
                            "bound_count",
                            "coverage_complete",
                            "binding_complete",
                            "receipt_count",
                            "row_counts",
                            "receipt_sha256s",
                            "unbound_cases",
                        ],
                        "properties": {
                            "case_count": {"type": "integer"},
                            "covered_count": {"type": "integer"},
                            "bound_count": {"type": "integer"},
                            "coverage_complete": {"type": "boolean"},
                            "binding_complete": {"type": "boolean"},
                            "receipt_count": {"type": "integer"},
                            "row_counts": {"type": "array", "items": {"type": "integer"}},
                            "receipt_sha256s": {
                                "type": "array",
                                "items": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            },
                            "unbound_cases": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "external_payload_birth_match_coverage": {
                        "type": "object",
                        "required": [
                            "case_count",
                            "match_case_count",
                            "coverage_complete",
                            "mismatch_domains",
                            "match_cases",
                        ],
                        "properties": {
                            "case_count": {"type": "integer"},
                            "match_case_count": {"type": "integer"},
                            "coverage_complete": {"type": "boolean"},
                            "mismatch_domains": {"type": "array", "items": {"type": "string"}},
                            "match_cases": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                    "provider_action_plan_coverage": {
                        "type": "object",
                        "required": [
                            "case_count",
                            "covered_count",
                            "coverage_complete",
                            "unresolved",
                            "action_plan_counts",
                        ],
                        "properties": {
                            "case_count": {"type": "integer"},
                            "covered_count": {"type": "integer"},
                            "coverage_complete": {"type": "boolean"},
                            "unresolved": {"type": "array", "items": {"type": "object"}},
                            "action_plan_counts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "case",
                                        "provider_blocker_count",
                                        "provider_action_plan_count",
                                    ],
                                    "properties": {
                                        "case": {"type": "string"},
                                        "provider_blocker_count": {"type": "integer"},
                                        "provider_action_plan_count": {"type": "integer"},
                                    },
                                },
                            },
                        },
                    },
                    "classical_source_receipt_coverage": {
                        "type": "object",
                        "required": [
                            "status",
                            "valid",
                            "receipt_present",
                            "source_list_receipt_sha256",
                            "source_list_receipt_material_sha256",
                            "refresh_receipt_present",
                            "latest_refresh_receipt_sha256",
                            "latest_refresh_record_count",
                            "source_count",
                            "locked_source_count",
                        ],
                        "properties": {
                            "status": {"type": ["string", "null"]},
                            "valid": {"type": ["boolean", "null"]},
                            "receipt_present": {"type": "boolean"},
                            "source_list_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "source_list_receipt_material_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "refresh_receipt_present": {"type": "boolean"},
                            "latest_refresh_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "latest_refresh_record_count": {"type": ["integer", "null"]},
                            "source_count": {"type": ["integer", "null"]},
                            "locked_source_count": {"type": ["integer", "null"]},
                        },
                    },
                    "known_gap_resolution_plan_coverage": {"$ref": "#/schemas/KnownGapResolutionPlanCoverage"},
                    "known_gap_handoff_bundle": {"$ref": "#/schemas/KnownGapHandoffBundle"},
                    "production_gate_registry_audit": {"$ref": "#/schemas/ProductionGateRegistryAudit"},
                    "production_resolution_plan_summary": {"$ref": "#/schemas/ProductionResolutionPlanSummary"},
                    "production_readiness_status": {"type": ["string", "null"]},
                    "production_ready": {"type": ["boolean", "null"]},
                    "release_approval_ready": {"type": ["boolean", "null"]},
                    "release_approval_status": {
                        "type": ["string", "null"],
                        "enum": ["release_ready", "release_blocked", None],
                    },
                    "release_blockers": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionBlocker"},
                    },
                    "known_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "outcome_dataset_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "provider_ledger": {"$ref": "#/schemas/ProductionReadinessProviderLedgerSummary"},
                    "outcome_dataset": {"$ref": "#/schemas/OutcomeDatasetReceiptMaterial"},
                    "evolution_trigger_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "evolution_trigger_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/EvolutionTriggerReceipt"},
                            {"type": "null"},
                        ]
                    },
                    "evolution_trigger_receipt_current": {"type": "boolean"},
                },
            },
            "ReleaseManifestReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ReleaseManifestReceiptMaterial"},
                },
            },
            "ReleaseManifestGateChecks": {
                "type": "object",
                "required": [
                    "history_integrity_passed",
                    "archive_integrity_passed",
                    "lineage_integrity_passed",
                    "audit_receipt_current",
                    "provider_onboarding_receipt_current",
                    "provider_protocols_receipt_current",
                    "benchmark_receipt_current",
                    "readiness_receipt_current",
                    "outcome_dataset_split_coverage_bound",
                    "provider_audit_contract_gates_bound",
                    "outcome_statistical_plan_preregistration_bound",
                    "classical_latest_refresh_receipt_bound",
                    "blocked_capability_coverage_bound",
                    "known_gap_handoff_bundle_bound",
                    "known_gap_command_coverage_bound",
                ],
                "properties": {
                    "history_integrity_passed": {"type": "boolean"},
                    "archive_integrity_passed": {"type": "boolean"},
                    "lineage_integrity_passed": {"type": "boolean"},
                    "audit_receipt_current": {"type": "boolean"},
                    "provider_onboarding_receipt_current": {"type": "boolean"},
                    "provider_protocols_receipt_current": {"type": "boolean"},
                    "benchmark_receipt_current": {"type": "boolean"},
                    "readiness_receipt_current": {"type": "boolean"},
                    "outcome_dataset_split_coverage_bound": {"type": "boolean"},
                    "provider_audit_contract_gates_bound": {"type": "boolean"},
                    "outcome_statistical_plan_preregistration_bound": {"type": "boolean"},
                    "classical_latest_refresh_receipt_bound": {"type": "boolean"},
                    "blocked_capability_coverage_bound": {"type": "boolean"},
                    "known_gap_handoff_bundle_bound": {"type": "boolean"},
                    "known_gap_command_coverage_bound": {"type": "boolean"},
                },
            },
            "ReferenceChartDomainMethodCoverage": {
                "type": "object",
                "required": ["required", "observed", "missing", "passed"],
                "properties": {
                    "required": {"type": "array", "items": {"type": "string"}},
                    "observed": {"type": "array", "items": {"type": "string"}},
                    "missing": {"type": "array", "items": {"type": "string"}},
                    "passed": {"type": "boolean"},
                },
            },
            "ReferenceChartMethodCoverage": {
                "type": "object",
                "required": ["passed", "domains"],
                "properties": {
                    "passed": {"type": "boolean"},
                    "domains": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/ReferenceChartDomainMethodCoverage"},
                    },
                },
            },
            "ReferenceChartCaseCheck": {
                "type": "object",
                "required": [
                    "name",
                    "passed",
                    "failures",
                    "checked_domains",
                    "method_coverage",
                    "provenance_coverage",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                    "checked_domains": {"type": "array", "items": {"type": "string"}},
                    "method_coverage": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "provenance_coverage": {
                        "type": "object",
                        "additionalProperties": {"type": "boolean"},
                    },
                },
            },
            "ReferenceChartChecks": {
                "type": "object",
                "required": ["passed", "passed_count", "total", "method_coverage", "cases"],
                "properties": {
                    "passed": {"type": "boolean"},
                    "passed_count": {"type": "integer"},
                    "total": {"type": "integer"},
                    "method_coverage": {"$ref": "#/schemas/ReferenceChartMethodCoverage"},
                    "cases": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ReferenceChartCaseCheck"},
                    },
                },
            },
            "ProviderChecksResponse": {
                "type": "object",
                "required": [
                    "status",
                    "profile",
                    "profile_readiness",
                    "integration_plan",
                    "production_guidance",
                    "live",
                    "checks",
                    "reference_chart_checks",
                ],
                "properties": {
                    "status": {"type": "string"},
                    "profile": {"type": "string", "enum": ["development", "production"]},
                    "profile_readiness": {"$ref": "#/schemas/ProviderProfileReadiness"},
                    "integration_plan": {"$ref": "#/schemas/ProviderIntegrationPlan"},
                    "production_guidance": {"$ref": "#/schemas/ProviderProductionGuidance"},
                    "live": {"type": "boolean"},
                    "ready_count": {"type": "integer"},
                    "total": {"type": "integer"},
                    "checks": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/ProviderReadinessCheck"},
                    },
                    "reference_chart_checks": {"$ref": "#/schemas/ReferenceChartChecks"},
                },
            },
            "ProviderExampleSmokeDomain": {
                "type": "object",
                "required": [
                    "check",
                    "script",
                    "ready",
                    "live_passed",
                    "contract_valid",
                    "protocol_identity_matches",
                    "provider_request_receipt_valid",
                    "provider_request_receipt_sha256",
                    "protocol_version",
                    "protocol_hash",
                    "command_is_bundled_example",
                    "production_credential_passed",
                    "production_blocker",
                ],
                "properties": {
                    "check": {"type": "string"},
                    "script": {"type": "string"},
                    "ready": {"type": "boolean"},
                    "live_passed": {"type": "boolean"},
                    "contract_valid": {"type": "boolean"},
                    "protocol_identity_matches": {"type": "boolean"},
                    "provider_request_receipt_valid": {"type": "boolean"},
                    "provider_request_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "protocol_version": {"type": ["string", "null"]},
                    "protocol_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "command_is_bundled_example": {"type": "boolean"},
                    "production_credential_passed": {"type": "boolean"},
                    "production_blocker": {"type": "string"},
                },
            },
            "ProviderExampleSmokeResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "status",
                    "production_certification_allowed",
                    "policy",
                    "domains",
                    "profile_readiness",
                    "integration_plan",
                    "example_provider_receipt",
                ],
                "properties": {
                    "repo": {"type": ["string", "null"]},
                    "status": {"type": "string", "enum": ["passed", "failed"]},
                    "production_certification_allowed": {"type": "boolean"},
                    "policy": {"type": "string"},
                    "domains": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/ProviderExampleSmokeDomain"},
                    },
                    "profile_readiness": {"type": "object"},
                    "integration_plan": {"$ref": "#/schemas/ProviderIntegrationPlan"},
                    "example_provider_receipt": {"$ref": "#/schemas/ProviderCertificationReceipt"},
                },
            },
            "ProviderOnboardingDomain": {
                "type": "object",
                "required": [
                    "domain",
                    "status",
                    "missing_evidence",
                    "env_var",
                    "provenance_env_var",
                    "protocol_version",
                    "protocol_hash",
                    "required_provenance_fields",
                    "certification_command",
                    "drift_command",
                    "deployment_checklist",
                    "next_actions",
                    "ledger_status",
                    "bundled_example_smoke",
                ],
                "properties": {
                    "domain": {"type": "string"},
                    "status": {"type": "string", "enum": ["ready", "blocked"]},
                    "missing_evidence": {"type": "array", "items": {"type": "string"}},
                    "env_var": {"type": ["string", "null"]},
                    "provenance_env_var": {"type": ["string", "null"]},
                    "protocol_version": {"type": ["string", "null"]},
                    "protocol_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "required_provenance_fields": {"type": "array", "items": {"type": "string"}},
                    "certification_command": {"type": "string"},
                    "drift_command": {"type": "string"},
                    "deployment_checklist": {"type": "array", "items": {"type": "string"}},
                    "next_actions": {"type": "array", "items": {"type": "string"}},
                    "ledger_status": {"$ref": "#/schemas/ProviderCertificationLedgerDomainStatus"},
                    "bundled_example_smoke": {
                        "type": "object",
                        "required": [
                            "live_passed",
                            "contract_valid",
                            "protocol_identity_matches",
                            "provider_request_receipt_valid",
                            "receipt_sha256",
                            "production_certification_allowed",
                        ],
                        "properties": {
                            "live_passed": {"type": ["boolean", "null"]},
                            "contract_valid": {"type": ["boolean", "null"]},
                            "protocol_identity_matches": {"type": ["boolean", "null"]},
                            "provider_request_receipt_valid": {"type": ["boolean", "null"]},
                            "receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                            "production_certification_allowed": {"type": "boolean"},
                        },
                    },
                },
            },
            "ProviderOnboardingReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "repo",
                    "status",
                    "domain_count",
                    "ready_domain_count",
                    "missing_evidence_by_domain",
                    "missing_evidence_counts",
                    "provider_ledger_exists",
                    "provider_ledger_latest_record_hash",
                    "example_provider_receipt_sha256",
                    "domains",
                    "policy",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["ready", "actions_required"]},
                    "domain_count": {"type": "integer"},
                    "ready_domain_count": {"type": "integer"},
                    "missing_evidence_by_domain": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "missing_evidence_counts": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    },
                    "provider_ledger_exists": {"type": "boolean"},
                    "provider_ledger_latest_record_hash": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "example_provider_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "domains": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/ProviderOnboardingDomain"},
                    },
                    "policy": {"type": "string"},
                },
            },
            "ProviderOnboardingReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/ProviderOnboardingReceiptMaterial"},
                },
            },
            "ProviderOnboardingResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "status",
                    "domains",
                    "provider_ledger",
                    "example_provider_receipt",
                    "provider_onboarding_receipt",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["ready", "actions_required"]},
                    "domains": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/ProviderOnboardingDomain"},
                    },
                    "provider_ledger": {"$ref": "#/schemas/ProviderCertificationLedgerStatus"},
                    "example_provider_receipt": {"$ref": "#/schemas/ProviderCertificationReceipt"},
                    "provider_onboarding_receipt": {"$ref": "#/schemas/ProviderOnboardingReceipt"},
                },
            },
            "StateOfArtAssessment": {
                "type": "object",
                "required": [
                    "verdict",
                    "production_ready_for_professional_calculation",
                    "request_scoped_production_ready_path",
                    "request_scoped_provenance_required",
                    "production_input_geocoding",
                    "birthplace_geocoding_production_gate",
                    "deliberation_receipt_production_gate",
                    "strength_dimensions",
                    "blocking_provider_capabilities",
                    "blocking_provider_scope",
                    "comparison_scope",
                ],
                "properties": {
                    "verdict": {
                        "type": "string",
                        "enum": [
                            "advanced_agentic_framework_not_full_domain_sota",
                            "near_sota_with_configured_providers",
                        ],
                    },
                    "production_ready_for_professional_calculation": {"type": "boolean"},
                    "request_scoped_production_ready_path": {"type": "boolean"},
                    "request_scoped_provenance_required": {"type": "boolean"},
                    "production_input_geocoding": {"type": "boolean"},
                    "birthplace_geocoding_production_gate": {"type": "string"},
                    "deliberation_receipt_production_gate": {"type": "string"},
                    "strength_dimensions": {"type": "array", "items": {"type": "string"}},
                    "blocking_provider_capabilities": {"type": "array", "items": {"type": "string"}},
                    "blocking_provider_scope": {"type": "string"},
                    "comparison_scope": {"type": "string"},
                    "last_reviewed": {"type": "string"},
                },
            },
            "PlanComplianceSection": {
                "type": "object",
                "required": [
                    "section",
                    "plan_ref",
                    "requirement",
                    "implemented",
                    "gap_ids",
                    "status",
                    "implemented_verified",
                    "gap_ids_verified",
                ],
                "properties": {
                    "section": {"type": "string"},
                    "plan_ref": {"type": "string"},
                    "requirement": {"type": "string"},
                    "implemented": {"type": "array", "items": {"type": "string"}},
                    "gap_ids": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string"},
                    "implemented_verified": {"type": "boolean"},
                    "gap_ids_verified": {"type": "boolean"},
                },
            },
            "PlanSectionGapResolution": {
                "type": "object",
                "required": [
                    "section",
                    "gap_ids",
                    "planned_gap_ids",
                    "gap_count",
                    "planned_gap_count",
                    "all_gaps_planned",
                    "verification_command_count",
                    "production_gate_ids",
                ],
                "properties": {
                    "section": {"type": "string"},
                    "gap_ids": {"type": "array", "items": {"type": "string"}},
                    "planned_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "gap_count": {"type": "integer"},
                    "planned_gap_count": {"type": "integer"},
                    "all_gaps_planned": {"type": "boolean"},
                    "verification_command_count": {"type": "integer"},
                    "production_gate_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
            "PlanSectionGapResolutionCoverage": {
                "type": "object",
                "required": [
                    "status",
                    "section_count",
                    "sections_with_gaps",
                    "sections_with_unplanned_gaps",
                    "missing_plan_gap_ids",
                    "invalid_plan_gap_ids",
                    "sections",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["covered", "incomplete"]},
                    "section_count": {"type": "integer"},
                    "sections_with_gaps": {"type": "array", "items": {"type": "string"}},
                    "sections_with_unplanned_gaps": {"type": "array", "items": {"type": "string"}},
                    "missing_plan_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "invalid_plan_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "sections": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/PlanSectionGapResolution"},
                    },
                },
            },
            "PlanCompliance": {
                "type": "object",
                "required": [
                    "source",
                    "source_receipt",
                    "section_count",
                    "implemented_count",
                    "sections_with_gaps",
                    "section_gap_resolution_coverage",
                    "matrix",
                ],
                "properties": {
                    "source": {"type": "string"},
                    "source_receipt": {
                        "type": "object",
                        "required": [
                            "path",
                            "exists",
                            "readable",
                            "encoding",
                            "byte_count",
                            "sha256",
                            "section_headings",
                            "section_heading_count",
                        ],
                        "properties": {
                            "path": {"type": "string"},
                            "exists": {"type": "boolean"},
                            "readable": {"type": "boolean"},
                            "encoding": {"type": "string"},
                            "byte_count": {"type": "integer"},
                            "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "section_headings": {"type": "array", "items": {"type": "string"}},
                            "section_heading_count": {"type": "integer"},
                        },
                    },
                    "section_count": {"type": "integer"},
                    "implemented_count": {"type": "integer"},
                    "sections_with_gaps": {"type": "array", "items": {"type": "string"}},
                    "section_gap_resolution_coverage": {
                        "$ref": "#/schemas/PlanSectionGapResolutionCoverage"
                    },
                    "matrix": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/PlanComplianceSection"},
                    },
                },
            },
            "PlanComplianceReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "source",
                    "source_receipt_sha256",
                    "section_count",
                    "implemented_count",
                    "sections_with_gaps",
                    "matrix_sha256",
                    "section_gap_resolution_coverage_sha256",
                    "coverage_status",
                    "missing_plan_gap_ids",
                    "invalid_plan_gap_ids",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "plan-compliance-receipt-v1"},
                    "source": {"type": "string"},
                    "source_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "section_count": {"type": "integer"},
                    "implemented_count": {"type": "integer"},
                    "sections_with_gaps": {"type": "array", "items": {"type": "string"}},
                    "matrix_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "section_gap_resolution_coverage_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "coverage_status": {"type": ["string", "null"]},
                    "missing_plan_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "invalid_plan_gap_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
            "PlanComplianceReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "plan-compliance-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/PlanComplianceReceiptMaterial"},
                },
            },
            "OutcomeDatasetManifest": {
                "type": "object",
                "required": [
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
                ],
                "properties": {
                    "dataset_id": {"type": "string"},
                    "version": {"type": "string"},
                    "purpose": {"type": "string"},
                    "consent": {"$ref": "#/schemas/OutcomeDatasetConsent"},
                    "privacy": {"$ref": "#/schemas/OutcomeDatasetPrivacy"},
                    "external_review": {
                        "type": "object",
                        "required": ["reviewed", "reviewer", "review_date", "approval", "protocol_id"],
                        "properties": {
                            "reviewed": {"type": "boolean", "const": True},
                            "reviewer": {"type": "string"},
                            "review_date": {"type": "string"},
                            "approval": {
                                "type": "string",
                                "enum": ["approved_for_quality_validation", "approved_for_audit_only"],
                            },
                            "protocol_id": {"type": "string"},
                        },
                    },
                    "data_split": {
                        "type": "object",
                        "required": [
                            "strategy",
                            "frozen",
                            "split_date",
                            "holdout_case_ids",
                            "leakage_controls",
                        ],
                        "properties": {
                            "strategy": {
                                "type": "string",
                                "enum": ["pre_registered_holdout", "audit_only", "temporal_holdout"],
                            },
                            "frozen": {"type": "boolean", "const": True},
                            "split_date": {"type": "string"},
                            "train_case_ids": {"type": "array", "items": {"type": "string"}},
                            "holdout_case_ids": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                            "leakage_controls": {"type": "string"},
                        },
                    },
                    "label_collection": {
                        "type": "object",
                        "required": ["source", "collected_before_analysis", "collection_window", "adjudication"],
                        "properties": {
                            "source": {"type": "string", "enum": ["self_report", "reviewer_scored", "mixed"]},
                            "collected_before_analysis": {"type": "boolean", "const": True},
                            "collection_window": {"type": "string"},
                            "adjudication": {"type": "string"},
                        },
                    },
                    "labels": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/schemas/OutcomeLabelDefinition"},
                    },
                    "baselines": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/schemas/OutcomeBaseline"},
                    },
                    "statistical_plan": {"$ref": "#/schemas/OutcomeStatisticalPlan"},
                    "records": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/schemas/OutcomeDatasetRecord"},
                    },
                },
            },
            "OutcomeDatasetConsent": {
                "type": "object",
                "required": ["documented", "scope", "withdrawal_process"],
                "properties": {
                    "documented": {"type": "boolean", "const": True},
                    "scope": {"type": "string", "enum": ["research", "benchmarking", "quality_validation"]},
                    "withdrawal_process": {"type": "string"},
                },
            },
            "OutcomeDatasetPrivacy": {
                "type": "object",
                "required": ["deidentified", "direct_identifiers_removed", "retention_policy"],
                "properties": {
                    "deidentified": {"type": "boolean", "const": True},
                    "direct_identifiers_removed": {"type": "boolean", "const": True},
                    "retention_policy": {
                        "type": "string",
                        "enum": ["delete_after_study", "bounded_archive", "user_controlled"],
                    },
                },
            },
            "OutcomeLabelDefinition": {
                "type": "object",
                "required": ["id", "type", "definition", "measurement_window"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["life_event_outcome", "report_quality", "schema_quality"]},
                    "definition": {"type": "string"},
                    "measurement_window": {"type": "string"},
                },
            },
            "OutcomeBaseline": {
                "type": "object",
                "required": ["name", "method"],
                "properties": {
                    "name": {"type": "string"},
                    "method": {"type": "string"},
                },
            },
            "OutcomeStatisticalPlan": {
                "type": "object",
                "required": [
                    "hypotheses",
                    "metrics",
                    "minimum_sample_size",
                    "holdout_strategy",
                    "pre_registered",
                    "registration_id",
                    "registered_at",
                    "analysis_freeze_date",
                ],
                "properties": {
                    "hypotheses": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                    "metrics": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                    "minimum_sample_size": {"type": "integer", "minimum": 30},
                    "holdout_strategy": {"type": "string"},
                    "pre_registered": {"type": "boolean", "const": True},
                    "registration_id": {"type": "string"},
                    "registered_at": {"type": "string"},
                    "analysis_freeze_date": {"type": "string"},
                    "plan_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "plan_receipt_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
                "anyOf": [
                    {"required": ["plan_sha256"]},
                    {"required": ["plan_receipt_sha256"]},
                ],
            },
            "OutcomeStatisticalPlanSummary": {
                "type": "object",
                "required": [
                    "pre_registered",
                    "registration_id",
                    "registered_at",
                    "analysis_freeze_date",
                    "minimum_sample_size",
                    "holdout_strategy",
                    "plan_sha256",
                    "plan_receipt_sha256",
                    "preregistration_complete",
                ],
                "properties": {
                    "pre_registered": {"type": "boolean"},
                    "registration_id": {"type": ["string", "null"]},
                    "registered_at": {"type": ["string", "null"]},
                    "analysis_freeze_date": {"type": ["string", "null"]},
                    "minimum_sample_size": {"type": ["integer", "null"]},
                    "holdout_strategy": {"type": ["string", "null"]},
                    "plan_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "plan_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "preregistration_complete": {"type": "boolean"},
                },
            },
            "OutcomeExternalReview": {
                "type": "object",
                "required": ["reviewed", "reviewer", "review_date", "approval", "protocol_id"],
                "properties": {
                    "reviewed": {"type": "boolean"},
                    "reviewer": {"type": ["string", "null"]},
                    "review_date": {"type": ["string", "null"]},
                    "approval": {
                        "type": ["string", "null"],
                        "enum": ["approved_for_quality_validation", "approved_for_audit_only", None],
                    },
                    "protocol_id": {"type": ["string", "null"]},
                },
            },
            "OutcomeDataSplit": {
                "type": "object",
                "required": ["strategy", "frozen", "train_count", "holdout_count"],
                "properties": {
                    "strategy": {"type": ["string", "null"]},
                    "frozen": {"type": "boolean"},
                    "split_date": {"type": ["string", "null"]},
                    "train_count": {"type": "integer"},
                    "holdout_count": {"type": "integer"},
                    "leakage_controls_present": {"type": "boolean"},
                },
            },
            "OutcomeDataSplitRecordCoverage": {
                "type": "object",
                "required": [
                    "record_count",
                    "assigned_count",
                    "train_count",
                    "holdout_count",
                    "unassigned_case_ids",
                    "unknown_case_ids",
                    "overlap_case_ids",
                    "coverage_complete",
                    "split_fingerprint",
                ],
                "properties": {
                    "record_count": {"type": "integer"},
                    "assigned_count": {"type": "integer"},
                    "train_count": {"type": "integer"},
                    "holdout_count": {"type": "integer"},
                    "unassigned_case_ids": {"type": "array", "items": {"type": "string"}},
                    "unknown_case_ids": {"type": "array", "items": {"type": "string"}},
                    "overlap_case_ids": {"type": "array", "items": {"type": "string"}},
                    "coverage_complete": {"type": "boolean"},
                    "split_fingerprint": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "OutcomeLabelCollection": {
                "type": "object",
                "required": ["source", "collected_before_analysis"],
                "properties": {
                    "source": {"type": ["string", "null"]},
                    "collected_before_analysis": {"type": "boolean"},
                    "collection_window": {"type": ["string", "null"]},
                    "adjudication": {"type": ["string", "null"]},
                },
            },
            "OutcomeDatasetRecord": {
                "type": "object",
                "required": ["case_id", "birth", "labels"],
                "properties": {
                    "case_id": {"type": "string"},
                    "birth": {
                        "type": "object",
                        "required": ["birth_date", "birth_time", "gender"],
                        "properties": {
                            "birth_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                            "birth_time": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
                            "gender": {"type": "string"},
                            "birthplace_region": {"type": "string"},
                            "timezone_offset": {"type": ["number", "string"]},
                        },
                        "not": {"required": ["name"]},
                    },
                    "labels": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/schemas/OutcomeRecordLabel"},
                    },
                    "input_overrides": {"type": "object"},
                },
            },
            "OutcomeRecordLabel": {
                "type": "object",
                "required": ["id", "type", "value"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["life_event_outcome", "report_quality", "schema_quality"]},
                    "value": {},
                },
            },
            "OutcomeQualityTaskFingerprint": {
                "type": "object",
                "required": ["case_id", "label_id", "split_role", "sha256"],
                "properties": {
                    "case_id": {"type": "string"},
                    "label_id": {"type": "string"},
                    "split_role": {"type": "string", "enum": ["train", "holdout", "unassigned"]},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "OutcomeQualityTaskProjection": {
                "type": "object",
                "required": [
                    "included_label_types",
                    "excluded_label_types",
                    "projected_task_count",
                    "audit_only_label_count",
                    "projected_task_fingerprints",
                ],
                "properties": {
                    "included_label_types": {"type": "array", "items": {"type": "string"}},
                    "excluded_label_types": {"type": "array", "items": {"type": "string"}},
                    "projected_task_count": {"type": "integer"},
                    "audit_only_label_count": {"type": "integer"},
                    "projected_task_fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/OutcomeQualityTaskFingerprint"},
                    },
                },
            },
            "OutcomeRecordFingerprint": {
                "type": "object",
                "required": ["case_id", "sha256"],
                "properties": {
                    "case_id": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "OutcomeLabelInventory": {
                "type": "object",
                "required": [
                    "definitions",
                    "record_labels",
                    "defined_label_ids",
                    "observed_label_ids",
                    "undefined_label_ids",
                ],
                "properties": {
                    "definitions": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    },
                    "record_labels": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    },
                    "defined_label_ids": {"type": "array", "items": {"type": "string"}},
                    "observed_label_ids": {"type": "array", "items": {"type": "string"}},
                    "undefined_label_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
            "OutcomeLabelProvenanceSummary": {
                "type": "object",
                "required": [
                    "label_count",
                    "complete_count",
                    "provenance_complete",
                    "missing",
                    "sources",
                    "reviewer_or_methods",
                    "audit_only_acknowledged_count",
                ],
                "properties": {
                    "label_count": {"type": "integer"},
                    "complete_count": {"type": "integer"},
                    "provenance_complete": {"type": "boolean"},
                    "missing": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["case_id", "label_id"],
                            "properties": {
                                "case_id": {"type": "string"},
                                "label_id": {"type": "string"},
                            },
                        },
                    },
                    "sources": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "reviewer_or_methods": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "audit_only_acknowledged_count": {"type": "integer"},
                },
            },
            "OutcomeOptimizationPolicy": {
                "type": "object",
                "required": [
                    "quality_task_label_types",
                    "audit_only_label_types",
                    "predictive_truth_optimization_enabled",
                    "predictive_truth_records",
                    "blocked_reason",
                ],
                "properties": {
                    "quality_task_label_types": {"type": "array", "items": {"type": "string"}},
                    "audit_only_label_types": {"type": "array", "items": {"type": "string"}},
                    "predictive_truth_optimization_enabled": {"type": "boolean"},
                    "predictive_truth_records": {"type": "integer"},
                    "blocked_reason": {"type": "string"},
                },
            },
            "OutcomeGovernanceGates": {
                "type": "object",
                "required": ["passed", "gates", "blocking_failures"],
                "properties": {
                    "passed": {"type": "boolean"},
                    "gates": {
                        "type": "object",
                        "additionalProperties": {"type": "boolean"},
                    },
                    "blocking_failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "OutcomeDatasetAudit": {
                "type": "object",
                "required": [
                    "status",
                    "valid",
                    "failures",
                    "record_count",
                    "record_fingerprints",
                    "data_split_record_coverage",
                    "label_inventory",
                    "label_provenance",
                    "quality_task_projection",
                    "predictive_optimization_enabled",
                    "optimization_policy",
                    "external_review",
                    "data_split",
                    "label_collection",
                    "statistical_plan",
                    "governance_gates",
                    "content_hash",
                ],
                "properties": {
                    "status": {"type": "string"},
                    "valid": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                    "dataset_id": {"type": ["string", "null"]},
                    "version": {"type": ["string", "null"]},
                    "record_count": {"type": "integer"},
                    "record_fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/OutcomeRecordFingerprint"},
                    },
                    "data_split_record_coverage": {"$ref": "#/schemas/OutcomeDataSplitRecordCoverage"},
                    "label_types": {"type": "array", "items": {"type": "string"}},
                    "label_inventory": {"$ref": "#/schemas/OutcomeLabelInventory"},
                    "label_provenance": {"$ref": "#/schemas/OutcomeLabelProvenanceSummary"},
                    "quality_task_projection": {"$ref": "#/schemas/OutcomeQualityTaskProjection"},
                    "predictive_truth_records": {"type": "integer"},
                    "predictive_optimization_enabled": {"type": "boolean"},
                    "optimization_policy": {"$ref": "#/schemas/OutcomeOptimizationPolicy"},
                    "external_review": {"$ref": "#/schemas/OutcomeExternalReview"},
                    "data_split": {"$ref": "#/schemas/OutcomeDataSplit"},
                    "label_collection": {"$ref": "#/schemas/OutcomeLabelCollection"},
                    "statistical_plan": {"$ref": "#/schemas/OutcomeStatisticalPlanSummary"},
                    "governance_gates": {"$ref": "#/schemas/OutcomeGovernanceGates"},
                    "policy": {"type": "string"},
                    "content_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "OutcomeDatasetEvolutionGate": {
                "type": "object",
                "required": [
                    "passed",
                    "status",
                    "manifest_path",
                    "reason",
                    "blocking_failures",
                    "predictive_optimization_enabled",
                ],
                "properties": {
                    "passed": {"type": "boolean"},
                    "status": {"type": "string"},
                    "manifest_path": {"type": ["string", "null"]},
                    "reason": {"type": "string"},
                    "blocking_failures": {"type": "array", "items": {"type": "string"}},
                    "predictive_optimization_enabled": {"type": "boolean"},
                },
            },
            "OutcomeDatasetConfigurationGuidance": {
                "type": "object",
                "required": [
                    "configured",
                    "env_var",
                    "current_manifest_path",
                    "example_manifest_path",
                    "example_is_demonstration_only",
                    "cli_audit_command",
                    "production_readiness_command",
                    "http_query",
                    "policy",
                ],
                "properties": {
                    "configured": {"type": "boolean"},
                    "env_var": {"type": "string", "const": "SEMAS_OUTCOME_DATASET_MANIFEST"},
                    "current_manifest_path": {"type": ["string", "null"]},
                    "example_manifest_path": {"type": "string"},
                    "example_is_demonstration_only": {"type": "boolean"},
                    "cli_audit_command": {"type": "string"},
                    "production_readiness_command": {"type": "string"},
                    "http_query": {"type": "string"},
                    "policy": {"type": "string"},
                },
            },
            "OutcomeDatasetAuditResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "manifest_path",
                    "audit",
                    "outcome_dataset_receipt",
                    "evolution_gate",
                    "configuration_guidance",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": ["string", "null"]},
                    "audit": {"$ref": "#/schemas/OutcomeDatasetAudit"},
                    "outcome_dataset_receipt": {"$ref": "#/schemas/OutcomeDatasetReceipt"},
                    "evolution_gate": {"$ref": "#/schemas/OutcomeDatasetEvolutionGate"},
                    "configuration_guidance": {"$ref": "#/schemas/OutcomeDatasetConfigurationGuidance"},
                },
            },
            "BirthProfileReviewStatusResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "manifest_path",
                    "configured",
                    "audit",
                    "birth_profile_review_manifest_receipt",
                    "production_gate",
                    "configuration_guidance",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "audit": {"type": "object"},
                    "birth_profile_review_manifest_receipt": {
                        "type": "object",
                        "required": ["schema_version", "sha256", "material"],
                        "properties": {
                            "schema_version": {
                                "type": "string",
                                "const": "birth-profile-review-manifest-summary-receipt-v1",
                            },
                            "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "material": {"type": "object"},
                        },
                    },
                    "production_gate": {
                        "type": "object",
                        "required": [
                            "id",
                            "passed",
                            "reason",
                            "blocking_failures",
                            "externally_reviewed",
                            "production_evidence",
                            "ready_for_import",
                        ],
                        "properties": {
                            "id": {"type": "string", "const": "birth_profile_review_manifest_ready_for_import"},
                            "passed": {"type": "boolean"},
                            "reason": {"type": "string"},
                            "blocking_failures": {"type": "array", "items": {"type": "string"}},
                            "externally_reviewed": {"type": "boolean"},
                            "production_evidence": {"type": "boolean"},
                            "ready_for_import": {"type": "boolean"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileSourceReviewWorkplanResponse": {
                "type": "object",
                "required": ["repo", "manifest_path", "configured", "source_review_workplan", "configuration_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "source_review_workplan": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "would_fetch_live_sources",
                            "would_write_review_manifest",
                            "request_count",
                            "work_item_count",
                            "review_progress_summary",
                            "field_gap_summary",
                            "work_items",
                            "source_review_gate",
                            "source_review_workplan_receipt",
                            "source_review_workplan_sha256",
                            "integrity_check",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {
                                "type": "string",
                                "const": "birth-profile-source-review-workplan-v1",
                            },
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "would_fetch_live_sources": {"type": "boolean"},
                            "would_write_review_manifest": {"type": "boolean"},
                            "request_count": {"type": "integer"},
                            "work_item_count": {"type": "integer"},
                            "review_progress_summary": {"type": "object"},
                            "field_gap_summary": {"type": "object"},
                            "work_items": {"type": "array", "items": {"type": "object"}},
                            "source_review_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {"type": "string", "const": "birth_profile_source_review_required"},
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "source_review_workplan_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-source-review-workplan-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "source_review_workplan_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "integrity_check": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "receipt_sha256_matches_material",
                                    "workplan_sha256_matches_material",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "workplan_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileSourceLookupPlanResponse": {
                "type": "object",
                "required": ["repo", "manifest_path", "cache_dir", "configured", "source_lookup_plan", "configuration_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "source_lookup_plan": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "would_fetch_live_sources",
                            "would_write_cache",
                            "would_write_review_manifest",
                            "source_family_catalog",
                            "selected_work_item_count",
                            "lookup_item_count",
                            "query_count",
                            "domain_summary",
                            "lookup_items",
                            "lookup_gate",
                            "source_lookup_plan_receipt",
                            "source_lookup_plan_sha256",
                            "integrity_check",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {"type": "string", "const": "birth-profile-source-lookup-plan-v1"},
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "would_fetch_live_sources": {"type": "boolean"},
                            "would_write_cache": {"type": "boolean"},
                            "would_write_review_manifest": {"type": "boolean"},
                            "source_family_catalog": {
                                "type": "object",
                                "required": [
                                    "schema_version",
                                    "source_family_count",
                                    "source_families",
                                    "birth_time_policy",
                                    "source_family_catalog_receipt",
                                    "source_family_catalog_sha256",
                                    "boundary",
                                ],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-source-family-catalog-v1",
                                    },
                                    "source_family_count": {"type": "integer"},
                                    "source_families": {"type": "array", "items": {"type": "object"}},
                                    "birth_time_policy": {"type": "string"},
                                    "source_family_catalog_receipt": {
                                        "type": "object",
                                        "required": ["schema_version", "sha256", "material"],
                                        "properties": {
                                            "schema_version": {
                                                "type": "string",
                                                "const": "birth-profile-source-family-catalog-receipt-v1",
                                            },
                                            "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                            "material": {"type": "object"},
                                        },
                                    },
                                    "source_family_catalog_sha256": {
                                        "type": "string",
                                        "pattern": "^[0-9a-f]{64}$",
                                    },
                                    "boundary": {"type": "string"},
                                },
                            },
                            "selected_work_item_count": {"type": "integer"},
                            "lookup_item_count": {"type": "integer"},
                            "query_count": {"type": "integer"},
                            "domain_summary": {"type": "array", "items": {"type": "object"}},
                            "lookup_items": {"type": "array", "items": {"type": "object"}},
                            "lookup_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "const": "birth_profile_source_lookup_requires_human_execution",
                                    },
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "source_lookup_plan_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-source-lookup-plan-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "source_lookup_plan_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "integrity_check": {
                                "type": "object",
                                "required": ["status", "receipt_sha256_matches_material", "plan_sha256_matches_material"],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "plan_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileSourceCacheTemplatePreviewResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "manifest_path",
                    "cache_dir",
                    "configured",
                    "source_cache_template_preview",
                    "configuration_guidance",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "source_cache_template_preview": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "would_write_cache",
                            "would_fetch_live_sources",
                            "would_import_profiles",
                            "template_count",
                            "templates",
                            "template_preview_gate",
                            "source_cache_template_preview_receipt",
                            "source_cache_template_preview_sha256",
                            "integrity_check",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {
                                "type": "string",
                                "const": "birth-profile-source-cache-template-preview-v1",
                            },
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "would_write_cache": {"type": "boolean"},
                            "would_fetch_live_sources": {"type": "boolean"},
                            "would_import_profiles": {"type": "boolean"},
                            "template_count": {"type": "integer"},
                            "templates": {"type": "array", "items": {"type": "object"}},
                            "template_preview_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "const": "birth_profile_source_cache_template_requires_manual_fill",
                                    },
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "source_cache_template_preview_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-source-cache-template-preview-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "source_cache_template_preview_sha256": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "integrity_check": {
                                "type": "object",
                                "required": ["status", "receipt_sha256_matches_material", "preview_sha256_matches_material"],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "preview_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileSourceCacheAuditResponse": {
                "type": "object",
                "required": ["repo", "manifest_path", "cache_dir", "configured", "source_cache_audit", "configuration_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "source_cache_audit": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "would_fetch_live_sources",
                            "would_write_cache",
                            "would_write_review_manifest",
                            "would_import_profiles",
                            "expected_cache_count",
                            "present_cache_count",
                            "missing_cache_count",
                            "reviewed_cache_count",
                            "accepted_cache_count",
                            "cache_items",
                            "cache_audit_gate",
                            "source_cache_audit_receipt",
                            "source_cache_audit_sha256",
                            "integrity_check",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {"type": "string", "const": "birth-profile-source-cache-audit-v1"},
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "would_fetch_live_sources": {"type": "boolean"},
                            "would_write_cache": {"type": "boolean"},
                            "would_write_review_manifest": {"type": "boolean"},
                            "would_import_profiles": {"type": "boolean"},
                            "expected_cache_count": {"type": "integer"},
                            "present_cache_count": {"type": "integer"},
                            "missing_cache_count": {"type": "integer"},
                            "reviewed_cache_count": {"type": "integer"},
                            "accepted_cache_count": {"type": "integer"},
                            "cache_items": {"type": "array", "items": {"type": "object"}},
                            "cache_audit_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "const": "birth_profile_source_cache_requires_reviewed_manifest_draft",
                                    },
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "source_cache_audit_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-source-cache-audit-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "source_cache_audit_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "integrity_check": {
                                "type": "object",
                                "required": ["status", "receipt_sha256_matches_material", "audit_sha256_matches_material"],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "audit_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileReviewedManifestDraftPreviewResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "manifest_path",
                    "cache_dir",
                    "configured",
                    "reviewed_manifest_draft_preview",
                    "configuration_guidance",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "reviewed_manifest_draft_preview": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "would_write_review_manifest",
                            "would_import_profiles",
                            "draft_ready_for_human_approval",
                            "review_request_count",
                            "complete_review_request_count",
                            "incomplete_review_request_count",
                            "draft_manifest",
                            "draft_manifest_sha256",
                            "draft_text_sha256",
                            "draft_gate",
                            "reviewed_manifest_draft_preview_receipt",
                            "reviewed_manifest_draft_preview_sha256",
                            "integrity_check",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {
                                "type": "string",
                                "const": "birth-profile-reviewed-manifest-draft-preview-v1",
                            },
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "would_write_review_manifest": {"type": "boolean"},
                            "would_import_profiles": {"type": "boolean"},
                            "draft_ready_for_human_approval": {"type": "boolean"},
                            "review_request_count": {"type": "integer"},
                            "complete_review_request_count": {"type": "integer"},
                            "incomplete_review_request_count": {"type": "integer"},
                            "draft_manifest": {"type": "object"},
                            "draft_manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "draft_text_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "draft_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "const": "birth_profile_reviewed_manifest_draft_requires_human_approval",
                                    },
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "reviewed_manifest_draft_preview_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-reviewed-manifest-draft-preview-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "reviewed_manifest_draft_preview_sha256": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "integrity_check": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "receipt_sha256_matches_material",
                                    "preview_sha256_matches_material",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "preview_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileReviewedManifestFilePreviewResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "manifest_path",
                    "cache_dir",
                    "target_path",
                    "configured",
                    "reviewed_manifest_file_preview",
                    "configuration_guidance",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "target_path": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "reviewed_manifest_file_preview": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "target_file",
                            "would_write_file",
                            "would_import_profiles",
                            "write_ready_for_human_approval",
                            "draft_manifest_sha256",
                            "draft_text_sha256",
                            "file_preview_gate",
                            "reviewed_manifest_file_preview_receipt",
                            "reviewed_manifest_file_preview_sha256",
                            "integrity_check",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {
                                "type": "string",
                                "const": "birth-profile-reviewed-manifest-file-preview-v1",
                            },
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "target_file": {"type": "string"},
                            "target_file_exists": {"type": "boolean"},
                            "target_file_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                            "would_write_file": {"type": "boolean"},
                            "would_import_profiles": {"type": "boolean"},
                            "write_ready_for_human_approval": {"type": "boolean"},
                            "draft_manifest_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                            "draft_text_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                            "file_preview_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "const": "birth_profile_reviewed_manifest_file_write_requires_human_approval",
                                    },
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "reviewed_manifest_file_preview_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-reviewed-manifest-file-preview-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "reviewed_manifest_file_preview_sha256": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "integrity_check": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "receipt_sha256_matches_material",
                                    "preview_sha256_matches_material",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "preview_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileImportPreviewResponse": {
                "type": "object",
                "required": ["repo", "manifest_path", "configured", "import_preview", "configuration_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "import_preview": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "would_write_file",
                            "import_allowed",
                            "import_preview_receipt",
                            "import_preview_sha256",
                            "integrity_check",
                            "import_gate",
                            "blocking_reasons",
                            "candidate_profiles",
                            "next_action",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {"type": "string", "const": "birth-profile-import-preview-v1"},
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "would_write_file": {"type": "boolean"},
                            "import_allowed": {"type": "boolean"},
                            "import_preview_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-import-preview-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "import_preview_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "integrity_check": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "receipt_sha256_matches_material",
                                    "preview_sha256_matches_material",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "preview_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "import_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {"type": "string", "const": "birth_profile_import_reviewed_profiles_present"},
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                            "candidate_profiles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "case_id",
                                        "public_name",
                                        "domain",
                                        "birth",
                                        "source",
                                        "identity_source_url",
                                        "review_status",
                                    ],
                                    "properties": {
                                        "case_id": {"type": "string"},
                                        "public_name": {"type": "string"},
                                        "domain": {"type": "string"},
                                        "birth": {
                                            "type": "object",
                                            "required": ["birth_date", "birth_time", "gender", "birthplace"],
                                            "properties": {
                                                "birth_date": {"type": "string"},
                                                "birth_time": {"type": "string"},
                                                "gender": {"type": "string"},
                                                "birthplace": {"type": "string"},
                                            },
                                        },
                                        "source": {
                                            "type": "object",
                                            "required": ["name", "url", "rating", "note"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "url": {"type": "string"},
                                                "rating": {"type": "string"},
                                                "note": {"type": "string"},
                                            },
                                        },
                                        "identity_source_url": {"type": "string"},
                                        "review_status": {"type": "string"},
                                        "collected_before_rule_change": {"type": "boolean"},
                                    },
                                },
                            },
                            "next_action": {"type": "string"},
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "BirthProfileFixturePatchPreviewResponse": {
                "type": "object",
                "required": ["repo", "manifest_path", "configured", "fixture_patch_preview", "configuration_guidance"],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": "string"},
                    "configured": {"type": "boolean"},
                    "fixture_patch_preview": {
                        "type": "object",
                        "required": [
                            "schema_version",
                            "status",
                            "valid",
                            "target_file",
                            "target_file_sha256",
                            "would_write_file",
                            "patch_ready_for_review",
                            "candidate_count",
                            "candidate_case_ids",
                            "candidate_profiles",
                            "patch_format",
                            "patch_text",
                            "patch_text_sha256",
                            "fixture_patch_preview_receipt",
                            "fixture_patch_preview_sha256",
                            "integrity_check",
                            "patch_gate",
                            "blocking_reasons",
                            "next_action",
                            "boundary",
                        ],
                        "properties": {
                            "schema_version": {
                                "type": "string",
                                "const": "birth-profile-fixture-patch-preview-v1",
                            },
                            "status": {"type": "string"},
                            "valid": {"type": "boolean"},
                            "target_file": {"type": "string"},
                            "target_file_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                            "would_write_file": {"type": "boolean"},
                            "patch_ready_for_review": {"type": "boolean"},
                            "candidate_count": {"type": "integer"},
                            "candidate_case_ids": {"type": "array", "items": {"type": "string"}},
                            "candidate_profiles": {"type": "array", "items": {"type": "object"}},
                            "patch_format": {"type": "string"},
                            "patch_text": {"type": "string"},
                            "patch_text_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "fixture_patch_preview_receipt": {
                                "type": "object",
                                "required": ["schema_version", "sha256", "material"],
                                "properties": {
                                    "schema_version": {
                                        "type": "string",
                                        "const": "birth-profile-fixture-patch-preview-receipt-v1",
                                    },
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "material": {"type": "object"},
                                },
                            },
                            "fixture_patch_preview_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            "integrity_check": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "receipt_sha256_matches_material",
                                    "preview_sha256_matches_material",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "receipt_sha256_matches_material": {"type": "boolean"},
                                    "preview_sha256_matches_material": {"type": "boolean"},
                                },
                            },
                            "patch_gate": {
                                "type": "object",
                                "required": ["id", "passed", "reason", "blocking_reasons"],
                                "properties": {
                                    "id": {"type": "string", "const": "birth_profile_fixture_patch_preview_ready"},
                                    "passed": {"type": "boolean"},
                                    "reason": {"type": "string"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                            "next_action": {"type": "string"},
                            "boundary": {"type": "string"},
                        },
                    },
                    "configuration_guidance": {
                        "type": "object",
                        "required": [
                            "example_manifest_path",
                            "example_is_demonstration_only",
                            "cli_command",
                            "http_query",
                            "policy",
                        ],
                        "properties": {
                            "example_manifest_path": {"type": "string"},
                            "example_is_demonstration_only": {"type": "boolean"},
                            "cli_command": {"type": "string"},
                            "http_query": {"type": "string"},
                            "policy": {"type": "string"},
                        },
                    },
                },
            },
            "FeedbackMemorySafetyAudit": {
                "type": "object",
                "required": [
                    "status",
                    "unsafe_feedback_count",
                    "unsafe_corrections",
                    "policy",
                    "ordinary_correction_count",
                    "safety_guardrail_prior",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["clean", "contains_quarantined_feedback"]},
                    "unsafe_feedback_count": {"type": "integer"},
                    "unsafe_corrections": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "policy": {"type": "string"},
                    "ordinary_correction_count": {"type": "integer"},
                    "safety_guardrail_prior": {"type": "number"},
                },
            },
            "EvidenceMaterializationItem": {
                "type": "object",
                "required": ["evidence", "kind", "status"],
                "properties": {
                    "evidence": {"type": "string"},
                    "kind": {"type": "string"},
                    "status": {"type": "string", "enum": ["passed", "failed", "unchecked"]},
                    "resolved": {"type": "string"},
                    "module": {"type": "string"},
                    "symbol": {"type": "string"},
                    "resolved_symbol": {"type": "string"},
                    "field_path": {"type": "string"},
                    "value_type": {"type": "string"},
                    "reason": {"type": "string"},
                    "checked_candidates": {"type": "array", "items": {"type": "string"}},
                    "checked_modules": {"type": "array", "items": {"type": "string"}},
                },
            },
            "EvidenceMaterializationRequirement": {
                "type": "object",
                "required": ["id", "status", "evidence"],
                "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string", "enum": ["passed", "failed", "partially_checked"]},
                    "evidence": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/EvidenceMaterializationItem"},
                    },
                },
            },
            "EvidenceMaterialization": {
                "type": "object",
                "required": [
                    "status",
                    "total_evidence",
                    "passed_count",
                    "failed_count",
                    "unchecked_count",
                    "requirements",
                    "policy",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["passed", "failed", "partially_checked"]},
                    "total_evidence": {"type": "integer"},
                    "passed_count": {"type": "integer"},
                    "failed_count": {"type": "integer"},
                    "unchecked_count": {"type": "integer"},
                    "requirements": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/EvidenceMaterializationRequirement"},
                    },
                    "policy": {"type": "string"},
                },
            },
            "ProviderOnboardingAuditSummary": {
                "type": "object",
                "required": [
                    "status",
                    "receipt_sha256",
                    "domain_count",
                    "ready_domain_count",
                    "example_provider_receipt_sha256",
                    "domain_missing_evidence",
                    "missing_evidence_counts",
                ],
                "properties": {
                    "status": {"type": ["string", "null"]},
                    "receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "domain_count": {"type": ["integer", "null"]},
                    "ready_domain_count": {"type": ["integer", "null"]},
                    "example_provider_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "domain_missing_evidence": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                    "missing_evidence_counts": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    },
                },
            },
            "CapabilityFlagMap": {
                "type": "object",
                "additionalProperties": {"type": "boolean"},
            },
            "RequestScopedProviderContractSummary": {
                "type": "object",
                "required": [
                    "status",
                    "checked_domains",
                    "provenance_checked_domains",
                    "requires_provenance_fields",
                    "meaning",
                ],
                "properties": {
                    "status": {"type": "string"},
                    "checked_domains": {"type": "array", "items": {"type": "string"}},
                    "provenance_checked_domains": {"type": "array", "items": {"type": "string"}},
                    "requires_provenance_fields": {"type": "array", "items": {"type": "string"}},
                    "meaning": {"type": "string"},
                },
            },
            "ProviderProtocolIdentityHandshakeSummary": {
                "type": "object",
                "required": ["ready", "domains", "failures"],
                "properties": {
                    "ready": {"type": "boolean"},
                    "domains": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": [
                                "sample_stdin_has_protocol_identity",
                                "stdin_schema_requires_protocol_identity",
                                "production_requires_stdout_echo",
                            ],
                            "properties": {
                                "sample_stdin_has_protocol_identity": {"type": "boolean"},
                                "stdin_schema_requires_protocol_identity": {"type": "boolean"},
                                "production_requires_stdout_echo": {"type": "boolean"},
                            },
                        },
                    },
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ProviderProtocolGovernanceSummary": {
                "type": "object",
                "required": [
                    "status",
                    "protocol_version",
                    "protocol_hash",
                    "protocol_receipt_sha256",
                    "protocol_document_sha256",
                    "domain_count",
                    "domains",
                    "domain_protocol_hashes",
                    "sample_stdout_contracts_valid",
                    "runtime_identity_handshake",
                    "production_gate",
                    "receipt_material_fields",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["ready", "incomplete"]},
                    "protocol_version": {"type": ["string", "null"]},
                    "protocol_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "protocol_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "protocol_document_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "domain_count": {"type": "integer"},
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "domain_protocol_hashes": {
                        "type": "object",
                        "additionalProperties": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                    "sample_stdout_contracts_valid": {"type": "boolean"},
                    "runtime_identity_handshake": {"$ref": "#/schemas/ProviderProtocolIdentityHandshakeSummary"},
                    "production_gate": {"type": "string"},
                    "receipt_material_fields": {"type": "array", "items": {"type": "string"}},
                },
            },
            "CapabilityAuditReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "capabilities",
                    "blocked_capability_coverage",
                    "known_gap_handoff_bundle",
                    "request_scoped_provider_contract",
                    "provider_protocol_governance",
                    "provider_onboarding",
                    "provider_production_guidance",
                    "github_comparison_receipt_sha256",
                    "plan_compliance_receipt_sha256",
                    "famous_case_validation",
                    "famous_case_school_calibration",
                    "famous_case_annual_event_calibration",
                    "industry_event_cross_domain_fixture_import",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "capability-audit-receipt-v1"},
                    "status": {"type": "string"},
                    "capabilities": {"$ref": "#/schemas/CapabilityFlagMap"},
                    "blocked_capability_coverage": {"$ref": "#/schemas/BlockedCapabilityCoverage"},
                    "known_gap_handoff_bundle": {"$ref": "#/schemas/KnownGapHandoffBundle"},
                    "request_scoped_provider_contract": {"$ref": "#/schemas/RequestScopedProviderContractSummary"},
                    "provider_protocol_governance": {"$ref": "#/schemas/ProviderProtocolGovernanceSummary"},
                    "provider_onboarding": {"$ref": "#/schemas/ProviderOnboardingAuditSummary"},
                    "provider_production_guidance": {"$ref": "#/schemas/ProviderProductionGuidance"},
                    "github_comparison_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "plan_compliance_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "famous_case_validation": {"$ref": "#/schemas/FamousCaseValidationReceiptSummary"},
                    "famous_case_school_calibration": {
                        "$ref": "#/schemas/FamousCaseSchoolCalibrationReceiptSummary"
                    },
                    "famous_case_annual_event_calibration": {
                        "$ref": "#/schemas/FamousCaseAnnualEventCalibrationReceiptSummary"
                    },
                    "industry_event_cross_domain_fixture_import": {
                        "$ref": "#/schemas/IndustryEventCrossDomainFixtureImportReceipt"
                    },
                },
            },
            "IndustryEventCrossDomainFixtureImportMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "candidate_path",
                    "query_plan_path",
                    "cache_dir",
                    "fixture_response_paths",
                    "offline_only",
                    "production_evidence",
                    "candidate_count",
                    "draft_count",
                    "positive_record_count",
                    "negative_record_count",
                    "record_count",
                    "domains",
                    "cross_domain_coverage_gate_passed",
                    "domain_coverage_summary",
                    "symbolic_scoring_readiness_summary",
                    "candidate_pool_fetch_cache_receipt_sha256",
                    "candidate_pool_draft_import_receipt_sha256",
                    "validation_label_table_receipt_sha256",
                    "boundary",
                    "failures",
                ],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "const": "industry-event-cross-domain-fixture-import-receipt-v1",
                    },
                    "status": {"type": "string", "enum": ["ready_example", "incomplete"]},
                    "candidate_path": {"type": "string"},
                    "query_plan_path": {"type": "string"},
                    "cache_dir": {"type": "string"},
                    "fixture_response_paths": {
                        "type": "object",
                        "required": ["film", "music", "sports"],
                        "properties": {
                            "film": {"type": "string"},
                            "music": {"type": "string"},
                            "sports": {"type": "string"},
                        },
                    },
                    "offline_only": {"type": "boolean"},
                    "production_evidence": {"type": "boolean"},
                    "candidate_count": {"type": "integer"},
                    "draft_count": {"type": "integer"},
                    "positive_record_count": {"type": "integer"},
                    "negative_record_count": {"type": "integer"},
                    "record_count": {"type": "integer"},
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "cross_domain_coverage_gate_passed": {"type": "boolean"},
                    "domain_coverage_summary": {"type": "array", "items": {"type": "object"}},
                    "symbolic_scoring_readiness_summary": {
                        "type": "object",
                        "required": [
                            "status",
                            "label_count",
                            "ready_label_count",
                            "blocked_label_count",
                            "case_count",
                            "ready_case_count",
                            "blocked_case_count",
                            "ready_case_ids",
                            "blocked_case_ids",
                            "missing_birth_profile_case_ids",
                            "domain_topic_summary",
                            "gates",
                            "birth_profile_completion_task_plan",
                            "birth_profile_completion_workplan_summary",
                            "birth_profile_review_manifest_summary",
                            "birth_profile_source_review_workplan_summary",
                            "birth_profile_source_lookup_plan_summary",
                            "birth_profile_source_cache_template_preview_summary",
                            "birth_profile_source_family_cache_enforcement_summary",
                            "birth_profile_substantive_evidence_cache_enforcement_summary",
                            "birth_profile_source_cache_audit_summary",
                            "birth_profile_reviewed_manifest_draft_preview_summary",
                            "birth_profile_reviewed_manifest_file_preview_summary",
                            "birth_profile_import_preview_summary",
                            "birth_profile_fixture_patch_preview_summary",
                            "symbolic_scoring_readiness_receipt_sha256",
                            "symbolic_annual_score_receipt_sha256",
                            "evidence_workplan_receipt_sha256",
                            "birth_profile_review_manifest_receipt_sha256",
                            "birth_profile_source_review_workplan_receipt_sha256",
                            "birth_profile_source_lookup_plan_receipt_sha256",
                            "birth_profile_source_cache_template_preview_receipt_sha256",
                            "birth_profile_source_cache_audit_receipt_sha256",
                            "birth_profile_reviewed_manifest_draft_preview_receipt_sha256",
                            "birth_profile_reviewed_manifest_file_preview_receipt_sha256",
                            "birth_profile_import_preview_receipt_sha256",
                            "birth_profile_fixture_patch_preview_receipt_sha256",
                            "boundary",
                        ],
                        "properties": {
                            "status": {"type": "string"},
                            "label_count": {"type": "integer"},
                            "ready_label_count": {"type": "integer"},
                            "blocked_label_count": {"type": "integer"},
                            "case_count": {"type": "integer"},
                            "ready_case_count": {"type": "integer"},
                            "blocked_case_count": {"type": "integer"},
                            "ready_case_ids": {"type": "array", "items": {"type": "string"}},
                            "blocked_case_ids": {"type": "array", "items": {"type": "string"}},
                            "missing_birth_profile_case_ids": {"type": "array", "items": {"type": "string"}},
                            "domain_topic_summary": {"type": "array", "items": {"type": "object"}},
                            "gates": {"type": "array", "items": {"type": "object"}},
                            "birth_profile_completion_task_plan": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "task_id",
                                        "domain",
                                        "symbolic_event_topic",
                                        "priority",
                                        "task_type",
                                        "blocked_label_count",
                                        "blocked_case_count",
                                        "blocked_case_ids",
                                        "blocked_public_names",
                                        "next_evidence_to_add",
                                        "acceptance_criteria",
                                        "blocking_reasons",
                                        "boundary",
                                    ],
                                    "properties": {
                                        "task_id": {"type": ["string", "null"]},
                                        "domain": {"type": ["string", "null"]},
                                        "symbolic_event_topic": {"type": ["string", "null"]},
                                        "priority": {"type": ["string", "null"]},
                                        "task_type": {"type": ["string", "null"]},
                                        "blocked_label_count": {"type": "integer"},
                                        "blocked_case_count": {"type": "integer"},
                                        "blocked_case_ids": {"type": "array", "items": {"type": "string"}},
                                        "blocked_public_names": {"type": "array", "items": {"type": "string"}},
                                        "next_evidence_to_add": {"type": "array", "items": {"type": "string"}},
                                        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                                        "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                        "boundary": {"type": "string"},
                                    },
                                },
                            },
                            "birth_profile_completion_workplan_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "source_task_count",
                                    "deferred_task_count",
                                    "work_item_count",
                                    "readiness_status",
                                    "deferred_blocked_gate_count",
                                    "deferred_failed_integrity_check_count",
                                    "deferred_task_summaries",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "valid": {"type": "boolean"},
                                    "source_task_count": {"type": "integer"},
                                    "deferred_task_count": {"type": "integer"},
                                    "work_item_count": {"type": "integer"},
                                    "readiness_status": {"type": "string"},
                                    "deferred_blocked_gate_count": {"type": "integer"},
                                    "deferred_failed_integrity_check_count": {"type": "integer"},
                                    "deferred_task_summaries": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": [
                                                "task_id",
                                                "domain",
                                                "symbolic_event_topic",
                                                "task_type",
                                                "blocked_case_ids",
                                                "local_birth_profile_suggestion_count",
                                                "local_birth_profile_suggestion_case_ids",
                                                "completion_work_order_status",
                                                "gate_summary_status",
                                                "blocked_gate_count",
                                                "failed_integrity_check_count",
                                                "next_action",
                                            ],
                                            "properties": {
                                                "task_id": {"type": ["string", "null"]},
                                                "domain": {"type": ["string", "null"]},
                                                "symbolic_event_topic": {"type": ["string", "null"]},
                                                "task_type": {"type": ["string", "null"]},
                                                "blocked_case_ids": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "local_birth_profile_suggestion_count": {"type": "integer"},
                                                "local_birth_profile_suggestion_case_ids": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "completion_work_order_status": {"type": ["string", "null"]},
                                                "gate_summary_status": {"type": ["string", "null"]},
                                                "blocked_gate_count": {"type": "integer"},
                                                "failed_integrity_check_count": {"type": "integer"},
                                                "next_action": {"type": ["string", "null"]},
                                            },
                                        },
                                    },
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_review_manifest_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "production_evidence",
                                    "request_count",
                                    "case_count",
                                    "domains",
                                    "blocked_label_count",
                                    "ready_for_import",
                                    "domain_summary",
                                    "failures",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "production_evidence": {"type": "boolean"},
                                    "request_count": {"type": "integer"},
                                    "case_count": {"type": "integer"},
                                    "domains": {"type": "array", "items": {"type": "string"}},
                                    "blocked_label_count": {"type": "integer"},
                                    "ready_for_import": {"type": "boolean"},
                                    "domain_summary": {"type": "array", "items": {"type": "object"}},
                                    "failures": {"type": "array", "items": {"type": "string"}},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_source_review_workplan_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_fetch_live_sources",
                                    "would_write_review_manifest",
                                    "request_count",
                                    "work_item_count",
                                    "review_progress_summary",
                                    "field_gap_summary",
                                    "source_review_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_fetch_live_sources": {"type": "boolean"},
                                    "would_write_review_manifest": {"type": "boolean"},
                                    "request_count": {"type": "integer"},
                                    "work_item_count": {"type": "integer"},
                                    "review_progress_summary": {"type": "object"},
                                    "field_gap_summary": {"type": "object"},
                                    "source_review_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_source_lookup_plan_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_fetch_live_sources",
                                    "would_write_cache",
                                    "would_write_review_manifest",
                                    "lookup_item_count",
                                    "query_count",
                                    "source_family_count",
                                    "source_family_catalog_bound",
                                    "birth_time_source_policy_bound",
                                    "identity_anchor_birth_time_disallowed",
                                    "lookup_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_fetch_live_sources": {"type": "boolean"},
                                    "would_write_cache": {"type": "boolean"},
                                    "would_write_review_manifest": {"type": "boolean"},
                                    "lookup_item_count": {"type": "integer"},
                                    "query_count": {"type": "integer"},
                                    "source_family_count": {"type": "integer"},
                                    "source_family_catalog_bound": {"type": "boolean"},
                                    "birth_time_source_policy_bound": {"type": "boolean"},
                                    "identity_anchor_birth_time_disallowed": {"type": "boolean"},
                                    "domain_summary": {"type": "array", "items": {"type": "object"}},
                                    "lookup_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_source_cache_audit_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_fetch_live_sources",
                                    "would_write_cache",
                                    "would_write_review_manifest",
                                    "would_import_profiles",
                                    "expected_cache_count",
                                    "present_cache_count",
                                    "missing_cache_count",
                                    "accepted_cache_count",
                                    "cache_audit_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_fetch_live_sources": {"type": "boolean"},
                                    "would_write_cache": {"type": "boolean"},
                                    "would_write_review_manifest": {"type": "boolean"},
                                    "would_import_profiles": {"type": "boolean"},
                                    "expected_cache_count": {"type": "integer"},
                                    "present_cache_count": {"type": "integer"},
                                    "missing_cache_count": {"type": "integer"},
                                    "accepted_cache_count": {"type": "integer"},
                                    "cache_audit_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_source_cache_template_preview_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_fetch_live_sources",
                                    "would_write_cache",
                                    "would_import_profiles",
                                    "template_count",
                                    "template_preview_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_fetch_live_sources": {"type": "boolean"},
                                    "would_write_cache": {"type": "boolean"},
                                    "would_import_profiles": {"type": "boolean"},
                                    "template_count": {"type": "integer"},
                                    "template_preview_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_source_family_cache_enforcement_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "probe_executed",
                                    "identity_anchor_birth_time_rejected",
                                    "accepted_cache_count_after_probe",
                                    "probe_source_family_id",
                                    "failure_contains_birth_time_policy",
                                    "failures",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "valid": {"type": "boolean"},
                                    "probe_executed": {"type": "boolean"},
                                    "identity_anchor_birth_time_rejected": {"type": "boolean"},
                                    "accepted_cache_count_after_probe": {"type": ["integer", "null"]},
                                    "probe_source_family_id": {"type": "string"},
                                    "failure_contains_birth_time_policy": {"type": "boolean"},
                                    "failures": {"type": "array", "items": {"type": "string"}},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_substantive_evidence_cache_enforcement_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "probe_executed",
                                    "metadata_only_reviewed_cache_rejected",
                                    "accepted_cache_count_after_probe",
                                    "probe_source_family_id",
                                    "failure_contains_substantive_birth_policy",
                                    "failures",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": "string"},
                                    "valid": {"type": "boolean"},
                                    "probe_executed": {"type": "boolean"},
                                    "metadata_only_reviewed_cache_rejected": {"type": "boolean"},
                                    "accepted_cache_count_after_probe": {"type": ["integer", "null"]},
                                    "probe_source_family_id": {"type": "string"},
                                    "failure_contains_substantive_birth_policy": {"type": "boolean"},
                                    "failures": {"type": "array", "items": {"type": "string"}},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_reviewed_manifest_draft_preview_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_write_review_manifest",
                                    "would_import_profiles",
                                    "draft_ready_for_human_approval",
                                    "review_request_count",
                                    "complete_review_request_count",
                                    "incomplete_review_request_count",
                                    "draft_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_write_review_manifest": {"type": "boolean"},
                                    "would_import_profiles": {"type": "boolean"},
                                    "draft_ready_for_human_approval": {"type": "boolean"},
                                    "review_request_count": {"type": "integer"},
                                    "complete_review_request_count": {"type": "integer"},
                                    "incomplete_review_request_count": {"type": "integer"},
                                    "draft_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_reviewed_manifest_file_preview_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_write_file",
                                    "would_import_profiles",
                                    "write_ready_for_human_approval",
                                    "target_file",
                                    "target_file_sha256",
                                    "file_preview_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_write_file": {"type": "boolean"},
                                    "would_import_profiles": {"type": "boolean"},
                                    "write_ready_for_human_approval": {"type": "boolean"},
                                    "target_file": {"type": "string"},
                                    "target_file_sha256": {
                                        "type": ["string", "null"],
                                        "pattern": "^[0-9a-f]{64}$",
                                    },
                                    "file_preview_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_import_preview_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_write_file",
                                    "import_allowed",
                                    "request_count",
                                    "blocked_request_count",
                                    "import_ready_request_count",
                                    "import_gate_passed",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_write_file": {"type": "boolean"},
                                    "import_allowed": {"type": "boolean"},
                                    "request_count": {"type": "integer"},
                                    "blocked_request_count": {"type": "integer"},
                                    "import_ready_request_count": {"type": "integer"},
                                    "import_gate_passed": {"type": "boolean"},
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "birth_profile_fixture_patch_preview_summary": {
                                "type": "object",
                                "required": [
                                    "status",
                                    "valid",
                                    "would_write_file",
                                    "patch_ready_for_review",
                                    "candidate_count",
                                    "candidate_case_ids",
                                    "patch_gate_passed",
                                    "target_file_sha256",
                                    "patch_text_sha256",
                                    "blocking_reasons",
                                    "integrity_check_status",
                                    "boundary",
                                ],
                                "properties": {
                                    "status": {"type": ["string", "null"]},
                                    "valid": {"type": "boolean"},
                                    "would_write_file": {"type": "boolean"},
                                    "patch_ready_for_review": {"type": "boolean"},
                                    "candidate_count": {"type": "integer"},
                                    "candidate_case_ids": {"type": "array", "items": {"type": "string"}},
                                    "patch_gate_passed": {"type": "boolean"},
                                    "target_file_sha256": {
                                        "type": ["string", "null"],
                                        "pattern": "^[0-9a-f]{64}$",
                                    },
                                    "patch_text_sha256": {
                                        "type": ["string", "null"],
                                        "pattern": "^[0-9a-f]{64}$",
                                    },
                                    "blocking_reasons": {"type": "array", "items": {"type": "string"}},
                                    "integrity_check_status": {"type": ["string", "null"]},
                                    "boundary": {"type": "string"},
                                },
                            },
                            "symbolic_scoring_readiness_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "symbolic_annual_score_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "evidence_workplan_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_review_manifest_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_source_review_workplan_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_source_lookup_plan_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_source_cache_template_preview_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_source_cache_audit_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_reviewed_manifest_draft_preview_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_reviewed_manifest_file_preview_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_import_preview_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "birth_profile_fixture_patch_preview_receipt_sha256": {
                                "type": ["string", "null"],
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "boundary": {"type": "string"},
                        },
                    },
                    "candidate_pool_fetch_cache_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "candidate_pool_draft_import_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "validation_label_table_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "boundary": {"type": "string"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "IndustryEventCrossDomainFixtureImportReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "const": "industry-event-cross-domain-fixture-import-receipt-v1",
                    },
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/IndustryEventCrossDomainFixtureImportMaterial"},
                },
            },
            "BlockedCapabilityCoverageEntry": {
                "type": "object",
                "required": [
                    "capability",
                    "accounted",
                    "classification",
                    "gap_ids",
                    "missing_gap_ids",
                    "owner_domains",
                    "blocking_scopes",
                    "policy",
                ],
                "properties": {
                    "capability": {"type": "string"},
                    "accounted": {"type": "boolean"},
                    "classification": {
                        "type": "string",
                        "enum": ["known_gap", "optional_configuration", "unaccounted"],
                    },
                    "gap_ids": {"type": "array", "items": {"type": "string"}},
                    "missing_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "owner_domains": {"type": "array", "items": {"type": "string"}},
                    "blocking_scopes": {"type": "array", "items": {"type": "string"}},
                    "policy": {"type": "string"},
                },
            },
            "BlockedCapabilityCoverage": {
                "type": "object",
                "required": [
                    "status",
                    "coverage_complete",
                    "false_capability_count",
                    "accounted_count",
                    "unaccounted_capabilities",
                    "entries",
                    "coverage_sha256",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["covered", "uncovered"]},
                    "coverage_complete": {"type": "boolean"},
                    "false_capability_count": {"type": "integer"},
                    "accounted_count": {"type": "integer"},
                    "unaccounted_capabilities": {"type": "array", "items": {"type": "string"}},
                    "entries": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/BlockedCapabilityCoverageEntry"},
                    },
                    "coverage_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "KnownGapHandoffCandidate": {
                "type": "object",
                "required": ["name", "url", "fit", "audit_note"],
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "fit": {"type": "string"},
                    "audit_note": {"type": "string"},
                },
            },
            "KnownGapHandoffItem": {
                "type": "object",
                "required": [
                    "gap_id",
                    "severity",
                    "status",
                    "owner_domain",
                    "blocking_scope",
                    "requirement",
                    "closure_condition",
                    "required_env_vars",
                    "required_provenance_env_vars",
                    "verification_commands",
                    "production_gate_ids",
                    "external_candidate_projects",
                    "blocked_capabilities",
                    "handoff_ready",
                ],
                "properties": {
                    "gap_id": {"type": "string"},
                    "severity": {"type": "string"},
                    "status": {"type": "string"},
                    "owner_domain": {"type": "string"},
                    "blocking_scope": {"type": "string"},
                    "requirement": {"type": "string"},
                    "closure_condition": {"type": "string"},
                    "required_env_vars": {"type": "array", "items": {"type": "string"}},
                    "required_provenance_env_vars": {"type": "array", "items": {"type": "string"}},
                    "verification_commands": {"type": "array", "items": {"type": "string"}},
                    "production_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "external_candidate_projects": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/KnownGapHandoffCandidate"},
                    },
                    "blocked_capabilities": {"type": "array", "items": {"type": "string"}},
                    "handoff_ready": {"type": "boolean"},
                },
            },
            "KnownGapHandoffBundle": {
                "type": "object",
                "required": [
                    "bundle_version",
                    "status",
                    "gap_count",
                    "open_gap_ids",
                    "missing_handoff_gap_ids",
                    "items",
                    "bundle_sha256",
                ],
                "properties": {
                    "bundle_version": {"type": "string", "const": "known-gap-handoff-v1"},
                    "status": {"type": "string", "enum": ["ready", "incomplete"]},
                    "gap_count": {"type": "integer"},
                    "open_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "missing_handoff_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "items": {"type": "array", "items": {"$ref": "#/schemas/KnownGapHandoffItem"}},
                    "bundle_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "KnownGapHandoffExportResponse": {
                "type": "object",
                "required": [
                    "schema_version",
                    "repo",
                    "status",
                    "known_gap_ids",
                    "known_gap_handoff_bundle",
                    "audit_receipt_sha256",
                    "expected_audit_receipt_sha256",
                    "audit_receipt_matches_expected",
                    "audit_receipt_mismatch_reason",
                    "handoff_export_receipt",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "known-gap-handoff-export-v1"},
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["ready", "incomplete"]},
                    "known_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "known_gap_handoff_bundle": {"$ref": "#/schemas/KnownGapHandoffBundle"},
                    "audit_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "expected_audit_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "audit_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "audit_receipt_mismatch_reason": {"type": "string"},
                    "handoff_export_receipt": {"$ref": "#/schemas/KnownGapHandoffExportReceipt"},
                },
            },
            "KnownGapHandoffExportReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "repo",
                    "status",
                    "known_gap_ids",
                    "bundle_sha256",
                    "audit_receipt_sha256",
                    "expected_audit_receipt_sha256",
                    "audit_receipt_matches_expected",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "known-gap-handoff-export-receipt-v1"},
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["ready", "incomplete"]},
                    "known_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "bundle_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "audit_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "expected_audit_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "audit_receipt_matches_expected": {"type": ["boolean", "null"]},
                },
            },
            "KnownGapHandoffExportReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "known-gap-handoff-export-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/KnownGapHandoffExportReceiptMaterial"},
                },
            },
            "KnownGapHandoffExportVerificationResponse": {
                "type": "object",
                "required": [
                    "schema_version",
                    "valid",
                    "failures",
                    "handoff_export_receipt_sha256",
                    "expected_handoff_export_receipt_sha256",
                    "handoff_export_receipt_matches_expected",
                    "expected_handoff_export_receipt_sha256_material",
                    "bundle_sha256",
                    "expected_bundle_sha256",
                    "bundle_hash_valid",
                    "receipt_material_valid",
                    "receipt_hash_valid",
                    "receipt_schema_valid",
                    "known_gap_ids_match_bundle",
                ],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "const": "known-gap-handoff-export-verification-v1",
                    },
                    "valid": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                    "handoff_export_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "expected_handoff_export_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "handoff_export_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "expected_handoff_export_receipt_sha256_material": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "bundle_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "expected_bundle_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "bundle_hash_valid": {"type": "boolean"},
                    "receipt_material_valid": {"type": "boolean"},
                    "receipt_hash_valid": {"type": "boolean"},
                    "receipt_schema_valid": {"type": "boolean"},
                    "known_gap_ids_match_bundle": {"type": "boolean"},
                },
            },
            "KnownGapHandoffExportVerificationRequest": {
                "type": "object",
                "required": ["handoff_export"],
                "properties": {
                    "handoff_export": {"$ref": "#/schemas/KnownGapHandoffExportResponse"},
                    "expected_handoff_export_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
            },
            "KnownGapHandoffChecklistRequest": {
                "type": "object",
                "required": ["handoff_export"],
                "properties": {
                    "handoff_export": {"$ref": "#/schemas/KnownGapHandoffExportResponse"},
                    "expected_handoff_export_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "expected_checklist_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
            },
            "KnownGapHandoffChecklistItem": {
                "type": "object",
                "required": [
                    "gap_id",
                    "owner_domain",
                    "blocking_scope",
                    "handoff_ready",
                    "ready_to_implement",
                    "required_env_vars",
                    "required_provenance_env_vars",
                    "external_candidate_projects",
                    "verification_commands",
                    "production_gate_ids",
                    "blocked_capabilities",
                    "closure_condition",
                    "checklist",
                ],
                "properties": {
                    "gap_id": {"type": "string"},
                    "owner_domain": {"type": "string"},
                    "blocking_scope": {"type": "string"},
                    "handoff_ready": {"type": "boolean"},
                    "ready_to_implement": {"type": "boolean"},
                    "required_env_vars": {"type": "array", "items": {"type": "string"}},
                    "required_provenance_env_vars": {"type": "array", "items": {"type": "string"}},
                    "external_candidate_projects": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/KnownGapHandoffCandidate"},
                    },
                    "verification_commands": {"type": "array", "items": {"type": "string"}},
                    "production_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "blocked_capabilities": {"type": "array", "items": {"type": "string"}},
                    "closure_condition": {"type": "string"},
                    "checklist": {"type": "array", "items": {"type": "string"}},
                },
            },
            "KnownGapHandoffChecklistReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "handoff_export_receipt_sha256",
                    "verification_valid",
                    "gap_ids",
                    "item_count",
                    "ready_item_count",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "known-gap-handoff-checklist-receipt-v1"},
                    "handoff_export_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "verification_valid": {"type": "boolean"},
                    "gap_ids": {"type": "array", "items": {"type": "string"}},
                    "item_count": {"type": "integer"},
                    "ready_item_count": {"type": "integer"},
                },
            },
            "KnownGapHandoffChecklistReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "known-gap-handoff-checklist-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/KnownGapHandoffChecklistReceiptMaterial"},
                },
            },
            "KnownGapHandoffChecklistResponse": {
                "type": "object",
                "required": [
                    "schema_version",
                    "status",
                    "verification",
                    "item_count",
                    "ready_item_count",
                    "items",
                    "expected_checklist_receipt_sha256",
                    "checklist_receipt_matches_expected",
                    "checklist_receipt_mismatch_reason",
                    "checklist_receipt",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "known-gap-handoff-checklist-v1"},
                    "status": {"type": "string", "enum": ["ready", "blocked"]},
                    "verification": {"$ref": "#/schemas/KnownGapHandoffExportVerificationResponse"},
                    "item_count": {"type": "integer"},
                    "ready_item_count": {"type": "integer"},
                    "items": {"type": "array", "items": {"$ref": "#/schemas/KnownGapHandoffChecklistItem"}},
                    "expected_checklist_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "checklist_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "checklist_receipt_mismatch_reason": {"type": "string"},
                    "checklist_receipt": {"$ref": "#/schemas/KnownGapHandoffChecklistReceipt"},
                },
            },
            "CapabilityAuditReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "capability-audit-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/CapabilityAuditReceiptMaterial"},
                },
            },
            "MethodSurfaceReceiptSummary": {
                "type": "object",
                "required": ["schema_version", "sha256", "domains"],
                "properties": {
                    "schema_version": {"type": "string", "const": "method-surface-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "domains": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "MethodLineageReceiptSummary": {
                "type": "object",
                "required": ["schema_version", "sha256", "record_count", "traditions", "implemented_statuses", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "mingli-method-lineage-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "record_count": {"type": "integer"},
                    "traditions": {"type": "array", "items": {"type": "string"}},
                    "implemented_statuses": {"type": "array", "items": {"type": "string"}},
                    "material": {"type": "object"},
                },
            },
            "FamousCaseValidationReceiptSummary": {
                "type": "object",
                "required": [
                    "schema_version",
                    "sha256",
                    "case_count",
                    "domains",
                    "sources",
                    "ratings",
                    "domain_coverage",
                    "birth_source_quality",
                    "material",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "mingli-famous-case-validation-v2"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "case_count": {"type": "integer"},
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "ratings": {"type": "array", "items": {"type": "string"}},
                    "domain_coverage": {"type": "array", "items": {"type": "object"}},
                    "birth_source_quality": {"type": "object"},
                    "material": {"type": "object"},
                },
            },
            "FamousCaseSchoolCalibrationReceiptSummary": {
                "type": "object",
                "required": [
                    "schema_version",
                    "sha256",
                    "fixture_sha256",
                    "case_count",
                    "mean_topic_recall",
                    "low_coverage_cases",
                    "school_summary",
                    "domain_summary",
                    "boundary",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "mingli-famous-case-school-calibration-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "fixture_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "case_count": {"type": "integer"},
                    "mean_topic_recall": {"type": "number"},
                    "low_coverage_cases": {"type": "array", "items": {"type": "object"}},
                    "school_summary": {"type": "array", "items": {"type": "object"}},
                    "domain_summary": {"type": "array", "items": {"type": "object"}},
                    "boundary": {"type": "string"},
                },
            },
            "FamousCaseAnnualEventCalibrationReceiptSummary": {
                "type": "object",
                "required": [
                    "schema_version",
                    "sha256",
                    "fixture_sha256",
                    "case_count",
                    "event_count",
                    "negative_year_count",
                    "false_positive_count",
                    "strict_exact_hit_count",
                    "strict_false_positive_count",
                    "exact_hit_rate",
                    "window_hit_rate",
                    "exact_precision",
                    "false_positive_rate",
                    "strict_exact_hit_rate",
                    "strict_exact_precision",
                    "strict_false_positive_rate",
                    "low_coverage_cases",
                    "birth_source_quality_summary",
                    "domain_summary",
                    "domain_topic_summary",
                    "domain_topic_refinement_queue",
                    "domain_topic_variant_sweep",
                    "topic_summary",
                    "industry_event_evidence_summary",
                    "industry_event_source_coverage",
                    "event_subtype_summary",
                    "rule_variant_sweep",
                    "rule_refinement_queue",
                    "evolution_task_plan",
                    "boundary",
                ],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "const": "mingli-famous-case-annual-event-calibration-v1",
                    },
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "fixture_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "case_count": {"type": "integer"},
                    "event_count": {"type": "integer"},
                    "negative_year_count": {"type": "integer"},
                    "false_positive_count": {"type": "integer"},
                    "strict_exact_hit_count": {"type": "integer"},
                    "strict_false_positive_count": {"type": "integer"},
                    "exact_hit_rate": {"type": "number"},
                    "window_hit_rate": {"type": "number"},
                    "exact_precision": {"type": "number"},
                    "false_positive_rate": {"type": "number"},
                    "strict_exact_hit_rate": {"type": "number"},
                    "strict_exact_precision": {"type": "number"},
                    "strict_false_positive_rate": {"type": "number"},
                    "low_coverage_cases": {"type": "array", "items": {"type": "object"}},
                    "birth_source_quality_summary": {"type": "object"},
                    "domain_summary": {"type": "array", "items": {"type": "object"}},
                    "domain_topic_summary": {"type": "array", "items": {"type": "object"}},
                    "domain_topic_refinement_queue": {"type": "array", "items": {"type": "object"}},
                    "domain_topic_variant_sweep": {"type": "array", "items": {"type": "object"}},
                    "topic_summary": {"type": "array", "items": {"type": "object"}},
                    "industry_event_evidence_summary": {"type": "array", "items": {"type": "object"}},
                    "industry_event_source_coverage": {"type": "object"},
                    "event_subtype_summary": {"type": "array", "items": {"type": "object"}},
                    "rule_variant_sweep": {"type": "array", "items": {"type": "object"}},
                    "rule_refinement_queue": {"type": "array", "items": {"type": "object"}},
                    "evolution_task_plan": {"type": "array", "items": {"type": "object"}},
                    "boundary": {"type": "string"},
                },
            },
            "KnownGapItem": {
                "type": "object",
                "required": [
                    "id",
                    "severity",
                    "status",
                    "owner_domain",
                    "blocking_scope",
                    "requirement",
                    "current_state",
                    "needed_to_close",
                    "closure_condition",
                    "verification_commands",
                    "production_gate_ids",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "severity": {"type": "string", "enum": ["major", "medium", "minor"]},
                    "status": {"type": "string", "enum": ["open"]},
                    "owner_domain": {"type": "string"},
                    "blocking_scope": {"type": "string"},
                    "requirement": {"type": "string"},
                    "current_state": {"type": "string"},
                    "needed_to_close": {"type": "string"},
                    "closure_condition": {"type": "string"},
                    "verification_commands": {"type": "array", "items": {"type": "string"}},
                    "production_gate_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ImplementedRequirement": {
                "type": "object",
                "required": ["id", "requirement", "evidence", "status"],
                "properties": {
                    "id": {"type": "string"},
                    "requirement": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string"},
                },
            },
            "GitHubComparisonItem": {
                "type": "object",
                "required": ["dimension", "this_project", "github_baseline", "relative_position", "required_to_lead"],
                "properties": {
                    "dimension": {"type": "string"},
                    "this_project": {"type": "string"},
                    "github_baseline": {"type": "string"},
                    "relative_position": {"type": "string"},
                    "required_to_lead": {"type": "string"},
                },
            },
            "GitHubComparisonReceiptMaterial": {
                "type": "object",
                "required": [
                    "schema_version",
                    "comparison_scope",
                    "last_reviewed",
                    "verdict",
                    "matrix_sha256",
                    "candidate_sha256",
                    "dimension_count",
                    "dimensions",
                    "relative_positions",
                    "candidate_projects",
                    "blocking_provider_capabilities",
                    "production_ready_for_professional_calculation",
                    "request_scoped_production_ready_path",
                    "request_scoped_provenance_required",
                    "local_capability_sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "github-comparison-receipt-v1"},
                    "comparison_scope": {"type": "string"},
                    "last_reviewed": {"type": "string"},
                    "verdict": {"type": "string"},
                    "matrix_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "candidate_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "dimension_count": {"type": "integer"},
                    "dimensions": {"type": "array", "items": {"type": "string"}},
                    "relative_positions": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    "candidate_projects": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ExternalIntegrationCandidate"},
                    },
                    "blocking_provider_capabilities": {"type": "array", "items": {"type": "string"}},
                    "production_ready_for_professional_calculation": {"type": "boolean"},
                    "request_scoped_production_ready_path": {"type": "boolean"},
                    "request_scoped_provenance_required": {"type": "boolean"},
                    "local_capability_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "GitHubComparisonReceipt": {
                "type": "object",
                "required": ["schema_version", "sha256", "material"],
                "properties": {
                    "schema_version": {"type": "string", "const": "github-comparison-receipt-v1"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "material": {"$ref": "#/schemas/GitHubComparisonReceiptMaterial"},
                },
            },
            "ExternalIntegrationCandidate": {
                "type": "object",
                "required": ["domain", "name", "url", "fit", "audit_note"],
                "properties": {
                    "domain": {"type": "string"},
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "fit": {"type": "string"},
                    "audit_note": {"type": "string"},
                },
            },
            "KnownGapResolutionPlanItem": {
                "type": "object",
                "required": [
                    "id",
                    "gap_id",
                    "severity",
                    "status",
                    "requirement",
                    "current_state",
                    "needed_to_close",
                    "closure_condition",
                    "verification_commands",
                    "owner_domain",
                    "production_gate_ids",
                    "blocking_scope",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "gap_id": {"type": "string"},
                    "severity": {"type": "string", "enum": ["major", "medium", "minor"]},
                    "status": {"type": "string", "enum": ["open"]},
                    "requirement": {"type": "string"},
                    "current_state": {"type": "string"},
                    "needed_to_close": {"type": "string"},
                    "closure_condition": {"type": "string"},
                    "verification_commands": {"type": "array", "items": {"type": "string"}},
                    "owner_domain": {"type": "string"},
                    "production_gate_ids": {"type": "array", "items": {"type": "string"}},
                    "blocking_scope": {"type": "string"},
                },
            },
            "CapabilityAuditResponse": {
                "type": "object",
                "required": [
                    "status",
                    "is_state_of_the_art",
                    "state_of_art",
                    "request_scoped_provider_contract",
                    "feedback_memory_safety",
                    "outcome_dataset",
                    "classical_source_list_path",
                    "classical_source_refresh",
                    "capabilities",
                    "blocked_capability_coverage",
                    "known_gap_handoff_bundle",
                    "provider_checks",
                    "provider_example_smoke",
                    "provider_onboarding",
                    "provider_protocol_governance",
                    "method_surface",
                    "method_lineage",
                    "famous_case_validation",
                    "famous_case_school_calibration",
                    "famous_case_annual_event_calibration",
                    "industry_event_cross_domain_fixture_import",
                    "audit_receipt",
                    "expected_audit_receipt_sha256",
                    "audit_receipt_matches_expected",
                    "audit_receipt_mismatch_reason",
                    "github_comparison_matrix",
                    "github_comparison_receipt",
                    "plan_compliance",
                    "plan_compliance_receipt",
                    "evidence_materialization",
                    "implemented_requirements",
                    "known_gaps",
                    "known_gap_resolution_plan",
                    "known_gap_resolution_plan_coverage",
                    "external_integration_candidates",
                    "next_highest_value_steps",
                ],
                "properties": {
                    "status": {"type": "string"},
                    "is_state_of_the_art": {"type": "string", "enum": ["partial"]},
                    "state_of_art": {"$ref": "#/schemas/StateOfArtAssessment"},
                    "request_scoped_provider_contract": {"$ref": "#/schemas/RequestScopedProviderContractSummary"},
                    "feedback_memory_safety": {"$ref": "#/schemas/FeedbackMemorySafetyAudit"},
                    "outcome_dataset": {"$ref": "#/schemas/OutcomeDatasetAudit"},
                    "classical_source_list_path": {"type": ["string", "null"]},
                    "classical_source_refresh": {"$ref": "#/schemas/ClassicalSourceListAudit"},
                    "capabilities": {"$ref": "#/schemas/CapabilityFlagMap"},
                    "blocked_capability_coverage": {"$ref": "#/schemas/BlockedCapabilityCoverage"},
                    "known_gap_handoff_bundle": {"$ref": "#/schemas/KnownGapHandoffBundle"},
                    "provider_checks": {"$ref": "#/schemas/ProviderChecksResponse"},
                    "provider_example_smoke": {"$ref": "#/schemas/ProviderExampleSmokeResponse"},
                    "provider_onboarding": {"$ref": "#/schemas/ProviderOnboardingResponse"},
                    "provider_protocol_governance": {"$ref": "#/schemas/ProviderProtocolGovernanceSummary"},
                    "method_surface": {"$ref": "#/schemas/MethodSurfaceReceiptSummary"},
                    "method_lineage": {"$ref": "#/schemas/MethodLineageReceiptSummary"},
                    "famous_case_validation": {"$ref": "#/schemas/FamousCaseValidationReceiptSummary"},
                    "famous_case_school_calibration": {
                        "$ref": "#/schemas/FamousCaseSchoolCalibrationReceiptSummary"
                    },
                    "famous_case_annual_event_calibration": {
                        "$ref": "#/schemas/FamousCaseAnnualEventCalibrationReceiptSummary"
                    },
                    "industry_event_cross_domain_fixture_import": {
                        "$ref": "#/schemas/IndustryEventCrossDomainFixtureImportReceipt"
                    },
                    "audit_receipt": {"$ref": "#/schemas/CapabilityAuditReceipt"},
                    "expected_audit_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "audit_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "audit_receipt_mismatch_reason": {"type": "string"},
                    "github_comparison_matrix": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/GitHubComparisonItem"},
                    },
                    "github_comparison_receipt": {"$ref": "#/schemas/GitHubComparisonReceipt"},
                    "plan_compliance": {"$ref": "#/schemas/PlanCompliance"},
                    "plan_compliance_receipt": {"$ref": "#/schemas/PlanComplianceReceipt"},
                    "evidence_materialization": {"$ref": "#/schemas/EvidenceMaterialization"},
                    "implemented_requirements": {"type": "array", "items": {"$ref": "#/schemas/ImplementedRequirement"}},
                    "known_gaps": {"type": "array", "items": {"$ref": "#/schemas/KnownGapItem"}},
                    "known_gap_resolution_plan": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/KnownGapResolutionPlanItem"},
                    },
                    "known_gap_resolution_plan_coverage": {"$ref": "#/schemas/KnownGapResolutionPlanCoverage"},
                    "external_integration_candidates": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ExternalIntegrationCandidate"},
                    },
                    "next_highest_value_steps": {"type": "array", "items": {"type": "string"}},
                },
            },
            "SpecialistLayer": {
                "type": "object",
                "required": ["level", "focus", "text", "source_ids", "evidence_required", "boundary_type"],
                "properties": {
                    "level": {"type": "string", "enum": ["macro", "micro", "yearly", "monthly", "uncertainty"]},
                    "focus": {"type": "string"},
                    "text": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "evidence_required": {"type": "boolean"},
                    "boundary_type": {"type": "string", "enum": ["symbolic_interpretation", "uncertainty"]},
                },
            },
            "SpecialistSource": {
                "type": "object",
                "required": ["source_id", "title", "tradition", "scope", "caution"],
                "properties": {
                    "source_id": {"type": "string"},
                    "title": {"type": "string"},
                    "tradition": {"type": "string", "enum": ["bazi", "ziwei", "qimen", "astrology"]},
                    "scope": {"type": "string"},
                    "caution": {"type": "string"},
                },
            },
            "SpecialistReport": {
                "type": "object",
                "required": ["agent", "chart", "macro", "micro", "yearly", "monthly", "uncertainty", "layers", "sources"],
                "properties": {
                    "agent": {"type": "string"},
                    "chart": {"type": "object"},
                    "macro": {"type": "string"},
                    "micro": {"type": "string"},
                    "yearly": {"type": "string"},
                    "monthly": {"type": "string"},
                    "uncertainty": {"type": "string"},
                    "layers": {
                        "type": "object",
                        "required": ["macro", "micro", "yearly", "monthly", "uncertainty"],
                        "properties": {
                            "macro": {"$ref": "#/schemas/SpecialistLayer"},
                            "micro": {"$ref": "#/schemas/SpecialistLayer"},
                            "yearly": {"$ref": "#/schemas/SpecialistLayer"},
                            "monthly": {"$ref": "#/schemas/SpecialistLayer"},
                            "uncertainty": {"$ref": "#/schemas/SpecialistLayer"},
                        },
                    },
                    "sources": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/SpecialistSource"},
                    },
                },
            },
            "AnnualTimelineTopic": {
                "type": "object",
                "required": [
                    "message",
                    "category",
                    "intensity",
                    "source",
                    "source_row_index",
                    "source_field",
                    "bazi_evidence_sha256",
                    "provider_quality",
                    "boundary",
                ],
                "properties": {
                    "message": {"type": "string"},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "source": {"type": "string", "const": "annual_luck.rows"},
                    "source_row_index": {"type": "integer"},
                    "source_field": {"type": "string"},
                    "bazi_evidence_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "provider_quality": {"type": "string"},
                    "boundary": {"type": "string"},
                },
            },
            "AnnualTimelineRow": {
                "type": "object",
                "required": [
                    "year",
                    "age",
                    "ganzhi",
                    "phase",
                    "category",
                    "intensity",
                    "element_focus",
                    "bazi_evidence",
                    "topics",
                    "risk_notes",
                    "source",
                    "source_row_index",
                    "boundary",
                ],
                "properties": {
                    "year": {"type": "integer"},
                    "age": {"type": "integer"},
                    "ganzhi": {"type": "string"},
                    "phase": {"type": "string"},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "element_focus": {"type": "string"},
                    "bazi_evidence": {"type": "object"},
                    "topics": {
                        "type": "object",
                        "required": [
                            "finance",
                            "official_career",
                            "career",
                            "study",
                            "relationship",
                            "friends",
                            "leadership",
                            "children_family",
                        ],
                        "properties": {
                            "finance": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "official_career": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "career": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "study": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "relationship": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "friends": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "leadership": {"$ref": "#/schemas/AnnualTimelineTopic"},
                            "children_family": {"$ref": "#/schemas/AnnualTimelineTopic"},
                        },
                    },
                    "risk_notes": {"type": "array", "items": {"type": "string"}},
                    "source": {"type": "string", "const": "annual_luck.rows"},
                    "source_row_index": {"type": "integer"},
                    "boundary": {"type": "string"},
                },
            },
            "AnnualTimelineReceiptRowFingerprint": {
                "type": "object",
                "required": ["year", "source_row_index", "sha256"],
                "properties": {
                    "year": {"type": "integer"},
                    "source_row_index": {"type": "integer"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "AnnualLuckRangeSummary": {
                "type": "object",
                "required": ["start_year", "end_year", "count"],
                "properties": {
                    "start_year": {"type": ["integer", "null"]},
                    "end_year": {"type": ["integer", "null"]},
                    "count": {"type": "integer"},
                },
            },
            "AnnualTimelineReceipt": {
                "type": "object",
                "required": [
                    "schema_version",
                    "annual_luck_range",
                    "annual_luck_rows_sha256",
                    "annual_timeline_sha256",
                    "row_count",
                    "start_year",
                    "end_year",
                    "topic_keys",
                    "category_counts",
                    "intensity_counts",
                    "row_fingerprints",
                    "topic_evidence_complete",
                    "topic_evidence_missing",
                    "validation_boundary",
                    "sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "annual-timeline-receipt-v1"},
                    "annual_luck_range": {"$ref": "#/schemas/AnnualLuckRangeSummary"},
                    "annual_luck_rows_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "annual_timeline_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "row_count": {"type": "integer"},
                    "start_year": {"type": ["integer", "null"]},
                    "end_year": {"type": ["integer", "null"]},
                    "topic_keys": {"type": "array", "items": {"type": "string"}},
                    "category_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "intensity_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "row_fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AnnualTimelineReceiptRowFingerprint"},
                    },
                    "topic_evidence_complete": {"type": "boolean"},
                    "topic_evidence_missing": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["year", "source_row_index", "topic"],
                            "properties": {
                                "year": {"type": ["integer", "null"]},
                                "source_row_index": {"type": ["integer", "null"]},
                                "topic": {"type": "string"},
                            },
                        },
                    },
                    "validation_boundary": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "AnnualLuckRowElements": {
                "type": "object",
                "required": ["stem", "branch", "focus"],
                "properties": {
                    "stem": {"type": "string"},
                    "branch": {"type": "string"},
                    "focus": {"type": "string"},
                },
            },
            "AnnualLuckTenGodPair": {
                "type": "object",
                "required": ["stem", "branch"],
                "properties": {
                    "stem": {"type": "string"},
                    "branch": {"type": "string"},
                },
            },
            "AnnualLuckActiveMajorLuck": {
                "type": "object",
                "properties": {
                    "index": {"type": ["integer", "null"]},
                    "ganzhi": {"type": ["string", "null"]},
                    "start_age": {"type": ["integer", "null"]},
                    "end_age": {"type": ["integer", "null"]},
                    "start_year": {"type": ["integer", "null"]},
                    "end_year": {"type": ["integer", "null"]},
                },
            },
            "AnnualLuckNatalPillarMatch": {
                "type": "object",
                "required": ["pillar", "relation", "note"],
                "properties": {
                    "pillar": {"type": "string"},
                    "relation": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
            "AnnualLuckBaziEvidence": {
                "type": "object",
                "required": [
                    "annual_pillar",
                    "annual_ten_gods",
                    "active_major_luck",
                    "useful_state",
                    "natal_pillar_matches",
                    "interpretation_basis",
                ],
                "properties": {
                    "annual_pillar": {"type": "string"},
                    "annual_ten_gods": {"$ref": "#/schemas/AnnualLuckTenGodPair"},
                    "active_major_luck": {"$ref": "#/schemas/AnnualLuckActiveMajorLuck"},
                    "useful_state": {"type": "string"},
                    "natal_pillar_matches": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AnnualLuckNatalPillarMatch"},
                    },
                    "interpretation_basis": {"type": "array", "items": {"type": "string"}},
                },
            },
            "AnnualEventMarkers": {
                "type": "object",
                "required": [
                    "career_launch",
                    "role_power",
                    "role_transition",
                    "business_power",
                    "relationship",
                    "movement",
                    "study_exam",
                    "public_visibility",
                    "health_pressure",
                    "adult_career_stage",
                    "basis",
                ],
                "properties": {
                    "career_launch": {"type": "boolean"},
                    "role_power": {"type": "boolean"},
                    "role_transition": {"type": "boolean"},
                    "business_power": {"type": "boolean"},
                    "relationship": {"type": "boolean"},
                    "movement": {"type": "boolean"},
                    "study_exam": {"type": "boolean"},
                    "public_visibility": {"type": "boolean"},
                    "health_pressure": {"type": "boolean"},
                    "adult_career_stage": {"type": "boolean"},
                    "basis": {"type": "array", "items": {"type": "string"}},
                },
            },
            "AnnualLuckRow": {
                "type": "object",
                "required": [
                    "year",
                    "age",
                    "ganzhi",
                    "phase",
                    "elements",
                    "bazi_evidence",
                    "event_markers",
                    "category",
                    "intensity",
                    "finance",
                    "official_career",
                    "career",
                    "study",
                    "relationship",
                    "friends",
                    "leadership",
                    "children_family",
                    "theme",
                    "risk_notes",
                ],
                "properties": {
                    "year": {"type": "integer"},
                    "age": {"type": "integer"},
                    "ganzhi": {"type": "string"},
                    "phase": {"type": "string"},
                    "elements": {"$ref": "#/schemas/AnnualLuckRowElements"},
                    "bazi_evidence": {"$ref": "#/schemas/AnnualLuckBaziEvidence"},
                    "event_markers": {"$ref": "#/schemas/AnnualEventMarkers"},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "finance": {"type": "string"},
                    "official_career": {"type": "string"},
                    "career": {"type": "string"},
                    "study": {"type": "string"},
                    "relationship": {"type": "string"},
                    "friends": {"type": "string"},
                    "leadership": {"type": "string"},
                    "children_family": {"type": "string"},
                    "theme": {"type": "string"},
                    "risk_notes": {"type": "array", "items": {"type": "string"}},
                },
            },
            "MonthlyLuckReceiptRowFingerprint": {
                "type": "object",
                "required": ["year", "month", "source_row_index", "sha256"],
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "source_row_index": {"type": "integer"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "MonthlyLuckRangeSummary": {
                "type": "object",
                "required": ["years", "months_per_year", "count"],
                "properties": {
                    "years": {"type": "array", "items": {"type": "integer"}},
                    "months_per_year": {"type": "integer"},
                    "count": {"type": "integer"},
                },
            },
            "MonthlyLuckBasisSummary": {
                "type": "object",
                "required": ["provider", "provider_quality", "useful_element", "dominant_element"],
                "properties": {
                    "provider": {"type": "string"},
                    "provider_quality": {"type": "string"},
                    "useful_element": {"type": ["string", "null"]},
                    "dominant_element": {"type": ["string", "null"]},
                },
            },
            "MonthlyLuckTopic": {
                "type": "object",
                "required": [
                    "message",
                    "category",
                    "intensity",
                    "source",
                    "source_row_index",
                    "source_field",
                    "bazi_evidence_sha256",
                    "provider_quality",
                    "boundary",
                ],
                "properties": {
                    "message": {"type": "string"},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "source": {"type": "string", "const": "monthly_luck.rows"},
                    "source_row_index": {"type": "integer"},
                    "source_field": {"type": "string"},
                    "bazi_evidence_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "provider_quality": {"type": "string"},
                    "boundary": {"type": "string"},
                },
            },
            "MonthlyLuckBaziEvidence": {
                "type": "object",
                "required": [
                    "monthly_pillar",
                    "monthly_ten_gods",
                    "active_major_luck",
                    "useful_state",
                    "natal_pillar_matches",
                    "month",
                    "interpretation_basis",
                ],
                "properties": {
                    "monthly_pillar": {"type": "string"},
                    "monthly_ten_gods": {"$ref": "#/schemas/AnnualLuckTenGodPair"},
                    "active_major_luck": {"$ref": "#/schemas/AnnualLuckActiveMajorLuck"},
                    "useful_state": {"type": "string"},
                    "natal_pillar_matches": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AnnualLuckNatalPillarMatch"},
                    },
                    "month": {"type": "integer"},
                    "interpretation_basis": {"type": "array", "items": {"type": "string"}},
                },
            },
            "MonthlyLuckRow": {
                "type": "object",
                "required": [
                    "year",
                    "month",
                    "month_name",
                    "ganzhi",
                    "elements",
                    "bazi_evidence",
                    "category",
                    "intensity",
                    "finance",
                    "official_career",
                    "career",
                    "study",
                    "relationship",
                    "friends",
                    "leadership",
                    "children_family",
                    "topics",
                    "theme",
                    "risk_notes",
                ],
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "month_name": {"type": "string"},
                    "ganzhi": {"type": "string"},
                    "elements": {"$ref": "#/schemas/AnnualLuckRowElements"},
                    "bazi_evidence": {"$ref": "#/schemas/MonthlyLuckBaziEvidence"},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "finance": {"type": "string"},
                    "official_career": {"type": "string"},
                    "career": {"type": "string"},
                    "study": {"type": "string"},
                    "relationship": {"type": "string"},
                    "friends": {"type": "string"},
                    "leadership": {"type": "string"},
                    "children_family": {"type": "string"},
                    "topics": {
                        "type": "object",
                        "required": [
                            "finance",
                            "official_career",
                            "career",
                            "study",
                            "relationship",
                            "friends",
                            "leadership",
                            "children_family",
                        ],
                        "properties": {
                            "finance": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "official_career": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "career": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "study": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "relationship": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "friends": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "leadership": {"$ref": "#/schemas/MonthlyLuckTopic"},
                            "children_family": {"$ref": "#/schemas/MonthlyLuckTopic"},
                        },
                    },
                    "theme": {"type": "string"},
                    "risk_notes": {"type": "array", "items": {"type": "string"}},
                },
            },
            "MonthlyLuck": {
                "type": "object",
                "required": ["range", "basis", "rows", "caution"],
                "properties": {
                    "range": {"$ref": "#/schemas/MonthlyLuckRangeSummary"},
                    "basis": {"$ref": "#/schemas/MonthlyLuckBasisSummary"},
                    "rows": {"type": "array", "items": {"$ref": "#/schemas/MonthlyLuckRow"}},
                    "caution": {"type": "string"},
                },
            },
            "MonthlyLuckReceipt": {
                "type": "object",
                "required": [
                    "schema_version",
                    "monthly_luck_range",
                    "monthly_luck_basis",
                    "monthly_luck_rows_sha256",
                    "row_count",
                    "years",
                    "months_by_year",
                    "category_counts",
                    "intensity_counts",
                    "row_fingerprints",
                    "topic_evidence_complete",
                    "topic_evidence_missing",
                    "validation_boundary",
                    "sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "monthly-luck-receipt-v1"},
                    "monthly_luck_range": {"$ref": "#/schemas/MonthlyLuckRangeSummary"},
                    "monthly_luck_basis": {"$ref": "#/schemas/MonthlyLuckBasisSummary"},
                    "monthly_luck_rows_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "row_count": {"type": "integer"},
                    "years": {"type": "array", "items": {"type": "integer"}},
                    "months_by_year": {
                        "type": "object",
                        "additionalProperties": {"type": "array", "items": {"type": "integer"}},
                    },
                    "category_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "intensity_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "row_fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/MonthlyLuckReceiptRowFingerprint"},
                    },
                    "topic_evidence_complete": {"type": "boolean"},
                    "topic_evidence_missing": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["year", "month", "source_row_index", "topic"],
                            "properties": {
                                "year": {"type": ["integer", "null"]},
                                "month": {"type": ["integer", "null"]},
                                "source_row_index": {"type": ["integer", "null"]},
                                "topic": {"type": "string"},
                            },
                        },
                    },
                    "validation_boundary": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "AuspiciousCalendarReceiptRowFingerprint": {
                "type": "object",
                "required": ["date", "source_row_index", "sha256"],
                "properties": {
                    "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "source_row_index": {"type": "integer"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "AuspiciousCalendarReceipt": {
                "type": "object",
                "required": [
                    "schema_version",
                    "calendar_range",
                    "calendar_basis",
                    "calendar_rows_sha256",
                    "method_layers_sha256",
                    "row_count",
                    "start_date",
                    "end_date",
                    "rating_counts",
                    "officer_counts",
                    "mansion_counts",
                    "row_fingerprints",
                    "provider_request_receipt_sha256",
                    "external_payload_receipt_sha256",
                    "validation_boundary",
                    "sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "auspicious-calendar-receipt-v1"},
                    "calendar_range": {"$ref": "#/schemas/AuspiciousCalendarRange"},
                    "calendar_basis": {"$ref": "#/schemas/AuspiciousCalendarBasis"},
                    "calendar_rows_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "method_layers_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "row_count": {"type": "integer"},
                    "start_date": {"type": ["string", "null"], "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "end_date": {"type": ["string", "null"], "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "rating_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "officer_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "mansion_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "row_fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AuspiciousCalendarReceiptRowFingerprint"},
                    },
                    "provider_request_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "external_payload_receipt_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "validation_boundary": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "AnnualPhaseTopicHighlight": {
                "type": "object",
                "required": ["dominant_message", "supporting_year_count", "source_years"],
                "properties": {
                    "dominant_message": {"type": "string"},
                    "supporting_year_count": {"type": "integer"},
                    "source_years": {"type": "array", "items": {"type": "integer"}},
                },
            },
            "AnnualPhaseSummary": {
                "type": "object",
                "required": [
                    "phase",
                    "start_year",
                    "end_year",
                    "start_age",
                    "end_age",
                    "year_count",
                    "dominant_category",
                    "category_counts",
                    "intensity_counts",
                    "high_volatility_years",
                    "constructive_years",
                    "topic_highlights",
                    "source",
                    "source_row_indexes",
                    "boundary",
                ],
                "properties": {
                    "phase": {"type": "string"},
                    "start_year": {"type": "integer"},
                    "end_year": {"type": "integer"},
                    "start_age": {"type": "integer"},
                    "end_age": {"type": "integer"},
                    "year_count": {"type": "integer"},
                    "dominant_category": {"type": "string"},
                    "category_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "intensity_counts": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "high_volatility_years": {"type": "array", "items": {"type": "integer"}},
                    "constructive_years": {"type": "array", "items": {"type": "integer"}},
                    "topic_highlights": {
                        "type": "object",
                        "required": [
                            "finance",
                            "official_career",
                            "career",
                            "study",
                            "relationship",
                            "friends",
                            "leadership",
                            "children_family",
                        ],
                        "properties": {
                            "finance": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "official_career": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "career": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "study": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "relationship": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "friends": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "leadership": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                            "children_family": {"$ref": "#/schemas/AnnualPhaseTopicHighlight"},
                        },
                    },
                    "source": {"type": "string", "const": "annual_luck.rows"},
                    "source_row_indexes": {"type": "array", "items": {"type": "integer"}},
                    "boundary": {"type": "string"},
                },
            },
            "AnnualLuck": {
                "type": "object",
                "required": ["range", "basis", "rows", "phase_summary", "caution"],
                "properties": {
                    "range": {
                        "type": "object",
                        "required": ["start_year", "end_year", "count"],
                        "properties": {
                            "start_year": {"type": "integer"},
                            "end_year": {"type": "integer"},
                            "count": {"type": "integer"},
                        },
                    },
                    "basis": {"type": "object"},
                    "rows": {"type": "array", "items": {"$ref": "#/schemas/AnnualLuckRow"}},
                    "phase_summary": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AnnualPhaseSummary"},
                    },
                    "caution": {"type": "string"},
                },
            },
            "VoteChallenge": {
                "type": "object",
                "required": ["agent", "reason", "preserved_as"],
                "properties": {
                    "agent": {"type": "string"},
                    "reason": {"type": "string"},
                    "preserved_as": {"type": "string", "const": "boundary_condition"},
                },
            },
            "VoteClaim": {
                "type": "object",
                "required": [
                    "id",
                    "topic",
                    "claim",
                    "supporters",
                    "challenges",
                    "primary_support_ratio",
                    "support_ratio",
                    "threshold",
                    "passed",
                    "source_ids",
                    "decision",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "topic": {"type": "string"},
                    "claim": {"type": "string"},
                    "supporters": {"type": "array", "items": {"type": "string"}},
                    "challenges": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/VoteChallenge"},
                    },
                    "primary_support_ratio": {"type": "number"},
                    "support_ratio": {"type": "number"},
                    "threshold": {"type": "number"},
                    "passed": {"type": "boolean"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "decision": {"type": "string", "enum": ["include_with_boundary", "hold_for_source_review"]},
                },
            },
            "VoteAudit": {
                "type": "object",
                "required": [
                    "claim_count",
                    "passed_claim_count",
                    "claim_pass_rate",
                    "threshold",
                    "evidence_bound",
                    "minority_positions_preserved",
                ],
                "properties": {
                    "claim_count": {"type": "integer"},
                    "passed_claim_count": {"type": "integer"},
                    "claim_pass_rate": {"type": "number"},
                    "threshold": {"type": "number"},
                    "evidence_bound": {"type": "boolean"},
                    "minority_positions_preserved": {"type": "boolean"},
                },
            },
            "VoteRecord": {
                "type": "object",
                "required": ["_summary", "_claims", "_audit"],
                "properties": {
                    "_summary": {
                        "type": "object",
                        "required": ["support_ratio", "threshold", "passed"],
                        "properties": {
                            "support_ratio": {"type": "number"},
                            "threshold": {"type": "number"},
                            "passed": {"type": "boolean"},
                        },
                    },
                    "_claims": {"type": "array", "items": {"$ref": "#/schemas/VoteClaim"}},
                    "_audit": {"$ref": "#/schemas/VoteAudit"},
                    "bazi": {"type": "object"},
                    "ziwei": {"type": "object"},
                    "qimen": {"type": "object"},
                    "astrology": {"type": "object"},
                },
            },
            "DeliberationReceipt": {
                "type": "object",
                "required": [
                    "schema_version",
                    "discussion_sha256",
                    "votes_sha256",
                    "source_review_sha256",
                    "conflicts_sha256",
                    "workflow_sha256",
                    "discussion_count",
                    "claim_count",
                    "passed_claim_count",
                    "source_review_status",
                    "conflict_count",
                    "minority_positions_preserved",
                    "sha256",
                ],
                "properties": {
                    "schema_version": {"type": "string", "const": "deliberation-receipt-v1"},
                    "discussion_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "votes_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "source_review_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "conflicts_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "workflow_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "discussion_count": {"type": "integer"},
                    "claim_count": {"type": "integer"},
                    "passed_claim_count": {"type": "integer"},
                    "source_review_status": {"type": "string"},
                    "conflict_count": {"type": "integer"},
                    "minority_positions_preserved": {"type": "boolean"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "SourceEvidenceProvenance": {
                "type": "object",
                "required": ["corpus", "source_type", "citation_policy"],
                "properties": {
                    "corpus": {"type": "string"},
                    "source_type": {"type": "string"},
                    "citation_policy": {"type": "string"},
                },
                "additionalProperties": {"type": "string"},
            },
            "SourceEvidenceSnippet": {
                "type": "object",
                "required": [
                    "source_id",
                    "snippet_id",
                    "keywords",
                    "note",
                    "caution",
                    "provenance",
                    "title",
                    "tradition",
                    "excerpt_type",
                ],
                "properties": {
                    "source_id": {"type": "string"},
                    "snippet_id": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "note": {"type": "string"},
                    "caution": {"type": "string"},
                    "provenance": {"$ref": "#/schemas/SourceEvidenceProvenance"},
                    "title": {"type": "string"},
                    "tradition": {"type": "string"},
                    "excerpt_type": {"type": "string"},
                },
            },
            "EvidenceSummaryItem": {
                "type": "object",
                "required": ["source_id", "snippet_id", "note", "caution"],
                "properties": {
                    "source_id": {"type": "string"},
                    "snippet_id": {"type": "string"},
                    "note": {"type": "string"},
                    "caution": {"type": "string"},
                },
            },
            "SourceReviewReport": {
                "type": "object",
                "required": [
                    "covered_sources",
                    "covered_traditions",
                    "unknown_sources",
                    "missing_traditions",
                    "evidence",
                    "evidence_index",
                    "missing_evidence",
                    "strictness",
                    "min_sources",
                    "status",
                ],
                "properties": {
                    "covered_sources": {"type": "array", "items": {"type": "string"}},
                    "covered_traditions": {"type": "array", "items": {"type": "string"}},
                    "unknown_sources": {"type": "array", "items": {"type": "string"}},
                    "missing_traditions": {"type": "array", "items": {"type": "string"}},
                    "evidence": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"$ref": "#/schemas/SourceEvidenceSnippet"},
                        },
                    },
                    "evidence_index": {"type": "object", "additionalProperties": True},
                    "missing_evidence": {"type": "array", "items": {"type": "string"}},
                    "strictness": {"type": "string"},
                    "min_sources": {"type": "integer"},
                    "status": {"type": "string", "enum": ["pass", "needs_more_sources"]},
                },
            },
            "TopicSynthesisConfidence": {
                "type": "object",
                "required": [
                    "level",
                    "evidence_count",
                    "cross_agent_count",
                    "production_provider_count",
                    "fallback_provider_count",
                    "blocked_provider_count",
                    "production_domains",
                    "fallback_domains",
                    "blocked_domains",
                    "downgrade_reasons",
                    "boundary",
                ],
                "properties": {
                    "level": {"type": "string", "enum": ["high", "medium", "low"]},
                    "evidence_count": {"type": "integer"},
                    "cross_agent_count": {"type": "integer"},
                    "production_provider_count": {"type": "integer"},
                    "fallback_provider_count": {"type": "integer"},
                    "blocked_provider_count": {"type": "integer"},
                    "production_domains": {"type": "array", "items": {"type": "string"}},
                    "fallback_domains": {"type": "array", "items": {"type": "string"}},
                    "blocked_domains": {"type": "array", "items": {"type": "string"}},
                    "downgrade_reasons": {"type": "array", "items": {"type": "string"}},
                    "boundary": {"type": "string"},
                },
            },
            "TopicSynthesisCrossAgentEvidence": {
                "type": "object",
                "required": ["agent", "signal", "support"],
                "properties": {
                    "agent": {"type": "string", "enum": ["bazi", "ziwei", "qimen", "astrology"]},
                    "signal": {"type": "string"},
                    "support": {},
                },
            },
            "TopicSynthesisAnnualFocus": {
                "type": "object",
                "required": [
                    "year",
                    "category",
                    "intensity",
                    "message",
                    "bazi_evidence",
                    "risk_notes",
                ],
                "properties": {
                    "year": {"type": "integer"},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "message": {"type": "string"},
                    "bazi_evidence": {"$ref": "#/schemas/AnnualLuckBaziEvidence"},
                    "risk_notes": {"type": "array", "items": {"type": "string"}},
                },
            },
            "TopicSynthesisMonthlyFocus": {
                "type": "object",
                "required": [
                    "year",
                    "month",
                    "category",
                    "intensity",
                    "message",
                    "bazi_evidence",
                ],
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer", "minimum": 1, "maximum": 12},
                    "category": {"type": "string"},
                    "intensity": {"type": "string"},
                    "message": {"type": "string"},
                    "bazi_evidence": {"$ref": "#/schemas/MonthlyLuckBaziEvidence"},
                },
            },
            "TopicSynthesisTimingSignal": {
                "type": "object",
                "required": [
                    "level",
                    "pillar",
                    "ten_gods",
                    "active_major_luck",
                    "useful_state",
                    "natal_match_count",
                ],
                "properties": {
                    "level": {"type": "string", "enum": ["annual", "monthly"]},
                    "pillar": {"type": "string"},
                    "ten_gods": {"$ref": "#/schemas/AnnualLuckTenGodPair"},
                    "active_major_luck": {"type": ["string", "null"]},
                    "useful_state": {"type": "string"},
                    "natal_match_count": {"type": "integer"},
                },
            },
            "TopicSynthesisTimingEvidence": {
                "type": "object",
                "required": ["annual", "monthly"],
                "properties": {
                    "annual": {"$ref": "#/schemas/TopicSynthesisTimingSignal"},
                    "monthly": {"$ref": "#/schemas/TopicSynthesisTimingSignal"},
                },
            },
            "TopicSynthesisItem": {
                "type": "object",
                "required": [
                    "label",
                    "headline",
                    "annual_focus",
                    "monthly_focus",
                    "timing_evidence",
                    "cross_agent_evidence",
                    "synthesis_confidence",
                    "evidence_summary",
                    "risk_boundary",
                ],
                "properties": {
                    "label": {"type": "string"},
                    "headline": {"type": "string"},
                    "annual_focus": {"$ref": "#/schemas/TopicSynthesisAnnualFocus"},
                    "monthly_focus": {"$ref": "#/schemas/TopicSynthesisMonthlyFocus"},
                    "timing_evidence": {"$ref": "#/schemas/TopicSynthesisTimingEvidence"},
                    "cross_agent_evidence": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/TopicSynthesisCrossAgentEvidence"},
                    },
                    "synthesis_confidence": {"$ref": "#/schemas/TopicSynthesisConfidence"},
                    "evidence_summary": {"type": "array", "items": {"type": "string"}},
                    "risk_boundary": {"type": "string"},
                },
            },
            "RenderedReports": {
                "type": "object",
                "required": ["en", "zh"],
                "properties": {
                    "en": {"type": "string"},
                    "zh": {"type": "string"},
                },
                "additionalProperties": {"type": "string"},
            },
            "LLMSynthesisReport": {
                "type": "object",
                "required": ["enabled", "generated", "language", "prompt_fingerprint", "text"],
                "properties": {
                    "enabled": {"type": "boolean"},
                    "generated": {"type": "boolean"},
                    "language": {"type": "string"},
                    "provider": {"type": ["string", "null"]},
                    "prompt_fingerprint": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
            "WorkflowReport": {
                "type": "object",
                "required": [
                    "discussion_rounds",
                    "cross_check_enabled",
                    "reconciliation_enabled",
                    "source_review_strictness",
                    "vote_threshold",
                    "preserve_conflicts",
                ],
                "properties": {
                    "discussion_rounds": {"type": "integer"},
                    "cross_check_enabled": {"type": "boolean"},
                    "reconciliation_enabled": {"type": "boolean"},
                    "source_review_strictness": {"type": "string"},
                    "vote_threshold": {"type": "number"},
                    "preserve_conflicts": {"type": "boolean"},
                },
            },
            "AuspiciousCalendarRange": {
                "type": "object",
                "required": ["start_date", "end_date", "count"],
                "properties": {
                    "start_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "end_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "count": {"type": "integer"},
                },
            },
            "AuspiciousCalendarBasis": {
                "type": "object",
                "required": ["provider", "provider_quality", "rule_set", "replacement_boundary"],
                "properties": {
                    "provider": {"type": "string"},
                    "provider_quality": {"type": "string"},
                    "rule_set": {"type": "string"},
                    "replacement_boundary": {"type": "string"},
                    "external_payload_receipt": {"type": "object"},
                },
            },
            "AuspiciousRecommendedHour": {
                "type": "object",
                "required": ["start", "end", "branch", "element"],
                "properties": {
                    "branch": {"type": "string"},
                    "element": {"type": "string"},
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "label": {"type": "string"},
                    "hour": {"type": "string"},
                    "rating": {"type": "string"},
                },
            },
            "AuspiciousDayRow": {
                "type": "object",
                "required": [
                    "date",
                    "weekday",
                    "ganzhi",
                    "solar_term",
                    "twelve_officer",
                    "twenty_eight_mansion",
                    "huangdao",
                    "rating",
                    "suitable",
                    "avoid",
                    "recommended_hours",
                    "risk_notes",
                ],
                "properties": {
                    "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "weekday": {"type": "string"},
                    "ganzhi": {"type": "string"},
                    "solar_term": {"type": "string"},
                    "twelve_officer": {"type": "string"},
                    "twenty_eight_mansion": {"type": "string"},
                    "huangdao": {"type": "boolean"},
                    "rating": {"type": "string", "enum": ["favorable", "mixed", "cautious"]},
                    "suitable": {"type": "array", "items": {"type": "string"}},
                    "avoid": {"type": "array", "items": {"type": "string"}},
                    "recommended_hours": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AuspiciousRecommendedHour"},
                    },
                    "risk_notes": {"type": "array", "items": {"type": "string"}},
                },
            },
            "AuspiciousMethodMatrixItem": {
                "type": "object",
                "required": ["method", "status", "evidence_fields", "summary"],
                "properties": {
                    "method": {"type": "string"},
                    "status": {"type": "string"},
                    "evidence_fields": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                },
            },
            "AuspiciousCalendar": {
                "type": "object",
                "required": [
                    "range",
                    "basis",
                    "rows",
                    "summary",
                    "twelve_officer_analysis",
                    "mansion_analysis",
                    "huangdao_analysis",
                    "hour_selection_analysis",
                    "risk_boundary_analysis",
                    "provider_quality_analysis",
                    "method_matrix",
                    "caution",
                ],
                "properties": {
                    "range": {"$ref": "#/schemas/AuspiciousCalendarRange"},
                    "basis": {"$ref": "#/schemas/AuspiciousCalendarBasis"},
                    "rows": {"type": "array", "items": {"$ref": "#/schemas/AuspiciousDayRow"}},
                    "summary": {
                        "type": "object",
                        "required": ["favorable_dates", "cautious_dates", "best_date"],
                        "properties": {
                            "favorable_dates": {"type": "array", "items": {"type": "string"}},
                            "cautious_dates": {"type": "array", "items": {"type": "string"}},
                            "best_date": {"type": ["string", "null"]},
                        },
                    },
                    "twelve_officer_analysis": {"type": "object"},
                    "mansion_analysis": {"type": "object"},
                    "huangdao_analysis": {"type": "object"},
                    "hour_selection_analysis": {"type": "object"},
                    "risk_boundary_analysis": {"type": "object"},
                    "provider_quality_analysis": {"type": "object"},
                    "method_matrix": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/AuspiciousMethodMatrixItem"},
                    },
                    "caution": {"type": "string"},
                },
            },
            "AstrologyPlanet": {
                "type": "object",
                "required": ["name", "sign", "degree", "absolute_degree", "house", "theme"],
                "properties": {
                    "name": {"type": "string"},
                    "sign": {"type": "string"},
                    "degree": {"type": "number"},
                    "absolute_degree": {"type": "number"},
                    "house": {"type": "integer"},
                    "theme": {"type": "string"},
                },
            },
            "AstrologyHouse": {
                "type": "object",
                "required": ["number", "cusp_sign", "ruler", "theme", "emphasis", "cusp_degree"],
                "properties": {
                    "number": {"type": "integer"},
                    "cusp_sign": {"type": "string"},
                    "ruler": {"type": "string"},
                    "theme": {"type": "string"},
                    "emphasis": {"type": "string"},
                    "cusp_degree": {"type": "number"},
                },
            },
            "AstrologyAspect": {
                "type": "object",
                "required": ["planet_a", "planet_b", "aspect", "orb", "theme"],
                "properties": {
                    "planet_a": {"type": "string"},
                    "planet_b": {"type": "string"},
                    "aspect": {"type": "string"},
                    "orb": {"type": "number"},
                    "theme": {"type": "string"},
                },
            },
            "AstrologyAnnualTransit": {
                "type": "object",
                "required": [
                    "year",
                    "age",
                    "transit_planet",
                    "target_natal_planet",
                    "activated_house",
                    "house_theme",
                    "focus",
                ],
                "properties": {
                    "year": {"type": "integer"},
                    "age": {"type": "integer"},
                    "transit_planet": {"type": "string"},
                    "target_natal_planet": {"type": "string"},
                    "activated_house": {"type": "integer"},
                    "house_theme": {"type": "string"},
                    "focus": {"type": "string"},
                    "focus_house": {"type": "integer"},
                    "activation": {"type": "string"},
                    "boundary": {"type": "string"},
                },
            },
            "AstrologyEphemerisQuality": {
                "type": "object",
                "required": ["provider_quality", "ephemeris_backed", "precision_level", "boundary"],
                "properties": {
                    "provider_quality": {"type": "string"},
                    "ephemeris_backed": {"type": "boolean"},
                    "precision_level": {"type": "string"},
                    "boundary": {"type": "string"},
                },
            },
            "AstrologyMethodMatrixItem": {
                "type": "object",
                "required": ["method", "status", "evidence_fields", "summary"],
                "properties": {
                    "method": {"type": "string"},
                    "status": {"type": "string"},
                    "evidence_fields": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                },
            },
            "ZiweiPalaceSummary": {
                "type": "object",
                "required": ["index", "name", "theme", "primary_stars", "auxiliary_stars", "markers", "strength"],
                "properties": {
                    "index": {"type": "integer"},
                    "name": {"type": "string"},
                    "theme": {"type": "string"},
                    "primary_stars": {"type": "array", "items": {"type": "string"}},
                    "auxiliary_stars": {"type": "array", "items": {"type": "string"}},
                    "markers": {"type": "array", "items": {"type": "string"}},
                    "strength": {"type": "string"},
                },
            },
            "ZiweiMajorLimit": {
                "type": "object",
                "required": ["index", "palace", "start_age", "end_age", "start_year", "end_year"],
                "properties": {
                    "index": {"type": "integer"},
                    "palace": {"type": "string"},
                    "start_age": {"type": "integer"},
                    "end_age": {"type": "integer"},
                    "start_year": {"type": "integer"},
                    "end_year": {"type": "integer"},
                },
            },
            "ZiweiAnnualActivation": {
                "type": "object",
                "required": ["year", "age", "palace", "theme"],
                "properties": {
                    "year": {"type": "integer"},
                    "age": {"type": "integer"},
                    "palace": {"type": "string"},
                    "theme": {"type": "string"},
                    "activation": {"type": "string"},
                },
            },
            "ZiweiProfile": {
                "type": "object",
                "required": [
                    "provider",
                    "provider_quality",
                    "ming_palace",
                    "body_palace",
                    "major_stars",
                    "highlighted_palaces",
                    "four_transformations",
                    "life_focus",
                    "triad_analysis",
                    "transformation_analysis",
                    "limit_activation_analysis",
                    "method_matrix",
                    "major_limits",
                    "annual_activation",
                    "caution",
                ],
                "properties": {
                    "provider": {"type": ["string", "null"]},
                    "provider_quality": {"type": ["string", "null"]},
                    "ming_palace": {"type": ["string", "null"]},
                    "body_palace": {"type": ["string", "null"]},
                    "major_stars": {"type": "array", "items": {"type": "string"}},
                    "highlighted_palaces": {"type": "array", "items": {"$ref": "#/schemas/ZiweiPalaceSummary"}},
                    "four_transformations": {"type": "object"},
                    "life_focus": {"type": "object"},
                    "triad_analysis": {"type": "object"},
                    "transformation_analysis": {"type": "object"},
                    "limit_activation_analysis": {"type": "object"},
                    "method_matrix": {"type": "array", "items": {"$ref": "#/schemas/AstrologyMethodMatrixItem"}},
                    "major_limits": {"type": "array", "items": {"$ref": "#/schemas/ZiweiMajorLimit"}},
                    "annual_activation": {"type": "array", "items": {"$ref": "#/schemas/ZiweiAnnualActivation"}},
                    "caution": {"type": ["string", "null"]},
                },
            },
            "QimenDuty": {
                "type": "object",
                "required": ["door", "door_palace", "star", "star_palace", "spirit"],
                "properties": {
                    "door": {"type": "string"},
                    "door_palace": {"type": "string"},
                    "star": {"type": "string"},
                    "star_palace": {"type": "string"},
                    "spirit": {"type": "string"},
                },
            },
            "QimenUsefulGod": {
                "type": "object",
                "required": ["palace", "direction", "door", "star", "spirit", "judgment"],
                "properties": {
                    "palace": {"type": "string"},
                    "direction": {"type": "string"},
                    "door": {"type": "string"},
                    "star": {"type": "string"},
                    "spirit": {"type": "string"},
                    "judgment": {"type": "string"},
                },
            },
            "QimenPalaceSummary": {
                "type": "object",
                "required": [
                    "number",
                    "name",
                    "direction",
                    "element",
                    "door",
                    "star",
                    "spirit",
                    "heaven_stem",
                    "earth_stem",
                    "theme",
                    "judgment",
                ],
                "properties": {
                    "number": {"type": "integer"},
                    "name": {"type": "string"},
                    "direction": {"type": "string"},
                    "element": {"type": "string"},
                    "door": {"type": "string"},
                    "star": {"type": "string"},
                    "spirit": {"type": "string"},
                    "heaven_stem": {"type": "string"},
                    "earth_stem": {"type": "string"},
                    "theme": {"type": "string"},
                    "judgment": {"type": "string"},
                },
            },
            "QimenPatternFlag": {
                "type": "object",
                "required": ["name", "palace", "meaning"],
                "properties": {
                    "name": {"type": "string"},
                    "palace": {"type": "string"},
                    "meaning": {"type": "string"},
                },
            },
            "QimenAnnualTiming": {
                "type": "object",
                "required": ["year", "age", "palace", "door", "judgment"],
                "properties": {
                    "year": {"type": "integer"},
                    "age": {"type": "integer"},
                    "palace": {"type": "string"},
                    "door": {"type": "string"},
                    "star": {"type": "string"},
                    "judgment": {"type": "string"},
                },
            },
            "QimenProfile": {
                "type": "object",
                "required": [
                    "provider",
                    "provider_quality",
                    "yin_yang",
                    "ju_number",
                    "duty",
                    "useful_gods",
                    "highlighted_palaces",
                    "pattern_flags",
                    "door_star_spirit_analysis",
                    "stem_relation_analysis",
                    "useful_god_analysis",
                    "pattern_risk_analysis",
                    "timing_activation_analysis",
                    "method_matrix",
                    "annual_timing",
                    "caution",
                ],
                "properties": {
                    "provider": {"type": ["string", "null"]},
                    "provider_quality": {"type": ["string", "null"]},
                    "yin_yang": {"type": ["string", "null"]},
                    "ju_number": {"type": ["integer", "null"]},
                    "duty": {"$ref": "#/schemas/QimenDuty"},
                    "useful_gods": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/schemas/QimenUsefulGod"},
                    },
                    "highlighted_palaces": {"type": "array", "items": {"$ref": "#/schemas/QimenPalaceSummary"}},
                    "pattern_flags": {"type": "array", "items": {"$ref": "#/schemas/QimenPatternFlag"}},
                    "door_star_spirit_analysis": {"type": "object"},
                    "stem_relation_analysis": {"type": "object"},
                    "useful_god_analysis": {"type": "object"},
                    "pattern_risk_analysis": {"type": "object"},
                    "timing_activation_analysis": {"type": "object"},
                    "method_matrix": {"type": "array", "items": {"$ref": "#/schemas/AstrologyMethodMatrixItem"}},
                    "annual_timing": {"type": "array", "items": {"$ref": "#/schemas/QimenAnnualTiming"}},
                    "caution": {"type": ["string", "null"]},
                },
            },
            "AstrologyProfile": {
                "type": "object",
                "required": [
                    "provider",
                    "provider_quality",
                    "zodiac",
                    "sun",
                    "moon",
                    "ascendant",
                    "planets",
                    "houses",
                    "aspects",
                    "annual_transits",
                    "ephemeris_quality",
                    "core_identity_analysis",
                    "house_emphasis_analysis",
                    "aspect_pattern_analysis",
                    "transit_activation_analysis",
                    "method_matrix",
                    "caution",
                ],
                "properties": {
                    "provider": {"type": ["string", "null"]},
                    "provider_quality": {"type": ["string", "null"]},
                    "zodiac": {"type": ["string", "null"]},
                    "sun": {"type": ["string", "null"]},
                    "moon": {"type": ["string", "null"]},
                    "ascendant": {"type": ["string", "null"]},
                    "planets": {"type": "array", "items": {"$ref": "#/schemas/AstrologyPlanet"}},
                    "houses": {"type": "array", "items": {"$ref": "#/schemas/AstrologyHouse"}},
                    "aspects": {"type": "array", "items": {"$ref": "#/schemas/AstrologyAspect"}},
                    "annual_transits": {"type": "array", "items": {"$ref": "#/schemas/AstrologyAnnualTransit"}},
                    "ephemeris_quality": {"$ref": "#/schemas/AstrologyEphemerisQuality"},
                    "core_identity_analysis": {"type": "object"},
                    "house_emphasis_analysis": {"type": "object"},
                    "aspect_pattern_analysis": {"type": "object"},
                    "transit_activation_analysis": {"type": "object"},
                    "method_matrix": {"type": "array", "items": {"$ref": "#/schemas/AstrologyMethodMatrixItem"}},
                    "caution": {"type": ["string", "null"]},
                },
            },
            "SchemaValidationSummary": {
                "type": "object",
                "required": ["schema_name", "valid", "error_count", "errors"],
                "properties": {
                    "schema_name": {"type": "string"},
                    "valid": {"type": "boolean"},
                    "error_count": {"type": "integer"},
                    "errors": {"type": "array", "items": {"type": "string"}},
                },
            },
            "AnalyzeResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "agent_version",
                    "passed",
                    "score",
                    "metrics",
                    "result",
                    "schema_validation",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "agent_version": {"type": "integer"},
                    "passed": {"type": "boolean"},
                    "score": {"type": "number"},
                    "metrics": {"type": "object", "additionalProperties": {"type": "number"}},
                    "schema_validation": {"$ref": "#/schemas/SchemaValidationSummary"},
                    "result": {
                        "type": "object",
                        "required": ["output", "specialists", "final_report"],
                        "properties": {
                            "output": {"type": "string"},
                            "specialists": {
                                "type": "object",
                                "required": ["bazi", "ziwei", "qimen", "astrology"],
                                "properties": {
                                    "bazi": {"$ref": "#/schemas/SpecialistReport"},
                                    "ziwei": {"$ref": "#/schemas/SpecialistReport"},
                                    "qimen": {"$ref": "#/schemas/SpecialistReport"},
                                    "astrology": {"$ref": "#/schemas/SpecialistReport"},
                                },
                            },
                            "final_report": {
                                "type": "object",
                                "required": [
                                    "title",
                                    "coordinator_version",
                                    "summary",
                                    "conflicts",
                                    "strategy_notes",
                                    "boundaries",
                                    "birth_profile",
                                    "request_provenance",
                                    "provider_summary",
                                    "votes",
                                    "deliberation_receipt",
                                    "source_review",
                                    "evidence_summary",
                                    "bazi_profile",
                                    "ziwei_profile",
                                    "qimen_profile",
                                    "astrology_profile",
                                    "annual_luck",
                                    "annual_timeline",
                                    "annual_timeline_receipt",
                                    "monthly_luck",
                                    "monthly_luck_receipt",
                                    "auspicious_calendar",
                                    "auspicious_calendar_receipt",
                                    "topic_synthesis",
                                    "rendered_reports",
                                    "llm_synthesis",
                                    "workflow",
                                ],
                                "properties": {
                                    "title": {"type": "string"},
                                    "coordinator_version": {"type": "integer"},
                                    "summary": {"type": "array", "items": {"type": "string"}},
                                    "conflicts": {"type": "array", "items": {"type": "string"}},
                                    "strategy_notes": {"type": "array", "items": {"type": "string"}},
                                    "boundaries": {"type": "array", "items": {"type": "string"}},
                                    "birth_profile": {"$ref": "#/schemas/BirthProfile"},
                                    "request_provenance": {"$ref": "#/schemas/RequestProvenance"},
                                    "provider_summary": {"$ref": "#/schemas/ProviderSummary"},
                                    "votes": {"$ref": "#/schemas/VoteRecord"},
                                    "deliberation_receipt": {"$ref": "#/schemas/DeliberationReceipt"},
                                    "source_review": {"$ref": "#/schemas/SourceReviewReport"},
                                    "evidence_summary": {
                                        "type": "array",
                                        "items": {"$ref": "#/schemas/EvidenceSummaryItem"},
                                    },
                                    "bazi_profile": {"$ref": "#/schemas/BaziProfile"},
                                    "ziwei_profile": {"$ref": "#/schemas/ZiweiProfile"},
                                    "qimen_profile": {"$ref": "#/schemas/QimenProfile"},
                                    "astrology_profile": {"$ref": "#/schemas/AstrologyProfile"},
                                    "annual_luck": {"$ref": "#/schemas/AnnualLuck"},
                                    "annual_timeline": {
                                        "type": "array",
                                        "items": {"$ref": "#/schemas/AnnualTimelineRow"},
                                    },
                                    "annual_timeline_receipt": {"$ref": "#/schemas/AnnualTimelineReceipt"},
                                    "monthly_luck": {"$ref": "#/schemas/MonthlyLuck"},
                                    "monthly_luck_receipt": {"$ref": "#/schemas/MonthlyLuckReceipt"},
                                    "auspicious_calendar": {"$ref": "#/schemas/AuspiciousCalendar"},
                                    "auspicious_calendar_receipt": {
                                        "$ref": "#/schemas/AuspiciousCalendarReceipt"
                                    },
                                    "topic_synthesis": {
                                        "type": "object",
                                        "required": [
                                            "finance",
                                            "official_career",
                                            "career",
                                            "study",
                                            "relationship",
                                            "friends",
                                            "leadership",
                                            "children_family",
                                        ],
                                        "properties": {
                                            "finance": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "official_career": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "career": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "study": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "relationship": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "friends": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "leadership": {"$ref": "#/schemas/TopicSynthesisItem"},
                                            "children_family": {"$ref": "#/schemas/TopicSynthesisItem"},
                                        },
                                    },
                                    "rendered_reports": {"$ref": "#/schemas/RenderedReports"},
                                    "llm_synthesis": {"$ref": "#/schemas/LLMSynthesisReport"},
                                    "workflow": {"$ref": "#/schemas/WorkflowReport"},
                                },
                            },
                        },
                    },
                },
            },
            "ReproducibilityStrategyFingerprint": {
                "type": "object",
                "required": ["name", "prompt_sha256"],
                "properties": {
                    "name": {"type": "string"},
                    "prompt_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "ReproducibilityManifest": {
                "type": "object",
                "required": [
                    "schema_version",
                    "run_type",
                    "deterministic",
                    "random_seed",
                    "python_version",
                    "genome_version",
                    "strategy_names",
                    "strategy_fingerprints",
                    "metric_floors",
                    "train_task_count",
                    "train_task_fingerprints",
                    "validation_task_count",
                    "validation_task_fingerprints",
                    "cost_governance",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "run_type": {"type": "string", "enum": ["population_evolution", "benchmark"]},
                    "deterministic": {"type": "boolean"},
                    "random_seed": {"type": ["integer", "null"]},
                    "python_version": {"type": "string"},
                    "genome_version": {"type": ["integer", "null"]},
                    "strategy_names": {"type": "array", "items": {"type": "string"}},
                    "strategy_fingerprints": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ReproducibilityStrategyFingerprint"},
                    },
                    "metric_floors": {"type": "object", "additionalProperties": {"type": "number"}},
                    "train_task_count": {"type": "integer"},
                    "train_task_fingerprints": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^[0-9a-f]{16}$"},
                    },
                    "validation_task_count": {"type": "integer"},
                    "validation_task_fingerprints": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^[0-9a-f]{16}$"},
                    },
                    "cost_governance": {"$ref": "#/schemas/EvolutionCostGovernance"},
                },
            },
            "EvolutionCostGovernance": {
                "type": "object",
                "required": [
                    "schema_version",
                    "candidate_count",
                    "baseline_evaluations",
                    "training_candidate_evaluations",
                    "validation_evaluations",
                    "train_task_count",
                    "validation_task_count",
                    "total_candidate_task_evaluations",
                    "llm_calls_allowed",
                    "llm_call_budget",
                    "remote_provider_calls_allowed",
                    "remote_provider_call_budget",
                    "iteration_frequency_policy",
                    "trigger_policy",
                    "stop_policy",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "candidate_count": {"type": "integer"},
                    "baseline_evaluations": {"type": "integer"},
                    "training_candidate_evaluations": {"type": "integer"},
                    "validation_evaluations": {"type": "integer"},
                    "train_task_count": {"type": "integer"},
                    "validation_task_count": {"type": "integer"},
                    "total_candidate_task_evaluations": {"type": "integer"},
                    "llm_calls_allowed": {"type": "boolean"},
                    "llm_call_budget": {"type": "integer"},
                    "remote_provider_calls_allowed": {"type": "boolean"},
                    "remote_provider_call_budget": {"type": "integer"},
                    "iteration_frequency_policy": {"type": "string"},
                    "trigger_policy": {"type": "string"},
                    "stop_policy": {"type": "string"},
                },
            },
            "BenchmarkExternalPayloadBirthMatchStatus": {
                "type": "object",
                "required": ["domain", "status", "mismatch_fields", "declared_birth_profile_sha256"],
                "properties": {
                    "domain": {"type": "string"},
                    "status": {"type": "string"},
                    "mismatch_fields": {"type": "array", "items": {"type": "string"}},
                    "declared_birth_profile_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
            },
            "BenchmarkCaseReportFeatures": {
                "type": "object",
                "properties": {
                    "birth_profile_present": {"type": "boolean"},
                    "birth_profile_fingerprint": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "birthplace_geocoded": {"type": "boolean"},
                    "birthplace_geocoding_quality": {"type": ["string", "null"]},
                    "request_provenance_present": {"type": "boolean"},
                    "request_provenance_chain_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "deliberation_receipt_present": {"type": "boolean"},
                    "deliberation_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "deliberation_claim_count": {"type": "integer"},
                    "annual_timeline_receipt_present": {"type": "boolean"},
                    "annual_timeline_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "annual_timeline_row_count": {"type": "integer"},
                    "annual_timeline_receipt_bound_to_provenance": {"type": "boolean"},
                    "monthly_luck_receipt_present": {"type": "boolean"},
                    "monthly_luck_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "monthly_luck_row_count": {"type": "integer"},
                    "monthly_luck_receipt_bound_to_provenance": {"type": "boolean"},
                    "auspicious_calendar_receipt_present": {"type": "boolean"},
                    "auspicious_calendar_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "auspicious_calendar_row_count": {"type": "integer"},
                    "auspicious_calendar_receipt_bound_to_provenance": {"type": "boolean"},
                    "auspicious_calendar_count": {"type": "integer"},
                    "chinese_render_duplicate_bullet_ratio": {"type": "number"},
                    "chinese_render_topic_evidence_anchor_ratio": {"type": "number"},
                    "chinese_render_topic_judgment_structure_ratio": {"type": "number"},
                    "chinese_render_ascii_letter_count": {"type": "integer"},
                    "chinese_render_ascii_question_present": {"type": "boolean"},
                    "chinese_render_code_marker_present": {"type": "boolean"},
                    "topic_confidence_summary": {"type": "object"},
                    "topic_confidence_boundaries_ok": {"type": "boolean"},
                    "topic_confidence_missing_topics": {"type": "array", "items": {"type": "string"}},
                    "topic_confidence_levels": {"type": "object"},
                    "provider_summary_status": {"type": "string"},
                    "provider_blocker_count": {"type": "integer"},
                    "provider_action_plan_count": {"type": "integer"},
                    "provider_action_plan_domains": {"type": "array", "items": {"type": "string"}},
                    "provider_action_plan_covers_blockers": {"type": "boolean"},
                    "provider_quality": {"type": ["string", "null"]},
                    "external_payload_receipt_domains": {"type": "array", "items": {"type": "string"}},
                    "external_payload_receipt_count": {"type": "integer"},
                    "external_payload_receipts_complete": {"type": "boolean"},
                    "external_payload_birth_match_statuses": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/BenchmarkExternalPayloadBirthMatchStatus"},
                    },
                    "external_payload_birth_mismatch_count": {"type": "integer"},
                    "external_payload_birth_mismatch_domains": {"type": "array", "items": {"type": "string"}},
                    "external_payload_birth_matches_ok": {"type": "boolean"},
                },
            },
            "BenchmarkCaseResult": {
                "type": "object",
                "required": ["name", "passed", "score", "metrics", "report_features"],
                "properties": {
                    "name": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "score": {"type": "number"},
                    "metrics": {"type": "object", "additionalProperties": {"type": "number"}},
                    "report_features": {"$ref": "#/schemas/BenchmarkCaseReportFeatures"},
                },
            },
            "BenchmarkResult": {
                "type": "object",
                "required": [
                    "genome_version",
                    "passed_rate",
                    "average_score",
                    "mean_metrics",
                    "reference_charts",
                    "empirical_validation",
                    "reproducibility_manifest",
                    "benchmark_receipt",
                    "cases",
                ],
                "properties": {
                    "genome_version": {"type": "integer"},
                    "candidate_name": {"type": ["string", "null"]},
                    "passed_rate": {"type": "number"},
                    "average_score": {"type": "number"},
                    "mean_metrics": {"type": "object", "additionalProperties": {"type": "number"}},
                    "reference_charts": {"type": "object"},
                    "empirical_validation": {"type": "object"},
                    "reproducibility_manifest": {"$ref": "#/schemas/ReproducibilityManifest"},
                    "benchmark_receipt": {"$ref": "#/schemas/ProviderCertificationReceipt"},
                    "cases": {"type": "array", "items": {"$ref": "#/schemas/BenchmarkCaseResult"}},
                },
            },
            "BenchmarkResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "benchmark",
                    "expected_benchmark_receipt_sha256",
                    "benchmark_receipt_matches_expected",
                    "benchmark_receipt_mismatch_reason",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "benchmark": {"type": "object"},
                    "expected_benchmark_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "benchmark_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "benchmark_receipt_mismatch_reason": {"type": "string"},
                },
            },
            "ReleaseManifestResponse": {
                "type": "object",
                "required": [
                    "repo",
                    "status",
                    "release_gate_checks",
                    "release_approval_ready",
                    "release_approval_status",
                    "release_blockers",
                    "live_requested",
                    "manifest_path",
                    "classical_source_list_path",
                    "coordinator_version",
                    "history_integrity",
                    "archive_integrity",
                    "lineage_integrity",
                    "audit_receipt",
                    "github_comparison_receipt",
                    "github_comparison_receipt_sha256",
                    "plan_compliance_receipt",
                    "plan_compliance_receipt_sha256",
                    "provider_onboarding_receipt",
                    "provider_protocols_receipt",
                    "expected_audit_receipt_sha256",
                    "audit_receipt_matches_expected",
                    "benchmark_receipt",
                    "expected_benchmark_receipt_sha256",
                    "benchmark_receipt_matches_expected",
                    "readiness_receipt",
                    "expected_readiness_receipt_sha256",
                    "readiness_receipt_matches_expected",
                    "release_manifest_receipt",
                    "expected_release_manifest_receipt_sha256",
                    "release_manifest_receipt_matches_expected",
                    "release_manifest_receipt_mismatch_reason",
                    "ledger_record_requested",
                    "ledger_recorded",
                    "ledger_record_path",
                    "ledger_record_index",
                    "ledger_record_hash",
                    "ledger_record_blocker",
                    "production_readiness_status",
                    "production_ready",
                    "known_gap_ids",
                    "provider_ledger",
                    "outcome_dataset",
                    "outcome_dataset_receipt",
                    "evolution_trigger_receipt_sha256",
                    "evolution_trigger_receipt",
                    "evolution_trigger_receipt_current",
                ],
                "properties": {
                    "repo": {"type": "string"},
                    "status": {"type": "string", "enum": ["release_manifest_ready", "release_blocked"]},
                    "release_gate_checks": {"$ref": "#/schemas/ReleaseManifestGateChecks"},
                    "release_approval_ready": {"type": "boolean"},
                    "release_approval_status": {"type": "string", "enum": ["release_ready", "release_blocked"]},
                    "release_blockers": {
                        "type": "array",
                        "items": {"$ref": "#/schemas/ProductionBlocker"},
                    },
                    "live_requested": {"type": "boolean"},
                    "manifest_path": {"type": ["string", "null"]},
                    "classical_source_list_path": {"type": ["string", "null"]},
                    "coordinator_version": {"type": "integer"},
                    "candidate_name": {"type": ["string", "null"]},
                    "history_integrity": {"$ref": "#/schemas/VersionHistoryIntegrity"},
                    "archive_integrity": {"$ref": "#/schemas/ArchiveIntegrityReport"},
                    "lineage_integrity": {"$ref": "#/schemas/LineageIntegrityReport"},
                    "audit_receipt": {"$ref": "#/schemas/CapabilityAuditReceipt"},
                    "github_comparison_receipt": {"$ref": "#/schemas/GitHubComparisonReceipt"},
                    "github_comparison_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "plan_compliance_receipt": {"$ref": "#/schemas/PlanComplianceReceipt"},
                    "plan_compliance_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "provider_onboarding_receipt": {"$ref": "#/schemas/ProviderOnboardingReceipt"},
                    "provider_protocols_receipt": {"$ref": "#/schemas/ProviderProtocolsReceipt"},
                    "expected_audit_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "audit_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "benchmark_receipt": {"$ref": "#/schemas/ProviderCertificationReceipt"},
                    "expected_benchmark_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "benchmark_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "readiness_receipt": {"$ref": "#/schemas/ProductionReadinessReceipt"},
                    "expected_readiness_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "readiness_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "release_manifest_receipt": {"$ref": "#/schemas/ReleaseManifestReceipt"},
                    "expected_release_manifest_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "release_manifest_receipt_matches_expected": {"type": ["boolean", "null"]},
                    "release_manifest_receipt_mismatch_reason": {"type": "string"},
                    "ledger_record_requested": {"type": "boolean"},
                    "ledger_recorded": {"type": "boolean"},
                    "ledger_record_path": {"type": "string"},
                    "ledger_record_index": {"type": ["integer", "null"]},
                    "ledger_record_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "ledger_record_blocker": {"type": "string"},
                    "production_readiness_status": {"type": "string"},
                    "production_ready": {"type": "boolean"},
                    "known_gap_ids": {"type": "array", "items": {"type": "string"}},
                    "provider_ledger": {"$ref": "#/schemas/ProviderCertificationLedgerStatus"},
                    "outcome_dataset": {"$ref": "#/schemas/OutcomeDatasetAudit"},
                    "outcome_dataset_receipt": {"$ref": "#/schemas/OutcomeDatasetReceipt"},
                    "evolution_trigger_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "evolution_trigger_receipt": {
                        "anyOf": [
                            {"$ref": "#/schemas/EvolutionTriggerReceipt"},
                            {"type": "null"},
                        ]
                    },
                    "evolution_trigger_receipt_current": {"type": "boolean"},
                },
            },
            "ReleaseManifestLedgerStatus": {
                "type": "object",
                "required": [
                    "path",
                    "exists",
                    "integrity_status",
                    "record_count",
                    "latest_record_index",
                    "latest_record_hash",
                    "latest_release_manifest_receipt_sha256",
                    "failures",
                ],
                "properties": {
                    "path": {"type": "string"},
                    "exists": {"type": "boolean"},
                    "integrity_status": {"type": "string", "enum": ["pass", "fail"]},
                    "record_count": {"type": "integer"},
                    "latest_record_index": {"type": ["integer", "null"]},
                    "latest_record_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    "latest_release_manifest_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ReleaseManifestLedgerResponse": {
                "type": "object",
                "required": ["repo", "ledger"],
                "properties": {
                    "repo": {"type": "string"},
                    "ledger": {"$ref": "#/schemas/ReleaseManifestLedgerStatus"},
                },
            },
            "ReleaseManifestDriftStatus": {
                "type": "object",
                "required": [
                    "status",
                    "passed",
                    "live_requested",
                    "expected_release_manifest_receipt_sha256",
                    "current_release_manifest_receipt_sha256",
                    "matches_expected",
                    "failures",
                ],
                "properties": {
                    "status": {"type": "string", "enum": ["passed", "drift_detected", "not_checked"]},
                    "passed": {"type": "boolean"},
                    "live_requested": {"type": "boolean"},
                    "expected_release_manifest_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "current_release_manifest_receipt_sha256": {
                        "type": ["string", "null"],
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "matches_expected": {"type": "boolean"},
                    "failures": {"type": "array", "items": {"type": "string"}},
                },
            },
            "ReleaseManifestDriftResponse": {
                "type": "object",
                "required": ["repo", "manifest_path", "classical_source_list_path", "ledger", "drift"],
                "properties": {
                    "repo": {"type": "string"},
                    "manifest_path": {"type": ["string", "null"]},
                    "classical_source_list_path": {"type": ["string", "null"]},
                    "ledger": {"$ref": "#/schemas/ReleaseManifestLedgerStatus"},
                    "drift": {"$ref": "#/schemas/ReleaseManifestDriftStatus"},
                },
            },
        },
        "provider_protocols": provider_protocol_document(),
        "endpoints": {
            "GET /health": "service liveness",
            "GET /status": "StatusResponse: repo, provider, latest evolution, archive, and memory status",
            "GET /history": "VersionHistoryResponse: coordinator genome versions, lineage fingerprints, and archive provenance",
            "GET /audit": "CapabilityAuditResponse: capability coverage, state-of-art comparison, plan compliance, source-list audit, and known professional-grade gaps; add ?classical_source_list=path-to-json&expected_audit_receipt_sha256=... to detect capability drift",
            "GET /known-gap-handoff": "KnownGapHandoffExportResponse: portable open-gap closure bundle with owner domains, env vars, candidate projects, commands, gates, and audit receipt binding",
            "GET /providers": "ProviderChecksResponse: optional professional provider readiness checks; add ?profile=production and ?live=1 to require production-domain live smoke checks",
            "GET /provider-examples": "ProviderExampleSmokeResponse: run bundled JSON-CLI protocol examples and emit a non-production receipt",
            "GET /provider-onboarding": "ProviderOnboardingResponse: machine-readable real-provider onboarding gaps, protocol hashes, certification commands, and ledger evidence requirements",
            "GET /certify-provider": "ProviderCertificationResponse: certify one JSON-CLI provider domain; add ?domain=ziwei|qimen|astrology|xuanze&live=1&command=...&provenance=...&expected_receipt_sha256=...&record=1",
            "GET /provider-ledger": "ProviderCertificationLedgerResponse: inspect provider certification ledger hash-chain status and domain coverage",
            "GET /provider-drift": "ProviderCertificationDriftResponse: compare current provider certification receipts with the provider ledger; add ?domain=ziwei|qimen|astrology|xuanze or ?live=0 to narrow or skip live execution",
            "GET /provider-protocols": "ProviderProtocolsResponse: machine-readable JSON-CLI provider contracts for external professional engines; add ?domain=ziwei|qimen|astrology|xuanze to narrow",
            "GET /outcome-dataset": "OutcomeDatasetAuditResponse: audit an optional outcome dataset manifest; add ?manifest=path-to-json",
            "GET /industry-events": "IndustryEventManifestStatusResponse: audit a public famous-case industry-event manifest; add ?manifest=path-to-json",
            "GET /industry-event-labels": "IndustryEventValidationLabelTableResponse: convert an industry-event manifest into annual validation labels; add ?manifest=path-to-json",
            "GET /industry-event-scoring-readiness": "IndustryEventSymbolicScoringReadinessResponse: check which industry-event labels have birth profiles for symbolic annual scoring; add ?manifest=path-to-json",
            "GET /industry-event-symbolic-score": "IndustryEventSymbolicAnnualScoreResponse: score ready industry-event labels against symbolic annual rows; add ?manifest=path-to-json",
            "GET /industry-event-evidence-workplan": "IndustryEventEvidenceWorkplanResponse: convert symbolic score tasks into reviewable candidate-pool collection work; add manifest, candidates, query_plan, and cache_dir",
            "GET /birth-profile-review": "BirthProfileReviewStatusResponse: audit a reviewed-birth-profile collection worklist before celebrity birth profiles are imported; add ?manifest=path-to-json",
            "GET /birth-profile-source-review-workplan": "BirthProfileSourceReviewWorkplanResponse: build a non-mutating human source-review workplan for celebrity birth-profile requests; add ?manifest=path-to-json",
            "GET /birth-profile-source-lookup-plan": "BirthProfileSourceLookupPlanResponse: build a dry-run source lookup plan for celebrity birth-profile review tasks; add ?manifest=path-to-json&cache_dir=dir&domain=film",
            "GET /birth-profile-source-cache-template-preview": "BirthProfileSourceCacheTemplatePreviewResponse: build non-mutating JSON templates for manual celebrity birth-profile source cache files; add ?manifest=path-to-json&cache_dir=dir&domain=film",
            "GET /birth-profile-source-cache-audit": "BirthProfileSourceCacheAuditResponse: audit manually prepared source lookup cache files without importing celebrity birth profiles; add ?manifest=path-to-json&cache_dir=dir&domain=film",
            "GET /birth-profile-reviewed-manifest-draft-preview": "BirthProfileReviewedManifestDraftPreviewResponse: build a non-mutating reviewed-manifest draft preview from accepted source cache evidence; add ?manifest=path-to-json&cache_dir=dir&domain=film",
            "GET /birth-profile-reviewed-manifest-file-preview": "BirthProfileReviewedManifestFilePreviewResponse: build a non-mutating file-write preview for an approved reviewed-manifest draft; add ?manifest=path-to-json&cache_dir=dir&target=path",
            "GET /birth-profile-import-preview": "BirthProfileImportPreviewResponse: build a non-mutating preview for reviewed birth-profile fixture import; add ?manifest=path-to-json",
            "GET /birth-profile-fixture-patch-preview": "BirthProfileFixturePatchPreviewResponse: build a non-mutating fixture patch preview from reviewed birth-profile candidates; add ?manifest=path-to-json",
            "GET /industry-event-queries": "IndustryEventQueryPlanStatusResponse: audit public famous-case industry-event source query templates; add ?query_plan=path-to-json",
            "GET /industry-event-candidates": "IndustryEventCandidateCasesStatusResponse: audit public celebrity candidate cases for future industry-event validation; add ?candidates=path-to-json",
            "GET /industry-event-candidate-fetch-cache": "IndustryEventCandidatePoolFetchCacheResponse: plan or execute fetch/cache steps for selected celebrity candidates; add candidates, query_plan, cache_dir, optional domain, split_role, and live=1",
            "GET /industry-event-candidate-draft-import": "IndustryEventCandidatePoolDraftImportResponse: import cached source responses for selected celebrity candidates into draft manifests; add candidates, query_plan, cache_dir, optional domain and split_role",
            "GET /industry-event-requests": "IndustryEventCollectionRequestBundleResponse: build offline source collection requests from a query plan; add case_id, public_name, person_qid, start_year, end_year, and optional domain",
            "GET /industry-event-fetch-cache": "IndustryEventFetchCacheResponse: plan or execute reviewed source fetches into cache; add case_id, public_name, person_qid, start_year, end_year, cache_dir, and optional live=1",
            "GET /industry-event-draft-manifest": "IndustryEventDraftManifestResponse: build a draft manifest from a cached source response; add response, case_id, public_name, person_qid, start_year, end_year, and domain",
            "GET /classical-sources": "ClassicalSourcesResponse: audit external classical-source refresh configuration; add ?source_list=path-to-json or configure SEMAS_CLASSIC_SOURCE_LIST",
            "GET /classical-refresh": "ClassicalSourcesRefreshResponse: download and ingest allowlisted, hash-pinned classical-source manifests; add ?source_list=path-to-json&cache_dir=path&output_dir=path",
            "GET /production-readiness": "ProductionReadinessResponse: aggregate hard production-readiness gates; add ?manifest=path-to-json&classical_source_list=path-to-json&live=1&expected_readiness_receipt_sha256=...&expected_audit_receipt_sha256=...",
            "GET /release-manifest": "ReleaseManifestResponse: aggregate status, audit, benchmark, readiness, provider-ledger, source-list, and outcome evidence receipts; accepts classical_source_list and expected_*_receipt_sha256 query parameters",
            "GET /release-ledger": "ReleaseManifestLedgerResponse: inspect release manifest ledger hash-chain status",
            "GET /release-drift": "ReleaseManifestDriftResponse: compare current release manifest receipt with the latest recorded release-ledger receipt; add ?manifest=path-to-json&classical_source_list=path-to-json&live=1",
            "GET /schema": "request schema document",
            "POST /analyze": "run analysis; body matches AnalyzeRequest",
            "POST /evolve": "EvolveResponse: run feedback-driven evolution; body matches EvolveRequest",
            "POST /known-gap-handoff-verify": "KnownGapHandoffExportVerificationResponse: verify a known-gap handoff export JSON object; body matches KnownGapHandoffExportVerificationRequest",
            "POST /known-gap-handoff-checklist": "KnownGapHandoffChecklistResponse: build per-gap implementation checklist from a verified handoff export; body matches KnownGapHandoffChecklistRequest",
            "POST /rollback": "RollbackResponse: roll coordinator back to a prior version and write audit lineage; body matches RollbackRequest",
            "POST /benchmark": "BenchmarkResponse: run built-in benchmark or compare versions; accepts expected_benchmark_receipt_sha256",
        },
    }


def schema_validation_errors(
    value: Any,
    *,
    schema_name: str = "AnalyzeResponse",
    schema_doc: dict[str, Any] | None = None,
) -> list[str]:
    """Return lightweight public-schema validation errors for runtime objects.

    The project intentionally avoids a runtime jsonschema dependency, so this
    covers the schema keywords emitted by schema_document: $ref, type, required,
    properties, items, additionalProperties, anyOf, enum, and const.
    """
    document = schema_doc or schema_document()
    schemas = document.get("schemas", {})
    schema = schemas.get(schema_name)
    if not isinstance(schema, dict):
        return [f"$: unknown schema {schema_name}"]
    if not isinstance(schemas, dict):
        return ["$: schema document has no schemas object"]
    return _schema_validation_errors(value, schema, schemas)


def _schema_type_matches(value: Any, expected: object) -> bool:
    types = expected if isinstance(expected, list) else [expected]
    return any(
        (item == "null" and value is None)
        or (item == "object" and isinstance(value, dict))
        or (item == "array" and isinstance(value, list))
        or (item == "string" and isinstance(value, str))
        or (item == "integer" and isinstance(value, int) and not isinstance(value, bool))
        or (item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
        or (item == "boolean" and isinstance(value, bool))
        for item in types
    )


def _schema_validation_errors(
    value: Any,
    schema: dict[str, Any],
    schemas: dict[str, Any],
    path: str = "$",
) -> list[str]:
    if not schema:
        return []
    if "$ref" in schema:
        ref_schema = schemas.get(schema["$ref"].split("/")[-1])
        if not isinstance(ref_schema, dict):
            return [f"{path}: unresolved ref {schema['$ref']}"]
        return _schema_validation_errors(value, ref_schema, schemas, path)
    if "anyOf" in schema:
        for item in schema["anyOf"]:
            if isinstance(item, dict) and not _schema_validation_errors(value, item, schemas, path):
                return []
        return [f"{path}: no anyOf branch matched"]
    if "const" in schema and value != schema["const"]:
        return [f"{path}: expected const {schema['const']!r}, got {value!r}"]
    errors: list[str] = []
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected enum {schema['enum']!r}, got {value!r}")
    if "type" in schema and not _schema_type_matches(value, schema["type"]):
        return [f"{path}: expected type {schema['type']!r}, got {type(value).__name__}"]
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: missing required")
        props = schema.get("properties", {}) if isinstance(schema.get("properties"), dict) else {}
        for key, subschema in props.items():
            if key in value and isinstance(subschema, dict):
                errors.extend(_schema_validation_errors(value[key], subschema, schemas, f"{path}.{key}"))
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            for key, item in value.items():
                if key not in props:
                    errors.extend(_schema_validation_errors(item, additional, schemas, f"{path}.{key}"))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            errors.extend(_schema_validation_errors(item, schema["items"], schemas, f"{path}[{index}]"))
    return errors
