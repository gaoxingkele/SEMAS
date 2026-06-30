"""Build a robust multi-factor combination from a cleaned factor library.

This script deliberately avoids the overfitting risk of weight-space genetic
algorithms.  Instead it:

1. Selects the top-K factors by training-set IC (or ICIR).
2. Z-scores each factor cross-sectionally.
3. Averages them with equal weights.
4. Optionally smooths the combined signal with a per-symbol EMA.
5. Reports train and test long-short backtest metrics.

Equal weight + smoothing is a strong, under-fitted baseline: it keeps the
benefits of diversification without fitting noisy relative weights to the
training period.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1:
        return s
    return s.groupby(level="symbol").transform(
        lambda x: x.ewm(span=span, min_periods=1).mean()
    )


def _icir(factor: pd.Series, forward: pd.Series) -> float:
    df = pd.DataFrame({"factor": factor, "forward": forward}).dropna()
    per_day = df.groupby(level="date").apply(
        lambda g: g["factor"].corr(g["forward"]), include_groups=False
    )
    return float(per_day.mean() / (per_day.std() + 1e-8))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML config with Tushare data settings")
    parser.add_argument("--factor-csv", type=Path, required=True, help="Input factor library CSV")
    parser.add_argument("--top-n", type=int, default=5, help="Number of factors to combine")
    parser.add_argument("--sort-by", type=str, default="train_ic", choices=["train_ic", "train_icir", "test_ic"])
    parser.add_argument("--smooth-span", type=int, default=10, help="EMA span for smoothing (1 = none)")
    parser.add_argument("--output-dir", type=Path, default=Path("china_a_share_alpha_output/factor_combination"))
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    train, test = load_tushare_data(cfg)

    lib = pd.read_csv(args.factor_csv)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

    # Compute train ICIR if needed.
    if args.sort_by == "train_icir":
        icirs = []
        for _, row in lib.iterrows():
            try:
                f = parse_expression(row["expression"]).eval(train)
                icirs.append(_icir(f, train["forward_return"]))
            except Exception:
                icirs.append(np.nan)
        lib["train_icir"] = icirs

    lib = lib.sort_values(args.sort_by, ascending=False).head(args.top_n)

    results = []
    for label, data, fwd in [("train", train, train["forward_return"]), ("test", test, test["forward_return"])]:
        frames = []
        for _, row in lib.iterrows():
            try:
                f = parse_expression(row["expression"]).eval(data)
                frames.append(_zscore(f).rename(row["factor"]))
            except Exception as exc:
                print(f"Skipping {row['factor']} on {label}: {exc}")

        mat = pd.concat(frames, axis=1).dropna()
        fwd_aligned = fwd.loc[mat.index]

        combined = _smooth(mat.mean(axis=1), args.smooth_span)
        combined = combined.clip(-5, 5)

        bt = run_long_short_backtest(combined, fwd_aligned, transaction_cost=0.001)
        result = {
            "period": label,
            "n_factors": len(lib),
            "smooth_span": args.smooth_span,
            "ic": ic_score(combined, fwd_aligned),
            "turnover": turnover_score(combined),
            "sharpe": bt["sharpe"],
            "annualized_return": bt["annualized_return"],
            "cost_adjusted_return": bt["cost_adjusted_return"],
            "max_drawdown": bt["max_drawdown"],
        }
        results.append(result)
        print(f"\n{label.upper()}:")
        for k, v in result.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")

    out = {
        "config": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "selected_factors": lib[["factor", "train_ic", "test_ic", "expression"]].to_dict(orient="records"),
        "results": results,
    }
    with open(args.output_dir / "combination_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    lib.to_csv(args.output_dir / "selected_factors.csv", index=False)
    print(f"\nSaved results to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
