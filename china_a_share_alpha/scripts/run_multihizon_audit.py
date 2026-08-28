"""Multi-horizon audit for the live library.

Evaluates each selected factor and the equal-weight ensemble on 5-day,
10-day, and 20-day forward returns.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.backtest.position_schedule import backtest_schedule, prepare_fold
from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1:
        return s
    return s.groupby(level="symbol").transform(lambda x: x.ewm(span=span, min_periods=1).mean())


def _build_equal_weight_signal(
    factor_frames: dict[str, pd.Series],
    smooth_span: int,
    min_factor_coverage: float = 0.5,
) -> tuple[pd.Series, dict[str, Any]]:
    """Build an equal-weight signal without requiring a complete-case intersection."""
    if not factor_frames:
        raise ValueError("no valid factor series")
    if not 0 < min_factor_coverage <= 1:
        raise ValueError("min_factor_coverage must be in (0, 1]")

    mat = pd.concat(factor_frames, axis=1)
    required = max(1, math.ceil(len(factor_frames) * min_factor_coverage))
    available = mat.notna().sum(axis=1)
    valid = available >= required
    signal = mat.mean(axis=1, skipna=True).where(valid).dropna()
    if signal.empty:
        raise ValueError(
            "no rows meet factor coverage threshold " f"({required}/{len(factor_frames)} factors)"
        )

    receipt = {
        "n_factors": len(factor_frames),
        "min_required_factors": required,
        "candidate_rows": int(len(mat)),
        "valid_rows": int(valid.sum()),
        "valid_row_fraction": float(valid.mean()),
    }
    return _smooth(signal.clip(-5, 5), smooth_span), receipt


def evaluate_library_hold(
    library: pd.DataFrame,
    test_data: pd.DataFrame,
    horizon: int,
    transaction_cost: float,
    smooth_span: int,
    evaluation_mode: str,
    min_factor_coverage: float = 0.5,
    history_data: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Evaluate a library and return a structured, validity-aware receipt."""
    if evaluation_mode not in {"simple_hold", "dynamic_trim"}:
        raise ValueError(f"unsupported evaluation_mode: {evaluation_mode}")

    lib = library.copy()
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda rank: f"factor_{rank}")

    evaluation_data = test_data
    if history_data is not None:
        evaluation_data = pd.concat([history_data, test_data])
        evaluation_data = evaluation_data[~evaluation_data.index.duplicated(keep="last")]
        evaluation_data = evaluation_data.sort_index()

    factor_frames: dict[str, pd.Series] = {}
    errors = []
    for row_index, row in lib.reset_index(drop=True).iterrows():
        factor_name = str(row.get("factor", f"factor_{row_index + 1}"))
        unique_name = f"{factor_name}__row_{row_index + 1}"
        try:
            expr = parse_expression(row["expression"])
            factor_frames[unique_name] = _zscore(expr.eval(evaluation_data))
        except Exception as exc:
            errors.append({"factor": factor_name, "error": str(exc)})

    receipt: dict[str, Any] = {
        "valid": False,
        "evaluation_mode": evaluation_mode,
        "horizon": int(horizon),
        "transaction_cost": float(transaction_cost),
        "smooth_span": int(smooth_span),
        "min_factor_coverage": float(min_factor_coverage),
        "n_library_rows": int(len(lib)),
        "n_factors_evaluated": int(len(factor_frames)),
        "factor_errors": errors,
        "history_rows": int(len(evaluation_data) - len(test_data)),
    }
    try:
        min_required_library_factors = max(1, math.ceil(len(lib) * min_factor_coverage))
        receipt["min_required_library_factors"] = min_required_library_factors
        if len(factor_frames) < min_required_library_factors:
            raise ValueError(
                "insufficient valid factors: "
                f"{len(factor_frames)}/{len(lib)}; "
                f"required {min_required_library_factors}"
            )
        signal, coverage = _build_equal_weight_signal(
            factor_frames,
            smooth_span,
            min_factor_coverage,
        )
        signal = signal.reindex(test_data.index).dropna()
        if evaluation_mode == "dynamic_trim":
            metrics = _dynamic_trim_backtest(
                signal,
                test_data["return"],
                horizon,
                transaction_cost,
            )
        else:
            metrics = _hold_backtest(
                signal,
                test_data["return"],
                horizon,
                transaction_cost,
            )
        if metrics.get("n_observations", 0) <= 1:
            raise ValueError("hold backtest produced insufficient observations")
    except Exception as exc:
        receipt["error"] = str(exc)
        return receipt

    receipt.update(coverage)
    receipt.update(metrics)
    receipt["valid"] = True
    return receipt


