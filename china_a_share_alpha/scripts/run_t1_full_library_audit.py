"""Audit every canonical factor library under the frozen T+1 exit contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from china_a_share_alpha.backtest.t1_exit_policy import DEFAULT_THRESHOLDS, run_t1_exit_backtest
from china_a_share_alpha.factor.parser import parse_expression


def _expressions(path: Path) -> tuple[str, ...]:
    frame = pd.read_csv(path)
    if "expression" not in frame.columns:
        return ()
    return tuple(sorted(set(frame["expression"].dropna().astype(str))))


def discover_libraries(output_root: Path) -> pd.DataFrame:
    """Find canonical libraries and collapse identical expression sets."""
    paths = (
        list(output_root.glob("factor_mining_loop/live_library*.csv"))
        + list(output_root.glob("dual_horizon_30round_campaign/*d/research_live_library.csv"))
        + list(output_root.glob("factor_mining_loop/iter_*/combined_library.csv"))
        + list(output_root.glob("dual_horizon_30round_campaign/*d/iter_*/combined_library.csv"))
        + [output_root / "alpha101_seed_library.csv"]
    )
    grouped: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        expressions = _expressions(path)
        if not expressions:
            continue
        digest = hashlib.sha256("\n".join(expressions).encode()).hexdigest()[:16]
        row = grouped.setdefault(
            digest,
            {
                "library_id": digest,
                "primary_path": str(path),
                "source_paths": [],
                "expressions": expressions,
                "expression_count": len(expressions),
            },
        )
        row["source_paths"].append(str(path))
    records = []
    for row in grouped.values():
        records.append(
            {
                **row,
                "source_count": len(row["source_paths"]),
                "source_paths_json": json.dumps(row["source_paths"], ensure_ascii=False),
            }
        )
    return pd.DataFrame(records).sort_values("primary_path").reset_index(drop=True)


def _load_snapshot(snapshot_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    folds = []
    for name in ("train", "val", "test"):
        fold = pd.read_parquet(snapshot_dir / manifest["files"][name]["file"])
        fold["audit_fold"] = name
        folds.append(fold)
    panel = pd.concat(folds).sort_index()
    metadata = pd.read_csv(snapshot_dir / "stock_basic.csv", encoding="utf-8")
    metadata = metadata.rename(columns={"ts_code": "symbol"})
    return panel, metadata, manifest


def _daily_zscore(series: pd.Series) -> pd.Series:
    grouped = series.groupby(level="date")
    mean = grouped.transform("mean")
    std = grouped.transform("std").replace(0, np.nan)
    return ((series - mean) / std).clip(-5, 5)


def build_library_signals(
    libraries: pd.DataFrame,
    full_panel: pd.DataFrame,
    test_index: pd.MultiIndex,
    min_factor_coverage: float,
) -> tuple[dict[str, pd.Series], pd.DataFrame]:
    """Evaluate every unique expression once and stream it into library sums."""
    expression_to_libraries: dict[str, list[int]] = {}
    for library_index, row in libraries.iterrows():
        for expression in row.expressions:
            expression_to_libraries.setdefault(expression, []).append(library_index)

    shape = (len(libraries), len(test_index))
    sums = np.zeros(shape, dtype=np.float32)
    counts = np.zeros(shape, dtype=np.uint16)
    errors: list[dict[str, str]] = []
    for position, (expression, library_indices) in enumerate(
        expression_to_libraries.items(), start=1
    ):
        try:
            evaluated = parse_expression(expression).eval(full_panel)
            values = _daily_zscore(evaluated).reindex(test_index).to_numpy(dtype=np.float32)
            valid = np.isfinite(values)
            safe = np.where(valid, values, 0.0)
            for library_index in library_indices:
                sums[library_index] += safe
                counts[library_index] += valid
        except Exception as exc:
            errors.append({"expression": expression, "error": str(exc)})
        if position % 10 == 0 or position == len(expression_to_libraries):
            print(f"EXPRESSIONS {position}/{len(expression_to_libraries)} errors={len(errors)}")

    signals: dict[str, pd.Series] = {}
    for library_index, row in libraries.iterrows():
        required = max(1, int(np.ceil(row.expression_count * min_factor_coverage)))
        valid = counts[library_index] >= required
        values = np.full(len(test_index), np.nan, dtype=np.float32)
        values[valid] = sums[library_index, valid] / counts[library_index, valid]
        signals[row.library_id] = pd.Series(values, index=test_index, name=row.library_id)
    return signals, pd.DataFrame(errors)


def _benchmark(panel: pd.DataFrame, symbols: set[str]) -> dict[str, float]:
    rows = panel[panel.index.get_level_values("symbol").astype(str).isin(symbols)]
    returns = rows["close"].groupby(level="symbol").pct_change(fill_method=None)
    daily = returns.groupby(level="date").mean().dropna()
    if len(daily) <= 1 or float(daily.std()) < 1e-12:
        return {"benchmark_sharpe": 0.0, "benchmark_return": 0.0, "benchmark_max_drawdown": 0.0}
    nav = (1.0 + daily).cumprod()
    return {
        "benchmark_sharpe": float(daily.mean() / daily.std() * np.sqrt(252)),
        "benchmark_return": float(nav.iloc[-1] ** (252 / len(daily)) - 1.0),
        "benchmark_max_drawdown": float((nav / nav.cummax() - 1.0).min()),
    }


def run_audit(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    snapshot_dir = Path(config["snapshot_dir"])
    output_root = Path(config["factor_output_root"])
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    libraries = discover_libraries(output_root)
    panel, metadata, manifest = _load_snapshot(snapshot_dir)
    test = panel[panel["audit_fold"] == "test"].drop(columns="audit_fold")
    test_index = test.index
    signals, errors = build_library_signals(
        libraries,
        panel.drop(columns="audit_fold"),
        test_index,
        float(config.get("min_factor_coverage", 0.5)),
    )

    metadata["market_group"] = metadata["market"].map(
        lambda value: (
            "innovation"
            if value in {"创业板", "科创板"}
            else "bse" if value == "北交所" else "main"
        )
    )
    symbol_groups = metadata.set_index("symbol")["market_group"].to_dict()
    panel_symbols = set(test.index.get_level_values("symbol").astype(str))
    universes = {
        "all_stocks": {"main", "innovation", "bse"},
        "main_board": {"main"},
        "innovation": {"innovation"},
        "bse": {"bse"},
    }
    benchmark_by_universe = {}
    universe_counts = {}
    for name, groups in universes.items():
        symbols = {symbol for symbol in panel_symbols if symbol_groups.get(symbol) in groups}
        universe_counts[name] = len(symbols)
        benchmark_by_universe[name] = _benchmark(test, symbols) if symbols else {}

    results: list[dict[str, Any]] = []
    all_trades: list[pd.DataFrame] = []
    total = len(libraries) * len(config["horizons"]) * len(universes)
    completed = 0
    for _, library in libraries.iterrows():
        signal = signals[library.library_id]
        for universe_name, groups in universes.items():
            for horizon in config["horizons"]:
                completed += 1
                if universe_counts[universe_name] < int(config.get("min_universe_symbols", 5)):
                    results.append(
                        {
                            "library_id": library.library_id,
                            "primary_path": library.primary_path,
                            "expression_count": library.expression_count,
                            "universe": universe_name,
                            "horizon": horizon,
                            "status": "unavailable",
                            "reason": "insufficient symbols in frozen snapshot",
                            "n_symbols": universe_counts[universe_name],
                        }
                    )
                    continue
                metrics, trades, _ = run_t1_exit_backtest(
                    signal,
                    test,
                    metadata,
                    horizon=int(horizon),
                    selection_fraction=float(config.get("selection_fraction", 0.2)),
                    transaction_cost=float(config.get("transaction_cost", 0.001)),
                    slippage=float(config.get("slippage", 0.0005)),
                    universe_groups=groups,
                )
                results.append(
                    {
                        "library_id": library.library_id,
                        "primary_path": library.primary_path,
                        "expression_count": library.expression_count,
                        "universe": universe_name,
                        "status": "ok" if metrics["valid"] else "invalid",
                        **benchmark_by_universe[universe_name],
                        **metrics,
                    }
                )
                if not trades.empty:
                    trades.insert(0, "horizon", horizon)
                    trades.insert(0, "universe", universe_name)
                    trades.insert(0, "library_id", library.library_id)
                    all_trades.append(trades)
                if completed % 20 == 0 or completed == total:
                    print(f"BACKTESTS {completed}/{total}")

    result_frame = pd.DataFrame(results)
    trade_frame = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    libraries.drop(columns="expressions").to_csv(output_dir / "library_catalog.csv", index=False)
    errors.to_csv(output_dir / "expression_errors.csv", index=False)
    result_frame.to_csv(output_dir / "library_strategy_results.csv", index=False)
    if not trade_frame.empty:
        trade_frame.to_parquet(output_dir / "trade_receipts.parquet", index=False)

    coverage = {
        "snapshot_id": manifest.get("snapshot_id"),
        "date_start": str(test.index.get_level_values("date").min().date()),
        "date_end": str(test.index.get_level_values("date").max().date()),
        "canonical_library_count": int(len(libraries)),
        "unique_expression_count": int(
            len({e for values in libraries.expressions for e in values})
        ),
        "expression_error_count": int(len(errors)),
        "universe_symbol_counts": universe_counts,
        "unavailable_asset_classes": {
            "indexes": (
                "no independent index OHLC panel in frozen snapshot; "
                "equal-weight universe benchmark reported"
            ),
            "etfs": "no ETF OHLC/factor panel in local cache",
        },
        "policy_thresholds": {
            name: {
                "stop_loss": value.stop_loss,
                "profit_activation": value.profit_activation,
                "trailing_drawdown": value.trailing_drawdown,
                "price_limit": value.price_limit,
            }
            for name, value in DEFAULT_THRESHOLDS.items()
        },
        "config": config,
    }
    (output_dir / "audit_manifest.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result_frame, libraries, coverage


def _write_report(results: pd.DataFrame, coverage: dict[str, Any], output_path: Path) -> None:
    valid = results.query("status == 'ok'").copy()
    lines = [
        "# T+1 分板块全因子库审计",
        "",
        f"- 冻结测试期：{coverage['date_start']} 至 {coverage['date_end']}",
        f"- 去重因子库：{coverage['canonical_library_count']}；独立表达式：{coverage['unique_expression_count']}",
        f"- 表达式错误：{coverage['expression_error_count']}",
        f"- 股票池覆盖：{coverage['universe_symbol_counts']}",
        "- ETF与独立指数行情不在本地冻结数据中，未伪造结果。",
        "",
        "## 各周期/股票池最佳库（按Sharpe）",
        "",
        "| Universe | Horizon | Library | Sharpe | Benchmark | Excess | Annual return | Max DD | Trades |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    if not valid.empty:
        best = valid.loc[valid.groupby(["universe", "horizon"])["sharpe"].idxmax()]
        for _, row in best.sort_values(["universe", "horizon"]).iterrows():
            lines.append(
                f"| {row.universe} | {int(row.horizon)}D | `{row.library_id}` | {row.sharpe:.3f} | "
                f"{row.benchmark_sharpe:.3f} | {row.sharpe - row.benchmark_sharpe:.3f} | "
                f"{row.annualized_return:.2%} | {row.max_drawdown:.2%} | {int(row.n_trades)} |"
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    results, _, coverage = run_audit(config)
    _write_report(results, coverage, Path(config["output_dir"]) / "REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
