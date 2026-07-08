"""One iteration of the continuous factor-mining loop.

The loop is designed around the loop-engineering principles:

1. STATE — durable memory across runs (`state.json` + `live_library.csv`).
2. TRIGGER — scheduled or manual invocation.
3. EVOLVE — run one seed of the enhanced factor loop, seeded with the live
   library from the previous iteration.
4. EVALUATE — clean the merged library on a hold-out validation fold and run
   an equal-weight combination.
5. DECIDE — promote the new library only if the test cost-adjusted return or
   Sharpe improves over the previous best.
6. REPORT — append a structured loop report.

No git mutations are performed automatically; human review is required before
committing a promoted genome.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import (
    load_tushare_data,
    load_tushare_data_with_val,
)
from china_a_share_alpha.factor.parser import parse_expression


DEFAULT_STATE = {
    "iteration": 0,
    "last_run": None,
    "best_test_sharpe": 0.0,
    "best_cost_adjusted_return": 0.0,
    "live_library_path": None,
    "history": [],
}


def load_state(state_path: Path) -> dict:
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_STATE.copy()


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def run_cmd(cmd: list[str], cwd: Path | None = None) -> str:
    """Run a command and return stdout; raise on error."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def merge_libraries(library_paths: list[Path], output_path: Path) -> int:
    """Merge multiple factor library CSVs, deduplicating by expression."""
    frames = []
    for p in library_paths:
        if not p.exists():
            continue
        df = pd.read_csv(p)
        if "factor" not in df.columns:
            df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")
        frames.append(df)
    if not frames:
        return 0
    merged = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["expression"])
    merged["rank"] = range(1, len(merged) + 1)
    merged.to_csv(output_path, index=False)
    return len(merged)


def add_high_zscore(library_path: Path, output_path: Path) -> None:
    df = pd.read_csv(library_path)
    if "factor" not in df.columns:
        df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")
    high = pd.DataFrame(
        [
            {
                "factor": "high_zscore_20",
                "expression": "cs_rank(ts_zscore(high, 20))",
                "train_ic": 0.0,
                "test_ic": 0.0,
                "test_sharpe": 0.0,
                "test_turnover": 0.0,
            }
        ]
    )
    merged = pd.concat([df, high], ignore_index=True)
    merged["rank"] = range(1, len(merged) + 1)
    merged.to_csv(output_path, index=False)


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def semantic_deduplicate(
    library_path: Path,
    data_config: dict,
    output_path: Path,
    corr_threshold: float = 0.95,
) -> int:
    """Drop semantically duplicate expressions based on train-set correlation.

    Keeps the first expression in library order and removes any later
    expression whose absolute Spearman correlation with an already-kept
    expression exceeds ``corr_threshold``.
    """
    if isinstance(data_config, (str, Path)):
        with open(data_config, "r", encoding="utf-8") as f:
            data_config = yaml.safe_load(f)

    df = pd.read_csv(library_path)
    if "factor" not in df.columns:
        df["factor"] = df["rank"].apply(lambda r: f"factor_{r}")

    if "val_date" in data_config:
        train, _, _ = load_tushare_data_with_val(data_config)
    else:
        train, _ = load_tushare_data(data_config)

    frames = []
    frame_meta = []  # (unique_col_name, original_factor_name, row)
    for idx, row in df.iterrows():
        try:
            expr = parse_expression(row["expression"])
            f = _zscore(expr.eval(train))
            base = row["factor"]
            # Ensure unique column names in case of duplicate factor labels.
            col_name = f"{base}_dup{idx}" if base in [m[0] for m in frame_meta] else base
            frames.append(f.rename(col_name))
            frame_meta.append((col_name, base, row))
        except Exception as exc:
            print(f"  [dedup] skipping invalid expression {row.get('factor')}: {exc}")

    if not frames:
        df.to_csv(output_path, index=False)
        return 0

    mat = pd.concat(frames, axis=1).dropna()

    # Drop degenerate columns (constant or zero variance) before correlation checks.
    valid_meta = []
    for col_name, base, row in frame_meta:
        if col_name not in mat.columns:
            continue
        std = mat[col_name].std()
        if pd.isna(std) or float(std) < 1e-12:
            print(f"  [dedup] dropping {base}: constant/degenerate series")
        else:
            valid_meta.append((col_name, base, row))
    mat = mat[[m[0] for m in valid_meta]]

    kept_rows = []
    kept_cols = []
    for col_name, base, row in valid_meta:
        if kept_cols:
            corr_values = mat[kept_cols].corrwith(mat[col_name], method="spearman").abs()
            corr_max = float(corr_values.max()) if not corr_values.empty else 0.0
            if pd.isna(corr_max):
                corr_max = 0.0
        else:
            corr_max = 0.0
        if corr_max < corr_threshold:
            kept_rows.append(row)
            kept_cols.append(col_name)
        else:
            print(f"  [dedup] dropping {base} (max |corr|={corr_max:.3f})")

    out = pd.DataFrame(kept_rows)
    out["rank"] = range(1, len(out) + 1)
    out.to_csv(output_path, index=False)
    return len(out)