def _compute_forward(data: pd.DataFrame, horizon: int) -> pd.Series:
    """Cumulative forward return over `horizon` trading days."""
    return data.groupby(level="symbol")["close"].pct_change(horizon).shift(-horizon)


def _backtest(factor: pd.Series, fwd: pd.Series, cost: float) -> dict:
    valid = factor.notna() & fwd.notna()
    f, r = factor.loc[valid], fwd.loc[valid]
    if f.empty:
        return {
            "sharpe": 0.0,
            "annualized_return": 0.0,
            "cost_adjusted_return": 0.0,
            "max_drawdown": 0.0,
        }
    bt = run_long_short_backtest(f, r, transaction_cost=cost)
    return {
        "sharpe": bt["sharpe"],
        "annualized_return": bt["annualized_return"],
        "cost_adjusted_return": bt["cost_adjusted_return"],
        "max_drawdown": bt["max_drawdown"],
    }


def _hold_backtest(
    signal: pd.Series,
    daily_returns: pd.Series,
    horizon: int,
    cost: float = 0.001,
) -> dict:
    """Hold top/bottom 20% cohorts with next-day return application."""
    panel = daily_returns.rename("return").to_frame()
    prepared = prepare_fold(
        name=f"simple_{horizon}d",
        signal=signal,
        panel=panel,
        horizon=horizon,
        selection_fraction=0.2,
    )
    return backtest_schedule(prepared, [1.0] * 10, transaction_cost=cost)


