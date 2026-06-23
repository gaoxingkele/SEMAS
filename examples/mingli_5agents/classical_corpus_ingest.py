"""Controlled ingestion for local classical-method corpus manifests.

The ingester converts curated external-source manifests into the JSONL schema
loaded by ``classical_text_index.py``. It deliberately rejects full-text fields
so the evidence layer stays limited to copyright-safe summaries or explicitly
licensed short metadata records.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "source_id",
    "passage_id",
    "title",
    "tradition",
    "keywords",
    "summary",
    "caution",
    "source_url",
    "license",
    "citation_policy",
}

FORBIDDEN_TEXT_FIELDS = {
    "full_text",
    "verbatim_text",
    "raw_text",
    "chapter_text",
}

ALLOWED_CITATION_POLICIES = {
    "paraphrase_only",
    "public_domain_short_excerpt",
    "open_license_short_excerpt",
}


def ingest_corpus_manifest(manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    """Validate and convert a curated manifest into one JSONL corpus file."""
    payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise ValueError("manifest must be a non-empty list or an object with a non-empty 'records' list")

    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_name = _safe_name(payload.get("corpus") if isinstance(payload, dict) else manifest_path.stem)
    output_path = output_dir / f"{corpus_name}.jsonl"
    retrieved_at = _retrieved_at(payload)
    normalized = [
        _normalize_record(record, manifest_path=manifest_path, corpus_name=corpus_name, retrieved_at=retrieved_at)
        for record in records
    ]
    content = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in normalized)
    output_path.write_text(content, encoding="utf-8")
    return {
        "status": "ingested",
        "manifest": str(manifest_path),
        "output_file": str(output_path),
        "record_count": len(normalized),
        "source_ids": sorted({record["source_id"] for record in normalized}),
        "traditions": sorted({record["tradition"] for record in normalized}),
        "source_urls": sorted({record["provenance"]["source_url"] for record in normalized}),
        "licenses": sorted({record["provenance"]["license"] for record in normalized}),
        "citation_policies": sorted({record["provenance"]["citation_policy"] for record in normalized}),
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def _normalize_record(
    record: Any,
    *,
    manifest_path: Path,
    corpus_name: str,
    retrieved_at: str,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("each corpus record must be a JSON object")
    forbidden = sorted(FORBIDDEN_TEXT_FIELDS & set(record))
    if forbidden:
        raise ValueError(f"record {record.get('passage_id', '<unknown>')} includes forbidden full-text fields: {', '.join(forbidden)}")
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        raise ValueError(f"record {record.get('passage_id', '<unknown>')} missing required fields: {', '.join(missing)}")
    if not isinstance(record["keywords"], list) or not record["keywords"]:
        raise ValueError(f"record {record['passage_id']} must include a non-empty keywords list")
    citation_policy = str(record["citation_policy"])
    if citation_policy not in ALLOWED_CITATION_POLICIES:
        raise ValueError(f"record {record['passage_id']} has unsupported citation_policy: {citation_policy}")

    provenance = dict(record.get("provenance") or {})
    provenance.update(
        {
            "corpus": corpus_name,
            "source_url": str(record["source_url"]),
            "license": str(record["license"]),
            "citation_policy": citation_policy,
            "manifest": str(manifest_path),
            "retrieved_at": str(record.get("retrieved_at") or retrieved_at),
            "ingest_policy": "summary_metadata_only_no_full_text",
        }
    )
    return {
        "source_id": str(record["source_id"]),
        "passage_id": str(record["passage_id"]),
        "title": str(record["title"]),
        "tradition": str(record["tradition"]),
        "keywords": [str(item).lower() for item in record["keywords"]],
        "summary": str(record["summary"]),
        "caution": str(record["caution"]),
        "provenance": provenance,
    }


def _retrieved_at(payload: Any) -> str:
    if isinstance(payload, dict) and payload.get("retrieved_at"):
        return str(payload["retrieved_at"])
    return datetime.now(timezone.utc).isoformat()


def _safe_name(value: Any) -> str:
    text = str(value or "external_corpus").strip().lower()
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in text)
    return safe.strip("_") or "external_corpus"
