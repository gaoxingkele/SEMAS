"""Tests for the versioned mingli skill registry and BaZi v2 binding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from examples.mingli_5agents.run_demo import bootstrap_repo
from examples.mingli_5agents.skill_registry import (
    MANIFEST_PATH,
    agent_skill_binding_receipt,
    audit_skill_registry,
    directory_sha256,
    load_skill_manifest,
)


def test_checked_in_manifest_covers_current_mingli_skill_set():
    manifest = load_skill_manifest()
    skill_ids = {item["id"] for item in manifest["skills"]}
    assert len(skill_ids) == 12
    assert set(manifest["required_bazi_primary_skills"]) <= skill_ids
    assert {
        "mingli-jicheng",
        "mingli-xingping-huihai",
        "mingli-ziwei",
        "mingli-xingzuo",
    } <= skill_ids
    assert all(len(item["sha256"]) == 64 for item in manifest["skills"])
    assert manifest["payload_policy"]["canonical_payload_in_repository"] is False


def test_registry_audit_detects_pass_and_drift(tmp_path: Path):
    skills_root = tmp_path / "skills"
    skill_path = skills_root / "mingli-probe"
    skill_path.mkdir(parents=True)
    skill_md = skill_path / "SKILL.md"
    skill_md.write_text("---\nname: mingli-probe\n---\n", encoding="utf-8")
    directory_hash, file_count = directory_sha256(skill_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "mingli-skill-manifest-v1",
                "skills": [
                    {
                        "id": "mingli-probe",
                        "file_count": file_count,
                        "sha256": directory_hash,
                        "skill_md_sha256": hashlib.sha256(skill_md.read_bytes()).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert audit_skill_registry(manifest_path, skills_root)["status"] == "pass"
    skill_md.write_text("changed", encoding="utf-8")
    receipt = audit_skill_registry(manifest_path, skills_root)
    assert receipt["status"] == "fail"
    assert receipt["failures"] == ["mingli-probe"]


def test_bazi_v2_pins_current_manifest_and_bootstraps_as_latest(tmp_path: Path):
    repo = bootstrap_repo(tmp_path)
    genome = repo.load_agent("bazi_analyst")
    assert genome.version == 2
    assert genome.parent_version == 1
    assert set(genome.meta["skill_bindings"]["primary"]) == set(
        load_skill_manifest()["required_bazi_primary_skills"]
    )
    receipt = agent_skill_binding_receipt(genome)
    assert receipt["status"] == "bound"
    assert (
        receipt["actual_manifest_sha256"] == hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    )
    assert len(receipt["bound_skill_ids"]) == 9
