"""Tests for isolated paired-policy campaign preparation and resume."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from china_a_share_alpha.loop.mining_policy_genome import MiningPolicyGenome
from china_a_share_alpha.loop.recursive_self_improve import ArchiveNode
from china_a_share_alpha.scripts.run_factor_mining_loop import exclusive_output_lock
from china_a_share_alpha.scripts.run_paired_policy_evaluation import (
    completed_arm_entry,
    evolution_configs_match,
    prepare_arm,
    validate_campaign_candidate,
)


def test_prepare_arm_freezes_seed_identity_and_disables_promotion(tmp_path: Path):
    library = tmp_path / "seed.csv"
    library.write_text("expression\nclose\n", encoding="utf-8")
    loop_path = prepare_arm(
        arm_dir=tmp_path / "arm",
        policy_id="child",
        parent_id="parent",
        policy=MiningPolicyGenome(version=2),
        seed=17,
        child_id="child",
        frozen_seed_library=library,
        base_loop={"data_config": "data.yaml", "evolution_config": "old.yaml"},
        base_evolution={"population_size": 5},
    )
    config = yaml.safe_load(loop_path.read_text(encoding="utf-8"))
    state = json.loads((tmp_path / "arm" / "state.json").read_text(encoding="utf-8"))
    assert config["promotion_enabled"] is False
    assert config["rsi_policy_id"] == "child"
    assert config["rsi_evaluation_seed"] == 17
    assert config["rsi_evaluation_group_id"] == "paired__child__seed_17"
    assert Path(state["live_library_path"]) == library.resolve()
    assert state["history"] == []


def test_completed_arm_entry_requires_matching_policy_and_seed(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "history": [
                    {"rsi_policy_id": "child", "seed": 17, "metrics": {}},
                    {"rsi_policy_id": "other", "seed": 18, "metrics": {}},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert completed_arm_entry(state_path, policy_id="child", seed=17) is not None
    assert completed_arm_entry(state_path, policy_id="child", seed=18) is None


def test_campaign_requires_single_valid_pair_pending_child():
    valid = ArchiveNode(
        node_id="child",
        parent_id="parent",
        policy=MiningPolicyGenome().to_dict(),
        fitness=2.0,
        paired_required=True,
        paired_status="pending",
        verification={"verified": True},
    )
    validate_campaign_candidate(valid)
    valid.verification = {"verified": False}
    try:
        validate_campaign_candidate(valid)
    except RuntimeError as exc:
        assert "single-run verification" in str(exc)
    else:
        raise AssertionError("invalid single-run child entered paired campaign")


def test_output_lock_rejects_duplicate_iteration_writer(tmp_path: Path):
    with exclusive_output_lock(tmp_path):
        try:
            with exclusive_output_lock(tmp_path):
                pass
        except RuntimeError as exc:
            assert "already locked" in str(exc)
        else:
            raise AssertionError("output lock allowed concurrent writers")
    assert not (tmp_path / ".factor_mining_iteration.lock").exists()


def test_evolution_reuse_requires_semantically_identical_configs(tmp_path: Path):
    left = tmp_path / "left.yaml"
    right = tmp_path / "right.yaml"
    left.write_text("population_size: 40\nparent_mode: dag_neighbors\n", encoding="utf-8")
    right.write_text("parent_mode: dag_neighbors\npopulation_size: 40\n", encoding="utf-8")
    assert evolution_configs_match(left, right)
    right.write_text("parent_mode: global\npopulation_size: 40\n", encoding="utf-8")
    assert not evolution_configs_match(left, right)
