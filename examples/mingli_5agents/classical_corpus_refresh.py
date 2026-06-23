"""Allowlisted refresh pipeline for external classical-method manifests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from examples.mingli_5agents.classical_corpus_ingest import ingest_corpus_manifest


DEFAULT_MAX_BYTES = 1_000_000
SOURCE_LIST_ENV_VAR = "SEMAS_CLASSIC_SOURCE_LIST"
REQUIRED_SOURCE_GOVERNANCE_FIELDS = {
    "license",
    "rights_basis",
    "review_status",
    "reviewed_by",
    "content_scope",
}
ALLOWED_SOURCE_REVIEW_STATUSES = {
    "public_domain_reviewed",
    "open_license_reviewed",
    "internal_reviewed_excerpt_only",
}


def source_list_audit(source_list_path: Path | None = None) -> dict[str, Any]:
    """Audit external classical-source refresh configuration without downloading."""
    path = source_list_path or _source_list_from_env()
    if path is None:
        return _with_source_list_receipt({
            "status": "unconfigured",
            "source_list": "",
            "exists": False,
            "valid": False,
            "source_count": 0,
            "locked_source_count": 0,
            "allowed_hosts": [],
            "allow_file_urls": False,
            "max_bytes": DEFAULT_MAX_BYTES,
            "source_audits": [],
            "content_hash": "",
            "failures": [f"{SOURCE_LIST_ENV_VAR} is not configured"],
            "refresh_command": (
                f"set {SOURCE_LIST_ENV_VAR}=path-to-source-list.json && "
                "python -m examples.mingli_5agents.classical_corpus_refresh"
            ),
        })
    if not path.exists():
        return _with_source_list_receipt({
            "status": "missing",
            "source_list": str(path),
            "exists": False,
            "valid": False,
            "source_count": 0,
            "locked_source_count": 0,
            "allowed_hosts": [],
            "allow_file_urls": False,
            "max_bytes": DEFAULT_MAX_BYTES,
            "source_audits": [],
            "content_hash": "",
            "failures": ["source list file does not exist"],
            "refresh_command": f"python -m examples.mingli_5agents.classical_corpus_refresh {path}",
        })
    try:
        raw = path.read_bytes()
        config = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _with_source_list_receipt({
            "status": "invalid",
            "source_list": str(path),
            "exists": True,
            "valid": False,
            "source_count": 0,
            "locked_source_count": 0,
            "allowed_hosts": [],
            "allow_file_urls": False,
            "max_bytes": DEFAULT_MAX_BYTES,
            "source_audits": [],
            "content_hash": "",
            "failures": [f"source list is not valid UTF-8 JSON: {exc}"],
            "refresh_command": f"python -m examples.mingli_5agents.classical_corpus_refresh {path}",
        })
    failures = _source_list_failures(config, source_list_dir=path.parent)
    sources = config.get("sources") if isinstance(config, dict) else []
    if not isinstance(sources, list):
        sources = []
    locked_count = sum(1 for item in sources if isinstance(item, dict) and _sha256_valid(item.get("sha256")))
    allow_file_urls = bool(config.get("allow_file_urls", False)) if isinstance(config, dict) else False
    max_bytes = int(config.get("max_bytes", DEFAULT_MAX_BYTES)) if isinstance(config, dict) else DEFAULT_MAX_BYTES
    try:
        allowed_hosts = sorted(_allowed_hosts(config)) if isinstance(config, dict) else []
    except ValueError:
        allowed_hosts = []
    source_audits = _source_entry_audits(
        sources,
        allowed_hosts=set(allowed_hosts),
        allow_file_urls=allow_file_urls,
        source_list_dir=path.parent,
    )
    return _with_source_list_receipt({
        "status": "ready" if not failures else "invalid",
        "source_list": str(path),
        "exists": True,
        "valid": not failures,
        "source_count": len(sources),
        "locked_source_count": locked_count,
        "allowed_hosts": allowed_hosts,
        "allow_file_urls": allow_file_urls,
        "max_bytes": max_bytes,
        "source_audits": source_audits,
        "content_hash": hashlib.sha256(raw).hexdigest(),
        "failures": failures,
        "refresh_command": f"python -m examples.mingli_5agents.classical_corpus_refresh {path}",
    })


def source_list_receipt(audit: dict[str, Any]) -> dict[str, Any]:
    """Return a stable receipt for a classical-source refresh audit."""
    material = {
        "schema_version": 1,
        "status": audit.get("status"),
        "source_list": audit.get("source_list", ""),
        "exists": bool(audit.get("exists")),
        "valid": bool(audit.get("valid")),
        "source_count": int(audit.get("source_count") or 0),
        "locked_source_count": int(audit.get("locked_source_count") or 0),
        "allowed_hosts": sorted(str(item) for item in audit.get("allowed_hosts", []) if str(item)),
        "allow_file_urls": bool(audit.get("allow_file_urls")),
        "max_bytes": int(audit.get("max_bytes") or DEFAULT_MAX_BYTES),
        "source_audits": _receipt_source_audits(audit.get("source_audits", [])),
        "content_hash": audit.get("content_hash", ""),
        "failures": list(audit.get("failures", [])),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _with_source_list_receipt(audit: dict[str, Any]) -> dict[str, Any]:
    audit["source_list_receipt"] = source_list_receipt(audit)
    return audit


def refresh_corpus_manifests(source_list_path: Path, cache_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Download allowlisted manifest files, cache them, and ingest into JSONL."""
    audit = source_list_audit(source_list_path)
    config = json.loads(source_list_path.read_text(encoding="utf-8-sig"))
    sources = config.get("sources") if isinstance(config, dict) else None
    if not isinstance(sources, list) or not sources:
        raise ValueError("source list must contain a non-empty 'sources' list")

    allowed_hosts = _allowed_hosts(config)
    allow_file_urls = bool(config.get("allow_file_urls", False))
    max_bytes = int(config.get("max_bytes", DEFAULT_MAX_BYTES))
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for item in sources:
        results.append(
            _refresh_one(
                item,
                source_list_dir=source_list_path.parent,
                cache_dir=cache_dir,
                output_dir=output_dir,
                allowed_hosts=allowed_hosts,
                allow_file_urls=allow_file_urls,
                max_bytes=max_bytes,
            )
        )
    aggregate = "".join(result["content_hash"] for result in results)
    result = {
        "status": "refreshed",
        "source_list": str(source_list_path),
        "cache_dir": str(cache_dir),
        "output_dir": str(output_dir),
        "source_list_receipt_sha256": audit.get("source_list_receipt", {}).get("sha256"),
        "source_list_receipt_material_sha256": _receipt_material_sha256(audit.get("source_list_receipt", {})),
        "source_count": len(results),
        "record_count": sum(int(result["ingest"]["record_count"]) for result in results),
        "allowed_hosts": sorted(allowed_hosts),
        "allow_file_urls": allow_file_urls,
        "sources": results,
        "content_hash": hashlib.sha256(aggregate.encode("utf-8")).hexdigest(),
    }
    result["refresh_receipt"] = classical_refresh_receipt(result)
    (output_dir / "refresh_receipt.json").write_text(
        json.dumps(result["refresh_receipt"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def classical_refresh_receipt(refresh: dict[str, Any]) -> dict[str, Any]:
    """Return a stable receipt for one completed classical-source refresh."""
    material = {
        "schema_version": 1,
        "status": refresh.get("status"),
        "source_list": refresh.get("source_list", ""),
        "source_list_receipt_sha256": refresh.get("source_list_receipt_sha256"),
        "source_list_receipt_material_sha256": refresh.get("source_list_receipt_material_sha256"),
        "cache_dir": refresh.get("cache_dir", ""),
        "output_dir": refresh.get("output_dir", ""),
        "source_count": int(refresh.get("source_count") or 0),
        "record_count": int(refresh.get("record_count") or 0),
        "allowed_hosts": sorted(str(item) for item in refresh.get("allowed_hosts", []) if str(item)),
        "allow_file_urls": bool(refresh.get("allow_file_urls")),
        "sources": _refresh_receipt_sources(refresh.get("sources", [])),
        "content_hash": refresh.get("content_hash", ""),
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return {
        "schema_version": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "material": material,
    }


def _refresh_one(
    item: Any,
    *,
    source_list_dir: Path,
    cache_dir: Path,
    output_dir: Path,
    allowed_hosts: set[str],
    allow_file_urls: bool,
    max_bytes: int,
) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("each source entry must be a JSON object")
    location = _source_location(item)
    name = _safe_name(item.get("name") or Path(urlparse(location).path or location).stem or "manifest")
    _validate_source_location(location, allowed_hosts=allowed_hosts, allow_file_urls=allow_file_urls)
    data = _download_source(location, source_list_dir=source_list_dir, max_bytes=max_bytes)
    actual_hash = hashlib.sha256(data).hexdigest()
    expected_hash = item.get("sha256")
    if expected_hash and str(expected_hash).lower() != actual_hash:
        raise ValueError(f"{name} sha256 mismatch: expected {expected_hash}, got {actual_hash}")

    cache_path = cache_dir / f"{name}.manifest.json"
    cache_path.write_bytes(data)
    ingest = ingest_corpus_manifest(cache_path, output_dir)
    return {
        "name": name,
        "url": location,
        "cache_file": str(cache_path),
        "content_hash": actual_hash,
        "ingest": ingest,
    }


def _download_source(location: str, *, source_list_dir: Path, max_bytes: int) -> bytes:
    parsed = urlparse(location)
    if not parsed.scheme and location:
        path = Path(location)
        if not path.is_absolute():
            path = source_list_dir / path
        data = path.read_bytes()
        if len(data) > max_bytes:
            raise ValueError(f"manifest exceeds max_bytes={max_bytes}")
        return data
    return _download(location, max_bytes=max_bytes)


def _download(url: str, *, max_bytes: int) -> bytes:
    with urlopen(url, timeout=15) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"manifest exceeds max_bytes={max_bytes}")
    return data


def _validate_source_location(location: str, *, allowed_hosts: set[str], allow_file_urls: bool) -> None:
    parsed = urlparse(location)
    if not parsed.scheme and location:
        if allow_file_urls:
            return
        raise ValueError("local source paths are disabled unless allow_file_urls is true")
    if parsed.scheme == "file":
        if allow_file_urls:
            return
        raise ValueError("file URLs are disabled unless allow_file_urls is true")
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported manifest URL scheme: {parsed.scheme}")
    host = parsed.hostname or ""
    if not host or host not in allowed_hosts:
        raise ValueError(f"manifest host is not allowlisted: {host}")


def _source_location(item: dict[str, Any]) -> str:
    if item.get("path"):
        return str(item.get("path"))
    return str(item.get("url") or "")


def _allowed_hosts(config: dict[str, Any]) -> set[str]:
    values = config.get("allowed_hosts")
    if values is None:
        values = [item.strip() for item in os.getenv("SEMAS_CLASSIC_ALLOWLIST_HOSTS", "").split(",")]
    hosts = {str(item).lower() for item in values if str(item).strip()}
    if not hosts and not bool(config.get("allow_file_urls", False)):
        raise ValueError("source list must define allowed_hosts or SEMAS_CLASSIC_ALLOWLIST_HOSTS")
    return hosts


def _safe_name(value: Any) -> str:
    text = str(value or "manifest").strip().lower()
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in text)
    return safe.strip("_") or "manifest"


def _source_list_from_env() -> Path | None:
    value = os.getenv(SOURCE_LIST_ENV_VAR)
    return Path(value) if value else None


def _source_list_failures(config: Any, *, source_list_dir: Path | None = None) -> list[str]:
    if not isinstance(config, dict):
        return ["source list must be a JSON object"]
    failures = []
    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        failures.append("source list must contain a non-empty sources list")
        sources = []
    allow_file_urls = bool(config.get("allow_file_urls", False))
    try:
        allowed_hosts = _allowed_hosts(config)
    except ValueError as exc:
        allowed_hosts = set()
        failures.append(str(exc))
    max_bytes = config.get("max_bytes", DEFAULT_MAX_BYTES)
    if not isinstance(max_bytes, int) or max_bytes <= 0 or max_bytes > DEFAULT_MAX_BYTES:
        failures.append(f"max_bytes must be a positive integer no larger than {DEFAULT_MAX_BYTES}")
    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            failures.append(f"sources[{index}] must be an object")
            continue
        failures.extend(_source_governance_failures(item, index))
        location = _source_location(item)
        parsed = urlparse(location)
        if not location:
            failures.append(f"sources[{index}] must define url or path")
        elif not parsed.scheme:
            if not allow_file_urls:
                failures.append(f"sources[{index}] local path requires allow_file_urls=true")
            if item.get("path") and not _sha256_valid(item.get("sha256")):
                failures.append(f"sources[{index}] local path manifest must pin a 64-character sha256")
        elif parsed.scheme == "file":
            if not allow_file_urls:
                failures.append(f"sources[{index}] file URL requires allow_file_urls=true")
        elif parsed.scheme in {"http", "https"}:
            host = parsed.hostname or ""
            if not host or host not in allowed_hosts:
                failures.append(f"sources[{index}] host is not allowlisted: {host}")
            if not _sha256_valid(item.get("sha256")):
                failures.append(f"sources[{index}] remote manifest must pin a 64-character sha256")
        else:
            failures.append(f"sources[{index}] unsupported URL scheme: {parsed.scheme}")
        if item.get("path") and source_list_dir is not None:
            candidate = Path(str(item.get("path")))
            if not candidate.is_absolute():
                candidate = source_list_dir / candidate
            if not candidate.exists():
                failures.append(f"sources[{index}] local path manifest does not exist")
    return failures


def _source_entry_audits(
    sources: list[Any],
    *,
    allowed_hosts: set[str],
    allow_file_urls: bool,
    source_list_dir: Path | None = None,
) -> list[dict[str, Any]]:
    audits = []
    for index, item in enumerate(sources):
        failures = []
        if not isinstance(item, dict):
            audits.append(
                {
                    "index": index,
                    "name": "",
                    "url": "",
                    "scheme": "",
                "host": "",
                "allowed": False,
                "sha256_pinned": False,
                "governance_valid": False,
                "license": "",
                "rights_basis": "",
                "review_status": "",
                "reviewed_by": "",
                "content_scope": "",
                "refreshable": False,
                "failures": ["source entry must be an object"],
            }
            )
            continue
        location = _source_location(item)
        parsed = urlparse(location)
        scheme = parsed.scheme
        host = (parsed.hostname or "").lower()
        sha256_pinned = _sha256_valid(item.get("sha256"))
        governance_failures = _source_governance_failures(item, index=None)
        allowed = False
        failures.extend(governance_failures)
        if not location:
            failures.append("source entry must define url or path")
        elif not scheme:
            scheme = "path"
            allowed = allow_file_urls
            if not allowed:
                failures.append("local path requires allow_file_urls=true")
            if item.get("path") and not sha256_pinned:
                failures.append("local path manifest must pin a 64-character sha256")
            if source_list_dir is not None:
                candidate = Path(location)
                if not candidate.is_absolute():
                    candidate = source_list_dir / candidate
                if not candidate.exists():
                    failures.append("local path manifest does not exist")
        elif scheme == "file":
            allowed = allow_file_urls
            if not allowed:
                failures.append("file URL requires allow_file_urls=true")
        elif scheme in {"http", "https"}:
            allowed = bool(host and host in allowed_hosts)
            if not allowed:
                failures.append(f"host is not allowlisted: {host}")
            if not sha256_pinned:
                failures.append("remote manifest must pin a 64-character sha256")
        else:
            failures.append(f"unsupported URL scheme: {scheme}")
        audits.append(
            {
                "index": index,
                "name": str(item.get("name") or ""),
                "url": location,
                "scheme": scheme,
                "host": host,
                "allowed": allowed,
                "sha256_pinned": sha256_pinned,
                "governance_valid": not governance_failures,
                "license": str(item.get("license") or ""),
                "rights_basis": str(item.get("rights_basis") or ""),
                "review_status": str(item.get("review_status") or ""),
                "reviewed_by": str(item.get("reviewed_by") or ""),
                "content_scope": str(item.get("content_scope") or ""),
                "refreshable": allowed and not failures,
                "failures": failures,
            }
        )
    return audits


def _receipt_source_audits(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    audits = []
    for item in values:
        if not isinstance(item, dict):
            continue
        audits.append(
            {
                "index": int(item.get("index") or 0),
                "name": str(item.get("name") or ""),
                "url": str(item.get("url") or ""),
                "scheme": str(item.get("scheme") or ""),
                "host": str(item.get("host") or ""),
                "allowed": bool(item.get("allowed")),
                "sha256_pinned": bool(item.get("sha256_pinned")),
                "governance_valid": bool(item.get("governance_valid")),
                "license": str(item.get("license") or ""),
                "rights_basis": str(item.get("rights_basis") or ""),
                "review_status": str(item.get("review_status") or ""),
                "reviewed_by": str(item.get("reviewed_by") or ""),
                "content_scope": str(item.get("content_scope") or ""),
                "refreshable": bool(item.get("refreshable")),
                "failures": [str(value) for value in item.get("failures", []) if str(value)],
            }
        )
    return audits


def _refresh_receipt_sources(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    sources = []
    for item in values:
        if not isinstance(item, dict):
            continue
        ingest = item.get("ingest") if isinstance(item.get("ingest"), dict) else {}
        sources.append(
            {
                "name": str(item.get("name") or ""),
                "url": str(item.get("url") or ""),
                "cache_file": str(item.get("cache_file") or ""),
                "content_hash": str(item.get("content_hash") or ""),
                "ingest_status": str(ingest.get("status") or ""),
                "ingest_output_file": str(ingest.get("output_file") or ""),
                "ingest_record_count": int(ingest.get("record_count") or 0),
                "ingest_content_hash": str(ingest.get("content_hash") or ""),
                "source_ids": sorted(str(value) for value in ingest.get("source_ids", []) if str(value)),
                "citation_policies": sorted(
                    str(value) for value in ingest.get("citation_policies", []) if str(value)
                ),
            }
        )
    return sources


def _receipt_material_sha256(receipt: Any) -> str | None:
    if not isinstance(receipt, dict) or not isinstance(receipt.get("material"), dict):
        return None
    encoded = json.dumps(receipt["material"], sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_governance_failures(item: dict[str, Any], index: int | None) -> list[str]:
    prefix = f"sources[{index}] " if index is not None else ""
    failures = []
    missing = sorted(field for field in REQUIRED_SOURCE_GOVERNANCE_FIELDS if not str(item.get(field, "")).strip())
    failures.extend(f"{prefix}{field} is required for source governance" for field in missing)
    review_status = str(item.get("review_status") or "")
    if review_status and review_status not in ALLOWED_SOURCE_REVIEW_STATUSES:
        failures.append(
            f"{prefix}review_status must be one of: {', '.join(sorted(ALLOWED_SOURCE_REVIEW_STATUSES))}"
        )
    return failures


def _sha256_valid(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(char in "0123456789abcdefABCDEF" for char in text)
