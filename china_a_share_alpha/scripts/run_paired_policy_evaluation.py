"""Run resumable paired multi-seed evaluations for an RSI policy mutation.

Each parent/child arm is isolated from the production loop, starts from the
same frozen seed library, and disables promotion writes. A completed production
child run may be reused when its policy identity and seed match exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from china_a_share_alpha.loop.mining_policy_genome import (
    MiningPolicyGenome,
    apply_policy_to_evolution_config,
    apply_policy_to_loop_config,
)
from china_a_share_alpha.loop.paired_policy_evaluation import (
    summarize_paired_evaluations,
)
from china_a_share_alpha.loop.recursive_self_improve import (
    PolicyArchive,
    record_paired_evaluation,
)
from china_a_share_alpha.scripts.run_factor_mining_loop import (
    DEFAULT_STATE,
    run_loop_iteration,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_yaml(path: Path) -> dict[str, Any]:
    return dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def prepare_arm(
    *,
    arm_dir: Path,
    policy_id: str,
    parent_id: str | None,
    policy: MiningPolicyGenome,
    seed: int,
    child_id: str,
    frozen_seed_library: Path,
    base_loop: dict[str, Any],
    base_evolution: dict[str, Any],
) -> Path:
    """Materialize an isolated, non-promoting arm and its initial state."""
    arm_dir.mkdir(parents=True, exist_ok=True)
    evolution_path = arm_dir / "evolution_config.yaml"
    loop_path = arm_dir / "loop_config.yaml"
    policy_path = arm_dir / "policy_genome.yaml"

    evolution_config = apply_policy_to_evolution_config(base_evolution, policy)
    loop_config = apply_policy_to_loop_config(base_loop, policy)
    loop_config.update(
        {
            "evolution_config": str(evolution_path.resolve()),
            "promotion_enabled": False,
            "rsi_policy_id": policy_id,
            "rsi_parent_id": parent_id,
            "rsi_mutation_surface": policy.island,
            "rsi_mutation_field": "paired_control" if policy_id != child_id else "paired_child",
            "rsi_evaluation_group_id": f"paired__{child_id}__seed_{seed}",
            "rsi_proposal_seed": int(seed),
            "rsi_evaluation_seed": int(seed),
        }
    )
    _write_yaml(evolution_path, evolution_config)
    _write_yaml(loop_path, loop_config)
    policy.to_yaml(policy_path)

    state_path = arm_dir / "state.json"
    if not state_path.exists():
        state = json.loads(json.dumps(DEFAULT_STATE))
        state["live_library_path"] = str(frozen_seed_library.resolve())
        state["state_schema_version"] = 2
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return loop_path


def completed_arm_entry(
    state_path: Path,
    *,
    policy_id: str,
    seed: int,
) -> dict[str, Any] | None:
    if not state_path.exists():
        return None
    state = json.loads(state_path.read_text(encoding="utf-8"))
    matches = [
        entry
        for entry in state.get("history") or []
        if entry.get("rsi_policy_id") == policy_id and int(entry.get("seed", -1)) == seed
    ]
    return matches[-1] if matches else None


def production_entry(
    state_path: Path,
    *,
    policy_id: str,
    seed: int,
) -> dict[str, Any] | None:
    return completed_arm_entry(state_path, policy_id=policy_id, seed=seed)


def evolution_configs_match(parent_path: Path, child_path: Path) -> bool:
    """Return true only when both arms have identical evolution semantics."""
    return _read_yaml(parent_path) == _read_yaml(child_path)


def validate_campaign_candidate(child: Any) -> None:
    """Refuse expensive pairing unless the single-run verifier passed first."""
    if not bool((child.verification or {}).get("verified")):
        raise RuntimeError(f"child failed or lacks single-run verification: {child.node_id}")
    if not child.paired_required or child.paired_status != "pending":
        raise RuntimeError(
            f"child is not awaiting paired evaluation: {child.node_id} "
            f"status={child.paired_status}"
        )


def run_arm(
    loop_path: Path,
    arm_dir: Path,
    *,
    policy_id: str,
    seed: int,
    reuse_evolution_from: Path | None = None,
) -> dict[str, Any]:
    cached = completed_arm_entry(arm_dir / "state.json", policy_id=policy_id, seed=seed)
    if cached is not None:
        return cached
    dry_run = False
    if reuse_evolution_from is not None:
        source_leaderboard = reuse_evolution_from / "factor_loop_leaderboard.csv"
        if not source_leaderboard.exists():
            raise RuntimeError(f"reusable evolution is incomplete: {reuse_evolution_from}")
        target_evolution = arm_dir / "iter_0001" / "evolution"
        if target_evolution.exists():
            raise RuntimeError(f"partial child evolution already exists: {target_evolution}")
        shutil.copytree(reuse_evolution_from, target_evolution)
        (arm_dir / "evolution_reuse_receipt.json").write_text(
            json.dumps(
                {
                    "source": str(reuse_evolution_from),
                    "leaderboard_sha256": _sha256(source_leaderboard),
                    "policy_id": policy_id,
                    "seed": seed,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        dry_run = True
    config = _read_yaml(loop_path)
    state = run_loop_iteration(config, arm_dir, dry_run=dry_run)
    entry = completed_arm_entry(arm_dir / "state.json", policy_id=policy_id, seed=seed)
    if entry is None:
        raise RuntimeError(
            f"paired arm completed without matching receipt: {policy_id} seed={seed}"
        )
    if int(state.get("iteration", 0)) != 1:
        raise RuntimeError(f"paired arm escaped isolated single-iteration state: {arm_dir}")
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Run paired RSI policy evaluation")
    parser.add_argument("--child-id", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[106, 107, 108])
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop/dgm_rsi/archive.json"),
    )
    parser.add_argument(
        "--base-loop-config",
        type=Path,
        default=Path("china_a_share_alpha/examples/factor_mining_loop_config.yaml"),
    )
    parser.add_argument(
        "--base-evolution-config",
        type=Path,
        default=Path("china_a_share_alpha/examples/factor_mining_loop_evolution_config.yaml"),
    )
    parser.add_argument("--baseline-library", type=Path, required=True)
    parser.add_argument(
        "--production-state",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop/state.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop/dgm_rsi/paired"),
    )
    parser.add_argument("--no-production-reuse", action="store_true")
    args = parser.parse_args()

    archive = PolicyArchive(args.archive)
    if args.child_id not in archive.nodes:
        raise KeyError(args.child_id)
    child = archive.nodes[args.child_id]
    if not child.parent_id or child.parent_id not in archive.nodes:
        raise RuntimeError(f"paired evaluation requires an archived parent: {args.child_id}")
    validate_campaign_candidate(child)
    parent = archive.nodes[child.parent_id]
    child_policy = MiningPolicyGenome.from_dict(child.policy)
    parent_policy = MiningPolicyGenome.from_dict(parent.policy)

    campaign_dir = args.output_dir / args.child_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    frozen_library = campaign_dir / "frozen_seed_library.csv"
    if not frozen_library.exists():
        shutil.copyfile(args.baseline_library, frozen_library)
    elif _sha256(frozen_library) != _sha256(args.baseline_library):
        raise RuntimeError("baseline library changed after paired campaign initialization")

    base_loop = _read_yaml(args.base_loop_config)
    base_evolution = _read_yaml(args.base_evolution_config)
    manifest = {
        "schema": "rsi_paired_policy_campaign_v1",
        "child_id": child.node_id,
        "parent_id": parent.node_id,
        "seeds": sorted(set(args.seeds)),
        "frozen_seed_library": str(frozen_library),
        "frozen_seed_library_sha256": _sha256(frozen_library),
        "base_loop_config_sha256": _sha256(args.base_loop_config),
        "base_evolution_config_sha256": _sha256(args.base_evolution_config),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (campaign_dir / "campaign_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    parent_entries: list[dict[str, Any]] = []
    child_entries: list[dict[str, Any]] = []

    for seed in sorted(set(args.seeds)):
        seed_dir = campaign_dir / f"seed_{seed:04d}"
        parent_dir = seed_dir / "parent"
        child_dir = seed_dir / "child"
        parent_loop = prepare_arm(
            arm_dir=parent_dir,
            policy_id=parent.node_id,
            parent_id=parent.parent_id,
            policy=parent_policy,
            seed=seed,
            child_id=child.node_id,
            frozen_seed_library=frozen_library,
            base_loop=base_loop,
            base_evolution=base_evolution,
        )
        child_loop = prepare_arm(
            arm_dir=child_dir,
            policy_id=child.node_id,
            parent_id=parent.node_id,
            policy=child_policy,
            seed=seed,
            child_id=child.node_id,
            frozen_seed_library=frozen_library,
            base_loop=base_loop,
            base_evolution=base_evolution,
        )
        child_entry = None
        if not args.no_production_reuse:
            child_entry = production_entry(
                args.production_state,
                policy_id=child.node_id,
                seed=seed,
            )
            if child_entry is not None:
                (child_dir / "production_reuse_receipt.json").write_text(
                    json.dumps(child_entry, indent=2, ensure_ascii=False), encoding="utf-8"
                )
        configs_match = evolution_configs_match(
            parent_dir / "evolution_config.yaml",
            child_dir / "evolution_config.yaml",
        )
        parent_reuse_source = None
        if child_entry is not None and configs_match:
            candidate_source = Path(str(child_entry.get("evolution_dir") or ""))
            if (candidate_source / "factor_loop_leaderboard.csv").exists():
                parent_reuse_source = candidate_source
        parent_entry = run_arm(
            parent_loop,
            parent_dir,
            policy_id=parent.node_id,
            seed=seed,
            reuse_evolution_from=parent_reuse_source,
        )
        parent_entries.append(parent_entry)

        if child_entry is None:
            reuse_source = None
            if configs_match:
                reuse_source = parent_dir / "iter_0001" / "evolution"
            child_entry = run_arm(
                child_loop,
                child_dir,
                policy_id=child.node_id,
                seed=seed,
                reuse_evolution_from=reuse_source,
            )
        child_entries.append(child_entry)

    receipt = summarize_paired_evaluations(
        parent_entries,
        child_entries,
        parent_id=parent.node_id,
        child_id=child.node_id,
    )
    receipt.update(
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "frozen_seed_library": str(frozen_library),
            "frozen_seed_library_sha256": _sha256(frozen_library),
            "base_loop_config_sha256": _sha256(args.base_loop_config),
            "base_evolution_config_sha256": _sha256(args.base_evolution_config),
        }
    )
    receipt_path = campaign_dir / "paired_evaluation_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    selection = record_paired_evaluation(archive, child.node_id, receipt)
    print(json.dumps({"receipt": str(receipt_path), **selection}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
