"""Generate latest-date stock picks from one or more factor libraries.

Loads the most recent data, evaluates each expression, builds the library's
combined signal, and outputs the top-N stocks ranked by signal strength.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1:
        return s
    return s.groupby(level="symbol").transform(lambda x: x.ewm(span=span, min_periods=1).mean())


def _load_stock_names(cache_dir: Path) -> pd.DataFrame:
    """Best-effort load of ts_code -> name mapping from cached stock_basic."""
    basic_path = cache_dir / "stock_basic.csv"
    if basic_path.exists():
        try:
            df = pd.read_csv(basic_path, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.read_csv(basic_path, dtype=str, encoding="utf-8-sig")
        if "ts_code" in df.columns and "name" in df.columns:
            return df[["ts_code", "name"]].drop_duplicates()
    return pd.DataFrame(columns=["ts_code", "name"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config")
    parser.add_argument("--library", type=Path, action="append", required=True,
                        help="Factor library CSV (may be repeated); label with --label")
    parser.add_argument("--label", action="append", required=True,
                        help="Label for each --library")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/latest_picks"))
    args = parser.parse_args()

    if len(args.library) != len(args.label):
        raise ValueError("--library and --label must have the same count")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    train, val, test = load_tushare_data_with_val(cfg)
    latest_date = test.index.get_level_values("date").max()
    cache_dir = Path(cfg.get("cache_dir", "china_a_share_alpha_output/tushare_backtest/tushare_cache"))
    names = _load_stock_names(cache_dir)

    all_rows = []
    for lib_path, label in zip(args.library, args.label):
        lib = pd.read_csv(lib_path)
        if "factor" not in lib.columns:
            lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

        frames = []
        weights = []
        for _, row in lib.iterrows():
            try:
                f = _zscore(parse_expression(row["expression"]).eval(test)).rename(row["factor"])
                frames.append(f)
                weights.append(float(row.get("weight", 1.0)))
            except Exception as exc:
                print(f"[{label}] Skipping {row.get('factor')}: {exc}")
        if not frames:
            continue
        mat = pd.concat(frames, axis=1).dropna()
        weights = np.array(weights) / sum(weights)
        combined = _smooth((mat @ weights).clip(-5, 5), args.smooth_span)

        latest = combined.xs(latest_date, level="date").dropna().sort_values(ascending=False)
        picks = latest.head(args.top_n).reset_index()
        picks.columns = ["ts_code", "signal"]
        picks["rank"] = range(1, len(picks) + 1)
        picks["horizon_label"] = label
        picks["date"] = latest_date.strftime("%Y-%m-%d")
        if not names.empty:
            picks = picks.merge(names, on="ts_code", how="left")
        all_rows.append(picks)
        out_path = args.output_dir / f"top{args.top_n}_{label}.csv"
        picks.to_csv(out_path, index=False)
        print(f"\n=== {label} (latest {latest_date.date()}) ===")
        print(picks.head(args.top_n).to_string(index=False))

    if all_rows:
        pd.concat(all_rows, ignore_index=True).to_csv(
            args.output_dir / "all_picks.csv", index=False
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
