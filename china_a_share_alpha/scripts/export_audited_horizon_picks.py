"""Export complete stock lists for the audited 5d dynamic and 10d static contracts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from china_a_share_alpha.scripts.evolve_20d_position_schedule import (
    _sha256_file,
    build_library_signal,
)
from china_a_share_alpha.scripts.run_frozen_promotion_audit import verify_snapshot

DYNAMIC_5D_SCHEDULE = np.array([1.0, 1.0, 0.7, 0.7, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0])
STATIC_10D_SCHEDULE = np.ones(10)


def build_horizon_selection(
    signal: pd.Series,
    panel: pd.DataFrame,
    horizon: int,
    schedule: np.ndarray,
    selection_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Return complete long and short cohorts as of the panel's final date."""
    dates = panel.index.get_level_values("date").unique().sort_values()
    latest_date = pd.Timestamp(dates[-1])
    rebalance_index = ((len(dates) - 1) // horizon) * horizon
    rebalance_date = pd.Timestamp(dates[rebalance_index])
    rebalance_signal = signal.xs(rebalance_date, level="date").dropna().sort_values()
    latest_signal = signal.xs(latest_date, level="date").dropna()
    count = max(1, int(len(rebalance_signal) * selection_fraction))
    longs = rebalance_signal.tail(count).index
    shorts = rebalance_signal.head(count).index

    latest_rank = latest_signal.rank(pct=True, ascending=False)
    latest_order = latest_signal.rank(method="first", ascending=False).astype("Int64")
    total_latest = int(len(latest_signal))

    long_rows = []
    for symbol in longs:
        percentile = float(latest_rank.get(symbol, np.nan))
        if np.isfinite(percentile):
            rank_bin = min(9, max(0, int(np.ceil(percentile * 10) - 1)))
            multiplier = float(schedule[rank_bin])
            current_rank = int(latest_order[symbol])
        else:
            rank_bin = -1
            multiplier = 0.0
            current_rank = pd.NA
        if multiplier >= 0.999:
            action = "HOLD_100"
        elif multiplier >= 0.699:
            action = "TRIM_70"
        elif multiplier >= 0.499:
            action = "TRIM_50"
        else:
            action = "EXIT_0"
        long_rows.append(
            {
                "symbol": symbol,
                "side": "long",
                "rebalance_date": rebalance_date.date().isoformat(),
                "as_of": latest_date.date().isoformat(),
                "rebalance_signal": float(rebalance_signal[symbol]),
                "current_signal": float(latest_signal.get(symbol, np.nan)),
                "current_rank": current_rank,
                "current_universe_size": total_latest,
                "current_rank_percentile": percentile,
                "rank_bin": rank_bin,
                "position_multiplier": multiplier,
                "base_weight": float(1.0 / count),
                "target_weight": float(multiplier / count),
                "action": action,
            }
        )

    short_rows = []
    for symbol in shorts:
        short_rows.append(
            {
                "symbol": symbol,
                "side": "short",
                "rebalance_date": rebalance_date.date().isoformat(),
                "as_of": latest_date.date().isoformat(),
                "rebalance_signal": float(rebalance_signal[symbol]),
                "current_signal": float(latest_signal.get(symbol, np.nan)),
                "current_rank": (
                    int(latest_order[symbol]) if symbol in latest_order.index else pd.NA
                ),
                "current_universe_size": total_latest,
                "current_rank_percentile": float(latest_rank.get(symbol, np.nan)),
                "rank_bin": pd.NA,
                "position_multiplier": 1.0,
                "base_weight": float(-1.0 / count),
                "target_weight": float(-1.0 / count),
                "action": "HOLD_SHORT",
            }
        )

    long_frame = pd.DataFrame(long_rows).sort_values(
        ["position_multiplier", "current_rank"], ascending=[False, True]
    )
    short_frame = pd.DataFrame(short_rows).sort_values("current_rank", ascending=False)
    metadata = {
        "as_of": latest_date.date().isoformat(),
        "rebalance_date": rebalance_date.date().isoformat(),
        "horizon": horizon,
        "selection_fraction": selection_fraction,
        "cohort_size": count,
        "current_positive_longs": int((long_frame["target_weight"] > 0).sum()),
        "exited_longs": int((long_frame["target_weight"] == 0).sum()),
        "shorts": int(len(short_frame)),
    }
    return long_frame, short_frame, metadata


def build_combined_long_list(
    long_5d: pd.DataFrame,
    long_10d: pd.DataFrame,
) -> pd.DataFrame:
    """Combine positive long positions without inventing unaudited capital weights."""
    active_5d = long_5d[long_5d["target_weight"] > 0].set_index("symbol")
    active_10d = long_10d[long_10d["target_weight"] > 0].set_index("symbol")
    symbols = sorted(set(active_5d.index) | set(active_10d.index))
    rows = []
    for symbol in symbols:
        in_5d = symbol in active_5d.index
        in_10d = symbol in active_10d.index
        if in_5d and in_10d:
            bucket = "CORE_5D_10D"
        elif in_5d:
            bucket = "PRIMARY_5D"
        else:
            bucket = "SECONDARY_10D"
        rows.append(
            {
                "symbol": symbol,
                "bucket": bucket,
                "selected_5d": in_5d,
                "selected_10d": in_10d,
                "rank_5d": int(active_5d.loc[symbol, "current_rank"]) if in_5d else pd.NA,
                "rank_10d": (int(active_10d.loc[symbol, "current_rank"]) if in_10d else pd.NA),
                "multiplier_5d": (
                    float(active_5d.loc[symbol, "position_multiplier"]) if in_5d else 0.0
                ),
                "component_weight_5d": (
                    float(active_5d.loc[symbol, "target_weight"]) if in_5d else 0.0
                ),
                "component_weight_10d": (
                    float(active_10d.loc[symbol, "target_weight"]) if in_10d else 0.0
                ),
            }
        )
    order = {"CORE_5D_10D": 0, "PRIMARY_5D": 1, "SECONDARY_10D": 2}
    result = pd.DataFrame(rows)
    result["bucket_order"] = result["bucket"].map(order)
    return result.sort_values(["bucket_order", "rank_5d", "rank_10d"]).drop(columns="bucket_order")


def export(
    snapshot_dir: Path,
    library_5d: Path,
    library_10d: Path,
    output_dir: Path,
    smooth_span: int = 10,
    min_factor_coverage: float = 0.5,
) -> dict[str, Any]:
    manifest = verify_snapshot(snapshot_dir)
    panels = {
        name: pd.read_parquet(snapshot_dir / manifest["files"][name]["file"])
        for name in ("train", "val", "test")
    }
    full_panel = pd.concat(panels.values()).sort_index()
    test_panel = panels["test"]
    names_path = snapshot_dir / "stock_basic.csv"
    names = pd.DataFrame(columns=["symbol", "name"])
    if names_path.exists():
        names = pd.read_csv(names_path, dtype=str, encoding="utf-8-sig")
        names = names.rename(columns={"ts_code": "symbol"})[["symbol", "name"]]
        names = names.drop_duplicates("symbol")
    libraries = {5: library_5d, 10: library_10d}
    schedules = {5: DYNAMIC_5D_SCHEDULE, 10: STATIC_10D_SCHEDULE}
    selections = {}
    library_receipts = {}
    output_dir.mkdir(parents=True, exist_ok=True)

    for horizon, library_path in libraries.items():
        library = pd.read_csv(library_path)
        signal, signal_receipt = build_library_signal(
            library,
            full_panel,
            smooth_span=smooth_span,
            min_factor_coverage=min_factor_coverage,
        )
        longs, shorts, metadata = build_horizon_selection(
            signal,
            test_panel,
            horizon=horizon,
            schedule=schedules[horizon],
        )
        if not names.empty:
            longs = longs.merge(names, on="symbol", how="left")
            shorts = shorts.merge(names, on="symbol", how="left")
        label = f"{horizon}d"
        longs.to_csv(output_dir / f"{label}_long_complete.csv", index=False)
        longs[longs["target_weight"] > 0].to_csv(
            output_dir / f"{label}_long_current.csv", index=False
        )
        shorts.to_csv(output_dir / f"{label}_short_current.csv", index=False)
        selections[label] = {"longs": longs, "shorts": shorts, "metadata": metadata}
        library_receipts[label] = {
            "path": str(library_path.resolve()),
            "sha256": _sha256_file(library_path),
            "rows": int(len(library)),
            "signal": signal_receipt,
        }

    combined = build_combined_long_list(selections["5d"]["longs"], selections["10d"]["longs"])
    if not names.empty:
        combined = combined.merge(names, on="symbol", how="left")
    combined.to_csv(output_dir / "combined_long_all.csv", index=False)
    receipt = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_verified": True,
        "as_of": selections["5d"]["metadata"]["as_of"],
        "not_realtime": True,
        "contract": {
            "5d": "top/bottom 20%, fixed dynamic trim, EMA10",
            "10d": "top/bottom 20%, static hold, EMA10",
            "history": "continuous train/validation/test signal warm-up",
            "combined_weights": "not assigned; component weights only",
        },
        "libraries": library_receipts,
        "selections": {label: values["metadata"] for label, values in selections.items()},
        "combined_counts": combined["bucket"].value_counts().sort_index().to_dict(),
        "stock_name_coverage": (
            float(combined["name"].notna().mean()) if "name" in combined else 0.0
        ),
    }
    (output_dir / "stock_selection_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    _write_markdown(output_dir / "stock_selection_complete.md", receipt, selections, combined)
    return receipt


def _write_markdown(
    path: Path,
    receipt: dict[str, Any],
    selections: dict[str, Any],
    combined: pd.DataFrame,
) -> None:
    lines = [
        "# Audited 5d / 10d Stock Selection",
        "",
        f"- As of: `{receipt['as_of']}` (frozen data, not real time)",
        f"- Snapshot: `{receipt['snapshot_id']}`",
        "- Stock names are included when a UTF-8 Tushare stock_basic file is available.",
        "- Component weights are shown; no unaudited combined capital weight is assigned.",
        "",
        "## Combined Positive Long List",
        "",
        "| Symbol | Name | Bucket | 5d rank | 10d rank | 5d multiplier |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in combined.itertuples(index=False):
        rank_5d = "" if pd.isna(row.rank_5d) else str(int(row.rank_5d))
        rank_10d = "" if pd.isna(row.rank_10d) else str(int(row.rank_10d))
        lines.append(
            f"| {row.symbol} | {getattr(row, 'name', '')} | {row.bucket} | "
            f"{rank_5d} | {rank_10d} | "
            f"{row.multiplier_5d:.1f} |"
        )
    for label in ("5d", "10d"):
        values = selections[label]
        lines.extend(
            [
                "",
                f"## {label.upper()} Complete Rebalance Long Cohort",
                "",
                f"Rebalance date: `{values['metadata']['rebalance_date']}`.",
                "",
                "| Symbol | Name | Current rank | Multiplier | Action | Target weight |",
                "|---|---|---:|---:|---|---:|",
            ]
        )
        for row in values["longs"].itertuples(index=False):
            rank = "" if pd.isna(row.current_rank) else str(int(row.current_rank))
            lines.append(
                f"| {row.symbol} | {getattr(row, 'name', '')} | {rank} | "
                f"{row.position_multiplier:.1f} | "
                f"{row.action} | {row.target_weight:.4%} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--library-5d", type=Path, required=True)
    parser.add_argument("--library-10d", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--min-factor-coverage", type=float, default=0.5)
    args = parser.parse_args()
    export(
        snapshot_dir=args.snapshot_dir,
        library_5d=args.library_5d,
        library_10d=args.library_10d,
        output_dir=args.output_dir,
        smooth_span=args.smooth_span,
        min_factor_coverage=args.min_factor_coverage,
    )


if __name__ == "__main__":
    main()
