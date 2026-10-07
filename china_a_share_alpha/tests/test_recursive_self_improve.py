"""Tests for DGM-style Recursive Self-Improvement mining-policy archive."""

from __future__ import annotations

import json
import random
from pathlib import Path

from china_a_share_alpha.loop.mining_policy_genome import ISLANDS, MiningPolicyGenome
from china_a_share_alpha.loop.recursive_self_improve import (
    ArchiveNode,
    PolicyArchive,
    audit_archive_against_state,
    diagnose_iteration,
    exclusive_proposal_lock,
    mutate_policy,
    policy_diff,
    propose_child,
    record_child_evaluation,
    verify_iteration_entry,
)


def test_diagnose_flat_hold_and_aggressive_dedup():
    entry = {
        "iteration": 53,
        "promoted": False,
        "n_cleaned": 20,
        "n_deduped": 15,
        "metrics": {"hold_sharpe": 1.726, "pool_ic": 0.012},
        "promotion_baseline": {"sharpe": 2.154},
        "gates": {"max_corr_ok": True},
    }
    d = diagnose_iteration(entry)
    assert "not_promoted" in d.codes
    assert "hold_regression" in d.codes
    assert "aggressive_dedup" in d.codes


def test_diagnose_near_miss_promote():
    entry = {
        "promoted": False,
        "n_cleaned": 18,
        "n_deduped": 18,
        "metrics": {"hold_sharpe": 2.306, "pool_ic": 0.011},
        "promotion_baseline": {"sharpe": 2.292},
        "gates": {"max_corr_ok": True},
    }
    d = diagnose_iteration(entry)
    assert "near_miss_promote" in d.codes
    assert "hold_regression" not in d.codes


def test_mutate_uses_single_surface_one_field():
    policy = MiningPolicyGenome(semantic_dedup_corr_threshold=0.95, keep_diversity_slots=0)
    diagnosis = diagnose_iteration(
        {
            "promoted": False,
            "n_cleaned": 19,
            "n_deduped": 12,
            "metrics": {"hold_sharpe": 2.056, "pool_ic": 0.008},
            "promotion_baseline": {"sharpe": 2.056},
            "gates": {"max_corr_ok": False},
        }
    )
    nxt = mutate_policy(policy, diagnosis, rng=random.Random(0))
    assert nxt.version == policy.version + 1
    assert nxt.island in ISLANDS
    assert nxt.notes.startswith("surface=")
    assert "field=" in nxt.notes
    # Anti-collapse: exactly one functional field changes; examiner stays frozen.
    assert len(policy_diff(policy, nxt)) == 1
    assert nxt.promote_hold_sharpe_threshold == policy.promote_hold_sharpe_threshold
    assert nxt.max_selection_correlation_gate == policy.max_selection_correlation_gate
    assert "relax_dedup+diversity,expand_search+dag,shrink_top_n" not in nxt.notes


def test_mutate_never_evolves_examiner_gates():
    policy = MiningPolicyGenome(max_selection_correlation_gate=0.7, island="search_budget")
    diagnosis = diagnose_iteration(
        {
            "promoted": False,
            "n_cleaned": 18,
            "n_deduped": 16,
            "metrics": {"hold_sharpe": 2.10, "pool_ic": 0.012},
            "promotion_baseline": {"sharpe": 2.29},
            "gates": {"max_corr_ok": False},
        }
    )
    for seed in range(40):
        nxt = mutate_policy(policy, diagnosis, rng=random.Random(seed))
        assert nxt.max_selection_correlation_gate == 0.7
        assert nxt.promote_hold_sharpe_threshold == 0.03
        assert nxt.island in ISLANDS
        assert nxt.island != "gate_relax"


def test_archive_sample_prefers_fit_underexplored(tmp_path: Path):
    path = tmp_path / "archive.json"
    archive = PolicyArchive(path)
    archive.add(
        ArchiveNode(
            node_id="a",
            parent_id=None,
            policy=MiningPolicyGenome(island="search_budget").to_dict(),
            fitness=2.0,
            n_children=0,
            eligible_parent=True,
            status="evaluated_valid",
        )
    )
    archive.add(
        ArchiveNode(
            node_id="b",
            parent_id="a",
            policy=MiningPolicyGenome(version=2, island="diversity").to_dict(),
            fitness=0.5,
            n_children=5,
            eligible_parent=True,
            status="evaluated_valid",
        )
    )
    rng = random.Random(1)
    picks = [archive.sample_parent(rng).node_id for _ in range(80)]
    # Fitness mode still exists; underexplored high-fit parent should appear often.
    assert picks.count("a") >= picks.count("b")


