"""Cross-universe factor audit for A-shares.

Tests hand-designed, TA-Lib, Alpha101, and evolved factors across:
- CSI300, CSI500, CSI1000 constituents
- Top market-cap major stocks
- Technology sector stocks

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
import tushare as ts

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.tushare_loader import _load_or_fetch
from china_a_share_alpha.evaluator.metrics import ic_score, icir_score, rank_ic_score, turnover_score
from china_a_share_alpha.examples.tushare_factors import PORTFOLIO_FACTORS, SINGLE_FACTORS
from china_a_share_alpha.factor.expression import FactorExpr
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.data.alpha101 import alpha_001, alpha_003, alpha_101


def _get_pro(token: str | None = None) -> Any:
    token = token or os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("TUSHARE_TOKEN is required")
    ts.set_token(token)
    return ts.pro_api()


def _latest_trade_date(pro, index_code: str) -> str:
    """Get the most recent trade date with constituent data for an index."""
    df = pro.index_weight(index_code=index_code)
    return str(df["trade_date"].max())


def get_universe_symbols(pro, universe: str, n_major: int = 50) -> list[str]:
    """Resolve a universe name to a list of ts_codes."""
    if universe == "csi300":
        date = _latest_trade_date(pro, "000300.SH")
        df = pro.index_weight(index_code="000300.SH", start_date=date, end_date=date)
        return df["con_code"].unique().tolist()
    if universe == "csi500":
        date = _latest_trade_date(pro, "000905.SH")
        df = pro.index_weight(index_code="000905.SH", start_date=date, end_date=date)
        return df["con_code"].unique().tolist()
    if universe == "csi1000":
        date = _latest_trade_date(pro, "000852.SH")
        df = pro.index_weight(index_code="000852.SH", start_date=date, end_date=date)
        return df["con_code"].unique().tolist()
    if universe == "major":
        # Use daily_basic total market cap on the most recent available date.
        trade_date = _latest_trade_date(pro, "000300.SH")
        db = pro.daily_basic(trade_date=trade_date, fields="ts_code,total_mv")
        db["total_mv"] = pd.to_numeric(db["total_mv"], errors="coerce")
        db = db.dropna(subset=["total_mv"]).sort_values("total_mv", ascending=False)
        return db.head(n_major)["ts_code"].tolist()
    if universe == "tech":
        # Technology-related Tushare industry names (Chinese encoding handled by tushare).
        tech_keywords = [
            "半导体", "元件", "计算机设备", "通信设备", "电子", "软件服务",
            "互联网", "通信", "IT设备", "电器仪表", "专用机械", "通用机械",
            "汽车配件", "汽车整车", "元器件", "半导体设备", "芯片",
        ]
        basics = pro.stock_basic(exchange="", list_status="L", fields="ts_code,industry,name")
        basics = basics.dropna(subset=["industry"])
        mask = basics["industry"].apply(lambda x: any(kw in x for kw in tech_keywords))
        return basics[mask]["ts_code"].unique().tolist()
    raise ValueError(f"Unknown universe: {universe}")


def load_universe_data(
    pro,
    symbols: list[str],
    start_date: str,
    end_date: str,
    cache_dir: Path,
) -> pd.DataFrame:
    """Load OHLCV panel for a custom symbol list from Tushare cache/API."""
    all_frames: list[pd.DataFrame] = []
    for i, ts_code in enumerate(symbols):
        try:
            df = _load_or_fetch(pro, ts_code, start_date, end_date, cache_dir)
            if df.empty:
                continue
            all_frames.append(df)
        except Exception as exc:
            print(f"Skipping {ts_code}: {exc}")
        if (i + 1) % 50 == 0:
            print(f"Loaded {i + 1}/{len(symbols)} symbols")
    if not all_frames:
        raise RuntimeError("No data loaded for universe.")

    data = pd.concat(all_frames, ignore_index=True)
    data["trade_date"] = pd.to_datetime(data["trade_date"], format="%Y%m%d")
    data = data.rename(columns={"ts_code": "symbol", "trade_date": "date", "vol": "volume"})
    data = data.set_index(["symbol", "date"]).sort_index()

    data["return"] = data.groupby(level="symbol")["close"].pct_change()
    data["forward_return"] = data.groupby(level="symbol")["return"].shift(-1)
    data["vwap"] = data["amount"] / (data["volume"].replace(0, np.nan))
    return data.dropna(subset=["open", "high", "low", "close", "volume", "amount", "forward_return"])


def add_talib_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add TA-Lib indicator columns to the panel."""
    import talib

    out = df.copy()

    def _apply(close_series, func, *args, **kwargs):
        return close_series.groupby(level="symbol").transform(lambda s: func(s.values, *args, **kwargs))

    close = out["close"]
    high = out["high"]
    low = out["low"]
    volume = out["volume"]

    out["rsi_14"] = _apply(close, talib.RSI, 14)
    out["cci_20"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.CCI(g["high"].values, g["low"].values, g["close"].values, 20), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["adx_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.ADX(g["high"].values, g["low"].values, g["close"].values, 14), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["willr_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.WILLR(g["high"].values, g["low"].values, g["close"].values, 14), index=g.index))
        .reset_index(level=0, drop=True)
    )
    out["atr_14"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.ATR(g["high"].values, g["low"].values, g["close"].values, 14), index=g.index))
        .reset_index(level=0, drop=True)
    )

    # MACD histogram
    def _macd_hist(g: pd.DataFrame) -> pd.Series:
        _, _, hist = talib.MACD(g["close"].values, 12, 26, 9)
        return pd.Series(hist, index=g.index)

    out["macd_hist"] = out.groupby(level="symbol").apply(_macd_hist).reset_index(level=0, drop=True)

    # Bollinger %B
    def _bbands_pctb(g: pd.DataFrame) -> pd.Series:
        upper, middle, lower = talib.BBANDS(g["close"].values, 20, 2, 2)
        return pd.Series((g["close"].values - lower) / (upper - lower + 1e-8), index=g.index)

    out["bbands_pctb"] = out.groupby(level="symbol").apply(_bbands_pctb).reset_index(level=0, drop=True)

    # OBV-like volume momentum
    out["obv"] = (
        out.groupby(level="symbol")
        .apply(lambda g: pd.Series(talib.OBV(g["close"].values, g["volume"].values), index=g.index))
        .reset_index(level=0, drop=True)
    )

    return out


