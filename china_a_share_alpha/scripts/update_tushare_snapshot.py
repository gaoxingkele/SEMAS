"""Incrementally extend a frozen A-share snapshot with latest Tushare data."""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import tushare as ts

from china_a_share_alpha.data.talib_features import add_talib_features
from china_a_share_alpha.scripts.run_frozen_promotion_audit import (
    _json_hash,
    _panel_summary,
    _sha256_file,
    verify_snapshot,
)

FINANCIAL_COLUMNS = [
    "roe",
    "roe_dt",
    "netprofit_yoy",
    "dt_netprofit_yoy",
    "grossprofit_margin",
    "debt_to_assets",
    "ocfps",
    "eps",
]
MONEYFLOW_COLUMNS = [
    "buy_elg_amount",
    "sell_elg_amount",
    "buy_lg_amount",
    "sell_lg_amount",
    "buy_md_amount",
    "sell_md_amount",
    "buy_sm_amount",
    "sell_sm_amount",
    "net_mf_amount",
]


def _call_with_retry(call: Callable[[], pd.DataFrame], label: str) -> pd.DataFrame:
    for attempt in range(3):
        try:
            result = call()
            return pd.DataFrame() if result is None else result
        except Exception:
            if attempt == 2:
                raise RuntimeError(f"Tushare request failed after retries: {label}")
            time.sleep(1.0 * (attempt + 1))
    raise AssertionError("unreachable")


def _fetch_date_endpoint(
    pro: Any,
    endpoint: str,
    trade_date: str,
    cache_dir: Path,
) -> pd.DataFrame:
    path = cache_dir / endpoint / f"{trade_date}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    method = getattr(pro, endpoint)
    frame = _call_with_retry(lambda: method(trade_date=trade_date), f"{endpoint}:{trade_date}")
    frame.to_parquet(path)
    time.sleep(0.12)
    return frame


def merge_incremental_rows(
    old_panel: pd.DataFrame,
    daily: pd.DataFrame,
    daily_basic: pd.DataFrame,
    moneyflow: pd.DataFrame,
    financial_updates: pd.DataFrame,
    current_symbols: set[str],
) -> pd.DataFrame:
    """Build enriched incremental rows and append them to historical data."""
    if daily.empty:
        raise ValueError("daily update is empty")
    frame = daily[daily["ts_code"].isin(current_symbols)].copy()
    frame = frame.rename(columns={"ts_code": "symbol", "trade_date": "date", "vol": "volume"})
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d")

    if not daily_basic.empty:
        basic = daily_basic[daily_basic["ts_code"].isin(current_symbols)].copy()
        basic = basic.rename(columns={"ts_code": "symbol", "trade_date": "date"})
        basic["date"] = pd.to_datetime(basic["date"], format="%Y%m%d")
        columns = ["symbol", "date", "turnover_rate", "pb", "total_mv", "circ_mv"]
        frame = frame.merge(
            basic[[column for column in columns if column in basic]],
            on=["symbol", "date"],
            how="left",
        )

    if not moneyflow.empty:
        flow = moneyflow[moneyflow["ts_code"].isin(current_symbols)].copy()
        flow = flow.rename(columns={"ts_code": "symbol", "trade_date": "date"})
        flow["date"] = pd.to_datetime(flow["date"], format="%Y%m%d")
        columns = ["symbol", "date", *MONEYFLOW_COLUMNS]
        frame = frame.merge(
            flow[[column for column in columns if column in flow]],
            on=["symbol", "date"],
            how="left",
        )
    if "buy_elg_amount" in frame and "sell_elg_amount" in frame:
        frame["net_elg_amount"] = frame["buy_elg_amount"] - frame["sell_elg_amount"]

    old_last = old_panel.groupby(level="symbol").tail(1).droplevel("date")
    for column in FINANCIAL_COLUMNS:
        frame[column] = frame["symbol"].map(old_last[column]) if column in old_last else np.nan
    if not financial_updates.empty:
        updates = financial_updates.copy()
        updates = updates[updates["ts_code"].isin(current_symbols)]
        updates["ann_date"] = pd.to_datetime(updates["ann_date"], format="%Y%m%d")
        for update in updates.sort_values("ann_date").itertuples(index=False):
            mask = (frame["symbol"] == update.ts_code) & (frame["date"] >= update.ann_date)
            for column in FINANCIAL_COLUMNS:
                value = getattr(update, column, np.nan)
                if pd.notna(value):
                    frame.loc[mask, column] = value

    for column in ("hk_vol", "hk_ratio"):
        frame[column] = np.nan
    sector_map = old_last["sector"] if "sector" in old_last else pd.Series(dtype=object)
    frame["sector"] = frame["symbol"].map(sector_map)
    frame = frame.set_index(["symbol", "date"]).sort_index()

    combined = pd.concat([old_panel, frame])
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined["return"] = combined.groupby(level="symbol")["close"].pct_change(fill_method=None)
    combined["forward_return"] = combined.groupby(level="symbol")["return"].shift(-1)
    combined["vwap"] = combined["amount"] / combined["volume"].replace(0, np.nan)
    combined = add_talib_features(combined)
    for column in old_panel.columns:
        if column not in combined:
            combined[column] = np.nan
    return combined[old_panel.columns]