def test_archive_sample_covers_multiple_modes(tmp_path: Path):
    path = tmp_path / "archive.json"
    archive = PolicyArchive(path)
    for i, island in enumerate(ISLANDS):
        archive.add(
            ArchiveNode(
                node_id=f"n{i}",
                parent_id=None,
                policy=MiningPolicyGenome(island=island, version=i + 1).to_dict(),
                fitness=1.0 + 0.1 * i,
                n_children=i,
                eligible_parent=True,
                status="evaluated_valid",
            )
        )
    rng = random.Random(7)
    picks = {archive.sample_parent(rng).node_id for _ in range(60)}
    assert len(picks) >= 3


def test_archive_normalizes_legacy_island_names(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="legacy",
            parent_id=None,
            policy=MiningPolicyGenome(island="search_budget").to_dict()
            | {"island": "gate_relax"},
            fitness=2.0,
            eligible_parent=True,
            status="evaluated_valid",
            mutation_surface="gate_relax",
            mutation_field="top_n",
            notes="surface=diversity,field=top_n,8->7",
        )
    )
    assert PolicyArchive._normalized_island(archive.nodes["legacy"]) == "diversity"
    assert archive.island_counts()["diversity"] == 1
    # Nodes without an explicit mutation_surface do not inflate island mass.
    archive.add(
        ArchiveNode(
            node_id="no_mut",
            parent_id=None,
            policy=MiningPolicyGenome(island="search_budget").to_dict(),
            fitness=1.0,
            eligible_parent=True,
            status="evaluated_valid",
        )
    )
    assert archive.island_counts()["search_budget"] == 0


def test_mutate_covers_all_islands_over_seeds():
    policy = MiningPolicyGenome()
    diagnosis = diagnose_iteration(
        {
            "promoted": False,
            "n_cleaned": 10,
            "n_deduped": 10,
            "metrics": {"hold_sharpe": 2.0, "pool_ic": 0.02},
            "promotion_baseline": {"sharpe": 2.0},
            "gates": {"max_corr_ok": True},
        }
    )
    seen: set[str] = set()
    for seed in range(120):
        nxt = mutate_policy(policy, diagnosis, rng=random.Random(seed))
        seen.add(nxt.island)
    assert seen == set(ISLANDS)


def _valid_entry(policy_id: str | None, iteration: int = 50) -> dict:
    return {
        "iteration": iteration,
        "seed": 7,
        "rsi_policy_id": policy_id,
        "promoted": False,
        "improved": False,
        "n_merged": 20,
        "n_cleaned": 12,
        "n_deduped": 10,
        "metrics": {"hold_sharpe": 2.1, "pool_ic": 0.012},
        "promotion_baseline": {"sharpe": 2.0},
        "gates": {
            "promotion_enabled": True,
            "train_sharpe_positive": True,
            "min_cleaned_count": True,
            "max_corr_ok": True,
            "candidate_evaluation_valid": True,
            "baseline_evaluation_valid": True,
            "hold_sharpe_ok": True,
        },
    }


def test_invalid_gate_cannot_become_parent(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="valid",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=1.0,
            status="evaluated_valid",
            eligible_parent=True,
        )
    )
    archive.add(
        ArchiveNode(
            node_id="invalid",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=9.0,
            status="evaluated_invalid",
            eligible_parent=False,
        )
    )
    picks = {archive.sample_parent(random.Random(i)).node_id for i in range(20)}
    assert picks == {"valid"}
    assert archive.best().node_id == "valid"


def test_pair_pending_node_blocks_next_proposal(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="child",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=2.1,
            status="evaluated_valid_pair_pending",
            eligible_parent=False,
            paired_required=True,
            paired_status="pending",
        )
    )
    assert [node.node_id for node in archive.pending()] == ["child"]


def test_verifier_rejects_identity_gate_and_examiner_changes():
    baseline = MiningPolicyGenome()
    changed_examiner = MiningPolicyGenome(max_selection_correlation_gate=0.9)
    entry = _valid_entry("other")
    entry["gates"]["max_corr_ok"] = False
    result = verify_iteration_entry(
        entry,
        expected_policy_id="child",
        policy=changed_examiner,
        evaluator_baseline=baseline,
    )
    assert not result["verified"]
    assert not result["identity_ok"]
    assert not result["frozen_evaluator_match"]
    assert result["failed_gates"] == ["max_corr_ok"]


def test_record_child_requires_explicit_policy_identity(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="policy_0000",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=2.0,
            status="bootstrap_verified",
            eligible_parent=True,
        )
    )
    archive.add(
        ArchiveNode(
            node_id="policy_0001",
            parent_id="policy_0000",
            policy=MiningPolicyGenome(version=2).to_dict(),
            fitness=0.0,
        )
    )
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"history": [_valid_entry("wrong-policy")]}), encoding="utf-8"
    )
    result = record_child_evaluation(archive, "policy_0001", state_path)
    assert not result["eligible_parent"]
    assert result["fitness"] == 0.0
    assert archive.nodes["policy_0001"].status == "evaluated_invalid"


