"""Clean a neutralized factor library by removing degenerate / noisy candidates.

A factor is kept only if it:
- evaluates without errors on both train and test sets,
- has finite train/test IC and Sharpe,
- is not constant (train std > threshold),
- passes minimum IC and Sharpe thresholds,
- does not contain suspicious constant operands in ts_corr / ts_cov.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest


def _has_constant_correlation(expr) -> bool:
    """Return True if expression contains ts_corr/ts_cov with a constant operand."""
    from china_a_share_alpha.factor.expression import (
        RollingBinaryOp,
        Const,
    )

    if isinstance(expr, RollingBinaryOp) and expr.op in ("ts_corr", "ts_cov"):
        if isinstance(expr.left, Const) or isinstance(expr.right, Const):
            return True
    # Recurse on children if available.
    for attr in ("child", "left", "right"):
        child = getattr(expr, attr, None)
        if child is not None and _has_constant_correlation(child):
            return True
    return False


def _is_degenerate(factor: pd.Series, min_std: float = 1e-8) -> bool:
    """Check whether a factor series is constant or mostly NaN."""
    if factor is None or factor.empty:
        return True
    if factor.isna().mean() > 0.5:
        return True
    finite = factor.dropna()
    if finite.empty:
        return True
    if not np.isfinite(finite).all():
        return True
    return float(finite.std()) < min_std


def clean_library(
    cfg: dict,
    library_path: Path,
    output_path: Path,
    min_train_ic: float = 0.005,
    min_test_ic: float = 0.003,
    min_test_sharpe: float = 0.0,
    max_turnover: float = 0.5,
) -> pd.DataFrame:
    """Load a factor library, evaluate each candidate, and write a cleaned CSV."""
    train, test = load_tushare_data(cfg)
    lib = pd.read_csv(library_path)

    # Try to identify a factor name column.
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

    kept = []
    skipped_reasons = []

    for _, row in lib.iterrows():
        name = row["factor"]
        expr_str = row["expression"]
        try:
            expr = parse_expression(expr_str)
        except Exception as exc:
            skipped_reasons.append((name, "parse_error", str(exc)))
            continue

        if _has_constant_correlation(expr):
            skipped_reasons.append((name, "constant_correlation", expr_str))
            continue

        try:
            f_train = expr.eval(train)
            f_test = expr.eval(test)
        except Exception as exc:
            skipped_reasons.append((name, "eval_error", str(exc)))
            continue

        if _is_degenerate(f_train) or _is_degenerate(f_test):
            skipped_reasons.append((name, "degenerate", expr_str))
            continue

        train_ic = ic_score(f_train, train["forward_return"])
        test_ic = ic_score(f_test, test["forward_return"])
        test_turnover = turnover_score(f_test)
        bt = run_long_short_backtest(f_test, test["forward_return"], transaction_cost=0.001)
        test_sharpe = bt.get("sharpe", 0.0)

        if not (
            abs(train_ic) >= min_train_ic
            and abs(test_ic) >= min_test_ic
            and test_sharpe >= min_test_sharpe
            and test_turnover <= max_turnover
        ):
            skipped_reasons.append(
                (name, "below_threshold", f"train_ic={train_ic:.4f} test_ic={test_ic:.4f} sharpe={test_sharpe:.2f} turnover={test_turnover:.2f}")
            )
            continue

        kept.append({
            **row.to_dict(),
            "train_ic": train_ic,
            "test_ic": test_ic,
            "test_turnover": test_turnover,
            "test_sharpe": test_sharpe,
        })

    cleaned = pd.DataFrame(kept)
    if cleaned.empty:
        raise RuntimeError("No factors survived cleaning. Loosen thresholds.")

    cleaned = cleaned.sort_values("test_ic", ascending=False).reset_index(drop=True)
    cleaned["rank"] = cleaned.index + 1
    cleaned.to_csv(output_path, index=False)

    summary = {
        "input_rows": int(len(lib)),
        "output_rows": int(len(cleaned)),
        "skipped": len(skipped_reasons),
        "skipped_reasons": skipped_reasons,
    }
    summary_path = output_path.with_name(output_path.stem + "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Kept {len(cleaned)} / {len(lib)} factors")
    print(f"Skipped reasons written to {summary_path}")
    print(cleaned[["rank", "factor", "train_ic", "test_ic", "test_sharpe", "test_turnover", "expression"]].head(10).to_string(index=False))
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean a factor library")
    parser.add_argument("config", help="YAML config with Tushare data settings")
    parser.add_argument("--library", type=Path, required=True, help="Input factor library CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output cleaned CSV")
    parser.add_argument("--min-train-ic", type=float, default=0.005)
    parser.add_argument("--min-test-ic", type=float, default=0.003)
    parser.add_argument("--min-test-sharpe", type=float, default=0.0)
    parser.add_argument("--max-turnover", type=float, default=0.5)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    clean_library(
        cfg,
        args.library,
        args.output,
        args.min_train_ic,
        args.min_test_ic,
        args.min_test_sharpe,
        args.max_turnover,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