def parse_combination_result(output_dir: Path) -> dict:
    result_file = output_dir / "combination_result.json"
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = {r["period"]: r for r in data["results"]}
    return {
        "test_sharpe": results.get("test", {}).get("sharpe", 0.0),
        "test_cost_adjusted_return": results.get("test", {}).get(
            "cost_adjusted_return", 0.0
        ),
        "test_ic": results.get("test", {}).get("ic", 0.0),
        "train_sharpe": results.get("train", {}).get("sharpe", 0.0),
        "train_cost_adjusted_return": results.get("train", {}).get(
            "cost_adjusted_return", 0.0
        ),
        "selection_correlation_max": data.get("selection_correlation_max", 1.0),
    }


def run_loop_iteration(
    cfg: dict,
    output_dir: Path,
    dry_run: bool = False,
    use_live_seed: bool = True,
) -> dict:
    """Execute one factor-mining loop iteration."""
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "state.json"
    state = load_state(state_path)

    iteration = state["iteration"] + 1
    iteration_dir = output_dir / f"iter_{iteration:04d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    live_library_path = (
        Path(state["live_library_path"])
        if state.get("live_library_path") and use_live_seed
        else None
    )

    # Build the seed library by merging the live library with any extra seed
    # libraries configured for this iteration (e.g., domain-specific priors).
    seed_library_path = iteration_dir / "seed_library.csv"
    extra_seed_paths = [
        Path(p) for p in cfg.get("extra_seed_libraries", []) if Path(p).exists()
    ]
    seed_sources = []
    if live_library_path and live_library_path.exists():
        seed_sources.append(live_library_path)
    seed_sources.extend(extra_seed_paths)
    if seed_sources:
        merge_libraries(seed_sources, seed_library_path)

    # ---- 1. EVOLVE ----
    seed = cfg.get("seed_base", 42) + iteration
    seed_output = iteration_dir / "evolution"
    seed_output.mkdir(parents=True, exist_ok=True)

    evolve_cmd = [
        sys.executable,
        "-u",
        "-W",
        "ignore",
        "-m",
        "china_a_share_alpha.scripts.run_enhanced_factor_loop",
        cfg["evolution_config"],
        "--output-dir",
        str(seed_output),
        "--seed",
        str(seed),
    ]
    if seed_library_path.exists() and not dry_run:
        evolve_cmd += ["--seed-library", str(seed_library_path)]

    print(f"[iter {iteration}] Running evolution seed={seed} ...")
    if not dry_run:
        run_cmd(evolve_cmd)
    else:
        print("  (dry-run: skipped evolution)")

    new_leaderboard = seed_output / "factor_loop_leaderboard.csv"

    # ---- 2. MERGE ----
    merged_library = iteration_dir / "merged_library.csv"
    merge_paths = [new_leaderboard]
    if live_library_path and live_library_path.exists():
        merge_paths.append(live_library_path)
    n_merged = merge_libraries(merge_paths, merged_library)
    print(f"[iter {iteration}] Merged library: {n_merged} expressions")

    # ---- 3. CLEAN ----
    cleaned_library = iteration_dir / "cleaned_library.csv"
    clean_cmd = [
        sys.executable,
        "-u",
        "-W",
        "ignore",
        "-m",
        "china_a_share_alpha.scripts.clean_factor_library",
        cfg["data_config"],
        "--library",
        str(merged_library),
        "--output",
        str(cleaned_library),
        "--min-train-ic",
        str(cfg.get("min_train_ic", 0.001)),
        "--min-test-ic",
        str(cfg.get("min_test_ic", 0.001)),
        "--min-test-sharpe",
        str(cfg.get("min_test_sharpe", 0.0)),
        "--max-turnover",
        str(cfg.get("max_turnover", 0.5)),
        "--max-nan-frac",
        str(cfg.get("max_nan_frac", 0.5)),
        "--min-daily-coverage",
        str(cfg.get("min_daily_coverage", 0.8)),
    ]
    if cfg.get("min_val_ic") is not None:
        clean_cmd += ["--min-val-ic", str(cfg["min_val_ic"])]
    if cfg.get("min_val_sharpe") is not None:
        clean_cmd += ["--min-val-sharpe", str(cfg["min_val_sharpe"])]

    print(f"[iter {iteration}] Cleaning merged library ...")
    run_cmd(clean_cmd)
    n_cleaned = len(pd.read_csv(cleaned_library)) if cleaned_library.exists() else 0
    print(f"[iter {iteration}] Cleaned library: {n_cleaned} expressions")

    # ---- 4. ADD high_zscore + SEMANTIC DEDUP ----
    combined_pre = iteration_dir / "combined_library_pre.csv"
    add_high_zscore(cleaned_library, combined_pre)

    combined_library = iteration_dir / "combined_library.csv"
    n_deduped = semantic_deduplicate(
        combined_pre,
        cfg["data_config"],
        combined_library,
        corr_threshold=cfg.get("semantic_dedup_corr_threshold", 0.95),
    )
    print(f"[iter {iteration}] After semantic dedup: {n_deduped} expressions")

    combo_output = iteration_dir / "combination"
    combo_cmd = [
        sys.executable,
        "-u",
        "-W",
        "ignore",
        "-m",
        "china_a_share_alpha.scripts.run_factor_combination",
        cfg["data_config"],
        "--factor-csv",
        str(combined_library),
        "--top-n",
        str(cfg.get("top_n", 10)),
        "--weight-method",
        cfg.get("weight_method", "equal"),
        "--smooth-span",
        str(cfg.get("smooth_span", 10)),
        "--output-dir",
        str(combo_output),
    ]
    if cfg.get("sort_by"):
        combo_cmd += ["--sort-by", cfg["sort_by"]]
    if cfg.get("max_pairwise_corr") is not None:
        combo_cmd += [
            "--max-pairwise-corr",
            str(cfg["max_pairwise_corr"]),
        ]

    print(f"[iter {iteration}] Running combination ...")
    run_cmd(combo_cmd)
    metrics = parse_combination_result(combo_output)



    # ---- 5. DECIDE with gates ----
    improvement_sharpe = metrics["test_sharpe"] - state["best_test_sharpe"]
    improvement_return = (
        metrics["test_cost_adjusted_return"] - state["best_cost_adjusted_return"]
    )

    gates = {
        "train_sharpe_positive": metrics["train_sharpe"]
        > cfg.get("min_train_sharpe_gate", 0.0),
        "min_cleaned_count": n_deduped >= cfg.get("min_cleaned_gate", 1),
        "max_corr_ok": metrics["selection_correlation_max"]
        <= cfg.get("max_selection_correlation_gate", 1.0),
    }
    gates_passed = all(gates.values())

    improved = (
        improvement_sharpe >= cfg.get("promote_sharpe_threshold", 0.05)
        or improvement_return >= cfg.get("promote_return_threshold", 0.005)
    )
    promote = improved and gates_passed

    if promote:
        new_live = output_dir / "live_library.csv"
        pd.read_csv(combined_library).to_csv(new_live, index=False)
        state["live_library_path"] = str(new_live)
        state["best_test_sharpe"] = float(metrics["test_sharpe"])
        state["best_cost_adjusted_return"] = float(metrics["test_cost_adjusted_return"])
        print(
            f"[iter {iteration}] PROMOTED new live library "
            f"(sharpe={metrics['test_sharpe']:.3f}, "
            f"cost_adj={metrics['test_cost_adjusted_return']:.3%})"
        )
    else:
        reasons = []
        if not improved:
            reasons.append("not improved")
        for name, ok in gates.items():
            if not ok:
                reasons.append(name)
        reason_str = ", ".join(reasons) if reasons else "unknown"
        print(
            f"[iter {iteration}] KEPT existing live library "
            f"(reason: {reason_str}; "
            f"new sharpe={metrics['test_sharpe']:.3f}, "
            f"new cost_adj={metrics['test_cost_adjusted_return']:.3%}; "
            f"best sharpe={state['best_test_sharpe']:.3f}, "
            f"best cost_adj={state['best_cost_adjusted_return']:.3%})"
        )

    # ---- 6. STATE + REPORT ----
    entry = {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "evolution_dir": str(seed_output),
        "n_merged": n_merged,
        "n_cleaned": n_cleaned,
        "n_deduped": n_deduped,
        "metrics": metrics,
        "gates": {k: bool(v) for k, v in gates.items()},
        "improved": improved,
        "promoted": promote,
    }
    state["iteration"] = iteration
    state["last_run"] = entry["timestamp"]
    state["history"].append(entry)
    save_state(state_path, state)

    report_path = write_report(output_dir, iteration_dir, state, entry, promote)
    print(f"[iter {iteration}] Report: {report_path}")

    return state


