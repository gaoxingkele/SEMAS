"""Path-barrier factor audit from 2025-01-01.

Signal day T: factor computed; buy at T close.
Holding window: T+1 .. T+H trading days (H in {5,10}).
Barriers from entry:
  - take-profit +15% (exit success when high first reaches entry * 1.15)
  - stop-loss -10% (fail when low first reaches entry * 0.90)
Same-day both barriers: conservative — count stop-loss first.
Timeout: neither barrier hit by T+H — fail (no +15% reached).

Also bins trades by sector / market-cap / PB / PE-proxy for hit-rate analysis.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.data.tushare_loader import load_tushare_data_with_val
from china_a_share_alpha.factor.parser import parse_expression
from china_a_share_alpha.scripts.run_multihizon_audit import _zscore

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "china_a_share_alpha/examples/enhanced_loop_config_val_frozen.yaml"
LIVE = ROOT / "china_a_share_alpha_output/factor_mining_loop/live_library.csv"
OUT = ROOT / "china_a_share_alpha_output/factor_mining_loop/path_barrier_audit_2025"
TAKE_PROFIT = 0.15
STOP_LOSS = 0.10
HORIZONS = (5, 10)
TOP_FRAC = 0.20
TEST_START = pd.Timestamp("2025-01-01")


def _prepare_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    train, val, test = load_tushare_data_with_val(cfg)
    full = pd.concat([train, val, test]).sort_index()
    full = full[~full.index.duplicated(keep="last")]
    full = full.copy()
    full["pe_proxy"] = np.where(
        full["eps"].notna() & (full["eps"] > 0),
        full["close"] / full["eps"],
        np.nan,
    )
    return full, test


def _path_outcome(
    entry: float,
    highs: np.ndarray,
    lows: np.ndarray,
    take_profit: float,
    stop_loss: float,
) -> tuple[str, int | None, float]:
    """Return (outcome, exit_day_offset_1based, max_favorable_excursion)."""
    tp = entry * (1.0 + take_profit)
    sl = entry * (1.0 - stop_loss)
    mfe = 0.0
    for i, (hi, lo) in enumerate(zip(highs, lows), start=1):
        if not np.isfinite(hi) or not np.isfinite(lo):
            continue
        mfe = max(mfe, hi / entry - 1.0)
        hit_sl = lo <= sl
        hit_tp = hi >= tp
        if hit_sl and hit_tp:
            return "stop_loss", i, mfe
        if hit_sl:
            return "stop_loss", i, mfe
        if hit_tp:
            return "take_profit", i, mfe
    return "timeout", None, mfe


def _bin_series(series: pd.Series, labels: list[str]) -> pd.Series:
    clean = series.replace([np.inf, -np.inf], np.nan)
    try:
        return pd.qcut(clean, q=len(labels), labels=labels, duplicates="drop")
    except ValueError:
        return pd.Series(["unknown"] * len(series), index=series.index)


def evaluate_factor(
    name: str,
    expression: str,
    panel: pd.DataFrame,
    dates: pd.DatetimeIndex,
    symbol_frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict]:
    factor = _zscore(parse_expression(expression).eval(panel))
    factor = factor.reindex(panel.index)

    # Cross-sectional top fraction each signal day (from TEST_START).
    signal = factor.unstack("symbol")
    close = panel["close"].unstack("symbol")
    high = panel["high"].unstack("symbol")
    low = panel["low"].unstack("symbol")
    sector = panel["sector"].unstack("symbol") if "sector" in panel.columns else None
    mv = panel["total_mv"].unstack("symbol")
    pb = panel["pb"].unstack("symbol")
    pe = panel["pe_proxy"].unstack("symbol")

    trade_rows: list[dict] = []
    signal_dates = [d for d in dates if d >= TEST_START]
    # Need H future days after signal; stop early enough.
    date_to_pos = {d: i for i, d in enumerate(dates)}

    for d in signal_dates:
        i = date_to_pos[d]
        # require max horizon days after signal
        if i + max(HORIZONS) >= len(dates):
            continue
        day_scores = signal.loc[d].dropna()
        if len(day_scores) < 10:
            continue
        k = max(1, int(np.ceil(len(day_scores) * TOP_FRAC)))
        picks = day_scores.nlargest(k)
        entry_prices = close.loc[d, picks.index]
        for sym, score in picks.items():
            entry = float(entry_prices.get(sym, np.nan))
            if not np.isfinite(entry) or entry <= 0:
                continue
            sec = (
                str(sector.loc[d, sym])
                if sector is not None and pd.notna(sector.loc[d, sym])
                else "unknown"
            )
            mv_v = float(mv.loc[d, sym]) if pd.notna(mv.loc[d, sym]) else np.nan
            pb_v = float(pb.loc[d, sym]) if pd.notna(pb.loc[d, sym]) else np.nan
            pe_v = float(pe.loc[d, sym]) if pd.notna(pe.loc[d, sym]) else np.nan
            for h in HORIZONS:
                fut_dates = dates[i + 1 : i + 1 + h]
                highs = high.loc[fut_dates, sym].to_numpy(dtype=float)
                lows = low.loc[fut_dates, sym].to_numpy(dtype=float)
                outcome, exit_day, mfe = _path_outcome(
                    entry, highs, lows, TAKE_PROFIT, STOP_LOSS
                )
                trade_rows.append(
                    {
                        "factor": name,
                        "expression": expression,
                        "horizon": h,
                        "signal_date": d,
                        "symbol": sym,
                        "score": float(score),
                        "entry_price": entry,
                        "outcome": outcome,
                        "exit_day": exit_day,
                        "mfe": mfe,
                        "hit_tp": outcome == "take_profit",
                        "hit_sl": outcome == "stop_loss",
                        "timeout": outcome == "timeout",
                        "sector": sec,
                        "total_mv": mv_v,
                        "pb": pb_v,
                        "pe_proxy": pe_v,
                    }
                )

    trades = pd.DataFrame(trade_rows)
    if trades.empty:
        return trades, {"factor": name, "error": "no trades"}

    # Add quantile bins within each horizon using all trades of that horizon.
    pieces = []
    for h, g in trades.groupby("horizon"):
        g = g.copy()
        g["mv_bin"] = _bin_series(
            g["total_mv"], ["mv_Q1_small", "mv_Q2", "mv_Q3", "mv_Q4", "mv_Q5_large"]
        )
        g["pb_bin"] = _bin_series(
            g["pb"], ["pb_Q1_low", "pb_Q2", "pb_Q3", "pb_Q4", "pb_Q5_high"]
        )
        g["pe_bin"] = _bin_series(
            g["pe_proxy"], ["pe_Q1_low", "pe_Q2", "pe_Q3", "pe_Q4", "pe_Q5_high"]
        )
        pieces.append(g)
    trades = pd.concat(pieces, ignore_index=True)

    summaries = []
    for h, g in trades.groupby("horizon"):
        summaries.append(
            {
                "factor": name,
                "expression": expression,
                "horizon": int(h),
                "n_trades": int(len(g)),
                "hit_tp_rate": float(g["hit_tp"].mean()),
                "hit_sl_rate": float(g["hit_sl"].mean()),
                "timeout_rate": float(g["timeout"].mean()),
                "avg_mfe": float(g["mfe"].mean()),
                "median_exit_day_tp": float(
                    g.loc[g["hit_tp"], "exit_day"].median()
                    if g["hit_tp"].any()
                    else np.nan
                ),
                "coverage_symbols": int(g["symbol"].nunique()),
                "coverage_days": int(g["signal_date"].nunique()),
            }
        )
    return trades, {"factor": name, "by_horizon": summaries}


def _bucket_table(trades: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    for (factor, horizon, bucket), g in trades.groupby(["factor", "horizon", key]):
        rows.append(
            {
                "factor": factor,
                "horizon": int(horizon),
                "bucket_type": key,
                "bucket": str(bucket),
                "n_trades": int(len(g)),
                "hit_tp_rate": float(g["hit_tp"].mean()),
                "hit_sl_rate": float(g["hit_sl"].mean()),
                "timeout_rate": float(g["timeout"].mean()),
                "avg_mfe": float(g["mfe"].mean()),
                "trade_share": float(len(g) / max(1, len(trades[(trades.factor == factor) & (trades.horizon == horizon)]))),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("loading panel...", flush=True)
    panel, _ = _prepare_panel()
    dates = panel.index.get_level_values("date").unique().sort_values()
    print(
        f"panel {dates.min().date()} -> {dates.max().date()}; "
        f"audit signals from {TEST_START.date()}",
        flush=True,
    )

    lib = pd.read_csv(LIVE)
    if "factor" not in lib.columns:
        lib["factor"] = [f"factor_{i+1}" for i in range(len(lib))]

    all_trades = []
    summaries = []
    for i, row in lib.iterrows():
        name = str(row["factor"])
        expr = str(row["expression"])
        print(f"[{i+1}/{len(lib)}] {name}", flush=True)
        try:
            trades, meta = evaluate_factor(name, expr, panel, dates, {})
            if trades.empty:
                print(f"  no trades: {meta}", flush=True)
                continue
            all_trades.append(trades)
            summaries.extend(meta["by_horizon"])
            for s in meta["by_horizon"]:
                print(
                    f"  H={s['horizon']} n={s['n_trades']} "
                    f"TP={s['hit_tp_rate']:.1%} SL={s['hit_sl_rate']:.1%} "
                    f"TO={s['timeout_rate']:.1%}",
                    flush=True,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {exc}", flush=True)
            summaries.append({"factor": name, "expression": expr, "error": str(exc)})

    if not all_trades:
        raise SystemExit("no trades produced")

    trades = pd.concat(all_trades, ignore_index=True)
    trades.to_csv(OUT / "trades_detail.csv", index=False, encoding="utf-8")
    summary = pd.DataFrame(summaries)
    summary.to_csv(OUT / "factor_summary.csv", index=False, encoding="utf-8")

    buckets = pd.concat(
        [
            _bucket_table(trades, "sector"),
            _bucket_table(trades, "mv_bin"),
            _bucket_table(trades, "pb_bin"),
            _bucket_table(trades, "pe_bin"),
        ],
        ignore_index=True,
    )
    buckets.to_csv(OUT / "bucket_hit_rates.csv", index=False, encoding="utf-8")

    # Best buckets overall (min sample)
    best_rows = []
    for key in ("sector", "mv_bin", "pb_bin", "pe_bin"):
        sub = buckets[buckets["bucket_type"] == key]
        for h in HORIZONS:
            hh = sub[sub["horizon"] == h]
            hh = hh[hh["n_trades"] >= 30].sort_values("hit_tp_rate", ascending=False)
            for _, r in hh.head(8).iterrows():
                best_rows.append(r.to_dict())
    pd.DataFrame(best_rows).to_csv(OUT / "best_buckets_min30.csv", index=False, encoding="utf-8")

    # Markdown report
    lines = [
        "# 路径障碍因子审计（2025-01-01 起）",
        "",
        "## 规则",
        "",
        "- 信号日 T 收盘价买入（因子当日算完）。",
        "- 观察窗口：T+1 起共 H=5 或 10 个交易日。",
        f"- 止盈：相对买入价上涨 **+{TAKE_PROFIT:.0%}**（盘中 high 触及即成功退出）。",
        f"- 止损：相对买入价下跌 **-{STOP_LOSS:.0%}**（盘中 low 触及即失败；同日触及两者时按止损优先）。",
        "- 窗口结束未触止盈：计为 timeout（未达目标）。",
        f"- 选股：每日截面因子值最高 **{TOP_FRAC:.0%}** 多头。",
        f"- 验证区间：信号日 ≥ **{TEST_START.date()}**（数据至 {dates.max().date()}）。",
        "",
        "## 因子总表（按 5日 止盈率排序）",
        "",
        "| 因子 | H | 笔数 | 止盈率 | 止损率 | 超时率 | 均MFE |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    s5 = summary[summary.get("horizon") == 5] if "horizon" in summary.columns else summary
    s5 = s5.dropna(subset=["hit_tp_rate"]).sort_values("hit_tp_rate", ascending=False)
    for _, r in s5.iterrows():
        lines.append(
            f"| {r['factor']} | 5 | {int(r['n_trades'])} | {r['hit_tp_rate']:.1%} | "
            f"{r['hit_sl_rate']:.1%} | {r['timeout_rate']:.1%} | {r['avg_mfe']:.1%} |"
        )
    lines.append("")
    lines.append("## 因子总表（10日）")
    lines.append("")
    lines.append("| 因子 | H | 笔数 | 止盈率 | 止损率 | 超时率 | 均MFE |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    s10 = summary[summary["horizon"] == 10].dropna(subset=["hit_tp_rate"]).sort_values(
        "hit_tp_rate", ascending=False
    )
    for _, r in s10.iterrows():
        lines.append(
            f"| {r['factor']} | 10 | {int(r['n_trades'])} | {r['hit_tp_rate']:.1%} | "
            f"{r['hit_sl_rate']:.1%} | {r['timeout_rate']:.1%} | {r['avg_mfe']:.1%} |"
        )

    # Top factor detail buckets
    if not s5.empty:
        top = str(s5.iloc[0]["factor"])
        lines.append("")
        lines.append(f"## 最优因子分箱（5日止盈率最高：{top}）")
        for key, title in (
            ("sector", "板块"),
            ("mv_bin", "市值分位"),
            ("pb_bin", "PB分位"),
            ("pe_bin", "PE代理分位"),
        ):
            lines.append("")
            lines.append(f"### {title}")
            lines.append("")
            lines.append("| 分箱 | 笔数 | 止盈率 | 止损率 | 超时率 | 占比 |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            sub = buckets[
                (buckets["factor"] == top)
                & (buckets["horizon"] == 5)
                & (buckets["bucket_type"] == key)
            ].sort_values("hit_tp_rate", ascending=False)
            for _, r in sub.head(12).iterrows():
                if r["n_trades"] < 15:
                    continue
                lines.append(
                    f"| {r['bucket']} | {int(r['n_trades'])} | {r['hit_tp_rate']:.1%} | "
                    f"{r['hit_sl_rate']:.1%} | {r['timeout_rate']:.1%} | {r['trade_share']:.1%} |"
                )

    lines.append("")
    lines.append(f"输出目录：`{OUT.as_posix()}`")
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "meta.json").write_text(
        json.dumps(
            {
                "take_profit": TAKE_PROFIT,
                "stop_loss": STOP_LOSS,
                "horizons": list(HORIZONS),
                "top_frac": TOP_FRAC,
                "test_start": str(TEST_START.date()),
                "test_end": str(dates.max().date()),
                "n_factors": int(lib.shape[0]),
                "same_day_rule": "stop_loss_priority",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print((OUT / "REPORT.md").read_text(encoding="utf-8")[:3500])
    print("DONE", OUT)


if __name__ == "__main__":
    main()
