"""Continuous multi-seed factor mining runner.

Runs the GP factor loop for multiple seeds, merges the resulting leaderboards
into a single global factor library, and optionally re-runs the backtest
comparison against the original hand-designed factors.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from china_a_share_alpha.run_factor_loop import run_config


def load_config(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def merge_leaderboards(library_dir: Path) -> pd.DataFrame:
    """Merge all seed leaderboards into one global library and deduplicate."""
    frames: list[pd.DataFrame] = []
    for csv in sorted(library_dir.glob("leaderboard_seed_*.csv")):
        frames.append(pd.read_csv(csv))
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    # Prefer candidates with positive and stable test IC.
    combined = combined[
        combined["train_ic"].notna()
        & combined["test_ic"].notna()
        & (combined["train_ic"] * combined["test_ic"] >= 0)
    ]
    combined = combined.drop_duplicates(subset=["expression"], keep="first")
    combined = combined.sort_values("test_ic", ascending=False).reset_index(drop=True)
    combined["rank"] = range(1, len(combined) + 1)
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run continuous multi-seed factor mining on Tushare data"
    )
    parser.add_argument("config", type=Path, help="Base YAML config")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3],
                        help="Seeds to run")
    parser.add_argument("--library-dir", type=Path,
                        default=Path("./china_a_share_alpha_output/tushare_factor_library"),
                        help="Directory to store merged factor library")
    parser.add_argument("--backtest", action="store_true",
                        help="Run the Tushare backtest comparison after mining")
    args = parser.parse_args()

    base_cfg = load_config(args.config)
    args.library_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[dict[str, Any]] = []
    for seed in args.seeds:
        cfg = dict(base_cfg)
        cfg["seed"] = seed
        cfg["output_dir"] = str(args.library_dir / f"seed_{seed}")
        cfg["repo_dir"] = str(args.library_dir / f".semas_repo_seed_{seed}")
        print(f"\n=== Running factor loop with seed {seed} ===")
        result = run_config(cfg)
        all_results.append(result)
        # Copy seed leaderboard to a predictable name.
        src = Path(cfg["output_dir"]) / "factor_loop_leaderboard.csv"
        dst = args.library_dir / f"leaderboard_seed_{seed}.csv"
        if src.exists():
            pd.read_csv(src).to_csv(dst, index=False)

    global_library = merge_leaderboards(args.library_dir)
    library_path = args.library_dir / "factor_library.csv"
    global_library.to_csv(library_path, index=False)
    print(f"\nGlobal factor library: {library_path} ({len(global_library)} unique factors)")

    if args.backtest and not global_library.empty:
        print("\nRunning backtest comparison with evolved library ...")
        import subprocess
        import sys

        backtest_cmd = [
            sys.executable, "-m", "china_a_share_alpha.scripts.run_tushare_backtest",
            "--start-date", base_cfg.get("start_date", "20210601"),
            "--end-date", base_cfg.get("end_date", "20260601"),
            "--split-date", base_cfg.get("split_date", "20240101"),
            "--evolved-csv", str(library_path),
            "--evolved-top-n", "20",
        ]
        subprocess.run(backtest_cmd, check=False)

    summary = {
        "seeds": args.seeds,
        "library_size": len(global_library),
        "library_path": str(library_path),
        "best_per_seed": [r["best"] for r in all_results],
    }
    summary_path = args.library_dir / "continuous_loop_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