def _zscore_series(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))


def evaluate_factor(
    name: str,
    expr: FactorExpr,
    full: pd.DataFrame,
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> dict[str, Any]:
    factor_full = expr.eval(full)
    factor_train = expr.eval(train)
    factor_test = expr.eval(test)

    # Use full data for backtest metrics.
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-universe A-share factor audit")
    parser.add_argument("--start-date", default="20210601")
    parser.add_argument("--end-date", default="20260601")
    parser.add_argument("--split-date", default="20240101")
    parser.add_argument("--universes", nargs="+", default=["csi300", "csi500", "csi1000", "major", "tech"])
    parser.add_argument("--output-dir", type=Path, default="./china_a_share_alpha_output/cross_universe_audit")
    parser.add_argument("--evolved-csv", type=Path,
                        default=Path("./china_a_share_alpha_output/tushare_factor_library_neutralized/factor_library.csv"))
    parser.add_argument("--evolved-top-n", type=int, default=5)
    parser.add_argument("--token", default=None, help="Tushare token (or set TUSHARE_TOKEN env)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path("china_a_share_alpha_output/tushare_backtest/tushare_cache")

    pro = _get_pro(args.token)
    start_date, end_date, split_date = args.start_date, args.end_date, pd.Timestamp(args.split_date)

    # Load evolved library.
    evolved_lib = pd.read_csv(args.evolved_csv) if args.evolved_csv.exists() else pd.DataFrame()

    all_results: list[dict[str, Any]] = []

    for universe in args.universes:
        print(f"\n=== Universe: {universe} ===")
        try:
            symbols = get_universe_symbols(pro, universe)
        except Exception as exc:
            print(f"Failed to resolve universe {universe}: {exc}")
            continue
        print(f"Symbols: {len(symbols)}")
        if len(symbols) == 0:
            continue

        data = load_universe_data(pro, symbols, start_date, end_date, cache_dir)
        print(f"Panel rows: {len(data)}, symbols: {data.index.get_level_values('symbol').nunique()}")

        # Add TA-Lib features.
        data = add_talib_features(data)

        train = data.loc[pd.IndexSlice[:, :split_date], :]
        test = data.loc[pd.IndexSlice[:, split_date:], :]

        factor_series_train: dict[str, pd.Series] = {}
        factor_series_full: dict[str, pd.Series] = {}

        # Hand-designed single factors.
        for name, expr in SINGLE_FACTORS.items():
            row = evaluate_factor(name, expr, data, train, test)
            factor_series_train[name] = expr.eval(train)
            factor_series_full[name] = expr.eval(data)
            row["universe"] = universe
            row["group"] = "hand_designed"
            all_results.append(row)

        # Hand-designed combined factors.
        for name, expr in PORTFOLIO_FACTORS.items():
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

        # TA-Lib factors (using cs_rank where appropriate).
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

        # IC-weighted combination of hand-designed factors.
        weights = build_ic_weighted_factor(factor_series_train, train["forward_return"])
        combined_full = pd.Series(0.0, index=data.index)
        combined_train = pd.Series(0.0, index=train.index)
        combined_test = pd.Series(0.0, index=test.index)
        for name, w in weights.items():
            combined_full = combined_full + w * _zscore_series(factor_series_full[name])
            combined_train = combined_train + w * _zscore_series(factor_series_train[name])
            combined_test = combined_test + w * _zscore_series(factor_series_train[name])

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
    csv_path = args.output_dir / "cross_universe_comparison.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"\nCSV: {csv_path}")

    # Generate Markdown report.
    report_lines = ["# A-Share Cross-Universe Factor Audit\n"]
    report_lines.append(f"**Date range:** {start_date} - {end_date}\n")
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

    report_path = args.output_dir / "cross_universe_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report: {report_path}")

    # Summary JSON.
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