def test_single_valid_child_waits_for_required_paired_evaluation(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="policy_0000",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=2.0,
            status="bootstrap_verified",
            eligible_parent=True,
        )
    )
    archive.add(
        ArchiveNode(
            node_id="policy_0001",
            parent_id="policy_0000",
            policy=MiningPolicyGenome(version=2).to_dict(),
            fitness=0.0,
            paired_required=True,
            paired_status="pending",
        )
    )
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"history": [_valid_entry("policy_0001")]}), encoding="utf-8"
    )
    result = record_child_evaluation(archive, "policy_0001", state_path)
    assert result["single_evaluation_verified"]
    assert not result["eligible_parent"]
    assert result["status"] == "evaluated_valid_pair_pending"
    assert archive.pending()[0].node_id == "policy_0001"


def test_legacy_archive_audit_invalidates_failed_gates(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="policy_0000",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=2.0,
        )
    )
    archive.add(
        ArchiveNode(
            node_id="policy_0001",
            parent_id="policy_0000",
            policy=MiningPolicyGenome(version=2).to_dict(),
            fitness=9.0,
        )
    )
    failed = _valid_entry(None)
    failed["gates"]["max_corr_ok"] = False
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"history": [failed]}), encoding="utf-8")
    receipt = audit_archive_against_state(archive, state_path, baseline_iteration=49)
    assert receipt["counts"]["invalid"] == 1
    assert archive.nodes["policy_0000"].eligible_parent
    assert not archive.nodes["policy_0001"].eligible_parent
    assert archive.nodes["policy_0001"].fitness == 0.0


def test_proposal_uses_sampled_parent_receipt_and_writes_identity(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    parent_entry = _valid_entry("policy_0000", iteration=49)
    parent_entry["n_cleaned"] = 20
    parent_entry["n_deduped"] = 10
    archive.add(
        ArchiveNode(
            node_id="policy_0000",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=2.0,
            status="bootstrap_verified",
            eligible_parent=True,
            evaluation_receipt=parent_entry,
        )
    )
    latest = _valid_entry(None, iteration=99)
    latest["gates"]["max_corr_ok"] = False
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"iteration": 99, "history": [latest], "best_hold_sharpe": 2.0}),
        encoding="utf-8",
    )
    loop_config = tmp_path / "loop.yaml"
    loop_config.write_text("evolution_config: old.yaml\n", encoding="utf-8")
    evolution_config = tmp_path / "evolution.yaml"
    evolution_config.write_text("population_size: 25\n", encoding="utf-8")
    receipt = propose_child(
        archive,
        state_path=state_path,
        base_loop_config=loop_config,
        base_evolution_config=evolution_config,
        work_dir=tmp_path / "work",
        seed=11,
    )
    # Diagnosis follows the latest inner-loop outcome (corr gate), not parent receipt.
    assert receipt["diagnosis"]["detail"]["iteration"] == 99
    assert "selection_corr_gate" in receipt["diagnosis"]["codes"]
    assert receipt["expected_iteration"] == 100
    assert receipt["proposal_seed"] == 11
    assert receipt["evaluation_seed"] == 11
    assert receipt["evaluation_group_id"].endswith("seed_11")
    generated = (tmp_path / "work" / "active" / "loop_config.yaml").read_text(
        encoding="utf-8"
    )
    assert "rsi_policy_id: policy_0001" in generated
    assert "rsi_parent_id: policy_0000" in generated
    assert archive.nodes["policy_0001"].status == "proposed"
    assert not archive.nodes["policy_0001"].eligible_parent
    assert archive.nodes["policy_0001"].paired_required
    assert archive.nodes["policy_0001"].paired_status == "pending"


def test_archive_identity_and_proposal_lock_are_exclusive(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    node = ArchiveNode(
        node_id="policy_0000",
        parent_id=None,
        policy=MiningPolicyGenome().to_dict(),
        fitness=2.0,
    )
    archive.add(node)
    try:
        archive.add(node)
    except RuntimeError as exc:
        assert "identity is immutable" in str(exc)
    else:
        raise AssertionError("duplicate archive identity was overwritten")

    with exclusive_proposal_lock(archive.path):
        try:
            with exclusive_proposal_lock(archive.path):
                pass
        except RuntimeError as exc:
            assert "proposal already in progress" in str(exc)
        else:
            raise AssertionError("proposal lock allowed concurrent allocation")
