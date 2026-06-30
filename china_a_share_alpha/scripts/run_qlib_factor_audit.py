"""Cross-universe factor audit using Qlib China A-share data.

Run with the Python 3.11 venv where pyqlib is installed, e.g.:
    C:/aicoding/semas_framework/.venv_py311/Scripts/python.exe -m china_a_share_alpha.scripts.run_qlib_factor_audit

Tests hand-designed, TA-Lib, Alpha101, and evolved factors across:
- CSI300, CSI500, CSI1000 constituents
- Top market-cap major stocks (from synthetic market_cap mapping)
- Technology sector stocks (from synthetic sector mapping)

Outputs a comparison CSV and Markdown report.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.alpha101 import alpha_001, alpha_003, alpha_101
from china_a_share_alpha.data.qlib_loader import _load_qlib_data
from china_a_share_alpha.evaluator.metrics import ic_score, icir_score, rank_ic_score, turnover_score
from china_a_share_alpha.examples.tushare_factors import PORTFOLIO_FACTORS, SINGLE_FACTORS
from china_a_share_alpha.factor.expression import Var
from china_a_share_alpha.factor.parser import parse_expression

# Force single-process mode; avoids Windows spawn multiprocessing issues.
os.environ["QLIB_SERIAL_MODE"] = "1"


def _required_columns(expr) -> set[str]:
    """Return the set of column names referenced by a factor expression."""
    if isinstance(expr, Var):
        return {expr.name}
    cols = set()
    for child in getattr(expr, "children", []):
        cols |= _required_columns(child)
    if hasattr(expr, "child"):
        cols |= _required_columns(expr.child)
    if hasattr(expr, "left"):
        cols |= _required_columns(expr.left)
    if hasattr(expr, "right"):
        cols |= _required_columns(expr.right)
    return cols


def add_talib_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add TA-Lib indicator columns to the panel."""
    import talib

    out = df.copy()

    def _to_double(s: pd.Series) -> np.ndarray:
        return s.values.astype(np.float64)

    out["rsi_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.RSI(_to_double(g["close"]), 14), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["cci_20"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.CCI(_to_double(g["high"]), _to_double(g["low"]), _to_double(g["close"]), 20), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["adx_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.ADX(_to_double(g["high"]), _to_double(g["low"]), _to_double(g["close"]), 14), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["willr_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.WILLR(_to_double(g["high"]), _to_double(g["low"]), _to_double(g["close"]), 14), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["atr_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.ATR(_to_double(g["high"]), _to_double(g["low"]), _to_double(g["close"]), 14), index=g.index))
        .reset_index(level=0, drop=True)
    )

    def _macd_hist(g: pd.DataFrame) -> pd.Series:
        _, _, hist = talib.MACD(_to_double(g["close"]), 12, 26, 9)
        return pd.Series(hist, index=g.index)

    out["macd_hist"] = out.groupby(level="symbol").apply(_macd_hist).reset_index(level=0, drop=True)

    def _bbands_pctb(g: pd.DataFrame) -> pd.Series:
        upper, _, lower = talib.BBANDS(_to_double(g["close"]), 20, 2, 2)
        return pd.Series((g["close"].values.astype(np.float64) - lower) / (upper - lower + 1e-8), index=g.index)

    out["bbands_pctb"] = out.groupby(level="symbol").apply(_bbands_pctb).reset_index(level=0, drop=True)

    out["obv"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.OBV(_to_double(g["close"]), _to_double(g["volume"])), index=g.index))
        .reset_index(level=0, drop=True)
    )

    return out


