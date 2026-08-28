"""External validation of frozen evolved factors on unused A-share stocks.

The candidate set is frozen from every campaign leaderboard row whose original
out-of-sample Sharpe exceeded a chosen threshold.  Validation uses historical
CSI 500 constituent snapshots and excludes every symbol in the original frozen
snapshot.  Constituent membership is applied as-of each historic rebalance
date, rather than using today's index members.

The script deliberately reads ``TUSHARE_TOKEN`` only from the environment; it
never serialises credentials into output artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tushare as ts

from china_a_share_alpha.backtest.long_short_backtest import run_long_short_backtest
from china_a_share_alpha.data.talib_features import add_talib_features
from china_a_share_alpha.data.tushare_loader import _load_or_fetch
from china_a_share_alpha.evaluator.metrics import ic_score, rank_ic_score
from china_a_share_alpha.factor.parser import parse_expression

INDEX_CODE = "000905.SH"


def _pro_client() -> Any:
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("TUSHARE_TOKEN must be set in the environment.")
    ts.set_token(token)
    return ts.pro_api()


def _original_symbols(snapshot_dir: Path) -> set[str]:
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    symbols: set[str] = set()
    for fold in ("train", "val", "test"):
        frame = pd.read_parquet(snapshot_dir / manifest["files"][fold]["file"], columns=[])
        symbols.update(frame.index.get_level_values("symbol").astype(str))
    return symbols


def _historical_membership(
    pro: Any, start_date: str, end_date: str, original_symbols: set[str]
) -> pd.DataFrame:
    weights = pro.index_weight(index_code=INDEX_CODE, start_date=start_date, end_date=end_date)
    if weights is None or weights.empty:
        raise RuntimeError("Tushare returned no historical CSI500 constituent records.")
    weights = weights[["trade_date", "con_code"]].drop_duplicates().copy()
    weights["trade_date"] = pd.to_datetime(weights["trade_date"], format="%Y%m%d")
    weights = weights[~weights["con_code"].isin(original_symbols)]
    return weights.sort_values(["trade_date", "con_code"])


def _freeze_candidates(campaign_dir: Path, min_original_sharpe: float) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in campaign_dir.glob("*d/iter_*/evolution/factor_loop_leaderboard.csv"):
        horizon = int(path.parts[-4].removesuffix("d"))
        iteration = int(path.parts[-3].removeprefix("iter_"))
        frame = pd.read_csv(path)
        frame["horizon"] = horizon
        frame["iteration"] = iteration
        frame["source_file"] = str(path.relative_to(campaign_dir))
        frames.append(frame)
    if not frames:
        raise RuntimeError(f"No leaderboards found under {campaign_dir}")
    all_rows = pd.concat(frames, ignore_index=True)
    selected = all_rows.loc[all_rows["test_sharpe"] > min_original_sharpe].copy()
    selected = selected.sort_values("test_sharpe", ascending=False)
    selected = selected.drop_duplicates(["horizon", "expression"], keep="first")
    selected["factor_id"] = selected.apply(
        lambda r: hashlib.sha256(f"{int(r.horizon)}|{r.expression}".encode()).hexdigest()[:16],
        axis=1,
    )
    columns = [
        "factor_id",
        "horizon",
        "iteration",
        "candidate_id",
        "expression",
        "test_sharpe",
        "test_mdd",
        "test_ic",
        "test_rank_ic",
        "turnover",
        "source_file",
    ]
    return selected[columns].sort_values(["horizon", "test_sharpe"], ascending=[True, False])


def _load_panel(
    pro: Any, symbols: list[str], start_date: str, end_date: str, cache_dir: Path
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for position, symbol in enumerate(symbols, start=1):
        try:
            frame = _load_or_fetch(pro, symbol, start_date, end_date, cache_dir)
            if not frame.empty:
                frames.append(frame)
        except Exception as exc:  # One unavailable security must not abort the audit.
            print(f"SKIP {symbol}: {exc}")
        if position % 25 == 0 or position == len(symbols):
            print(f"DATA {position}/{len(symbols)}")
    if not frames:
        raise RuntimeError("No symbol data could be loaded.")
    panel = pd.concat(frames, ignore_index=True)
    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    panel = panel.rename(columns={"ts_code": "symbol", "trade_date": "date", "vol": "volume"})
    panel = panel.set_index(["symbol", "date"]).sort_index()
    panel["return"] = panel.groupby(level="symbol")["close"].pct_change(fill_method=None)
    panel["vwap"] = panel["amount"] / panel["volume"].replace(0, np.nan)
    panel = add_talib_features(panel)
    return panel


def _active_rows(panel: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    """Keep rows for the last known historical constituent set on each date."""
    dates = panel.index.get_level_values("date")
    rebalance_dates = np.sort(membership["trade_date"].unique())
    lookup = pd.DataFrame({"date": pd.Index(dates.unique()).sort_values()})
    lookup["rebalance_date"] = pd.merge_asof(
        lookup,
        pd.DataFrame({"rebalance_date": rebalance_dates}),
        left_on="date",
        right_on="rebalance_date",
        direction="backward",
    )["rebalance_date"]
    active = membership.rename(columns={"trade_date": "rebalance_date", "con_code": "symbol"})
    index_frame = panel.index.to_frame(index=False).merge(lookup, on="date", how="left")
    index_frame = index_frame.merge(active, on=["symbol", "rebalance_date"], how="inner")
    return panel.loc[pd.MultiIndex.from_frame(index_frame[["symbol", "date"]])].sort_index()


def _labels(panel: pd.DataFrame, horizon: int) -> pd.Series:
    return panel.groupby(level="symbol")["close"].transform(
        lambda s: s.pct_change(horizon, fill_method=None).shift(-horizon)
    )


def _metric_row(factor: pd.Series, labels: pd.Series) -> dict[str, float]:
    bt = run_long_short_backtest(factor, labels, transaction_cost=0.001)
    return {
        "ic": ic_score(factor, labels),
        "rank_ic": rank_ic_score(factor, labels),
        "sharpe": float(bt["sharpe"]),
        "annualized_return": float(bt["annualized_return"]),
        "max_drawdown": float(bt["max_drawdown"]),
        "turnover": float(bt["turnover"]),
        "cost_adjusted_return": float(bt["cost_adjusted_return"]),
        "observations": int(pd.DataFrame({"f": factor, "r": labels}).dropna().shape[0]),
    }


def _evaluate(
    candidates: pd.DataFrame, panel: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    results: list[dict[str, Any]] = []
    periods = {
        "full": (start, end),
        "2025": (start, min(end, pd.Timestamp("2025-12-31"))),
        "2026": (max(start, pd.Timestamp("2026-01-01")), end),
    }
    for _, candidate in candidates.iterrows():
        try:
            factor = parse_expression(candidate.expression).eval(panel)
            labels = _labels(panel, int(candidate.horizon))
            for period, (period_start, period_end) in periods.items():
                if period_start > period_end:
                    continue
                mask = (factor.index.get_level_values("date") >= period_start) & (
                    factor.index.get_level_values("date") <= period_end
                )
                row = candidate.to_dict()
                row.update(
                    {
                        "period": period,
                        "period_start": str(period_start.date()),
                        "period_end": str(period_end.date()),
                    }
                )
                row.update(_metric_row(factor.loc[mask], labels.loc[mask]))
                results.append(row)
        except Exception as exc:
            results.append({**candidate.to_dict(), "period": "error", "error": str(exc)})
    return pd.DataFrame(results)


def _report(results: pd.DataFrame, path: Path, metadata: dict[str, Any]) -> None:
    full = results.query("period == 'full'").copy()
    positive = full[(full["sharpe"] > 0) & (full["ic"] > 0)] if not full.empty else full
    lines = [
        "# 未使用股票外部验证：历史 CSI500（2025–2026）",
        "",
        "该结果为冻结候选集合的横截面外部验证，不据此再选择或晋升因子。",
        "",
        f"- 冻结候选数：{metadata['candidate_count']}（原股票池 OOS Sharpe > {metadata['min_original_sharpe']}）",
        f"- 原快照排除股票数：{metadata['original_symbol_count']}；外部股票数：{metadata['external_symbol_count']}",
        f"- 可审计期间：{metadata['evaluation_start']} 至 {metadata['evaluation_end']}。",
        "- 股票池按每个历史 CSI500 成分记录日向前填充；2025 年 1–5 月无可用历史成分记录，未声称覆盖。",
        "- 交易假设：每日五分位多空，单边成本 10bp；5D/10D 标签为对应的前瞻持有期收益。",
        "",
        "## 全期同向（Sharpe>0 且 IC>0）的候选",
        "",
    ]
    if positive.empty:
        lines.append("无。")
    else:
        show = positive.sort_values("sharpe", ascending=False).head(30)
        lines += [
            "| Horizon | Iteration | Factor ID | Sharpe | IC | Max DD | Expression |",
            "|---:|---:|---|---:|---:|---:|---|",
        ]
        for _, r in show.iterrows():
            lines.append(
                f"| {int(r.horizon)}D | {int(r.iteration)} | {r.factor_id} | {r.sharpe:.3f} | "
                f"{r.ic:.4f} | {r.max_drawdown:.3f} | `{r.expression}` |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--start-date", default="20240101", help="Data burn-in start date.")
    parser.add_argument("--evaluation-start", default="20250530")
    parser.add_argument("--end-date", default="20260716")
    parser.add_argument("--min-original-sharpe", type=float, default=2.0)
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=0,
        help="Deterministic random external-stock sample size; zero uses the full union.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    original = _original_symbols(args.snapshot_dir)
    pro = _pro_client()
    membership = _historical_membership(pro, args.evaluation_start, args.end_date, original)
    symbols = sorted(membership["con_code"].unique())
    if args.max_symbols:
        if args.max_symbols > len(symbols):
            raise ValueError("--max-symbols exceeds the unused historical CSI500 universe.")
        rng = np.random.default_rng(20260721)
        symbols = sorted(rng.choice(symbols, size=args.max_symbols, replace=False).tolist())
        membership = membership[membership["con_code"].isin(symbols)]
    candidates = _freeze_candidates(args.campaign_dir, args.min_original_sharpe)
    candidates.to_csv(args.output_dir / "frozen_candidates.csv", index=False)
    membership.to_csv(args.output_dir / "historical_unused_csi500_membership.csv", index=False)

    panel = _load_panel(pro, symbols, args.start_date, args.end_date, args.cache_dir)
    panel = _active_rows(panel, membership)
    start, end = pd.Timestamp(args.evaluation_start), pd.Timestamp(args.end_date)
    results = _evaluate(candidates, panel, start, end)
    results.to_csv(args.output_dir / "external_validation_results.csv", index=False)
    metadata = {
        "candidate_count": int(len(candidates)),
        "min_original_sharpe": args.min_original_sharpe,
        "original_symbol_count": len(original),
        "external_symbol_count": len(symbols),
        "evaluation_start": args.evaluation_start,
        "evaluation_end": args.end_date,
        "data_start": args.start_date,
        "index_code": INDEX_CODE,
        "sample_size": args.max_symbols or len(symbols),
        "sample_seed": 20260721 if args.max_symbols else None,
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    _report(results, args.output_dir / "external_validation_report.md", metadata)
    print(json.dumps(metadata))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
