"""Export factor values for external quantitative algorithms.

Loads the latest data, evaluates every unique expression from the given factor
libraries, computes cross-sectional z-scores, and writes a panel CSV/Parquet
file suitable for ML models, portfolio optimizers, or other backtest engines.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config")
    parser.add_argument("--library", type=Path, action="append", required=True)
    parser.add_argument("--label", action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/factor_exports"))
    parser.add_argument("--format", choices=["csv", "parquet", "both"], default="both")
    args = parser.parse_args()

    if len(args.library) != len(args.label):
        raise ValueError("--library and --label must have the same count")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    train, val, test = load_tushare_data_with_val(cfg)
    # Use the union of train+val+test for a complete panel; external users can
    # filter by date themselves.
    all_data = pd.concat([train, val, test]).sort_index()

    unique_expressions: dict[str, str] = {}
    library_index: list[dict] = []
    for lib_path, label in zip(args.library, args.label):
        lib = pd.read_csv(lib_path)
        if "factor" not in lib.columns:
            lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")
        lib_exprs = {}
        for _, row in lib.iterrows():
            expr = row["expression"]
            base_name = row["factor"]
            # Make a globally unique name to avoid collisions across libraries.
            name = f"{label}_{base_name}"
            unique_expressions[name] = expr
            lib_exprs[base_name] = name
        library_index.append({"label": label, "path": str(lib_path), "factor_map": lib_exprs})

    # Evaluate each unique expression.
    factor_frames = {}
    for name, expr in unique_expressions.items():
        try:
            factor_frames[name] = _zscore(parse_expression(expr).eval(all_data)).rename(name)
        except Exception as exc:
            print(f"Skipping {name}: {exc}")

    if not factor_frames:
        print("No valid factor expressions.")
        return 1

    panel = pd.concat(factor_frames.values(), axis=1)

    # Add combined signals (equal weight within each library).
    combined_cols = []
    for idx, lib_info in enumerate(library_index):
        lib_cols = [lib_info["factor_map"][base] for base in lib_info["factor_map"] if lib_info["factor_map"][base] in panel.columns]
        if lib_cols:
            combined_name = f"combined_{lib_info['label']}"
            panel[combined_name] = panel[lib_cols].mean(axis=1)
            combined_cols.append(combined_name)

    # Reset index to flat columns for external tools.
    panel_out = panel.reset_index()
    panel_out["date"] = panel_out["date"].dt.strftime("%Y-%m-%d")

    if args.format in ("csv", "both"):
        csv_path = args.output_dir / "factor_values.csv"
        panel_out.to_csv(csv_path, index=False)
        print(f"Wrote {csv_path}")
    if args.format in ("parquet", "both"):
        parquet_path = args.output_dir / "factor_values.parquet"
        # Parquet handles date index better; keep MultiIndex.
        panel.index = pd.MultiIndex.from_tuples(panel.index, names=["symbol", "date"])
        panel.to_parquet(parquet_path)
        print(f"Wrote {parquet_path}")

    # Metadata.
    meta = {
        "data_config": args.config,
        "output_dir": str(args.output_dir),
        "date_range": {
            "start": all_data.index.get_level_values("date").min().isoformat(),
            "end": all_data.index.get_level_values("date").max().isoformat(),
        },
        "unique_factors": len(unique_expressions),
        "factor_names": list(unique_expressions.keys()),
        "combined_signals": combined_cols,
        "libraries": library_index,
        "expressions": unique_expressions,
    }
    meta_path = args.output_dir / "factor_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Wrote {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
