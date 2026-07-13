"""Multi-horizon audit for the live library.

Evaluates each selected factor and the equal-weight ensemble on 5-day,
10-day, and 20-day forward returns.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.evaluator.metrics import ic_score, turnover_score
from china_a_share_alpha.factor.parser import parse_expression


def _zscore(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def _smooth(s: pd.Series, span: int) -> pd.Series:
    if span <= 1:
        return s
    return s.groupby(level="symbol").transform(lambda x: x.ewm(span=span, min_periods=1).mean())


def _compute_forward(data: pd.DataFrame, horizon: int) -> pd.Series:
    """Cumulative forward return over `horizon` trading days."""
    return data.groupby(level="symbol")["close"].pct_change(horizon).shift(-horizon)


def _backtest(factor: pd.Series, fwd: pd.Series, cost: float) -> dict:
    valid = factor.notna() & fwd.notna()
    f, r = factor.loc[valid], fwd.loc[valid]
    if f.empty:
        return {"sharpe": 0.0, "annualized_return": 0.0, "cost_adjusted_return": 0.0, "max_drawdown": 0.0}
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
    """Realistic non-overlapping H-day holding backtest.

    Rebalances every `horizon` trading days, holds long/short decile positions
    for `horizon` days, and compounds daily P&L.
    """
    dates = daily_returns.index.get_level_values("date").unique().sort_values()
    rebalance = set(range(0, len(dates), horizon))
    positions: dict[str, dict] = {}
    records = []
    for i, d in enumerate(dates):
        expired = [s for s, info in positions.items() if info["entry_idx"] + horizon <= i]
        for s in expired:
            del positions[s]
        if i in rebalance:
            try:
                sig = signal.xs(d, level="date")
            except KeyError:
                sig = pd.Series(dtype=float)
            sig = sig.dropna()
            if len(sig) >= 20:
                n = max(1, len(sig) // 10)
                ranked = sig.sort_values()
                shorts = ranked.head(n).index.tolist()
                longs = ranked.tail(n).index.tolist()
                for s in shorts:
                    positions[s] = {"side": -1, "w": 1.0 / n, "entry_idx": i}
                for s in longs:
                    positions[s] = {"side": 1, "w": 1.0 / n, "entry_idx": i}
        if positions:
            try:
                dr = daily_returns.xs(d, level="date")
            except KeyError:
                dr = pd.Series(dtype=float)
            pnl = 0.0
            for s, info in positions.items():
                if s in dr.index and pd.notna(dr[s]):
                    pnl += info["side"] * info["w"] * dr[s]
            if i in rebalance:
                pnl -= cost * 2.0
            records.append({"date": d, "ret": pnl})
    port = pd.DataFrame(records).set_index("date")["ret"].dropna()
    if port.empty:
        return {"sharpe": 0.0, "annualized_return": 0.0, "cost_adjusted_return": 0.0, "max_drawdown": 0.0}
    sharpe = port.mean() / (port.std() + 1e-12) * np.sqrt(252)
    ann_ret = (1 + port).prod() ** (252 / len(port)) - 1
    cum = (1 + port).cumprod()
    maxdd = (cum / cum.cummax() - 1).min()
    return {
        "sharpe": float(sharpe),
        "annualized_return": float(ann_ret),
        "cost_adjusted_return": float(ann_ret),
        "max_drawdown": float(maxdd),
    }


def _dynamic_trim_backtest(
    signal: pd.Series,
    daily_returns: pd.Series,
    horizon: int,
    cost: float = 0.001,
) -> dict:
    """Dynamic trim hold backtest.

    Rebalances every `horizon` days with long top 20% / short bottom 20%.
    During the holding window, long positions are trimmed based on cross-sectional
    rank deterioration:
      * rank 20%-40% -> position * 0.7
      * rank 40%-60% -> position * 0.5
      * rank 60%-100% -> exit
    If a stock is still in the top 20% when its horizon expires, it is kept.
    """
    dates = daily_returns.index.get_level_values("date").unique().sort_values()
    rebalance = set(range(0, len(dates), horizon))
    positions: dict[str, dict] = {}
    records = []
    prev_long_target = set()

    for i, d in enumerate(dates):
        try:
            sig = signal.xs(d, level="date")
        except KeyError:
            sig = pd.Series(dtype=float)
        sig = sig.dropna()
        ranked = sig.rank(pct=True, ascending=False) if len(sig) > 0 else pd.Series(dtype=float)
        top20 = set(ranked[ranked <= 0.2].index)
        bot20 = set(ranked[ranked >= 0.8].index)

        # Expire positions whose horizon ended and are not still top 20%
        expired = [s for s, info in positions.items() if info.get("entry_idx", 0) + horizon <= i]
        for s in expired:
            if s not in top20:
                del positions[s]
            else:
                positions[s]["entry_idx"] = i

        turnover = 0.0
        if i in rebalance and len(sig) >= 20:
            n = max(1, len(sig) // 5)  # 20%
            longs = sig.sort_values().tail(n).index.tolist()
            shorts = sig.sort_values().head(n).index.tolist()
            new_long_target = set(longs)
            turnover += len(new_long_target ^ prev_long_target) / (len(new_long_target) + len(prev_long_target) + 1e-8)
            for s in list(positions.keys()):
                if positions[s]["side"] == 1:
                    del positions[s]
            for s in longs:
                positions[s] = {"side": 1, "w": 1.0 / n, "entry_idx": i}
            for s in shorts:
                positions[s] = {"side": -1, "w": 1.0 / n, "entry_idx": i}
            prev_long_target = new_long_target

        # Mid-cycle trimming for long positions
        for s in list(positions.keys()):
            if positions[s]["side"] != 1:
                continue
            if s not in ranked.index:
                del positions[s]
                continue
            r = ranked[s]
            if r >= 0.8:
                del positions[s]
            elif r >= 0.6:
                positions[s]["w"] *= 0.5
            elif r >= 0.4:
                positions[s]["w"] *= 0.7

        if positions:
            try:
                dr = daily_returns.xs(d, level="date")
            except KeyError:
                dr = pd.Series(dtype=float)
            pnl = 0.0
            long_w_sum = 0.0
            short_w_sum = 0.0
            for s, info in positions.items():
                if s in dr.index and pd.notna(dr[s]):
                    if info["side"] == 1:
                        pnl += info["w"] * dr[s]
                        long_w_sum += info["w"]
                    else:
                        pnl -= info["w"] * dr[s]
                        short_w_sum += info["w"]
            if long_w_sum > 0:
                pnl /= long_w_sum
            if short_w_sum > 0:
                pnl /= short_w_sum
            pnl -= cost * turnover
            records.append({"date": d, "ret": pnl})

    port = pd.DataFrame(records).set_index("date")["ret"].dropna()
    if port.empty:
        return {"sharpe": 0.0, "annualized_return": 0.0, "cost_adjusted_return": 0.0, "max_drawdown": 0.0}
    sharpe = port.mean() / (port.std() + 1e-12) * np.sqrt(252)
    ann_ret = (1 + port).prod() ** (252 / len(port)) - 1
    cum = (1 + port).cumprod()
    maxdd = (cum / cum.cummax() - 1).min()
    return {
        "sharpe": float(sharpe),
        "annualized_return": float(ann_ret),
        "cost_adjusted_return": float(ann_ret),
        "max_drawdown": float(maxdd),
    }


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
    for _, row in lib.iterrows():
        try:
            factor_frames["train"][row["factor"]] = _zscore(parse_expression(row["expression"]).eval(train))
            factor_frames["val"][row["factor"]] = _zscore(parse_expression(row["expression"]).eval(val))
            factor_frames["test"][row["factor"]] = _zscore(parse_expression(row["expression"]).eval(test))
        except Exception as exc:
            print(f"Skipping {row['factor']}: {exc}")

    per_factor_rows = []
    ensemble_rows = []

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
            fstats = {p: _period_stats(factor_frames[p][fname], fwd[p]) for p in fwd}
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

    df_factors = pd.DataFrame(per_factor_rows)
    df_ensemble = pd.DataFrame(ensemble_rows)
    df_factors.to_csv(args.output_dir / "per_factor_horizon.csv", index=False)
    df_ensemble.to_csv(args.output_dir / "ensemble_horizon.csv", index=False)

    # Realistic non-overlapping hold backtest for the ensemble.
    hold_rows = []
    for h in args.horizons:
        ens_test = _ensemble(factor_frames["test"], args.smooth_span)
        hold = _hold_backtest(ens_test, test["return"], h, args.transaction_cost)
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
    lines += ["", "## Realistic H-Day Hold Backtest (ensemble)", "", "| Horizon | Sharpe | Ann. return | Cost-adj | Max DD |", "|---|---|---|---|---|"]
    for _, r in df_hold.iterrows():
        lines.append(
            f"| {r['horizon']}d | {r['sharpe']:.4f} | {r['annualized_return']:.2%} | "
            f"{r['cost_adjusted_return']:.2%} | {r['max_drawdown']:.2%} |"
        )
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
