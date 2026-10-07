"""Tests for paired multi-seed RSI policy selection."""

from __future__ import annotations

import json
from pathlib import Path

from china_a_share_alpha.loop.mining_policy_genome import MiningPolicyGenome
from china_a_share_alpha.loop.paired_policy_evaluation import (
    summarize_paired_evaluations,
    verify_paired_arm,
)
from china_a_share_alpha.loop.recursive_self_improve import (
    ArchiveNode,
    PolicyArchive,
    record_paired_evaluation,
)


def _entry(policy_id: str, seed: int, hold: float, *, corr_ok: bool = True) -> dict:
    return {
        "seed": seed,
        "rsi_policy_id": policy_id,
        "metrics": {"hold_sharpe": hold},
        "gates": {
            "promotion_enabled": False,
            "train_sharpe_positive": True,
            "min_cleaned_count": True,
            "max_corr_ok": corr_ok,
            "candidate_evaluation_valid": True,
            "baseline_evaluation_valid": True,
            "hold_sharpe_ok": True,
        },
    }


def test_arm_verifier_ignores_disabled_promotion_but_enforces_identity_and_gates():
    valid = verify_paired_arm(
        _entry("child", 11, 2.1),
        expected_policy_id="child",
        expected_seed=11,
    )
    wrong = verify_paired_arm(
        _entry("other", 11, 2.1, corr_ok=False),
        expected_policy_id="child",
        expected_seed=11,
    )
    assert valid["verified"]
    assert not wrong["verified"]
    assert not wrong["identity_ok"]
    assert wrong["failed_gates"] == ["max_corr_ok"]


def test_paired_summary_selects_consistent_child_improvement():
    parents = [_entry("parent", seed, hold) for seed, hold in [(1, 2.0), (2, 2.1), (3, 1.9)]]
    children = [_entry("child", seed, hold) for seed, hold in [(1, 2.1), (2, 2.2), (3, 1.95)]]
    receipt = summarize_paired_evaluations(
        parents,
        children,
        parent_id="parent",
        child_id="child",
    )
    assert receipt["selected"]
    assert receipt["summary"]["valid_pairs"] == 3
    assert receipt["summary"]["win_rate"] == 1.0
    assert receipt["summary"]["median_delta"] > 0.0


def test_paired_summary_rejects_missing_or_regressing_pairs():
    parents = [_entry("parent", seed, 2.0) for seed in (1, 2, 3)]
    children = [_entry("child", 1, 2.2), _entry("child", 2, 1.7)]
    receipt = summarize_paired_evaluations(
        parents,
        children,
        parent_id="parent",
        child_id="child",
    )
    assert not receipt["selected"]
    assert not receipt["gates"]["min_pairs"]
    assert not receipt["gates"]["all_pairs_valid"]
    assert not receipt["gates"]["worst_regression_ok"]


def test_paired_selection_controls_archive_parent_eligibility(tmp_path: Path):
    archive = PolicyArchive(tmp_path / "archive.json")
    archive.add(
        ArchiveNode(
            node_id="parent",
            parent_id=None,
            policy=MiningPolicyGenome().to_dict(),
            fitness=2.0,
            status="evaluated_valid",
            eligible_parent=True,
        )
    )
    archive.add(
        ArchiveNode(
            node_id="child",
            parent_id="parent",
            policy=MiningPolicyGenome(version=2).to_dict(),
            fitness=2.1,
            status="evaluated_valid_pair_pending",
            eligible_parent=False,
            paired_required=True,
            paired_status="pending",
            verification={"verified": True},
        )
    )
    parents = [_entry("parent", seed, 2.0) for seed in (1, 2, 3)]
    children = [_entry("child", seed, 2.1) for seed in (1, 2, 3)]
    receipt = summarize_paired_evaluations(
        parents,
        children,
        parent_id="parent",
        child_id="child",
    )
    result = record_paired_evaluation(archive, "child", receipt)
    assert result["selected"]
    assert archive.nodes["child"].eligible_parent
    persisted = json.loads((tmp_path / "archive.json").read_text(encoding="utf-8"))
    child = next(row for row in persisted["nodes"] if row["node_id"] == "child")
    assert child["paired_status"] == "selected"