def _dynamic_trim_backtest(
    signal: pd.Series,
    daily_returns: pd.Series,
    horizon: int,
    cost: float = 0.001,
) -> dict:
    """Apply the fixed long-book trim schedule with next-day returns."""
    panel = daily_returns.rename("return").to_frame()
    prepared = prepare_fold(
        name=f"dynamic_trim_{horizon}d",
        signal=signal,
        panel=panel,
        horizon=horizon,
        selection_fraction=0.2,
    )
    schedule = [1.0, 1.0, 0.7, 0.7, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0]
    return backtest_schedule(prepared, schedule, transaction_cost=cost)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="YAML data config with val_date")
    parser.add_argument("--factor-csv", type=Path, required=True)
    parser.add_argument("--horizons", type=int, nargs="+", default=[5, 10, 20])
    parser.add_argument("--transaction-cost", type=float, default=0.001)
    parser.add_argument("--smooth-span", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    train, val, test = load_tushare_data_with_val(cfg)

    lib = pd.read_csv(args.factor_csv)
    if "factor" not in lib.columns:
        lib["factor"] = lib["rank"].apply(lambda r: f"factor_{r}")

    factor_frames = {"train": {}, "val": {}, "test": {}}
    expression_by_factor = {}
    for row_index, row in lib.reset_index(drop=True).iterrows():
        factor_name = f"{row['factor']}__row_{row_index + 1}"
        try:
            factor_frames["train"][factor_name] = _zscore(
                parse_expression(row["expression"]).eval(train)
            )
            factor_frames["val"][factor_name] = _zscore(
                parse_expression(row["expression"]).eval(val)
            )
            factor_frames["test"][factor_name] = _zscore(
                parse_expression(row["expression"]).eval(test)
            )
            expression_by_factor[factor_name] = row["expression"]
        except Exception as exc:
            print(f"Skipping {row['factor']}: {exc}")

    per_factor_rows = []
    ensemble_rows = []

    def _ensemble(factor_dict: dict, span: int) -> pd.Series:
        signal, _ = _build_equal_weight_signal(factor_dict, span)
        return signal

    def _period_stats(factor: pd.Series, fwd: pd.Series) -> dict:
        valid = factor.notna() & fwd.notna()
        f, r = factor.loc[valid], fwd.loc[valid]
        return {
            "ic": ic_score(f, r),
            "turnover": turnover_score(f),
            **_backtest(f, r, args.transaction_cost),
        }

    for h in args.horizons:
        fwd = {
            "train": _compute_forward(train, h),
            "val": _compute_forward(val, h),
            "test": _compute_forward(test, h),
        }

        ens = {p: _ensemble(factor_frames[p], args.smooth_span) for p in fwd}
        stats = {p: _period_stats(ens[p], fwd[p]) for p in fwd}
        ensemble_rows.append(
            {
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
            }
        )

        for fname in factor_frames["test"]:
            row_expr = expression_by_factor[fname]
            fstats = {p: _period_stats(factor_frames[p][fname], fwd[p]) for p in fwd}
            per_factor_rows.append(
                {
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
                }
            )

    df_factors = pd.DataFrame(per_factor_rows)
    df_ensemble = pd.DataFrame(ensemble_rows)
    df_factors.to_csv(args.output_dir / "per_factor_horizon.csv", index=False)
    df_ensemble.to_csv(args.output_dir / "ensemble_horizon.csv", index=False)

    # Realistic non-overlapping hold backtest for the ensemble.
    hold_rows = []
    for h in args.horizons:
        hold = evaluate_library_hold(
            lib,
            test,
            horizon=h,
            transaction_cost=args.transaction_cost,
            smooth_span=args.smooth_span,
            evaluation_mode="simple_hold",
        )
        hold_rows.append({"horizon": h, **hold})
    df_hold = pd.DataFrame(hold_rows)
    df_hold.to_csv(args.output_dir / "hold_ensemble_horizon.csv", index=False)

    # Markdown report
    lines = [
        "# Multi-Horizon Audit (5d / 10d / 20d)",
        "",
        "## Equal-Weight Ensemble",
        "",
        "| Horizon | Train IC | Train Sharpe | Val IC | Val Sharpe | Test IC | Test Sharpe | Cost-adj | Turnover | Max DD |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in df_ensemble.iterrows():
        lines.append(
            f"| {r['horizon']}d | {r['train_ic']:.4f} | {r['train_sharpe']:.4f} | "
            f"{r['val_ic']:.4f} | {r['val_sharpe']:.4f} | {r['test_ic']:.4f} | {r['test_sharpe']:.4f} | "
            f"{r['test_cost_adj_return']:.2%} | {r['test_turnover']:.4f} | {r['test_max_drawdown']:.2%} |"
        )
    lines += [
        "",
        "## Realistic H-Day Hold Backtest (ensemble)",
        "",
        "| Horizon | Sharpe | Ann. return | Cost-adj | Max DD |",
        "|---|---|---|---|---|",
    ]
    for _, r in df_hold.iterrows():
        if r.get("valid", False):
            lines.append(
                f"| {r['horizon']}d | {r['sharpe']:.4f} | {r['annualized_return']:.2%} | "
                f"{r['cost_adjusted_return']:.2%} | {r['max_drawdown']:.2%} |"
            )
        else:
            lines.append(f"| {r['horizon']}d | INVALID | - | - | - |")
    lines += ["", "## Per-Factor Test Sharpe by Horizon", ""]
    pivot = df_factors.pivot(index="factor", columns="horizon", values="test_sharpe").reset_index()
    cols = ["factor"] + [c for c in pivot.columns if c != "factor"]
    pivot = pivot[cols]
    lines.append("| " + " | ".join(str(c) for c in pivot.columns) + " |")
    lines.append("| " + " | ".join("---" for _ in pivot.columns) + " |")
    for _, r in pivot.iterrows():
        vals = []
        for c in pivot.columns:
            v = r[c]
            if isinstance(v, (int, np.integer)):
                vals.append(str(v))
            elif isinstance(v, float):
                vals.append(f"{v:.4f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    lines += ["", f"Full CSV: `{args.output_dir / 'per_factor_horizon.csv'}`"]
    (args.output_dir / "multihizon_audit.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved to {args.output_dir}")
    print(df_ensemble.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
