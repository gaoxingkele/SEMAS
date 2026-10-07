"""Paired multi-seed evaluation for RSI mining-policy mutations.

Parent and child must run on identical deterministic seeds. Selection uses the
distribution of within-seed hold-Sharpe deltas, after both arms pass the same
frozen non-promotion feasibility gates.

[source: wiki/think/rsi_causal_credit_assignment_20260920.md]
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Iterable


PAIR_RECEIPT_SCHEMA = "rsi_paired_policy_evaluation_v1"
PAIR_VALIDITY_GATES: tuple[str, ...] = (
    "train_sharpe_positive",
    "min_cleaned_count",
    "max_corr_ok",
    "candidate_evaluation_valid",
    "baseline_evaluation_valid",
    "hold_sharpe_ok",
)


def _index_by_seed(entries: Iterable[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for entry in entries:
        seed = int(entry["seed"])
        if seed in indexed:
            raise ValueError(f"duplicate paired-evaluation seed: {seed}")
        indexed[seed] = entry
    return indexed


def verify_paired_arm(
    entry: dict[str, Any],
    *,
    expected_policy_id: str,
    expected_seed: int,
) -> dict[str, Any]:
    """Verify one isolated paired-evaluation arm."""
    gates = entry.get("gates") or {}
    missing_gates = [name for name in PAIR_VALIDITY_GATES if name not in gates]
    failed_gates = [name for name in PAIR_VALIDITY_GATES if gates.get(name) is False]
    hold = (entry.get("metrics") or {}).get("hold_sharpe")
    hold_finite = hold is not None and math.isfinite(float(hold))
    identity_ok = entry.get("rsi_policy_id") == expected_policy_id
    seed_ok = int(entry.get("seed", -1)) == int(expected_seed)
    verified = bool(
        identity_ok and seed_ok and hold_finite and not missing_gates and not failed_gates
    )
    return {
        "verified": verified,
        "identity_ok": identity_ok,
        "seed_ok": seed_ok,
        "hold_finite": hold_finite,
        "missing_gates": missing_gates,
        "failed_gates": failed_gates,
    }


def summarize_paired_evaluations(
    parent_entries: Iterable[dict[str, Any]],
    child_entries: Iterable[dict[str, Any]],
    *,
    parent_id: str,
    child_id: str,
    min_pairs: int = 3,
    min_win_rate: float = 2.0 / 3.0,
    min_mean_delta: float = 0.0,
    min_median_delta: float = 0.0,
    max_worst_regression: float = 0.10,
) -> dict[str, Any]:
    """Build a deterministic selection receipt from matched parent/child runs."""
    parents = _index_by_seed(parent_entries)
    children = _index_by_seed(child_entries)
    seeds = sorted(set(parents) | set(children))
    pairs: list[dict[str, Any]] = []
    deltas: list[float] = []

    for seed in seeds:
        parent = parents.get(seed)
        child = children.get(seed)
        if parent is None or child is None:
            pairs.append(
                {
                    "seed": seed,
                    "valid": False,
                    "reason": "missing_parent" if parent is None else "missing_child",
                }
            )
            continue
        parent_check = verify_paired_arm(
            parent,
            expected_policy_id=parent_id,
            expected_seed=seed,
        )
        child_check = verify_paired_arm(
            child,
            expected_policy_id=child_id,
            expected_seed=seed,
        )
        valid = bool(parent_check["verified"] and child_check["verified"])
        row: dict[str, Any] = {
            "seed": seed,
            "valid": valid,
            "parent_verification": parent_check,
            "child_verification": child_check,
        }
        if valid:
            parent_hold = float((parent.get("metrics") or {})["hold_sharpe"])
            child_hold = float((child.get("metrics") or {})["hold_sharpe"])
            delta = child_hold - parent_hold
            row.update(
                {
                    "parent_hold_sharpe": parent_hold,
                    "child_hold_sharpe": child_hold,
                    "delta": delta,
                    "child_won": delta > 0.0,
                }
            )
            deltas.append(delta)
        pairs.append(row)

    valid_pairs = len(deltas)
    total_pairs = len(seeds)
    mean_delta = statistics.fmean(deltas) if deltas else None
    median_delta = statistics.median(deltas) if deltas else None
    worst_delta = min(deltas) if deltas else None
    win_rate = sum(delta > 0.0 for delta in deltas) / valid_pairs if deltas else 0.0
    gates = {
        "min_pairs": valid_pairs >= int(min_pairs),
        "all_pairs_valid": valid_pairs == total_pairs and total_pairs > 0,
        "mean_delta_positive": mean_delta is not None and mean_delta > min_mean_delta,
        "median_delta_positive": median_delta is not None
        and median_delta > min_median_delta,
        "win_rate_ok": win_rate >= min_win_rate,
        "worst_regression_ok": worst_delta is not None
        and worst_delta >= -abs(max_worst_regression),
    }
    return {
        "schema": PAIR_RECEIPT_SCHEMA,
        "parent_id": parent_id,
        "child_id": child_id,
        "seeds": seeds,
        "pairs": pairs,
        "summary": {
            "total_pairs": total_pairs,
            "valid_pairs": valid_pairs,
            "mean_delta": mean_delta,
            "median_delta": median_delta,
            "worst_delta": worst_delta,
            "win_rate": win_rate,
        },
        "thresholds": {
            "min_pairs": int(min_pairs),
            "min_win_rate": float(min_win_rate),
            "min_mean_delta": float(min_mean_delta),
            "min_median_delta": float(min_median_delta),
            "max_worst_regression": float(max_worst_regression),
        },
        "gates": gates,
        "selected": all(gates.values()),
    }


__all__ = [
    "PAIR_RECEIPT_SCHEMA",
    "PAIR_VALIDITY_GATES",
    "summarize_paired_evaluations",
    "verify_paired_arm",
]
