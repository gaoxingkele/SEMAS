"""Persistent CLI for the mingli five-agent SEMAS framework."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.api_core import (
    analyze_case,
    benchmark,
    capability_audit,
    classical_sources_refresh,
    classical_sources_status,
    ensure_repo,
    evolve_case,
    init_repo,
    known_gap_handoff,
    known_gap_handoff_implementation_checklist,
    outcome_dataset_manifest_status,
    provider_examples,
    provider_onboarding,
    provider_certification,
    provider_certification_drift,
    provider_certification_ledger,
    provider_checks,
    provider_protocols,
    production_readiness,
    release_manifest,
    release_manifest_drift,
    release_manifest_ledger,
    rollback_coordinator,
    schema_document,
    status,
    verify_known_gap_handoff_export,
    version_history,
)


DEFAULT_REPO = Path(".semas_mingli_repo")


def _json_default(value: Any) -> str:
    return str(value)


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-16")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(data: dict[str, Any]) -> None:
    """Write a JSON response to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=_json_default))


def configure_stdout_encoding() -> None:
    """Prefer UTF-8 JSON output even on Windows code pages."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if not callable(reconfigure):
        return
    try:
        reconfigure(encoding="utf-8")
    except (OSError, TypeError, ValueError):
        return


def cmd_init(args: argparse.Namespace) -> int:
    write_json(init_repo(args.repo))
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    task_input = read_json(args.input)
    expected = read_json(args.expected) if args.expected else None
    write_json(analyze_case(args.repo, task_input, expected))
    return 0


def cmd_evolve(args: argparse.Namespace) -> int:
    task_input = read_json(args.input)
    expected = read_json(args.feedback)
    write_json(evolve_case(args.repo, task_input, expected, validate_on_input=args.validate_on_input))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    write_json(status(args.repo))
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    write_json(version_history(args.repo))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    write_json(
        capability_audit(
            args.repo,
            expected_audit_receipt_sha256=args.expected_audit_receipt_sha256,
            classical_source_list_path=args.classical_source_list,
        )
    )
    return 0


def cmd_known_gap_handoff(args: argparse.Namespace) -> int:
    write_json(
        known_gap_handoff(
            args.repo,
            expected_audit_receipt_sha256=args.expected_audit_receipt_sha256,
            classical_source_list_path=args.classical_source_list,
        )
    )
    return 0


def cmd_known_gap_handoff_verify(args: argparse.Namespace) -> int:
    write_json(
        verify_known_gap_handoff_export(
            read_json(args.input),
            expected_handoff_export_receipt_sha256=args.expected_handoff_export_receipt_sha256,
        )
    )
    return 0


def cmd_known_gap_handoff_checklist(args: argparse.Namespace) -> int:
    write_json(
        known_gap_handoff_implementation_checklist(
            read_json(args.input),
            expected_handoff_export_receipt_sha256=args.expected_handoff_export_receipt_sha256,
            expected_checklist_receipt_sha256=args.expected_checklist_receipt_sha256,
        )
    )
    return 0


def cmd_providers(args: argparse.Namespace) -> int:
    write_json(provider_checks(args.repo, live=args.live, profile=args.profile))
    return 0


def cmd_provider_examples(args: argparse.Namespace) -> int:
    write_json(provider_examples(args.repo))
    return 0


def cmd_provider_onboarding(args: argparse.Namespace) -> int:
    write_json(provider_onboarding(args.repo))
    return 0


def cmd_certify_provider(args: argparse.Namespace) -> int:
    write_json(
        provider_certification(
            args.repo,
            args.domain,
            live=args.live,
            command=args.command,
            provenance=args.provenance,
            expected_receipt_sha256=args.expected_receipt_sha256,
            record=args.record,
        )
    )
    return 0


def cmd_provider_ledger(args: argparse.Namespace) -> int:
    write_json(provider_certification_ledger(args.repo))
    return 0


def cmd_provider_drift(args: argparse.Namespace) -> int:
    write_json(provider_certification_drift(args.repo, live=args.live, domain=args.domain))
    return 0


def cmd_provider_protocols(args: argparse.Namespace) -> int:
    write_json(provider_protocols(args.repo, domain=args.domain))
    return 0


def cmd_outcome_dataset(args: argparse.Namespace) -> int:
    write_json(outcome_dataset_manifest_status(args.repo, manifest_path=args.manifest))
    return 0


def cmd_classical_sources(args: argparse.Namespace) -> int:
    write_json(classical_sources_status(args.repo, source_list_path=args.source_list))
    return 0


def cmd_classical_refresh(args: argparse.Namespace) -> int:
    write_json(
        classical_sources_refresh(
            args.repo,
            source_list_path=args.source_list,
            cache_dir=args.cache_dir,
            output_dir=args.output_dir,
        )
    )
    return 0


def cmd_production_readiness(args: argparse.Namespace) -> int:
    write_json(
        production_readiness(
            args.repo,
            manifest_path=args.manifest,
            classical_source_list_path=args.classical_source_list,
            live=args.live,
            expected_readiness_receipt_sha256=args.expected_readiness_receipt_sha256,
            expected_audit_receipt_sha256=args.expected_audit_receipt_sha256,
        )
    )
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    write_json(
        benchmark(
            args.repo,
            version=args.version,
            baseline_version=args.baseline_version,
            expected_benchmark_receipt_sha256=args.expected_benchmark_receipt_sha256,
        )
    )
    return 0


def cmd_release_manifest(args: argparse.Namespace) -> int:
    write_json(
        release_manifest(
            args.repo,
            manifest_path=args.manifest,
            classical_source_list_path=args.classical_source_list,
            live=args.live,
            record=args.record,
            expected_audit_receipt_sha256=args.expected_audit_receipt_sha256,
            expected_benchmark_receipt_sha256=args.expected_benchmark_receipt_sha256,
            expected_readiness_receipt_sha256=args.expected_readiness_receipt_sha256,
            expected_release_manifest_receipt_sha256=args.expected_release_manifest_receipt_sha256,
        )
    )
    return 0


def cmd_release_ledger(args: argparse.Namespace) -> int:
    write_json(release_manifest_ledger(args.repo))
    return 0


def cmd_release_drift(args: argparse.Namespace) -> int:
    write_json(
        release_manifest_drift(
            args.repo,
            manifest_path=args.manifest,
            classical_source_list_path=args.classical_source_list,
            live=args.live,
        )
    )
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    write_json(rollback_coordinator(args.repo, to_version=args.to_version, reason=args.reason))
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    write_json(schema_document())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mingli five-agent SEMAS CLI")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Persistent SEMAS repo path")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Initialize the persistent repo")
    init_parser.set_defaults(func=cmd_init)

    analyze_parser = sub.add_parser("analyze", help="Run analysis against the latest genome")
    analyze_parser.add_argument("--input", type=Path, required=True, help="JSON file with {'birth': ...}")
    analyze_parser.add_argument("--expected", type=Path, help="Optional expected/feedback JSON")
    analyze_parser.set_defaults(func=cmd_analyze)

    evolve_parser = sub.add_parser("evolve", help="Store feedback and run population evolution")
    evolve_parser.add_argument("--input", type=Path, required=True, help="JSON file with {'birth': ...}")
    evolve_parser.add_argument("--feedback", type=Path, required=True, help="JSON file with {'feedback': ...}")
    evolve_parser.add_argument(
        "--validate-on-input",
        action="store_true",
        help="Use the same input as a validation holdout for small local runs",
    )
    evolve_parser.set_defaults(func=cmd_evolve)

    status_parser = sub.add_parser("status", help="Show latest genome, archive, and memory state")
    status_parser.set_defaults(func=cmd_status)

    history_parser = sub.add_parser("history", help="Show coordinator version lineage and archive provenance")
    history_parser.set_defaults(func=cmd_history)

    audit_parser = sub.add_parser("audit", help="Show implementation coverage and known gaps")
    audit_parser.add_argument(
        "--expected-audit-receipt-sha256",
        help="Previously recorded audit receipt sha256 to compare against the current capability audit",
    )
    audit_parser.add_argument(
        "--classical-source-list",
        type=Path,
        help="Reviewed classical-source manifest list path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    audit_parser.set_defaults(func=cmd_audit)

    handoff_parser = sub.add_parser(
        "known-gap-handoff",
        help="Export the portable closure handoff bundle for every open known gap",
    )
    handoff_parser.add_argument(
        "--expected-audit-receipt-sha256",
        help="Previously recorded audit receipt sha256 to compare before exporting the handoff bundle",
    )
    handoff_parser.add_argument(
        "--classical-source-list",
        type=Path,
        help="Reviewed classical-source manifest list path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    handoff_parser.set_defaults(func=cmd_known_gap_handoff)

    handoff_verify_parser = sub.add_parser(
        "known-gap-handoff-verify",
        help="Verify a known-gap handoff export JSON file and its receipt",
    )
    handoff_verify_parser.add_argument("--input", type=Path, required=True, help="Known-gap handoff export JSON file")
    handoff_verify_parser.add_argument(
        "--expected-handoff-export-receipt-sha256",
        help="Expected handoff export receipt sha256 to compare with the input file",
    )
    handoff_verify_parser.set_defaults(func=cmd_known_gap_handoff_verify)

    handoff_checklist_parser = sub.add_parser(
        "known-gap-handoff-checklist",
        help="Build an implementation checklist from a known-gap handoff export JSON file",
    )
    handoff_checklist_parser.add_argument("--input", type=Path, required=True, help="Known-gap handoff export JSON file")
    handoff_checklist_parser.add_argument(
        "--expected-handoff-export-receipt-sha256",
        help="Expected handoff export receipt sha256 to verify before building the checklist",
    )
    handoff_checklist_parser.add_argument(
        "--expected-checklist-receipt-sha256",
        help="Expected checklist receipt sha256 to compare with the generated checklist",
    )
    handoff_checklist_parser.set_defaults(func=cmd_known_gap_handoff_checklist)

    providers_parser = sub.add_parser("providers", help="Show optional provider readiness checks")
    providers_parser.add_argument(
        "--profile",
        choices=["development", "production"],
        default="development",
        help="Readiness profile to evaluate; production requires all professional domains and live JSON-CLI checks",
    )
    providers_parser.add_argument(
        "--live",
        action="store_true",
        help="Execute configured JSON-CLI providers with a minimal smoke-test payload",
    )
    providers_parser.set_defaults(func=cmd_providers)

    provider_examples_parser = sub.add_parser(
        "provider-examples",
        help="Run bundled JSON-CLI provider protocol examples and emit a non-production receipt",
    )
    provider_examples_parser.set_defaults(func=cmd_provider_examples)

    provider_onboarding_parser = sub.add_parser(
        "provider-onboarding",
        help="Show machine-readable real-provider onboarding gaps and certification commands",
    )
    provider_onboarding_parser.set_defaults(func=cmd_provider_onboarding)

    certify_parser = sub.add_parser("certify-provider", help="Certify one JSON-CLI professional provider")
    certify_parser.add_argument("domain", choices=["ziwei", "qimen", "astrology", "xuanze"])
    certify_parser.add_argument("--command", help="Provider command to certify without mutating the environment")
    certify_parser.add_argument(
        "--provenance",
        help="Structured provider provenance JSON or semicolon key/value text for one-off certification",
    )
    certify_parser.add_argument(
        "--expected-receipt-sha256",
        help="Previously recorded certification receipt sha256 to compare against the current provider output",
    )
    certify_parser.add_argument(
        "--record",
        action="store_true",
        help="Append a passing certification receipt to the repo provider certification ledger",
    )
    certify_parser.add_argument(
        "--no-live",
        dest="live",
        action="store_false",
        default=True,
        help="Skip the JSON-CLI smoke test and only inspect configuration/provenance",
    )
    certify_parser.set_defaults(func=cmd_certify_provider)

    ledger_parser = sub.add_parser("provider-ledger", help="Show provider certification ledger integrity and coverage")
    ledger_parser.set_defaults(func=cmd_provider_ledger)

    drift_parser = sub.add_parser("provider-drift", help="Compare current providers with recorded certification receipts")
    drift_parser.add_argument("--domain", choices=["ziwei", "qimen", "astrology", "xuanze"], help="Optional single provider domain to check")
    drift_parser.add_argument(
        "--no-live",
        dest="live",
        action="store_false",
        default=True,
        help="Skip live provider execution and return the not-checked drift boundary",
    )
    drift_parser.set_defaults(func=cmd_provider_drift)

    protocols_parser = sub.add_parser("provider-protocols", help="Show JSON-CLI provider integration contracts")
    protocols_parser.add_argument("--domain", choices=["ziwei", "qimen", "astrology", "xuanze"], help="Optional single provider domain to show")
    protocols_parser.set_defaults(func=cmd_provider_protocols)

    outcome_parser = sub.add_parser("outcome-dataset", help="Audit an outcome dataset manifest")
    outcome_parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional outcome dataset manifest JSON path; omitted shows the unconfigured boundary",
    )
    outcome_parser.set_defaults(func=cmd_outcome_dataset)

    classical_sources_parser = sub.add_parser(
        "classical-sources",
        help="Audit external classical-source refresh configuration",
    )
    classical_sources_parser.add_argument(
        "--source-list",
        type=Path,
        help="Optional source-list JSON path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    classical_sources_parser.set_defaults(func=cmd_classical_sources)

    classical_refresh_parser = sub.add_parser(
        "classical-refresh",
        help="Refresh allowlisted classical-source manifests into a local JSONL corpus",
    )
    classical_refresh_parser.add_argument(
        "--source-list",
        type=Path,
        help="Optional source-list JSON path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    classical_refresh_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Optional cache directory for downloaded source manifests",
    )
    classical_refresh_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory for ingested JSONL corpus files",
    )
    classical_refresh_parser.set_defaults(func=cmd_classical_refresh)

    readiness_parser = sub.add_parser("production-readiness", help="Run hard production-readiness gates")
    readiness_parser.add_argument("--manifest", type=Path, help="Externally reviewed outcome dataset manifest path")
    readiness_parser.add_argument(
        "--classical-source-list",
        type=Path,
        help="Reviewed classical-source manifest list path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    readiness_parser.add_argument(
        "--live",
        action="store_true",
        help="Execute configured JSON-CLI provider smoke checks as part of production readiness",
    )
    readiness_parser.add_argument(
        "--expected-readiness-receipt-sha256",
        help="Previously recorded production-readiness receipt sha256 to compare against the current gate result",
    )
    readiness_parser.add_argument(
        "--expected-audit-receipt-sha256",
        help="Previously recorded capability audit receipt sha256 to enforce during production readiness",
    )
    readiness_parser.set_defaults(func=cmd_production_readiness)

    benchmark_parser = sub.add_parser("benchmark", help="Run built-in benchmark cases")
    benchmark_parser.add_argument("--version", type=int, help="Coordinator genome version to evaluate")
    benchmark_parser.add_argument(
        "--baseline-version",
        type=int,
        help="Optional baseline version for comparison against --version/latest",
    )
    benchmark_parser.add_argument(
        "--expected-benchmark-receipt-sha256",
        help="Previously recorded benchmark receipt sha256 to compare against the current benchmark/candidate output",
    )
    benchmark_parser.set_defaults(func=cmd_benchmark)

    release_parser = sub.add_parser("release-manifest", help="Build an aggregate release evidence manifest")
    release_parser.add_argument("--manifest", type=Path, help="Externally reviewed outcome dataset manifest path")
    release_parser.add_argument(
        "--classical-source-list",
        type=Path,
        help="Reviewed classical-source manifest list path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    release_parser.add_argument(
        "--live",
        action="store_true",
        help="Execute configured JSON-CLI provider smoke checks while building the release manifest",
    )
    release_parser.add_argument(
        "--record",
        action="store_true",
        help="Append a ready release manifest receipt to the repo release ledger",
    )
    release_parser.add_argument("--expected-audit-receipt-sha256", help="Expected capability audit receipt sha256")
    release_parser.add_argument("--expected-benchmark-receipt-sha256", help="Expected benchmark receipt sha256")
    release_parser.add_argument("--expected-readiness-receipt-sha256", help="Expected production readiness receipt sha256")
    release_parser.add_argument(
        "--expected-release-manifest-receipt-sha256",
        help="Previously recorded release manifest receipt sha256 to compare against the current manifest",
    )
    release_parser.set_defaults(func=cmd_release_manifest)

    release_ledger_parser = sub.add_parser("release-ledger", help="Show release manifest ledger integrity")
    release_ledger_parser.set_defaults(func=cmd_release_ledger)

    release_drift_parser = sub.add_parser("release-drift", help="Compare current release manifest with the release ledger")
    release_drift_parser.add_argument("--manifest", type=Path, help="Externally reviewed outcome dataset manifest path")
    release_drift_parser.add_argument(
        "--classical-source-list",
        type=Path,
        help="Reviewed classical-source manifest list path; omitted uses SEMAS_CLASSIC_SOURCE_LIST",
    )
    release_drift_parser.add_argument(
        "--live",
        action="store_true",
        help="Execute configured JSON-CLI provider smoke checks while comparing release drift",
    )
    release_drift_parser.set_defaults(func=cmd_release_drift)

    rollback_parser = sub.add_parser("rollback", help="Roll coordinator back to a prior version")
    rollback_parser.add_argument("--to-version", type=int, required=True, help="Prior coordinator version to restore")
    rollback_parser.add_argument("--reason", help="Optional operator reason written to rollback archive lineage")
    rollback_parser.set_defaults(func=cmd_rollback)

    schema_parser = sub.add_parser("schema", help="Show HTTP/API request schema")
    schema_parser.set_defaults(func=cmd_schema)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
