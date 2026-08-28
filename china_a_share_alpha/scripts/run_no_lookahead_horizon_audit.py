"""Audit 5d/10d/20d factor libraries with one no-lookahead contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from china_a_share_alpha.scripts.analyze_factor_ma_correlation import (
    daily_cross_sectional_spearman,
    summarize_correlations,
)
from china_a_share_alpha.scripts.analyze_ma_neutralized_alpha import (
    forward_compound_return,
    layer_return_summary,
)
from china_a_share_alpha.scripts.evolve_20d_position_schedule import (
    _sha256_file,
    backtest_schedule,
    build_library_signal,
    prepare_fold,
)
from china_a_share_alpha.scripts.run_frozen_promotion_audit import verify_snapshot

STATIC_SCHEDULE = [1.0] * 10
LEGACY_TRIM_SCHEDULE = [1.0, 1.0, 0.7, 0.7, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0]


def classify_horizon_value(
    validation: dict[str, Any],
    test: dict[str, Any],
) -> str:
    statistical = all(
        metrics["native_ic"]["mean_spearman"] > 0
        and metrics["layers_native"]["top_minus_bottom"] > 0
        for metrics in (validation, test)
    )
    executable = all(
        metrics["selected_hold"]["sharpe"] > 0 and metrics["selected_hold"]["annualized_return"] > 0
        for metrics in (validation, test)
    )
    if statistical and executable:
        return "ROBUST_RESEARCH_AND_EXECUTION_VALUE"
    if statistical:
        return "STATISTICAL_VALUE_ONLY"
    if executable:
        return "EXECUTION_VALUE_WITHOUT_STABLE_20D_IC"
    return "NO_ROBUST_VALUE"


def apply_stability_verdict(
    base_verdict: str,
    train: dict[str, Any],
    annual_test_hold: dict[str, Any],
) -> str:
    """Downgrade an otherwise positive result when time slices reverse sign."""
    if base_verdict != "ROBUST_RESEARCH_AND_EXECUTION_VALUE":
        return base_verdict
    train_reversal = (
        train["native_ic"]["mean_spearman"] <= 0
        or train["layers_native"]["top_minus_bottom"] <= 0
        or train["selected_hold"]["annualized_return"] <= 0
    )
    annual_reversal = any(
        metrics["annualized_return"] <= 0 for metrics in annual_test_hold.values()
    )
    if train_reversal or annual_reversal:
        return "RESEARCH_AND_EXECUTION_VALUE_REGIME_SENSITIVE"
    return base_verdict


def _evaluate_fold(
    fold_name: str,
    panel: pd.DataFrame,
    signal: pd.Series,
    native_horizon: int,
    transaction_cost: float,
    min_symbols: int,
    hac_lag: int,
    selected_schedule_name: str | None = None,
) -> dict[str, Any]:
    fold_signal = signal.reindex(panel.index).dropna()
    forward_native = forward_compound_return(panel["return"], native_horizon)
    forward_20d = forward_compound_return(panel["return"], 20)
    native_ic = summarize_correlations(
        daily_cross_sectional_spearman(fold_signal, forward_native, min_symbols),
        hac_lag=hac_lag,
    )
    ic_20d = summarize_correlations(
        daily_cross_sectional_spearman(fold_signal, forward_20d, min_symbols),
        hac_lag=hac_lag,
    )
    layers_native = layer_return_summary(
        fold_signal,
        forward_native,
        n_layers=5,
        min_symbols=min_symbols,
        hac_lag=hac_lag,
    )
    prepared = prepare_fold(
        name=f"{fold_name}_{native_horizon}d",
        signal=fold_signal,
        panel=panel,
        horizon=native_horizon,
        selection_fraction=0.2,
    )
    hold_results = {
        "static": backtest_schedule(prepared, STATIC_SCHEDULE, transaction_cost),
        "legacy_trim": backtest_schedule(prepared, LEGACY_TRIM_SCHEDULE, transaction_cost),
    }
    if selected_schedule_name is None:
        selected_schedule_name = max(
            hold_results,
            key=lambda name: hold_results[name]["sharpe"],
        )
    return {
        "native_ic": native_ic,
        "ic_20d": ic_20d,
        "layers_native": layers_native,
        "hold_candidates": hold_results,
        "selected_schedule": selected_schedule_name,
        "selected_hold": hold_results[selected_schedule_name],
    }


def _annual_hold_results(
    panel: pd.DataFrame,
    signal: pd.Series,
    horizon: int,
    schedule_name: str,
    transaction_cost: float,
) -> dict[str, Any]:
    schedule = STATIC_SCHEDULE if schedule_name == "static" else LEGACY_TRIM_SCHEDULE
    years = panel.index.get_level_values("date").year
    results = {}
    for year in sorted(set(years)):
        year_panel = panel[years == year]
        year_signal = signal.reindex(year_panel.index).dropna()
        if year_signal.empty:
            continue
        prepared = prepare_fold(
            name=f"{horizon}d_{year}",
            signal=year_signal,
            panel=year_panel,
            horizon=horizon,
            selection_fraction=0.2,
        )
        results[str(year)] = backtest_schedule(prepared, schedule, transaction_cost)
    return results


def analyze(
    snapshot_dir: Path,
    libraries: dict[int, Path],
    output_dir: Path,
    transaction_cost: float,
    smooth_span: int,
    min_factor_coverage: float,
    min_symbols: int,
    hac_lag: int,
) -> dict[str, Any]:
    manifest = verify_snapshot(snapshot_dir)
    fold_names = ["train", "val", "test"]
    fold_panels = {
        name: pd.read_parquet(snapshot_dir / manifest["files"][name]["file"]) for name in fold_names
    }
    full_panel = pd.concat(fold_panels.values()).sort_index()

    results = {}
    library_receipts = {}
    decay_rows = []
    for horizon, library_path in sorted(libraries.items()):
        library = pd.read_csv(library_path)
        signal, signal_receipt = build_library_signal(
            library,
            full_panel,
            smooth_span=smooth_span,
            min_factor_coverage=min_factor_coverage,
        )
        library_receipts[f"{horizon}d"] = {
            "path": str(library_path.resolve()),
            "sha256": _sha256_file(library_path),
            "rows": int(len(library)),
            "signal": signal_receipt,
        }

        horizon_results = {}
        validation = _evaluate_fold(
            "val",
            fold_panels["val"],
            signal,
            horizon,
            transaction_cost,
            min_symbols,
            hac_lag,
        )
        selected_schedule = validation["selected_schedule"]
        train = _evaluate_fold(
            "train",
            fold_panels["train"],
            signal,
            horizon,
            transaction_cost,
            min_symbols,
            hac_lag,
            selected_schedule_name=selected_schedule,
        )
        test = _evaluate_fold(
            "test",
            fold_panels["test"],
            signal,
            horizon,
            transaction_cost,
            min_symbols,
            hac_lag,
            selected_schedule_name=selected_schedule,
        )
        annual_test_hold = _annual_hold_results(
            fold_panels["test"],
            signal,
            horizon,
            selected_schedule,
            transaction_cost,
        )
        base_verdict = classify_horizon_value(validation, test)
        horizon_results.update({"train": train, "val": validation, "test": test})
        horizon_results["selected_schedule"] = selected_schedule
        horizon_results["verdict"] = apply_stability_verdict(
            base_verdict,
            train,
            annual_test_hold,
        )
        horizon_results["annual_test_hold"] = annual_test_hold

        for fold_name, fold_panel in fold_panels.items():
            fold_signal = signal.reindex(fold_panel.index).dropna()
            for forward_horizon in (1, 5, 10, 20):
                forward = forward_compound_return(fold_panel["return"], forward_horizon)
                metrics = summarize_correlations(
                    daily_cross_sectional_spearman(fold_signal, forward, min_symbols),
                    hac_lag=hac_lag,
                )
                decay_rows.append(
                    {
                        "library_horizon": horizon,
                        "fold": fold_name,
                        "forward_horizon": forward_horizon,
                        **metrics,
                    }
                )
        results[f"{horizon}d"] = horizon_results

    receipt = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_verified": True,
        "contract": {
            "signal": f"equal-weight factor z-scores with EMA span {smooth_span}",
            "selection": "choose static or fixed legacy trim on validation Sharpe only",
            "lookahead_rule": "positions formed at d earn returns beginning d+1",
            "transaction_cost": transaction_cost,
            "factor_coverage": min_factor_coverage,
            "ic_decay_horizons": [1, 5, 10, 20],
            "native_layers": 5,
        },
        "libraries": library_receipts,
        "results": results,
        "ic_decay": decay_rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "no_lookahead_horizon_audit_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=True, allow_nan=False),
        encoding="utf-8",
    )
    pd.DataFrame(decay_rows).to_csv(output_dir / "ic_decay.csv", index=False)
    _write_summary_csv(output_dir / "horizon_summary.csv", receipt)
    _write_markdown(output_dir / "no_lookahead_horizon_audit.md", receipt)
    return receipt


def _summary_rows(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for horizon_name, result in receipt["results"].items():
        for fold in ("train", "val", "test"):
            metrics = result[fold]
            rows.append(
                {
                    "library": horizon_name,
                    "fold": fold,
                    "selected_schedule": result["selected_schedule"],
                    "native_ic": metrics["native_ic"]["mean_spearman"],
                    "native_ic_hac_t": metrics["native_ic"]["hac_t_stat"],
                    "ic_20d": metrics["ic_20d"]["mean_spearman"],
                    "q5_minus_q1": metrics["layers_native"]["top_minus_bottom"],
                    "layer_spread_t": metrics["layers_native"]["spread_hac_t_stat"],
                    "hold_sharpe": metrics["selected_hold"]["sharpe"],
                    "hold_annualized_return": metrics["selected_hold"]["annualized_return"],
                    "hold_max_drawdown": metrics["selected_hold"]["max_drawdown"],
                    "verdict": result["verdict"],
                }
            )
    return rows


def _write_summary_csv(path: Path, receipt: dict[str, Any]) -> None:
    pd.DataFrame(_summary_rows(receipt)).to_csv(path, index=False)


def _write_markdown(path: Path, receipt: dict[str, Any]) -> None:
    lines = [
        "# No-Lookahead 5d / 10d / 20d Audit",
        "",
        f"- Snapshot: `{receipt['snapshot_id']}`",
        "- Positions formed at day d earn returns beginning day d+1",
        "- Cost: 10 bps one-way on actual target changes",
        "- Static versus fixed trim selected on validation only",
        "",
        "| Library | Fold | Schedule | Native IC | Q5-Q1 | Hold Sharpe | Ann. return | Max DD | Verdict |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in _summary_rows(receipt):
        lines.append(
            f"| {row['library']} | {row['fold']} | {row['selected_schedule']} | "
            f"{row['native_ic']:.4f} | {row['q5_minus_q1']:.2%} | "
            f"{row['hold_sharpe']:.4f} | {row['hold_annualized_return']:.2%} | "
            f"{row['hold_max_drawdown']:.2%} | {row['verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Test-Fold IC Decay",
            "",
            "| Library | 1d | 5d | 10d | 20d |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    decay = pd.DataFrame(receipt["ic_decay"])
    for horizon in sorted(decay["library_horizon"].unique()):
        selected = decay[(decay["library_horizon"] == horizon) & (decay["fold"] == "test")]
        values = dict(zip(selected["forward_horizon"], selected["mean_spearman"]))
        lines.append(
            f"| {horizon}d | {values[1]:.4f} | {values[5]:.4f} | "
            f"{values[10]:.4f} | {values[20]:.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--library-5d", type=Path, required=True)
    parser.add_argument("--library-10d", type=Path, required=True)
    parser.add_argument("--library-20d", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--transaction-cost", type=float, default=0.001)
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--min-factor-coverage", type=float, default=0.5)
    parser.add_argument("--min-symbols", type=int, default=30)
    parser.add_argument("--hac-lag", type=int, default=20)
    args = parser.parse_args()
    analyze(
        snapshot_dir=args.snapshot_dir,
        libraries={5: args.library_5d, 10: args.library_10d, 20: args.library_20d},
        output_dir=args.output_dir,
        transaction_cost=args.transaction_cost,
        smooth_span=args.smooth_span,
        min_factor_coverage=args.min_factor_coverage,
        min_symbols=args.min_symbols,
        hac_lag=args.hac_lag,
    )


if __name__ == "__main__":
    main()
