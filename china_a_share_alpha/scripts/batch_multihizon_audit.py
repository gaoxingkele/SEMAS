"""Batch multi-horizon audit for all evolved factor libraries.

Evaluates every iteration library from the 5d, 10d, and 20d factor-mining loops
on 5-day, 10-day, and 20-day forward returns.  Loads the data panel once and
reuses it across all libraries for efficiency.

Outputs:
    - Per-iteration CSVs (ensemble + per-factor + hold) under
      ``<output_root>/<loop_name>/iter_NNNN/horizon_audit/``.
    - ``<output_root>/batch_audit_summary.csv`` aggregating ensemble metrics.
    - ``<output_root>/batch_audit_summary.md`` with a readable table.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.factor.parser import parse_expression

# Re-use helper logic from the single-library audit script.
from china_a_share_alpha.scripts.run_multihizon_audit import (
    _backtest,
    _compute_forward,
    _hold_backtest,
    _smooth,
    _zscore,
)


def _load_library(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "factor" not in df.columns:
        df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")
    return df


def _evaluate_library(
    lib: pd.DataFrame,
    data: dict[str, pd.DataFrame],
    horizons: list[int],
    transaction_cost: float,
    smooth_span: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run multi-horizon audit for one factor library."""
    periods = ["train", "val", "test"]
    factor_frames = {p: {} for p in periods}
    for _, row in lib.iterrows():
        try:
            expr = parse_expression(row["expression"])
            for p in periods:
                factor_frames[p][row["factor"]] = _zscore(expr.eval(data[p]))
        except Exception as exc:
            print(f"  skipping {row.get('factor')}: {exc}")

    def _ensemble(factor_dict: dict, span: int) -> pd.Series:
        mat = pd.concat(factor_dict.values(), axis=1).dropna()
        weights = np.ones(len(factor_dict)) / len(factor_dict)
        return _smooth((mat @ weights).clip(-5, 5), span)

    def _period_stats(factor: pd.Series, fwd: pd.Series) -> dict:
        valid = factor.notna() & fwd.notna()
        f, r = factor.loc[valid], fwd.loc[valid]
        return {
            "ic": ic_score(f, r),
            "turnover": turnover_score(f),
            **_backtest(f, r, transaction_cost),
        }

    per_factor_rows = []
    ensemble_rows = []
    for h in horizons:
        fwd = {p: _compute_forward(data[p], h) for p in periods}
        ens = {p: _ensemble(factor_frames[p], smooth_span) for p in periods}
        stats = {p: _period_stats(ens[p], fwd[p]) for p in periods}
        ensemble_rows.append({
            "horizon": h,
            "train_ic": stats["train"]["ic"],
            "train_sharpe": stats["train"]["sharpe"],
            "train_cost_adj_return": stats["train"]["cost_adjusted_return"],
            "val_ic": stats["val"]["ic"],
            "val_sharpe": stats["val"]["sharpe"],
            "val_cost_adj_return": stats["val"]["cost_adjusted_return"],
            "test_ic": stats["test"]["ic"],
            "test_sharpe": stats["test"]["sharpe"],
            "test_cost_adj_return": stats["test"]["cost_adjusted_return"],
            "test_turnover": stats["test"]["turnover"],
            "test_max_drawdown": stats["test"]["max_drawdown"],
        })

        for fname in factor_frames["test"]:
            row_expr = lib.loc[lib["factor"] == fname, "expression"].values[0]
            fstats = {p: _period_stats(factor_frames[p][fname], fwd[p]) for p in periods}
            per_factor_rows.append({
                "factor": fname,
                "expression": row_expr,
                "horizon": h,
                "train_ic": fstats["train"]["ic"],
                "train_sharpe": fstats["train"]["sharpe"],
                "train_cost_adj_return": fstats["train"]["cost_adjusted_return"],
                "val_ic": fstats["val"]["ic"],
                "val_sharpe": fstats["val"]["sharpe"],
                "val_cost_adj_return": fstats["val"]["cost_adjusted_return"],
                "test_ic": fstats["test"]["ic"],
                "test_sharpe": fstats["test"]["sharpe"],
                "test_cost_adj_return": fstats["test"]["cost_adjusted_return"],
                "test_turnover": fstats["test"]["turnover"],
                "test_max_drawdown": fstats["test"]["max_drawdown"],
            })

    # Realistic non-overlapping hold backtest for the ensemble.
    hold_rows = []
    daily_returns = data["test"]["return"]
    for h in horizons:
        ens_test = _ensemble(factor_frames["test"], smooth_span)
        hold = _hold_backtest(ens_test, daily_returns, h, transaction_cost)
        hold_rows.append({"horizon": h, **hold})

    return pd.DataFrame(ensemble_rows), pd.DataFrame(per_factor_rows), pd.DataFrame(hold_rows)


