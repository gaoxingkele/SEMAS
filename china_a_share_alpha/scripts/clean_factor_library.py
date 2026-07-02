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

from china_a_share_alpha.data.tushare_loader import (
    load_tushare_data,
    load_tushare_data_with_val,
)
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


def _is_degenerate(factor: pd.Series, min_std: float = 1e-8, max_nan_frac: float = 0.2, min_daily_coverage: float = 0.5) -> bool:
    """Check whether a factor series is constant, mostly NaN, or too sparse."""
    if factor is None or factor.empty:
        return True
    if factor.isna().mean() > max_nan_frac:
        return True
    finite = factor.dropna()
    if finite.empty:
        return True
    if not np.isfinite(finite).all():
        return True
    if float(finite.std()) < min_std:
        return True
    # Require reasonable cross-sectional coverage on most days.
    coverage = factor.groupby(level="date").apply(lambda s: s.notna().mean())
    if coverage.mean() < min_daily_coverage:
        return True
    return False


def clean_library(
    cfg: dict,
    library_path: Path,
    output_path: Path,
    min_train_ic: float = 0.005,
    min_test_ic: float = 0.003,
    min_test_sharpe: float = 0.0,
    min_val_ic: float = 0.0,
    min_val_sharpe: float = 0.0,
    max_turnover: float = 0.5,
    max_nan_frac: float = 0.2,
    min_daily_coverage: float = 0.5,
) -> pd.DataFrame:
    """Load a factor library, evaluate each candidate, and write a cleaned CSV.

    If ``val_date`` is present in ``cfg`` the loader returns train/val/test
    panels and the cleaner uses the validation fold for selection, keeping the
    final test set fully held out.
    """
    if "val_date" in cfg:
        train, val, test = load_tushare_data_with_val(cfg)
    else:
        train, test = load_tushare_data(cfg)
        val = None
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
            f_val = expr.eval(val) if val is not None else None
        except Exception as exc:
            skipped_reasons.append((name, "eval_error", str(exc)))
            continue

        if _is_degenerate(f_train, max_nan_frac=max_nan_frac, min_daily_coverage=min_daily_coverage):
            skipped_reasons.append((name, "degenerate_train", expr_str))
            continue
        if _is_degenerate(f_test, max_nan_frac=max_nan_frac, min_daily_coverage=min_daily_coverage):
            skipped_reasons.append((name, "degenerate_test", expr_str))
            continue
        if f_val is not None and _is_degenerate(f_val, max_nan_frac=max_nan_frac, min_daily_coverage=min_daily_coverage):
            skipped_reasons.append((name, "degenerate_val", expr_str))
            continue

        train_ic = ic_score(f_train, train["forward_return"])
        test_ic = ic_score(f_test, test["forward_return"])
        test_turnover = turnover_score(f_test)
        bt = run_long_short_backtest(f_test, test["forward_return"], transaction_cost=0.001)
        test_sharpe = bt.get("sharpe", 0.0)

        record = {
            **row.to_dict(),
            "train_ic": train_ic,
            "test_ic": test_ic,
            "test_turnover": test_turnover,
            "test_sharpe": test_sharpe,
        }

        if f_val is not None:
            val_ic = ic_score(f_val, val["forward_return"])
            val_turnover = turnover_score(f_val)
            val_bt = run_long_short_backtest(f_val, val["forward_return"], transaction_cost=0.001)
            val_sharpe = val_bt.get("sharpe", 0.0)
            record.update({
                "val_ic": val_ic,
                "val_turnover": val_turnover,
                "val_sharpe": val_sharpe,
            })
            if not (
                abs(train_ic) >= min_train_ic
                and abs(val_ic) >= min_val_ic
                and val_sharpe >= min_val_sharpe
                and abs(test_ic) >= min_test_ic
                and test_sharpe >= min_test_sharpe
                and test_turnover <= max_turnover
                and np.sign(train_ic) == np.sign(val_ic)
            ):
                skipped_reasons.append(
                    (name, "below_threshold", f"train_ic={train_ic:.4f} val_ic={val_ic:.4f} val_sharpe={val_sharpe:.2f} test_ic={test_ic:.4f} sharpe={test_sharpe:.2f} turnover={test_turnover:.2f}")
                )
                continue
        else:
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

        kept.append(record)

    cleaned = pd.DataFrame(kept)
    if cleaned.empty:
        raise RuntimeError("No factors survived cleaning. Loosen thresholds.")

    sort_key = "val_ic" if "val_ic" in cleaned.columns else "test_ic"
    cleaned = cleaned.sort_values(sort_key, ascending=False).reset_index(drop=True)
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
    print_cols = ["rank", "factor", "train_ic", sort_key, "test_ic", "test_sharpe", "test_turnover", "expression"]
    print(cleaned[[c for c in print_cols if c in cleaned.columns]].head(10).to_string(index=False))
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean a factor library")
    parser.add_argument("config", help="YAML config with Tushare data settings")
    parser.add_argument("--library", type=Path, required=True, help="Input factor library CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output cleaned CSV")
    parser.add_argument("--min-train-ic", type=float, default=0.005)
    parser.add_argument("--min-test-ic", type=float, default=0.003)
    parser.add_argument("--min-test-sharpe", type=float, default=0.0)
    parser.add_argument("--min-val-ic", type=float, default=0.0)
    parser.add_argument("--min-val-sharpe", type=float, default=0.0)
    parser.add_argument("--max-turnover", type=float, default=0.5)
    parser.add_argument("--max-nan-frac", type=float, default=0.2)
    parser.add_argument("--min-daily-coverage", type=float, default=0.5)
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
        args.min_val_ic,
        args.min_val_sharpe,
        args.max_turnover,
        args.max_nan_frac,
        args.min_daily_coverage,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
