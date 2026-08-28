"""Freeze a data panel and audit live libraries under one promotion contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.scripts.run_multihizon_audit import evaluate_library_hold


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _safe_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in config.items()
        if "token" not in key.lower() and "secret" not in key.lower()
    }


def _panel_summary(panel: pd.DataFrame) -> dict[str, Any]:
    dates = panel.index.get_level_values("date")
    symbols = panel.index.get_level_values("symbol")
    return {
        "rows": int(len(panel)),
        "symbols": int(symbols.nunique()),
        "date_min": dates.min().isoformat(),
        "date_max": dates.max().isoformat(),
        "columns": list(panel.columns),
    }


def freeze_snapshot(
    config_path: Path,
    snapshot_dir: Path,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if cache_dir is not None:
        config["cache_dir"] = str(cache_dir.resolve())

    train, val, test = load_tushare_data_with_val(config)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    panels = {"train": train, "val": val, "test": test}
    files = {}
    for name, panel in panels.items():
        path = snapshot_dir / f"{name}.parquet"
        panel.to_parquet(path)
        files[name] = {
            "file": path.name,
            "sha256": _sha256_file(path),
            **_panel_summary(panel),
        }

    manifest_core = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_config_path": str(config_path),
        "source_config": _safe_config(config),
        "source_config_sha256": _sha256_file(config_path),
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "files": files,
    }
    manifest_core["snapshot_id"] = _json_hash(
        {
            "source_config": manifest_core["source_config"],
            "files": {name: value["sha256"] for name, value in files.items()},
        }
    )
    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_core, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest_core


def verify_snapshot(snapshot_dir: Path) -> dict[str, Any]:
    manifest_path = snapshot_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for name, metadata in manifest["files"].items():
        path = snapshot_dir / metadata["file"]
        if not path.exists():
            errors.append(f"missing {name} panel: {path}")
            continue
        actual = _sha256_file(path)
        if actual != metadata["sha256"]:
            errors.append(f"checksum mismatch for {name}: {actual}")
    if errors:
        raise ValueError("invalid frozen snapshot: " + "; ".join(errors))
    return manifest


def _resolve_artifact(
    path_value: str,
    artifact_root: Path,
    fallback_artifact_root: Path | None = None,
) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    primary = artifact_root / path
    if primary.exists() or fallback_artifact_root is None:
        return primary
    return fallback_artifact_root / path


def audit_snapshot(
    snapshot_dir: Path,
    audit_config_path: Path,
    output_dir: Path,
    artifact_root: Path,
    fallback_artifact_root: Path | None = None,
) -> dict[str, Any]:
    manifest = verify_snapshot(snapshot_dir)
    panels = {
        name: pd.read_parquet(snapshot_dir / manifest["files"][name]["file"])
        for name in ("train", "val", "test")
    }
    test = panels["test"]
    history = pd.concat(panels.values()).sort_index()
    with audit_config_path.open("r", encoding="utf-8") as handle:
        audit_config = yaml.safe_load(handle)

    results = []
    for spec in audit_config["libraries"]:
        library_path = _resolve_artifact(
            spec["library_path"], artifact_root, fallback_artifact_root
        )
        state_path = _resolve_artifact(spec["state_path"], artifact_root, fallback_artifact_root)
        result = {
            "name": spec["name"],
            "library_path": str(library_path),
            "state_path": str(state_path),
            "library_exists": library_path.exists(),
            "state_exists": state_path.exists(),
            "evaluation_mode": spec["evaluation_mode"],
            "horizon": int(spec["horizon"]),
        }
        if not library_path.exists():
            result.update({"valid": False, "verdict": "FAIL", "error": "library missing"})
            results.append(result)
            continue

        library = pd.read_csv(library_path)
        receipt = evaluate_library_hold(
            library,
            test,
            horizon=int(spec["horizon"]),
            transaction_cost=float(spec.get("transaction_cost", 0.001)),
            smooth_span=int(spec.get("smooth_span", 10)),
            evaluation_mode=spec["evaluation_mode"],
            min_factor_coverage=float(spec.get("min_factor_coverage", 0.5)),
            history_data=history,
        )
        result.update(receipt)
        result["library_sha256"] = _sha256_file(library_path)
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            result["state_iteration"] = state.get("iteration")
            result["state_best_hold_sharpe"] = state.get("best_hold_sharpe")

        min_sharpe = float(spec.get("min_hold_sharpe", 0.0))
        result["min_hold_sharpe"] = min_sharpe
        result["verdict"] = (
            "PASS" if receipt["valid"] and receipt["sharpe"] >= min_sharpe else "FAIL"
        )
        results.append(result)

    receipt = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_verified": True,
        "audit_config_path": str(audit_config_path),
        "audit_config_sha256": _sha256_file(audit_config_path),
        "evaluator_sha256": _sha256_file(Path(__file__).with_name("run_multihizon_audit.py")),
        "overall_verdict": (
            "PASS" if results and all(result["verdict"] == "PASS" for result in results) else "FAIL"
        ),
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "promotion_audit_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_markdown_receipt(receipt, output_dir / "promotion_audit_receipt.md")
    return receipt


def reconcile_states(receipt_path: Path, apply: bool = False) -> list[dict[str, Any]]:
    """Reconcile state baselines only when the audited library and state still match."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("snapshot_verified"):
        raise ValueError("receipt does not contain a verified snapshot")

    actions = []
    for result in receipt["results"]:
        if result.get("verdict") != "PASS" or not result.get("valid"):
            raise ValueError(f"cannot reconcile failed result: {result['name']}")
        library_path = Path(result["library_path"])
        state_path = Path(result["state_path"])
        if _sha256_file(library_path) != result["library_sha256"]:
            raise ValueError(f"library changed after audit: {library_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("iteration") != result.get("state_iteration"):
            raise ValueError(f"state changed after audit: {state_path}")

        history_by_iteration = {}
        for entry in state.get("history", []):
            iteration = entry.get("iteration")
            if isinstance(iteration, int):
                history_by_iteration[iteration] = entry
        state["history"] = [
            history_by_iteration[iteration] for iteration in sorted(history_by_iteration)
        ]
        baseline = {
            key: result[key]
            for key in (
                "valid",
                "evaluation_mode",
                "horizon",
                "transaction_cost",
                "smooth_span",
                "min_factor_coverage",
                "n_library_rows",
                "n_factors_evaluated",
                "valid_rows",
                "valid_row_fraction",
                "sharpe",
                "annualized_return",
                "cost_adjusted_return",
                "max_drawdown",
                "n_observations",
                "library_path",
                "library_sha256",
            )
        }
        baseline["library_path"] = state.get("live_library_path", baseline["library_path"])
        baseline["snapshot_id"] = receipt["snapshot_id"]
        baseline["evaluated_at"] = receipt["created_at"]
        state["state_schema_version"] = 2
        state["best_hold_sharpe"] = result["sharpe"]
        state["promotion_baseline"] = baseline
        state["last_reconciled_audit"] = {
            "receipt_path": str(receipt_path),
            "snapshot_id": receipt["snapshot_id"],
            "reconciled_at": datetime.now(timezone.utc).isoformat(),
        }
        actions.append(
            {
                "name": result["name"],
                "state_path": str(state_path),
                "iteration": state.get("iteration"),
                "history_entries": len(state["history"]),
                "baseline_sharpe": result["sharpe"],
                "applied": apply,
            }
        )
        if apply:
            temporary = state_path.with_suffix(state_path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary.replace(state_path)
    return actions


def _write_markdown_receipt(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Frozen Promotion Audit Receipt",
        "",
        f"- Snapshot: `{receipt['snapshot_id']}`",
        f"- Snapshot verified: {receipt['snapshot_verified']}",
        f"- Overall verdict: **{receipt['overall_verdict']}**",
        "",
        "| Library | Mode | Horizon | Valid | Sharpe | Return | Max DD | Rows | Verdict |",
        "|---|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for result in receipt["results"]:
        if result.get("valid"):
            lines.append(
                f"| {result['name']} | {result['evaluation_mode']} | "
                f"{result['horizon']}d | YES | {result['sharpe']:.4f} | "
                f"{result['annualized_return']:.2%} | {result['max_drawdown']:.2%} | "
                f"{result.get('valid_rows', 0)} | {result['verdict']} |"
            )
        else:
            lines.append(
                f"| {result['name']} | {result['evaluation_mode']} | "
                f"{result['horizon']}d | NO | - | - | - | 0 | {result['verdict']} |"
            )
    lines += [
        "",
        "This receipt is read-only: it does not promote or replace any live library.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("config", type=Path)
    freeze_parser.add_argument("--snapshot-dir", type=Path, required=True)
    freeze_parser.add_argument("--cache-dir", type=Path)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--snapshot-dir", type=Path, required=True)
    audit_parser.add_argument("--audit-config", type=Path, required=True)
    audit_parser.add_argument("--output-dir", type=Path, required=True)
    audit_parser.add_argument("--artifact-root", type=Path, default=Path("."))
    audit_parser.add_argument("--fallback-artifact-root", type=Path)

    reconcile_parser = subparsers.add_parser("reconcile-state")
    reconcile_parser.add_argument("--receipt", type=Path, required=True)
    reconcile_parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.command == "freeze":
        manifest = freeze_snapshot(args.config, args.snapshot_dir, args.cache_dir)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    elif args.command == "audit":
        receipt = audit_snapshot(
            args.snapshot_dir,
            args.audit_config,
            args.output_dir,
            args.artifact_root.resolve(),
            args.fallback_artifact_root.resolve() if args.fallback_artifact_root else None,
        )
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    else:
        actions = reconcile_states(args.receipt, apply=args.apply)
        print(json.dumps(actions, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
