"""Darwin-Gödel-style Recursive Self-Improvement for factor mining policies.

Outer loop maintains an **archive** of mining-policy genomes. Each round:
1. Sample a parent from the archive (fitness × underexplored bonus).
2. Self-modify the policy from the parent's failure / performance receipt.
3. Materialize patched loop/evolution YAML.
4. (Caller) runs one inner factor-mining iteration and records hold Sharpe.

This is RSI = Recursive Self-Improvement, NOT Relative Strength Index.

[source: arXiv:2505.22954 Darwin Gödel Machine]
[source: arXiv:2603.19461 HyperAgents / DGM-H]
[source: arXiv:2410.04444 Gödel Agent]
[source: SEMAS_SELF_UPGRADE_DESIGN.md]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from china_a_share_alpha.loop.mining_policy_genome import (
    ISLANDS,
    LEGACY_ISLAND_MAP,
    MUTATION_FIELDS,
    MiningPolicyGenome,
    apply_policy_to_evolution_config,
    apply_policy_to_loop_config,
)


@dataclass
class ArchiveNode:
    node_id: str
    parent_id: str | None
    policy: dict[str, Any]
    fitness: float  # feasible hold Sharpe; 0.0 for proposed/invalid nodes
    n_children: int = 0
    diagnosis_codes: list[str] = field(default_factory=list)
    created_at: str = ""
    notes: str = ""
    status: str = "proposed"
    eligible_parent: bool = False
    source_iteration: int | None = None
    evaluation_receipt: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    mutation_surface: str = ""
    mutation_field: str = ""
    mutation_before: Any = None
    mutation_after: Any = None
    paired_required: bool = False
    paired_status: str = "not_required"
    paired_evaluation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArchiveNode":
        return cls(
            node_id=str(data["node_id"]),
            parent_id=data.get("parent_id"),
            policy=dict(data["policy"]),
            fitness=float(data.get("fitness", 0.0)),
            n_children=int(data.get("n_children", 0)),
            diagnosis_codes=list(data.get("diagnosis_codes") or []),
            created_at=str(data.get("created_at") or ""),
            notes=str(data.get("notes") or ""),
            status=str(data.get("status") or "legacy_unverified"),
            eligible_parent=bool(data.get("eligible_parent", False)),
            source_iteration=(
                int(data["source_iteration"])
                if data.get("source_iteration") is not None
                else None
            ),
            evaluation_receipt=dict(data.get("evaluation_receipt") or {}),
            verification=dict(data.get("verification") or {}),
            mutation_surface=str(data.get("mutation_surface") or ""),
            mutation_field=str(data.get("mutation_field") or ""),
            mutation_before=data.get("mutation_before"),
            mutation_after=data.get("mutation_after"),
            paired_required=bool(
                data.get("paired_required", data.get("status") == "proposed")
            ),
            paired_status=str(
                data.get(
                    "paired_status",
                    "pending" if data.get("status") == "proposed" else "grandfathered",
                )
            ),
            paired_evaluation=dict(data.get("paired_evaluation") or {}),
        )


@dataclass
class FailureDiagnosis:
    codes: list[str]
    detail: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"codes": self.codes, "detail": self.detail}


class PolicyArchive:
    """Open-ended archive of mining policies (DGM stepping stones)."""

    def __init__(self, path: Path):
        self.path = path
        self.nodes: dict[str, ArchiveNode] = {}
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw.get("nodes", []):
                node = ArchiveNode.from_dict(item)
                self.nodes[node.node_id] = node

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "dgm_mining_policy_archive_v2",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }
        temp_path = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        temp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        temp_path.replace(self.path)

    def add(self, node: ArchiveNode) -> None:
        if node.node_id in self.nodes:
            raise RuntimeError(f"archive node identity is immutable: {node.node_id}")
        self.nodes[node.node_id] = node
        if node.parent_id and node.parent_id in self.nodes:
            self.nodes[node.parent_id].n_children += 1
        self.save()
    def record_evaluation(
        self,
        node_id: str,
        *,
        fitness: float,
        feasible: bool,
        source_iteration: int,
        receipt: dict[str, Any],
        verification: dict[str, Any],
    ) -> None:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        node = self.nodes[node_id]
        node.fitness = float(fitness) if feasible else 0.0
        if feasible and node.paired_required:
            node.status = "evaluated_valid_pair_pending"
            node.eligible_parent = False
            node.paired_status = "pending"
        else:
            node.status = "evaluated_valid" if feasible else "evaluated_invalid"
            node.eligible_parent = bool(feasible)
            if not feasible and node.paired_required:
                node.paired_status = "single_invalid"
        node.source_iteration = int(source_iteration)
        node.evaluation_receipt = dict(receipt)
        node.verification = dict(verification)
        self.save()

    def pending(self) -> list[ArchiveNode]:
        return [
            node
            for node in self.nodes.values()
            if node.status == "proposed"
            or (node.paired_required and node.paired_status == "pending")
        ]

    @staticmethod
    def _normalized_island(node: ArchiveNode) -> str:
        raw = str(
            node.mutation_surface
            or (node.policy or {}).get("island")
            or "search_budget"
        )
        island = LEGACY_ISLAND_MAP.get(raw, raw)
        return island if island in ISLANDS else "search_budget"

    def island_counts(self, *, recent_only: bool = False, recent_n: int = 12) -> dict[str, int]:
        """Count mutation surfaces. Prefer explicit mutation_surface over inherited island."""
        counts = {name: 0 for name in ISLANDS}
        nodes = list(self.nodes.values())
        if recent_only:
            numbered = []
            for node in nodes:
                match = re.search(r"(\d+)$", node.node_id)
                if match is not None:
                    numbered.append((int(match.group(1)), node))
            numbered.sort(key=lambda item: item[0])
            nodes = [node for _, node in numbered[-recent_n:]]
        for node in nodes:
            # Only count nodes that actually mutated under the multi-surface regime.
            if not node.mutation_surface and "surface=" not in (node.notes or ""):
                continue
            counts[self._normalized_island(node)] += 1
        return counts

    def recent_mutation_keys(self, n: int = 8) -> list[tuple[str, str]]:
        numbered = []
        for node in self.nodes.values():
            match = re.search(r"(\d+)$", node.node_id)
            if match is None:
                continue
            surface = str(node.mutation_surface or "")
            field = str(node.mutation_field or "")
            if not surface:
                continue
            numbered.append((int(match.group(1)), (surface, field)))
        numbered.sort(key=lambda item: item[0])
        return [key for _, key in numbered[-n:]]

    def sample_parent(self, rng: random.Random) -> ArchiveNode:
        """Mixture sampling to avoid fitness-only collapse.

        Modes (default weights):
          - fitness: hold-Sharpe mass
          - underexplored: 1/(1+n_children)
          - novelty: distance of policy fingerprint from archive centroid
          - uniform: pure random

        [source: arXiv:2505.22954 §Population-based Open-ended Exploration]
        """
        if not self.nodes:
            raise RuntimeError("empty policy archive")
        nodes = [node for node in self.nodes.values() if node.eligible_parent]
        if not nodes:
            raise RuntimeError("archive has no verified feasible parent nodes")
        mode = rng.choices(
            ["fitness", "underexplored", "novelty", "uniform"],
            weights=[0.35, 0.25, 0.25, 0.15],
            k=1,
        )[0]
        if mode == "uniform" or len(nodes) == 1:
            return rng.choice(nodes)

        fingerprints = []
        for node in nodes:
            try:
                fingerprints.append(MiningPolicyGenome.from_dict(node.policy).fingerprint())
            except Exception:  # noqa: BLE001
                fingerprints.append(("?",))

        # Numeric projection of fingerprint for novelty distance.
        def _vec(fp: tuple[Any, ...]) -> list[float]:
            out: list[float] = []
            for item in fp:
                if isinstance(item, (int, float)):
                    out.append(float(item))
                elif isinstance(item, str):
                    out.append(float(sum(ord(c) for c in item) % 97) / 97.0)
                else:
                    out.append(0.0)
            return out

        vectors = [_vec(fp) for fp in fingerprints]
        dim = max(len(v) for v in vectors)
        vectors = [v + [0.0] * (dim - len(v)) for v in vectors]
        centroid = [sum(row[i] for row in vectors) / len(vectors) for i in range(dim)]

        weights: list[float] = []
        for node, vec in zip(nodes, vectors):
            fit = max(0.05, float(node.fitness))
            explore = 1.0 / (1.0 + float(node.n_children))
            novelty = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, centroid))) + 0.05
            # Soft penalty if island already over-represented among high-fitness nodes.
            island = self._normalized_island(node)
            island_mass = sum(
                1
                for other in nodes
                if self._normalized_island(other) == island
                and float(other.fitness) >= 2.0
            )
            island_penalty = 1.0 / (1.0 + 0.35 * island_mass)
            if mode == "fitness":
                weights.append(fit * explore * island_penalty)
            elif mode == "underexplored":
                weights.append(explore * (0.5 + 0.5 * fit) * island_penalty)
            else:  # novelty
                weights.append(novelty * explore * island_penalty)

        total = sum(weights)
        if total <= 0:
            return rng.choice(nodes)
        pick = rng.random() * total
        cum = 0.0
        for node, w in zip(nodes, weights):
            cum += w
            if pick <= cum:
                return node
        return nodes[-1]

    def best(self, *, eligible_only: bool = True) -> ArchiveNode | None:
        nodes = (
            [node for node in self.nodes.values() if node.eligible_parent]
            if eligible_only
            else list(self.nodes.values())
        )
        if not nodes:
            return None
        return max(nodes, key=lambda n: n.fitness)


@contextmanager
def exclusive_proposal_lock(archive_path: Path):
    """Serialize child-ID allocation and active-config materialization."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = archive_path.with_name(f".{archive_path.name}.proposal.lock")
    payload = json.dumps(
        {
            "pid": os.getpid(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "archive": str(archive_path.resolve()),
        },
        ensure_ascii=False,
    )
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        owner = lock_path.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(f"RSI proposal already in progress: {owner}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        yield lock_path
    finally:
        lock_path.unlink(missing_ok=True)


def diagnose_iteration(
    entry: dict[str, Any], state: dict[str, Any] | None = None
) -> FailureDiagnosis:
    codes: list[str] = []
    metrics = entry.get("metrics") or {}
    gates = entry.get("gates") or {}
    detail: dict[str, Any] = {
        "iteration": entry.get("iteration"),
        "promoted": entry.get("promoted"),
        "hold_sharpe": metrics.get("hold_sharpe"),
        "pool_ic": metrics.get("pool_ic"),
        "n_merged": entry.get("n_merged"),
        "n_cleaned": entry.get("n_cleaned"),
        "n_deduped": entry.get("n_deduped"),
    }

    if not bool(entry.get("promoted")):
        codes.append("not_promoted")

    baseline = None
    if state is not None:
        baseline = state.get("best_hold_sharpe")
    promo_base = entry.get("promotion_baseline") or {}
    if isinstance(promo_base, dict) and promo_base.get("sharpe") is not None:
        baseline = promo_base.get("sharpe")
    detail["baseline_hold_sharpe"] = baseline

    hold = metrics.get("hold_sharpe")
    if hold is not None and baseline is not None:
        delta = float(hold) - float(baseline)
        detail["hold_delta"] = delta
        if abs(delta) < 0.01:
            codes.append("flat_hold")
        elif delta < -0.05:
            codes.append("hold_regression")
        elif delta >= 0.03:
            codes.append("hold_improved")
        elif delta > 0:
            codes.append("near_miss_promote")

    n_cleaned = entry.get("n_cleaned")
    n_deduped = entry.get("n_deduped")
    if (
        isinstance(n_cleaned, int)
        and isinstance(n_deduped, int)
        and n_cleaned >= 4
        and n_deduped + 2 <= n_cleaned
    ):
        codes.append("aggressive_dedup")

    if gates.get("max_corr_ok") is False:
        codes.append("selection_corr_gate")

    pool_ic = metrics.get("pool_ic")
    if pool_ic is not None and float(pool_ic) < 0.01:
        codes.append("low_pool_ic")

    if bool(entry.get("promoted")) and "hold_improved" in codes:
        codes.append("success")
    elif not codes:
        codes.append("neutral")

    return FailureDiagnosis(codes=sorted(set(codes)), detail=detail)


REQUIRED_FEASIBILITY_GATES: tuple[str, ...] = (
    "promotion_enabled",
    "train_sharpe_positive",
    "min_cleaned_count",
    "max_corr_ok",
    "candidate_evaluation_valid",
    "baseline_evaluation_valid",
    "hold_sharpe_ok",
)

FROZEN_EVALUATOR_FIELDS: tuple[str, ...] = (
    "promote_hold_sharpe_threshold",
    "max_selection_correlation_gate",
)


def compact_iteration_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Keep enough evidence for diagnosis without copying large backtest payloads."""
    metrics = entry.get("metrics") or {}
    return {
        "iteration": entry.get("iteration"),
        "timestamp": entry.get("timestamp"),
        "seed": entry.get("seed"),
        "rsi_policy_id": entry.get("rsi_policy_id"),
        "rsi_parent_id": entry.get("rsi_parent_id"),
        "rsi_mutation_surface": entry.get("rsi_mutation_surface"),
        "rsi_mutation_field": entry.get("rsi_mutation_field"),
        "n_merged": entry.get("n_merged"),
        "n_cleaned": entry.get("n_cleaned"),
        "n_deduped": entry.get("n_deduped"),
        "metrics": {
            "hold_sharpe": metrics.get("hold_sharpe"),
            "hold_annualized_return": metrics.get("hold_annualized_return"),
            "hold_max_drawdown": metrics.get("hold_max_drawdown"),
            "pool_ic": metrics.get("pool_ic"),
            "pool_rank_ic": metrics.get("pool_rank_ic"),
            "selection_correlation_max": metrics.get("selection_correlation_max"),
        },
        "gates": dict(entry.get("gates") or {}),
        "promotion_baseline": {
            "sharpe": (entry.get("promotion_baseline") or {}).get("sharpe"),
        },
        "improved": bool(entry.get("improved")),
        "promoted": bool(entry.get("promoted")),
    }


def verify_iteration_entry(
    entry: dict[str, Any],
    *,
    expected_policy_id: str | None,
    policy: MiningPolicyGenome,
    evaluator_baseline: MiningPolicyGenome,
    allow_legacy_binding: bool = False,
) -> dict[str, Any]:
    """Independent feasibility check used before an archive node can reproduce."""
    gates = entry.get("gates") or {}
    missing_gates = [name for name in REQUIRED_FEASIBILITY_GATES if name not in gates]
    failed_gates = [name for name in REQUIRED_FEASIBILITY_GATES if gates.get(name) is False]
    observed_policy_id = entry.get("rsi_policy_id")
    identity_ok = bool(
        expected_policy_id is None
        or observed_policy_id == expected_policy_id
        or (allow_legacy_binding and observed_policy_id is None)
    )
    frozen_evaluator_match = all(
        getattr(policy, name) == getattr(evaluator_baseline, name)
        for name in FROZEN_EVALUATOR_FIELDS
    )
    hold = (entry.get("metrics") or {}).get("hold_sharpe")
    hold_finite = hold is not None and math.isfinite(float(hold))
    feasible = bool(
        identity_ok
        and frozen_evaluator_match
        and hold_finite
        and not missing_gates
        and not failed_gates
    )
    return {
        "verified": feasible,
        "identity_ok": identity_ok,
        "observed_policy_id": observed_policy_id,
        "expected_policy_id": expected_policy_id,
        "binding_mode": "legacy_sequence_inference" if allow_legacy_binding else "explicit",
        "frozen_evaluator_match": frozen_evaluator_match,
        "missing_gates": missing_gates,
        "failed_gates": failed_gates,
        "hold_finite": hold_finite,
    }


def audit_archive_against_state(
    archive: PolicyArchive,
    state_path: Path,
    *,
    baseline_iteration: int = 49,
) -> dict[str, Any]:
    """Migrate legacy nodes into verified, invalid, or pending archive states."""
    state = json.loads(state_path.read_text(encoding="utf-8"))
    entries = {int(row["iteration"]): row for row in state.get("history") or []}
    baseline_node = archive.nodes.get("policy_0000")
    if baseline_node is None:
        raise RuntimeError("policy_0000 is required for evaluator baseline audit")
    evaluator_baseline = MiningPolicyGenome.from_dict(baseline_node.policy)
    counts = {"bootstrap": 0, "valid": 0, "invalid": 0, "pending": 0}

    for node in archive.nodes.values():
        match = re.search(r"(\d+)$", node.node_id)
        if match is None:
            node.status = "evaluated_invalid"
            node.eligible_parent = False
            node.fitness = 0.0
            counts["invalid"] += 1
            continue
        offset = int(match.group(1))
        iteration = baseline_iteration + offset
        entry = entries.get(iteration)
        node.source_iteration = iteration if entry is not None else None
        if offset == 0:
            node.status = "bootstrap_verified"
            node.eligible_parent = True
            node.verification = {
                "verified": True,
                "binding_mode": "bootstrap",
                "frozen_evaluator_match": True,
            }
            if entry is not None:
                node.evaluation_receipt = compact_iteration_entry(entry)
            counts["bootstrap"] += 1
            continue
        if entry is None:
            node.status = "proposed"
            node.eligible_parent = False
            node.fitness = 0.0
            node.verification = {"verified": False, "reason": "iteration_not_found"}
            counts["pending"] += 1
            continue
        policy = MiningPolicyGenome.from_dict(node.policy)
        verification = verify_iteration_entry(
            entry,
            expected_policy_id=node.node_id,
            policy=policy,
            evaluator_baseline=evaluator_baseline,
            allow_legacy_binding=True,
        )
        receipt = compact_iteration_entry(entry)
        hold = (receipt.get("metrics") or {}).get("hold_sharpe")
        archive.record_evaluation(
            node.node_id,
            fitness=float(hold or 0.0),
            feasible=bool(verification["verified"]),
            source_iteration=iteration,
            receipt=receipt,
            verification=verification,
        )
        counts["valid" if verification["verified"] else "invalid"] += 1
    archive.save()
    best = archive.best()
    return {
        "baseline_iteration": baseline_iteration,
        "counts": counts,
        "eligible_parent_count": sum(
            1 for node in archive.nodes.values() if node.eligible_parent
        ),
        "best_eligible": (
            {"node_id": best.node_id, "fitness": best.fitness} if best is not None else None
        ),
        "invalid_node_ids": [
            node.node_id
            for node in archive.nodes.values()
            if node.status == "evaluated_invalid"
        ],
        "pending_node_ids": [node.node_id for node in archive.pending()],
    }


def _choose_island(
    diagnosis: FailureDiagnosis,
    archive: PolicyArchive | None,
    rng: random.Random,
) -> str:
    """Pick exactly one island; bias by diagnosis but force underused lineages."""
    codes = set(diagnosis.codes)
    preferred: list[str] = []
    if "selection_corr_gate" in codes:
        preferred.extend(["diversity", "parent_selection"])
    if "near_miss_promote" in codes or "flat_hold" in codes:
        preferred.extend(["diversity", "parent_selection", "search_budget"])
    if "hold_regression" in codes or "low_pool_ic" in codes:
        preferred.extend(["search_budget", "parent_selection"])
    if "aggressive_dedup" in codes:
        preferred.append("diversity")
    if not preferred:
        preferred = list(ISLANDS)

    counts = (
        archive.island_counts(recent_only=True, recent_n=12)
        if archive is not None
        else {name: 0 for name in ISLANDS}
    )
    recent_keys = archive.recent_mutation_keys(8) if archive is not None else []
    recent_surfaces = {surface for surface, _ in recent_keys}
    # Soft-ban surfaces that already dominate the last few proposes.
    overused = {name for name in ISLANDS if counts.get(name, 0) >= 2}

    def _filtered(pool: list[str]) -> list[str]:
        out = [name for name in pool if name not in overused]
        if not out:
            out = [name for name in pool if name not in recent_surfaces]
        return out or list(pool)

    # 50% underused, 35% diagnosis-preferred, 15% uniform — stronger anti-collapse.
    mode = rng.choices(
        ["underused", "preferred", "uniform"], weights=[0.5, 0.35, 0.15], k=1
    )[0]
    if mode == "uniform":
        return rng.choice(_filtered(list(ISLANDS)))
    if mode == "underused":
        min_count = min(counts.get(name, 0) for name in ISLANDS)
        candidates = [
            name for name in ISLANDS if counts.get(name, 0) <= min_count + 0
        ]
        return rng.choice(_filtered(candidates))
    return rng.choice(_filtered(preferred))


def _mutated_value(field_name: str, current: Any, rng: random.Random) -> Any:
    """Return a different in-bounds value for exactly one policy field."""
    if field_name == "parent_mode":
        return "global" if current == "dag_neighbors" else "dag_neighbors"
    if field_name == "ast_regularizer_enabled":
        return not bool(current)

    bounds: dict[str, tuple[float, float, tuple[float, ...]]] = {
        "population_size": (16, 40, (-4, -2, 2, 4)),
        "max_generations": (5, 14, (-2, -1, 1, 2)),
        "patience": (2, 6, (-1, 1)),
        "global_epsilon": (0.05, 0.40, (-0.05, 0.05)),
        "dag_edge_similarity": (0.20, 0.60, (-0.05, 0.05)),
        "semantic_dedup_corr_threshold": (0.85, 0.99, (-0.02, 0.02)),
        "keep_diversity_slots": (0, 5, (-1, 1)),
        "top_n": (6, 12, (-1, 1)),
        "ast_similarity_tau": (0.70, 0.95, (-0.05, 0.05)),
    }
    low, high, deltas = bounds[field_name]
    candidates: list[Any] = []
    for delta in deltas:
        value: Any = min(high, max(low, float(current) + delta))
        value = int(round(value)) if isinstance(current, int) else round(float(value), 10)
        if value != current:
            candidates.append(value)
    if not candidates:
        raise RuntimeError(f"no legal mutation available for {field_name}={current!r}")
    return rng.choice(candidates)


def policy_diff(
    parent: MiningPolicyGenome,
    child: MiningPolicyGenome,
) -> dict[str, tuple[Any, Any]]:
    """Return functional policy changes, excluding lineage metadata."""
    ignored = {"version", "notes", "island"}
    child_values = child.to_dict()
    return {
        key: (before, child_values[key])
        for key, before in parent.to_dict().items()
        if key not in ignored and before != child_values[key]
    }


def _apply_single_field(
    policy: MiningPolicyGenome,
    surface: str,
    rng: random.Random,
) -> tuple[str, Any, Any]:
    """Mutate exactly one functional field within one search surface."""
    fields = list(MUTATION_FIELDS[surface])
    rng.shuffle(fields)
    for field_name in fields:
        before = getattr(policy, field_name)
        try:
            after = _mutated_value(field_name, before, rng)
        except RuntimeError:
            continue
        setattr(policy, field_name, after)
        policy.island = surface
        return field_name, before, after
    raise RuntimeError(f"mutation surface {surface!r} has no legal field edit")


def mutate_policy(
    policy: MiningPolicyGenome,
    diagnosis: FailureDiagnosis,
    rng: random.Random | None = None,
    archive: PolicyArchive | None = None,
) -> MiningPolicyGenome:
    """Self-modify exactly one functional field on one search surface.

    Previous behavior stacked every diagnosis repair (relax_dedup + expand_dag +
    shrink_top_n), so the archive collapsed to one recipe. DGM open-endedness
    requires lineage diversity.
    [source: arXiv:2505.22954]
    """
    rng = rng or random.Random()
    p = MiningPolicyGenome.from_dict(policy.to_dict())
    # Examiner stays frozen: search policy must not grade itself easier.
    p.promote_hold_sharpe_threshold = float(policy.promote_hold_sharpe_threshold)
    p.max_selection_correlation_gate = float(policy.max_selection_correlation_gate)
    surface = _choose_island(diagnosis, archive, rng)
    field_name, before, after = _apply_single_field(p, surface, rng)
    diff = policy_diff(policy, p)
    if len(diff) != 1 or field_name not in diff:
        raise RuntimeError(f"RSI mutation must change one field, got {diff}")
    notes = [f"surface={surface}", f"field={field_name}", f"{before!r}->{after!r}"]
    if "success" in set(diagnosis.codes):
        notes.append("success_keep")
    p.version = int(p.version) + 1
    p.notes = ",".join(notes)
    return p


def materialize_policy_configs(
    policy: MiningPolicyGenome,
    *,
    base_loop_config: Path,
    base_evolution_config: Path,
    out_dir: Path,
    rsi_metadata: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    loop_raw = yaml.safe_load(base_loop_config.read_text(encoding="utf-8"))
    evo_raw = yaml.safe_load(base_evolution_config.read_text(encoding="utf-8"))

    evo_out = out_dir / "evolution_config.yaml"
    loop_out = out_dir / "loop_config.yaml"

    evo_cfg = apply_policy_to_evolution_config(evo_raw, policy)
    evo_out.write_text(
        yaml.safe_dump(evo_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    loop_cfg = apply_policy_to_loop_config(loop_raw, policy)
    loop_cfg.update(rsi_metadata or {})
    loop_cfg["evolution_config"] = str(evo_out).replace("\\", "/")
    # Ensure no Relative Strength Index seed libraries leak in.
    loop_cfg.pop("extra_seed_libraries", None)
    loop_out.write_text(
        yaml.safe_dump(loop_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    policy.to_yaml(out_dir / "policy_genome.yaml")
    return loop_out, evo_out


def bootstrap_archive(
    archive: PolicyArchive,
    *,
    baseline_fitness: float,
    seed_policy: MiningPolicyGenome | None = None,
    state_path: Path | None = None,
) -> ArchiveNode:
    if archive.nodes:
        best = archive.best()
        if best is None and state_path is not None and state_path.exists():
            # v1 archives lack eligible_parent; migrate via independent gate audit.
            audit_archive_against_state(archive, state_path)
            best = archive.best()
        if best is None:
            # Last-resort open-endedness: keep positive-fitness stepping stones.
            for node in archive.nodes.values():
                if float(node.fitness) > 0.0:
                    node.eligible_parent = True
                    if node.status in {"", "proposed", "legacy_unverified"}:
                        node.status = "legacy_fitness_eligible"
            archive.save()
            best = archive.best()
        assert best is not None, "archive has nodes but no eligible parent after migration"
        return best
    policy = seed_policy or MiningPolicyGenome()
    node = ArchiveNode(
        node_id="policy_0000",
        parent_id=None,
        policy=policy.to_dict(),
        fitness=float(baseline_fitness),
        created_at=datetime.now(timezone.utc).isoformat(),
        notes="bootstrap_iter49_baseline",
        status="bootstrap_verified",
        eligible_parent=True,
        source_iteration=49,
        verification={"verified": True, "binding_mode": "bootstrap"},
    )
    archive.add(node)
    return node


def _propose_child_unlocked(
    archive: PolicyArchive,
    *,
    state_path: Path,
    base_loop_config: Path,
    base_evolution_config: Path,
    work_dir: Path,
    seed: int = 0,
) -> dict[str, Any]:
    """Sample parent → mutate → materialize; return receipt for inner eval."""
    rng = random.Random(seed)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    pending = archive.pending()
    if pending:
        pending_ids = ", ".join(node.node_id for node in pending)
        raise RuntimeError(f"record or audit pending RSI nodes before proposing: {pending_ids}")

    parent = archive.sample_parent(rng)
    history = state.get("history") or []
    latest = history[-1] if history else None
    # Diagnose from the latest inner-loop outcome so recent corr-gate / promote
    # signals steer the next surface; parent genome still comes from sampling.
    if latest is not None:
        diagnosis = diagnose_iteration(latest, state)
    else:
        parent_entry = parent.evaluation_receipt or {
            "promoted": True,
            "metrics": {"hold_sharpe": parent.fitness},
            "promotion_baseline": {"sharpe": parent.fitness},
            "gates": {name: True for name in REQUIRED_FEASIBILITY_GATES},
        }
        diagnosis = diagnose_iteration(parent_entry)
    parent_policy = MiningPolicyGenome.from_dict(parent.policy)
    child_policy = mutate_policy(parent_policy, diagnosis, rng=rng, archive=archive)
    # Avoid repeating a recently failed identical (surface, field) edit.
    recent_keys = set(archive.recent_mutation_keys(6))
    for _ in range(8):
        key = (child_policy.island, next(iter(policy_diff(parent_policy, child_policy))))
        if key not in recent_keys:
            break
        child_policy = mutate_policy(parent_policy, diagnosis, rng=rng, archive=archive)
    diff = policy_diff(parent_policy, child_policy)
    if len(diff) != 1:
        raise RuntimeError(f"child must contain exactly one functional edit: {diff}")
    mutation_field, (mutation_before, mutation_after) = next(iter(diff.items()))
    mutation_surface = child_policy.island

    indexes = [
        int(match.group(1))
        for node_id in archive.nodes
        if (match := re.search(r"(\d+)$", node_id)) is not None
    ]
    child_id = f"policy_{max(indexes, default=-1) + 1:04d}"
    round_dir = work_dir / child_id
    evaluation_group_id = f"{parent.node_id}__{child_id}__seed_{seed}"
    rsi_metadata = {
        "rsi_policy_id": child_id,
        "rsi_parent_id": parent.node_id,
        "rsi_mutation_surface": mutation_surface,
        "rsi_mutation_field": mutation_field,
        "rsi_evaluation_group_id": evaluation_group_id,
        "rsi_proposal_seed": int(seed),
        "rsi_evaluation_seed": int(seed),
    }
    loop_out, evo_out = materialize_policy_configs(
        child_policy,
        base_loop_config=base_loop_config,
        base_evolution_config=base_evolution_config,
        out_dir=round_dir,
        rsi_metadata=rsi_metadata,
    )

    child = ArchiveNode(
        node_id=child_id,
        parent_id=parent.node_id,
        policy=child_policy.to_dict(),
        fitness=0.0,  # filled after empirical inner-loop eval
        diagnosis_codes=diagnosis.codes,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=child_policy.notes,
        status="proposed",
        eligible_parent=False,
        mutation_surface=mutation_surface,
        mutation_field=mutation_field,
        mutation_before=mutation_before,
        mutation_after=mutation_after,
        paired_required=True,
        paired_status="pending",
    )
    archive.add(child)

    active_dir = work_dir / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(loop_out, active_dir / "loop_config.yaml")
    shutil.copy(evo_out, active_dir / "evolution_config.yaml")
    child_policy.to_yaml(active_dir / "policy_genome.yaml")

    receipt = {
        "child_id": child_id,
        "parent_id": parent.node_id,
        "diagnosis": diagnosis.to_dict(),
        "policy": child_policy.to_dict(),
        "mutation_surface": mutation_surface,
        "mutation_field": mutation_field,
        "mutation_before": mutation_before,
        "mutation_after": mutation_after,
        "evaluation_group_id": evaluation_group_id,
        "expected_iteration": int(state.get("iteration", 0)) + 1,
        "proposal_seed": int(seed),
        "evaluation_seed": int(seed),
        "loop_config": str(active_dir / "loop_config.yaml"),
        "round_dir": str(round_dir),
        "config_hashes": {
            "loop_config_sha256": hashlib.sha256(loop_out.read_bytes()).hexdigest(),
            "evolution_config_sha256": hashlib.sha256(evo_out.read_bytes()).hexdigest(),
        },
    }
    (round_dir / "propose_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (active_dir / "last_propose_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return receipt


def propose_child(
    archive: PolicyArchive,
    *,
    state_path: Path,
    base_loop_config: Path,
    base_evolution_config: Path,
    work_dir: Path,
    seed: int = 0,
) -> dict[str, Any]:
    """Atomically allocate and materialize one immutable child proposal."""
    with exclusive_proposal_lock(archive.path):
        refreshed = PolicyArchive(archive.path)
        receipt = _propose_child_unlocked(
            refreshed,
            state_path=state_path,
            base_loop_config=base_loop_config,
            base_evolution_config=base_evolution_config,
            work_dir=work_dir,
            seed=seed,
        )
        archive.nodes = refreshed.nodes
        return receipt


def record_child_evaluation(
    archive: PolicyArchive,
    child_id: str,
    state_path: Path,
) -> dict[str, Any]:
    """Verify identity and hard gates before making a child reproducible."""
    if child_id not in archive.nodes:
        raise KeyError(child_id)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    history = state.get("history") or []
    if not history:
        raise RuntimeError("factor-mining state has no completed iteration")
    entry = history[-1]
    node = archive.nodes[child_id]
    baseline = archive.nodes.get("policy_0000")
    if baseline is None:
        raise RuntimeError("policy_0000 is required as frozen evaluator baseline")
    verification = verify_iteration_entry(
        entry,
        expected_policy_id=child_id,
        policy=MiningPolicyGenome.from_dict(node.policy),
        evaluator_baseline=MiningPolicyGenome.from_dict(baseline.policy),
    )
    receipt = compact_iteration_entry(entry)
    hold = (receipt.get("metrics") or {}).get("hold_sharpe")
    fitness = float(hold) if hold is not None else 0.0
    archive.record_evaluation(
        child_id,
        fitness=fitness,
        feasible=bool(verification["verified"]),
        source_iteration=int(entry["iteration"]),
        receipt=receipt,
        verification=verification,
    )
    result = {
        "child_id": child_id,
        "fitness": fitness if verification["verified"] else 0.0,
        "raw_hold_sharpe": fitness,
        "eligible_parent": archive.nodes[child_id].eligible_parent,
        "status": archive.nodes[child_id].status,
        "single_evaluation_verified": bool(verification["verified"]),
        "paired_status": archive.nodes[child_id].paired_status,
        "verification": verification,
    }
    receipt_path = archive.path.parent / child_id / "evaluation_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def record_paired_evaluation(
    archive: PolicyArchive,
    child_id: str,
    paired_receipt: dict[str, Any],
) -> dict[str, Any]:
    """Apply an independently produced paired-seed selection receipt."""
    if child_id not in archive.nodes:
        raise KeyError(child_id)
    node = archive.nodes[child_id]
    identity_ok = bool(
        paired_receipt.get("schema") == "rsi_paired_policy_evaluation_v1"
        and paired_receipt.get("child_id") == child_id
        and paired_receipt.get("parent_id") == node.parent_id
    )
    gates = paired_receipt.get("gates") or {}
    gates_ok = bool(gates and all(value is True for value in gates.values()))
    single_ok = bool((node.verification or {}).get("verified"))
    selected = bool(identity_ok and gates_ok and paired_receipt.get("selected") and single_ok)
    node.paired_required = True
    node.paired_evaluation = dict(paired_receipt)
    node.paired_status = "selected" if selected else "rejected"
    node.eligible_parent = selected
    node.status = "evaluated_valid_pair_selected" if selected else "paired_rejected"
    if not selected:
        node.fitness = 0.0
    archive.save()
    result = {
        "child_id": child_id,
        "parent_id": node.parent_id,
        "selected": selected,
        "eligible_parent": node.eligible_parent,
        "status": node.status,
        "identity_ok": identity_ok,
        "single_evaluation_verified": single_ok,
        "paired_gates_ok": gates_ok,
    }
    receipt_path = archive.path.parent / child_id / "paired_selection_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def record_child_fitness(archive: PolicyArchive, child_id: str, state_path: Path) -> float:
    """Backward-compatible wrapper returning only feasible archive fitness."""
    return float(record_child_evaluation(archive, child_id, state_path)["fitness"])


def main() -> int:
    parser = argparse.ArgumentParser(description="DGM-style RSI propose step for mining policies")
    parser.add_argument(
        "--state",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop/state.json"),
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop/dgm_rsi/archive.json"),
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop/dgm_rsi"),
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
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--bootstrap-fitness",
        type=float,
        default=2.056,
        help="Initial archive fitness (iter-49 hold Sharpe)",
    )
    parser.add_argument(
        "--record-fitness",
        type=str,
        default="",
        help="If set to a child_id, only record fitness from state and exit",
    )
    parser.add_argument(
        "--audit-existing",
        action="store_true",
        help="Migrate legacy nodes using hard gates and frozen evaluator fields",
    )
    parser.add_argument("--baseline-iteration", type=int, default=49)
    args = parser.parse_args()

    archive = PolicyArchive(args.archive)
    if args.audit_existing:
        result = audit_archive_against_state(
            archive,
            args.state,
            baseline_iteration=args.baseline_iteration,
        )
        result["archive_sha256"] = hashlib.sha256(args.archive.read_bytes()).hexdigest()
        result["state_sha256"] = hashlib.sha256(args.state.read_bytes()).hexdigest()
        result["created_at"] = datetime.now(timezone.utc).isoformat()
        (args.archive.parent / "phase1_audit_receipt.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.record_fitness:
        result = record_child_evaluation(archive, args.record_fitness, args.state)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    bootstrap_archive(
        archive,
        baseline_fitness=args.bootstrap_fitness,
        state_path=args.state,
    )
    receipt = propose_child(
        archive,
        state_path=args.state,
        base_loop_config=args.base_loop_config,
        base_evolution_config=args.base_evolution_config,
        work_dir=args.work_dir,
        seed=args.seed,
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    print(
        "\nNext inner iter:\n"
        f"  py -3 -u -m china_a_share_alpha.scripts.run_factor_mining_loop {receipt['loop_config']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