def update_snapshot(
    source_snapshot: Path,
    output_snapshot: Path,
    cache_dir: Path,
    end_date: str,
) -> dict[str, Any]:
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("TUSHARE_TOKEN is required")
    ts.set_token(token)
    pro = ts.pro_api()
    manifest = verify_snapshot(source_snapshot)
    panels = {
        name: pd.read_parquet(source_snapshot / manifest["files"][name]["file"])
        for name in ("train", "val", "test")
    }
    old_full = pd.concat(panels.values()).sort_index()
    old_max = pd.Timestamp(panels["test"].index.get_level_values("date").max())
    start_date = (old_max + pd.Timedelta(days=1)).strftime("%Y%m%d")

    calendar = _call_with_retry(
        lambda: pro.trade_cal(
            exchange="SSE", start_date=start_date, end_date=end_date, is_open="1"
        ),
        "trade_cal",
    )
    trade_dates = sorted(calendar["cal_date"].astype(str).tolist())
    if not trade_dates:
        raise ValueError(f"no new open dates from {start_date} through {end_date}")
    latest_date = trade_dates[-1]

    weights = _call_with_retry(
        lambda: pro.index_weight(
            index_code="000300.SH",
            start_date=(pd.Timestamp(latest_date) - pd.Timedelta(days=180)).strftime("%Y%m%d"),
            end_date=latest_date,
        ),
        "index_weight:000300.SH",
    )
    weight_date = str(weights["trade_date"].max())
    current_symbols = set(weights.loc[weights["trade_date"].astype(str) == weight_date, "con_code"])
    historical_symbols = set(old_full.index.get_level_values("symbol"))
    missing_history = sorted(current_symbols - historical_symbols)
    if missing_history:
        raise ValueError(f"current constituents missing frozen history: {missing_history}")

    daily_parts = []
    basic_parts = []
    flow_parts = []
    for index, trade_date in enumerate(trade_dates, start=1):
        daily_parts.append(_fetch_date_endpoint(pro, "daily", trade_date, cache_dir))
        basic_parts.append(_fetch_date_endpoint(pro, "daily_basic", trade_date, cache_dir))
        flow_parts.append(_fetch_date_endpoint(pro, "moneyflow", trade_date, cache_dir))
        if index % 10 == 0:
            print(f"Fetched {index}/{len(trade_dates)} trade dates", flush=True)

    daily_frame = pd.concat([frame for frame in daily_parts if not frame.empty], ignore_index=True)
    basic_frame = pd.concat([frame for frame in basic_parts if not frame.empty], ignore_index=True)
    flow_frame = pd.concat([frame for frame in flow_parts if not frame.empty], ignore_index=True)
    actual_latest_date = str(daily_frame["trade_date"].astype(str).max())
    dates_with_data = int(daily_frame["trade_date"].astype(str).nunique())
    financial_updates = _call_with_retry(
        lambda: pro.fina_indicator_vip(start_date=start_date, end_date=actual_latest_date),
        f"fina_indicator_vip:{start_date}:{actual_latest_date}",
    )
    combined = merge_incremental_rows(
        old_full,
        daily_frame,
        basic_frame,
        flow_frame,
        financial_updates,
        current_symbols,
    )
    updated_test = combined[
        combined.index.get_level_values("date")
        >= panels["test"].index.get_level_values("date").min()
    ]

    output_snapshot.mkdir(parents=True, exist_ok=True)
    output_panels = {"train": panels["train"], "val": panels["val"], "test": updated_test}
    files = {}
    for name, panel in output_panels.items():
        path = output_snapshot / f"{name}.parquet"
        panel.to_parquet(path)
        files[name] = {"file": path.name, "sha256": _sha256_file(path), **_panel_summary(panel)}

    stock_basic = _call_with_retry(
        lambda: pro.stock_basic(
            exchange="", list_status="L", fields="ts_code,name,industry,market"
        ),
        "stock_basic",
    )
    stock_basic.to_csv(output_snapshot / "stock_basic.csv", index=False, encoding="utf-8-sig")
    source = {
        "provider": "Tushare Pro",
        "incremental_start": start_date,
        "requested_end": end_date,
        "calendar_latest_open_date": latest_date,
        "latest_trade_date": actual_latest_date,
        "index_code": "000300.SH",
        "index_weight_date": weight_date,
        "current_constituents": len(current_symbols),
        "calendar_open_dates": len(trade_dates),
        "new_trade_dates": dates_with_data,
        "financial_update_rows": int(len(financial_updates)),
    }
    manifest_core = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_id": manifest["snapshot_id"],
        "source_config": source,
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "files": files,
    }
    manifest_core["snapshot_id"] = _json_hash(
        {"source_config": source, "files": {name: value["sha256"] for name, value in files.items()}}
    )
    (output_snapshot / "manifest.json").write_text(
        json.dumps(manifest_core, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    return manifest_core


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-snapshot", type=Path, required=True)
    parser.add_argument("--output-snapshot", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--end-date", required=True, help="YYYYMMDD")
    args = parser.parse_args()
    manifest = update_snapshot(
        source_snapshot=args.source_snapshot,
        output_snapshot=args.output_snapshot,
        cache_dir=args.cache_dir,
        end_date=args.end_date,
    )
    print(json.dumps({"snapshot_id": manifest["snapshot_id"], **manifest["source_config"]}))


if __name__ == "__main__":
    main()
