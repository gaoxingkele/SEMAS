"""Versioned registry and integrity checks for installed mingli skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

MANIFEST_PATH = Path(__file__).with_name("skill_manifest.json")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def default_skills_root() -> Path:
    """Return the configured Codex skills directory without mutating it."""
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "skills"
    return Path.home() / ".codex" / "skills"


def file_sha256(path: Path) -> str:
    """Hash one file as raw bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_sha256(path: Path) -> tuple[str, int]:
    """Hash a directory deterministically from relative paths and file bytes."""
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), len(files)


def load_skill_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Load and minimally validate the checked-in skill manifest."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "mingli-skill-manifest-v1":
        raise ValueError("unsupported mingli skill manifest schema")
    skills = payload.get("skills")
    if not isinstance(skills, list) or not skills:
        raise ValueError("mingli skill manifest must contain skills")
    identifiers = [item.get("id") for item in skills if isinstance(item, dict)]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("mingli skill manifest contains duplicate skill ids")
    return payload


def audit_skill_registry(
    manifest_path: Path = MANIFEST_PATH,
    skills_root: Path | None = None,
) -> dict[str, Any]:
    """Compare installed skill payloads with the checked-in hash pins."""
    manifest = load_skill_manifest(manifest_path)
    root = skills_root or default_skills_root()
    entries: list[dict[str, Any]] = []
    for declared in manifest["skills"]:
        skill_id = str(declared["id"])
        skill_path = root / skill_id
        if not skill_path.is_dir():
            entries.append(
                {
                    "id": skill_id,
                    "status": "missing",
                    "path": str(skill_path),
                    "expected_sha256": declared["sha256"],
                }
            )
            continue
        actual_sha256, file_count = directory_sha256(skill_path)
        skill_md = skill_path / "SKILL.md"
        skill_md_sha256 = file_sha256(skill_md) if skill_md.is_file() else None
        matches = (
            actual_sha256 == declared["sha256"]
            and skill_md_sha256 == declared["skill_md_sha256"]
            and file_count == declared["file_count"]
        )
        entries.append(
            {
                "id": skill_id,
                "status": "pass" if matches else "drift",
                "path": str(skill_path),
                "expected_sha256": declared["sha256"],
                "actual_sha256": actual_sha256,
                "expected_skill_md_sha256": declared["skill_md_sha256"],
                "actual_skill_md_sha256": skill_md_sha256,
                "expected_file_count": declared["file_count"],
                "actual_file_count": file_count,
            }
        )
    failures = [item["id"] for item in entries if item["status"] != "pass"]
    return {
        "schema_version": "mingli-skill-registry-audit-v1",
        "status": "pass" if not failures else "fail",
        "manifest_path": str(manifest_path),
        "manifest_sha256": file_sha256(manifest_path),
        "skills_root": str(root),
        "skill_count": len(entries),
        "passing_skill_count": len(entries) - len(failures),
        "failures": failures,
        "entries": entries,
    }


def agent_skill_binding_receipt(
    genome: Mapping[str, Any] | Any,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Build a receipt proving that an agent genome pins the current manifest."""
    if hasattr(genome, "model_dump"):
        payload = genome.model_dump()
    else:
        payload = dict(genome)
    meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
    declaration = meta.get("skill_manifest", {}) if isinstance(meta, dict) else {}
    bindings = meta.get("skill_bindings", {}) if isinstance(meta, dict) else {}
    relative_path = declaration.get("path") if isinstance(declaration, dict) else None
    expected_sha256 = declaration.get("sha256") if isinstance(declaration, dict) else None
    manifest_path = project_root / str(relative_path) if relative_path else None
    actual_sha256 = (
        file_sha256(manifest_path) if manifest_path and manifest_path.is_file() else None
    )
    if not relative_path:
        status = "unbound"
    elif actual_sha256 is None:
        status = "manifest_missing"
    elif actual_sha256 != expected_sha256:
        status = "manifest_drift"
    else:
        status = "bound"
    groups = ("primary", "auxiliary", "side_validation")
    bound_ids = [
        str(skill_id)
        for group in groups
        for skill_id in (bindings.get(group, []) if isinstance(bindings, dict) else [])
    ]
    material = {
        "schema_version": "agent-skill-binding-receipt-v1",
        "agent": payload.get("name"),
        "agent_version": payload.get("version"),
        "status": status,
        "manifest_path": relative_path,
        "expected_manifest_sha256": expected_sha256,
        "actual_manifest_sha256": actual_sha256,
        "bound_skill_ids": bound_ids,
        "binding_mode": bindings.get("orchestration") if isinstance(bindings, dict) else None,
        "fallback": bindings.get("fallback") if isinstance(bindings, dict) else None,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {**material, "sha256": hashlib.sha256(encoded).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit installed mingli skills")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--skills-root", type=Path)
    args = parser.parse_args()
    receipt = audit_skill_registry(args.manifest, args.skills_root)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
