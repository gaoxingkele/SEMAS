"""Optimized path-barrier factor audit (2025+).

Calibration (from live-library path MFE/MAE on 2025+ CSI300 Top20% picks):
  - 5d MFE p50≈3.5%, p70≈6.7%; MAE p30≈-5.2%
  - 10d MFE p50≈5.4%, p70≈10%; MAE p30≈-7.3%

Default optimized contract (v2):
  - H=5:  TP=+6%, SL=-5%
  - H=10: TP=+8%, SL=-6%
  - Expiry: if neither barrier hit by T+H, exit at day-H **close**
    (realized return = close_H/entry - 1). No more pure "timeout fail".

Signal: day-T close buy; window T+1..T+H; same-day both barriers → SL first.
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
from china_a_share_alpha.scripts.run_multihizon_audit import _zscore

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "china_a_share_alpha/examples/enhanced_loop_config_val_frozen.yaml"
LIVE = ROOT / "china_a_share_alpha_output/factor_mining_loop/live_library.csv"

# Horizon-specific barriers: (take_profit, stop_loss)
PRESETS: dict[str, dict[int, tuple[float, float]]] = {
    "legacy_15_10": {5: (0.15, 0.10), 10: (0.15, 0.10)},
    "optimized_v2": {5: (0.06, 0.05), 10: (0.08, 0.06)},
    "tight_v2": {5: (0.05, 0.04), 10: (0.06, 0.05)},
    "wide_v2": {5: (0.08, 0.06), 10: (0.10, 0.08)},
}

TOP_FRAC = 0.20
TEST_START = pd.Timestamp("2025-01-01")


def _prepare_panel() -> pd.DataFrame:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    train, val, test = load_tushare_data_with_val(cfg)
    full = pd.concat([train, val, test]).sort_index()
    full = full[~full.index.duplicated(keep="last")].copy()
    full["pe_proxy"] = np.where(
        full["eps"].notna() & (full["eps"] > 0),
        full["close"] / full["eps"],
        np.nan,
    )
    return full


def _path_outcome(
    entry: float,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    take_profit: float,
    stop_loss: float,
) -> tuple[str, int, float, float]:
    """Return (outcome, exit_day_1based, mfe, realized_return)."""
    tp = entry * (1.0 + take_profit)
    sl = entry * (1.0 - stop_loss)
    mfe = 0.0
    for i, (hi, lo) in enumerate(zip(highs, lows), start=1):
        if not np.isfinite(hi) or not np.isfinite(lo):
            continue
        mfe = max(mfe, float(hi / entry - 1.0))
        hit_sl = lo <= sl
        hit_tp = hi >= tp
        if hit_sl and hit_tp:
            return "stop_loss", i, mfe, -stop_loss
        if hit_sl:
            return "stop_loss", i, mfe, -stop_loss
        if hit_tp:
            return "take_profit", i, mfe, take_profit
    # Expire at last available close.
    last_close = next((float(c) for c in closes[::-1] if np.isfinite(c)), np.nan)
    if not np.isfinite(last_close):
        return "expire_invalid", len(closes), mfe, np.nan
    realized = last_close / entry - 1.0
    return "expire_close", len(closes), mfe, float(realized)


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
    barriers: dict[int, tuple[float, float]],
) -> tuple[pd.DataFrame, list[dict]]:
    factor = _zscore(parse_expression(expression).eval(panel)).reindex(panel.index)
    signal = factor.unstack("symbol")
    close = panel["close"].unstack("symbol")
    high = panel["high"].unstack("symbol")
    low = panel["low"].unstack("symbol")
    sector = panel["sector"].unstack("symbol") if "sector" in panel.columns else None
    mv = panel["total_mv"].unstack("symbol")
    pb = panel["pb"].unstack("symbol")
    pe = panel["pe_proxy"].unstack("symbol")
    date_to_pos = {d: i for i, d in enumerate(dates)}
    horizons = sorted(barriers.keys())
    max_h = max(horizons)

    trade_rows: list[dict] = []
    for d in dates:
        if d < TEST_START:
            continue
        i = date_to_pos[d]
        if i + max_h >= len(dates):
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
            for h in horizons:
                tp, sl = barriers[h]
                fut = dates[i + 1 : i + 1 + h]
                highs = high.loc[fut, sym].to_numpy(dtype=float)
                lows = low.loc[fut, sym].to_numpy(dtype=float)
                closes = close.loc[fut, sym].to_numpy(dtype=float)
                outcome, exit_day, mfe, realized = _path_outcome(
                    entry, highs, lows, closes, tp, sl
                )
                trade_rows.append(
                    {
                        "factor": name,
                        "expression": expression,
                        "horizon": h,
                        "tp": tp,
                        "sl": sl,
                        "signal_date": d,
                        "symbol": sym,
                        "score": float(score),
                        "entry_price": entry,
                        "outcome": outcome,
                        "exit_day": exit_day,
                        "mfe": mfe,
                        "realized_return": realized,
                        "hit_tp": outcome == "take_profit",
                        "hit_sl": outcome == "stop_loss",
                        "expire_close": outcome == "expire_close",
                        "sector": sec,
                        "total_mv": mv_v,
                        "pb": pb_v,
                        "pe_proxy": pe_v,
                    }
                )

    trades = pd.DataFrame(trade_rows)
    if trades.empty:
        return trades, []

    pieces = []
    for _, g in trades.groupby("horizon"):
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
        rr = g["realized_return"].dropna()
        summaries.append(
            {
                "factor": name,
                "expression": expression,
                "horizon": int(h),
                "tp": float(barriers[int(h)][0]),
                "sl": float(barriers[int(h)][1]),
                "n_trades": int(len(g)),
                "hit_tp_rate": float(g["hit_tp"].mean()),
                "hit_sl_rate": float(g["hit_sl"].mean()),
                "expire_close_rate": float(g["expire_close"].mean()),
                "avg_realized_return": float(rr.mean()) if len(rr) else np.nan,
                "median_realized_return": float(rr.median()) if len(rr) else np.nan,
                "win_rate": float((rr > 0).mean()) if len(rr) else np.nan,
                "avg_mfe": float(g["mfe"].mean()),
                "expectancy_per_trade": float(rr.mean()) if len(rr) else np.nan,
                "coverage_symbols": int(g["symbol"].nunique()),
                "coverage_days": int(g["signal_date"].nunique()),
            }
        )
    return trades, summaries


def _bucket_table(trades: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    for (factor, horizon, bucket), g in trades.groupby(["factor", "horizon", key]):
        base_n = len(trades[(trades.factor == factor) & (trades.horizon == horizon)])
        rr = g["realized_return"].dropna()
        rows.append(
            {
                "factor": factor,
                "horizon": int(horizon),
                "bucket_type": key,
                "bucket": str(bucket),
                "n_trades": int(len(g)),
                "hit_tp_rate": float(g["hit_tp"].mean()),
                "hit_sl_rate": float(g["hit_sl"].mean()),
                "expire_close_rate": float(g["expire_close"].mean()),
                "avg_realized_return": float(rr.mean()) if len(rr) else np.nan,
                "win_rate": float((rr > 0).mean()) if len(rr) else np.nan,
                "trade_share": float(len(g) / max(1, base_n)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", default="optimized_v2", choices=sorted(PRESETS))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    barriers = PRESETS[args.preset]
    out = args.output_dir or (
        ROOT
        / "china_a_share_alpha_output/factor_mining_loop"
        / f"path_barrier_audit_2025_{args.preset}"
    )
    out.mkdir(parents=True, exist_ok=True)

    print(f"preset={args.preset} barriers={barriers}", flush=True)
    panel = _prepare_panel()
    dates = panel.index.get_level_values("date").unique().sort_values()
    lib = pd.read_csv(LIVE)
    if "factor" not in lib.columns:
        lib["factor"] = [f"factor_{i+1}" for i in range(len(lib))]

    all_trades = []
    summaries: list[dict] = []
    for i, row in lib.iterrows():
        name = str(row["factor"])
        expr = str(row["expression"])
        print(f"[{i+1}/{len(lib)}] {name}", flush=True)
        try:
            trades, meta = evaluate_factor(name, expr, panel, dates, barriers)
            if trades.empty:
                continue
            all_trades.append(trades)
            summaries.extend(meta)
            for s in meta:
                print(
                    f"  H={s['horizon']} TP={s['hit_tp_rate']:.1%} SL={s['hit_sl_rate']:.1%} "
                    f"EXP={s['expire_close_rate']:.1%} E[r]={s['avg_realized_return']:.2%} "
                    f"win={s['win_rate']:.1%}",
                    flush=True,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {exc}", flush=True)

    trades = pd.concat(all_trades, ignore_index=True)
    trades.to_csv(out / "trades_detail.csv", index=False, encoding="utf-8")
    summary = pd.DataFrame(summaries)
    summary.to_csv(out / "factor_summary.csv", index=False, encoding="utf-8")
    buckets = pd.concat(
        [
            _bucket_table(trades, "sector"),
            _bucket_table(trades, "mv_bin"),
            _bucket_table(trades, "pb_bin"),
            _bucket_table(trades, "pe_bin"),
        ],
        ignore_index=True,
    )
    buckets.to_csv(out / "bucket_hit_rates.csv", index=False, encoding="utf-8")

    lines = [
        f"# 路径障碍因子审计（优化预设 `{args.preset}`）",
        "",
        "## 规则",
        "",
        "- 信号日 T **收盘价**买入；窗口 T+1..T+H。",
        "- 分周期止盈/止损（相对买入价，盘中 high/low）：",
    ]
    for h, (tp, sl) in sorted(barriers.items()):
        lines.append(f"  - **{h}日**：止盈 +{tp:.0%}，止损 −{sl:.0%}")
    lines.extend(
        [
            "- 同日触及两者：止损优先。",
            "- **到期处理**：未触障碍则在第 H 日 **收盘价平仓**，计入已实现收益（不再把 timeout 当纯失败）。",
            f"- 选股：每日因子 Top {TOP_FRAC:.0%}；验证信号 ≥ {TEST_START.date()}（至 {dates.max().date()}）。",
            "",
            "## 校准依据",
            "",
            "- 旧规则 +15%/−10% 对 5 日过严（MFE p90 才≈14%），导致 83–93% timeout。",
            "- optimized_v2 贴近路径分位：5 日 MFE≈p60–p70、MAE≈p30；10 日略放宽。",
            "",
            "## 因子总表（按 5 日期望收益排序）",
            "",
            "| 因子 | H | TP/SL | 笔数 | 止盈率 | 止损率 | 到期平仓率 | 期望收益 | 胜率 |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for h in sorted(barriers):
        sub = summary[summary["horizon"] == h].sort_values(
            "avg_realized_return", ascending=False
        )
        if h != 5:
            lines.append("")
            lines.append(f"## 因子总表（{h}日，按期望收益排序）")
            lines.append("")
            lines.append(
                "| 因子 | H | TP/SL | 笔数 | 止盈率 | 止损率 | 到期平仓率 | 期望收益 | 胜率 |"
            )
            lines.append("|---|---:|---|---:|---:|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            lines.append(
                f"| {r['factor']} | {int(r['horizon'])} | +{r['tp']:.0%}/−{r['sl']:.0%} | "
                f"{int(r['n_trades'])} | {r['hit_tp_rate']:.1%} | {r['hit_sl_rate']:.1%} | "
                f"{r['expire_close_rate']:.1%} | {r['avg_realized_return']:.2%} | {r['win_rate']:.1%} |"
            )

    # Top factor buckets by expectancy
    if not summary.empty:
        top5 = summary[summary["horizon"] == 5].sort_values(
            "avg_realized_return", ascending=False
        )
        if not top5.empty:
            top = str(top5.iloc[0]["factor"])
            lines.append("")
            lines.append(f"## 最优因子分箱（5日期望最高：{top}）")
            for key, title in (
                ("sector", "板块"),
                ("mv_bin", "市值分位"),
                ("pb_bin", "PB分位"),
                ("pe_bin", "PE代理分位"),
            ):
                lines.append("")
                lines.append(f"### {title}")
                lines.append("")
                lines.append("| 分箱 | 笔数 | 止盈率 | 到期平仓 | 期望收益 | 胜率 |")
                lines.append("|---|---:|---:|---:|---:|---:|")
                sub = buckets[
                    (buckets["factor"] == top)
                    & (buckets["horizon"] == 5)
                    & (buckets["bucket_type"] == key)
                    & (buckets["n_trades"] >= 30)
                ].sort_values("avg_realized_return", ascending=False)
                for _, r in sub.head(10).iterrows():
                    lines.append(
                        f"| {r['bucket']} | {int(r['n_trades'])} | {r['hit_tp_rate']:.1%} | "
                        f"{r['expire_close_rate']:.1%} | {r['avg_realized_return']:.2%} | {r['win_rate']:.1%} |"
                    )

    lines.append("")
    lines.append(f"输出：`{out.as_posix()}`")
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "meta.json").write_text(
        json.dumps(
            {
                "preset": args.preset,
                "barriers": {str(k): {"tp": v[0], "sl": v[1]} for k, v in barriers.items()},
                "expire_rule": "close_on_horizon_end",
                "top_frac": TOP_FRAC,
                "test_start": str(TEST_START.date()),
                "test_end": str(dates.max().date()),
                "same_day_rule": "stop_loss_priority",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print((out / "REPORT.md").read_text(encoding="utf-8")[:4000])
    print("DONE", out)


if __name__ == "__main__":
    main()