def write_report(
    output_dir: Path,
    iteration_dir: Path,
    state: dict,
    entry: dict,
    promoted: bool,
) -> Path:
    """Write a human-readable loop report."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"loop_report_{ts}.md"
    metrics = entry["metrics"]

    lines = [
        f"# Factor Mining Loop Report — Iteration {entry['iteration']}",
        "",
        f"- **Timestamp**: {entry['timestamp']}",
        f"- **Evolution seed**: {entry['seed']}",
        f"- **Merged expressions**: {entry['n_merged']}",
        f"- **Cleaned expressions**: {entry['n_cleaned']}",
        f"- **Deduplicated expressions**: {entry.get('n_deduped', entry['n_cleaned'])}",
        f"- **Promoted**: {'YES' if promoted else 'NO'}",
        "",
        "## Metrics",
        "",
        "| Period | Sharpe | Cost-adj return | IC |",
        "|---|---|---|---|",
        f"| Train | {metrics['train_sharpe']:.4f} | {metrics['train_cost_adjusted_return']:.4f} | - |",
        f"| Test | {metrics['test_sharpe']:.4f} | {metrics['test_cost_adjusted_return']:.4f} | {metrics['test_ic']:.4f} |",
        "",
        "## Gates",
        "",
        f"- train_sharpe_positive: {entry['gates']['train_sharpe_positive']}",
        f"- min_cleaned_count: {entry['gates']['min_cleaned_count']}",
        f"- max_corr_ok: {entry['gates']['max_corr_ok']} (max corr = {metrics.get('selection_correlation_max', 1.0):.4f})",
        "",
        "## Decision",
        "",
    ]
    if promoted:
        lines += [
            "The new library improved on the previous best and has been promoted to live library.",
            "",
            f"- New best Sharpe: {state['best_test_sharpe']:.4f}",
            f"- New best cost-adjusted return: {state['best_cost_adjusted_return']:.4f}",
            "",
            "> Human gate: review the new `live_library.csv` before committing.",
        ]
    else:
        lines += [
            "The new library did not improve on the previous best. The existing live library is retained.",
            "",
            f"- Previous best Sharpe: {state['best_test_sharpe']:.4f}",
            f"- Previous best cost-adjusted return: {state['best_cost_adjusted_return']:.4f}",
        ]

    lines += [
        "",
        "## Artifacts",
        "",
        f"- Evolution: `{iteration_dir / 'evolution'}`",
        f"- Merged library: `{iteration_dir / 'merged_library.csv'}`",
        f"- Cleaned library: `{iteration_dir / 'cleaned_library.csv'}`",
        f"- Combination: `{iteration_dir / 'combination'}`",
        "",
        "---",
        "",
        "Next iteration will use the current live library as its seed.",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Loop config YAML")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("china_a_share_alpha_output/factor_mining_loop"),
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip evolution")
    parser.add_argument(
        "--no-live-seed",
        action="store_true",
        help="Start evolution from scratch instead of seeding with the live library",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    run_loop_iteration(
        cfg,
        args.output_dir,
        dry_run=args.dry_run,
        use_live_seed=not args.no_live_seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
