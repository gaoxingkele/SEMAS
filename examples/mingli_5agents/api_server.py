"""Stdlib HTTP API for the mingli five-agent SEMAS framework."""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.mingli_5agents.api_core import (
    analyze_case,
    benchmark,
    capability_audit,
    classical_sources_refresh,
    classical_sources_status,
    evolve_case,
    init_repo,
    known_gap_handoff,
    known_gap_handoff_implementation_checklist,
    outcome_dataset_manifest_status,
    provider_certification,
    provider_certification_drift,
    provider_certification_ledger,
    provider_checks,
    provider_examples,
    provider_onboarding,
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


class MingliApiHandler(BaseHTTPRequestHandler):
    """HTTP handler bound to one persistent SEMAS repo path."""

    repo_path: Path = DEFAULT_REPO
    server_version = "MingliFiveAgentAPI/1.0"

    def do_GET(self) -> None:
        route, query = self._route()
        try:
            if route == "/health":
                self._write_json({"status": "ok"})
            elif route == "/status":
                self._write_json(status(self.repo_path))
            elif route == "/history":
                self._write_json(version_history(self.repo_path))
            elif route == "/audit":
                classical_source_list = _first(query.get("classical_source_list"))
                self._write_json(
                    capability_audit(
                        self.repo_path,
                        expected_audit_receipt_sha256=_first(query.get("expected_audit_receipt_sha256")),
                        classical_source_list_path=Path(classical_source_list) if classical_source_list else None,
                    )
                )
            elif route == "/known-gap-handoff":
                classical_source_list = _first(query.get("classical_source_list"))
                self._write_json(
                    known_gap_handoff(
                        self.repo_path,
                        expected_audit_receipt_sha256=_first(query.get("expected_audit_receipt_sha256")),
                        classical_source_list_path=Path(classical_source_list) if classical_source_list else None,
                    )
                )
            elif route == "/providers":
                self._write_json(
                    provider_checks(
                        self.repo_path,
                        live=_truthy(_first(query.get("live"))),
                        profile=_first(query.get("profile")) or "development",
                    )
                )
            elif route == "/provider-examples":
                self._write_json(provider_examples(self.repo_path))
            elif route == "/provider-onboarding":
                self._write_json(provider_onboarding(self.repo_path))
            elif route == "/certify-provider":
                domain = _first(query.get("domain"))
                if not domain:
                    self._write_json({"error": "bad_request", "message": "missing query field: domain"}, HTTPStatus.BAD_REQUEST)
                else:
                    self._write_json(
                        provider_certification(
                            self.repo_path,
                            domain=domain,
                            live=not _falsey(_first(query.get("live"))),
                            command=_first(query.get("command")),
                            provenance=_first(query.get("provenance")),
                            expected_receipt_sha256=_first(query.get("expected_receipt_sha256")),
                            record=_truthy(_first(query.get("record"))),
                        )
                    )
            elif route == "/provider-ledger":
                self._write_json(provider_certification_ledger(self.repo_path))
            elif route == "/provider-drift":
                self._write_json(
                    provider_certification_drift(
                        self.repo_path,
                        live=not _falsey(_first(query.get("live"))),
                        domain=_first(query.get("domain")),
                    )
                )
            elif route == "/provider-protocols":
                self._write_json(provider_protocols(self.repo_path, domain=_first(query.get("domain"))))
            elif route == "/outcome-dataset":
                manifest = _first(query.get("manifest"))
                self._write_json(
                    outcome_dataset_manifest_status(
                        self.repo_path,
                        manifest_path=Path(manifest) if manifest else None,
                    )
                )
            elif route == "/classical-sources":
                source_list = _first(query.get("source_list"))
                self._write_json(
                    classical_sources_status(
                        self.repo_path,
                        source_list_path=Path(source_list) if source_list else None,
                    )
                )
            elif route == "/classical-refresh":
                source_list = _first(query.get("source_list"))
                cache_dir = _first(query.get("cache_dir"))
                output_dir = _first(query.get("output_dir"))
                self._write_json(
                    classical_sources_refresh(
                        self.repo_path,
                        source_list_path=Path(source_list) if source_list else None,
                        cache_dir=Path(cache_dir) if cache_dir else None,
                        output_dir=Path(output_dir) if output_dir else None,
                    )
                )
            elif route == "/production-readiness":
                manifest = _first(query.get("manifest"))
                classical_source_list = _first(query.get("classical_source_list"))
                self._write_json(
                    production_readiness(
                        self.repo_path,
                        manifest_path=Path(manifest) if manifest else None,
                        classical_source_list_path=Path(classical_source_list) if classical_source_list else None,
                        live=_truthy(_first(query.get("live"))),
                        expected_readiness_receipt_sha256=_first(query.get("expected_readiness_receipt_sha256")),
                        expected_audit_receipt_sha256=_first(query.get("expected_audit_receipt_sha256")),
                    )
                )
            elif route == "/release-manifest":
                manifest = _first(query.get("manifest"))
                classical_source_list = _first(query.get("classical_source_list"))
                self._write_json(
                    release_manifest(
                        self.repo_path,
                        manifest_path=Path(manifest) if manifest else None,
                        classical_source_list_path=Path(classical_source_list) if classical_source_list else None,
                        live=_truthy(_first(query.get("live"))),
                        record=_truthy(_first(query.get("record"))),
                        expected_audit_receipt_sha256=_first(query.get("expected_audit_receipt_sha256")),
                        expected_benchmark_receipt_sha256=_first(query.get("expected_benchmark_receipt_sha256")),
                        expected_readiness_receipt_sha256=_first(query.get("expected_readiness_receipt_sha256")),
                        expected_release_manifest_receipt_sha256=_first(
                            query.get("expected_release_manifest_receipt_sha256")
                        ),
                    )
                )
            elif route == "/release-ledger":
                self._write_json(release_manifest_ledger(self.repo_path))
            elif route == "/release-drift":
                manifest = _first(query.get("manifest"))
                classical_source_list = _first(query.get("classical_source_list"))
                self._write_json(
                    release_manifest_drift(
                        self.repo_path,
                        manifest_path=Path(manifest) if manifest else None,
                        classical_source_list_path=Path(classical_source_list) if classical_source_list else None,
                        live=_truthy(_first(query.get("live"))),
                    )
                )
            elif route == "/schema":
                self._write_json(schema_document())
            else:
                self._write_json({"error": "not_found", "path": route}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._write_error(exc)

    def do_POST(self) -> None:
        route, query = self._route()
        try:
            body = self._read_json()
            if route == "/init":
                self._write_json(init_repo(self.repo_path))
            elif route == "/analyze":
                expected = body.pop("expected", None)
                self._write_json(analyze_case(self.repo_path, body, expected))
            elif route == "/evolve":
                self._write_json(
                    evolve_case(
                        self.repo_path,
                        body["input"],
                        body["feedback"],
                        validate_on_input=bool(body.get("validate_on_input", False)),
                    )
                )
            elif route == "/benchmark":
                self._write_json(
                    benchmark(
                        self.repo_path,
                        version=_optional_int(body.get("version") or _first(query.get("version"))),
                        baseline_version=_optional_int(
                            body.get("baseline_version") or _first(query.get("baseline_version"))
                        ),
                        expected_benchmark_receipt_sha256=(
                            body.get("expected_benchmark_receipt_sha256")
                            or _first(query.get("expected_benchmark_receipt_sha256"))
                        ),
                    )
                )
            elif route == "/known-gap-handoff-verify":
                handoff_export = body.get("handoff_export") if isinstance(body.get("handoff_export"), dict) else body
                self._write_json(
                    verify_known_gap_handoff_export(
                        handoff_export,
                        expected_handoff_export_receipt_sha256=(
                            body.get("expected_handoff_export_receipt_sha256")
                            or _first(query.get("expected_handoff_export_receipt_sha256"))
                        ),
                    )
                )
            elif route == "/known-gap-handoff-checklist":
                handoff_export = body.get("handoff_export") if isinstance(body.get("handoff_export"), dict) else body
                self._write_json(
                    known_gap_handoff_implementation_checklist(
                        handoff_export,
                        expected_handoff_export_receipt_sha256=(
                            body.get("expected_handoff_export_receipt_sha256")
                            or _first(query.get("expected_handoff_export_receipt_sha256"))
                        ),
                        expected_checklist_receipt_sha256=(
                            body.get("expected_checklist_receipt_sha256")
                            or _first(query.get("expected_checklist_receipt_sha256"))
                        ),
                    )
                )
            elif route == "/rollback":
                self._write_json(
                    rollback_coordinator(
                        self.repo_path,
                        to_version=int(body.get("to_version") or _first(query.get("to_version"))),
                        reason=body.get("reason") or _first(query.get("reason")),
                    )
                )
            else:
                self._write_json({"error": "not_found", "path": route}, HTTPStatus.NOT_FOUND)
        except KeyError as exc:
            self._write_json({"error": "bad_request", "message": f"missing field: {exc}"}, HTTPStatus.BAD_REQUEST)
        except json.JSONDecodeError as exc:
            self._write_json({"error": "bad_json", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._write_error(exc)

    def log_message(self, format: str, *args: Any) -> None:
        """Keep default server quiet in tests and scripted runs."""
        return

    def _route(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urlparse(self.path)
        return parsed.path.rstrip("/") or "/", parse_qs(parsed.query)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if length == 0:
            return {}
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")
        return data

    def _write_json(self, data: dict[str, Any], status_code: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(int(status_code))
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _write_error(self, exc: Exception) -> None:
        self._write_json(
            {"error": exc.__class__.__name__, "message": str(exc)},
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


def make_handler(repo_path: Path) -> type[MingliApiHandler]:
    """Create a handler class bound to a repo path."""

    class BoundMingliApiHandler(MingliApiHandler):
        pass

    BoundMingliApiHandler.repo_path = repo_path
    return BoundMingliApiHandler


def serve(host: str, port: int, repo_path: Path) -> ThreadingHTTPServer:
    """Create and return a configured HTTP server."""
    return ThreadingHTTPServer((host, port), make_handler(repo_path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mingli five-agent SEMAS HTTP API")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Persistent SEMAS repo path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    httpd = serve(args.host, args.port, args.repo)
    print(f"Serving mingli API on http://{args.host}:{args.port} with repo {args.repo}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _first(values: list[str] | None) -> str | None:
    return values[0] if values else None


def _truthy(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def _falsey(value: str | None) -> bool:
    return str(value).lower() in {"0", "false", "no", "off"}


if __name__ == "__main__":
    raise SystemExit(main())
