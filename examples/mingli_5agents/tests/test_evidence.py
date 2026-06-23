"""Tests for local evidence retrieval."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from examples.mingli_5agents.classical_corpus_ingest import ingest_corpus_manifest
from examples.mingli_5agents.classical_corpus_refresh import refresh_corpus_manifests, source_list_audit
from examples.mingli_5agents.classical_text_index import classical_index_audit, retrieve_classical_passages
from examples.mingli_5agents.api_core import classical_sources_refresh, classical_sources_status
from examples.mingli_5agents.evaluators.evidence_provenance_evaluator import evidence_provenance_score
from examples.mingli_5agents.evidence import retrieve_evidence, retrieve_many


EXAMPLE_CLASSICAL_SOURCE_LIST = (
    Path(__file__).resolve().parents[1] / "providers" / "classical_source_list_example.json"
)


def _source_governance_fields() -> dict[str, str]:
    return {
        "license": "CC0-1.0",
        "rights_basis": "test fixture authored for repository validation",
        "review_status": "open_license_reviewed",
        "reviewed_by": "unit test",
        "content_scope": "method metadata fixture only",
    }


def test_bundled_classical_source_list_is_hash_pinned_and_refreshable(tmp_path):
    audit = source_list_audit(EXAMPLE_CLASSICAL_SOURCE_LIST)

    assert audit["status"] == "ready"
    assert audit["valid"] is True
    assert audit["locked_source_count"] == 1
    assert audit["source_audits"][0]["scheme"] == "path"
    assert audit["source_audits"][0]["sha256_pinned"] is True
    assert audit["source_audits"][0]["governance_valid"] is True
    assert audit["source_audits"][0]["license"] == "CC0-1.0"
    assert audit["source_list_receipt"]["material"]["source_audits"][0]["review_status"] == "open_license_reviewed"
    assert audit["source_audits"][0]["refreshable"] is True

    result = refresh_corpus_manifests(EXAMPLE_CLASSICAL_SOURCE_LIST, tmp_path / "cache", tmp_path / "corpus")

    assert result["status"] == "refreshed"
    assert result["record_count"] == 3
    material_sha = hashlib.sha256(
        json.dumps(audit["source_list_receipt"]["material"], sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assert result["refresh_receipt"]["material"]["source_list_receipt_sha256"] == audit["source_list_receipt"]["sha256"]
    assert result["refresh_receipt"]["material"]["source_list_receipt_material_sha256"] == material_sha
    assert result["refresh_receipt"]["material"]["sources"][0]["source_ids"] == [
        "bazi_ziping_method_boundary",
        "qimen_timing_method_boundary",
        "ziwei_palace_method_boundary",
    ]


def test_retrieve_evidence_by_source_id():
    snippets = retrieve_evidence("bazi_ziping", query="pillar element balance")
    assert snippets
    assert snippets[0]["source_id"] == "bazi_ziping"
    assert "pillar" in snippets[0]["keywords"]
    assert snippets[0]["provenance"]["corpus"] == "built_in_seed"
    assert snippets[0]["excerpt_type"] == "paraphrase"


def test_retrieve_many_returns_empty_for_unknown_source():
    result = retrieve_many(["bazi_ziping", "unknown_source"], query="source")
    assert result["bazi_ziping"]
    assert result["unknown_source"] == []


def test_classical_index_loads_optional_jsonl_corpus(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "custom.jsonl").write_text(
        json.dumps(
            {
                "source_id": "bazi_ziping",
                "passage_id": "custom_balance",
                "title": "Custom balance note",
                "tradition": "bazi",
                "keywords": ["custom", "balance"],
                "summary": "Custom local corpus summary.",
                "caution": "Local test caution.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    snippets = retrieve_classical_passages("bazi_ziping", query="custom", corpus_dir=corpus)
    assert snippets[0]["snippet_id"] == "custom_balance"
    assert snippets[0]["provenance"]["corpus"] == "custom"
    audit = classical_index_audit(corpus)
    assert audit["external_record_count"] == 1
    assert "bazi_ziping" in audit["source_ids"]


def test_ingest_corpus_manifest_writes_provenance_jsonl(tmp_path):
    manifest = tmp_path / "manifest.json"
    output_dir = tmp_path / "corpus"
    manifest.write_text(
        json.dumps(
            {
                "corpus": "Open Mingli Notes",
                "retrieved_at": "2026-06-21T00:00:00+00:00",
                "records": [
                    {
                        "source_id": "qimen_plate",
                        "passage_id": "open_qimen_layer_note",
                        "title": "Open Qi Men layer note",
                        "tradition": "qimen",
                        "keywords": ["open", "plate", "layer"],
                        "summary": "Curated summary of an open-source Qi Men layer explanation.",
                        "caution": "Use as method context only.",
                        "source_url": "https://example.org/qimen-note",
                        "license": "CC-BY-4.0",
                        "citation_policy": "open_license_short_excerpt",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    audit = ingest_corpus_manifest(manifest, output_dir)
    snippets = retrieve_classical_passages("qimen_plate", query="open layer", corpus_dir=output_dir)

    assert audit["status"] == "ingested"
    assert audit["record_count"] == 1
    assert audit["licenses"] == ["CC-BY-4.0"]
    assert snippets[0]["snippet_id"] == "open_qimen_layer_note"
    assert snippets[0]["provenance"]["source_url"] == "https://example.org/qimen-note"
    assert snippets[0]["provenance"]["ingest_policy"] == "summary_metadata_only_no_full_text"


def test_ingest_corpus_manifest_accepts_utf8_bom(tmp_path):
    manifest = tmp_path / "manifest.json"
    output_dir = tmp_path / "corpus"
    manifest.write_text(
        "\ufeff"
        + json.dumps(
            {
                "records": [
                    {
                        "source_id": "bazi_ziping",
                        "passage_id": "bom_manifest_case",
                        "title": "BOM manifest case",
                        "tradition": "bazi",
                        "keywords": ["bom"],
                        "summary": "BOM manifest fixture.",
                        "caution": "Fixture only.",
                        "source_url": "https://example.org/bom-manifest",
                        "license": "CC0-1.0",
                        "citation_policy": "paraphrase_only",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    audit = ingest_corpus_manifest(manifest, output_dir)

    assert audit["status"] == "ingested"
    assert audit["record_count"] == 1


def test_ingest_corpus_manifest_rejects_full_text_fields(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "source_id": "bazi_ziping",
                    "passage_id": "unsafe_full_text",
                    "title": "Unsafe full text",
                    "tradition": "bazi",
                    "keywords": ["unsafe"],
                    "summary": "Summary is fine.",
                    "caution": "Caution.",
                    "source_url": "https://example.org/unsafe",
                    "license": "unknown",
                    "citation_policy": "paraphrase_only",
                    "full_text": "Do not ingest full text through this path.",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="forbidden full-text fields"):
        ingest_corpus_manifest(manifest, tmp_path / "corpus")


def test_refresh_corpus_manifests_downloads_allowlisted_manifest(tmp_path):
    remote_manifest = tmp_path / "remote_manifest.json"
    remote_manifest.write_text(
        json.dumps(
            {
                "corpus": "Remote Fixture",
                "retrieved_at": "2026-06-21T00:00:00+00:00",
                "records": [
                    {
                        "source_id": "ziwei_palace",
                        "passage_id": "remote_ziwei_palace_note",
                        "title": "Remote Zi Wei palace note",
                        "tradition": "ziwei",
                        "keywords": ["remote", "palace"],
                        "summary": "Allowlisted fixture summary.",
                        "caution": "Fixture only.",
                        "source_url": "https://example.org/ziwei-palace",
                        "license": "CC0-1.0",
                        "citation_policy": "public_domain_short_excerpt",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allow_file_urls": True,
                "sources": [{"name": "remote-fixture", "url": remote_manifest.as_uri(), **_source_governance_fields()}],
            }
        ),
        encoding="utf-8",
    )

    result = refresh_corpus_manifests(source_list, tmp_path / "cache", tmp_path / "corpus")
    snippets = retrieve_classical_passages("ziwei_palace", query="remote palace", corpus_dir=tmp_path / "corpus")

    assert result["status"] == "refreshed"
    assert result["source_count"] == 1
    assert result["record_count"] == 1
    assert len(result["refresh_receipt"]["sha256"]) == 64
    assert result["refresh_receipt"]["material"]["record_count"] == 1
    assert result["refresh_receipt"]["material"]["sources"][0]["ingest_record_count"] == 1
    assert result["refresh_receipt"]["material"]["sources"][0]["ingest_content_hash"] == result["sources"][0]["ingest"][
        "content_hash"
    ]
    assert snippets[0]["snippet_id"] == "remote_ziwei_palace_note"
    assert snippets[0]["provenance"]["manifest"].endswith("remote-fixture.manifest.json")


def test_refresh_corpus_manifests_accepts_utf8_bom_source_list(tmp_path):
    remote_manifest = tmp_path / "remote_manifest.json"
    remote_manifest.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_id": "bazi_ziping",
                        "passage_id": "bom_source_list_case",
                        "title": "BOM source list case",
                        "tradition": "bazi",
                        "keywords": ["bom"],
                        "summary": "BOM source list fixture.",
                        "caution": "Fixture only.",
                        "source_url": "https://example.org/bom-source-list",
                        "license": "CC0-1.0",
                        "citation_policy": "paraphrase_only",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        "\ufeff"
        + json.dumps(
            {
                "allow_file_urls": True,
                "sources": [{"name": "bom-fixture", "url": remote_manifest.as_uri(), **_source_governance_fields()}],
            }
        ),
        encoding="utf-8",
    )

    result = refresh_corpus_manifests(source_list, tmp_path / "cache", tmp_path / "corpus")

    assert result["status"] == "refreshed"
    assert result["record_count"] == 1
    assert len(result["refresh_receipt"]["sha256"]) == 64


def test_classical_sources_refresh_returns_api_receipt(tmp_path):
    remote_manifest = tmp_path / "remote_manifest.json"
    remote_manifest.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_id": "bazi_ziping",
                        "passage_id": "api_refresh_case",
                        "title": "API refresh case",
                        "tradition": "bazi",
                        "keywords": ["api", "refresh"],
                        "summary": "API refresh fixture.",
                        "caution": "Fixture only.",
                        "source_url": "https://example.org/api-refresh",
                        "license": "CC0-1.0",
                        "citation_policy": "paraphrase_only",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allow_file_urls": True,
                "sources": [{"name": "api-refresh-fixture", "url": remote_manifest.as_uri(), **_source_governance_fields()}],
            }
        ),
        encoding="utf-8",
    )

    result = classical_sources_refresh(
        tmp_path / "repo",
        source_list_path=source_list,
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "corpus",
    )

    assert result["status"] == "refreshed"
    assert result["refreshed"] is True
    assert result["refresh"]["record_count"] == 1
    assert result["refresh_receipt"] == result["refresh"]["refresh_receipt"]
    assert result["refresh_receipt"]["material"]["source_list_receipt_sha256"] == result["source_list_receipt"]["sha256"]
    material_sha = hashlib.sha256(
        json.dumps(result["source_list_receipt"]["material"], sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assert result["refresh_receipt"]["material"]["source_list_receipt_material_sha256"] == material_sha
    assert result["refresh_receipt"]["material"]["sources"][0]["citation_policies"] == ["paraphrase_only"]
    assert result["audit"]["status"] == "ready"
    assert len(result["source_list_receipt"]["sha256"]) == 64


def test_refresh_corpus_manifests_rejects_unallowlisted_host(tmp_path):
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allowed_hosts": ["allowed.example"],
                "sources": [
                    {
                        "name": "bad-host",
                        "url": "https://blocked.example/manifest.json",
                        **_source_governance_fields(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not allowlisted"):
        refresh_corpus_manifests(source_list, tmp_path / "cache", tmp_path / "corpus")


def test_refresh_corpus_manifests_rejects_hash_mismatch(tmp_path):
    remote_manifest = tmp_path / "remote_manifest.json"
    remote_manifest.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_id": "bazi_ziping",
                        "passage_id": "hash_case",
                        "title": "Hash case",
                        "tradition": "bazi",
                        "keywords": ["hash"],
                        "summary": "Hash mismatch fixture.",
                        "caution": "Fixture only.",
                        "source_url": "https://example.org/hash-case",
                        "license": "CC0-1.0",
                        "citation_policy": "paraphrase_only",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allow_file_urls": True,
                "sources": [
                    {
                        "name": "hash-fixture",
                        "url": remote_manifest.as_uri(),
                        "sha256": "0" * 64,
                        **_source_governance_fields(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sha256 mismatch"):
        refresh_corpus_manifests(source_list, tmp_path / "cache", tmp_path / "corpus")


def test_source_list_audit_reports_unconfigured_without_downloading(monkeypatch):
    monkeypatch.delenv("SEMAS_CLASSIC_SOURCE_LIST", raising=False)

    result = source_list_audit()

    assert result["status"] == "unconfigured"
    assert result["valid"] is False
    assert result["source_count"] == 0
    assert "SEMAS_CLASSIC_SOURCE_LIST" in result["failures"][0]
    assert result["source_list_receipt"]["material"]["status"] == "unconfigured"
    assert len(result["source_list_receipt"]["sha256"]) == 64
    assert result["source_list_receipt"] == source_list_audit()["source_list_receipt"]


def test_classical_sources_status_exposes_configuration_guidance(tmp_path, monkeypatch):
    monkeypatch.delenv("SEMAS_CLASSIC_SOURCE_LIST", raising=False)

    unconfigured = classical_sources_status(tmp_path / "repo")
    guidance = unconfigured["configuration_guidance"]
    assert unconfigured["configured"] is False
    assert guidance["configured"] is False
    assert guidance["env_var"] == "SEMAS_CLASSIC_SOURCE_LIST"
    assert guidance["current_source_list_path"] is None
    assert guidance["example_source_list_path"].endswith("classical_source_list_example.json")
    assert guidance["example_is_demonstration_only"] is True
    assert "classical-sources --source-list <source-list.json>" in guidance["cli_audit_command"]
    assert "classical-refresh --source-list <source-list.json>" in guidance["cli_refresh_command"]
    assert "production-readiness --classical-source-list <source-list.json>" in guidance[
        "production_readiness_command"
    ]
    assert guidance["http_query"] == "GET /classical-sources?source_list=<source-list.json>"
    assert "must not be treated as a production corpus" in guidance["policy"]

    configured = classical_sources_status(tmp_path / "repo", source_list_path=EXAMPLE_CLASSICAL_SOURCE_LIST)
    configured_guidance = configured["configuration_guidance"]
    assert configured["configured"] is True
    assert configured_guidance["configured"] is True
    assert configured_guidance["current_source_list_path"] == str(EXAMPLE_CLASSICAL_SOURCE_LIST)
    assert str(EXAMPLE_CLASSICAL_SOURCE_LIST) in configured_guidance["cli_refresh_command"]


def test_source_list_audit_accepts_allowlisted_locked_remote_manifest(tmp_path):
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allowed_hosts": ["classics.example"],
                "max_bytes": 100000,
                "sources": [
                    {
                        "name": "locked-source",
                        "url": "https://classics.example/manifest.json",
                        "sha256": "a" * 64,
                        **_source_governance_fields(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = source_list_audit(source_list)

    assert result["status"] == "ready"
    assert result["valid"] is True
    assert result["source_count"] == 1
    assert result["locked_source_count"] == 1
    assert result["allowed_hosts"] == ["classics.example"]
    assert len(result["content_hash"]) == 64
    assert result["source_list_receipt"]["material"]["content_hash"] == result["content_hash"]
    assert result["source_list_receipt"]["material"]["locked_source_count"] == 1
    assert result["source_audits"] == [
        {
            "index": 0,
            "name": "locked-source",
            "url": "https://classics.example/manifest.json",
            "scheme": "https",
            "host": "classics.example",
            "allowed": True,
            "sha256_pinned": True,
            "governance_valid": True,
            "license": "CC0-1.0",
            "rights_basis": "test fixture authored for repository validation",
            "review_status": "open_license_reviewed",
            "reviewed_by": "unit test",
            "content_scope": "method metadata fixture only",
            "refreshable": True,
            "failures": [],
        }
    ]
    assert result["source_list_receipt"]["material"]["source_audits"] == result["source_audits"]
    assert len(result["source_list_receipt"]["sha256"]) == 64


def test_source_list_audit_accepts_utf8_bom_source_list(tmp_path):
    source_list = tmp_path / "sources_bom.json"
    payload = json.dumps(
        {
            "allowed_hosts": ["classics.example"],
            "sources": [
                {
                    "name": "locked-source",
                    "url": "https://classics.example/manifest.json",
                    "sha256": "a" * 64,
                    **_source_governance_fields(),
                }
            ],
        }
    )
    source_list.write_bytes(("\ufeff" + payload).encode("utf-8"))

    result = source_list_audit(source_list)

    assert result["status"] == "ready"
    assert result["valid"] is True
    assert result["source_audits"][0]["refreshable"] is True


def test_source_list_audit_rejects_unlocked_remote_manifest(tmp_path):
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allowed_hosts": ["classics.example"],
                "sources": [
                    {
                        "name": "unlocked",
                        "url": "https://classics.example/manifest.json",
                        **_source_governance_fields(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = source_list_audit(source_list)

    assert result["status"] == "invalid"
    assert result["valid"] is False
    assert any("must pin a 64-character sha256" in item for item in result["failures"])
    assert result["source_audits"][0]["allowed"] is True
    assert result["source_audits"][0]["sha256_pinned"] is False
    assert result["source_audits"][0]["refreshable"] is False
    assert "remote manifest must pin a 64-character sha256" in result["source_audits"][0]["failures"]
    assert result["source_list_receipt"]["material"]["status"] == "invalid"


def test_source_list_audit_rejects_missing_source_governance_metadata(tmp_path):
    source_list = tmp_path / "sources.json"
    source_list.write_text(
        json.dumps(
            {
                "allowed_hosts": ["classics.example"],
                "sources": [
                    {
                        "name": "ungoverned",
                        "url": "https://classics.example/manifest.json",
                        "sha256": "a" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = source_list_audit(source_list)

    assert result["status"] == "invalid"
    assert result["valid"] is False
    assert result["source_audits"][0]["governance_valid"] is False
    assert result["source_audits"][0]["refreshable"] is False
    assert any("license is required for source governance" in item for item in result["failures"])
    assert "rights_basis is required for source governance" in result["source_audits"][0]["failures"]


def test_evidence_provenance_metric_requires_audit_fields():
    result = {"source_review": {"evidence": {"bazi_ziping": retrieve_evidence("bazi_ziping")}}}
    assert evidence_provenance_score(result) == 1.0

    result["source_review"]["evidence"]["bazi_ziping"][0].pop("provenance")
    assert evidence_provenance_score(result) < 1.0