def _zscore_series(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def evaluate_factor(name: str, expr, full: pd.DataFrame, train: pd.DataFrame, test: pd.DataFrame) -> dict[str, Any]:
    factor_full = expr.eval(full)
    factor_train = expr.eval(train)
    factor_test = expr.eval(test)
    bt = run_long_short_backtest(factor_full, full["forward_return"], transaction_cost=0.001)
    return {
        "factor": name,
        "ic": ic_score(factor_full, full["forward_return"]),
        "rank_ic": rank_ic_score(factor_full, full["forward_return"]),
        "icir": icir_score(factor_full, full["forward_return"]),
        "train_ic": ic_score(factor_train, train["forward_return"]),
        "test_ic": ic_score(factor_test, test["forward_return"]),
        "turnover": turnover_score(factor_full),
        "ann_return": bt["annualized_return"],
        "sharpe": bt["sharpe"],
        "max_drawdown": bt["max_drawdown"],
        "cost_adjusted_return": bt["cost_adjusted_return"],
    }


def build_ic_weighted_factor(factor_series_train: dict[str, pd.Series], train_forward: pd.Series) -> dict[str, float]:
    ics = {name: ic_score(f, train_forward) for name, f in factor_series_train.items()}
    weights = {name: np.sign(ic) * abs(ic) for name, ic in ics.items()}
    total = sum(abs(w) for w in weights.values()) + 1e-8
    return {name: w / total for name, w in weights.items()}


def load_universe_data(base_cfg: dict[str, Any], universe: str, n_major: int = 50) -> pd.DataFrame:
    """Load full panel for a universe using Qlib data."""
    cfg = base_cfg.copy()
    # Community Qlib data does not include $sector/$market_cap; rely on synthetic mapping.
    cfg["load_sector"] = False
    cfg["load_market_cap"] = False

    if universe in ("csi300", "csi500", "csi1000", "csiall", "all"):
        cfg["instruments"] = universe
        train, test = _load_qlib_data(cfg)
        return pd.concat([train, test]).sort_index()

    # For custom universes, load csiall first, then filter.
    cfg["instruments"] = "csiall"
    train, test = _load_qlib_data(cfg)
    full = pd.concat([train, test]).sort_index()

    if universe == "major":
        # Use synthetic market_cap from deterministic mapping.
        from china_a_share_alpha.data.sector_mapping import load_sector_market_cap
        symbols = full.index.get_level_values("symbol").unique()
        mapping = load_sector_market_cap(symbols, cfg)
        median_caps = mapping["market_cap"].sort_values(ascending=False)
        selected_symbols = median_caps.head(n_major).index.tolist()
        return full.loc[pd.IndexSlice[selected_symbols, :], :]

    if universe == "tech":
        # Use synthetic sector from deterministic mapping.
        from china_a_share_alpha.data.sector_mapping import load_sector_market_cap
        symbols = full.index.get_level_values("symbol").unique()
        mapping = load_sector_market_cap(symbols, cfg)
        tech_keywords = ["电子", "计算机", "通信", "半导体", "软件", "元件", "设备", "传媒"]
        mask = mapping["sector"].apply(lambda x: any(kw in x for kw in tech_keywords))
        selected_symbols = mapping[mask].index.tolist()
        return full.loc[pd.IndexSlice[selected_symbols, :], :]

    raise ValueError(f"Unknown universe: {universe}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Qlib-based cross-universe A-share factor audit")
    parser.add_argument("--start-time", default="2018-01-01")
    parser.add_argument("--end-time", default="2023-12-31")
    parser.add_argument("--split-date", default="2021-01-04")
    parser.add_argument("--data-dir", type=Path, default=Path("C:/aicoding/semas_framework/.qlib_py311/qlib_data/cn_data"))
    parser.add_argument("--universes", nargs="+", default=["csi300", "csi500", "csi1000", "major", "tech"])
    parser.add_argument("--output-dir", type=Path, default="./china_a_share_alpha_output/qlib_factor_audit")
    parser.add_argument("--evolved-csv", type=Path,
                        default=Path("./china_a_share_alpha_output/tushare_factor_library_neutralized/factor_library.csv"))
    parser.add_argument("--evolved-top-n", type=int, default=5)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    base_cfg = {
        "data_source": "qlib",
        "data_dir": str(args.data_dir),
        "start_time": args.start_time,
        "end_time": args.end_time,
        "split_date": args.split_date,
        "forward_period": 5,
    }
    split_date = pd.Timestamp(args.split_date)

    evolved_lib = pd.read_csv(args.evolved_csv) if args.evolved_csv.exists() else pd.DataFrame()

    all_results: list[dict[str, Any]] = []

    for universe in args.universes:
        print(f"\n=== Universe: {universe} ===")
        try:
            data = load_universe_data(base_cfg, universe)
        except Exception as exc:
            print(f"Failed to load universe {universe}: {exc}")
            continue
        print(f"Panel rows: {len(data)}, symbols: {data.index.get_level_values('symbol').nunique()}")
        if len(data) == 0:
            continue

        # Add derived fields.
        data = data[~data.index.duplicated(keep="first")].sort_index()
        data["return"] = data.groupby(level="symbol")["close"].pct_change()
        data = add_talib_features(data)

        train = data.loc[pd.IndexSlice[:, :split_date], :]
        test = data.loc[pd.IndexSlice[:, split_date:], :]

        factor_series_train: dict[str, Any] = {}
        factor_series_test: dict[str, Any] = {}
        factor_series_full: dict[str, Any] = {}

        # Hand-designed single factors.
        for name, expr in SINGLE_FACTORS.items():
            missing = _required_columns(expr) - set(data.columns)
            if missing:
                print(f"  Skipping {name}: missing columns {missing}")
                continue
            row = evaluate_factor(name, expr, data, train, test)
            factor_series_train[name] = expr.eval(train)
            factor_series_test[name] = expr.eval(test)
            factor_series_full[name] = expr.eval(data)
            row["universe"] = universe
            row["group"] = "hand_designed"
            all_results.append(row)

        # Hand-designed combined factors.
        for name, expr in PORTFOLIO_FACTORS.items():
            missing = _required_columns(expr) - set(data.columns)
            if missing:
                print(f"  Skipping {name}: missing columns {missing}")
                continue
            row = evaluate_factor(name, expr, data, train, test)
            row["universe"] = universe
            row["group"] = "hand_designed"
            all_results.append(row)

        # Alpha101 factors.
        alpha_factors = {
            "alpha101_001": alpha_001(),
            "alpha101_003": alpha_003(),
            "alpha101_101": alpha_101(),
        }
        for name, expr in alpha_factors.items():
            try:
                row = evaluate_factor(name, expr, data, train, test)
                row["universe"] = universe
                row["group"] = "alpha101"
                all_results.append(row)
            except Exception as exc:
                print(f"  Failed {name}: {exc}")

        # TA-Lib factors.
        talib_factor_specs = {
            "talib_rsi_14": parse_expression("cs_rank(rsi_14)"),
            "talib_macd_hist": parse_expression("cs_rank(macd_hist)"),
            "talib_bbands_pctb": parse_expression("cs_rank(bbands_pctb)"),
            "talib_cci_20": parse_expression("cs_rank(cci_20)"),
            "talib_adx_14": parse_expression("cs_rank(adx_14)"),
            "talib_willr_14": parse_expression("cs_rank(willr_14)"),
            "talib_atr_14": parse_expression("cs_rank(atr_14)"),
            "talib_obv": parse_expression("cs_rank(obv)"),
        }
        for name, expr in talib_factor_specs.items():
            try:
                row = evaluate_factor(name, expr, data, train, test)
                row["universe"] = universe
                row["group"] = "talib"
                all_results.append(row)
            except Exception as exc:
                print(f"  Failed {name}: {exc}")

        # IC-weighted combination.
        weights = build_ic_weighted_factor(factor_series_train, train["forward_return"])
        combined_full = pd.Series(0.0, index=data.index)
        combined_train = pd.Series(0.0, index=train.index)
        combined_test = pd.Series(0.0, index=test.index)
        for name, w in weights.items():
            combined_full = combined_full + w * _zscore_series(factor_series_full[name])
            combined_train = combined_train + w * _zscore_series(factor_series_train[name])
            combined_test = combined_test + w * _zscore_series(factor_series_test[name])

        bt = run_long_short_backtest(combined_full, data["forward_return"], transaction_cost=0.001)
        all_results.append({
            "factor": "ic_weighted_train",
            "universe": universe,
            "group": "combined",
            "ic": ic_score(combined_full, data["forward_return"]),
            "rank_ic": rank_ic_score(combined_full, data["forward_return"]),
            "icir": icir_score(combined_full, data["forward_return"]),
            "train_ic": ic_score(combined_train, train["forward_return"]),
            "test_ic": ic_score(combined_test, test["forward_return"]),
            "turnover": turnover_score(combined_full),
            "ann_return": bt["annualized_return"],
            "sharpe": bt["sharpe"],
            "max_drawdown": bt["max_drawdown"],
            "cost_adjusted_return": bt["cost_adjusted_return"],
        })

        # Evolved factors.
        if not evolved_lib.empty:
            for _, erow in evolved_lib.head(args.evolved_top_n).iterrows():
                expr_str = erow["expression"]
                name = f"evolved_{erow['rank']}"
                try:
                    expr = parse_expression(expr_str)
                    row = evaluate_factor(name, expr, data, train, test)
                    row["universe"] = universe
                    row["group"] = "evolved"
                    row["expression"] = expr_str
                    all_results.append(row)
                except Exception as exc:
                    print(f"  Failed evolved {name}: {exc}")

    results_df = pd.DataFrame(all_results)
    csv_path = args.output_dir / "qlib_comparison.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"\nCSV: {csv_path}")

    report_lines = ["# Qlib Cross-Universe Factor Audit\n"]
    report_lines.append(f"**Date range:** {args.start_time} - {args.end_time}\n")
    report_lines.append(f"**Split date:** {args.split_date}\n")
    report_lines.append(f"**Universes:** {', '.join(args.universes)}\n\n")

    for universe in args.universes:
        sub = results_df[results_df["universe"] == universe]
        if sub.empty:
            continue
        report_lines.append(f"## Universe: {universe}\n\n")
        report_lines.append("### Top by Sharpe\n\n")
        top_sharpe = sub.sort_values("sharpe", ascending=False).head(10)
        report_lines.append(top_sharpe[["factor", "group", "ic", "rank_ic", "sharpe", "max_drawdown", "test_ic"]].to_markdown(index=False))
        report_lines.append("\n\n### Top by IC\n\n")
        top_ic = sub.sort_values("ic", ascending=False).head(10)
        report_lines.append(top_ic[["factor", "group", "ic", "rank_ic", "sharpe", "test_ic"]].to_markdown(index=False))
        report_lines.append("\n\n")

    report_path = args.output_dir / "qlib_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report: {report_path}")

    summary = {
        "universes": args.universes,
        "n_factors": len(results_df),
        "best_by_sharpe": results_df.loc[results_df["sharpe"].idxmax()].to_dict(),
        "best_by_ic": results_df.loc[results_df["ic"].idxmax()].to_dict(),
    }
    summary_path = args.output_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"Summary: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