def _find_iteration_libraries(loop_dir: Path) -> list[tuple[int, Path]]:
    """Return (iteration_number, library_path) for all iter_NNNN directories."""
    libs: list[tuple[int, Path]] = []
    if not loop_dir.exists():
        return libs
    for child in loop_dir.iterdir():
        if not child.is_dir():
            continue
        m = re.match(r"iter_(\d+)", child.name)
        if not m:
            continue
        iter_num = int(m.group(1))
        combined = child / "combined_library.csv"
        cleaned = child / "cleaned_library.csv"
        if combined.exists():
            libs.append((iter_num, combined))
        elif cleaned.exists():
            libs.append((iter_num, cleaned))
    libs.sort(key=lambda x: x[0])
    return libs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config with val_date")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--loops", type=str, nargs="+", default=["5d", "10d", "20d"])
    parser.add_argument(
        "--loop-dirs",
        type=Path,
        nargs="+",
        default=[
            Path("china_a_share_alpha_output/factor_mining_loop"),
            Path("china_a_share_alpha_output/factor_mining_loop_10d"),
            Path("china_a_share_alpha_output/factor_mining_loop_20d"),
        ],
    )
    parser.add_argument("--horizons", type=int, nargs="+", default=[5, 10, 20])
    parser.add_argument("--transaction-cost", type=float, default=0.001)
    parser.add_argument("--smooth-span", type=int, default=10)
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print("Loading data panel (one-time)...")
    train, val, test = load_tushare_data_with_val(cfg)
    data = {"train": train, "val": val, "test": test}
    print("Data loaded.")

    summary_rows = []
    loop_mapping = dict(zip(args.loops, args.loop_dirs))

    for loop_name, loop_dir in loop_mapping.items():
        print(f"\n=== {loop_name} loop: {loop_dir} ===")
        libs = _find_iteration_libraries(loop_dir)
        print(f"Found {len(libs)} iteration libraries")
        for iter_num, lib_path in libs:
            print(f"  Auditing iter {iter_num:04d} ({lib_path.name})...")
            lib = _load_library(lib_path)
            ens_df, pf_df, hold_df = _evaluate_library(
                lib, data, args.horizons, args.transaction_cost, args.smooth_span
            )

            audit_dir = args.output_root / loop_name / f"iter_{iter_num:04d}"
            audit_dir.mkdir(parents=True, exist_ok=True)
            ens_df.to_csv(audit_dir / "ensemble_horizon.csv", index=False)
            pf_df.to_csv(audit_dir / "per_factor_horizon.csv", index=False)
            hold_df.to_csv(audit_dir / "hold_ensemble_horizon.csv", index=False)

            for _, r in ens_df.iterrows():
                summary_rows.append({
                    "loop": loop_name,
                    "iteration": iter_num,
                    "horizon": int(r["horizon"]),
                    "n_factors": len(lib),
                    "train_ic": r["train_ic"],
                    "train_sharpe": r["train_sharpe"],
                    "train_cost_adj_return": r["train_cost_adj_return"],
                    "val_ic": r["val_ic"],
                    "val_sharpe": r["val_sharpe"],
                    "val_cost_adj_return": r["val_cost_adj_return"],
                    "test_ic": r["test_ic"],
                    "test_sharpe": r["test_sharpe"],
                    "test_cost_adj_return": r["test_cost_adj_return"],
                    "test_turnover": r["test_turnover"],
                    "test_max_drawdown": r["test_max_drawdown"],
                })
            for _, r in hold_df.iterrows():
                # Merge hold metrics into the matching summary row.
                for row in summary_rows:
                    if (
                        row["loop"] == loop_name
                        and row["iteration"] == iter_num
                        and row["horizon"] == int(r["horizon"])
                    ):
                        row["hold_sharpe"] = r["sharpe"]
                        row["hold_annualized_return"] = r["annualized_return"]
                        row["hold_cost_adj_return"] = r["cost_adjusted_return"]
                        row["hold_max_drawdown"] = r["max_drawdown"]

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(args.output_root / "batch_audit_summary.csv", index=False)

    # Markdown report.
    lines = [
        "# Batch Multi-Horizon Audit Summary (5d / 10d / 20d)",
        "",
        "Equal-weight ensemble evaluated on train / validation / test folds.",
        "",
        "## Per-Iteration Ensemble Metrics",
        "",
        "| Loop | Iter | Horizon | N | Train IC | Train Sharpe | Val IC | Val Sharpe | Test IC | Test Sharpe | Cost-adj | Turnover | Max DD | Hold Sharpe | Hold Return | Hold DD |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['loop']} | {r['iteration']} | {r['horizon']}d | {r['n_factors']} | "
            f"{r['train_ic']:.4f} | {r['train_sharpe']:.4f} | "
            f"{r['val_ic']:.4f} | {r['val_sharpe']:.4f} | "
            f"{r['test_ic']:.4f} | {r['test_sharpe']:.4f} | "
            f"{r['test_cost_adj_return']:.2%} | {r['test_turnover']:.4f} | {r['test_max_drawdown']:.2%} | "
            f"{r.get('hold_sharpe', 0):.4f} | {r.get('hold_annualized_return', 0):.2%} | {r.get('hold_max_drawdown', 0):.2%} |"
        )
    lines += ["", f"Full summary CSV: `{args.output_root / 'batch_audit_summary.csv'}`"]
    (args.output_root / "batch_audit_summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"\nDone. Summary: {args.output_root / 'batch_audit_summary.csv'}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
